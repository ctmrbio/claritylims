# -*- coding: utf-8 -*-
from clarity_ext.extensions import GeneralExtension
import xlwt
import collections
import datetime
import random
CT_HEADER = u"Cт"


class Extension(GeneralExtension):
    def execute(self):
        file_handle = "Result file"
        today = datetime.date.today().strftime("%y%m%d")
        user = self.context.current_user

        file_name = "EXAMPLE-FILE_{}_{}.xls".format(user.initials, today)
        wb = xlwt.Workbook()
        ws = wb.add_sheet('Results')

        self.create_upper_header_info(ws)

        table_row_start = 7
        column_index = 0

        # Creating the header of the table
        for key in self.create_table():
            ws.write(table_row_start, column_index, key)
            column_index += 1

        column_index = 0
        # Creating the content of the table
        for well in self.context.output_container:
            for key in self.create_table():
                if well.artifact:
                    try:
                        ws.write(well.index_right_first + table_row_start, column_index, eval(self.create_table()[key]))
                    # When the value in the table is not a variable
                    except NameError:
                        ws.write(well.index_right_first + table_row_start, column_index, self.create_table()[key])
                # This is only used to create empty rows with well number i.e. A1
                else:
                    if key == "Well":
                        ws.write(well.index_right_first + table_row_start, column_index, eval(self.create_table()[key]))
                column_index += 1
            column_index = 0
            wb.save(file_name)

        full_path, file_handle = self.context.file_service.pre_queue(file_name, file_handle)
        wb.save(full_path)

        self.context.file_service.queue(file_name, file_handle)

    def create_table(self):
        header = collections.OrderedDict()
        header["Well"] = "well.alpha_num_key"
        header["Sample Name"] = "well.artifact.name"
        header["Target Name"] = "well.artifact.name"
        header["Task"] = "UNKNOWN"
        header["Reporter"] = "SYBR"
        header["Quencher"] = "None"
        header[CT_HEADER] = "random.randint(0,46)"
        header[CT_HEADER + " Mean"] = "random.randint(0,40)"
        header[CT_HEADER + " SD"] = "0.473177612"
        header["Quantity"] = "None"
        header["Quantity Mean"] = "None"
        header["Quantity SD"] = "None"
        header["Automatic Ct"] = "TRUE"
        header["Threshold"] = "0.134671769"
        header["Ct Threshold"] = "TRUE"
        header["Automatic Baseline"] = "None"
        header["Baseline Start"] = "3"
        header["Baseline End"] = "39"
        header["Tm1"] = "62.47861099"
        header["Tm2"] = "None"
        header["Tm3"] = "None"
        header["Comments"] = "None"
        header["NOAMP"] = "Y"
        header["EXPFAIL"] = "Y"

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
        yield self.test("24-39151", commit=False)
