
import socket

from clarity_ext.extensions import GeneralExtension
from genologics.config import BASEURI


class Extension(GeneralExtension):

    def execute(self):
        for artifact in self.context.artifact_service.all_input_artifacts():
            _, step_id = artifact.parent_process.id.split("-", 1)
            path_to_step = "/clarity/work-complete/" + step_id
            if "localhost" in BASEURI:
                domain = socket.getfqdn()
            else:
                domain = BASEURI
            clarity_full_path = domain + path_to_step
            artifact.udf_map.force("Link to RT-PCR Step", clarity_full_path)
            self.context.update(artifact)

    def integration_tests(self):
        yield self.test("24-44020", commit=False)
