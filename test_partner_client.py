
from datetime import datetime
import requests
from requests import ConnectionError, Timeout
import retry
import re

# TODO Figure out logging given how Clarity works.


class TestPartnerSampleInformation(object):

    def __init__(self, referral_code, lab_referral, arrival_date, result_date, comment, cov19_result):

        # REVIEW Discussion point. Not all values here are required, but I see no reason not
        #        to send them, since I do thing we should have them for all cases.

        super().__init__()

        if not isinstance(str, referral_code) and not len(referral_code) == 10:
            raise AssertionError(
                "referral_code needs to be 10 digit number string.")

        if not (int(referral_code[:-1]) % 10 == int(referral_code[-1])):
            raise AssertionError("Check code digit {} (last digit) did not match mod10 requierment" +
                                 "in referral code: {}".format(referral_code[-1], referral_code))

        self.referral_code = referral_code

        if len(lab_referral) > 50:
            raise AssertionError(
                "Cannot have more then 50 characters in lab_referral code.")

        # REVIEW When reviewing verify against docs that
        #        this regex is actually correct.
        allowed_chars_regex = re.compile(r"[^A-Za-z0-9\s\.-]")
        if not bool(re.search(lab_referral)):
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

        valid_covid_responses = ["negative", "positive", "failed"]

        if cov19_result not in valid_covid_responses:
            raise AssertionError("cov_19_result has to have one of the following values: {}".format(
                ", ".join(valid_covid_responses)))

    def get_as_dict(self):
        return vars(self)


class FailedInContactingTestPartner(Exception):
    pass


class TestPartnerClient(object):
    # This is valid for v.6 for the parters API

    def __init__(self, config):
        # TODO Figure out how to configure this, given Claritys normal setup
        super().__init__()
        self._url = config.get("test_partner_url")
        self._user = config.get("test_partner_user")
        self._password = config.get("test_partner_password")

    # TODO decide if we want to retry or not. It depends a little bit on the
    #      rest of the scenario. This could potentially take us into a long chain
    #      of retries. That would mean things take a long time before failing.
    #      Don't know what is best here.
    @retry((ConnectionError, Timeout), tries=3, delay=2, backoff=2)
    def send_single_sample_result(self, test_partner_sample_info):

        if not isinstance(TestPartnerSampleInformation):
            raise AssertionError(
                "Expected type of test_partner_sample_info is TestPartnerSampleInformation")

        parameters = test_partner_sample_info.get_as_dict().update(
            {"user": self._user, "password": self._password})
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(
            self._url, header=headers, data=parameters)

        if not response.status_code == 200:
            raise FailedInContactingTestPartner("Did not get a 200 response from test partner. " +
                                                "Response status code was: {}" +
                                                "and response text: {}".format(response.status_code, response.text))

        # Example of successful API call response
        # success
        # referrral_code=1234567890
        # covid19_result=failed
        # arrival_date=20140310
        # test_date=20140310
        # result_date=20140310
        # comment=ett testmeddelande
        response_text_parts = response.text.split("\n")
        if response_text_parts[0] == "success":
            # REVIEW Should we for a True/False return for this, or something else?
            #        Since it also raises on some failures, it might not be necessary,
            #        if we don't expect to do anything with the results.
            return True
        else:
            return False

        # TODO Figure out how text response should be parsed if there is an error.

    # TODO Finish this when/if there is a batch API at the partner.
    @retry((ConnectionError, Timeout), tries=3, delay=2, backoff=2)
    def send_many_sample_results(self, test_partner_sample_info_list):
        pass
