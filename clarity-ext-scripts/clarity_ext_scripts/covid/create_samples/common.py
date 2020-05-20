"""
Contains classes that are common to the workflow for creating samples.

There are several extensions that all use this logic:
    * validate_sample_creation_list.py 
    * import_samples.py (TODO should be named create_samples.py for consistency)

    * validate_discarded_samples.py 
    * create_discard_samples.py

    * assign_unregistered_to_anonymous.py

These will for example share common files.
"""

import logging
from uuid import uuid4
import pandas as pd
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.partner_api_client import (
    TESTING_ORG, ORG_URI_BY_NAME, KARLSSON_AND_NOVAK,
    OrganizationReferralCodeNotFound, PartnerClientAPIException)

logger = logging.getLogger(__name__)


class PandasWrapper(object):
    """
    Wraps a pandas file, having methods to consistenly fetch from a context
    """

    # Override this in subclasses
    FILE_HANDLE = "Some file handle"

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
        return pd.read_csv(file_like, sep=cls.SEPARATOR, dtype="string")

    @staticmethod
    def filter_before_parse(file_like):
        """
        If required in subclasses, return a new file_like that has been filtered
        """
        return file_like


class BaseRawSampleListFile(PandasWrapper):
    """
    Describes the CSV file that hangs on the 'Raw sample list' file handle.

    Note that this is currently subtly different between the two use cases
    """
    FILE_HANDLE = "Raw sample list"

    # Subclass should define the COLUMNS as constants and a HEADER that lists all headers

    # COLUMN_*

    HEADERS = ["<Should be subclassed>"]

    # The column from which we can get the fake status in integration tests
    COLUMN_FAKE_STATUS = "<Should be subclassed>"

    def ValidatedSampleListFile(self):
        # Generates a new file of type ValidatedSampleListFile from this file. Ensures
        # that all columns we require later in the workflow are now named the same.
        ret = ValidatedSampleListFile(self.csv)
        ret.COLUMN_FAKE_STATUS = self.COLUMN_FAKE_STATUS
        return ret


class ValidatedSampleListFile(PandasWrapper):
    """
    Defines constants etc. that are in the ValidatedSampleList.

    This file is built using the data from the raw sample list file as a baseline, but adds
    metadata related to the validation.
    """

    FILE_HANDLE = "Validated sample list"

    COLUMN_REFERENCE = "Sample Id"
    COLUMN_REGION = "Region"
    COLUMN_DEVIATION = "Deviation"

    COLUMN_SERVICE_REQUEST_ID = "service_request_id"
    COLUMN_STATUS = "status"
    COLUMN_COMMENT = "comment"
    COLUMN_ORG_URI = "org_uri"
    COLUMN_POSITION = "Position"  # NOTE: This is not in the discard samples file

    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    STATUS_UNREGISTERED = "unregistered"

    STATUS_ALL = [
        STATUS_OK,
        STATUS_ERROR,
        STATUS_UNREGISTERED
    ]


BUTTON_TEXT_ASSIGN_UNREGISTERED_TO_ANONYMOUS = "Assign unregistered to anonymous"


class BaseValidateRawSampleListExtension(GeneralExtension):
    def _search_for_id(self, validated_sample_list, client, ordering_org, row):
        """
        Searches for an ID for this ordering_org and barcode.

        Returns the tuple:
            (service_request_id, status, comment, org_uri)

        :validated_sample_list: The validated sample list we get the data from
        :client: The KNM api client instance
        :ordering_org: The organization requiring the data
        :row: The row we're currently processing
        """
        org_uri = ORG_URI_BY_NAME[ordering_org]
        barcode = str(row[validated_sample_list.COLUMN_REFERENCE])

        if ordering_org == TESTING_ORG:
            # The user can send in a "fake status" from the raw sample list, by including it
            # in COLUMN_FAKE_STATUS. If we don't recognize it as one of the status flags, we
            # should just use "ok"
            status = row[validated_sample_list.COLUMN_FAKE_STATUS]
            if status not in validated_sample_list.STATUS_ALL:
                status = validated_sample_list.STATUS_OK

            comment = "This data is faked for integration purposes (Internal testing was selected)"

            if status == validated_sample_list.STATUS_OK:
                service_request_id = "faked-{}".format(uuid4())
                logger.warn("Using testing org. Service request ID faked: {}".format(
                    service_request_id))
            else:
                service_request_id = ""
            return service_request_id, status, comment, org_uri

        try:
            response = client.search_for_service_request(org_uri, barcode)
            service_request_id = response["resource"]["id"]
            status = validated_sample_list.STATUS_OK
            comment = ""
        except OrganizationReferralCodeNotFound as e:
            self.usage_warning(
                "These barcodes are not registered for the org {}. "
                "Press '{}' in order to fetch anonymous service requests for these.".format(
                    org_uri,
                    BUTTON_TEXT_ASSIGN_UNREGISTERED_TO_ANONYMOUS), barcode)
            status = validated_sample_list.STATUS_UNREGISTERED

            # Overwrite the org_uri so we use KARLSSON_AND_NOVAK, because this will be anonymous
            org_uri = ORG_URI_BY_NAME[KARLSSON_AND_NOVAK]

            # An "unregistered" status signals to the next step in the workflow that we need
            # to fetch an anonymous service request:
            status = validated_sample_list.STATUS_UNREGISTERED
            service_request_id = ""
            comment = ("No matching request was found for this referral code. "
                       "Press '{}' in order to fetch anonymous service requests for these.".format(
                           BUTTON_TEXT_ASSIGN_UNREGISTERED_TO_ANONYMOUS
                       ))
        except PartnerClientAPIException as e:
            self.usage_error_defer(
                "Something was wrong with {} for barcode(s). "
                "See file validated sample list for details.".format(org_uri), barcode)
            service_request_id = ""
            status = validated_sample_list.STATUS_ERROR
            comment = e.message
        return service_request_id, status, comment, org_uri


class BaseCreateSamplesExtension(GeneralExtension):
    def get_validated_sample_list(self):
        """
        Gets a validated sample list and raises an error if it's not valid.

        NOTE: Anonymous service requests are given a name from KNM here 
        """
        validated_sample_list = ValidatedSampleListFile.create_from_context(
            self.context)

        errors = list()
        unregistered = list()

        for ix, row in validated_sample_list.csv.iterrows():
            status = row[validated_sample_list.COLUMN_STATUS]
            ref = row[validated_sample_list.COLUMN_REFERENCE]
            if status == validated_sample_list.STATUS_UNREGISTERED:
                unregistered.append(ref)
            elif status == validated_sample_list.STATUS_ERROR:
                errors.append(ref)
            elif status != validated_sample_list.STATUS_OK:
                raise AssertionError("Unexpected status: {}".format(status))

        if len(errors) + len(unregistered) > 0:
            msg = "There are {} errors and {} unregistered in the sample list. " \
                "Check the file 'Validated sample list' for details".format(
                    len(errors), len(unregistered))
            self.usage_error(msg)

        return validated_sample_list
