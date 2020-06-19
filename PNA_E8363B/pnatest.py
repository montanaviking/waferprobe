# driver test for PNA
import visa
import matplotlib.pyplot as plt
#import pyqtgraph.examples
import time
import os
import numpy as np
import pylab
#import mwavepy as mv
from pna import Pna
from loadpull_system_calibration import *
from pulsed_measurements import ramped_sweep_drain
from oscilloscope import *
#from parameter_analyzer import *
from amrel_power_supply import *
from pulsegenerator import *
from cascade import CascadeProbeStation                                                    # Cascade wafer prober


Vgs=-2.
gatecomp=0.001
period=2.
Vdslow=-1.
Vdshigh=0.

rm = visa.ResourceManager()
print (rm.list_resources())
# bias=amrelPowerSupply(rm=rm)
#scope=OscilloscopeDS1052E(rm=rm,shortoutput=True)
pna=Pna(rm=rm,navg=1)                                  # set up Pna and get Pna handle
#vdsgen=PulseGeneratorDG1022(rm=rm)
#
#pna.pna_load_instrumentstate(instrumentstatename="S22.sta",type='s22')
#pna.pna_RF_onoff(RFon=True)
#pna.pna_getS(navg=1)        # measure DUT S-parameters if we are using the PNA
pna.pna_get_S_oneport(navg=1,type="s11")
#pna.pna_RF_onoff(RFon=False)            # turn off PNA RF so as not to interfere with the noise measurements
#
# wafername="QH34"
# runnumber=2
# maskname="v6_2finger_single"
# wafername_runno=wafername+"meas"+str(runnumber)
# pathname = "C:/Users/test/python/data/"+wafername_runno
#
# cascade = CascadeProbeStation(rm=rm)         # setup Cascade NO probeplan file here! This also moves
# probc=ConstellationsdB(maskname=maskname,wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
# probeconstellations=probc.get_probing_constellations(probe_device_list="C5_R5_B50_D32")
#
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
# 	devicename=device["name"]
# 	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 	print ("probing devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"])

	#err,gatestatus,Vgsactual,Ig=bias.setvoltage(Vset=abs(Vgs),compliance=gatecomp)
#timstampsscope,Id,Vds=ramped_sweep_drain(scope=scope,pulsegenerator=vdsgen,period=period,Vdslow=Vdslow,Vdshigh=Vdshigh,average=1,volttocurrentcalibrationfactor=volttocurrentcalibrationfactor,drainminguess=Vdslow-.5,drainmaxguess=Vdshigh+0.5)
# vdsgen.ramp(period=period, Vmin=Vdslow, Vmax=Vdshigh, pulsegeneratoroutputZ="50")
# vdsgen.pulsetrainon()
#
# freq,s22=pna.getS22_time(sweeptime=period,power=-15,numberofpoints=10)
# vdsgen.pulsetrainoff()
# #bias.output_off()
# time.sleep(10)
# #
# # cascade.move_separate()
# # cascade.unlockstage()
# print("done probing wafer")
