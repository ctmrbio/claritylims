from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.label_printer import label_printer


class Extension(GeneralExtension):
    """
    Generate a list of barcodes as zpl code for containers in step.
    The barcode is here the name of the containers
    """
    def execute(self):
        file_name = 'printfile.zpl'
        containers = self.context.output_containers
        label_printer.generate_zpl_for_containers(containers, lims_id_as_barcode=False)
        contents = label_printer.contents
        upload_packet = [(file_name, contents)]
        self.context.file_service.upload_files("Print files", upload_packet)

    def integration_tests(self):
        yield "24-38734"