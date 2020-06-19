__author__ = 'PMarsh Carbonics'
import visa
from spectrum_analyzer import *
from loadpull_system_calibration import *
from rf_synthesizer import *
from harmonic_measurement import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
sa=SpectrumAnalyzer(rm=rm)
rf=Synthesizer(rm=rm,maximumpowersetting=14)
pwrstart = -5.
pwrstop = -15.
delpwr=5.
sysTOI=85.

pathname = "C:/Users/test/harmonic"
dist=Harmonic_distortion(rm=rm, sa=sa, rf=rf, spectrum_analyser_input_attenuation=10, fundamental_frequency=170.*1E6, source_calibration_factor_fundamental=sourcecalfactorharmonic, SA_calibration_factor_fundamental=outputcalfactorharmonic_1st,
                         SA_calibration_factor_2nd_harmonic=outputcalfactorharmonic_2nd, SA_calibration_factor_3rd_harmonic=outputcalfactorharmonic_3rd)
dist.get_harmonic_fundamental(powerlevel=-10.,maxdeltapower=0.2,gatecomp=1E-5,draincomp=0.1)
dist.writefile_harmonicdistortion(pathname=pathname,devicename="systemdistortion",wafername="dist_Nov12_2018",xloc=0,yloc=0)


