from uuid import uuid4
import logging
from datetime import datetime
import pandas as pd
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.partner_api_client import PartnerAPIV7Client


logger = logging.getLogger(__name__)


# NOTE: When editing organization keys, one must also update the Clarity field
# "Ordering organization"
TESTING_ORG = "Internal testing"

ORG_URI_BY_NAME = {
    TESTING_ORG: "http://uri.ctmr.scilifelab.se/id/Identifier/ctmr-internal-testing-code",
    "Karlsson and Novak": "http://uri.d-t.se/id/Identifier/i-referral-code",
}


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
            barcode = row["barcode"]
            well = row["well"]

            control_type = barcode if barcode in Controls.ALL else None

            if not control_type:
                if ordering_org == TESTING_ORG:
                    service_request_id = uuid4()
                    logger.warn("Using testing org. Service request ID faked: {}".format(
                        service_request_id))
                else:
                    response = client.search_for_service_request(
                        org_uri, barcode)
                    service_request_id = response["resource"]["id"]

                if service_request_id == "warning":
                    service_request_id = ""
                    status = "error"
                    comment = response["resource"]["issue"][0]["details"][
                        "text"]
                    self.usage_error_defer(
                        "Can't find service_request_id for barcode(s)", barcode)
                else:
                    status = "ok"
                    comment = ""
                raw_sample_list.loc[ix, "org_uri"] = org_uri
            else:
                service_request_id = ""
                status = "ok"
                comment = ""

            raw_sample_list.loc[ix, "service_request_id"] = service_request_id
            raw_sample_list.loc[ix, "status"] = status
            raw_sample_list.loc[ix, "comment"] = comment.replace(
                ";", "<SC>")  # If we have the separator in the comment

        validated_sample_list = raw_sample_list.to_csv(index=False, sep=";")

        timestamp = datetime.now().strftime("%y%m%dT%H%M%S")
        file_name = "validated_sample_list_{}.csv".format(timestamp)
        self.context.file_service.upload(
            "Validated sample list", file_name, validated_sample_list,
            self.context.file_service.FILE_PREFIX_NONE)

    def integration_tests(self):
        yield "24-43219"


class Controls(object):
    POSITIVE_PLASMID_CONTROL = "positive plasmid control"
    NEGATIVE_WATER_CONTROL = "negative water control"
    POSITIVE_VIRUS_CONTROL = "positive virus control"

    ALL = {
        POSITIVE_PLASMID_CONTROL,
        NEGATIVE_WATER_CONTROL,
        POSITIVE_VIRUS_CONTROL,
    }


def get_raw_sample_list(context):
    file_name = "Raw sample list"
    f = context.local_shared_file(file_name, mode="rb")
    return pd.read_csv(f, encoding="utf-8", sep=";")
