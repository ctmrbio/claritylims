from clarity_ext_scripts.covid.rtpcr_analysis_service import ABI7500RTPCRAnalysisService
from clarity_ext_scripts.covid.rtpcr_analysis_service import QuantStudio7AnalysisService
from clarity_ext_scripts.covid.rtpcr_analysis_service import DIAGNOSIS_RESULT_KEY
from clarity_ext_scripts.covid.rtpcr_analysis_service import FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL
from clarity_ext_scripts.covid.rtpcr_analysis_service import FAILED_STATES
from clarity_ext.domain.validation import UsageError


RT_PCR_POSITIVE_CONTROL = 'Positive PCR Control'
RT_PCR_NEGATIVE_CONTROL = 'Negative PCR Control'


class RtPcrAnalyseExecution(object):
    def __init__(self, context):
        self.context = context

    def execute(self):
        if not self._has_assay_udf():
            raise UsageError("The udf 'Assay' must be filled in before running this script")

        if not self._has_instrument_udf():
            raise UsageError("The udf 'Instrument Used' must be filled in before running this script")

        # Prepare analyse service input args
        ct_analysis_service, udf_name_for_ct_control = self._instantiate_service()
        samples = list()
        positive_controls = list()
        negative_controls = list()
        for _, output in self.context.all_analytes:
            result = {
                "id": output.id,
                "FAM-CT": output.udf_famct,
                udf_name_for_ct_control: output.udf_map[udf_name_for_ct_control].value,
            }
            if output.name == RT_PCR_POSITIVE_CONTROL:
                positive_controls.append(result)
            elif output.name == RT_PCR_NEGATIVE_CONTROL:
                negative_controls.append(result)
            else:
                samples.append(result)

        if len(positive_controls) == 0 or len(negative_controls) == 0:
            raise UsageError('positive and negative rtPCR controls were not found on this plate.')

        # Fetch results from service
        result_gen = ct_analysis_service.analyze_samples(
            positive_controls, negative_controls, samples)

        # Populate udfs
        artifact_dict = {output.id: output for _, output in self.context.all_analytes}
        for result in result_gen:
            output = artifact_dict[result["id"]]
            original_sample = output.sample()
            covid_result = result[DIAGNOSIS_RESULT_KEY]
            output.udf_map.force("rtPCR covid-19 result", covid_result)
            output.udf_map.force("rtPCR Passed", covid_result not in FAILED_STATES)
            original_sample.udf_map.force("rtPCR covid-19 result latest", covid_result)
            # TODO: "rtPCR Passed" may be redundant?
            original_sample.udf_map.force("rtPCR Passed latest", covid_result not in FAILED_STATES)
            self.context.update(original_sample)
            self.context.update(output)

        # Check control values
        artifacts_that_failed = [
            name for name in artifact_dict
            if artifact_dict[name].udf_rtpcr_covid19_result ==
               FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL
        ]
        rt_pcr_passed = len(artifacts_that_failed) == 0
        self.context.current_step.udf_map.force("rtPCR Passed", rt_pcr_passed)
        self.context.update(self.context.current_step)

    def _instantiate_service(self):
        if self.instrument == 'qPCR ABI 7500':
            service = ABI7500RTPCRAnalysisService()
        elif self.instrument == 'Quant Studio 7':
            service = QuantStudio7AnalysisService()
        else:
            raise UsageError("The instrument in 'Instrument Used' is not recognized: {}"
                             .format(self.instrument))

        udf_name_for_ct_control = service.internal_control_reporter_key
        return service, udf_name_for_ct_control

    @property
    def assay(self):
        return self.context.current_step.udf_assay

    @property
    def instrument(self):
        return self.context.current_step.instrument

    def _has_instrument_udf(self):
        try:
            _ = self.instrument
        except AttributeError:
            return False

        return True

    def _has_assay_udf(self):
        try:
            _ = self.assay
        except AttributeError:
            return False

        return True
