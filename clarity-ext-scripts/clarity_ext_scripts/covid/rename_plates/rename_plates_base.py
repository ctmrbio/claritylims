import re
from abc import abstractmethod
from clarity_ext.extensions import GeneralExtension
from clarity_ext.domain.validation import UsageError


class Extension(GeneralExtension):
    """
    Names are expected to be on one of two formats. either:
       <prefix>_<date>_<step abbr>_<time>
    Or
       <prefix>_<date>_<step abbr>_<time>.<version>

    Example:

      Input plate                 Output plate
      ==========================================================
      COVID_200416_PREXT_134035   COVID_200416_RNA_134035.v1
      COVID_200416_RNA_134035.v1  COVID_200416_rtPCR_134035.v1

    Before giving the plate the name, there is a check for if it's unique, i.e. that there
    is no plate with the same name. In such a case, the version is increased:

      Input plate                 First try                   Second try
      ==================================================================================
      COVID_200416_RNA_134035.v1  COVID_200416_RNA_134035.v1  COVID_200416_RNA_134035.v2
    """

    def execute(self):
        pattern = re.compile(self.input_pattern())
        template = self.rename_template()
        for in_cont, out_cont in self.context.containers:
            m = pattern.match(in_cont.name)
            tokens = m.groupdict()
            tokens["step"] = self.step_abbreviation()
            base_name = template.format(**tokens)
            out_cont.name = self.add_version_number(base_name)
            self.context.update(out_cont)

    @staticmethod
    def input_pattern():
        """Defines the pattern that's used to match against the input container name."""
        return r"(?P<prefix>.+)_(?P<date>.+)_(?P<step>.+)_(?P<time>[^.]+)(\..+)?"

    @staticmethod
    def rename_template():
        """The template used for renaming containers. Override this in inheriting classes"""
        return "{prefix}_{date}_{step}_{time}"

    def add_version_number(self, base_name):
        return base_name

    @abstractmethod
    def step_abbreviation(self):
        pass

    def date_string(self):
        try:
            if len(self.context.current_step.udf_date_yymmdd) != 6:
                raise UsageError("The date format is not correct, YYMMDD, leave empty if not used.")
            return self.time(self.context.current_step.udf_date_yymmdd)
        except AttributeError:
            return self.time("%y%m%d")

    def integration_tests(self):
        yield "24-38714"
