from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.ct_discriminator import CtDiscriminator
from clarity_ext.domain.validation import UsageError


class RTPCRAnalyseService(object):
    def __init__(self, context):
        self.context = context

    def execute(self):
        ct_analysis_service = CtDiscriminator(self.context)

        rt_pcr_control_types = ['rtpcr_pos', 'rtpcr_neg']
        found_controls = list()
        # 1. Check control values
        for _, output in self.context.all_analytes:
            if output.udf_control == 'Yes' and output.udf_control_type.lower() in rt_pcr_control_types:
                found_controls.append(output.udf_control_type.lower())
                if not ct_analysis_service.validate_control_value(
                        output.udf_control_type, output.udf_ct):
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
            covid_result = ct_analysis_service.analyze(ct)
            original_sample.udf_map.force("rtPCR covid-19 result", covid_result)
            original_sample.udf_map.force("rtPCR Passed", True)
            self.context.update(original_sample)
