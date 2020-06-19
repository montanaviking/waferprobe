# measure the preamp noise parameters
# input parameters:
from amrel_power_supply import *
from spectrum_analyzer import *
from pulsegenerator import *
from pna import *
from oscilloscope import *
from pulsed_measurements import ramped_sweep_gate
from swept_Spar import *
from loadpull_system_calibration import *
from HP8970B_noisemeter import *
from focustuner_pos import *
from writefile_measured import X_writefile_noiseparameters_v2, X_writefile_noisefigure_v2, X_writefile_systemnoisefigure_vs_time,X_writefile_systemnoisefigure_vs_frequency
from utilities import floatequal
from read_write_spar_noise import read_noise_parameters, read_spar, spar_flip_ports
from calculate_noise_parameters_focus import calculate_nffromnp, calculate_gavail,calculate_NP_DUT_direct_timedomain,calculate_NP_noisemeter
#from noise_system_constants_calfiles import *
from scipy.interpolate import CubicSpline

eps=1E-6            # used to compare floating point numbers
# reflectioncoefficients is a list of reflection coefficients used to measure the noise parameters in the format mag,ang where ang is in degrees
class NoiseParametersSweptGate(object):
	def __init__(self,rm=None,usePNA=True,cascadefiles_port1=None,cascadefiles_port2=None,system_noiseparametersfile=None,reflectioncoefficients=None,tunercalfile=None,tunerIP=("192.168.1.31",23)):
		#self.measureDUToutputgamma=measureDUToutputgamma            # if True then measure output DUT reflection coefficient directly, else calculate it from the DUT S-parameters along with the tuner gamma setting
		self._usePNA=usePNA
		self._vgsgen=PulseGeneratorDG1022(rm=rm)
		self._noisemeter = NoiseMeter(rm=rm,ENR=15,preset=True,turnonnoisesourceonly=True)               # ENR is bogus because the noise meter is being used only to drive the noise source
		self._scope=OscilloscopeDS1052E(rm=rm)        # oscilloscope
		self._pna=Pna(rm=rm)            # network analyzer
		self._ps=amrelPowerSupply(rm=rm)              # DC power supply for DC drain bias
		self._spectrumanalyzer=SpectrumAnalyzer(rm=rm)


		self._pna.pna_RF_onoff(RFon=False)                   # if possible, turn off PNA RF so as not to interfer with the noise measurements
		casaded2port1=None
		casaded2port2=None
		#############
		if reflectioncoefficients==None: raise ValueError("ERROR! No reflection coefficients given for the noise parameter measurements")
		if system_noiseparametersfile!=None and len(system_noiseparametersfile)>0: self._npsys=read_noise_parameters(system_noiseparametersfile)           # get noise measurement system noise parameters
		else: self._npsys=None
		self.reflectioncoefficients=reflectioncoefficients                      # user-selected set reflection coefficients to be provided at the cascaded tuner 1 port during noise figure measurements of format [[mag,angle], [mag,angle], etc...]
		#cascade available 2port networks onto port1 of tuner
		if cascadefiles_port1!=None and len(cascadefiles_port1)>0:
			for c in cascadefiles_port1:
				if c[1]=='flip':
					casaded2port1=spar_flip_ports(read_spar(c[0]))  # then flip ports 1 and 2 on this two-port
				else:
					casaded2port1=read_spar(c[0])                              # don't flip ports
		#cascade available 2port networks onto port2 of tuner
		if cascadefiles_port2!=None and len(cascadefiles_port2)>0:
			for c in cascadefiles_port2:
				if c[1]=='flip':
					casaded2port2=spar_flip_ports(read_spar(c[0]))  # then flip ports 1 and 2 on this two-port
				else:
					casaded2port2=read_spar(c[0])                              # don't flip ports
		self._tuner=FocusTuner(IP=tunerIP,S1=casaded2port1,S2=casaded2port2,tunertype='source',tunercalfile=tunercalfile)
