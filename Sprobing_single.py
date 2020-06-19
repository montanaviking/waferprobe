# main wafer probing routine
#import pylab as pl
import visa
#from utilities import formatnum
import time

#from IP3_measure import IP3
#from spectrum_analyzer import *
#from rf_sythesizer import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())
from HP8970B_noisemeter import *

#from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from pna import Pna                                                                 # network analyzer
#from old.plotSmeas import dataPlotter
from device_parameter_request import DeviceParameters

pna = Pna(rm,1)                                                                    # setup network analyzer
noisesource = NoiseMeter(rm=rm,ENR=15,preset=True,turnonnoisesourceonly=True)               # ENR is bogus because the noise meter is being used only to drive the noise source
#iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
#sp = dataPlotter()
#quit()

# bias
#Vds_bias = 10.                                                                   # also used for S-parameter drain bias
gatecomp = 5E-4                                                                   # gate current compliance in A
draincomp = 0.1                                                                   # drain current compliance in A
#Vgs_bias = 0.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
goodId=0.1E-4                        # drain current must exceed this to qualify device for further testing
goodonoff=10.                       # acceptable on-off ratio for S-parameter testing
Vgs_validation = -2.
Vds_validation = -1.
Vgs_pinchoffval=1.



#pathname = "C:/Users/test/python/data/TOIsysApril27_2018"
#pathname = "C:/Users/test/focus_setups/cascadeprobes"

#pathname="C:/Users/test/python/data/"

#pathname="C:/Users/test/focus_setups/power/July12_2019/"
#pathname="C:/Users/test/python/data/QH4meas11/"
#wafername="QH4meas11"
X=0
Y=0

Vgs_bias=0
Vds_bias=0
runno="meas1"
wafername=""
#devicename="R1_C8_line_1300um_TRLcal"

pathname="c:/Users/test/focus_setups/noise/"
#devicename="6dBpad_SN18830"

#devicename="ACP40-A_JC2G4_Oct9_2019__short"

#devname="biastee_isolator_TOI_Nov28_2018"
#wafername="Wf170_ESDtest"
#wafername="Wf167_aftermountfrommicroQ_June_2018"
#wafername="QW2"
#devname="pad_R-25W3L7.5_v6quartz_TRLcal"
#devname="pad_R-100W3L30_v6quartz_SOLTp1cal"
#devname="short"
#iv.fetbiasoff()
#
# iv.measure_ivtransferloop_controlledslew(backgated=False,Vgsslewrate=1.,Vds=Vds_bias,Vgs_start=-4,Vgs_stop=-2,Vgs_step=0.05,gatecomp=gatecomp,draincomp=draincomp)
# iv.writefile_ivtransferloop(pathname=pathname,devicename=devname,wafername=wafername,xloc_probe=0,yloc_probe=0,devicenamemodifier=formatnum(Vds_bias,precision=2)+'_')
#iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=-1, Vgs_start=-10., Vgs_stop=2., Vgs_step=.1, gatecomp=gatecomp, draincomp=draincomp)
#iv.writefile_ivtransfer(pathname=pathname,devicename=devname,wafername=wafername,xloc_probe=0,yloc_probe=0,devicenamemodifier='')
# iv.measure_ivfoc_topgate(sweepdelay=0.1, Vds_start=-0.1,Vds_stop=0.1,Vds_npts=21, Vgs_start=0,Vgs_stop=0.,Vgs_npts=1,gatecomp=.1,draincomp=.1)
# iv.writefile_ivfoc(pathname=pathname,devicename=devname,wafername=wafername, xloc=0,yloc=0,devicenamemodifier="")
#Id,Ig,drainstatus,gatestatus=iv.fetbiason_topgate(Vds=Vds_bias, Vgs=Vgs_bias, gatecomp=gatecomp, draincomp=draincomp,timeiter=10,maxchangeId=0.01,maxtime=40.)				# bias device

# print("Vds, Vgs, Id, Ig",Vds_bias,Vgs_bias,Id,Ig)
#
# #pna.pna_RF_onoff(on=True)

