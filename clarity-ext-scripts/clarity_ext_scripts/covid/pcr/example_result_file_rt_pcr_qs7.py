import xlwt
import collections
import datetime
import random
from clarity_ext.extensions import GeneralExtension


class Extension(GeneralExtension):
    def execute(self):
        file_handle_name = "Result file"
        timestamp = datetime.datetime.now().strftime("%y%m%dT%H%M%S")
        user = self.context.current_user

        file_name = "EXAMPLE-FILE_QS7_{}_{}.xls".format(user.initials, timestamp)
        wb = xlwt.Workbook()
        ws = wb.add_sheet('Results')
        self.create_upper_header_info(ws)

        table_row_start = 42
        column_index = 0

        # Creating the header of the table
        for key in self.create_first_row():
            ws.write(table_row_start, column_index, key)
            column_index += 1
        counter_first_row = 1
        counter_second_row = 2
        # Creating the content of the table
        for well in self.context.output_container:
            first_row = self.create_first_row(well, well.artifact)
            second_row = self.create_second_row(well, well.artifact)
            column_index = 0
            counter_first_row = self.populate_table(column_index, table_row_start, first_row, counter_first_row, ws)

            counter_second_row = self.populate_table(column_index, table_row_start, second_row, counter_second_row, ws)

        full_path, file_handle = self.context.file_service.pre_queue(file_name, file_handle_name)
        wb.save(full_path)

        self.context.file_service.queue(full_path, file_handle)

    def populate_table(self, column_index, table_row_start, row, counter_row, ws):
        for key, value in row.items():
            ws.write(counter_row + table_row_start, column_index, value)
            column_index += 1
        counter_row += 2
        return counter_row

    def create_first_row(self, well=None, artifact=None):

        header = collections.OrderedDict()
        header["Well"] = well.index_down_first if well else None
        header["Well Position"] = well.alpha_num_key if artifact else None
        header["Omit"] = "FALSE"
        header["Sample Name"] = artifact.name if artifact else None
        header["Target Name"] = "NCoV Orf1ab"
        header["Task"] = self.task(artifact) if artifact else None if artifact else None
        header["Reporter"] = "FAM" if artifact else None
        header["Quencher"] = "None"
        header["CT"] = self.random_number(artifact)if artifact else None
        header["Ct Mean"] = self.random_number(artifact)if artifact else None
        header["Ct SD"] = None
        header["Quantity"] = None
        header["Quantity Mean"] = None
        header["Quantity SD"] = None
        header["Y-Intercept"] = None
        header["R(superscript 2)"] = None
        header["Slope"] = None
        header["Efficiency"] = None
        header["Automatic Ct Threshold"] = "FALSE"
        header["Ct Threshold"] = "188 495.138"
        header["Automatic Baseline"] = "TRUE"
        header["Baseline Start"] = "1"
        header["Baseline End"] = random.randint(0, 15)
        header["Comments"] = None
        return header

    def create_second_row(self, well=None, artifact=None):

        header = collections.OrderedDict()
        header["Well"] = well.index_down_first if well else None
        header["Well Position"] = well.alpha_num_key if artifact else None
        header["Omit"] = "FALSE"
        header["Sample Name"] = artifact.name if artifact else None
        header["Target Name"] = "RNaseP"
        header["Task"] = self.task(artifact) if artifact else None
        header["Reporter"] = "VIC" if artifact else None
        header["Quencher"] = "None"
        header["CT"] = self.random_number(artifact) if artifact else None
        header["Ct Mean"] = self.random_number(artifact)if artifact else None
        header["Ct SD"] = None
        header["Quantity"] = None
        header["Quantity Mean"] = None
        header["Quantity SD"] = None
        header["Y-Intercept"] = None
        header["R(superscript 2)"] = None
        header["Slope"] = None
        header["Efficiency"] = None
        header["Automatic Ct Threshold"] = "FALSE"
        header["Ct Threshold"] = "39 589.086"
        header["Automatic Baseline"] = "FALSE"
        header["Baseline Start"] = "3"
        header["Baseline End"] = random.randint(0, 15)
        header["Comments"] = None

        return header

    def task(self, artifact):
        if artifact.name.lower().startswith("negative"):
            return "NTC"
        else:
            return "UNKNOWN"

    def random_number(self, artifact):
        if artifact.name.lower().startswith("negative"):
            return random.randint(0, 1)
        elif artifact.name.lower().startswith("positive"):
            return random.randint(30, 40)
        else:
            return random.randint(0, 40)

    def create_upper_header_info(self, ws):
        ws.write(0, 0, "Block Type")
        ws.write(1, 0, "Calibration Background is expired ")
        ws.write(2, 0, "Calibration Background performed on")
        ws.write(3, 0, "Calibration Normalization FAM-ROX is expired")
        ws.write(4, 0, "Calibration Normalization FAM-ROX performed on")
        ws.write(5, 0, "Calibration Normalization VIC-ROX is expired")
        ws.write(6, 0, "Calibration Normalization VIC-ROX performed on")
        ws.write(7, 0, "Calibration Pure Dye CY5 is expired")
        ws.write(8, 0, "Calibration Pure Dye CY5 performed on")
        ws.write(9,  0, "Calibration Pure Dye FAM is expired")
        ws.write(10, 0, "Calibration Pure Dye FAM performed on")
        ws.write(11, 0, "Calibration Pure Dye NED is expired")
        ws.write(12, 0, "Calibration Pure Dye NED performed on")
        ws.write(13, 0, "Calibration Pure Dye ROX is expired")
        ws.write(14, 0, "Calibration Pure Dye ROX performed on")
        ws.write(15, 0, "Calibration Pure Dye SYBR is expired")
        ws.write(16, 0, "Calibration Pure Dye SYBR performed on")
        ws.write(17, 0, "Calibration Pure Dye TAMRA is expired")
        ws.write(18, 0, "Calibration Pure Dye TAMRA performed on")
        ws.write(19, 0, "Calibration Pure Dye VIC is expired")
        ws.write(20, 0, "Calibration Pure Dye VIC performed on")
        ws.write(21, 0, "Calibration ROI is expired ")
        ws.write(22, 0, "Calibration ROI performed on")
        ws.write(23, 0, "Calibration Uniformity is expired ")
        ws.write(24, 0, "Calibration Uniformity performed on")
        ws.write(25, 0, "Chemistry")
        ws.write(26, 0, "Date Created")
        ws.write(27, 0, "Experiment Barcode")
        ws.write(28, 0, "Experiment Comment")
        ws.write(29, 0, "Experiment File Name")
        ws.write(30, 0, "Experiment Name")
        ws.write(31, 0, "Experiment Run End Time")
        ws.write(32, 0, "Experiment Type")
        ws.write(33, 0, "Instrument Name")
        ws.write(34, 0, "Instrument Serial Number")
        ws.write(35, 0, "Instrument Type")
        ws.write(36, 0, "Passive Reference")
        ws.write(37, 0, "Quantification Cycle Method")
        ws.write(38, 0, "Signal Smoothing On")
        ws.write(39, 0, "Stage/ Cycle where Analysis is performed")
        ws.write(40, 0, "User Name")
        
        ws.write(0, 1, "96-Well Block (0.2mL)")
        ws.write(1, 1, "No")
        ws.write(2, 1, "02-18-2020")
        ws.write(3, 1, "No")
        ws.write(4, 1, "02-18-2020")
        ws.write(5, 1, "No")
        ws.write(6, 1, "02-18-2020")
        ws.write(7, 1, "Yes")
        ws.write(8, 1, "01-10-2019")
        ws.write(9, 1, "No")
        ws.write(10, 1, "02-18-2020")
        ws.write(11, 1, "No")
        ws.write(12, 1, "02-18-2020")
        ws.write(13, 1, "No")
        ws.write(14, 1, "02-18-2020")
        ws.write(15, 1, "No")
        ws.write(16, 1, "02-18-2020")
        ws.write(17, 1, "No")
        ws.write(18, 1, "02-18-2020")
        ws.write(19, 1, "No")
        ws.write(20, 1, "02-18-2020")
        ws.write(21, 1, "No")
        ws.write(22, 1, "02-18-2020")
        ws.write(23, 1, "No")
        ws.write(24, 1, "02-18-2020")
        ws.write(25, 1, "TAQMAN")
        ws.write(26, 1, "2020-04-17 17:04:37 PM CEST")
        ws.write(27, 1, "")
        ws.write(28, 1, "")
        ws.write(29, 1, "D:\\file.eds")
        ws.write(30, 1, "2020-04-17 140736")
        ws.write(31, 1, "2020-04-17 17:38:24 PM CEST")
        ws.write(32, 1, "Standard Curve")
        ws.write(33, 1, "278870044")
        ws.write(34, 1, "278870044")
        ws.write(35, 1, "QuantStudio(TM) 7 Flex System")
        ws.write(36, 1, "")
        ws.write(37, 1, "Ct")
        ws.write(38, 1, "true")
        ws.write(39, 1, "Stage 2, Step 2")
        ws.write(40, 1, "")

    def integration_tests(self):
        yield self.test("24-43779", commit=False)
