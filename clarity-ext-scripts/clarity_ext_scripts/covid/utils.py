import time
from datetime import datetime


class UniqueBarcodeGenerator(object):
    """
    Generates a unique barcode ID that's guaranteed to be unique if there is only
    one person generating barcodes at a time (they use the current second to mark a unique time),
    while also being short enough to fit within a limited length barcode (currently 14 characters).
    
    Format: <one letter prefix><2 digit type_id (0-99)><8 chars timestamp in hex><3 digits running>
    """

    def __init__(self, type_id, prefix):
        """
        :type_id: ID of the entity being represented. Any integer between 0-99
        :prefix: Any character
        """

        timestamp = int(time.time())
        # hex string on the format 0xd...d (10 chars)
        timestamp_string = hex(timestamp)
        # Get rid of the 0x prefix (8 chars unless we're running this in 2106 or later)
        timestamp_string = timestamp_string[2:]

        self.batch_name = '{}{:02d}{}'.format(
            prefix, type_id, timestamp_string)

        batch_name_len = 11
        if len(self.batch_name) != batch_name_len:
            raise AssertionError(
                "Expected batch_name to be of length {}".format(batch_name_len))

    def generate(self, number_of_barcodes):
        if number_of_barcodes < 1 or number_of_barcodes > 999:
            raise AssertionError(
                "Number of barcodes must be an integer in the range 1-999")

        for ix in range(number_of_barcodes):
            running_number_in_batch = '{0:03d}'.format(ix)
            name = self.batch_name + running_number_in_batch
            yield name
