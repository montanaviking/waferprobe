__author__ = 'PMarsh Carbonics'
# version 2
from spectrum_analyzer import *
from rf_synthesizer import *
from focustuner import *
from writefile_measured import X_writefile_TOI
from utilities import *
from read_write_spar_noise import read_spar, spar_flip_ports
import numpy as np
from numpy import unravel_index as uind
from IVplot import plotTOI
from calculated_parameters import *
from scipy.interpolate import griddata
from calculated_parameters import convertRItoMA
from HP438A import *
import time
epsilon = 1.E-20                  # used to compare floating point numbers to account for rounding errors
synthesizerpowersetforcalibration=0.    # used to calibrate synthesizer set values to corresponding RF power levels at DUT input. This is the dBm power setting of the RF synthesizers.
DUTinputsensor='A'
	# uses Focus tuner
	# uses power meter to read fundamental powers on the input of the DUT. The spectrum analyzer reads output fundamentals and third order products
	# perform 3rd order intercept point measurement at one frequency over a two-tone input power sweep with a load tuner

	# Input parameters for class constructor
	# cascadefiles_port1[i][j]: is the S-parameters cascade data for all two-ports connected to the tuner port 1, which is the tuner port facing the DUT side
	# i is the index of the 2-port because several 2-ports might be cascaded on the tuner port 1. cascadefiles_port1[i][1] is 'flip' or 'noflip' depending on whether or not
	# the 2-port should be flipped (ports 1 and 2 exchanged) prior to cascading it. cascadefiles_port1[i][0] is the 2x2 matrix of the S-parameters at the center frequency
	#
	# cascadefiles_port2[i][j]: is the same as cascadefiles_port1[i][j], except that that these are the 2-port circuits cascaded onto the tuner port 2 side between the tuner and spectrum analyzer and/or output power meter
	# spectrum_analyzer_input_attenuation: is the spectrum analyzer's attanuation setting - must be 0dB, 5dB, 10dB,...
	# number_of_averages: is the number of averages setting for the spectrum analyzer
	# powerlevel_start: minimum (dBm) applied fundamental power level referenced to DUT input
	# powerlevel_stop: maximum (dBm) applied fundamental power level referenced to DUT input
	# powerlevel_step: step (dB) applied fundamental power level referenced to DUT input
	# center_frequency: average of the two-tone frequencies in Hz
	# frequency_spread: difference of frequency (Hz) between high and low fundamentals of the two-tone signal. The frequency spread must be small enough so that there is a very small difference of system properties between the two fundamental tones.
	# spectrum_analyzer_cal_factor: is dB power meter - dB spectrum analyzer display - i.e. the difference between what the power meter reads and the spectrum analyzer reads for a signal at the spectrum analyzer input at the lower frequency of the 2-tones - usually a positive number
	# source_calibration_factor: (dB) is the actual power at the DUT input - that measured at the power sensor connected to the power divider on the input side of the DUT
	# system_TOI: the measured TOI of the system, in dBm, with a thru replacing the DUT
	# powermetercalfactor: This is the power meter calibration factor at the center_frequency.
	# loglin: This determines the output setting of the power meter. Normally set to 'LG' for a dBm output
	# lowerfrequencysynthesizerdesignator: The synthesizer which is designated to produce the lower frequency of the two fundamental tones.
	# upperfrequencysynthesizerdesignator: The synthesizer which is designated to produce the upper frequency of the two fundamental tones.
	# estimated_gain: is the estimated DUT gain

	# internal parameters
	# sa: is the spectrum analyzer handle
	# rflow:is the synthesizer handle of the synthesizer tuned to the lower of the two-tone frequencies

	# rfhigh is synthesizer handle of the synthesizer tuned to the lower of the two-tone frequencies

	# centfreq is the frequency point midway between the two tones in Hz
	# self._deltafreq is the frequency separation between the two tones in Hz

	# source_calibration_factor_lowerfreq=PDUTin-PsynAset where PDUTin is the power at the DUT input, as read by the power meter and corrected for probe loss when synthesizer A power (lower frequency) is set to PsynAset and synthesizer B (upper frequency) is off. self._sourcecalfactor is expected to be set to a negative dB quantity
	# source_calibration_factor_upperfreq=PDUTin-PsynBset where PDUTin is the power at the DUT input, as read by the power meter and corrected for probe loss when synthesizer B power (upper frequency) is set to PsynBset and synthesizer B (upper frequency) is off. self._sourcecalfactor is expected to be set to a negative dB quantity
	# self._tuner_loss is the loss from the output of the DUT to the input of the spectrum analyzer (reference input of the spectrum analyzer) default = 0
