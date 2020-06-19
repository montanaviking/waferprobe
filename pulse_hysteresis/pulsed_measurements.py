# phil Marsh Carbonics Inc
# measures and saves data for pulsed transfer curves, IV, hysteresis
# this version as of Sept 2018, measures Id (drain current) by using a differential probe to read voltage across a small resistor in the drain circuit (about 1.8ohms). This differential probe
# output is fed into the scope's channel 1 and the gate pulse sample is fed into the scope channel 2.

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
# maximumId_guess - an estimate of the absolute value of the maximum drain current (A) expected for this measurement. This is used to set the worst-case Vds guesses to allow proper scope autoscaling when measuring the drain voltage.
# volttocurrentcalibrationfactor is the conversion factor of the scope channel 1 (output from differential probe) such that volttocurrentcalibrationfactor*scopechannel1voltage = drain current (A) assuming that the differential scope probe gain is set to 100, units are Amps/Volt
# startoffsettime is the actual time (sec) that the pulse starts relative to the trigger
# assumes that the gate drive circuit is terminated in 50ohms

import visa
import collections as c
import scipy as sc
from oscilloscope import OscilloscopeDS1052E
from pulsegenerator import *
from pulse_utilities import *
import time
import numpy as np
from writefile_measured import X_writefile_pulsedtransfer
#import loadpull_system_calibration

class pulsedGate(object):
	def __init__(self,scope=None,pulsegenerator=None,cascadeprobe=None,pulsewidth=None,soaktime=None,quiescentVgs=None,startoffsettime=5.5E-6,startpulselogtime=None,stoppulselogtime=None,pulseVgs_start=None,pulseVgs_stop=None,pulseVgs_step=None,Vds=None,maximumId_guess=50E-3,volttocurrentcalibrationfactor=6.6225E-3):
		if scope==None: raise ValueError("ERROR! No scope specified")
		if pulsegenerator==None: raise ValueError("ERROR! No pulse generator specified")
		if Vds==None or maximumId_guess==None: raise ValueError("ERROR! illegal values for drain voltage or expected Ids ")
		self._maximumId_guess=maximumId_guess                 # expected maximum of the absolute value of drain current (A)
		#self.Vds=Vds                               # drain voltage in off state
		self.__pulse=pulsegenerator                 # handle for controlling scope
		self.__scope=scope                          # handle for controlling pulse generator
		self.__cascadeprobe=cascadeprobe            # handle for probe station control
		self._pulseVgs_start=pulseVgs_start
		self._pulseVgs_stop=pulseVgs_stop
		self._pulseVgs_step=pulseVgs_step
		self._quiescentVgs=quiescentVgs
		self._pulsewidth=pulsewidth
		self._quiescenttime=soaktime
		self._startpulselogtime=startpulselogtime+startoffsettime
		self._stoppulselogtime=stoppulselogtime+startoffsettime
		self._volttocurrentcalibrationfactor=volttocurrentcalibrationfactor
		self.__scope.set_trigger(sweep="single")                        # set scope triggering to capture one pulse then stop - until reset
		self.__scope.stop()                                             # turn off scope data aquisition for now
		self.__scope.set_fulltimescale(fullscale=self._quiescenttime+self._pulsewidth) # set full time scale of scope (full capture time)
		self.__pulse.pulsetrainoff()           # turn off pulse generator
