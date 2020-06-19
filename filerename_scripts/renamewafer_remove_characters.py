__author__ = 'viking'
from utilities import *
import re
# renames wafers removing set of characters from name
#pathname="/carbonics/owncloudsync/X.Selected_Measurements/Wf169/Wf169meas4"
pathname="/carbonics/owncloudsync/X.Selected_Measurements/QH28/QH28meas4"
filenamecontains='QH'
#pathname_mod=pathname+sub('DC')
pathname_mod=pathname+"/RF_noise_allfreq_4"
newpath=pathname+'/new'
if not os.path.exists(newpath):											# if necessary, make the directory to contain the data
		os.makedirs(newpath)
filelisting = os.listdir(pathname_mod)

#patternold=re.compile(r'C[0-9]_R[0-9]*')
#patternnew=re.compile(r'C[0-9]_R[0-9]_ORTH_*')

startpositionstring="Vds"
endpositionstring="Vds"

for fdata in filelisting:
    startindex=fdata.find(startpositionstring)
    endindex=fdata.find(endpositionstring,startindex+1)
    newfilename=fdata[:startindex]+fdata[endindex:]
    if os.path.isfile(pathname_mod+'/'+fdata) and parse_rpn(targetfilename=fdata,expression=filenamecontains):
        print(fdata)
        dfr=open(pathname_mod+'/'+fdata,'r')
        dataf=dfr.read()
        dfr.close()
        dfw=open(newpath+'/'+newfilename,'w')
        olddevicename=fdata.split(fdata.split("_")[-1])[0][:-1]
        newdevicename=newfilename.split(newfilename.split("_")[-1])[0][:-1]
        print(" new name =",dfw)
        dfw.write(dataf.replace(olddevicename,newdevicename))
        dfw.close()
