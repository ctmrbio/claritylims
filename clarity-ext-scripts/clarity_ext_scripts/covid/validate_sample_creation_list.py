import cStringIO
from uuid import uuid4
import logging
from datetime import datetime
import pandas as pd
from clarity_ext_scripts.covid.controls import Controls
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.partner_api_client import (
    PartnerAPIV7Client, TESTING_ORG, ORG_URI_BY_NAME, OrganizationReferralCodeNotFound, PartnerClientAPIException)
from clarity_ext_scripts.covid.controls import controls_barcode_generator


logger = logging.getLogger(__name__)


class Extension(GeneralExtension):
    """
    Validates all samples in a sample creation list.

    Before execution of this script, a research engineer has uploaded a raw csv on the format:

        barcode;well

    to the `Raw sample list` file handle.

    This script generates a new sample list. It's equivalent to the original sample
    list, but also adds three new fields:

    ```
    barcode: <barcode from csv>
    well: <well from csv>
    *status: <error | success>
    *service_request_id: <the service request ID from KNM>
    *comment: <details about the error, if any>
    ```

    This will be the input for creating samples later on. That extension must require that there
    are no errors in any of the rows. If there is an error, no sample should be created.

    In the case of an error, the research engineer has these options:

        * Edit the raw sample list and run validate again.
        * Edit this script or request changes at KNM.
        * In an extreme case, e.g. given manual confirmation, the research engineer can upload a new
          validated file with manually edited information.
    """

    def _search_for_id(self, client,  org_uri, barcode):
        try:
            response = client.search_for_service_request(
                org_uri, barcode)
            service_request_id = response["resource"]["id"]
            status = "ok"
            comment = ""
        except OrganizationReferralCodeNotFound as e:
            self.usage_warning(
                "Can't find service_request_id in {} for barcode(s). Will set them to anonymous.".format(
                    org_uri), barcode)
            service_request_id = "anonymous"
            status = "anonymous"
            comment = ("No matching request was found for this referral code. Will create an anonymous "
                       "ServiceRequest for this referral code.")
        except PartnerClientAPIException as e:
            self.usage_error_defer(
                "Something was wrong with {} for barcode(s). See file validated sample list for details.".format(
                    org_uri), barcode)
            service_request_id = ""
            status = "error"
            comment = e.message
        return service_request_id, status, comment

    def execute(self):
        # 1. Get the ordering organizations URI
        try:
            ordering_org = self.context.current_step.udf_ordering_organization
        except AttributeError:
            self.usage_error("You must select an ordering organization")
        org_uri = ORG_URI_BY_NAME[ordering_org]

        # 2. Create an API client
        #    Make sure that there is a config at ~/.config/clarity-ext/clarity-ext.config
        config = {
            key: self.config[key]
            for key in [
                "test_partner_base_url", "test_partner_code_system_base_url",
                "test_partner_user", "test_partner_password"
            ]
        }
        client = PartnerAPIV7Client(**config)

        # 3. Read the raw sample list. A semicolon separated list of `barcode;well`
        raw_sample_list = get_raw_sample_list(self.context)

        # 4. Create the validated list
        for ix, row in raw_sample_list.iterrows():
            barcode = row["Sample Id"]
            well = row["Position"]
            # NOTE: The well is in the format "A01" etc
            if len(well) != 3:
                raise AssertionError(
                    "Expected the Position in the raw sample list to be on the format A01. "
                    "Got: {}".format(well))
            row = well[0]
            col = int(well[1:])
            well = "{}:{}".format(row, col)
            # TODO It seems that we always need controls here, which
            #      we need to check if that will always be the case.
            is_control = controls_barcode_generator.parse(barcode)

            if not is_control:
                if ordering_org == TESTING_ORG:
                    service_request_id = uuid4()
                    status = "ok"
                    comment = ""
                    logger.warn("Using testing org. Service request ID faked: {}".format(
                        service_request_id))
                else:
                    service_request_id, status, comment = self._search_for_id(
                        client, org_uri, barcode)

                raw_sample_list.loc[ix, "org_uri"] = org_uri
            else:
                service_request_id = ""
                status = "ok"
                comment = ""

            raw_sample_list.loc[ix, "service_request_id"] = service_request_id
            raw_sample_list.loc[ix, "status"] = status
            raw_sample_list.loc[ix, "comment"] = comment.replace(
                ";", "<SC>")  # If we have the separator in the comment

        validated_sample_list = raw_sample_list.to_csv(index=False, sep=",")

        timestamp = datetime.now().strftime("%y%m%dT%H%M%S")

        file_name = "validated_sample_list_{}.csv".format(timestamp)
        self.context.file_service.upload(
            "Validated sample list", file_name, validated_sample_list,
            self.context.file_service.FILE_PREFIX_NONE)

    def integration_tests(self):
        yield self.test("24-44013", commit=False)


def get_raw_sample_list(context):
    file_name = "Raw sample list"
    f = context.local_shared_file(file_name, mode="rb")

    filtered = cStringIO.StringIO()
    # Ignore everything at or after the line that contains this text:
    stop_condition = "Sample Tracking Report Name"

    for line in f:
        if stop_condition in line:
            break
        filtered.write(line + "\n")
    filtered.seek(0)
    return pd.read_csv(filtered, encoding="utf-8", sep=",")
