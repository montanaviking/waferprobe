# measures 1dB compression point at a single tone using the spectrum analyzer to measure power
# uses an output tuner to set reflection coefficient presented to the DUT output. The DUT input is at 50ohms
# must use synthesizer A
# opens handles for spectrum analyzer, tuner, and synthesizer but NOT parameter analyzer or power supply which are handled outside this code
__author__ = 'PMarsh Carbonics'
from spectrum_analyzer import *
from parameter_analyzer import *
from rf_sythesizer import *
from focustuner import *
from writefile_measured import X_writefile_Pcompression, X_writefile_Pgain
from read_write_spar_noise_v2 import read_spar, spar_flip_ports
from calculated_parameters import *
from IVplot import plotCompression
import numpy as np
from utilities import *
from operator import itemgetter, attrgetter
import time
# Input parameters
	# self._saatten is the spectrum analyzer's attanuation setting - must be 0dB, 5dB, 10dB,...
	# self._powerlevel_min is the lowest power setting at the DUT input, to measure the linear gain
	# self._powerlevel_max is the highest power setting at the DUT input, to measure the linear gain
	# self._powerlevel_step is the stepsize of the power at the DUT input, to determine linear gain
	# self._comp_step is the stepsize of the power sweep about the compression point to give a better-resolved compression characteristics curve (swept from self._powerlevel_max to self._maxpower in steps of self._comp_step)
	# self._maxpower is the maximum power at the DUT input, used to iterate to determine 1dB compression point
	# self._frequency is the frequency setting of the synthesizer
	# fractlinfitlower is the lower power point in terms of fraction of self._powerlevel_max-self._powerlevel_min that we fit the line to find the linear Pout vs Pin line. This line will be used to find the 1dB compression point
	# fractlinfitupper is the upper power point in terms of fraction of self._powerlevel_max-self._powerlevel_min that we fit the line to find the linear Pout vs Pin line. This line will be used to find the 1dB compression point
	# self.__rfAcalfactor = PDUTout-Psaread where PDUTout the power, at the DUT output, read by the power meter and then corrected for the probe loss and Psain is the power read on the spectrum analyzer display.
	# self._sourcecalfactor=PDUTin-PsynAset where PDUTin is the power at the DUT input, as read by the power meter and corrected for probe loss when synthesizer A is set to PsynAset and synthesizer B is off. self._sourcecalfactor is expected to be set to a negative dB quantity
