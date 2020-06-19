# measure the preamp i.e. noise measurement system noise parameters
# calculates noise figure vs input reflection of noise meter then deembeds DUT noise figure based on noise meter noise figure calculated from the noise meter noise parameters

from measure_noiseparameters_sweptgate import *
from pna import *
import os
from read_write_spar_noise import *

rm = visa.ResourceManager()

# directories

#datadir=tundir             # noisefigure data directory
#system inputs
#tundir="C:/Users/test/focus_setups/noise"
tundir ="C:/Users/test/focus_setups/noise/"          # base directory of noise calibrations
inputcircuitfile=tundir+"noise__coupler_biastee_isolator_April17_2020_SRI.s2p"
#outputcircuitfile=tundir+"/RF/JC2G4_Oct9_2019trl_SRI.s2p"           # this is the probe on the left side
#outputcircuitfile=tundir+"/RF/JC2G4_May4_2018_SRI.s2p"           # this is the probe on the left side
#outputcircuitfile=tundir+"/RF/noise_outputcableport2_oct11_2019_SRI.s2p"
tunercal="c:/Users/test/focus_setups/tunercals_sourcepull/tunercal_1389source_April16_2020_1GHz_1.6GHz_13pts.txt"
pna=Pna(rm=rm,navg=4)

# DUT inputs
#SDUT=datadir+"10dB_pad_SRI.s2p"
pna.pna_RF_onoff(RFon=False)
#outputs
dembeddednoise="system_probe_NF_Dec20_2019"
rawnoise=tundir+"/system_probe_rawnoise_Dec20_2019.csv"
systemnoiseparametersfilename="system_probe_Dec20_2019_noiseparameters.xls"

cas2=None
#fulltunerpath=os.path.join(tundir,tunerfile)
#cas2=[[outputcircuitfile,'noflip']]         # wafer probe on tuner output for source pull
cas1=[[inputcircuitfile,'noflip']]          # tuner cascade instructions
#########################
#frequencies=np.linspace(1200,1500,31)
frequencies=[1200,1300,1400,1500]           # selected frequencies MHz
#frequencies=[1200]
# requested_reflections=[ [0.815,-178.140], [0.664,-178.137], [0.398,-177.587], [0.175,-174.514], [0.019,-59.625], [0.194,-2.082], [0.427,1.006], [0.616,-2.009], [0.819,0.185], [0.153,-88.134], [0.322,-87.394], [0.511,-88.900], [0.681,-89.174], [0.846,-89.335], [0.251,84.432], [0.497,88.310], [0.740,87.738], [0.880,88.099], [0.797,140.043], [0.535,140.301], [0.290,134.614], [0.085,124.442], [0.112,38.901], [0.307,42.137], [0.506,43.261], [0.736,42.470], [0.897,42.268], [0.143,-127.465], [0.277,-130.394], [0.479,-131.929], [0.653,-134.254], [0.818,-132.004], [0.157,-51.808], [0.379,-47.296], [0.588,-46.146], [0.825,-47.483], [0.711,-45.947], [0.291,-20.955], [0.106,-100.496], [0.112,-38.728], [0.116,80.299], [0.133,155.191], [0.182,36.902], [0.199,-148.473], [0.255,-85.612], [0.280,-55.165], [0.205,110.741], [0.228,59.351], [0.233,153.374], [0.529,-111.505], [0.505,-66.238], [0.495,-25.784], [0.453,23.017], [0.474,67.760], [0.483,120.790], [0.497,160.919], [0.474,-160.012], [0.674,20.859], [0.635,-15.713], [0.388,141.806], [0.375,-148.484], [0.395,-87.171], [0.353,95.492], [0.306,15.169], [0.717,13.111], [0.732,-17.516], [0.713,-0.957], [0.663,-33.494], [0.814,30.241], [0.822,-30.628], [0.325,-2.098] ]
requested_reflections= [ [0.471,-89.397], [0.449,0.958], [0.394,88.578], [0.411,-179.026], [0.234,-125.345], [0.200,-47.370], [0.223,36.658], [0.241,136.153], [0.828,-133.471], [0.822,140.347], [0.863,49.891], [0.857,-47.839], [0.823,-89.319], [0.826,-0.484], [0.836,-179.521], [0.882,90.306], [0,0] ]
#requested_reflections=[[0.5,45],[0.5,135],[0.5,-135],[0.5,-45], [0.2,0], [0.2,90],[0.2,180],[0.2,-90],[0.5,32],[0.5,50],[0,0]]
#requested_reflections=[[0.7,45], [0.3,0], [0.3,90],[0.3,180],[0.3,-90],[0,0]]
NP=NoiseParametersSweptGate(rm=rm,tunerIP=("192.168.1.31",23),navgPNA=2,usePNA=False,reflectioncoefficients=requested_reflections,tunercalfile=tunercal,cascadefiles_port1=cas1,cascadefiles_port2=cas2,measureDUToutputgamma=False)
#NP.measure_noiseparameters(frequenciesGHz=frequencies,DUTSpar=read_spar(SDUT))
# NP.get_NF_DUTandsystem_timedomain(frequencyMHz=1250, setup=True, NFaverage=2024, preamp=True)
# NP.writefile_systemnoisefigure_vs_time(pathname="C:/Users/test/python/data/testnoisesys",filename="timedomain_1250MHz_preampon")
NP.get_NF_DUTandsystem_frequencydomain(NFaverage=2,startfrequencyMHz=1000,stopfrequencyMHz=1600,videobandwidthsetting=10,resolutionbandwidthsetting=20E6,preamp=True)
NP.writefile_systemnoisefigure_vs_frequency(pathname="C:/Users/test/python/data/testnoisesys_April17_2020",filename="frequencydomain_preampon_RBW10MHz")
#NP.writefile_noiseparameters(pathname=datadir,devicename='6dB_pad')
# write_noisefigure_frequency_position_reflection(noisefilename=dembeddednoise,NF=NP.NF,tuner=NP,dBiNPut=False)
# write_noisefigure_frequency_position_reflection(noisefilename=rawnoise,NF=NP.NFraw,tuner=NP)
# NP.writefile_noiseparameters(pathname=tundir,devicename=systemnoiseparametersfilename)
# NP.writefile_noisefigure(pathname=tundir,devicename=dembeddednoise)
#pna.pna_RF_onoff(RFon=False)