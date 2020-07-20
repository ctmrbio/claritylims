import base64
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

# NOTE: When editing organization keys, one must also update the Clarity field
# "Ordering organization"
TESTING_ORG = "Internal testing"
KARLSSON_AND_NOVAK = "Karlsson and Novak"
ORG_KUL = "KUL"
ORG_LABPORTALEN = "Labportalen"

ORG_URI_BY_NAME = {
    TESTING_ORG: "http://uri.ctmr.scilifelab.se/id/Identifier/ctmr-internal-testing-code",
    KARLSSON_AND_NOVAK: "http://uri.d-t.se/id/Identifier/i-referral-code",
    ORG_KUL: "http://uri.d-t.se/id/Identifier/i-lab/region-stockholm-karolinska",
    ORG_LABPORTALEN: "http://uri.d-t.se/id/Identifier/i-lab/labportalen"
}


class PartnerClientAPIException(Exception):
    pass


class OrganizationReferralCodeNotFound(PartnerClientAPIException):
    pass


class MoreThanOneOrganizationReferralCodeFound(PartnerClientAPIException):
    pass


class FailedInContactingTestPartner(PartnerClientAPIException):
    pass


class ServiceRequestAlreadyExists(PartnerClientAPIException):
    pass


class CouldNotCreateServiceRequest(PartnerClientAPIException):
    pass


def verify_test_partner_referral_code(code):
    """
    Will check if the check number of the given code is correct.
    Return True if code is ok, else False.
    """
    return mod10verify(code)


class PartnerAPISampleInformation(object):

    def __init__(self, referral_code, lab_referral, arrival_date, result_date, comment, cov19_result):
        try:
            if not isinstance(referral_code, str) and not len(referral_code) == 10:
                raise AssertionError(
                    "referral_code needs to be 10 digit number string.")

            if not verify_test_partner_referral_code(referral_code):
                raise AssertionError(("Check code digit {} (last digit) did not match mod10 requirement"
                                      "in referral code: {}."
                                      "Please verify the code is correct.").format(referral_code[-1],
                                                                                   referral_code))

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

            self.cov19_result = cov19_result

        except AssertionError as e:
            log.error(e.message)
            raise e

    def get_as_dict(self):
        return vars(self)


class PartnerAPIClient(object):
    """
    This is a client to enable posting data to the test partners api. It is currently valid for v.6 of the partner's API.
    """

    def __init__(self, test_partner_url, test_partner_user, test_partner_password,
                 integration_test_mode=False, integration_test_should_fail=0):
        self._url = test_partner_url
        self._user = test_partner_user
        self._password = test_partner_password
        if integration_test_mode:
            self._integration_test_mode = integration_test_mode
            self._integration_test_should_fail = integration_test_should_fail
            self._integration_test_has_failed = 0
        else:
            self._integration_test_mode = False

    def _integration_test(self):
        if self._integration_test_has_failed < self._integration_test_should_fail:
            self._integration_test_has_failed += 1
            raise FailedInContactingTestPartner(("'Fake failed' to contact test partner because integration test "
                                                 "mode is active. This is failure {} of {}.").format(
                self._integration_test_has_failed,
                self._integration_test_should_fail
            ))

    # TODO Remember to re-enable.
    # @retry((ConnectionError, Timeout), tries=3, delay=2, backoff=2)
    def send_single_sample_result(self, test_partner_sample_info):
        """
        Send a single sample result to the test partner.
        @param test_partner_sample_info and instance of PartnerAPISampleInformation
        This will raise FailedInContactingTestPartner if there is any errors, with the details of the
        failure in the exception message. On a successful upload it will return True. Please note that since this
        actually never returns False, it is mostly useful for testing purposes.
        """

        log.debug("Attempting to send information for sample with id: {}".format(
            test_partner_sample_info.referral_code))

        if not isinstance(test_partner_sample_info, PartnerAPISampleInformation):
            raise AssertionError(
                "Expected type of test_partner_sample_info is TestPartnerSampleInformation")

        # If the client is setup in integration test mode, it might fail or return here
        # depending one what settings have been activate.
        # This is not for production use!
        if self._integration_test_mode:
            self._integration_test()
            return True

        parameters = test_partner_sample_info.get_as_dict()
        parameters.update(
            {"user": self._user, "password": self._password})
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(
            self._url, headers=headers, data=parameters)

        if not response.status_code == 200:
            mess = ("Did not get a 200 response from test partner. "
                    "Response status code was: {} "
                    "and response text: {}").format(
                response.status_code, response.text)
            log.error(mess)
            raise FailedInContactingTestPartner(mess)

        log.debug("Got response: {} with text: {}, and headers: {}".format(
            response, response.text, response.headers))
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

    # TODO Finish this when/if there is a batch API at the partner.
    @retry((ConnectionError, Timeout), tries=3, delay=2, backoff=2)
    def send_many_sample_results(self, test_partner_sample_info_list):
        raise NotImplementedError


