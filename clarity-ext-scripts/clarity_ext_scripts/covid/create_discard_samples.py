import pandas as pd
from clarity_ext.extensions import GeneralExtension
from clarity_ext.domain import Container, Sample
from clarity_ext_scripts.covid.controls import controls_barcode_generator, Controls
from clarity_ext_scripts.covid.partner_api_client import PartnerAPIV7Client, ORG_URI_BY_NAME, KARLSSON_AND_NOVAK, \
    ServiceRequestAlreadyExists, CouldNotCreateServiceRequest

class Extension(GeneralExtension):
    """
    Requires two step UDFs:
        * Assign to workflow: Any workflow
        * Project: Any project

    Requires a CSV file with the headers barcode;well


    Creates two containers with samples and controls in Clarity:
        COVID_<date>_PREXT_<time>
            <sample_name_in_csv>_<timestamp w sec>
            <control_name_in_csv>_<timestamp w sec>_<running>
            ...
        COVID_<date>_BIOBANK_<time>
            <sample_name_in_csv>_<timestamp w sec>_BIOBANK
            <control_name_in_csv>_<timestamp w sec>_<running>_BIOBANK
            ...

    The <running> part of the names is a running number for controls.
    """

    def create_sample(self, original_name, timestamp, project, specifier, org_uri, service_request_id):
        name = map(str, [original_name, timestamp])
        if specifier:
            name.append(specifier)
        name = "_".join(name)
        sample = Sample(sample_id=None, name=name, project=project)
        sample.udf_map.force("Control", "No")

        # Add KNM data:test_partner_user
        sample.udf_map.force("KNM data added at", timestamp)
        sample.udf_map.force("KNM org URI", org_uri)
        sample.udf_map.force("KNM service request id", service_request_id)

        return sample

    def create_in_mem_container(
            self, row, container_specifier, sample_specifier, date, time):
        """Creates an in-memory container with the samples

        The name of the container will be on the form:

           COVID_<date>_<container_specifier>_<time to sec>

        The name of the samples will be:

            <name in csv>_<timestamp>_<sample_specifier>

        The name of the controls will be on the form:

            <name in csv>_<timestamp>_<control_specifier>
        """
        timestamp = date + "T" + time

        # 1. Get the project
        project = self.context.clarity_service.get_project_by_name(
            self.context.current_step.udf_project)

        # 2. Create a Tube in memory:
        container_type = "Tube"
        name = "COVID_{}_{}_{}".format(date, container_specifier, time)
        container = Container(container_type=container_type, name=name)

        # 3. Create in-memory samples
        for ix, row in csv.iterrows():
            original_name = row["reference"]
            org_uri = row["org_uri"]
            service_request_id = row["service_request_id"]

            substance = self.create_sample(
                original_name, timestamp, project, sample_specifier, org_uri,
                service_request_id)
            substance.udf_map.force("Sample Buffer", "None")
            substance.udf_map.force("Step ID created in", self.context.current_step.id)
            container[well] = substance
        return container

    def _create_anonymous_service_request(self, client, referral_code):
        try:
            service_request_id = client.create_anonymous_service_request(
                referral_code)
            return service_request_id
        except CouldNotCreateServiceRequest:
            self.usage_error_defer(
                ("Could not create ServiceRequests for the following barcode(s). KNM probably did not "
                 "recognize them. Please investigate the barcode(s)."), referral_code)
        except ServiceRequestAlreadyExists:
            self.usage_error_defer(
                ("There already exists a ServiceRequest for the following barcode(s). This means something "
                 "odd is going on. Maybe you set a sample to anonymous in the 'Validated sample list', that should not "
                 "have been set to anonymous? Contact your friendly sysadmin for help."), referral_code)

    def execute(self):
        config = {
            key: self.config[key]
            for key in [
                "test_partner_base_url", "test_partner_code_system_base_url",
                "test_partner_user", "test_partner_password"
            ]
        }
        client = PartnerAPIV7Client(**config)

        # This is for debug reasons only. Set this to True to create samples even if they have
        # been created before. This will overwrite the field udf_created_containers.
        force = False

        start = self.context.start
        date = start.strftime("%y%m%d")
        time = start.strftime("%H%M%S")

        # 2. Read the samples from the uploaded csv and ensure they are valid
        file_name = "Validated sample list"
        f = self.context.local_shared_file(file_name, mode="rb")
        csv = pd.read_csv(f, encoding="utf-8", sep=",", dtype=str)

        print(csv)

        errors = list()
        for ix, row in csv.iterrows():
            if row["status"] != "discard":
                errors.append(row["reference"])

        if len(errors):
            msg = "There are {} samples which are not marked as 'discard' in the sample list. " \
                "Check the file 'Validated sample list' for details".format(
                    len(errors))
            self.usage_error(msg)

        # 3. Create the two plates in memory
        for ix, row in csv.iterrows():
            print(ix, row)
            tube = self.create_in_mem_container(row,
                                                   container_specifier="DISCARD",
                                                   sample_specifier="",
                                                   date=date,
                                                   time=time)
            print(tube)
        return
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
        yield self.test("24-45963", commit=False)
