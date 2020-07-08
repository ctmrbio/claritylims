import logging
from datetime import datetime
from clarity_ext.extensions import GeneralExtension

logger = logging.getLogger(__name__)

class Extension(GeneralExtension):
    """
    Reports sample results to third party partner
    """

    def report(self, substance):
        pass

    def execute(self):
        for plate in self.context.input_containers:
            for well in plate.occupied:
                substance = CtmrCovidSubstanceInfo(well.artifact)
                self.report(substance)

    def integration_tests(self):
        yield "24-88888"
