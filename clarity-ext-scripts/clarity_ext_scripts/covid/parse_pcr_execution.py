# -*- coding: utf-8 -*-

import pandas as pd
from datetime import datetime
from clarity_ext.domain.validation import UsageError

CT_HEADER = u"Cт"


class ParsePcrExecution(object):
    def __init__(self, context):
        self.context = context

    def execute(self):
        if not self._has_instrument_udf():
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
        return self.context.current_step.udf_instrument_used

    def _has_instrument_udf(self):
        try:
            _ = self.instrument
        except AttributeError:
            return False

        return True


class Quant7Parser(object):
    def __init__(self, context):
        self.context = context

    def parse(self, file_name):
        file_stream = self.context.local_shared_file(file_name, mode="rb")
        data = pd.read_excel(file_stream, 'Results', index_col=0, skiprows=7, encoding='utf-8')
        for _, output in self.context.all_analytes:
            entry = data.loc[output.well.alpha_num_key]
            target_name = entry["Target Name"]

            if target_name != output.name:
                raise AssertionError("Incorrect name of target '{}' in well '{}' in '{}'. "
                        "Expected {}".format(
                            target_name, output.well.alpha_num_key, file_name, output.name))

            ct = entry[CT_HEADER]

            # add the measurement to the output artifact
            output.udf_map.force("CT", ct)
            self.context.update(output)

            # also add the measurement to the original sample, where it should be understood
            # as the latest measurement

            # ISO format without the microseconds
            now_iso = datetime.now().isoformat().split(".")[0]

            original_sample = output.sample()
            original_sample.udf_map.force("CT latest", ct)
            original_sample.udf_map.force("CT latest date", now_iso)
            # LIMS ID of the source of the CT measurement
            original_sample.udf_map.force("CT source", output.api_resource.uri)
            self.context.update(original_sample)
