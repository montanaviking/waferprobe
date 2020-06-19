# measures 1dB compression point at a single tone using the spectrum analyzer to measure power
# must use synthesizer A
__author__ = 'PMarsh Carbonics'
from spectrum_analyzer import *
from parameter_analyzer import *
from rf_synthesizer import *
from writefile_measured import X_writefile_Pcompression
from utilities import *
import collections as col
from operator import itemgetter, attrgetter
import time
# Input parameters
	# sa is the spectrum analyzer handle
	# rfA is the synthesizer handle of the synthesizer A used in these tests
	# self._saatten is the spectrum analyzer's attanuation setting - must be 0dB, 5dB, 10dB,...
	# self._powergain_min is the lowest power setting at the DUT input, to measure the gain
	# self._powergain_max is the lowest power setting at the DUT input, to measure the gain
	# self._powergain_step is the stepsize of the power at the DUT input, to determine gain
	# self._comp_step is the stepsize of the power sweep about the compression point to give a better-resolved compression characteristics curve (swept from self._powergain_max to self._maxpower in steps of self._comp_step)
	# self._maxpower is the maximum power at the DUT input, used to iterate to determine 1dB compression point
	# self._frequency is the frequency setting of the synthesizer
	# fractlinfitlower is the lower power point in terms of fraction of self._powergain_max-self._powergain_min that we fit the line to find the linear Pout vs Pin line. This line will be used to find the 1dB compression point
	# fractlinfitupper is the upper power point in terms of fraction of self._powergain_max-self._powergain_min that we fit the line to find the linear Pout vs Pin line. This line will be used to find the 1dB compression point
	# self._sacalfactor = PDUTout-Psaread where PDUTout the power, at the DUT output, read by the power meter and then corrected for the probe loss and Psain is the power read on the spectrum analyzer display.
	# self._sourcecalfactor=PDUTin-PsynAset where PDUTin is the power at the DUT input, as read by the power meter and corrected for probe loss when synthesizer A is set to PsynAset and synthesizer B is off. self._sourcecalfactor is expected to be set to a negative dB quantity

