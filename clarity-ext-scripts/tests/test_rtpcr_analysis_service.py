
from clarity_ext_scripts.covid.rtpcr_analysis_service import *
from clarity_ext_scripts.covid.partner_api_client import COVID_RESPONSE_FAILED, \
    COVID_RESPONSE_NEGATIVE, COVID_RESPONSE_POSITIVE
from mock import patch
import pytest


class TestRTPCRAnalysisService(object):
    def test_can_analyze_samples(self):

        pos_controls = [{"id": "pos-1", "FAM-CT": 25, "HEX-CT": 20},
                        {"id": "pos-2", "FAM-CT": 20, "HEX-CT": 18}]

        neg_controls = [{"id": "neg-1", "FAM-CT": 0, "HEX-CT": 20},
                        {"id": "neg-2", "FAM-CT": 0, "HEX-CT": 18}]

        samples = [{"id": "cov-1-pos", "FAM-CT": 20, "HEX-CT": 20},
                   {"id": "cov-2-neg", "FAM-CT": 0, "HEX-CT": 18},
                   {"id": "cov-3-fail", "FAM-CT": 40, "HEX-CT": 18}]

        service = RTPCRAnalysisService(
            covid_reporter_key="FAM", internal_control_reporter_key="HEX")

        result = service.analyze_samples(positive_controls=pos_controls,
                                         negative_controls=neg_controls,
                                         samples=samples)

        expected = [
            {"id": "pos-1", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "pos-2", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "neg-1", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "neg-2", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "cov-1-pos", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "cov-2-neg", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "cov-3-fail", "diagnosis_result": FAILED_BY_TO_HIGH_COVID_VALUE}]

        assert expected == list(result)
