# measures 1dB compression point at a single tone using the spectrum analyzer to measure power
# uses power meter to read output power
# uses an output tuner to set reflection coefficient presented to the DUT output. The DUT input is at 50ohms
# must use synthesizer A
# opens handles for spectrum analyzer, tuner, and synthesizer but NOT parameter analyzer or power supply which are handled outside this code
__author__ = 'PMarsh Carbonics'
from spectrum_analyzer import *
from parameter_analyzer import *
from rf_synthesizer import *
from focustuner import *
from writefile_measured import X_writefile_Pcompression, X_writefile_Pgain
from read_write_spar_noise import read_spar, spar_flip_ports
from calculated_parameters import *
from IVplot import plotCompression
import numpy as np
from utilities import *
from HP438A import *
from numpy import unravel_index as uind
from calculated_parameters import convertRItoMA
from scipy.interpolate import griddata
from operator import itemgetter, attrgetter
import time
# see file /carbonics/owncloudsync/programs/python/software_documentation/software_developer_documentation/measurement_software_TOI.odp
# Input parameters
# rm is the handle for the VISA GPIB software
# tunertype = 'load' or 'source' is the type of tuner 'load' is used here
# calfactorA is the power meter A's calibration factor as read (for the RF frequency used) off the power sensor connected to port A of the power meter. NOTE: power meter A is ALWAYS used to sense the DUT input power
# calfactorB is the power meter B's calibration factor as read (for the RF frequency used) off the power sensor connected to port B of the power meter. NOTE: power meter B is ALWAYS used to sense the DUT output power (from port 2 of the tuner)
# source_calibration_factor=PDUTin-PsynAset (dB) where PDUTin is the power at the DUT input, as read by the power meter and corrected for probe loss when synthesizer A is set to PsynAset and synthesizer B is off. self._source_calibration_factor is expected to be set to a negative dB quantity
# input_sensor_calfactor = DUT input power - powermeter A measured power (dB)
# loglin='LG' sets up power meters to read in dBm - this is the default
# cascadefiles_port1[i][j] where cascadefiles_port1[i][0] are the S-parameters to be cascaded onto the tuner port 1 and cascadefiles_port1[i][1]='flip' or 'noflip' which controls how these S-parameter are cascaded
# cascadefiles_port2[i][j] where cascadefiles_port2[i][0] are the S-parameters to be cascaded onto the tuner port 2 and cascadefiles_port2[i][1]='flip' or 'noflip' which controls how these S-parameter are cascaded
# powerlevellinear_min = the minimum RF power (dBm) referenced to that incident on the DUT input while testing over the linear range
# powerlevellinear_max = the maximum RF power (dBm) referenced to that incident on the DUT input while testing over the linear range
# maxpower = maximum power setting referenced to that incident on the DUT input (dBm) during the compression test.
# comp_fillin_step = power step size (dBm) to fill in input powers between powerlevellinear_max and maxpower. Note that maxpower>powerlevellinear_max
# powerlevel_step = the power stepsize (dBm) when measuring between powerlevellinear_min and powerlevellinear_max, i.e. the expected linear power region of the DUT



	# powerlevellinear_min is the lowest power setting at the DUT input, to measure the linear gain
	# powerlevellinear_max is the highest power setting at the DUT input, to measure the linear gain
	# powerlevel_step is the stepsize of the power at the DUT input, to determine linear gain
	# self._comp_step is the stepsize of the power sweep about the compression point to give a better-resolved compression characteristics curve (swept from self._powerlevellinear_max to self._maxpower in steps of self._comp_step)
	# self._maxpower is the maximum power at the DUT input, used to iterate to determine 1dB compression point
	# self._frequency is the frequency setting of the synthesizer
	# fractlinfitlower is the lower power point in terms of fraction of self._powerlevellinear_max-self._powerlevel_min that we fit the line to find the linear Pout vs Pin line. This line will be used to find the 1dB compression point
	# fractlinfitupper is the upper power point in terms of fraction of self._powerlevellinear_max-self._powerlevel_min that we fit the line to find the linear Pout vs Pin line. This line will be used to find the 1dB compression point
	# self.__rfAcalfactor = PDUTout-Psaread where PDUTout the power, at the DUT output, read by the power meter and then corrected for the probe loss and Psain is the power read on the spectrum analyzer display.
	# self._source_calibration_factor=PDUTin-PsynAset where PDUTin is the power at the DUT input, as read by the power meter and corrected for probe loss when synthesizer A is set to PsynAset and synthesizer B is off. self._source_calibration_factor is expected to be set to a negative dB quantity
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
class PowerCompressionTunedFocus(FocusTuner,HP438A):
	def __init__(self, rm=None, tunertype='load', calfactorA=97.6, calfactorB=97.55, source_calibration_factor=None, input_sensor_calfactor=None, loglin='LG', cascadefiles_port1=None, cascadefiles_port2=None,
	             powerlevellinear_min=None, powerlevellinear_max=None, maxpower=None, comp_fillin_step=None, powerlevel_step=None):
		#cascade available 2port networks onto ports 1 and 2 of the tuner
		# for x=1 or 2 (port 1 or 2 of tuner) cascadefile_portx[i][0] is the S-parameter full filename and  cascadefile_portx[i][1] is "flip" or "noflip". "flip" means to transpose ports 1 and 2 of the S-parameters read from the file
		S1=None
		S2=None
		if cascadefiles_port1!=None and len(cascadefiles_port1)>0:
			# add the first of the cascaded 2-ports to form S1 - the two-port attached to port 1 of the tuner
			if cascadefiles_port1[0][1]=='flip':   S1=spar_flip_ports(read_spar(cascadefiles_port1[0][0]))                      # exchange port 1 with port 2 of the two-port to be cascaded
			else:   S1=read_spar(cascadefiles_port1[0][0])
			del cascadefiles_port1[0]               # remove first 2-port file since its S-parameters have already been added to the first element of the cascade
			for c in cascadefiles_port1:            # c[0] is the S-parameter full filename and c[1] is "flip" or "noflip". "flip" means to transpose ports 1 and 2 of the S-parameters read from the file
				if c[1]=='flip': S1=cascadeSf(S1,spar_flip_ports(read_spar(c[0])))  # then flip ports 1 and 2 on this two-port and cascade it to form the two-port attached to port 1 of the tuner
				else: S1=cascadeSf(S1,read_spar(c[0]))                              # don't flip ports
		#cascade available 2port networks onto port2 of tuner
		if cascadefiles_port2!=None and len(cascadefiles_port2)>0:
			# add the first of the cascaded 2-ports to form S1 - the two-port attached to port 1 of the tuner
			if cascadefiles_port2[0][1]=='flip':   S2=spar_flip_ports(read_spar(cascadefiles_port2[0][0]))                      # exchange port 1 with port 2 of the two-port to be cascaded
			else:   S2=read_spar(cascadefiles_port2[0][0])
			del cascadefiles_port2[0]               # remove first 2-port file since its S-parameters have already been added to the first element of the cascade
			for c in cascadefiles_port2:            # c[0] is the S-parameter full filename and c[1] is "flip" or "noflip". "flip" means to transpose ports 1 and 2 of the S-parameters read from the file
				if c[1]=='flip': S2=cascadeSf(S2,spar_flip_ports(read_spar(c[0])))  # then flip ports 1 and 2 on this two-port and cascade it to form the two-port attached to port 1 of the tuner
				else: S2=cascadeSf(S2,read_spar(c[0]))                              # don't flip ports

		super(PowerCompressionTunedFocus,self).__init__(S1=S1,S2=S2,tunertype=tunertype)                    # initialize Focus tuner
		HP438A.__init__(self,rm=rm,calfactorA=calfactorA, calfactorB=calfactorB,loglin=loglin)           # set up power meter
		try: self.__rfA=Synthesizer(rm=rm,syn="A")            # synthesizer A should be the self.__rflow (lower frequency tone) because it has the high-accuracy attenuators
		except: raise ValueError("ERROR! No RF frequency synthesizer found!")
		self._comp_fillin_step=comp_fillin_step
		self.__rfA.off()							# turn off synthesizer
		self._powerlevellinear_min=powerlevellinear_min
		self._powerlevellinear_max=powerlevellinear_max
		self._powerlevel_step=powerlevel_step
		self._maxpower=maxpower
		self._source_calibration_factor=source_calibration_factor # dB difference between the power at the DUT's input (port 1) - as measured on the power meter, and the power setting on the RF synthesizer A. Almost always a negative dB number
		self._input_sensor_calfactor=input_sensor_calfactor     # dBm power at DUT input - dBm power read by the powermeter A

