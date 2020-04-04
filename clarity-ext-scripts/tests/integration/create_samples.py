# Creates a batch of samples in the COVID-19 project
#
# It would be beneficial to be able to batch post these entities 
# There is a batch put method in genologics, but
# I don't know how the instance should be created before using it
# because when creating an object with e.g. `c = Container()`
# it requires a uri or id

import logging
import itertools
from genologics.entities import Sample, Project, Container, Containertype
from genologics.lims_utils import lims
from datetime import datetime

logger = logging.getLogger(__name__)

# Hardcoding this uri for now:
plate_96_well = Containertype(lims,
        uri="https://ctmr-lims-stage.scilifelab.se/api/v2/containertypes/1") 

# We assume for now that we get the samples in on a 96 well plate
project_name = "Test-Covid19"
batch_id = datetime.now().isoformat()
container_name = "{}-cont-{}".format(project_name.lower(), batch_id)
container = Container.create(lims, name=container_name, type=plate_96_well)

# TODO: Is there a method for this in genologics that doesn't
# iterate over all projects?
def find_project_by_name(name):
    for project in lims.get_projects():
        if project.name.startswith(name):
            return project

simulated_results = [("pos", 5), ("neg", 5)]
logger.info("Finding project...")
project = find_project_by_name("Test-Covid19")

positions = ("{}:{}".format(i, j) for i, j in itertools.product("ABCDEFGH", range(1, 13)))

for result_type, num_of_result in simulated_results:
    for ix in range(num_of_result):
        sample_name = "{}-sample-{}-{}-{}".format(
                project.name.lower(), result_type, batch_id, ix + 1)
        sample = Sample.create(lims,
                container=container,
                position=next(positions),
                name=sample_name,
                project=project,
                udfs={"Control": "No",
                      "Sample Buffer": "None"})
