#
from spectrum_analyzer import *
import visa
rm=visa.ResourceManager()
sa=SpectrumAnalyzer(rm)
frequency=1498E6
sweeptime=100E-3
resolutionbandwidth=200./sweeptime
videobandwidth=resolutionbandwidth/2
referencelevelsetting,frequency,measuredpower=sa.measure_peak_level_autoscale(referencelevel=-40.,frequency=frequency,frequencyspan=10E3,resolutionbandwidth=100,averages=2)
satimestamps_raw,pfundlower_read,frequency=sa.measure_amplitude_waveform(frequency=frequency,sweeptime=sweeptime,resolutionbandwidth=resolutionbandwidth,
		                        videobandwidth=videobandwidth,attenuation=10.,referencelevelguess=referencelevelsetting,numberofaverages=16)
a=1