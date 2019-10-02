#!/usr/bin/env python3
__doc__ = """
Parse measured fragment size. 

Usage:
    bash -c "/opt/gls/clarity/miniconda3/bin/python /opt/gls/clarity/customextensions/parse_fragment_size.py
    --pid {processLuid}
    --tapestation-csv 'TapeStation CSV File'
    --udf-fragsize 'Fragment size'
    "
"""
__author__ = "CTMR, Fredrik Boulund"
__date__ = "2019"
from argparse import ArgumentParser
from collections import defaultdict, namedtuple
import logging
import csv
import re

from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.entities import Process
from genologics.lims import Lims


logging.basicConfig(
    level=logging.INFO, 
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
    Peak = namedtuple("Peak", ["Well", "Sample", "Size", "Percent", "Observations"])
    measured_peaks = defaultdict(list)
    with open(tapestation_csv) as csv:
        reader = csv.DictReader(csv)
        for line in reader:
            try:
                peak = Peak(
                    line["Well"],
                    line["Sample Description"], 
                    line["Size [bp]"],
                    line["% Integrated Area"],
                    line["Observations"])
            except KeyError:
                raise(RuntimeError("Could not parse line: {}".format(line)))
            if peak.Observations in ignored_observations:
                continue
            if peak.Size > min_fragsize and peak.Size < max_fragsize:
                measured_peaks[peak.well] += peak
    return measured_peaks


def is_well(string, well_re=re.compile(r'[A-Z][0-9]{1,2}')):
    return well_re.match(string)


def main(lims, args, logger):
    p = Process(lims, id=args.pid)
    
    tapestation_file = get_tapestation_file(p, args.tapestation_csv)
    if not tapestation_file:
        raise(RuntimeError("Cannot find the TapeStation csv file, are you sure it has been uploaded?"))

    # Precompute lookup dictionary for output artifacts
    output_artifacts = {artifact.id: artifact for artifact in p.all_outputs(unique=True)}
    input_output_map = {}
    for input_, output_ in p.input_output_maps:
        if output_["output-generation-type"] == "PerInput": 
            input_output_map[input_["limsid"]] = output_["limsid"]
    logger.info("output_artifacts: %s", output_artifacts)
    logger.info("input_output_map: %s", input_output_map)


    outputs = []
    measured_peaks = parse_tapestation_csv(args.tapestation_csv, args.min_fragsize, args.max_fragsize)
    for well, peaks in measured_peaks:
        fragment_size = -1
        if len(peaks) == 1:
            fragment_size = peaks[0].Size

        # TODO:
        # Find the artifact to modify
        # Modify the relevant UDF
        # Add it to outputs

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
