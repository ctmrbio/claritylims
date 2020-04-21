import re
import time
from datetime import datetime


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

        self.batch_name = '{}{:02d}{}'.format(self.prefix, type_id, timestamp_string)

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