# measure the gate pulsed transfer curve using channel 1
	def measure_transfer_curve(self):
		period=self._pulsewidth+self._quiescenttime
		self.pulseVgs=np.arange(self._pulseVgs_start,self._pulseVgs_stop,self._pulseVgs_step)                       # set up Vgs array - these values are the pulsed values of the gate voltage
		# find actual minimum and maximum drain voltages
		self.Idp=c.deque()
		self.Idt=c.deque()          # time domain current
		self.Vgst=c.deque()         # time domain Vgs driv4
		#self.It=c.deque()
		self.ts=c.deque()
		self.Idp_stddev=c.deque()
		#self.Ids_stddev=c.deque()
		# if self.Vds<2.: probeattenuation=1
		# else: probeattenuation=10
		# loop to measure Id(Vgs_pulse) transfer curve of the DUT
		for pv in self.pulseVgs:
			######### set up scope autoscaling ###################
			if pv<self._quiescentVgs:   # negative-going pulse
				polarity='-'
				autoscalepulsehigh=self._quiescentVgs
				autoscalepulselow=pv
				drainminguessch1=-self._maximumId_guess/self._volttocurrentcalibrationfactor
				drainmaxguessch1=0.
			else:       # pv>self._quiescentVgs positive-going pulse
				polarity="+"
				autoscalepulselow=self._quiescentVgs
				autoscalepulsehigh=pv
				drainminguessch1=0.
				drainmaxguessch1=self._maximumId_guess/self._volttocurrentcalibrationfactor
			self.__scope.set_trigger(level=0.7,sweep="SINGLE")         # default here is that the scope is triggered externally
			self.__scope.set_fulltimescale(fullscale=5*self._pulsewidth)                 # set horizontal scale on scope
			# autoscale scope channel 1 (connected to DUT drain via differential probe)
			minvch1,maxvch1,actualpulsewidth1,actualvoltagelow1,actualvoltagehigh1 = autoscale(pulse=self.__pulse, scope=self.__scope, pulsewidth=2.*self._pulsewidth, period=4*self._pulsewidth, channel=1, scopebottomscale_guess=drainminguessch1, scopetopscale_guess=drainmaxguessch1, pulsegen_min_voltage=autoscalepulselow, pulsegen_max_voltage=autoscalepulsehigh, probeattenuation=1, pulsegeneratoroutputZ=50)
			# autoscale scope channel 2 (on DUT gate voltage)
			minvch2,maxvch2,actualpulsewidth2,actualvoltagelow2,actualvoltagehigh2 = autoscale(pulse=self.__pulse, scope=self.__scope, pulsewidth=2.*self._pulsewidth, period=4*self._pulsewidth, channel=2, scopebottomscale_guess=autoscalepulselow, scopetopscale_guess=autoscalepulsehigh, pulsegen_min_voltage=autoscalepulselow, pulsegen_max_voltage=autoscalepulsehigh, probeattenuation=1, pulsegeneratoroutputZ=50)
			############## done scope autoscaling ###################################
			# set up pulses
			print("pulsed_measurements.py line 110 pulsed gate voltage =",pv)
			# first set range of channel 1 - to measure the DUT drain
			if polarity=="-": self.__pulse.set_pulsesetup_singlepulse(polarity=polarity,pulsewidth=self._pulsewidth,period=self._quiescenttime+self._pulsewidth,voltagelow=pv,voltagehigh=self._quiescentVgs,pulsegeneratoroutputZ=50)    # have a negative-going gate pulse voltage)
			elif polarity=="+": self.__pulse.set_pulsesetup_singlepulse(polarity=polarity,pulsewidth=self._pulsewidth,period=self._quiescenttime+self._pulsewidth,voltagelow=self._quiescentVgs,voltagehigh=pv,pulsegeneratoroutputZ=50)    # have a positive-going gate pulse voltage
			ch1bottomscale=minvch1-0.1*abs(maxvch1-minvch1)
			ch1topscale=maxvch1+0.1*abs(maxvch1-minvch1)
			ch2bottomscale=minvch2-0.1*abs(maxvch2-minvch2)
			ch2topscale=maxvch2+0.1*abs(maxvch2-minvch2)
			self.__scope.set_dualchannel(ch1_bottomscale=ch1bottomscale,ch1_topscale=ch1topscale,ch2_bottomscale=ch2bottomscale,ch2_topscale=ch2topscale)
			actualfulltimescale,actualtimeoffset=self.__scope.set_fulltimescale(fullscale=self._quiescenttime+self._pulsewidth)
			self.actualsoaktime=self.__scope.capture2ndpulse()                                   # capture 2nd pulse and stop scope's data gathering. actualsoaktime is the duration of DC soak voltage application prior to application of the pulse
			print("from pulsed_measurements.py line 106 soaktime=",self.actualsoaktime)
			pulsedata=self.__scope.get_dual_data(R=1./self._volttocurrentcalibrationfactor)                      # capture data vs time up to the total log time specified (self._totallogtime)
			# now find pulse current average over the selected interval
			Idpulsed=[pulsedata["I"][i] for i in range(0,len(pulsedata["t"])) if pulsedata["t"][i]>=self._startpulselogtime and pulsedata["t"][i]<=self._stoppulselogtime]          # find pulsed current waveform by averaging the measured Id across the pulse
			self.Idp.append(np.mean(Idpulsed))                          # find the pulsed current averaged over the time period specified self._stoppulselogtime>t>self._startpulselogtime
			print("from line 111 in pulsed_measurements.py pulsed Vgs, averaged pulsed Id current = ",pv,self.Idp[-1])
			self.Idp_stddev.append(np.std(Idpulsed)/self.Idp[-1])      # find the standard deviation of the pulsed current
			self.Idt.append(pulsedata["I"])                             # Id vs time
			self.Vgst.append(pulsedata["Vch2"])                         # Vgs data vs time
			self.ts.append(pulsedata["t"])                              # timestamp data
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
	while "STOP"!=str(scope.get_trigger_status()): continue
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
# The DUT gate is subjected to triangle wave voltage ramps on the gate and the voltage on the gate is read with channel1 while drain current is read with channel 2
##
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
# volttocurrentcalibrationfactor is the factor used to convert the channel2 oscilloscope voltage to drain current. Units are amps/volt where volt is the displayed voltage on the oscilloscope and
#  amps is the drain current. The default value, 6.6225E-3, is valid for Rdrain (drain resistor in test setup) = 1.8ohm and the differential probe amp gain set to 100.
# average  is the number of averages used to acquire the data
# drainminguess is a guess of the minimum pulsed voltage read on the scope's channel1 used to autoscale the scope channel1
# drainmaxguess is a guess of the maximum pulsed voltage read on the scope's channel1 used to autoscale the scope channel1
# gateterminated indicates whether or not the gate is terminated with a 50ohm termination so as to match the gate pulses and reduce ringing. If so, gateterminated=True if
#       gateterminated=False, then the pulse generator output is adjusted to work into and provide requested voltages to an open circuit rather than 50ohms
# average is exponent i.e. 2**average to give the number of averages for each data point. For average>8, average is rounded up to the next 256 averages so that average=9 gives 2*256 averages and average=10 gives 3*256 averages etc...
# scopetriggerHFfilteron: if True then filter trigger signal (low pass filer) with a cutoff of 150KHz
# when called the first time OR if Vgslow and/or Vgshigh have been changed, then call with setupautoscale=True to autoscale the oscilloscope. This can be bypassed to save time if you're sure it's unnecessary.

