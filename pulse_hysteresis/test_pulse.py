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

wafername="QH4"
runnumber=7
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/QH4meas7"
cascade = CascadeProbeStation(rm=rm)                                                               # setup Cascade
probc=ConstellationsdB(maskname="v6_2finger_single",wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probe_device_list=["C8_R5_B100_D12"])

pconst=probeconstellations[0]
cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
devicename=device["name"]
print("device ", pconst["name"])
#ps.measure_ivtransfer_topgate(inttime='2',delaytime=0.05,Vds=Vds, Vgs_start=-3, Vgs_stop=2, Vgs_step=0.2, gatecomp=gcomp, draincomp=dcomp)
Idval,Igval,Idcompstatval,Igcompstatval=ps.fetbiason_topgate(Vgs=Vgs, Vds=Vds, gatecomp=gcomp, draincomp=dcomp)

navg=1
period=5.
pulsevoltagelow=-3.
pulsevoltagehigh=0.
pulsewidth=5E-6

topgate=pulsevoltagehigh+0.1*abs(pulsevoltagehigh-pulsevoltagelow)
botgate=pulsevoltagelow-0.1*abs(pulsevoltagehigh-pulsevoltagelow)
topdrain=-0.
botdrain=-1.1
startpulselogtime=0E-6
stoppulselogtime=100E-6


scope.set_trigger(level=0.7,sweep="SINGLE")

# # channel 1 autoscale
# channel 1 is the drain
scope.set_fulltimescale(fullscale=5*100E-6)                 # set horizontal scale on scope
minvch1,maxvch1,actualpulsewidth1,actualvoltagelow1,actualvoltagehigh1 = autoscale(pulse=pulse, scope=scope, pulsewidth=100E-6, period=1E-3, channel=1, scopebottomscale_guess=botdrain, scopetopscale_guess=topdrain, pulsegen_min_voltage=pulsevoltagelow, pulsegen_max_voltage=pulsevoltagehigh, probeattenuation=1, pulsegeneratoroutputZ=50)
minvch2,maxvch2,actualpulsewidth2,actualvoltagelow2,actualvoltagehigh2 = autoscale(pulse=pulse, scope=scope, pulsewidth=100E-6, period=1E-3, channel=2, scopebottomscale_guess=botdrain, scopetopscale_guess=topdrain, pulsegen_min_voltage=pulsevoltagelow, pulsegen_max_voltage=pulsevoltagehigh, probeattenuation=1, pulsegeneratoroutputZ=50)

# if actualvoltagelow!=botdrain: print("bot,actualvoltagelow",botdrain,actualvoltagelow)
# if actualvoltagehigh!=topdrain: print("top,actualvoltagehigh",topdrain,actualvoltagehigh)
# print("final channel 1 (gate) minv,maxv ",minvch1,maxvch1)



# minvch1,maxvch1,actualpulsewidth,actualvoltagelow,actualvoltagehigh = autoscale(pulse=pulse, scope=scope, pulsewidth=pulsewidth, period=min(0.1,2*period), channel=1, scopebottomscale_guess=botdrain, scopetopscale_guess=topdrain, pulsegen_min_voltage=pulsevoltagelow, pulsegen_max_voltage=pulsevoltagehigh, probeattenuation=1, pulsegeneratoroutputZ=50)
# pulse.set_pulsesetup_continuous(polarity='-',pulsewidth=pulsewidth,period=period,voltagehigh=pulsevoltagehigh,voltagelow=pulsevoltagelow,pulsegeneratoroutputZ='inf')
# pulse.pulsetrainon()
pulse.pulsetrainoff()
pulse.ramppulses(period=1E-3, quiescentvoltage=0., pulsedvoltage=-3, pulsewidth=4E-6, dutycyclefraction=0.2, pulsegeneratoroutputZ="50")
#pulse.set_pulsesetup_continuous(pulsewidth=5E-6,period=50E-6,voltagelow=-1,voltagehigh=0)
#pulse.pulsewaveform_controlledslew(period=1E-3,voltagequescent=0.,voltagepulse=-1,pulsewidth=5E-6,risefalltimenpts=2,nptsinpulse=20)
pulse.pulsetrainon()

scope.set_dualchannel(ch1_bottomscale=minvch1,ch1_topscale=maxvch1,ch2_bottomscale=minvch2,ch2_topscale=maxvch2)

scope.set_average(256)
scope.set_trigger(level=0.7,sweep="SINGLE")
actualfulltimescale,actualtimeoffset=scope.set_fulltimescale(fullscale=1E-3)

scope.stop()
scope.run()
pulse.pulsetrainoff()
ps.fetbiasoff()
ret=scope.get_dual_data(R=0)
#timeresolution=2E-7
timesmooth=1E-6
deltat=np.average(np.diff(ret['t']))
t=list(ret['t'])
V1=list(ret['Vch1'])
V2=list(ret['Vch2'])
#Navg=int(timeresolution/deltat)
Nsmooth=int(timesmooth/deltat)
#timestamps=[]

#timestamps=[np.average([t[j] for j in range(i, i+Navg)]) for i in range(0,len(t)-Navg-1)]
# for i in range(0,len(t)-Navg):
# 	avg=np.average([V1[j] for j in range(i, i+Navg)])
# 	Vch1.append(avg)
timestamps=[t[i] for i in range(0,len(t)) if t[i]<1E-3]
Vch1=[V1[i] for i in range(0,len(t)) if t[i]<1E-3]
Vch2=[V2[i] for i in range(0,len(t)) if t[i]<1E-3]

#Vch1=[np.average([V1[j] for j in range(i-int(Nsmooth/2),i+int(Nsmooth/2))]) for i in range(int(Nsmooth/2),len(V1)-int(Nsmooth/2),1) if t[i]<0.2E-3]
#timestamps=[np.average([t[j] for j in range(i-int(Nsmooth/2),i+int(Nsmooth/2))]) for i in range(int(Nsmooth/2),len(t)-int(Nsmooth/2),1) if t[i]<0.2E-3]
#timestamps=[np.average([t[j] for j in range(i-int(Navg/2), i+int(Navg/2)+1)]) for i in range(int(Navg/2),len(t)-Navg-1,Navg) if t[i]<1E-3]
#Vch1=[np.average([V1[j] for j in range(i-int(Nsmooth/2),i+int(Nsmooth/2))]) for i in range(int(Nsmooth/2),len(V1)-int(Nsmooth/2),1) if t[i]<0.2E-3]
#Vch1=[np.average([Vch1[j] for j in range(i-int(Navg/2), i+int(Navg/2)+1)]) for i in range(int(Navg/2),len(Vch1)-int(Navg/2)-1,Navg) if t[i]<1E-3]

filename="C:/Users/test/test_pulse/pulses.xls"
outf = open(filename, 'w')
outf.write("time(sec)\tch2volt(V)\tch1volt(V)\n")
for i in range(0,len(timestamps)):
	print(timestamps[i],Vch2[i],Vch1[i])
	outf.write('%10.5E\t%10.5E\t%10.5E\n' %(timestamps[i],Vch2[i],Vch1[i]) )
outf.close()

print(len(ret))


