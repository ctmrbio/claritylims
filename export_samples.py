DESC = """Create an overview excel file on the Aggregate QC step""" 

from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.lims import Lims
import genologics
import sys
import xlwt

def main(lims):
    containers = [
        "27-1449",
        "27-1967",
        "27-1453",
        "27-2014",
        "27-1988",
    ]
    for container in containers:
        arts = lims.get_artifacts(containerlimsid=container)
        new_workbook = xlwt.Workbook()
        new_sheet = new_workbook.add_sheet('Sheet 1')
        new_sheet.write(0, 0, container)
        for i, artifact in enumerate(arts):
            sample_name = artifact.name
            container_name = artifact.location[0].name
            well = artifact.location[1]
            #print("%s / %s" % (container_name, container))
            print("%s,%s" % (sample_name, well))
            for col, field in enumerate([sample_name, container_name, well]):
                new_sheet.write(i + 1, col, field)
        new_workbook.save("sample_list_%s.xls" % container)

if __name__ == "__main__":
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims)
