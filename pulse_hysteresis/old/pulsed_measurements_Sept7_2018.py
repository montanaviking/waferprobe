# phil Marsh Carbonics Inc
# measures and saves data for pulsed transfer curves, IV, hysteresis
# Input Parameters:
# scope - VISA handle for the oscilloscope
# pulsegenerator - VISA handle for the pulse generator
# pulsewidth - the width of the applied gate pulse in seconds i.e. time spent at the pulsed voltage
# soaktime - the time, in seconds, spent at the quiescent voltage prior to application of the gate pulse
# soakvoltage - the voltage applied to the gate for the duration of the soaktime
# startsoaklogtime - the time, in seconds, after application of the pulse, of the start of voltage averaging to obtain the DUT drain soak voltage and current. This is the start time over which the drain voltage is integrated to obtain the soak voltage and current
# stopsoaklogtime - the time, in seconds, after application of the pulse, of the end of voltage averaging to obtain the DUT drain soak voltage and current. This is the ending time over which the drain voltage is integrated to obtain the soak voltage and current
#       The total averaging time to obtain the drain soak voltage is = stopsoaklogtime-startsoaklogtime
# startpulselogtime - the time, in seconds, after application of the pulse, of the start of voltage averaging to obtain the DUT drain pulsed voltage and current. This is the start time over which the drain voltage is integrated to obtain the pulsed voltage and current
# stoppulselogtime - the time, in seconds, after application of the pulse, of the end of voltage averaging to obtain the DUT drain pulsed voltage and current. This is the ending time over which the drain voltage is integrated to obtain the pulsed voltage and current
#       The total averaging time to obtain the drain pulsed voltage is = stoppulselogtime-startpulselogtim
# pulseVgs_start - the first of the array of gate pulse voltages to obtain Id(Vgspulse) - i.e. the gate pulsed transfer curve of the DUT
# pulseVgs_stop - the last of the array of gate pulse voltages to obtain Id(Vgspulse) - i.e. the gate pulsed transfer curve of the DUT
# pulseVgs_step - the Vgs stepsize of the array of gate pulse voltages to obtain Id(Vgspulse) - i.e. the gate pulsed transfer curve of the DUT
# Vds - the drain voltage at zero Id  - i.e. zero drain current. This is used to calculate the DUT drain current from the DUT drain voltage
# maximumId_guess - an estimate of the maximum drain current expected for this measurement. This is used to set the worst-case Vds guesses to allow proper scope autoscaling when measuring the drain voltage.
# R - drain resistance placed between the DUT drain and the drain power supply - used to obtain time-domain DUT Id from the time-domain Vds on the DUT drain.

import visa
import collections as c
import scipy as sc
from oscilloscope import OscilloscopeDS1052E
from pulsegenerator import *
from pulse_utilities import *
import time
import numpy as np
from writefile_measured import X_writefile_pulsedtransfer

class pulsedGate(object):
	def __init__(self,scope=None,pulsegenerator=None,cascadeprobe=None,pulsewidth=None,soaktime=None,soakvoltage=None,startsoaklogtime=None,stopsoaklogtime=None,startpulselogtime=None,stoppulselogtime=None,pulseVgs_start=None,pulseVgs_stop=None,pulseVgs_step=None,Vds=None,maximumId_guess=None,R=None):
		if scope==None: raise ValueError("ERROR! No scope specified")
		if pulsegenerator==None: raise ValueError("ERROR! No pulse generator specified")
		if Vds==None or maximumId_guess==None: raise ValueError("ERROR! illegal values for drain voltage or expected Ids ")
		self._expectedId=maximumId_guess                 # expected maximum drain current
		self.Vds=Vds                               # drain voltage in off state
		self.__pulse=pulsegenerator                 # handle for controlling scope
		self.__scope=scope                          # handle for controlling pulse generator
		self.__cascadeprobe=cascadeprobe            # handle for probe station control
		self._pulseVgs_start=pulseVgs_start
		self._pulseVgs_stop=pulseVgs_stop
		self._pulseVgs_step=pulseVgs_step
		self._soakvoltage=soakvoltage
		self._pulsewidth=pulsewidth
		self._soaktime=soaktime
		self._startpulselogtime=startpulselogtime
		self._stoppulselogtime=stoppulselogtime
		self._startsoaklogtime=startsoaklogtime
		self._stopsoaklogtime=stopsoaklogtime
		self._R=R
		self.__scope.set_trigger(sweep="single")                        # set scope triggering to capture one pulse then stop - until reset
		self.__scope.stop()                                             # turn off scope data aquisition for now
		self.__scope.set_fulltimescale(fullscale=self._stopsoaklogtime) # set full time scale of scope (full capture time)
		self.__pulse.pulsetrainoff()           # turn off pulse generator
