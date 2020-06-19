#### calculate noise parameters from noise figure, DUT, and system data
import numpy as np
from calculate_noise_parameters_v2 import calculate_gavail, convertMAtoRI, calculate_nffromnp,solvefornoiseparameters, convertRItoMA, deembed_noise_figure
from read_write_spar_noise_v2 import read_spar

direct="/carbonics/owncloudsync/documents/analysis/noise/noise_Feb22_2017/"
#input files
systemNPfile=direct+"system_cable_Feb22_2017_noiseparameter.xls"
DUTrawnoisefile=direct+"DUT_tunertestiso_2_cable_Feb22_2017_rawnoise.csv"
DUTnoisefigurefile=direct+"DUT_tunertestiso_2_cable_Feb22_2017_NF_noisefigure.xls"
SDUTfile=direct+"DUT_tuner_isolator_Feb22_2017_SRI.s2p"

# output
DUTnoisecalc_out=direct+"DUT_isolator_2_cable_calculated.xls"

try: fsysNP=open(systemNPfile,'r')
except: raise ValueError("ERROR! could not find system noise parameters")
try: fDUTrawnoise=open(DUTrawnoisefile,'r')
except: raise ValueError("ERROR! could not find DUT+system raw noise figures")
try: fDUTnoisefigure=open(DUTnoisefigurefile,'r')
except: raise ValueError("ERROR! could not find DUT noise figures")
# fSDUT=open(SDUTfile,"r")
fDUTout=open(DUTnoisecalc_out,'w')

# output files


NPsys={}
for l in fsysNP:
	if '#' not in l and '!' not in l:
		freq=str(int(1E3*float(l.split()[0])))          # frequency in MHz
		NPsys[freq]={}
		#NPsys[freq]['Fmin']=np.power(10.,float(l.split()[1])/10.)
		NPsys[freq]['FmindB']=float(l.split()[1])
		NPsys[freq]['gopt']=convertMAtoRI(float(l.split()[2]),float(l.split()[3]))
		NPsys[freq]['Rn']=float(l.split()[4])
fsysNP.close()

DUT={}
for l in fDUTnoisefigure:
	if '#' in l and 'frequency' in l:
		freq=str(int(1E3*float(l.split('GHZ')[0].split()[-1].strip())))
		DUT[freq]={}
	elif '#' not in l and '!' not in l and 'frequency' not in l:
		pos=l.split()[0]
		DUT[freq][pos]={}
		DUT[freq][pos]['gammatuner']=convertMAtoRI(float(l.split()[1]),float(l.split()[2]))
		#DUT[freq][pos]['FDUT']=np.power(10.,float(l.split()[3])/10.)
		DUT[freq][pos]['FDUT']=float(l.split()[3])
		DUT[freq][pos]['gaDUT']=float(l.split()[5])
		DUT[freq][pos]['gatuner']=float(l.split()[7])
fDUTnoisefigure.close()

DUTNFraw={}
for l in fDUTrawnoise:
	if '#' in l and 'frequency' in l:
		freq=str(int(float(l.split('GHZ')[0].split()[-1].strip())))
		DUTNFraw[freq]={}
	elif '#' not in l and '!' not in l and 'frequency' not in l:
		pos=l.split()[0]
		DUTNFraw[freq][pos]={}
		DUTNFraw[freq][pos]['gammatuner']=convertMAtoRI(float(l.split()[1]),float(l.split()[2]))
		DUTNFraw[freq][pos]['NFraw']=np.power(10.,float(l.split()[3])/10.)              # raw noise figure in linear
fDUTrawnoise.close()

SDUT=read_spar(sparfilename=SDUTfile)

#######
# deembed noise figure

Fdeembeddedcalc={}
gaDUT={}
for f in DUT.keys():
	Fdeembeddedcalc[f]={}
	gaDUT[f]={}
	S11DUT=SDUT[f][0,0]
	S12DUT=SDUT[f][0,1]
	S21DUT=SDUT[f][1,0]
	S22DUT=SDUT[f][1,1]

	Fmin_sys=np.power(10,NPsys[f]['FmindB']/10)           # convert system input minimum noise figure from dB to linear format at the frequency f. Used only if there is a DUT being measured

	for p in DUT[f].keys():
		gammaDUTout=S22DUT+(S12DUT*S21DUT*DUT[f][p]['gammatuner']/(1-S11DUT*DUT[f][p]['gammatuner']))
		gaDUT[f][p]=calculate_gavail(SDUT=SDUT[f],gammain=DUT[f][p]['gammatuner'])[0]              # sanity check
		#Fsys=Fmin_sys+(4*NPsys[f]['Rn']/50.)*np.square(abs(NPsys[f]['gopt']-gammaDUTout))/(np.square(abs(1+NPsys[f]['gopt']))*(1-np.square(abs(gammaDUTout)))) # preamp noise figure (linear) within the noise measurement system
		Fsys=np.power(10,calculate_nffromnp(reflectioncoef=gammaDUTout,noiseparameters=NPsys[f])/10)
		Fdeembeddedcalc[f][p]=(DUTNFraw[f][p]['NFraw']*DUT[f][p]['gatuner'])-((Fsys-1)/gaDUT[f][p])             # deembedded DUT linear noise figure
		print("test",f,p,Fdeembeddedcalc[f][p]/DUTNFraw[f][p]['NFraw']*DUT[f][p]['gatuner'])
# now calculate noise figure from raw noisefigure and system noise parameters
freqs=sorted(list(DUT.keys()))
for f in freqs:
	F=[]
	gam=[]
	for p in DUT[f].keys():
		F.append(Fdeembeddedcalc[f][p])
		gam.append((DUT[f][p]['gammatuner']))
	NP=solvefornoiseparameters(F=F,gamma=gam)
	fDUTout.write("frequency MHz\tFmindB\tgopt (mag,angle)\tRn\tGassocdB\n")
	fDUTout.write("%s\t%10.2f\t%10.2f %10.2f\t%10.2f\t%10.2f\n" %(f,NP[0],convertRItoMA(NP[1]).real,convertRItoMA(NP[1]).imag,NP[2],10*np.log10(calculate_gavail(SDUT=SDUT[f],gammain=NP[1])[0])))
	fDUTout.write("frequency MHz\ttuner position\ttuner reflection MA\tdeembedded noise figure dB\tdeembedded noise figure dB calc\tDUT gavail\tDUT gavailcalc\ttuner gavail\n")
	fDUTout.write("%s\n" %(f))
	for p in DUT[f].keys():
		fDUTout.write("\t%s\t%10.3f %10.3f\t%10.3f\t%10.3f\t%10.3f\t%10.3f\t%10.3f\n" %(str(p),convertRItoMA(DUT[f][p]['gammatuner']).real,convertRItoMA(DUT[f][p]['gammatuner']).imag, DUT[f][p]['FDUT'],10.*np.log10(Fdeembeddedcalc[f][p]), DUT[f][p]['gaDUT'],gaDUT[f][p],DUT[f][p]['gatuner']))
fDUTout.close()
