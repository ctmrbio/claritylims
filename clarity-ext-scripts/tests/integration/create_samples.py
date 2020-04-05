# Creates a batch of samples in the COVID-19 project
#
# It would be beneficial to be able to batch post these entities 
# There is a batch put method in genologics, but I don't know how the instance should be created
# before using it
# because when creating an object with e.g. `c = Container()`
# it requires a uri or id
#
# Some results are cached between runs. Remove the file cache.sqlite in order to clear it

import logging
import itertools
from genologics.entities import Sample, Project, Container, Containertype, Artifact
from genologics.lims_utils import lims
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

project_name = "Test-Covid19"
workflow_name = "Test-Covid19"

# Hardcoding this uri for now:
plate_96_well = Containertype(lims,
        uri="https://ctmr-lims-stage.scilifelab.se/api/v2/containertypes/1") 

project = lims.get_projects(name=project_name)[0]
workflow = lims.get_workflows(name=workflow_name)[0]

def create_batch(pos, neg):
    """
    Creates a batch of `pos` positive samples and `neg` negative samples.

    Negative samples should be considered negative in the following tests and positive should
    be considered positive. There is no difference in the two except for the name.
    """
    assert 1 < pos + neg <= 96
    batch_id = datetime.now().strftime("%y%m%d_%H%M%S")

    container_name = "{}-cont-{}".format(project_name.lower(), batch_id)
    container = Container.create(lims, name=container_name, type=plate_96_well)
    simulated_results = [("pos", pos), ("neg", neg)]

    positions = ("{}:{}".format(i, j) for i, j in itertools.product("ABCDEFGH", range(1, 13)))

    created_artifacts = list()
    batch_ix = 1
    for result_type, num_of_result in simulated_results:
        for _ in range(num_of_result):
            sample_name = "{}-sample-{}-{}_{}".format(
                    project.name.lower(), result_type, batch_id, batch_ix)
            sample = Sample.create(lims,
                    container=container,
                    position=next(positions),
                    name=sample_name,
                    project=project,
                    udfs={"Control": "No",
                          "Sample Buffer": "None"})
            artifact = Artifact(lims, id=sample.id + "PA1")
            created_artifacts.append(artifact)
            batch_ix += 1
    lims.route_artifacts(created_artifacts, workflow_uri=workflow.uri)

create_batch(5, 5)

