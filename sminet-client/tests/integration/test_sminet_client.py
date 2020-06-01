import string
import random
from datetime import datetime
import lxml.etree as ET
import pytest
from sminet_client import (SampleInfo, ReferringClinic, Patient, Doctor, SmiNetConfig,
                           LabDiagnosisType, LabResult, Laboratory, SmiNetLabExport,
                           SmiNetConfigNotFoundError, Notification,
                           SmiNetClient, SmiNetValidationError)


"""
Tests an integration to the SmiNet. Requires a configuration file (see README.md)
"""

try:
    config = SmiNetConfig.create_from_search_paths()
except SmiNetConfigNotFoundError:
    pytest.xfail("This test requires a sminet_client configuration file")


def generate_valid_contract_with_random_sample_id():
    """
    Returns a tuple of the parameters required to upload sample info via client.create
    """

    constant_date = datetime(2020, 4, 30)
    request_created = datetime(2020, 5, 18, 18, 11, 6)
    prefix = "int-tests-"
    rnd = "".join(random.choice(string.ascii_uppercase + string.digits)
                  for _ in range(25 - len(prefix)))
    sample_id = prefix + rnd

    sample_info = SampleInfo(status=1, sample_id=sample_id, sample_date_arrival=constant_date,
                             sample_date_referral=constant_date, sample_material="Svalg",
                             sample_free_text_referral="Extra info")
    referring_clinic = ReferringClinic(
        "Clinic name", "", "C", Doctor("Some doctor"))
    patient = Patient("121212-1212", "k", "Tolvan Tolvansson", 23)
    reporting_doctor = Doctor("Reporting Doctor")

    lab_diagnosis = LabDiagnosisType("SCOV2", "SARS-CoV-2 (covid-19)")
    lab_result = LabResult("C", lab_diagnosis)
    notification = Notification(sample_info, reporting_doctor, referring_clinic, patient,
                                lab_result)
    laboratory = Laboratory(config.lab_number, config.lab_name)
    export = SmiNetLabExport(request_created, laboratory, notification)
    return export


def test_can_create_request():
    """
    Tests creating a request. The test is xfailed if the configuration is not available
    """
    client = SmiNetClient(config)
    export = generate_valid_contract_with_random_sample_id()
    timestamp = datetime.now().strftime("%y%m%dT%H%M%S")
    file_name = "{}-{}".format(timestamp,
                               export.notification.sample_info.sample_id)
    client.create(export, file_name)


def test_can_create_request_with_missing_info():
    """
    Ensure that we can create info were the following data is missing
    """
    client = SmiNetClient(config)
    export = generate_valid_contract_with_random_sample_id()

    export.notification.patient.patient_age = "1"  # This can not be empty
    export.notification.patient.patient_age = None
    export.notification.patient.patient_name = ""

    timestamp = datetime.now().strftime("%y%m%dT%H%M%S")
    file_name = "some-empty-{}-{}".format(timestamp,
                                          export.notification.sample_info.sample_id)
    client.create(export, file_name)


def test_covid_request_xml_is_valid_against_xsd_schema():
    client = SmiNetClient(config)
    export = generate_valid_contract_with_random_sample_id()
    xml = export.to_element(client.SMINET_ENVIRONMENT_STAGE)
    client.validate(xml)


def test_covid_request_xml_is_not_valid_against_xsd_schema():
    """
    Ensure that we get a validation error if making a significant change to the xml doc
    """
    client = SmiNetClient(config)
    export = generate_valid_contract_with_random_sample_id()
    xml = export.to_element(client.SMINET_ENVIRONMENT_STAGE)
    element = ET.Element("extra")
    xml.append(element)
    with pytest.raises(SmiNetValidationError):
        client.validate(xml)
