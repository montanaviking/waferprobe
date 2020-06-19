
__author__ = 'PMarsh Carbonics'
# pulse and acqusition of pulse data for hysteresis testing
# Phil Marsh Carbonics Inc
import visa
from oscilloscope import OscilloscopeDS1052E
from pulsegenerator import *
from pulsed_measurements import *
from parameter_analyzer import *
import time
from cascade import *
from cascade import CascadeProbeStation
from create_probeconstellations_devices.probe_constellations_map import *



rm=visa.ResourceManager()
print(rm.list_resources())
print("scope is")
scope=OscilloscopeDS1052E(rm)
pulsegenerator=PulseGeneratorDG1022(rm)
ps=ParameterAnalyzer(rm)

soaktime=10E-3
pulsewidth=2E-6
soakvoltage=0.
Vds=-1.
maximumId_guess=3E-3
pulseVgs_start=-0.25
pulseVgs_step=-0.25
pulseVgs_stop=-3.0

startpulselogtime=1.5E-6
stoppulselogtime=1.8E-6


wafername="QH10"
runnumber=3
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno
cascade = CascadeProbeStation(rm=rm)                                                               # setup Cascade
probc=ConstellationsdB(maskname="v6_2finger_single",wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probe_device_list=["C4_R5_B50_D22"])

pconst=probeconstellations[0]
cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
devicename=device["name"]
print("device ", pconst["name"])
# ps.measure_ivtransfer_topgate(inttime='2',delaytime=0.05,Vds=Vds, Vgs_start=-3, Vgs_stop=2, Vgs_step=0.2, gatecomp=gcomp, draincomp=dcomp)
# ps.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=pconst["X"],yloc=pconst["Y"])
# quit()
Idval,Igval,Idcompstatval,Igcompstatval=ps.fetbiason_topgate(Vgs=0, Vds=Vds, gatecomp=0.001, draincomp=0.05)

navg=256
period=1.E-3
Vgshigh=-3.
Vgslow=0.

#filename="C:/Users/test/test_pulse/pulses_tri.xls"
ptran=pulsedGate(scope=scope,pulsegenerator=pulsegenerator,cascadeprobe=cascade,pulsewidth=pulsewidth,soaktime=soaktime,quiescentVgs=soakvoltage,startpulselogtime=startpulselogtime,stoppulselogtime=stoppulselogtime,pulseVgs_start=pulseVgs_start,pulseVgs_stop=pulseVgs_stop,pulseVgs_step=pulseVgs_step,Vds=Vds,maximumId_guess=maximumId_guess,volttocurrentcalibrationfactor=6.6225E-3)
ptran.measure_transfer_curve()
ptran.writefile_pulsedtransfer(pathname=pathname, wafername=wafername_runno, xloc=pconst["X"], yloc=pconst["Y"], Vds=Vds,devicename=devicename,writetimedomain=True)
cascade.move_separate()
cascade.unlockstage()