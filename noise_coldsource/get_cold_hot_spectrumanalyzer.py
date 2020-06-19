from setup_noise_coldsource import *
import numpy as np
from utilities import dBtolin
############
# measure the noise spectrum with the noise source off (cold) and the noise source on (hot)
# input parameters:
# noisesource is the combination of the HP346B + HP8970B noise meter. The actual noise diode is hte HP346B and the HP8970B is used as the diode power supply
# spectrumanalyzer is the spectrum analyzer used to read the noise
# average is the number of averages of sweeps of the spectrum analyzer for noise measurements
# startfrequencyMHz is the spectrum analyzer lower end of frequencies in MHz
# stopfrequencyMHz is the spectrum analyzer upper end of frequencies in MHz
# resolutionbandwidthsetting, in Hz, is the requested resolution bandwidth setting for the spectrum analyzer, Note that it isn't necessarily the actual resolution bandwidth
# videobandwidthsetting, in Hz, is the requested video bandwidth setting for the spectrum analyzer, Note that it isn't necessarily the actual video bandwidth
# If autoscalereflevel=False then referencelevelguess is the set reference level, in dBm, of the spectrum analyzer. If autoscalereflevel=True, then referencelevelguess is a starting point to autorange the spectrum analyzer
# autoscalereflevel=False, means do not autoscale the spectrum ananlyzer, autoscalereflevel=True, means DO autoscale the spectrum ananlyzer