##################################################################################################################################
##################################################################################################################################
# get noise parameters vs time and Vgs at the requested frequencies (list)
# inputs are the self.tuner_data[frequencyMHz][motor position]=[s] where [s] is the 2x2 array of tuner S-parameters (real+jimaginary) at the frequency = frequencyMHz (MHz) and tuner motor position specified
# RFfrequency_start, RFfrequency_stop, RFfrequency_step are in MHz The frequencies actually measured are those which occur in the self.tuner_data, parameter DUTSpar, and the parameter frequenciesMHz
# DUTSpar is a set of swept DUT S-parameters of format DUTSpar['typeS']['frequency_MHz'][itime]
# similar to the measure_noiseparameters() method except that the requested reflections are only for the lowest frequency, hereafter called f0, in the frequency sequence
# tuner positions are set according to the requested reflections at f0. Noise figure is measured at all the frequencies only for those tuner positions specified for f0. This allows measurement of all frequencies without moving the tuner for each
# specified tuner position.
# ENRtable is the excess noise ratio of the noise source in dB vs frequency at discrete frequency points and is a dictionary ["frequency MHz"]
# REQUIRES always both a 2-port PNA calibration AND a 1-port s22 PNA calibration
# REQUIRES that the instrument states of the PNA contain all the frequencies selected by the user
	def measure_noiseparameters(self,PNAaverage=32, NFaverage=512, sweepfrequency=1E3, Vsweptmax=0., Vsweptmin=-1, Vconstbias=-1, holdtime=0, RFMHzfrequency_list=None, DCcomp=0.1,maxdeltaNF=None,instrumentstate2port="2port_LF.sta", calset2port="CalSet_1",instrumentstate1port="S22.sta",calset1port="CalSet_2",pnaoffsettime2p=0.000056,pnaoffsettime1p=0.2E-3,videobandwidthsetting=10000):
		# Now measure DUT noise parameters if and only if both the DUT S-parameters are supplied AND the system noise parameters are provided. Otherwise, we assume that this is a system noise parameter measurement
		Gatuner={}                     # tuner available gain, linear and NOT dB. self.Gatuner[frequencyMHz][tuner position]. Note here, than unless otherwise stated, the "tuner" is the COMPOSITE tuner formed by cascading all the devices on the input side of the tuner
		tunerdata={}                        # tuner data, tunerdata[frequency][tuner position][type] where type is 'gamma_MA' which is tuner reflection coeficient mag+jangle,
											# 'gamma_RI' which is tuner reflection coefficient real+jimaginary ,
											#  'gain' which is the tuner available gain, linear not dB
											#  'Spar', which is a Numpy 2-d array of real, imaginary complex pairs of S-parameters: [[s11,s12],[s21,s22]], i.e. the S-parameters of the tuner
											#  'frequency', 'pos'

		DUTSparraw={}                       # 2-port not interpolated DUT S-parameters DUTSparraw[frequencyMHz][timestampindex][2x2 matrix] where the 2x2 matrix is [[s11,s12],[s21,s22]]
		DUTSpar={}                     # 2-port time-interpolated DUT S-parameters DUT['S'][frequencyMHz][timestampindex][2x2 matrix] where the 2x2 matrix is [[s11,s12],[s21,s22]] and self.DUT['time'][timestampindex] is an array with timestamps in seconds
		DUTSpar['S']={}
		GaDUTtimedomain={}             # DUT available gain, linear not dB, calculated from DUTSpar. these data are interpolated. self.GaDUT[frequencyMHz][timestampindex]
		#NFrawtimedomain={}                  # noise figure (dB) of the system+DUT. NFrawtimedomain[frequencyMHz][tuner position][timestampindex]. These data are NOT interpolated.
		#NPtimedomain={}                # calculated noise parameter of the DUT. NPtimedomain[frequencyMHz][timestampindex]. These data are ARE interpolated in timestampindex.
		#NFtimedomain={}                # measured noise figures of the DUT NFtimedomain[frequencyMHz][tuner position][timestampindex]. These data are ARE interpolated in timestampindex.
		DUToutputgamma={}              # output reflection coefficient, real+jimaginary, of the DUT at frequency frequencyMHz and tuner position (which controls the tuner reflection coefffient) vs timestampindex pos DUToutputgamma[frequencyMHz][tuner position][type][timestampindex] where type is 'gamma' or 'time' These data are ARE interpolated in timestampindex.
		Id={}                          # drain current in A interpolated in timestampindex Id[frequencyMHz][tuner position]['I' or 'time'][timestampindex] captured at the given tuner position and frequency measurement where 'I' gives the current in amps and 'time' the time in seconds
		Vgs={}                         # gate voltage in V interpolated in timestampindex Vgs[frequencyMHz][tuner position]['V' or 'time'][timestampindex] captured at the given tuner position and frequency measurement where 'V' gives the gate voltage in volts and 'time' the time in seconds
		systemwithDUTNFdB={}                  # noise figure of DUT + noise meter, systemwithDUTNFdB[frequencyMHz][tuner position][timestampindex] in dB
		select_pos={}                       # selected tuner positions
		noisecold={}            # noise (dBm) spectrum power from the spectrum analyzer, with the noise source off. this is interpolated in time. noisecold[frequencyMHz][tuner position][timestampindex]
		noisehot={}            # noise (dBm) spectrum power from the spectrum analyzer, with the noise source on. this is interpolated in time. noisecold[frequencyMHz][tuner position][timestampindex]

		# measure swept DUT S-parameters if none are supplied
		self._tuner.set_tuner_Z0()                     # set tuner to minimum reflections point because the PNA was calibrated in this state
		self._ps.setvoltage(channel=1,Vset=Vconstbias,compliance=DCcomp)            # turn on drain supply
		# turn on gate sweep and read voltages and drain currents. The raw data will be interpolated to match that coming from the PNA and spectrum analyzer
		timestampsVgssweep,Id_Vgssweep,Vgssweep=ramped_sweep_gate(scope=self._scope,pulsegenerator=self._vgsgen,period=1/sweepfrequency,Vgslow=Vsweptmin,Vgshigh=Vsweptmax,average=8,setupautoscale=True,volttocurrentcalibrationfactor=volttocurrentcalibrationfactor,scopetriggerHFfilteron=True)

		frequencies_str=[str(int(f)) for f in RFMHzfrequency_list]                  # convert selected frequencies to strings

		for f in frequencies_str:       # set up intermmediate (uniterpolated) data output arrays and measure the DUT 2-port S-parameters
			Gatuner[f]={}       # available gain from tuner (always < 1 and linear, not dB) self.Gatuner[frequencyMHz][tuner position]
			tunerdata[f]={}     # tuner data ['frequencyMHz']['pos']['type']
			GaDUTtimedomain[f]={}        # associated gain ['frequencyMHz']['pos']['timestampindex'] where 'frequencyMHz' is type str frequency in MHz, 'pos' is type str tuner position, and timestamp is timestamp index
			DUToutputgamma[f]={}                # DUToutputgamma[frequencyMHz][tuner position]['gamma' or 'time'][timestampindex]
			Id[f]={}
			Vgs[f]={}
			systemwithDUTNFdB[f]={}              # system[frequencyMHz][tuner position][timestampindex]
			noisecold[f]={}
			noisehot[f]={}
			# get 2-port swept gate S-parameters of the DUT ################################################
			freqHz=1E6*int(f)           # convert frequency from a str (MHz) to a floating point number in Hz
			nptsPNA,sweeptimePNA=self._pna.get_max_npts(sweepperiod=1/sweepfrequency,RFfrequency=freqHz,instrumentstate=instrumentstate2port,calset=calset2port)
			sweeptimepna2p,timestampspna2p_raw,DUTSparraw[f]=self._pna.getS_2port_time(frequency=freqHz,sweeptime=1/sweepfrequency,navg=PNAaverage,numberofpoints=nptsPNA,offsettime=pnaoffsettime2p,returnmatrixformat=True,instrumentstate=instrumentstate2port,calset=calset2port)     # get 2-port S-parameters in DUTSparraw[frequency MHz][timestampindex][2x2 matrix] format
		##########################################
		for f in frequencies_str:               # loop through selected frequencies (MHz)
			# find tuner positions, spos[], for all selected reflection coefficients at the frequency MHz under consideration (f) for the composite tuner = tuner itself + all cascaded circuits on the input of the DUT
			# tuner positions are str data type with the format 'posA,posB' where posA and posB are integers in str format and spos is a list of such
			spos=[[int(self._tuner.getPOS_reflection(frequency=f,gamma=complex(rr[0],rr[1]),gamma_format='ma')['pos'].split(",")[0]), int(self._tuner.getPOS_reflection(frequency=f,gamma=complex(rr[0],rr[1]),gamma_format='ma')['pos'].split(",")[1])] for rr in self.reflectioncoefficients]          # get positions for selected reflection coefficients format int p1,p2 at the frequency f (MHz)
			select_pos[f]=sorted(spos, key=lambda x: (x[0],x[1]))       # sort all tuner positions from lowest to highest positions to speed tuning
			setupVgssweep=True
			for p in select_pos[f]:                  # loop through selected tuner positions. These tuner positions were selected based on selected reflection coefficients at f0, the lowest frequency analyzed
				# setup dictionaries
				self._tuner.setPOS(pos1=p[0],pos2=p[1])   # set the source tuner position to select the available tuner gamma (reflection coefficient of the composite tuner) closest to the one which is available
				# tuner data at set position and set frequency
				tun=self._tuner.get_tuner_reflection_gain(frequency=f,position=",".join([str(p[0]),str(p[1])]))        # get tuner S-parameter  and other data at frequency f (MHz) and the tuner position defined by the selected reflection coefficient
				pos=tun['pos']                       # get the tuner position x,y to use to index parameters such as GaDUT
				Gatuner[f][pos]=tun['gain']        # tuner gain at this position, in linear (not dB)
				tunerdata[f][pos]=tun                                           # tuner data vs frequency and tuner position, ['frequencyMHz']['pos']['type']
				Id[f][pos]={}
				Vgs[f][pos]={}
				DUToutputgamma[f][pos]={}
				# measure and get the raw system+DUT noisefigure in dB  vs time using the spectrum analyzer ##################################
				timestampssa_raw,NF_raw_dB,Vswept_raw,Id_raw,drainstatus,noisecold_raw,noisehot_raw = self.get_NF_DUTandsystem_timedomain(frequencyMHz=f,NFaverage=NFaverage,sweepfrequency=sweepfrequency,Vsweptmin=Vsweptmin,Vsweptmax=Vsweptmax,Vconstbias=Vconstbias,DCcomp=DCcomp,holdtime=holdtime,setup=setupVgssweep,videobandwidthsetting=videobandwidthsetting)
				setupVgssweep=False
				# get the output DUT reflection coefficient so we can then deembed the DUT noise figure from the DUT+system noise figure. Note that this does depend on the tuner position and reflection coefficient so we must measure it for each tuner position and frequency
				timestampspna1p_raw, s22_1praw=self._pna.getS22_time(frequency=1E6*int(f),sweepfrequency=sweepfrequency,instrumentstate=instrumentstate1port,calset=calset1port,navg=PNAaverage,offsettime=pnaoffsettime1p)      # get output DUT reflection coeffient as s22_1praw at the given tuner gamma setting, PNA RF port power is left off after this measurement so as not to interfere with noise measurements

				#### generate the base set of common timestamps used to interpolate the data #########################
				maxtime=min([max(timestampspna2p_raw),max(timestampspna1p_raw),max(timestampssa_raw)])          # get minimum of max times for all the time-domain data
				timestamps=np.linspace(start=0,stop=maxtime,num=100).tolist()        # Interpolate to give us 100 time points for the interpolated common timestamps

				#interpolate the 2-port S-parameter time data in time to the common timestamps array, timestamps
				s11=[DUTSparraw[f][i][0][0] for i in range(0,len(timestampspna2p_raw))]      # s11[timestampindex]
				s21=[DUTSparraw[f][i][1][0] for i in range(0,len(timestampspna2p_raw))]      # s21[timestampindex]
				s12=[DUTSparraw[f][i][0][1] for i in range(0,len(timestampspna2p_raw))]      # s12[timestampindex]
				s22=[DUTSparraw[f][i][1][1] for i in range(0,len(timestampspna2p_raw))]      # s22[timestampindex]
				DUTSpar['S'][f]=[ [[np.interp(timestamps[i],timestampspna2p_raw,s11),np.interp(timestamps[i],timestampspna2p_raw,s12)],[np.interp(timestamps[i],timestampspna2p_raw,s21),np.interp(timestamps[i],timestampspna2p_raw,s22)]] for i in range(0,len(timestamps)) if timestamps[i]>=timestampspna2p_raw[0]]    # interpolated 2-port DUT S-parameters
				DUTSpar['time']=[t for t in timestamps if t>=timestampspna2p_raw[0]]            # keep timestamps consistent

				# interpolate the DUT output reflection data to the common timestamps array, timestamps
				DUToutputgamma[f][pos]['gamma']=[np.interp(t,timestampspna1p_raw,s22_1praw) for t in timestamps if t>=timestampspna1p_raw[0] ]
				DUToutputgamma[f][pos]['time']=[t for t in timestamps if t>=timestampspna1p_raw[0]]            # keep timestamps consistent

				# interpolate the system+DUT noisefigure at frequency f and tuner position p ####################
				systemwithDUTNFdB[f][pos]=[np.interp(t,timestampssa_raw,NF_raw_dB) for t in timestamps]        # systemNF[timestampindex] is a noisefigure in dB
				noisecold[f][pos]=[np.interp(t,timestampssa_raw,noisecold_raw) for t in timestamps]        # noisecold_raw[timestampindex] is a noise level in dBm
				noisehot[f][pos]=[np.interp(t,timestampssa_raw,noisehot_raw) for t in timestamps]        # noisecold_raw[timestampindex] is a noise level in dBm

				#interpolate the drain current and gate sweep voltage
				Id[f][pos]['I']= [np.interp(t,timestampssa_raw,Id_raw) for t in timestamps]
				Id[f][pos]['time']=[t for t in timestamps]
				Vgs[f][pos]['V']= [np.interp(t,timestampssa_raw,Vswept_raw) for t in timestamps]
				Vgs[f][pos]['time']=[t for t in timestamps]

				# trim off data on beginning of time sequences, as and if needed so that all data are time-consistent
				maxbeginningtime=max(DUTSpar['time'][0],DUToutputgamma[f][pos]['time'][0])
				#maxbeginningtimeindex=min([i for i in range(0,len(timestamps)) if timestamps[i]>=maxbeginningtime])
				maxtime=min(timestamps[-1],DUToutputgamma[f][pos]['time'][-1],DUTSpar['time'][-1])
				#maxindex=timestamps.index(maxtime)
				#maxbeginningtimeindex=int(max(timestamps.index(DUTSpar['time'][0]),timestamps.index(DUToutputgamma[f][pos]['time'][0])))     # DUTSpar and DUToutputgamma are the only two lists that might be missing timepoints at the start due to the offset times. If so, we must likewise trim points from the other data to keep it time index-consistent
				# if data do not begin at the first index of timestamp, then trim data to make sure they all begin at the same timestamp
				systemwithDUTNFdB[f][pos]=[systemwithDUTNFdB[f][pos][i] for i in range(0,len(timestamps)) if timestamps[i]>=maxbeginningtime and timestamps[i]<=maxtime]
				Id[f][pos]['I']=[Id[f][pos]['I'][i] for i in range(0,len(timestamps)) if timestamps[i]>=maxbeginningtime and timestamps[i]<=maxtime]
				Id[f][pos]['time']=[Id[f][pos]['time'][i] for i in range(0,len(timestamps)) if timestamps[i]>=maxbeginningtime and timestamps[i]<=maxtime]
				Vgs[f][pos]['V']=[Vgs[f][pos]['V'][i] for i in range(0,len(timestamps)) if timestamps[i]>=maxbeginningtime and timestamps[i]<=maxtime]
				Vgs[f][pos]['time']=[Vgs[f][pos]['time'][i] for i in range(0,len(timestamps)) if timestamps[i]>=maxbeginningtime and timestamps[i]<=maxtime]

				DUTSpar['S'][f]= [DUTSpar['S'][f][i] for i in range(0,len(DUTSpar['time'])) if DUTSpar['time'][i]>=maxbeginningtime and DUTSpar['time'][i]<=maxtime]
				DUTSpar['time']= [DUTSpar['time'][i] for i in range(0,len(DUTSpar['time'])) if DUTSpar['time'][i]>=maxbeginningtime and DUTSpar['time'][i]<=maxtime]
				DUToutputgamma[f][pos]['gamma']= [DUToutputgamma[f][pos]['gamma'][i] for i in range(0,len(DUToutputgamma[f][pos]['time'])) if DUToutputgamma[f][pos]['time'][i]>=maxbeginningtime and DUToutputgamma[f][pos]['time'][i]<=maxtime]
				DUToutputgamma[f][pos]['time']= [DUToutputgamma[f][pos]['time'][i] for i in range(0,len(DUToutputgamma[f][pos]['time'])) if DUToutputgamma[f][pos]['time'][i]>=maxbeginningtime and DUToutputgamma[f][pos]['time'][i]<=maxtime]
				timestamps=[timestamps[i] for i in range(0,len(timestamps)) if timestamps[i]>=maxbeginningtime and timestamps[i]<=maxtime]
				# sanity check -> failure indicates a bug
				if len(Vgs[f][pos]['V'])!=len(timestamps): raise ValueError("ERROR! Vgs[f][pos]['V'] not same length as timestamps")
				if len(Vgs[f][pos]['time'])!=len(timestamps): raise ValueError("ERROR! Vgs[f][pos]['time'] not same length as timestamps")
				if len(Id[f][pos]['I'])!=len(timestamps): raise ValueError("ERROR! Id[f][pos]['I'] not same length as timestamps")
				if len(Id[f][pos]['time'])!=len(timestamps): raise ValueError("ERROR! Id[f][pos]['time'] not same length as timestamps")
				if len(DUTSpar['S'][f])!=len(timestamps): raise ValueError("ERROR! DUTSpar['S'][f] not same length as timestamps")
				if len(DUTSpar['time'])!=len(timestamps): raise ValueError("ERROR! DUTSpar['time'] not same length as timestamps")
				if len(DUToutputgamma[f][pos]['gamma'])!=len(timestamps): raise ValueError("ERROR! DUToutputgamma[f][pos]['gamma'] not same length as timestamps")
				if len(DUToutputgamma[f][pos]['time'])!=len(timestamps): raise ValueError("ERROR! DUToutputgamma[f][pos]['time'] not same length as timestamps")
				if len(systemwithDUTNFdB[f][pos])!=len(timestamps): raise ValueError("ERROR! systemwithDUTNFdB[f][pos] not same length as timestamps")
				#############################################################################################################################################################################
		self._ps.output_off()       # turn off drain DC bias first
		self._vgsgen.pulsetrainoff()              # turn off gate swept bias next
		################ Now calculate noise parameters #########################################
		# NPtimedomain is the DUT noise parameters. NPtimedomain[frequency MHz]['parametertype'][timestampindex] where 'parametertype' is FmindB, gopt, Rn, GassocdB, gain_type, gavaildB, gammainopt, and gammaoutopt
		# NFmeastimedomain is the DUT noise figure NFmeastimedomain[frequency MHz][tuner position][timestampindex] linear and not dB
		# NFcalcfromNPtimedomain noise figures in dB of the DUT calculated from DUT noise parameters at each tuner position (tuner reflection coefficient). NFcalcfromNPtimedomain[frequencyMHz][tuner position][timestampindex]. These data are ARE interpolated in timestampindex.
		# return Id and Vgs at the lowest frequency and tuner position only as these are not expected to vary with either frequency nor tuner position, Id[timestampindex], Vgs[timestampindex]
		# tunerdata[frequencyMHz][tunerposition][type] where type is one of gamma_MA is complex gamma_mag.real+jgamma_angle.imag where gamma_angle is in degrees;  gamma_RI is complex gamma.real+jgamma.imag; gain is linear, not dB and always < 1. since the tuner is a passive device, Spar is a 2x2 matrix of S-parameters in real+jimaginary format;
		# frequency in MHz, tunerposition is the tuner position
		# 2-port time-interpolated DUT S-parameters DUT['S'][frequencyMHz][timestampindex][2x2 matrix] where the 2x2 matrix is [[s11,s12],[s21,s22]] and self.DUT['time'][timestampindex] is an array with timestamps in seconds
		# output reflection coefficient, real+jimaginary, of the DUT at frequency frequencyMHz and tuner position (which controls the tuner reflection coefffient) vs timestampindex pos DUToutputgamma[frequencyMHz][tuner position][type][timestampindex] where type is 'gamma' or 'time' These data are ARE interpolated in timestampindex.
		# noise figure of DUT + system system[frequencyMHz][tuner position][timestampindex] in dB
		NPtimedomain,NFmeastimedomain = calculate_NP_DUT_direct_timedomain(tunerdata=tunerdata,NPnoisemeter=self._npsys,NFDUTnoisemeterdB=systemwithDUTNFdB,SDUT=DUTSpar['S'],DUToutputreflectioncoefficient=DUToutputgamma,maxdeltaNF=maxdeltaNF)        # use directly-measured 1-port DUT output reflection coefficient
		select_pos_str={f:[str(p[0])+','+str(p[1]) for p in select_pos[f]] for f in frequencies_str }
		NFcalcfromNPtimedomain={f:{p:[calculate_nffromnp(reflectioncoef=DUToutputgamma[f][p]['gamma'][i],noiseparameters={'FmindB':NPtimedomain[f]['FmindB'][i],'gopt':NPtimedomain[f]['gopt'][i],'Rn':NPtimedomain[f]['Rn'][i]},typedBout=True) for i in range(0,len(timestamps))] for p in select_pos_str[f]} for f in frequencies_str}
		Vgs_time=Vgs[frequencies_str[0]][select_pos_str[frequencies_str[0]][0]]['V']
		Id_time=Id[frequencies_str[0]][select_pos_str[frequencies_str[0]][0]]['I']
		return {'timestamps':timestamps,'tunerdata':tunerdata,'NP':NPtimedomain,'NFfromNP':NFcalcfromNPtimedomain,'NFmeas':NFmeastimedomain,'DUTSpar':DUTSpar,'DUToutputgamma':DUToutputgamma,'NFsysDUT':systemwithDUTNFdB,'Vgs':Vgs_time,'Id':Id_time,'noisecold':noisecold,'noisehot':noisehot}             # return the noise parameters vs frequency, deembedded DUT or system noise figure (dB), amd system+DUT or raw system noise figure in dB respectively
