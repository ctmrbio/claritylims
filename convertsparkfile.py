import argparse
import xlrd
#from StringIO import StringIO
#import pycurl
#from lxml import etree

#import glsapiutil

__author__ = "CTMR, Kim Wong"
__date__ = "2018"
__doc__ = """
Take the default output file from a Tecan Spark and convert it to a
CSV file which can be easily parsed by the built-in parseCSV script
for concentration upload.
Converts >Max to 99.9 and <Min to 0.0.

A file looking like this:
A1,1.1234
B1,2.3456
C1,1.1234
D1,>Max
E1,1.1234


Will be converted to a file looking like this:
SampleID Concentration
Test Container_A1,1.1234
Test Container_B1,2.3456
Test Container_C1,1.1234
Test Container_D1,99.9
Test Container_E1,1.1234
"""

HOSTNAME = "https://ctmr-lims.scilifelab.se"
VERSION = "v2"

#def check_qc_pass(value, operator, threshold):
#    return operator_map[operator](value, threshold)
#
#def determine_qc_flag(concentration, operator, threshold):
#    flag = check_qc_pass(concentration, operator, threshold)
#    return 'PASSED' if flag else 'FAILED'
#
#def extract_xml(username, password, artifactsURI, outputFileLuid):
#    """Extracts the individual XML structures from the given
#    artifact outputFileLuid.
#    """
#    url = artifactsURI + outputFileLuid     
#    c = pycurl.Curl()
#    c.setopt(c.USERPWD, "%s:%s" % (username, password))
#    c.setopt(c.URL, url)
#    curl_buffer = StringIO()
#    c.setopt(c.WRITEFUNCTION, curl_buffer.write)
#    c.perform()
#    c.close()
#    xml = etree.fromstring(curl_buffer.getvalue())
#    return xml
#
#def extract_udf_from_xml(xml, udf_name):
#    """Extracts a UDF from an XML element.
#    TODO: implement different type handling
#    """
#    # a bit hacky, but xml.findall('udf:field', xml.nsmap) as in this
#    # link doesn't seem to work, so...
#    #https://stackoverflow.com/questions/14853243/parsing-xml-with-namespace-in-python-via-elementtree
#    tags = xml.findall('{' + xml.nsmap['udf'] + '}field')
#    if len(tags) == 0:
#        return None
#    for tag in tags:
#        tag_attribs = tag.attrib
#        udf_type = tag_attribs['type']
#        udf_name_ = tag_attribs['name']
#        if udf_name_ == udf_name:
#            return tag.text
#
#def update_qc_flag(input_xml, qc_flag):
#    tag = input_xml.find('qc-flag')
#    if tag is not None:
#        tag.text = qc_flag
#        input_xml
#    else:
#        raise AttributeError("The given XML does not have a qc-flag!")
#
#    return input_xml
#
#def run_put_request(username, password, artifactsURI, outputFileLuid, xml_data):
#    curl_buffer = StringIO()
#
#    url = artifactsURI + outputFileLuid
#    post_data = etree.tostring(xml_data)
#
#    c = pycurl.Curl()
#    c.setopt(c.USERPWD, "%s:%s" % (username, password))
#    c.setopt(c.URL, url)
#    c.setopt(c.WRITEFUNCTION, curl_buffer.write)
#    header = [
#        'Content-Type: application/xml',
#        'Accept: application/xml'
#    ]
#    c.setopt(c.HTTPHEADER, header)
#    c.setopt(c.CUSTOMREQUEST, "PUT")
#    c.setopt(c.POSTFIELDS, post_data)
#    c.perform()
#    c.close()
#
#    return curl_buffer.getvalue()

def get_container_name():
    # need to get the container name to append it to the wells
    return "Test Container"

def reformat_file(username, password, input_file, output_file, log_file):
    with open(output_file, 'w') as f_out:
        f_out.write("SampleID,Concentration\n")

        container_name = get_container_name()

        print(input_file)
        workbook = xlrd.open_workbook(input_file)
        sheet = workbook.sheet_by_index(0)
        for row in range(0, sheet.nrows):
            well = sheet.cell(row, 0).value
            measurement = str(sheet.cell(row, 1).value)
            if measurement == '':
                continue

            if measurement == '>Max':
                measurement = '99.9'
            elif measurement == '<Min':
                measurement = '0.0'

            f_out.write(container_name + "_" + well + "," + measurement + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert Tecan Spark output file into LIMS-friendly CSV')
    parser.add_argument('-u', '--username', required=True, help='username')
    parser.add_argument('-p', '--password', required=True, help='password')
    parser.add_argument('-i', '--inputSparkFile', required=True, help='input spark file')
    parser.add_argument('-l', '--outputLogFile', required=True, help='input spark file')
    parser.add_argument('-o', '--outputCSVFile', required=True, help='input spark file')

    args = parser.parse_args()

#    api = glsapiutil.glsapiutil()
#    api.setHostname(HOSTNAME)
#    api.setVersion(VERSION)
#    api.setup(args.username, args.password)

    reformat_file(args.username, args.password, args.inputSparkFile, args.outputCSVFile, args.outputLogFile)
