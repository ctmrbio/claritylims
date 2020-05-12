import time
import datetime
from clarity_ext_scripts.covid.controls import Controls, controls_barcode_generator
from clarity_ext.extensions import GeneralExtension


class Extension(GeneralExtension):
    """
    Called from the Create controls step:

    * Fills in step UDF "Number of controls" (1-999)
    * Selects ControlType from a dropdown
    * User presses "Create controls"
    * Script generates a list in the csv file "Generated controls". It has a list of barcodes
      which can be interpreted back with UniqueBarcodeGenerator

    Note that this doesn't actually create any controls in Clarity, only names that the
    extension `import_samples` recognizes as such, it will do a similar mapping back to known
    control types.
    """

    def execute(self):
        control_type_name = self.context.current_step.udf_control_type
        control_key = Controls.MAP_FROM_READABLE_TO_KEY[control_type_name]
        control_abbrev = Controls.MAP_FROM_KEY_TO_ABBREVIATION[control_key]
        number_of_controls = self.context.current_step.udf_number_of_controls
        if number_of_controls < 1 or number_of_controls > 999:
            self.usage_error(
                "Number of controls must be an integer in the range 1-999")

        content = ["barcode,name"]
        for barcode in controls_barcode_generator.generate(control_key, number_of_controls):
            content.append("{},{}-{}".format(barcode, control_abbrev, barcode))
        timestamp = datetime.datetime.now().strftime("%y%m%dT%H%M%S")
        file_name = "barcodes_{}.csv".format(timestamp)
        content = "\n".join(content)
        files = [(file_name, content)]
        self.context.file_service.upload_files("Barcodes", files)

    def integration_tests(self):
        # yield "24-23564"  # lims-dev
        yield "24-43788"
