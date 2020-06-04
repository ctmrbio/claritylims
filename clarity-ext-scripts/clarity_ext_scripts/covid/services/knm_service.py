from clarity_ext_scripts.covid.partner_api_client import PartnerAPIV7Client
from clarity_ext.utils import lazyprop


class NoSupportedCountyCodeFound(Exception):
    pass


class KNMService(object):
    NoSupportedCountyCodeFound = NoSupportedCountyCodeFound

    def __init__(self, config):
        self.config = KNMConfig(config)
        self.client = PartnerAPIV7Client(**self.config)


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

    def __init__(self, org_uri, org_referral_code, date_arrival, material):
        """
        :org_uri: The organization URI as defined by KNM
        :org_referral_code: The referral code within the organization
        :date_arrival: The date the sample was added to the LIMS
        :material: The material, one of the constants in SampleMaterialType
        """
        self.org_uri = org_uri
        self.org_referral_code = org_referral_code
        self.date_arrival = date_arrival
        self.material = material

    @classmethod
    def create_from_lims_sample(cls, sample):
        raise NotImplementedError()


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
