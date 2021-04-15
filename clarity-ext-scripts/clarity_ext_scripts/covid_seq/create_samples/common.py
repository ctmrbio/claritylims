# encoding: utf-8
"""
Contains classes that are common to the workflow for creating samples.
"""
import logging
from uuid import uuid4
from collections import defaultdict
import pandas as pd
from clarity_ext.extensions import GeneralExtension

logger = logging.getLogger(__name__)


class PandasWrapper(object):
    """
    Wraps a pandas file, having methods to consistently fetch from a context
    """

    # Override these in subclasses
    FILE_HANDLE = "Some file handle"  # Override in subclass
    HEADERS = [""]                    # Override in subclass

    SEPARATOR = ","

    def __init__(self, csv):
        self.csv = csv

    @classmethod
    def create_from_context(cls, context):
        # Creates an instance of this file from the extension context
        f = context.local_shared_file(cls.FILE_HANDLE, mode="rb")
        f = cls.filter_before_parse(f)
        csv = cls.parse_to_csv(f)
        return cls(csv)

    @classmethod
    def parse_to_csv(cls, file_like):
        """Parse file_like as CSV, interpreting all fields as a string."""
        return pd.read_csv(file_like, sep=cls.SEPARATOR, dtype=str, na_filter=False)

    @staticmethod
    def filter_before_parse(file_like):
        """
        If required in subclasses, return a new file_like that has been filtered
        """
        return file_like


class SamplesheetFile(PandasWrapper):
    """
    Describes the CSV file that is submitted to the 'Samplesheet' file handle.
    """
    FILE_HANDLE = "Samplesheet"

    COLUMN_WELL = "well"
    COLUMN_SAMPLE_ID = "sample_id"
    COLUMN_REGION_CODE = "region_code"
    COLUMN_LAB_CODE = "lab_code"
    COLUMN_SELECTION_CRITERIA = "selection_criteria"
    COLUMN_SELECTION_CRITERIA_DETAIL = "selection_criteria_detail"
    COLUMN_BIOBANK_PLATE_ID = "biobank_plate_id"
    COLUMN_BIOBANK_TUBE_ID = "biobank_tube_id"
    COLUMN_CT_1 = "Ct_1"
    COLUMN_CT_2 = "Ct_2"
    COLUMN_CT_3 = "Ct_3"
    COLUMN_CT_4 = "Ct_4"
    COLUMN_CT_5 = "Ct_5"

    HEADERS = [
        COLUMN_WELL,
        COLUMN_SAMPLE_ID,
        COLUMN_REGION_CODE,
        COLUMN_LAB_CODE,
        COLUMN_SELECTION_CRITERIA,
        COLUMN_SELECTION_CRITERIA_DETAIL,
        COLUMN_BIOBANK_PLATE_ID,
        COLUMN_BIOBANK_TUBE_ID,
        COLUMN_CT_1,
        COLUMN_CT_2,
        COLUMN_CT_3,
        COLUMN_CT_4,
        COLUMN_CT_5,
    ]

    VALID_REGION_CODES = {
        "01",  # Region Stockholm
        "03",  # Region Uppsala
        "04",  # Region Sörmland
        "05",  # Region Östergötland
        "06",  # Region Jönköpings län
        "07",  # Region Kronoberg
        "08",  # Region Kalmar län
        "09",  # Region Gotland
        "10",  # Region Blekinge
        "12",  # Region Skåne
        "13",  # Region Halland
        "14",  # Västra Götalandsregionen
        "17",  # Region Värmland
        "18",  # Region Örebro län
        "19",  # Region Västmanland
        "20",  # Region Dalarna
        "21",  # Region Gävleborg
        "22",  # Region Västernorrland
        "23",  # Region Jämtland Härjedalen
        "24",  # Region Västerbotten
        "25",  # Region Norrbotten
    }

    VALID_LABCODES = {
        "SE110",  # Växjö
        "SE120",  # Malmö
        "SE240",  # Kalmar
        "SE320",  # Borås
        "SE450",  # Karlstad
        "SE250",  # Halmstad
        "SE310",  # Trollhättan NÄL
        "SE300",  # Sahlgrenska
        "SE230",  # Karlskrona
        "SE540",  # Visby
        "SE100",  # Karolinska
        "SE130",  # Unilabs
        "SE140",  # SYNLAB
        "SE330",  # Unilabs
        "SE350",  # Jönköping
        "SE400",  # Linköping
        "SE420",  # Unilabs
        "SE430",  # Västerås
        "SE440",  # Örebro
        "SE600",  # Uppsala
        "SE610",  # Gävle
        "SE620",  # Falun
        "SE700",  # Sundsvall
        "SE710",  # Östersund
        "SE720",  # Umeå
        "SE730",  # Sunderby, Luleå
        "SENPC",  # National Pandemic Center
        "SEADG",  # A05diagnistics
        "SEABC",  # ABC lab
        "SEDNC",  # Dynamic Code
    }

    VALID_SELECTION_CRITERIA = {
        "Allmän övervakning",
        "Allmän övervakning öppenvård",
        "Allmän övervakning slutenvård",
        "Utbrottsutredning",
        "Vaccinationsgenombrott",
        "Riskland",
        "SGTF",
        "Reinfektion",
        "Information saknas",
    }


