from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.partner_api_client import PartnerAPIClient


class Extension(GeneralExtension):
    """
    Reports sample results to third party partner 
    """

    def execute(self):
        try:
            url = self.config["covid.test_partner_url"]
            user = self.config["covid.test_partner_user"]
            password = self.config["covid.test_partner_password"]
        except:
            raise AssertionError("You must provide url, username and password for the test partner")

        client = PartnerAPIClient(url, user, password)
        print(client)


    def integration_tests(self):
        yield "24-38707"
