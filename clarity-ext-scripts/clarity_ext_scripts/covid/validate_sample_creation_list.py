import cStringIO
from uuid import uuid4
import logging
from datetime import datetime
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.partner_api_client import (
    PartnerAPIV7Client, TESTING_ORG, ORG_URI_BY_NAME, OrganizationReferralCodeNotFound,
    PartnerClientAPIException, ServiceRequestAlreadyExists, CouldNotCreateServiceRequest,
    KARLSSON_AND_NOVAK)
from clarity_ext_scripts.covid.controls import controls_barcode_generator
from clarity_ext_scripts.covid.utils import KNMClient
from clarity_ext_scripts.covid.create_samples.common import (
	BaseRawSampleListFile, ValidatedSampleListFile,
        BaseValidateRawSampleListExtension
)


logger = logging.getLogger(__name__)


class RawSampleListColumns(object):
    COLUMN_REFERENCE = "Sample Id"
    COLUMN_POSITION = "Position"
    COLUMN_USER_DEFINED1 = "USERDEFINED1"

    HEADERS = ["Rack Id", "Cavity Id",
               COLUMN_POSITION, COLUMN_REFERENCE,
               "CONCENTRATION", "CONCENTRATIONUNIT", "VOLUME",
               COLUMN_USER_DEFINED1,  # Contains a control name or the integration test knm status 
               "USERDEFINED2", "USERDEFINED3", "USERDEFINED4", "USERDEFINED5",
               "PlateErrors", "SampleErrors", "SAMPLEINSTANCEID", "SAMPLEID"]

    # The column from which we can get the fake status in integration tests
    COLUMN_FAKE_STATUS = COLUMN_USER_DEFINED1 


class RawSampleListFile(RawSampleListColumns, BaseRawSampleListFile):
    """
    Describes the CSV file that hangs on the 'Raw sample list' file handle.
    """
    @staticmethod
    def filter_before_parse(file_like):
        filtered = cStringIO.StringIO()
        # Ignore everything at or after the line that contains this text:
        stop_condition = "Sample Tracking Report Name"

        for line in file_like:
            if stop_condition in line:
                break
            filtered.write(line + "\n")
        filtered.seek(0)
        return filtered


class Extension(BaseValidateRawSampleListExtension):
    """
    Validates all samples in a sample creation list.

    Before execution of this script, a research engineer has uploaded a raw csv on the format:

        barcode;well

    to the `Raw sample list` file handle.

    This script generates a new sample list. It's equivalent to the original sample
    list, but also adds three new fields:

    ```
    barcode: <barcode from csv>
    well: <well from csv>
    *status: <error | success>
    *service_request_id: <the service request ID from KNM>
    *comment: <details about the error, if any>
    ```

    This will be the input for creating samples later on. That extension must require that there
    are no errors in any of the rows. If there is an error, no sample should be created.

    In the case of an error, the research engineer has these options:

        * Edit the raw sample list and run validate again.
        * Edit this script or request changes at KNM.
        * In an extreme case, e.g. given manual confirmation, the research engineer can upload a new
          validated file with manually edited information.
    """

    def execute(self):
        # Validate the 'Raw biobank file' exists and is in concordance with the 'Raw sample list'
        # if not, abort script execution
        from clarity_ext_scripts.covid.fetch_biobank_barcodes import FetchBiobankBarcodes
        validator = FetchBiobankBarcodes(self.context)
        validator.validate()

        # 1. Get the ordering organizations URI
        try:
            ordering_org = self.context.current_step.udf_ordering_organization
        except AttributeError:
            self.usage_error("You must select an ordering organization")

        # 2. Create an API client
        #    Make sure that there is a config at ~/.config/clarity-ext/clarity-ext.config
        client = KNMClient(self)

        # 3. Read the raw sample list.
        raw_sample_list = RawSampleListFile.create_from_context(self.context)
        validated_sample_list = raw_sample_list.ValidatedSampleListFile()

        # 4. Create the validated list
        for ix, row in validated_sample_list.csv.iterrows():
            barcode = row[validated_sample_list.COLUMN_REFERENCE]
            well = row[validated_sample_list.COLUMN_POSITION]

            # NOTE: The well is in the format "A01" etc
            if len(well) != 3:
                raise AssertionError(
                    "Expected the Position in the raw sample list to be on the format A01. "
                    "Got: {}".format(well))
            plate_row = well[0]
            plate_col = int(well[1:])
            well = "{}:{}".format(plate_row, plate_col)
            # TODO It seems that we always need controls here, which
            #      we need to check if that will always be the case.
            is_control = controls_barcode_generator.parse(barcode)

            if not is_control:
                service_request_id, status, comment, org_uri = self._search_for_id(
                        validated_sample_list, client, ordering_org, row)
                validated_sample_list.csv.loc[ix,
                                              validated_sample_list.COLUMN_ORG_URI] = org_uri
            else:
                service_request_id = ""
                status = ValidatedSampleListFile.STATUS_OK
                comment = ""

            validated_sample_list.csv.loc[ix,
                                          validated_sample_list.COLUMN_SERVICE_REQUEST_ID] = service_request_id
            validated_sample_list.csv.loc[ix,
                                          validated_sample_list.COLUMN_STATUS] = status
            validated_sample_list.csv.loc[ix, validated_sample_list.COLUMN_COMMENT] = comment.replace(
                ",", "<SC>")  # If we have the separator in the comment

        validated_sample_list_content = validated_sample_list.csv.to_csv(
            index=False, sep=",")

        timestamp = datetime.now().strftime("%y%m%dT%H%M%S")

        file_name = "validated_sample_list_{}.csv".format(timestamp)
        self.context.file_service.upload(
            "Validated sample list", file_name, validated_sample_list_content,
            self.context.file_service.FILE_PREFIX_NONE)

    def integration_tests(self):
        yield self.test("24-46735", commit=True)
