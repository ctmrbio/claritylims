import sys
import getopt
import glsapiutilv2
import re

def setFinalStatus( uri, status, message ):
	
	newuri = uri + "/programstatus"

	XML = api.getResourceByURI( newuri )
	newXML = re.sub('(.*<status>)(.*)(<\/status>.*)', '\\1' + status + '\\3', XML)
	newXML = re.sub('(.*<\/status>)(.*)', '\\1' + '<message>' + message + '</message>' + '\\2', newXML)

	response = api.updateObject( newXML, newuri )

def main():

	global api

	pURI = ""
	username = ""
	password = ""
	status = ""
	message = ""
	hostname = ""

   	opts, extraparams = getopt.getopt(sys.argv[1:], "l:u:p:s:m:") 

	for o,p in opts:
		if o == '-l':
			pURI = p
			hostname = re.sub('(.*)(\/api/.*)', '\\1', pURI)

		elif o == '-u':
			username = p
		elif o == '-p':
			password = p
		elif o == '-s':
			status = p
		elif o == '-m':
			message = p

	api = glsapiutilv2.glsapiutil()
	api.setHostname( hostname )
	api.setup( username, password )

	setFinalStatus( pURI, status, message )

if __name__ == "__main__":
    main()