#pna.pna_get_S_oneport(navg=4,type="s11")
# 		#Id,Ig,ds,gs=iv.fetbiason_topgate(Vgs_bias, Vds_bias, gatecomp, draincomp)				# bias device again to update currents etc..
# 			#print("Vds, Vgs, Id, Ig",Vds_bias,Vgs_bias,Id,Ig)
# #iv.fetbiasoff()													# bias off

#devicename="JC23F_open_May4_2020"
#devicename="noisemetergamma_May21_2020"
devicenamec="noisediodegammacold_May21_2020"
devicenameh="noisediodegammahot_May21_2020"


noisesource.noise_sourceonoff(on=False)     # turn off noise source
pna.pna_get_S_oneport(instrumentstate="S22.sta",calset="CalSet_3",type="s22",navg=4)												# get the 1-2GHz S-parameters
pna.writefile_spar(measurement_type="s22_only_RI",pathname=pathname,devicename=devicenamec,wafername=wafername,xloc=0,yloc=0,Vds=Vds_bias,Vgs=0,Id=0,Ig=0,devicenamemodifier="1_1.6GHz")
pna.writefile_spar(measurement_type="s22_only_DB",pathname=pathname,devicename=devicenamec,wafername=wafername,xloc=0,yloc=0,Vds=0,Vgs=0,Id=0,Ig=0,gatestatus='',drainstatus='',devicenamemodifier="1_1.6GHz")

noisesource.noise_sourceonoff(on=True)     # turn on noise source)
pna.pna_get_S_oneport(instrumentstate="S22.sta",calset="CalSet_3",type="s22",navg=4)												# get the 1-2GHz S-parameters
pna.writefile_spar(measurement_type="s22_only_RI",pathname=pathname,devicename=devicenameh,wafername=wafername,xloc=0,yloc=0,Vds=Vds_bias,Vgs=0,Id=0,Ig=0,devicenamemodifier="1_1.6GHz")
pna.writefile_spar(measurement_type="s22_only_DB",pathname=pathname,devicename=devicenameh,wafername=wafername,xloc=0,yloc=0,Vds=0,Vgs=0,Id=0,Ig=0,gatestatus='',drainstatus='',devicenamemodifier="1_1.6GHz")
noisesource.noise_sourceonoff(on=False)     # turn off noise source
# pna.pna_getS_2port(instrumentstate="2port_LF.sta",calset="CalSet_1",navg=4)												# get the 2-40GHz S-parameters
# pna.writefile_spar(measurement_type="all_RI",pathname=pathname,devicename=devicename,wafername=wafername,xloc=0,yloc=0,Vds=Vds_bias,Vgs=0,Id=0,Ig=0,devicenamemodifier="")
# pna.writefile_spar(measurement_type="all_DB",pathname=pathname,devicename=devicename,wafername=wafername,xloc=0,yloc=0,Vds=0,Vgs=0,Id=0,Ig=0,gatestatus='',drainstatus='',devicenamemodifier="")

# devicename="R6_C6_transitionopen"
# pna.pna_getS_2port(instrumentstate="2port_LF.sta",calset="CalSet_2",navg=4)												# get the 2-40GHz S-parameters
# pna.writefile_spar(measurement_type="all_RI",pathname=pathname,devicename=devicename,wafername=wafername,xloc=0,yloc=0,Vds=Vds_bias,Vgs=0,Id=0,Ig=0,devicenamemodifier="0.5_4GHz")
# pna.writefile_spar(measurement_type="all_DB",pathname=pathname,devicename=devicename,wafername=wafername,xloc=0,yloc=0,Vds=0,Vgs=0,Id=0,Ig=0,gatestatus='',drainstatus='',devicenamemodifier="0.5_4GHz")
# pna.pna_getS_2port(instrumentstate="2port_HF_TRL.sta",calset="CalSet_1",navg=4)												# get the 2-40GHz S-parameters
# pna.writefile_spar(measurement_type="all_RI",pathname=pathname,devicename=devicename,wafername=wafername,xloc=0,yloc=0,Vds=Vds_bias,Vgs=0,Id=0,Ig=0,devicenamemodifier="2_40GHz")
# pna.writefile_spar(measurement_type="all_DB",pathname=pathname,devicename=devicename,wafername=wafername,xloc=0,yloc=0,Vds=0,Vgs=0,Id=0,Ig=0,gatestatus='',drainstatus='',devicenamemodifier="2_40GHz")