__author__ = 'viking'
# fix TLM device file naming to add suffix on the TLM length
from utilities import *
import re
# renames wafers
#pathname="/carbonics/owncloudsync/X.Selected_Measurements/Wf169/Wf169meas4"
pathname="/carbonics/owncloudsync/X.Selected_Measurements/L11/L11meas1"
filenamecontains='xls'
pathname_mod=pathname+sub('DC')
newpath=pathname+'/new'
if not os.path.exists(newpath):											# if necessary, make the directory to contain the data
		os.makedirs(newpath)
filelisting = os.listdir(pathname_mod)

#patternold=re.compile(r'TLM_R[0-9]*')
#patternnew=re.compile(r'C[0-9]_R[0-9]_ORTH_*')


#
#oldname="TLM"
# newwafername="Vds_-0.01"
for fdata in filelisting:
    if 'TLM' in fdata:
        oldtlmlength="_".join(['TLM',fdata.split('TLM_')[1].split('_')[0]])
        newtlmlength="".join([oldtlmlength,'um'])
        if os.path.isfile(pathname_mod+'/'+fdata) and parse_rpn(targetfilename=fdata,expression=filenamecontains):
            print(fdata)
            dfr=open(pathname_mod+'/'+fdata,'r')
            dataf=dfr.read()
            dfr.close()
            dfw=open(newpath+'/'+fdata.replace(oldtlmlength,newtlmlength),'w')
            #fd0=fdata.split(patternold)
            #dfw=open(newpath+'/'+fdata.replace(patternold,patternnew),'w')
            print(" new name =",dfw)
            dfw.write(dataf.replace(oldtlmlength,newtlmlength))
            #dfw.write(dataf.replace(patternold,patternnew))
            dfw.close()

    #flines = [l for l in df.read().splitlines()]        # get all file lines
