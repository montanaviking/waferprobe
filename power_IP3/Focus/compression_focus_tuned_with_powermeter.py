# measures 1dB compression point at a single tone using the spectrum analyzer to measure power
# uses power meter with two sensors to read input and output power
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

# see /carbonics/owncloudsync/documents/code_documentation/software_development/measurement_software_TOI.odp for test layout
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
DUTinputsensor='A'
DUToutputsensor='B'
#navg_fundamental=2      # number of averages used by the spectrum analyzer to read the RF power level
spanfund=1.             # frequency span in MHz for spectrum analyzer power measurments
minimumpowermetermeasurement=-25.   # dBm lower limit of raw accurate power meter measurements
maximuminputpowermetermeasurement=20.   # dBm upper limit of raw accurate power meter measurements
maximumoutputpowermetermeasurement=13.5   # dBm upper limit of raw accurate power meter measurements 13.5dBm with LNA
maxrefleveladjusttries=10

# minreadablepower=-35.0          # minimum RF power that is readable by the power meter
# maxreadablepower=20.0          # minimum RF power that is readable by the power meter
class PowerCompressionTunedFocus(FocusTuner,HP438A):
	def __init__(self,rm=None,sa=None,tunertype='load',calfactorA=97.6,calfactorB=97.7,loglin='LG',cascadefiles_port1=None,cascadefiles_port2=None,spectrum_analyzer_cal_factor=None,frequency=None,
				 source_calibration_factor=None, minpower=None,maxpower=None,comp_fillin_step=None,steppower=None,estimated_gain=-10, synthesizerpowersetmaximum=0,synthesizerpowersetforcalibration=-10):
		self._sacalfactor=spectrum_analyzer_cal_factor # dB difference between the tuner output (port 2) (as measured by the power meter) and the spectrum analyzer level. This takes into account the loss between the tuner port 2 (output) and the spectrum analyzer as well as calibration of the spectrum analyzer display
		self.frequency=int(float(frequency))        # synthesizer frequency in MHz
		self.__sa=sa                                # spectrum analyzer handle
		self._reflevelgaincorrection=0.
		self._estimated_gain=estimated_gain
		self.synthesizerpowersetmaximum=synthesizerpowersetmaximum
		self.synthesizerpowersetforcalibration=synthesizerpowersetforcalibration
		print("using compression_focus_tuned_with_powermeter.py version July 24, 2018")
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
				else: S1=cascadeSf(S2,read_spar(c[0]))                              # don't flip ports

		super(PowerCompressionTunedFocus,self).__init__(S1=S1,S2=S2,tunertype=tunertype)                    # initialize Focus tuner
		HP438A.__init__(self,rm=rm,calfactorA=calfactorA, calfactorB=calfactorB,loglin=loglin)           # set up power meter
		try: self.__rfA=Synthesizer(rm=rm,syn="A",maximumpowersetting=synthesizerpowersetmaximum)            # synthesizer A should be the self.__rflow (lower frequency tone) because it has the high-accuracy attenuators
		except: raise ValueError("ERROR! No RF frequency synthesizer found!")
		self._comp_fillin_step=comp_fillin_step
		self.__rfA.off()							# turn off synthesizer
		self._steppower=steppower   # power step used in the initial power sweep
		self._minpower=minpower     # maximum DUT input power during compression test - in compression regime this is the absolute minimum ever applied to the DUT input
		self._maxpower=maxpower     # maximum DUT input power during compression test this is the absolute maximum ever applied to the DUT input
		self._sourcecalfactor=source_calibration_factor # dB difference between the power at the DUT's input (port 1) - as measured on the power meter, and the power setting on the RF synthesizer A. Almost always a negative dB number
		#self._outputpowermetercalfactor=output_calibration_factor # dB difference between the output power meter - the output power at the composite tuner output port 2. This accounts for the loss of the coupler port and the gain of the amplifier on that port prior to the output power sensor
		#self._syn_settingtometer_input=None				# power sensor measurement on the RF synthesizer (dB) - RF synthesizer power setting (dB), initialized via first call to __setDUTinputpower()
		self.__rfA.set_frequency(1E6*self.frequency)									        # set frequency of synthesizer in Hz
		self.__findsourceinputcalibrationfactor()
		if sa!=None:        # we are using the spectrum analyzer to read DUT output power
			self.__sa.set_autoresolutionbandiwidth('y')
			self.__sa.set_autovideobandiwidth('y')
			self.__sa.set_numberaverages(32)
			self.__sa.set_referencelevel(-150.)
			f,nf=self.__sa.measure_spectrum(centfreq=1E6*self.frequency,span=1E6*spanfund,returnspectrum=False)       # read spectrum analyzer noise level
			self._noisefloor=np.average(nf)
			self.__sa.set_referencelevel(10.)
