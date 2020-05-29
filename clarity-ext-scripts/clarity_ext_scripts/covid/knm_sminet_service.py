import codecs
import dateutil.parser
from datetime import datetime
from clarity_ext_scripts.covid.partner_api_client import PartnerAPIV7Client
from sminet_client import SmiNetClient, SmiNetConfig
from clarity_ext.utils import lazyprop
from sminet_client import (SampleInfo, ReferringClinic, Patient, Doctor, SmiNetConfig, NotificationType,
                           LabDiagnosisType, LabResult, Laboratory, SmiNetLabExport)
from sminet_client import Gender as SmiNetGender
from clarity_ext_scripts.covid.knm_service import KNMConfig, ServiceRequestProvider


class KNMSmiNetIntegrationService(object):

    MAP_GENDER_FROM_KNM_TO_SMINET = {
        "male": SmiNetGender.MALE,
        "female": SmiNetGender.FEMALE,
        "other": SmiNetGender.UNKNOWN,
        "unknown": SmiNetGender.UNKNOWN,
        None: SmiNetGender.UNKNOWN,
    }

    def __init__(self, config):
        self.config = config

        knm_config = KNMConfig(config)
        sminet_config = SmiNetConfig(**config)

        self.knm_client = PartnerAPIV7Client(**knm_config)
        self.sminet_client = SmiNetClient(sminet_config)

    def get_county_from_organization(self, organization):
        """
        Given the raw json from the KNM service, returns a county understood by SmiNet
        """
        aliases = organization["alias"]
        for alias in aliases:
            county_code = alias.split("-")[0]
            # TODO: THIS IS JUST FOR TEMPORARY TEST PURPOSES (waiting for knm fix)
            if county_code == "SE":
                county_code = "AB"

            if self.sminet_client.is_supported_county_code(county_code):
                return county_code
        raise NoSupportedCountyCodeFound(
            "No supported county code found in alias list. Found: {}".format(aliases))

    def create_sample_info(self, provider, sample):
        sample_date_referral = provider.service_request["resource"]["authoredOn"]
        # The date is on ISO8601 format:
        sample_date_referral = dateutil.parser.isoparse(sample_date_referral)

        return SampleInfo(status=1,
                          sample_id=sample.org_referral_code,
                          sample_date_arrival=sample.date_arrival,
                          sample_date_referral=sample_date_referral,
                          sample_material="Svalg",
                          sample_free_text_referral="Anamnes: Personalprov")

    def create_referring_clinic(self, provider):
        """Creates a referring clinic object from KNM data"""
        referring_clinic_name = provider.patient["managingOrganization"]["display"]
        referring_clinic_county = self.get_county_from_organization(
            provider.organization)
        referring_doctor = provider.service_request["resource"]["requester"]["display"]

        # TODO: We don't have an address for the referring clinic
        return ReferringClinic(referring_clinic_name, "",
                               referring_clinic_county, Doctor(referring_doctor))


    def map_gender(self, knm_gender):
        """Returns gender in the format required by SmiNet"""
        pass

    def create_patient(self, provider):
        """Creates a Patient object from KNM data"""

        def patient_identifier():
            try:
                patient_identifier = provider.patient["identifier"]
            except KeyError:
                raise IntegrationError(
                    "Missing field 'identifier' on the patient resource for {}".format(provider))

            if len(patient_identifier) == 0:
                raise IntegrationError(
                    "Field 'identifier' is empty on patient resource for {}".format(provider))

            try:
                return patient_identifier[0]["value"]
            except:
                raise IntegrationError(
                    "First entry in 'identifier' doesn't have a value key for {}".format(provider))

        def patient_gender():
            gender = provider.patient["gender"]
            try:
                return self.MAP_GENDER_FROM_KNM_TO_SMINET[gender]
            except KeyError:
                raise IntegrationError(
                    "Unexpected value for key 'gender' ({}) for {}".format(gender, provider))

        def patient_name():
            """
            The name of the patient. Returns an empty string if we don't have the expected data
            """
            name = provider.patient["name"]

            if len(name) == 0:
                return ""

            name = name[0]

            try:
                return name["text"]
            except KeyError:
                return ""

        return Patient(patient_identifier(),
                       patient_gender(),
                       patient_name(),
                       None)

    def get_sminet_export(self, sample):
        """
        Returns a SmiNetLabExport from a sample 

        :sample: A KNMSampleAccessor object
        """

        provider = ServiceRequestProvider(
            self.knm_client, sample.org_uri, sample.org_referral_code)

        sample_info = self.create_sample_info(provider, sample)
        print(sample_info)
        reporting_doctor = Doctor("Lars Engstrand")
        print(reporting_doctor)
        referring_clinic = self.create_referring_clinic(provider)
        print(referring_clinic)
        patient = self.create_patient(provider)
        lab_result = LabResult("C",
                               LabDiagnosisType("SCOV2", "SARS-CoV-2 (covid-19)"))

        notification = NotificationType(sample_info, reporting_doctor, referring_clinic, patient,
                                        lab_result)
        laboratory = Laboratory(91, "National Pandemic Center at KI")

        return SmiNetLabExport(datetime.utcnow(), laboratory, notification)

    def export_to_sminet(self, sample):
        export = self.get_sminet_export(sample)
        self.sminet_client.create(export, export.notification.sample_info.sample_id)


class IntegrationError(Exception):
    pass
