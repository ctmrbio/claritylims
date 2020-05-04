import re
from clarity_ext.service.file_service import Csv
from clarity_ext.domain.validation import UsageError
from clarity_ext.utils import single

BIOBANK_FILE_HEADER = ['well', 'biobank_barcode', 'something_else', 'plate_barcode']


class FetchBiobankBarcodes(object):
    """
    This is intended to be part of create samples script. By injecting context,
    it might be tested in isolation by creating a dummy script.
    """

    def __init__(self, context):
        self.context = context
        self.barcode_by_sample_code = None

    def execute(self):
        """
        Just for testing, validate() and map_barcodes() are called separately from
        different scripts
        """
        self.validate()
        self.barcode_by_sample_code =\
            self.biobank_barcode_by_sample_referal_code()
        self._print(self.barcode_by_sample_code)

    def validate(self):
        try:
            file_stream = self.context.local_shared_file('Raw biobank list')
        except IOError:
            raise UsageError("Please upload the file to 'Raw barcode list' before proceeding!")

        biobank_matrix = self._build_biobank_matrix(file_stream)
        plate_barcodes = {
            biobank_matrix[key]['plate_barcode'] for key in biobank_matrix
        }
        if len(plate_barcodes) > 1:
            raise UsageError("There are more than one destination plates the file in 'Raw barcode list'!")

        # Validate that sample list file has plate barcode as name
        filenames = self.context.file_service.list_filenames('Raw sample list')
        base_names = [n.split('.')[0] for n in filenames]
        plate_barcode = single(list(plate_barcodes))
        if plate_barcode not in base_names:
            raise UsageError(
                "The 'Raw sample list' name is not matching with the plate "
                "barcode in 'Raw biobank list', {}".format(plate_barcode))

        # Validate that all wells in biobank file are matched in sample list file
        file_stream2 = self.context.local_shared_file('Raw sample list')
        sample_matrix = self._build_sample_matrix(file_stream2, plate_barcode)
        for key in biobank_matrix:
            try:
                if biobank_matrix[key]['biobank_barcode'] != 'NO TUBE':
                    _ = sample_matrix[key]['Sample Id']
            except KeyError:
                raise UsageError(
                    "The well references are not matching between the "
                    "files in 'Raw biobank list' and 'Raw sample list, "
                    "well '{}' has no match in the 'Raw sample list'"
                    .format(biobank_matrix[key]['well'])
                )

        # Validate that 'NO TUBE' entries in biobank file is empty in sample list
        # Perhaps this is a little too aggressive validation?
        sample_matrix_keys = [k for k in sample_matrix]
        for key in biobank_matrix:
            if biobank_matrix[key]['biobank_barcode'] == 'NO TUBE' \
                    and key in sample_matrix_keys \
                    and sample_matrix[key]['Sample Id']:
                biobank_well = biobank_matrix[key]['well']
                sample_list_well = sample_matrix[key]['Position']
                raise UsageError(
                    "There is an empty entry in the biobank barcode file "
                    "that is not empty in the sample list file, "
                    "biobank well: {}, sample list well: {}"
                    .format(biobank_well, sample_list_well))

    def biobank_barcode_by_sample_referal_code(self):
        file_stream = self.context.local_shared_file('Raw biobank list')
        biobank_matrix = self._build_biobank_matrix(file_stream)
        plate_barcode = self._plate_barcode_from(biobank_matrix)
        file_stream2 = self.context.local_shared_file('Raw sample list')
        sample_matrix = self._build_sample_matrix(file_stream2, plate_barcode)
        barcode_map = dict()
        for key in biobank_matrix:
            if biobank_matrix[key]['biobank_barcode'] == 'NO TUBE':
                continue
            biobank_barcode = biobank_matrix[key]['biobank_barcode']
            sample_referal_code = sample_matrix[key]['Sample Id']
            barcode_map[sample_referal_code] = biobank_barcode

        return barcode_map

    def _build_sample_matrix(self, file_stream, plate_barcode):
        csv = Csv(file_stream)
        matrix = dict()
        pattern = re.compile(r"(?P<row>[A-Z])(?P<col>[0-9]+)")
        for line in csv:
            trimmed_row = map(str.strip, line.values)
            row_as_dict = dict(zip(csv.header, trimmed_row))
            well_robot_format = line['Position']
            m = pattern.match(well_robot_format)
            if m is None:
                continue
            tokens = m.groupdict()
            well_default_format = '{}{}'.format(tokens['row'], int(tokens['col']))
            matrix[self._biobank_key(well_default_format, plate_barcode)] = row_as_dict
        return matrix

    def _print(self, var):
        from pprint import pprint
        pprint(var)

    def _build_biobank_matrix(self, file_stream):
        contents = file_stream.read()
        rows = contents.split('\n')
        matrix = dict()
        for row in rows:
            split_row = row.split(",")
            if len(split_row) != len(BIOBANK_FILE_HEADER):
                continue
            trimmed_row = map(str.strip, split_row)
            row_as_dict = dict(zip(BIOBANK_FILE_HEADER, trimmed_row))
            well = row_as_dict['well']
            plate_barcode = row_as_dict['plate_barcode']
            matrix[self._biobank_key(well, plate_barcode)] = row_as_dict
        return matrix

    def _plate_barcode_from(self, biobank_matrix):
        any_key = [k for k in biobank_matrix][0]
        return biobank_matrix[any_key]['plate_barcode']

    def _biobank_key(self, well, plate_barcode):
        return '{}_{}'.format(well, plate_barcode)
