import logging
import csv
from cStringIO import StringIO
from collections import OrderedDict
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid_seq.utils import DNBSEQ_DB
from clarity_ext.cli import load_config

logger = logging.getLogger(__name__)

class Extension(GeneralExtension):
    """
    Generate DNBSEQ sequencing samplesheet
    """
    def execute(self):
        start = self.context.start
        self.date = start.strftime("%Y%m%d")

        self.db = DNBSEQ_DB()
        sequencer_name = self.context.current_step.udf_sequencer_name
        self.sequencer_id = self.db._get_sequencer_id(sequencer_name)

        samplesheet_data = self.generate_samplesheet_data()

        self.upload_samplesheet(samplesheet_data)

    def generate_samplesheet_data(self):
        """
        Generate a list of dicts representing samplesheet rows
        """
        sheet = []
        for idx, pool in enumerate(set(self._all_outputs)):
            for sample in pool.samples:
                row = OrderedDict()
                row["row_id"] = idx
                row["sample_id"] = sample.name
                row["project_id"] = sample.project.name
                row["flowcell_id"] = self.context.current_step.udf_flowcell_id
                row["lims_id"] = sample.id
                row["well"] =  sample.udf_well_id
                row["adapter_id"] = sample.udf_adapter_id_forward
                row["adapter_id_reverse"] = sample.udf_adapter_id_reverse
                row["sequencer_id"] = self.sequencer_id
                row["lane_id"] = pool.udf_lane_id
                row["pool_id"] = pool.name
                sheet.append(row)
                logger.info(row)
        return sheet

    def upload_samplesheet(self, samplesheet_data):
        """
        Upload samplesheet file to step placeholder
        """
        fieldnames = samplesheet_data[0].keys()
        contents = StringIO()
        
        with open(contents, 'w') as f:
            writer = csv.DictWriter(f, 
                delimiter="\t", 
                fieldnames=fieldnames,
            )
            writer.writeheader()
            for row in samplesheet_data:
                writer.write(row)

        filename = "{}_{}_{}.tsv".format(
            self.date,
            self.sequencer_id,
            self.context.current_step.udf_flowcell_id,
        )
        upload_packet = [(filename, contents)]
        self.context.file_service.upload_files("Sequencing Samplesheet", upload_packet)

    @property
    def _all_inputs(self):
        return [artifact for artifact, _ in self.context.artifact_service.all_aliquot_pairs()]

    @property
    def _all_outputs(self):
        return [artifact for _, artifact in self.context.artifact_service.all_aliquot_pairs()]

    def integration_tests(self):
           yield "24-46735"
