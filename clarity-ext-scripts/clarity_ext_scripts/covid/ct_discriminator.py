from clarity_ext.domain.validation import UsageError


class CtDiscriminatorForPlate(object):
    """
    A service to analyze if a sample is positive for Covid19
    Given:
    CT value of sample
    Discriminator for assay (lower bound, upper bound)
    It's expected to be 2 controls on a plate, and these are to be
    validated before ordinary samples are analyzed.
    """
    def __init__(self):
        self.has_valid_pos_control = False
        self.has_valid_neg_control = False

    def validate_control_value(self, control_type, ct_value, lower_bound, upper_bound):
        if control_type.lower() == 'rtpcr_pos' and ct_value <= lower_bound:
            self.has_valid_pos_control = True
        if control_type.lower() == 'rtpcr_neg' and ct_value >= upper_bound:
            self.has_valid_neg_control = True

    def is_valid(self):
        return self.has_valid_neg_control and self.has_valid_pos_control

    def analyze(self, ct_value, lower_bound, upper_bound):
        """
        Returns: String with value of either 'positive', 'negative', 'failed'
        """
        if not self.has_valid_pos_control or not self.has_valid_neg_control:
            raise UsageError("There are no valid control samples")
        if ct_value <= lower_bound:
            return 'positive'
        elif ct_value >= upper_bound:
            return 'negative'
        return 'failed'
