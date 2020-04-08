from clarity_ext.extensions import GeneralExtension
from clarity_ext.service.file_service import Csv
from clarity_ext.domain.validation import UsageError


class Extension(GeneralExtension):
    def execute(self):
        upload_packets = list()
        max_number_of_lists = 5  # TODO: decide max number, perhaps it is just 1 anyway?
        if len(self.context.output_containers) > max_number_of_lists:
            raise UsageError('The allowed max number of plates is currently set to {},'
                             ' please contact system administrator'.format(max_number_of_lists))
        for container in self.context.output_containers:
            csv = Csv(delim='\t', newline='\n')
            csv.file_name = 'sample_list_{}.txt'.format(container.name)
            for well in container.occupied:
                artifact = well.artifact
                csv.append([artifact.name, well.index_down_first])
            upload_packet = (csv.file_name, csv.to_string(include_header=False))
            upload_packets.append(upload_packet)
        self.context.file_service.upload_files("Sample list", upload_packets)

    def integration_tests(self):
        yield "24-38734"