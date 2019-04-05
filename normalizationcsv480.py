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
    --newCsvFilename '{compoundOutputFileLuid3}'
   [--concUdf 'Concentration']
   [--concOnOutput]
    "
"""

def get_udf_if_exists(artifact, udf, default=""):
    if udf in artifact.udf:
        return artifact.udf[udf]
    else:
        return default

def sort_samples_columnwise(sample, well_re):
    """A1 -> 0, B1 -> 1, A2 -> 8, B2 -> 9
        Column number is worth x * 8
        Row letter is worth +y
    """
    row_letters = "ABCDEFGH"
    match = re.search(well_re, sample.location[1])
    if not match:
        raise(RuntimeError("No valid well position found for sample '%s'!" % sample.name))
    row = match.group(1)
    col = match.group(2)
    row_index = row_letters.index(row)
    col_value = (int(col) - 1) * 8

    return col_value + row_index

def find_output_artifact(name, p):
    for i, artifact in enumerate(p.all_outputs(unique=True)):
        if artifact.name == name:
            return artifact
    raise(RuntimeError("Could not find output artifact for sample '%s'!" % name))

def main(lims, args, epp_logger):
    p = Process(lims, id=args.pid)

    with open(args.newCsvFilename, 'w', newline='') as csvfile:
        pass

    # the well location information is on the input samples,
    well_re = re.compile("([A-Z]):*([0-9]{1,2})")
    samples_in = p.all_inputs(unique=True)
    samples_in.sort(key=lambda sample: sort_samples_columnwise(sample, well_re)) # wrap the call in a lambda to be able to pass in the regex

    if args.concOnOutput:
        samples = [find_output_artifact(s.name, p) for s in samples_in] # required in the WGS step
    else:
        samples = samples_in

    for i, sample in enumerate(samples):
        concentration = get_udf_if_exists(sample, args.concUdf, default=None)
        if concentration is not None:
            concentration = float(concentration)
        else:
            raise RuntimeError("Could not find UDF '%s' of sample '%s'" % (args.concUdf, sample.name))

        if concentration == 0.0:
            concentration = 0.01

        well = samples_in[i].location[1].split(':')
        well = ''.join(well)

        with open(args.newCsvFilename, 'a') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=';')
            csv_writer.writerow([well, concentration])

if __name__ == "__main__":
    """See __doc__ at the top of this file for a description."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--pid', required=True, help='Lims id for current Process')
    parser.add_argument('--newCsvFilename', required=True, help='LIMS name of the normalization CSV file to be created')
    parser.add_argument('--concUdf', default="Concentration", help='Name of the concentration UDF')
    parser.add_argument('--concOnOutput', default=False, action='store_true', help='The initial WGS QC step writes the concentrations to the outputs, whereas the normal aggregation steps have them on the input.')

    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()

    main(lims, args, None)
    print("CSV creation successful!")
