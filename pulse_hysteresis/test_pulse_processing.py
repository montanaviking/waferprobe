__author__ = 'PMarsh Carbonics'
# pulse and acqusition of pulse data for hysteresis testing
# Phil Marsh Carbonics Inc
import visa
from oscilloscope import OscilloscopeDS1052E
from pulse_utilities import *
from pulsegenerator import *
from parameter_analyzer import *
from cascade import CascadeProbeStation
from scipy import stats
from create_probeconstellations_devices.probe_constellations_map import *

import numpy as np
import time

inputfile="/carbonics/owncloudsync/documents/analysis/test_pulse/pulses.xls"
inf=open(inputfile,'r')
t=[]
V1=[]
V2=[]
for l in inf.read().splitlines():
	if 'time' not in l:
		t.append(float(l.split()[0]))
		V2.append(float(l.split()[1]))
		V1.append(float(l.split()[2]))

timeresolution=2E-7
timesmooth=3E-6
deltat=np.average(np.diff(t))
#Navg=int(timeresolution/deltat)
Nsmooth=int(timesmooth/deltat)
rampperiod=0.2E-3
pulsewidth=4E-6
dutycycle=0.5
pulseperiod=pulsewidth/dutycycle
Nwindow=int(1.1*pulseperiod/deltat)
#timestamps=[]


# remove extra points
Vch1=[V1[i] for i in range(0,len(V1)) if t[i]<rampperiod]
Vch2=[V2[i] for i in range(0,len(V2)) if t[i]<rampperiod]
t=[x for x in t if x<rampperiod]

Vch1=np.convolve(Vch1,np.ones((Nsmooth,))/Nsmooth,mode='valid')
Vch2=np.convolve(Vch2,np.ones((Nsmooth,))/Nsmooth,mode='valid')
timestamps=np.convolve(t,np.ones((Nsmooth,))/Nsmooth,mode='valid')

#timestamps=[np.average([t[j] for j in range(i-int(Navg/2), i+int(Navg/2)+1)]) for i in range(int(Navg/2),len(t)-Navg-1,Navg) if t[i]<1E-3]
#Vch1=[np.average([V1[j] for j in range(i-int(Nsmooth/2),i+int(Nsmooth/2))]) for i in range(int(Nsmooth/2),len(V1)-int(Nsmooth/2),1) if t[i]<0.2E-3]
#Vch1=[np.average([Vch1[j] for j in range(i-int(Navg/2), i+int(Navg/2)+1)]) for i in range(int(Navg/2),len(Vch1)-int(Navg/2)-1,Navg) if t[i]<1E-3]

# now find peak values and their times
# first establish the period of the
i=0
v1=[]
t1=[]
savepoint=True
while i<len(timestamps)-Nwindow:
	iminv=np.argmin([Vch1[ii] for ii in range(i,Nwindow+i)])        # get index of minimum (maximum negative) in the window interval
	if iminv<=Nwindow/2 and savepoint:             # pulse is near center of window
		v1.append(Vch1[i+iminv])
		t1.append(timestamps[i+iminv])
		i+=2
		savepoint=False
	else: i+=1                      # else keep sliding window
	if iminv>Nwindow/2:
		savepoint=True

i=0
v2=[]
t2=[]
savepoint=True
while i<len(timestamps)-Nwindow:
	iminv=np.argmin([Vch2[ii] for ii in range(i,Nwindow+i)])        # get index of minimum (maximum negative) in the window interval
	if iminv<=Nwindow/2 and savepoint:             # pulse is near center of window
		v2.append(Vch2[i+iminv])
		t2.append(timestamps[i+iminv])
		i+=2
		savepoint=False
	else: i+=1                      # else keep sliding window
	if iminv>Nwindow/2:
		savepoint=True


filename="/carbonics/owncloudsync/documents/analysis/test_pulse/smoothpulses.xls"
outf = open(filename, 'w')
outf.write("time(sec)\tvolt2(V)\tvolt1(V)\n")
for i in range(0,len(timestamps)):
	#print(timestamps[i],Vch1[i])
	outf.write('%10.5E\t%10.5E\t%10.5E\n' %(timestamps[i],Vch2[i],Vch1[i]) )
outf.close()

filename="/carbonics/owncloudsync/documents/analysis/test_pulse/pulse_values.xls"
outf = open(filename, 'w')
outf.write("time2(sec)\tvolt2(V)\ttime1 (sec)\tvolt1(V)\n")
for i in range(0,min(len(v1),len(v2))):
	#print(t[i],v2[i],v1[i])
	outf.write('%10.5E\t%10.5E\t%10.5E\t%10.5E\n' %(t2[i],v2[i],t1[i],v1[i]) )
outf.close()


filename="/carbonics/owncloudsync/documents/analysis/test_pulse/parametric_values.xls"
outf = open(filename, 'w')

# now match timepoints and plot the volt1 (representing the drain current) as a function of volt2 (representing the gate voltage
outf.write("v2\tv1\n")
for i in range(0,len(t2)):
	i1closest=min(range(len(t1)), key=lambda j:abs(t1[j]-t2[i]))
	outf.write('%10.5E\t%10.5E\n' %(v2[i],v1[i1closest]))
outf.close()

