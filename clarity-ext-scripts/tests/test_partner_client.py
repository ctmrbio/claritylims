
from clarity_ext_scripts.covid.partner_api_client import *
from mock import patch
import pytest


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
            self.headers = {"fake": "value"}

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

    def test_can_verify_referral_coded(self):
        valid = ["8125520216",
                 "7362148855",
                 "1282544442"]
        for v in valid:
            assert verify_test_partner_referral_code(v)

        invalid = ["8125520215",
                   "7362148853",
                   "1282544449"]

        for i in invalid:
            assert not verify_test_partner_referral_code(i)

    def test_can_activate_integration_test_mode(self):
        sample = PartnerAPISampleInformation(referral_code="1234567897", lab_referral="internal-123",
                                             arrival_date="20200302", result_date="20200303",
                                             comment="What an awesome sample.", cov19_result="negative")

        config = {"test_partner_url": "https://example.com",
                  "test_partner_user": "api-1",
                  "test_partner_password": "1337",
                  "integration_test_mode": True,
                  "integration_test_should_fail": 2}

        client = PartnerAPIClient(**config)

        # Fail two times, and then work on the third try.
        with pytest.raises(FailedInContactingTestPartner):
            client.send_single_sample_result(sample)

        with pytest.raises(FailedInContactingTestPartner):
            client.send_single_sample_result(sample)

        res = client.send_single_sample_result(sample)
        assert res


class TestPartnerAPIV7Client(object):

    class MockValidSearchResponse(object):
        def __init__(self):
            self.status_code = 200
            self.headers = {"fake": "value"}

        def json(self):
            return {
                "resourceType": "Bundle",
                "id": "bundle-search-result",
                "type": "searchset",
                "total": 1,
                "entry": [
                    {
                        "resourceType": "ServiceRequest",
                        "id": "1",
                        "identifiers": [
                            {
                                "system":
                                "http://example.com/id/Identifier/i-external-lab-id/region-stockholm-karolinska",
                                "value": "ABC123"
                            },
                            {
                                "assigner": {
                                    "display": "Direkttest unique referral code"
                                },
                                "system": "http://example.com/id/Identifier/i-referral-code",
                                "value": "1234567897"
                            }
                        ],
                        "status": "active",
                        "intent": "original-order",
                        "subject": {
                            "reference": "Patient/4000"
                        },
                        "requester": {
                            "reference": "Organization/123"
                        },
                        "code": {
                            "coding": [
                                {
                                    "system": "http://example.com/id/CodeSystem/cs-analysis/ctmr",
                                    "code": "stdqpcr-covid19"
                                }
                            ],
                            "text": "Standard qPCR"
                        }
                    }],
                "search": {
                    "mode": "match"
                }
            }

    class MockNoSearchResponse(object):
        def __init__(self):
            self.status_code = 200
            self.headers = {"fake": "value"}

        def json(self):
            return {
                "resourceType": "Bundle",
                "id": "bundle-search-warning",
                "type": "searchset",
                "total": 0,
                "entry": [
                    {
                        "resource": {
                            "resourceType": "OperationOutcome",
                            "id": "warning",
                            "issue": [
                                {
                                    "severity": "warning",
                                    "code": "not-found",
                                    "details": {
                                        "text": "No mathing ServiceRequest found"
                                    }
                                }
                            ]
                        },
                        "search": {
                            "mode": "outcome"
                        }
                    }
                ]
            }

    class MockOkPostResponse(object):
        def __init__(self):
            self.status_code = 201
            self.headers = {"fake": "value"}

    class MockFailedPostResponse(object):
        def __init__(self):
            self.status_code = 400
            self.headers = {"fake": "value"}

        def json(self):
            return {"reason": "YOU did something bad!"}

    config = {"test_partner_base_url": "https://example.com",
              "test_partner_code_system_base_url": "http://uri.example.com",
              "test_partner_user": "api-1",
              "test_partner_password": "1337"}

    client = PartnerAPIV7Client(**config)

    def test_can_get_search_result(self):
        mock_search_response = self.MockValidSearchResponse()

        with patch('requests.get', return_value=mock_search_response) as mock_search_response_ctl:
            response = self.client.search_for_service_request(
                "http://example.com/id/Identifier/i-external-lab-id/region-stockholm-karolinska", "ABC123")
            assert response == mock_search_response.json()["entry"][0]

    def test_raises_when_no_search_result_found(self):
        mock_search_response = self.MockNoSearchResponse()

        with patch('requests.get', return_value=mock_search_response) as mock_search_response_ctl:
            with pytest.raises(OrganizationReferralCodeNotFound):
                response = self.client.search_for_service_request(
                    "http://example.com/id/Identifier/i-external-lab-id/region-stockholm-karolinska", "ABC123")

    def test_can_create_positive_diagnosis_payload(self):
        # TODO is the contained observations below missing the "resourceType": "Observation" field?
        expected_payload = {
            "resourceType": "DiagnosticReport",
            "contained": [
                {
                    "resourceType": "Observation",
                    "id": "1",
                    "status": "final",
                    "code": {
                        "coding": [
                            {"system": "http://uri.ctmr.scilifelab.se/id/CodeSystem/cs-observations",
                             "code": "v1-ct-value-mgi-real-time-fluorescent-RT-PCR-2019-nCoV"}
                        ]
                    },
                    "valueQuantity": {
                        "value": 25
                    }
                },
            ],
            "basedOn": [
                {
                    "reference": "ServiceRequest/1000"
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://uri.example.com/id/CodeSystem/cs-result-types",
                        "code": "positive"
                    }
                ]
            },
            "result": [
                {
                    "reference": "#1"
                },
            ]
        }
        result = self.client._create_payload(service_request_id="1000",
                                             diagnosis_result="positive",
                                             analysis_results=[{"value": 25}])
        assert result == expected_payload

    def test_can_create_negative_diagnosis_payload(self):
        pass

    def test_can_create_failed_diagnosis_payload(self):
        pass

    def test_can_post_diagnosis_result(self):
        mock_ok_response = self.MockOkPostResponse()

        with patch('requests.post', return_value=mock_ok_response) as mock_post_response_ctl:
            self.client.post_diagnosis_report(service_request_id="1000",
                                              diagnosis_result="positive",
                                              analysis_results=[{"value": 25}])
            mock_post_response_ctl.assert_called_once()

    def test_failed_post_diagnosis_result_raises(self):
        mock_failed_response = self.MockFailedPostResponse()

        # TODO Note that the analysis results may not look like this at all...
        with patch('requests.post', return_value=mock_failed_response) as mock_post_response_ctl:
            with pytest.raises(FailedInContactingTestPartner):
                self.client.post_diagnosis_report(service_request_id="1000",
                                                  diagnosis_result="positive",
                                                  analysis_results=[{"value": 30}])
