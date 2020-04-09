import pytest
from clarity_ext_scripts.covid.label_printer import label_printer


class TestLabelPrinter(object):
    def test_single_container__with_lims_id_as_barcode(self):
        label_printer.printer.contents = list()
        container = FakeContainer('container1', '92-123')
        label_printer.generate_zpl_for_containers([container], lims_id_as_barcode=True)
        contents = label_printer.contents
        assert contents == "^XA^LH90,20^FO0,49^BY4^BCN,160,N,N,N^FD123^FS^FO308," \
                           "49^AB44,28^FB842,4,20,^FDcontainer1^FS^XZ"

    def test_two_containers__with_lims_id_as_barcode(self):
        label_printer.printer.contents = list()
        container1 = FakeContainer('container1', '92-123')
        container2 = FakeContainer('container2', '92-124')
        label_printer.generate_zpl_for_containers([container1, container2], lims_id_as_barcode=True)
        contents = label_printer.contents
        assert contents == "^XA^LH90,20^FO0,49^BY4^BCN,160,N,N,N^FD123^FS^FO308,49^AB44,28^FB842,4,20,"\
                           "^FDcontainer1^FS^XZ\n^XA^LH90,20^FO0,49^BY4^BCN,160,N,N,N^FD124^FS^FO308,"\
                           "49^AB44,28^FB842,4,20,^FDcontainer2^FS^XZ"

    def test_single_container__with_name_as_barcode(self):
        label_printer.printer.contents = list()
        container = FakeContainer('container1', '92-123')
        label_printer.generate_zpl_for_containers([container], lims_id_as_barcode=False)
        contents = label_printer.contents
        assert contents == "^XA^LH90,20^FO0,49^BY4^BCN,160,N,N,N^FDcontainer1^FS^FO616," \
                           "49^AB44,28^FB534,4,20,^FDcontainer1^FS^XZ"


class FakeContainer(object):
    def __init__(self, name, lims_id):
        self.name = name
        self.id = lims_id
