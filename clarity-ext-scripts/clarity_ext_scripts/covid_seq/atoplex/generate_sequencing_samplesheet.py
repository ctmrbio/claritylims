import logging
from clarity_ext.extensions import GeneralExtension

logger = logging.getLogger(__name__)

class Extension(GeneralExtension):
    """
    Generate DNBSEQ sequencing samplesheet
    """
    def execute(self):
        start = self.context.start
        date = start.strftime("%Y%m%d")

        for idx, pool in enumerate(set(self._all_inputs)):
            for sample in pool.samples:
                #logger.info(self.context.current_step.udf_sequencer_id)
                #logger.info(self.context.current_step.udf_flowcell_id)
                logger.info(sample.udf_adapter_id_forward)
                logger.info(sample.udf_adapter_id_reverse)


    @property
    def _all_inputs(self):
        return [artifact for artifact, _ in self.context.artifact_service.all_aliquot_pairs()]

    def integration_tests(self):
           yield "24-46735"
