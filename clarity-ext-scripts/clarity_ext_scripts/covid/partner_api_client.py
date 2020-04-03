
from datetime import datetime
from luhn import verify as mod10verify
from luhn import generate as mod10generate
import logging
import requests
from requests import ConnectionError, Timeout
from retry import retry
import re


log = logging.getLogger(__name__)

COVID_RESPONSE_POSITIVE = "positive"
COVID_RESPONSE_NEGATIVE = "negative"
COVID_RESPONSE_FAILED = "failed"

VALID_COVID_RESPONSES = {COVID_RESPONSE_POSITIVE,
                         COVID_RESPONSE_NEGATIVE, COVID_RESPONSE_FAILED}


class PartnerAPISampleInformation(object):

    def __init__(self, referral_code, lab_referral, arrival_date, result_date, comment, cov19_result):
        try:
            if not isinstance(referral_code, str) and not len(referral_code) == 10:
                raise AssertionError(
                    "referral_code needs to be 10 digit number string.")

            if not mod10verify(referral_code):
                raise AssertionError("Check code digit {} (last digit) did not match mod10 requirement"
                                     "in referral code: {}. Expected: {}".format(referral_code[-1],
                                                                                 referral_code,
                                                                                 mod10generate(referral_code[:-1])))

            self.referral_code = referral_code

            if len(lab_referral) > 50:
                raise AssertionError(
                    "Cannot have more then 50 characters in lab_referral code.")

            disallowed_chars_regex = re.compile(r"[^A-Za-z0-9\s\.-]")
            if bool(re.search(disallowed_chars_regex, lab_referral)):
                raise AssertionError(
                    "lab_referral can only contain A-Z, a-z, 0-9, white spaces, and -.")

            self.lab_referral = lab_referral

            def verify_date_format(date_str):
                try:
                    datetime.strptime(date_str, '%Y%m%d')
                except ValueError:
                    raise AssertionError(
                        "Incorrect date format on {}, should be YYYYMMDD".format(date_str))

            verify_date_format(arrival_date)
            self.arrival_date = arrival_date

            verify_date_format(result_date)
            self.result_date = result_date

            if len(comment) > 255:
                raise AssertionError(
                    "comments cannot have more than 255 characters")

            self.comment = comment

            if cov19_result not in VALID_COVID_RESPONSES:
                raise AssertionError("cov_19_result has to have one of the following values: {}".format(
                    ", ".join(VALID_COVID_RESPONSES)))
        except AssertionError as e:
            log.error(e.message)
            raise e

    def get_as_dict(self):
        return vars(self)


class FailedInContactingTestPartner(Exception):
    pass


class PartnerAPIClient(object):
    """
    This is a client to enable posting data to the test partners api. It is currently valid for v.6 of the parter's API.
    """

    def __init__(self, test_partner_url, test_partner_user, test_partner_password):
        self._url = test_partner_url
        self._user = test_partner_user
        self._password = test_partner_password

    @retry((ConnectionError, Timeout), tries=3, delay=2, backoff=2)
    def send_single_sample_result(self, test_partner_sample_info):
        """
        Send a single sample result to the test partner.
        @param test_partner_sample_info and instance of PartnerAPISampleInformation
        This will raise FailedInContactingTestPartner if there is any errors, with the details of the
        failure in the exception message. On a successful upload it will return True. Please note that since this
        actually never returns False, it is mostly useful for testing purposes.
        """

        if not isinstance(test_partner_sample_info, PartnerAPISampleInformation):
            raise AssertionError(
                "Expected type of test_partner_sample_info is TestPartnerSampleInformation")

        parameters = test_partner_sample_info.get_as_dict().update(
            {"user": self._user, "password": self._password})
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(
            self._url, header=headers, data=parameters)

        if not response.status_code == 200:
            mess = "Did not get a 200 response from test partner. "
            "Response status code was: {}"
            "and response text: {}".format(
                response.status_code, response.text)
            log.error(mess)
            raise FailedInContactingTestPartner(mess)

        # Example of successful API call response
        # success
        # referrral_code=1234567890
        # covid19_result=failed
        # arrival_date=20140310
        # test_date=20140310
        # result_date=20140310
        # comment=ett testmeddelande
        response_text_parts = response.text.split("\n")
        if not response_text_parts[0] == "success":
            mess = "The response from the test partner indicated some error. This was the response: {}".format(
                response.text)
            log.error(mess)
            raise FailedInContactingTestPartner(mess)

        return True

        # TODO Figure out how text response should be parsed if there is an error.

    # TODO Finish this when/if there is a batch API at the partner.
    @retry((ConnectionError, Timeout), tries=3, delay=2, backoff=2)
    def send_many_sample_results(self, test_partner_sample_info_list):
        pass
