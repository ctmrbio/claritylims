from argparse import ArgumentParser
import logging

from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.entities import Process
from genologics.lims import Lims
import xlrd
import re

__author__ = "CTMR, Kim Wong"
__date__ = "2019"
__doc__ = """
Takes an output file from the Tecan Spark and sets the relevant
concentration UDF on the samples in the step.
Usage:
    bash -c "/opt/gls/clarity/miniconda3/bin/python /opt/gls/clarity/customextensions/sparkoutput.py 
    --pid {processLuid}
    --sparkOutputFile 'Spark HighSens File'
    --concentrationUdf 'QuantIt HS Concentration'
   [--convertToNm
    --fragmentSize '620bp'
    --concentrationUdfNm 'QuantIt HS Concentration (nM)']
    2> {compoundOutputFileLuid1}
    "
"""

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s %(levelname)s:%(message)s"
)

def format_fragment_size(fragment_size):
    # can either be '620bp' or '620' or maybe even '620 bp'
    match = re.search(r'([0-9]{2,4})\s*(bp)?', fragment_size)
    if match:
        return float(match.group(1))
    raise(RuntimeError("Invalid fragment size '%s'! Please specify the fragment size in the format '620' or '620bp'" % fragment_size))

def get_spark_file(process, filename):
    content = None
    for outart in process.all_outputs():
        #get the right output artifact
        if outart.type == 'ResultFile' and outart.name == filename:
            try:
                fid = outart.files[0].id
                content = lims.get_file_contents(id=fid)
            except:
                raise(RuntimeError("Cannot access the Spark output file to read the concentrations, are you sure it has been uploaded?"))
            break
    return content

def is_well(string, well_re):
    return well_re.match(string)

def find_input_in_well(well, p):
    for i, artifact in enumerate(p.all_inputs(unique=True)):
        if artifact.type == "Analyte":
            artifact_well = artifact.location[1]
            artifact_well = "".join(artifact_well.split(":"))
            if artifact_well == well:
                return artifact

def find_output_in_well(well, p):
    for i, artifact in enumerate(p.all_outputs(unique=True)):
        if artifact.location[1] is not None:
            artifact_well = artifact.location[1]
            artifact_well = "".join(artifact_well.split(":"))
            if artifact_well == well:
                return artifact

def format_concentration(concentration):
    if type(concentration) == str:
        if concentration == "<Min":
            concentration = 0.0
        elif concentration == ">Max":
            concentration = 99.9
        else:
            concentration = float(concentration)
    elif type(concentration) == int:
        concentration = float(concentration)
    elif type(concentration) != float:
        raise(RuntimeError("Error! Invalid concentration '%s' for well %s, row %s" % (concentration, well, row_i)))
    return concentration

def convert_to_nm(concentration, fragment_size):
    # convert from ng/ul to nM
    basepair_mw = 660
    return (concentration * 1000000) / (fragment_size * basepair_mw)

def main(lims, args, logger):
    p = Process(lims, id=args.pid)
    
    # Precompute lookup dictionaries for output artifacts and input_output_maps
    output_artifacts = {artifact.id: artifact for artifact in p.all_outputs(unique=True)}
    input_output_map = {}
    for input_, output_ in p.input_output_maps:
        if output_["output-generation-type"] == "PerInput": 
            input_output_map[input_["limsid"]] = output_["limsid"]
    logger.info("output_artifacts: %s", output_artifacts)
    logger.info("input_output_map: %s", input_output_map)

    sparkfile = get_spark_file(p, args.sparkOutputFilename)
    if not sparkfile:
        raise(RuntimeError("Cannot find the Spark output file, are you sure it has been uploaded?"))

    workbook = xlrd.open_workbook(file_contents=sparkfile.read())
    sheet = workbook.sheet_by_index(0)

    well_re = re.compile("[A-Z][0-9]{1,2}")
    if args.convertToNm:
        fragment_size = format_fragment_size(args.fragmentSize)
    outputs = []

    for row_i in range(0, sheet.nrows):
        if is_well(sheet.cell(row_i, 0).value, well_re):
            well = sheet.cell(row_i, 0).value
            if args.wellFromOutput:
                artifact = find_output_in_well(well, p)
            else:
                artifact = find_input_in_well(well, p)
            if not artifact:
                raise(RuntimeError("Error! Cannot find sample at well position %s, row %s" % (well, row_i)))
            logger.info("Input artifact: %s", artifact)

            if sheet.ncols > 2: # some files may be missing the "NoCalc" column
                concentration = sheet.cell(row_i, 2).value
            else:
                concentration = sheet.cell(row_i, 1).value

            if concentration == "NoCalc":
                concentration = sheet.cell(row_i, 1).value
            concentration = format_concentration(concentration)
            logger.info("concentration: %s", concentration)
            
            # Find output artifact
            output = output_artifacts[input_output_map[artifact.id]]
            logger.info("Output artifact: %s", output)

            output.udf[args.concentrationUdf] = concentration
            outputs.append(output)

            if args.convertToNm:
                concentration_nm = convert_to_nm(concentration, fragment_size)
                output.udf[args.concentrationUdfNm] = concentration_nm

    for out in outputs:
        out.put()

if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--pid', required=True, help='LIMS ID for current Process')
    parser.add_argument('--concentrationUdf', required=True, help='The concentration UDF to set')
    parser.add_argument('--sparkOutputFilename', required=True, help='LIMS name of the Spark file uploaded to the process')
    # for setting an additional nM concentration UDF, e.g. 'QuantIt HS Concentration (nM)'
    parser.add_argument('--convertToNm', default=False, action='store_true', help='Should the parsed concentrations be converted from ng/ul to nM or not?')
    parser.add_argument('--fragmentSize', default='620bp', help='The average fragment size of the DNA, if converting to nM')
    parser.add_argument('--concentrationUdfNm', default='QuantIt HS Concentration (nM)', help='The nM concentration UDF to set')
    parser.add_argument('--wellFromOutput', default=False, action='store_true', help='Should the wells on the samples be found in the inputs or the outputs? The initial WGS QC step requires them to be read from the outputs, since the inputs are usually placed into new wells.')

    args = parser.parse_args()
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    logger = logging.getLogger(__name__)

    main(lims, args, logger)
    print("Successful assignment!")
