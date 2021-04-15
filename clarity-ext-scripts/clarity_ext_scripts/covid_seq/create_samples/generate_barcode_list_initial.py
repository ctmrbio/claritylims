from clarity_ext.extensions import GeneralExtension
from clarity_ext.domain import Container
from clarity_ext_scripts.covid_seq.label_printer import label_printer
import datetime


class Extension(GeneralExtension):
    """
    Prints barcodes for containers that are listed in the step field `Created containers`
    The two barcodes are placed in one file
    """
    def execute(self):
        try:
            created_containers = self.context.current_step.udf_created_containers
        except AttributeError:
            self.usage_error(
                "No containers have been created in this step. "
                "Please press 'Create samples' first")

        containers = list()
        today = datetime.date.today()
        date = today.strftime("%y%m%d")
        current_step_id = self.context.current_step.id
        file_name = '{}_PREXT_BIOBANK_Barcodes-{}.zpl'.format(date, current_step_id)

        for line in created_containers.split("\n"):
            container_id, container_name = line.split(":")
            container = Container(container_id=container_id, name=container_name,
                                  container_type=Container.CONTAINER_TYPE_96_WELLS_PLATE)
            containers.append(container)
        label_printer.generate_zpl_for_containers(containers, lims_id_as_barcode=True)

        contents = label_printer.contents
        upload_packet = [(file_name, contents)]
        self.context.file_service.upload_files("Zebra barcodes file", upload_packet)

    def integration_tests(self):
        yield self.test("24-44013", commit=False)
