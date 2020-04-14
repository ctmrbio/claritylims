# -*- coding: utf-8 -*-
from clarity_ext.extensions import GeneralExtension
import xlwt
from datetime import datetime


class Extension(GeneralExtension):
    def execute(self):
        file_name = "Example.txt"
        file_handle = "Input file RT-PCR"

        wb = xlwt.Workbook()
        ws = wb.add_sheet('A Test Sheet')
        ws.write(2, 0, 1)
        ws.write(2, 1, 1)
        ws.write(2, 2, xlwt.Formula("A3+B3"))

        wb.save('Example.xls')

        file_name_with_content = [(file_name, "1234")]
        self.context.file_service.upload_files(file_handle, file_name_with_content)

    def integration_tests(self):
        yield self.test("24-39151", commit=False)
