# Phil Marsh, Carbonics Inc November 2018

# the following is designed to measure the output third order intercept point (TOI) for carbon nanotube devices:
# This class will measure the TOI vs Vgs and seeks to speed-up the this measurement by having the gate voltage swept using the
# signal generator as the Vgs source with a triangle Vgs waveform.
# the frequency of the Vgs waveform can vary typically from 10Hz to 10KHz but likely will be limited at the high frequency end by
# the need to keep the noise floor low when measuring TOI. A higher Vgs sweep frequency will require a larger resolution bandwidth setting on
# the spectrum analyzer, thus raising its effective noise floor.
#
# The spectrum analyzer which measures the fundamental and third-order products will be set to zero span so as to capture the fundamental and third-order
# RF signal products as functions of time (due to the Vgs waveform)
# we can then obtain the fundamental and 3rd order RF products as functions of Vgs from the corresponding functions of time.
# this class will therefore output the levels in dBm, of the fundamentals and third order products as functions of Vgs as well as the TOI vs Vgs calculated from the former.

# frequencies in Hz power levels in dBm, system TOI is estimated system input third order intercept point in dBm (input of system on output of device under test)

# Inputs to constructor
# spectrum_analyser_input_attenuation                       *** this should be at least 10dB because the spectrum analyser input is a bad match at 0dB attenuation setting
# spectrum_analyzer_cal_factor                              *** this is the spectrum analyzer power reading - actual spectrum analyzer power input (measured by the power meter)
from numpy import unravel_index as uind
#from parameter_analyzer import *
from writefile_measured import *
from amrel_power_supply import *
from spectrum_analyzer import *
from pulsegenerator import *
from HP438A import *
from rf_synthesizer import *
from oscilloscope import *
from pulsed_measurements import ramped_sweep_gate
from loadpull_system_calibration import *
from focustuner import *
from calculated_parameters import *
from read_write_spar_noise import *
from scipy.interpolate import griddata
from calculated_parameters import convertRItoMA
from loadpull_system_calibration import *
#from writefile_measured import X_writefile_TOI_Vgssweep


#from pulsed_measurements import ramped_sweep_gate
from pulse_utilities import *
lowerfrequencysynthesizerdesignator='A'
upperfrequencysynthesizerdesignator='B'
synthesizerpowersetforcalibration=0.    # used to calibrate synthesizer set values to corresponding RF power levels at DUT input. This is the dBm power setting of the RF synthesizers.
acceptableTOIabovenoisefloor=10.        # number dB that a third order product must exceed noise floor to be averaged into the averaged third order product
DUTinputsensor='A'

class IP3_Vgssweep(object):
	def __init__(self,rm=None, lower_rf_synthesizer=None, upper_rf_synthesizer=None, powermeter=None, vgsgen=None,bias=None,sa=None,scope=None,tuner=None,                              # handles for instruments used in this test. When no instrument handle is passed, this class creates the handle in the constructor
				 spectrum_analyser_input_attenuation=10.,powerlevel_minimum=None,powerlevel_maximum=None, powerlevel_step=None,
				 center_frequency=None,frequency_spread=None,spectrum_analyzer_cal_factor=None, outputcalfactoruntuned=None, source_cal_factor=None,usecas1=True,usecas2=True,
				 Vgsperiod=1E-3,Vgsmin=None,Vgsmax=None,syscheckonly=False):
		if probefile!=None:
			cas1=[[probefile,'flip']]
		else: cas1=None
		cas2=[[tuneroutputcable,'noflip']]
		if Vgsmin==None: raise ValueError("ERROR! must specify minimum of gate voltage sweep")
		if Vgsmax==None: raise ValueError("ERROR! must specify maximum of gate voltage sweep")
		self._Vgsmin=Vgsmin
		self._Vgsmax=Vgsmax
		if Vgsperiod==None: raise ValueError("ERROR! must specify period in sec of gate voltage sweep")
		self._settingcallowerfreq=None
		self._settingcalupperfreq=None
		self.Vgsperiod=Vgsperiod
		if rm!=None: self.rm=rm
		else: self.rm=visa.ResourceManager()
		if vgsgen!=None: self.__vgsgen=vgsgen
		else: self.__vgsgen=PulseGeneratorDG1022(self.rm)
		if not syscheckonly:
			if bias!=None: self.__bias=bias
			else: self.__bias=amrelPowerSupply(self.rm)
		self.syscheckonly=syscheckonly
		if sa!=None: self.__sa=sa
		else: self.__sa=SpectrumAnalyzer(self.rm)
		if lower_rf_synthesizer!=None: self.__rflow=lower_rf_synthesizer
		else: self.__rflow=Synthesizer(self.rm,syn=lowerfrequencysynthesizerdesignator)
		if upper_rf_synthesizer!=None: self.__rfhigh=upper_rf_synthesizer
		else: self.__rfhigh=Synthesizer(self.rm,syn=upperfrequencysynthesizerdesignator)
		if scope!=None: self.__scope=scope
		else: self.__scope=OscilloscopeDS1052E(self.rm,shortoutput=True)
		if spectrum_analyzer_cal_factor!=None: self.__spectrum_analyser_cal_factor=spectrum_analyzer_cal_factor     # if specified, use value supplied by the constructor parameter list
		else: self.__spectrum_analyser_cal_factor=sacalfactor           # No constructor parameter list value supplied so use loadpull_system_calibration value
		if spectrum_analyzer_cal_factor!=None: self.__source_cal_factor=source_cal_factor # This is PinDUT-Ppowermeter in dB
		else: self.__source_cal_factor=sourcecalfactor           # then use loadpull_system_calibration value
		# if outputcalfactoruntuned!=None: self.__outputcalfactor=outputcalfactoruntuned
		# else: self.__outputcalfactor=outputcalfactoruntunedTOI     # then use loadpull_system_calibration value
		if powermeter!=None: self.__pmeter=powermeter
		else: self.__pmeter=HP438A(self.rm,calfactorA=powermeterAcalfactor)     # use power meter calibration from loadpull_system_calibration.py

		# set up tuner
		if tuner!=None and tuner!='untuned':
			self.__tuner=tuner
		elif tuner==None:
			S1=None
			S2=None
			if cas1!=None and len(cas1)>0 and usecas1:
			# add the first of the cascaded 2-ports to form S1 - the two-port attached to port 1 of the tuner which is facing the DUT
				if cas1[0][1]=='flip':   S1=spar_flip_ports(read_spar(cas1[0][0]))                      # exchange port 1 with port 2 of the two-port to be cascaded
				else:   S1=read_spar(cas1[0][0])
				del cas1[0]               # remove first 2-port file since its S-parameters have already been added to the first element of the cascade
				for c in cas1:            # c[0] is the S-parameter full filename and c[1] is "flip" or "noflip". "flip" means to transpose ports 1 and 2 of the S-parameters read from the file
					if c[1]=='flip': S1=cascadeSf(S1,spar_flip_ports(read_spar(c[0])))  # then flip ports 1 and 2 on this two-port and cascade it to form the two-port attached to port 1 of the tuner
					else: S1=cascadeSf(S1,read_spar(c[0]))                              # don't flip ports
			#cascade available 2port networks onto port2 of tuner which is the tuner side facing the bias Tee and/or spectrum analyzer
			if cas2!=None and len(cas2)>0 and usecas2:
				# add the first of the cascaded 2-ports to form S1 - the two-port attached to port 1 of the tuner
				if cas2[0][1]=='flip':   S2=spar_flip_ports(read_spar(cas2[0][0]))                      # exchange port 1 with port 2 of the two-port to be cascaded
				else:   S2=read_spar(cas2[0][0])
				del cas2[0]               # remove first 2-port file since its S-parameters have already been added to the first element of the cascade
				for c in cas2:            # c[0] souris the S-parameter full filename and c[1] is "flip" or "noflip". "flip" means to transpose ports 1 and 2 of the S-parameters read from the file
					if c[1]=='flip': S2=cascadeSf(S2,spar_flip_ports(read_spar(c[0])))  # then flip ports 1 and 2 on this two-port and cascade it to form the two-port attached to port 2 of the tuner
					else: S2=cascadeSf(S2,read_spar(c[0]))                              # don't flip ports
			self.__tuner=FocusTuner(S1=S1,S2=S2,tunertype='load')
		else: self.__tuner='untuned'            # we are not using the tuner

		print(self.rm.list_resources())

		self._powerlevel_minimum=powerlevel_minimum            # minimum DUT input power (dBm) tested. This is is the last power level applied
		self._powerlevel_maximum=powerlevel_maximum           # maximum DUT input power (dBm) tested. This is is the last power level applied
		self._powerlevel_step=abs(powerlevel_step)             # DUT input power (dBm) step
		self._flower=center_frequency-frequency_spread/2     # lower fundamental frequency in Hz
		self._fupper=center_frequency+frequency_spread/2     # upper fundamental frequency in Hz
		self.centfreq=center_frequency
		#self._sacalfactor=spectrum_analyzer_cal_factor # dB difference between the tuner output (port 2) (as measured by the power meter) and the spectrum analyzer level. This takes into account the loss between the tuner port 2 (output) and the spectrum analyzer as well as calibration of the spectrum analyzer display
		#self._sourcecalfactor=source_calibration_factor
		self.haveTOI=False                          # This indicates whether we have measured TOI data
		self.haveTOIsearch=False                          # This indicates whether we have measured TOI search data
		# set up spectrum analyzer
		self.__sa.set_attenuation(spectrum_analyser_input_attenuation)
		self.__spectrum_analyser_input_attenuation=spectrum_analyser_input_attenuation
		self.__sa.set_numberaverages(1)

		# set up RF synthesizers
		self.__rflow.off()
		self.__rfhigh.off()
		self.__rflow.set_frequency(self._flower)  # set lower frequency of two-tone
		self.__rfhigh.set_frequency(self._fupper) # set upper frequency of two-tone

		# set up gate pulse generator
		self.__vgsgen.ramp(period=Vgsperiod,Vmin=Vgsmin,Vmax=Vgsmax,pulsegeneratoroutputZ='50')
		self.__vgsgen.pulsetrainoff()

		# set up oscilloscope
		self.__scope.set_trigger(sweep="single")

		# variable initialization
		self.timestamps_gainonly=None       # initialized in self. measure_gainonly()

