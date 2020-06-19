# measures 1dB compression point at a single tone using the spectrum analyzer to measure power
# uses power meter to read output power
# uses an output tuner to set reflection coefficient presented to the DUT output. The DUT input is at 50ohms
# must use synthesizer A
# opens handles for spectrum analyzer, tuner, and synthesizer but NOT parameter analyzer or power supply which are handled outside this code
__author__ = 'PMarsh Carbonics'
from spectrum_analyzer import *
from parameter_analyzer import *
from rf_sythesizer import *
from MauryTunerMT986_v2 import *
from writefile_measured import X_writefile_Pcompression, X_writefile_Pgain
from read_write_spar_noise_v2 import read_spar, spar_flip_ports
from calculated_parameters import *
from IVplot import plotCompression
import numpy as np
from utilities import *
from HP438A import *
from operator import itemgetter, attrgetter
import time
# Input parameters
	# self._saatten is the spectrum analyzer's attanuation setting - must be 0dB, 5dB, 10dB,...
	# self._powerlevel_min is the lowest power setting at the DUT input, to measure the linear gain
	# self._powerlevellinear_max is the highest power setting at the DUT input, to measure the linear gain
	# self._powerlevel_step is the stepsize of the power at the DUT input, to determine linear gain
	# self._comp_step is the stepsize of the power sweep about the compression point to give a better-resolved compression characteristics curve (swept from self._powerlevellinear_max to self._maxpower in steps of self._comp_step)
	# self._maxpower is the maximum power at the DUT input, used to iterate to determine 1dB compression point
	# self._frequency is the frequency setting of the synthesizer
	# fractlinfitlower is the lower power point in terms of fraction of self._powerlevellinear_max-self._powerlevel_min that we fit the line to find the linear Pout vs Pin line. This line will be used to find the 1dB compression point
	# fractlinfitupper is the upper power point in terms of fraction of self._powerlevellinear_max-self._powerlevel_min that we fit the line to find the linear Pout vs Pin line. This line will be used to find the 1dB compression point
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
minreadablepower=-35.0          # minimum RF power that is readable by the power meter
maxreadablepower=20.0          # minimum RF power that is readable by the power meter
class PowerCompressionTunedMaury(MauryTunerMT986, HP438A):
	def __init__(self,rm=None,tunerfile=None,tunernumber=1,calfactor=97.6, loglin='LG',cascadefiles_port1=None,cascadefiles_port2=None,powerlevellinear_min=None,powerlevellinear_max=None,maxpower=None,comp_fillin_step=None,powerlevel_step=None,source_calibration_factor=None):
		if tunerfile!=None and tunerfile!="": # have tuner
			super(PowerCompressionTunedMaury, self).__init__(rm=rm, tunerfile=tunerfile, tunernumber=tunernumber)
			HP438A.__init__(self,rm=rm,calfactor=calfactor,loglin=loglin)           # set up power meter
			# set up tuner
			#cascade available 2port networks onto port1 of tuner
			if cascadefiles_port1!=None and len(cascadefiles_port1)>0:
				for c in cascadefiles_port1:
					if c[1]=='flip': casaded2port=spar_flip_ports(read_spar(c[0]))  # then flip ports 1 and 2 on this two-port
					else: casaded2port=read_spar(c[0])                              # don't flip ports
					self.cascade_tuner(1,casaded2port)                              # cascade 2-port onto tuner's port 1
			#cascade available 2port networks onto port2 of tuner
			if cascadefiles_port2!=None and len(cascadefiles_port2)>0:
				for c in cascadefiles_port2:
					if c[1]=='flip': casaded2port=spar_flip_ports(read_spar(c[0]))  # then flip ports 1 and 2 on this two-port
					else: casaded2port=read_spar(c[0])                              # don't flip ports
					self.cascade_tuner(2,casaded2port)                              # cascade 2-port onto tuner's port 2
		try: self.__rfA=Synthesizer(rm=rm,syn="A")            # synthesizer A should be the self.__rflow (lower frequency tone) because it has the high-accuracy attenuators
		except: raise ValueError("ERROR! No RF frequency synthesizer found!")
		self._comp_fillin_step=comp_fillin_step
		self.__rfA.off()							# turn off synthesizer
		self._powerlevellinear_min=powerlevellinear_min
		self._powerlevellinear_max=powerlevellinear_max
		self._powerlevel_step=powerlevel_step
		self._maxpower=maxpower

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
	def measurePcomp(self,ps=None, fractlinfitlower=0.,fractlinfitupper=1.,compressiontarget=1.,maxcompressionlevelerror=0.1, powermeterfilterfactor=None,output_reflection=None,frequency=None,Vgs=0.,Vds=0.,draincomp=0.1,gatecomp=0.1,plotcompression=True,maxiterations=30):
		#maxiterations=2						# maximum allowed number of power iterations/point
		# compressiontarget is the target level of gain compression, maxcompressionlevelerror is the maximum error allowed between the compressiontarget and the actual power compression level
		if maxcompressionlevelerror<0.02: raise ValueError("maxcompressionlevelerror set too low")
		self.frequency=frequency
		self.compressiontarget=compressiontarget
		self.__rfA.off()							# turn off synthesizer
		self.__rfA.set_frequency(self.frequency)									        # set frequency of synthesizer

		self._toohighlevel=False														# warning flag for synthesizer level set too high and causing too much gain compression for an accurate gain
		self.Vgs=Vgs
		self.Vds=Vds
		self.draincomp=draincomp
		self.gatecomp=gatecomp
		#self._powermeterfilterfactor=powermeterfilterfactor
		# note that sourcecalfactor is the dB difference between the power meter measured power and that set on the rf synthesizer (A) = dB power meter - dB synthesizer setting (usually negative dB)
		powerlevelset_min=self._powerlevellinear_min-self._sourcecalfactor  			# powerlevelset_min is the lowest power direct setting used on the synthesizer it is the requested lowest power corrected by the losses from synthesizer to the DUT input. This is reference to the DUT input
		powerlevelset_max=self._powerlevellinear_max-self._sourcecalfactor				# powerlevelset_max is the highest power direct setting used on the synthesizer it is the requested highest power corrected by the losses from synthesizer to the DUT input. This is reference to the DUT input
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
		if ps!=None:    # then there is bias
			ps.fetbiason_topgate(Vgs=self.Vgs,Vds=self.Vds,draincomp=self.draincomp,gatecomp=self.gatecomp,timeiter=timeiterbias,maxchangeId=maxchangeId,maxtime=maxtime)       # turn on DUT bias
		self.__rfA.set_power(powerlevelset_min)																# turn on synthesizer to minimum power used in this test
		prfmin=self.readpower()
		self.__rfA.set_power(powerlevelset_max)
		prfmax=self.readpower()
		if prfmin<minreadablepower: raise ValueError("ERROR: powerlevelset_min too low - below accurate reading capability of power sensor")
		elif prfmin>maxreadablepower: raise ValueError("ERROR: powerlevelset_min too high - above accurate reading capability of power meter and could damage power sensor")

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
			pos,actualrcoefRI,self.actualrcoefMA[pos]=self.get_tuner_position_from_reflection(frequency=int(1E-6*self.frequency), requested_reflection=np.complex(ref[0],ref[1]), reflection_type='MA')
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
			pwrlinearsteps=np.arange(powerlevelset_min,powerlevelset_max+self._powerlevel_step,self._powerlevel_step)       # arrau of RF synthesizer direct power settings. These are the powers set on the RF synthesizer and the actual power at the DUT input will be lower
			for plevelset in pwrlinearsteps:                # loop through input power levels (in linear regime)
				pin=formatnum(plevelset+self._sourcecalfactor,precision=2,nonexponential=True)				# actual DUT input power, i.e. pin, used as key for data, resolution=0.1dB
				if "unleveled"==self.__rfA.set_power(plevelset): print ("Warning1: power at DUT: power beyond capability at ",plevelset+self._sourcecalfactor)
				if ps!=None:    # then there is bias
					print("from compression_maury_tuned.py line 159 pin dBm = ",pin)
					self.IdDUT[pos][pin],self.IgDUT[pos][pin],self.drainstatusDUT[pos][pin],self.gatestatusDUT[pos][pin] = ps.fetbiason_topgate(Vgs=self.Vgs,Vds=self.Vds,draincomp=self.draincomp,gatecomp=self.gatecomp,timeiter=timeiterbias,maxchangeId=maxchangeId,maxtime=maxtime)
					print("from compression_maury_tuned.py line 161 pin dBm = ",pin)
				else:
					self.IdDUT[pos][pin]=0.
					self.IgDUT[pos][pin]=0.
					self.drainstatusDUT[pos][pin]=0.
					self.gatestatusDUT[pos][pin]=0.

				if self.gatestatusDUT[pos][pin]!='N' or self.drainstatusDUT[pos][pin]!='N': print("WARNING! gate or drain in compliance while finding small-signal gain")
				prf_uncorrected=self.readpower()     # get uncorrected RF DUT output power in dBm
				self.pDUTout[pos][pin]=prf_uncorrected+self.tuner_loss[pos]                          # DUT output RF power corrected for tuner loss (recall that the tuner includes all RF devices between the DUT and input of power sensor
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
			while compression<self.compressiontarget-maxcompressionlevelerror and abs(self.compressiontarget-compression)>maxcompressionlevelerror and iterations<=maxiterations:			# search to find power level where target gain compression is reached
				# measure gain compression (compression) at the high power level search limit to see if we need to increase this
				print("from compression_maury_tuned.py line 197 gain compression dB and pin = ",compression,plevelset+self._sourcecalfactor)
				iterations+=1
				if "unleveled"==self.__rfA.set_power(plevelsethigh): print ("Warning2: power at DUT: power beyond capability at ",plevelsethigh+self._sourcecalfactor)  # set initial RF synthesizer output to start at highest power level for compression measurement
				prf_uncorrected=self.readpower(filter=powermeterfilterfactor)     # get uncorrected RF DUT output power in dBm
				pDUTouthigh=prf_uncorrected+self.tuner_loss[pos]					# DUT output power level corrected for tuner loss (i.e. all RF 2-ports between DUT and power sensor losses are included in the tuner loss)
				pDUTinhigh= plevelsethigh+self._sourcecalfactor                                 # DUT power input corrected for input circuit losses.  Note that self._sourcecalfactor is generally negative and represents the gain of the input circuit from RF synthesizer to DUT
				gainatpowerpoint= pDUTouthigh-pDUTinhigh					                    # DUT gain at the set power level.
				compressionhigh=self.DUTgain[pos]-gainatpowerpoint									# compression is the difference between the gain at the power level point and the small-signal linear regime gain measured earlier
				if compressionhigh-maxcompressionlevelerror>=self.compressiontarget:						# then upper limit compresses so OK
					# measure gain compression (compression) at the low power level search limit and lower it if at or above requested gain compression
					if "unleveled"==self.__rfA.set_power(plevelsetlow): print ("Warning3: power at DUT: power beyond capability at ",plevelsetlow+self._sourcecalfactor)
					prf_uncorrected=self.readpower(filter=powermeterfilterfactor)     # get uncorrected RF DUT output power in dBm
					pDUToutlow=prf_uncorrected+self.tuner_loss[pos]											# DUT output power level corrected for tuner loss (i.e. all RF 2-ports between DUT and power sensor losses are included in the tuner loss)
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
						prf_uncorrected=self.readpower(filter=powermeterfilterfactor)                                                    # get uncorrected RF DUT output power in dBm
						self.pDUTout[pos][pin]=prf_uncorrected+self.tuner_loss[pos]							# DUT output power level is the raw output power level corrected for errors and losses in the cabling and spectrum analyzer read errors
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
			self.inputcompressionpoint[pos]=float(pin)
			self.outputcompressionpoint[pos]=self.pDUTout[pos][pin]
			################################################################################################################################################
			# If the sweep near the compression point is specified, find the power characteristics near the compression point to fill in the power compression characteristics about the compression point
			#
			if self._comp_fillin_step!=None and self._comp_fillin_step>0.1:       # sweep about compression point ONLY if the stepsize here is provided and legal
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
					print("from line 287 in compression_maury_tuned_with_powermeter.py before read of power, pin= ",pin)
					prf_uncorrected=self.readpower(filter=powermeterfilterfactor)                                                    # get uncorrected RF DUT output power in dBm
					self.pDUTout[pos][pin]=prf_uncorrected+self.tuner_loss[pos]                                           # DUT output power
					print("from line 287 in compression_maury_tuned_with_powermeter.py after read of power, pout= ",self.pDUTout[pos][pin])
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
# RFinputpower is the DUT input RF power in dBm
# output reflection is an array of arrays i.e. [[mag,angle],[mag,angle],.....] of the reflection coefficients to try on the output of the DUT
	def gain_vs_outputreflection(self,output_reflection=None,RFinputpower=-10.,frequency=None,powermeterfilterfactor=None,DUTSparfile=None):
		# loop through different output reflections set by the tuner on the DUT
		self.RFinputpower=RFinputpower
		self.frequency=frequency
		self.__rfA.set_frequency(self.frequency)									# set frequency of synthesizer
		self.actualrcoefMA={}    # actual reflection coefficient as set by tuner in magnitude and angle
		self.rfoutputlevel={}
		self.DUTgain={}
		self.tuner_loss={}
		self.tunergain50ohms={}                         # tuner gain in 50ohm system (to check system)
		self.__rfA.set_power(leveldBm=self.RFinputpower-self._sourcecalfactor)
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
			rfoutputlevel_uncorrected=self.readpower(filter=powermeterfilterfactor)                                                    # get uncorrected RF DUT output power in dBm
			self.rfoutputlevel[pos]=self.tuner_loss[pos]+rfoutputlevel_uncorrected
			#self.rfoutputlevel[pos]=self.tuner_loss[pos]+10.*np.log10(abs(pow(10.,rfoutputlevel_uncorrected/10.)))      # correct the read RF output level for tuner loss and convert to linear (mW)
			self.DUTgain[pos]=self.rfoutputlevel[pos]-self.RFinputpower             # DUT gain measured at the given RF input power and frequency
			self.tunergain50ohms[pos]=self.get_tuner50gain(frequency=int(1E-6*frequency),position=pos,flipports=False)
			print("reflection "+str(self.actualrcoefMA[pos])+" RF output raw dBm "+str(rfoutputlevel_uncorrected)+" RF output raw-tunergain50ohms "+str(rfoutputlevel_uncorrected-self.tunergain50ohms[pos]))
		self.__rfA.off()                # turn off RF generator

###################################################################################################################
	# write power compression data to file
	writefile_Pcompression_tuned=X_writefile_Pcompression_tuned
	writefile_Pgain=X_writefile_Pgain
#####################################################################################################################