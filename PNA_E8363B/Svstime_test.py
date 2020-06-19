# measures output drain impedance vs time

import visa
import PyQt5
import numpy as np
from oscilloscope import *
from amrel_power_supply import *
from pulsegenerator import *
from pulsed_measurements import ramped_sweep_gate
from loadpull_system_calibration import *               # gets the calibration parameter to convert the differential voltage to Id
rm = visa.ResourceManager()
from pna import *
pna=Pna(rm=rm)
timestampspna,s11_raw,s21_raw,s12_raw,s22_raw=pna.getS_2port_time(navg=1,sweeptime='MIN')               # get S22 vs time for swept drain voltage
a=1


