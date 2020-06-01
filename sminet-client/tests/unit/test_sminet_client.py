import os
from datetime import datetime
from sminet_client import (Doctor, Notification, LabDiagnosisType,
                           LabResult, Laboratory, SmiNetLabExport, StatusType, SampleMaterial)


def get_fixture(fname):
    fixtures = os.path.join(os.path.dirname(__file__), "..", "fixtures")
    with open(os.path.join(fixtures, fname)) as fs:
        return fs.read()


def create_document():
    constant_date = datetime(2020, 4, 30)
    request_created = datetime(2020, 5, 18, 18, 11, 6)

    sample_info = Notification.SampleInfo(
        status=StatusType.FINAL_RESPONSE,
        sample_id="123",
        sample_date_arrival=constant_date,
        sample_date_referral=constant_date,
        sample_material=SampleMaterial.SVALG,
        sample_free_text_referral="Free text")
    referring_clinic = Notification.ReferringClinic(
        "Clinic name", "", "C", Doctor("Referring doctor"))
    patient = Notification.Patient("1234", "k", "Patient Name", 23)
    reporting_doctor = Notification.Doctor("Reporting Doctor")

    lab_diagnosis = LabDiagnosisType("SCOV2", "SARS-CoV-2 (covid-19)")
    lab_result = LabResult("C", lab_diagnosis)
    notification = Notification(sample_info, reporting_doctor, referring_clinic, patient,
                                lab_result)
    laboratory = Laboratory(1, "Some lab")
    export = SmiNetLabExport(request_created, laboratory, notification)
    return export.to_document("http://stage.sminet.se/xml-schemas/SmiNetLabExport.xsd")


def test_can_create_expected_request():
    expected = get_fixture("valid_request.xml")
    actual = create_document()
    assert expected == actual
