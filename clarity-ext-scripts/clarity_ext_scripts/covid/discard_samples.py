import logging
from datetime import datetime
from clarity_ext_scripts.covid.partner_api_client import (
        TESTING_ORG, ORG_URI_BY_NAME, COVID_RESPONSE_FAILED,
        PartnerClientAPIException)
from clarity_ext_scripts.covid.utils import CtmrCovidSubstanceInfo
from clarity_ext_scripts.covid.services.knm_service import KNMClientFromExtension
from clarity_ext_scripts.covid.import_samples import BaseCreateSamplesExtension

logger = logging.getLogger(__name__)

UDF_TRUE = "Yes"


class Extension(BaseCreateSamplesExtension):
    """
    Reports discarded samples to third party partner
    """

    def report(self, analyte):
        timestamp = datetime.now().strftime("%y%m%dT%H%M%S")
        sample = analyte.sample()

        org_uri = sample.udf_knm_org_uri
        service_request_id = sample.udf_knm_service_request_id

        test_mode = org_uri == ORG_URI_BY_NAME[TESTING_ORG]

        if not test_mode:
            try:
                self.client.post_diagnosis_report(service_request_id=service_request_id,
                                                  diagnosis_result=COVID_RESPONSE_FAILED,
                                                  analysis_results=[{"value": -1}])
            except PartnerClientAPIException as e:
                self.usage_error_defer(
                    "Error while uploading sample to KNM", sample.name)
                logger.error(e)
                # This sample will be retried next time
                return
        else:
            logger.warn(
                "Reporting results for test org for analyte {}".format(sample.name))

        # Update udfs
        analyte.udf_map.force("KNM result uploaded", UDF_TRUE)
        analyte.udf_map.force("KNM result uploaded date", timestamp)
        analyte.udf_map.force(
            "Status", CtmrCovidSubstanceInfo.STATUS_DISCARDED_AND_REPORTED)
        self.context.update(analyte)

        sample.udf_map.force("KNM result uploaded", UDF_TRUE)
        sample.udf_map.force("KNM result uploaded date", timestamp)
        sample.udf_map.force("KNM uploaded source", analyte.api_resource.uri)
        sample.udf_map.force(
            "Status", CtmrCovidSubstanceInfo.STATUS_DISCARDED_AND_REPORTED)
        sample.udf_map.force("Status artifact source",
                             analyte.api_resource.uri)
        self.context.update(sample)
        self.context.commit()

    def execute(self):
        self.client = KNMClientFromExtension(self)
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
        yield "24-45997"
