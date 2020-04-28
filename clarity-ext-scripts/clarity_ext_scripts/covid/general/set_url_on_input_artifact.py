from clarity_ext.extensions import GeneralExtension


class Extension(GeneralExtension):
    def execute(self):
        for artifact in self.context.artifact_service.all_input_artifacts():

            _, step_id = artifact.parent_process.id.split("-", 1)
            path_to_step = "/clarity/work-complete/" + step_id
            import urlparse
            url = artifact.parent_process.uri

            parse_object = urlparse.urlparse(url)
            parse_object = parse_object._replace(path=path_to_step)

            url = parse_object.geturl()

            artifact.udf_map.force("Link to RT-PCR Step", url)

            self.context.update(artifact)

    def integration_tests(self):
        yield self.test("24-45313", commit=False)
