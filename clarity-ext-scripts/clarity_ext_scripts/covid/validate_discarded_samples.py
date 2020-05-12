import cStringIO
import pandas as pd
from datetime import datetime
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.partner_api_client import (
    PartnerAPIV7Client, TESTING_ORG, ORG_URI_BY_NAME, OrganizationReferralCodeNotFound, PartnerClientAPIException)


class Extension(GeneralExtension):
    """
    TODO: Add description
    """
    def execute(self):
        try:
            ordering_org = self.context.current_step.udf_ordering_organization
        except AttributeError:
            self.usage_error("You must select an ordering organization")
        org_uri = ORG_URI_BY_NAME[ordering_org]
        config = {
            key: self.config[key]
            for key in [
                "test_partner_base_url", "test_partner_code_system_base_url",
                "test_partner_user", "test_partner_password"
            ]
        }
        client = PartnerAPIV7Client(**config)

        raw_sample_list = get_raw_sample_list(self.context)
        print(raw_sample_list)
        for ix, row in raw_sample_list.iterrows():
            barcode = row["reference"]

            service_request_id, status, comment = self._search_for_id(client, org_uri, barcode)
            raw_sample_list.loc[ix, "service_request_id"] = service_request_id
            raw_sample_list.loc[ix, "status"] = "discard"
            raw_sample_list.loc[ix, "comment"] = comment.replace(
                ";", "<SC>")  # If we have the separator in the comment
        print(raw_sample_list)
        validated_sample_list = raw_sample_list.to_csv(index=False, sep=",")

        timestamp = datetime.now().strftime("%y%m%dT%H%M%S")

        file_name = "validated_sample_list_{}.csv".format(timestamp)
        self.context.file_service.upload(
            "Validated sample list", file_name, validated_sample_list,
            self.context.file_service.FILE_PREFIX_NONE)

    def _search_for_id(self, client,  org_uri, barcode):
        try:
            response = client.search_for_service_request(
                org_uri, str(barcode))
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

    def integration_tests(self):
        # TODO: Replace with a valid step ID
        yield "24-44671"

def get_raw_sample_list(context):
    file_name = "Raw sample list"
    f = context.local_shared_file(file_name, mode="rb")

    return pd.read_csv(f, encoding="utf-8", sep=",")
