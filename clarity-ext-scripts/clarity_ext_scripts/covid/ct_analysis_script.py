from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.rtpcr_analyse_service import RTPCRAnalyseService


class Extension(GeneralExtension):
    """
    This class is for testing. In production, CtAnalysisService is called from
    within parse_qpcr.py
    """
    def execute(self):
        ct_analysis_service = RTPCRAnalyseService(self.context)
        ct_analysis_service.execute()

    def integration_tests(self):
        yield "24-39151"
