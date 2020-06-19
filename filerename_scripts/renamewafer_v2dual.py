__author__ = 'viking'
# transform left and right probing to adjacent columns using present columns test2
from utilities import *
# renames wafers
xlocoffset=1750
pathname="/carbonics/owncloudsync/X.Selected_Measurements/L15/L15meas2"
#pathname='/home/viking/ownCloud/X.Selected_Measurements/L16/L16meas1'
filenamecontains='.xls'
pathname_mod=pathname+sub('DC')
newpath=pathname+'/new'
if not os.path.exists(newpath):											# if necessary, make the directory to contain the data
		os.makedirs(newpath)
filelisting = os.listdir(pathname_mod)

elimfromdev=['xls','_foc.','_transfer.','_transferloop.','_transferloop4.','.S2P','_pulseddraintimedomain.','_pulsedtimedomain.','_loop4foc.','_loopfoc.']             # substrings to eliminate from filenames to form devicenames
#elimfrom_proberesistancetest='D11_'                                      # remove this from the probe resistance test data files

for fnameold in filelisting:
	if os.path.isfile(pathname_mod+'/'+fnameold) and parse_rpn(targetfilename=fnameold,expression=filenamecontains):
		print(fnameold)
		dfr=open(pathname_mod+'/'+fnameold,'r')
		dataf=dfr.read()
		dfr.close()
		oldlines = [l for l in dataf.splitlines()]

		#colnumberold=fnameold[fnameold.index('_C')+2]
		colnumberold=fnameold.split('_C')[1].split('_')[0].strip()
		if '_RP_' in fnameold:
			colnumbernew=str(int(colnumberold)+1)
			fnamenew=fnameold.replace('RP_','').replace('C'+colnumberold,'C'+colnumbernew)
			#fnamenew = fnameold.replace('_RP', '').replace('C' + colnumberold, 'C' + colnumbernew)
			for l in oldlines:
				if 'x probeing location um' in l or 'x location um' in l:
					oldxlocprobe = l.split('\t')[1]     # find old value of xloc which will need to be modified
					oldxlocline=l                       # old line containing old x probe location
					newxlocline=l.replace(oldxlocprobe,str(int(oldxlocprobe)+xlocoffset))
					dataf=dataf.replace(oldxlocline,newxlocline)
		elif '_LP_' in fnameold:
			fnamenew=fnameold.replace('LP_','')
			#fnamenew = fnameold.replace('_LP', '')

		#if 'proberesistancetest' in fnamenew: fnamenew=fnamenew.replace(elimfrom_proberesistancetest,'')
		devnameold=fnameold
		devnamenew=fnamenew
		for e in elimfromdev:
			devnameold=devnameold.replace(e,'')             # form old device name
			devnamenew=devnamenew.replace(e,'')             # form new device name
		dfw=open("".join([newpath,'/',fnamenew]),'w')      # make new device file
		#print(" new name =",dfw)
		print(" new name =", devnameold, devnamenew)
		dfw.write(dataf.replace(devnameold,devnamenew))         # replace all instances of old device name with the new device name in the new file and write to disk
		dfw.close()