# measure the gate pulsed transfer curve using channel 1
	def measure_transfer_curve(self):
		self.pulseVgs=np.arange(self._pulseVgs_start,self._pulseVgs_stop,self._pulseVgs_step)                       # set up Vgs array - these values are the pulsed values of the gate voltage
		if self._pulseVgs_start<self._soakvoltage:
			polarity="-"                                                                                            # gate pulses are negative-going, i.e. the pulsed gate voltage < gate quiescent (soak) voltage
			if self._pulseVgs_stop>=self._soakvoltage: raise ValueError("ERROR! start voltage < soak voltage but stop voltage > soak voltage")
			self.__pulse.set_pulsesetup(polarity=polarity,pulsewidth=self._pulsewidth,period=self._soaktime+self._pulsewidth,voltagelow=self._pulseVgs_start,voltagehigh=self._soakvoltage)     # set up pulse generator for single pulse
		elif self._pulseVgs_start>self._soakvoltage:
			polarity="+"                                                                                            # gate pulses are positive-going, i.e. the pulsed gate voltage > gate quiescent (soak) voltage
			if self._pulseVgs_stop<=self._soakvoltage: raise ValueError("ERROR! start voltage > soak voltage but stop voltage < soak voltage")
			self.__pulse.set_pulsesetup(polarity=polarity,pulsewidth=self._pulsewidth,period=self._soaktime+self._pulsewidth,voltagelow=self._soakvoltage,voltagehigh=self._pulseVgs_start)
		else: raise ValueError("ERROR! pulsed voltage cannot equal soak voltage")

		self.__pulse.set_pulsesetup(polarity=polarity,pulsewidth=self._pulsewidth,period=self._soaktime+self._pulsewidth,)      # set up pulse generator
		self.__pulse.pulsetrainon()                 # turn on pulse generator

		#separate probe from DUT to allow measurement of actual drain voltage without DUT current
		isincontact=self.__cascadeprobe.get_isincontact()
		self.__cascadeprobe.move_separate()
		if polarity=="+":                               # then we are applying positive-going gate pulses and the device is likely n-channel
			mindrainvoltage=self.Vds-self._R*self._expectedId
			maxdrainvoltage=1.2*self.Vds
		elif polarity=="-":                             # then we are applying negative-going gate pulses and the device is likely p-channel e.g. p-channel carbon nanotube transistors
			mindrainvoltage=1.2*self.Vds
			maxdrainvoltage=self.Vds+self._R*self._expectedId
		else: raise ValueError("ERROR illegal value for polarity")
		autoscale(pulse=self.__pulse, scope=self.__scope, pulsewidth=self._pulsewidth, period=max(0.1,3.*self._pulsewidth), channel=1, scopebottomscale_guess=mindrainvoltage, scopetopscale_guess=maxdrainvoltage, pulsegen_min_voltage=-0.1, pulsegen_max_voltage=0.1, probeattenuation=1, pulsegeneratoroutputZ=50)
		self.__pulse.set_pulsesetup(polarity=polarity,pulsewidth=self._pulsewidth,period=self._soaktime+self._pulsewidth,voltagelow=-0.1,voltagehigh=0.1)
		self.__scope.capture2ndpulse()
		vddarray=self.__scope.get_data(R=self._R,timerange=self._stopsoaklogtime,referencevoltage=0.)
		self.Vds=np.average([vddarray["Vt"][i] for i in range(0,len(vddarray["t"])) if vddarray["t"][i]>=self._startpulselogtime and vddarray["t"][i]<=0.95*self._stopsoaklogtime])
		print("from pulsed_measurements.py line 86 Vds=",self.Vds)
		if isincontact: self.__cascadeprobe.move_contact()

		# estimate minimum and maximum drain voltages we expect the scope to see to allow the scope to autorange
		if polarity=="+":                               # then we are applying positive-going gate pulses and the device is likely n-channel
			mindrainvoltage=self.Vds-self._R*self._expectedId
			maxdrainvoltage=1.2*self.Vds
		elif polarity=="-":                             # then we are applying negative-going gate pulses and the device is likely p-channel e.g. p-channel carbon nanotube transistors
			mindrainvoltage=1.2*self.Vds
			maxdrainvoltage=self.Vds+self._R*self._expectedId
		else: raise ValueError("ERROR illegal value for polarity")
		# find actual minimum and maximum drain voltages
		self.Idp=c.deque()
		self.Ids=c.deque()
		self.It=c.deque()
		self.ts=c.deque()
		self.Idp_stddev=c.deque()
		self.Ids_stddev=c.deque()
		if self.Vds<2.: probeattenuation=1
		else: probeattenuation=10

		# loop to measure Id(Vgs_pulse) transfer curve of the DUT
		for pv in self.pulseVgs:
			# set up pulses
			print("pulsed_measurements.py line 110 pulsed gate voltage =",pv)
			# first set range of channel 1 - to measure the DUT drain
			if polarity=="-":  mindrainvoltage,maxdrainvoltage,dummy,dummy,dummy = autoscale(pulse=self.__pulse, scope=self.__scope, pulsewidth=self._pulsewidth, period=max(0.1,3.*self._pulsewidth), channel=1, scopebottomscale_guess=mindrainvoltage, scopetopscale_guess=maxdrainvoltage, pulsegen_min_voltage=pv, pulsegen_max_voltage=self._soakvoltage, probeattenuation=1, pulsegeneratoroutputZ=50)
			elif polarity=="+": mindrainvoltage,maxdrainvoltage,dummy,dummy,dummy = autoscale(pulse=self.__pulse, scope=self.__scope, pulsewidth=self._pulsewidth, period=max(0.1,3.*self._pulsewidth), channel=1, scopebottomscale_guess=mindrainvoltage, scopetopscale_guess=maxdrainvoltage, pulsegen_min_voltage=self._soakvoltage, pulsegen_max_voltage=pv, probeattenuation=1, pulsegeneratoroutputZ=50)
			else: raise ValueError("ERROR! illegal polarity value for pulse")
			if polarity=="-": self.__pulse.set_pulsesetup(polarity=polarity,pulsewidth=self._pulsewidth,period=self._soaktime+self._pulsewidth,voltagelow=pv,voltagehigh=self._soakvoltage)    # have a negative-going gate pulse voltage)
			elif polarity=="+": self.__pulse.set_pulsesetup(polarity=polarity,pulsewidth=self._pulsewidth,period=self._soaktime+self._pulsewidth,voltagelow=self._soakvoltage,voltagehigh=pv)    # have a positive-going gate pulse voltage
			self.actualsoaktime=self.__scope.capture2ndpulse()                                   # capture 2nd pulse and stop scope's data gathering. actualsoaktime is the duration of DC soak voltage application prior to application of the pulse
			print("from pulsed_measurements.py line 119 soaktime=",self.actualsoaktime)
			ps=self.__scope.get_data(R=self._R,timerange=self._stopsoaklogtime,referencevoltage=self.Vds)                      # capture data vs time up to the total log time specified (self._totallogtime)
			# now find pulse current average over the selected interval
			Idpulsed=[ps["Ip"][i] for i in range(0,len(ps["t"])) if ps["t"][i]>=self._startpulselogtime and ps["t"][i]<=self._stoppulselogtime]          # find pulsed current waveform by averaging the measured voltage across the pulse and subtracting the zero-current drain voltage and dividing by the drain resistance
			Idsoak=[ps["Ip"][i] for i in range(0,len(ps["t"])) if ps["t"][i]>=0.5*self._stopsoaklogtime and ps["t"][i]<=0.95*self._stopsoaklogtime]                  # find the soak current waveform by averaging the measured voltage across the pulse and subtracting the zero-current drain voltage and dividing by the drain resistance
			self.Idp.append(np.mean(Idpulsed))                          # find the pulsed current averaged over the time period specified self._stoppulselogtime>t>self._startpulselogtime
			self.Idp_stddev.append(np.std(Idpulsed)/self.Idp[-1])      # find the standard deviation of the pulsed current
			self.Ids.append(np.mean(Idsoak))                            # find the quiescent (soak) current averaged over the time period specified, i.e. the last half of the total time
			self.Ids_stddev.append(np.std(Idsoak)/self.Ids[-1])         # find the standard deviation of the soak current
			#self.It.append(ps["I"])                                     # current waveform at the particular gate pulse amplitude, pv
			#self.ts.apppend(ps["t"])                                    # timestamp array associated with the current waveform at the particular gate pulse amplitude
		return
	writefile_pulsedtransfer = X_writefile_pulsedtransfer
