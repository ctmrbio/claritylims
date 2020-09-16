import logging
from clarity_ext.domain import Container, Sample
from clarity_ext_scripts.covid.controls import controls_barcode_generator, Controls
from clarity_ext_scripts.covid.services.knm_service import KNMClientFromExtension, ServiceRequestProvider
from clarity_ext_scripts.covid.create_samples.common import BaseCreateSamplesExtension

logger = logging.getLogger(__name__)

class Extension(BaseCreateSamplesExtension):
    """
    Requires two step UDFs:
        * Assign to workflow: Any workflow
        * Project: Any project

    Requires a CSV file with the headers barcode;well


    Creates two containers with samples and controls in Clarity:
        COVID_<date>_PREXT_<time>
            <sample_name_in_csv>_<region_from_ServiceRequest>-<subregion_from_ServiceRequest>_<timestamp w sec>
            <control_name_in_csv>_<timestamp w sec>_<running>
            ...
        COVID_<date>_BIOBANK_<time>
            <sample_name_in_csv>_<region_from_ServiceRequest>-<subregion_from_ServiceRequest>_<timestamp w sec>_BIOBANK
            <control_name_in_csv>_<timestamp w sec>_<running>_BIOBANK
            ...

    The <running> part of the names is a running number for controls.
    """

    def create_sample(self, original_name, timestamp, project, specifier, org_uri, service_request_id):

        provider = ServiceRequestProvider(
            self.client, org_uri, original_name)

        try:
            referring_clinic_name = provider.patient["managingOrganization"]["display"].encode("ascii", "ignore")
        except AttributeError:
            logger.warning("Found no referring clinic information for %s" % original_name)
            referring_clinic_name = ""

        name = [
            original_name,
            "".join(referring_clinic_name.split()),
            timestamp,
        ]
        if specifier:
            name.append(specifier)
        name = "_".join(str(component) for component in name if component)
        sample = Sample(sample_id=None, name=name, project=project)
        sample.udf_map.force("Control", "False")

        # Add KNM data:test_partner_user
        sample.udf_map.force("KNM data added at", timestamp)
        sample.udf_map.force("KNM org URI", org_uri)
        sample.udf_map.force("KNM service request id", service_request_id)

        return sample

    def create_control(self, original_name, control_type, timestamp,
                       running_number, project, specifier):
        control_type_name = Controls.MAP_FROM_KEY_TO_ABBREVIATION[control_type]
        name = map(str, [control_type_name, timestamp, running_number])
        if specifier:
            name.append(specifier)
        name = "_".join(name)
        control = Sample(sample_id=None, name=name, project=project)
        control.udf_map.force("Control", "True")
        control.udf_map.force("Control type", control_type_name)
        return control

    def create_in_mem_container(
            self, samples_file, container_specifier, sample_specifier, control_specifier, date,
            time, biobank_barcode_by_sample_referal_code=None
    ):
        """Creates an in-memory container with the samples

        The name of the container will be on the form:

           COVID_<date>_<container_specifier>_<time to sec>

        The name of the samples will be:

            <name in csv>_<region>-<subregion>_<timestamp>_<sample_specifier>

        <region> and <subregion> will have whitespace chars removed.

        The name of the controls will be on the form:

            <name in csv>_<timestamp>_<control_specifier>
        """
        timestamp = date + "T" + time

        # 1. Get the project
        project = self.context.clarity_service.get_project_by_name(
            self.context.current_step.udf_project)

        # 2. Create a 96 well plate in memory:
        container_type = "96 well plate"
        name = "COVID_{}_{}_{}".format(date, container_specifier, time)
        container = Container(container_type=container_type, name=name)

        # 3. Create in-memory samples
        control_running = 0
        for ix, row in samples_file.csv.iterrows():
            original_name = row[samples_file.COLUMN_REFERENCE]
            well = row[samples_file.COLUMN_POSITION]
            org_uri = row[samples_file.COLUMN_ORG_URI]
            service_request_id = row[samples_file.COLUMN_SERVICE_REQUEST_ID]

            control_type_tuple = controls_barcode_generator.parse(
                original_name)

            if control_type_tuple:
                control_type, _, _ = control_type_tuple
                control_running += 1
                substance = self.create_control(
                    original_name, control_type, timestamp,
                    control_running, project, control_specifier)
            else:
                substance = self.create_sample(
                    original_name, timestamp, project, sample_specifier, org_uri,
                    service_request_id)
                if biobank_barcode_by_sample_referal_code:
                    biobank_barcode = biobank_barcode_by_sample_referal_code[
                        original_name
                    ]
                    substance.udf_map.force("Biobank barcode", biobank_barcode)
            substance.udf_map.force("Sample Buffer", "None")
            substance.udf_map.force(
                "Step ID created in", self.context.current_step.id)
            container[well] = substance
        return container

    def execute(self):
        """
        Creates samples from a validated import file
        """
        self.client = KNMClientFromExtension(self)

        # This is for debug reasons only. Set this to True to create samples even if they have
        # been created before. This will overwrite the field udf_created_containers.
        force = False

        # 1. Don't create samples again if we've already created them. This is a limitation
        # that we add to make sure that we don't have more than 2 container labels to print.
        try:
            udf_container_log = self.context.current_step.udf_created_containers
        except AttributeError:
            udf_container_log = ""
        if udf_container_log and not force:
            raise AssertionError(
                "Samples have already been created in this step")

        container_log = list()

        start = self.context.start
        date = start.strftime("%y%m%d")
        time = start.strftime("%H%M%S")

        # 2. Read the samples from the uploaded csv and ensure they are valid
        validated_sample_list = self.get_validated_sample_list()

        # 3. Create the two plates in memory
        from clarity_ext_scripts.covid.fetch_biobank_barcodes import FetchBiobankBarcodes
        fetch_biobank_barcodes = FetchBiobankBarcodes(self.context)
        barcode_by_sample =\
            fetch_biobank_barcodes.biobank_barcode_by_sample_referral_code()
        prext_plate = self.create_in_mem_container(validated_sample_list,
                                                   container_specifier="PREXT",
                                                   sample_specifier="",
                                                   control_specifier="",
                                                   date=date,
                                                   time=time)

        biobank_plate = self.create_in_mem_container(
            validated_sample_list,
            container_specifier="BIOBANK",
            sample_specifier="BIOBANK",
            control_specifier="BIOBANK",
            date=date,
            time=time,
            biobank_barcode_by_sample_referal_code=barcode_by_sample)

        # 4. Create the container and samples in clarity
        workflow = self.context.current_step.udf_assign_to_workflow
        prext_plate = self.context.clarity_service.create_container(
            prext_plate, with_samples=True, assign_to=workflow)
        biobank_plate = self.context.clarity_service.create_container(
            biobank_plate, with_samples=True)

        # 5. Add both containers to a UDF so they can be printed
        for plate in [prext_plate, biobank_plate]:
            container_log.append("{}:{}".format(plate.id, plate.name))

        self.context.current_step.udf_map.force(
            "Created containers", "\n".join(container_log))
        self.context.update(self.context.current_step)

    def integration_tests(self):
        yield self.test("24-46746", commit=True)
