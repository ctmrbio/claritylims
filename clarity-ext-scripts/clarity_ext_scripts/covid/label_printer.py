import re


class LabelPrinterService(object):
    """Defines the business rules for printing to a label printer"""

    HEIGHT_SHORT = 80
    HEIGHT_MEDIUM = 120
    HEIGHT_TALL = 160
    HEIGHT_CUSTOM = 48

    WIDTH_NARROW = 4
    WIDTH_WIDE = 6
    WIDTH_CUSTOM = 2

    def __init__(self, printer):
        self.printer = printer

    def generate_zpl_for_containers(self, containers, lims_id_as_barcode=False):
        """
        Print out labels for all listed containers, using container name as barcode.
        Inserts newline in name string according to SNP&SEQ barcode policy (newline
        before plate id)
        :param containers: An unique list of containers
        :return:
        """
        for c in containers:
            if lims_id_as_barcode:
                # Remove the prefix part of lims id
                barcode = c.id.split("-", 1)[1]
            else:
                barcode = c.name
            self.generate_zpl_for_container(name=c.name, barcode=barcode)

    def generate_zpl_for_container(self, name, barcode):
        """Prints a default bar code label for a container"""
        offset = (0, 0)
        print_info = LabelPrintInfo(name, barcode, self.HEIGHT_CUSTOM,
                                    self.WIDTH_CUSTOM, offset, LabelPrintInfo.POS_RIGHT)
        self.append_contents(print_info)

    def generate_zpl_for_control(self, name, barcode):
        self.generate_zpl_for_container(name, barcode)

    def append_contents(self, label_print_info):
        """Prints to the registered printer, using a LabelPrintInfo"""
        self.printer.append_contents(label_print_info)

    @property
    def contents(self):
        content = '\n'.join(self.printer.contents)
        content = ''.join(["\n", "${", content, "}$", "\n"])
        return content

    @staticmethod
    def create():
        return LabelPrinterService(LabelPrinterService.create_printer())

    @staticmethod
    def create_printer():
        # Creates the default production version of a printer:
        return ZebraLabelPrinter(font="L", zoom_factor=1, vertical_spacing=1,
                                 block_width_points=850, label_width_points=1240, text_max_lines=1,
                                 space_points=20, chars_per_line=28)


class LabelPrintInfo(object):
    POS_RIGHT = 1
    POS_TOP = 2

    """Represents what to print, not related to any particular printer"""

    def __init__(self, text, barcode, height, width, offset, position):
        """
        :param text: The label's text
        :param barcode: The barcode
        :param height: Height of the label
        :param width: Module width of barcode (narrow line width used as a base unit for barcode sizing)
        :param offset: Offset as an (x, y) tuple
        :param position: Either POS_RIGHT, for aligning the text to the right of the barcode or POS_TOP.
        """
        self.text = text                # container name
        self.barcode = barcode
        self.height = height            # LabelPrinterService.HEIGHT_CUSTOM = 30
        self.width = width              # LabelPrinterService.WIDTH_CUSTOM = 2
        self.offset = offset            # (0, 0)
        self.position = position        # self.POS_RIGHT = 1


class ZebraLabelPrinter(object):
    """Specifies both the file format needed for this printer as well as the communication mechanism"""
    
    FONT_SIZES = {
        "A": (5, 9), "B": (7, 11), "C": (10, 18), "D": (10, 18), "E": (15, 28), 
        "F": (13, 26), "G": (40, 60), "H": (13, 21), "J": (25, 32), "L": (20,25)
    }

    def __init__(self, font, zoom_factor, vertical_spacing, block_width_points, label_width_points,
                 text_max_lines, space_points, chars_per_line):
        self.font = font                                    # L
        self.zoom_factor = zoom_factor                      # 1
        self.vertical_spacing = vertical_spacing            # 1
        self.block_width_points = block_width_points        # 850
        # the length of the label in points for easy calc of positions
        self.label_width_points = label_width_points        # 1240

        self.text_max_lines = text_max_lines                # 1
        self.space_points = space_points                    # 20
        self.chars_per_line = chars_per_line                # 28
        self.contents = list()

    def append_contents(self, info):
        self.contents.append(self.parse(info))

    def _parse(self, info):
        text_width, text_height = self.FONT_SIZES[self.font]                # (20, 25) self.FONT_SIZES['K']
        text_width, text_height = text_width * self.zoom_factor, text_height * self.zoom_factor
        first_row_offset = (7, self.vertical_spacing)                       # (7, 1)
        second_row_offset = (7, info.height + 7*self.vertical_spacing)      # (7, 48 + 7 * 1)

        yield "^XA"
        yield "^LH{},{}".format(*info.offset)                               # (0, 0)
        yield "^FO{},{}".format(*first_row_offset)                          # (7, 1)
        yield "^BY1.6,"
        yield "^BCN,{},N,".format(info.height)
        yield "^FD{}^FS".format(info.barcode)

        yield "^FO{},{}".format(*second_row_offset)
        yield "^A0,{},{}".format(text_height, text_width)
        # Labels 50x9 mm can't have more than 380 points width per field (Under default dpi). Fields are always 1 line, line spacing is senseless in this case
        yield "^FB380,1,"
        # use built in linebreak functionality for bulk of string
        yield "^FD{}^FS".format(self.replace_newlines(info.text))
        yield "^XZ"

    def replace_newlines(self, text):
        return text.replace("\n", "\&")

    def split_text(self, text, new_line, characters_per_line):
        # NOTE: This could be replaced with textwrap.wrap, but not doing that right away since this
        # is a direct port from Chiasma (textwrap.wrap removes trailing spaces).
        def chunks(seq, n):
            while seq:
                yield seq[:n]
                seq = seq[n:]
        return new_line.join(chunks(text, characters_per_line))

    def parse(self, info):
        # TODO: Test printing several labels too
        return "".join(self._parse(info))


# Provide a default label_printer so it can be easily used in extensions:
label_printer = LabelPrinterService.create()
