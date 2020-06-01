import dateutil.parser
from datetime import datetime
from sminet_client import (SampleInfo, ReferringClinic, Patient, Doctor,
                           SmiNetLabExport, StatusType, Notification)
from sminet_client import Gender as SmiNetGender
from clarity_ext_scripts.covid.services.knm_service import ServiceRequestProvider


class KNMSmiNetIntegrationService(object):

    MAP_GENDER_FROM_KNM_TO_SMINET = {
        "male": SmiNetGender.MALE,
        "female": SmiNetGender.FEMALE,
        "other": SmiNetGender.UNKNOWN,
        "unknown": SmiNetGender.UNKNOWN,
        None: SmiNetGender.UNKNOWN,
    }

    def __init__(self, config, knm_service, sminet_service):
        self.config = config
        self.sminet_service = sminet_service
        self.knm_service = knm_service

    def get_county_from_organization(self, organization):
        """
        Given the raw json from the KNM service, returns a county understood by SmiNet
        """
        aliases = organization["alias"]
        for alias in aliases:
            county_code = alias.split("-")[0]
            if self.sminet_service.client.is_supported_county_code(county_code):
                return county_code
        raise self.knm_service.NoSupportedCountyCodeFound(
            "No supported county code found in alias list. Found: {}".format(aliases))

    def create_sample_info(self, provider, sample, free_text):
        sample_date_referral = provider.service_request["resource"]["authoredOn"]
        # The date is on ISO8601 format:
        sample_date_referral = dateutil.parser.isoparse(sample_date_referral)

        return SampleInfo(status=StatusType.FINAL_RESPONSE,
                          sample_id=sample.org_referral_code,
                          sample_date_arrival=sample.date_arrival,
                          sample_date_referral=sample_date_referral,
                          sample_material=sample.material,
                          sample_free_text_referral=free_text)

    def create_referring_clinic(self, provider):
        """Creates a referring clinic object from KNM data"""
        referring_clinic_name = provider.patient["managingOrganization"]["display"]
        referring_clinic_county = self.get_county_from_organization(
            provider.organization)
        referring_doctor = provider.service_request["resource"]["requester"]["display"]

        # TODO: We don't have an address for the referring clinic
        return ReferringClinic(referring_clinic_name, "",
                               referring_clinic_county, Doctor(referring_doctor))

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
            except KeyError:
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

    def export_to_sminet(self, sample, doctor_name, lab_result, sample_free_text):
        """
        Exports a SmiNetLabExport based on a sample

        :sample: A KNMSampleAccessor object
        :doctor_name: Name of the doctor
        :lab_result: A LabResult entry (for convenience one can use those created by SmiNetService)
        """
        # Generate export:
        provider = ServiceRequestProvider(
            self.knm_service.client, sample.org_uri, sample.org_referral_code)

        sample_info = self.create_sample_info(
            provider, sample, sample_free_text)
        reporting_doctor = Doctor(doctor_name)
        referring_clinic = self.create_referring_clinic(provider)
        patient = self.create_patient(provider)
        notification = Notification(sample_info, reporting_doctor, referring_clinic, patient,
                                    lab_result)
        laboratory = self.sminet_service.get_laboratory()

        export = SmiNetLabExport(datetime.now(), laboratory, notification)

        # Send it
        self.sminet_service.client.create(
            export, export.notification.sample_info.sample_id)


class IntegrationError(Exception):
    pass