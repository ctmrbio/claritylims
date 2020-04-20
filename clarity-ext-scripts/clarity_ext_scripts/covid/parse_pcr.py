from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.parse_pcr_execution import ParsePcrExecution


class Extension(GeneralExtension):
    def execute(self):
        runner = ParsePcrExecution(self.context)
        runner.execute()

    def integration_tests(self):
        yield "24-39151"
