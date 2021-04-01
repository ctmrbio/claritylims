import logging
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid_seq.utils import DNBSEQ_DB

logger = logging.getLogger(__name__)

class Extension(GeneralExtension):
    """
    Generate DNBSEQ sequencing samplesheet
    """
    def execute(self):
        start = self.context.start
        date = start.strftime("%Y%m%d")

        db = DNBSEQ_DB()

        sequencer_name = self.context.current_step.udf_sequencer_name
        logger.info(db._get_sequencer_id("Ada"))

        sheet = []
        for idx, pool in enumerate(set(self._all_inputs)):
            for sample in pool.samples:
                row = dict()
                row["row_id"] = idx
                row["sample_id"] = sample.name
                row["project_id"] = "COVIDseq"  # HARDCODED??
                row["flowcell_id"] = self.context.current_step.udf_flowcell_id
                row["lims_id"] = sample.id
                row["well"] = sample.position
                row["adapter_id"] = sample.udf_adapter_id_forward
                row["adapter_id_reverse"] = sample.udf_adapter_id_reverse
                row["sequencer_id"] = self.context.current_step.udf_sequencer_id
                row["lane_id"] = sample.udf_lane_id
                row["pool_id"] = pool.name
                sheet.append(row)
                logger.info(row)


    @property
    def _all_inputs(self):
        return [artifact for artifact, _ in self.context.artifact_service.all_aliquot_pairs()]

    def integration_tests(self):
           yield "24-46735"
