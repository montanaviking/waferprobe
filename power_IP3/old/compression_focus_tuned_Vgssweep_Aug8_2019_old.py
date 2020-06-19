from numpy import unravel_index as uind
#from parameter_analyzer import *
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
from writefile_measured import X_writefile_Pcompression_tuned_Vgssweep

spanfund=1.             # frequency span in MHz for spectrum analyzer power measurments
minimumpowermetermeasurement=-25.   # dBm lower limit of raw accurate power meter measurements
maximuminputpowermetermeasurement=20.   # dBm upper limit of raw accurate power meter measurements
maximumoutputpowermetermeasurement=13.5   # dBm upper limit of raw accurate power meter measurements 13.5dBm with LNA
maxrefleveladjusttries=10
#from pulsed_measurements import ramped_sweep_gate
from pulse_utilities import *

synthesizerpowersetforcalibration=-35.    # used to calibrate synthesizer set values to corresponding RF power levels at DUT input. This is the dBm power setting of the RF synthesizers.
acceptableTOIabovenoisefloor=10.        # number dB that a third order product must exceed noise floor to be averaged into the averaged third order product
DUTinputsensor='A'

class Pcomp_Vgssweep(object):
	def __init__(self,rm=None, rf_synthesizer=None, powermeter=None, vgsgen=None,bias=None,sa=None,scope=None,tuner=None,                              # handles for instruments used in this test. When no instrument handle is passed, this class creates the handle in the constructor
	             spectrum_analyser_input_attenuation=10.,powerlevel_minimum=None,powerlevel_maximum=None, powerlevel_step=None,
	             frequency=None,spectrum_analyzer_cal_factor=None, source_cal_factor=None,usecas1=True,usecas2=True,
	             Vgsperiod=1E-3,Vgsmin=None,Vgsmax=None,syscheckonly=False):

		if probefile!=None: cas1=[[probefile,'flip']]
		else: cas1=None
		if tuneroutputcable!=None: cas2=[[tuneroutputcable,'noflip']]
		else: cas2=None
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
		if rf_synthesizer!=None: self.__rf=rf_synthesizer
		else: self.__rf=Synthesizer(rm=rm,syn=DUTinputsensor)
		if scope!=None: self.__scope=scope
		else: self.__scope=OscilloscopeDS1052E(self.rm,shortoutput=True)
		if spectrum_analyzer_cal_factor!=None: self.__spectrum_analyser_cal_factor=spectrum_analyzer_cal_factor
		else: self.__spectrum_analyser_cal_factor=sacalfactor           # then use loadpull_system_calibration value
		if source_cal_factor!=None: self.__source_cal_factor=source_cal_factor # This is PinDUT-Ppowermeter in dB
		else: self.__source_cal_factor=sourcecalfactor           # then use loadpull_system_calibration value
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
					if c[1]=='flip': S2=cascadeSf(S2,spar_flip_ports(read_spar(c[0])))  # then flip ports 1 and 2 on this two-port and cascade it to form the two-port attached to port 1 of the tuner
					else: S2=cascadeSf(S2,read_spar(c[0]))                              # don't flip ports
			self.__tuner=FocusTuner(S1=S1,S2=S2,tunertype='load')
		else: self.__tuner='untuned'            # we are not using the tuner

		print(self.rm.list_resources())

		self.powerlevel_minimum=powerlevel_minimum            # minimum DUT input power (dBm) tested. This is is the last power level applied
		self.powerlevel_maximum=powerlevel_maximum           # maximum DUT input power (dBm) tested. This is is the last power level applied
		self.powerlevel_step=abs(powerlevel_step)             # DUT input power (dBm) step
		self.frequency=frequency     # fundamental frequency in Hz
		self.haveTOI=False                          # This indicates whether we have measured TOI data
		self.haveTOIsearch=False                          # This indicates whether we have measured TOI search data
		# set up spectrum analyzer
		self.__sa.set_attenuation(spectrum_analyser_input_attenuation)
		self.__spectrum_analyser_input_attenuation=spectrum_analyser_input_attenuation
		self.__sa.set_numberaverages(1)

		# set up RF synthesizer
		self.__rf.off()
		self.__rf.set_frequency(self.frequency)  # set fundamental frequency

		# set up gate pulse generator
		self.__vgsgen.ramp(period=Vgsperiod,Vmin=Vgsmin,Vmax=Vgsmax,pulsegeneratoroutputZ='50')
		self.__vgsgen.pulsetrainoff()

		# set up oscilloscope
		self.__scope.set_trigger(sweep="single")

		# variable initialization
		self.timestamps_gainonly=None       # initialized in self. measure_gainonly()
