# measure DUT noise parameters

from calculate_noise_parameters_focus import *

from measure_noiseparameters_focus import *
from pna import *
from read_write_spar_noise import *
from parameter_analyzer import *
rm = visa.ResourceManager()

# directories
tundir="C:/Users/test/focus_setups"

datadir=tundir             # noisefigure data directory
#system inputs
tunercal="c:/Users/test/focus_setups/calibration_S1tunerS2_Aug14_2017.txt"
cas2=None
probefile=tundir+"/cascade_JC23F_1-1.6GHz_Aug14_2017_RI.s2p"
cas2=[[probefile,'noflip']]
#inputcircuitfile=tundir+"/input_circuit_biasT+coupler+circulator_1-1.6GHz_Mar17_2017_SRI.s2p"
#systemnoiseparameters=tundir+"/system_cable_Aug10_2017_noiseparameter.xls"
systemnoiseparameters=tundir+"/system_probe_Aug14_2017_noiseparameter.xls"


pna=Pna(rm=rm,navg=32)

# DUT inputs
#SDUT=datadir+"10dB_pad_SRI.s2p"
pna.pna_RF_onoff(RFon=False)
#outputs
dembeddednoise="DUT_tuner_2017"
rawnoise=datadir+"/DUT_tuner_rawnoise.csv"
DUTnoiseparametersfilename="DUT_tuner"

#iv = ParameterAnalyzer(rm)
# fulltunerpath=os.path.join(tundir,tunerfile)
# cas1=[[probefile,'flip']]
# cas2=[[inputcircuitfile,'noflip']]          # tuner cascade instructions
#########################
frequencies=[1000]           # selected frequencies GHz
#frequencies=[1000,1100,1200,1300,1400,1500,1600]
#requested_reflections=[ [0.042,96.509], [0.158,30.556], [0.132,-39.700], [0.166,-151.235], [0.166,136.688], [0.205,79.067], [0.143,-86.067], [0.259,-132.359], [0.485,-127.503], [0.206,-61.869], [0.435,-53.802], [0.054,-110.817], [0.063,-46.333], [0.120,96.911], [0.104,65.215], [0.253,123.640], [0.450,121.095], [0.254,56.314], [0.450,54.430], [0.392,-95.661], [0.361,88.444], [0.329,179.541], [0.335,-0.378], [0.500,155.642], [0.514,-32.837], [0.508,-148.066], [0.370,32.979], [0.107,173.394] ]
requested_reflections=[ [0.871,4.645], [0.859,-6.628], [0.754,8.327], [0.800,1.578], [0.826,15.842], [0.698,15.113], [0.666,4.401], [0.717,-6.386], [0.814,-12.530], [0.580,-12.272], [0.540,4.914], [0.712,-18.847], [0.608,16.934], [0.916,19.644], [0.903,-16.036] ]

NP=NoiseParameters(rm=rm,ENR=14.79,navgNF=8,navgPNA=32,usePNA=True,tunercalfile=tunercal,cascadefiles_port1=None,cascadefiles_port2=cas2,reflectioncoefficients=requested_reflections,system_noiseparametersfile=systemnoiseparameters)
NP.measure_noiseparameters_highspeed(frequenciesMHz=frequencies)
# Id,Ig,drainstatus,gatestatus=iv.fetbiason_topgate(Vgs=-.4, Vds=-2.5, draincomp=.02, gatecomp=0.02,timeiter=10.,maxchangeId=0.01,maxtime=40.)				# bias device
# print("Id, Ig 1st",Id,Ig)
# NP.measure_noiseparameters(frequenciesMHz=frequencies)
# iv.fetbiasoff()
#NP.writefile_noiseparameters(pathname=datadir,devicename='6dB_pad')
# write_noisefigure_frequency_position_reflection(noisefilename=dembeddednoise,NF=NP.NF,tuner=NP,dBiNPut=False)
write_noisefigure_frequency_position_reflection(noisefilename=rawnoise,NF=NP.NFraw,tuner=NP)
NP.writefile_noiseparameters(pathname=tundir,devicename=DUTnoiseparametersfilename)
NP.writefile_noisefigure(pathname=tundir,devicename=dembeddednoise)

pna.pna_RF_onoff(RFon=False)