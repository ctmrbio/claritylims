from clarity_ext.extensions import TemplateExtension
from clarity_ext.domain import Container
import datetime


class Extension(TemplateExtension):

    def shared_file(self):
        return "Input file RT-PCR"

    def file_prefix(self):
        """Removes the prefix from the json file"""
        from clarity_ext.service import FileService
        return FileService.FILE_PREFIX_NONE

    def filename(self):
        timestamp = datetime.datetime.now().strftime("%y%m%dT%H%M%S")
        container_name = self.context.output_container.name
        return "{}_QuantStudio-7_{}.txt".format(container_name, timestamp)

    def artifacts(self):
        max_number_of_plates = 1  # TODO: decide max number, perhaps it is just 1 anyway?
        if len(self.context.output_containers) > max_number_of_plates:
            raise Exception("The allowed max number of plates is currently set to {}".format(max_number_of_plates))
        for well in self.context.output_container.list_wells(Container.RIGHT_FIRST):
            yield well

    def integration_tests(self):
        yield self.test("24-43779", commit=False)
