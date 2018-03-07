from __future__ import print_function
import argparse

import xml.dom.minidom
from xml.dom.minidom import parseString

import glsapiutil

HOSTNAME = "https://ctmr-lims.scilifelab.se"
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
CACHE_IDS = []


def getStepConfiguration(stepURI):
	stepXML = api.getResourceByURI(stepURI)
	stepDOM = parseString(stepXML)
	nodes = stepDOM.getElementsByTagName("configuration")
	if nodes:
		return nodes[0].toxml()
	else:
		return None


def cacheArtifact(limsid):
	if limsid not in CACHE_IDS:
		CACHE_IDS.append(limsid)


def prepareCache():
	lXML = '<ri:links xmlns:ri="http://genologics.com/ri">'
	for limsid in CACHE_IDS:
		link = '<link uri="' + BASE_URI + 'artifacts/' + limsid + '" rel="artifacts"/>'
		lXML += link
	lXML += '</ri:links>'
	mXML = api.getBatchResourceByURI(BASE_URI + "artifacts/batch/retrieve", lXML)
	ARTIFACTS = parseString(mXML)
	return ARTIFACTS


def getArtifact(ARTIFACTS, limsid):
	elements = ARTIFACTS.getElementsByTagName("art:artifact")
	for artifact in elements:
		climsid = artifact.getAttribute("limsid")
		if climsid == limsid:
			return artifact


def createContainer(container_type, name):
	if container_type == '96':
		cType = '1'
		cTypeName = "96 well plate"
	elif container_type == '48':
		cType = '54'
		cTypeName = "48 tube rack individual coded"
	elif container_type == '384':
		cType = '3'
		cTypeName = "384 well plate"

	xml ='<?xml version="1.0" encoding="UTF-8"?>'
	xml += '<con:container xmlns:con="http://genologics.com/ri/container">'
	xml += '<name>' + name + '</name>'
	xml += '<type uri="' + BASE_URI + 'containertypes/' + cType + '" name="' + cTypeName + '"/>'
	xml += '</con:container>'

	response = api.createObject(xml, BASE_URI + "containers")

	rDOM = parseString(response)
	nodes = rDOM.getElementsByTagName("con:container")
	if nodes:
		response = nodes[0].getAttribute("limsid")

	return response


def autoPlace(api, limsid, stepURI, container_type, container_name):
	container = createContainer(container_type, container_name)

	## step one: get the process XML
	pURI = BASE_URI + "processes/" + limsid
	pXML = api.getResourceByURI(pURI)
	pDOM = parseString(pXML)

	IOMaps = pDOM.getElementsByTagName("input-output-map")

	for IOMap in IOMaps:
		output = IOMap.getElementsByTagName("output")
		oType = output[0].getAttribute("output-type")

		## switch these lines depending upon whether you are placing ResultFile measurements, or real Analytes
		if oType == "Analyte":
		##if oType == "ResultFile":

			limsid = output[0].getAttribute("limsid")
			cacheArtifact(limsid)
			nodes = IOMap.getElementsByTagName("input")
			iLimsid = nodes[0].getAttribute("limsid")
			cacheArtifact(iLimsid)

			## create a map entry
			if not iLimsid in I2OMap.keys():
				I2OMap[iLimsid] = []
			temp = I2OMap[iLimsid]
			temp.append(limsid)
			I2OMap[iLimsid] = temp

	## build our cache of Analytes
	ARTIFACTS = prepareCache()

	pXML = '<?xml version="1.0" encoding="UTF-8"?>'
	pXML += ('<stp:placements xmlns:stp="http://genologics.com/ri/step" uri="' + stepURI +  '/placements">')
	pXML += ('<step uri="' + stepURI + '"/>')
	pXML += getStepConfiguration(stepURI)
	pXML += '<selected-containers>'
	pXML += ('<container uri="' + BASE_URI + 'containers/' + container + '"/>')
	pXML += '</selected-containers><output-placements>'

	## let's process our cache, one input at a time
	for key in I2OMap:

		## get the well position for the input
		iDOM = getArtifact(ARTIFACTS, key)
		nodes = iDOM.getElementsByTagName("value")
		iWP = api.getInnerXml(nodes[0].toxml(), "value")
		## well placement should always contain a :
		if iWP.find(":") == -1:
			print("WARN: Unable to determine well placement for artifact:", key)
			break

		outs = I2OMap[key]
		print(key, str(outs))
		for output in outs:
			oDOM = getArtifact(ARTIFACTS, output)
			oURI = oDOM.getAttribute("uri")
			oWP = iWP
			plXML = '<output-placement uri="' + oURI + '">'
			plXML += ('<location><container uri="' + BASE_URI + 'containers/' + container + '" limsid="' + container + '"/>')
			plXML += ('<value>' + oWP + '</value></location></output-placement>')
			pXML += plXML

	pXML += '</output-placements></stp:placements>'

	rXML = api.createObject(pXML, stepURI + "/placements")
	rDOM = parseString(rXML)
	nodes = rDOM.getElementsByTagName("output-placement")
	if nodes:
		msg = "Auto-placement of replicates occurred successfully"
		api.reportScriptStatus(stepURI, "OK", msg)
	else:
		msg = "An error occurred trying to auto-place these replicates" = rXML
		print(msg)
		api.reportScriptStatus(stepURI, "WARN", msg)



if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Place samples')
	parser.add_argument('-l', '--limsid', help='')
	parser.add_argument('-u', '--username', help='username')
	parser.add_argument('-p', '--password', help='password')
	parser.add_argument('-s', '--stepURI', help='')
	args = parser.parse_args()

	api = glsapiutil.glsapiutil()
	api.setHostname(HOSTNAME)
	api.setVersion(VERSION)
	api.setup(args.username, args.password)

	autoPlace(api, args.limsid, args.stepURI, '96', '96 well plate')
