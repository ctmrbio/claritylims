"""
Extension for creating discarded samples from a validated file
"""

from clarity_ext.domain import Container, Sample
from clarity_ext_scripts.covid.utils import CtmrCovidSubstanceInfo
from clarity_ext_scripts.covid.import_samples import BaseCreateSamplesExtension


class Extension(BaseCreateSamplesExtension):
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

    @staticmethod
    def create_sample(original_name, timestamp, project, specifier, org_uri,
                      service_request_id):
        """
        Creates the sample in memory
        """
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
        sample.udf_map.force("Source", "KNM")
        sample.udf_map.force("Status", CtmrCovidSubstanceInfo.STATUS_DISCARD)

        return sample

    def create_in_mem_container(
            self, row, container_specifier, sample_specifier, date, time, container_running):
        """Creates an in-memory container with a single sample. Note that currently
        the container is a 96 well plate as a quick fix, it would make more sense to have a
        Tube.

        The name of the container will be on the form:

           COVID_<date>_<container_specifier>_<time to sec>

        The name of the sample will be:

            <name in csv>_<timestamp>_<sample_specifier>
        """
        timestamp = date + "T" + time

        # 1. Get the project
        project = self.context.clarity_service.get_project_by_name(
            self.context.current_step.udf_project)

        # 2. Create a plate in memory:
        container_type = "96 well plate"
        name = "COVID_{}_{}_{}_{}".format(
            date, container_specifier, time, container_running + 1)
        container = Container(container_type=container_type, name=name)

        # 3. Create in-memory sample
        original_name = row["Sample Id"]
        org_uri = row["org_uri"]
        service_request_id = row["service_request_id"]

        substance = self.create_sample(
            original_name, timestamp, project, sample_specifier, org_uri,
            service_request_id)
        substance.udf_map.force("Sample Buffer", "None")
        substance.udf_map.force("Step ID created in",
                                self.context.current_step.id)

        container.append(substance)
        return container

    def raise_if_already_created(self):
        """
        Raises an exception if the samples have already been created, indicated by that
        there exists a file on the file handle 'Created sample list'
        """
        try:
            created_sample_list_file = self.context.local_shared_file(
                "Created sample list", mode="rb")
            if created_sample_list_file:
                self.usage_error("Can't create samples more than once")
        except IOError:
            # We expect the file not to be there
            pass

    def execute(self):
        """
        Create discard samples based on a validated list of samples.
        """
        self.raise_if_already_created()

        start = self.context.start
        date = start.strftime("%y%m%d")
        time = start.strftime("%H%M%S")

        # 2. Read the samples from the uploaded csv and ensure they are valid
        validated_sample_list = self.get_validated_sample_list()

        # TODO: create a wrapper for this too
        created_sample_list = validated_sample_list.csv

        # 3. Create the plates in memory
        in_mem_containers = list()
        for index, row in created_sample_list.iterrows():
            plate = self.create_in_mem_container(row,
                                                 container_specifier="DISCARD",
                                                 sample_specifier="DISCARD",
                                                 date=date,
                                                 time=time,
                                                 container_running=index)
            in_mem_containers.append(plate)
            created_sample_list.loc[index, "plate_name"] = plate.name
            created_sample_list.loc[index,
                                    "sample_name"] = plate["A1"].artifact.name
        created_sample_list_content = created_sample_list.to_csv(
            index=False, sep=",")

        # 4. Create the container and samples in clarity
        workflow = self.context.current_step.udf_assign_to_workflow
        for in_mem_container in in_mem_containers:
            _ = self.context.clarity_service.create_container(
                in_mem_container, with_samples=True, assign_to=workflow)

        timestamp = start.strftime("%y%m%dT%H%M%S")
        file_name = "created_sample_list_{}.csv".format(timestamp)
        self.context.file_service.upload(
            "Created sample list", file_name, created_sample_list_content,
            self.context.file_service.FILE_PREFIX_NONE)

    def integration_tests(self):
        yield self.test("24-47148", commit=False)
