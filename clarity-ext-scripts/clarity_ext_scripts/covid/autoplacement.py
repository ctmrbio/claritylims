from clarity_ext.extensions import GeneralExtension
import genologics


class Extension(GeneralExtension):
    """
    Automatically places all samples in the source plate to the same position in a new target plate.

    This script should run when entering the sample placement view
    """
    def execute(self):
        for cont in self.context.input_containers:
            from datetime import datetime

            new_name = "{}-{}".format(cont.name, datetime.now().isoformat())
            #self.context.copy_container(cont, new_name, auto_place=True)

            # NOTE: We require a one-to-one mapping between inputs and outputs
            from genologics.entities import StepPlacements, Step
            import lxml.etree as etree
            #import lxml.etree as etree
            step = Step(self.context.session.api, id=self.context.session.current_step_id)
            step.get()
            print(">>>", step.configuration.uri)
            placements = StepPlacements._create(self.context.session.api, step=step, configuration=step.configuration)
            print(placements.uri)
            with open("generated.xml", "w") as fs:
                #fs.write(etree.tostring(placements.root, pretty_print=True))
                print(etree.tostring(placements.root))

            return


            for i, o in self.context.all_analytes:
                #print(i.api_resource.uri, o.api_resource.uri)
                pass

            # pXML = '<?xml version="1.0" encoding="UTF-8"?>'
            # pXML += ( '<stp:placements xmlns:stp="http://genologics.com/ri/step" uri="' + args[ "stepURI" ] +  '/placements">' )
            # pXML += ( '<step uri="' + args[ "stepURI" ] + '"/>' )
            # pXML += getStepConfiguration()
            # pXML += '<selected-containers>'
            # pXML += ( '<container uri="' + BASE_URI + 'containers/' + c96 + '"/>' )
            # pXML += '</selected-containers><output-placements>'



    def integration_tests(self):
        yield "24-38730"

exit

#import sys
#import getopt
#import xml.dom.minidom
##import glsapiutil
#from xml.dom.minidom import parseString

def getStepConfiguration( ):

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

# def getArtifact( limsid ):

# 	response = None

# 	elements = ARTIFACTS.getElementsByTagName( "art:artifact" )
# 	for artifact in elements:
# 		climsid = artifact.getAttribute( "limsid" )
# 		if climsid == limsid:
# 			response = artifact

# 	return response

def autoPlace():

	global I2OMap

        # DONE 1. Create a 96 well plate
	c96 = createContainer( '96', '96 WP' )

        # DONE 2. Get the xml for the process to get the iomap
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
	autoPlace()

if __name__ == "__main__":
	main()
