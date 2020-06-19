# measure the preamp noise parameters

from old.noiseparameters import *
from old.read_write_spar_noise import *

rm = visa.ResourceManager()

# directories
tundir="C:/Users/test/maury_setups/noise/"
datadir="C:/Users/test/python/data/noisefiguretests/RF/Feb9_2017/"             # noisefigure data directory
#system inputs
tunerfile=tundir+"1-1.6GHz_longcable_Feb5_2017.tun"
probefile=tundir+"cascade_RFprobe_APC40-A-GSG_SNJC23G_1-1.6GHz_Feb2_2017_RI.s2p"
inputcircuitfile=tundir+"input_circuit_biasT+coupler+circulator_1-1.6GHz_Feb1_2017_SRI.s2p"
#systemnoiseparametersfilename=datadir+"preamp_noiseparameters_cable_Feb7_2017.csv"
systemnoiseparametersfilename=datadir+"system_noiseparameters_probe_Feb9_2017.csv"

# DUT inputs
#SDUT=datadir+"10dB_pad_SRI.s2p"

#outputs
dembeddednoise=datadir+"probethru_NF.csv"
rawnoise=datadir+"probethru_rawNF.csv"
DUTnoiseparameters=datadir+"probethru_np.csv"

fulltunerpath=os.path.join(tundir,tunerfile)
cas1=[[probefile,'flip']]
cas2=[[inputcircuitfile,'noflip']]          # tuner cascade instructions
#########################
frequencies=[1.2]           # selected frequencies GHz
requested_reflections=[[0.7,0.],[0.7,90],[0.7,180],[0.5,270], [0.5,45], [0.5,135],[0.5,225],[0.5,315], [0.6,0.],[0.6,90],[0.6,180],[0.6,270], [0.4,45.],[0.4,135],[0.4,225],[0.4,315], [0.3,0],[0.3,90],[0.3,180],[0.3,270], [0.2,45.],[0.2,135],[0.2,225],[0.2,315], [0,0]]
#requested_reflections=[[0.7,0.],[0.7,90],[0.7,180],[0.5,270], [0.5,45], [0.5,135],[0.5,225],[0.5,315]]
np=NoiseParameters(rm=rm,ENR=12.99,navgNF=16,navgPNA=64,usePNA=True,tunerfile=tunerfile,tunernumber=1,cascadefiles_port1=cas1,cascadefiles_port2=cas2,system_noiseparametersfile=systemnoiseparametersfilename,reflectioncoefficients=requested_reflections)
#np.measure_noiseparameters(frequenciesGHz=frequencies,DUTSpar=read_spar(SDUT))
np.measure_noiseparameters(frequenciesGHz=frequencies)
np.writefile_noiseparameters(pathname=datadir,devicename='probethru')
write_noisefigure_frequency_position_reflection(noisefilename=dembeddednoise,NF=np.NF,tuner=np,dBinput=False)
write_noisefigure_frequency_position_reflection(noisefilename=rawnoise,NF=np.NFraw,tuner=np,dBinput=True)
write_noise_parameters(noisefilename=DUTnoiseparameters,npar=np.NP,preampresults=False)