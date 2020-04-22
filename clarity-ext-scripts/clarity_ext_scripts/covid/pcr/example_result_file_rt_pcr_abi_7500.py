import xlwt
import collections
import datetime
import random
from clarity_ext.extensions import GeneralExtension
from clarity_ext_scripts.covid.parse_pcr import CT_HEADER


class Extension(GeneralExtension):
    def execute(self):
        file_handle_name = "Result file"
        timestamp = datetime.datetime.now().strftime("%y%m%dT%H%M%S")
        user = self.context.current_user

        file_name = "EXAMPLE-FILE_ABI7500_{}_{}.xls".format(user.initials, timestamp)
        wb = xlwt.Workbook()
        ws = wb.add_sheet('Results')

        self.create_upper_header_info(ws)

        table_row_start = 7
        column_index = 0

        # Creating the header of the table
        for key in self.create_row():
            ws.write(table_row_start, column_index, key)
            column_index += 1

        # Creating the content of the table
        for well in self.context.output_container:
            row = self.create_row(well, well.artifact)
            column_index = 0
            for key, value in row.items():
                ws.write(well.index_right_first +
                         table_row_start, column_index, value)
                column_index += 1

        full_path, file_handle = self.context.file_service.pre_queue(file_name, file_handle_name)
        wb.save(full_path)

        self.context.file_service.queue(full_path, file_handle)

    def create_row(self, well=None, artifact=None):
        header = collections.OrderedDict()
        header["Well"] = well.alpha_num_key if well else None
        header["Sample Name"] = artifact.name if artifact else None
        header["Target Name"] = artifact.name if artifact else None
        header["Task"] = "UNKNOWN" if artifact else None
        header["Reporter"] = "SYBR" if artifact else None
        header["Quencher"] = "None" if artifact else None
        header[CT_HEADER] = random.randint(0, 46) if artifact else None
        header[CT_HEADER + " Mean"] = random.randint(0, 40) if artifact else None
        header[CT_HEADER + " SD"] = "0.473177612" if artifact else None
        header["Quantity"] = "None" if artifact else None
        header["Quantity Mean"] = "None" if artifact else None
        header["Quantity SD"] = "None" if artifact else None
        header["Automatic Ct"] = "TRUE" if artifact else None
        header["Threshold"] = "0.134671769" if artifact else None
        header["Ct Threshold"] = "TRUE" if artifact else None
        header["Automatic Baseline"] = "None" if artifact else None
        header["Baseline Start"] = "3" if artifact else None
        header["Baseline End"] = "39" if artifact else None
        header["Tm1"] = "62.47861099" if artifact else None
        header["Tm2"] = "None" if artifact else None
        header["Tm3"] = "None" if artifact else None
        header["Comments"] = "None" if artifact else None
        header["NOAMP"] = "Y" if artifact else None
        header["EXPFAIL"] = "Y" if artifact else None

        return header

    def create_upper_header_info(self, ws):
        ws.write(0, 0, "Block Type")
        ws.write(1, 0, "Chemistry")
        ws.write(2, 0, "Experiment File Name")
        ws.write(3, 0, "Experiment Run End Time")
        ws.write(4, 0, "Instrument Type")
        ws.write(5, 0, "Passive Reference")

        ws.write(0, 1, "96fast")
        ws.write(1, 1, "SYBR_GREEN")
        ws.write(2, 1, "D:\Example.eds")
        ws.write(3, 1, "Not Started")
        ws.write(4, 1, "sds7500fast")
        ws.write(5, 1, "ROX")

    def integration_tests(self):
        yield self.test("24-43779", commit=False)
