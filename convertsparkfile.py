# -*- coding: utf-8 -*-

from StringIO import StringIO
from lxml import etree
import argparse
import glsapiutil
import pycurl
import re
import requests

__author__ = "CTMR, Kim Wong"
__date__ = "2018"
__doc__ = """
Take the default output file from a Tecan Spark and convert it to a
CSV file which can be easily parsed by the built-in parseCSV script
for concentration upload.
Converts >Max to 99.9 and <Min to 0.0.

A file looking like this:
A1,1.1234,NoCalc
B1,2.3456,NoCalc
C1,1.1234,NoCalc
D1,>Max,NoCalc
E1,1.1234,NoCalc

Will be converted to a file looking like this:
SampleID Concentration
Test Container_A1,1.1234
Test Container_B1,2.3456
Test Container_D1,99.9
Test Container_E1,1.1234
"""
import xlrd

HOSTNAME = "https://ctmr-lims-stage.scilifelab.se"
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"

well_list = []
luid_list = []

def get_file_URI(fileLUID):
   return BASE_URI + "files/" + fileLUID + "/download"

def extract_xml(username, password, url):
    """Extracts the individual XML structures from the given path.
    """
    c = pycurl.Curl()
    c.setopt(c.USERPWD, "%s:%s" % (username, password))
    c.setopt(c.URL, url)
    curl_buffer = StringIO()
    c.setopt(c.WRITEFUNCTION, curl_buffer.write)
    c.perform()
    c.close()
    xml = etree.fromstring(curl_buffer.getvalue())
    return xml

def extract_file_lims_id(xml):
    """Extracts the URI part of the element found in the artifact XML
    <file:file limsid=“40-1333” uri=“https://ctmr-lims-stage.scilifelab.se/api/v2/files/40-1333”/>
    """
    tags = xml.findall('{' + xml.nsmap['file'] + '}file')
    if len(tags) == 0:
        return None
    for tag in tags:
        file_limsid = tag.attrib['limsid']
        file_uri = tag.attrib['uri']

        return file_limsid

def is_well(string):
    well_re = re.compile("[A-Z][0-9]{1,2}")
    return well_re.match(string)

def spark_conversion(username, password, artifacts_URI, input_file_luid, new_csv_filename):
    input_file_xml = extract_xml(username, password, artifacts_URI + input_file_luid)
    input_file_lims_id = extract_file_lims_id(input_file_xml)
    download_uri = get_file_URI(input_file_lims_id)
    input_file = requests.get(download_uri, auth=(username, password))
    # temp file, just for iterating through
    with open("tempfile.xlsx", 'wb') as f:
        for chunk in input_file.iter_content():
            f.write(chunk)

    with open(new_csv_filename, 'w') as f:
        # empty file if it exists
        f.write("SampleID,Concentration\n")
        pass
    workbook = xlrd.open_workbook("tempfile.xlsx")
    sheet = workbook.sheet_by_index(0)
    container_id = str(sheet.cell(0, 0).value)
    if is_well(container_id):
        raise ValueError("Cell A1 must have the container name!")

    conc_col = 1 # the column where the concentration value lies
    if str(sheet.cell(1, 1).value) == "NoCalc":
        # this may possibly be the other column
        conc_col = 2

    for row in range(1, sheet.nrows):
        well = sheet.cell(row, 0).value
        if not is_well(well):
            continue

        measurement = str(sheet.cell(row, 1).value)
        if measurement == '>Max':
            measurement = '99.9'
        elif measurement == '<Min':
            measurement = '0.0'

        with open(new_csv_filename, 'a') as f:
            f.write(container_id + "_" + well)
            f.write(",")
            f.write(measurement)
            f.write("\n")

if __name__ == "__main__":
    """See __doc__ at the top of this file for a description."""
    parser = argparse.ArgumentParser(description='Convert Tecan Spark output file into LIMS-friendly CSV and upload the well concentrations.')
    parser.add_argument('-u', '--username', required=True, help='username')
    parser.add_argument('-p', '--password', required=True, help='password')
    parser.add_argument('-f', '--newCSVFilename', required=True, help='uri of the process')
    parser.add_argument('-a', '--artifactsURI', required=True, help='artifacts uri')
    parser.add_argument('-i', '--inputSparkFile', required=True, help='input spark file')
    parser.add_argument('-x', '--instrumentUsed', required=True, help='instrument used')

    args = parser.parse_args()

    api = glsapiutil.glsapiutil()
    api.setHostname(HOSTNAME)
    api.setVersion(VERSION)
    api.setup(args.username, args.password)

    spark_conversion(args.username, args.password, args.artifactsURI, args.inputSparkFile, args.newCSVFilename)
    print("Conversion successful!")
