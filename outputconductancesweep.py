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
from probe_constellations_map import *
from  outputZ import *
from writefile_measured import writefile_ivfoc_Vdsswept

#Vgs=-2.
gatecomp=0.001
frequency=[0.5E9,1.E9,1.5E9,3.E9,5.E9,10.E9]
IFbandwidth=40000
Pin=-15.
period=0.01
Vdslow=-2.
Vdshigh=2.

rm = visa.ResourceManager()
print (rm.list_resources())
bias=amrelPowerSupply(rm=rm)
scope=OscilloscopeDS1052E(rm=rm,shortoutput=True)
pna=Pna(rm=rm,navg=1,readdefaultconfig=False)                                  # set up Pna and get Pna handle
vdsgen=PulseGeneratorDG1022(rm=rm)

wafername="QH27"
runnumber=6
maskname="v6_2finger_single"
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno

#
cascade = CascadeProbeStation(rm=rm)         # setup Cascade NO probeplan file here! This also moves
probc=ConstellationsdB(maskname=maskname,wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probelistfilename=pathname+"/selected_devices.csv")
#probeconstellations=probc.get_probing_constellations(probe_device_list="C9_R5_T50_D12")

for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
	devicename=device["name"]
	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
	print ("probing devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"])
	for freq in frequency:
	# ret=measure_outputZ_sweptVds(gatebiassource=bias,scope=scope,pna=pna,siggen=vdsgen,frequency=frequency,Pin=Pin,period=period,IFbandwidth=IFbandwidth,npts=100,numberofaverages=256,Vgs_start=-3,Vgs_stop=0,Vgs_step=0.5,Vds_start=0,Vds_stop=-1.5)
	# writefile_ivfoc_Vdsswept(pathname=pathname,devicename=devicename,wafername=wafername,xloc=pconst['X'],yloc=pconst['Y'],devicenamemodifier="Vds1",data=ret)
		ret=measure_outputZ_sweptVds(gatebiassource=bias,scope=scope,pna=pna,siggen=vdsgen,frequency=freq,Pin=Pin,period=period,IFbandwidth=IFbandwidth,npts=100,numberofaverages=256,Vgs_start=-3,Vgs_stop=-3,Vgs_step=0.,Vds_start=0,Vds_stop=-1.,drainterminated=True)
		writefile_ivfoc_Vdsswept(pathname=pathname,devicename=devicename,wafername=wafername,xloc=pconst['X'],yloc=pconst['Y'],devicenamemodifier="f_"+formatnum(freq/1E9,precision=1,nonexponential=True)+"_Vds_-1_2nd",data=ret)
	#writefile_ivfoc_Vdsswept(pathname=pathname,devicename="test",wafername=wafername,xloc=0,yloc=0,devicenamemodifier="",data=ret)
	# ret=measure_outputZ_sweptVds(gatebiassource=bias,scope=scope,pna=pna,siggen=vdsgen,frequency=frequency,Pin=Pin,period=period,IFbandwidth=IFbandwidth,npts=100,numberofaverages=256,Vgs_start=-3,Vgs_stop=0,Vgs_step=0.5,Vds_start=0,Vds_stop=-0.5)
	# writefile_ivfoc_Vdsswept(pathname=pathname,devicename=devicename,wafername=wafername,xloc=pconst['X'],yloc=pconst['Y'],devicenamemodifier="Vds0.5",data=ret)
	# err,gatestatus,Vgsactual,Ig=bias.setvoltage(Vset=abs(Vgs),compliance=gatecomp)
	# timstampsscope,Id,Vds=ramped_sweep_drain(scope=scope,pulsegenerator=vdsgen,period=period,Vdslow=Vdslow,Vdshigh=Vdshigh,average=10,volttocurrentcalibrationfactor=volttocurrentcalibrationfactor,drainminguess=Vdslow-.5,drainmaxguess=Vdshigh+0.5)
	# timepts,s22=pna.getS22_time(sweeptime=period,power=-15,numberofpoints=50,ifbandwidth=10000,navg=512)
vdsgen.pulsetrainoff()
bias.output_off()


cascade.move_separate()
cascade.unlockstage()
print("done probing wafer")
