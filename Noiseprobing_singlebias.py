# main wafer probing routine
import visa
import numpy as np
from measure_noiseparameters_focus import *
from read_write_spar_noise import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
#iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
# bias
Vds_bias = 0                                                                   # also used for S-parameter drain bias
#
gatecomp = 5E-5                                                                   # gate current compliance in A
draincomp = 0.1                                                                   # drain current compliance in A
Vgs_bias_start = -0.5                                                                     # gate bias for S-parameters
Vgs_bias_stop = -2.0
Vgs_bias_step=-0.1

Vgs_values=np.linspace(start=Vgs_bias_start,stop=Vgs_bias_stop,num=1+int((Vgs_bias_stop-Vgs_bias_start)/Vgs_bias_step))

tundir="C:/Users/test/focus_setups/noise/"          # base directory of noise calibrations
inputcircuitfile=tundir+"noise__coupler_biastee_isolator_April23_2020_SRI.s2p"
tunercal="c:/Users/test/focus_setups/tunercals_sourcepull/tunercal_1389source_April16_2020_1GHz_1.6GHz_13pts.txt"

systemnoiseparametersfilename=tundir+"noisesystem_spectrum_analyzer_April27_2020_SRI.s2p_noiseparameter.xls"
#systemnoiseparametersfilename=tundir+"noisesystem_spectrum_analyzer_noisolatorprobe_May4_2020_SRI.s2p_noiseparameter.xls"
#probefile=tundir+"/RF/JC2G4_Oct9_2019trl_SRI.s2p"           # this is the probe on the left side
#probefile=tundir+"/RF/JC2G4_May4_2018_SRI.s2p"           # this is the probe on the left side
#probefile=tundir+"/RF/noise_outputcableport2_oct11_2019_SRI.s2p"
#cas2=[[probefile,'noflip']]
cas2=None
cas1=[[inputcircuitfile,'noflip']]          # tuner cascade instructions

wafername="NPtests"

#devicename="noisesystemtest_6dBpad_serialno_18830_Dec20_2019"
#devicename="ZX60-2522M-S+_SN-F517501621"
devicename="highref_isolator_May19_2020_0.15dBdelta"
#devicename="noisesystemtest_thru_Dec20_2019"
wafername_runno="NPtests1"
pathname="C:/Users/test/python/data/NPtests1/"


#requested_reflections=[ [0.419,136.599], [0.450,-131.747], [0.467,-40.985], [0.447,48.737], [0.172,86.740], [0.145,-177.240], [0.169,0.908], [0.163,-81.455], [0.497,-84.965], [0.377,-1.795], [0.360,90.749], [0.358,-178.107] ]
#requested_reflections = [ [0.471,-89.397], [0.449,0.958], [0.394,88.578], [0.411,-179.026], [0.234,-125.345], [0.200,-47.370], [0.223,36.658], [0.241,136.153] ]
#requested_reflections = [ [0.321,15.333], [0.718,72.355], [0.519,31.119], [0.470,73.888], [0.605,105.739], [0.409,131.371], [0.412,-42.348], [0.505,-18.662], [0.201,-71.726], [0.200,73.090], [0.541,60.575], [0.410,94.716], [0.699,-17.472], [0.402,-65.097], [0.254,-126.121], [0.414,-155.555], [0,0] ]
#requested_reflections = [ [0.321,15.333], [0.718,72.355], [0.519,31.119], [0.470,73.888], [0.605,105.739], [0,0], [.45,45]]
#requested_reflections = [[0.77,65],[.7, 42],[.5,82],[.43,42],[.7,54],[.85,50],[.51,60],[.83,84],[.79,22],[.7,170],[.9,170],[.5,170],[0.73,166],[.2,170],[0,0],[.5,0],[.9,117]]
#requested_reflections=[[.5,0],[0.5,90],[0.5,180],[0.5,-90],[0.3,0],[0.3,90],[0.3,180],[0.3,-90],[0,0],[.1,0],[.1,90],[.1,180],[.1,-90]]
requested_reflections=[ [0.804,116.780], [0.551,129.103], [0.536,95.156], [0.819,132.232], [0.865,106.549], [0.559,112.884], [0.744,152.747], [0.338,130.023], [0.763,93.623], [0.509,154.375], [.9,115], [.6,115],[.8,125],[.8,105]  ]
NP=NoiseParameters(rm=rm,tunerIP=("192.168.1.31",23),navgNF=1,navgPNA=2,usespectrumanalyzer=True,usePNA=True,tunercalfile=tunercal,cascadefiles_port1=cas1,cascadefiles_port2=cas2,reflectioncoefficients=requested_reflections,system_noiseparametersfile=systemnoiseparametersfilename)

#frequencies=list(np.linspace(1200,1500,31))          # selected frequencies MHz
frequencies=[1250]        # selected frequencies MHz
Vgs=0
Id=0
Ig=0
# iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=Vds_bias, Vgs_start=-2, Vgs_stop=1., Vgs_step=0.1, gatecomp=gatecomp,draincomp=draincomp)
# iv.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=0,yloc=0,devicenamemodifier='Vds='+formatnum(Vds_bias,precision=2,nonexponential=True)+'_beforenoisepar')

# for Vgs in Vgs_values:
# 	Id,Ig,drainstatus,gatestatus=iv.fetbiason_topgate(Vgs=Vgs, Vds=Vds_bias, gatecomp=gatecomp, draincomp=draincomp,timeiter=30.,maxchangeId=0.01,maxtime=40.)				# bias device
#print("Vgs Vds Id, Ig 1st",Vgs,Vds_bias,Id,Ig)
NP.measure_noiseparameters_highspeed(frequenciesMHz=frequencies,spectrumanalyzerresolutionbandwidth=100E3,spectrumanalyzervideobandwidth=10,pna_instrumentstate2port="2port_LF.sta",pna_instrumentstate1port="S22.sta",pna_calset2port="CalSet_1",pna_calset1port="CalSet_2",autoscalespectrumanalyzer=False,maxdeltaNF=0.15)
#pna.pna_getS(8)												# get the S-parameters
#[sparf,devname]=pna.writefile_spar(measurement_type="All_RI",pathname=pathname,devicename=devicename,wafername=wafername,xloc=0,yloc=0,Vds=Vds_bias,Vgs=Vgs,Id=Id,Ig=Ig,gatestatus=gatestatus,drainstatus=drainstatus,devicenamemodifier="Vds"+formatnum(Vds_bias,precision=2)+"V_Vgs"+formatnum(Vgs,precision=2)+"V")
#iv.fetbiasoff()
NP.writefile_noisefigure(pathname=pathname,wafername=wafername_runno,devicename=devicename,Vds=Vds_bias,Vgs=Vgs,Id=Id,Ig=Ig,devicenamemodifier="")
NP.writefile_noiseparameters(pathname=pathname,wafername=wafername_runno,devicename=devicename,Vds=Vds_bias,Vgs=Vgs,Id=Id,Ig=Ig,devicenamemodifier="")
