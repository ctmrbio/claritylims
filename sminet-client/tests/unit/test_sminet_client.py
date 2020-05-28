import os
from lxml import etree
from datetime import datetime
from sminet_client import (SampleInfo, ReferringClinic, Patient, Doctor, SmiNetConfig, NotificationType,
        LabDiagnosisType, LabResult, Laboratory, SmiNetLabExport)


def get_fixture(fname):
    fixtures = os.path.join(os.path.dirname(__file__), "..", "fixtures")
    with open(os.path.join(fixtures, fname)) as fs:
        return fs.read()


def create_document():
    constant_date = datetime(2020, 4, 30)
    request_created = datetime(2020, 5, 18, 18, 11, 6)

    sample_info = SampleInfo(status=1, sample_id="123", sample_date_arrival=constant_date,
                             sample_date_referral=constant_date, sample_material="Svalg",
                             sample_free_text_referral="Free text")
    referring_clinic = ReferringClinic("Clinic name", "", "C", Doctor("Referring doctor"))
    patient = Patient("1234", "k", "Patient Name", 23)
    reporting_doctor = Doctor("Reporting Doctor")

    lab_diagnosis = LabDiagnosisType("SCOV2", "SARS-CoV-2 (covid-19)")
    lab_result = LabResult("C", lab_diagnosis)
    notification = NotificationType(sample_info, reporting_doctor, referring_clinic, patient,
                                    lab_result)
    laboratory = Laboratory(1, "Some lab")
    export = SmiNetLabExport(request_created, laboratory, notification)
    return export.to_document("http://stage.sminet.se/xml-schemas/SmiNetLabExport.xsd")

def test_can_create_expected_request():
    expected = get_fixture("valid_request.xml")
    actual = create_document()
    assert expected == actual 


