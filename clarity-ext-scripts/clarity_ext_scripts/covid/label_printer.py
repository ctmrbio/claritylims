import re


class LabelPrinterService:
    """Defines the business rules for printing to a label printer"""

    HEIGHT_SHORT = 80
    HEIGHT_MEDIUM = 120
    HEIGHT_TALL = 160

    WIDTH_NARROW = 4
    WIDTH_WIDE = 6

    def __init__(self, printer):
        self.printer = printer

    def generate_zpl_for_containers(self, containers):
        """
        Print out labels for all listed containers, using container name as barcode.
        Inserts newline in name string according to SNP&SEQ barcode policy (newline
        before plate id)
        :param containers: An unique list of containers
        :return:
        """
        newline_pattern = re.compile("(^.+_)(PL\d+_\d+$)")
        for c in containers:
            without_prefix = c.id.split("-", 1)[1]
            processed_name = ""
            match_res = newline_pattern.match(c.name)
            if match_res:
                processed_name = match_res.group(1) + "\n" + match_res.group(2)
            else:
                processed_name = c.name
            self.generate_zpl_for_container(name=processed_name, barcode=without_prefix)

    def generate_zpl_for_container(self, name, barcode):
        """Prints a default bar code label for a container"""
        print_info = LabelPrintInfo(name, barcode, self.HEIGHT_TALL,
                                    self.WIDTH_NARROW, (90, 20), LabelPrintInfo.POS_RIGHT)
        self.append_contents(print_info)

    def append_contents(self, label_print_info):
        """Prints to the registered printer, using a LabelPrintInfo"""
        self.printer.append_contents(label_print_info)

    @property
    def contents(self):
        return '\n'.join(self.printer.contents)

    @staticmethod
    def create():
        return LabelPrinterService(LabelPrinterService.create_printer())

    @staticmethod
    def create_printer():
        # Creates the default production version of a printer:
        return ZebraLabelPrinter(font="B", zoom_factor=4, spacing=5,
                                 block_width_points=850, label_width_points=1240, text_max_lines=4,
                                 space_points=20, chars_per_line=28)


class LabelPrintInfo:
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
        self.text = text
        self.barcode = barcode
        self.height = height
        self.width = width
        self.offset = offset
        self.position = position


class ZebraLabelPrinter:

    FONT_SIZES = {"A": (5, 9), "B": (7, 11), "C": (10, 18), "D": (10, 18),
                  "E": (15, 28), "F": (13, 26), "G": (40, 60), "H": (13, 21)}

    """Specifies both the file format needed for this printer as well as the communication mechanism"""
    def __init__(self, font, zoom_factor, spacing, block_width_points, label_width_points,
                 text_max_lines, space_points, chars_per_line):
        self.font = font
        self.zoom_factor = zoom_factor
        self.spacing = spacing
        self.block_width_points = block_width_points
        self.label_width_points = label_width_points    #the length of the label in points for easy calc of positions

        self.text_max_lines = text_max_lines
        self.space_points = space_points
        self.chars_per_line = chars_per_line
        self.contents = list()

    def append_contents(self, info):
        self.contents.append(self.parse(info))

    def _parse(self, info):
        start            = 11 * info.width
        data             = len(info.barcode) * 11 * info.width
        CRC              = 11 * info.width
        stop             = 12 * info.width
        text_spacing     = 10 * info.width #spacing between barcode and info text


        text_width, text_height = self.FONT_SIZES[self.font]
        text_width, text_height = text_width * self.zoom_factor, text_height * self.zoom_factor

        yield "^XA"
        yield "^LH{},{}".format(*info.offset)

        if info.position == LabelPrintInfo.POS_TOP:
            yield "^A{font}{height},{width}".format(font=self.font, height=text_height, width=text_width)
            yield "^FO{},{}".format(0, 0)
            yield "^FD{}^FS".format(info.text)

        yield "^FO{},{}".format(0, text_height + self.spacing)

        yield "^BY{}".format(info.width)
        yield "^BCN,{},N,N,N".format(info.height)
        yield "^FD{}^FS".format(info.barcode)

        if info.position == LabelPrintInfo.POS_RIGHT:
            if info.width <= 4:
                barcode_width = start + data + CRC + stop + text_spacing
            else:
                barcode_width = len(info.barcode) * info.width * 7 + 200
            yield "^FO{},{}".format(barcode_width, text_height + self.spacing)
            yield "^A{}{},{}".format(self.font, text_height, text_width)
            yield "^FB{},{},{},".format(self.label_width_points - info.offset[0] - barcode_width, self.text_max_lines, self.space_points)
            yield "^FD{}^FS".format(self.replace_newlines(info.text)) #use built in linebreak functionality for bulk of string
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
