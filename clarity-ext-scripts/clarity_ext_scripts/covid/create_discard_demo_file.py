import datetime
import random
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.controls import Controls, controls_barcode_generator
from clarity_ext.domain.container import Container


class Extension(GeneralExtension):
    """
    Generates demo files for the create sample step
    """

    def generate_raw_sample_list(self, num_samples):
        """
        Generates a sample list with a certain number of samples and all available controls
        """
        def rows():
            timestamp = self.context.start.strftime("%y%m%dT%H%M%S")
            headers = ["reference", "source", "reason"]
            yield headers

            samples = [
                str(random.randint(1000000000, 9999999999))
                for _ in range(num_samples)]

            for ix, sample in enumerate(samples):
                yield [sample, "KNM", "No reason"]

        return "\n".join(",".join(row) for row in rows())

    def execute(self):
        timestamp = self.context.start.strftime("%y%m%dT%H%M%S")
        plate_barcode = 'demo_barcode_' + timestamp

        sample_list_contents = self.generate_raw_sample_list(10)
        fname = "{}.csv".format(plate_barcode)
        upload_tuple = [(fname, sample_list_contents)]
        self.context.file_service.upload_files("Raw sample list", upload_tuple)

    def integration_tests(self):
        yield "24-44668"
