import re
import pandas as pd
from clarity_ext.extensions import GeneralExtension
from clarity_ext.utils import single
from clarity_ext.domain import Container, Sample

POSITIVE_PLASMID_CONTROL = "positive plasmid control"
NEGATIVE_WATER_CONTROL = "negative water control"
POSITIVE_VIRUS_CONTROL = "positive virus control"

CONTROLS_IN_CSV = {
    POSITIVE_PLASMID_CONTROL,
    NEGATIVE_WATER_CONTROL,
    POSITIVE_VIRUS_CONTROL,
}


class Extension(GeneralExtension):
    """
    Requires two step UDFs:
        * Assign to workflow: Any workflow 
        * Project: Any project

    Requires a CSV file with the headers barcode;well 


    Creates two containers with samples and controls in Clarity:
        COVID_PREXT_<timestamp> 
            <sample_name_in_csv>_<timestamp w sec>
            <control_name_in_csv>_<timestamp w sec>_<running>  
            ...
        COVID_BIOBANK_<timestamp> 
            <sample_name_in_csv>_<timestamp w sec>_BIOBANK
            <control_name_in_csv>_<timestamp w sec>_<running>_BIOBANK
            ...

    The <running> part of the names is a running number for controls.
    """

    def create_sample(self, original_name, timestamp, project, specifier):
        name = map(str, [original_name, timestamp])
        if specifier:
            name.append(specifier)
        name = "_".join(name)
        sample = Sample(sample_id=None, name=name, project=project)
        sample.udf_map.force("Control", "No")
        return sample

    def create_control(self, original_name, control_type, timestamp,
            running_number, project, specifier):
        name = map(str, [original_name, timestamp, running_number])
        if specifier:
            name.append(specifier)
        name = "_".join(name)
        control = Sample(sample_id=None, name=name, project=project)
        control.udf_map.force("Control", "Yes")
        control.udf_map.force("Control type", control_type)
        return control

    def create_in_mem_container(
            self, csv, container_specifier, sample_specifier, control_specifier, timestamp):
        """Creates an in-memory container with the samples
        
        The name of the container will be on the form:
            
           COVID_<container_specifier>_<timestamp> 

        The name of the samples will be:

            <name in csv>_<timestamp>_<sample_specifier>

        The name of the controls will be on the form:

            <name in csv>_<timestamp>_<control_specifier>
        """
        # 1. Get the project
        project = self.context.clarity_service.get_project_by_name(
            self.context.current_step.udf_project)

        # 2. Create a 96 well plate in memory:
        container_type = "96 well plate"
        name = "COVID_{}_{}".format(container_specifier, timestamp)
        container = Container(container_type=container_type, name=name)

        # 3. Create in-memory samples
        control_running = 0
        for ix, row in csv.iterrows():
            original_name = row["barcode"]
            well = row["well"]
            control_type = original_name if original_name in CONTROLS_IN_CSV else None
            if control_type:
                control_running += 1
                substance = self.create_control(
                    original_name, control_type, timestamp,
                    control_running, project, control_specifier)
            else:
                substance = self.create_sample(
                    original_name, timestamp, project, sample_specifier)
            substance.udf_map.force("Sample Buffer", "None")
            container[well] = substance
        return container

    def execute(self):
        timestamp = self.context.start.strftime("%Y%m%dT%H%M%S")

        # 1. Read the samples from the uploaded csv
        file_name = "Sample creation list"
        f = self.context.local_shared_file(file_name, mode="rb")
        csv = pd.read_csv(f, encoding="utf-8", sep=";")

        prext_plate = self.create_in_mem_container(csv,
                                                   container_specifier="PREXT",
                                                   sample_specifier="",
                                                   control_specifier="",
                                                   timestamp=timestamp)

        biobank_plate = self.create_in_mem_container(csv,
                                                     container_specifier="BIOBANK",
                                                     sample_specifier="BIOBANK",
                                                     control_specifier="BIOBANK",
                                                     timestamp=timestamp)

        # 4. Create the container and samples in clarity
        workflow = self.context.current_step.udf_assign_to_workflow
        self.context.clarity_service.create_container(
            prext_plate, with_samples=True, assign_to=workflow)
        self.context.clarity_service.create_container(
            biobank_plate, with_samples=True)

    def integration_tests(self):
        yield "24-39260"