###################################################################################
# Find RF input power level which gives the DUT gain output compression specified by compressiontarget (usually 1dB)
# parameters:
#   fractlinfitlower, fractlinfitupper -> the lower and upper bounds of the least-squares linear fit to the output power vs input power in the uncompressed power level region - the linear fit is the DUT gain at small signal
#   compressiontarget is the amount of gain compression targeted by this measurement. e.g. if compresstarget=1, then return the input power level which produces 1dB gain compression in the DUT
#   maxcompressionlevelerror is the maximum deviation from the target compression point where measurement iterations are ended
#   output_reflection is the array of reflection coefficients mag,angle targets for the tuner reflection coefficient presented to the DUT output - output_reflection = [[mag1,angle1],[mag2,angle2],....]
#   frequency is the measurement frequency in MHz truncated to MHz
#   ps is the parameter analyzer handle. Assumes use of a Keithely 4200 parameter analyzer to supply DC bias
#   Vgs, Vds, draincomp, gatecomp, are respectively the gate voltage, drain voltage, drain current compliance limit (A), and gate current compliance limit (A)
	def measurePcomp(self,ps=None, fractlinfitlower=0.,fractlinfitupper=1.,compressiontarget=1.,maxcompressionlevelerror=0.1, powermeterfilterfactor=None,output_reflection=None,frequency=None,Vgs=0.,Vds=0.,draincomp=0.1,gatecomp=0.1,plotcompression=True,maxiterations=30):
		#maxiterations=2						# maximum allowed number of power iterations/point
		# compressiontarget is the target level of gain compression, maxcompressionlevelerror is the maximum error allowed between the compressiontarget and the actual power compression level
		if maxcompressionlevelerror<0.02: raise ValueError("maxcompressionlevelerror set too low")
		self.frequency=int(float(frequency))        # frequency in MHz, truncated to MHz
		self.compressiontarget=compressiontarget
		self.__rfA.off()							# turn off synthesizer
		self.__rfA.set_frequency(1E6*self.frequency)									        # set frequency of synthesizer in Hz

		self._toohighlevel=False														# warning flag for synthesizer level set too high and causing too much gain compression for an accurate gain
		self.Vgs=Vgs
		self.Vds=Vds
		self.draincomp=draincomp
		self.gatecomp=gatecomp
		#self._powermeterfilterfactor=powermeterfilterfactor
		# note that sourcecalfactor is the dB difference between the power meter measured power and that set on the rf synthesizer (A) = dB power meter - dB synthesizer setting (usually negative dB)
		# powerlevelsetlinear_min and powerlevelsetlinear_max define the linear range to test for small-signal gain
		powerlevelsetlinear_min=self._powerlevellinear_min-self._source_calibration_factor  			# powerlevelsetlinear_min is the lowest linear power direct setting used on the synthesizer it is the requested lowest power corrected by the losses from synthesizer to the DUT input. This is reference to the DUT input
		powerlevelsetlinear_max=self._powerlevellinear_max-self._source_calibration_factor			# powerlevelsetlinear_max is the highest linear power direct setting used on the synthesizer it is the requested highest power corrected by the losses from synthesizer to the DUT input. This is reference to the DUT input
		maxpowerset=self._maxpower-self._source_calibration_factor							# maximum power setting to calculate compression levels
		# make sure that the synthesizer maximum power level is leveled and OK
		#plevelmax=max(powerlevelsetlinear_max,self._maxpower)
		while self.__rfA.set_power(powerlevelsetlinear_max)=='unleveled': # power level setting is beyond the synthesizer's capability so reduce the maximum requested power
			powerlevelsetlinear_max=powerlevelsetlinear_max-1.1*self._powerlevel_step
			print ("Warning: powerlevelsetlinear_max: power beyond capability so reducing maximum power set at synthesizers to ", powerlevelsetlinear_max)
		while self.__rfA.set_power(maxpowerset)=='unleveled': # power level setting is beyond the synthesizer's capability so reduce the maximum requested power
			maxpowerset=maxpowerset-1.1*self._powerlevel_step
			print ("Warning: maxpowerset: power beyond capability so reducing maximum power set at synthesizers to ", maxpowerset)
			print ("Warning: maxpowerset: power beyond capability so reducing maximum power set at DUT input to ", maxpowerset+self._source_calibration_factor)
		print ("sourcecalfactor", self._source_calibration_factor)
		if maxpowerset<=powerlevelsetlinear_max+self._powerlevel_step: raise ValueError("ERROR: maximum power for linear measurements is too high or maximum power for compression measurement is too low")
		if int((fractlinfitupper-fractlinfitlower)*(powerlevelsetlinear_max-powerlevelsetlinear_min)/self._powerlevel_step)<2:	raise ValueError("ERROR: Check power level step size and fractions to fit line")
		# find DUT gain
		if ps!=None:    # then there is bias
			ps.fetbiason_topgate(Vgs=self.Vgs,Vds=self.Vds,draincomp=self.draincomp,gatecomp=self.gatecomp,timeiter=timeiterbias,maxchangeId=maxchangeId,maxtime=maxtime)       # turn on DUT bias
		self.__rfA.set_power(powerlevelsetlinear_min)																# turn on synthesizer to minimum power used in this test
		if self.readpower(sensor='A')<minreadablepower: raise ValueError("ERROR sensor A input: powerlevelsetlinear_min too low - below accurate reading capability of power sensor")
		if self.readpower(sensor='B')<minreadablepower: raise ValueError("ERROR sensor B output: powerlevelsetlinear_min too low - below accurate reading capability of power sensor")
		self.__rfA.set_power(powerlevelsetlinear_max)
		if self.readpower(sensor='A')>maxreadablepower: raise ValueError("ERROR sensor A input: powerlevelsetlinear_min too high - above accurate reading capability of power meter and could damage power sensor")
		if self.readpower(sensor='B')>maxreadablepower: raise ValueError("ERROR sensor B input: powerlevelsetlinear_min too high - above accurate reading capability of power meter and could damage power sensor")
		self.__rfA.set_power(maxpowerset)
		if self.readpower(sensor='A')>maxreadablepower: raise ValueError("ERROR sensor A input: maxpowerset too high - above accurate reading capability of power meter and could damage power sensor")
		if self.readpower(sensor='B')>maxreadablepower: raise ValueError("ERROR sensor B input: maxpowerset too high - above accurate reading capability of power meter and could damage power sensor")
		self.__rfA.off()
		self.gatestatusDUT={}
		self.drainstatusDUT={}
		self.tuner_loss={}
		self.actualrcoefMA={}   # actual reflection coefficient that the tuner presents to the DUT output magnitude, angle (degrees)
		self.actualrcoefRI={}   # actual reflection coefficient that the tuner presents to the DUT output real + jimaginary (complex
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
			retg=self.set_tuner_reflection(frequency=self.frequency,gamma=complex(ref[0],ref[1]),gamma_format='ma')     # set tuner reflection coefficient
			pos=retg['pos']             # tuner mechanical position in string format p1,p2 where p1 is the carriage position and p2 the slug position
			self.actualrcoefMA[pos]=retg['gamma_MA']                 # actual reflection coefficient of tuner at position pos (from S1+tuner+S2 using tuner calibration data) in magnitude+jangle
			self.actualrcoefRI[pos]=retg['gamma_RI']                # actual reflection coefficient of tuner at position pos in real+jimaginary
			self.tuner_loss[pos]=-10.*np.log10(retg['gain'])          # get tuner loss in dB (positive number)
			self.pDUTout[pos]={}
			self.IgDUT[pos]={}
			self.IdDUT[pos]={}
			self.drainstatusDUT[pos]={}
			self.gatestatusDUT[pos]={}
			###############################################################################################
			# measure DUT linear gain
			# power should be low enough that the gain is linear and not in compression
			pwrlinearsteps=np.arange(powerlevelsetlinear_min,powerlevelsetlinear_max+self._powerlevel_step,self._powerlevel_step)       # array of RF synthesizer direct power settings for linear regime testing. These are the powers set on the RF synthesizer and the actual power at the DUT input will be lower
			for plevelset in pwrlinearsteps:                # loop through input power levels (in linear regime)
				if "unleveled"==self.__rfA.set_power(plevelset): print ("Warning1: power at DUT: power beyond capability at ",plevelset+self._source_calibration_factor)
				pin=formatnum(self.readpower(sensor='A')+self._input_sensor_calfactor,precision=2,nonexponential=True)  # actual DUT input power, i.e. pin, used as key for data, resolution=0.1dB
				#pin=formatnum(plevelset+self._source_calibration_factor,precision=2,nonexponential=True)				# actual DUT input power, i.e. pin, used as key for data, resolution=0.1dB
				if ps!=None:    # then there is bias
					print("from compression_focus_tuned_with_powermeter.py line 196 pin dBm = ",pin)
					self.IdDUT[pos][pin],self.IgDUT[pos][pin],self.drainstatusDUT[pos][pin],self.gatestatusDUT[pos][pin] = ps.fetbiason_topgate(Vgs=self.Vgs,Vds=self.Vds,draincomp=self.draincomp,gatecomp=self.gatecomp,timeiter=timeiterbias,maxchangeId=maxchangeId,maxtime=maxtime)
					print("from compression_focus_tuned_with_powermeter.py line 198 pin dBm = ",pin)
				else:
					self.IdDUT[pos][pin]=0.
					self.IgDUT[pos][pin]=0.
					self.drainstatusDUT[pos][pin]=0.
					self.gatestatusDUT[pos][pin]=0.
				if self.gatestatusDUT[pos][pin]!='N' or self.drainstatusDUT[pos][pin]!='N': print("WARNING! gate or drain in compliance while finding small-signal gain")
				prf_uncorrected=self.readpower(sensor='B')     # get uncorrected RF DUT output power in dBm. This will be corrected by the tuner loss to arrive at the DUT output power
				self.pDUTout[pos][pin]=prf_uncorrected+self.tuner_loss[pos]    # DUT output RF power corrected for tuner loss (recall that the tuner includes all RF devices between the DUT and input of power sensor)
			# done measuring linear gain regime so find linear gain
			pinDUT=sorted([float(p) for p in self.pDUTout[pos].keys()])
			poutDUT=[self.pDUTout[pos][formatnum(p,precision=2)] for p in pinDUT]
			gainm,g,r=linfitendexclude(x=pinDUT,y=poutDUT,lowerfraction=fractlinfitlower,upperfraction=fractlinfitupper)			# find DUT output linear fit for the given tuner motor position and reflection coefficient - it is the Y intercept point
			self.DUTgain[pos]=np.average(np.subtract(poutDUT,pinDUT))       # find the DUT gain from the linear portion of the Pout vs Pin curve
			if max(np.subtract(self.DUTgain[pos],np.subtract(poutDUT,pinDUT)))>0.1:
				self._toohighlevel=True			# then the linear portion of this test is driving the DUT into compression by more than 0.1dB so we need to reduce the power levels
				print("WARNNING: power level too high - causing excessive gain compression for accurate gain measurement")
			# now have DUT linear gain so let's find the DUT input power to get the 1dB compression point
			############################ done measuring DUT over linear regime ############################################################
			compression=0.					# measured gain compression
			deltalinearpowersetting=self._powerlevel_step                     # this was the power level step used in the linear gain regime to measure the DUT linear gain
			plevelsethigh_compression=powerlevelsetlinear_max+2.*deltalinearpowersetting        # maximum RF source setting to search for compression point
			plevelsetlow_compression=powerlevelsetlinear_max                              # minimum RF source setting to search for compression point
			plevelset_compression=(plevelsetlow_compression+plevelsethigh_compression)/2.                   # start DUT input power search at plevelset_compression which is halfway between minimum and maximum search power values
			############# done finding DUT gain from linear portion of power curve ####################

			########## now find the compression point ###############
			iterations=0
			while compression<self.compressiontarget-maxcompressionlevelerror and abs(self.compressiontarget-compression)>maxcompressionlevelerror and iterations<=maxiterations:			# search to find power level where target gain compression is reached
				# measure gain compression (compression) at the high power level search limit to see if we need to increase this
				print("from compression_focus_tuned_with_powermeter.py line 229 gain compression dB and pin = ",compression,plevelset_compression+self._source_calibration_factor)
				iterations+=1
				if "unleveled"==self.__rfA.set_power(plevelsethigh_compression): print ("Warning2: power at DUT: power beyond capability at ",plevelsethigh_compression+self._source_calibration_factor)  # set initial RF synthesizer output to start at highest power level for compression measurement
				pDUTouthigh=self.readpower(sensor='B',filter=powermeterfilterfactor)+self.tuner_loss[pos]					# DUT output power level corrected for tuner loss (i.e. all RF 2-ports between DUT and power sensor losses are included in the tuner loss)
				pDUTinhigh= self.readpower(sensor='A',filter=powermeterfilterfactor)+self._input_sensor_calfactor   # DUT power input corrected for input circuit losses.
				gainatpowerpoint= pDUTouthigh-pDUTinhigh					                    # measured DUT gain at the set power level.
				compressionhigh=self.DUTgain[pos]-gainatpowerpoint									# compression is the difference between the gain at the power level point and the small-signal linear regime gain measured earlier
				if compressionhigh-maxcompressionlevelerror>=self.compressiontarget:						# then upper limit compresses so OK
					# measure gain compression (compression) at the low power level search limit and lower it if at or above requested gain compression
					if "unleveled"==self.__rfA.set_power(plevelsetlow_compression): print ("Warning3: power at DUT: power beyond capability at ",plevelsetlow_compression+self._source_calibration_factor)
					pDUToutlow=self.readpower(sensor='B',filter=powermeterfilterfactor)+self.tuner_loss[pos]											# DUT output power level corrected for tuner loss (i.e. all RF 2-ports between DUT and power sensor losses are included in the tuner loss)
					pDUTinlow=self.readpower(sensor='A',filter=powermeterfilterfactor)+self._input_sensor_calfactor     # get corrected RF DUT input power in dBm
					gainatpowerpoint=pDUToutlow-pDUTinlow
					compressionlow=self.DUTgain[pos]-gainatpowerpoint										# compression is the difference between the gain at the power level point and the small-signal gain measured earlier
					if compressionlow+maxcompressionlevelerror<=self.compressiontarget:						# then lower limit is not at requested compressesion so OK
						# Adjust power setting to find requested compression power point
						if "unleveled"==self.__rfA.set_power(plevelset_compression): print ("Warning4: power at DUT: power beyond capability at ",plevelset_compression+self._source_calibration_factor)
						pin=formatnum(self.readpower(sensor='A',filter=powermeterfilterfactor)+self._input_sensor_calfactor,precision=2,nonexponential=True)				# DUT measured input power, i.e. pin, used as key for data, resolution=0.1dB
						if ps!=None: # then there is bias
							self.IdDUT[pos][pin],self.IgDUT[pos][pin],self.drainstatusDUT[pos][pin],self.gatestatusDUT[pos][pin]=ps.fetbiason_topgate(Vgs=self.Vgs,Vds=self.Vds,draincomp=self.draincomp,gatecomp=self.gatecomp,timeiter=timeiterbias,maxchangeId=maxchangeId,maxtime=maxtime) # DUT bias on and/or read DUT currents
						else:
							self.IdDUT[pos][pin]=0.
							self.IgDUT[pos][pin]=0.
							self.drainstatusDUT[pos][pin]=0.
							self.gatestatusDUT[pos][pin]=0.
						if self.gatestatusDUT[pos][pin]!='N' or self.drainstatusDUT[pos][pin]!='N': print("WARNING! gate or drain in compliance while finding compression point")
						self.pDUTout[pos][pin]=self.readpower(sensor='B',filter=powermeterfilterfactor)+self.tuner_loss[pos]							# DUT output power level is the raw output power level corrected for errors and losses in the cabling and spectrum analyzer read errors
						gainatpowerpoint=self.pDUTout[pos][pin]- float(pin)			# DUT gain at the set power level. Input power = pin
						compression=self.DUTgain[pos]-gainatpowerpoint										# compression is the difference between the gain at the power level point and the small-signal gain, self.DUTgain[pos], measured earlier
						print("from compression_focus_tuned_with_powermeter.py line 261 gain compression dB = ",compression)
					# now set the rf synthesizer power level for the next iteration
						if compression<self.compressiontarget-maxcompressionlevelerror:
							plevelsetlow_compression=plevelset_compression
							plevelset_compression=(plevelsetlow_compression+plevelsethigh_compression)/2.										# binary search for the RF power level which gives the requested gain compression to within the requested error
						elif compression>self.compressiontarget+maxcompressionlevelerror:
							plevelsethigh_compression=plevelset_compression
							plevelset_compression=(plevelsetlow_compression+plevelsethigh_compression)/2.										# binary search for the RF power level which gives the requested gain compression to within the requested error
					else:
						plevelsetlow_compression=plevelsetlow_compression-deltalinearpowersetting								# lower power limit is too high (at or beyond specified compression) so decrease it
						if plevelsetlow_compression>maxpowerset: plevelsetlow_compression=plevelsetlow_compression-deltalinearpowersetting    # limit DUT input power to at or less than maxpowerset
				else:
					plevelsethigh_compression+=deltalinearpowersetting												# upper power level was still not driving into compression so increase it
					if plevelsethigh_compression>maxpowerset:
						plevelsethigh_compression=maxpowerset    # limit DUT input power to at or less than maxpowerset
						print("WARNING attempt to set plevelsethigh_compression>maxpowerset i.e. the maximum power allowed at the DUT input")
			######################## done finding compression point####################################################
			if iterations>maxiterations:
				print("WARNING! maximum number of iterations exceeded! No results given for Pcompression!",iterations)
				self.inputcompressionpoint[pos]=-9999.
				self.outputcompressionpoint[pos]=-9999.
			else:
				self.inputcompressionpoint[pos]=float(pin)
				self.outputcompressionpoint[pos]=self.pDUTout[pos][pin]
			################################################################################################################################################
			# If the sweep near the compression point is specified, find the power characteristics near the compression point to fill in the power compression characteristics about the compression point
			#
			if self._comp_fillin_step!=None and self._comp_fillin_step>0.1:       # sweep about compression point ONLY if the stepsize here is provided and legal
				pwrcompsteps=np.arange(powerlevelsetlinear_max, maxpowerset+self._comp_fillin_step,self._comp_fillin_step)
				for plevelset_compression in pwrcompsteps:
					#pin=formatnum(plevelset_compression+self._source_calibration_factor,precision=2,nonexponential=True)									# DUT input power
					if "unleveled"==self.__rfA.set_power(plevelset_compression): print ("Warning5: power at DUT: power beyond capability at ",plevelset_compression+self._source_calibration_factor)
					pin=formatnum(self.readpower(sensor='A',filter=powermeterfilterfactor)+self._input_sensor_calfactor,precision=2,nonexponential=True)				# DUT measured input power, i.e. pin, used as key for data, resolution=0.1dB
					if ps!=None:        # then there is bias
						self.IdDUT[pos][pin],self.IgDUT[pos][pin],self.drainstatusDUT[pos][pin],self.gatestatusDUT[pos][pin]= ps.fetbiason_topgate(Vgs=self.Vgs,Vds=self.Vds,draincomp=self.draincomp,gatecomp=self.gatecomp)
					else:
						self.IdDUT[pos][pin]=0.
						self.IgDUT[pos][pin]=0.
						self.drainstatusDUT[pos][pin]=0.
						self.gatestatusDUT[pos][pin]=0.
					if self.gatestatusDUT[pos][pin]!='N' or self.drainstatusDUT[pos][pin]!='N': print("WARNING! gate or drain in compliance while filling points out on compression")
					print("from line 302 in compression_focus_tuned_with_powermeter.py before read of power, pin= ",pin)
					self.pDUTout[pos][pin]=self.readpower(sensor='B',filter=powermeterfilterfactor)+self.tuner_loss[pos]                                           # DUT output power
					print("from line 305 in compression_focus_tuned_with_powermeter.py after read of power, pout= ",self.pDUTout[pos][pin])
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
# frequency is in MHz
# RFinputpower is the DUT input RF power in dBm
# output reflection is an array of arrays i.e. [[mag,angle],[mag,angle],.....] of the reflection coefficients to try on the output of the DUT
	def gain_vs_outputreflection(self,output_reflection=None,RFinputpower=-10.,frequency=None,powermeterfilterfactor=None,DUTSparfile=None):
		# loop through different output reflections set by the tuner on the DUT
		self.RFinputpower=RFinputpower
		self.frequency=frequency
		self.__rfA.set_frequency(1E6*self.frequency)									# set frequency of synthesizer
		self.actualrcoefMA={}    # actual reflection coefficient as set by tuner in magnitude and angle
		self.rfoutputlevel={}
		self.DUTgain={}
		self.tuner_loss={}
		self.tunergain50ohms={}                         # tuner gain in 50ohm system (to check system)
		if "unleveled"==self.__rfA.set_power(leveldBm=self.RFinputpower-self._source_calibration_factor):  print ("Warning1: power at DUT: power beyond capability at ",self.RFinputpower)
		self.__rfA.on()                                 # turn on synthesizer
		self.calcDUTgain={}
		self.calcDUTgain_from_cascade={}
		try: DUTSpar=read_spar(sparfilename=DUTSparfile)         # read DUT S-parameter files
		except: DUTSpar=None
		for ref in output_reflection:
			# set the tuner reflection coefficient presented to the DUT output
			retg=self.set_tuner_reflection(self.frequency,gamma=complex(ref[0],ref[1]),gamma_format='ma')      # frequency in MHz
			pos=retg['pos']             # tuner mechanical position in string format p1,p2 where p1 is the carriage position and p2 the slug position
			self.actualrcoefMA[pos]=retg['gamma_MA']            # actual reflection coefficient of tuner at position pos (from S1+tuner+S2 using tuner calibration data)
			Stuner=retg['Spar']      # tuner S-parameters
			self.tuner_loss[pos]=-10.*np.log10(retg['gain'])           # get tuner loss in dB (positive number)
			if DUTSpar!=None:
				DUTcascadetunerS=cascadeS(DUTSpar[str(int(self.frequency))],Stuner)
				self.calcDUTgain_from_cascade[pos]=20*np.log10(abs(DUTcascadetunerS[1,0]))+self.tuner_loss[pos]    # calculated DUT gain
				self.calcDUTgain[pos]=convertSRItoGt(S=DUTSpar[str(int(self.frequency))],gammaout=retg['gamma_RI'],dBout=True)    # calculated DUT gain in dB
			rfoutputlevel_uncorrected=self.readpower(sensor='B',filter=powermeterfilterfactor)                                                    # get uncorrected RF DUT output power in dBm
			self.rfoutputlevel[pos]=self.tuner_loss[pos]+rfoutputlevel_uncorrected
			measuredRFDUTinputpower=self.readpower(sensor='A',filter=powermeterfilterfactor)+self._input_sensor_calfactor
			self.DUTgain[pos]=self.rfoutputlevel[pos]-measuredRFDUTinputpower             # DUT gain measured at the given RF input power and frequency
			self.tunergain50ohms[pos]=20*np.log10(abs(retg['Spar'][1,0]))                     # tuner gain dB in a 50ohm system
			print("reflection "+str(self.actualrcoefMA[pos])+" RF output raw dBm "+str(rfoutputlevel_uncorrected)+" RF output raw-tunergain50ohms "+str(rfoutputlevel_uncorrected-self.tunergain50ohms[pos]))
		self.__rfA.off()                # turn off RF generator
