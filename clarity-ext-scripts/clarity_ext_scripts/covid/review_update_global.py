from clarity_ext.extensions import GeneralExtension
from clarity_ext.domain.validation import UsageError


class Extension(GeneralExtension):
    def execute(self):
        self._validate()
        for _, output in self.context.artifact_service.all_aliquot_pairs():
            original_sample = output.sample
            original_sample.udf_map.force(
                "rtPCR covid-19 result latest", output.udf_rtpcr_covid19_result)
            original_sample.udf_map.force("rtPCR Passed latest", output.udf_rtpcr_passed)
            self.context.update(original_sample)

    def _validate(self):
        error_artifacts = list()
        for _, output in self.context.artifact_service.all_aliquot_pairs():
            if not self._has_covid19_result(output):
                error_artifacts.append(output)
        if len(error_artifacts) > 0:
            raise UsageError("The update script must be run before exiting!")

    def _has_covid19_result(self, artifact):
        try:
            result = artifact.udf_rtpcr_covid19_result
            if result is None:
                return False
        except AttributeError:
            return False
        return True

    def integration_tests(self):
        yield self.test("24-45334", commit=True)
