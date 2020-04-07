from clarity_ext_scripts.covid.rename_plates.rename_plates_base import Extension as RenamePlatesBase
from clarity_ext_scripts.covid.rename_plates.plate_name_generator import InheritancePlateNameGenerator


class Extension(RenamePlatesBase):
    def __init__(self, *args, **kwargs):
        super(Extension, self).__init__(*args, **kwargs)
        self.name_generator = InheritancePlateNameGenerator()

    def step_abbreviation(self):
        return "RNA"

    def add_version_number(self, base_name):
        return self.name_generator.add_version_number(base_name, self.context)

    def running_number(self, container):
        return self.name_generator.running_number(container, self.context)

    def integration_tests(self):
        yield "24-38714"