######################################################################################################################################################################################################



#################################################################################################################################################################################################################
# measure transfer curve from points gathered from triangle waveform composed of pulses
#
# The DUT gate is subjected to short pulses pulsing from quescentVgs (long duration portion) to pulsedVgs (short duration portion) where these pulses' maximum amplitudes
# trace out a ramp up (to the maximum absolute value of pulsedVgs) then ramp down profile over a period specified by the parameter "period"
# The oscilloscope's channel2 is used to read the gate voltage pulses
# The oscilloscope's channel1 reads a differential probe which reads the voltage across a 1.8ohm resistor in series with the DUT drain. Channel2 voltage is therefore proportional
# to the DUT instantaneous drain current and the differential probe has a bandwidth of approximately 1MHz
# scope triggering is performed externally from the pulse generator's trigger output
#
#
# scope is the oscilloscope handle
# pulsegenerator is the waveform generator handle
#
# period is the total time to sweep the pulse amplitude from quescentVgs to pulsedVgs back to quescentVgs
# dutycyclefraction is the total fraction of time taken by the pulses at pulsedVgs
# pulsewidth is the width of the individual gate pulses used to make the triangular amplitude sweep of the set of pulses
# soaktime is the time in seconds that the pulse generator and DUT operates prior to making a measurement. This is to allow the DUT to reach close to a steady-state to reduce
#               the effects of threshold drift and hysteresis
# quescentVgs is the quescent gate voltage. This voltage is held throughout the majority of the signal time
# pulseVgs is the pulsed gate voltage. This is the gate voltage which is held during a minority of the signal time where the duty cycle
# volttocurrentcalibrationfactor is the factor used to convert the channel1 oscilloscope voltage to drain current. Units are amps/volt where volt is the displayed voltage on the oscilloscope and
#  amps is the drain current. The default value, 6.6225E-3, is valid for Rdrain (drain resistor in test setup) = 1.8ohm and the differential probe amp gain set to 100.
# average  is the number of averages used to acquire the data
# smoothfactor is the time window relative to the pulse width used to smooth the data and reduce the volumn of data output
# drainminguess is a guess of the minimum pulsed voltage read on the scope's channel1 used to autoscale the scope channel1
# drainmaxguess is a guess of the maximum pulsed voltage read on the scope's channel1 used to autoscale the scope channel1
# gateterminated indicates whether or not the gate is terminated with a 50ohm termination so as to match the gate pulses and reduce ringing. If so, gateterminated=True if
#       gateterminated=False, then the pulse generator output is adjusted to work into and provide requested voltages to an open circuit rather than 50ohms
#
def ramped_sweep_pulsed_gate(scope=None, pulsegenerator=None, period=None, dutycyclefraction=None, pulsewidth=None, soaktime=None, quiescentVgs=0., pulsedVgs=None, volttocurrentcalibrationfactor=6.6225E-3, average=256, smoothfactor=0.2, drainminguess=-2., drainmaxguess=0., gateterminated=True):
	if scope==None: raise ValueError("ERROR! No scope specified")
	if pulsegenerator==None: raise ValueError("ERROR! No pulse generator specified")
	if dutycyclefraction==None: raise ValueError("ERROR! must specify dutycyclefraction")
	if pulsedVgs==None: raise ValueError("ERROR! must specify pulsed gate voltage")

	######### set up scope autoscaling ###################
	if pulsedVgs<quiescentVgs:
		autoscalepulsehigh=quiescentVgs
		autoscalepulselow=pulsedVgs
	else:
		autoscalepulselow=quiescentVgs
		autoscalepulsehigh=pulsedVgs
	scope.set_trigger(level=0.7,sweep="SINGLE")         # default here is that the scope is triggered externally
	scope.set_fulltimescale(fullscale=5*pulsewidth)                 # set horizontal scale on scope
	# autoscale scope channel 1 (connected to DUT drain via differential probe)
	minvch1,maxvch1,actualpulsewidth1,actualvoltagelow1,actualvoltagehigh1 = autoscale(pulse=pulsegenerator, scope=scope, pulsewidth=pulsewidth, period=10*pulsewidth, channel=1, scopebottomscale_guess=drainminguess, scopetopscale_guess=drainmaxguess, pulsegen_min_voltage=autoscalepulselow, pulsegen_max_voltage=autoscalepulsehigh, probeattenuation=1, pulsegeneratoroutputZ=50)
	# autoscale scope channel 2 (on DUT gate voltage)
	minvch2,maxvch2,actualpulsewidth2,actualvoltagelow2,actualvoltagehigh2 = autoscale(pulse=pulsegenerator, scope=scope, pulsewidth=pulsewidth, period=10*pulsewidth, channel=2, scopebottomscale_guess=autoscalepulselow, scopetopscale_guess=autoscalepulsehigh, pulsegen_min_voltage=autoscalepulselow, pulsegen_max_voltage=autoscalepulsehigh, probeattenuation=1, pulsegeneratoroutputZ=50)
	############## done scope autoscaling ###################################

	pulsegenerator.pulsetrainoff()                      # turn off pulse generator
	if gateterminated: pulsegeneratoroutput="50"
	else:  pulsegeneratoroutput="INF"
	pulsegenerator.ramppulses(period=period, quiescentvoltage=quiescentVgs, pulsedvoltage=pulsedVgs, pulsewidth=pulsewidth, dutycyclefraction=dutycyclefraction, pulsegeneratoroutputZ=pulsegeneratoroutput)
	pulsegenerator.pulsetrainon()
	time.sleep(soaktime)                                # DUT drift stabilization soak (seconds)
	ch1bottomscale=minvch1-0.1*abs(maxvch1-minvch1)
	ch1topscale=maxvch1+0.1*abs(maxvch1-minvch1)
	ch2bottomscale=minvch2-0.1*abs(maxvch2-minvch2)
	ch2topscale=maxvch2+0.1*abs(maxvch2-minvch2)
	scope.set_dualchannel(ch1_bottomscale=ch1bottomscale,ch1_topscale=ch1topscale,ch2_bottomscale=ch2bottomscale,ch2_topscale=ch2topscale)

	scope.set_average(average)
	scope.set_trigger(level=0.7,sweep="SINGLE")         # default here is the scope is triggered externally from the pulse generator
	actualfulltimescale,actualtimeoffset=scope.set_fulltimescale(fullscale=period)
	scope.stop()
	scope.run()
	pulsegenerator.pulsetrainoff()
	ret=scope.get_dual_data(R=0)

	t=list(ret['t'])
	V1=list(ret['Vch1'])            # gate voltage vs time
	V2=list(ret['Vch2'])            # proportional to voltage drop across drain resistor vs time
	deltat=np.average(np.diff(t))   # get delta time for raw scope data
	if smoothfactor!=None and smoothfactor>0:
		Nsmooth=int(smoothfactor*pulsewidth/deltat)         # average and consolidate raw data over this window (number of data points)
	else: Nsmooth=0

	if Nsmooth>=2:
		timestamps=[np.average([t[j] for j in range(i-int(Nsmooth/2),i+int(Nsmooth/2))]) for i in range(int(Nsmooth/2),len(t)-int(Nsmooth/2),1) if t[i]<period]
		Id=[volttocurrentcalibrationfactor*np.average([V1[j] for j in range(i-int(Nsmooth/2),i+int(Nsmooth/2))]) for i in range(int(Nsmooth/2),len(V1)-int(Nsmooth/2),1) if t[i]<period]
		Vgs=[np.average([V2[j] for j in range(i-int(Nsmooth/2),i+int(Nsmooth/2))]) for i in range(int(Nsmooth/2),len(V2)-int(Nsmooth/2),1) if t[i]<period]
	else:
		timestamps=[t[i] for i in range(0,len(t)) if t[i]<period]
		Id=[volttocurrentcalibrationfactor*V1[i] for i in range(0,len(t)) if t[i]<period]
		Vgs=[V2[i] for i in range(0,len(t)) if t[i]<period]
	return timestamps,Id,Vgs
