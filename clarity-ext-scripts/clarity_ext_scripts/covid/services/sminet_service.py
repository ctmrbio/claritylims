from sminet_client import (SmiNetConfig, LabResult,
                           Laboratory, LabDiagnosisType, SmiNetClient)


class SmiNetService(object):

    def __init__(self, config):
        self.config = SmiNetConfig(**config)
        self.client = SmiNetClient(self.config)

    def get_laboratory(self):
        """
        Retrieves the configured laboratory
        """
        return Laboratory(self.config.lab_number, self.config.lab_name)

    @staticmethod
    def create_scov2_positive_lab_result():
        lab_diagnosis = LabDiagnosisType("SCOV2", "SARS-CoV-2 (covid-19)")
        return LabResult("C", lab_diagnosis)
