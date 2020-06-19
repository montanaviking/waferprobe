# measure the preamp i.e. noise measurement system noise parameters
# calculates noise figure vs input reflection of noise meter then deembeds DUT noise figure based on noise meter noise figure calculated from the noise meter noise parameters

from measure_noiseparameters_focus import *
from pna import *
import os
from read_write_spar_noise import *

rm = visa.ResourceManager()

# directories
tundir="C:/Users/test/focus_setups/noise"
datadir=tundir             # noisefigure data directory
#system inputs
#tunerfile=tundir+"/S1_1-1.6GHz_July20_2017_SRI.s2p"
probefile=tundir+"/cascade_RFprobe_APC40-A-GSG_SNJC23G_1-1.6GHz_Feb14_2017_RI.s2p"
inputcircuitfile=tundir+"/S1_1-1.6GHz_July20_2017_SRI.s2p"

pna=Pna(rm=rm,navg=64)

# DUT inputs
#SDUT=datadir+"10dB_pad_SRI.s2p"
pna.pna_RF_onoff(RFon=False)
#outputs
# dembeddednoise="DUT2assystem_tuner_NF_Feb24_2017"
# rawnoise=datadir+"/RF/DUT2assystem_tuner_rawnoise_Feb24_2017.csv"
# systemnoiseparametersfilename="DUT2assystem_tuner_Feb24_2017"

dembeddednoise="system_cable_NF_July21_2017"
rawnoise=datadir+"/system_cable_rawnoise_July21_2017.csv"
systemnoiseparametersfilename="system_cable_July21_2017"

#fulltunerpath=os.path.join(tundir,tunerfile)
#cas1=[[probefile,'noflip']]
cas1=[[inputcircuitfile,'noflip']]          # tuner cascade instructions
#########################
#frequencies=[1000,1100,1200,1300,1400,1500,1600]           # selected frequencies MHz
frequencies=[1500]
#requested_reflections=[[0.8,45],[0.8,135],[0.8,-135],[0.8,-45], [0.3,0], [0.3,90],[0.3,180],[0.3,-90],[0.4,45], [0.4,-45],[0.4,135],[0.4,-135],[0,0],[0.5,0],[0.5,45],[0.5,135],[0.5,-135],[0.5,-45],[0.2,0], [0.2,90],[0.2,180],[0.2,-90],[0.6,0],[0.6,45],[0.6,135],[0.6,-135],[0.6,-45]]
requested_reflections=[[0.5,45],[0.5,135],[0.5,-135],[0.5,-45], [0.2,0], [0.2,90],[0.2,180],[0.2,-90],[0.5,32],[0.5,50],[0,0]]
#requested_reflections=[[0.7,45], [0.3,0], [0.3,90],[0.3,180],[0.3,-90],[0,0]]
NP=NoiseParameters(rm=rm,ENR=14.79,navgPNA=4,navgNF=8,usePNA=False,reflectioncoefficients=requested_reflections)
#NP.measure_noiseparameters(frequenciesGHz=frequencies,DUTSpar=read_spar(SDUT))
NP.measure_noiseparameters(frequenciesMHz=frequencies)
#NP.writefile_noiseparameters(pathname=datadir,devicename='6dB_pad')
# write_noisefigure_frequency_position_reflection(noisefilename=dembeddednoise,NF=NP.NF,tuner=NP,dBiNPut=False)
write_noisefigure_frequency_position_reflection(noisefilename=rawnoise,NF=NP.NFraw,tuner=NP)
NP.writefile_noiseparameters(pathname=tundir,devicename=systemnoiseparametersfilename)
NP.writefile_noisefigure(pathname=tundir,devicename=dembeddednoise)
#pna.pna_RF_onoff(RFon=False)