def ramped_sweep_gate(scope=None, pulsegenerator=None, period=None, soaktime=1., Vgslow=0., Vgshigh=None, volttocurrentcalibrationfactor=None, average=8, drainminguess=-2., drainmaxguess=0., gateterminated=True,setupautoscale=True,scopetriggerHFfilteron=False):
	if scope==None: raise ValueError("ERROR! No scope specified")
	if pulsegenerator==None: raise ValueError("ERROR! No pulse generator specified")
	if volttocurrentcalibrationfactor==None: raise ValueError("ERROR! voltage to current calibration not set")
	######### set up scope autoscaling ###################
	if Vgshigh<Vgslow:
		autoscalepulsehigh=Vgslow
		autoscalepulselow=Vgshigh
		pulsegenerator.normal()
	else:
		autoscalepulselow=Vgslow
		autoscalepulsehigh=Vgshigh
		pulsegenerator.normal()
	if scopetriggerHFfilteron: scope.set_trigger(level=1.0,sweep="SINGLE",coupling="HF")         # default here is that the scope is triggered externally coupling="HF"  causes the trigger line to reject frequencies > 150KHz. This might be necessary due to mistriggering
	else: scope.set_trigger(level=1.0,sweep="SINGLE")
	scope.set_fulltimescale(fullscale=period)                 # set horizontal scale on scope for autoscaling
	################ scope autoscaling########
	if setupautoscale:
		pulsewidthautoscale=period/2.                      # set pulse width for autoscaling
		# autoscale scope channel 1 (connected to DUT drain via differential probe)
		minvch1,maxvch1,actualpulsewidth1,actualvoltagelow1,actualvoltagehigh1 = autoscale(pulse=pulsegenerator, scope=scope, pulsewidth=pulsewidthautoscale, period=period, channel=1, scopebottomscale_guess=drainminguess, scopetopscale_guess=drainmaxguess, pulsegen_min_voltage=autoscalepulselow, pulsegen_max_voltage=autoscalepulsehigh, probeattenuation=1, pulsegeneratoroutputZ=50)
		# autoscale scope channel 2 (on DUT gate voltage)
		minvch2,maxvch2,actualpulsewidth2,actualvoltagelow2,actualvoltagehigh2 = autoscale(pulse=pulsegenerator, scope=scope, pulsewidth=pulsewidthautoscale, period=period, channel=2, scopebottomscale_guess=autoscalepulselow, scopetopscale_guess=autoscalepulsehigh, pulsegen_min_voltage=autoscalepulselow, pulsegen_max_voltage=autoscalepulsehigh, probeattenuation=1, pulsegeneratoroutputZ=50)
		# set up scope to proper scale
		ch1bottomscale=minvch1-0.2*abs(maxvch1-minvch1)
		ch1topscale=maxvch1+0.2*abs(maxvch1-minvch1)
		ch2bottomscale=minvch2-0.1*abs(maxvch2-minvch2)
		ch2topscale=maxvch2+0.1*abs(maxvch2-minvch2)
		scope.set_dualchannel(ch1_bottomscale=ch1bottomscale,ch1_topscale=ch1topscale,ch2_bottomscale=ch2bottomscale,ch2_topscale=ch2topscale)
	############## done scope autoscaling ###################################
	#pulsegenerator.pulsetrainoff()                      # turn off pulse generator
	if gateterminated: pulsegeneratoroutput="50"
	else:  pulsegeneratoroutput="INF"
	pulsegenerator.ramp(period=period, Vmin=Vgslow, Vmax=Vgshigh, pulsegeneratoroutputZ=pulsegeneratoroutput)
	pulsegenerator.pulsetrainon()
	time.sleep(soaktime)                                # DUT drift stabilization soak (seconds)
	if scopetriggerHFfilteron: scope.set_trigger(level=1.0,sweep="SINGLE",coupling="HF")         # default here is that the scope is triggered externally coupling="HF"  causes the trigger line to reject frequencies > 150KHz. This might be necessary due to mistriggering
	else: scope.set_trigger(level=1.0,sweep="SINGLE")
	actualfulltimescale,actualtimeoffset=scope.set_fulltimescale(fullscale=period)
	if average<=8:
		if average<0: average=0
		scope.set_average(int(pow(2,average)))
		scope.stop()
		scope.run()
		#pulsegenerator.pulsetrainoff()
		ret=scope.get_dual_data(R=0)
		t=list(ret['t'])
		Vgs_raw=list(ret['Vch1'])            # gate voltage vs time
		VId_raw=list(ret['Vch2'])            # proportional to voltage drop across drain resistor vs time
		#deltat=np.average(np.diff(t))   # get delta time for raw scope data
		# remove excess points and use calibration to convert channel1 voltage to a drain current
		timestamps=[t[i] for i in range(0,len(t)) if t[i]<period]
		Id=[volttocurrentcalibrationfactor*VId_raw[i] for i in range(0,len(t)) if t[i]<period]
		Vgs=[Vgs_raw[i] for i in range(0,len(t)) if t[i]<period]
	elif average>8:
		Vgs_array=[]
		Id_array=[]
		for navg256set in range(8,average):
			scope.set_average(256)
			scope.stop()
			scope.run()
			ret=scope.get_dual_data(R=0)
			t=list(ret['t'])
			Vgs_raw=list(ret['Vch1'])            # gate voltage vs time
			VId_raw=list(ret['Vch2'])            # proportional to voltage drop across drain resistor vs time
			# remove excess points and use calibration to convert channel1 voltage to a drain current
			Id_array.append([volttocurrentcalibrationfactor*VId_raw[i] for i in range(0,len(t)) if t[i]<period])
			Vgs_array.append([Vgs_raw[i] for i in range(0,len(t)) if t[i]<period])
		timestamps=[t[i] for i in range(0,len(t)) if t[i]<period]
		#pulsegenerator.pulsetrainoff()
		# now perform higher-level averaging
		Id=np.mean(Id_array,axis=0,dtype=np.float64)
		Vgs=np.mean(Vgs_array,axis=0,dtype=np.float64)
	# introduce the delay in the drain signal relative to the gate which is due to the differential probe's pulse response
	draindelay=0.35E-7
	Ndelay=int(draindelay/np.average(np.diff(t)))       # number of points to delay the gate voltage by
	if Ndelay>1:
		Vgs=[Vgs[i] for i in range(Ndelay,len(Vgs))]        # time delayed gate voltage waveform
		Id=[Id[i] for i in range(0,len(Vgs))]               # truncate Id to keep it the same size as Vgs
		timestamps=[timestamps[i] for i in range(0,len(Vgs))] # truncate timestamps to keep it the same size as Vgs
	# now optionally smooth and consolidate data to reduce number of samples
	return timestamps,Id,Vgs
