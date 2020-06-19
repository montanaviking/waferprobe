__author__ = 'PMarsh Carbonics'
from spectrum_analyzer import *
from rf_synthesizer import *
from writefile_measured import X_writefile_TOI
from utilities import *
import time

	# perform 3rd order intercept point measurement at one frequency over a two-tone input power sweep
	# Input parameters
	# sa is the spectrum analyzer handle
	# rflow is the synthesizer handle of the synthesizer tuned to the lower of the two-tone frequencies
	# saatten is the spectrum analyzer's attanuation setting - must be 0dB, 5dB, 10dB,...
	# rfhigh is synthesizer handle of the synthesizer tuned to the lower of the two-tone frequencies
	# plevelstart is the lowest power level setting of the synthesizers' output levels
	# plevelmax is the maximum allowed power level setting of the sythesizers' outpout levels
	# pleveldel is the stepsize of the two-tone levels to determine the TOI
	# centfreq is the frequency point midway between the two tones
	# self._deltafreq is the frequency separation between the two tones

	# self._sacalfactor is dB power meter - dB spectrum analyzer display
	# self._sourcecalfactor=PDUTin-PsynAset where PDUTin is the power at the DUT input, as read by the power meter and corrected for probe loss when synthesizer A is set to PsynAset and synthesizer B is off. self._sourcecalfactor is expected to be set to a negative dB quantity
	# self._tuner_loss is the loss from the output of the DUT to the input of the spectrum analyzer (reference input of the spectrum analyzer) default = 0

