from datetime import datetime
from sminet_client import (SmiNetConfig, NotificationType, LabResult,
                           Laboratory, SmiNetLabExport, LabDiagnosisType)


def create_scov2_positive_lab_result():
    lab_diagnosis = LabDiagnosisType("SCOV2", "SARS-CoV-2 (covid-19)")
    return LabResult("C", lab_diagnosis)


def create_covid_request(sample_info, referring_clinic, patient, reporting_doctor,
                         laboratory, created=None):
    """
    Creates a request to SmiNet that's valid for the Covid project.

    :sample_info: An object created with the SampleInfo factory
    :referring_clinic: An object created with the ReferringClinic factory
    :patient: An object created with the Patient factory
    """

    if not created:
        created = datetime.now()

    notification = NotificationType(sample_info, reporting_doctor, referring_clinic, patient,
                                    create_scov2_positive_lab_result())

    contract = SmiNetLabExport(created, laboratory, notification)
    return contract


def get_sminet_config():
    """
    Gets a configuration object for the sminet client fetched from the clarity-ext config file
    """
    return SmiNetConfig.create_from_search_paths(["~/.config/clarity-ext/clarity-ext.config"])