# return values dictionary
# frequenciesMHz is the frequencies in MHz
# noisecold is the noise power (dBm) with the noise diode off
# noisehot is the noise power (dBm) with the noise diode on
# referencelevel is the actual reference level setting reported by the spectrum analyzer
# resolutionbandwidth is the actual resolution bandwidth, in Hz, reported by the spectrum analyzer
# videobandwidth is the actual video bandwidth, in Hz, reported by the spectrum analyzer
# if measurehot=True, then measure the noise with the noise diode on
# def get_cold_hot_spectrumanalyzer(spectrumanalyzer=None,noisesource=None,average=16,startfrequencyMHz=1000,stopfrequencyMHz=1600,resolutionbandwidthsetting=10E6,videobandwidthsetting=10E3,referencelevelguess=-50.,autoscalereflevel=False,measurehot=True):
# 	referencelevelsetting=referencelevelguess           # used to set value of reference level if not using self._spectrumanalyzer.measure_peak_level_autoscale()
# 	centfreq=round((startfrequencyMHz+stopfrequencyMHz)/2.)*1E6       # center frequency Hz
# 	span=abs(round(stopfrequencyMHz-startfrequencyMHz)*1E6)       # frequency span frequency Hz
#
# 	# cold noise measurement (noise source off)#####################
# 	if noisesource!=None: noisesource.noise_sourceonoff(on=False)     # turn off noise source, make sure noise source is off
# 	else: measurehot=False          # if we did not provide a noise source, then assume this is a cold source measurement
# 	if autoscalereflevel:
# 		referencelevelsetting,measuredfrequency,measuredpower = spectrumanalyzer.measure_peak_level_autoscale(referencelevel=referencelevelguess,frequency=centfreq,frequencyspan=span,averages=1,measurenoise=True)       # perform autoscaling IF requested
# 		if measuredpower+15.>referencelevelsetting: referencelevelsetting=referencelevelsetting+10.
# 	maxfreqcold,maxsigcold,frequenciescold_sa,noisecold_sa=spectrumanalyzer.measure_spectrum(numberofaverages=average,centfreq=centfreq,span=span,videobandwidth=videobandwidthsetting,resolutionbandwidth=resolutionbandwidthsetting,referencelevel=referencelevelsetting,attenuation=0,preamp=True)
# 	frequenciescold_sa=[1E-6*f for f in frequenciescold_sa]# convert frequencies from Hz to MHz
#
# 	actualreferencelevel=spectrumanalyzer.get_referencelevel()  # in Hz
# 	actualresolutionbandwidth=spectrumanalyzer.get_resolutionbandwidth()    # in Hz
# 	actualvideobandwidth=spectrumanalyzer.get_videobandwidth()      # in Hz
#
# 	# hot noise measurement (noise source on)###########################
# 	if measurehot:
# 		noisesource.noise_sourceonoff(on=True)     # turn on noise source)
# 		if autoscalereflevel:
# 			referencelevelsetting,measuredfrequency,measuredpower=spectrumanalyzer.measure_peak_level_autoscale(referencelevel=referencelevelguess,frequency=centfreq,frequencyspan=span,averages=1,measurenoise=True)       # perform autoscaling IF requested
# 			if measuredpower+15.>referencelevelsetting: referencelevelsetting=referencelevelsetting+10.
# 		maxfreqhot,maxsighot,frequencieshot,noisehot_sa=spectrumanalyzer.measure_spectrum(numberofaverages=average,centfreq=centfreq,span=span,videobandwidth=videobandwidthsetting,resolutionbandwidth=resolutionbandwidthsetting,referencelevel=referencelevelsetting,attenuation=0,preamp=True)
# 		return {'frequenciesMHz':frequenciescold_sa,'noisecold':noisecold_sa,'noisehot':noisehot_sa,'referencelevel':actualreferencelevel,'resolutionbandwidth':actualresolutionbandwidth,'videobandwidth':actualvideobandwidth}     # self.frequenciescold_sa is a list of int frequencies in MHz
# 	else:
# 		return {'frequenciesMHz':frequenciescold_sa,'noisecold':noisecold_sa,'referencelevel':actualreferencelevel,'resolutionbandwidth':actualresolutionbandwidth,'videobandwidth':actualvideobandwidth}     # self.frequenciescold_sa is a list of int frequencies in MHz
##########################################################################################################################################################################################################
def get_cold_hot_spectrumanalyzer(spectrumanalyzer=None,noisesource=None,average=16,frequenciesMHz=None,resolutionbandwidthsetting=3E6,videobandwidthsetting=10E3,referencelevelguess=-50.,autoscalereflevel=False,measurehot=True,formatdB=True):
	referencelevelsetting=referencelevelguess           # used to set value of reference level if not using self._spectrumanalyzer.measure_peak_level_autoscale()
	noisecold={}
	noisehot={}
	# cold noise measurement (noise source off)#####################
	if noisesource==None: measurehot=False   # turn off noise source, make sure noise source is off

	for f in frequenciesMHz:
		if noisesource!=None: noisesource.noise_sourceonoff(on=False)     # turn off noise source, make sure noise source is off
		# cold noise measurement (noise source on)###########################
		maxfreqcold,maxsigcold,frequenciescold_sa,noisecold_sa=spectrumanalyzer.measure_spectrum(numberofaverages=average,centfreq=round(1E6*f),span=100E3,videobandwidth=videobandwidthsetting,resolutionbandwidth=resolutionbandwidthsetting,referencelevel=referencelevelsetting,attenuation=0,preamp=True)
		if formatdB: noisecold[str(f)]=np.average(noisecold_sa)
		else: noisecold[str(f)]=dBtolin(np.average(noisecold_sa))
		if measurehot:
			noisesource.noise_sourceonoff(on=True)     # turn on noise source, make sure noise source is on
			# hot noise measurement (noise source on)###########################
			maxfreqhot,maxsighot,frequencieshot,noisehot_sa=spectrumanalyzer.measure_spectrum(numberofaverages=average,centfreq=round(1E6*f),span=100E3,videobandwidth=videobandwidthsetting,resolutionbandwidth=resolutionbandwidthsetting,referencelevel=referencelevelsetting,attenuation=0,preamp=True)
			if formatdB: noisehot[str(f)]=np.average(noisehot_sa)
			else: noisehot[str(f)]=dBtolin(np.average(noisehot_sa))
	if noisesource!=None: noisesource.noise_sourceonoff(on=False)     # turn off noise source, make sure noise source is off

	actualreferencelevel=spectrumanalyzer.get_referencelevel()  # in Hz
	actualresolutionbandwidth=spectrumanalyzer.get_resolutionbandwidth()    # in Hz
	actualvideobandwidth=spectrumanalyzer.get_videobandwidth()      # in Hz

	if measurehot:
		return {'noisecold':noisecold,'noisehot':noisehot,'referencelevel':actualreferencelevel,'resolutionbandwidth':actualresolutionbandwidth,'videobandwidth':actualvideobandwidth}     # self.frequenciescold_sa is a list of int frequencies in MHz
	else:
		return {'noisecold':noisecold,'referencelevel':actualreferencelevel,'resolutionbandwidth':actualresolutionbandwidth,'videobandwidth':actualvideobandwidth}     # self.frequenciescold_sa is a list of int frequencies in MHz
##########################################################################################################################################################################################################