class IP3(object):
	def __init__(self,rm=None,spectrum_analyser_input_attenuation=10.,number_of_averages=8,powerlevel_start=None,powerlevel_stop=None,powerlevel_step=None,center_frequency=None,frequency_spread=None,spectrum_analyzer_cal_factor=None,source_calibration_factor=None,output_loss=0.,system_TOI=None):
		try: self.__sa=SpectrumAnalyzer(rm)
		except: raise ValueError("ERROR! No spectrum analyzer found!")
		try: self.__rflow=Synthesizer(rm=rm,syn="A")            # synthesizer A should be the self.__rflow (lower frequency tone) because it has the high-accuracy attenuators
		except: raise ValueError("ERROR! No lower frequency RF source found for two-tone!")
		try: self.__rfhigh=Synthesizer(rm=rm,syn="B")
		except: raise ValueError("ERROR! No upper frequency RF source found for two-tone!")
		#self.__sa=sa
		#self.__rfhigh=rfhigh                # handle to control the upper-frequency RF source
		#self.__rflow=rflow                  # handle to control the lower-frequency RF source
		self._epsilon = 1.E-20                  # used to compare floating point numbers to account for rounding errors
		self._saatten=spectrum_analyser_input_attenuation
		self._navg=number_of_averages
		self._plevelstart=powerlevel_start
		self._plevelstop=powerlevel_stop
		self._pleveldel=powerlevel_step
		self._centfreq=center_frequency
		self._deltafreq=frequency_spread
		self._sacalfactor=spectrum_analyzer_cal_factor
		self._sourcecalfactor=source_calibration_factor
		self._sysTOI=system_TOI                     # system third order intercept point
		self._output_loss=output_loss				# loss in dB from the DUT to the spectrum analyzer reference input (as characterized by a power meter in the system setup) Note that this is a LOSS, not a gain so a positive number indicates a LOSS in dB
		self._reflevelgaincorrection=0.             # add this to the reference level if we get input saturation, to correct for gain if necessary
		self._delpowm=0.                            # difference in dB between the two tone inputs

	#########################################################################################################################
	# fractlinfit is the fraction of the input two-tone power range to use to linear fit the distortion product power vs input power
	# in order to find the third order intercept point
	def measureTOI(self,fractlinfitlower=0.,fractlinearfitupper=0.,expected_gain=0.):
		maxrefleveladjusttries=10                                   # maximum number of times allowed to adjust reference level due to errors caused by signal saturation
		plevelstart = self._plevelstart - self._sourcecalfactor  # plevelstart is the lowest power direct setting used on the synthesizers it is the requested lowest power corrected by the losses from synthesizer to the DUT input.
		plevelmax= self._plevelstop - self._sourcecalfactor				# plevelmax is the highest power direct setting used on the synthesizers it is the requested highest power corrected by the losses from synthesizer to the DUT input.

		flow = self._centfreq-self._deltafreq/2.           # lower fundamental frequency of the two-tone
		fhigh = self._centfreq+self._deltafreq/2.          # upper fundamental frequency of the two-tone
		spanfund = 100.E3                      # measurement span about the fundamentals
		spand=1000.                             # measurement span about the distortion products
		resbwfund = 1000.                       # resolution bandwidth used to measure fundamental two-tone components
		# turn off synthesizers to measure noise floor
		self.__rflow.off()
		self.__rfhigh.off()
		#return()    #debug
		self.__sa.set_attenuation(self._saatten)                      # set attenuation level of spectrum analyzer
		self.__sa.set_numberaverages(self._navg)                   # set number of averages
		# first measure noise floor for lower distortion product - expected to be the same as for upper frequency product as well
		# decrease resolution bandwidth by one increment for distortion product measurements

		f,TO_power=self.__sa.measure_spectrum(centfreq=flow - self._deltafreq, span=spand, returnspectrum=False)
		self.__sa.set_autoresolutionbandwidth('y')
		self.__sa.set_autovideobandwidth('y')
		#self._resbwdistortion=self.__sa.decrease_resolutionbandwidth()
		f,TO_power=self.__sa.measure_spectrum(centfreq=flow - self._deltafreq, span=spand,returnspectrum=False)			# get raw measured noise floor

		self.noisefloor=np.average(TO_power)                  # get noise floor as measured directly at the spectrum analyzer without correction
		noisefloorlin = pow(10.,self.noisefloor/10.)     # noisefloor in mW as measured directly at spectrum analyzer without correction for system losses

		# set two-tone synthesizer frequencies
		self.__rflow.set_frequency(self._centfreq - self._deltafreq / 2.)  # set lower frequency of two-tone
		self.__rfhigh.set_frequency(self._centfreq + self._deltafreq / 2.) # set upper frequency of two-tone
		self.__rflow.set_power(plevelmax)
		self.__rfhigh.set_power(plevelmax)
		#bad here
		while self.__rflow.set_power(plevelmax)=='unleveled' or self.__rfhigh.set_power(plevelmax)=='unleveled':
			# power level setting is beyond at least one of the synthesizer's capability so reduce the maximum requested power
			#plevelmax=plevelmax-self._pleveldel
			print ("Warning: maximum requested synthesizer power beyond capability so reducing maximum power set at synthesizers to", plevelmax)
			plevelmax=plevelmax-1.1*self._pleveldel
		print ("plevelmax = ",plevelmax)
		print ("sourcecalfactor", self._sourcecalfactor)
		print("plevelmax setting actual", self._plevelstop)

		plevel = plevelmax
		self.TOIptt = []                                    # measured two-tone fundamental DUT output power level array
		self.TOIpdl = []                                    # power level array of the lower third order distortion product
		self.TOIpdh = []                                    # power level array of the upper third order distortion product
		self.pinDUT=[]										# average fundamental input power applied to the DUT
		self.sys = []                                   	# third order product due to system IP3
		#delpowm=0.
		##### beginning of power loop
		while plevel >= plevelstart:                          # start third order intercept test at highest power plevel is the raw power setting of the synthesizer which will give the desired power at the DUT input
			print("plevel setting in loop ",plevel)
			#print "set res 1"
			reflevel=10.*int((plevel+expected_gain+self._reflevelgaincorrection + self._sourcecalfactor-self._sacalfactor)/10.)     # set spectrum analyzer reference level to nearest increment of 10dB
			self.__sa.set_referencelevel(reflevel)                 # set reference level of spectrum analyzer
			self.__sa.set_resolutionbandwidth(resolutionbandwidth=resbwfund)       # set resolution bandwidth to lock to span for fundamental measurements
			#print "set res 2"
			pwrhigh = plevel-self._delpowm                # attempt to correct for errors on two tone signal levels to attempt to make both of the two tone have the same levels
			self.__rfhigh.set_power(pwrhigh)
			if self.__rfhigh.set_power(pwrhigh)!='ok': raise ValueError('ERROR high 1 power set too high on upper-frequency synthesizer')
			self.__rflow.set_power(plevel)
			if self.__rflow.set_power(plevel)!='ok': raise ValueError('ERROR low power set too high on lower-frequency synthesizer')

			#loop to find reference level which doesn't saturate spectrum analyzer input######################
			reftries=0
			reflevelOK=False
			while reftries<maxrefleveladjusttries and not reflevelOK:      #loop to find reference level which doesn't saturate spectrum analyzer input
				reflevelOK=True
				try: flowm,plowm=self.__sa.measure_spectrum(centfreq=flow,span=spanfund,returnspectrum=False)     #measure lower fundamental of two tone input
				except:
					reflevelOK=False
					self._reflevelgaincorrection+=10.                       # increment reference level by 10dB to try to get spectrum analyzer out of saturation
					reflevel+=10.
					self.__sa.set_referencelevel(reflevel)
					reftries+=1
				try: fhighm,phighm=self.__sa.measure_spectrum(centfreq=fhigh,span=spanfund,returnspectrum=False)  #measure upper fundamental of two tone input
				except:
					reflevelOK=False
					self._reflevelgaincorrection+=10.                       # increment reference level by 10dB to try to get spectrum analyzer out of saturation
					reflevel+=10.
					self.__sa.set_referencelevel(reflevel)
					reftries+=1
				#print("from line 136 IP3.py reflevel=",reflevel,reftries)        #debug
			if reftries>0:
				reflevel+=10
				self._reflevelgaincorrection+=10.
				self.__sa.set_referencelevel(reflevel)
			##########################################
			if reftries>=maxrefleveladjusttries: raise ValueError("ERROR! could not get spectrum analyzer out of input saturation")
			# iterate synthesizer power levels to produce the same level in both of the two-tones as measured by the spectrum analyzer
			while True:
				#print "set res 3" #debug
				flowm,plowm=self.__sa.measure_spectrum(centfreq=flow,span=spanfund,returnspectrum=False)     #measure lower fundamental of two tone input in dBm
				fhighm,phighm=self.__sa.measure_spectrum(centfreq=fhigh,span=spanfund,returnspectrum=False)  #measure upper fundamental of two tone input in dBm
				#print "set res 5" #debug
				self._delpowm = phighm-plowm
				if abs(self._delpowm)<0.1: break                       # iterate power adjustment until power difference between fundamentals is acceptably low
				pwrhigh=self.__rfhigh.get_power()-self._delpowm               # set power to even out fundamental power levels
				self.__rfhigh.set_power(pwrhigh)
				if self.__rfhigh.set_power(pwrhigh)!='ok': raise ValueError('ERROR high 2 power set too high on upper-frequency synthesizer')

			pfundaverage = dBaverage(self._output_loss+self._sacalfactor + plowm, self._output_loss+self._sacalfactor + phighm) 		# average of the two-tone lower and upper frequency powers as measured at the spectrum analyzer input with the spectrum analyzer loss calibrated out
			self.pinDUT.append(plevel+self._sourcecalfactor)		# power into DUT with synthesizer to DUT losses calibrated out (should be actual power to DUT input in dBm)
			self.TOIptt.append(pfundaverage)                                                        #measured fundamental power level as calibrated to the DUT output
			#self.__sa.set_resolutionbandwidth(self._resbwdistortion)                                 # set the resolution bandwidth to measure distortion product

			reflevel=80.+10.*int(self.noisefloor / 10.)     # set spectrum analyzer reference level to nearest increment of 10dB to measure distortion products. Here the noise floor is raw data as measured at the spectrum analyzer without correction for system losses
			self.__sa.set_referencelevel(reflevel)                 # set reference level of spectrum analyzer to show distortion products

			if abs(plevel-plevelmax)<self._epsilon:                        # is this the maximum power level? If so, find the actual third order (TO) frequencies
				self.__sa.set_autoresolutionbandwidth('y')                  # set automatic resolution bandwidth
				self.__sa.set_autovideobandwidth('y')                       # set automatic video bandwidth
				TO_freq_lower,TO_power=self.__sa.measure_spectrum(centfreq=flowm - self._deltafreq, span=10.*spand,returnspectrum=False)       # measure upper frequency 3rd order product power level and frequency
				TO_freq_lower,TO_power=self.__sa.measure_spectrum(centfreq=TO_freq_lower,span=spand,returnspectrum=False)      # reduce frequency sweep span and re-measure lower TO frequency
				TO_freq_upper,TO_power=self.__sa.measure_spectrum(centfreq=TO_freq_upper,span=spand,returnspectrum=False)       # reduce frequency sweep span and re-measure upper TO frequency
				self._resbwdistortion=self.__sa.decrease_resolutionbandwidth()                             # set resolution bandwidth one notch lower than that automatically determined

			self.__sa.set_autoresolutionbandwidth('y')                  # set automatic resolution bandwidth
			self.__sa.set_autovideobandwidth('y')                       # set automatic video bandwidth
			#self.__sa.set_resolutionbandwidth(self._resbwdistortion)                                 # set the resolution bandwidth to measure distortion product
			TO_freq_lower_static,TO_power_uncorrected=self.__sa.measure_spectrum(centfreq=TO_freq_lower,span=spand,returnspectrum=False)       # measure lower frequency 3rd order product power level and frequency
			TO_power = self._output_loss+self._sacalfactor + 10. * np.log10(abs(pow(10., TO_power_uncorrected / 10.) - noisefloorlin))      # calibrate to power meter readings and subtract out noise floor
			print ("lower third order product at DUT output =",TO_power+self._output_loss) #debug
			self.TOIpdl.append(TO_power)												# lower third order product as corrected to the DUT output
			#self.__sa.set_resolutionbandwidth(self._resbwdistortion)                                 # set the resolution bandwidth to measure distortion product
			TO_freq_upper_static,TO_power_uncorrected=self.__sa.measure_spectrum(centfreq=TO_freq_upper,span=spand,returnspectrum=False)       # measure upper frequency 3rd order product power level and frequency
			TO_power = self._output_loss+self._sacalfactor + 10. * np.log10(abs(pow(10., TO_power_uncorrected / 10.) - noisefloorlin))      # calibrate to power meter readings and subtract out noise floor
			print ("upper third order product at DUT output =",TO_power+self._output_loss) 	# debug
			self.TOIpdh.append(TO_power)												# upper third order product as corrected to the DUT output
			self.sys.append(3. * self.TOIptt[-1] - 2. * self._sysTOI)     # find third order product due to TOI of system AT THE DUT OUTPUT Note that self._sysTOI was calibrated to the DUT output when characterizing the system with a through in place of the DUT and self.TOIptt is the fundamental power at the DUT output
			print("IP3.py line 161 sys",self.sys[-1],self._sysTOI,self.TOIptt[-1])
			plevel = plevel-self._pleveldel                     # decrement power level of the fundamental two-tones for next measurement
			self.__rflow.vclear()
			self.__rfhigh.vclear()
		########## end of power loop
		self.__rflow.off()
		self.__rfhigh.off()

		# find both 3rd order intercept points, corrected power levels at the spectrum analyzer input, and corrected linear fits
		# first get only TOIs
		self.TOIml,self.TOIbl,rl = linfitendexclude(x=self.pinDUT,y=self.TOIpdl,lowerfraction=fractlinfitlower,upperfraction=fractlinearfitupper )  # distortion product linear fit for lower distortion product to find TOI
		self.TOImh,self.TOIbh,rh = linfitendexclude(x=self.pinDUT,y=self.TOIpdh,lowerfraction=fractlinfitlower,upperfraction=fractlinearfitupper )  # distortion product linear fit for upper distortion product to find TOI
		self.poutm,self.DUTgain,rf=linfitendexclude(x=self.pinDUT,y=self.TOIptt,lowerfraction=fractlinfitlower,upperfraction=fractlinearfitupper )  # this is the fundamental output power vs input power and is used to calculate the DUT gain in dB from the slope. If the DUT has a loss, this is a negative number
		# find TOIs
		self.TOIl=  self.DUTgain+((self.TOIbl-self.DUTgain) / (self.poutm - self.TOIml)) # output third order intercept point as determined from lower frequency 3rd order product
		self.TOIh= self.DUTgain+((self.TOIbh-self.DUTgain) / (self.poutm - self.TOImh)) # output third order intercept point as determined from upper frequency 3rd order product

		self.fitquality = min([rl, rh])    # find worst-case fitting "goodness" parameter
		# self.pinDUT and self.TOI.ptt are respectively the fundamental (each of the two-tones') powers (dBm) at the input of the DUT, as calibrated by the power meter during the system setup, and the output of the DUT
		# self.TOIl, self.TOIh are the lower sideband and upper sideband respective third intercept points, referenced to the DUT output
		# TOIpdl, TOIpdh the DUT output power arrays of the lower and upper respective third order sidebands
		# self.noisefloor is the system noise floor referenced to the DUT output and fitquality, the worst-case r-value (for both lower and upper tones) of the linear fits of the distortion product powers. ptt is the power of both fundamental tones (powers should be equal)
		# self.DUTgain is the DUT gain calculated from the slope of self.TOIptt
		# self.TOIml, self.TOIbl are respectively the slope and y intercept (dBm graph) of the least-squares linear fit of self.TOIptt vs self.TOIl measured arrays.
		# self.TOImh, self.TOIbh are respectively the slope and y intercept (dBm graph) of the least-squares linear fit of self.TOIptt vs self.TOIh measured arrays.
		# self.pinb is the y intercept point of the DUT fundamental output power (referenced to the DUT output) vs the fundamental input power (referenced to the input of the DUT. The corresponding slope is the self.DUTgain

		return self.TOIl, self.TOIh, self.DUTgain, self.pinDUT,self.TOIptt, self.TOIpdl, self.TOIpdh, self.noisefloor, self.TOIml, self.TOImh, self.poutm, self.TOIbl, self.TOIbh,self.fitquality
	####################################################################################################################
	# write TOI data to file
	writefile_TOI=X_writefile_TOI