class PowerCompression(object):
	def __init__(self,synthesizer=None,spectrumanalyzer=None,parameteranalyzer=None,spectrum_analyser_input_attenuation=20.,number_of_averages=8,powergain_min=None,powergain_max=None,maxpower=None,comp_step=None,powergain_step=None,frequency=None,spectrum_analyzer_cal_factor=None,source_calibration_factor=None,Vgs=0.,Vds=0.,Igcomp=0.,Idcomp=0.,gain=0.):
		if spectrum_analyzer_cal_factor==None or source_calibration_factor==None: raise ValueError("ERROR: Either spectrum_analyzer_cal_factor or source_calibration_factor are missing")
		if spectrumanalyzer==None: raise ValueError("ERROR! Must specify a valid spectrumanalyzer object")
		if synthesizer==None: raise ValueError("ERROR! Must specify a valid synthesizer object")
		self._rfA=synthesizer
		self._sa=spectrumanalyzer
		self._ps=parameteranalyzer			# parameter analyzer for the power supply
		self._Vds=Vds
		self._Vgs=Vgs
		self._Igcomp=Igcomp
		self._Idcomp=Idcomp
		self.settlingtime=0.1
		self._comp_step=comp_step
		if gain!=None: self._gain=gain
		else: self._gain=0.
		self._reflevelgaincorrection=gain                   # initially correct the reference level setting for the expected gain of the DUT


		if parameteranalyzer!=None and Vgs!=None and Vds!=None and Vds!=0.:			# then assume that there is a power supply to be used
			if Igcomp==0.:	raise ValueError("ERROR! Need to specify gate compliance")
			if Idcomp==0.:	raise ValueError("ERROR! Need to specify drain compliance")
			self._ps.fetbiasoff()

		self._rfA.off()							# turn off synthesizer

		self._epsilon = 1.E-20                  # used to compare floating point numbers to account for rounding errors
		self._saspan = 100.E3					# spectrum analyzer frequency span in Hz

		self._saatten=spectrum_analyser_input_attenuation
		self._navg=number_of_averages
		self._powergain_min=powergain_min
		self._powergain_max=powergain_max
		self._powergain_step=powergain_step
		self._maxpower=maxpower
		self._frequency=frequency				# operation frequency in Hz
		self._sacalfactor=spectrum_analyzer_cal_factor
		self._sourcecalfactor=source_calibration_factor

	def measurePcomp(self,fractlinfitlower=0.,fractlinfitupper=1.,compressiontarget=1.,maxcompressionlevelerror=0.1):
		maxiterations=20						# maximum allowed number of power iterations/point
		# compressiontarget is the target level of gain compression, maxcompressionlevelerror is the maximum error allowed between the compressiontarget and the actual power compression level
		if maxcompressionlevelerror<0.02: raise ValueError("maxcompressionlevelerror set too low")

		self._rfA.off()							# turn off synthesizer
		self._rfA.set_frequency(self._frequency)									# set frequency of synthesizer
		self._sa.set_attenuation(self._saatten)                     				# set input attenuation level of spectrum analyzer
		self._sa.set_numberaverages(self._navg)                   					# set number of averages
		self._sa.set_autoresolutionbandwidth('y')
		self._sa.set_autovideobandwidth('y')
		self._toohighlevel=False														# warning flag for synthesizer level set too high and causing too much gain compression for an accurate gain

		powergainset_min = self._powergain_min - self._sourcecalfactor  			# powergainset_min is the lowest power direct setting used on the synthesizer it is the requested lowest power corrected by the losses from synthesizer to the DUT input. This is reference to the DUT input
		powergainset_max= self._powergain_max - self._sourcecalfactor				# powergainset_max is the highest power direct setting used on the synthesizer it is the requested highest power corrected by the losses from synthesizer to the DUT input. This is reference to the DUT input
		maxpowerset=self._maxpower-self._sourcecalfactor							# maximum power setting to calculate compression levels

		# make sure that the synthesizer maximum power level is leveled and OK
		#plevelmax=max(powergainset_max,self._maxpower)
		while self._rfA.set_power(powergainset_max)=='unleveled': # power level setting is beyond the synthesizer's capability so reduce the maximum requested power
			powergainset_max=powergainset_max-1.1*self._powergain_step
			print ("Warning: powergainset_max: power beyond capability so reducing maximum power set at synthesizers to ", powergainset_max)
		while self._rfA.set_power(maxpowerset)=='unleveled': # power level setting is beyond the synthesizer's capability so reduce the maximum requested power
			maxpowerset=maxpowerset-1.1*self._powergain_step
			print ("Warning: maxpowerset: power beyond capability so reducing maximum power set at synthesizers to ", maxpowerset)
			print ("Warning: maxpowerset: power beyond capability so reducing maximum power set at DUT input to ", maxpowerset+self._sourcecalfactor)

		print ("sourcecalfactor", self._sourcecalfactor)

		if maxpowerset<=powergainset_max+self._powergain_step: raise ValueError("ERROR: maximum power for linear measurements is too high or maximum power for compression is too low")

		if int((fractlinfitupper-fractlinfitlower)*(powergainset_max-powergainset_min)/self._powergain_step)<2:	raise ValueError("ERROR: Check power level step size and fractions to fit line")
		# find DUT gain
		# first deternmine if the minimum power setting we'll use during this measurement is above the noise floor at the spectrum analyzer
		self._rfA.off()
		self._sa.set_referencelevel(-50.)
		noisefloor,maxsig=self._sa.measure_noisefloor(self._frequency, self._saspan, 'nospectrum')			# get noise floor with synthesizer turned off
		print("from compression.py line 77 raw noise floor is: ",noisefloor)
		reflevel=10.*int((self._reflevelgaincorrection+powergainset_min + self._sourcecalfactor-self._sacalfactor) / 10.)                # set spectrum analyzer reference level to nearest increment of 10dB
		self._sa.set_referencelevel(reflevel)                 # set reference level of spectrum analyzer
		self._rfA.set_power(powergainset_min)																# turn on synthesizer to minimum power used in this test
		#f,prf=self._sa.measure_spectrum(self._frequency, self._saspan, 'nospectrum')						# get raw signal power level reading for minimum synthesizer power setting
		reflevel,f,prf=self.autoadjust_reference_level(referencelevel=reflevel,frequency=self._frequency,frequencyspan=self._saspan)
		if prf<noisefloor+6.: raise ValueError("ERROR: powergainset_min too low - below noise floor")

		pDUTin=[]
		pDUTout=[]
		gatestatusDUT=[]
		drainstatusDUT=[]
		IgDUT=[]
		IdDUT=[]
		###############################################################################################
		# find DUT gain - power should be low enough that the gain is linear and not in compression
		#self._reflevelgaincorrection=self._gain
		DUTgainest=0.
		pwrlinearsteps=np.arange(powergainset_min,powergainset_max+self._powergain_step,self._powergain_step)
		for plevelset in pwrlinearsteps:
			pDUTin.append(plevelset+self._sourcecalfactor)									# DUT input power
			reflevel=self._reflevelgaincorrection+DUTgainest+5.+plevelset + self._sourcecalfactor-self._sacalfactor
			#reflevel=10.*int((DUTgainest+5.+plevelset + self._sourcecalfactor-self._sacalfactor) / 10.)                # set spectrum analyzer reference level to nearest increment of 10dB
			self._sa.set_referencelevel(reflevel)                 # set reference level of spectrum analyzer
			if "unleveled"==self._rfA.set_power(plevelset):
				print ("Warning1: power at DUT: power beyond capability at ",plevelset+self._sourcecalfactor)
			if self._ps!=None and self._Vgs!=None and self._Vds!=None and self._Vds!=0.:			# then assume that there is a power supply to be used
				time.sleep(self.settlingtime)
				Id,Ig,drainstatus,gatestatus= self._ps.fetbiason_topgate(Vgs=self._Vgs,Vds=self._Vds,draincomp=self._Idcomp,gatecomp=self._Igcomp)
				IdDUT.append(Id)
				IgDUT.append(Ig)
				gatestatusDUT.append(gatestatus)
				drainstatusDUT.append(drainstatus)
				if gatestatus!='N' or drainstatus!='N':
					print("WARNING! gate or drain in compliance while finding small-signal gain")
			reflevel,f,prf=self.autoadjust_reference_level(referencelevel=reflevel,frequency=self._frequency,frequencyspan=self._saspan)
			DUTgainest=(prf+self._sacalfactor)/(plevelset+self._sourcecalfactor)
			pDUTout.append(prf+self._sacalfactor)
		self.gainm,self.DUTgain,r= linfitendexclude(x=pDUTin,y=pDUTout,lowerfraction=fractlinfitlower,upperfraction=fractlinfitupper )			# find DUT small-signal gain
		if max(np.subtract(self.DUTgain,np.subtract(pDUTout,pDUTin)))>0.1:
			self._toohighlevel=True			# then the linear portion of this test is driving the DUT into compression by more than 0.1dB so we need to reduce the power levels
			print("WARNNING: power level too high - causing excessive gain compression for accurate gain measurement")
		# now have DUT gain so let's find the DUT input power to get the 1dB compression point
		########################################################################################

		compression=0.					# measured gain compression
		deltapowersetting=self._powergain_step
		plevelsethigh=powergainset_max+2.*deltapowersetting
		plevelsetlow=powergainset_max
		plevelset=(plevelsetlow+plevelsethigh)/2.
		############# done finding DUT gain from linear portion of power curve ####################

		########## now find the compression point ###############
		iterations=0
		self._reflevelgaincorrection=self.DUTgain
		self._sa.set_numberaverages(1)                          # set number of averages to 1 because these measurements are at high power (not small signal)
		while compression<compressiontarget-maxcompressionlevelerror and abs(compressiontarget-compression)>maxcompressionlevelerror and iterations<=maxiterations:			# search to find power level where target gain compression is reached
			# measure gain compression (compression) at the high power level search limit to see if we need to increase this
			iterations+=1
			reflevel=self._reflevelgaincorrection+self.DUTgain+5.+plevelsethigh + self._sourcecalfactor-self._sacalfactor
			#reflevel=10.*int((self.DUTgain+5.+plevelsethigh + self._sourcecalfactor-self._sacalfactor) / 10.)                # set spectrum analyzer reference level to nearest increment of 10dB
			self._sa.set_referencelevel(reflevel)                 # set reference level of spectrum analyzer
			if "unleveled"==self._rfA.set_power(plevelsethigh):
				print ("Warning2: power at DUT: power beyond capability at ",plevelsethigh+self._sourcecalfactor)
			#f,praw=self._sa.measure_spectrum(self._frequency, self._saspan, 'nospectrum')		# read raw output power level
			reflevel,f,praw=self.autoadjust_reference_level(referencelevel=reflevel,frequency=self._frequency,frequencyspan=self._saspan)
			pDUTinhigh=praw+self._sacalfactor													# DUT output power level
			gainatpowerpoint=pDUTinhigh-(plevelsethigh+self._sourcecalfactor)					# DUT gain at the set power level
			compressionhigh=self.DUTgain-gainatpowerpoint										# compression is the difference between the gain at the power level point and the small-signal gain measured earlier
			if compressionhigh-maxcompressionlevelerror>=compressiontarget:						# then upper limit compresses so OK
				# measure gain compression (compression) at the low power level search limit and lower it if at or above requested gain compression
				reflevel=self._reflevelgaincorrection+self.DUTgain+5.+plevelsetlow + self._sourcecalfactor-self._sacalfactor
				#reflevel=10.*int((self.DUTgain+5.+plevelsetlow + self._sourcecalfactor-self._sacalfactor) / 10.)                # set spectrum analyzer reference level to nearest increment of 10dB
				self._sa.set_referencelevel(reflevel)                 # set reference level of spectrum analyzer
				if "unleveled"==self._rfA.set_power(plevelsetlow):
					print ("Warning3: power at DUT: power beyond capability at ",plevelsetlow+self._sourcecalfactor)
				#f,praw=self._sa.measure_spectrum(self._frequency, self._saspan, 'nospectrum')		# read raw output power level
				reflevel,f,praw=self.autoadjust_reference_level(referencelevel=reflevel,frequency=self._frequency,frequencyspan=self._saspan) # read raw output power level
				pDUTinlow=praw+self._sacalfactor													# DUT output power level
				gainatpowerpoint=pDUTinlow-(plevelsetlow+self._sourcecalfactor)						# DUT gain at the set power level
				compressionlow=self.DUTgain-gainatpowerpoint										# compression is the difference between the gain at the power level point and the small-signal gain measured earlier
				if compressionlow+maxcompressionlevelerror<=compressiontarget:						# then lower limit is not at requested compressesion so OK
					# Adjust power setting to find requested compression power point
					pDUTin.append(plevelset+self._sourcecalfactor)									# DUT input power is the power set level (plevelset= synthesizer power setting) corrected by the synthesizer to DUT errors and losses
					reflevel=self._reflevelgaincorrection+self.DUTgain+5.+plevelset + self._sourcecalfactor-self._sacalfactor
					#reflevel=10.*int((self.DUTgain+5.+plevelset + self._sourcecalfactor-self._sacalfactor) / 10.)                # set spectrum analyzer reference level to nearest increment of 10dB
					self._sa.set_referencelevel(reflevel)                 # set reference level of spectrum analyzer
					if "unleveled"==self._rfA.set_power(plevelset):													# set synthesizer power level
						print ("Warning4: power at DUT: power beyond capability at ",plevelset+self._sourcecalfactor)
					if self._ps!=None and self._Vgs!=None and self._Vds!=None and self._Vds!=0.:			# then assume that there is a power supply to be used
						time.sleep(self.settlingtime)
						Id,Ig,drainstatus,gatestatus= self._ps.fetbiason_topgate(Vgs=self._Vgs,Vds=self._Vds,draincomp=self._Idcomp,gatecomp=self._Igcomp)
						IdDUT.append(Id)
						IgDUT.append(Ig)
						gatestatusDUT.append(gatestatus)
						drainstatusDUT.append(drainstatus)
						if gatestatus!='N' or drainstatus!='N':
							print("WARNING! gate or drain in compliance while finding large-signal compression")
					#f,praw=self._sa.measure_spectrum(self._frequency, self._saspan, 'nospectrum')	# read raw output power level
					reflevel,f,praw=self.autoadjust_reference_level(referencelevel=reflevel,frequency=self._frequency,frequencyspan=self._saspan)
					pDUTout.append(praw+self._sacalfactor)											# DUT output power level is the raw output power level corrected for errors and losses in the cabling and spectrum analyzer read errors
					gainatpowerpoint=pDUTout[-1]-pDUTin[-1]											# DUT gain at the set power level
					compression=self.DUTgain-gainatpowerpoint										# compression is the difference between the gain at the power level point and the small-signal gain measured earlier
				# now set the rf synthesizer power level for the next iteration
					if compression<compressiontarget-maxcompressionlevelerror:
						plevelsetlow=plevelset
						plevelset=(plevelsetlow+plevelsethigh)/2.										# binary search for the RF power level which gives the requested gain compression to within the requested error
					elif compression>compressiontarget+maxcompressionlevelerror:
						plevelsethigh=plevelset
						plevelset=(plevelsetlow+plevelsethigh)/2.										# binary search for the RF power level which gives the requested gain compression to within the requested error
				else: plevelsetlow=plevelsetlow-deltapowersetting								# lower power limit is too high (at or beyond specified compression) so decrease it
			else: plevelsethigh+=deltapowersetting												# upper power level was still not driving into compression so increase it
		######################## done finding compression point####################################################
		if iterations>maxiterations: print("WARNING! maximum number of iterations exceeded! Results might be inaccurate ",iterations)
		self.inputcompressionpoint=pDUTin[-1]
		self.outputcompressionpoint=pDUTout[-1]
		self.compressiontarget=compressiontarget
		self.noisefloor=noisefloor
		################################################################################################################################################
		# If the sweep near the compression point is specified, find the power characteristics near the compression point to fill in the power compression characteristics about the compression point
		#
		if self._comp_step!=None and self._comp_step>0.1 and self._comp_step<self._powergain_step:       # sweep about compression point ONLY if the stepsize here is provided and legal
			#self._sa.set_numberaverages(1)                   					# set number of averages to 1 because these measurements are at high powers
			pwrcompsteps=np.arange(powergainset_max, maxpowerset+self._comp_step,self._comp_step)
			for plevelset in pwrcompsteps:
				pDUTin.append(plevelset+self._sourcecalfactor)									# DUT input power
				reflevel=self._reflevelgaincorrection+self.DUTgain+5.+plevelset + self._sourcecalfactor-self._sacalfactor
				#reflevel=10.*int((self.DUTgain+5.+plevelset + self._sourcecalfactor-self._sacalfactor) / 10.)                # set spectrum analyzer reference level to nearest increment of 10dB
				self._sa.set_referencelevel(reflevel)                 # set reference level of spectrum analyzer
				if "unleveled"==self._rfA.set_power(plevelset):
					print ("Warning5: power at DUT: power beyond capability at ",plevelset+self._sourcecalfactor)
				if self._ps!=None and self._Vgs!=None and self._Vds!=None and self._Vds!=0.:			# then assume that there is a power supply to be used
					time.sleep(self.settlingtime)
					Id,Ig,drainstatus,gatestatus= self._ps.fetbiason_topgate(Vgs=self._Vgs,Vds=self._Vds,draincomp=self._Idcomp,gatecomp=self._Igcomp)
					IdDUT.append(Id)
					IgDUT.append(Ig)
					gatestatusDUT.append(gatestatus)
					drainstatusDUT.append(drainstatus)
					if gatestatus!='N' or drainstatus!='N':
						print("WARNING! gate or drain in compliance while finding small-signal gain")
				#f,prf=self._sa.measure_spectrum(self._frequency, self._saspan, 'nospectrum')
				reflevel,f,prf=self.autoadjust_reference_level(referencelevel=reflevel,frequency=self._frequency,frequencyspan=self._saspan)
				pDUTout.append(prf+self._sacalfactor)                                           # DUT output power
		############## done finding power characteristics near compression point #########################################################################
		# turn off RF synthesizer output and bias because the measurements are done
		self._rfA.off()
		if self._ps!=None and self._Vgs!=None and self._Vds!=None and self._Vds!=0.:			# then assume that there is a power supply to be used
			self._ps.fetbiasoff()

		# now sort and remove duplicates from output vs input power
		# remove duplicates
		pinunique=list(set(pDUTin))
		pout=[pDUTout[pDUTin.index(p)] for p in pinunique]
		if self._Vds!=0.:		# we are using a bias
			Id=[IdDUT[pDUTin.index(p)] for p in pinunique]
			Ig=[IgDUT[pDUTin.index(p)] for p in pinunique]
			gatestatus=[gatestatusDUT[pDUTin.index(p)] for p in pinunique]
			drainstatus=[drainstatusDUT[pDUTin.index(p)] for p in pinunique]
		# now sort in ascending input powers
		self.DUTcompression_pin=sorted(pinunique)
		self.DUTcompression_pout=[p[1] for p in sorted(zip(pinunique,pout),key=itemgetter(0))]
		if self._Vds!=0.:
			self.DUTcompression_Id=[p[1] for p in sorted(zip(pinunique,Id),key=itemgetter(0))]
			self.DUTcompression_Ig=[p[1] for p in sorted(zip(pinunique,Ig),key=itemgetter(0))]
			self.DUTcompression_gatestatus=[p[1] for p in sorted(zip(pinunique,gatestatus),key=itemgetter(0))]
			self.DUTcompression_drainstatus=[p[1] for p in sorted(zip(pinunique,drainstatus),key=itemgetter(0))]