# outputs: Note that each tuner position corresponds to a tuner reflection coefficient as presented to the DUT
# self.gatestatusDUT[pos] is the gate status during the search for compression point (normal='N' in compliance='C') vs tuner position
# self.drainstatusDUT[pos] is the drain status during the search for compression point (normal='N' in compliance='C') vs tuner position
# self.tuner_loss[pos] is the tuner loss vs tuner position
# self.actualrcoefMA[pos] is the actual tuner reflection coefficient presented to the DUT, for a given tuner position
# self.IgDUT[pos] is the DUT gate current during compression vs tuner position
# self.IdDUT[pos] is the DUT drain current during compression vs tuner position
# self.DUTgain[pos] is the DUT small-signal gain vs tuner position
settlingtime=0.1
epsilon = 1.E-20                  # used to compare floating point numbers to account for rounding errors
saspan= 100.E3					# spectrum analyzer frequency span in Hz
timeiterbias=1.                 # time in sec allowed to settle Id, Ig, in DUT prior to each reading of Id to see if Id has settled before moving on. This is set to allow Id to settle and remove the transient effects of hysteresis in the DUT IV curves
maxchangeId=0.01                # the maximum % change allowed in Id between readings of Id (at intervals of timeiterbias) to force settling of Id so as to mitigate hysteresis effects
maxtime=40.                     # the maximum time in sec that the Id is allowed to settle over
class PowerCompressionTunedFocus(FocusTuner):
	def __init__(self,rm=None,tunerfile=None,tunernumber=1,cascadefiles_port1=None,cascadefiles_port2=None, spectrum_analyser_input_attenuation=10.,number_of_averages=8,powerlevel_min=None,powerlevel_max=None,maxpower=None,comp_fillin_step=None,powerlevel_step=None,spectrum_analyzer_cal_factor=None,source_calibration_factor=None,expectedgain=0.):
		#cascade available 2port networks onto ports 1 and 2 of the tuner
		# for x=1 or 2 (port 1 or 2 of tuner) cascadefile_portx[i][0] is the S-parameter full filename and  cascadefile_portx[i][1] is "flip" or "noflip". "flip" means to transpose ports 1 and 2 of the S-parameters read from the file
		if cascadefiles_port1!=None and len(cascadefiles_port1)>0:
			if cascadefiles_port1[0][1]=='flip':   Sr=spar_flip_ports(read_spar(cascadefiles_port1[0][0]))
			else:   Sr=read_spar(cascadefiles_port1[0][0])
			del cascadefiles_port1[0]               # remove first 2-port file since its S-parameters have already been added to the first element of the cascade
			for c in cascadefiles_port1:            # c[0] is the S-parameter full filename and c[1] is "flip" or "noflip". "flip" means to transpose ports 1 and 2 of the S-parameters read from the file
				if c[1]=='flip': Sr=spar_flip_ports(read_spar(c[0]))  # then flip ports 1 and 2 on this two-port
				else: Sr=read_spar(c[0])                              # don't flip ports
				self.cascade_tuner(1,casaded2port)                              # cascade 2-port onto tuner's port 1
		#cascade available 2port networks onto port2 of tuner
		if cascadefiles_port2!=None and len(cascadefiles_port2)>0:
			for c in cascadefiles_port2:
				if c[1]=='flip': casaded2port=spar_flip_ports(read_spar(c[0]))  # then flip ports 1 and 2 on this two-port
				else: casaded2port=read_spar(c[0])                              # don't flip ports
				self.cascade_tuner(2,casaded2port)                              # cascade 2-port onto tuner's port 2
		super(PowerCompressionTunedFocus,self).__init__(S1=)                    # initialize Focus tuner

		try: self.__sa=SpectrumAnalyzer(rm)
		except: raise ValueError("ERROR! No spectrum analyzer found!")
		try: self.__rfA=Synthesizer(rm=rm,syn="A")            # synthesizer A should be the self.__rflow (lower frequency tone) because it has the high-accuracy attenuators
		except: raise ValueError("ERROR! No RF frequency synthesizer found!")
		# try: self.__ps=ParameterAnalyzer(rm)
		# except: raise ValueError("ERROR! No parameter analyzer detected")
		self._comp_fillin_step=comp_fillin_step
		self._expected_gain=expectedgain
		self._reflevelgaincorrection=expectedgain                   # initially correct the reference level setting for the expected gain of the DUT
		self.__rfA.off()							# turn off synthesizer

		self._saatten=spectrum_analyser_input_attenuation
		self._navg=number_of_averages
		self._powerlevel_min=powerlevel_min
		self._powerlevel_max=powerlevel_max
		self._powerlevel_step=powerlevel_step
		self._maxpower=maxpower
		#self._frequency=frequency				# operation frequency in Hz
		self._sacalfactor=spectrum_analyzer_cal_factor # dB difference between the tuner output (port 2) (as measured by the power meter) and the spectrum analyzer level. This takes into account the loss between the tuner port 2 (output) and the spectrum analyzer as well as calibration of the spectrum analyzer display
		self._sourcecalfactor=source_calibration_factor # dB difference between the power at the DUT's input (port 1) - as measured on the power meter, and the power setting on the RF synthesizer A. Almost always a negative dB number