##################################################################################################################################################################################################################################
##################################################################################################################################################################################################################################
# find self._settingcal =PinDUT-Psetting where PinDUT is the actual power at the input of the DUT and Psetting is the synthesizer power setting. This allows setting of the synthesizer power to get a PinDUT, as Psetting=PinDUT-self._settingcal
# This finds the above using: self._settingcal = self._sourcecalfactor+powermeter reading - power setting of  the synthesizer
# where the powermeter reading refers to the powermeter coupled to the input DUT port.
# the self._sourcecalfactor = source_calibration_factor = (dB) is the actual power at the DUT input - that measured at the power sensor connected to the coupler at the input side of the DUT
# this method produces the calibration factors: self._settingcallowerfreq and self._settingcalupperfreq calibration factors as described above
# assumes that the RF synthesizer frequency has been set
	def __findsourceinputcalibrationfactor(self):
		# turn off synthesizer
		self.__rf.off()
		if 'unleveled'==self.__rf.set_power(synthesizerpowersetforcalibration):              # set 0dBm on lower-frequency RF source to calibrate its power output
			raise ValueError("ERROR from __findsourceinputcalibrationfactors ! attempt to set lower frequency RF synthesizer above power level at which the power is calibrated")
		powersensorraw=self.__pmeter.readpower(sensor=DUTinputsensor)
		if powersensorraw<minimumpowermetermeasurement: raise ValueError("ERROR! power sensor reading too low in __findsourceinputcalibrationfactor(). Need to increase synthesizer power synthesizerpowersetforcalibration")
		powersetting=self.__rf.get_power()
		self._settingcal=self.__source_cal_factor+powersensorraw-powersetting  # get source calibration factor = PinDUT-Psettinglower
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
		if 'unleveled'==self.__rf.set_power(powersetting):              # set 0dBm on lower-frequency RF source to calibrate its power output
			print("WARNING from __findsourceinputcalibrationfactors ! unleveled! attempt to set lower frequency RF synthesizer above power level at which the power is calibrated")
		settingcal=9999999999999.          # ensure that loop runs at least once
		noloops=0
		while abs(settingcal-self._settingcal)>maxloopdberror and noloops<=maxloopdberror:
			noloops+=1
			powerDUTinputsensor=self.__pmeter.readpower(sensor=DUTinputsensor)           # read input sensor powermeter - raw uncorrected power data
			if powerDUTinputsensor<minimumpowermetermeasurement:
				print(" input power meter raw data = ",powerDUTinputsensor)
				print("WARNING!  power meter A level too low for input power meter")
			if powerDUTinputsensor>maximuminputpowermetermeasurement:
				print(" input power meter raw data = ",powerDUTinputsensor)
				print("WARNING!  power meter A level too high for input power meter")
			settingcal=self.__source_cal_factor+powerDUTinputsensor-self.__rf.get_power()
			print("settingcal-self._settingcal = ",settingcal-self._settingcal)
			if abs(settingcal-self._settingcal)>maxloopdberror:
				print("WARNING self._settingcal is being corrected")
				self._settingca=settingcal
		PDUTinputmeasured=self.__source_cal_factor+powerDUTinputsensor             # Corrected input DUT power level
		# leave RF synthesizer in off state
		if not on: self.__rf.off()         # leave in off state if this is requested
		return PDUTinputmeasured        # dBm
######################################################################################################################################################################################################################################
#####################################################################################################################################################################################################################################
# measure the DUT gain for Vgs rapidly swept via the function generator
# DUT output is IS tuned but at 50ohms and the losses from the DUT output to the spectrum analyzer are quantified by self.__outputcalfactor and the self.__spectrum_analyzer_cal_factor
# produces the DUT gain and TOI vs Vgs
# setup: If True then set up Vgs sweep generator

