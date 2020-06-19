__author__ = 'viking'
# set device name inside files to be the same as the filename
from utilities import *
import re
# renames wafers
#pathname="/carbonics/owncloudsync/X.Selected_Measurements/Wf169/Wf169meas4"
pathname="/carbonics/owncloudsync/X.Selected_Measurements/QH5/QH5meas5"
filenamecontains='s2p'
pathname_mod=pathname+sub('SPAR')
newpath=pathname+'/new'
if not os.path.exists(newpath):											# if necessary, make the directory to contain the data
		os.makedirs(newpath)
filelisting = os.listdir(pathname_mod)


for fdata in filelisting:
	if os.path.isfile(pathname_mod+'/'+fdata) and parse_rpn(targetfilename=fdata,expression=filenamecontains):
		print(fdata)
		dfr=open(pathname_mod+'/'+fdata,'r')
		dataf=dfr.read()
		dfr.close()
		oldfirstline=dataf.split("\n")[0]

		newfirstline="\t".join([dataf.split("\t")[0],fdata.replace("_"+fdata.split("_")[-1],"")])
		dfw=open(newpath+'/'+fdata,'w')
		print(" new name =",dfw)
		dfw.write(dataf.replace(oldfirstline,newfirstline))
		dfw.close()
