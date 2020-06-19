__author__ = 'PMarsh Carbonics'
import visa
import time
from parameter_analyzer import *
from spectrum_analyzer import *
from rf_sythesizer import *
from IVplot import plotspectrum

rm = visa.ResourceManager()                                                         # setup GPIB communications
print rm.list_resources()

#ps=ParameterAnalyzer(rm)
sa = SpectrumAnalyzer(rm)
rfA = Synthesizer(rm,"A")
rfB= Synthesizer(rm,"B")

# Vgsbias = -2
# Vdsbias = -2
# gcomp = 1e-4
# dcomp = 1e-3

# transfer curves
# Vgs_transstart = 0.5
# Vgs_transstop = -2.5
# Vgs_transstep = -0.05
#ps.fetbiason(Vgsbias,Vdsbias,gcomp,dcomp)
# print "Vds =", ps.Vds_bias
# print "Id =", ps.Id_bias
# print "Vgs =",ps.Vgs_bias
# print "Ig =", ps.Ig_bias

fcent = 1E9
fdelta = 100E6
fspanf = 100E3                 # measurement span for each frequency component of the fundamentals
fspand = 20E3                 # measurement span for each frequency component of the fundamentals
ffa = fcent-fdelta/2
ffb= fcent+fdelta/2
fda = ffa-fdelta
fdb = ffb+fdelta
atten = 20.
pwr = 14.
print "ffa,ffb,fda,fdb = ", ffa,ffb,fda,fdb
sa.set_referencelevel(0.)
rfA.set_frequency(ffa)
rfB.set_frequency(ffb)

rfA.set_power(pwr)
rfB.set_power(pwr)
sa.set_numberaverages(10)
rfA.off()
rfB.off()
# find noise floors
sa.set_referencelevel(-50.)
sa.set_attenuation(atten)

sa.set_resolutionbandwidth(3.,'Hz')
nfa,m,freq,spectrum=sa.measure_noisefloor(ffa,fspand,'spectrum')
# #plotspectrum(freq,spectrum,'noisefloor')
# nfb,m,freq,spectrum=sa.measure_noisefloor(ffb,fspand,'spectrum')
# nfda,m,freq,spectrum=sa.measure_noisefloor(fda,fspand,'spectrum')
# nfdb,m,freq,spectrum=sa.measure_noisefloor(fdb,fspand,'spectrum')

sa.set_referencelevel(0.)
sa.set_attenuation(atten)
rfA.on()
rfB.on()
# adjust fundamental powers to be the same
sa.set_resolutionbandwidth(1000.,'Hz')
while True:
	ffam,sfam,freq,spectrum=sa.measure_spectrum(ffa,fspand,'spectrum')
	#plotspectrum(freq,spectrum,'fundamental a')
	ffbm,sfbm,freq,spectrum=sa.measure_spectrum(ffb,fspand,'spectrum')
	#plotspectrum(freq,spectrum,'fundamental b')
	deltap = sfam-sfbm
	print "delta power =",deltap
	if abs(deltap)<0.1: break
	else:
		rfA.set_power(rfA.get_power()-deltap)

sa.set_referencelevel(-40.)
sa.set_attenuation(atten)
sa.set_resolutionbandwidth(3.,'Hz')
fda = ffam-fdelta
fdam,sdam,freq,spectrum=sa.measure_spectrum(fda,fspand,'spectrum')
#plotspectrum(freq,spectrum,'distortion a')
fdb = ffbm+fdelta
fdbm,sdbm,freq,spectrum=sa.measure_spectrum(fdb,fspand,'spectrum')
#plotspectrum(freq,spectrum,'distortion b')

print "lower fundamental frequency,level,nf ", ffam,sfam,nfa
print "upper fundamental frequency,level,nf ", ffbm,sfbm#,nfb
print "lower distortion frequency,level,nf ", fdam,sdam#,nfda
print "upper distortion frequency,level,nf ", fdbm,sdbm#,nfdb
print "attenuation", sa.get_attenuation()