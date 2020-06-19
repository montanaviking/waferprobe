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
import numpy as np
import time

inputfile="/carbonics/owncloudsync/documents/analysis/test_pulse/pulses_tri.xls"
inf=open(inputfile,'r')
t=[]
V1=[]
V2=[]
for l in inf.read().splitlines():
	if 'time' not in l:
		t.append(float(l.split()[0]))
		V2.append(float(l.split()[1]))
		V1.append(float(l.split()[2]))

#timeresolution=2E-7
timesmooth=1E-4
#draindelay=0.35E-7             # delay of drain circuit relative to gate due to scope probe bandwidth limitations
deltat=np.average(np.diff(t))
#pulseperiod=10E-6
#Ndelay=int(draindelay/deltat)           # drain delay in terms of raw data points
Nsmooth=int(timesmooth/deltat)          # convolution window for smoothing and consolidation of timeseries


#Nwindow=int(1.1*pulseperiod/deltat)
#timestamps=[]


# Vch1=[np.average([V1[j] for j in range(i-int(Nsmooth/2),i+int(Nsmooth/2))]) for i in range(int(Nsmooth/2),len(V1)-int(Nsmooth/2),1) if t[i]<rampperiod]
# Vch2=[np.average([V2[j] for j in range(i-int(Nsmooth/2),i+int(Nsmooth/2))]) for i in range(int(Nsmooth/2),len(V1)-int(Nsmooth/2),1) if t[i]<rampperiod]
#timestamps=[np.average([t[j] for j in range(i-int(Nsmooth/2),i+int(Nsmooth/2))]) for i in range(int(Nsmooth/2),len(t)-int(Nsmooth/2),1) if t[i]<rampperiod]

# remove extra points
# Vch1=[V1[i] for i in range(0,len(V1))]
# Vch2=[V2[i] for i in range(0,len(V2))]

# correct for drain delay to prevent artifactual hysteresis
#if Ndelay>2: V1=[V1[i] for i in range(Ndelay,len(V1))]         # delay the timing of the gate to compensate for drain delay


if Nsmooth>4:
	# smooth
	Vch1=np.convolve(V1,np.ones((Nsmooth,))/Nsmooth,mode='valid')
	Vch2=np.convolve(V2,np.ones((Nsmooth,))/Nsmooth,mode='valid')
	timestamps=np.convolve(t,np.ones((Nsmooth,))/Nsmooth,mode='valid')
	# consolidate data points
	arraysize=min(len(Vch1),len(Vch2),len(timestamps))                       # make all arrays the same size
	Vch1=[Vch1[i] for i in range(0,arraysize-Nsmooth,Nsmooth) ]
	Vch2=[Vch2[i] for i in range(0,arraysize-Nsmooth,Nsmooth) ]
	timestamps=[timestamps[i] for i in range(0,arraysize,Nsmooth) if i<arraysize]
else:
	timestamps=[tt for tt in t]
	Vch1=[vv for vv in V1]
	Vch2=[vv for vv in V2]



arraysize=min(len(Vch1),len(Vch2),len(timestamps))
filename="/carbonics/owncloudsync/documents/analysis/test_pulse/smoothpulses_tri.xls"
outf = open(filename, 'w')
outf.write("time(sec)\tvolt2(V)\tvolt1(V)\n")
for i in range(0,arraysize):
	#print(timestamps[i],Vch1[i])
	outf.write('%10.5E\t%10.5E\t%10.5E\n' %(timestamps[i],Vch2[i],Vch1[i]) )
outf.close()




filename="/carbonics/owncloudsync/documents/analysis/test_pulse/parametric_values_tri.xls"
outf = open(filename, 'w')

# now match timepoints and plot the volt1 (representing the drain current) as a function of volt2 (representing the gate voltage
outf.write("Vgs(V)\tId(A)\n")
for i in range(0,arraysize):
	outf.write('%10.5E\t%10.5E\n' %(Vch2[i],Vch1[i]))
outf.close()

