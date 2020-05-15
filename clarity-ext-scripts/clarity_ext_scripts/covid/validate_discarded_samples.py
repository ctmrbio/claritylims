import cStringIO
import pandas as pd
from datetime import datetime
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.partner_api_client import (
    PartnerAPIV7Client, OrganizationReferralCodeNotFound,
    PartnerClientAPIException)
from clarity_ext_scripts.covid.create_samples.common import (
    BaseValidateRawSampleListExtension, BaseRawSampleListFile)
from clarity_ext_scripts.covid.utils import KNMClient


class RawSampleListColumns(object):
    COLUMN_REFERENCE = "reference"
    COLUMN_SOURCE = "source"
    COLUMN_REASON = "reason"
    COLUMN_FAKE_STATUS = COLUMN_REASON 


class RawSampleListFile(RawSampleListColumns, BaseRawSampleListFile):
    pass


class Extension(BaseValidateRawSampleListExtension):
    """
    Creates a list of validated discarded samples from a raw list of samples
    """

    def execute(self):
        try:
            ordering_org = self.context.current_step.udf_ordering_organization
        except AttributeError:
            self.usage_error("You must select an ordering organization")
        client = KNMClient(self) 

        raw_sample_list = RawSampleListFile.create_from_context(self.context)
        validated_sample_list = raw_sample_list.ValidatedSampleListFile()
        
        for ix, row in validated_sample_list.csv.iterrows():
            barcode = row[validated_sample_list.COLUMN_REFERENCE]
            service_request_id, status, comment, org_uri = self._search_for_id(validated_sample_list,
                client, ordering_org, row)

            validated_sample_list.csv.loc[ix, validated_sample_list.COLUMN_SERVICE_REQUEST_ID] = service_request_id
            validated_sample_list.csv.loc[ix, validated_sample_list.COLUMN_COMMENT] = comment.replace(
                ",", "<SC>")  # If we have the separator in the comment
            validated_sample_list.csv.loc[ix, validated_sample_list.COLUMN_ORG_URI] = org_uri
            validated_sample_list.csv.loc[ix, validated_sample_list.COLUMN_STATUS] = status
            
        validated_sample_list_content = validated_sample_list.csv.to_csv(index=False, sep=",")

        timestamp = datetime.now().strftime("%y%m%dT%H%M%S")

        file_name = "validated_sample_list_{}.csv".format(timestamp)
        self.context.file_service.upload(
            validated_sample_list.FILE_HANDLE, file_name, validated_sample_list_content,
            self.context.file_service.FILE_PREFIX_NONE)

    def integration_tests(self):
        yield "24-46737"

