import re
import time
from datetime import datetime
from clarity_ext_scripts.covid.partner_api_client import PartnerAPIV7Client


class UniqueBarcodeGenerator(object):
    """
    Generates a unique barcode ID that's guaranteed to be unique if there is only
    one person generating barcodes at a time (they use the current second to mark a unique time),
    while also being short enough to fit within a limited length barcode (currently 14 characters).
    
    Format: <one letter prefix><2 digit type_id (0-99)><8 chars timestamp in hex><3 digits running>
    """

    def __init__(self, prefix):
        """
        :prefix: Any character
        """
        self.prefix = prefix
        self.pattern = re.compile(
            "^" +
            prefix +
            "(?P<type_id>\d{2})" +
            "(?P<timestamp>\w{8})" +
            "(?P<running>\d{3})" +
            "$")

    def parse(self, barcode):
        """
        Returns the tuple (type_id, timestamp, running number) if the barcode was generated
        with this generator and prefix. Otherwise returns None
        """
        m = self.pattern.match(barcode)

        if not m:
            return None

        vals = m.groupdict()
        type_id = int(vals["type_id"])
        timestamp = vals["timestamp"]
        timestamp = int("0x" + timestamp, 16)
        timestamp = datetime.fromtimestamp(timestamp)

        running = int(vals["running"])
        return (type_id, timestamp, running)

    def generate(self, type_id, number_of_barcodes):
        """
        :type_id: ID of the entity being represented. Any integer between 0-99
        :number_of_barcodes: Number of barcodes to generate
        """
        timestamp = int(time.time())
        # hex string on the format 0xd...d (10 chars)
        timestamp_string = hex(timestamp)
        # Get rid of the 0x prefix (8 chars unless we're running this in 2106 or later)
        timestamp_string = timestamp_string[2:]

        self.batch_name = '{}{:02d}{}'.format(
            self.prefix, type_id, timestamp_string)

        batch_name_len = 11
        if len(self.batch_name) != batch_name_len:
            raise AssertionError(
                "Expected batch_name to be of length {}".format(batch_name_len))

        if number_of_barcodes < 1 or number_of_barcodes > 999:
            raise AssertionError(
                "Number of barcodes must be an integer in the range 1-999")

        for ix in range(number_of_barcodes):
            running_number_in_batch = '{0:03d}'.format(ix)
            name = self.batch_name + running_number_in_batch
            yield name


class CtmrCovidSubstanceInfo(object):
    """
    Gives extra info about the substance based on different CTMR business rules, e.g. naming
    of control samples.

    Hides info on for example if the information is on the analyte or the original sample and
    will also work as well with a built in clarity control as a control that's in fact a sample.
    """

    STATUS_DISCARD = "DISCARD"
    STATUS_DISCARDED_AND_REPORTED = "DISCARDED_AND_REPORTED"

    def __init__(self, substance):
        """
        :substance: A sample, analyte or a built-in control
        """
        self.substance = substance

    @staticmethod
    def _deduce_control_type_from_sample(sample):
        from clarity_ext_scripts.covid.controls import Controls
        try:
            control_type_abbrev = sample.udf_control_type
            for key, abbrev in Controls.MAP_FROM_KEY_TO_ABBREVIATION.items():
                if abbrev == control_type_abbrev:
                    return key
            raise AssertionError("udf_control_type on the sample contains undefined value: {}"
                                 .format(control_type_abbrev))
        except AttributeError:
            return None

    @staticmethod
    def _deduce_control_type_from_analyte_name(name):
        """
        If an analyte has the exact name of a control, it must be that control.
        """
        from clarity_ext_scripts.covid.controls import Controls
        if name in Controls.MAP_FROM_READABLE_TO_KEY:
            return Controls.MAP_FROM_READABLE_TO_KEY[name]

    @property
    def control_type(self):
        """
        Returns the Control type from the Controls enum if this is a control. Otherwise returns
        None.
        """
        from clarity_ext.domain import Sample, Analyte

        if isinstance(self.substance, Sample):
            return self._deduce_control_type_from_sample(self.substance)
        elif isinstance(self.substance, Analyte):
            control_type = self._deduce_control_type_from_analyte_name(
                self.substance.name)
            if control_type:
                return control_type
            return self._deduce_control_type_from_sample(self.substance.sample())
        else:
            raise NotImplementedError("Not implemented substance type {}".format(
                type(self.substance)))
