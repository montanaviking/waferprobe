#### calculate noise parameters from noise figure, DUT, and system data
# this deembeds the DUT noise figure from the system and system+DUT noise parameters
import numpy as np
from calculate_noise_parameters_v2 import calculate_gavail, convertMAtoRI, calculate_nffromnp,solvefornoiseparameters, convertRItoMA, deembed_noise_figure
from read_write_spar_noise_v2 import read_spar
from calculated_parameters import convertSRItoGMAX

direct="/carbonics/owncloudsync/documents/analysis/noise/noise_Feb23_2017/"
#input files
# systemNPfile=direct+"system_cable_Feb23_2017_noiseparameter.xls"
# systemNFfile=direct+"system_cable_NF_Feb23_2017_noisefigure.xls"
# DUTsystemNFfile=direct+"DUT2assystem_cable_NF_Feb23_2017_noisefigure.xls"
# DUTsysNPfile=direct+"DUT2assystem_cable_Feb23_2017_noiseparameter.xls"
# SDUTfile=direct+"DUT2_tuner_Feb23_2017_SRI.s2p"
systemNPfile=direct+"system_Feb24_2017_noiseparameter.xls"
systemNFfile=direct+"system_NF_Feb24_2017_noisefigure.xls"
DUTsystemNFfile=direct+"DUT2assystem_tuner_NF_Feb24_2017_noisefigure.xls"
DUTsysNPfile=direct+"DUT2assystem_tuner_Feb24_2017_noiseparameter.xls"
SDUTfile=direct+"DUTtuner_Feb24_2017_SRI.s2p"
# output files
DUTNPfile=direct+"DUTsystuner_Feb23_2017_noiseparameter.xls"
NFcalcfile=direct+"NFsystuner_calculations.xls"

# input files
fNPsys=open(systemNPfile,'r')
fNPDUTsys=open(DUTsysNPfile,'r')
fNFsys=open(systemNFfile,'r')
fNFDUTsys=open(DUTsystemNFfile,'r')
# output files
fDUTnoiseparameter=open(DUTNPfile,'w')
fNFcalc=open(NFcalcfile,'w')
# output files

## noise parameters of noise system following the DUT
NPsys={}
for l in fNPsys:
	if '#' not in l and '!' not in l:
		freq=str(int(1E3*float(l.split()[0])))          # frequency in MHz
		NPsys[freq]={}
		NPsys[freq]['FmindB']=float(l.split()[1])
		NPsys[freq]['gopt']=convertMAtoRI(float(l.split()[2]),float(l.split()[3]))
		NPsys[freq]['Rn']=float(l.split()[4])
fNPsys.close()

# noise parameters at the input of the DUT = noise parameters of the system composed of the DUT + noise system following the DUT
NPDUTsys={}
for l in fNPDUTsys:
	if '#' not in l and '!' not in l:
		freq=str(int(1E3*float(l.split()[0])))          # frequency in MHz
		NPDUTsys[freq]={}
		NPDUTsys[freq]['FmindB']=float(l.split()[1])
		NPDUTsys[freq]['gopt']=convertMAtoRI(float(l.split()[2]),float(l.split()[3]))
		NPDUTsys[freq]['Rn']=float(l.split()[4])
fNPDUTsys.close()


# read noise figure of the system and the reflection coefficient
NFsys={}
for l in fNFsys:
	if '#' in l and 'frequency' in l:
		f=str(int(1000*float(l.split('GHZ')[0].split()[-1].strip())))
		NFsys[f]={}
	elif '#' not in l and '!' not in l and 'frequency' not in l:
		pos=l.split()[0]
		NFsys[f][pos]={}
		NFsys[f][pos]['gammatuner']=convertMAtoRI(float(l.split()[1]),float(l.split()[2]))
		NFsys[f][pos]['NFdB']=float(l.split()[3])              # noise figure in dB
fNFsys.close()

# read noise figure of the DUT+system and the reflection coefficient
NFDUTsys={}
for l in fNFDUTsys:
	if '#' in l and 'frequency' in l:
		f=str(int(1000*float(l.split('GHZ')[0].split()[-1].strip())))
		NFDUTsys[f]={}
	elif '#' not in l and '!' not in l and 'frequency' not in l:
		pos=l.split()[0]
		NFDUTsys[f][pos]={}
		NFDUTsys[f][pos]['gammatuner']=convertMAtoRI(float(l.split()[1]),float(l.split()[2]))
		NFDUTsys[f][pos]['NFdB']=float(l.split()[3])              # noise figure in dB
fNFDUTsys.close()



SDUT=read_spar(sparfilename=SDUTfile)

#reflections=[complex(R,I) for R in np.linspace(-.55,.55,5) for I in np.linspace(-.55,.55,5)]            # grid of reflections

