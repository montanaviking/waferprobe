__author__ = 'viking'
from utilities import *
# renames wafers
pathname="/home/viking/Desktop/phil@carbonicsinc.com/07. Measurements/T51/T51meas2_TM"
filenamecontains='1A'
pathname_mod=pathname+sub('DC')
newpath=pathname+'/new'
if not os.path.exists(newpath):											# if necessary, make the directory to contain the data
		os.makedirs(newpath)
filelisting = os.listdir(pathname_mod)

newseq=['1A','TLM']
elim = ['']
elimfromdev=['xls','_foc.','_transfer.','_transferloop.','.S2P']             # substrings to eliminate from filenames to form devicenames

for fnameold in filelisting:
    if os.path.isfile(pathname_mod+'/'+fnameold) and parse_rpn(targetfilename=fnameold,expression=filenamecontains):
        print(fnameold)
        dfr=open(pathname_mod+'/'+fnameold,'r')
        dataf=dfr.read()
        dfr.close()
        #fnameold=fnameold.replace('.xls','')                    # remove the file extension
        # find new wafer name
        for e in elim: fnamenew=fnameold.replace(e,'')        # first clean out all unwanted strings from filename
        oldfnameparts=[s for s in fnamenew.split(sep='_') if s!='']                   # get all components of filename while eliminating null characters
        oldseq=[s for s in oldfnameparts for ns in newseq if ns in s]
        fsindexold=[oldfnameparts.index(s) for ns in oldseq for s in oldfnameparts if ns in s]
        fsindexnew=[oldfnameparts.index(s) for ns in newseq for s in oldfnameparts if ns in s]
        if len(fnameold.split('__'))==2 and fnameold.split('__')[0]==oldfnameparts[0] : oldfnameparts[0]="".join([oldfnameparts[0],'_'])
        if len(fnameold.split('__'))==2 and fnameold.split('__')[0]=="".join([oldfnameparts[0],"_",oldfnameparts[1]]) : oldfnameparts[1]="".join([oldfnameparts[1],'_'])
        newfilenameparts=list(oldfnameparts)        # copy to new file name parts
        for i in range(0, len(fsindexnew)):
            newfilenameparts[fsindexold[i]]=oldfnameparts[fsindexnew[i]]
        fnamenew="".join(["".join([s,'_']) for s in newfilenameparts if newfilenameparts.index(s) !=len(newfilenameparts)-1])             # form new device and filename by concatenating all but the final portion
        fnamenew="".join([fnamenew,newfilenameparts[-1]])                           # concatenate the final portion of the filename, leaving out the _  since we don't want the _ at the end of the new filenames
        dfw=open("".join([newpath,'/',fnamenew]),'w')      # make new device file
        print(" new name =",dfw)
        devnameold=fnameold
        devnamenew=fnamenew
        for s in elimfromdev:   # convert device filename to device name
            devnameold=devnameold.replace(s,'')
            devnamenew=devnamenew.replace(s,'')
        dfw.write(dataf.replace(devnameold,devnamenew))         # replace all instances of old device name with the new device name in the new file and write to disk
        dfw.close()

    #flines = [l for l in df.read().splitlines()]        # get all file lines



