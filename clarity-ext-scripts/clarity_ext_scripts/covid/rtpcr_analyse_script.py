from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.rtpcr_analysis_service import RTPCRAnalysisService
from clarity_ext.domain.validation import UsageError

BOUNDARY_DICT = {'Assay 1': (10, 50)}
RT_PCR_POSITIVE_CONTROL = 'rtpcr_pos'
RT_PCR_NEGATIVE_CONTROL = 'rtpcr_neg'


class Extension(GeneralExtension):
    def execute(self):
        self.initial_validation()
        ct_analysis_service = RTPCRAnalysisService()
        lower_bound, upper_bound = BOUNDARY_DICT[self.assay]

        rt_pcr_control_types = [RT_PCR_POSITIVE_CONTROL, RT_PCR_NEGATIVE_CONTROL]
        found_controls = list()
        self.context.current_step.udf_map.force("rtPCR Passed", False)
        for _, output in self.context.all_analytes:
            original_sample = output.sample()
            original_sample.udf_map.force("rtPCR Passed", False)

        # 1. Check control values
        for _, output in self.context.all_analytes:
            original_sample = output.sample()
            if original_sample.udf_control == 'Yes' \
                    and original_sample.udf_control_type.lower() in rt_pcr_control_types:
                found_controls.append(original_sample.udf_control_type.lower())
                ct_analysis_service.validate_control_value(
                    original_sample.udf_control_type, output.udf_ct,
                    lower_bound, upper_bound)

        if not set(rt_pcr_control_types).issubset(set(found_controls)):
            raise UsageError('positive and negative rtPCR controls were not found on this plate: {}'
                             .format(set(found_controls)))

        if not ct_analysis_service.is_valid():
            return

        # 2. Control values ok, pass this run
        self.context.current_step.udf_rtpcr_passed = True

        # 3. Populate values
        for _, output in self.context.all_analytes:
            original_sample = output.sample()
            ct = output.udf_ct
            covid_result = ct_analysis_service.analyze(ct, lower_bound, upper_bound)
            original_sample.udf_map.force("rtPCR covid-19 result", covid_result)
            original_sample.udf_map.force("rtPCR Passed", True)
            self.context.update(original_sample)

    def initial_validation(self):
        if not self._has_assay_udf():
            raise UsageError("The udf 'Assay' must be filled in before running this script")
        if self.assay not in BOUNDARY_DICT:
            raise UsageError("The current assay value is not recognized: {}"
                             .format(self.assay))

    @property
    def assay(self):
        return self.context.current_step.udf_assay

    def _has_assay_udf(self):
        try:
            _ = self.assay
        except AttributeError:
            return False

        return True

    def integration_tests(self):
        # yield "24-39269"
        yield "24-40616"