powerdampfactor=0.9         # used to improve convergence of loop which equalizes powers of both of the two-tone fundamentals
class IP3_Tuned(FocusTuner,HP438A):
	def __init__(self,rm=None,cascadefiles_port1=None,cascadefiles_port2=None, spectrum_analyzer_input_attenuation=10., number_of_averages=8, powerlevel_start=None, powerlevel_stop=None, powerlevel_step=None,
	             center_frequency=None, frequency_spread=None,spectrum_analyzer_cal_factor=None, source_calibration_factor=None, system_TOI=None,
	             powermetercalfactor=None,loglin='LG',lowerfrequencysynthesizerdesignator='A',upperfrequencysynthesizerdesignator='B',estimated_gain=-10): # normally synthesizer A should be the self.__rflow (lower frequency tone) because it has the high-accuracy attenuators
		#cascade available 2port networks onto ports 1 and 2 of the tuner
		# for x=1 or 2 (port 1 or 2 of tuner) cascadefile_portx[i][0] is the S-parameter full filename and  cascadefile_portx[i][1] is "flip" or "noflip". "flip" means to transpose ports 1 and 2 of the S-parameters read from the file
		tunertype='load'            # the tuner will always be used in the 'load' mode for TOI measurements
		# cascade two-ports to tuner which form the test set
		print("from line 67 in IP3_focus_tuned.py version 2")
		S1=None
		S2=None
		self._estimated_gain=estimated_gain
		self._reflevelgaincorrection=self._estimated_gain
		self._navg_fundamental=2        # number of averages of spectrum analyzer to read fundamental power levels
		if cascadefiles_port1!=None and len(cascadefiles_port1)>0:
			# add the first of the cascaded 2-ports to form S1 - the two-port attached to port 1 of the tuner which is facing the DUT
			if cascadefiles_port1[0][1]=='flip':   S1=spar_flip_ports(read_spar(cascadefiles_port1[0][0]))                      # exchange port 1 with port 2 of the two-port to be cascaded
			else:   S1=read_spar(cascadefiles_port1[0][0])
			del cascadefiles_port1[0]               # remove first 2-port file since its S-parameters have already been added to the first element of the cascade
			for c in cascadefiles_port1:            # c[0] is the S-parameter full filename and c[1] is "flip" or "noflip". "flip" means to transpose ports 1 and 2 of the S-parameters read from the file
				if c[1]=='flip': S1=cascadeSf(S1,spar_flip_ports(read_spar(c[0])))  # then flip ports 1 and 2 on this two-port and cascade it to form the two-port attached to port 1 of the tuner
				else: S1=cascadeSf(S1,read_spar(c[0]))                              # don't flip ports
		#cascade available 2port networks onto port2 of tuner which is the tuner side facing the bias Tee and/or spectrum analyzer
		if cascadefiles_port2!=None and len(cascadefiles_port2)>0:
			# add the first of the cascaded 2-ports to form S1 - the two-port attached to port 1 of the tuner
			if cascadefiles_port2[0][1]=='flip':   S2=spar_flip_ports(read_spar(cascadefiles_port2[0][0]))                      # exchange port 1 with port 2 of the two-port to be cascaded
			else:   S2=read_spar(cascadefiles_port2[0][0])
			del cascadefiles_port2[0]               # remove first 2-port file since its S-parameters have already been added to the first element of the cascade
			for c in cascadefiles_port2:            # c[0] souris the S-parameter full filename and c[1] is "flip" or "noflip". "flip" means to transpose ports 1 and 2 of the S-parameters read from the file
				if c[1]=='flip': S2=cascadeSf(S2,spar_flip_ports(read_spar(c[0])))  # then flip ports 1 and 2 on this two-port and cascade it to form the two-port attached to port 1 of the tuner
				else: S1=cascadeSf(S2,read_spar(c[0]))                              # don't flip ports
		#######
		super(IP3_Tuned,self).__init__(S1=S1,S2=S2,tunertype=tunertype)                    # initialize Focus tuner
		HP438A.__init__(self,rm=rm,calfactorA=powermetercalfactor,loglin=loglin)           # set up power meter to use sensor A
		try: self.__sa=SpectrumAnalyzer(rm)
		except: raise ValueError("ERROR! No spectrum analyzer found!")
		try: self.__rflow=Synthesizer(rm=rm,syn=lowerfrequencysynthesizerdesignator)
		except: raise ValueError("ERROR! No lower frequency RF source found for two-tone!")
		try: self.__rfhigh=Synthesizer(rm=rm,syn=upperfrequencysynthesizerdesignator)
		except: raise ValueError("ERROR! No upper frequency RF source found for two-tone!")

		self._lowerfrequencysynthesizerdesignator=lowerfrequencysynthesizerdesignator
		self._upperfrequencysynthesizerdesignator=upperfrequencysynthesizerdesignator


		self._saatten=spectrum_analyzer_input_attenuation
		self._navg=number_of_averages
		self._plevelstart=powerlevel_start          # maximum DUT input power (dBm) tested. This is is the first power level applied
		self._plevelstop=powerlevel_stop            # minimum DUT input power (dBm) tested. This is is the last power level applied
		self._pleveldel=abs(powerlevel_step)             # DUT input power (dBm) step
		self._centfreq=center_frequency             # this is the mean frequency of the two-tones in Hz. The tuner and S-parameters assume this is the frequency of operation
		self._deltafreq=frequency_spread
		self._sacalfactor=spectrum_analyzer_cal_factor # dB difference between the tuner output (port 2) (as measured by the power meter) and the spectrum analyzer level. This takes into account the loss between the tuner port 2 (output) and the spectrum analyzer as well as calibration of the spectrum analyzer display
		self._sourcecalfactor=source_calibration_factor # This is PinDUT-Ppowermeter in dB

		self._sysTOI=system_TOI                     # system third order intercept point
		# set up synthesizers
		self.__rflow.off()
		self.__rfhigh.off()
		# set two-tone synthesizer frequencies
		self.__rflow.set_frequency(self._centfreq-self._deltafreq/2.)  # set lower frequency of two-tone
		self.__rfhigh.set_frequency(self._centfreq+self._deltafreq/2.) # set upper frequency of two-tone

		self.__findsourceinputcalibrationfactors()  # get calibration factors which determine the power level settings of the synthesizers to produce corresponding desired power levels referenced to the DUT input