###################################################################################################################
########################################################################################################################################################################################################################################################
	# Search for optimum reflection presented to DUT which maximizes the compression point (usually 1dB compression point)
	# all data are saved to be plotted later
	# initial output reflections are the list of reflections, magnitude and angle, presented to the DUT prior to performing the search. These initial values provide a sample sufficient to perform the search by
	# performing a cubic spline and finding the maximum output Pcomp from the cubic spline interpolation AFTER the Pcomp values have been measured at all the initial_output_reflections points.
	# the stopping_criteria is the dB improvement that must be made in the last step to continue the search. Search stops when the next optimum interpolated point is: interpolated optimum point < last measured optimum + stopping_criteria
	# the maximum_reflection is the maximum reflection coefficient magnitude available from the tuner at the DUT output
	# method not ready to use yet!!
	# def Pcompsearch(self,initial_output_reflections=None,fractlinfitlower=0.,fractlinearfitupper=1.,compressiontarget=1.,maxcompressionlevelerror=0.1, powermeterfilterfactor=None,output_reflection=None,frequency=None,Vgs=0.,Vds=0.,draincomp=0.1,gatecomp=0.1,plotcompression=True,maxiterations=30):
	# 	nopts=200       # number of points in real and imaginary reflection coefficient on the Smith chart
	# 	deltagamma=.1     # length of the extrapolation vector of the reflection coefficient when searching outside the tested values of reflection coefficient for the maximum Pcomp
	# 	deltaPcompstopcriterian=0.2           # stop search when the current interpolated Pcomp is within deltaPcompstopcriterian dBm of the last interpolated Pcomp
	# 	minreflection=-1.
	# 	maxreflection=1.
	# 	Pcompmaxintlast=-999999            # interpolated maximum Pcomp (dBm)from last set of measurements set to big initial number to get at least one interation
	# 	self.Pcompmaxint=-9999
	# 	#deltagammai=int(deltagamma*nopts/(maxreflection-minreflection))            # number of index points in the reflection used to distance the new points which are outside the ICP (interpolated constellation polygon)
	# 	digamma=(maxreflection-minreflection)/nopts                                  # change in gamma/index point
	# 	gamma_outofICP=-9999999  # fill value for griddata interpolation for reflections outside the convex polygon formed by the reflection data plotted on the Smith chart. This is set very negative soas to always be the smallest value and produce the proper search
	#
	# 	gamma_to_measure=initial_output_reflections        # new gamma points to be measured, start with initial points specified in calling this method
	# 	gamma_measured=[]            # gamma points already measured
	# 	outputPcomp_average=[]        # measured output Pcomp (dBm) already measured
	# 	# loop to find output reflection coefficient which gives highest IOP3 average
	# 	while self.Pcompmaxint>deltaPcompstopcriterian+Pcompmaxintlast:                 # loop at least once and stop when there is no significant improvement in the interpolated Pcomp
	# 		Pcompmaxintlast=self.Pcompmaxint
	# 		self.measurePcomp(output_reflection=gamma_to_measure,fractlinfitlower=fractlinfitlower,fractlinfitupper=fractlinearfitupper,compressiontarget=compressiontarget,
	# 		                  maxcompressionlevelerror=maxcompressionlevelerror,powermeterfilterfactor=powermeterfilterfactor,frequency=frequency,Vgs=Vgs,Vds=Vds,draincomp=draincomp,
	# 		                  gatecomp=gatecomp,plotcompression=plotcompression,maxiterations=maxiterations)       # measure compression point at output reflection points to establish a search surface
	# 		del gamma_to_measure
	# 		gamma_to_measure=[]
	# 		for p in self.actualrcoefRI.keys():				# convert actual reflection coefficient and average between high and low sideband TOI to arrays from dictionaries
	# 			gamma_measured.append(self.actualrcoefRI[p])    # self.actualrcoefRI[p] is the actual reflection coefficient at tuner position p from self.measureTOI()
	# 			outputTOI_average.append(self.TOIavg[p])        # self.TOIavg[p] is the actual output averaged third order intercept point at tuner position p from self.measureTOI()
	# 															# average TOI (average of lower-frequency 3rd order product TOI and upper-frequency third order product measured) in recently-measured TOI in dBm,
	# 															# associated with the reflection coefficients in self.actualrcoefRI[] (type dictionary)
	# 		gamma_real_int = np.linspace(minreflection, maxreflection, nopts)  # real reflection coefficient on the interpolated grid
	# 		gamma_imag_int = np.linspace(minreflection, maxreflection,nopts)  # imaginary reflection coefficient on the interpolated grid
	# 		# 2D cubic spline interpolation (x,y,z) z=self._paraplotint[ii,ir] where ii is the imaginary index and ir the real index find the ICP (interpolated constellation polygon)
	# 		print("from line 110 in IP3_focus_tuned.py size of gamma_measured, outputTOI", len(gamma_measured),len(outputTOI_average) )
	# 		self._TOIfit = griddata((np.real(gamma_measured),np.imag(gamma_measured)), outputTOI_average,(gamma_real_int[None,:], gamma_imag_int[:,None]),method='cubic',fill_value=gamma_outofICP)
	# 		iiopt,iropt=uind(self._TOIfit.argmax(),self._TOIfit.shape)    # find indices ii, ir, (imaginary rho, real rho) corresponding to highest average output INTERPOLATED TOI.
	# 		self.TOImaxint=self._TOIfit[iiopt,iropt]     # maximum interpolated TOI from current dataset
	# 		del gamma_measured
	# 		if self.TOImaxint>deltaPcompstopcriterian+TOImaxintlast:               # perform calculations only if not done with search
	# 			gammaopt_int=complex(gamma_real_int[iropt],gamma_imag_int[iiopt])               # complex gamma which maximizes interpolated TOI
	# 			# is the optimum reflecton coefficient at or near the edge of the ICP? If so, we need to test up to 4 more gamma points i.e. west, east, north, and south of the interpolated optimum gamma, excepting those points that are within the ICP
	# 			if  self._TOIfit[iiopt,iropt-1]==gamma_outofICP or self._TOIfit[iiopt-1,iropt]==gamma_outofICP or  self._TOIfit[iiopt,iropt+1]==gamma_outofICP or self._TOIfit[iiopt+1,iropt]==gamma_outofICP:   # is the optimum interpolated reflection coefficient at the edge of the ICP?
	# 				# optimum interpolated reflection coefficient is outside the ICP so produce up to four new measurement points outside the ICP (usually no more than three new points)
	# 				if -deltagamma < min(-gammaopt_int.real-np.sqrt(np.square(gammaopt_int.real)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))), -gammaopt_int.real+np.sqrt(np.square(gammaopt_int.real)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int)))):
	# 					deltagamma_realneg = min(-gammaopt_int.real-np.sqrt(np.square(gammaopt_int.real)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))), -gammaopt_int.real+np.sqrt(np.square(gammaopt_int.real)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))))
	# 				else: deltagamma_realneg=-deltagamma
	# 				if deltagamma > max(-gammaopt_int.real-np.sqrt(np.square(gammaopt_int.real)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))), -gammaopt_int.real+np.sqrt(np.square(gammaopt_int.real)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int)))):
	# 					deltagamma_realpos = max(-gammaopt_int.real-np.sqrt(np.square(gammaopt_int.real)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))), -gammaopt_int.real+np.sqrt(np.square(gammaopt_int.real)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))))
	# 				else: deltagamma_realpos=deltagamma
	# 				if -deltagamma < min(-gammaopt_int.imag-np.sqrt(np.square(gammaopt_int.imag)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))), -gammaopt_int.imag+np.sqrt(np.square(gammaopt_int.imag)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int)))):
	# 					deltagamma_imagneg = min(-gammaopt_int.imag-np.sqrt(np.square(gammaopt_int.imag)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))), -gammaopt_int.imag+np.sqrt(np.square(gammaopt_int.imag)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))))
	# 				else: deltagamma_imagneg=-deltagamma
	# 				if deltagamma > max(-gammaopt_int.imag-np.sqrt(np.square(gammaopt_int.imag)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))), -gammaopt_int.imag+np.sqrt(np.square(gammaopt_int.imag)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int)))):
	# 					deltagamma_imagpos = max(-gammaopt_int.imag-np.sqrt(np.square(gammaopt_int.imag)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))), -gammaopt_int.imag+np.sqrt(np.square(gammaopt_int.imag)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))))
	# 				else: deltagamma_imagpos=deltagamma
	# 				# now find corresponding delta indicies for new gammas to test and also the new gammas themselves
	# 				# exclude the gamma points which lie within the ICP
	# 				i_realneg=iropt+int(deltagamma_realneg/digamma)             # real index point of west gamma point to test
	# 				i_realpos=iropt+int(deltagamma_realpos/digamma)             # real index point of east gamma point to test
	# 				i_imagneg=iropt+int(deltagamma_imagneg/digamma)             # imaginary index point of south gamma point to test
	# 				i_imagpos=iropt+int(deltagamma_imagpos/digamma)             # imaginary index point of north gamma point to test
	#
	# 				if self._TOIfit[iiopt,i_realneg]==gamma_outofICP:   # is west gamma outside the ICP? If so, add it to the gammas to be tested for TOI
	# 					westgamma=complex(gamma_real_int[i_realneg],gamma_imag_int[iiopt])      # complex west gamma
	# 					westgammaMA=convertRItoMA(westgamma)                    # magnitude+jangle
	# 					gamma_to_measure.append([westgammaMA.real,westgammaMA.imag])
	#
	# 				if self._TOIfit[iiopt,i_realpos]==gamma_outofICP:   # is east gamma outside the ICP? If so, add it to the gammas to be tested for TOI
	# 					eastgamma=complex(gamma_real_int[i_realpos],gamma_imag_int[iiopt])      # complex west gamma
	# 					eastgammaMA=convertRItoMA(eastgamma)                    # magnitude+jangle
	# 					gamma_to_measure.append([eastgammaMA.real,eastgammaMA.imag])
	#
	# 				if self._TOIfit[i_imagneg,iropt]==gamma_outofICP:   # is south gamma outside the ICP? If so, add it to the gammas to be tested for TOI
	# 					southgamma=complex(gamma_real_int[iropt],gamma_imag_int[i_imagneg])      # complex south gamma
	# 					southgammaMA=convertRItoMA(southgamma)                    # magnitude+jangle
	# 					gamma_to_measure.append([southgammaMA.real,southgammaMA.imag])
	#
	# 				if self._TOIfit[i_imagpos,iropt]==gamma_outofICP:   # is north gamma outside the ICP? If so, add it to the gammas to be tested for TOI
	# 					northgamma=complex(gamma_real_int[iropt],gamma_imag_int[i_imagpos])      # complex north gamma
	# 					northgammaMA=convertRItoMA(northgamma)                    # magnitude+jangle
	# 					gamma_to_measure.append([northgammaMA.real,northgammaMA.imag])
	# 			# also add the reflection coefficient at the interpolated maximum of TOI to the reflections to be measured i.e. gamma[]
	# 			# remember that gammaopt_int is interpolated reflection coefficient (real+jimaginary) where the interpolated TOI is a maximum
	# 			# so add this reflection coefficient to that to measure
	# 			gammaopt_intMA=convertRItoMA(gammaopt_int)      # convert the interpolated optimum reflection coefficient from real+jimaginary  to [magnitude+jangle]
	# 			gamma_to_measure.append([gammaopt_intMA.real,gammaopt_intMA.imag])         # add it to the gammas to measured. Note that this will be the ONLY gamma to measure if the optimum interpolated gamma is within the ICP
	# 			print("from line 163 in IP3_focus_tuned.py gamma_to_measure",gamma_to_measure)
	# 	return self.TOImaxint, gammaopt_intMA
########################################################################################################################################################################################################################################################
	# write power compression data to file
	writefile_Pcompression_tuned=X_writefile_Pcompression_tuned
	writefile_Pgain=X_writefile_Pgain
#####################################################################################################################