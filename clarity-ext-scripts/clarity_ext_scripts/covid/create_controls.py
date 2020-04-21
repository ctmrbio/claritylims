import time
from clarity_ext_scripts.covid.controls import Controls
from clarity_ext_scripts.covid.utils import UniqueBarcodeGenerator
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

        gen = UniqueBarcodeGenerator(control_key, "x")
        content = ["barcode,name"]
        for ix, barcode in enumerate(gen.generate(number_of_controls)):
            content.append("{},{}-{}".format(barcode, control_abbrev, barcode))
        file_name = "barcodes.csv"
        content = "\n".join(content)
        files = [(file_name, content)]
        self.context.file_service.upload_files("Barcodes", files)

    def integration_tests(self):
        # yield "24-23564"  # lims-dev
        yield "24-43787"
