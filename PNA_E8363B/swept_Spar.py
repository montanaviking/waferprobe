# measures S-parameters and Id vs time and parameterized to Vgs(t) or Vds(t)
# drain voltage is constant


import visa
import PyQt5
import numpy as np
from oscilloscope import *
from amrel_power_supply import *
from pulsegenerator import *
from pulsed_measurements import ramped_sweep_gate
from loadpull_system_calibration import *               # gets the calibration parameter to convert the differential voltage to Id
rm = visa.ResourceManager()
from pna import *
from amrel_power_supply import *
from pulsegenerator import *
from oscilloscope import *
from calculated_parameters import *

# measure S-parameters vs time for a Vgs or Vds sweep. This swept voltage is Vswept. User determines with setup and calling code whether the
# gate or drain voltage is swept.
# Calling parameters (inputs)
# rm is the VISA resource manager
# sweepfrequency is that of the triangle-wave Vswept representing Vgs or Vds sweep and is in Hz
# PNApower is the PNA port power in dBm. This should be unchanged from that used in the calibration!
# PNAaverage is the number of PNA time sweeps which are averaged to produce the S-parameters vs time. Averaging reduces measurement uncertainty
# sweepfrequency is the frequency (Hz) rate at which the triangle-wave Vgs or Vds is swept
# Vsweptmax is the maximum sweep voltage
# Vsweptmin is the minimum sweep volage
# Vconstbias is the constant voltage bias (Vds or Vgs). If the drain voltage is swept, then Vconstbias is the gate voltage and vice-versa.
# holdtime is the time in seconds that the DUT is allowed to equalibriate with before the first measurements
# RFfrequency_start is the first RF frequency of the S-parameters vs time measurement in Hz
# RFfrequency_stop is the last RF frequency of the S-parameters vs time measurement in Hz
# RFfrequency_step is the RF frequency step of the S-parameters vs time measurement in Hz
# Note that the following function assumes that one has provided the correct instrument state file for S-parameters vs time, named "2port_time.sta" and
# also a valid calibration stored in "CalSet_1". RFfrequency_start and RFfrequency_stop much lie within the range of that specified in "CalSet_1".

