DESC = """Create an overview excel file on the Aggregate QC step""" 

from argparse import ArgumentParser

import genologics
from genologics.lims import Lims
from genologics.config import BASEURI, USERNAME, PASSWORD

from genologics.entities import Process

import logging
import sys
import xlwt

def get_udf_if_exists(artifact, udf):
    if (udf in artifact.udf):
        return artifact.udf[udf]
    else:
        return ""

def get_field_style(field, threshold):
    style = xlwt.XFStyle()
    if type(field) == int or type(field) == float:
        if float(field) < threshold:
            style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour red;')
    return style

def main(lims, args, epp_logger):
    p = Process(lims, id = args.pid)

    new_workbook = xlwt.Workbook()
    new_sheet = new_workbook.add_sheet('Sheet 1')
    for col, heading in enumerate(["Sample name", "Container", "Well", "QuantIt HS Concentration", "QuantIt BR Concentration", "Qubit Concentration", "Chosen Concentration"]):
        new_sheet.write(0, col, heading)
    
    for i, artifact in enumerate(p.all_inputs(unique=True)):
        sample_name = artifact.name
        container = artifact.location[0].name
        well = artifact.location[1]
        conc_hs = get_udf_if_exists(artifact, "QuantIt HS Concentration")
        conc_br = get_udf_if_exists(artifact, "QuantIt BR Concentration")
        conc_qb = get_udf_if_exists(artifact, "Qubit Concentration")
        conc_chosen = get_udf_if_exists(artifact, "Concentration")
        for col, field in enumerate([sample_name, container, well, conc_hs, conc_br, conc_qb, conc_chosen]):
            style = get_field_style(field, float(args.threshold))
            new_sheet.write(i + 1, col, field, style)

    new_workbook.save(args.outputFilename)

if __name__ == "__main__":
    # Initialize parser with standard arguments and description
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid', required=True,
                        help='Lims id for current Process')
    parser.add_argument('--outputFilename', required=True,
                        help='lims ID of the new file')
    parser.add_argument('--log', default=sys.stdout,
                        help=('File name for standard log file, '
                              'for runtime information and problems.'))
    parser.add_argument('-t', '--threshold', default=4,
                        help='threshold for red text')

    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args, None)