######################################################################################################################################################################################################################################
##################################################################################################################################################################################################################################
# find self._settingcallowerfreq = self._sourcecalfactor+powermeter reading+ power setting of lower frequency tone synthesizer
#  and find self._settingcalupperfreq = self._sourcecalfactor+powermeter reading+ power setting of higher frequency tone synthesizer
# where the powermeter reading refers to the powermeter coupled to the input DUT port. This reading is made with only one of the synthesizers on at a time.
# the self._sourcecalfactor = source_calibration_factor = (dB) is the actual power at the DUT input - that measured at the power sensor connected to the power divider on the input side of the DUT
# this method produces the calibration factors: self._settingcallowerfreq and self._settingcalupperfreq calibration factors as described above
# assumes that the RF synthesizer frequencies have been set
	def __findsourceinputcalibrationfactors(self):
		# turn off both synthesizers
		self.__rflow.off()
		self.__rfhigh.off()
		if 'unleveled'==self.__rflow.set_power(synthesizerpowersetforcalibration):              # set 0dBm on lower-frequency RF source to calibrate its power output
			raise ValueError("ERROR from __findsourceinputcalibrationfactors ! attempt to set lower frequency RF synthesizer above power level at which the power is calibrated")
		powersensorraw=self.readpower(sensor=DUTinputsensor)
		powersetting=self.__rflow.get_power()
		self._settingcallowerfreq=self._sourcecalfactor+powersensorraw-powersetting  # get lower frequency source calibration factor = PinDUT-Psettinglower
		self.__rflow.off()
		if 'unleveled'==self.__rfhigh.set_power(synthesizerpowersetforcalibration):              # set 0dBm on upper-frequency RF source to calibrate its power output
			raise ValueError("ERROR from __findsourceinputcalibrationfactors ! attempt to set upper frequency RF synthesizer above power level at which the power is calibrated")
		powersensorraw=self.readpower(sensor=DUTinputsensor)
		powersetting=self.__rfhigh.get_power()
		self._settingcalupperfreq=self._sourcecalfactor+powersensorraw-powersetting  # get lower frequency source calibration factor = PinDUT-Psettingupper
		self.__rfhigh.off()
		self.__rflow.off()
######################################################################################################################################################################################################################################
##################################################################################################################################################################################################################################
# Sets the RF power referred to the DUT input for the selected RF synthesizer
# return: actual power referred to the DUT input = self.
# Inputs:
# self._settingcallowerfreq: is frequency source calibration factor = PinDUT-Psettinglower in dB where PinDUT is the desired RF lower tone power at the DUT input. Determined from automated measurement in __findsourceinputcalibrationfactors()
# self._settingcalupperfreq: is frequency source calibration factor = PinDUT-Psettingupper in dB where PinDUT is the desired RF upper tone power at the DUT input. Determined from automated measurement in __findsourceinputcalibrationfactors()
# self._sourcecalfactor: is the # This is PinDUT-Ppowermeter in dB which was measured manually for system characterization
# syndesignator selects the RF synthesizer which is to have its output level set. syndesignator='rflow' selects the RF sythesizer which emits the lower-frequency fundamental and syndesignator='rfhigh' selects the RF sythesizer which produces the higher-frequency fundamental
# assumes that the RF synthesizer frequencies have been set and that the power meter is calibrated and has the correct calibration factor set
	def __setDUTinputpower(self,pinDUT=None,syndesignator=None):
		maxloopdberror=0.05
		self.__rflow.off()
		self.__rfhigh.off()
		if syndesignator.lower()=='rflow':
			powersetting=pinDUT-self._settingcallowerfreq
			if 'unleveled'==self.__rflow.set_power(powersetting):              # set 0dBm on lower-frequency RF source to calibrate its power output
				raise ValueError("ERROR from __findsourceinputcalibrationfactors ! attempt to set lower frequency RF synthesizer above power level at which the power is calibrated")
			settingcallowerfreq=9999999999999.          # ensure that loop runs at least once
			noloops=0
			while abs(settingcallowerfreq-self._settingcallowerfreq)>maxloopdberror and noloops<=maxloopdberror:
				noloops+=1
				powerDUTinputsensor=self.readpower(sensor=DUTinputsensor)           # read input sensor powermeter - raw uncorrected power data
				settingcallowerfreq=self._sourcecalfactor+powerDUTinputsensor-self.__rflow.get_power()
				print("settingcallowerfreq-self._settingcallowerfreq = ",settingcallowerfreq-self._settingcallowerfreq)
				if abs(settingcallowerfreq-self._settingcallowerfreq)>maxloopdberror:
					print("WARNING lower frequency self._settingcallowerfreq is being corrected")
					self._settingcallowerfreq=settingcallowerfreq
		elif syndesignator.lower()=='rfhigh':
			powersetting=pinDUT-self._settingcalupperfreq
			if 'unleveled'==self.__rfhigh.set_power(powersetting):              # set 0dBm on lower-frequency RF source to calibrate its power output
				raise ValueError("ERROR from __findsourceinputcalibrationfactors ! attempt to set lower frequency RF synthesizer above power level at which the power is calibrated")
			settingcalupperfreq=9999999999999.          # ensure that loop runs at least once
			noloops=0
			while abs(settingcalupperfreq-self._settingcalupperfreq)>maxloopdberror and noloops<=maxloopdberror:
				noloops+=1
				powerDUTinputsensor=self.readpower(sensor=DUTinputsensor)           # read input sensor powermeter - raw uncorrected power data
				settingcalupperfreq=self._sourcecalfactor+powerDUTinputsensor-self.__rfhigh.get_power()
				print("settingcalupperfreq-self._settingcallowerfreq = ",settingcalupperfreq-self._settingcalupperfreq)
				if abs(settingcalupperfreq-self._settingcalupperfreq)>0.05:
					print("WARNING lower frequency self._settingcallowerfreq is being corrected ")
					self._settingcallowerfreq=settingcalupperfreq
		else: raise ValueError("ERROR! did not set synthesizer designator")
		PDUTinputmeasured=self._sourcecalfactor+powerDUTinputsensor             # Corrected input DUT power level
		# leave RF synthesizers in off state
		self.__rflow.off()
		self.__rfhigh.off()
		return PDUTinputmeasured
	######################################################################################################################################################################################################################################
