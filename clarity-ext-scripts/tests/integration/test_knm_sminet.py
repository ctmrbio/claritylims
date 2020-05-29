import os
from lxml import etree as ET
from uuid import uuid4
import random
import string
import yaml
import pytest
from datetime import datetime
from sminet_client import (SampleInfo, ReferringClinic, Patient, Doctor,
                           SmiNetClient, SmiNetValidationError, SmiNetConfig, Laboratory)

from clarity_ext_scripts.covid.sminet_settings import get_sminet_config, create_covid_request
from clarity_ext_scripts.covid.knm_service import KNMConfig
from clarity_ext_scripts.covid.knm_sminet_service import KNMSmiNetIntegrationService
from clarity_ext_scripts.covid.partner_api_client import (
    PartnerAPIV7Client, KARLSSON_AND_NOVAK, ORG_URI_BY_NAME)
from clarity_ext.cli import load_config


"""
Tests the SmiNet/KNM integration
"""

try:
    config = load_config()
except ConfigNotFoundError:
    pytest.xfail("This test requires a sminet_client configuration file")


def generate_valid_contract_with_random_sample_id():
    """
    Returns a tuple of the parameters required to upload sample info via client.create 
    """
    constant_date = datetime(2020, 4, 30)
    request_created = datetime(2020, 5, 18, 18, 11, 6)
    timestamp = datetime.now().strftime("%y%m%dT%H%M%S")
    prefix = "{}-".format(timestamp)
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
    laboratory = Laboratory(91, "National Pandemic Center at KI")
    return create_covid_request(sample_info, referring_clinic, patient, reporting_doctor, laboratory)


@pytest.mark.now()
def test_can_create_request():
    """
    NOTE: We work against a whitelist on a jump server. Information available from team lead.
    NOTE: Reads config from your clarity-ext config which should point to the test environment.
          If sminet config is not available, the test is ignored. This is because the test
          can't run on the build server because it's not whitelisted at the moment.
    """

    from clarity_ext_scripts.covid.knm_service import KNMSampleAccessor

    integration = KNMSmiNetIntegrationService(config)
    org_uri = ORG_URI_BY_NAME[KARLSSON_AND_NOVAK]
    sample = KNMSampleAccessor(org_uri, "5236417647", datetime.now())
    integration.export_to_sminet(sample)
    return

    #7224014063
    print(organization)
    print(patient)
    print("INFO")
    print(referring_clinic_name)

    return

    print(req)
    client = SmiNetClient(config)

    # export = generate_valid_contract_with_random_sample_id()
    # file_name = export.notification.sample_info.sample_id
    # client.create(export, file_name)

    sminet_client = get_sminet_client()

    print(org_uri)

    #sample_date_referral = req.
    from pprint import pprint
    pprint(req)
    resource = req["resource"]

    ## Build SampleInfo
    sample_id = resource["id"]
    # TODO: date-received on the submitted sample
    sample_date_arrival = datetime.datetime(2020, 1, 1)
    sample_date_referral = resource["authoredOn"]  # ISO-format
    sample_date_referral = knm_client.parse_date(sample_date_referral)
    sample_info = SampleInfo(
        status=1,
        sample_id=sample_id,
        sample_date_arrival=sample_date_arrival,
        sample_date_referral=sample_date_referral,
        sample_material="Svalg",
        sample_free_text_referral="Anamnes: Personalprov")
    print(sample_info)

    ## Build ReferringClinic:
    # referringDoctor: {ServiceRequest.requester.display}
    #  resource["requester"]["display"]  TODO: is None now!

    ## Build Patient object
    #
    patient_reference = resource["subject"]["reference"]
    patient_json = knm_client.get_by_reference(patient_reference)

    patient_organization_ref = patient_json["managingOrganization"]["reference"]
    organization_json = knm_client.get_by_reference(patient_organization_ref)

    patient_sex = patient_json["gender"]

    print("Patient")
    print(patient_json)
    print(organization_json)
    print(patient_sex)

    print(knm_client.get_by_reference("Organization/4"))

    # Patient
    # patientId: {ServiceRequest.subject.reference -> Patient.identifier[0].value}</patientId>
    # patientSex: {ServiceRequest.subject.reference -> Patient.gender}</patientSex>
    # patientName: {ServiceRequest.subject.reference -> Patient.name[0].text}</patientName>
    # patientAge: {(ServiceRequest.subject.reference -> Patient.identifier[0].value[8:] - NOW() )}

    # {u'managingOrganization':
    #     {
    #         u'display': u'Region V\xe4sterbotten - Personalprov regionen', u'reference': u'Organization/4-9'},
    #         u'name': [{u'text': u'No one', u'given': [u'No'], u'family': u'one'}],
    #         u'resourceType': u'Patient',
    #         u'gender': u'unknown',
    #         u'address': [{u'country': u'SE'}],
    #         u'id': u'626'
    #     }

    # {u'resource': {
    #            u'code': {u'coding': [{u'code': u'covid19',
    #                                   u'system': u'http://uri.d-t.se/id/CodeSystem/cs-test-types'}],
    #                      u'text': u'Covid-19'},
    #            u'id': u'624',
    #            u'identifier': [{u'assigner': {u'display': u'Direkttest unique referral code'},
    #                             u'system': u'http://uri.d-t.se/id/Identifier/i-referral-code',
    #                             u'value': u'3834043766'}],
    #            u'intent': u'original-order',
    #            u'requester': None,
    #            u'resourceType': u'ServiceRequest',
    #            u'status': u'active',
    #            u'subject': {u'reference': u'Patient/626'}},
    #  u'search': {u'mode': u'match'}}
