import logging
import csv
from cStringIO import StringIO
from collections import OrderedDict
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid_seq.utils import DNBSEQ_DB, DBError, DBIntegrityError

logger = logging.getLogger(__name__)

class Extension(GeneralExtension):
    """
    Generate DNBSEQ sequencing samplesheet
    """
    def execute(self):
        start = self.context.start
        self.date = start.strftime("%Y%m%d")

        self.db = DNBSEQ_DB()

        try:
            sequencer_name = self.context.current_step.udf_sequencer_name
        except AttributeError:
            self.usage_error_defer("Sequencer name must be set.")
            sequencer_name = ""
        self.sequencer_id = self.db._get_sequencer_id(sequencer_name)

        try: 
            self.flowcell_id = self.context.current_step.udf_flowcell_id
        except AttributeError:
            self.usage_error_defer("Flowcell ID not filled in.")

        samplesheet_data = self.generate_samplesheet_data()
        self.upload_samplesheet(samplesheet_data)

        self.db.submit_samplesheet(
            self.sequencer_id,
            self.flowcell_id,
            samplesheet_data,
        )

    def generate_samplesheet_data(self):
        """
        Generate a list of dicts representing samplesheet rows
        """
        sheet = []
        for pool in set(self._all_outputs):
            try:
                pool.udf_lane_id
            except AttributeError:
                self.usage_error("Pool {} has not been assigned a lane id!".format(
                    pool.name
                ))
            for row_id, sample in enumerate(pool.samples, start=1):
                row = OrderedDict()
                row["row_id"] = row_id
                row["sample_id"] = sample.name
                row["project_id"] = sample.project.name
                row["lims_id"] = sample.id
                row["well"] = sample.udf_well_id
                row["adapter_id"] = sample.udf_adapter_id_forward
                row["adapter_id_reverse"] = sample.udf_adapter_id_reverse
                row["sequencer_id"] = self.sequencer_id
                row["flowcell_id"] = self.flowcell_id
                row["lane_id"] = pool.udf_lane_id
                row["pool_id"] = pool.name
                sheet.append(row)
        return sheet

    def upload_samplesheet(self, samplesheet_data):
        """
        Upload samplesheet file to step placeholder
        """
        fieldnames = samplesheet_data[0].keys()
        contents = StringIO()
        
        writer = csv.DictWriter(contents, 
            delimiter="\t", 
            fieldnames=fieldnames,
        )
        writer.writeheader()
        for row in samplesheet_data:
            writer.writerow(row)

        filename = "DNBSEQ_{}_{}_{}.tsv".format(
            self.date,
            self.sequencer_id,
            self.context.current_step.udf_flowcell_id,
        )
        upload_packet = [(filename, contents.getvalue())]
        self.context.file_service.upload_files(
            "Sequencing Samplesheet", 
            upload_packet,
        )

    @property
    def _all_inputs(self):
        return [artifact for artifact, _ in self.context.artifact_service.all_aliquot_pairs()]

    @property
    def _all_outputs(self):
        return [artifact for _, artifact in self.context.artifact_service.all_aliquot_pairs()]

    def integration_tests(self):
           yield "24-46735"
