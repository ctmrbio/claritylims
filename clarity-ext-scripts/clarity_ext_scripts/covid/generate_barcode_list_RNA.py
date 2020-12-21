import textwrap
from clarity_ext.extensions import GeneralExtension


class Extension(GeneralExtension):
    """
    Generate a set of two identical barcodes as zpl code for container in step.
    The barcode encodes the name of the container.
    """
    def execute(self):
        file_name = 'printfile.zpl'
        containers = self.context.output_containers

        barcode_template = [
            "^XA",
            "^LH0,0",
            "^FO7,1",
              "^BY1,",
              "^BCN,48,N,",
              "^FD{bc_data}",
            "^FS",
            "^FO7,55",
              "^A0,20,25",
              "^FB380,1,",
              "^FD{label_text}",
            "^FS",
            "^XZ",
        ]

        container_barcodes = []
        for c in containers:
            barcode_data = c.name
            container_barcodes.append(
                ''.join(barcode_template).format(bc_data=barcode_data, label_text=barcode_data))

        content = "\n".join(container_barcodes)
        contents = ''.join([
            "\n",
            "${",
            content,
            content.replace("RNA", "rtPCR").replace(".", ""),  # rtPCR team requires barcode to scan into a suitable filename
            "}$",
            "\n"])
        upload_packet = [(file_name, contents)]
        self.context.file_service.upload_files("Print files", upload_packet)

    def integration_tests(self):
        yield "24-39294"
