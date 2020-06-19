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
from pulsed_measurements import ramped_sweep_pulsed_gate
from scipy import stats
import numpy as np
import time


rm=visa.ResourceManager()
print(rm.list_resources())
ps=ParameterAnalyzer(rm)
scope=OscilloscopeDS1052E(rm)
pulse=PulseGeneratorDG1022(rm)

gcomp=0.001
dcomp=0.1
Vds=-1
Vgs=-2

wafername="QH11"
runnumber=2
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/QH11meas2"
cascade = CascadeProbeStation(rm=rm)                                                               # setup Cascade
probc=ConstellationsdB(maskname="v6_2finger_single",wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probe_device_list=["C5_R5_B50_D13"])

pconst=probeconstellations[0]
cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
devicename=device["name"]
print("device ", pconst["name"])
#ps.measure_ivtransfer_topgate(inttime='2',delaytime=0.05,Vds=Vds, Vgs_start=-3, Vgs_stop=2, Vgs_step=0.2, gatecomp=gcomp, draincomp=dcomp)
Idval,Igval,Idcompstatval,Igcompstatval=ps.fetbiason_topgate(Vgs=Vgs, Vds=Vds, gatecomp=gcomp, draincomp=dcomp)

navg=256
period=0.2E-3
pulsevoltage=-3.5
quiescentvoltage=-0.
pulsewidth=4E-6
dutycycle=0.5

t,V1,V2=ramped_sweep_pulsed_gate(scope=scope, pulsegenerator=pulse, period=period, dutycyclefraction=dutycycle, pulsewidth=pulsewidth, soaktime=10.,
                                 quiescentVgs=quiescentvoltage, drainmaxguess=0.,drainminguess=-1.,
                                 pulsedVgs=pulsevoltage, smoothfactor=0, volttocurrentcalibrationfactor=6.6225E-3)


filename="C:/Users/test/test_pulse/pulses.xls"
outf = open(filename, 'w')
outf.write("time(sec)\tch2volt(V)\tch1volt(V)\n")
for i in range(0,len(t)):
	print(t[i],V2[i],V1[i])
	outf.write('%10.5E\t%10.5E\t%10.5E\n' %(t[i],V2[i],V1[i]) )
outf.close()