##################################################################################################################################################################################################################################
# find self._settingcal =PinDUT-Psetting where PinDUT is the actual power at the input of the DUT and Psetting is the synthesizer power setting. This allows setting of the synthesizer power to get a PinDUT, as Psetting=PinDUT-self._settingcal
# This finds the above using: self._settingcal = self._sourcecalfactor+powermeter reading - power setting of  the synthesizer
# where the powermeter reading refers to the powermeter coupled to the input DUT port.
# the self._sourcecalfactor = source_calibration_factor = (dB) is the actual power at the DUT input - that measured at the power sensor connected to the coupler at the input side of the DUT
# this method produces the calibration factors: self._settingcallowerfreq and self._settingcalupperfreq calibration factors as described above
# assumes that the RF synthesizer frequency has been set
	def __findsourceinputcalibrationfactor(self):
		# turn off synthesizer
		self.__rfA.off()
		if 'unleveled'==self.__rfA.set_power(self.synthesizerpowersetforcalibration):              # set 0dBm on lower-frequency RF source to calibrate its power output
			raise ValueError("ERROR from __findsourceinputcalibrationfactors ! attempt to set lower frequency RF synthesizer above power level at which the power is calibrated")
		powersensorraw=self.readpower(sensor=DUTinputsensor)
		if powersensorraw<minimumpowermetermeasurement: raise ValueError("ERROR! power sensor reading too low in __findsourceinputcalibrationfactor(). Need to increase synthesizer power synthesizerpowersetforcalibration")
		powersetting=self.__rfA.get_power()
		self._settingcal=self._sourcecalfactor+powersensorraw-powersetting  # get source calibration factor = PinDUT-Psettinglower
######################################################################################################################################################################################################################################
##################################################################################################################################################################################################################################
# Sets the RF power referred to the DUT input for the selected RF synthesizer
# return: actual power referred to the DUT input = self.
# Inputs:
# self._settingcal: is frequency source calibration factor = PinDUT-Psetting in dB where PinDUT is the desired RF lower tone power at the DUT input. Determined from automated measurement in __findsourceinputcalibrationfactors()
# self._sourcecalfactor: is the PinDUT-Ppowermeter in dB which was measured manually during system characterization
# assumes that the RF synthesizer frequency has been set and that the power meter is calibrated and has the correct calibration factor set
	def __setDUTinputpower(self,pinDUT=None,on=True):
		maxloopdberror=0.05
		#self.__rfA.off()
		powersetting=pinDUT-self._settingcal
		if 'unleveled'==self.__rfA.set_power(powersetting):              # set 0dBm on lower-frequency RF source to calibrate its power output
			print("WARNING from __findsourceinputcalibrationfactors ! unleveled! attempt to set lower frequency RF synthesizer above power level at which the power is calibrated")
		settingcal=9999999999999.          # ensure that loop runs at least once
		noloops=0
		while abs(settingcal-self._settingcal)>maxloopdberror and noloops<=maxloopdberror:
			noloops+=1
			powerDUTinputsensor=self.readpower(sensor=DUTinputsensor)           # read input sensor powermeter - raw uncorrected power data
			if powerDUTinputsensor<minimumpowermetermeasurement:
				print(" input power meter raw data = ",powerDUTinputsensor)
				print("WARNING!  power meter A level too low for input power meter")
			if powerDUTinputsensor>maximuminputpowermetermeasurement:
				print(" input power meter raw data = ",powerDUTinputsensor)
				print("WARNING!  power meter A level too low for input power meter")
			settingcal=self._sourcecalfactor+powerDUTinputsensor-self.__rfA.get_power()
			print("settingcal-self._settingcal = ",settingcal-self._settingcal)
			if abs(settingcal-self._settingcal)>maxloopdberror:
				print("WARNING self._settingcal is being corrected")
				self._settingca=settingcal
		PDUTinputmeasured=self._sourcecalfactor+powerDUTinputsensor             # Corrected input DUT power level
		# leave RF synthesizer in off state
		if not on: self.__rfA.off()         # leave in off state if this is requested
		return PDUTinputmeasured        # dBm
