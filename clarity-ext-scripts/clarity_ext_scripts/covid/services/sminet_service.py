from sminet_client import (SmiNetConfig, LabResult,
                           Laboratory, LabDiagnosisType, SmiNetClient)


class SmiNetService(object):

    STATUS_SUCCESS = "success"  # We've already uploaded the results to SmiNet
    STATUS_ERROR = "error"  # We've tried to upload the results to SmiNet but failed

    # The sample shouldn't be reported even if it's in the report step. This can be either
    # because the extension figures this out based on business rules, or a research engineer
    # marks it manually as such
    STATUS_IGNORE = "ignore"

    STATUS_RETRY = "retry"

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