# Pin is the RF power (dBm) for each of the two-tone fundamentals
# output reflection is magnitude and angle (degrees)
#
	def measure_gainonly(self, Pin=None, output_reflection=None, Vds=0., draincomp=0.1, setup=True):
		if output_reflection==None or len(output_reflection)<1: raise ValueError("ERROR! no tuner reflections given")
		if Pin==None:
			if (self.powerlevel_minimum==self.powerlevel_maximum) or (self.powerlevel_step==0): Pin=self.powerlevel_minimum
		self.Pin=Pin
		self.Vds=Vds
		self.Idaverage=0.
		self.drainstatus='N'
		# set up tuner reflection
		retg=self.__tuner.set_tuner_reflection(frequency=int(1E-6*self.frequency),gamma=complex(output_reflection[0],output_reflection[1]),gamma_format='ma')          # centfreq is the single-tone fundamental, in Hz -> convert to MHz for this method call
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

		self.__findsourceinputcalibrationfactor() # set RF synthesizer calibration factor to relate the RF synthesizers' level settings to the actual levels at the DUT input
		self.__setDUTinputpower(pinDUT=Pin)       # set input power of fundamental to DUT input at Pin
		# set up RF synthesizer
		self.__rf.on()
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
		#referencelevelsetting,frequency,measuredpower=self.__sa.measure_peak_level_autoscale(referencelevel=Pin-20.,frequency=frequency,frequencyspan=frequencyspan_autoscale,resolutionbandwidth=resolutionbandwidthsetting_autoscale,averages=2)
		satimestamps_raw,pfund_read,self.frequency,self.actualresolutionbandwidth,self.actualvideobandwidth=self.__sa.measure_amplitude_waveform(frequency=self.frequency,sweeptime=self.Vgsperiod,resolutionbandwidth=resolutionbandwidthsetting,
		                        videobandwidth=videobandwidthsetting,attenuation=self.__spectrum_analyser_input_attenuation,numberofaverages=16)
		maxtimestampint=min(self.Vgstimestamps_raw[-1],satimestamps_raw[-1])             # find the maximum interpolation time stamp
		self.timestamps_gainonly=np.linspace(start=0,stop=maxtimestampint,num=200).tolist()
		self.Vgs_gainonly=[np.interp(t,self.Vgstimestamps_raw,self.Vgs_raw) for t in self.timestamps_gainonly]
		self.Id_gainonly=[np.interp(t,self.Vgstimestamps_raw,self.Id_raw) for t in self.timestamps_gainonly]
		pfund_raw=list(map(lambda x: x+outcorrectiontotal,pfund_read))
		self.pfund_gainonly=[np.interp(t,satimestamps_raw,pfund_raw) for t in self.timestamps_gainonly]
		self.gainonly=np.subtract(self.pfund_gainonly,Pin).tolist()
