import datetime
import random
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.controls import Controls, controls_barcode_generator
from clarity_ext.domain.container import Container
from clarity_ext_scripts.covid.create_samples.common import ValidatedSampleListFile
from clarity_ext_scripts.covid.validate_sample_creation_list import RawSampleListFile


class Extension(GeneralExtension):
    """
    Generates demo files for the create sample step
    """

    def generate_raw_sample_list(self, num_ok=0, num_error=0, num_unregistered=0):
        """
        Generates a sample list with a certain number of samples and all available controls

        The samples will be generated with different status based on their name. This will only
        happen if validating with the "Internal testing" organization.

        :num_ok: Number of samples with the status "ok" to create
        :num_error: Number of samples with the status "error" to create
        :num_unregistered: Number of samples with the status "unregistered" to create
        """
        def rows():
            timestamp = self.context.start.strftime("%y%m%dT%H%M%S")
            yield RawSampleListFile.HEADERS

            rows = 8  # Rows in a 96 well plate

            def generate(num, name):
                return [(str(random.randint(1000000000, 9999999999)), name)
                        for _ in range(num)]

            ok = generate(num_ok, ValidatedSampleListFile.STATUS_OK)
            error = generate(num_error, ValidatedSampleListFile.STATUS_ERROR)
            unregistered = generate(
                num_unregistered, ValidatedSampleListFile.STATUS_UNREGISTERED)
            samples_and_controls = ok + error + unregistered

            # Add all controls:
            for c in Controls.ALL:
                generated = next(controls_barcode_generator.generate(c, 1))
                abbreviation = Controls.MAP_FROM_KEY_TO_ABBREVIATION[c]
                samples_and_controls.append((generated, abbreviation))

            for ix, sample_or_control_info in enumerate(samples_and_controls):
                sample_or_control_id, sample_or_control_name = sample_or_control_info
                rack_id = "LVL" + timestamp
                row = chr(ix % rows + ord("A"))
                col = ix / rows + 1
                cavity_id = "{}_{}{:03d}".format(rack_id, row, col)
                pos = "{}{:02d}".format(row, col)
                yield ([rack_id, cavity_id, pos, sample_or_control_id] +
                       [""] * 3 +
                       [sample_or_control_name] +
                       [""] * 8)

            # Add postfix rows that should be ignored later
            extra_cols = [""] * (len(RawSampleListFile.HEADERS) - 1)
            yield ["Sample Tracking Report Name : Plate Report Extended"] + extra_cols
            yield ["Last action tracked : 4/25/2020 2:13:13 PM"] + extra_cols
            yield ["Created by Operator at 4/25/2020 2:13:20 PM"] + extra_cols
            yield [":000000000000"] + extra_cols

        return "\n".join(",".join(row) for row in rows())

    def generate_raw_biobank_list(self, plate_barcode):
        container = Container(
            container_type=Container.CONTAINER_TYPE_96_WELLS_PLATE)

        def rows():
            # Always fill up one entire plate
            for well in container:
                barcode = 'LV{}'.format(random.randint(1000000000, 9999999999))
                yield [well.alpha_num_key, barcode, plate_barcode]

        return "\n".join(", ".join(row) for row in rows())

    def execute(self):
        plate_barcode = 'demo_barcode_123'
        biobank_contents = self.generate_raw_biobank_list(plate_barcode)
        fname = 'demo_biobank_barcodes_for_plate_{}.csv'.format(plate_barcode)
        upload_tuple = [(fname, biobank_contents)]
        self.context.file_service.upload_files(
            "Raw biobank list", upload_tuple)

        sample_list_contents = self.generate_raw_sample_list(
            num_ok=8, num_unregistered=2)
        fname = "{}.csv".format(plate_barcode)
        upload_tuple = [(fname, sample_list_contents)]
        self.context.file_service.upload_files("Raw sample list", upload_tuple)

    def integration_tests(self):
        yield "24-46735"