###################################################################################
# Find RF input power level which gives the DUT gain output compression specified by compressiontarget (usually 1dB)
# parameters:
#   fractlinfitlower, fractlinfitupper -> the lower and upper bounds of the least-squares linear fit to the output power vs input power in the uncompressed power level region - the linear fit is the DUT gain at small signal
#   compressiontarget is the amount of gain compression targeted by this measurement. e.g. if compresstarget=1, then return the input power level which produces 1dB gain compression in the DUT
#   maxcompressionlevelerror is the maximum deviation from the target compression point where measurement iterations are ended
#   output_reflection is the array of reflection coefficients real+jimaginary, targets for the tuner reflection coefficient presented to the DUT output - output_reflection = [[real1,jimaginary1],[real2,jimaginary2],....]
#   frequency is the measurement frequency in Hz
#   ps is the parameter analyzer handle. Assumes use of a Keithely 4200 parameter analyzer to supply DC bias
#   Vgs, Vds, draincomp, gatecomp, are respectively the gate voltage, drain voltage, drain current compliance limit (A), and gate current compliance limit (A)
	def measurePcomp(self,ps=None, fractlinfitlower=0.,fractlinfitupper=1.,compressiontarget=1.,maxcompressionlevelerror=0.1,output_reflection=None,frequency=None,Vgs=0.,Vds=0.,draincomp=0.1,gatecomp=0.1,plotcompression=True,maxiterations=30):
		#maxiterations=2						# maximum allowed number of power iterations/point
		# compressiontarget is the target level of gain compression, maxcompressionlevelerror is the maximum error allowed between the compressiontarget and the actual power compression level
		if maxcompressionlevelerror<0.02: raise ValueError("maxcompressionlevelerror set too low")
		self.frequency=frequency
		self.compressiontarget=compressiontarget
		self.__rfA.off()							# turn off synthesizer
		self.__rfA.set_frequency(self.frequency)									        # set frequency of synthesizer
		self.__sa.set_attenuation(self._saatten)                     				# set input attenuation level of spectrum analyzer
		self.__sa.set_numberaverages(self._navg)                   					# set number of averages
		self.__sa.set_autoresolutionbandwidth('y')
		self.__sa.set_autovideobandwidth('y')
		self._toohighlevel=False														# warning flag for synthesizer level set too high and causing too much gain compression for an accurate gain
		self.Vgs=Vgs
		self.Vds=Vds
		self.draincomp=draincomp
		self.gatecomp=gatecomp
		# note that sourcecalfactor is the dB difference between the power meter measured power and that set on the rf synthesizer (A) = dB power meter - dB synthesizer setting (usually negative dB)
		powerlevelset_min=self._powerlevel_min-self._sourcecalfactor  			# powerlevelset_min is the lowest power direct setting used on the synthesizer it is the requested lowest power corrected by the losses from synthesizer to the DUT input. This is reference to the DUT input
		powerlevelset_max=self._powerlevel_max-self._sourcecalfactor				# powerlevelset_max is the highest power direct setting used on the synthesizer it is the requested highest power corrected by the losses from synthesizer to the DUT input. This is reference to the DUT input
		maxpowerset=self._maxpower-self._sourcecalfactor							# maximum power setting to calculate compression levels
		# make sure that the synthesizer maximum power level is leveled and OK
		#plevelmax=max(powerlevelset_max,self._maxpower)
		while self.__rfA.set_power(powerlevelset_max)=='unleveled': # power level setting is beyond the synthesizer's capability so reduce the maximum requested power
			powerlevelset_max=powerlevelset_max-1.1*self._powerlevel_step
			print ("Warning: powerlevelset_max: power beyond capability so reducing maximum power set at synthesizers to ", powerlevelset_max)
		while self.__rfA.set_power(maxpowerset)=='unleveled': # power level setting is beyond the synthesizer's capability so reduce the maximum requested power
			maxpowerset=maxpowerset-1.1*self._powerlevel_step
			print ("Warning: maxpowerset: power beyond capability so reducing maximum power set at synthesizers to ", maxpowerset)
			print ("Warning: maxpowerset: power beyond capability so reducing maximum power set at DUT input to ", maxpowerset+self._sourcecalfactor)
		print ("sourcecalfactor", self._sourcecalfactor)
		if maxpowerset<=powerlevelset_max+self._powerlevel_step: raise ValueError("ERROR: maximum power for linear measurements is too high or maximum power for compression is too low")
		if int((fractlinfitupper-fractlinfitlower)*(powerlevelset_max-powerlevelset_min)/self._powerlevel_step)<2:	raise ValueError("ERROR: Check power level step size and fractions to fit line")
		# find DUT gain
		# first deternmine if the minimum power setting we'll use during this measurement is above the noise floor at the spectrum analyzer
		self.__rfA.off()
		self.__sa.set_referencelevel(-50.)
		noisefloor,maxsig=self.__sa.measure_noisefloor(centfreq=self.frequency, span=saspan, nospec='nospectrum')			# get noise floor with synthesizer turned off
		print("from compression.py line 77 raw noise floor is: ",noisefloor)
		reflevel=10.*int((self._reflevelgaincorrection+powerlevelset_min+self._sourcecalfactor-self._sacalfactor)/10.)                # set spectrum analyzer reference level to nearest increment of 10dB
		self.__sa.set_referencelevel(reflevel)                 # set reference level of spectrum analyzer
		self.__rfA.set_power(powerlevelset_min)																# turn on synthesizer to minimum power used in this test
		#f,prf=self.__sa.measure_spectrum(self._frequency, self._saspan, 'nospectrum')						# get raw signal power level reading for minimum synthesizer power setting
		reflevel,f,prf=self.autoadjust_reference_level(referencelevel=reflevel,frequency=self.frequency,frequencyspan=saspan)
		if prf<noisefloor+6.: raise ValueError("ERROR: powerlevelset_min too low - below noise floor")

		self.gatestatusDUT={}
		self.drainstatusDUT={}
		self.tuner_loss={}
		self.actualrcoefMA={}
		self.IgDUT={}
		self.IdDUT={}
		self.DUTgain={}
		#pDUTin={}
		self.pDUTout={}
		self.inputcompressionpoint={}
		self.outputcompressionpoint={}
		self.noisefloor={}
		################################
		# loop through select load tuner positions of which each corresponds to a tuner reflection presented to the DUT output (load pull)
		for ref in output_reflection:
			pos,actualrcoefRI,self.actualrcoefMA[pos] =self.get_tuner_position_from_reflection(frequency=int(1E-6*self.frequency), requested_reflection=np.complex(ref[0],ref[1]), reflection_type='MA')
			# pDUTi=[]
			# pDUTo=[]
			self.pDUTout[pos]={}
			self.IgDUT[pos]={}
			self.IdDUT[pos]={}
			self.drainstatusDUT[pos]={}
			self.gatestatusDUT[pos]={}
			self.set_tuner_position(position=pos)                       # set tuner position
			self.tuner_loss[pos]=-10.*np.log10(self.get_tuner_availablegain_loadpull(frequency=int(1E-6*self.frequency),position=pos,flipports=False))           # get tuner loss in dB (positive number)
			###############################################################################################
			# measure DUT linear gain
			# power should be low enough that the gain is linear and not in compression
			#self._reflevelgaincorrection=self._expected_gain
			reflevel=self._reflevelgaincorrection+5.+self._sourcecalfactor-self._sacalfactor
			self.__sa.set_referencelevel(reflevel)                 # set reference level of spectrum analyzer first try

			pwrlinearsteps=np.arange(powerlevelset_min,powerlevelset_max+self._powerlevel_step,self._powerlevel_step)
			for plevelset in pwrlinearsteps:                # loop through input power levels (in linear regime)
				pin=formatnum(plevelset+self._sourcecalfactor,precision=1,nonexponential=True)				# DUT input power, i.e. pin, used as key for data, resolution=0.1dB
				if "unleveled"==self.__rfA.set_power(plevelset): print ("Warning1: power at DUT: power beyond capability at ",plevelset+self._sourcecalfactor)
				if ps!=None:    # then there is bias
					self.IdDUT[pos][pin],self.IgDUT[pos][pin],self.drainstatusDUT[pos][pin],self.gatestatusDUT[pos][pin] = ps.fetbiason_topgate(Vgs=self.Vgs,Vds=self.Vds,draincomp=self.draincomp,gatecomp=self.gatecomp,timeiter=timeiterbias,maxchangeId=maxchangeId,maxtime=maxtime)
				else:
					self.IdDUT[pos][pin]=0.
					self.IgDUT[pos][pin]=0.
					self.drainstatusDUT[pos][pin]=0.
					self.gatestatusDUT[pos][pin]=0.

				if self.gatestatusDUT[pos][pin]!='N' or self.drainstatusDUT[pos][pin]!='N': print("WARNING! gate or drain in compliance while finding small-signal gain")
				reflevel,f,prf_uncorrected=self.autoadjust_reference_level(referencelevel=reflevel,frequency=self.frequency,frequencyspan=saspan)               # get uncorrected RF DUT output power in dBm
				self.pDUTout[pos][pin]=prf_uncorrected+self.tuner_loss[pos]+self._sacalfactor                          # DUT output RF power corrected for tuner loss and spectrum analyzer power offset
			# done measuring linear gain regime so find linear gain
			pinDUT=sorted([float(p) for p in self.pDUTout[pos].keys()])
			poutDUT=[self.pDUTout[pos][formatnum(p,precision=2)] for p in pinDUT]
			gainm,g,r=linfitendexclude(x=pinDUT,y=poutDUT,lowerfraction=fractlinfitlower,upperfraction=fractlinfitupper)			# find DUT output linear fit for the given tuner motor position and reflection coefficient - it is the Y intercept point
			self.DUTgain[pos]=np.average(np.subtract(poutDUT,pinDUT))       # find the DUT gain from the linear portion of the Pout vs Pin curve
			if max(np.subtract(self.DUTgain[pos],np.subtract(poutDUT,pinDUT)))>0.1:
				self._toohighlevel=True			# then the linear portion of this test is driving the DUT into compression by more than 0.1dB so we need to reduce the power levels
				print("WARNNING: power level too high - causing excessive gain compression for accurate gain measurement")
			# now have DUT linear gain so let's find the DUT input power to get the 1dB compression point
			########################################################################################
			compression=0.					# measured gain compression
			deltapowersetting=self._powerlevel_step                     # this was the power level step used in the linear gain regime to measure the DUT linear gain
			plevelsethigh=powerlevelset_max+2.*deltapowersetting        # maximum DUT input power level to search for compression point
			plevelsetlow=powerlevelset_max                              # minimum DUT input power to search for compression point
			plevelset=(plevelsetlow+plevelsethigh)/2.                   # start DUT input power search at plevelset which is halfway between minimum and maximum search power values
			############# done finding DUT gain from linear portion of power curve ####################

			########## now find the compression point ###############
			iterations=0
			self.__sa.set_numberaverages(1)                          # set number of spectrum analyzer averages to 1 because these measurements are at high power (not small signal)
			while compression<self.compressiontarget-maxcompressionlevelerror and abs(self.compressiontarget-compression)>maxcompressionlevelerror and iterations<=maxiterations:			# search to find power level where target gain compression is reached
				# measure gain compression (compression) at the high power level search limit to see if we need to increase this
				print("from compression_maury_tuned.py line 197 gain compression dB and pin = ",compression,plevelset+self._sourcecalfactor)
				iterations+=1
				if "unleveled"==self.__rfA.set_power(plevelsethigh): print ("Warning2: power at DUT: power beyond capability at ",plevelsethigh+self._sourcecalfactor)  # set initial RF synthesizer output to start at highest power level for compression measurement
				reflevel,f,prf_uncorrected=self.autoadjust_reference_level(referencelevel=reflevel,frequency=self.frequency,frequencyspan=saspan)                       # read uncorrected RF power via spectrum analyzer
				pDUTouthigh=prf_uncorrected+self.tuner_loss[pos]+self._sacalfactor					# DUT output power level corrected for tuner loss and spectrum analyzer offset
				pDUTinhigh= plevelsethigh+self._sourcecalfactor                                 # DUT power input corrected for input circuit losses.  Note that self._sourcecalfactor is generally negative and represents the gain of the input circuit from RF synthesizer to DUT
				gainatpowerpoint= pDUTouthigh-pDUTinhigh					                    # DUT gain at the set power level.
				compressionhigh=self.DUTgain[pos]-gainatpowerpoint									# compression is the difference between the gain at the power level point and the small-signal linear regime gain measured earlier
				if compressionhigh-maxcompressionlevelerror>=self.compressiontarget:						# then upper limit compresses so OK
					# measure gain compression (compression) at the low power level search limit and lower it if at or above requested gain compression
					if "unleveled"==self.__rfA.set_power(plevelsetlow): print ("Warning3: power at DUT: power beyond capability at ",plevelsetlow+self._sourcecalfactor)
					reflevel,f,prf_uncorrected=self.autoadjust_reference_level(referencelevel=reflevel,frequency=self.frequency,frequencyspan=saspan) # read raw output power level
					pDUToutlow=prf_uncorrected+self.tuner_loss[pos]+self._sacalfactor											# DUT output power level dBm
					gainatpowerpoint=pDUToutlow-(plevelsetlow+self._sourcecalfactor)						# DUT gain at the set power level
					compressionlow=self.DUTgain[pos]-gainatpowerpoint										# compression is the difference between the gain at the power level point and the small-signal gain measured earlier
					if compressionlow+maxcompressionlevelerror<=self.compressiontarget:						# then lower limit is not at requested compressesion so OK
						# Adjust power setting to find requested compression power point
						pin=formatnum(plevelset+self._sourcecalfactor,precision=2,nonexponential=True)				# DUT input power, i.e. pin, used as key for data, resolution=0.1dB	(plevelset= synthesizer power setting) corrected by the synthesizer to DUT errors and losses
						if "unleveled"==self.__rfA.set_power(plevelset): print ("Warning4: power at DUT: power beyond capability at ",plevelset+self._sourcecalfactor)
						if ps!=None: # then there is bias
							self.IdDUT[pos][pin],self.IgDUT[pos][pin],self.drainstatusDUT[pos][pin],self.gatestatusDUT[pos][pin]=ps.fetbiason_topgate(Vgs=self.Vgs,Vds=self.Vds,draincomp=self.draincomp,gatecomp=self.gatecomp,timeiter=timeiterbias,maxchangeId=maxchangeId,maxtime=maxtime) # DUT bias on and/or read DUT currents
						else:
							self.IdDUT[pos][pin]=0.
							self.IgDUT[pos][pin]=0.
							self.drainstatusDUT[pos][pin]=0.
							self.gatestatusDUT[pos][pin]=0.
						if self.gatestatusDUT[pos][pin]!='N' or self.drainstatusDUT[pos][pin]!='N': print("WARNING! gate or drain in compliance while finding compression point")
						reflevel,f,prf_uncorrected=self.autoadjust_reference_level(referencelevel=reflevel,frequency=self.frequency,frequencyspan=saspan)
						self.pDUTout[pos][pin]=prf_uncorrected+self.tuner_loss[pos]+self._sacalfactor											# DUT output power level is the raw output power level corrected for errors and losses in the cabling and spectrum analyzer read errors
						gainatpowerpoint=self.pDUTout[pos][pin]-(plevelset+self._sourcecalfactor)			# DUT gain at the set power level. Input power = plevelset+self._sourcecalfactor
						compression=self.DUTgain[pos]-gainatpowerpoint										# compression is the difference between the gain at the power level point and the small-signal gain, self.DUTgain[pos], measured earlier
						print("from compression_maury_tuned.py line 222 gain compression dB = ",compression)
					# now set the rf synthesizer power level for the next iteration
						if compression<self.compressiontarget-maxcompressionlevelerror:
							plevelsetlow=plevelset
							plevelset=(plevelsetlow+plevelsethigh)/2.										# binary search for the RF power level which gives the requested gain compression to within the requested error
						elif compression>self.compressiontarget+maxcompressionlevelerror:
							plevelsethigh=plevelset
							plevelset=(plevelsetlow+plevelsethigh)/2.										# binary search for the RF power level which gives the requested gain compression to within the requested error
					else:
						plevelsetlow=plevelsetlow-deltapowersetting								# lower power limit is too high (at or beyond specified compression) so decrease it
						if plevelsetlow>maxpowerset: plevelsetlow=plevelsetlow-deltapowersetting    # limit DUT input power to at or less than maxpowerset
				else:
					plevelsethigh+=deltapowersetting												# upper power level was still not driving into compression so increase it
					if plevelsethigh>maxpowerset:
						plevelsethigh=maxpowerset    # limit DUT input power to at or less than maxpowerset
						print("WARNING attempt to set plevelsethigh>maxpowerset i.e. the maximum power allowed at the DUT input")
			######################## done finding compression point####################################################
			if iterations>maxiterations: print("WARNING! maximum number of iterations exceeded! Results might be inaccurate ",iterations)
			# self.inputcompressionpoint[pos]=plevelset+self._sourcecalfactor
			# self.outputcompressionpoint[pos]=self.pDUTout[pos][formatnum(plevelset+self._sourcecalfactor,precision=2,nonexponential=True)]
			self.inputcompressionpoint[pos]=float(pin)
			self.outputcompressionpoint[pos]=self.pDUTout[pos][pin]
			self.noisefloor[pos]=noisefloor
			################################################################################################################################################
			# If the sweep near the compression point is specified, find the power characteristics near the compression point to fill in the power compression characteristics about the compression point
			#
			if self._comp_fillin_step!=None and self._comp_fillin_step>0.1 and self._comp_fillin_step<self._powerlevel_step:       # sweep about compression point ONLY if the stepsize here is provided and legal
				pwrcompsteps=np.arange(powerlevelset_max, maxpowerset+self._comp_fillin_step,self._comp_fillin_step)
				for plevelset in pwrcompsteps:
					pin=formatnum(plevelset+self._sourcecalfactor,precision=2,nonexponential=True)									# DUT input power
					if "unleveled"==self.__rfA.set_power(plevelset): print ("Warning5: power at DUT: power beyond capability at ",plevelset+self._sourcecalfactor)
					if ps!=None:        # then there is bias
						self.IdDUT[pos][pin],self.IgDUT[pos][pin],self.drainstatusDUT[pos][pin],self.gatestatusDUT[pos][pin]= ps.fetbiason_topgate(Vgs=self.Vgs,Vds=self.Vds,draincomp=self.draincomp,gatecomp=self.gatecomp)
					else:
						self.IdDUT[pos][pin]=0.
						self.IgDUT[pos][pin]=0.
						self.drainstatusDUT[pos][pin]=0.
						self.gatestatusDUT[pos][pin]=0.
					if self.gatestatusDUT[pos][pin]!='N' or self.drainstatusDUT[pos][pin]!='N': print("WARNING! gate or drain in compliance while filling points out on compression")
					reflevel,f,prf_uncorrected=self.autoadjust_reference_level(referencelevel=reflevel,frequency=self.frequency,frequencyspan=saspan)
					self.pDUTout[pos][pin]=prf_uncorrected+self.tuner_loss[pos]+self._sacalfactor                                           # DUT output power
			############## done finding power characteristics near compression point #########################################################################

			# now plot the pout vs pin curve if the user chose to do so
			# if plotcompression:
			prfin=[formatnum(prf,precision=2,nonexponential=True) for prf in sorted([float(p) for p in self.pDUTout[pos].keys()])]   # input RF powers
			prfout=[self.pDUTout[pos][p] for p in prfin]
			prfin=[float(p) for p in prfin]
			plotCompression(pin=prfin,pout=prfout,gainm=gainm,gain=self.DUTgain[pos],inputcompression=self.inputcompressionpoint[pos],outputcompression=self.outputcompressionpoint[pos])
	# turn off RF synthesizer output and bias because the measurements are done
		self.__rfA.off()
		if ps!=None: ps.fetbiasoff()             # turn off DC power supply