#############################################################################################################################################################################################################################################################
# get raw noisefigure vs timestamps (and hence vs Vgsweep). This is the noisefigure of the noise measurement system + DUT with no deembedding i.e. the noise figure of everything between the noise source and the input to the noise measurement system
# frequencyMHz is in MHz, sweep frequency is in Hz
# drain current and compliance data gathered only when setup==True
# ENR is the excess noise ratio in dB for the noise source when on (hot)
# it's not necessary to correct or calibrate the spectrum analyzer readings for losses or level inaccuracies because we are taking the ratio of spectrum analyzer noise readings and systemic errors should cancel
# return values:
# timestamps[timestampindex]        These are the timestamps in sec vs index
# NFdB[timestampindex] These are the corresponding noise figures of the system+DUT as a function of time.
# Vswept[timestampindex]  This is the swept voltage as a function of time (usually the triangle gate voltage waveform)
# Id[timestamps]    This is the drain current as a function of time
# drainstatus This is the drain status 'N' means not in compliance (normal)
	def get_NF_DUTandsystem_timedomain(self,frequencyMHz=None,NFaverage=512, sweepfrequency=1E3, Vsweptmax=0., Vsweptmin=-1, Vconstbias=-1,DCcomp=0.1,holdtime=5,setup=False,resolutionbandwidthsetting=None,videobandwidthsetting=None):
		sweepperiod=1/sweepfrequency
		if resolutionbandwidthsetting==None:   # if one or both of resolution and video bandwidth settings are NOT supplied, then set resolution and video bandwidths according to the sweepfrequency
			resolutionbandwidthsetting=50./sweepperiod          # in Hz
			#resolutionbandwidthsetting_autoscale=4./sweepperiod # in Hz
		else:
			resolutionbandwidthsetting_autoscale=4000. # in Hz
		if videobandwidthsetting==None:
			videobandwidthsetting=resolutionbandwidthsetting/2  # in Hz
		#frequencyspan_autoscale=max(20*resolutionbandwidthsetting_autoscale,20E3)            # used to find the precise frequency in order to center the signal in the frequency axis
		if setup:            # generally, setup is done just once per noise parameter measurement to save time since we don't expect the drain current to change much over the course of measurement. setup=True must be performed at least once to obtain valid self._Vgswepttimes_raw etc..
			self._ps.output_off()       # turn off drain DC bias first
			self._vgsgen.pulsetrainoff()              # turn off gate swept bias next
			self._vgsgen.ramp(period=sweepperiod,Vmin=Vsweptmin,Vmax=Vsweptmax,pulsegeneratoroutputZ='50')
			self._vgsgen.pulsetrainon()       # turn on swept gate bias
			self._err,self._drainstatus,self._Vconstbias,self._Idaverage = self._ps.setvoltage(Vset=abs(Vconstbias),compliance=DCcomp)   # turn on drain DC bias last
			if self._drainstatus!='N': raise ValueError("ERROR! drain reached compliance during get_NF_singlefrequency()")
			time.sleep(holdtime)            # soak bias to allow traps to settle prior to spectrum analyzer time measurements
			# sweep gate and gather Id and Vgs vs time data
			self._Vswepttimestamps_raw,self._Id_raw,self._Vswept_raw = ramped_sweep_gate(scope=self._scope, pulsegenerator=self._vgsgen, period=sweepperiod,Vgslow=Vsweptmin,Vgshigh=Vsweptmax,average=8,setupautoscale=True,volttocurrentcalibrationfactor=volttocurrentcalibrationfactor, scopetriggerHFfilteron=True)        # measure raw voltage and currents and save these for later iterations of this method
		# read "cold" noise (noise source off)###############
		self._noisemeter.noise_sourceonoff(on=False)     # turn off noise source
		satimestamps_raw,noise_raw_sa,frequency_sa,actualresolutionbandwidth,actualvideobandwidth=self._spectrumanalyzer.measure_amplitude_waveform(referencelevelguess=-50,frequency=1E6*int(frequencyMHz),sweeptime=sweepperiod,resolutionbandwidth=resolutionbandwidthsetting,videobandwidth=videobandwidthsetting,attenuation=0.,numberofaverages=NFaverage,preampon=True,autoscalespectrumanalyzer=False)
		maxtimestampint=min(self._Vswepttimestamps_raw[-1],satimestamps_raw[-1])             # find the maximum interpolation time stamp, need only once!
		timestamps=np.linspace(start=0,stop=maxtimestampint,num=100).tolist()        # Interpolate to give us 100 time points
		Vswept=[np.interp(t,self._Vswepttimestamps_raw,self._Vswept_raw) for t in timestamps]
		Id=[np.interp(t,self._Vswepttimestamps_raw,self._Id_raw) for t in timestamps]
		noisecold_sa=[np.interp(t,satimestamps_raw,noise_raw_sa) for t in timestamps]                 # interpolated spectrum analyzer noise vs time with noise source off, noisecold is in dBm

		# read "hot" noise (noise source on)########################
		self._noisemeter.noise_sourceonoff(on=True)     # turn on noise source
		satimestamps_raw,noise_raw_sa,frequency_sa,actualresolutionbandwidth,actualvideobandwidth=self._spectrumanalyzer.measure_amplitude_waveform(referencelevelguess=-50,frequency=1E6*int(frequencyMHz),sweeptime=sweepperiod,resolutionbandwidth=resolutionbandwidthsetting,videobandwidth=videobandwidthsetting,attenuation=0.,numberofaverages=NFaverage,preampon=True,autoscalespectrumanalyzer=False)
		maxtimestampint=min(self._Vswepttimestamps_raw[-1],satimestamps_raw[-1])             # find the maximum interpolation time stamp, need only once!
		timestamps=np.linspace(start=0,stop=maxtimestampint,num=100).tolist()        # Interpolate to give us 100 time points
		Vswept=[np.interp(t,self._Vswepttimestamps_raw,self._Vswept_raw) for t in timestamps]
		Id=[np.interp(t,self._Vswepttimestamps_raw,self._Id_raw) for t in timestamps]
		noisehot_sa=[np.interp(t,satimestamps_raw,noise_raw_sa) for t in timestamps]                 # interpolated spectrum analyzer noise vs time with noise source on, noisehot is in dBm

		# calculate raw system+DUT noise figure at frequencyMHz vs time using the Y factor technique applied to all timesteps##########################
		YfactdB=[noisehot_sa[i]-noisecold_sa[i] for i in range(0,len(timestamps))]        # calculate Y-factor in dB vs timestamps
		Yfact = [dBtolin(y) for y in YfactdB]                           # convert dB to linear
		ENR=ENRtablecubicspline(frequencyMHz)          # get ENR (dB) from the cubic spline fit of the ENR table in loadpull_system_calibration.py
		NFdB=[ENR-lintodB(y-1) for y in Yfact]          # noisefigure of DUT+measurement system vs timestamps, Yfact is linear NFdB is in dB
		# NFdBaverageacrosstime=dBaverage(NFdB)           # convert the dB value to linear, average, and then convert the average back to dB
		# YfactdBaverageacrosstime=dBaverage(YfactdB)     # convert the dB value to linear, average, and then convert the average back to dB
		# noisecold_sa = [n-lintodB(actualresolutionbandwidth) for n in self.noisecold_sa]     # convert cold noise to dBm/Hz
		# noisehot_sa = [n-lintodB(actualresolutionbandwidth) for n in self.noisehot_sa]     # convert hot noise to dBm/Hz
		return timestamps, NFdB, Vswept,Id,self._drainstatus,noisecold_sa,noisehot_sa                                     # return timestamps, DUT+system noise figure in dB, swept gate voltage, and measured drain current  vs timestamp, noisecold_sa and noisehot_sa are the time-domain noise powers with the noise source off and on  respectively
