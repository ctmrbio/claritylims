from __future__ import print_function
from clarity_ext.extensions import GeneralExtension
import re

def blow(ooo, level=0):
    for mmm in dir(ooo):
        if re.search("^__.*__$", mmm):
            continue
        if mmm in ooo.__dict__:
            sss='\t'*level+'in dict'
        else:
            sss='\t'*level+'no dict'
        try:
            ttt = getattr(ooo, mmm, 'Never')
            tttttt = str(type(ttt))
            if tttttt == '<type \'instancemethod\'>':
                continue
            elif tttttt == '<type \'function\'>':
                continue
            print(sss, mmm, tttttt, ttt, sep=':\t')
        except:
            print('no attr', mmm, sep=':\t')
            continue
        if level > 1:   # This should be adjustable parameter
            continue
        if re.search("^<class.*", tttttt):
            blow(ttt, level+1)
        elif tttttt == '<type \'instance\'>':
            blow(ttt, level+1)

class Extension(GeneralExtension):
    """
    TODO: Add description
    """
    def execute(self):
        blow(self.context)

    def integration_tests(self):
        # TODO: Replace with a valid step ID
        yield "24-48532"