# outputs
# full 2-port S-parameters vs RF frequency and time
# spar['typeS']['frequency_MHz'][itime] where 'typeS' is the S-parameter type, e.g. s11,s21,s12,s22; 'frequency_MHz' is the measurement frequency in MHz,
# and itime is the timestamp index. Note that all four S-parameters are measured in one measurement set of timestamps for each RF frequency.
#
# Drain current (Id) vs RF frequency and time. Note that the drain current should not be expected to change much as a function of the measurement frequency, however,
# Id is measured separately for each RF frequency measurement set so that it's guaranteed to be associated with the corresponding S-parameter measurements.
# id['frequency_MHz'][itime]
#
# Gate voltage or drain voltage (Vswept) vs RF frequency and time.
# Gate voltage or drain voltage (Vswept) is measured separately for each RF frequency measurement set so that it's guaranteed to be associated with the corresponding S-parameter
# measurements.
# Vswept['frequency_MHz'][itime]
#
# timestamps[itime]
def swept_Spar(rm=None, pna=None, vgsgen=None, Vconstbiassupply=None, scope=None, gatesweep=True,instrumentstate="",calset="", PNAaverage=32, sweepfrequency=1E3, Vsweptmax=0., Vsweptmin=-1, Vconstbias=-1, holdtime=0, RFfrequency_start=None, RFfrequency_stop=None, RFfrequency_step=None, DCcomp=0.1, offsettime=0.):
	if(Vsweptmax<=Vsweptmin): raise ValueError("ERROR! maximum Vswept must be > minimum Vswept")
	if(RFfrequency_start==None or RFfrequency_stop==None or RFfrequency_step==None or (RFfrequency_start>RFfrequency_stop)):
		raise ValueError("ERROR! invalid or missing RF frequency parameters")
	if(RFfrequency_start==RFfrequency_stop): RFfrequencies=[RFfrequency_start]
	else: RFfrequencies = np.linspace(RFfrequency_start,RFfrequency_stop,int((RFfrequency_stop-RFfrequency_start)/RFfrequency_step))
	sweepperiod=1/sweepfrequency             # period (sec) of the Vswept sweep
	if pna==None: pna=Pna(rm=rm)                     # network analyzer
	if vgsgen==None: vgsgen=PulseGeneratorDG1022(rm)         # pulse generator
	if Vconstbiassupply==None: Vconstbiassupply=amrelPowerSupply(rm)          # DC drain supply
	if scope==None: scope=OscilloscopeDS1052E(rm=rm, shortoutput=True)      # oscilloscope to measure Id(t)
	####################
	# initial setup #######################
	gatestatus=None
	drainstatus=None
	##############################
	# returned data arrays
	spar = {}
	Id={}
	Vswept={}
	Cgs={}
	Cgd={}
	Cds={}
	gm_ex={}
	go_ex={}
	vgsgen.pulsetrainoff()
	if gatesweep:   # then the gate is swept and the drain has a DC bias
		Vconstbiassupply.output_off()       # turn off drain DC bias first
		vgsgen.pulsetrainoff()              # turn off gate swept bias next
		vgsgen.ramp(period=sweepperiod,Vmin=Vsweptmin,Vmax=Vsweptmax,pulsegeneratoroutputZ='50')
		vgsgen.pulsetrainon()       # turn on swept gate bias
		err,drainstatus,Vconstbias,Idaverage = Vconstbiassupply.setvoltage(Vset=abs(Vconstbias),compliance=DCcomp)   # turn on drain DC bias last
	else:           # the drain is swept so turn off and on gate first
		vgsgen.pulsetrainoff()      # turn off drain first
		Vconstbiassupply.output_off()   # turn off gate DC bias
		err,gatestatus,Vconstbias,Idaverage = Vconstbiassupply.setvoltage(Vset=abs(Vconstbias),compliance=DCcomp)   # turn on gate DC bias
		vgsgen.ramp(period=sweepperiod,Vmin=Vsweptmin,Vmax=Vsweptmax,pulsegeneratoroutputZ='50')    # turn on drain swept bias
		vgsgen.pulsetrainon()       # turn on drain swept bias

	time.sleep(holdtime)            # soak bias to allow traps to settle prior to S-parameter time measurements
	# find the maximum number of time points (best time resolution) possible which still allows the minimum PNA time sweep period to be just slightly less than the
	# Vswept sweep period. We need to ensure that the PNA's sweep to complete in no more time than taken for the Vswept sweep period. However, we also want to
	# measure the largest number of timepoints possible to obtain the best time (and Vswept) resolution possible.
	npts,pnasweeptime=pna.get_max_npts(sweepperiod=sweepperiod,RFfrequency=RFfrequency_start) # npts is the maximum number of timepoints possible and pnasweeptime, the PNA's actual sweep time in sec
	# turn on Vconstbias and the Vswept generator and autoscale the scope
	if drainstatus!='N': raise ValueError("ERROR! drain reached compliance")