######################################################################################################################################################################################################################################q)        # use readings to continuously re-calibrate)
######################################################################################################################################################################################################################################
	# read power at tuner output port (dBm) or input of spectrum analyzer.
	# reads the output power sensor to find the RF output power of the selected fundamental at the output of the composite tuner. The actual DUT output power must be calculated by removing the loss of the composite tuner
	# Input is self._outpowercalfactor = dB difference between the output power meter - the output power at the composite tuner output port 2. This accounts for the loss of the coupler port and the gain of the amplifier on that port prior to the output power sensor
	def __readDUToutputpower(self):
		prf_last=-99999999
		prf=9999999
		niter=0
		nitermax=20
		while abs(prf-prf_last)>0.1:
			niter+=1
			if niter>nitermax: raise ValueError("ERROR! too many iterations while trying to stabilize output power")
			print("from line 170 in compression_focus_tuned_with_powermeter.py iteration of measurement of output fundamental ",niter)
			if self.__sa!=None:            # we are using the spectrum analyzer to measure output power and not the powermeter
				self.__sa.set_autoresolutionbandiwidth('y')
				self.__sa.set_autovideobandiwidth('y')
				reftries=0
				reflevelOK=False
				self.__sa.set_numberaverages(2)            # set up spectrum analyzer averages to read fundamental RF power levels
				while reftries<maxrefleveladjusttries and not reflevelOK:      #loop to find reference level which doesn't saturate spectrum analyzer input
					reflevelOK=True
					try: frf,prf=self.__sa.measure_spectrum(centfreq=1E6*self.frequency,span=1E6*spanfund,returnspectrum=False)     #measure lower fundamental of two tone input
					except:
						reflevelOK=False
						self._reflevelgaincorrection+=10.                       # increment reference level by 10dB to try to get spectrum analyzer out of saturation
						self.__sa.set_referencelevel(self._reflevelgaincorrection+self._estimated_gain)
						reftries+=1
				if reftries>=maxrefleveladjusttries: raise ValueError("ERROR! could not get spectrum analyzer out of input saturation")
				if prf<10.+self.noisefloor:  raise ValueError("ERROR! not enough RF power into spectrum analyzer to accurately measure")
			else: # using power meter
				prf=self.readpower(sensor=DUToutputsensor)  # read the raw RF power at the output of the composite tuner coupler
				if prf>maximumoutputpowermetermeasurement:
					print("output power too high raw power = ",prf)
					raise ValueError("ERROR! output power meter raw data too high for good measurement")
				if prf<minimumpowermetermeasurement:
					print("output power too low raw power = ",prf)
					#raise ValueError("ERROR! not enough RF power into output power meter to accurately measure")
			prf_last=prf
		return prf      # composite tuner output power in dBm
