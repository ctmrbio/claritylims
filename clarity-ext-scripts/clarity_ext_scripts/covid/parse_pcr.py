# -*- coding: utf-8 -*-

import pandas as pd
from clarity_ext.extensions import GeneralExtension
from datetime import datetime
from clarity_ext_scripts.covid.rtpcr_analyes_service import RTPCRAnalyseService

CT_HEADER = u"Cт"


class Extension(GeneralExtension):
    def execute(self):
        file_name = "Result file"
        f = self.context.local_shared_file(file_name, mode="rb")
        data = pd.read_excel(f, 'Results', index_col=0, skiprows=7, encoding='utf-8')
        rt_pcr_analyze_service = RTPCRAnalyseService(self.context)

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

        rt_pcr_analyze_service.execute()

    def integration_tests(self):
        yield "24-39151"
