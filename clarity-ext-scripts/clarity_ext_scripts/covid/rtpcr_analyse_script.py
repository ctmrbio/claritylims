from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.rtpcr_analyse_execution import RtPcrAnalyseExecution


class Extension(GeneralExtension):
    def execute(self):
        runner = RtPcrAnalyseExecution(self.context)
        runner.execute()

    def integration_tests(self):
        yield "24-44139"
