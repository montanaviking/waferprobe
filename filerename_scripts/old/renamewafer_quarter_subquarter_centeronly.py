__author__ = 'viking'
# transform left and right probing to adjacent columns
# see wafer H37 slow for example
from utilities import *
# renames wafers
xlocoffset=18200
pathname="/home/viking/Desktop/phil@carbonicsinc.com/07. Measurements/T1/T1meas1"
filenamecontains='.xls'
pathname_mod=pathname+sub('DC')
newpath=pathname+'/new'
if not os.path.exists(newpath):											# if necessary, make the directory to contain the data
		os.makedirs(newpath)
filelisting = os.listdir(pathname_mod)

elimfromdev=['xls','_foc.','_transfer.','_transferloop.','.S2P']             # substrings to eliminate from filenames to form devicenames
elimfrom_proberesistancetest='TLM0.3_'                                      # remove this from the probe resistance test data files

for fnameold in filelisting:
	if os.path.isfile(pathname_mod+'/'+fnameold) and parse_rpn(targetfilename=fnameold,expression=filenamecontains):
		print(fnameold)
		dfr=open(pathname_mod+'/'+fnameold,'r')
		dataf=dfr.read()
		dfr.close()
		oldlines = [l for l in dataf.splitlines()]

		if 'RP' in fnameold:
			if 'ROW2' in fnameold: fnamenew=fnameold.replace('RP_','').replace('ROW2','ROW2_C3')
			if 'ROW3' in fnameold: fnamenew=fnameold.replace('RP_','').replace('ROW3','ROW3_C3')
			for l in oldlines:
				if 'x probeing location um' in l or 'x location um' in l:
					oldxlocprobe = l.split('\t')[1]     # find old value of xloc which will need to be modified
					oldxlocline=l                       # old line containing old x probe location
					newxlocline=l.replace(oldxlocprobe,str(int(oldxlocprobe)+xlocoffset))
					dataf=dataf.replace(oldxlocline,newxlocline)
		elif 'LP' in fnameold:
			if 'ROW2' in fnameold: fnamenew=fnameold.replace('LP_','').replace('ROW2','ROW2_C2')
			if 'ROW3' in fnameold: fnamenew=fnameold.replace('LP_','').replace('ROW3','ROW3_C2')
			for l in oldlines:
				if 'x probeing location um' in l or 'x location um' in l:
					oldxlocprobe = l.split('\t')[1]     # find old value of xloc which will need to be modified
					oldxlocline=l                       # old line containing old x probe location
					newxlocline=l.replace(oldxlocprobe,str(int(oldxlocprobe)+xlocoffset))
					dataf=dataf.replace(oldxlocline,newxlocline)

		if 'proberesistancetest' in fnamenew: fnamenew=fnamenew.replace(elimfrom_proberesistancetest,'')
		devnameold=fnameold
		devnamenew=fnamenew
		for e in elimfromdev:
			devnameold=devnameold.replace(e,'')             # form old device name
			devnamenew=devnamenew.replace(e,'')             # form new device name
		dfw=open("".join([newpath,'/',fnamenew]),'w')      # make new device file
		print(" new name =",dfw)
		dfw.write(dataf.replace(devnameold,devnamenew))         # replace all instances of old device name with the new device name in the new file and write to disk
		dfw.close()