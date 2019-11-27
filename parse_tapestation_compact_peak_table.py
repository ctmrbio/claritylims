#!/usr/bin/env python3
__doc__ = """
Parse peaks from Compact Peak Table (csv) from TapeStation.

Usage in Clarity LIMS:
    bash -c "/opt/gls/clarity/miniconda3/bin/python /opt/gls/clarity/customextensions/parse_tapestation_compact_peak_table.py
    --pid {processLuid}
    --tapestation-csv 'TapeStation Compact Peak Table'
    --udf-fragsize 'Average Fragment Size (bp)'
    2> {compoundOutfileLuid3}
    "
"""
__author__ = "CTMR, Fredrik Boulund"
__date__ = "2019"
from argparse import ArgumentParser
from collections import defaultdict, namedtuple
import logging
import csv
import re
from sys import stderr

from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.entities import Process
from genologics.lims import Lims


logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s %(levelname)s:%(message)s"
)

def get_tapestation_file(process, filename):
    """Find the correct output file to process."""
    content = None
    for outart in process.all_outputs():
        if outart.type == 'ResultFile' and outart.name == filename:
            try:
                fid = outart.files[0].id
                content = lims.get_file_contents(id=fid)
            except:
                raise(RuntimeError("Cannot access the TapeStation CSV file to read the fragment sizes, are you sure it has been uploaded?"))
            break
    return content


def parse_tapestation_csv(tapestation_csv, min_fragsize, max_fragsize):
    """Parse TapeStation CSV into a dictionary of observed peaks."""
    ignored_observations = {"Lower Marker", "Upper Marker"}
    ignored_sample_descriptions = {"Ladder"}
    Peak = namedtuple("Peak", ["Well", "Sample", "Size", "Percent", "Observations"])
    measured_peaks = defaultdict(list)
    reader = csv.DictReader(tapestation_csv, delimiter=',')
    for line in reader:
        if line["Observations"] in ignored_observations:
            continue
        if line["Sample Description"] in ignored_sample_descriptions:
            continue
        if not line["Size [bp]"]:
            fragment_size = 0
        else:
            fragment_size = int(line["Size [bp]"])
        if not line["% Integrated Area"]:
            integrated_area = 0
        else:
            integrated_area = float(line["% Integrated Area"])
        try:
            peak = Peak(
                line["Well"],
                line["Sample Description"], 
                fragment_size,
                integrated_area,
                line["Observations"])
        except KeyError:
            raise(RuntimeError("Could not parse line: {}".format(line)))
        except ValueError:
            raise(RuntimeError("Could not parse line: {}".format(line)))
        if peak.Size > min_fragsize and peak.Size < max_fragsize:
            measured_peaks[peak.Well].append(peak)
    return measured_peaks


def find_input_in_well(well, p):
    for i, artifact in enumerate(p.all_inputs(unique=True)):
        if artifact.type == "Analyte":
            artifact_well = artifact.location[1]
            artifact_well = "".join(artifact_well.split(":"))
            if artifact_well == well:
                if artifact:
                    return artifact
                else:
                    logger.error("Artifact %s, %s is invalid: %s", well, p, artifact)


def is_well(string, well_re=re.compile(r'[A-Z][0-9]{1,2}')):
    return well_re.match(string)


def main(lims, args, logger):
    logger.debug("Getting Process with ID %s", args.pid)
    p = Process(lims, id=args.pid)
    logger.debug(p)
    
    # Precompute lookup dictionary for output artifacts
    output_artifacts = {artifact.id: artifact for artifact in p.all_outputs(unique=True)}
    logger.debug(output_artifacts)
    logger.debug(p.input_output_maps)
    input_output_map = {}
    for input_, output_ in p.input_output_maps:
        if output_["output-generation-type"] == "PerInput": 
            input_output_map[input_["limsid"]] = output_["limsid"]
    logger.debug("output_artifacts: %s", output_artifacts)
    logger.debug("input_output_map: %s", input_output_map)


    tapestation_file = get_tapestation_file(p, args.tapestation_csv)
    if not tapestation_file:
        raise(RuntimeError("Cannot find the TapeStation csv file, are you sure it has been uploaded?"))
    logger.debug(tapestation_file)

    outputs = []
    measured_peaks = parse_tapestation_csv(tapestation_file.splitlines(), args.min_fragsize, args.max_fragsize)
    for well, peaks in measured_peaks.items():
        fragment_size = -1
        if len(peaks) == 1:
            fragment_size = peaks[0].Size
        logger.debug([well, peaks, fragment_size])

        # Find input artifact, this has well information
        artifact = find_input_in_well(well, p)

        # Find output artifact, this has the UDF where we store the peak size
        output = output_artifacts[input_output_map[artifact.id]]
        logger.debug("Output artifact: %s", output)

        logger.debug("Modifying UDF '%s' of artifact '%s'", args.udf_fragsize, artifact)
        output.udf[args.udf_fragsize] = fragment_size
        outputs.append(output)
    
    for out in outputs:
        out.put()


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--pid", 
            required=True, 
            help="LIMS ID for current Process.")
    parser.add_argument("--tapestation-csv", dest="tapestation_csv",
            required=True, 
            help="LIMS name of the TapeStation CSV file uploaded to the process.")
    parser.add_argument("--udf-fragsize", dest="udf_fragsize",
            required=True, 
            help="The UDF to set")
    parser.add_argument("--min-fragsize", dest="min_fragsize",
            type=int,
            default=200,
            help="Minimum expected fragment size [%(default)s].")
    parser.add_argument("--max-fragsize", dest="max_fragsize",
            type=int,
            default=1000,
            help="Maximum expected fragment size [%(default)s].")

    args = parser.parse_args()
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    logger = logging.getLogger(__name__)

    main(lims, args, logger)
    print("parse_fragment_size.py completed succesfully!")
