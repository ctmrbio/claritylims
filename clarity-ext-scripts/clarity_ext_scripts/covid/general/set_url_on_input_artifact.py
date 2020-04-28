from clarity_ext.extensions import GeneralExtension
import urlparse
import socket


class Extension(GeneralExtension):
    def execute(self):
        for artifact in self.context.artifact_service.all_input_artifacts():

            _, step_id = artifact.parent_process.id.split("-", 1)
            path_to_step = "/clarity/work-complete/" + step_id
            
            url = artifact.parent_process.uri
            host_name = socket.getfqdn()
            if host_name == "c1-ctmr-lims-stage01.ki.se":
                server_domain = "ctmr-lims-stage.scilifelab.se"
            elif host_name == "c1-ctmr-lims-prod01.ki.se":
                server_domain = "ctmr-lims-prod.scilifelab.se"
            else:
                server_domain = urlparse.urlparse(url).netloc

            parse_object = urlparse.urlparse(url)
            parse_object = parse_object._replace(netloc=server_domain, path=path_to_step)

            url = parse_object.geturl()

            artifact.udf_map.force("Link to RT-PCR Step", url)

            self.context.update(artifact)

    def integration_tests(self):
        yield self.test("24-45334", commit=False)
