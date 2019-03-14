# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.entities import Process
from genologics.lims import Lims
import csv
import genologics

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
    --pid {processLuid}
    --sparkOutputFile 'Spark HighSens File'
    --concentrationUdf 'QuantIt HS Concentration'
   [--convertToNm
    --fragmentSize '620bp'
    --concentrationUdfNm 'QuantIt HS Concentration (nM)']
    "
"""

- [ ] Tecan wants 0.01 instead of 0 when taking the negative control (if it's 0, it takes none of the samples; in the other case, it takes everything) -- do this in the Create Fluent Input File script!
- [ ] Also, the Fluent input file should list all of the wells of the plate, even if they're empty!
- [ ] The Fluent input file should be column-wise (A1, B1, C1, D1)


def calculate_sample_required(conc1, conc2, vol2):
    """Classic C1V1 = C2V2. Calculates V1.
    All arguments should be floats.
    """
    return (conc2 * vol2) / conc1

def calculate_volumes_required(sample_conc, target_concentration, target_volume, threshold_conc_no_normalization, normalize_low_volumes=False):
    """Returns a tuple of the sample volume (s) and water volume (w)
    which should be input into the robot. All values should be floats.
    """
    if sample_conc < threshold_conc_no_normalization and not normalize_low_volumes:
        # don't normalize the sample if the concentration is too low
        return (0, 0)

    sample_required = calculate_sample_required(sample_conc, target_concentration, target_volume)
    water_required = target_volume - sample_required
    too_low_volume = 1
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

def get_udf_if_exists(artifact, udf, default=""):
    if (udf in artifact.udf):
        return artifact.udf[udf]
    else:
        return default

def main(lims, args, epp_logger):
    p = Process(lims, id = args.pid)
    target_concentration = float(args.targetConcentration)
    target_volume = float(args.targetVolume)
    threshold_conc_no_normalize = float(args.thresholdConcNoNormalize)

    with open(args.newCsvFilename, 'w', newline='') as csvfile:
        pass

    for i, artifact in enumerate(p.all_outputs(unique=True)):
        if artifact.type != "Analyte":
            # only work on analytes (not result files)
            continue
        concentration = get_udf_if_exists(artifact, args.concentrationUDF, default=None)
        if concentration == 0.0: # hack because this doesn't pass "if concentration:" lol
            sample_required, water_required = calculate_volumes_required(concentration, target_concentration, target_volume, threshold_conc_no_normalize, args.normalizeLowVolumes)
        elif concentration:
            concentration = float(concentration)
            sample_required, water_required = calculate_volumes_required(concentration, target_concentration, target_volume, threshold_conc_no_normalize, args.normalizeLowVolumes)
        else:
            raise RuntimeError("Could not find UDF 'Concentration' of sample '%s'" % artifact.name)
        well = artifact.location[1]
        with open(args.newCsvFilename, 'a') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',')
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
    parser.add_argument('--normalizeLowVolumes', default=False, help='a flag to determine whether samples with concentrations under the threshold should be normalized anyway')

    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()

    main(lims, args, None)
    print("Creation successful!")
