import logging
from clarity_ext.extensions import GeneralExtension
from clarity_ext.utils import single
from clarity_ext_scripts.covid_seq.utils import DNBSEQ_DB

logger = logging.getLogger(__name__)

class Extension(GeneralExtension):
    """
    Generate DNBSEQ sequencing samplesheet
    """
    def execute(self):
        existing_samplesheet_file = False
        try: 
            existing_file = single(
                self.context.file_service.list_filenames('Sequencing Samplesheet')
            )
        except IndexError:
            pass
        if not existing_samplesheet_file:
            self.usage_error("No samplesheet has been generated yet.")
        
        self.db = DNBSEQ_DB()
        sequencer_name = self.context.current_step.udf_sequencer_name
        self.sequencer_id = self.db._get_sequencer_id(sequencer_name)
        self.flowcell_id = self.context.current_step.udf_flowcell_id

        samplesheet_data = self.generate_samplesheet_data()

        #self.db.submit_samplesheet(
        #    self.sequencer_id,
        #    self.flowcell_id,
        #    samplesheet_data,
        #)

    def integration_tests(self):
        yield "24-46735