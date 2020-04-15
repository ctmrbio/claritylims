import re
import pandas as pd
from clarity_ext.extensions import GeneralExtension
from clarity_ext.utils import single
from clarity_ext.domain import Container, Sample


class Extension(GeneralExtension):
    def is_control(self, name):
        # Returns a control type if the name indicates that this is a control sample. Otherwise
        # returns None.
        for control_type, pattern in self.control_mapping.items():
            if pattern.match(name):
                return control_type
        return None

    def create_sample_or_control(self, original_name, project, index):
        sample_name_fmt = self.context.current_step.udf_sample_name
        control_name_fmt = self.context.current_step.udf_control_name

        control_type = self.is_control(original_name)

        name_fmt = control_name_fmt if control_type else sample_name_fmt
        name = format_name(original_name, index, name_fmt, self.context.start)
        sample_or_control = Sample(sample_id=None, name=name, project=project)
        sample_or_control.udf_map.force(
            "Control", "Yes" if control_type else "No")
        if control_type:
            sample_or_control.udf_map.force("Control type", control_type)
        return sample_or_control

    def execute(self):
        self.control_mapping = dict()
        for mapping in self.context.current_step.udf_control_mapping.split(","):
            map_from, map_to = mapping.split(":")
            self.control_mapping[map_to] = re.compile(map_from)

        # 0. Get the project
        project = self.context.clarity_service.get_project_by_name(
            self.context.current_step.udf_project)

        # 1. Create a 96 well plate in memory:
        container_type = self.context.current_step.udf_container_type
        container_name_fmt = self.context.current_step.udf_container_name
        name = format_name(None, 1, container_name_fmt, self.context.start)
        container = Container(container_type=container_type, name=name)

        # 2. Read the samples from the uploaded csv
        file_name = "Sample creation list"
        f = self.context.local_shared_file(file_name, mode="rb")
        data = pd.read_csv(f, encoding='utf-8')

        # 3. Create in-memory samples
        for ix, row in data.iterrows():
            original_name = row["name"]
            well = row["well"]
            sample_or_control = self.create_sample_or_control(
                original_name, project, ix)
            # This is required. TODO: What should it be?
            sample_or_control.udf_map.force("Sample Buffer", "None")
            container[well] = sample_or_control

        # 4. Create the container and samples in clarity
        workflow = self.context.current_step.udf_assign_to_workflow
        container = self.context.clarity_service.create_container(container,
                                                                  with_samples=True, assign_to=workflow)

    def integration_tests(self):
        yield "24-39257"


def format_name(basename, index, fmt, start):
    """
    Returns a name for the sample or container, based on the
    entry in the CSV file, given the format string.

    Supports:
        {name}: The name field in the csv file
        {date:fmt}: The date (at the start of executing this script)
        {index}: The running number of entities created in this batch, 1-based.
    """
    tags = re.findall(r"{.*?}", fmt)
    name = fmt
    for tag in tags:
        keyword = tag[1:-1]
        if ":" in keyword:
            keyword, extra_fmt = keyword.split(":")
        else:
            extra_fmt = None

        if keyword == "date":
            value = start.strftime(extra_fmt)
        elif keyword == "name":
            value = basename
        elif keyword == "index":
            value = str(index)
        else:
            raise AssertionError("Unknown format keyword {}".format(keyword))
        name = name.replace(tag, value)

    if "{" in name or "}" in name:
        raise AssertionError(
            "Format specifiers left in generated name: {}".format(name))

    return name