#####################################################################################################################
# Measure gains vs the tuner's reflection coefficient applied to the output of the DUT
# frequency is in Hz
# RFpower is the DUT input RF power in dBm
# output reflection is an array of arrays i.e. [[mag,angle],[mag,angle],.....] of the reflection coefficients to try on the output of the DUT
	def gain_vs_outputreflection(self,output_reflection=None,RFpower=-10.,frequency=None,DUTSparfile=None):
		# loop through different output reflections set by the tuner on the DUT
		self.RFpower=RFpower
		self.frequency=frequency
		self.__rfA.set_frequency(self.frequency)									# set frequency of synthesizer
		self.actualrcoefMA={}    # actual reflection coefficient as set by tuner in magnitude and angle
		self.__sa.set_numberaverages(self._navg)                   # set number of averages for spectrum analyzer
		self.__sa.set_autoresolutionbandwidth('y')
		self.__sa.set_autovideobandwidth('y')
		self.rfoutputlevel={}
		self.DUTgain={}
		self.tuner_loss={}
		self.tunergain50ohms={}                         # tuner gain in 50ohm system (to check system)
		self.__rfA.set_power(leveldBm=self.RFpower-self._sourcecalfactor)
		self.__rfA.on()                                 # turn on synthesizer
		self.calcDUTgain={}
		self.calcDUTgain_from_cascade={}
		try: DUTSpar=read_spar(sparfilename=DUTSparfile)         # read DUT S-parameter files
		except: DUTSpar=None
		for ref in output_reflection:
			# set the tuner reflection coefficient presented to the DUT output
			pos,actualrcoefRI,self.actualrcoefMA[pos] =self.get_tuner_position_from_reflection(frequency=int(1E-6*self.frequency), requested_reflection=np.complex(ref[0],ref[1]), reflection_type='MA')
			self.set_tuner_position(position=pos)                       # set tuner position
			Stuner=self.tuner_data[str(int(1E-6*self.frequency))][pos]      # tuner S-parameters
			self.tuner_loss[pos]=-10.*np.log10(self.get_tuner_availablegain_loadpull(frequency=int(1E-6*self.frequency),position=pos,flipports=False))           # get tuner loss in dB (positive number)
			if DUTSpar!=None:
				DUTcascadetunerS=cascadeS(DUTSpar[str(int(1E-6*self.frequency))],Stuner)
				self.calcDUTgain_from_cascade[pos]=20*np.log10(abs(DUTcascadetunerS[1,0]))+self.tuner_loss[pos]    # calculated DUT gain
				self.calcDUTgain[pos]=convertSRItoGt(S=DUTSpar[str(int(1E-6*self.frequency))],gammaout=actualrcoefRI,dBout=True)    # calculated DUT gain in dB
			self.__sa.set_attenuation(self._saatten)                   # set attenuation level of spectrum analyzer
			reflevel=10.*int((self.RFpower+self._expected_gain+self._reflevelgaincorrection+self._sourcecalfactor-self._sacalfactor-self.tuner_loss[pos])/10.)     # set spectrum analyzer reference level to nearest increment of 10dB
			#self.__sa.set_referencelevel(reflevel)                 # set reference level of spectrum analyzer
			pref,f,rfoutputlevel_uncorrected=self.autoadjust_reference_level(referencelevel=reflevel,frequency=self.frequency,frequencyspan=saspan)
			self.rfoutputlevel[pos]=self.tuner_loss[pos]+self._sacalfactor+10.*np.log10(abs(pow(10.,rfoutputlevel_uncorrected/10.)))      # correct the read RF output level for tuner loss
			self.DUTgain[pos]=self.rfoutputlevel[pos]-self.RFpower
			self.tunergain50ohms[pos]=self.get_tuner50gain(frequency=int(1E-6*frequency),position=pos,flipports=False)
			print("reflection "+str(self.actualrcoefMA[pos])+" RF output raw dBm "+str(rfoutputlevel_uncorrected+self._sacalfactor)+" RF output raw-tunergain50ohms "+str(rfoutputlevel_uncorrected+self._sacalfactor-self.tunergain50ohms[pos]))
		self.__rfA.off()                # turn off RF generator
