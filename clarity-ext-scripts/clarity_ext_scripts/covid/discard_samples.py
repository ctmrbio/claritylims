import logging
from datetime import datetime
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.partner_api_client import (
    PartnerAPIV7Client, TESTING_ORG, ORG_URI_BY_NAME, COVID_RESPONSE_FAILED,
    PartnerClientAPIException)
from clarity_ext_scripts.covid.rtpcr_analysis_service import FAILED_STATES
from clarity_ext_scripts.covid.controls import Controls
from clarity_ext_scripts.covid.utils import CtmrCovidSubstanceInfo

logger = logging.getLogger(__name__)

UDF_TRUE = "Yes"

class Extension(GeneralExtension):
    """
    Reports sample results to third party partner
    """

    def get_client(self):
        config = {
            key: self.config[key]
            for key in [
                "test_partner_base_url", "test_partner_code_system_base_url",
                "test_partner_user", "test_partner_password"
            ]
        }
        return PartnerAPIV7Client(**config)

    def report(self, analyte):
        timestamp = datetime.now().strftime("%y%m%dT%H%M%S")
        sample = analyte.sample()

        org_uri = sample.udf_knm_org_uri
        service_request_id = sample.udf_knm_service_request_id

        if org_uri == ORG_URI_BY_NAME[TESTING_ORG]:
            logger.warn(
                "Reporting results for test org for analyte {}".format(sample.name))
            return
#       ToDo: Anonymous samples?
        try:
            self.client.post_diagnosis_report(service_request_id=service_request_id,
                                 diagnosis_result=COVID_RESPONSE_FAILED,
                                 analysis_results=[{"value": -1}])

            # Update udfs
            analyte.udf_map.force("KNM result uploaded", UDF_TRUE)
            analyte.udf_map.force("KNM result uploaded date", timestamp)
            analyte.udf_map.force("Status", CtmrCovidSubstanceInfo.STATUS_DISCARDED_AND_REPORTED)
            self.context.update(analyte)

            sample.udf_map.force("KNM result uploaded", UDF_TRUE)
            sample.udf_map.force("KNM result uploaded date", timestamp)
            sample.udf_map.force("KNM uploaded source",
                                 analyte.api_resource.uri)
            sample.udf_map.force("Status", CtmrCovidSubstanceInfo.STATUS_DISCARDED_AND_REPORTED)
            sample.udf_map.force("Status artifact source", analyte.api_resource.uri)
            self.context.update(sample)
            self.context.commit()
        except PartnerClientAPIException as e:
            self.usage_error_defer(
                "Error while uploading sample to KNM", sample.name)
            logger.error(e)

    def execute(self):
        self.client = self.get_client()
        for plate in self.context.input_containers:
            for well in plate.occupied:
                already_uploaded = False
                try:
                    already_uploaded = well.artifact.udf_knm_result_uploaded == UDF_TRUE
                except AttributeError:
                    pass

                if already_uploaded:
                    logger.info("Analyte {} has already been uploaded".format(
                        well.artifact.name))
                    continue

                self.report(well.artifact)

    def integration_tests(self):
        # TODO: Replace with a valid step ID
        yield "24-45972"