##################################################################################################################################################################################################################################
# find self._settingcallowerfreq = self.__source_cal_factor+powermeter reading+ power setting of lower frequency tone synthesizer
#  and find self._settingcalupperfreq = self.__source_cal_factor+powermeter reading+ power setting of higher frequency tone synthesizer
# where the powermeter reading refers to the powermeter coupled to the input DUT port. This reading is made with only one of the synthesizers on at a time.
# the self.__source_cal_factor = source_calibration_factor = (dB) is the actual power at the DUT input - that measured at the power sensor connected to the power divider on the input side of the DUT
# this method produces the calibration factors: self._settingcallowerfreq and self._settingcalupperfreq calibration factors as described above
# assumes that the RF synthesizer frequencies have been set
	def __findsourceinputcalibrationfactors(self):
		# turn off both synthesizers
		self.__rflow.off()
		self.__rfhigh.off()
		if 'unleveled'==self.__rflow.set_power(synthesizerpowersetforcalibration):              # set 0dBm on lower-frequency RF source to calibrate its power output
			raise ValueError("ERROR from __findsourceinputcalibrationfactors ! attempt to set lower frequency RF synthesizer above power level at which the power is calibrated")
		powersensorraw=self.__pmeter.readpower(sensor=DUTinputsensor)
		powersetting=self.__rflow.get_power()
		self._settingcallowerfreq=self.__source_cal_factor+powersensorraw-powersetting  # get lower frequency source calibration factor = PinDUT-Psettinglower
		self.__rflow.off()
		if 'unleveled'==self.__rfhigh.set_power(synthesizerpowersetforcalibration):              # set 0dBm on upper-frequency RF source to calibrate its power output
			raise ValueError("ERROR from __findsourceinputcalibrationfactors ! attempt to set upper frequency RF synthesizer above power level at which the power is calibrated")
		powersensorraw=self.__pmeter.readpower(sensor=DUTinputsensor)
		powersetting=self.__rfhigh.get_power()
		self._settingcalupperfreq=self.__source_cal_factor+powersensorraw-powersetting  # get lower frequency source calibration factor = PinDUT-Psettingupper
		self.__rfhigh.off()
		self.__rflow.off()
######################################################################################################################################################################################################################################
##################################################################################################################################################################################################################################
# Sets the RF power referred to the DUT input for the selected RF synthesizer
# return: actual power referred to the DUT input = self.
# Inputs:
# self._settingcallowerfreq: is frequency source calibration factor = PinDUT-Psettinglower in dB where PinDUT is the desired RF lower tone power at the DUT input. Determined from automated measurement in __findsourceinputcalibrationfactors()
# self._settingcalupperfreq: is frequency source calibration factor = PinDUT-Psettingupper in dB where PinDUT is the desired RF upper tone power at the DUT input. Determined from automated measurement in __findsourceinputcalibrationfactors()
# self.__source_cal_factor: is the # This is PinDUT-Ppowermeter in dB which was measured manually for system characterization
# syndesignator selects the RF synthesizer which is to have its output level set. syndesignator='rflow' selects the RF sythesizer which emits the lower-frequency fundamental and syndesignator='rfhigh' selects the RF sythesizer which produces the higher-frequency fundamental
# assumes that the RF synthesizer frequencies have been set and that the power meter is calibrated and has the correct calibration factor set
	def __setDUTinputpower(self,pinDUT=None,syndesignator=None):
		if self.__source_cal_factor==None: raise ValueError("ERROR! have not yet set __source_cal_factor")
		if self._settingcallowerfreq==None or self._settingcalupperfreq==None:
			self.__findsourceinputcalibrationfactors()
		maxloopdberror=0.05
		self.__rflow.off()
		self.__rfhigh.off()
		if syndesignator.lower()==lowerfrequencysynthesizerdesignator.lower():
			powersetting=pinDUT-self._settingcallowerfreq
			if 'unleveled'==self.__rflow.set_power(powersetting):              # set 0dBm on lower-frequency RF source to calibrate its power output
				raise ValueError("ERROR from __findsourceinputcalibrationfactors ! attempt to set lower frequency RF synthesizer above power level at which the power is calibrated")
			settingcallowerfreq=9999999999999.          # ensure that loop runs at least once
			noloops=0
			while abs(settingcallowerfreq-self._settingcallowerfreq)>maxloopdberror and noloops<=maxloopdberror:
				noloops+=1
				powerDUTinputsensor=self.__pmeter.readpower(sensor=DUTinputsensor)           # read input sensor powermeter - raw uncorrected power data
				if powerDUTinputsensor<-99:
					print("WARNING! lower-frequency power below that which can be accurately read")
					return powerDUTinputsensor
				if powerDUTinputsensor>=99:
					print("WARNING! lower-frequency power above that which can be accurately read")
					return powerDUTinputsensor
				settingcallowerfreq=self.__source_cal_factor+powerDUTinputsensor-self.__rflow.get_power()
				print("settingcallowerfreq-self._settingcallowerfreq = ",settingcallowerfreq-self._settingcallowerfreq)
				if abs(settingcallowerfreq-self._settingcallowerfreq)>maxloopdberror:
					print("WARNING lower frequency self._settingcallowerfreq is being corrected")
					self._settingcallowerfreq=settingcallowerfreq
		elif syndesignator.lower()==upperfrequencysynthesizerdesignator.lower():
			powersetting=pinDUT-self._settingcalupperfreq
			if 'unleveled'==self.__rfhigh.set_power(powersetting):              # set 0dBm on lower-frequency RF source to calibrate its power output
				raise ValueError("ERROR from __findsourceinputcalibrationfactors ! attempt to set lower frequency RF synthesizer above power level at which the power is calibrated")
			settingcalupperfreq=9999999999999.          # ensure that loop runs at least once
			noloops=0
			while abs(settingcalupperfreq-self._settingcalupperfreq)>maxloopdberror and noloops<=maxloopdberror:
				noloops+=1
				powerDUTinputsensor=self.__pmeter.readpower(sensor=DUTinputsensor)           # read input sensor powermeter - raw uncorrected power data
				if powerDUTinputsensor<-99:
					print("WARNING! upper-frequency power below that which can be accurately read")
					return powerDUTinputsensor
				if powerDUTinputsensor>=99:
					print("WARNING! upper-frequency power above that which can be accurately read")
					return powerDUTinputsensor
				settingcalupperfreq=self.__source_cal_factor+powerDUTinputsensor-self.__rfhigh.get_power()
				print("settingcalupperfreq-self._settingcallowerfreq = ",settingcalupperfreq-self._settingcalupperfreq)
				if abs(settingcalupperfreq-self._settingcalupperfreq)>0.05:
					print("WARNING lower frequency self._settingcallowerfreq is being corrected ")
					self._settingcallowerfreq=settingcalupperfreq
		else: raise ValueError("ERROR! did not set synthesizer designator")
		PDUTinputmeasured=self.__source_cal_factor+powerDUTinputsensor             # Corrected input DUT power level
		# leave RF synthesizers in off state
		self.__rflow.off()
		self.__rfhigh.off()
		return PDUTinputmeasured
