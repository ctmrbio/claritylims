
import logging


# TODO Move these constants into some other file
from clarity_ext_scripts.covid.partner_api_client import VALID_COVID_RESPONSES, \
    COVID_RESPONSE_FAILED, COVID_RESPONSE_NEGATIVE, COVID_RESPONSE_POSITIVE


log = logging.getLogger(__name__)


class AnalysisServiceException(Exception):
    pass


class MultipleAnalysisErrors(AnalysisServiceException):
    pass


class PositiveControlWasNegative(AnalysisServiceException):
    pass


class NegativeControlWasPositive(AnalysisServiceException):
    pass


class RTPCRAnalysisService(object):

    HEX_THRESHOLD = 32
    FAM_THRESHOLD = 38

    def __init__(self):
        pass

# Understanding of the analysis criterias
# FAM = COVID, HEX = Human internal control
# Positive if CT(FAM) = <=38
# Failed  if CT(FAM)= >38
# Negative if CT(FAM) = 0 and CT(HEX) = <=32
# Retest if CT(FAM) = 0 and CT(HEX) = >32

# TODO Should we issue a re-test status here
# TODO Later we might have to account for giving two trails over 38 as positive.

    def _analyze_sample(self, sample):
        fam_ct = sample["FAM-CT"]
        hex_ct = sample["HEX-CT"]
        if fam_ct > self.FAM_THRESHOLD:
            return COVID_RESPONSE_FAILED
        elif fam_ct == 0 and hex_ct <= self.HEX_THRESHOLD:
            return COVID_RESPONSE_NEGATIVE
        elif fam_ct == 0 and hex_ct > self.HEX_THRESHOLD:
            # TODO Should retest and failed be the same thing or not.
            return COVID_RESPONSE_FAILED
        elif fam_ct <= self.FAM_THRESHOLD:
            return COVID_RESPONSE_POSITIVE
        else:
            # TODO Don't know if it is actually a good idea to raise here or not...
            raise NotImplementedError(
                "Got CT-value for FAM: {} and CT-value for HEX: {}.".format(fam_ct, hex_ct))

    def _analyze_controls(self, positive_controls, negative_controls):
        errors = []
        for pos_control in positive_controls:
            if self._analyze_sample(pos_control) == COVID_RESPONSE_NEGATIVE:
                errors += PositiveControlWasNegative(
                    "Positive control sample: {} was negative for covid-19".format(pos_control["id"]))

        for neg_control in negative_controls:
            if self._analyze_sample(neg_control) == COVID_RESPONSE_POSITIVE:
                errors += NegativeControlWasPositive(
                    "Negative control sample: {} was positive for covid-19".format(
                        neg_control["id"]))

        if errors:
            for e in errors:
                log.error(e.message)
            raise MultipleAnalysisErrors(errors)

    def analyze_samples(self, positive_controls, negative_controls, samples):
        """
        This assumes all controls and samples are from the same plate.
        All samples, and controls should be submitted as dict-like objects on the format:
         {"id": "<sample id>", "FAM-CT": <value as numeric>, "HEX-Ct": <value as numric>}

        The method will return a generator of objects on the format:
         {"id": "<same as sample id above>",
             "diagnosis_result": "<CONST COVID RESPONSE>"}
        """

        # TODO Should we validate that there are controls on the plate?

        # If controls fail, fail all samples on plate.
        try:
            self._analyze_controls(positive_controls, negative_controls)
        except MultipleAnalysisErrors:
            for sample in samples:
                yield {"id": sample["id"], "diagnosis_result": COVID_RESPONSE_FAILED}
            # No need to continue looking at the samples, as we fail them all here.
            return

        # Check samples
        for sample in samples:
            result = self._analyze_sample(sample)
            yield {"id": sample["id"], "diagnosis_result": result}
