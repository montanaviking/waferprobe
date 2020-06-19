__author__ = 'test'
import visa
import time
from parameter_analyzer import *
from spectrum_analyzer import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print rm.list_resources()

ps=ParameterAnalyzer(rm)
sa = SpectrumAnalyzer(rm)

Vgsbias = -2
Vdsbias = -2
gcomp = 1e-4
dcomp = 1e-3

# transfer curves
Vgs_transstart = 0.5
Vgs_transstop = -2.5
Vgs_transstep = -0.05
ps.fetbiason_topgate(Vgsbias, Vdsbias, gcomp, dcomp)
print "Vds =", ps.Vds_bias
print "Id =", ps.Id_bias
print "Vgs =",ps.Vgs_bias
print "Ig =", ps.Ig_bias

time.sleep(90.)
ps.fetbiasoff()
