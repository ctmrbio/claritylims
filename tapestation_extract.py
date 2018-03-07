from __future__ import print_function
import sys
import subprocess
import argparse

import requests
import xml.dom.minidom
import xml.etree.ElementTree as ET

from glsapiutil import glsapiutil


HOSTNAME = 'https://ctmr-lims.scilifelab.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"


def download_pdf(artifactluid_of_pdf, username, password):
    """
    Finds the file LUID from artifact LUID of the PDF
    """
    artif_URI = BASE_URI + "artifacts/" + artifactluid_of_pdf
    artGET = requests.get(artif_URI, auth=(username, password))       # GET artifact XML
    artXML = artGET.text
    root = ET.fromstring(artXML)

    #The following part doesn't make sense
    #############################################################

    fileLUID = root.findall("{http://genologics.com/ri/file}file")[0].get("limsid")
   

    #############################################################

    file_URI = BASE_URI + "files/" + fileLUID + "/download"
    fileGET = requests.get(file_URI, auth=(username, password))       # Retrieves the pdf file
    with open("frag.pdf", 'wb') as fd:
        for chunk in fileGET.iter_content():                          # Saving data stream to file in local
            fd.write(chunk)


def getartifact_batch(LUIDs):

    lXML = ['<ri:links xmlns:ri="http://genologics.com/ri">']
    for limsid in LUIDs:
        lXML.append( '<link uri="' + BASE_URI + 'artifacts/' + limsid + '" rel="artifacts"/>' )
    lXML.append('</ri:links>')
    lXML = ''.join(lXML)
    mXML = api.getBatchResourceByURI(BASE_URI + "artifacts/batch/retrieve", lXML)

    try:
        mDOM = xml.dom.minidom.parseString(mXML)
        nodes = mDOM.getElementsByTagName("art:artifact")
        if len(nodes) > 0:
            return mXML
        else:
            return None

    except xml.etree.ElementTree.ParseError as e:
        print("Could not parse xml: {}".format(mXML), e)


def make_wellmap(batchDom):
    """
    Return a dict of which sample is in which well
    """
    nodes = batchDOM.getElementsByTagName("art:artifact")
    well_map = {}
    for node in nodes:
        limsID = node.getAttribute("limsid")
        node_value = node.getElementsByTagName("value")
        well = node_value[0].firstChild.data
        place = well[0] + well[2:]
        well_map[str(place)] = str(limsID)

    return well_map


def main(startpage=10):

    #Setup the api
    api = glsapiutil()
    api.setHostname(HOSTNAME)
    api.setVersion(VERSION)
    api.setup(args.username, args.password)

    download_pdf(args.artifactLUID, args.username, args.password)

    outputfileLUIDs = args.outputfileLUIDs.split(" ")
    batchXML = getartifact_batch(outputfileLUIDs)
    batchDOM = xml.dom.minidom.parseString(batchXML)
    well_map = make_wellmap(batchDOM)

    wells = [x + str(y) for y in range(1,13) for x in 'ABCDEFGH']

    page = startpage
    for well_loc in wells:
       if well_loc in well_map.keys():
          limsid = well_map[well_loc]
          filename = limsid + "_" + well_loc
          ppmname = filename + "-000.ppm"
          jpegname = filename + "-000.jpeg"

          cmd1 = ['pdfimages', 'frag.pdf', '-j', '-f', str(page), '-l', str(page), filename]
          p1 = subprocess.Popen(cmd1)
          p1.wait()
          page += 1

          cmd2 = ['convert', ppmname, jpegname]
          p2 = subprocess.Popen(cmd2)                       #conversion to .jpeg
          p2.wait()

          cmd3 = ['rm' ,'*ppm']                             #removing ppm image so it isn't inadvertently attached
          p3 = subprocess.Popen(cmd3)
          p3.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract images from tapestation PDF')
    parser.add_argument('-a', '--artifactLUID', help='')
    parser.add_argument('-u', '--username', help='username')
    parser.add_argument('-p', '--password', help='password')
    parser.add_argument('-f', '--outputfileLUIDs', help='')
    args = parser.parse_args()
    main()
