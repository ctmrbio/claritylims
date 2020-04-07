# -*- coding: utf-8 -*-

import csv


class ABI7500FASTResults(object):
    """
    Will parse the result file of a ABI7500 FAST qPCR machine.

    Usage example:

        res = ABI7500FASTResults(
            "qpcr_data.csv")

        for r in res.results():
            print(r[u'Cт'])

    Note that the result file may contain unicode and in order to handle that,
    the encoding needs to be provided for the source file, i.e. put:

        # -*- coding: utf-8 -*-

    At the top of the file, and when you access a unicode encoded key, you need to
    add the `u` in front of the string.
    """

    def __init__(self, path_to_result_file):
        self._path_to_result_file = path_to_result_file
        self._read_result_file()

    def _read_result_file(self):
        with open(self._path_to_result_file, 'r') as csvfile:
            csvreader = csv.reader(csvfile)

            header = {}
            data_header = None
            data = []
            footer = {}

            state = "header"
            for row in csvreader:
                # NB Not Python 3 compatible.
                row = [unicode(entry, "utf8") for entry in row]

                # Skip any empty rows
                if not row[0]:
                    continue

                # Check which state we should be in
                if row[0] == "Well":
                    state = "data"
                    data_header = row
                    continue

                if row[0] == "Analysis Type":
                    state = "footer"

                # Read the data
                if state == "header":
                    header[row[0]] = row[1]

                if state == "data":
                    data_entry = dict(zip(data_header, row))
                    data.append(data_entry)

                if state == "footer":
                    footer[row[0]] = row[1]

            return (header, data, footer)

    def results(self):
        header, data, footer = self._read_result_file()
        return data

    def header(self):
        header, data, footer = self._read_result_file()
        return header

    def footer(self):
        header, data, footer = self._read_result_file()
        return footer