##################################################################################################################################################################
# produce continuous triangle waveform for gate drive and read the gate voltage vs time on oscilloscope
# def ramped_sweep_Vgs(scope=None, pulsegenerator=None, period=None, soaktime=0., Vgslow=0., Vgshigh=None, average=1, gateminguess=-2., gatemaxguess=0., gateterminated=True,scopechannel=1,triggerLP=False):
# 	if scope==None: raise ValueError("ERROR! No scope specified")
# 	if pulsegenerator==None: raise ValueError("ERROR! No pulse generator specified")
# 	######### set up scope autoscaling ###################
# 	if Vgshigh<Vgslow:
# 		autoscalepulsehigh=Vgslow
# 		autoscalepulselow=Vgshigh
# 		pulsegenerator.normal()
# 	else:
# 		autoscalepulsehigh=Vgshigh
# 		autoscalepulselow=Vgslow
# 		pulsegenerator.normal()
# 	scope.set_trigger(level=1.,sweep="SINGLE")         # default here is that the scope is triggered externally
# 	if triggerLP: scope.set_trigger(sweep="SINGLE",coupling="HF")
# 	scope.set_fulltimescale(fullscale=period)                 # set horizontal scale on scope for autoscaling
# 	pulsewidthautoscale=period/2.                      # set pulse width for autoscaling
# 	minvch1,maxvch1,actualpulsewidth1,actualvoltagelow1,actualvoltagehigh1 = autoscale(pulse=pulsegenerator, scope=scope, pulsewidth=pulsewidthautoscale, period=period, channel=scopechannel, scopebottomscale_guess=gateminguess, scopetopscale_guess=gatemaxguess, pulsegen_min_voltage=autoscalepulselow, pulsegen_max_voltage=autoscalepulsehigh, probeattenuation=1, pulsegeneratoroutputZ=50)
# 	############## done scope autoscaling ###################################
# 	pulsegenerator.pulsetrainoff()                      # turn off pulse generator
# 	if gateterminated: pulsegeneratoroutput="50"
# 	else:  pulsegeneratoroutput="INF"
# 	pulsegenerator.ramp(period=period, Vmin=Vgslow, Vmax=Vgshigh, pulsegeneratoroutputZ=pulsegeneratoroutput)
# 	pulsegenerator.pulsetrainon()
# 	time.sleep(soaktime)                                # DUT drift stabilization soak (seconds)
# 	# set up scope to proper scale
# 	ch1bottomscale=minvch1-0.2*abs(maxvch1-minvch1)
# 	ch1topscale=maxvch1+0.2*abs(maxvch1-minvch1)
#
# 	scope.set_channel(channel=scopechannel,bottomscale=ch1bottomscale,topscale=ch1topscale)
# 	scope.set_average(average)
# 	scope.set_trigger(level=1.,sweep="SINGLE")         # default here is the scope is triggered externally from the pulse generator
# 	actualfulltimescale,actualtimeoffset=scope.set_fulltimescale(fullscale=period)
# 	scope.stop()
# 	scope.run()
# 	while "STOP"!=str(scope.get_trigger_status()): continue
# 	pulsegenerator.pulsetrainoff()
# 	ret=scope.get_data(timerange=period)
#
# 	t=list(ret['t'])                # timestamps
# 	V=list(ret['Vt'])            # gate voltage vs time
#
# 	# remove excess points and use calibration to convert scope voltage to a drain current
# 	timestamps=[t[i] for i in range(0,len(t)) if t[i]<period]
# 	Vgs=[V[i] for i in range(0,len(t)) if t[i]<period]
# 	return timestamps,Vgs

