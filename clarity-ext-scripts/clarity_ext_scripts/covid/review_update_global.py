from clarity_ext.extensions import GeneralExtension


class Extension(GeneralExtension):
    def execute(self):
        for _, output in self.context.artifact_service.all_aliquot_pairs():
            original_sample = output.sample
            original_sample.udf_map.force(
                "rtPCR covid-19 result latest", output.udf_rtpcr_covid19_result)
            original_sample.udf_map.force("rtPCR Passed latest", output.udf_rtpcr_passed)
            self.context.update(original_sample)

    def integration_tests(self):
        yield self.test("24-45334", commit=True)
