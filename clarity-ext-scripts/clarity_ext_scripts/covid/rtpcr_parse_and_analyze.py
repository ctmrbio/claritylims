from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.parse_pcr_execution import ParsePcrExecution
from clarity_ext_scripts.covid.rtpcr_analyse_execution import RtPcrAnalyseExecution


class Extension(GeneralExtension):
    def execute(self):
        parse_runner = ParsePcrExecution(self.context)
        parse_runner.execute()
        analyze_runner = RtPcrAnalyseExecution(self.context)
        analyze_runner.execute()

    def integration_tests(self):
        yield "24-39151"