########################################################################################################################################################################################################################################################
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
#   self._maxpower=maximum DUT input power during compression test
#
	def measurePcomp(self,ps=None,compressiontarget=1.,maxcompressionlevelerror=0.1,output_reflection=None,Vgs=0.,Vds=0.,draincomp=0.1,gatecomp=0.1):
		if maxcompressionlevelerror<0.02: raise ValueError("maxcompressionlevelerror set too low")
		#self.frequency=int(float(frequency))        # frequency in MHz, truncated to MHz
		self.compressiontarget=compressiontarget
		self.__rfA.off()							# turn off synthesizer
		self.__rfA.set_frequency(1E6*self.frequency)									        # set frequency of synthesizer in Hz

		self._toohighlevel=False														# warning flag for synthesizer level set too high and causing too much gain compression for an accurate gain
		self.Vgs=Vgs
		self.Vds=Vds
		self.draincomp=draincomp
		self.gatecomp=gatecomp

		if self._maxpower<=self._minpower+self._steppower: raise ValueError("ERROR: maximum power for linear measurements is too high or maximum power for compression is too low")
		if int((self._maxpower-self._minpower)/self._steppower)<2:	raise ValueError("ERROR: Check power level step size to fit line")
		# find DUT gain
		# first deternmine if the minimum power setting we'll use during this measurement is above the minimum which can be accurately read
		if ps!=None:    # then there is bias
			ps.fetbiason_topgate(Vgs=self.Vgs,Vds=self.Vds,draincomp=self.draincomp,gatecomp=self.gatecomp,timeiter=timeiterbias,maxchangeId=maxchangeId,maxtime=maxtime)       # turn on DUT bias
		prfmin=self.__setDUTinputpower(pinDUT=self._minpower)
		if prfmin<minreadablepower:
			print("prfmin =",prfmin)
			raise ValueError("ERROR: powerlevelset_min too low - below accurate reading capability of power sensor A")
		elif prfmin>maxreadablepower:
			print("prfmin =",prfmin)
			raise ValueError("ERROR: powerlevelset_min too high - above accurate reading capability of power sensor A and could damage power sensor")
		prfmax=self.__setDUTinputpower(pinDUT=self._maxpower)
		if prfmax<minreadablepower:
			print("prfmax =",prfmax)
			raise ValueError("ERROR: powerlevelset_max too low - below accurate reading capability of power sensor A")
		elif prfmax>maxreadablepower:
			print("prfmax =",prfmax)
			raise ValueError("ERROR: powerlevelset_max too high - above accurate reading capability of power sensor A and could damage power sensor")

		self.gatestatusDUT={}
		self.drainstatusDUT={}
		self.tuner_loss={}
		self.actualrcoefMA={}   # actual reflection coefficient that the tuner presents to the DUT output magnitude, angle (degrees)
		self.actualrcoefRI={}   # actual reflection coefficient that the tuner presents to the DUT output real + jimaginary (complex
		self.IgDUT={}
		self.IdDUT={}
		self.DUTgain={}
		self.gainvspin={}
		self.gainvspinspline={}
		self.pDUTout={}
		self.pin_spline={}
		self.pout_spline={}
		self.inputcompressionpoint={}
		self.outputcompressionpoint={}
		self.noisefloor={}
		################################
		# loop through select load tuner positions of which each corresponds to a tuner reflection presented to the DUT output (load pull)
		for ref in output_reflection:
			retg=self.set_tuner_reflection(frequency=self.frequency,gamma=complex(ref[0],ref[1]),gamma_format='ma')
			pos=retg['pos']             # tuner mechanical position in string format p1,p2 where p1 is the carriage position and p2 the slug position
			self.actualrcoefMA[pos]=retg['gamma_MA']                 # actual reflection coefficient of tuner at position pos (from S1+tuner+S2 using tuner calibration data) in magnitude+jangle
			self.actualrcoefRI[pos]=retg['gamma_RI']                # actual reflection coefficient of tuner at position pos in real+jimaginary
			self.tuner_loss[pos]=-10.*np.log10(retg['gain'])          # get tuner loss in dB (positive number) with pos as the tuner motor positions used as a key for this dictionary
			self.pDUTout[pos]={}                                    # DUT output RF power (dBm) dictionary with tuner position and DUT input power [pos][pin] as keys
			self.IgDUT[pos]={}
			self.IdDUT[pos]={}
			self.pin_spline[pos]=[]
			self.pout_spline[pos]=[]
			self.drainstatusDUT[pos]={}
			self.gatestatusDUT[pos]={}
			self.gainvspin[pos]=[]
			self.gainvspinspline[pos]=[]
			###############################################################################################
			# initial DUT power sweep
			pwrsteps=np.arange(self._minpower,self._maxpower+self._steppower,self._steppower)       # array of power settings referred to DUT input.
			if len(pwrsteps)<3: raise ValueError("ERROR! not enough power steps!")
			for plevelset in pwrsteps:                # loop through input power levels (in linear regime)
				pDUTin=self.__setDUTinputpower(plevelset)
				pin=formatnum(pDUTin,precision=2,nonexponential=True)				# pDUTin is the actual DUT input power (dBm), pin, used as key for data, resolution=0.1dB is the DUT input power in string form to use for keys in the dictionary
				if ps!=None:    # then there is bias
					print("from compression_focus_tuned.py line 262 pin dBm = ",pin)
					self.IdDUT[pos][pin],self.IgDUT[pos][pin],self.drainstatusDUT[pos][pin],self.gatestatusDUT[pos][pin] = ps.fetbiason_topgate(Vgs=self.Vgs,Vds=self.Vds,draincomp=self.draincomp,gatecomp=self.gatecomp,timeiter=timeiterbias,maxchangeId=maxchangeId,maxtime=maxtime)
					print("from compression_focus_tuned.py line 264 pin dBm = ",pin)
					if self.gatestatusDUT[pos][pin]!='N' or self.drainstatusDUT[pos][pin]!='N': print("WARNING! gate or drain in compliance while finding small-signal gain")
				else:
					self.IdDUT[pos][pin]=0.
					self.IgDUT[pos][pin]=0.
					self.drainstatusDUT[pos][pin]=0.
					self.gatestatusDUT[pos][pin]=0.
				self.pDUTout[pos][pin]=self.__readDUToutputpower()+self.tuner_loss[pos]       # actual deembededDUT output RF power corrected for tuner loss (recall that the tuner includes all RF devices between the DUT and input of power sensor
			# sort poutDUT and pinDUT in ascending pinDUT order
			pinDUTsortedasc=[p for p in self.pDUTout[pos].keys()]
			pinDUTsortedasc.sort(key=float)
			pinDUT=[float(p) for p in pinDUTsortedasc]
			poutDUT=[self.pDUTout[pos][p] for p in pinDUTsortedasc]
			# average gain over lowest 3 points of PinDUT to estimate small signal gain to find compression point
			avggain=np.average([poutDUT[i]-pinDUT[i] for i in range(0,3)])
			self.DUTgain[pos]=avggain
			if poutDUT[-1]-pinDUT[-1]<1.5*compressiontarget:
				print("WARNING! maximum power too low, need to increase maximum power to get sufficient gain compression")
			# now find the first point in compression
			compression=avggain-(poutDUT[-1]-pinDUT[-1])
			pwrsteps=np.arange(pinDUT[-1],pinDUT[2],-self._comp_fillin_step)
			# fill in power points to provide finer resolution about the compression point
			i=0
			while(compression>compressiontarget and i<len(pwrsteps)):
				pDUTin=self.__setDUTinputpower(pwrsteps[i])
				pin=formatnum(pDUTin,precision=2,nonexponential=True)
				if ps!=None:    # then there is bias
					print("from compression_focus_tuned.py line 262 pin dBm = ",pin)
					self.IdDUT[pos][pin],self.IgDUT[pos][pin],self.drainstatusDUT[pos][pin],self.gatestatusDUT[pos][pin] = ps.fetbiason_topgate(Vgs=self.Vgs,Vds=self.Vds,draincomp=self.draincomp,gatecomp=self.gatecomp,timeiter=timeiterbias,maxchangeId=maxchangeId,maxtime=maxtime)
					print("from compression_focus_tuned.py line 264 pin dBm = ",pin)
					if self.gatestatusDUT[pos][pin]!='N' or self.drainstatusDUT[pos][pin]!='N': print("WARNING! gate or drain in compliance while finding small-signal gain")
				else:
					self.IdDUT[pos][pin]=0.
					self.IgDUT[pos][pin]=0.
					self.drainstatusDUT[pos][pin]=0.
					self.gatestatusDUT[pos][pin]=0.
				self.pDUTout[pos][pin]=self.__readDUToutputpower()+self.tuner_loss[pos]       # actual deembededDUT output RF power corrected for tuner loss (recall that the tuner includes all RF devices between the DUT and input of power sensor
				compression=avggain-(self.pDUTout[pos][pin]-pDUTin)
				i+=1
			# sort poutDUT and pinDUT in ascending pinDUT order
			pinDUTsortedasc=[p for p in self.pDUTout[pos].keys()]           # string data type Pin are dictionary keys
			pinDUTsortedasc.sort(key=float)                                 # string data type, sort these dictionary keys as though they are floats, i.e. in numerical order
			pinDUT=[float(p) for p in pinDUTsortedasc]                      # convert Pin dictionary keys to floats
			poutDUT=[self.pDUTout[pos][p] for p in pinDUTsortedasc]         # use sorted keys to sort Pout by Pin
			self.gainvspin[pos]=[poutDUT[i]-pinDUT[i] for i in range(0,len(pinDUT))]
			########################################################################################
			# find compression point from cubic spline fit
			#######################################################################################
			try: poutpinsplinefunc=UnivariateSpline(pinDUT,poutDUT,k=3)
			except: raise ValueError("ERROR! could not produce spline fit of pout vs pin")
			self.pin_spline[pos]=np.arange(min(pinDUT),max(pinDUT),0.1)
			self.pout_spline[pos]=[poutpinsplinefunc(pin) for pin in self.pin_spline[pos]]
			self.gainvspinspline[pos]=[self.pout_spline[pos][i]-self.pin_spline[pos][i] for i in range(0,len(self.pin_spline[pos]))]
			icomp=min(range(len(self.pout_spline[pos])),key=lambda i: abs((avggain-(self.pout_spline[pos][i]-self.pin_spline[pos][i]))-compressiontarget))
			if avggain-(self.pout_spline[pos][icomp]-self.pin_spline[pos][icomp])<0:
				print("WARNING compression is negative")
			self.inputcompressionpoint[pos]=float(self.pin_spline[pos][icomp])
			self.outputcompressionpoint[pos]=float(self.pout_spline[pos][icomp])
			############## done finding compression point #########################################################################

			# now plot the pout vs pin curve
			# if plotcompression:
			prfin=[formatnum(prf,precision=2,nonexponential=True) for prf in sorted([float(p) for p in self.pDUTout[pos].keys()])]   # input RF powers
			prfout=[self.pDUTout[pos][p] for p in prfin]
			prfin=[float(p) for p in prfin]
			plotCompression(pin=prfin,pout=prfout,gainm=avggain,gain=avggain,inputcompression=self.inputcompressionpoint[pos],outputcompression=self.outputcompressionpoint[pos])
	# turn off RF synthesizer output and bias because the measurements are done
		self.__rfA.off()
		if ps!=None: ps.fetbiasoff()             # turn off DC power supply
