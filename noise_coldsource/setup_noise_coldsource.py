################3
# ENR table for HP346B, SN 2330A03414 calibrated Dec 4, 2019 by Tektronix
from scipy.interpolate import CubicSpline

import visa
from amrel_power_supply import *
from spectrum_analyzer import *
from pulsegenerator import *
from pna import *
from oscilloscope import *
from pulsed_measurements import ramped_sweep_gate
from swept_Spar import *
from loadpull_system_calibration import *
from HP8970B_noisemeter import *
from focustuner_pos import *
from writefile_measured import X_writefile_noiseparameters_v2, X_writefile_noisefigure_v2, X_writefile_systemnoisefigure_vs_time,X_writefile_systemnoisefigure_vs_frequency
from utilities import floatequal
from read_write_spar_noise import read_noise_parameters, read_spar, spar_flip_ports
from calculate_noise_parameters_focus import calculate_nffromnp, calculate_gavail,calculate_NP_DUT_direct_timedomain,calculate_NP_noisemeter
from read_write_spar_noise_coldsource import *

T0=290      # reference noise temperature K
from get_cold_hot_spectrumanalyzer import *

# rm=visa.ResourceManager()
# noisesource=NoiseMeter(rm=rm,ENR=15,preset=True,turnonnoisesourceonly=True)               # ENR is bogus because the noise meter is being used only to drive the noise source
# spectrumanalyzer=SpectrumAnalyzer(rm=rm)



# ENR table in MHz
#
ENRtablefreqMHz = {"10":15.63,"100":15.60,"1000":15.43,"2000":15.34,"3000":15.13,"4000":15.11,"5000":15.15,"6000":15.10,"7000":15.44,"8000":15.43,"9000":15.55,"10000":15.40,"11000":15.42,"12000":15.38,"13000":15.22,"14000":15.07,"15000":15.10,"16000":15.24,"17000":15.39,"18000":15.47}
ENRtablefreqMHz_int=sorted([int(f) for f in ENRtablefreqMHz.keys()])          # convert ENRtable frequencies to integers and sort from lowest to highest frequency
ENRtable_values = [ENRtablefreqMHz[str(f)] for f in ENRtablefreqMHz_int]               # ENR table sorted by frequency and converted to values with frequency index
ENRtable = CubicSpline(ENRtablefreqMHz_int,ENRtable_values)                  # get cubic spline of ENR table yields ENR of noise diode in dB