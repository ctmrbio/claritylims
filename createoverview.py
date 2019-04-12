DESC = """Create an overview excel file on the Aggregate QC step""" 

from argparse import ArgumentParser
from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.entities import Process
from genologics.lims import Lims
import genologics
import logging
import re
import sys
import xlwt

fields = {
    "Sample Name": None,
    "Original DNA Plate LIMS ID": None,
    "Container Name": None,
    "Container ID": None,
    "Well": None,
    "Project": None,
    "Sample Origin": None,
    "Sample Buffer": None,
    "Indexes": None,
    "PCR Method": None,
    "QuantIt HS Concentration": None,
    "QuantIt BR Concentration": None,
    "Qubit Concentration": None,
    "Chosen Concentration": None,
    "QuantIt HS Concentration (nM)": None,
    "QuantIt BR Concentration (nM)": None,
    "Qubit Concentration (nM)": None,
    "Chosen Concentration (nM)": None,
}

def get_udf_if_exists(artifact, udf):
    if (udf in artifact.udf):
        return artifact.udf[udf]
    else:
        return ""

def get_field_style(field, red_threshold, orange_threshold):
    style = xlwt.XFStyle()
    if type(field) == int or type(field) == float:
        if float(field) < red_threshold:
            style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour red;')
        elif float(field) < orange_threshold:
            style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour orange;')
    return style

def sort_samples_columnwise(output, well_re):
    """A1 -> 0, B1 -> 1, A2 -> 8, B2 -> 9
        Column number is worth x * 8
        Row letter is worth +y
    """
    row_letters = "ABCDEFGH"
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
    raise(RuntimeError("Could not find output artifact for sample '%s'!" % name))

def main(lims, args, epp_logger):
    p = Process(lims, id = args.pid)

    new_workbook = xlwt.Workbook()
    new_sheet = new_workbook.add_sheet('Sheet 1')
    for col, heading in enumerate(fields.keys()):
        new_sheet.write(0, col, heading)
    
    well_re = re.compile("([A-Z]):*([0-9]{1,2})")
    artifacts = p.all_inputs(unique=True)
    artifacts.sort(key=lambda sample: sort_samples_columnwise(sample, well_re)) # wrap the call in a lambda to be able to pass in the regex

    if args.udfsOnOutput:
        outputs = [find_output_artifact(s.name, p) for s in artifacts] # required for the WGS step

    for i, artifact in enumerate(artifacts):
        sample = artifact.samples[0] # the original, submitted sample
        fields["Sample Name"] = artifact.name
        fields["Original DNA Plate LIMS ID"] = ""
        if artifiact.location:
            fields["Container Name"] = artifact.location[0].name
            fields["Well"] = artifact.location[1]
        else:
            fields["Container Name"] = "Unknown Container"
            fields["Well"] = "Unknown Well"
        if sample.project:
            fields["Project"] = sample.project.name
        else:
            fields["Project"] = ""
        fields["Sample Origin"] = get_udf_if_exists(sample, "Sample Origin")
        fields["Sample Buffer"] = get_udf_if_exists(sample, "Sample Buffer")
        fields["Indexes"] = artifact.reagent_labels
        fields["PCR Method"] = ""
        if args.udfsOnOutput:
            udf_sample = outputs[i] # use the equivalent output of the sample to find the UDF measurement
        else:
            udf_sample = artifact
        fields["QuantIt HS Concentration"] = get_udf_if_exists(udf_sample, "QuantIt HS Concentration")
        fields["QuantIt BR Concentration"] = get_udf_if_exists(udf_sample, "QuantIt BR Concentration")
        fields["Qubit Concentration"] = get_udf_if_exists(udf_sample, "Qubit Concentration")
        fields["Chosen Concentration"] = get_udf_if_exists(udf_sample, "Concentration")
        fields["QuantIt HS Concentration (nM)"] = get_udf_if_exists(udf_sample, "QuantIt HS Concentration (nM)")
        fields["QuantIt BR Concentration (nM)"] = get_udf_if_exists(udf_sample, "QuantIt BR Concentration (nM)")
        fields["Qubit Concentration (nM)"] = get_udf_if_exists(udf_sample, "Qubit Concentration (nM)")
        fields["Chosen Concentration (nM)"] = get_udf_if_exists(udf_sample, "Concentration (nM)")
        #for col, field in enumerate([sample_name, container, well, conc_hs, conc_br, conc_qb, conc_chosen]):
        for col, field in enumerate(fields.values()):
            style = get_field_style(field, float(args.redTextConcThreshold), float(args.orangeTextConcThreshold))
            new_sheet.write(i + 1, col, field, style)

    new_workbook.save(args.outputFile)

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid', required=True,
                        help='LIMS id for current Process')
    parser.add_argument('--outputFile', required=True,
                        help='LIMS ID of the new file')
    parser.add_argument('--log', default=sys.stdout,
                        help=('File name for standard log file, '
                              'for runtime information and problems.'))
    parser.add_argument('--redTextConcThreshold', default=1.0, help='Under this threshold concentration is red text')
    parser.add_argument('--orangeTextConcThreshold', default=4.0, help='Under this threshold concentration is orange text')
    parser.add_argument('--udfsOnOutput', default=False, action='store_true', help='The final WGS QC step writes the concentrations to the outputs, whereas the normal aggregation steps have them on the input.')

    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args, None)
