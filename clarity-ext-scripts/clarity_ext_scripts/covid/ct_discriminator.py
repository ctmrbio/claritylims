from clarity_ext.domain.validation import UsageError


VALID_ASSAYS = ['Assay 1']

BOUNDARY_DICT = {'Assay 1': (10, 50)}


class CtDiscriminator(object):
    """
    A service to analyze if a sample is positive for Covid19
    Given:
    CT value of sample
    Discriminator for assay (lower bound, upper bound)
    This service does not update any artifact from context, it only reads from it
    """
    def __init__(self, context):
        self.context = context
        self.initial_validation()

    def initial_validation(self):
        if not self._has_assay_udf():
            raise UsageError("The udf 'Assay' must be filled in before running this script")
        if self.assay not in VALID_ASSAYS:
            raise UsageError("The current assay value is not recognized: {}"
                             .format(self.assay))

    @property
    def assay(self):
        return self.context.current_step.udf_assay

    def _has_assay_udf(self):
        try:
            _ = self.assay
        except AttributeError:
            return False

        return True

    def _get_discriminator_values(self):
        """
        Returns: lower bound, upper bound
        ct <= lower bound: counted as a positive value
        ct >=upper bound: is counted as a negative value
        lower bound < ct < upper bound: undefined
        """
        return BOUNDARY_DICT[self.assay]

    def validate_control_value(self, control_type, ct_value):
        lower_bound, upper_bound = self._get_discriminator_values()
        if control_type.lower() == 'rtpcr_pos' and ct_value > lower_bound:
            return False
        if control_type.lower() == 'rtpcr_neg' and ct_value < upper_bound:
            return False
        return True

    def analyze(self, ct_value):
        """
        Returns: String with value of either 'positive', 'negative', 'failed'
        """
        lower_bound, upper_bound = self._get_discriminator_values()
        if ct_value <= lower_bound:
            return 'positive'
        elif ct_value >= upper_bound:
            return 'negative'
        return 'failed'
