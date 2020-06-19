__author__ = 'viking'
from utilities import *
import re
# renames wafers
#pathname="/carbonics/owncloudsync/X.Selected_Measurements/Wf169/Wf169meas4"
pathname="/carbonics/owncloudsync/X.Selected_Measurements/QH10/QH10meas12"
filenamecontains='noise'
#pathname_mod=pathname+sub('DC')
pathname_mod=pathname+"/RF"
newpath=pathname+'/new'
if not os.path.exists(newpath):											# if necessary, make the directory to contain the data
		os.makedirs(newpath)
filelisting = os.listdir(pathname_mod)

#patternold=re.compile(r'C[0-9]_R[0-9]*')
#patternnew=re.compile(r'C[0-9]_R[0-9]_ORTH_*')

oldwafername="pull_C"
newwafername="pull__C"
for fdata in filelisting:
    if os.path.isfile(pathname_mod+'/'+fdata) and parse_rpn(targetfilename=fdata,expression=filenamecontains):
        print(fdata)
        dfr=open(pathname_mod+'/'+fdata,'r')
        dataf=dfr.read()
        dfr.close()
        if oldwafername in fdata:
            dfw=open(newpath+'/'+fdata.replace(oldwafername,newwafername),'w')
        #fd0=fdata.split(patternold)
        #dfw=open(newpath+'/'+fdata.replace(patternold,patternnew),'w')
            print(" new name =",dfw)
            dfw.write(dataf.replace(oldwafername,newwafername))
        #dfw.write(dataf.replace(patternold,patternnew))
            dfw.close()
