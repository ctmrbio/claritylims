import pandas as pd
from clarity_ext.extensions import GeneralExtension

# NOTE: The file actually contains the cyrillic small letter te. To avoid using that for indexing
# we instead use the location of the column (zero indexed, where the Well column is not a part of
# the table)

class Extension(GeneralExtension):
    def execute(self):
        ct_col = 5
        file_name = "Result file"
        f = self.context.local_shared_file(file_name, mode="rb")
        data = pd.read_excel(f, 'Results', index_col=0, skiprows=7, encoding='utf-8')

        for _, output in self.context.all_analytes:
            entry = data.loc[output.well.alpha_num_key]
            target_name = entry["Target Name"]

            if target_name != output.name:
                raise AssertionError("Incorrect name of target '{}' in well '{}' in '{}'. "
                        "Expected {}".format(
                            target_name, output.well.alpha_num_key, file_name, output.name))

            ct = entry[ct_col]
            # TODO: What should we do if its undetermined?
            ct = -1 if ct == "Undetermined" else ct
            output.udf_map.force("CT", ct)
            self.context.update(output)

    def integration_tests(self):
        yield "24-39151"
