from clarity_ext.extensions import GeneralExtension
from clarity_ext.domain.validation import UsageError
from clarity_ext_scripts.covid.rtpcr_analysis_service import FAILED_BY_REVIEW
from clarity_ext_scripts.covid.rtpcr_analysis_service import FAILED_STATES
from clarity_ext_scripts.covid.partner_api_client import \
    COVID_RESPONSE_NEGATIVE, COVID_RESPONSE_POSITIVE
from clarity_ext_scripts.covid.rtpcr_analysis_service import FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL
from clarity_ext_scripts.covid.controls import Controls


class Extension(GeneralExtension):

    def execute(self):
        self._validate()
        self._update_individual_artifacts()
        self._conditionally_fail_entire_plate()

    def _conditionally_fail_entire_plate(self):
        # If controls are set to failed, fail entire plate
        is_any_control_failed = \
            any(
                c.udf_reviewer_result == FAILED_BY_REVIEW
                for c in self.control_artifacts if self._has_reviewer_result_udf(c)
            )

        if is_any_control_failed:
            ordinary_artifacts = [
                artifact for artifact in self.all_artifacts
                if artifact.name not in [c.name for c in self.control_artifacts]
            ]
            for artifact in ordinary_artifacts:
                original_sample = artifact.sample
                artifact.udf_map.force("Reviewer result", FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL)
                original_sample.udf_map.force(
                    "rtPCR covid-19 result latest", FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL)
                original_sample.udf_map.force("rtPCR Passed latest", "False")
                self.context.update(original_sample)
                self.context.update(artifact)

    def _update_individual_artifacts(self):
        # Update individual samples and controls
        for artifact in self.all_artifacts:
            if self._has_reviewer_result_udf(artifact):
                original_sample = artifact.sample
                original_sample.udf_map.force(
                    "rtPCR covid-19 result latest", artifact.udf_reviewer_result)
                rt_pcr_passed = artifact.udf_reviewer_result != FAILED_BY_REVIEW
                original_sample.udf_map.force("rtPCR Passed latest", str(rt_pcr_passed))
                self.context.update(original_sample)
                self.context.update(artifact)

    @property
    def all_artifacts(self):
        return [artifact for _, artifact in self.context.artifact_service.all_aliquot_pairs()]

    @property
    def all_inputs(self):
        return [input for input, _ in self.context.artifact_service.all_aliquot_pairs()]

    @property
    def control_artifacts(self):
        pos_prefix = Controls.MAP_FROM_KEY_TO_ABBREVIATION[Controls.MGI_POSITIVE_CONTROL]
        neg_name = self._get_neg_control_name(Controls.NEGATIVE_PCR_CONTROL)
        control_artifacts = list()
        for artifact in self.all_artifacts:
            if artifact.name.startswith(pos_prefix) or artifact.name == neg_name:
                control_artifacts.append(artifact)
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
        for artifact in self.all_artifacts:
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
        for control in self.control_artifacts:
            if self._has_reviewer_result_udf(control):
                original_sample = control.sample
                if original_sample.udf_rtpcr_covid19_result_latest in FAILED_STATES\
                        and control.udf_reviewer_result != FAILED_BY_REVIEW:
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
        yield self.test("24-45313", commit=True)
