# -*- coding: utf-8 -*-

import csv
import io
from lxml import etree
import argparse
import glsapiutil3
import pycurl
import re
import requests

__author__ = "CTMR, Kim Wong"
__date__ = "2018"
__doc__ = """
Using the input sample "Concentration (nM)" UDF, plus the step UDFs
"Target Concentration (nM)" and "Target Volume (uL)", this script
creates a CSV file for input on the Tecan 
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

HOSTNAME = "https://ctmr-lims-prod.scilifelab.se"
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"

well_list = []
luid_list = []

def calculate_sample_required(conc1, conc2, vol2):
    """Classic C1V1 = C2V2. Calculates V1.
    All arguments should be floats.
    """
    return (conc2 * vol2) / conc1

def calculate_volumes_required(sample_conc, target_concentration, target_volume):
    """Returns a tuple of the sample volume (s) and water volume (w)
    which should be input into the robot. All values should be floats.
    """
    sample_required = calculate_sample_required(sample_conc, target_concentration, target_volume)
    water_required = target_volume - sample_required
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

def create_normalisation_csv(username, password, artifacts_uri, output_file_luids, new_csv_filename, log_filename, target_concentration, target_volume):
    target_concentration = float(target_concentration)
    target_volume = float(target_volume)

    with open(new_csv_filename, 'w', newline='') as csvfile:
        pass

    for luid in output_file_luids:
        xml = extract_xml(username, password, artifacts_uri, luid)
        concentration = extract_udf_from_xml(xml, "Concentration")
        if concentration:
            concentration = float(concentration)
            sample_required, water_required = calculate_volumes_required(concentration, target_concentration, target_volume)
        else:
            raise RuntimeError("Could not find UDF 'Concentration' of sample '%s'" % luid)
        well = "A1" # temporary lol
        with open(new_csv_filename, 'a') as f:
            csv_writer = csv.writer(csvfile, delimiter=' ')
            csv_writer.writerow([well, water_required, sample_required])

if __name__ == "__main__":
    """See __doc__ at the top of this file for a description."""
    parser = argparse.ArgumentParser(description='Convert Tecan Spark output file into LIMS-friendly CSV and upload the well concentrations.')
    parser.add_argument('-u', '--username', required=True, help='username')
    parser.add_argument('-p', '--password', required=True, help='password')
    parser.add_argument('-a', '--artifactsURI', required=True, help='artifacts uri')
    parser.add_argument('-x', '--outputFileLuids', required=True, help='output file luids')
    parser.add_argument('-f', '--newCSVFilename', required=True, help='limsid of the csv file to write to')
    parser.add_argument('-l', '--logFilename', required=True, help='limsid of the log file to write to')
    parser.add_argument('-c2', '--targetConcentration', required=True, help='target concentration')
    parser.add_argument('-v2', '--targetVolume', required=True, help='target volume')

    args = parser.parse_args()

    api = glsapiutil3.glsapiutil3()
    api.setHostname(HOSTNAME)
    api.setVersion(VERSION)
    api.setup(args.username, args.password)

    outputFileLuids = args.outputFileLuids.split(' ')

    create_normalisation_csv(args.username, args.password, args.artifactsURI, outputFileLuids, args.newCSVFilename, args.logFilename, args.targetConcentration, args.targetVolume)
    )
    print("Creation successful!")
