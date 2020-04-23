# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
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

    def _determine_start_row(self, file_handle):
        file_stream = self.context.local_shared_file(file_handle, mode="rb")
        data = pd.read_excel(file_stream, 'Results', index_col=None, header=None, encoding='utf-8')
        header_row_entry = data[(data[0] == 'Well') & (data[1] == 'Well Position')].index
        header_row_index = header_row_entry.values[0]
        return header_row_index

    def parse(self, file_handle):
        header_row_index = self._determine_start_row(file_handle)
        file_stream = self.context.local_shared_file(file_handle, mode="rb")
        data = pd.read_excel(file_stream, 'Results', index_col=None,
                             skiprows=header_row_index, encoding='utf-8')
        for _, output in self.context.all_analytes:
            try:
                _ = data.loc[(data['Sample Name'] == output.name)]
            except KeyError:
                raise UsageError("Sample name could not be found in pcr output file: {}".format(output.name))
            fam_row = data.loc[(data['Sample Name'] == output.name) & (data['Reporter'] == 'FAM')]
            vic_row = data.loc[(data['Sample Name'] == output.name) & (data['Reporter'] == 'VIC')]
            target_name = fam_row["Sample Name"].values[0]
            if target_name != output.name:
                raise AssertionError("Incorrect name of target '{}' in well '{}' in '{}'. "
                        "Expected {}".format(
                            target_name, output.well.alpha_num_key, file_handle, output.name))

            fam_ct = fam_row["CT"].values[0]
            vic_ct = vic_row["CT"].values[0]
            fam_ct = self._parse_ct(fam_ct)
            vic_ct = self._parse_ct(vic_ct)

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
        if (isinstance(ct, basestring) and ct.lower() == 'undetermined') or np.isnan(ct):
            ct = 0
        return ct