#####################################################################################################################################################################################################################################
#####################################################################################################################################################################################################################################
# Measure gain compression with swept Vgs
# increase Pin levels until only the selected timestamp values indicated by mintimecompress and maxtimecompress time interval gain data are compressed to or exceeding the compression target = compressiontarget
# self.powerlevel_maximum is the maximum allowable input power in dBm allowed during this test, can be overridden by argument
# self.powerlevel_minimum is the starting power level of this test, lowest power level used (dBm), can be overridden by argument
# self.powerlevel_step is the step of the input power level, dB, can be overridden by argument
#
	def measurePcomp(self,compressiontarget=1.,output_reflection=[0.,0.],powerlevel_maximum=None,powerlevel_minimum=None,powerlevel_step=None,mincompressiontime=0,maxcompressiontime=99999,Vds=0.,frequency=None,draincomp=0.1):
		numberoflinearpts=2         # this is the number of pin points used to calculate the gain
		if frequency!=None:
			self.frequency=frequency
		self.output_reflection=output_reflection
		if self.frequency==None or self.frequency<10E6: raise ValueError("ERROR! invalid or no frequency given")
		if powerlevel_maximum!=None: self.powerlevel_maximum=powerlevel_maximum
		if self.powerlevel_maximum==None: raise ValueError("ERROR! Invalid powerlevel_maximum value")
		if powerlevel_minimum!=None: self.powerlevel_minimum=powerlevel_minimum
		if self.powerlevel_minimum==None: raise ValueError("ERROR! Invalid powerlevel_minimum value")
		if self.powerlevel_maximum<self.powerlevel_maximum: raise ValueError("ERROR! powerlevel_minimum>powerlevel_maximum")
		if powerlevel_step!=None: self.powerlevel_step=powerlevel_step
		if self.powerlevel_step==None or self.powerlevel_step<0.: raise ValueError("ERROR! invalid powerlevel_step")
		if powerlevel_minimum!=None: self.powerlevel_minimum=powerlevel_minimum
		if self.powerlevel_minimum==None: raise ValueError("ERROR! invalid powerlevel_minimum_compression")
		self.mincompressiontime=mincompressiontime
		self.maxcompressiontime=maxcompressiontime
		if self.mincompressiontime<0.: self.mincompressiontime=0.
		self.gaincompression=[]
		self.compressiontarget=compressiontarget
		# this loop is used to drive the DUT into compression and measure the gain
		ncompts=int((self.powerlevel_maximum-self.powerlevel_minimum)/self.powerlevel_step)+1
		pcomp_gain=[]              # [pin index][timestamp index], gain in dB
		pcomp_pfund=[]             # [pin index][timestamp index], fundamental output power from DUT
		#self.pcomp_compression=[]           # [pin index][timestamp index], gain compression in dB
		self.pcomp_pin=np.linspace(start=self.powerlevel_minimum,stop=self.powerlevel_maximum,num=ncompts)

		for ip in range(0,len(self.pcomp_pin)):          # gain is assumed to be linear (unchanging) for first numberoflinearpts pin points
			if ip==0: setup=True
			else: setup=False
			self.measure_gainonly(Pin=self.pcomp_pin[ip],output_reflection=self.output_reflection,Vds=Vds,draincomp=draincomp,setup=setup)
			pcomp_gain.append(self.gainonly)     # gain vs [input power index][time index]
			pcomp_pfund.append(self.pfund_gainonly)     # output power vs pin [input power index][time index]
			print("from line 277 in compression_focus_tuned_Vgssweep.py pin setting ",self.pcomp_pin[ip],pcomp_gain[ip])
			if len(pcomp_gain)==numberoflinearpts:   # then get the linear gain from only the first (lowest pin) numberoflinearpts
				self.pcomp_lineargain=[np.average([pcomp_gain[ipin][it] for ipin in range(0,numberoflinearpts)]) for it in range(0,len(self.timestamps_gainonly))]            # linear gain vs time [index timestamp], calculated only for the lowest numberoflinearpts points of pin
		# find compression
			# do this calculation just once for each input power level since it won't
			if ip==0:
				if self.maxcompressiontime>self.timestamps_gainonly[-1]: self.maxcompressiontime=self.timestamps_gainonly
				timestampminindex=findnearest(self.timestamps_gainonly,self.mincompressiontime)
				timestampmaxindex=findnearest(self.timestamps_gainonly,self.maxcompressiontime)

			# if len(pcomp_gain)>numberoflinearpts:
			# 	if min(np.subtract(self.pcomp_lineargain,pcomp_gain[-1][timestampminindex:timestampmaxindex+1]))>(1.5+compressiontarget):
			# 		break       # jump out of loop because we already have compression
		pcomp_compression=[list(np.subtract(self.pcomp_lineargain,p)) for p in pcomp_gain]       # indices are [pin index][timestamp index]
		# now transform all parameters to swap indices so that indices are now [timestamp index][pin index]
		self.pcomp_gain=list(np.array(pcomp_gain).transpose())    # [timestamp index][pin index] this is the DUT gain dB
		self.pcomp_pfund=list(np.array(pcomp_pfund).transpose())  # [timestamp index][pin index]            This is the DUT fundamental power output
		self.pcomp_compression=list(np.array(pcomp_compression).transpose())  # [timestamp index][pin index] This is the compression (reduction) of gain from its small signal value
		# now find compression points vs timestamps
		# debug
		ft=UnivariateSpline(self.pcomp_pin,np.subtract(self.pcomp_compression[0],compressiontarget),k=3)          # spline fit of difference between gain compression
		rt_=ft.roots()
		# end of debug
		functsplinepcomp=[UnivariateSpline(self.pcomp_pin,np.subtract(self.pcomp_compression[it],compressiontarget),k=3) for it in range(0,len(self.pcomp_compression))]
		pcomp_inputcompressionpoints=[functsplinepcomp[it].roots()[-1] if len(functsplinepcomp[it].roots())>0 else -999 for it in range(0,len(self.timestamps_gainonly)) ] # first input compression point vs timestamp [index timestamp]
		self.outputcompressionpoints=[pcomp_inputcompressionpoints[it]+self.pcomp_lineargain[it]-compressiontarget if pcomp_inputcompressionpoints[it]!=-999 else -999 for it in range(0,len(pcomp_inputcompressionpoints))]  # output compression points. If none for a given timestep index, then set value to -999 [index timestamp]
		self.maxoutputcompression=max(self.outputcompressionpoints)         # maximum output compression
#####################################################################################################################################################################################################################################
#####################################################################################################################################################################################################################################
# turn off power supplies and signal sources
	def alloff(self):
		self.__bias.output_off()                                                # turn off power supply
		self.__rf.off()
		self.__vgsgen.pulsetrainoff()
#####################################################################################################################################################################################################################################
	writefile_Pcompression_tuned_Vgssweep=X_writefile_Pcompression_tuned_Vgssweep