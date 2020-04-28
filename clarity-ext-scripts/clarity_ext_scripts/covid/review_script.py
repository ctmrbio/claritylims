from clarity_ext.extensions import GeneralExtension
from clarity_ext.domain.validation import UsageError
from clarity_ext_scripts.covid.rtpcr_analysis_service import FAILED_BY_REVIEW
from clarity_ext_scripts.covid.rtpcr_analysis_service import FAILED_STATES
from clarity_ext_scripts.covid.partner_api_client import \
    COVID_RESPONSE_NEGATIVE, COVID_RESPONSE_POSITIVE
from clarity_ext_scripts.covid.rtpcr_analysis_service import FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL
from clarity_ext_scripts.covid.controls import Controls


class Extension(GeneralExtension):

    def __init__(self, *args, **kwargs):
        super(Extension, self).__init__(*args, **kwargs)
        self.updated_artifacts = dict()
        self.updated_samples = dict()

    def execute(self):
        self._validate()
        self._update_individual_artifacts()
        self._conditionally_fail_entire_plate()
        # This is a fix for when different instances of the same
        #  artifacts/samples are updated at different locations in script
        for key in self.updated_artifacts:
            self.context.update(self.updated_artifacts[key])
        for key in self.updated_samples:
            self.context.update(self.updated_samples[key])

    def _conditionally_fail_entire_plate(self):
        # If controls are set to failed, fail entire plate
        is_any_control_failed = \
            any(
                c.udf_reviewer_result == FAILED_BY_REVIEW
                for _, c in self.control_artifacts if self._has_reviewer_result_udf(c)
            )

        if is_any_control_failed:
            ordinary_artifacts = [
                artifact for artifact in self.all_outputs
                if artifact.name not in [c.name for _, c in self.control_artifacts]
            ]
            for artifact in ordinary_artifacts:
                original_sample = artifact.sample
                artifact.udf_map.force(
                    "rtPCR covid-19 result", FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL)
                original_sample.udf_map.force(
                    "rtPCR covid-19 result latest", FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL)
                original_sample.udf_map.force("rtPCR Passed latest", "False")
                artifact.udf_map.force("rtPCR Passed", "False")
                self.updated_artifacts[artifact.id] = artifact
                self.updated_samples[original_sample.id] = original_sample

    def _update_individual_artifacts(self):
        # Update individual samples and controls
        for input, output in self.context.artifact_service.all_aliquot_pairs():
            original_sample = output.sample
            if self._has_reviewer_result_udf(output):
                output.udf_map.force(
                    "rtPCR covid-19 result", output.udf_reviewer_result)
                original_sample.udf_map.force(
                    "rtPCR covid-19 result latest", output.udf_reviewer_result)
                rt_pcr_passed = output.udf_reviewer_result != FAILED_BY_REVIEW
                original_sample.udf_map.force("rtPCR Passed latest", str(rt_pcr_passed))
                output.udf_map.force("rtPCR Passed", str(rt_pcr_passed))
            else:
                # Fetch original values from previous step in case user regret a review
                output.udf_map.force(
                    "rtPCR covid-19 result", input.udf_rtpcr_covid19_result)
                output.udf_map.force("rtPCR Passed", input.udf_rtpcr_passed)
                original_sample.udf_map.force(
                    "rtPCR covid-19 result latest", input.udf_rtpcr_covid19_result)
                original_sample.udf_map.force("rtPCR Passed latest", input.udf_rtpcr_passed)
            self.updated_artifacts[output.id] = output
            self.updated_samples[original_sample.id] = original_sample

    @property
    def all_outputs(self):
        return [artifact for _, artifact in self.context.artifact_service.all_aliquot_pairs()]

    @property
    def all_inputs(self):
        return [input for input, _ in self.context.artifact_service.all_aliquot_pairs()]

    @property
    def control_artifacts(self):
        pos_prefix = Controls.MAP_FROM_KEY_TO_ABBREVIATION[Controls.MGI_POSITIVE_CONTROL]
        neg_name = self._get_neg_control_name(Controls.NEGATIVE_PCR_CONTROL)
        control_artifacts = list()
        for input, output in self.context.artifact_service.all_aliquot_pairs():
            if output.name.startswith(pos_prefix) or output.name == neg_name:
                control_artifacts.append((input, output))
        return control_artifacts

    def _get_neg_control_name(self, key):
        key_to_readable = {
            Controls.MAP_FROM_READABLE_TO_KEY[readable]: readable
            for readable in Controls.MAP_FROM_READABLE_TO_KEY
        }
        return key_to_readable[key]

    def _validate(self):
        # Check valid values for reviewer result udf
        valid_values = [
            COVID_RESPONSE_POSITIVE,
            COVID_RESPONSE_NEGATIVE,
            FAILED_BY_REVIEW,
            FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL
        ]
        for artifact in self.all_outputs:
            if self._has_reviewer_result_udf(artifact) \
                    and artifact.udf_reviewer_result not in valid_values:
                raise UsageError("This sample has a not allowed value for 'Reviewer result',"
                                 "valid values: ({}), actual value: {}, sample: {}"
                                 .format(', '.join(valid_values), artifact.udf_reviewer_result,
                                         artifact.name))

        # Check only one plate
        all_containers = {artifact.container.name for artifact in self.all_inputs}
        if len(all_containers) > 1:
            raise UsageError("There are more than 1 plate in this step, which is not allowed!")

        # Check that no control has changed from failed to passed
        for input_control, output_control in self.control_artifacts:
            if self._has_reviewer_result_udf(output_control):
                if input_control.udf_rtpcr_covid19_result in FAILED_STATES\
                        and output_control.udf_reviewer_result != FAILED_BY_REVIEW:
                    raise UsageError("Passing controls that were previously failed is not yet implemented!")

    def _has_reviewer_result_udf(self, artifact):
        try:
            result = artifact.udf_reviewer_result
            if result is None:
                return False
        except AttributeError:
            return False
        return True

    def integration_tests(self):
        yield self.test("24-45334", commit=True)