#################################################################################################################################################################################################################
# measure transfer curve from points gathered from continuous triangle waveform
#
# The DUT drain is subjected to triangle wave voltage ramps on the gate and the voltage on the drain is read with channel1 while drain current is read with channel 2
##
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
# volttocurrentcalibrationfactor is the factor used to convert the channel2 oscilloscope voltage to drain current. Units are amps/volt where volt is the displayed voltage on the oscilloscope and
#  amps is the drain current. The default value, 6.6225E-3, is valid for Rdrain (drain resistor in test setup) = 1.8ohm and the differential probe amp gain set to 100.
# average  is the number of averages used to acquire the data
# drainminguess is a guess of the minimum pulsed voltage read on the scope's channel1 used to autoscale the scope channel1
# drainmaxguess is a guess of the maximum pulsed voltage read on the scope's channel1 used to autoscale the scope channel1
# gateterminated indicates whether or not the gate is terminated with a 50ohm termination so as to match the gate pulses and reduce ringing. If so, gateterminated=True if
#       gateterminated=False, then the pulse generator output is adjusted to work into and provide requested voltages to an open circuit rather than 50ohms
# average is exponent i.e. 2**average to give the number of averages for each data point. For average>8, average is rounded up to the next 256 averages so that average=9 gives 2*256 averages and average=10 gives 3*256 averages etc...
# volttocurrentcalibrationfactor=6.5763E-3
def ramped_sweep_drain(scope=None, pulsegenerator=None, period=None, soaktime=1., Vdslow=None, Vdshigh=None, volttocurrentcalibrationfactor=None, average=8, drainminguess=-2., drainmaxguess=0., drainterminated=True,setupautoscale=True):
	if scope==None: raise ValueError("ERROR! No scope specified")
	if pulsegenerator==None: raise ValueError("ERROR! No pulse generator specified")
	if Vdslow==None: raise ValueError("ERROR! no Vdslow value specified")
	if Vdshigh==None: raise ValueError("ERROR! no Vdhigh value specified")
	if volttocurrentcalibrationfactor==None: raise ValueError("ERROR! voltage to current calibration not set")
	if drainterminated: pulsegeneratoroutput="50"
	else:  pulsegeneratoroutput="INF"
	######### set up scope autoscaling ###################
	if Vdshigh<Vdslow:
		autoscalepulsehigh=Vdslow
		autoscalepulselow=Vdshigh
		pulsegenerator.normal()
	else:
		autoscalepulselow=Vdslow
		autoscalepulsehigh=Vdshigh
		pulsegenerator.normal()
	scope.set_trigger(level=1.0,sweep="SINGLE")         # default here is that the scope is triggered externally
	scope.set_fulltimescale(fullscale=period)                 # set horizontal scale on scope for autoscaling
	################ scope autoscaling########
	if setupautoscale:
		pulsewidthautoscale=period/2.                      # set pulse width for autoscaling
		# autoscale scope channel 1 (connected to DUT drain via differential probe)
		minvch1,maxvch1,actualpulsewidth1,actualvoltagelow1,actualvoltagehigh1 = autoscale(pulse=pulsegenerator, scope=scope, pulsewidth=pulsewidthautoscale, period=period, channel=1, scopebottomscale_guess=drainminguess, scopetopscale_guess=drainmaxguess, pulsegen_min_voltage=autoscalepulselow, pulsegen_max_voltage=autoscalepulsehigh, probeattenuation=1, pulsegeneratoroutputZ=pulsegeneratoroutput)
		# autoscale scope channel 2 (on DUT drain voltage)
		minvch2,maxvch2,actualpulsewidth2,actualvoltagelow2,actualvoltagehigh2 = autoscale(pulse=pulsegenerator, scope=scope, pulsewidth=pulsewidthautoscale, period=period, channel=2, scopebottomscale_guess=autoscalepulselow, scopetopscale_guess=autoscalepulsehigh, pulsegen_min_voltage=autoscalepulselow, pulsegen_max_voltage=autoscalepulsehigh, probeattenuation=1, pulsegeneratoroutputZ=pulsegeneratoroutput)
		# set up scope to proper scale
		ch1bottomscale=minvch1-0.2*abs(maxvch1-minvch1)
		ch1topscale=maxvch1+0.2*abs(maxvch1-minvch1)
		ch2bottomscale=minvch2-0.1*abs(maxvch2-minvch2)
		ch2topscale=maxvch2+0.1*abs(maxvch2-minvch2)
		scope.set_dualchannel(ch1_bottomscale=ch1bottomscale,ch1_topscale=ch1topscale,ch2_bottomscale=ch2bottomscale,ch2_topscale=ch2topscale)
	############## done scope autoscaling ###################################
	pulsegenerator.pulsetrainoff()                      # turn off pulse generator
	pulsegenerator.ramp(period=period, Vmin=Vdslow, Vmax=Vdshigh, pulsegeneratoroutputZ=pulsegeneratoroutput)
	pulsegenerator.pulsetrainon()
	time.sleep(soaktime)                                # DUT drift stabilization soak (seconds)
	scope.set_trigger(level=1.0,sweep="SINGLE")         # default here is the scope is triggered externally from the pulse generator
	actualfulltimescale,actualtimeoffset=scope.set_fulltimescale(fullscale=period)
	if average<=8:
		if average<0: average=0
		scope.set_average(int(pow(2,average)))
		scope.stop()
		scope.run()
		ret=scope.get_dual_data(R=0)
		t=list(ret['t'])
		Vds_raw=list(ret['Vch1'])            # drain voltage vs time
		VId_raw=list(ret['Vch2'])            # proportional to voltage drop across drain resistor vs time
		# remove excess points and use calibration to convert channel1 voltage to a drain current
		timestamps=[t[i] for i in range(0,len(t)) if t[i]<period]
		Id=[volttocurrentcalibrationfactor*VId_raw[i] for i in range(0,len(t)) if t[i]<period]
		Vds=[Vds_raw[i] for i in range(0,len(t)) if t[i]<period]
	elif average>8:
		Vds_array=[]
		Id_array=[]
		for navg256set in range(8,average):
			scope.set_average(256)
			scope.stop()
			scope.run()
			ret=scope.get_dual_data(R=0)
			t=list(ret['t'])
			Vds_raw=list(ret['Vch1'])            # drain voltage vs time
			VId_raw=list(ret['Vch2'])            # proportional to voltage drop across drain resistor vs time
			# remove excess points and use calibration to convert channel1 voltage to a drain current
			Id_array.append([volttocurrentcalibrationfactor*VId_raw[i] for i in range(0,len(t)) if t[i]<period])
			Vds_array.append([Vds_raw[i] for i in range(0,len(t)) if t[i]<period])
		timestamps=[t[i] for i in range(0,len(t)) if t[i]<period]
		#pulsegenerator.pulsetrainoff()
		# now perform higher-level averaging
		Id=np.mean(Id_array,axis=0,dtype=np.float64)
		Vds=np.mean(Vds_array,axis=0,dtype=np.float64)
	# introduce the delay in the drain signal relative to the gate which is due to the differential probe's pulse response
	draindelay=0.35E-7
	Ndelay=int(draindelay/np.average(np.diff(t)))       # number of points to delay the gate voltage by
	if Ndelay>1:
		Vds=[Vds[i] for i in range(Ndelay,len(Vds))]        # time delayed gate voltage waveform
		Id=[Id[i] for i in range(0,len(Vds))]               # truncate Id to keep it the same size as Vgs
		timestamps=[timestamps[i] for i in range(0,len(Vds))] # truncate timestamps to keep it the same size as Vgs
	# now optionally smooth and consolidate data to reduce number of samples
	return timestamps,Id,Vds
##################################################################################################################################################################