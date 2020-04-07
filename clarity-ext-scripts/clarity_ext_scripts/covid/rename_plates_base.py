from abc import abstractmethod
from clarity_ext.extensions import GeneralExtension
from clarity_ext.domain.validation import UsageError


class Extension(GeneralExtension):
    def execute(self):
        for container in self.context.output_containers:
            template = self.rename_template()
            base_name = template.format(
                running_number=self.running_number(container),
                step=self.step_abbreviation(),
                date_string=self.date_string())
            container.name = self.add_version_number(base_name)
            self.context.update(container)

    @staticmethod
    def rename_template():
        """The template used for renaming containers. Override this in inheriting classes"""
        return "COVID_{running_number}_{step}_{date_string}"

    def add_version_number(self, base_name):
        return base_name

    @abstractmethod
    def step_abbreviation(self):
        pass

    @abstractmethod
    def running_number(self, container):
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