class BaseCreateSamplesExtension(GeneralExtension):
    def validate_samplesheet(self, valid_biobank_plate_id=""):
        """
        Validate samplesheet and raise error if it's not valid.
        """
        samplesheet = SamplesheetFile.create_from_context(
            self.context)

        errors = list()
        if not valid_biobank_plate_id:
            errors.append("No Biobank plate id entered in step!")

        observed_wells = defaultdict(int)
        observed_sample_ids = defaultdict(int)
        for idx, row in samplesheet.csv.iterrows():
            well = row[samplesheet.COLUMN_WELL]
            sample_id = row[samplesheet.COLUMN_SAMPLE_ID]
            biobank_plate_id = row[samplesheet.COLUMN_BIOBANK_PLATE_ID]
            biobank_tube_id = row[samplesheet.COLUMN_BIOBANK_TUBE_ID]
            selection_criteria = row[samplesheet.COLUMN_SELECTION_CRITERIA]
            region_code = row[samplesheet.COLUMN_REGION_CODE]
            lab_code = row[samplesheet.COLUMN_LAB_CODE]

            observed_wells[well] += 1
            observed_sample_ids[sample_id] += 1

            if not sample_id:
                errors.append("Row {}, sample_id is empty".format(idx))
            if not biobank_tube_id:
                # Replace empty biobank_tube_id value in the underlying DataFrame
                samplesheet.csv.iloc[idx][samplesheet.COLUMN_BIOBANK_TUBE_ID] = "{}_{}".format(
                    biobank_plate_id, well)
            if biobank_plate_id and (biobank_plate_id != valid_biobank_plate_id):
                errors.append("Row {}, Biobank plate ID is inconsistent!".format(idx))
            if selection_criteria not in samplesheet.VALID_SELECTION_CRITERIA:
                errors.append("Row {}, Selection criteria not valid: {}".format(idx, selection_criteria))
            if region_code not in samplesheet.VALID_REGION_CODES:
                errors.append("Row {}, Region code not valid: {}".format(idx, region_code))
            if lab_code not in samplesheet.VALID_LABCODES:
                errors.append("Row {}, Lab code not valid: {}".format(idx, lab_code))

        for well, count in observed_wells.iteritems():
            if count > 1:
                errors.append("{} exists more than once!".format(well))
        for sample_id, count in observed_sample_ids.iteritems():
            if count > 1:
                errors.append("{} exists more than once!".format(sample_id))

        if len(errors) > 0:
            msg = "There are {} errors in the sample list. " \
                "Please check the input file and try again. " \
                "{}".format(
                    len(errors), errors)
            self.usage_error(msg)

        return samplesheet