#################################################################################################################################################################################################################
# measure transfer curve from points gathered from continuous triangle waveform
#
# The DUT gate is subjected to short pulses pulsing from quescentVgs (long duration portion) to pulsedVgs (short duration portion) where these pulses' maximum amplitudes
# trace out a ramp up (to the maximum absolute value of pulsedVgs) then ramp down profile over a period specified by the parameter "period"
# The oscilloscope's channel2 is used to read the gate voltage pulses
# The oscilloscope's channel1 reads a differential probe which reads the voltage across a 1.8ohm resistor in series with the DUT drain. Channel2 voltage is therefore proportional
# to the DUT instantaneous drain current and the differential probe has a bandwidth of approximately 1MHz
# scope triggering is performed externally from the pulse generator's trigger output
#
#
# scope is the oscilloscope handle
# pulsegenerator is the waveform generator handle
#
# period is the total time to sweep the pulse amplitude from quescentVgs to pulsedVgs back to quescentVgs
# dutycyclefraction is the total fraction of time taken by the pulses at pulsedVgs
# pulsewidth is the width of the individual gate pulses used to make the triangular amplitude sweep of the set of pulses
# soaktime is the time in seconds that the pulse generator and DUT operates prior to making a measurement. This is to allow the DUT to reach close to a steady-state to reduce
#               the effects of threshold drift and hysteresis
# quescentVgs is the quescent gate voltage. This voltage is held throughout the majority of the signal time
# pulseVgs is the pulsed gate voltage. This is the gate voltage which is held during a minority of the signal time where the duty cycle
# volttocurrentcalibrationfactor is the factor used to convert the channel1 oscilloscope voltage to drain current. Units are amps/volt where volt is the displayed voltage on the oscilloscope and
#  amps is the drain current. The default value, 6.6225E-3, is valid for Rdrain (drain resistor in test setup) = 1.8ohm and the differential probe amp gain set to 100.
# average  is the number of averages used to acquire the data
# smoothfactor is the time window relative to the pulse width used to smooth the data and reduce the volumn of data output
# drainminguess is a guess of the minimum pulsed voltage read on the scope's channel1 used to autoscale the scope channel1
# drainmaxguess is a guess of the maximum pulsed voltage read on the scope's channel1 used to autoscale the scope channel1
# gateterminated indicates whether or not the gate is terminated with a 50ohm termination so as to match the gate pulses and reduce ringing. If so, gateterminated=True if
#       gateterminated=False, then the pulse generator output is adjusted to work into and provide requested voltages to an open circuit rather than 50ohms

