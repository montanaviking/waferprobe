# main wafer probing routine
import visa
import numpy as np
#from measure_noiseparameters_sweptgate import *
from get_DUTnoiseparameters_sweptgate_coldsource import *
from read_write_spar_noise import *
from writefile_measured import writefile_noiseparameters_Vgssweep, writefile_noisefigure_Vgssweep

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
#iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
# bias
Vds_bias = 2                                                                   # also used for S-parameter drain bias
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
inputprobe=tundir+"ACP150_JC2G6-1_May4_2020_SRI.s2p"
inputfile_noisemeterdiodedata=tundir+"1_1.6GHz_gainbandwidth_gamma_June12_2020.xls"
inputfile_noisemeternoiseparameters=tundir+"nmcold_npJune12_2020_noiseparameter.xls"
cas2=None
#cas2=[[inputprobe,'noflip']]          # tuner cascade instructions for cascade probe
cas1=[[inputcircuitfile,'noflip']]          # tuner cascade instructions

wafername="NPtests"

#devicename="noisesystemtest_6dBpad_serialno_18830_Dec20_2019"
#devicename="ZX60-2522M-S+_SN-F517501621"
#devicename="GaNHEMT_swept_May14_2020"
devicename="couplerisolator_swept_June15_2020"
#devicename="noisesystemtest_thru_Dec20_2019"
wafername_runno="GaNnoise_May14_2020"
pathname="C:/Users/test/python/data/GaNnoise_May14_2020"


requested_reflections=[ [0.015,-50.368], [0.225,91.200], [0.239,-86.499], [0.275,-177.543], [0.252,-2.691], [0.793,48.837], [0.787,139.588], [0.761,-141.322], [0.849,-46.019] ]
#NP=NoiseParametersSweptGate(rm=rm,tunerIP=("192.168.1.31",23),usePNA=True,tunercalfile=tunercal,cascadefiles_port1=cas1,cascadefiles_port2=cas2,reflectioncoefficients=requested_reflections,system_noiseparametersfile=systemnoiseparametersfilename)
np=get_DUTnoiseparameters_sweptgate_coldsource(tunercalfile=tunercal,cascadefiles_port1=cas1,cascadefiles_port2=cas2,reflectioncoefficients=requested_reflections,system_noiseparametersfile=inputfile_noisemeternoiseparameters,inputfile_noisemeterdiodedata=inputfile_noisemeterdiodedata,
                                               NFaverage=16, frequenciesMHz=[1250],navgPNA=4)

#frequencies=list(np.linspace(1200,1500,31))          # selected frequencies MHz
#frequencies=[1250]        # selected frequencies MHz

# iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=Vds_bias, Vgs_start=-2, Vgs_stop=1., Vgs_step=0.1, gatecomp=gatecomp,draincomp=draincomp)
# iv.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=0,yloc=0,devicenamemodifier='Vds='+formatnum(Vds_bias,precision=2,nonexponential=True)+'_beforenoisepar')

# for Vgs in Vgs_values:
# 	Id,Ig,drainstatus,gatestatus=iv.fetbiason_topgate(Vgs=Vgs, Vds=Vds_bias, gatecomp=gatecomp, draincomp=draincomp,timeiter=30.,maxchangeId=0.01,maxtime=40.)				# bias device
#print("Vgs Vds Id, Ig 1st",Vgs,Vds_bias,Id,Ig)
#np = NP.measure_noiseparameters(PNAaverage=4,NFaverage=4000,RFMHzfrequency_list=[1250],Vsweptmax=-1.8,Vsweptmin=-2.8,Vconstbias=Vds_bias,maxdeltaNF=100,videobandwidthsetting=10E3)
#np = NP.measure_noiseparameters(PNAaverage=4,NFaverage=10000,RFMHzfrequency_list=[1250],Vsweptmax=0,Vsweptmin=-1,Vconstbias=Vds_bias,maxdeltaNF=100,videobandwidthsetting=10E3)
#pna.pna_getS(8)												# get the S-parameters
#[sparf,devname]=pna.writefile_spar(measurement_type="All_RI",pathname=pathname,devicename=devicename,wafername=wafername,xloc=0,yloc=0,Vds=Vds_bias,Vgs=Vgs,Id=Id,Ig=Ig,gatestatus=gatestatus,drainstatus=drainstatus,devicenamemodifier="Vds"+formatnum(Vds_bias,precision=2)+"V_Vgs"+formatnum(Vgs,precision=2)+"V")
#iv.fetbiasoff()
writefile_noiseparameters_Vgssweep(pathname=pathname,wafername=wafername_runno,devicename=devicename,timestamps=np['timestamps'],Vds=Vds_bias,Vgs=np['Vgs'],Id=np['Id'],NP=np['NP'],videobandwidth=np['videobandwidth'],resolutionbandwidth=np['resolutionbandwidth'],devicenamemodifier="")
writefile_noisefigure_Vgssweep(pathname=pathname,wafername=wafername_runno,devicename=devicename,Vds=Vds_bias,Vgs=np['Vgs'],Id=np['Id'],timestamps=np['timestamps'],NFmeas=np['NF'],NFcalcfromNP=np['NFcalcfromNP'],gammatuner=np['gammatunerMA'],videobandwidth=np['videobandwidth'],resolutionbandwidth=np['resolutionbandwidth'],devicenamemodifier="")

