# test of untuned Vgs swept TOI measurement

from IP3_Vgssweep import *
from loadpull_system_calibration import *


gcomp=0.001
dcomp=0.1
Vds=-1
Vgs=0.
rm=visa.ResourceManager()
#ps=ParameterAnalyzer(rm)

#Idval,Igval,Idcompstatval,Igcompstatval=ps.fetbiason_topgate(Vgs=Vgs, Vds=Vds, gatecomp=gcomp, draincomp=dcomp)
IP3=IP3_Vgssweep(rm=rm, powerlevel_minimum=-14, powerlevel_maximum=-14, powerlevel_step=0, center_frequency=1.5E9, frequency_spread=4E6, Vgsmin=-2.5, Vgsmax=0, Vgsperiod=0.1,tuner='untuned')
IP3.measureTOI_gain_untuned(Vds=Vds)