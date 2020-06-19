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

pulse=PulseGeneratorDG1022(rm)

pulse.pulsetrainoff()
#pulse.ramppulses(period=1E-3, quiescentvoltage=3., pulsedvoltage=-3, pulsewidth=4E-6, dutycyclefraction=0.2, pulsegeneratoroutputZ="50")
pulse.ramp(period=.5E-3,Vmin=-2,Vmax=-1,pulsegeneratoroutputZ='50')
pulse.pulsetrainon()

time.sleep(120)
