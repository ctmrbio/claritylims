import random
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid_seq.create_samples.common import SamplesheetFile

class Extension(GeneralExtension):
    """
    Generate demo samplesheet for the create sample step.
    """
    def execute(self):
        plate_id = 'DEMO123'
        filename = '{}_COVIDSeq_samplesheet.csv'.format(plate_id)
        samplesheet_rows = [
            ",".join(SamplesheetFile.HEADERS),
            ",".join([
                "A1", "12348971234", "01", "SEADG", "Riskland", "Eng. mutant", 
                plate_id, "", "27.75", "26.31", "", "", "",
            ]),
            ",".join([
                "B1", "987654321", "03", "SEADG", "Riskland", "Eng. mutant", 
                plate_id, "", "21.75", "22.31", "", "", "",
            ]),
            ",".join([
                "C11", "demosample1", "12", "SEADG", "Information saknas", "", 
                plate_id, "", "29.75", "28.31", "", "", "",
            ]),
            ",".join([
                "D3", "othersample2", "20", "SEABC", "Utbrottsutredning", "Liten ort", 
                plate_id, "", "37.75", "36.31", "", "", "",
            ]),
        ]
        samplesheet_contents = "\n".join(samplesheet_rows)
        upload_tuple = [(filename, samplesheet_contents)]
        self.context.file_service.upload_files("Samplesheet", upload_tuple)

    def integration_tests(self):
        yield "24-46735"