######################################################################################################################################################################################################################################
##################################################################################################################################################################################################################################
# Gets the RF power referred to the DUT input for the selected RF synthesizer
# return: actual power referred to the DUT input
# Inputs:
# self.__source_cal_factor: is the # This is PinDUT-Ppowermeter in dB which was measured manually for system characterization
# syndesignator selects the RF synthesizer which is to have its output level set. syndesignator='rflow' selects the RF sythesizer which emits the lower-frequency fundamental and syndesignator='rfhigh' selects the RF sythesizer which produces the higher-frequency fundamental
# assumes that the RF synthesizer frequencies have been set and that the power meter is calibrated and has the correct calibration factor set
	def __getDUTinputpower(self,syndesignator=None):
		if syndesignator.lower()=='rflow':
			self.__rfhigh.off()
			self.__rflow.on()
			pmeter=self.__pmeter.readpower(sensor=DUTinputsensor)
			if pmeter<-99:
				print("WARNING! lower-frequency power below that which can be accurately read")
				return pmeter
			if pmeter>=99:
				print("WARNING! lower-frequency power above that which can be accurately read")
				return pmeter
			pinDUT=self.__source_cal_factor+pmeter
			self.__rflow.off()
		elif syndesignator.lower()=='rfhigh':
			self.__rflow.off()
			self.__rfhigh.on()
			pmeter=self.__pmeter.readpower(sensor=DUTinputsensor)
			if pmeter<-99:
				print("WARNING! upper-frequency power below that which can be accurately read")
				return pmeter
			if pmeter>=99:
				print("WARNING! upper-frequency power above that which can be accurately read")
				return pmeter
			pinDUT=self.__source_cal_factor+pmeter
			self.__rfhigh.off()
		else: raise ValueError("ERROR! no synthesizer designator given")
		return pinDUT
######################################################################################################################################################################################################################################
######################################################################################################################################################################################################################################
# measure the DUT output third order intercept point for Vgs rapidly swept via the function generator
# DUT output is NOT tuned but at 50ohms and the losses from the DUT output to the spectrum analyzer are quantified by self.__outputcalfactor and the self.__spectrum_analyzer_cal_factor
# produces the DUT gain and TOI vs Vgs
# Pin is the RF power (dBm) for each of the two-tone fundamentals
# 	def measureTOI_gain_untuned(self, Pin=None, Vds=0., draincomp=0.1, gatecomp=5E-6):
# 		if Pin==None:
# 			if (self._powerlevel_minimum==self._plevelevel_maximum) or (self._powerlevel_step==0): Pin=self._powerlevel_minimum
# 		outcorrectiontotal=self.__outputcalfactor+self.__spectrum_analyser_cal_factor      # power output at DUT output - power reading on spectrum analyzer
# 		# set up RF synthesizers
# 		deltaf=self._fupper-self._flower
# 		flower_3rd=self._flower-deltaf
# 		fupper_3rd=self._fupper+deltaf
# 		resolutionbandwidth=200./self.Vgsperiod
# 		videobandwidth=resolutionbandwidth/2
# 		self.__findsourceinputcalibrationfactors() # set RF synthesizer calibration factors to relate the RF synthesizers' level settings to the actual levels at the DUT input
# 		self.__setDUTinputpower(pinDUT=Pin,syndesignator=lowerfrequencysynthesizerdesignator)       # set input power of lower fundamental to DUT input at Pin
# 		self.__setDUTinputpower(pinDUT=Pin,syndesignator=upperfrequencysynthesizerdesignator)       # set input power of upper fundamental to DUT input at Pin
# 		# set up oscilloscope to read gate voltage vs time
#
# 		# set up Vgs (gate voltage triangular wavefunction) sweep generator
# 		Vgstimestamps_raw,Vgs_raw=ramped_sweep_Vgs(scope=self.__scope,pulsegenerator=self.__vgsgen,period=self.Vgsperiod,Vgslow=self._Vgsmin,Vgshigh=self._Vgsmax)              # set and get Vgs waveform vs time
# 		self.__vgsgen.pulsetrainon()
# 		self.__rfhigh.on()
# 		self.__rflow.on()
# 		self.__bias.fetbiason_topgate(Vgs=0,Vds=Vds,gatecomp=gatecomp,draincomp=draincomp,maxchangeId=0.1,maxtime=30.,timeiter=10.)     # turn on drain bias and allow drain current to stabilize
# 		# read the spectrum analyzer uncalibrated power output vs time for the lower fundamental tone
# 		referencelevelsetting,self._flower,measuredpower=self.__sa.measure_peak_level_autoscale(referencelevel=Pin-20.,frequency=self._flower,frequencyspan=10E3,resolutionbandwidth=100,averages=2)
# 		satimestamps_raw,pfundlower_read,self._flower=self.__sa.measure_amplitude_waveform(frequency=self._flower,sweeptime=self.Vgsperiod,resolutionbandwidth=resolutionbandwidth,
# 								videobandwidth=self.videobandwidth,attenuation=self.__spectrum_analyser_input_attenuation,referencelevelguess=referencelevelsetting,numberofaverages=16)
# 		# read the spectrum analyzer uncalibrated power output vs time for the upper fundamental tone
# 		referencelevelsetting,self._fupper,measuredpower=self.__sa.measure_peak_level_autoscale(referencelevel=Pin-20.,frequency=self._fupper,frequencyspan=10E3,resolutionbandwidth=100,averages=2)
# 		t,pfundupper_read,self._fupper=self.__sa.measure_amplitude_waveform(frequency=self._fupper,sweeptime=self.Vgsperiod,resolutionbandwidth=resolutionbandwidth,
# 								 videobandwidth=videobandwidth,attenuation=self.__spectrum_analyser_input_attenuation,referencelevelguess=referencelevelsetting,numberofaverages=16)
# 		# # read the spectrum analyzer uncalibrated power output vs time for the lower third order tone
# 		referencelevelsetting,flower_3rd,measuredpower=self.__sa.measure_peak_level_autoscale(referencelevel=Pin-20.,frequency=flower_3rd,frequencyspan=10E3,resolutionbandwidth=10,averages=4)
# 		t,p3rdlower_read,flower_3rd=self.__sa.measure_amplitude_waveform(frequency=flower_3rd,sweeptime=self.Vgsperiod,resolutionbandwidth=resolutionbandwidth,
# 								 videobandwidth=videobandwidth,attenuation=self.__spectrum_analyser_input_attenuation,referencelevelguess=referencelevelsetting,numberofaverages=64)
# 		# # read the spectrum analyzer uncalibrated power output vs time for the upper third order tone
# 		referencelevelsetting,fupper_3rd,measuredpower=self.__sa.measure_peak_level_autoscale(referencelevel=Pin-20.,frequency=fupper_3rd,frequencyspan=10E3,resolutionbandwidth=10,averages=4)
# 		t,p3rdupper_read,fupper_3rd=self.__sa.measure_amplitude_waveform(frequency=fupper_3rd,sweeptime=self.Vgsperiod,resolutionbandwidth=resolutionbandwidth,
# 								 videobandwidth=videobandwidth,attenuation=self.__spectrum_analyser_input_attenuation,referencelevelguess=referencelevelsetting,numberofaverages=64)
# 		# # correct the RF output powers read vs time, from the spectrum analyzer. Correct them for the losses encountered between the DUT output and display of the spectrum analyzer
# 		pfundlower_raw=list(map(lambda x: x+outcorrectiontotal,pfundlower_read))
# 		pfundupper_raw=list(map(lambda x: x+outcorrectiontotal,pfundupper_read))
# 		p3rdlower_raw=list(map(lambda x: x+outcorrectiontotal,p3rdlower_read))
# 		p3rdupper_raw=list(map(lambda x: x+outcorrectiontotal,p3rdupper_read))
#
# 		maxtimestampint=min(Vgstimestamps_raw[-1],satimestamps_raw[-1])             # find the maximum interpolation time stamp
# 		self.timestamps=np.linspace(start=0,stop=maxtimestampint,num=200)
# 		self.Vgs=[np.interp(t,Vgstimestamps_raw,Vgs_raw) for t in self.timestamps]
# 		self.pfundlower=[np.interp(t,satimestamps_raw,pfundlower_raw) for t in self.timestamps]
# 		self.pfundupper=[np.interp(t,satimestamps_raw,pfundupper_raw) for t in self.timestamps]
# 		self.pfund=np.average([self.pfundlower,self.pfundupper],axis=0)
# 		self.p3rdlower=[np.interp(t,satimestamps_raw,p3rdlower_raw) for t in self.timestamps]
# 		self.p3rdupper=[np.interp(t,satimestamps_raw,p3rdupper_raw) for t in self.timestamps]
# 		self.TOI_lower_Vgsswept=np.add(self.pfund,np.multiply(0.5,np.subtract(self.pfund,self.p3rdlower)))
# 		self.TOI_upper_Vgsswept=np.add(self.pfund,np.multiply(0.5,np.subtract(self.pfund,self.p3rdupper)))
# 		self.TOI_Vgsswept=np.minimum(self.TOI_lower_Vgsswept,self.TOI_upper_Vgsswept)
# 		self.gain_Vgsswept=np.subtract(self.pfund,Pin)
# 		##### debug
# 		f=open("C:/Users/test/python/data/TOI_swept_Vgs/testTOI.xls",'w')
# 		f.write('Vgs\tpfund\t3rdlower\t3rdupper\tTOIlower\tTOIupper\tTOI\tgain')
# 		for i in range(0,len(self.Vgs)):
# 			f.write('\n%10.5E\t%10.5E\t%10.5E\t%10.5E\t%10.5E\t%10.5E\t%10.5E\t%10.5E' % (self.Vgs[i], self.pfund[i], self.p3rdlower[i], self.p3rdupper[i], self.TOI_lower_Vgsswept[i], self.TOI_upper_Vgsswept[i], self.TOI_Vgsswept[i], self.gain_Vgsswept[i]))
# 		f.close()
# 		quit()
# 		#### done debug
# 		return
######################################################################################################################################################################################################################################
######################################################################################################################################################################################################################################
# measure the DUT output third order intercept point for Vgs rapidly swept via the function generator
# DUT output is IS tuned but at 50ohms and the losses from the DUT output to the spectrum analyzer are quantified by self.__outputcalfactor and the self.__spectrum_analyzer_cal_factor
# produces the DUT gain and TOI vs Vgs
# setup: If True then set up Vgs sweep generator
# quickmeasurement: If True, then measure only the lower-frequency fundamental and determine the TOI from this only
	# this should help to speed-up the TOI search of the output impedance plane