# step through RF frequencies to get Vswept, Id, and S-parameters vs frequency and time.
	for freq in RFfrequencies:      # freq is in Hz
		freqMHz=str(int(freq/1E6))          # convert frequency point to a string (MHz)
		if freq==RFfrequencies[0]:          # first frequency point - initialize system and take/save the dataset for first measurement frequency
			# get data vs time
			Vswepttimestamps_raw,Id_raw,Vswept_raw = ramped_sweep_gate(scope=scope, pulsegenerator=vgsgen, period=sweepperiod,Vgslow=Vsweptmin,Vgshigh=Vsweptmax,average=8,setupautoscale=True,volttocurrentcalibrationfactor=volttocurrentcalibrationfactor, scopetriggerHFfilteron=True)
			actualsweeptime,PNAtimestamps_raw,s11_raw,s21_raw,s12_raw,s22_raw=pna.getS_2port_time(frequency=freq,instrumentstate=instrumentstate,calset=calset, navg=PNAaverage, sweeptime='MIN', numberofpoints=npts, offsettime=offsettime) # measure S-parameters vs time
			maxtimestampint=min(Vswepttimestamps_raw[-1],PNAtimestamps_raw[-1])             # find the maximum interpolation time stamp, need only once!
			timestamps=np.linspace(start=0,stop=maxtimestampint,num=100).tolist()        # need to gather timestamps only once! Interpolate to give us 100 time points
			# remove timestamps at beginning to account for delay of scope relative to
		else: # save time by not autoscaling for subsequent Vswept and Id measurements
			Vswepttimestamps_raw,Id_raw,Vswept_raw = ramped_sweep_gate(scope=scope, pulsegenerator=vgsgen, period=sweepperiod,Vgslow=Vsweptmin,Vgshigh=Vsweptmax,average=PNAaverage,setupautoscale=False,volttocurrentcalibrationfactor=volttocurrentcalibrationfactor, scopetriggerHFfilteron=True)
		# interpolate so that timestamps from the Ids and S-parameter measurements match timestamps

		# S-parameter data with interpolation in time applied
		# the following separation of real and imaginary S-parameter is necessary only because I used an obsolete version of np.interp()
		s11_raw_real=[s.real for s in s11_raw]
		s11_raw_imag=[s.imag for s in s11_raw]
		s21_raw_real=[s.real for s in s21_raw]
		s21_raw_imag=[s.imag for s in s21_raw]
		s12_raw_real=[s.real for s in s12_raw]
		s12_raw_imag=[s.imag for s in s12_raw]
		s22_raw_real=[s.real for s in s22_raw]
		s22_raw_imag=[s.imag for s in s22_raw]
		# also correct for the requested time offset by eliminating false data points
		#interpolate S-parameter time data in time to timestamps array
		spar['s11']= {freqMHz:[complex(np.interp(t,PNAtimestamps_raw,s11_raw_real),np.interp(t,PNAtimestamps_raw,s11_raw_imag)) for t in timestamps if t>=offsettime]}
		spar['s21']= {freqMHz:[complex(np.interp(t,PNAtimestamps_raw,s21_raw_real),np.interp(t,PNAtimestamps_raw,s21_raw_imag)) for t in timestamps if t>=offsettime]}
		spar['s12']= {freqMHz:[complex(np.interp(t,PNAtimestamps_raw,s12_raw_real),np.interp(t,PNAtimestamps_raw,s12_raw_imag)) for t in timestamps if t>=offsettime]}
		spar['s22']= {freqMHz:[complex(np.interp(t,PNAtimestamps_raw,s22_raw_real),np.interp(t,PNAtimestamps_raw,s22_raw_imag)) for t in timestamps if t>=offsettime]}
		# correct timestamps for the requested time offset
		numtimepoints=min([len(timestamps),len(spar['s11'][freqMHz])])
		Vswept[freqMHz] = [np.interp(t,Vswepttimestamps_raw,Vswept_raw) for t in timestamps if t>=offsettime]     # time-interpolated gate voltage for all four S-parameters
		Id[freqMHz] = [np.interp(t,Vswepttimestamps_raw,Id_raw) for t in timestamps if t>=offsettime]       # time-interpolated drain voltage for all four S-parameters
		# now find some parameters derived from S-parameters
		gm_ex[freqMHz]=[convertSRItoRFGm(s11=spar['s11'][freqMHz][i],s21=spar['s21'][freqMHz][i],s12=spar['s12'][freqMHz][i],s22=spar['s22'][freqMHz][i]) for i in range(0,len(spar['s11'][freqMHz])) ]                    # extrinsic gm (S)
		go_ex[freqMHz]=[convertSRItoRFGo(s22=spar['s22'][freqMHz][i]) for i in range(0,len(spar['s22'][freqMHz])) ]                    # extrinsic output conductance, go (S)
		Cgs[freqMHz]=[convertSRItoCgs(s11=spar['s11'][freqMHz][i],s21=spar['s21'][freqMHz][i],s12=spar['s12'][freqMHz][i],s22=spar['s22'][freqMHz][i],frequency=1E6*float(freqMHz)) for i in range(0,len(spar['s11'][freqMHz])) ]                    # approximate Cgs in fF
		Cgd[freqMHz]=[convertSRItoCgd(s11=spar['s11'][freqMHz][i],s21=spar['s21'][freqMHz][i],s12=spar['s12'][freqMHz][i],s22=spar['s22'][freqMHz][i],frequency=1E6*float(freqMHz)) for i in range(0,len(spar['s11'][freqMHz])) ]                    # approximate Cds in fF
		Cds[freqMHz]=[convertSRItoCds(s11=spar['s11'][freqMHz][i],s21=spar['s21'][freqMHz][i],s12=spar['s12'][freqMHz][i],s22=spar['s22'][freqMHz][i],frequency=1E6*float(freqMHz)) for i in range(0,len(spar['s11'][freqMHz])) ]                    # approximate Cds in fF
	timestamps = timestamps[0:numtimepoints]
	if gatesweep:   # the gate is swept and the drain has a DC bias
		Vconstbiassupply.output_off() # turn off DC drain bias first
		vgsgen.pulsetrainoff()      # turn off triangle-wave drive to gate
	else:   # the drain is swept and the gate has a DC bias
		vgsgen.pulsetrainoff() # turn off triangle-wave drive to drain first
		Vconstbiassupply.output_off() # turn off DC gate bias
	return(timestamps,Vswept,Id,spar,gm_ex,go_ex,Cgs,Cgd,Cds)


