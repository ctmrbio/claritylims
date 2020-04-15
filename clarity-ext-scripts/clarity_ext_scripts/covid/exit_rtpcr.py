from clarity_ext.extensions import GeneralExtension


class Extension(GeneralExtension):
    """
    Make sure user has confirmed that a run was failed
    """
    def execute(self):
        if self.context.current_step.udf_rtpcr_passed == "False":
            self.require_step_udf("Confirm failed run:")

    def require_step_udf(self, required_udf):
        udf_value = ''
        udf_exists = required_udf in self.context.current_step.udf_map.raw_map
        if udf_exists:
            udf_value = self.context.current_step.udf_map[required_udf].value
        if not udf_value == "Done":
            self.usage_error_defer("Please confirm that the run was failed: '{}'", required_udf)

    def integration_tests(self):
        yield self.test("24-10152", commit=False)
