from clarity_ext.extensions import GeneralExtension
from clarity_ext.service.file_service import Csv


class Extension(GeneralExtension):
    def execute(self):
        csv = Csv(delim='\t', newline='\n')
        csv.file_name = 'container_names.txt'
        for container in self.context.output_containers:
            csv.append([container.name])
        upload_packet = [(csv.file_name, csv.to_string(include_header=False))]
        self.context.file_service.upload_files("Print files", upload_packet)

    def integration_tests(self):
        yield "24-38734"