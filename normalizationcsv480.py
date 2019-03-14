# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.entities import Process
from genologics.lims import Lims
import csv
import genologics
import re

__author__ = "CTMR, Kim Wong"
__date__ = "2019"
__doc__ = """
Using the input sample "Concentration" UDF, create a CSV file
for input into a Tecan Fluent 480 in the format:

A1;0
B1;0.29222
C1;6.2814
D1;2.8037
E1;24
[...]

Where the first column is the well and the second column is the
concentration.

Usage:
    bash -c "/opt/gls/clarity/miniconda3/bin/python /opt/gls/clarity/customextensions/normalizationcsv480.py 
    --pid {processLuid}
    --newCsvFilename 'Fluent File (download me!)'
   [--concUdf 'Concentration']
    "
"""

def get_udf_if_exists(artifact, udf, default=""):
    if (udf in artifact.udf):
        return artifact.udf[udf]
    else:
        return default

row_letters = "ABCDEFGH"
well_re = re.compile("([A-Z]):*([0-9]{1,2})")

def sort_samples_columnwise(output):
    """A1 -> 0, B1 -> 1, A2 -> 8, B2 -> 9
        Column number is worth x * 8
        Row letter is worth +y
    """
    match = re.search(well_re, output.location[1])
    if not match:
        raise(RuntimeError("No valid well position found for output '%s'!" % output.name))
    row = match.group(1)
    col = match.group(2)
    row_index = row_letters.index(row)
    col_value = (int(col) - 1) * 8

    return col_value + row_index

def find_output_artifact(name, p):
    for i, artifact in enumerate(p.all_outputs(unique=True)):
        if artifact.name == name:
            return artifact

def main(lims, args, epp_logger):
    p = Process(lims, id=args.pid)

    with open(args.newCsvFilename, 'w', newline='') as csvfile:
        pass

    # the well location information is on the input samples,
    samples = p.all_inputs(unique=True)
    samples.sort(key=sort_samples_columnwise)

    # but the concentration is on the output files
    outputs = [find_output_artifact(s.name, p) for s in samples]

    for i, output in enumerate(outputs):
        concentration = get_udf_if_exists(output, 'QuantIt HS Concentration', default=None)
        print(concentration)
        concentration = get_udf_if_exists(output, args.concUdf, default=None)
        print(concentration)
        if concentration is not None:
            concentration = float(concentration)
        else:
            raise RuntimeError("Could not find UDF '%s' of sample '%s'" % (args.concUdf, output.name))

        well = samples[i].location[1].split(':')
        well = well.join('')

        with open(args.newCsvFilename, 'a') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=';')
            csv_writer.writerow([well, concentration])

if __name__ == "__main__":
    """See __doc__ at the top of this file for a description."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--pid', required=True, help='Lims id for current Process')
    parser.add_argument('--newCsvFilename', required=True, help='LIMS name of the normalization CSV file to be created')
    parser.add_argument('--concUdf', default="Concentration", help='Name of the concentration UDF')

    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()

    main(lims, args, None)
    print("CSV creation successful!")
