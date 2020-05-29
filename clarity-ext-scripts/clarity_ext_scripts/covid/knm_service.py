from clarity_ext_scripts.covid.partner_api_client import PartnerAPIV7Client
from clarity_ext.utils import lazyprop


def KNMConfig(config):
    """
    Creates config required for KNM from the clarity-ext config (which has more than that)
    """
    return {
        key: config[key]
        for key in [
            "test_partner_base_url",
            "test_partner_code_system_base_url",
            "test_partner_user",
            "test_partner_password"
        ]
    }


def KNMClientFromExtension(extension):
    # A factory for a KnmClient from an extension
    config = KNMConfig(extension.config)
    return PartnerAPIV7Client(**config)


class KNMSampleAccessor(object):
    """
    Describes a sample/analyte in the LIMS that has originally come via the KNM workflow
    """

    def __init__(self, org_uri, org_referral_code, date_arrival):
        self.org_uri = org_uri
        self.org_referral_code = org_referral_code
        self.date_arrival = date_arrival

    @classmethod
    def create_from_lims_sample(cls, sample):
        pass


class ServiceRequestProvider(object):
    """
    Represents a service request. Has methods to retrieve all data we require on it. Gives
    a higher level abstraction of the api for readability.
    """

    def __init__(self, client, org_uri, org_referral_code):
        self.client = client
        self.org_uri = org_uri
        self.org_referral_code = org_referral_code

    @lazyprop
    def service_request(self):
        # The service_request json response
        return self.client.search_for_service_request(self.org_uri, self.org_referral_code)

    @lazyprop
    def patient(self):
        # The patient data corresponding with the service request
        return self.client.get_by_reference(self.patient_ref)

    @lazyprop
    def organization(self):
        managing_organization = self.patient["managingOrganization"]
        return self.client.get_by_reference(managing_organization["reference"])

    @property
    def patient_ref(self):
        # A reference identifying the patient
        return self.service_request["resource"]["subject"]["reference"]

    def __str__(self):
        return "{}|{}".format(self.org_uri, self.org_referral_code)


class NoSupportedCountyCodeFound(Exception):
    pass

