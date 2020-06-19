# measure the preamp i.e. noise measurement system noise parameters
# calculates noise figure vs input reflection of noise meter then deembeds DUT noise figure based on noise meter noise figure calculated from the noise meter noise parameters

from measure_noiseparameters_focus import *
from pna import *
import os
from read_write_spar_noise import *

rm = visa.ResourceManager()

# directories

#datadir=tundir             # noisefigure data directory
#system inputs
tundir="C:/Users/test/focus_setups/noise/"
#tundir ="C:/Users/test/python/data/RFamptests1/RF/"          # base directory of noise calibrations
inputcircuitfile=tundir+"noise__coupler_biastee_isolator_April23_2020_SRI.s2p"
inputprobe=tundir+"ACP150_JC2G6-1_May4_2020_SRI.s2p"
#outputcircuitfile=tundir+"/RF/JC2G4_Oct9_2019trl_SRI.s2p"           # this is the probe on the left side
#outputcircuitfile=tundir+"/RF/JC2G4_May4_2018_SRI.s2p"           # this is the probe on the left side
#outputcircuitfile=tundir+"/RF/noise_outputcableport2_oct11_2019_SRI.s2p"
tunercal="c:/Users/test/focus_setups/tunercals_sourcepull/tunercal_1389source_April16_2020_1GHz_1.6GHz_13pts.txt"
pna=Pna(rm=rm,navg=4)

# DUT inputs
#SDUT=datadir+"10dB_pad_SRI.s2p"
pna.pna_RF_onoff(RFon=False)
#outputs
# dembeddednoise="noisesystem_spectrum_analyzer_NF_April24_2020_11"
# rawnoise=tundir+"noisesystem_spectrum_analyzer_rawnoise_April24_2020_11.xls"
# systemnoiseparametersfilename="noisesystem_spectrum_analyzer_April24_2020_SRI_11.s2p"
dembeddednoise="noisesystem_spectrum_analyzer_noisolatorprobe_NF_May4_2020"
# rawnoise=tundir+"noisesystem_spectrum_analyzer_rawnoise_April24_2020_11.xls"
systemnoiseparametersfilename="noisesystem_spectrum_analyzer_noisolatorprobe_May4_2020_SRI.s2p"


cas2=[[inputprobe,'noflip']]          # tuner cascade instructions for cascade probe
#fulltunerpath=os.path.join(tundir,tunerfile)
#cas2=[[outputcircuitfile,'noflip']]         # wafer probe on tuner output for source pull
cas1=[[inputcircuitfile,'noflip']]          # tuner cascade instructions
#########################
#frequencies=np.linspace(1200,1500,31)
frequencies=[1250,1350,1450,1550]           # selected frequencies MHz
#frequencies=[1250]
# requested_reflections=[ [0.815,-178.140], [0.664,-178.137], [0.398,-177.587], [0.175,-174.514], [0.019,-59.625], [0.194,-2.082], [0.427,1.006], [0.616,-2.009], [0.819,0.185], [0.153,-88.134], [0.322,-87.394], [0.511,-88.900], [0.681,-89.174], [0.846,-89.335], [0.251,84.432], [0.497,88.310], [0.740,87.738], [0.880,88.099], [0.797,140.043], [0.535,140.301], [0.290,134.614], [0.085,124.442], [0.112,38.901], [0.307,42.137], [0.506,43.261], [0.736,42.470], [0.897,42.268], [0.143,-127.465], [0.277,-130.394], [0.479,-131.929], [0.653,-134.254], [0.818,-132.004], [0.157,-51.808], [0.379,-47.296], [0.588,-46.146], [0.825,-47.483], [0.711,-45.947], [0.291,-20.955], [0.106,-100.496], [0.112,-38.728], [0.116,80.299], [0.133,155.191], [0.182,36.902], [0.199,-148.473], [0.255,-85.612], [0.280,-55.165], [0.205,110.741], [0.228,59.351], [0.233,153.374], [0.529,-111.505], [0.505,-66.238], [0.495,-25.784], [0.453,23.017], [0.474,67.760], [0.483,120.790], [0.497,160.919], [0.474,-160.012], [0.674,20.859], [0.635,-15.713], [0.388,141.806], [0.375,-148.484], [0.395,-87.171], [0.353,95.492], [0.306,15.169], [0.717,13.111], [0.732,-17.516], [0.713,-0.957], [0.663,-33.494], [0.814,30.241], [0.822,-30.628], [0.325,-2.098] ]
#requested_reflections= [ [0.471,-89.397], [0.449,0.958], [0.394,88.578], [0.411,-179.026], [0.234,-125.345], [0.200,-47.370], [0.223,36.658], [0.241,136.153], [0.828,-133.471], [0.822,140.347], [0.863,49.891], [0.857,-47.839], [0.823,-89.319], [0.826,-0.484], [0.836,-179.521], [0.882,90.306], [0,0] ]
#requested_reflections=[[0.5,45],[0.5,135],[0.5,-135],[0.5,-45], [0.2,0], [0.2,90],[0.2,180],[0.2,-90],[0.5,32],[0.5,50],[0,0]]
#requested_reflections=[[0.85,0], [0.85,90], [0.85,180],[0.85,-90],[0.5,45], [0.5,135], [0.5,-135],[0.5,-45],[0.3,0], [0.3,90], [0.3,180],[0.3,-90],[0,0]]

requested_reflections=[[.24,140],[.86,90.5],[.86,49.3],[.2,41.4],[0.81,-.7],[.42,-0.6],[.86,-46.7],[.22,-48.1],[.8,-88.7],[.45,-87.4],[.85,-133.4],[.26,-122.9],[.85,-179.2],[.4,-177.2],[.81,139.9],[.36,89.9],[0.3,180],[0.3,-90],[0,0]]
#requested_reflections=[[.24,140],[.86,90.5],[.86,90.5],[.86,49.3],[.2,41.4],[.01,137.4],[0.81,-.7],[.42,-0.6]]
#requested_reflections=[[.24,140],[.86,90.5],[.86,49.3],[.2,41.4],[.01,137.4],[0.81,-.7],[.42,-0.6]]
NP=NoiseParameters(rm=rm,tunerIP=("192.168.1.31",23),navgPNA=2,navgNF=1,usePNA=False,usespectrumanalyzer=True,reflectioncoefficients=requested_reflections,tunercalfile=tunercal,cascadefiles_port1=cas1,cascadefiles_port2=cas2)        # do not use pna since we are measuring system noise parameters
#NP.measure_noiseparameters(frequenciesGHz=frequencies,DUTSpar=read_spar(SDUT))
NP.measure_noiseparameters_highspeed(frequenciesMHz=frequencies,spectrumanalyzerresolutionbandwidth=4E6,spectrumanalyzervideobandwidth=10,autoscalespectrumanalyzer=False,maxdeltaNF=0.1)
#NP.writefile_noiseparameters(pathname=datadir,devicename='6dB_pad')
# write_noisefigure_frequency_position_reflection(noisefilename=dembeddednoise,NF=NP.NF,tuner=NP,dBiNPut=False)
#write_noisefigure_frequency_position_reflection(noisefilename=rawnoise,NF=NP.NFraw,tuner=NP)
NP.writefile_noiseparameters(pathname=tundir,devicename=systemnoiseparametersfilename)
NP.writefile_noisefigure(pathname=tundir,devicename=dembeddednoise)
#pna.pna_RF_onoff(RFon=False)