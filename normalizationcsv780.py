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
Using the input sample "Concentration (nM)" UDF, plus the step UDFs
"Target Concentration (nM)" and "Target Volume (uL)", this script
creates a CSV file for input on the Tecan for normalization in the
format:

A1  0;0 10;0
B1  7;6 2;4
C1  0;0 0;0
D1  33;5    6;5
E1  35;1    4;9
[...]

Usage:
    bash -c "/opt/gls/clarity/miniconda3/bin/python /opt/gls/clarity/customextensions/normalizationcsv780.py 
    --pid '{processLuid}'
    --newCsvFilename '{compoundOutputFileLuid3}'
   [--concentrationUDF 'Concentration (nM)']
    --targetConcentration '{udf:Target Concentration (nM)}'
    --targetVolume '{udf:Target Volume (ul)}'
   [--thresholdConcNoNormalize '1.0']
   [--concOnOutput]
    "
"""

def calculate_sample_required(conc1, conc2, vol2):
    """Classic C1V1 = C2V2. Calculates V1.
    All arguments should be floats.
    """
    if conc1 == 0.0:
        conc1 = 0.000001 # don't want to divide by zero :)
    return (conc2 * vol2) / conc1

def calculate_volumes_required(sample_conc, target_concentration, target_volume, threshold_conc_no_normalization, is_control=False):
    """Returns a tuple of the sample volume (s) and water volume (w)
    which should be input into the robot. All values should be floats.
    """
    if sample_conc < threshold_conc_no_normalization and not is_control:
        # Don't normalize the sample if the concentration is too low and it isn't a control.
        # If the threshold is 0, then all samples will be normalized.
        # Control samples are normalized even if their volumes are too low (then all of
        # the sample is taken (i.e. target_volume))
        return (0.0, 0.0)

    sample_required = calculate_sample_required(sample_conc, target_concentration, target_volume)
    water_required = target_volume - sample_required
    too_low_volume = 1.5 # the volume which is too low for pipetting
    # firstly, is the sample concentration is too low:
    if sample_required > target_volume:
        s = target_volume
        w = 0.0
    # otherwise, if the sample concentration is too high:
    elif sample_required < too_low_volume:
        if sample_required * 2.0 > too_low_volume:
            s = sample_required * 2.0
            w = water_required * 2.0
        elif sample_required * 3.0 > too_low_volume:
            s = sample_required * 3.0
            w = water_required * 3.0
        else:
            s = sample_required * 4.0
            w = water_required * 4.0
    # but maybe it's lagom!
    else:
        s = sample_required
        w = water_required
    return (s, w)

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

def get_udf_if_exists(sample, udf, default=""):
    if (udf in sample.udf):
        return sample.udf[udf]
    else:
        return default

def find_output_artifact(name, p):
    for i, artifact in enumerate(p.all_outputs(unique=True)):
        if artifact.name == name:
            return artifact
    raise(RuntimeError("Could not find output artifact for sample '%s'!" % name))

control_re = re.compile("neg|pos", re.IGNORECASE)
def is_control(sample_name):
    """Try to deduce if the sample is a control or not from the sample name.
    Just checks for 'neg' or 'pos' in the sample name, which could possibly
    return false positives...
    """
    match = re.search(control_re, sample_name)
    return match

def format_volume(volume, decimal_sep=';'):
    volume_string = "{:.2f}".format(volume) # format to 2 decimal places
    volume_string = volume_string.replace('.', decimal_sep)
    return volume_string

def main(lims, args, epp_logger):
    p = Process(lims, id = args.pid)
    target_concentration = float(args.targetConcentration)
    target_volume = float(args.targetVolume)
    threshold_conc_no_normalize = float(args.thresholdConcNoNormalize)

    with open(args.newCsvFilename, 'w', newline='') as csvfile:
        pass

    samples_in = p.all_inputs(unique=True) 

    well_re = re.compile("([A-Z]):*([0-9]{1,2})")
    samples_in.sort(key=lambda sample: sort_samples_columnwise(sample, well_re)) # wrap the call in a lambda to be able to pass in the regex

    if args.concOnOutput:
        samples = [find_output_artifact(s.name, p) for s in samples_in] # required for the WGS step
    else:
        samples = samples_in

    print(samples)

    for i, sample in enumerate(samples):
        if not args.concOnOutput and sample.type != "Analyte":
            # if 16S, only work on analytes (not result files)
            # but WGS should work on result files
            continue
        concentration = get_udf_if_exists(sample, args.concentrationUDF, default=None)
        if concentration is not None:
            concentration = float(concentration)
            sample_required, water_required = calculate_volumes_required(concentration, target_concentration, target_volume, threshold_conc_no_normalize, is_control(sample.name))
            sample_required = format_volume(sample_required)
            water_required = format_volume(water_required)
        else:
            raise RuntimeError("Could not find UDF '%s' of sample '%s'" % (args.concentrationUDF, sample.name))
        well = samples_in[i].location[1].split(':')
        well = ''.join(well)

        with open(args.newCsvFilename, 'a') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter='\t')
            csv_writer.writerow([well, water_required, sample_required])

if __name__ == "__main__":
    """See __doc__ at the top of this file for a description."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--pid', required=True, help='Lims id for current Process')
    parser.add_argument('--newCsvFilename', required=True, help='limsid of the csv file to write to')
    parser.add_argument('--concentrationUDF', default='Concentration (nM)', help='The name of the UDF to read the concentrations from')
    parser.add_argument('--targetConcentration', required=True, help='target concentration')
    parser.add_argument('--targetVolume', required=True, help='target volume')
    parser.add_argument('--thresholdConcNoNormalize', default=1.0, help='the volume which all samples should be over for them to be normalized (otherwise they are ignored and 0 sample and 0 water is taken from them)')
    parser.add_argument('--concOnOutput', default=False, action='store_true', help='The initial WGS QC step writes the concentrations to the outputs, whereas the normal aggregation steps have them on the input.')

    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()

    main(lims, args, None)
    print("Creation successful!")
