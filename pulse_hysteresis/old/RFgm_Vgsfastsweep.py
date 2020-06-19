# measure RF Gm over a Vgs waveform
# measures RF Gm vs Vgs for a fast-swept Vgs waveform (triangle wave at ~1KHz

__author__ = 'PMarsh Carbonics'
# pulse and acqusition of pulse data for hysteresis testing
# Phil Marsh Carbonics Inc
import visa
from oscilloscope import OscilloscopeDS1052E
from pulse_utilities import *
from pulsegenerator import *
from spectrum_analyzer import *
from scipy import stats
import numpy as np
import time


rm=visa.ResourceManager()
print(rm.list_resources())

pulse=PulseGeneratorDG1022(rm)

def RFgm_Vgsfastsweep(Vgsmin=None,Vgsmax=None,sweepperiod=None,attenuation=10,numberofaverages=64,referencelevelguess=-70,soaktime=10.):
	pulse.pulsetrainoff()
	pulse.ramp(period=sweepperiod,Vmin=Vgsmin,Vmax=Vgsmax,pulsegeneratoroutputZ='50')
	pulse.pulsetrainon()
	time.sleep(soaktime)