class PartnerAPIV7Client(object):
    """
    This is a client for v7 of the test partners API.

    The workflow it is designed to support goes along these lines:
      - Search for a ServiceRequest from a organization based on the
        unique organization and their provided sample id. The returned
        ServiceRequest object will contain the test partner referral code,
        and the ServiceRequest id. These values are needed when creating the
        diagnosis result.
      - TODO Post a DiagnosisResult to a specific test partner referral code.
    """

    def __init__(self, test_partner_base_url, test_partner_user, test_partner_password,
                 test_partner_code_system_base_url):
        self._base_url = test_partner_base_url
        self._user = test_partner_user
        self._password = test_partner_password
        self._test_partner_code_system_base_url = test_partner_code_system_base_url
        self._session = requests.Session()

    def _base64_encoded_credentials(self):
        user_and_password = "{}:{}".format(self._user, self._password)
        return base64.b64encode(user_and_password)

    def _generate_headers(self):
        b64_encoded_user_and_password = self._base64_encoded_credentials()

        headers = {"Authorization": "Basic {}".format(
            b64_encoded_user_and_password),
            "Content-Type": "application/fhir+json"}
        return headers

    def search_for_service_request(self, org, org_referral_code):
        try:
            params = {"identifier": "|".join([org, org_referral_code])}
            search_url = "{}/ServiceRequest".format(self._base_url)
            headers = self._generate_headers()

            response = self._session.get(
                url=search_url, headers=headers, params=params)

            # TODO Add integration test mode

            if not response.status_code == 200:
                mess = "Did not get a 200 response from test partner. Response status code was: {}".format(
                    response.status_code)
                try:
                    mess += " and response json: {}".format(response.json())
                except ValueError:
                    mess += " and the response json was empty."
                raise FailedInContactingTestPartner(mess)

            response_json = response.json()

            nbr_of_results = response_json["total"]

            if nbr_of_results == 1:
                service_request = response_json["entry"][0]
                return service_request
            elif nbr_of_results > 1:
                raise MoreThanOneOrganizationReferralCodeFound(
                    ("More than one partner referral code was found for organization: {} "
                     "and organization referral code: {}").format(org, org_referral_code))
            else:
                log.debug("Response json was: {}".format(response_json))
                raise OrganizationReferralCodeNotFound(
                    ("No partner referral code was found for organization: {} "
                     "and organization referral code: {}").format(org, org_referral_code))
        except PartnerClientAPIException as e:
            log.info("Error while connecting to KNM: {}".format(e.message))
            raise e

    def create_anonymous_service_request(self, referral_code):
        """
        This method can be used to create an anonymous service request, that is
        a service request that is not tied to a particular person. This is useful
        when a sample arrives in the lab that has not been properly registered.
        """

        # Pretty much all of this is hard coded, because we will only need to
        # create a single patient at the time.
        payload = {
            "resourceType": "ServiceRequest",
            "contained": [
                {
                    "resourceType": "Patient",
                    "id": "1",
                    "managingOrganization": {
                        "reference": "Organization/2-44"  # Organization/2-44 is "NPC Anonymous"
                    }
                }
            ],
            "identifier": [
                {
                    "system": "{}/id/Identifier/i-referral-code".format(self._test_partner_code_system_base_url),
                    "value": referral_code
                }
            ],
            "status": "active",
            "intent": "original-order",
            "subject": {
                "reference": "#1"
            },
            "code": {
                "coding": [
                    {
                        "system": "{}/id/CodeSystem/cs-test-types".format(
                            self._test_partner_code_system_base_url),
                        "code": "SARS-CoV-2-RNA"
                    }
                ]
            }
        }
        try:
            url = "{}/ServiceRequest".format(
                self._base_url)
            headers = self._generate_headers()

            log.debug("Attemping to create an anonymous ServiceRequst for referral code: {}".format(
                referral_code))

            response = self._session.post(url=url,
                                          json=payload,
                                          headers=headers)

            if response.status_code == 201:
                response_json = response.json()
                service_request_id = response_json["id"]
                log.debug(("Successfully created an anonymous ServiceRequest"
                           " for referral code: {}, got id: {}").format(
                    referral_code, service_request_id))
                return service_request_id
            elif response.status_code == 400:
                raise CouldNotCreateServiceRequest(("Could not create a ServiceRequest for id: {} "
                                                    "This is most likely because the test partner did not "
                                                    "recognize the id.".format(
                                                        referral_code)))
            elif response.status_code == 409:
                raise ServiceRequestAlreadyExists(
                    "There appears to already exist a ServiceRequest for id: {}".format(referral_code))
            else:
                raise PartnerClientAPIException(("Did not get 201 answer from partner API. When trying to create a "
                                                 "ServiceRequest for id: {}"
                                                 "Response was: {} and json: {}").format(
                                                     referral_code,
                                                     response.status_code,
                                                     response.json()))
        except PartnerClientAPIException as e:
            log.error(e.message)
            raise e

    def post_diagnosis_report(self, service_request_id, diagnosis_result, analysis_results,
                              integration_test=False):

        if integration_test:
            log.warn("Integration testing on, not reporting {} to 3rd party".format(
                service_request_id))
            return True

        try:
            payload = self._create_payload(
                service_request_id, diagnosis_result, analysis_results)
            url = "{}/DiagnosticReport".format(
                self._base_url)
            headers = self._generate_headers()

            response = self._session.post(url=url,
                                          json=payload,
                                          headers=headers)

            # TODO Add integration test mode
            if not response.status_code == 201:
                mess = "Did not get a 201 response from test partner. Response status code was: {}".format(
                    response.status_code)
                try:
                    mess += " and response json: {}".format(response.json())
                except ValueError:
                    mess += " and the response json was empty."
                raise FailedInContactingTestPartner(mess)

            return True

        except PartnerClientAPIException as e:
            log.error(e.message)
            raise e

    def get_by_reference(self, ref):
        """
        Get's a resource by reference, such as Organization/123 or Patient/345

        :ref: The reference, e.g. Patient/123
        """
        url = "{}/{}".format(self._base_url, ref)
        headers = self._generate_headers()
        response = self._session.get(url=url, headers=headers)
        if response.status_code != 200:
            print(response.text)
            raise PartnerClientAPIException(
                "Couldn't get resource '{}', status code: {}".format(
                    url, response.status_code))
        return response.json()

    def get_org_uri_by_name(self, name):
        return ORG_URI_BY_NAME[name]

    def _create_payload(self, service_request_id, diagnosis_result, analysis_results):
        # TODO Need to think about if this needs refactoring later, to more easily support multiple
        #      analysis types. This is going to be rather unwieldy to add more as it is implemented
        #      atm.
        observations = self._create_observations(analysis_results)
        diagnosis_result_as_codeable_concept = self._translate_diagnosis_result_to_codeable_concept(
            diagnosis_result)
        return self._create_diagnosis_report_object(service_request_id=service_request_id,
                                                    observations=observations,
                                                    codeable_concept=diagnosis_result_as_codeable_concept)

    def _create_observations(self, analysis_results):
        # TODO Need to decide on format for the analysis results to be gathered in.
        observations = []
        for index, result in enumerate(analysis_results):
            observations.append(
                self._create_observation(index+1, result["value"]))
        return observations

    def _create_observation(self, index, value):
        # TODO Note this this now hard codes the observation type. We will need to
        #      extend this if we implement other types of analysis.
        return {
            "resourceType": "Observation",
            "id": str(index),
            "status": "final",
            "code": {
                "coding": [
                    {"system": "http://uri.ctmr.scilifelab.se/id/CodeSystem/cs-observations",
                     "code": "v1-ct-value-mgi-real-time-fluorescent-RT-PCR-2019-nCoV"}
                ]
            },
            "valueQuantity": {
                "value": value
            }
        }

    def _translate_diagnosis_result_to_codeable_concept(self, diagnosis_result):
        if diagnosis_result not in VALID_COVID_RESPONSES:
            raise AssertionError("Diagnosis result {} not in list of valid resonses: {}.".format(
                diagnosis_result, VALID_COVID_RESPONSES
            ))
        return {
            "coding": [
                {
                    "system": "{}/id/CodeSystem/cs-result-types".format(self._test_partner_code_system_base_url),
                    "code": diagnosis_result
                }
            ]
        }

    def _create_diagnosis_report_object(self, service_request_id, observations, codeable_concept):
        # TODO Do we not need to use the referral code? Is it really just the service_request_id
        #      we need to use? I can't see where it is supposed to go.
        return {
            "resourceType": "DiagnosticReport",
            "contained": observations,
            "basedOn": [
                {
                    "reference": "ServiceRequest/{}".format(service_request_id)
                }
            ],
            "code": codeable_concept,
            "result": map(lambda x: {"reference": "#{}".format(x["id"])}, observations)
        }