#####################################################################################################################
# Measure gains vs the tuner's reflection coefficient applied to the output of the DUT
# frequency is in MHz
# RFinputpower is the DUT input RF power in dBm
# output reflection is an array of arrays i.e. [[mag,angle],[mag,angle],.....] of the reflection coefficients to try on the output of the DUT
	def gain_vs_outputreflection(self,output_reflection=None,RFinputpower=-10.,DUTSparfile=None):
		# loop through different output reflections set by the tuner on the DUT
		self.RFinputpower=RFinputpower
		self.__rfA.set_frequency(1E6*self.frequency)									# set frequency of synthesizer
		self.actualrcoefMA={}    # actual reflection coefficient as set by tuner in magnitude and angle
		self.rfoutputlevel={}
		self.DUTgain={}
		self.tuner_loss={}
		self.tunergain50ohms={}                         # tuner gain in 50ohm system (to check system)
		#self.__rfA.set_power(leveldBm=self.RFinputpower-self._sourcecalfactor)
		self.__setDUTinputpower(pinDUT=self.RFinputpower)
		self.__rfA.on()                                 # turn on synthesizer
		self.calcDUTgain={}
		self.calcDUTgain_from_cascade={}
		try: DUTSpar=read_spar(sparfilename=DUTSparfile)         # read DUT S-parameter files
		except: DUTSpar=None                                        # no DUT S-parameters!
		for ref in output_reflection:
			# set the tuner reflection coefficient presented to the DUT output
			retg=self.set_tuner_reflection(self.frequency,gamma=complex(ref[0],ref[1]),gamma_format='ma')      # frequency in MHz
			pos=retg['pos']             # tuner mechanical position in string format p1,p2 where p1 is the carriage position and p2 the slug position
			self.actualrcoefMA[pos]=retg['gamma_MA']            # actual reflection coefficient (mag, ang in degrees) of tuner at position pos (from S1+tuner+S2 using tuner calibration data)
			Stuner=retg['Spar']      # tuner S-parameters
			self.tuner_loss[pos]=-10.*np.log10(retg['gain'])           # get tuner loss in dB (a positive number for actual loss)
			if DUTSpar!=None:
				DUTcascadetunerS=cascadeS(DUTSpar[str(int(self.frequency))],Stuner)
				self.calcDUTgain_from_cascade[pos]=20*np.log10(abs(DUTcascadetunerS[1,0]))+self.tuner_loss[pos]    # calculated DUT gain
				self.calcDUTgain[pos]=convertSRItoGt(S=DUTSpar[str(int(self.frequency))],gammaout=retg['gamma_RI'],dBout=True)    # calculated DUT gain in dB
			rfoutputlevel_uncorrected=self.__readDUToutputpower()                                                   # get uncorrected RF DUT output power in dB, i.e. RF power at the composite tuner output
			self.rfoutputlevel[pos]=self.tuner_loss[pos]+rfoutputlevel_uncorrected      # corrected DUT output power which is referenced to the DUT output
			self.DUTgain[pos]=self.rfoutputlevel[pos]-self.RFinputpower             # DUT gain measured at the given RF input power and frequency
			self.tunergain50ohms[pos]=20*np.log10(retg['Spar'][1,0])                     # tuner gain dB in a 50ohm system
			#print("reflection "+str(self.actualrcoefMA[pos])+" DUT gain dB "+self.DUTgain[pos]+" RF output raw dBm "+str(rfoutputlevel_uncorrected)+" RF output raw-tunergain50ohms "+str(rfoutputlevel_uncorrected-self.tunergain50ohms[pos]))
			print("reflection "+str(self.actualrcoefMA[pos])+" DUT gain dB "+str(self.DUTgain[pos]))
		self.__rfA.off()                # turn off RF generator
