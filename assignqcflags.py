import argparse
from lxml import etree
import pycurl
from StringIO import StringIO

import glsapiutil

__author__ = "CTMR, Kim Wong"
__date__ = "2018"
__doc__ = """
Assign the QC flags to samples based on the uploaded concentration.
Written as a learning exercise and to replace the in-built Assign QC Flags
script which does not work in LIMS version 5.0.4."""

HOSTNAME = "https://ctmr-lims.scilifelab.se"
VERSION = "v2"

def less_equal(a, b):
   return a <= b

def greater_equal(a, b):
   return a >= b

def equal(a, b):
   return a == b

def not_equal(a, b):
   return a != b

operator_map = {
   '<=': less_equal,
   '>=': greater_equal,
   '=': equal,
   '==': equal,
   '!=': not_equal,
}

def check_qc_pass(value, operator, threshold):
    return operator_map[operator](value, threshold)

def determine_qc_flag(concentration, operator, threshold):
    flag = check_qc_pass(concentration, operator, threshold)
    return 'PASSED' if flag else 'FAILED'

def extract_xml(username, password, artifactsURI, outputFileLuid):
    """Extracts the individual XML structures from the given
    artifact outputFileLuid.
    """
    url = artifactsURI + outputFileLuid

    c = pycurl.Curl()
    c.setopt(c.USERPWD, "%s:%s" % (username, password))
    c.setopt(c.URL, url)
    curl_buffer = StringIO()
    c.setopt(c.WRITEFUNCTION, curl_buffer.write)
    c.perform()
    c.close()
    xml = etree.fromstring(curl_buffer.getvalue())
    return xml

def extract_udf_from_xml(xml, udf_name):
    """Extracts a UDF from an XML element.
    TODO: implement different type handling
    """
    # a bit hacky, but xml.findall('udf:field', xml.nsmap) as in this
    # link doesn't seem to work, so...
    #https://stackoverflow.com/questions/14853243/parsing-xml-with-namespace-in-python-via-elementtree
    tags = xml.findall('{' + xml.nsmap['udf'] + '}field')
    if len(tags) == 0:
        return None
    for tag in tags:
        tag_attribs = tag.attrib
        udf_type = tag_attribs['type']
        udf_name_ = tag_attribs['name']
        if udf_name_ == udf_name:
            return tag.text

def update_qc_flag(input_xml, qc_flag):
    tag = input_xml.find('qc-flag')
    if tag is not None:
        tag.text = qc_flag
        input_xml
    else:
        raise AttributeError("The given XML does not have a qc-flag!")

    return input_xml

def run_put_request(username, password, artifactsURI, outputFileLuid, xml_data):
    curl_buffer = StringIO()

    url = artifactsURI + outputFileLuid
    post_data = etree.tostring(xml_data)

    c = pycurl.Curl()
    c.setopt(c.USERPWD, "%s:%s" % (username, password))
    c.setopt(c.URL, url)
    c.setopt(c.WRITEFUNCTION, curl_buffer.write)
    header = [
        'Content-Type: application/xml',
        'Accept: application/xml'
    ]
    c.setopt(c.HTTPHEADER, header)
    c.setopt(c.CUSTOMREQUEST, "PUT")
    c.setopt(c.POSTFIELDS, post_data)
    c.perform()
    c.close()
    
    return curl_buffer.getvalue()

def determine_and_set_qc_flags(username, password, artifactsURI, outputFileLuids, operator, threshold):
    threshold = float(threshold)
    for luid in outputFileLuids:
        xml = extract_xml(username, password, artifactsURI, luid)
        concentration = extract_udf_from_xml(xml, 'Concentration')
        if concentration:
            concentration = float(concentration)
        qc_flag = determine_qc_flag(concentration, operator, threshold)
        modified_xml = update_qc_flag(xml, qc_flag)
        run_put_request(username, password, artifactsURI, luid, modified_xml)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse concentrations and modify QC flags')
    parser.add_argument('-u', '--username', required=True, help='username')
    parser.add_argument('-p', '--password', required=True, help='password')
    parser.add_argument('-o', '--operator', required=True, help='comparison operator')
    parser.add_argument('-t', '--threshold', required=True, help='concentration threshold')
    parser.add_argument('-a', '--artifactsURI', required=True, help='artifacts uri')
    parser.add_argument('-x', '--outputFileLuids', required=True, help='output file luids')

    args = parser.parse_args()

    api = glsapiutil.glsapiutil()
    api.setHostname(HOSTNAME)
    api.setVersion(VERSION)
    api.setup(args.username, args.password)

    outputFileLuids = args.outputFileLuids.split(' ')

    determine_and_set_qc_flags(args.username, args.password, args.artifactsURI, outputFileLuids, args.operator, args.threshold)

""" Example XML of a relevant artifact:
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<art:artifact xmlns:udf="http://genologics.com/ri/userdefined" xmlns:file="http://genologics.com/ri/file" xmlns:art="http://genologics.com/ri/artifact" uri="http://localhost:9080/api/v2/artifacts/92-37152?state=22418" limsid="92-37152">
    <name>DHR003_working</name>
    <type>ResultFile</type>
    <output-type>ResultFile</output-type>
    <parent-process uri="http://localhost:9080/api/v2/processes/24-8222" limsid="24-8222"/>
    <qc-flag>UNKNOWN</qc-flag>
    <sample uri="http://localhost:9080/api/v2/samples/WON301A292" limsid="WON301A292"/>
    <reagent-label name="Fecal"/>
    <udf:field type="Numeric" name="Concentration">6.6054</udf:field>
    <workflow-stages/>
</art:artifact>
"""