##########################################################################################################################################################################################################
# get system noisefigure vs frequency using spectrum analyzer in the frequency domain
# this is used to get the noise figure of the noise measurement system "noisemeter" for system calibration purposes
# this uses the swept-measurement sweepfrequency (Hz) to set the resolution and video bandwidths so as to mimic the spectrum analyzer settings for the time-domain measurements
	def get_NF_DUTandsystem_frequencydomain(self,NFaverage=16,sweepfrequency=None,startfrequencyMHz=1000,stopfrequencyMHz=1600,resolutionbandwidthsetting=10E6,videobandwidthsetting=10E3,preamp=False):
		self.preamp=preamp
		if sweepfrequency!=None:                # then use the sweepfrequency to set the resolution and video bandwidths of the spectrum analyzer
			sweepperiod=1/sweepfrequency
			resolutionbandwidthsetting=50./sweepperiod          # in Hz
			#resolutionbandwidthsetting_autoscale=4./sweepperiod # in Hz
			videobandwidthsetting=resolutionbandwidthsetting/2  # in Hz
		centfreq=int((startfrequencyMHz+stopfrequencyMHz)/2.)*1E6       # center frequency Hz
		span=abs(int(stopfrequencyMHz-startfrequencyMHz)*1E6)       # frequency span frequency Hz
		# cold noise measurement (noise source off)
		self._noisemeter.noise_sourceonoff(on=False)     # turn off noise source
		referencelevelsetting,measuredfrequency,measuredpower=self._spectrumanalyzer.measure_peak_level_autoscale(referencelevel=-70,frequency=centfreq,frequencyspan=span,videobandwidth=resolutionbandwidthsetting,resolutionbandwidth=resolutionbandwidthsetting,averages=2,measurenoise=True)       # perform autoscaling
		if measuredpower+15.>referencelevelsetting: referencelevelsetting=referencelevelsetting+10.
		maxfreqcold,maxsigcold,self.frequenciescold,self.noisecold_sa=self._spectrumanalyzer.measure_spectrum(numberofaverages=NFaverage,centfreq=centfreq,span=span,videobandwidth=videobandwidthsetting,resolutionbandwidth=resolutionbandwidthsetting,referencelevel=referencelevelsetting,attenuation=0,preamp=self.preamp)
		self.frequenciescold=[1E-6*f for f in self.frequenciescold]# convert frequencies from Hz to MHz
		# hot noise measurement (noise source on)
		self._noisemeter.noise_sourceonoff(on=True)     # turn on noise source
		referencelevelsetting,measuredfrequency,measuredpower=self._spectrumanalyzer.measure_peak_level_autoscale(referencelevel=-70,frequency=centfreq,frequencyspan=span,videobandwidth=resolutionbandwidthsetting,resolutionbandwidth=resolutionbandwidthsetting,averages=2,measurenoise=True)       # perform autoscaling
		if measuredpower+15.>referencelevelsetting: referencelevelsetting=referencelevelsetting+10.
		maxfreqhot,maxsighot,frequencieshot,self.noisehot_sa=self._spectrumanalyzer.measure_spectrum(numberofaverages=NFaverage,centfreq=centfreq,span=span,videobandwidth=videobandwidthsetting,resolutionbandwidth=resolutionbandwidthsetting,referencelevel=referencelevelsetting,attenuation=0,preamp=self.preamp)
		frequencieshot=[1E-6*f for f in frequencieshot]# convert frequencies from Hz to MHz
		# calculate raw system+DUT noise figure, dB, vs frequency (MHz) using the Y factor technique applied to all measured frequencies
		if(len(self.frequenciescold) != len(frequencieshot)): raise ValueError("Internal ERROR!, Bug! number of cold measurement frequencies does not match the number of hot measurement frequencies")
		self.YfactdB=[self.noisehot_sa[i]-self.noisecold_sa[i] for i in range(0,len(self.frequenciescold))]        # calculate Y-factor in dB vs frequency
		Yfact = [dBtolin(y) for y in self.YfactdB]                           # convert dB to linear
		self.ENR=[ENRtablecubicspline(f) for f in self.frequenciescold]          # get ENR (dB) from the cubic spline fit of the ENR table in loadpull_system_calibration.py
		self.NFdB=[self.ENR[i]-lintodB(Yfact[i]-1) for i in range(0,len(self.frequenciescold))]          # noisefigure of DUT+measurement system vs frequency, Yfact is linear
		self.actualresolutionbandwidth=self._spectrumanalyzer.get_resolutionbandwidth()             # get actual resolution bandwidth in Hz
		self.noisecold_sa = [n-lintodB(self.actualresolutionbandwidth) for n in self.noisecold_sa]     # convert cold noise to dBm/Hz
		self.noisehot_sa = [n-lintodB(self.actualresolutionbandwidth) for n in self.noisehot_sa]     # convert hot noise to dBm/Hz
		return self.frequenciescold,self.NFdB
