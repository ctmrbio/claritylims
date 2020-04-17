from clarity_ext_scripts.covid.label_printer import label_printer


class TestLabelPrinter(object):
    def test_single_container__with_lims_id_as_barcode(self):
        label_printer.printer.contents = list()
        container = FakeContainer('container1', '92-123')
        label_printer.generate_zpl_for_containers([container], lims_id_as_barcode=True)
        contents = label_printer.contents
        assert contents == "^XA^LH0,0^FO10,5^BY2^BCN,30,N,N,N^FD123^FS^FO10,40^A0,32," \
                           "25^FB1086,4,20,^FDcontainer1^FS^XZ"

    def test_two_containers__with_lims_id_as_barcode(self):
        label_printer.printer.contents = list()
        container1 = FakeContainer('container1', '92-123')
        container2 = FakeContainer('container2', '92-124')
        label_printer.generate_zpl_for_containers([container1, container2], lims_id_as_barcode=True)
        contents = label_printer.contents
        assert contents == "^XA^LH0,0^FO10,5^BY2^BCN,30,N,N,N^FD123^FS^FO10,40^A0,32,25^FB1086,4,20," \
                           "^FDcontainer1^FS^XZ\n" \
                           "^XA^LH0,0^FO10,5^BY2^BCN,30,N,N,N^FD124^FS^FO10,40^A0,32,25^FB1086,4,20," \
                           "^FDcontainer2^FS^XZ"

    def test_single_container__with_name_as_barcode(self):
        label_printer.printer.contents = list()
        container = FakeContainer('container1', '92-123')
        label_printer.generate_zpl_for_containers([container], lims_id_as_barcode=False)
        contents = label_printer.contents
        assert contents == "^XA^LH0,0^FO10,5^BY2^BCN,30,N,N,N^FDcontainer1^FS^FO10," \
                           "40^A0,32,25^FB932,4,20,^FDcontainer1^FS^XZ"

    def test_dmitry_barcode(self):
        label_printer.printer.contents = list()
        container = FakeContainer('27-7277', '92-7277')
        label_printer.generate_zpl_for_containers([container], lims_id_as_barcode=True)
        contents = label_printer.contents
        assert contents == "^XA^LH0,0^FO10,5^BY2^BCN,30,N,N,N^FD7277^FS^FO10,40^A0," \
                           "32,25^FB1064,4,20,^FD27-7277^FS^XZ"

    def test_with_long_container_name__lims_id_as_barcode(self):
        label_printer.printer.contents = list()
        container = FakeContainer('COVID_200416_RNA_144401.v1', '92-727789')
        label_printer.generate_zpl_for_containers([container], lims_id_as_barcode=True)
        contents = label_printer.contents
        assert contents == "^XA^LH0,0^FO10,5^BY2^BCN,30,N,N,N^FD727789^FS^FO10," \
                           "40^A0,32,25^FB1020,4,20,^FDCOVID_200416_RNA_144401.v1^FS^XZ"

    def test_with_long_container_name__name_as_barcode(self):
        label_printer.printer.contents = list()
        container = FakeContainer('COVID_200416_PREXT_144401', 'COVID_200416_PREXT_144401')
        label_printer.generate_zpl_for_containers([container], lims_id_as_barcode=False)
        contents = label_printer.contents
        assert contents == "^XA^LH0,0^FO10,5^BY2^BCN,30,N,N,N^FDCOVID_200416_PREXT_144401^FS^FO10," \
                           "40^A0,32,25^FB602,4,20,^FDCOVID_200416_PREXT_144401^FS^XZ"


class FakeContainer(object):
    def __init__(self, name, lims_id):
        self.name = name
        self.id = lims_id
