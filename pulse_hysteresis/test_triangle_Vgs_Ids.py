__author__ = 'PMarsh Carbonics'
# pulse and acqusition of pulse data for hysteresis testing
# Phil Marsh Carbonics Inc
import visa
from oscilloscope import OscilloscopeDS1052E
from pulse_utilities import *
from pulsegenerator import *
from parameter_analyzer import *
from cascade import CascadeProbeStation
from create_probeconstellations_devices.probe_constellations_map import *
from pulsed_measurements import ramped_sweep_gate
from IP3_Vgssweep import *
from scipy import stats
import numpy as np
import time


rm=visa.ResourceManager()
print(rm.list_resources())
ps=ParameterAnalyzer(rm)
scope=OscilloscopeDS1052E(rm,shortoutput=True)
pulse=PulseGeneratorDG1022(rm)
Pin=-14
#IP3=IP3_Vgssweep(rm=rm, vgsgen=pulse,bias=ps, scope=scope,powerlevel_minimum=Pin, powerlevel_maximum=Pin, powerlevel_step=0, center_frequency=1.5E9, frequency_spread=4E6, Vgsmin=-2.5, Vgsmax=0, Vgsperiod=0.01)

gcomp=0.001
dcomp=0.1
Vds=-1
Vgs=0.

wafername="QW10"
runnumber=1
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno
#pathname="C:/Users/test/test_pulse"
cascade = CascadeProbeStation(rm=rm)                                                               # setup Cascade
probc=ConstellationsdB(maskname="v6_2finger_single",wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
#probeconstellations=probc.get_probing_constellations(probe_device_list=["C8_R5_B100_D12"])
#probeconstellations=probc.get_probing_constellations(probe_device_list=["C5_R7_B50_D23"])
probeconstellations=probc.get_probing_constellations(probe_device_list=["C9_R4_T50_D23"])

pconst=probeconstellations[0]
cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
devicename=device["name"]
print("device ", pconst["name"])
# ps.measure_ivtransfer_topgate(inttime='2',delaytime=0.05,Vds=Vds, Vgs_start=-3, Vgs_stop=2, Vgs_step=0.2, gatecomp=gcomp, draincomp=dcomp)
# ps.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=pconst["X"],yloc=pconst["Y"])
# quit()
Idval,Igval,Idcompstatval,Igcompstatval=ps.fetbiason_topgate(Vgs=Vgs, Vds=Vds, gatecomp=gcomp, draincomp=dcomp)

navg=256
period=10E-3
Vgshigh=0
Vgslow=-2.5
#IP3.measureTOI_gain(Pin=Pin,output_reflection=[0.,-180],Vds=Vds,noavg_dist=256,setup=True,quickmeasurement=True)
#t,Id,Vgs=ramped_sweep_gate(scope=scope, pulsegenerator=pulse, period=period, soaktime=10., Vgslow=Vgslow, Vgshigh=Vgshigh,drainmaxguess=0.,drainminguess=-2.,volttocurrentcalibrationfactor=6.6225E-3,average=18)

filename="C:/Users/test/test_pulse/pulses_tri.xls"
outf = open(filename, 'w')
outf.write("time(sec)\tch2volt(V)\tch1volt(V)\n")
for i in range(0,len(t)):
	print(t[i],Vgs[i],Id[i])
	outf.write('%10.5E\t%10.5E\t%10.5E\n' %(t[i],Vgs[i],Id[i]) )
outf.close()
cascade.move_separate()
cascade.unlockstage()




