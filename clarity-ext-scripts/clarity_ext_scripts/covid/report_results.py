import logging
from datetime import datetime
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.partner_api_client import (
    PartnerAPIV7Client, TESTING_ORG, ORG_URI_BY_NAME, COVID_RESPONSE_FAILED,
    PartnerClientAPIException)
from clarity_ext_scripts.covid.rtpcr_analysis_service import FAILED_STATES
from clarity_ext_scripts.covid.controls import Controls
from clarity_ext_scripts.covid.services.knm_service import KNMClientFromExtension


logger = logging.getLogger(__name__)

UDF_TRUE = "Yes"


class Extension(GeneralExtension):
    """
    Reports sample results to third party partner 
    """

    def map_from_internal_to_external_result(self, sample):
        covid_result = sample.udf_rtpcr_covid19_result_latest
        # Internal values (on analyte)
        if covid_result in FAILED_STATES:
            return COVID_RESPONSE_FAILED
        return covid_result

    def report(self, analyte):
        timestamp = datetime.now().strftime("%y%m%dT%H%M%S")
        sample = analyte.sample()

        org_uri = sample.udf_knm_org_uri
        service_request_id = sample.udf_knm_service_request_id
        fam_ct = sample.udf_famct_latest

        if org_uri == ORG_URI_BY_NAME[TESTING_ORG]:
            logger.warn(
                "Reporting results for test org for analyte {}".format(sample.name))
            return

        result = self.map_from_internal_to_external_result(sample)
        try:
            self.client.post_diagnosis_report(service_request_id=service_request_id,
                                              diagnosis_result=result,
                                              analysis_results=[{"value": fam_ct}])

            # Update udfs
            analyte.udf_map.force("KNM result uploaded", UDF_TRUE)
            analyte.udf_map.force("KNM result uploaded date", timestamp)
            self.context.update(analyte)

            sample.udf_map.force("KNM result uploaded", UDF_TRUE)
            sample.udf_map.force("KNM result uploaded date", timestamp)
            sample.udf_map.force("KNM uploaded source",
                                 analyte.api_resource.uri)
            self.context.update(sample)
            self.context.commit()
        except PartnerClientAPIException as e:
            self.usage_error_defer(
                "Error while uploading sample to KNM", sample.name)
            logger.error(e)

    def is_control(self, sample):
        if sample.name in Controls.MAP_FROM_READABLE_TO_KEY:
            # We recognize built in controls by their name, not the UDF.
            return True
        if sample.udf_control == UDF_TRUE:
            return True
        return False

    def execute(self):
        self.client = KNMClientFromExtension(self)
        for plate in self.context.input_containers:
            for well in plate.occupied:
                already_uploaded = False
                try:
                    already_uploaded = well.artifact.udf_knm_result_uploaded == UDF_TRUE
                except AttributeError:
                    pass

                if self.is_control(well.artifact.sample()):
                    continue
                elif already_uploaded:
                    logger.info("Analyte {} has already been uploaded".format(
                        well.artifact.name))
                    continue

                self.report(well.artifact)

    def integration_tests(self):
        yield "24-44118"
