from clarity_ext.extensions import GeneralExtension


class Extension(GeneralExtension):
    """
    This class is used for setup a test step
    """
    def execute(self):
        i = 0
        values = [100, 100, 15, 15, 60, 60, 60, 50]
        for _, output in self.context.all_analytes:
            original_sample = output.sample()
            if i == 0:
                original_sample.udf_map.force("Control", "Yes")
                original_sample.udf_map.force("Control type", "rtpcr_pos")
            elif i == 1:
                original_sample.udf_map.force("Control", "Yes")
                original_sample.udf_map.force("Control type", "rtpcr_neg")
            else:
                original_sample.udf_map.force("Control", "No")
                original_sample.udf_map.force("Control type", "")
            output.udf_map.force("CT", values[i])
            self.context.update(original_sample)
            self.context.update(output)
            print("updated artifact {}, ct to {}".format(output.name, values[i]))
            i += 1

    def integration_tests(self):
        yield "24-40616"
