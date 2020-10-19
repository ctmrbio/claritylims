import logging

import paramiko

from clarity_ext.extensions import GeneralExtension
from clarity_ext.utils import single

logger = logging.getLogger(__name__)

CSV_SEPARATOR = ";"
UDF_TRUE = True

class SFTPConnection:
    """
    Maintains an SFTP server connection with a convenience function for file upload. 
    """

    def __init__(self, host, port, username, password):
        self.transport = paramiko.Transport((host, port))
        self.transport.connect(None, username, password)
        self.sftp_server = paramiko.SFTPClient.from_transport(self.transport)
    
    def upload_file(self, localpath, remotepath):
        self.sftp_server.put(localpath, remotepath)


class Extension(GeneralExtension):
    """
    Upload sample information to KI Biobank's SFTP server
    """

    def generate_biobank_info(self, samples):
        rows = []

        columns = [
            "Samplebarcode",
            "Sampletype",
            "Collectiondate",
            "Region",
            "ResearchSample",
            "Mothersamplebarcode",
            "RTPCRResult",
        ]
        rows.append(CSV_SEPARATOR.join(columns)))

        for sample in samples:
            biobank_tube_barcode = sample.udf_biobank_barcode
            sample_type = "Svalg"
            collection_date = sample  # TODO: Get collection date from DT
            region = sample  # TODO: Get region from DT
            research_sample = "No"
            mothersample_barcode = sample.name  # TODO: Get refcode from DT
            rtpcr_result = sample.udf_rtpcr_result_latest

            rows.append(CSV_SEPARATOR.join([
                biobank_tube_barcode,
                sample_type,
                collection_date,
                region,
                research_sample,
                mothersample_barcode,
                rtpcr_result,
            ]))
        return "\n".join(rows)

    def connect_to_KI_biobank_SFTP(self):
        host = self.config["covid.ki_biobank_url"]
        port = 22
        username = self.config["covid.ki_biobank_username"]
        password = self.config["covid.ki_biobank_password"]
        biobank_sftp_server = SFTPConnection(host, port, username, password)
        return biobank_sftp_server

    def execute(self):
        samples_to_biobank = []
        for plate in self.context.input_containers:
            for well in plate.occupied:
                already_uploaded = False
                try:
                    already_uploaded = well.artifact.udf_biobanked == UDF_TRUE
                except AttributeError:
                    pass

                if self.is_control(well.artifact.sample()):
                    continue
                elif already_uploaded:
                    logger.info("Analyte {} has already been uploaded".format(
                        well.artifact.name))
                    continue

                sample = well.artifact.sample()

                samples_to_biobank.append(sample)
        
        biobank_info_csv = self.generate_biobank_info(samples_to_biobank)

        upload_tuple = ("FILENAME.csv", biobank_info_csv)

        self.context.file_service.upload_files("Biobank export file", upload_tuple)

        biobank_sftp_server = self.connect_to_KI_biobank_SFTP()

        target_path = "./Provleveranser/{}".format("filename.csv")  # TODO: Find a suitable filename
        biobank_sftp_server.upload_file(
            single(self.context.file_service.list_filenames("Biobank export file")),  # TODO: Double check how to get the path of the file
            target_path
        )

    
    def integration_tests(self):
        yield self.test("", commit=False)