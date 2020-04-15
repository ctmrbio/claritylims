from clarity_ext.extensions import GeneralExtension
from clarity_ext.domain import Container
from clarity_ext_scripts.covid.label_printer import label_printer


class Extension(GeneralExtension):
    """
    Prints barcodes for containers that are listed in the step field `Created containers`
    """

    def create_upload_file(self, container):
        file_name = 'barcode-{}.zpl'.format(container.name)
        label_printer.generate_zpl_for_containers(
            [container], lims_id_as_barcode=True)
        contents = label_printer.contents
        return (file_name, contents)

    def execute(self):
        try:
            created_containers = self.context.current_step.udf_created_containers
        except AttributeError:
            self.usage_error(
                "No containers have been created in this step. "
                "Please press 'Create samples' first")

        files = list()
        for line in created_containers.split("\n"):
            container_id, container_name = line.split(":")
            container = Container(container_id=container_id, name=container_name,
                                  container_type=Container.CONTAINER_TYPE_96_WELLS_PLATE)
            files.append(self.create_upload_file(container))

        self.context.file_service.upload_files("Barcodes", files)

    def integration_tests(self):
        yield "24-40639"
