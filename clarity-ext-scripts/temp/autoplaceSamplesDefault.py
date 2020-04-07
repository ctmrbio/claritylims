import sys
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = ""
VERSION = ""
BASE_URI = ""

DEBUG = False
api = None

ARTIFACTS = None
CACHE_IDS = []
I2OMap = {} # A mapping of inputs to their outputs

def setupGlobalsFromURI( uri ):

	global HOSTNAME
	global VERSION
	global BASE_URI

	tokens = uri.split( "/" )
	HOSTNAME = "/".join(tokens[0:3])
	VERSION = tokens[4]
	BASE_URI = "/".join(tokens[0:5]) + "/"

	if DEBUG is True:
		print HOSTNAME
		print BASE_URI

def getStepConfiguration( ):

        # Fetch https://ctmr-lims-stage.scilifelab.se/api/v2/steps/24-38730/ and just return
        # the configuration part, i.e.
        # https://ctmr-lims-stage.scilifelab.se/api/v2/steps/24-38730/
	response = ""

	if len( args[ "stepURI" ] ) > 0:
		stepXML = api.getResourceByURI( args[ "stepURI" ] )
		stepDOM = parseString( stepXML )
		nodes = stepDOM.getElementsByTagName( "configuration" )
		if nodes:
			response = nodes[0].toxml()

	return response

def cacheArtifact( limsid ):

	global CACHE_IDS

	if limsid not in CACHE_IDS:
		CACHE_IDS.append( limsid )

def prepareCache():

	global ARTIFACTS

	lXML = '<ri:links xmlns:ri="http://genologics.com/ri">'

	for limsid in CACHE_IDS:
		link = '<link uri="' + BASE_URI + 'artifacts/' + limsid + '" rel="artifacts"/>'
		lXML += link
	lXML += '</ri:links>'

	mXML = api.getBatchResourceByURI( BASE_URI + "artifacts/batch/retrieve", lXML )
	ARTIFACTS = parseString( mXML )

def getArtifact( limsid ):

	response = None

	elements = ARTIFACTS.getElementsByTagName( "art:artifact" )
	for artifact in elements:
		climsid = artifact.getAttribute( "limsid" )
		if climsid == limsid:
			response = artifact

	return response

def createContainer( type, name ):

	response = ""

	if type == '96':
		cType = '1'
		cTypeName = "96 well plate"
	elif type == '384':
		cType = '3'
		cTypeName = "384 well plate"

	xml ='<?xml version="1.0" encoding="UTF-8"?>'
	xml += '<con:container xmlns:con="http://genologics.com/ri/container">'
	xml += '<name>' + name + '</name>'
	xml += '<type uri="' + BASE_URI + 'containertypes/' + cType + '" name="' + cTypeName + '"/>'
	xml += '</con:container>'

	response = api.createObject( xml, BASE_URI + "containers" )

	rDOM = parseString( response )
	Nodes = rDOM.getElementsByTagName( "con:container" )
	if Nodes:
		temp = Nodes[0].getAttribute( "limsid" )
		response = temp

	return response

def autoPlace():

	global I2OMap

	c96 = createContainer( '96', '96 WP' )

	## step one: get the process XML
	pURI = BASE_URI + "processes/" + args[ "limsid" ]
	pXML = api.getResourceByURI( pURI )
	pDOM = parseString( pXML )

	IOMaps = pDOM.getElementsByTagName( "input-output-map" )

	for IOMap in IOMaps:

		output = IOMap.getElementsByTagName( "output" )
		oType = output[0].getAttribute( "output-type" )

		## switch these lines depending upon whether you are placing ResultFile measurements, or real Analytes
		if oType == "Analyte":
		##if oType == "ResultFile":

			limsid = output[0].getAttribute( "limsid" )
			cacheArtifact( limsid )
			nodes = IOMap.getElementsByTagName( "input" )
			iLimsid = nodes[0].getAttribute( "limsid" )
			cacheArtifact( iLimsid )

			## create a map entry
			if not iLimsid in I2OMap.keys():
				I2OMap[ iLimsid ] = []
			temp = I2OMap[ iLimsid ]
			temp.append( limsid )
			I2OMap[ iLimsid ] = temp


	## build our cache of Analytes
	prepareCache()

	pXML = '<?xml version="1.0" encoding="UTF-8"?>'
	pXML += ( '<stp:placements xmlns:stp="http://genologics.com/ri/step" uri="' + args[ "stepURI" ] +  '/placements">' )
	pXML += ( '<step uri="' + args[ "stepURI" ] + '"/>' )
	pXML += getStepConfiguration()
	pXML += '<selected-containers>'
	pXML += ( '<container uri="' + BASE_URI + 'containers/' + c96 + '"/>' )
	pXML += '</selected-containers><output-placements>'

	## let's process our cache, one input at a time
	for key in I2OMap:

		## get the well position for the input
		iDOM = getArtifact( key )
		nodes = iDOM.getElementsByTagName( "value" )
		iWP = api.getInnerXml( nodes[0].toxml(), "value" )
		## well placement should always contain a :
		if iWP.find( ":" ) == -1:
			print( "WARN: Unable to determine well placement for artifact " + key )
			break

		outs = I2OMap[ key ]
		print( key + str(outs) )
		for output in outs:
			oDOM = getArtifact( output )
			oURI = oDOM.getAttribute( "uri" )

			oWP = iWP

			plXML = '<output-placement uri="' + oURI + '">'
			plXML += ( '<location><container uri="' + BASE_URI + 'containers/' + c96 + '" limsid="' + c96 + '"/>' )
			plXML += ( '<value>' + oWP + '</value></location></output-placement>' )

			pXML += plXML

	pXML += '</output-placements></stp:placements>'

	rXML = api.createObject( pXML, args[ "stepURI" ] + "/placements" )
	rDOM = parseString( rXML )
	nodes = rDOM.getElementsByTagName( "output-placement" )
	if nodes:
		msg = "Auto-placement of replicates occurred successfully"
		api.reportScriptStatus( args[ "stepURI" ], "OK", msg )
	else:
		msg = "An error occurred trying to auto-place these replicates"
		msg = msg + rXML
		print msg
		api.reportScriptStatus( args[ "stepURI" ], "WARN", msg )

def main():

	global api
	global args

	args = {}

	opts, extraparams = getopt.getopt(sys.argv[1:], "l:u:p:s:")

	for o,p in opts:
		if o == '-l':
			args[ "limsid" ] = p
		elif o == '-u':
			args[ "username" ] = p
		elif o == '-p':
			args[ "password" ] = p
		elif o == '-s':
			args[ "stepURI" ] = p
                        # http://localhost:9080/api/v2/steps/24-38717

	setupGlobalsFromURI( args[ "stepURI" ] )
	api = glsapiutil.glsapiutil()
	api.setHostname( HOSTNAME )
	api.setVersion( VERSION )
	api.setup( args[ "username" ], args[ "password" ] )

	## at this point, we have the parameters the EPP plugin passed, and we have network plumbing
	## so let's get this show on the road!

	autoPlace()

if __name__ == "__main__":
	main()
