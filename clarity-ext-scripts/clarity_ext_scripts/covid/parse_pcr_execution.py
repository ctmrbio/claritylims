# -*- coding: utf-8 -*-

import pandas as pd
import math
from datetime import datetime
from clarity_ext.domain.validation import UsageError


class ParsePcrExecution(object):
    def __init__(self, context):
        self.context = context

    def execute(self):
        if self.instrument is None:
            raise UsageError("The udf 'Instrument Used' must be filled in before running this script")
        file_handle = "Result file"
        parser = self._instantiate_parser()
        parser.parse(file_handle)

    def _instantiate_parser(self):
        if self.instrument == 'qPCR ABI 7500':
            raise UsageError('Parsing qPCR ABI 7500 is not implemented')
        elif self.instrument == 'Quant Studio 7':
            parser = Quant7Parser(self.context)
        else:
            raise UsageError("The instrument in 'Instrument Used' is not recognized: {}"
                             .format(self.instrument))
        return parser

    @property
    def instrument(self):
        return self.context.current_step.instrument


class Quant7Parser(object):
    def __init__(self, context):
        self.context = context

    def _determine_start_row(self, panda_contents):
        header_row_entry = panda_contents[
            (panda_contents[0] == 'Well') & (panda_contents[1] == 'Well Position')
            ]
        header_row_index = header_row_entry.index.values[0]
        header = [header_row_entry[index].values[0] for index in header_row_entry]
        return header_row_index, header

    def _build_matrix(self, data, header):
        """
        This returns the data in pcr output file represented as a dict of dict
        the outer key is "<Sample Name><Reporter>"
        the inner key is the column name as in the file
        example: myval = matrix['sample1FAM']['Sample Name']
        myval --> 'sample1'
        """
        rows = [index for index in data.values]
        matrix = dict()
        for numpy_row in rows:
            row = [d for d in numpy_row]
            row_as_dict = dict(zip(header, row))
            key = self._key(row_as_dict['Sample Name'], row_as_dict['Reporter'])
            matrix[key] = row_as_dict
        return matrix

    def _key(self, sample_name, reporter):
        return '{}{}'.format(sample_name, reporter)

    def _fetch_contents(self, file_handle):
        file_stream1 = self.context.local_shared_file(file_handle, mode="rb")
        panda_contents = pd.read_excel(
            file_stream1, 'Results', index_col=None, header=None, encoding='utf-8')
        header_row_index, header = self._determine_start_row(panda_contents)
        file_stream2 = self.context.local_shared_file(file_handle, mode="rb")
        panda_matrix = pd.read_excel(
            file_stream2, 'Results', index_col=None, skiprows=header_row_index,
            encoding='utf-8')
        return self._build_matrix(panda_matrix, header)

    def parse(self, file_handle):
        matrix = self._fetch_contents(file_handle)
        for _, output in self.context.all_analytes:
            try:
                _ = matrix[self._key(output.name, 'FAM')]
            except KeyError:
                raise UsageError("Sample name could not be found in pcr output file: {}".format(output.name))
            fam_row = matrix[self._key(output.name, 'FAM')]
            vic_row = matrix[self._key(output.name, 'VIC')]
            fam_ct = self._parse_ct(fam_row["CT"])
            vic_ct = self._parse_ct(vic_row["CT"])

            # add the measurement to the output artifact
            output.udf_map.force("FAM-CT", fam_ct)
            output.udf_map.force("VIC-CT", vic_ct)
            self.context.update(output)

            # also add the measurement to the original sample, where it should be understood
            # as the latest measurement

            # ISO format without the microseconds
            now_iso = datetime.now().isoformat().split(".")[0]

            original_sample = output.sample()
            original_sample.udf_map.force("FAM-CT latest", fam_ct)
            original_sample.udf_map.force("VIC-CT latest", vic_ct)
            original_sample.udf_map.force("CT latest date", now_iso)
            # LIMS ID of the source of the CT measurement
            original_sample.udf_map.force("CT source", output.api_resource.uri)
            self.context.update(original_sample)

    def _parse_ct(self, ct):
        # CT values with no signal is shown as an empty cell in the output file
        # which in turn is interpreted as NaN by pandas.
        if (isinstance(ct, basestring) and ct.lower() == 'undetermined') or math.isnan(ct):
            ct = 0
        return ct
