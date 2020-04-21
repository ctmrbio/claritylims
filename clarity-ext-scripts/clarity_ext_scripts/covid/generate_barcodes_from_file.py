import datetime
import pandas as pd
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.label_printer import label_printer

class Extension(GeneralExtension):
    """
    Generates a barcode file from an input file. The input file should be a csv on the format:

        barcode,name
    """
    def execute(self):
        barcodes = self.get_barcodes_file()
        timestamp = datetime.datetime.now().strftime("%y%m%dT%H%M%S")
        file_name = 'barcodes_{}.zpl'.format(timestamp)

        for ix, row in barcodes.iterrows():
            barcode = row["barcode"]
            name = row["name"]
            label_printer.generate_zpl_for_control(name, barcode)
        contents = label_printer.contents
        files = [(file_name, contents)]
        self.context.file_service.upload_files("Barcodes for printer", files)

    def get_barcodes_file(self):
        file_name = "Barcodes"
        f = self.context.local_shared_file(file_name, mode="rb")
        return pd.read_csv(f, encoding="utf-8", sep=",")

    def integration_tests(self):
        yield "24-43788"