#####################################################################################################################
# adjust reference level so that the input signal is not saturating the spectrum analyzer's input A/D convertor
	def autoadjust_reference_level(self,referencelevel=None,frequency=None,frequencyspan=None):
		maxrefleveladjusttries=10
		self.__sa.set_numberaverages(1)                   					# set number of averages to 1 because these are at high power levels
		#loop to find reference level which doesn't saturate spectrum analyzer input######################
		reftries=0
		reflevelOK=False
		while reftries<maxrefleveladjusttries and not reflevelOK:      #loop to find reference level which doesn't saturate spectrum analyzer input
			reflevelOK=True
			try: measuredfrequency,measuredpowerlevel=self.__sa.measure_spectrum(centfreq=frequency,span=frequencyspan,returnspectrum=False)     #measure signal level
			except:
				reflevelOK=False
				referencelevel+=10.
				self._reflevelgaincorrection+=10.
				self.__sa.set_referencelevel(referencelevel)
				reftries+=1
		if reftries>=maxrefleveladjusttries: raise ValueError("ERROR! number of retries with lowered reflevel exceeded")
		# if referencelevel<measuredpowerlevel:
		# 	self._reflevelgaincorrection=measuredpowerlevel+5.-referencelevel
		# 	referencelevel=measuredpowerlevel+5.
		# 	self.__sa.set_referencelevel(referencelevel)
		# 	measuredfrequency,measuredpowerlevel=self.__sa.measure_spectrum(centfreq=frequency,span=frequencyspan,returnspectrum=False)     #measure signal level
		return referencelevel,measuredfrequency,measuredpowerlevel
###################################################################################################################
	# write power compression data to file
	writefile_Pcompression_tuned=X_writefile_Pcompression_tuned
	writefile_Pgain=X_writefile_Pgain
#####################################################################################################################