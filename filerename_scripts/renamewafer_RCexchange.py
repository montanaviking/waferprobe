__author__ = 'viking'
# swap rows and columns. Used to translate data for V4 MAP layout rotated 90 deg counterclockwise
from utilities import *
# renames wafers
numberofcolold=25      # number of columns on 0 deg wafer layout
numberofrowold=25       # number of columns on 0 deg wafer layout
numberofcolnew=numberofrowold      # number of columns on new 90 deg wafer layout
numberofrownew=numberofcolold       # number of rows on 0 deg wafer layout
deltaxold=1750      # reticle stepsize in old 0deg x direction
deltayold=1750      # reticle stepsize in old 0deg y direction
deltaxnew=deltayold
deltaynew=deltaxold
devselectstring="_H"        # exchange rows/columns on ONLY these devices which have this substring in their device names
#maxxold=(numberofcolold-1)*deltaxold+sizeofretxold
#maxyold=(numberofrowold-1)*deltayold

pathname="/carbonics/owncloudsync/X.Selected_Measurements/FQ3/FQ3meas1"
filenamecontains='.xls'
pathname_mod=pathname+sub('DC')
newpath=pathname+'/new'
if not os.path.exists(newpath):											# if necessary, make the directory to contain the data
		os.makedirs(newpath)
filelisting = os.listdir(pathname_mod)

elimfromdev=['xls','_foc.','_transfer.','_transferloop.','_transferloop4.','.S2P']             # substrings to eliminate from filenames to form devicenames
#elimfrom_proberesistancetest='D11_'                                      # remove this from the probe resistance test data files

for fnameold in filelisting:
	if os.path.isfile(pathname_mod+'/'+fnameold) and parse_rpn(targetfilename=fnameold,expression=filenamecontains+" "+devselectstring+" and"):
		print(fnameold)
		dfr=open(pathname_mod+'/'+fnameold,'r')
		dataf=dfr.read()
		dfr.close()
		oldlines = [l for l in dataf.splitlines()]

		colnumberold=int(fnameold.split('_C')[1].split('_')[0].strip())      # get 0deg oriented column number
		rownumberold=int(fnameold.split('_R')[1].split('_')[0].strip())      # get 0deg oriented row number

		rownumbernew=numberofcolold-int(colnumberold)+1
		colnumbernew=rownumberold
		fnamenew=fnameold.replace('_R'+str(rownumberold),'_R'+str(rownumbernew)).replace('C'+str(colnumberold),'C'+str(colnumbernew))
		# find old x and y location relative to the reticle location

		# for l in oldlines:
		# 	if 'y probeing location um' in l or 'y location um' in l:
		# 		yold = int(l.split('\t')[1])     # find old value of y
		# for l in oldlines:
		# 	if 'x probeing location um' in l or 'x location um' in l:
		# 		xretlocold=colnumberold*deltaxold
		# 		relxold = int(l.split('\t')[1])-xretlocold     # find old value of relative xloc which will need to be modified
		# 	oldxlocline=l                       # old line containing old x probe location
		# 	newxlocline=l.replace(oldxlocprobe,str(int(oldxlocprobe)+xlocoffset))
		# 	dataf=dataf.replace(oldxlocline,newxlocline)

		#if 'proberesistancetest' in fnamenew: fnamenew=fnamenew.replace(elimfrom_proberesistancetest,'')
		devnameold=fnameold
		devnamenew=fnamenew
		for e in elimfromdev:
			devnameold=devnameold.replace(e,'')             # form old device name
			devnamenew=devnamenew.replace(e,'')             # form new device name

		dfw=open("".join([newpath,'/',fnamenew]),'w')      # make new device file
		print(" old name, new name =", devnameold, devnamenew)
		dfw.write(dataf.replace(devnameold,devnamenew))         # replace all instances of old device name with the new device name in the new file and write to disk
		dfw.close()