# Pin is the RF power (dBm) for each of the two-tone fundamentals
# output reflection is magnitude and angle (degrees)
#
	def measureTOI_gain(self, Pin=None, output_reflection=None,Vds=0., draincomp=0.1,noavg_dist=64,setup=True,quickmeasurement=True):
		if output_reflection==None or len(output_reflection)<1: raise ValueError("ERROR! no tuner reflections given")
		if Pin==None:
			if (self._powerlevel_minimum==self._plevelevel_maximum) or (self._powerlevel_step==0): Pin=self._powerlevel_minimum
		self.Pin=Pin
		self.Vds=Vds
		self.Idaverage=0.
		self.drainstatus='N'
		# set up RF synthesizers
		self.deltafreq=self._fupper-self._flower
		flower_3rd=self._flower-self.deltafreq
		fupper_3rd=self._fupper+self.deltafreq
		self.centfreq=(self._flower+self._fupper)/2.         # center frequency is average of frequencies of two tones
		# set up tuner reflection
		retg=self.__tuner.set_tuner_reflection(frequency=int(1E-6*self.centfreq),gamma=complex(output_reflection[0],output_reflection[1]),gamma_format='ma')          # centfreq is the average frequency of the two-tone input, in Hz -> convert to MHz for this method call
		self.pos=retg['pos']             # tuner mechanical position in string format p1,p2 where p1 is the carriage position and p2 the slug position
		self.actualrcoefMA=retg['gamma_MA']                 # actual reflection coefficient of tuner at position pos (from S1+tuner+S2 using tuner calibration data) magnitude+jangle (deg) (complex number)
		self.actualrcoefRI=retg['gamma_RI']                 # actual reflection coefficient of tuner at position pos (from S1+tuner+S2 using tuner calibration data) real + jimaginary (complex number)
		tuner_loss=-10.*np.log10(retg['gain'])          # get tuner loss in dB (positive number). This is the loss of the composite tuner and includes everything from the output of the DUT to the input of the spectrum analyzer
		####
		outcorrectiontotal=tuner_loss+self.__spectrum_analyser_cal_factor      # power output at DUT output - power reading on spectrum analyzer
		resolutionbandwidthsetting=50./self.Vgsperiod
		resolutionbandwidthsetting_autoscale=4./self.Vgsperiod
		videobandwidthsetting=resolutionbandwidthsetting/2
		#videobandwidthsetting_autoscale=resolutionbandwidthsetting_autoscale/2
		frequencyspan_autoscale=max(20*resolutionbandwidthsetting_autoscale,20E3)            # used to find the precise frequency in order to center the signal in the frequency axis

		self.__findsourceinputcalibrationfactors() # set RF synthesizer calibration factors to relate the RF synthesizers' level settings to the actual levels at the DUT input
		self.__setDUTinputpower(pinDUT=Pin,syndesignator=lowerfrequencysynthesizerdesignator)       # set input power of lower fundamental to DUT input at Pin
		self.__setDUTinputpower(pinDUT=Pin,syndesignator=upperfrequencysynthesizerdesignator)       # set input power of upper fundamental to DUT input at Pin
		# set up oscilloscope to read gate voltage vs time
		self.__rfhigh.on()
		self.__rflow.on()
		self.__vgsgen.pulsetrainon()                    # turn on gate waveform drive
		if setup:
		# set up Vgs (gate voltage triangular wavefunction) sweep generator
			if not self.syscheckonly: err,self.drainstatus,self.Vds,self.Idaverage = self.__bias.setvoltage(Vset=abs(Vds),compliance=draincomp)
			self.Vgstimestamps_raw,self.Id_raw,self.Vgs_raw = ramped_sweep_gate(scope=self.__scope, pulsegenerator=self.__vgsgen, period=self.Vgsperiod,Vgslow=self._Vgsmin,Vgshigh=self._Vgsmax,average=8,volttocurrentcalibrationfactor=volttocurrentcalibrationfactor)
			if not self.syscheckonly: self.Idaverage,Voutactual,self.drainstatus=self.__bias.get_Iout(channel=1)
			   # turn on drain bias and allow drain current to stabilize
			print("from line 387 in IP3_Vgssweep.py IP3_Vgssweep.py self.drainstatus ",self.drainstatus,self.Vds)
			if self.drainstatus!='N':
				print("WARNING! shorted drain!")
				return
		else:
			self.Vgstimestamps_raw,self.Id_raw,self.Vgs_raw = ramped_sweep_gate(scope=self.__scope, pulsegenerator=self.__vgsgen, period=self.Vgsperiod,Vgslow=self._Vgsmin,Vgshigh=self._Vgsmax,average=8,setupautoscale=False,volttocurrentcalibrationfactor=volttocurrentcalibrationfactor)
			if not self.syscheckonly: self.Idaverage,Voutactual,self.drainstatus=self.__bias.get_Iout(channel=1)
				 # turn on drain bias and allow drain current to stabilize
			print("from line 396 IP3_Vgssweep.py self.drainstatus ",self.drainstatus,self.Vds)
			if self.drainstatus!='N':
				print("WARNING! shorted drain!")
				return
		self.__vgsgen.pulsetrainon()

		satimestamps_raw,pfundlower_read,self._flower,self.actualresolutionbandwidth,self.actualvideobandwidth=self.__sa.measure_amplitude_waveform(frequency=self._flower,sweeptime=self.Vgsperiod,resolutionbandwidth=resolutionbandwidthsetting,
								videobandwidth=videobandwidthsetting,attenuation=self.__spectrum_analyser_input_attenuation,numberofaverages=16)
		if not quickmeasurement:
			# read the spectrum analyzer uncalibrated power output vs time for the upper fundamental tone
			referencelevelsetting,self._fupper,measuredpower=self.__sa.measure_peak_level_autoscale(referencelevel=Pin-20.,frequency=self._fupper,frequencyspan=frequencyspan_autoscale,resolutionbandwidth=resolutionbandwidthsetting_autoscale,averages=2)
			t,pfundupper_read,self._fupper,dummy1,dummy2=self.__sa.measure_amplitude_waveform(frequency=self._fupper,sweeptime=self.Vgsperiod,resolutionbandwidth=resolutionbandwidthsetting,
								 videobandwidth=videobandwidthsetting,attenuation=self.__spectrum_analyser_input_attenuation,referencelevelguess=referencelevelsetting,numberofaverages=16)
		# # read the spectrum analyzer uncalibrated power output vs time for the lower third order tone
		referencelevelsetting,flower_3rd,measuredpower=self.__sa.measure_peak_level_autoscale(referencelevel=Pin-20.,frequency=flower_3rd,frequencyspan=frequencyspan_autoscale,resolutionbandwidth=resolutionbandwidthsetting_autoscale,averages=4)
		t,p3rdlower_read,flower_3rd,dummy1,dummy2=self.__sa.measure_amplitude_waveform(frequency=flower_3rd,sweeptime=self.Vgsperiod,resolutionbandwidth=resolutionbandwidthsetting,
								 videobandwidth=videobandwidthsetting,attenuation=self.__spectrum_analyser_input_attenuation,referencelevelguess=referencelevelsetting,numberofaverages=noavg_dist)
		# # read the spectrum analyzer uncalibrated power output vs time for the upper third order tone
		referencelevelsetting,fupper_3rd,measuredpower=self.__sa.measure_peak_level_autoscale(referencelevel=Pin-20.,frequency=fupper_3rd,frequencyspan=frequencyspan_autoscale,resolutionbandwidth=resolutionbandwidthsetting_autoscale,averages=4)
		t,p3rdupper_read,fupper_3rd,dummy1,dummy2=self.__sa.measure_amplitude_waveform(frequency=fupper_3rd,sweeptime=self.Vgsperiod,resolutionbandwidth=resolutionbandwidthsetting,
								 videobandwidth=videobandwidthsetting,attenuation=self.__spectrum_analyser_input_attenuation,referencelevelguess=referencelevelsetting,numberofaverages=noavg_dist)
		# # correct the RF output powers read vs time, from the spectrum analyzer. Correct them for the losses encountered between the DUT output and display of the spectrum analyzer

		maxtimestampint=min(self.Vgstimestamps_raw[-1],satimestamps_raw[-1])             # find the maximum interpolation time stamp
		self.timestamps=np.linspace(start=0,stop=maxtimestampint,num=200).tolist()
		self.Vgs=[np.interp(t,self.Vgstimestamps_raw,self.Vgs_raw) for t in self.timestamps]
		self.Id=[np.interp(t,self.Vgstimestamps_raw,self.Id_raw) for t in self.timestamps]
		pfundlower_raw=list(map(lambda x: x+outcorrectiontotal,pfundlower_read))
		p3rdlower_raw=list(map(lambda x: x+outcorrectiontotal,p3rdlower_read))
		self.pfundlower=[np.interp(t,satimestamps_raw,pfundlower_raw) for t in self.timestamps]
		self.p3rdlower=[np.interp(t,satimestamps_raw,p3rdlower_raw) for t in self.timestamps]
		p3rdupper_raw=list(map(lambda x: x+outcorrectiontotal,p3rdupper_read))
		self.p3rdupper=[np.interp(t,satimestamps_raw,p3rdupper_raw) for t in self.timestamps]
		if not quickmeasurement:
			pfundupper_raw=list(map(lambda x: x+outcorrectiontotal,pfundupper_read))
			self.pfundupper=[np.interp(t,satimestamps_raw,pfundupper_raw) for t in self.timestamps]
			self.pfund=np.average([self.pfundlower,self.pfundupper],axis=0).tolist()
		else:       # if we are doing a quick measurement so did not measure the upper fundamental
			self.pfund=list(self.pfundlower)
		self.TOI_lower_Vgsswept=np.add(self.pfund,np.multiply(0.5,np.subtract(self.pfund,self.p3rdlower))).tolist()
		self.TOI_upper_Vgsswept=np.add(self.pfund,np.multiply(0.5,np.subtract(self.pfund,self.p3rdupper))).tolist()
		self.TOI_Vgsswept=np.minimum(self.TOI_lower_Vgsswept,self.TOI_upper_Vgsswept).tolist()
		self.TOI_over_Pdc_Vgsswept=np.subtract(self.TOI_Vgsswept,np.add(30.,np.multiply(10.,np.log10(np.abs(np.multiply(self.Vds,self.Id)))))).tolist()            # this is the output TOI-Pdc in dB, for all timestamps index: [timestamps]
		self.TOI_over_Pdc_Vgsswept_best=max(self.TOI_over_Pdc_Vgsswept)                                                                             # best case TOI-Pdc (scalar)
		#indextimestampmaxTOI=self.TOI_Vgsswept.index(max(self.TOI_Vgsswept))
		self.gain_Vgsswept=np.subtract(self.pfund,Pin).tolist()
		#self.gain_at_maxTOI_Vgsswept=self.gain_Vgsswept[indextimestampmaxTOI]
		self.haveTOI=True
		return{"Pin":self.Pin,"motorposition":self.pos,"reflection_coefficientMA":self.actualrcoefMA,"reflection_coefficientRI":self.actualrcoefRI,"TOI":self.TOI_Vgsswept,"TOIlower":self.TOI_lower_Vgsswept,"TOIupper":self.TOI_upper_Vgsswept,"timestamps":self.timestamps,"gain":self.gain_Vgsswept,"Vgs":self.Vgs,"Id":self.Id,
			   "pfund":self.pfund,"p3rdlower":self.p3rdlower,"p3rdupper":self.p3rdupper,"Idaverage":self.Idaverage,"drainstatus":self.drainstatus,"resolution_bandwidth":self.actualresolutionbandwidth,"video_bandwidth":self.actualvideobandwidth,"TOIoverPdc":self.TOI_over_Pdc_Vgsswept,"TOIoverPdcbest":self.TOI_over_Pdc_Vgsswept_best}
