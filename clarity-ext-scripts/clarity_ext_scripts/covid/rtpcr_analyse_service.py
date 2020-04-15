from clarity_ext_scripts.covid.ct_discriminator import CtDiscriminatorForPlate
from clarity_ext.domain.validation import UsageError

VALID_ASSAYS = ['Assay 1']

BOUNDARY_DICT = {'Assay 1': (10, 50)}


class RTPCRAnalyseService(object):
    def __init__(self, context):
        self.context = context

    def execute(self):
        self.initial_validation()
        ct_analysis_service = CtDiscriminatorForPlate()
        lower_bound, upper_bound = BOUNDARY_DICT[self.assay]

        rt_pcr_control_types = ['rtpcr_pos', 'rtpcr_neg']
        found_controls = list()
        self.context.current_step.udf_rtpcr_passed = False
        for _, output in self.context.all_analytes:
            original_sample = output.sample()
            original_sample.udf_map.force("rtPCR Passed", False)

        # 1. Check control values
        for _, output in self.context.all_analytes:
            if output.udf_control == 'Yes' and output.udf_control_type.lower() in rt_pcr_control_types:
                found_controls.append(output.udf_control_type.lower())
                ct_analysis_service.validate_control_value(
                    output.udf_control_type, output.udf_ct, lower_bound, upper_bound)

        if not ct_analysis_service.is_valid():
            return

        if set(rt_pcr_control_types) not in set(found_controls):
            raise UsageError('positive and negative rtPCR controls were not found on this plate: {}'
                             .format(set(found_controls)))

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
        if self.assay not in VALID_ASSAYS:
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
