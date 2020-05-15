import random
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.create_samples.common import ValidatedSampleListFile


class Extension(GeneralExtension):
    """
    Generates demo files for the create sample step
    """

    def generate_raw_sample_list(self, num_ok=0, num_unregistered=0, num_error=0):
        """
        Generates a sample list with a certain number of samples and all available controls
        """

        def rows():
            def generate(num, reason):
                return [(str(random.randint(1000000000, 9999999999)), reason)
                        for _ in range(num)]

            headers = ["reference", "source", "reason"]
            yield headers

            ok = generate(num_ok, ValidatedSampleListFile.STATUS_OK)
            error = generate(num_error, ValidatedSampleListFile.STATUS_ERROR)
            unregistered = generate(
                num_unregistered, ValidatedSampleListFile.STATUS_UNREGISTERED)
            samples = ok + error + unregistered

            for ix, sample_info in enumerate(samples):
                sample_id, reason = sample_info
                yield [sample_id, "KNM", reason]

        return "\n".join(",".join(row) for row in rows())

    def execute(self):
        timestamp = self.context.start.strftime("%y%m%dT%H%M%S")
        plate_barcode = 'demo_barcode_' + timestamp

        sample_list_contents = self.generate_raw_sample_list(
            num_ok=8, num_unregistered=2)
        fname = "{}.csv".format(plate_barcode)
        upload_tuple = [(fname, sample_list_contents)]
        self.context.file_service.upload_files("Raw sample list", upload_tuple)

    def integration_tests(self):
        yield "24-46737"
