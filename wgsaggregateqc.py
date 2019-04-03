from argparse import ArgumentParser
from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.entities import Process
from genologics.lims import Lims
import xlrd
import re

__author__ = "CTMR, Kim Wong"
__date__ = "2019"
__doc__ = """
Chooses which concentration to use from the concentrations set on the outputs of this step.
QC flags will also be set for each sample based on the given threshold(s).
Usage:
    bash -c "python /opt/gls/clarity/customextensions/wgsaggregateqc.py 
    --pid {processLuid}
    --concUdfHS 'QuantIt HS Concentration'
    --concUdfBR 'QuantIt BR Concentration'
    --concUdfQB 'Qubit Concentration'
    --concUdfChosen 'Concentration'
    --qcPassCondition '>0.3'
   [--qcPassCondition2 '>0']
"""

def less(a, b):
   return a < b

def greater(a, b):
   return a > b

def less_equal(a, b):
   return a <= b

def greater_equal(a, b):
   return a >= b

operator_map = {
   '<': less,
   '>': greater,
   '<=': less_equal,
   '>=': greater_equal,
}

def check_qc_pass(value, operator, threshold):
    return operator_map[operator](value, threshold)

def determine_qc_flag(concentration, operator, threshold):
    flag = check_qc_pass(concentration, operator, threshold)
    return 'PASSED' if flag else 'FAILED'

def parse_qc_condition(qc_condition):
    # should be formatted as >4.0 or <=3 etc
    match = re.search(r'([<>]=?)\s?(\d+.?\d*)', qc_condition)
    if match:
        operator = match.group(1)
        threshold = float(match.group(2))
        return (operator, threshold)
    raise(RuntimeError("Error! Invalid qc_condition '%s'. Format as >4.0 or <=3 etc" % qc_condition))

def get_file_artifact(process, filename):
    for outart in process.all_outputs():
        if outart.type == 'ResultFile' and outart.name == filename:
            return outart
    return None

def format_concentration(concentration):
    if type(concentration) == str:
        if concentration == "<Min":
            concentration = 0.0
        elif concentration == ">Max":
            concentration = 99.9
    elif type(concentration) == int:
        concentration = float(concentration)
    elif type(concentration) != float:
        raise(RuntimeError("Error! Invalid concentration '%s' for well %s, row %s" % (concentration, well, row_i)))
    return concentration

def get_outputs(p):
    # to avoid the uploaded files (maybe there's a better way to do this)
    outputs = []
    for i in p.all_inputs(unique=True):
        if i.type != 'Analyte':
            continue
        for o in p.all_outputs(unique=True):
            if i.name == o.name:
                outputs.append(o)
                continue
    return outputs

def choose_concentration(output, args):
    conc_hs = output.udf.get(args.concUdfHS)
    conc_br = output.udf.get(args.concUdfBR)
    conc_qb = output.udf.get(args.concUdfQB)
    conc_chosen = output.udf.get(args.concUdfChosen)
    if conc_hs is None: # conc_hs is mandatory
        raise(RuntimeError("Error! Sample '%s' is missing UDF '%s'!" % (output.name, args.concUdfHS)))
#    elif conc_chosen is None: # conc_chosen is mandatory
#        raise(RuntimeError("Error! Sample '%s' is missing UDF '%s'!" % (output.name, args.concUdfChosen)))

    if conc_qb is not None:
        conc_selected = conc_qb
    elif conc_br is not None:
        conc_selected = conc_br
    else:
        conc_selected = conc_hs

    return conc_selected

def main(lims, args, logger):
    p = Process(lims, id=args.pid)

    operator, threshold = parse_qc_condition(args.qcPassCondition)
    if args.qcPassCondition2:
        operator2, threshold2 = parse_qc_condition(args.qcPassCondition2)

    for i, output in enumerate(get_outputs(p)):
        concentration = choose_concentration(output, args)
        output.udf[args.concUdfChosen] = concentration
        
        qc_pass = check_qc_pass(concentration, operator, threshold)
        qc_flag = 'PASSED' if qc_pass else 'FAILED'

        if args.qcPassCondition2:
            qc_pass2 = check_qc_pass(concentration, operator, threshold)
            # set qc flag based on both conditions
            qc_flag = 'PASSED' if (qc_pass and qc_pass2) else 'FAILED'

        output.qc_flag = qc_flag

#    # create fluent file
#    fluent_file = get_file_artifact(p, args.fluentNormalizationFilename)
#    if fluent_file:
#
#    # create overview file
#    overview_file = get_file_artifact(p, args.overviewFilename)
#    if overview_file:

    for i, output in enumerate(get_outputs(p)):
        output.put()

#    workbook = xlrd.open_workbook(file_contents=sparkfile.read())
#    sheet = workbook.sheet_by_index(0)
#
#    well_re = re.compile("[A-Z][0-9]{1,2}")
#
#    for row_i in range(0, sheet.nrows):
#        if is_well(sheet.cell(row_i, 0).value, well_re):
#            well = sheet.cell(row_i, 0).value
#            artifact = find_input_in_well(well, p)
#            if not artifact:
#                raise(RuntimeError("Error! Cannot find sample at well position %s, row %s" % (well, row_i)))
#
#            concentration = sheet.cell(row_i, 2).value
#            if concentration == "NoCalc":
#                concentration = sheet.cell(row_i, 1).value
#            concentration = format_concentration(concentration)
#
#            output = find_output_artifact(artifact.name, p)
#            output.udf[args.concentrationUdf] = concentration
#            output.put()

if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--pid', required=True, help='LIMS ID for current Process')
#    parser.add_argument('--fluentNormalizationFilename', required=True, help='LIMS name of the Fluent Normalization file to be downloaded')
#    parser.add_argument('--overviewFilename', required=True, help='LIMS name of the Overview file to be downloaded')
    parser.add_argument('--concUdfHS', default='QuantIt HS Concentration', help='Name of the HighSensitivity concentration UDF')
    parser.add_argument('--concUdfBR', default='QuantIt BR Concentration', help='Name of the BroadRange concentration UDF')
    parser.add_argument('--concUdfQB', default='Qubit Concentration', help='Name of the Qubit concentration UDF')
    parser.add_argument('--concUdfChosen', default='Concentration', help='Name of the concentration UDF to be set as the chosen concentration')
    parser.add_argument('--qcPassCondition', required=True, help='The condition for passing QC. e.g. <10.4')
    parser.add_argument('--qcPassCondition2', help='An optional second condition for passing QC. e.g. <10.4')

    args = parser.parse_args()
    lims = Lims(BASEURI, USERNAME, PASSWORD)

    main(lims, args, None)
    print("Successful assignment!")