frequencies=[str(ff) for ff in sorted([int(f) for f in NPDUTsys.keys()])]
NPDUT={}
NFDUTcalc={}
NFsyscalc={}
NFDUTsyscalc={}
NFsyscalcwithDUT={}
commonpositions={}
for f in frequencies:
	FDUT=[]
	NPDUT[f]={}
	NFDUTcalc[f]={}
	NFsyscalc[f]={}
	NFsyscalcwithDUT[f]={}
	NFDUTsyscalc[f]={}
	reflections=[]
	commonpositions[f]=list(set(NFDUTsys[f].keys())&set(NFsys[f].keys()))
	for p in commonpositions[f]:
		R=NFDUTsys[f][p]['gammatuner']
		reflections.append(R)
		gammaDUTout=SDUT[f][1,1]+(SDUT[f][0,1]*SDUT[f][1,0]*R/(1-SDUT[f][0,0]*R))        # DUT output (DUT port 2) reflection coefficient with the reflection coefficient R (tuner reflection coefficient) at the DUT input (port 1 of the DUT)
		gaDUT=calculate_gavail(SDUT=SDUT[f],gammain=R)[0]                                  # DUT available gain for the reflection coefficient R (tuner reflection coefficient) at the input of the DUT
		NFsyscalcwithDUT[f][p]=calculate_nffromnp(reflectioncoef=gammaDUTout,noiseparameters=NPsys[f],typedBout=False)       # noise figure (linear) of the noise meter at frequency f + any preamp used with the noise meter when presented with the DUT output reflection coefficient
		NFDUTsyscalc[f][p]=calculate_nffromnp(reflectioncoef=R,noiseparameters=NPDUTsys[f],typedBout=False)       # noise figure (linear) of the DUT+noise meter at frequency f when presented with the reflection coefficient R at the input of the DUT
		NFDUTcalc[f][p]=NFDUTsyscalc[f][p]-((NFsyscalcwithDUT[f][p]-1)/gaDUT)      # noise figure (linear) of DUT at frequency f and reflection coefficient R presented at the DUT input
		NFsyscalc[f][p]=calculate_nffromnp(reflectioncoef=R,noiseparameters=NPsys[f],typedBout=False)       # noise figure (linear) of the noise meter at frequency f + any preamp used with the noise meter when presented with the tuner (R) reflection coefficient
		FDUT.append(NFDUTcalc[f][p])                           # noise figure (linear) of DUT at frequency f and reflection coefficient R presented at the DUT input
	NPDUT[f]['FmindB'],NPDUT[f]['gopt'],NPDUT[f]['Rn']=solvefornoiseparameters(F=FDUT,gamma=reflections)                          # calculate DUT noise parameters
	ret=calculate_gavail(SDUT=SDUT[f],gammain=NPDUT[f]['gopt'])
	NPDUT[f]['GassocdB']=10.*np.log10(ret[0])                                # associated gain in dB
	NPDUT[f]['Gassoctype']=ret[1]
	NPDUT[f]['gavaildB']=10.*np.log10(convertSRItoGMAX(SDUT[f][0,0],SDUT[f][1,0],SDUT[f][0,1],SDUT[f][1,1])['gain'])
# write DUT noise parameters
fDUTnoiseparameter.write("frequency MHz\tFmindB\tgopt (mag,angle)\tRn\tGassoc dB\tGassoc type\tDUT available gain dB\n")
frequencies=[str(ff) for ff in sorted([int(f) for f in NPDUT.keys()])]
for f in frequencies:
	fDUTnoiseparameter.write("%10.1f\t%10.2f\t%10.2f %10.2f\t%10.2f\t%10.2f\t%s\t%10.2f\n" %(int(f), NPDUT[f]['FmindB'], convertRItoMA(NPDUT[f]['gopt']).real, convertRItoMA(NPDUT[f]['gopt']).imag, NPDUT[f]['Rn'], NPDUT[f]['GassocdB'], NPDUT[f]['Gassoctype'], NPDUT[f]['gavaildB']))
fDUTnoiseparameter.close()

# write calculated noise figures
for f in frequencies:
	fNFcalc.write("frequency MHz\t%d\n" %(int(f)))
	fNFcalc.write("\tposition\treflection coefficient MA \tnoise figure system dB\tcalculated noise figure system dB\tcalculated noise figure system dB with DUT\tnoise figure DUT+system dB\tcalculated noise figure DUT+system dB\tcalculated noise figure DUT dB\tDUTS11 MA\n")
	for p in commonpositions[f]:
		fNFcalc.write("\t%s\t%10.2f %10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f %10.2f\n"
		              %(p, convertRItoMA(NFDUTsys[f][p]['gammatuner']).real, convertRItoMA(NFDUTsys[f][p]['gammatuner']).imag, NFsys[f][p]['NFdB'], 10.*np.log10(NFsyscalc[f][p]),  10.*np.log10(NFsyscalcwithDUT[f][p]), NFDUTsys[f][p]['NFdB'], 10.*np.log10(NFDUTsyscalc[f][p]), 10.*np.log10(NFDUTcalc[f][p]), convertRItoMA(SDUT[f][0,0]).real, convertRItoMA(SDUT[f][0,0]).imag))
fNFcalc.close()