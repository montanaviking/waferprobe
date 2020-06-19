__author__ = 'viking'
from utilities import *
# renames wafers
xlocoffset=4550
pathname="/home/viking/Desktop/phil@carbonicsinc.com/07. Measurements/"
filenamecontains='.xls'
pathname_mod=pathname+sub('DC')
newpath=pathname+'/new'
if not os.path.exists(newpath):											# if necessary, make the directory to contain the data
		os.makedirs(newpath)
filelisting = os.listdir(pathname_mod)

elimfromdev=['xls','_foc.','_transfer.','_transferloop.','.S2P']             # substrings to eliminate from filenames to form devicenames

for fnameold in filelisting:
    if os.path.isfile(pathname_mod+'/'+fnameold) and parse_rpn(targetfilename=fnameold,expression=filenamecontains):
        print(fnameold)
        dfr=open(pathname_mod+'/'+fnameold,'r')
        dataf=dfr.read()
        dfr.close()
        oldlines = [l for l in dataf.splitlines()]

        colnumberold=fnameold[fnameold.index('_C')+2]
        if 'RP' in fnameold:
            colnumbernew=str(int(colnumberold)+1)
            fnamenew=fnameold.replace('RP_','').replace('C'+colnumberold,'C'+colnumbernew)
            for l in oldlines:
                if 'x probeing location um' in l or 'x location um' in l:
                    oldxlocprobe = l.split('\t')[1]     # find old value of xloc which will need to be modified
                    oldxlocline=l                       # old line containing old x probe location
                    newxlocline=l.replace(oldxlocprobe,str(int(oldxlocprobe)+xlocoffset))
                    dataf=dataf.replace(oldxlocline,newxlocline)
        elif 'LP' in fnameold:
            fnamenew=fnameold.replace('LP_','')
        devnameold=fnameold
        devnamenew=fnamenew
        for e in elimfromdev:
            devnameold=devnameold.replace(e,'')             # form old device name
            devnamenew=devnamenew.replace(e,'')             # form new device name
        dfw=open("".join([newpath,'/',fnamenew]),'w')      # make new device file
        print(" new name =",dfw)
        dfw.write(dataf.replace(devnameold,devnamenew))         # replace all instances of old device name with the new device name in the new file and write to disk
        dfw.close()