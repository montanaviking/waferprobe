# measure DUT noise parameters

from calculate_noise_parameters_v2 import *

from noiseparameters_v3 import *
from pna import *
from read_write_spar_noise_v2 import *
from parameter_analyzer import *
rm = visa.ResourceManager()

# directories
tundir="C:/Users/test/maury_setups/noise"
datadir=tundir             # noisefigure data directory
#system inputs
tunerfile=tundir+"/1-1.6GHz_longcable_Mar1_2017.tun"
probefile=tundir+"/cascade_RFprobe_APC40-A-GSG_SNJC23G_1-1.6GHz_Feb14_2017_RI.s2p"
inputcircuitfile=tundir+"/input_circuit_biasT+coupler+circulator_1-1.6GHz_Mar17_2017_SRI.s2p"
systemnoiseparameters=tundir+"/system_probe_Mar21_2017_noiseparameter.xls"

pna=Pna(rm=rm,navg=64)

# DUT inputs
#SDUT=datadir+"10dB_pad_SRI.s2p"
pna.pna_RF_onoff(RFon=False)
#outputs
dembeddednoise="DUT_cnt_probe_NF_Mar21_2017"
rawnoise=datadir+"/DUT_cnt_probe_Mar21_2017_rawnoise.csv"
DUTnoiseparametersfilename="DUT_cnt_probe_Mar21_2017"

iv = ParameterAnalyzer(rm)
fulltunerpath=os.path.join(tundir,tunerfile)
cas1=[[probefile,'flip']]
cas2=[[inputcircuitfile,'noflip']]          # tuner cascade instructions
#########################
#frequencies=[1000,1100,1200,1300,1400,1500,1600]           # selected frequencies GHz
frequencies=[1200]
#requested_reflections=[[0.8,45],[0.8,135],[0.8,-135],[0.8,-45], [0.3,0], [0.3,90],[0.3,180],[0.3,-90],[0.4,45], [0.4,-45],[0.4,135],[0.4,-135],[0.5,45],[0.5,135],[0.5,-135],[0.5,-45],[0.2,0], [0.2,90],[0.2,180],[0.2,-90],[0.6,32],[0.5,50],[0,0], [0.85,0], [0.7,0],[.85,20], [.85,-20]]
#requested_reflections=[[0.7,-20],[0.7,20], [0.85,0], [0.7,0],[.85,20], [.85,-20], [.6,0],[.4,0],[.5,20],[.5,-20],[0,0],[.7,40]]
requested_reflections=[[0.5,45],[0.5,135],[0.5,-135],[0.5,-45], [0.2,0], [0.2,90],[0.2,180],[0.2,-90],[0.6,32],[0.5,50],[0,0]]
#requested_reflections=[[0.5,135], [0.2,0], [0.2,90],[0.2,180],[0.2,-90],[0.5,50],[0,0],[.4,120],[.4,110]]
#requested_reflections=[[0.8,45],[0.8,0],[0.6,10], [0.3,0], [0.3,90],[0.3,180],[0.4,45], [0.4,-45],[0.5,30],[0,0],[0.3,30]]
#requested_reflections=[[0.6,10], [0.3,90],[0.4,45],[0.5,30],[0,0]]
NP=NoiseParameters(rm=rm,ENR=12.99,navgNF=128,navgPNA=64,usePNA=True,tunerfile=tunerfile,tunernumber=1,cascadefiles_port1=cas1,cascadefiles_port2=cas2,reflectioncoefficients=requested_reflections,system_noiseparametersfile=systemnoiseparameters)
#NP.measure_noiseparameters(frequenciesGHz=frequencies,DUTSpar=read_spar(SDUT))
Id,Ig,drainstatus,gatestatus=iv.fetbiason_topgate(Vgs=-.4, Vds=-2.5, draincomp=.02, gatecomp=0.02,timeiter=10.,maxchangeId=0.01,maxtime=40.)				# bias device
print("Id, Ig 1st",Id,Ig)
NP.measure_noiseparameters(frequenciesMHz=frequencies)
iv.fetbiasoff()
#NP.writefile_noiseparameters(pathname=datadir,devicename='6dB_pad')
# write_noisefigure_frequency_position_reflection(noisefilename=dembeddednoise,NF=NP.NF,tuner=NP,dBiNPut=False)
write_noisefigure_frequency_position_reflection(noisefilename=rawnoise,NF=NP.NFraw,tuner=NP)
NP.writefile_noiseparameters(pathname=tundir,devicename=DUTnoiseparametersfilename)
NP.writefile_noisefigure(pathname=tundir,devicename=dembeddednoise)

pna.pna_RF_onoff(RFon=False)