###################################################################################################################
########################################################################################################################################################################################################################################################
	# Search for optimum reflection presented to DUT which maximizes the compression point (usually 1dB compression point)
	# all data are saved to be plotted later
	# initial output reflections are the list of reflections, magnitude and angle, presented to the DUT prior to performing the search. These initial values provide a sample sufficient to perform the search by
	# performing a cubic spline and finding the maximum output Pcomp from the cubic spline interpolation AFTER the Pcomp values have been measured at all the initial_output_reflections points.
	# the stopping_criteria is the dB improvement that must be made in the last step to continue the search. Search stops when the next optimum interpolated point is: interpolated optimum point < last measured optimum + stopping_criteria
	# the maximum_reflection is the maximum reflection coefficient magnitude available from the tuner at the DUT output
	def Pcompsearch(self,initial_output_reflections=None,fractlinfitlower=0.,fractlinearfitupper=1.,compressiontarget=1.,maxcompressionlevelerror=0.1, powermeterfilterfactor=None,output_reflection=None,frequency=None,Vgs=0.,Vds=0.,draincomp=0.1,gatecomp=0.1,plotcompression=True,maxiterations=30):
		nopts=200       # number of points in real and imaginary reflection coefficient on the Smith chart
		deltagamma=.1     # length of the extrapolation vector of the reflection coefficient when searching outside the tested values of reflection coefficient for the maximum Pcomp
		deltaPcompstopcriterian=0.2           # stop search when the current interpolated Pcomp is within deltaPcompstopcriterian dBm of the last interpolated Pcomp
		minreflection=-1.
		maxreflection=1.
		Pcompmaxintlast=-999999            # interpolated maximum Pcomp (dBm)from last set of measurements set to big initial number to get at least one interation
		self.Pcompmaxint=-9999
		#deltagammai=int(deltagamma*nopts/(maxreflection-minreflection))            # number of index points in the reflection used to distance the new points which are outside the ICP (interpolated constellation polygon)
		digamma=(maxreflection-minreflection)/nopts                                  # change in gamma/index point
		gamma_outofICP=-9999999  # fill value for griddata interpolation for reflections outside the convex polygon formed by the reflection data plotted on the Smith chart. This is set very negative soas to always be the smallest value and produce the proper search

		gamma_to_measure=initial_output_reflections        # new gamma points to be measured, start with initial points specified in calling this method
		gamma_measured=[]            # gamma points already measured
		outputPcomp_average=[]        # measured output Pcomp (dBm) already measured
		# loop to find output reflection coefficient which gives highest IOP3 average
		while self.Pcompmaxint>deltaPcompstopcriterian+Pcompmaxintlast:                 # loop at least once and stop when there is no significant improvement in the interpolated Pcomp
			Pcompmaxintlast=self.Pcompmaxint
			self.measurePcomp(output_reflection=gamma_to_measure,fractlinfitlower=fractlinfitlower,fractlinfitupper=fractlinearfitupper,compressiontarget=compressiontarget,
							  maxcompressionlevelerror=maxcompressionlevelerror,powermeterfilterfactor=powermeterfilterfactor,frequency=frequency,Vgs=Vgs,Vds=Vds,draincomp=draincomp,
							  gatecomp=gatecomp,plotcompression=plotcompression,maxiterations=maxiterations)       # measure compression point at output reflection points to establish a search surface
			del gamma_to_measure
			gamma_to_measure=[]
			for p in self.actualrcoefRI.keys():				# convert actual reflection coefficient and average between high and low sideband TOI to arrays from dictionaries
				gamma_measured.append(self.actualrcoefRI[p])    # self.actualrcoefRI[p] is the actual reflection coefficient at tuner position p from self.measureTOI()
				outputTOI_average.append(self.TOIavg[p])        # self.TOIavg[p] is the actual output averaged third order intercept point at tuner position p from self.measureTOI()
																# average TOI (average of lower-frequency 3rd order product TOI and upper-frequency third order product measured) in recently-measured TOI in dBm,
																# associated with the reflection coefficients in self.actualrcoefRI[] (type dictionary)
			gamma_real_int = np.linspace(minreflection, maxreflection, nopts)  # real reflection coefficient on the interpolated grid
			gamma_imag_int = np.linspace(minreflection, maxreflection,nopts)  # imaginary reflection coefficient on the interpolated grid
			# 2D cubic spline interpolation (x,y,z) z=self._paraplotint[ii,ir] where ii is the imaginary index and ir the real index find the ICP (interpolated constellation polygon)
			print("from line 110 in IP3_focus_tuned.py size of gamma_measured, outputTOI", len(gamma_measured),len(outputTOI_average) )
			self._TOIfit = griddata((np.real(gamma_measured),np.imag(gamma_measured)), outputTOI_average,(gamma_real_int[None,:], gamma_imag_int[:,None]),method='cubic',fill_value=gamma_outofICP)
			iiopt,iropt=uind(self._TOIfit.argmax(),self._TOIfit.shape)    # find indices ii, ir, (imaginary rho, real rho) corresponding to highest average output INTERPOLATED TOI.
			self.TOImaxint=self._TOIfit[iiopt,iropt]     # maximum interpolated TOI from current dataset
			del gamma_measured
			if self.TOImaxint>deltaPcompstopcriterian+TOImaxintlast:               # perform calculations only if not done with search
				gammaopt_int=complex(gamma_real_int[iropt],gamma_imag_int[iiopt])               # complex gamma which maximizes interpolated TOI
				# is the optimum reflecton coefficient at or near the edge of the ICP? If so, we need to test up to 4 more gamma points i.e. west, east, north, and south of the interpolated optimum gamma, excepting those points that are within the ICP
				if  self._TOIfit[iiopt,iropt-1]==gamma_outofICP or self._TOIfit[iiopt-1,iropt]==gamma_outofICP or  self._TOIfit[iiopt,iropt+1]==gamma_outofICP or self._TOIfit[iiopt+1,iropt]==gamma_outofICP:   # is the optimum interpolated reflection coefficient at the edge of the ICP?
					# optimum interpolated reflection coefficient is outside the ICP so produce up to four new measurement points outside the ICP (usually no more than three new points)
					if -deltagamma < min(-gammaopt_int.real-np.sqrt(np.square(gammaopt_int.real)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))), -gammaopt_int.real+np.sqrt(np.square(gammaopt_int.real)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int)))):
						deltagamma_realneg = min(-gammaopt_int.real-np.sqrt(np.square(gammaopt_int.real)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))), -gammaopt_int.real+np.sqrt(np.square(gammaopt_int.real)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))))
					else: deltagamma_realneg=-deltagamma
					if deltagamma > max(-gammaopt_int.real-np.sqrt(np.square(gammaopt_int.real)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))), -gammaopt_int.real+np.sqrt(np.square(gammaopt_int.real)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int)))):
						deltagamma_realpos = max(-gammaopt_int.real-np.sqrt(np.square(gammaopt_int.real)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))), -gammaopt_int.real+np.sqrt(np.square(gammaopt_int.real)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))))
					else: deltagamma_realpos=deltagamma
					if -deltagamma < min(-gammaopt_int.imag-np.sqrt(np.square(gammaopt_int.imag)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))), -gammaopt_int.imag+np.sqrt(np.square(gammaopt_int.imag)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int)))):
						deltagamma_imagneg = min(-gammaopt_int.imag-np.sqrt(np.square(gammaopt_int.imag)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))), -gammaopt_int.imag+np.sqrt(np.square(gammaopt_int.imag)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))))
					else: deltagamma_imagneg=-deltagamma
					if deltagamma > max(-gammaopt_int.imag-np.sqrt(np.square(gammaopt_int.imag)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))), -gammaopt_int.imag+np.sqrt(np.square(gammaopt_int.imag)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int)))):
						deltagamma_imagpos = max(-gammaopt_int.imag-np.sqrt(np.square(gammaopt_int.imag)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))), -gammaopt_int.imag+np.sqrt(np.square(gammaopt_int.imag)+np.square(maximum_tuner_reflection)-np.square(abs(gammaopt_int))))
					else: deltagamma_imagpos=deltagamma
					# now find corresponding delta indicies for new gammas to test and also the new gammas themselves
					# exclude the gamma points which lie within the ICP
					i_realneg=iropt+int(deltagamma_realneg/digamma)             # real index point of west gamma point to test
					i_realpos=iropt+int(deltagamma_realpos/digamma)             # real index point of east gamma point to test
					i_imagneg=iropt+int(deltagamma_imagneg/digamma)             # imaginary index point of south gamma point to test
					i_imagpos=iropt+int(deltagamma_imagpos/digamma)             # imaginary index point of north gamma point to test

					if self._TOIfit[iiopt,i_realneg]==gamma_outofICP:   # is west gamma outside the ICP? If so, add it to the gammas to be tested for TOI
						westgamma=complex(gamma_real_int[i_realneg],gamma_imag_int[iiopt])      # complex west gamma
						westgammaMA=convertRItoMA(westgamma)                    # magnitude+jangle
						gamma_to_measure.append([westgammaMA.real,westgammaMA.imag])

					if self._TOIfit[iiopt,i_realpos]==gamma_outofICP:   # is east gamma outside the ICP? If so, add it to the gammas to be tested for TOI
						eastgamma=complex(gamma_real_int[i_realpos],gamma_imag_int[iiopt])      # complex west gamma
						eastgammaMA=convertRItoMA(eastgamma)                    # magnitude+jangle
						gamma_to_measure.append([eastgammaMA.real,eastgammaMA.imag])

					if self._TOIfit[i_imagneg,iropt]==gamma_outofICP:   # is south gamma outside the ICP? If so, add it to the gammas to be tested for TOI
						southgamma=complex(gamma_real_int[iropt],gamma_imag_int[i_imagneg])      # complex south gamma
						southgammaMA=convertRItoMA(southgamma)                    # magnitude+jangle
						gamma_to_measure.append([southgammaMA.real,southgammaMA.imag])

					if self._TOIfit[i_imagpos,iropt]==gamma_outofICP:   # is north gamma outside the ICP? If so, add it to the gammas to be tested for TOI
						northgamma=complex(gamma_real_int[iropt],gamma_imag_int[i_imagpos])      # complex north gamma
						northgammaMA=convertRItoMA(northgamma)                    # magnitude+jangle
						gamma_to_measure.append([northgammaMA.real,northgammaMA.imag])
				# also add the reflection coefficient at the interpolated maximum of TOI to the reflections to be measured i.e. gamma[]
				# remember that gammaopt_int is interpolated reflection coefficient (real+jimaginary) where the interpolated TOI is a maximum
				# so add this reflection coefficient to that to measure
				gammaopt_intMA=convertRItoMA(gammaopt_int)      # convert the interpolated optimum reflection coefficient from real+jimaginary  to [magnitude+jangle]
				gamma_to_measure.append([gammaopt_intMA.real,gammaopt_intMA.imag])         # add it to the gammas to measured. Note that this will be the ONLY gamma to measure if the optimum interpolated gamma is within the ICP
				print("from line 163 in IP3_focus_tuned.py gamma_to_measure",gamma_to_measure)
		return self.TOImaxint, gammaopt_intMA
########################################################################################################################################################################################################################################################
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