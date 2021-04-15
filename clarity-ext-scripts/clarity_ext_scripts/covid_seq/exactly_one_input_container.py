import logging
from clarity_ext.extensions import GeneralExtension

logger = logging.getLogger(__name__)

class Extension(GeneralExtension):
    """
    Raise error if user started step with more than one input container.
    """
    def execute(self):
        if len(self._all_input_containers) > 1:
            self.usage_error(
                "More than one input container! "
                "Please abort and restart step with exactly one input container."
            )

    @property
    def _all_input_containers(self):
        return [in_cont for in_cont, _ in self.context.containers]

    def integration_tests(self):
           yield "24-46735"