#####################################################################################################################################################################################################################################
#####################################################################################################################################################################################################################################
# measure the DUT gain for Vgs rapidly swept via the function generator
# DUT output is IS tuned but at 50ohms and the losses from the DUT output to the spectrum analyzer are quantified by self.__outputcalfactor and the self.__spectrum_analyzer_cal_factor
# produces the DUT gain and TOI vs Vgs
# setup: If True then set up Vgs sweep generator

# Pin is the RF power (dBm) for each of the two-tone fundamentals
# output reflection is magnitude and angle (degrees)
#
	def measure_gainonly(self, Pin=None, output_reflection=None, Vds=0., draincomp=0.1, setup=True,frequency=None):
		if output_reflection==None or len(output_reflection)<1: raise ValueError("ERROR! no tuner reflections given")
		if Pin==None:
			if (self._powerlevel_minimum==self._powerlevel_maximum) or (self._powerlevel_step==0): Pin=self._powerlevel_minimum
		self.Pin=Pin
		self.Vds=Vds
		self.Idaverage=0.
		self.drainstatus='N'
		# set up tuner reflection
		if frequency==None: frequency=self.centfreq
		else: self.centfreq=frequency
		retg=self.__tuner.set_tuner_reflection(frequency=int(1E-6*frequency),gamma=complex(output_reflection[0],output_reflection[1]),gamma_format='ma')          # centfreq is the single-tone fundamental, in Hz -> convert to MHz for this method call
		self.pos=retg['pos']             # tuner mechanical position in string format p1,p2 where p1 is the carriage position and p2 the slug position
		self.actualrcoefMA=retg['gamma_MA']                 # actual reflection coefficient of tuner at position pos (from S1+tuner+S2 using tuner calibration data) magnitude+jangle (deg) (complex number)
		self.actualrcoefRI=retg['gamma_RI']                 # actual reflection coefficient of tuner at position pos (from S1+tuner+S2 using tuner calibration data) real + jimaginary (complex number)
		tuner_loss=-10.*np.log10(retg['gain'])          # get tuner loss in dB (positive number). This is the loss of the composite tuner and includes everything from the output of the DUT to the input of the spectrum analyzer
		####
		outcorrectiontotal=tuner_loss+self.__spectrum_analyser_cal_factor      # power output at DUT output - power reading on spectrum analyzer
		resolutionbandwidthsetting=50./self.Vgsperiod
		resolutionbandwidthsetting_autoscale=4./self.Vgsperiod
		videobandwidthsetting=resolutionbandwidthsetting/2
		frequencyspan_autoscale=max(20*resolutionbandwidthsetting_autoscale,20E3)            # used to find the precise frequency in order to center the signal in the frequency axis

		self.__findsourceinputcalibrationfactors() # set RF synthesizer calibration factors to relate the RF synthesizers' level settings to the actual levels at the DUT input using the power meter
		self.__setDUTinputpower(pinDUT=Pin,syndesignator=lowerfrequencysynthesizerdesignator)       # set input power of fundamental to DUT input at Pin
		# set up oscilloscope to read gate voltage vs time
		self.__rfhigh.off()                         # make sure that the upper-frequency synthesizer is off
		self.__rflow.set_frequency(frequency)  # set the frequency of single-tone fundamental
		self.__rflow.on()
		self.__vgsgen.pulsetrainon()                    # turn on gate waveform drive
		if setup:       # often, we only need to set the gate drive and bias once.
		# set up Vgs (gate voltage triangular wavefunction) sweep generator
			if not self.syscheckonly: err,self.drainstatus,self.Vds_actual,self.Idaverage=self.__bias.setvoltage(Vset=abs(Vds),compliance=draincomp)     # turn on drain bias and allow drain current to stabilize
			self.Vgstimestamps_raw,self.Id_raw,self.Vgs_raw = ramped_sweep_gate(scope=self.__scope, pulsegenerator=self.__vgsgen, period=self.Vgsperiod,Vgslow=self._Vgsmin,Vgshigh=self._Vgsmax,average=8,volttocurrentcalibrationfactor=volttocurrentcalibrationfactor)
		# read the spectrum analyzer uncalibrated power output vs time for the fundamental single tone

		#referencelevelsetting,frequency,measuredpower=self.__sa.measure_peak_level_autoscale(referencelevel=Pin-20.,frequency=frequency,frequencyspan=frequencyspan_autoscale,resolutionbandwidth=resolutionbandwidthsetting_autoscale,averages=2)
		satimestamps_raw,pfund_read,frequency,self.actualresolutionbandwidth,self.actualvideobandwidth=self.__sa.measure_amplitude_waveform(frequency=frequency,sweeptime=self.Vgsperiod,resolutionbandwidth=resolutionbandwidthsetting,
								videobandwidth=videobandwidthsetting,attenuation=self.__spectrum_analyser_input_attenuation,numberofaverages=16)
		maxtimestampint=min(self.Vgstimestamps_raw[-1],satimestamps_raw[-1])             # find the maximum interpolation time stamp
		self.timestamps_gainonly=np.linspace(start=0,stop=maxtimestampint,num=200).tolist()
		self.Vgs_gainonly=[np.interp(t,self.Vgstimestamps_raw,self.Vgs_raw) for t in self.timestamps_gainonly]
		self.Id_gainonly=[np.interp(t,self.Vgstimestamps_raw,self.Id_raw) for t in self.timestamps_gainonly]
		pfund_raw=list(map(lambda x: x+outcorrectiontotal,pfund_read))
		self.pfund_gainonly=[np.interp(t,satimestamps_raw,pfund_raw) for t in self.timestamps_gainonly]
		self.gain_gainonly=np.subtract(self.pfund_gainonly,Pin).tolist()
		if not self.syscheckonly: self.__bias.output_off()     # turn off drain bias
		self.__vgsgen.pulsetrainoff()   # turn off gate sweep
		return frequency
