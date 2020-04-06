from clarity_ext_scripts.covid.rename_plates import Extension as RenamePlatesBase


class Extension(RenamePlatesBase):
    def step_abbreviation(self):
        return "START"

    def integration_tests(self):
        yield "24-38714"