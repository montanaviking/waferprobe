# measure the preamp i.e. noise measurement system noise parameters

from old.noiseparameters import *
from old.read_write_spar_noise import *
from pna import *

rm = visa.ResourceManager()

# directories
tundir="C:/Users/test/maury_setups/noise"
datadir=tundir             # noisefigure data directory
#system inputs
tunerfile=tundir+"/1-1.6GHz_longcable_Feb16_2017.tun"
probefile=tundir+"/cascade_RFprobe_APC40-A-GSG_SNJC23G_1-1.6GHz_Feb14_2017_RI.s2p"
inputcircuitfile=tundir+"/input_circuit_biasT+coupler+circulator_1-1.6GHz_Feb17_2017_SRI.s2p"

pna=Pna(rm=rm,navg=64)

# DUT inputs
#SDUT=datadir+"10dB_pad_SRI.s2p"
pna.pna_RF_onoff(RFon=False)
#outputs
dembeddednoise="system_cable_NF.csv"
rawnoise=datadir+"/system_cable_rawnoise.csv"
systemnoiseparametersfilename="system_cable_noiseparameters_Feb18_2017"

fulltunerpath=os.path.join(tundir,tunerfile)
#cas1=[[probefile,'flip']]
cas2=[[inputcircuitfile,'noflip']]          # tuner cascade instructions
#########################
#frequencies=[1.0,1.1,1.2,1.3,1.4,1.5,1.6]           # selected frequencies GHz
frequencies=[1.0]
requested_reflections=[[0.7,45],[0.7,135],[0.7,-135],[0.7,-45], [0.3,0], [0.3,90],[0.3,180],[0.3,-90],[0.4,45], [0.4,-45],[0.4,135],[0.4,-135],[0,0]]
#requested_reflections=[[0.7,45],[0.7,135],[0.7,-135],[0.7,-45], [0.3,0], [0.3,90],[0.3,180],[0.3,-90],[0,0]]
NP=NoiseParameters(rm=rm,ENR=12.99,navgPNA=64,navgNF=16,usePNA=False,tunerfile=tunerfile,tunernumber=1,cascadefiles_port2=cas2,reflectioncoefficients=requested_reflections)
#NP.measure_noiseparameters(frequenciesGHz=frequencies,DUTSpar=read_spar(SDUT))
NP.measure_noiseparameters(frequenciesGHz=frequencies)
#NP.writefile_noiseparameters(pathname=datadir,devicename='6dB_pad')
# write_noisefigure_frequency_position_reflection(noisefilename=dembeddednoise,NF=NP.NF,tuner=NP,dBiNPut=False)
write_noisefigure_frequency_position_reflection(noisefilename=rawnoise,NF=NP.NFraw,tuner=NP)
NP.writefile_noiseparameters(pathname=tundir,devicename=systemnoiseparametersfilename)
NP.writefile_noisefigure(pathname=tundir,devicename=dembeddednoise)

pna.pna_RF_onoff(RFon=False)