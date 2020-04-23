
from clarity_ext_scripts.covid.rtpcr_analysis_service import *
from clarity_ext_scripts.covid.partner_api_client import COVID_RESPONSE_FAILED, \
    COVID_RESPONSE_NEGATIVE, COVID_RESPONSE_POSITIVE
from mock import patch
import pytest


class TestRTPCRAnalysisService(object):
    """
    Test for the analysis service. The scenarios correspond to the scenarios given in the
    drive document used to document test cases.
    """

    service = RTPCRAnalysisService(
        covid_reporter_key="FAM-CT", internal_control_reporter_key="HEX-CT")

    def test_can_analyze_samples_scenario1(self):
        """
        Controls are ok. Fail one sample on FAM value
        """

        pos_controls = [{"id": "pos-1", "FAM-CT": 25, "HEX-CT": 20},
                        {"id": "pos-2", "FAM-CT": 20, "HEX-CT": 18}]

        neg_controls = [{"id": "neg-1", "FAM-CT": 0, "HEX-CT": 20},
                        {"id": "neg-2", "FAM-CT": 0, "HEX-CT": 18}]

        samples = [{"id": "cov-1", "FAM-CT": 20, "HEX-CT": 20},
                   {"id": "cov-2", "FAM-CT": 0, "HEX-CT": 18},
                   {"id": "cov-3", "FAM-CT": 40, "HEX-CT": 18}]

        result = self.service.analyze_samples(positive_controls=pos_controls,
                                              negative_controls=neg_controls,
                                              samples=samples)

        expected = [
            {"id": "pos-1", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "pos-2", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "neg-1", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "neg-2", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "cov-1", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "cov-2", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "cov-3", "diagnosis_result": FAILED_BY_TOO_HIGH_COVID_VALUE}]

        assert expected == list(result)

    def test_can_analyze_samples_scenario2(self):
        """
        Fail on neg control is positive
        """

        pos_controls = [{"id": "pos-1", "FAM-CT": 25, "HEX-CT": 20},
                        {"id": "pos-2", "FAM-CT": 20, "HEX-CT": 18}]

        neg_controls = [{"id": "neg-1", "FAM-CT": 20, "HEX-CT": 20},
                        {"id": "neg-2", "FAM-CT": 0, "HEX-CT": 18}]

        samples = [{"id": "cov-1", "FAM-CT": 20, "HEX-CT": 20},
                   {"id": "cov-2", "FAM-CT": 0, "HEX-CT": 18},
                   {"id": "cov-3", "FAM-CT": 40, "HEX-CT": 18}]

        result = self.service.analyze_samples(positive_controls=pos_controls,
                                              negative_controls=neg_controls,
                                              samples=samples)

        expected = [
            {"id": "pos-1", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "pos-2", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "neg-1", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "neg-2", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "cov-1",
                "diagnosis_result": FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL},
            {"id": "cov-2",
                "diagnosis_result": FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL},
            {"id": "cov-3", "diagnosis_result": FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL}]

        assert expected == list(result)

    def test_can_analyze_samples_scenario3(self):
        """
        Controls are ok. Fail one sample on high HEX value
        """

        pos_controls = [{"id": "pos-1", "FAM-CT": 25, "HEX-CT": 20},
                        {"id": "pos-2", "FAM-CT": 20, "HEX-CT": 18}]

        neg_controls = [{"id": "neg-1", "FAM-CT": 0, "HEX-CT": 20},
                        {"id": "neg-2", "FAM-CT": 0, "HEX-CT": 18}]

        samples = [{"id": "cov-1", "FAM-CT": 20, "HEX-CT": 20},
                   {"id": "cov-2", "FAM-CT": 0, "HEX-CT": 18},
                   {"id": "cov-3", "FAM-CT": 0, "HEX-CT": 33}]

        result = self.service.analyze_samples(positive_controls=pos_controls,
                                              negative_controls=neg_controls,
                                              samples=samples)

        expected = [
            {"id": "pos-1", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "pos-2", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "neg-1", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "neg-2", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "cov-1",
                "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "cov-2",
                "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "cov-3", "diagnosis_result": FAILED_BY_INTERNAL_CONTROL}]

        assert expected == list(result)

    def test_can_analyze_samples_scenario4(self):
        """
        Samples fail because positive control has negative result
        """

        pos_controls = [{"id": "pos-1", "FAM-CT": 0, "HEX-CT": 20},
                        {"id": "pos-2", "FAM-CT": 0, "HEX-CT": 18}]

        neg_controls = [{"id": "neg-1", "FAM-CT": 0, "HEX-CT": 20},
                        {"id": "neg-2", "FAM-CT": 0, "HEX-CT": 18}]

        samples = [{"id": "cov-1", "FAM-CT": 20, "HEX-CT": 20},
                   {"id": "cov-2", "FAM-CT": 0, "HEX-CT": 18},
                   {"id": "cov-3", "FAM-CT": 0, "HEX-CT": 33}]

        result = self.service.analyze_samples(positive_controls=pos_controls,
                                              negative_controls=neg_controls,
                                              samples=samples)

        expected = [
            {"id": "pos-1", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "pos-2", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "neg-1", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "neg-2", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "cov-1",
                "diagnosis_result": FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL},
            {"id": "cov-2",
                "diagnosis_result": FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL},
            {"id": "cov-3", "diagnosis_result": FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL}]

        assert expected == list(result)

    def test_can_analyze_samples_scenario5(self):
        """
        Samples are failed because positive control is failed.
        """

        pos_controls = [{"id": "pos-1", "FAM-CT": 25, "HEX-CT": 20},
                        {"id": "pos-2", "FAM-CT": 0, "HEX-CT": 33}]

        neg_controls = [{"id": "neg-1", "FAM-CT": 0, "HEX-CT": 20},
                        {"id": "neg-2", "FAM-CT": 0, "HEX-CT": 18}]

        samples = [{"id": "cov-1", "FAM-CT": 20, "HEX-CT": 20},
                   {"id": "cov-2", "FAM-CT": 0, "HEX-CT": 18},
                   {"id": "cov-3", "FAM-CT": 0, "HEX-CT": 33}]

        result = self.service.analyze_samples(positive_controls=pos_controls,
                                              negative_controls=neg_controls,
                                              samples=samples)

        expected = [
            {"id": "pos-1", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "pos-2", "diagnosis_result": FAILED_BY_INTERNAL_CONTROL},
            {"id": "neg-1", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "neg-2", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "cov-1",
                "diagnosis_result": FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL},
            {"id": "cov-2",
                "diagnosis_result": FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL},
            {"id": "cov-3", "diagnosis_result": FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL}]

        assert expected == list(result)

    def test_can_analyze_samples_scenario6(self):
        """
        Samples are failed because negative control failed.
        """

        pos_controls = [{"id": "pos-1", "FAM-CT": 25, "HEX-CT": 20},
                        {"id": "pos-2", "FAM-CT": 20, "HEX-CT": 18}]

        neg_controls = [{"id": "neg-1", "FAM-CT": 0, "HEX-CT": 20},
                        {"id": "neg-2", "FAM-CT": 40, "HEX-CT": 18}]

        samples = [{"id": "cov-1", "FAM-CT": 20, "HEX-CT": 20},
                   {"id": "cov-2", "FAM-CT": 0, "HEX-CT": 18},
                   {"id": "cov-3", "FAM-CT": 0, "HEX-CT": 33}]

        result = self.service.analyze_samples(positive_controls=pos_controls,
                                              negative_controls=neg_controls,
                                              samples=samples)

        expected = [
            {"id": "pos-1", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "pos-2", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "neg-1", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "neg-2", "diagnosis_result": FAILED_BY_TOO_HIGH_COVID_VALUE},
            {"id": "cov-1",
                "diagnosis_result": FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL},
            {"id": "cov-2",
                "diagnosis_result": FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL},
            {"id": "cov-3", "diagnosis_result": FAILED_ENTIRE_PLATE_BY_FAILED_EXTERNAL_CONTROL}]

        assert expected == list(result)

    def test_can_analyze_samples_scenario7(self):
        """
        For no signal on both channels of a negative control, it should be negative
        """

        pos_controls = [{"id": "pos-1", "FAM-CT": 25, "HEX-CT": 20},
                        {"id": "pos-2", "FAM-CT": 20, "HEX-CT": 18}]

        neg_controls = [{"id": "neg-1", "FAM-CT": 0, "HEX-CT": 0},
                        {"id": "neg-2", "FAM-CT": 0, "HEX-CT": 0}]

        samples = [{"id": "cov-1", "FAM-CT": 20, "HEX-CT": 20},
                   {"id": "cov-2", "FAM-CT": 14, "HEX-CT": 18},
                   {"id": "cov-3", "FAM-CT": 40, "HEX-CT": 33}]

        result = self.service.analyze_samples(positive_controls=pos_controls,
                                              negative_controls=neg_controls,
                                              samples=samples)

        expected = [
            {"id": "pos-1", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "pos-2", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "neg-1", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "neg-2", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "cov-1",
                "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "cov-2",
                "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "cov-3", "diagnosis_result": FAILED_BY_TOO_HIGH_COVID_VALUE}]

        assert expected == list(result)

    def test_can_analyze_samples_scenario8(self):
        """
        For no signal on both channels of a sample, it should fail
        """
        pos_controls = [{"id": "pos-1", "FAM-CT": 25, "HEX-CT": 20},
                        {"id": "pos-2", "FAM-CT": 20, "HEX-CT": 18}]

        neg_controls = [{"id": "neg-1", "FAM-CT": 0, "HEX-CT": 0},
                        {"id": "neg-2", "FAM-CT": 0, "HEX-CT": 0}]

        samples = [{"id": "cov-1", "FAM-CT": 0, "HEX-CT": 0},
                   {"id": "cov-2", "FAM-CT": 14, "HEX-CT": 18},
                   {"id": "cov-3", "FAM-CT": 40, "HEX-CT": 33}]

        result = self.service.analyze_samples(positive_controls=pos_controls,
                                              negative_controls=neg_controls,
                                              samples=samples)

        expected = [
            {"id": "pos-1", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "pos-2", "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "neg-1", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "neg-2", "diagnosis_result": COVID_RESPONSE_NEGATIVE},
            {"id": "cov-1",
                "diagnosis_result": FAILED_BY_INTERNAL_CONTROL},
            {"id": "cov-2",
                "diagnosis_result": COVID_RESPONSE_POSITIVE},
            {"id": "cov-3", "diagnosis_result": FAILED_BY_TOO_HIGH_COVID_VALUE}]

        assert expected == list(result)
