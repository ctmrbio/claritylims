import cStringIO
import pandas as pd
from datetime import datetime
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.partner_api_client import (
    PartnerAPIV7Client, TESTING_ORG, ORG_URI_BY_NAME, OrganizationReferralCodeNotFound,
    PartnerClientAPIException)
from clarity_ext_scripts.covid.validate_sample_creation_list import BaseValidateExtension


class Extension(BaseValidateExtension):
    """
    Creates a list of validated discarded samples from a raw list of samples
    """

    def execute(self):
        try:
            ordering_org = self.context.current_step.udf_ordering_organization
        except AttributeError:
            self.usage_error("You must select an ordering organization")
        config = {
            key: self.config[key]
            for key in [
                "test_partner_base_url", "test_partner_code_system_base_url",
                "test_partner_user", "test_partner_password"
            ]
        }
        client = PartnerAPIV7Client(**config)

        raw_sample_list = get_raw_sample_list(self.context)
        for ix, row in raw_sample_list.iterrows():
            barcode = row["reference"]
            service_request_id, status, comment, org_uri = self._search_for_id(
                client, ordering_org, barcode)
            raw_sample_list.loc[ix, "service_request_id"] = service_request_id
            raw_sample_list.loc[ix, "status"] = "discard"
            raw_sample_list.loc[ix, "comment"] = comment.replace(
                ",", "<SC>")  # If we have the separator in the comment
            raw_sample_list.loc[ix, "org_uri"] = org_uri
        validated_sample_list = raw_sample_list.to_csv(index=False, sep=",")

        timestamp = datetime.now().strftime("%y%m%dT%H%M%S")

        file_name = "validated_sample_list_{}.csv".format(timestamp)
        self.context.file_service.upload(
            "Validated sample list", file_name, validated_sample_list,
            self.context.file_service.FILE_PREFIX_NONE)

    def integration_tests(self):
        yield "24-45999"


def get_raw_sample_list(context):
    file_name = "Raw sample list"
    f = context.local_shared_file(file_name, mode="rb")

    return pd.read_csv(f, encoding="utf-8", sep=",")