####################################################################################################################
	# write power compression data to file
	writefile_Pcompression=X_writefile_Pcompression
#####################################################################################################################
# adjust reference level so that the input signal is not saturating the spectrum analyzer's input A/D convertor
	def autoadjust_reference_level(self,referencelevel=None,frequency=None,frequencyspan=None):
		maxrefleveladjusttries=10
		self._sa.set_numberaverages(1)                   					# set number of averages to 1 because these are at high power levels
		#loop to find reference level which doesn't saturate spectrum analyzer input######################
		reftries=0
		reflevelOK=False
		while reftries<maxrefleveladjusttries and not reflevelOK:      #loop to find reference level which doesn't saturate spectrum analyzer input
			reflevelOK=True
			try: measuredfrequency,measuredpowerlevel=self._sa.measure_spectrum(frequency,frequencyspan,'nospectrum')     #measure signal level
			except:
				reflevelOK=False
				referencelevel+=10.
				self._reflevelgaincorrection+=10.
				self._sa.set_referencelevel(referencelevel)
				reftries+=1
		if reftries>=maxrefleveladjusttries: raise ValueError("ERROR! number of retries with lowered reflevel exceeded")
		if referencelevel<measuredpowerlevel:
			self._reflevelgaincorrection=measuredpowerlevel+5.-referencelevel
			referencelevel=measuredpowerlevel+5.
			self._sa.set_referencelevel(referencelevel)
			measuredfrequency,measuredpowerlevel=self._sa.measure_spectrum(frequency,frequencyspan,'nospectrum')     #measure signal level
		return referencelevel,measuredfrequency,measuredpowerlevel
			##########################################