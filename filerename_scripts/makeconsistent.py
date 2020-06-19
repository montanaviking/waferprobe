__author__ = 'viking'
from utilities import *
import re
# make internal device name consistent with filename
#pathname="/carbonics/owncloudsync/X.Selected_Measurements/Wf169/Wf169meas4"
pathname="/carbonics/owncloudsync/X.Selected_Measurements/QH28/QH28meas4"
filenamecontains='QH'
pathname_mod=pathname+sub('RF')
newpath=pathname+'/new'
if not os.path.exists(newpath):											# if necessary, make the directory to contain the data
		os.makedirs(newpath)
filelisting = os.listdir(pathname_mod)

for fdata in filelisting:
    # get device name
    suffix=fdata.split("_")[-1]
    newdevicename=fdata.split("_"+suffix)[0]
    if os.path.isfile(pathname_mod+'/'+fdata) and parse_rpn(targetfilename=fdata,expression=filenamecontains):
        print(fdata)
        dfr=open(pathname_mod+'/'+fdata,'r')
        dataf=dfr.read()
        dfr.close()
        olddevicename=""
        # now find devicename in selected file
        for l in dataf.splitlines():
            if ("device" in l.split("\t")[0]) and ("name" in l.split("\t")[0]) and ("__" not in l):
                olddevicename = l.split("\t")[1].strip()
        if olddevicename!="":
            dfw=open(newpath+'/'+fdata,'w')
            print(" file name =",dfw)
            dfw.write(dataf.replace(olddevicename,newdevicename))
            dfw.close()
        else:
            print("WARNING no file replaced for file ")