def ramped_sweep_gate(scope=None, pulsegenerator=None, period=None, soaktime=None, Vgslow=0., Vgshigh=None, volttocurrentcalibrationfactor=6.6225E-3, average=256, smoothtime=None, drainminguess=-2., drainmaxguess=0., gateterminated=True):
	if scope==None: raise ValueError("ERROR! No scope specified")
	if pulsegenerator==None: raise ValueError("ERROR! No pulse generator specified")
	######### set up scope autoscaling ###################
	if Vgshigh<Vgslow:
		autoscalepulsehigh=Vgslow
		autoscalepulselow=Vgshigh
		pulsegenerator.normal()
	else:
		autoscalepulselow=Vgshigh
		autoscalepulsehigh=Vgslow
		pulsegenerator.normal()
	scope.set_trigger(level=0.7,sweep="SINGLE")         # default here is that the scope is triggered externally
	scope.set_fulltimescale(fullscale=period)                 # set horizontal scale on scope for autoscaling
	pulsewidthautoscale=period/2.                      # set pulse width for autoscaling
	# autoscale scope channel 1 (connected to DUT drain via differential probe)
	minvch1,maxvch1,actualpulsewidth1,actualvoltagelow1,actualvoltagehigh1 = autoscale(pulse=pulsegenerator, scope=scope, pulsewidth=pulsewidthautoscale, period=period, channel=1, scopebottomscale_guess=drainminguess, scopetopscale_guess=drainmaxguess, pulsegen_min_voltage=autoscalepulselow, pulsegen_max_voltage=autoscalepulsehigh, probeattenuation=1, pulsegeneratoroutputZ=50)
	# autoscale scope channel 2 (on DUT gate voltage)
	minvch2,maxvch2,actualpulsewidth2,actualvoltagelow2,actualvoltagehigh2 = autoscale(pulse=pulsegenerator, scope=scope, pulsewidth=pulsewidthautoscale, period=period, channel=2, scopebottomscale_guess=autoscalepulselow, scopetopscale_guess=autoscalepulsehigh, pulsegen_min_voltage=autoscalepulselow, pulsegen_max_voltage=autoscalepulsehigh, probeattenuation=1, pulsegeneratoroutputZ=50)
	############## done scope autoscaling ###################################
	pulsegenerator.pulsetrainoff()                      # turn off pulse generator
	if gateterminated: pulsegeneratoroutput="50"
	else:  pulsegeneratoroutput="INF"
	pulsegenerator.ramp(period=period, Vmin=Vgslow, Vmax=Vgshigh, pulsegeneratoroutputZ=pulsegeneratoroutput)
	pulsegenerator.pulsetrainon()
	time.sleep(soaktime)                                # DUT drift stabilization soak (seconds)
	# set up scope to proper scale
	ch1bottomscale=minvch1-0.2*abs(maxvch1-minvch1)
	ch1topscale=maxvch1+0.2*abs(maxvch1-minvch1)
	ch2bottomscale=minvch2-0.1*abs(maxvch2-minvch2)
	ch2topscale=maxvch2+0.1*abs(maxvch2-minvch2)
	scope.set_dualchannel(ch1_bottomscale=ch1bottomscale,ch1_topscale=ch1topscale,ch2_bottomscale=ch2bottomscale,ch2_topscale=ch2topscale)

	scope.set_average(average)
	scope.set_trigger(level=0.7,sweep="SINGLE")         # default here is the scope is triggered externally from the pulse generator
	actualfulltimescale,actualtimeoffset=scope.set_fulltimescale(fullscale=period)
	scope.stop()
	scope.run()
	pulsegenerator.pulsetrainoff()
	ret=scope.get_dual_data(R=0)

	t=list(ret['t'])
	V1=list(ret['Vch1'])            # gate voltage vs time
	V2=list(ret['Vch2'])            # proportional to voltage drop across drain resistor vs time
	#deltat=np.average(np.diff(t))   # get delta time for raw scope data
	# remove excess points and use calibration to convert channel1 voltage to a drain current
	timestamps=[t[i] for i in range(0,len(t)) if t[i]<period]
	Id=[volttocurrentcalibrationfactor*V1[i] for i in range(0,len(t)) if t[i]<period]
	Vgs=[V2[i] for i in range(0,len(t)) if t[i]<period]
	# now optionally smooth and consolidate data to reduce number of samples
	return timestamps,Id,Vgs