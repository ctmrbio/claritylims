import logging
from clarity_ext.domain import Container, Sample
from clarity_ext_scripts.covid_seq.create_samples.common import BaseCreateSamplesExtension

logger = logging.getLogger(__name__)

class Extension(BaseCreateSamplesExtension):
    """
    Requires three step UDFs:
        * Assign to workflow: Any workflow
        * Project: Any project
        * Biobank plate id: The identifier of the "biobank plate" that is imported

    Creates two containers with samples and controls in Clarity:
        COVID_SEQ_<biobank_plate_id>_PREXT_<time>
            <sample_name_in_csv>_<region_code_in_csv>_<lab_code_in_csv>_<timestamp w sec>
            ...
        COVID_SEQ_<date>_BIOBANK_<time>
            <sample_name_in_csv>_<region_code_in_csv>_<lab_code_in_csv>_<timestamp w sec>_BIOBANK
            ...
    """

    def create_sample(self, sample_id, region_code, lab_code, 
            timestamp, project, specifier=""):
        name = [
            sample_id,
            region_code,
            lab_code,
            timestamp,
        ]
        if specifier:
            name.append(specifier)
        name = "_".join(str(component) for component in name if component)
        sample = Sample(sample_id=None, name=name, project=project)
        sample.udf_map.force("Control", "False")
        sample.udf_map.force("Sample Buffer", "None")

        return sample

    def create_in_mem_container(self, samplesheet, container_specifier, 
            sample_specifier, date, time):
        """Create an in-memory container with samples

        The name of the container will be on the form:

           COVID_SEQ_<biobank_plate_id>_<container_specifier>_<time to sec>

        The name of the samples will be:

           <sample_name_in_csv>_<region_code_in_csv>_<lab_code_in_csv>_<timestamp w sec>
        """
        timestamp = date + "T" + time

        # 1. Get the project name and biobank plate id from step UDFs
        project = self.context.clarity_service.get_project_by_name(
            self.context.current_step.udf_project)
        biobank_plate_id = self.context.current_step.udf_biobank_plate_id

        # 2. Create a 96 well plate in memory:
        container_type = "96 well plate"
        name = "COVID_SEQ_{}_{}_{}".format(
            biobank_plate_id, container_specifier, timestamp)
        container = Container(container_type=container_type, name=name)

        # 3. Create in-memory samples
        for _, row in samplesheet.csv.iterrows():
            well = row[samplesheet.COLUMN_WELL]
            sample_id = row[samplesheet.COLUMN_SAMPLE_ID]
            region_code = row[samplesheet.COLUMN_REGION_CODE]
            lab_code = row[samplesheet.COLUMN_LAB_CODE]
            selection_criteria = row[samplesheet.COLUMN_SELECTION_CRITERIA]
            selection_criteria_detail = row[samplesheet.COLUMN_SELECTION_CRITERIA_DETAIL]
            biobank_plate_id = row[samplesheet.COLUMN_BIOBANK_PLATE_ID]
            biobank_tube_id = row[samplesheet.COLUMN_BIOBANK_TUBE_ID]
            ct_values = [
                row[samplesheet.COLUMN_CT_1],
                row[samplesheet.COLUMN_CT_2],
                row[samplesheet.COLUMN_CT_3],
                row[samplesheet.COLUMN_CT_4],
                row[samplesheet.COLUMN_CT_5],
            ]

            substance = self.create_sample(
                sample_id, 
                region_code,
                lab_code,
                timestamp, 
                project, 
                sample_specifier,
            )
            substance.udf_map.force("Region code", region_code)
            substance.udf_map.force("Lab code", lab_code)
            substance.udf_map.force("Ct_1", str(ct_values[0]))
            substance.udf_map.force("Ct_2", str(ct_values[1]))
            substance.udf_map.force("Ct_3", str(ct_values[2]))
            substance.udf_map.force("Ct_4", str(ct_values[3]))
            substance.udf_map.force("Ct_5", str(ct_values[4]))
            substance.udf_map.force("Selection criteria", selection_criteria)
            substance.udf_map.force("Selection criteria detail", selection_criteria_detail)
            substance.udf_map.force("Biobank plate id", biobank_plate_id)
            substance.udf_map.force("Biobank tube id", biobank_tube_id)
            substance.udf_map.force(
                "Step ID created in", self.context.current_step.id)
            container[well] = substance
        return container

    def execute(self):
        """
        Creates samples from a validated import file
        """
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
        valid_biobank_plate_id = self.context.current_step.udf_biobank_plate_id
        validated_samplesheet = self.validate_samplesheet(valid_biobank_plate_id)

        # 3. Create the two plates in memory
        prext_plate = self.create_in_mem_container(
            validated_samplesheet,
            container_specifier="PREXT",
            sample_specifier="",
            date=date,
            time=time,
        )
        biobank_plate = self.create_in_mem_container(
            validated_samplesheet,
            container_specifier="BIOBANK",
            sample_specifier="BIOBANK",
            date=date,
            time=time,
        )

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
