from uuid import uuid4
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.create_samples.common import ValidatedSampleListFile
from clarity_ext_scripts.covid.knm_service import KNMClientFromExtension
from clarity_ext_scripts.covid.partner_api_client import (
    ORG_URI_BY_NAME, TESTING_ORG, CouldNotCreateServiceRequest, ServiceRequestAlreadyExists)


class Extension(GeneralExtension):
    """
    Goes through the 'Validated sample list' ensuring that each sample that has the unregistered
    status gets an anonymous service request id.

    Uploads a new file to the validated sample list file handle. The name of it will be on the form
    'validated_sample_list_no_unregistered_<timestamp>.csv'

    Note that the user is not required to run this extension. They can create samples directly
    if there is a validated sample list that only has status "ok" in it. However, if there
    is any sample without it, samples won't be created.
    """

    def execute(self):
        client = KNMClientFromExtension(self)
        validated_sample_list = ValidatedSampleListFile.create_from_context(
            self.context)
        no_unregistered = ValidatedSampleListFile(validated_sample_list.csv)

        for ix, row in no_unregistered.csv.iterrows():
            if row[no_unregistered.COLUMN_STATUS] == no_unregistered.STATUS_UNREGISTERED:
                org_uri = row[no_unregistered.COLUMN_ORG_URI]
                ref = row[no_unregistered.COLUMN_REFERENCE]
                service_request_id, comment = self._create_anonymous_service_request(
                    client, ref, org_uri)
                if service_request_id:
                    no_unregistered.csv.at[ix,
                                           no_unregistered.COLUMN_SERVICE_REQUEST_ID] = service_request_id
                    no_unregistered.csv.at[ix,
                                           no_unregistered.COLUMN_STATUS] = no_unregistered.STATUS_OK
                else:
                    no_unregistered.csv.at[ix,
                                           no_unregistered.COLUMN_STATUS] = no_unregistered.STATUS_ERROR

                no_unregistered.csv.at[ix,
                                       no_unregistered.COLUMN_COMMENT] = comment

        no_unregistered_content = no_unregistered.csv.to_csv(
            index=False, sep=",")
        timestamp = self.context.start.strftime("%y%m%dT%H%M%S")
        file_name = "validated_sample_list_no_unregistered_{}.csv".format(
            timestamp)
        self.context.file_service.upload(
            no_unregistered.FILE_HANDLE, file_name, no_unregistered_content,
            self.context.file_service.FILE_PREFIX_NONE)

    def _create_anonymous_service_request(self, client, referral_code, org_uri):
        test_mode = org_uri == ORG_URI_BY_NAME[TESTING_ORG]

        if test_mode:
            return "faked-{}-anon".format(uuid4()), \
                "Faked an anymous request ID for an unregistered sample"

        try:
            service_request_id = client.create_anonymous_service_request(
                referral_code)
            return service_request_id, "Fetched an anonymous request ID for an unregistered sample"
        except CouldNotCreateServiceRequest:
            self.usage_error_defer(
                ("Could not create ServiceRequests for the following barcode(s). "
                 "KNM probably did not recognize them. "
                 "Please investigate the barcode(s)."), referral_code)
        except ServiceRequestAlreadyExists:
            self.usage_error_defer(
                ("There already exists a ServiceRequest for the following barcode(s). This means something "
                 "odd is going on. Maybe you set a sample to anonymous in the 'Validated sample list', that should not "
                 "have been set to anonymous? Contact your friendly sysadmin for help."), referral_code)
        return None, "Could not fetch an anonymous request ID for unregistered sample"

    def integration_tests(self):
        yield "24-46746"
