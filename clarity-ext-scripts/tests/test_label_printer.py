from clarity_ext_scripts.covid.label_printer import label_printer


class TestLabelPrinter(object):

    def test_single_container__with_lims_id_as_barcode(self):
        label_printer.printer.contents = list()
        container = FakeContainer('container1', '92-123')
        label_printer.generate_zpl_for_containers(
            [container], lims_id_as_barcode=True)
        contents = label_printer.contents
        assert contents == "\n${^XA^LH0,0^FO7,5^BY1,^BCN,30,N,^FD123^FS^FO7,40^A0,32," \
                           "25^FB380,1,^FDcontainer1^FS^XZ}$\n"

    def test_two_containers__with_lims_id_as_barcode(self):
        label_printer.printer.contents = list()
        container1 = FakeContainer('container1', '92-123')
        container2 = FakeContainer('container2', '92-124')
        label_printer.generate_zpl_for_containers(
            [container1, container2], lims_id_as_barcode=True)
        contents = label_printer.contents
        assert contents == "\n${^XA^LH0,0^FO7,5^BY1,^BCN,30,N,^FD123^FS^FO7,40^A0,32,25^FB380," \
                           "^FDcontainer1^FS^XZ\n" \
                           "^XA^LH0,0^FO7,5^BY1,^BCN,30,N,^FD124^FS^FO7,40^A0,32,25^FB380," \
                           "^FDcontainer2^FS^XZ}$\n"

    def test_single_container__with_name_as_barcode(self):
        label_printer.printer.contents = list()
        container = FakeContainer('container1', '92-123')
        label_printer.generate_zpl_for_containers([container])
        contents = label_printer.contents
        assert contents == "\n${^XA^LH0,0^FO7,5^BY1,^BCN,30,N,^FDcontainer1^FS^FO7," \
                           "40^A0,32,25^FB380,1,^FDcontainer1^FS^XZ}$\n"

    def test_dmitry_barcode(self):
        label_printer.printer.contents = list()
        container = FakeContainer('27-7277', '92-7277')
        label_printer.generate_zpl_for_containers(
            [container], lims_id_as_barcode=True)
        contents = label_printer.contents
        assert contents == "\n${^XA^LH0,0^FO7,5^BY1,^BCN,30,N,^FD7277^FS^FO7,40^A0," \
                           "32,25^FB380,1,^FD27-7277^FS^XZ}$\n"

    def test_with_long_container_name__lims_id_as_barcode(self):
        label_printer.printer.contents = list()
        container = FakeContainer('COVID_200416_RNA_144401.v1', '92-727789')
        label_printer.generate_zpl_for_containers(
            [container], lims_id_as_barcode=True)
        contents = label_printer.contents
        assert contents == "\n${^XA^LH0,0^FO7,5^BY1,^BCN,30,N,^FD727789^FS^FO7," \
                           "40^A0,32,25^FB380,1,^FDCOVID_200416_RNA_144401.v1^FS^XZ}$\n"

    def test_with_long_container_name__name_as_barcode(self):
        label_printer.printer.contents = list()
        container = FakeContainer(
            'COVID_200416_RNA_144401.v1', '92-727789')
        label_printer.generate_zpl_for_containers([container])
        contents = label_printer.contents
        assert contents == "\n${^XA^LH0,0^FO7,5^BY1,^BCN,30,N,^FDCOVID_200416_RNA_144401.v1^FS^FO7," \
                           "40^A0,32,25^FB380,1,^FDCOVID_200416_RNA_144401.v1^FS^XZ}$\n"


class FakeContainer(object):
    def __init__(self, name, lims_id):
        self.name = name
        self.id = lims_id
