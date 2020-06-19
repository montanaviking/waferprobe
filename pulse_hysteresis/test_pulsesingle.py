__author__ = 'PMarsh Carbonics'
# pulse and acqusition of pulse data for hysteresis testing
# Phil Marsh Carbonics Inc
import visa
from oscilloscope import OscilloscopeDS1052E
from pulsegenerator import *
from pulse_utilities import *
#from scipy import stats
#import time
import collections as c
rm=visa.ResourceManager()
print(rm.list_resources())
print("scope is")
scope=OscilloscopeDS1052E(rm)
pulse=PulseGeneratorDG1022(rm)
navg=1
period=5.
pulsevoltagelow=-3.
pulsevoltagehigh=1.
pulsewidth=50E-6
#pulsewidth=5E-3
triggerholdoff=scope.set_trigger(sweep="single")
print("trigger holdoff is",triggerholdoff)
scope.stop()
scope.set_fulltimescale(fullscale=5*pulsewidth)                 # set horizontal scale on scope

topgate=pulsevoltagehigh+0.1*abs(pulsevoltagehigh-pulsevoltagelow)
botgate=pulsevoltagelow-0.1*abs(pulsevoltagehigh-pulsevoltagelow)
topdrain=-0.
botdrain=-1.1
startpulselogtime=0E-6
stoppulselogtime=100E-6
#startpulselogtime=5E-7
#stoppulselogtime=startpulselogtime+0.4*pulsewidth
# autoscale channel #1 The pulse generator is set up to produce the correct amplitude and a shorter period than is used for the actual pulsed measurements
# channel 1 is the drain
minvch1,maxvch1,actualpulsewidth,actualvoltagelow,actualvoltagehigh = autoscale(pulse=pulse, scope=scope, pulsewidth=pulsewidth, period=min(0.1,5.*period), channel=1, scopebottomscale_guess=botdrain, scopetopscale_guess=topdrain, pulsegen_min_voltage=pulsevoltagelow, pulsegen_max_voltage=pulsevoltagehigh, probeattenuation=1, pulsegeneratoroutputZ=50)
if actualvoltagelow!=botdrain: print("bot,actualvoltagelow",botdrain,actualvoltagelow)
if actualvoltagehigh!=topdrain: print("top,actualvoltagehigh",topdrain,actualvoltagehigh)
print("final channel 1 (gate) minv,maxv ",minvch1,maxvch1)

# channel 2 is the gate
minvch2,maxvch2,actualpulsewidth,actualvoltagelow,actualvoltagehigh = autoscale(pulse=pulse, scope=scope, pulsewidth=pulsewidth, period=min(0.1,5.*period), channel=2, scopebottomscale_guess=botgate, scopetopscale_guess=topgate, pulsegen_min_voltage=pulsevoltagelow, pulsegen_max_voltage=pulsevoltagehigh, probeattenuation=10, pulsegeneratoroutputZ=50)
print("final channel 2 (drain) minv,maxv ",minvch2,maxvch2)
# set up pulse generator to produce actual pulses to be measured
#
pulse.set_pulsesetup(pulsewidth=pulsewidth,period=period,voltagehigh=pulsevoltagehigh,voltagelow=pulsevoltagelow,pulsegeneratoroutputZ=50)


#scope.set_channel(displaychannel=True,channel=1)

soaktime=scope.capture2ndpulse()        # capture scope data after 2nd pulse
# now get gate and drain voltages
d1=scope.get_data(channel=1,R=27.3,timerange=10.*pulsewidth,referencevoltage=-1.)      #channel 1 data (gate)
d2=scope.get_data(channel=2,R=27.3,timerange=10.*pulsewidth,referencevoltage=-1.)      #channel 2 data (drain)
vtpulse=[d1["Vt"][i] for i in range(0,len(d1["t"])) if d1["t"][i]>=startpulselogtime and d1["t"][i]<=stoppulselogtime]
vtref = [d2["Vt"][i] for i in range(0,len(d2["t"])) if d2["t"][i]>=5.*pulsewidth and d2["t"][i]<=10*pulsewidth]

Vpulse=np.mean(vtpulse)
Vpulsestddev=np.std(vtpulse)
Vref=np.mean(vtref)
Vrefstddev=np.std(vtref)


Vgspulse=[d1["Vt"][i] for i in range(0,len(d1["t"])) if d1["t"][i]>=startpulselogtime and d1["t"][i]<=stoppulselogtime]
Vdspulse=[d2["Vt"][i] for i in range(0,len(d2["t"])) if d2["t"][i]>=startpulselogtime and d2["t"][i]<=stoppulselogtime]
print("Vref = "+formatnum(Vref,precision=2)+" Vref std dev fraction "+formatnum(Vrefstddev/Vref,precision=2)+" Vpulse= "+formatnum(Vpulse,precision=2)+" Vpulse std dev fraction "+formatnum(Vpulsestddev/Vpulse,precision=2))

fout=open("C:/Users/test/python/junkdata/test.xls",'w')
fout.write("time\tvoltage\n")
deltai=1
fout.write("time S\tVds\tI(A)\tVgs\n")

for ii in range(0,len(d1["t"]),deltai):
	#fout.write('%10.6E\t%10.3f\t%10.3E\n'%(d["t"][ii],d["Vt"][ii],d["Ip"][ii]))
	if d1["t"][ii]>=startpulselogtime and d1["t"][ii]<=stoppulselogtime:
		fout.write('%10.6E\t%10.3f\t%10.3E\t%10.3E\n'%(d1["t"][ii],d1["Vt"][ii],d1["Ip"][ii],d2["Vt"][ii]))

print("soak time = ",soaktime)
#print("time array ",timearray)

#print("voltage low, high ",pulse.set_voltage(voltagehigh=-1.,voltagelow=-2.))
#print("actual full scope timescale setting ",actualfulltimescale)