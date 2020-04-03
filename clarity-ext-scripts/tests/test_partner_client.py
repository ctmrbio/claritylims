
from clarity_ext_scripts.covid.partner_api_client import PartnerAPISampleInformation, FailedInContactingTestPartner, \
    PartnerAPIClient
from mock import patch


class TestPartnerAPIClient(object):

    class MockValidPostResponse(object):
        def __init__(self):
            self.status_code = 200

            # TODO If we want more advanced tests here, note that maybe this info needs to line up with the info sent.
            #      Right now the client does not validate the response.
            self.text = """success
referrral_code=1234567890
covid19_result=failed
arrival_date=20140310
test_date=20140310
result_date=20140310
comment=ett testmeddelande"""

    def test_validate_sample_information_instance(self):
        # If all values are ok, don't raise
        # TODO Get some valid referral codes from partner. In their example it is 0 below, but it appears it should
        #      actually be a 7 based on the library I use, and online calculators I have tested.
        PartnerAPISampleInformation(referral_code="1234567897", lab_referral="internal-123", arrival_date="20200302",
                                    result_date="20200303", comment="What an awesome sample.", cov19_result="negative")

    def test_can_send_sample_information_instance(self):
        with patch('requests.post', return_value=self.MockValidPostResponse()) as mock_requests_post:
            sample = PartnerAPISampleInformation(referral_code="1234567897", lab_referral="internal-123",
                                                 arrival_date="20200302", result_date="20200303",
                                                 comment="What an awesome sample.", cov19_result="negative")
            config = {"test_partner_url": "https://example.com",
                      "test_partner_user": "api-1",
                      "test_partner_password": "1337"}

            client = PartnerAPIClient(**config)
            res = client.send_single_sample_result(sample)
            assert res