#####################################################################################################################################################################################################################################
#####################################################################################################################################################################################################################################
#   search the output reflection plane for the optimum output reflection, gamma opt, presented to the DUT output for TOI while sweeping the gate bias
# this searches for the gamma opt based on the highest output TOI in the entire gate bias sweep
	def TOIsearch(self,Vds=None,Pin=None,initial_output_reflections=None,stopping_criteria=0.5,maximum_tuner_reflection=0.92,maxnumberoftries=12,noavgdist=64,quickmeasurement=True,draincomp=0.1):
		if Pin==None: raise ValueError("ERROR! Pin not specified")
		if Vds==None: raise ValueError("ERROR! Vds not specified")
		self.quickmeasurementTOI=quickmeasurement
		nopts=200       # number of points in real and imaginary reflection coefficient on the Smith chart
		deltagamma=.1     # length of the extrapolation vector of the reflection coefficient when searching outside the tested values of reflection coefficient for the maximum TOI
		deltaTOIstopcriterian=stopping_criteria           # stop search when the current interpolated TOI is within deltaTOIstopcriterian dBm of the last interpolated TOI
		minreflection=-1.
		maxreflection=1.
		TOImaxintlast=-999999            # interpolated maximum TOI (dBm)from last set of measurements set to big initial number to get at least one interation
		self.TOI_maxall=-9999
		#deltagammai=int(deltagamma*nopts/(maxreflection-minreflection))            # number of index points in the reflection used to distance the new points which are outside the ICP (interpolated constellation polygon)
		digamma=(maxreflection-minreflection)/nopts                                  # change in gamma/index point
		gamma_outofICP=-9999999  # fill value for griddata interpolation for reflections outside the convex polygon formed by the reflection data plotted on the Smith chart. This is set very negative soas to always be the smallest value and produce the proper search
		gamma_to_measure=list(initial_output_reflections)        # new gamma points to be measured, start with initial points specified in calling this method. This is an array of pairs i.e. magnitude, phase degrees
		# loop to find output reflection coefficient which gives highest IOP3 average
		notries=0
		# quantities already measured.
		self.Id_measured_search=[]              # drain current (time domain)
		self.gammaMA_measured_search=[]           # output reflection coefficients (magnitude and angle degrees) single reflection coefficient per element [reflection coefficient index]
		self.gammaRI_measured_search=[]           # output reflection coefficients (real+jimaginary) (complex) single reflection coefficient per element [reflection coefficient index]
		self.pos_measured_search=[]             # associated tuner motor positions each element is a single string at a given reflection coefficient [reflection coefficient index]
		self.TOI_measured_search=[]             # associated measured TOI values (minimum between upper and lower tone TOI) dBm where each element is an array over all the swept gate voltages at a given reflection coefficient e.g. self.TOI_measured_search[reflection coefficient index][timestamp index]
		self.gain_measured_search=[]            # associated gains dB at a where each element is an array over all the swept gate voltages at a given reflection coefficient  index [reflection coefficient index][timestamp index]
		self.maxTOI_vsgamma_measured_search=[]          # each element is the maximum TOI associated with a given reflection coefficient index [reflection coefficient index]
		self.gainatmaxTOI_measured_search=[]     # associated gain (dB) at the gate voltage which gives the maximum TOI for the given reflection coefficient index [reflection coefficient index]
		self.pfund_measured_search=[]          # average of fundamental 2-tones (average dBm)  DUT output power index [reflection coefficient index][timestamp index]
		self.p3rdlower_measured_search=[]       # lower-frequency output 3rd order product (dBm) index [reflection coefficient index][timestamp index]
		self.p3rdupper_measured_search=[]       # upper-frequency output 3rd order product (dBm) index [reflection coefficient index][timestamp index]
		self.TOI_lower_measured_search=[]       # output TOI derived from output lower-frequency 3rd order product (dBm) index [reflection coefficient index][timestamp index]
		self.TOI_upper_measured_search=[]       # output TOI derived from output upper-frequency 3rd order product (dBm) index [reflection coefficient index][timestamp index]
		self.TOI_over_Pdc_measured_search=[]    # TOI-Pdc [reflection coefficient index][timestamp index]
		self.TOI_over_Pdc_best_measured_search=[]   # max(TOI-Pdc) [reflection coefficient index]

		#self.pfundlower
		measureTOIsetup=True                    # set up measurement of TOI just once for this TOI search
		while self.TOI_maxall>deltaTOIstopcriterian+TOImaxintlast and notries<maxnumberoftries:                 # loop at least once and stop when there is no significant improvement in the interpolated TOI
			notries+=1
			TOImaxintlast=self.TOI_maxall
			# now find the maximum TOI and other parameters for all the output reflection coefficients to measure (gamma_to_measure array)
			for g in gamma_to_measure:          # gamma_to_measure is array of pairs which are the selected output reflection coefficients (gamma) in the form of real pairs [magnitude,angle] where angle is in degrees
				ret=self.measureTOI_gain(Pin=Pin,output_reflection=g,Vds=Vds,setup=measureTOIsetup,noavg_dist=noavgdist,quickmeasurement=quickmeasurement,draincomp=draincomp)       # measure TOI at user-specified output reflection points ( to establish a search surface )
				if self.drainstatus!='N': return
				measureTOIsetup=False                                                                       # setup Vgs generator drive and Vds only once in the search
				self.pos_measured_search.append(ret['motorposition'])
				self.gammaRI_measured_search.append(ret['reflection_coefficientRI'])        # gamma is in the form real+jimaginary    (complex number)
				self.gammaMA_measured_search.append(ret['reflection_coefficientMA'])        # gamma is in the form real+jangle (degrees)    (complex number)
				self.Id_measured_search.append(ret['Id'])
				self.gain_measured_search.append(ret['gain'])
				self.TOI_measured_search.append(ret['TOI'])
				maxTOI=max(self.TOI_measured_search[-1])                         # get maximum TOI, over the Vgs sweep (timestamps), and its timestamp index for this gamma (g)
				indextimestampmaxTOI=self.TOI_measured_search[-1].index(maxTOI)           # get the timestamp index which has the maximum TOI for the given output reflection (gamma) index
				self.maxTOI_vsgamma_measured_search.append(maxTOI)                       # save the maximum TOI vs time for this gamma (Vgs sweep)
				self.gainatmaxTOI_measured_search.append(self.gain_measured_search[-1][indextimestampmaxTOI])        # get the gain associated with the maximum TOI for this gamma, over the Vgs sweep
				self.pfund_measured_search.append(ret['pfund'])
				self.p3rdlower_measured_search.append(ret['p3rdlower'])
				self.p3rdupper_measured_search.append(ret['p3rdupper'])
				self.TOI_lower_measured_search.append(ret['TOIlower'])
				self.TOI_upper_measured_search.append(ret['TOIupper'])
				self.TOI_over_Pdc_measured_search.append(ret['TOIoverPdc'])
				self.TOI_over_Pdc_best_measured_search.append(ret['TOIoverPdcbest'])      # [gamma index]
			self.Vgs_measured_search=ret['Vgs']                                 # Vgs bias values sweep  (V) vs time [timestamp index]
			self.timestamps_search=ret['timestamps']                            # timestamps of swept Vgs [timestamp index]
			self.TOI_maxall=max(self.maxTOI_vsgamma_measured_search)                                                # best case overall measured TOI for this device (float scalar)
			del gamma_to_measure            # get new set of gammas to measure from the 2D spline fit of TOI on the output gamma plane
			gamma_to_measure=[]             # get new set of gammas to measure from the 2D spline fit of TOI on the output gamma plane
			gamma_real_int = np.linspace(minreflection, maxreflection, nopts)  # real reflection coefficient on the interpolated grid
			gamma_imag_int = np.linspace(minreflection, maxreflection,nopts)  # imaginary reflection coefficient on the interpolated grid
			# 2D cubic spline interpolation (x,y,z) z=self._paraplotint[ii,ir] where ii is the imaginary index and ir the real index find the ICP (interpolated constellation polygon)
			print("from line 469 in IP3_Vgssweep.py size of gamma_measured", len(self.gammaRI_measured_search) )
			self._TOIfit=griddata((np.real(self.gammaRI_measured_search),np.imag(self.gammaRI_measured_search)), self.maxTOI_vsgamma_measured_search, (gamma_real_int[None, :], gamma_imag_int[:, None]), method='cubic', fill_value=gamma_outofICP)
			iiopt,iropt=uind(self._TOIfit.argmax(),self._TOIfit.shape)    # find indices ii, ir, (imaginary rho, real rho) of the reflection coefficients corresponding to highest average output INTERPOLATED TOI.
			TOImaxint=self._TOIfit[iiopt,iropt]     # maximum interpolated TOI from current dataset
			#del gamma_measured
			if self.TOI_maxall>deltaTOIstopcriterian+TOImaxintlast:               # perform calculations only if not done with search
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
					if i_realneg<0: i_realneg=0
					elif i_realneg>199: i_realneg=199
					i_realpos=iropt+int(deltagamma_realpos/digamma)             # real index point of east gamma point to test
					if i_realpos<0: i_realpos=0
					elif i_realpos>199: i_realpos=199
					i_imagneg=iiopt+int(deltagamma_imagneg/digamma)             # imaginary index point of south gamma point to test
					if i_imagneg<0: i_imagneg=0
					elif i_imagneg>199: i_imagneg=199
					i_imagpos=iiopt+int(deltagamma_imagpos/digamma)             # imaginary index point of north gamma point to test
					if i_imagpos<0: i_imagpos=0
					elif i_imagpos>199: i_imagpos=199
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
				self.gammaopt_intMA=convertRItoMA(gammaopt_int)      # convert the interpolated optimum reflection coefficient from real+jimaginary  to [magnitude+jangle]
				gamma_to_measure.append([self.gammaopt_intMA.real,self.gammaopt_intMA.imag])         # add them to the gammas to be measured. Note that this will be the ONLY gamma to measure if the optimum interpolated gamma is within the ICP
				print("from line 564 in IP3_Vgssweep.py gamma_to_measure",gamma_to_measure)

		indexgammamaxTOI=self.maxTOI_vsgamma_measured_search.index(self.TOI_maxall)                        # index (gamma) for best case overall measured TOI for this device (int scalar)
		self.gain_at_TOI_maxall=self.gainatmaxTOI_measured_search[indexgammamaxTOI]                # associated gain at the gamma which produces the best overall TOI (float scalar)
		self.gamma_at_TOI_maxall=self.gammaMA_measured_search[indexgammamaxTOI]                      # associated gamma (output reflection coefficient, magnitude+jngle degrees) which produces the highest overall TOI (complex scalar)
		self.pos_at_TOI_maxall=self.pos_measured_search[indexgammamaxTOI]                           # associated motor position which produces the highest overall TOI (str)
		self.gain_vstimestamp_at_best_gamma=self.gain_measured_search[indexgammamaxTOI]                   # gain vs timestamp at the gamma which produces the highest peak TOI [timestamp index]
		indextimestampmaxTOI=self.TOI_measured_search[indexgammamaxTOI].index(self.TOI_maxall)      # index of timestamp which produced the highest overall TOI
		self.Vgs_at_TOI_maxall=self.Vgs_measured_search[indextimestampmaxTOI]                            # Vgs which produces maximum overall TOI (scalar)

		# quantities sorted according to best TOI in timesteps (Vgs sweep) -> sort low to high TOI. Note that in the following, optimum timestep is the timestep where TOI is maximized for the given gamma
		#self.Vgs_sortedTOI=sortlist(tosort=self.Vgs_measured_search,sortfrom=self.maxTOI_vsgamma_measured_search)
		self.Id_sortedTOI=sortlist(tosort=self.Id_measured_search,sortfrom=self.maxTOI_vsgamma_measured_search)
		self.pfund_sortedTOI=sortlist(tosort=self.pfund_measured_search,sortfrom=self.maxTOI_vsgamma_measured_search)
		self.p3rdlower_sortedTOI=sortlist(tosort=self.p3rdlower_measured_search,sortfrom=self.maxTOI_vsgamma_measured_search)
		self.p3rdupper_sortedTOI=sortlist(tosort=self.p3rdupper_measured_search,sortfrom=self.maxTOI_vsgamma_measured_search)
		self.gamma_sortedTOI=sortlist(tosort=self.gammaMA_measured_search, sortfrom=self.maxTOI_vsgamma_measured_search)            # gamma sorted by maximum TOI attained for each gamma magnitude+jngle degrees index [gamma index]
		self.pos_sortedTOI=sortlist(tosort=self.pos_measured_search, sortfrom=self.maxTOI_vsgamma_measured_search)            # motor position sorted by maximum TOI attained for each gamma magnitude+jngle degrees [gamma index]
		self.TOImax_sortedTOI=sortlist(tosort=self.maxTOI_vsgamma_measured_search, sortfrom=self.maxTOI_vsgamma_measured_search)            # maximum TOI (over timestamps) at optimum timestep sorted by maximum TOI [gamma index]
		self.TOI_sortedTOI=sortlist(tosort=self.TOI_measured_search, sortfrom=self.maxTOI_vsgamma_measured_search)            # TOI vs timestamps at optimum timestep sorted by maximum TOI [gamma index]
		self.TOIupper_sortedTOI=sortlist(tosort=self.TOI_upper_measured_search,sortfrom=self.maxTOI_vsgamma_measured_search)
		self.TOIlower_sortedTOI=sortlist(tosort=self.TOI_lower_measured_search,sortfrom=self.maxTOI_vsgamma_measured_search)
		self.gain_sortedTOI=sortlist(tosort=self.gain_measured_search,sortfrom=self.maxTOI_vsgamma_measured_search)
		self.gainmaxTOI_sortedTOI=sortlist(tosort=self.gainatmaxTOI_measured_search, sortfrom=self.maxTOI_vsgamma_measured_search)     # gain at optimum timestep sorted by TOI [gamma index]
		self.TOI_over_Pdc_sortedTOI=sortlist(tosort=self.TOI_over_Pdc_measured_search, sortfrom=self.maxTOI_vsgamma_measured_search)     # TOI-Pdc (dB) sorted by TOI [gamma index][timestamp]
		self.maxTOI_over_Pdc_sortedTOI=sortlist(tosort=self.TOI_over_Pdc_best_measured_search, sortfrom=self.maxTOI_vsgamma_measured_search)     #  maximum TOI-Pdc (dB) sorted by TOI [gamma index] best at all timestamps at the selected gamma
		self.haveTOIsearch=True

		# now find the time-domain (vs Vgs) parameters for the gamma having the highest TOI in its Vgs sweep
		#if quickmeasurement:
		#  run a full measurement of TOI which includes the upper and lower 3rd order products measurements
		bestgamma=[self.gamma_at_TOI_maxall.real,self.gamma_at_TOI_maxall.imag]                         # best gamma, i.e. gave highest TOI
		ret=self.measureTOI_gain(Pin=Pin,output_reflection=bestgamma,Vds=Vds,noavg_dist=256,quickmeasurement=quickmeasurement)
		if self.drainstatus!='N': return
		self.p3rdlower_vstimestamp_at_best_gamma=ret['p3rdlower']              # lower frequency output 3rd order product (dBm) at gamma which produces the highest TOI [timestamp index]
		self.p3rdupper_vstimestamp_at_best_gamma=ret['p3rdupper']              # upper frequency output 3rd order product (dBm) at gamma which produces the highest TOI [timestamp index]
		self.TOI_lower_vstimestamp_at_best_gamma=ret['TOIlower']              # output TOI derived from lower 3rd order product (dBm) at gamma which produces the highest TOI [timestamp index]
		self.TOI_upper_vstimestamp_at_best_gamma=ret['TOIupper']              # output TOI derived from upper 3rd order product (dBm) at gamma which produces the highest TOI [timestamp index]
		self.TOI_vstimestamp_at_best_gamma=ret['TOI']                     # TOI vs timestamps at the gamma which produces the highest TOI [timestamp index]
		self.pfund_vstimestamp_at_best_gamma=ret['pfund']                     # pfund (dBm) at gamma which produces the highest TOI [timestamp index]
		self.TOI_over_Pdc_at_best_gamma=ret['TOIoverPdc']                   # TOI-Pdc (dB) [timestamp index] at gamma which produces the highest TOI
		self.gain_vstimestamp_at_best_gamma=ret['gain']                           # associated gain at gamma which produces the highest TOI [timestamp index]
		self.TOI_gamma_at_best_gamma=bestgamma
		self.alloff()
		# else:
		# 	self.p3rdlower_vstimestamp_at_best_gamma=self.p3rdlower_measured_search[indexgammamaxTOI]              # lower frequency output 3rd order product (dBm) at gamma which produces the highest TOI [timestamp index]
		# 	self.p3rdupper_vstimestamp_at_best_gamma=self.p3rdupper_measured_search[indexgammamaxTOI]                                               # upper frequency output 3rd order product (dBm) at gamma which produces the highest TOI [timestamp index]
		# 	self.TOI_lower_vstimestamp_at_best_gamma=self.TOI_lower_measured_search[indexgammamaxTOI]              # output TOI derived from lower 3rd order product (dBm) at gamma which produces the highest TOI [timestamp index]
		# 	self.TOI_upper_vstimestamp_at_best_gamma=self.TOI_upper_measured_search[indexgammamaxTOI]              # output TOI derived from upper 3rd order product (dBm) at gamma which produces the highest TOI [timestamp index]
		# 	self.TOI_vstimestamp_at_best_gamma=self.TOI_measured_search[indexgammamaxTOI]                     # TOI vs timestamps at the gamma which produces the highest TOI [timestamp index]
		# 	self.pfund_vstimestamp_at_best_gamma=self.pfund_measured_search[indexgammamaxTOI]                     # average of upper and lower pfund (dBm) at gamma which produces the highest TOI [timestamp index]
#####################################################################################################################################################################################################################################
#####################################################################################################################################################################################################################################
# turn off power supplies and signal sources
	def alloff(self):
		self.__bias.output_off()                                                # turn off power supply
		self.__rflow.off()
		self.__rfhigh.off()
		self.__vgsgen.pulsetrainoff()
#####################################################################################################################################################################################################################################
#####################################################################################################################################################################################################################################
# write TOI data to file
	writefile_TOI_Vgssweep=X_writefile_TOI_Vgssweep
	writefile_Vgssweep_TOIsearch=X_writefile_Vgssweep_TOIsearch
	writefile_gainonly_Vgssweep=X_writefile_gainonly_Vgssweep