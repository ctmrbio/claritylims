from datetime import datetime
import logging
from sminet_client import SampleMaterial, SmiNetError
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.utils import CtmrCovidSubstanceInfo
from clarity_ext_scripts.covid.services.sminet_service import SmiNetService
from clarity_ext_scripts.covid.services.knm_service import KNMSampleAccessor
from clarity_ext_scripts.covid.services.knm_sminet_service import (
    KNMSmiNetIntegrationService, IntegrationError, UnregisteredPatient)
from clarity_ext_scripts.covid.partner_api_client import (
    COVID_RESPONSE_POSITIVE, PartnerClientAPIException)


UDF_TRUE = "Yes"
logger = logging.getLogger(__name__)


def should_report(substance):
    """
    A substance is ignored from SmiNet reporting if it's a control, has been run before or doesn't
    have a positive result. It is also ignored if the research engineer has set the UDF
    "SmiNet status" to "ignore"

    Samples that should be reported must be in the SmiNet state `retry` or `error` or None
    """
    if substance.is_control:
        return False

    if substance.submitted_sample.udf_rtpcr_covid19_result_latest != COVID_RESPONSE_POSITIVE:
        return False

    if substance.sminet_status in [SmiNetService.STATUS_IGNORE, SmiNetService.STATUS_SUCCESS]:
        return False

    if substance.sminet_status not in [
            None,
            SmiNetService.STATUS_RETRY,
            SmiNetService.STATUS_ERROR]:
        raise AssertionError(
            "Unexpected SmiNet status: {}".format(substance.sminet_status))

    return True


class Extension(GeneralExtension):
    """
    Reports results to SmiNet.

    For all analytes in the step:
    * If sminet_status is not set:
        * Checks if it should be imported.
            * If it shouldn't, updates it to "ignore"
            * If it should, tries to send the data
    * If sminet_status is "error", retries it
    * If sminet_status is "ignore", ignores it


    Test data required:
    * Positive  => success
    * Negative  => ignore
    * Failed    => ignore
    * Anonymous => ignore
    """

    def report(self, substance):
        """
        Reports this substance to SmiNet and updates the status in the LIMS.
        """

        org_referral_code = substance.submitted_sample.name.split("_")[0]
        date_arrival = substance.submitted_sample.api_resource.date_received
        date_arrival = datetime.strptime(date_arrival, "%Y-%m-%d")

        sample = KNMSampleAccessor(substance.submitted_sample.udf_knm_org_uri,
                                   org_referral_code,
                                   date_arrival,
                                   SampleMaterial.SVALG)

        integration = KNMSmiNetIntegrationService(self.config)
        lab_result = SmiNetService.create_scov2_positive_lab_result()

        error_msg = ""

        try:
            integration.export_to_sminet(sample,
                                         doctor_name="Lars Engstrand",
                                         lab_result=lab_result,
                                         sample_free_text="",
                                         service_request_notes_to_append={"order_note"})
            status = SmiNetService.STATUS_SUCCESS
        except UnregisteredPatient:
            status = SmiNetService.STATUS_IGNORE
        except PartnerClientAPIException as knm_error:
            error_msg = knm_error.message
            self.usage_error_defer("Error while fetching data from KNM",
                                   substance.submitted_sample.name)
            status = SmiNetService.STATUS_ERROR
        except SmiNetError as sminet_error:
            error_msg = sminet_error.message
            self.usage_error_defer("Error while uploading sample to SmiNet",
                                   substance.submitted_sample.name)
            status = SmiNetService.STATUS_ERROR
        except IntegrationError as int_error:
            self.usage_error_defer("Error while uploading sample to SmiNet",
                                   substance.submitted_sample.name)
            error_msg = int_error.message
            status = SmiNetService.STATUS_ERROR

        timestamp = datetime.now().strftime("%y%m%dT%H%M%S")

        substance.submitted_sample.udf_map.force("SmiNet status", status)
        substance.substance.udf_map.force("SmiNet status", status)

        substance.submitted_sample.udf_map.force(
            "SmiNet uploaded date", timestamp)
        substance.submitted_sample.udf_map.force("SmiNet artifact source",
                                                 substance.substance.api_resource.uri)
        substance.submitted_sample.udf_map.force(
            "SmiNet last error", error_msg)
        self.context.update(substance.submitted_sample)
        self.context.update(substance.substance)
        self.context.commit()

    def execute(self):
        for plate in self.context.input_containers:
            for well in plate.occupied:
                substance = CtmrCovidSubstanceInfo(well.artifact)
                if should_report(substance):
                    self.report(substance)

    def integration_tests(self):
        yield "24-48808"
