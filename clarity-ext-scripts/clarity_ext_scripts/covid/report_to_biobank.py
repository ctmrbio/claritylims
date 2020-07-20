from __future__ import print_function
import logging
import pprint
from datetime import datetime
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.utils import CtmrCovidSubstanceInfo

logger = logging.getLogger(__name__)

class Extension(GeneralExtension):
    """
    Reports sample results to third party partner
    """

    def report(self, sample):
        pp = pprint.PrettyPrinter()
        pp.pprint(sample.id)
        pp.pprint(sample.name)
        pp.pprint(vars(sample.project))
        pp.pprint(sample.udf_map)
#        logger.info("Report2bioBank: sample: {}".format(pp.pformat(sample.project)))

    def execute(self):
        pp = pprint.PrettyPrinter()
        for plate in self.context.input_containers:
            pp.pprint("Plate {}: {}".format(plate.id, plate.name))
            for well in plate.occupied:
                pp.pprint("Well {}: {}".format(well.artifact.well, well.artifact.id))
#                pp.pprint(well.artifact)
                substance = CtmrCovidSubstanceInfo(well.artifact)
#                pp.pprint(substance.substance)
                sample = substance.submitted_sample
#                pp.pprint(vars(sample))
                self.report(sample)

    def integration_tests(self):
        yield "24-51976"