##########################################################################################################################################################################################################
#############################################################################################################################################################################################################################################################
# get time-domain noisefigure vs timestamps (and hence vs Vgsweep). This is the noisefigure of the deembedded DUT and requires the noise parameters of the noise measurement system
# frequencyMHz is in MHz, sweep frequency is in Hz
# drain current and compliance data gathered only when setup==True
# ENR is the excess noise ratio in dB for the noise source when on (hot)
# it's not necessary to correct or calibrate the spectrum analyzer readings for losses or level inaccuracies because we are taking the ratio of spectrum analyzer noise readings and systemic errors should cancel
#
#	def get_NF_timedomain(self,frequencyMHz=None,NFaverage=512, sweepfrequency=1E3, Vsweptmax=0., Vsweptmin=-1, Vconstbias=-1,DCcomp=0.1,holdtime=5,setup=False,resolutionbandwidthsetting=None,videobandwidthsetting=None,preamp=False):

##########################################################################################################################################################################################################

######################################################################################################################################
	writefile_noiseparameters = X_writefile_noiseparameters_v2
	writefile_noisefigure = X_writefile_noisefigure_v2
	writefile_systemnoisefigure_vs_time=X_writefile_systemnoisefigure_vs_time
	writefile_systemnoisefigure_vs_frequency=X_writefile_systemnoisefigure_vs_frequency
