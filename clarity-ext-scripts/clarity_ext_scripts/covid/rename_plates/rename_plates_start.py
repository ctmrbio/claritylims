from clarity_ext_scripts.covid.rename_plates.rename_plates_base import Extension as RenamePlatesBase


class Extension(RenamePlatesBase):
    def step_abbreviation(self):
        return "START"

    def running_number(self, container):
        _, running_number = container.id.split("-")
        return running_number

    def integration_tests(self):
        yield "24-38714"