# read power at tuner output port (dBm)
# reads the output power sensor to find the RF output power of the selected fundamental at the output of the composite tuner.
# Here, the selected RF synthesizer source is switched on and the output sensor is read to measure its power at the composite tuner output in dBm.
# Input is self._outpowercalfactor = dB difference between the output power meter - the output power at the composite tuner output port 2. This accounts for the loss of the coupler port and the gain of the amplifier on that port prior to the output power sensor
# TODO Not used July 18, 2018
	def __readDUToutputpower(self,syndesignator=None):
		if syndesignator.lower()=='rflow':            # this is the lower-frequency synthesizer
			self.__rfhigh.off()                         # turn off high-frequency synthesizer so we can measure only the composite tuner output power due to the low-frequency synthesizer
		elif syndesignator.lower()=='rfhigh':            # this is the higher-frequency synthesizer
			self.__rflow.off()                         # turn off low-frequency synthesizer so we can measure only the composite tuner output power due to the high-frequency synthesizer
		else: raise ValueError("ERROR! Missing or illegal value for synthesizer specifier when measuring composite tuner output RF power")
		tuneroutputraw=self.readpower(sensor=DUToutputsensor)  # read the RF power at the output of the composite tuner coupler
		tuneroutput=tuneroutputraw-self._outpowermetercalfactor # use the calibration supplied by the user, to deembed the output power to the composite tuner output
		return tuneroutput      # composite tuner output power due to the selected RF synthesizer
	########################################################################################################################################################################################################################################################
	# Search for optimum reflection presented to DUT which maximizes the average between lower and upper -frequency output TOI
	# all data are saved to be plotted later
	# initial output reflections are the list of reflections, magnitude and angle, presented to the DUT prior to performing the search. These initial values provide a sample sufficient to perform the search by
	# performing a cubic spline and finding the maximum output TOI from the cubic spline interpolation AFTER the TOI values have been measured at all the initial_output_reflections points.
	# the stopping_criteria is the dB improvement that must be made in the last step to continue the search. Search stops when the next optimum interpolated point is: interpolated optimum point < last measured optimum + stopping_criteria
	# the maximum_reflection is the maximum reflection coefficient magnitude available from the tuner at the DUT output
	def TOIsearch(self,initial_output_reflections=None,fractlinfitlower=0.,fractlinearfitupper=0.,plotgraphs=False,stopping_criteria=0.2,maximum_tuner_reflection=0.85):
		nopts=200       # number of points in real and imaginary reflection coefficient on the Smith chart
		deltagamma=.1     # length of the extrapolation vector of the reflection coefficient when searching outside the tested values of reflection coefficient for the maximum TOI
		deltaTOIstopcriterian=stopping_criteria           # stop search when the current interpolated TOI is within deltaTOIstopcriterian dBm of the last interpolated TOI
		minreflection=-1.
		maxreflection=1.
		TOImaxintlast=-999999            # interpolated maximum TOI (dBm)from last set of measurements set to big initial number to get at least one interation
		self.TOImaxint=-9999
		#deltagammai=int(deltagamma*nopts/(maxreflection-minreflection))            # number of index points in the reflection used to distance the new points which are outside the ICP (interpolated constellation polygon)
		digamma=(maxreflection-minreflection)/nopts                                  # change in gamma/index point
		gamma_outofICP=-9999999  # fill value for griddata interpolation for reflections outside the convex polygon formed by the reflection data plotted on the Smith chart. This is set very negative soas to always be the smallest value and produce the proper search

		gamma_to_measure=initial_output_reflections        # new gamma points to be measured, start with initial points specified in calling this method

		# loop to find output reflection coefficient which gives highest IOP3 average
		while self.TOImaxint>deltaTOIstopcriterian+TOImaxintlast:                 # loop at least once and stop when there is no significant improvement in the interpolated TOI
			TOImaxintlast=self.TOImaxint
			self.measureTOI(output_reflection=gamma_to_measure,fractlinfitlower=fractlinfitlower,fractlinearfitupper=fractlinearfitupper,plotgraphs=plotgraphs,cleardata=False)       # measure TOI at output reflection points to establish a search surface
			gamma_to_measure=[]
			gamma_measured=[]
			outputTOI_average=[]        # measured output TOI (dBm) already measured
			for p in self.actualrcoefRI.keys():				# convert actual reflection coefficient and average between high and low sideband TOI to arrays from dictionaries
				gamma_measured.append(self.actualrcoefRI[p])    # self.actualrcoefRI[p] is the actual reflection coefficient at tuner position p from self.measureTOI()
				outputTOI_average.append(self.TOIavg[p])        # self.TOIavg[p] is the actual output averaged third order intercept point at tuner position p from self.measureTOI()
																# average TOI (average of lower-frequency 3rd order product TOI and upper-frequency third order product measured) in recently-measured TOI in dBm,
																# associated with the reflection coefficients in self.actualrcoefRI[] (type dictionary)
			gamma_real_int = np.linspace(minreflection, maxreflection, nopts)  # real reflection coefficient on the interpolated grid
			gamma_imag_int = np.linspace(minreflection, maxreflection,nopts)  # imaginary reflection coefficient on the interpolated grid
			# 2D cubic spline interpolation (x,y,z) z=self._paraplotint[ii,ir] where ii is the imaginary index and ir the real index find the ICP (interpolated constellation polygon)
			print("from line 116 in IP3_focus_tuned.py size of gamma_measured, outputTOI", len(gamma_measured),len(outputTOI_average) )
			self._TOIfit=griddata((np.real(gamma_measured),np.imag(gamma_measured)), outputTOI_average,(gamma_real_int[None,:], gamma_imag_int[:,None]),method='cubic',fill_value=gamma_outofICP)
			iiopt,iropt=uind(self._TOIfit.argmax(),self._TOIfit.shape)    # find indices ii, ir, (imaginary rho, real rho) of the reflection coefficients corresponding to highest average output INTERPOLATED TOI.
			self.TOImaxint=self._TOIfit[iiopt,iropt]     # maximum interpolated TOI from current dataset
			#del gamma_measured
			if self.TOImaxint>deltaTOIstopcriterian+TOImaxintlast:               # perform calculations only if not done with search
				gammaopt_int=complex(gamma_real_int[iropt],gamma_imag_int[iiopt])               # complex gamma which maximizes the interpolated TOI fit from the 2-D cubic spline
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
						eastgamma=complex(gamma_real_int[i_realpos],gamma_imag_int[iiopt])      # complex east gamma
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
				print("from line 167 in IP3_focus_tuned.py gamma_to_measure",gamma_to_measure)
		return self.TOImaxint, gammaopt_intMA
	########################################################################################################################################################################################################################################################
	# Measure the third order intercept point over all the specified reflection coefficients
	# This version uses the power sensor A to measure the DUT fundamental input power and the power sensor B to measure the DUT output power
	# This measurement uses an input power meter to monitor the DUT input fundamental (two-tone) levels and an output meter to monitor the DUT output fundamental (two-tone) levels
	# therefore, the DUT gain at the fundamental frequency is measured
	# fractlinfit is the fraction of the input two-tone power range to use to linear fit the distortion product power vs input power
	# in order to find the third order intercept point
	# fractlinearfitlower is the linear fit lower bound spacing away from the swept lower bound as a fraction of the total input power in dBm swept from the lower bound to upper bound of specified input power sweep in dBm e.g. 0.1 for 10%
	# fractlinearfitupper is the linear fit upper bound spacing away from the swept lower bound as a fraction of the total input power in dBm swept from the lower bound to upper bound of specified input power sweep in dBm e.g. 0.9 for 90%
	# output_reflection is the list which specifies the requested magnituded (linear) and angle of the reflection coefficient the tuner presents to the DUT output in the format [[mag1,ang1],[mag2,ang2],...[magn,angn]]
	# cleardata=True : clear data from prevous runs cleardata=False : accumulate data between runs
	def measureTOI(self,output_reflection=None,fractlinfitlower=0.,fractlinearfitupper=0.,plotgraphs=False,cleardata=True):
		maxrefleveladjusttries=10
		if output_reflection==None or len(output_reflection)<1: raise ValueError("ERROR! no tuner reflections given")
		if cleardata or not hasattr(self,'TOIh'):           # clear data arrays or declare them if they don't exist
			self.TOIl={}            #lower sideband third order intercept point (dBm) referenced to the DUT output
			self.TOIh={}            #upper sideband third order intercept point (dBm) referenced to the DUT output
			self.TOIavg={}          # average of third-order output intercept point (average of the dBm values) between lower and upper sidebands i.e. self.TOIl{}+self.TOIh{} for all tuner positions (and reflections) measured
			self.DUTgain={}         # self.DUTgain is the DUT gain calculated from the slope of self.TOIptt
			self.pinDUT={}          # self.pinDUT is the fundamental (each of the two-tones') powers (dBm) at the input of the DUT as calibrated by the power meter during the system setup, and the output of the DUT
			self.TOIptt={}          # the fundamental output power (dBm) at the output of the DUT
			self.TOIpdl={}          # the output power (dBm) at the DUT output of the lower tone
			self.TOIpdh={}          # the output power (dBm) at the DUT output of the upper tone
			self.noisefloor={}      # Noise floor of the spectrum analyzer, referenced to the DUT output (dBm in the resolution bandwidth used to perform the signal measurements via the spectrum analyzer)
			self.TOIml={}           # slope (dBm/dBm) of the lower distortion product vs fundamental power
			self.TOImh={}           # slope (dBm/dBm) of the upper distortion product vs fundamental power
			self.poutm={}           # measured slope of DUT fundamental output power vs fundamental input power (dBm)
			self.TOIbl={}           # y intercept of the lower distortion product (dBm)
			self.TOIbh={}           # y intercept of the upper distortion product (dBm)

			self.fitquality={}      # worst-case quality of fit between TOI distortion products (dBm)
			self.actualrcoefMA={}   # actual reflection coefficient that the tuner presents to the DUT output magnitude, angle (degrees)
			self.actualrcoefRI={}   # actual reflection coefficient that the tuner presents to the DUT output real + jimaginary (complex)
			self.sys={}             # system 3rd order products (dBm) vs DUT fundamental two-tone output power (power of one tone)

		for ref in output_reflection:
			# set the tuner reflection coefficient presented to the DUT output
			retg=self.set_tuner_reflection(frequency=int(1E-6*self._centfreq),gamma=complex(ref[0],ref[1]),gamma_format='ma')          # self._centfreq is the average frequency of the two-tone input, in Hz -> convert to MHz for this method call
			pos=retg['pos']             # tuner mechanical position in string format p1,p2 where p1 is the carriage position and p2 the slug position
			self.actualrcoefMA[pos]=retg['gamma_MA']                 # actual reflection coefficient of tuner at position pos (from S1+tuner+S2 using tuner calibration data) magnitude and angle (deg)
			print("from line 329 in IP3_focus_tuned.py pos, gamma=",self.actualrcoefMA[pos],pos)
			self.actualrcoefRI[pos]=retg['gamma_RI']                # actual reflection coefficient of tuner at position pos in real+jimaginary
			self._tuner_loss=-10.*np.log10(retg['gain'])          # get tuner loss in dB (positive number)

			flow = self._centfreq-self._deltafreq/2.           # lower fundamental frequency of the two-tone
			fhigh = self._centfreq+self._deltafreq/2.          # upper fundamental frequency of the two-tone
			spanfund = 100.E3                      # measurement span about the fundamentals
			spand=1000.                             # measurement span about the distortion products
			resbwfund = 1000.                       # resolution bandwidth used to measure fundamental two-tone components
			# turn off synthesizers to measure noise floor
			self.__rflow.off()
			self.__rfhigh.off()

			self.__sa.set_attenuation(self._saatten)                   # set requested attenuation level of spectrum analyzer
			self.__sa.set_numberaverages(self._navg)                   # set requested number of averages for spectrum analyzer
			# first measure noise floor for lower distortion product - expected to be the same as for upper frequency product as well
			# decrease resolution bandwidth by one increment for distortion product measurements
			f,TO_power=self.__sa.measure_spectrum(centfreq=flow-self._deltafreq, span=spand, returnspectrum=False)
			self.__sa.set_autoresolutionbandwidth('y')
			self.__sa.set_autovideobandwidth('y')
			f,TO_power=self.__sa.measure_spectrum(centfreq=flow-self._deltafreq, span=spand,returnspectrum=False)			# get raw measured noise floor

			self.noisefloor[pos]=np.average(TO_power)                  # get noise floor as measured directly at the spectrum analyzer without correction
			noisefloorlin = pow(10.,self.noisefloor[pos]/10.)     # noisefloor in mW as measured directly at spectrum analyzer without correction for system losses

			# set two-tone synthesizer frequencies
			self.__rflow.set_frequency(self._centfreq-self._deltafreq/2.)  # set lower frequency of two-tone
			self.__rfhigh.set_frequency(self._centfreq+self._deltafreq/2.) # set upper frequency of two-tone
			# attempt to set RF synthesizers to the maximum power specified in this test. plevelmax is the maximum
			self.__setDUTinputpower(pinDUT=max(self._plevelstart,self._plevelstop),syndesignator='rflow')       # attempt to set lower frequency RF source to maximum requested DUT input power
			self.__setDUTinputpower(pinDUT=max(self._plevelstart,self._plevelstop),syndesignator='rfhigh')       # attempt to set upper frequency RF source to maximum requested DUT input power
			self.__rflow.off()
			self.__rfhigh.off()

			plevelsDUT = np.linspace(start=self._plevelstart,stop=self._plevelstop,num=1+int(abs((self._plevelstop-self._plevelstart)/self._pleveldel)))                                      # start two-tone test at the maximum RF power and work down plevel is the direct power setting
			self.TOIptt[pos] = []                                    # measured two-tone fundamental DUT output power level array
			self.TOIpdl[pos] = []                                    # power level array of the lower third order distortion product
			self.TOIpdh[pos] = []                                    # power level array of the upper third order distortion product
			self.pinDUT[pos]=[]										# average fundamental input power applied to the DUT
			self.sys[pos] = []                                   	# third order product due to system IP3

			##### measure third order products starting with the highest specified fundamental power (power levels of each of the two fundamental tones)
			plevelmax=max(plevelsDUT)
			for plevel in plevelsDUT:                          # start third order intercept test at starting power. plevel is the power incident on the DUT input
				print("DUT incident power setting in loop ",plevel)
				# set fundamental DUT input powers
				pinDUTlowfreq=self.__setDUTinputpower(pinDUT=plevel,syndesignator='rflow')        # set lower-frequency fundamental power level and read the actual level at the DUT from the power meter
				pinDUThighfreq=self.__setDUTinputpower(pinDUT=plevel,syndesignator='rfhigh')        # set lower-frequency fundamental power level and read the actual level at the DUT from the power meter
				self.__rflow.on()
				self.__rfhigh.on()
				if abs(pinDUThighfreq-pinDUTlowfreq)>0.1: raise ValueError("ERROR! DUT input powers are unequal ",pinDUThighfreq-pinDUTlowfreq)
				#loop to find spectrum analyzer reference level which doesn't saturate spectrum analyzer input######################
				reftries=0
				reflevelOK=False
				self.__sa.set_numberaverages(self._navg_fundamental)            # set up spectrum analyzer averages to read fundamental RF power levels
				while reftries<maxrefleveladjusttries and not reflevelOK:      #loop to find reference level which doesn't saturate spectrum analyzer input
					reflevelOK=True
					try: flowm,plowm=self.__sa.measure_spectrum(centfreq=flow,span=spanfund,returnspectrum=False)     #measure lower fundamental of two tone input
					except:
						reflevelOK=False
						self._reflevelgaincorrection+=10.                       # increment reference level by 10dB to try to get spectrum analyzer out of saturation
						self.__sa.set_referencelevel(self._reflevelgaincorrection+self._estimated_gain)
						reftries+=1
					try: fhighm,phighm=self.__sa.measure_spectrum(centfreq=fhigh,span=spanfund,returnspectrum=False)  #measure upper fundamental of two tone input
					except:
						reflevelOK=False
						self._reflevelgaincorrection+=10.                       # increment reference level by 10dB to try to get spectrum analyzer out of saturation
						self.__sa.set_referencelevel(self._reflevelgaincorrection+self._estimated_gain)
						reftries+=1
					#print("from line 136 IP3.py reflevel=",reflevel,reftries)        #debug
				# if reftries>0:
				# 	self._reflevelgaincorrection+=10.
				# 	self.__sa.set_referencelevel(reflevel)
				##########################################
				if reftries>=maxrefleveladjusttries: raise ValueError("ERROR! could not get spectrum analyzer out of input saturation")
				# iterate synthesizer power levels to produce the same level in both of the two-tones as measured by the spectrum analyzer #######################

				#flowm,plowm=self.__sa.measure_spectrum(centfreq=flow,span=spanfund,returnspectrum=False)     #measure lower fundamental of two tone input in dBm this is a raw spectrum analyzer reading and needs to be corrected to get actual fundamental power level
				#fhighm,phighm=self.__sa.measure_spectrum(centfreq=fhigh,span=spanfund,returnspectrum=False)  #measure upper fundamental of two tone input in dBm this is a raw spectrum analyzer reading and needs to be corrected to get actual fundamental power level

				#################################################################################################################################################
				pfundaverage_DUTpout = dBaverage(self._tuner_loss + self._sacalfactor + plowm, self._tuner_loss + self._sacalfactor + phighm) 		# average of the two-tone lower and upper frequency powers referred to the DUT output using the spectrum analyzer measured input power with the spectrum analyzer loss and tuner loss calibrated out
				self.pinDUT[pos].append(plevel)		# power into DUT with synthesizer to DUT losses calibrated out (should be actual power to DUT input in dBm)
				self.TOIptt[pos].append(pfundaverage_DUTpout)                                                        #measured fundamental power level as referred to the DUT output

				reflevel=80.+10.*int(self.noisefloor[pos]/10.)     # set spectrum analyzer reference level to nearest increment of 10dB to measure distortion products. Here the noise floor is raw data as measured at the spectrum analyzer without correction for system losses
				self.__sa.set_referencelevel(reflevel)                 # set reference level of spectrum analyzer to show distortion products
				self.__sa.set_numberaverages(self._navg)            # set up spectrum analyzer averages to read third order (TO) RF power levels
				if abs(plevel-plevelmax)<epsilon:                        # is this the maximum power level? If so, find the actual third order (TO) frequencies because the third order products are most visible at the highest power levels
					self.__sa.set_autoresolutionbandwidth('y')                  # set automatic resolution bandwidth
					self.__sa.set_autovideobandwidth('y')                       # set automatic video bandwidth
					# at this point, we are interested in finding just the exact frequencies of the third order products so we can zero in on them later with a narrow resolution bandwidth which improves sensitivity/accuracy and reduces noise. The powers are less important for these initial measurements
					TO_freq_lower,TO_power=self.__sa.measure_spectrum(centfreq=flowm-self._deltafreq, span=10.*spand,returnspectrum=False)       # measure lower frequency 3rd order product power level and frequency
					TO_freq_lower,TO_power=self.__sa.measure_spectrum(centfreq=TO_freq_lower,span=spand,returnspectrum=False)      # reduce frequency sweep span and re-measure lower TO frequency
					TO_freq_upper,TO_power=self.__sa.measure_spectrum(centfreq=fhighm+self._deltafreq, span=10.*spand,returnspectrum=False)       # measure upper frequency 3rd order product power level and frequency
					TO_freq_upper,TO_power=self.__sa.measure_spectrum(centfreq=TO_freq_upper,span=spand,returnspectrum=False)       # reduce frequency sweep span and re-measure upper TO frequency
					self._resbwdistortion=self.__sa.decrease_resolutionbandwidth()                             # set resolution bandwidth one notch lower than that automatically determined

				self.__sa.set_autoresolutionbandwidth('y')                  # set automatic resolution bandwidth
				self.__sa.set_autovideobandwidth('y')                       # set automatic video bandwidth

				# The previous measurement gave us precise frequencies of third order products so measure third order power levels using a narrow frequency span to minimize noise
				TO_freq_lower_static,TO_power_uncorrected=self.__sa.measure_spectrum(centfreq=TO_freq_lower,span=spand,returnspectrum=False)       # measure lower frequency 3rd order product power level and frequency
				TO_power = self._tuner_loss+self._sacalfactor+10.*np.log10(abs(pow(10.,TO_power_uncorrected/10.)-noisefloorlin))      # calibrate to power meter readings and subtract out noise floor
				print ("lower third order product at DUT output =", TO_power + self._tuner_loss) #debug
				self.TOIpdl[pos].append(TO_power)												# lower third order product as corrected to the DUT output
				#self.__sa.set_resolutionbandwidth(self._resbwdistortion)                                 # set the resolution bandwidth to measure distortion product
				TO_freq_upper_static,TO_power_uncorrected=self.__sa.measure_spectrum(centfreq=TO_freq_upper,span=spand,returnspectrum=False)       # measure upper frequency 3rd order product power level and frequency
				TO_power = self._tuner_loss+self._sacalfactor+10.*np.log10(abs(pow(10.,TO_power_uncorrected/10.)-noisefloorlin))      # calibrate to power meter readings and subtract out noise floor
				print ("upper third order product at DUT output =", TO_power + self._tuner_loss) 	# debug
				self.TOIpdh[pos].append(TO_power)												# upper third order product as corrected to the DUT output
				self.sys[pos].append(3.*self.TOIptt[pos][-1]-2.*self._sysTOI)     # find third order product due to TOI of system AT THE DUT OUTPUT Note that self._sysTOI was calibrated to the DUT output when characterizing the system with a through in place of the DUT and self.TOIptt[pos] is the fundamental power at the DUT output
				#print("sys TOI ",self.sys[pos][-1],self._sysTOI,self.TOIptt[pos][-1])
				print("tuner reflection IP3_maury_tuned.py line 230 sys",self.sys[pos][-1],self._sysTOI,self.TOIptt[pos][-1])
				plevel = plevel-self._pleveldel                     # decrement power level of the fundamental two-tones for next measurement
				self.__rflow.vclear()
				self.__rfhigh.vclear()
			########## end of power loop, ready to calculate TOI from fundamentals and 3rd order product power levels ############################################
			self.__rflow.off()
			self.__rfhigh.off()
			# find both 3rd order intercept points, corrected power levels at the spectrum analyzer input, and corrected linear fits
			# first get only TOIs
			self.TOIml[pos],self.TOIbl[pos],rl = linfitendexclude(x=self.pinDUT[pos],y=self.TOIpdl[pos],lowerfraction=fractlinfitlower,upperfraction=fractlinearfitupper )  # distortion product linear fit for lower distortion product to find TOI
			self.TOImh[pos],self.TOIbh[pos],rh = linfitendexclude(x=self.pinDUT[pos],y=self.TOIpdh[pos],lowerfraction=fractlinfitlower,upperfraction=fractlinearfitupper )  # distortion product linear fit for upper distortion product to find TOI
			self.poutm[pos],g,rf=linfitendexclude(x=self.pinDUT[pos],y=self.TOIptt[pos],lowerfraction=fractlinfitlower,upperfraction=fractlinearfitupper )  # this is the fundamental output power vs input power and is used to calculate the DUT gain in dB from the slope. If the DUT has a loss, this is a negative number
			self.DUTgain[pos]=np.average(np.subtract(self.TOIptt[pos],self.pinDUT[pos]))       # find the DUT gain from the Pout vs Pin curve
			# find TOIs
			# self.TOIl[pos]=self.DUTgain[pos]+((self.TOIbl[pos]-self.DUTgain[pos])/(self.poutm[pos]-self.TOIml[pos])) # output third order intercept point as determined from lower frequency 3rd order product
			# self.TOIh[pos]=self.DUTgain[pos]+((self.TOIbh[pos]-self.DUTgain[pos])/(self.poutm[pos]-self.TOImh[pos])) # output third order intercept point as determined from upper frequency 3rd order product
			self.TOIl[pos]=self.poutm[pos]*((self.TOIbl[pos]-g)/(self.poutm[pos]-self.TOIml[pos]))+g # output third order intercept point as determined from lower frequency 3rd order product
			self.TOIh[pos]=self.poutm[pos]*((self.TOIbh[pos]-g)/(self.poutm[pos]-self.TOImh[pos]))+g # output third order intercept point as determined from upper frequency 3rd order product
			self.TOIavg[pos]=np.average([self.TOIl[pos],self.TOIh[pos]])          # average of lower and upper frequency output third order intercept points (dBm)
			self.fitquality[pos] = min([rl,rh])    # find worst-case fitting "goodness" parameter
			if plotgraphs:         # then plot the IOP graph
				plotTOI(pfund_in=self.pinDUT[pos],pfund_out=self.TOIptt[pos],ptoiL=self.TOIpdl[pos], ptoiH=self.TOIpdh[pos], noisefloor=self.noisefloor[pos], gain=self.DUTgain[pos], ml=self.TOIml[pos], bl=self.TOIbl[pos], mh=self.TOImh[pos], bh=self.TOIbh[pos], mpout=self.poutm[pos], plotfundmax=-self.DUTgain[pos]+self.TOIh[pos]+1., plotfundmin=-self.DUTgain[pos]+self.TOIh[pos] - ((self.TOIh[pos]-self.noisefloor[pos])/3.)-1.)
				print ("output lower TOI =",self.TOIl[pos])
				print ("output upper TOI =",self.TOIh[pos])
				print ("output noise floor =",self.noisefloor[pos])
			self._estimated_gain=self.DUTgain[max(self.DUTgain.keys(),key=(lambda k:self.DUTgain[k]))]      # set estimated gain for setting spectrum analyzer reference level
		return self.TOIl, self.TOIh, self.DUTgain, self.pinDUT,self.TOIptt, self.TOIpdl, self.TOIpdh, self.noisefloor, self.TOIml, self.TOImh, self.poutm, self.TOIbl, self.TOIbh,self.fitquality,self.actualrcoefMA
	###################################################################################################################
	# write TOI data to file
	writefile_TOI=X_writefile_TOI