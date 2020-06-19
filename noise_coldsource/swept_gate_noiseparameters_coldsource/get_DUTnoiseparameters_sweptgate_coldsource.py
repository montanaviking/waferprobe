#
pna=None
spectrumanalyzer=None
ps=None             # Amrel power supply
vgsgen=None         # function/pulse generator
scope=None
from setup_noise_coldsource import *
from calculate_noise_parameters_focus import solvefornoiseparameters, calculate_gavail_timedomain,solvefornoiseparameters_timedomain
from scipy.signal import savgol_filter
import numpy.fft as fft

rm=visa.ResourceManager()
#noisesource=NoiseMeter(rm=rm,ENR=15,preset=True,turnonnoisesourceonly=True)               # ENR is bogus because the noise meter is being used only to drive the noise source
if spectrumanalyzer==None:
	spectrumanalyzer=SpectrumAnalyzer(rm=rm)
if pna==None:
	pna=Pna(rm=rm)
if ps==None:
	ps=amrelPowerSupply(rm=rm)          # Amrel DC power supply
if vgsgen==None:
	vgsgen=PulseGeneratorDG1022(rm=rm)  # gate bias drive function generator
if scope==None:
	scope=OscilloscopeDS1052E(rm=rm)    # oscilloscope


##################################################################################################################################
# get noise parameters at requested frequencies using the cold source method
# Inputs:
# cascadefiles_port1 ->  list of 2-port S-parameter files i.e. [[sparfile1,'type1'],[sparfile2,'type2'],.....] where sparfilex is the full pathname of the file containing the S-parameters of the 2 port cascaded on the port 1 side of the tuner to form the composite tuner
# , 'typex'='flip', then flip the 2port prior to cascading 'typex'='noflip', then do not flip the 2-port prior to cascading. 2 ports are cascaded in their order in the cascadefiles_port1 list
# cascadefiles_port2 ->  list of 2-port S-parameter files i.e. [[sparfile1,'type1'],[sparfile2,'type2'],.....] similar to cascadefiles_port1 except these are cascaded on the port 2 side (nearest the DUT) to form the composite tuner
# system_noiseparametersfile -> the full filename containing the noise parameters of the composite noise meter
# reflectioncoefficients -> the reflection coefficients, at the lowest frequency measured, requested on the DUT side of the composite tuner. This results in requested tuner position, from which the reflection coefficients are read from the composite tuner data for
# all the measurement frequencies. Note that the reflectionscoefficients are actually close to those set ONLY at the lowest frequency measured. reflectioncoefficients has the form [[magnitude1,angle1],magnitude2,angle2], ......] and generally one should use eight or more [magnitudex,anglex] values
# anglex is in degrees
# tunercalfile is full pathname of the file containing the S-parameters of the tuner. Note that the composite tuner's S-parameters are calculated from these data + that of the cascaded 2ports specified in cascadefiles_port1 and cascadefiles_port2.
# frequenciesMHz is a list of the frequencies in MHz where the noise parameters of the DUT should be measured NOTE, these frequencies will be measured ONLY if they are common to the DUT S-parameter measurements, the data in tunercalfile, AND the data given for the composite noise meter
# pna_calset1port, pna_calset2port are the calset specifications for the calibrations of the one port DUT output reflection coefficient and 2-port DUT S-parameters respectively.
# pna_instrumentstate1port, pna_instrumentstate2port are the instrument state specifications for the one port DUT output reflection coefficient and 2-port DUT S-parameters respectively.

def get_DUTnoiseparameters_sweptgate_coldsource(cascadefiles_port1=None,cascadefiles_port2=None,system_noiseparametersfile=None,reflectioncoefficients=None,tunercalfile=None,tunerIP=("192.168.1.31",23),
                                      NFaverage=512, sweepfrequency=1E3, Vsweptmax=0., Vsweptmin=-1, Vconstbias=-1, holdtime=0, DCcomp=0.1,
                                      frequenciesMHz=None,pna_calset2port="CalSet_1",pna_instrumentstate2port="2port_LF.sta",navgPNA=4,pnaoffsettime2p=0.000056,
                                      spectrumanalyzerresolutionbandwidth=4E6,spectrumanalyzervideobandwidth=10000,
                                      inputfile_noisemeterdiodedata=None,maxdeltaNF=500,maxvideofreqindex=2):
	pna.pna_RF_onoff(RFon=False)                   # if possible, turn off PNA RF so as not to interfer with the noise measurements
	frequencies=None
	if frequenciesMHz!=None and len(frequenciesMHz)>0:          # did we include the list of user-selected frequencies (frequenciesMHz type is a list of int)
		frequencies=[str(int(f)) for f in frequenciesMHz]    # round frequencies to int then convert to str list
	# ##############now define composite tuner###################
	#cascade available 2port networks onto port1 of tuner
	cascaded2port1=None
	cascaded2port2=None
	if cascadefiles_port1!=None and len(cascadefiles_port1)>0:
		for c in cascadefiles_port1:
			if c[1]=='flip':
				cascaded2port1=spar_flip_ports(read_spar(c[0]))  # then flip ports 1 and 2 on this two-port cascaded2port1[frequencyMHz][2x2 S-parameter matrix]
			else:
				cascaded2port1=read_spar(c[0])                              # don't flip ports, cascaded2port1[frequencyMHz][2x2 S-parameter matrix]
	#cascade available 2port networks onto port2 of tuner
	if cascadefiles_port2!=None and len(cascadefiles_port2)>0:
		for c in cascadefiles_port2:
			if c[1]=='flip':
				cascaded2port2=spar_flip_ports(read_spar(c[0]))  # then flip ports 1 and 2 on this two-port
			else:
				cascaded2port2=read_spar(c[0])                              # don't flip ports
	tuner=FocusTuner(IP=tunerIP,S1=cascaded2port1,S2=cascaded2port2,tunertype='source',tunercalfile=tunercalfile)           # set up the tuner with the tuner calibration file tunerfile to produce the composite tuner
	#############################################################
	nmgb_raw=read_Gnm_gamma(inputfile=inputfile_noisemeterdiodedata)        # read gain-bandwidth product and reflection coefficient data from file, nmgb['frequencies']-> frequencies in MHz, nmgb['GB'] gain-bandwidth product linear, not dB
																		# nmgb['gammanm'] is the input reflection coefficient of the composite noise meter real+jimaginary
																		# nmgb['gammadcold'] is the reflection coefficient of the cold source termination attached to the port opposite the DUT side, of the composite tuner, real+jimaginary
	if reflectioncoefficients==None: raise ValueError("ERROR! No reflection coefficients given for the noise parameter measurements")
	nmnp_raw=read_noise_parameters(system_noiseparametersfile)           # get the noise parameters of composite noise meter nmnp[frequencyMHz]['type'] where type is FmindB, gopt, or Rn with FmindB -> minimun noise figure in dB, gopt->reflection
																		# coefficient presented to the composite noise meter which gives FmindB as the composite noise meter's noise figure
																		# Rn is the noise resistance in ohms, of the composite noise meter
	sweepperiod=1/sweepfrequency
	# Now measure DUT noise parameters if and only if both the DUT S-parameters are supplied AND the system noise parameters are provided. Otherwise, we assume that this is a system noise parameter measurement
	GaDUT={}              # Available gain of DUT (linear not dB)  GaDUT[frequencyMHz][tuner position][timestampindex]
	NFDUTnm={}              # noise figure (linear not dB) of  DUT + composite noise meter NFDUTnm[frequencyMHz][tuner position][timestampindex]
	tunerdata={}          # tuner data tunerdata[frequencyMHz][tuner position][type] where type is one of 'gamma_MA', 'gamma_RI', 'gain', 'Spar', 'frequency' (in MHz), 'pos'
						# where gamma_MA is the composite tuner's reflection coefficient in mag+jangle and gamma_RI the same in real+jimaginary
						 # gain -> the composite tuner's available gain (linear not dB), Spar -> the 2x2 Sparameter matrix of the composite tuner, pos -> the tuner mechanical slug positions
	noise={}            # noise[frequencyMHz][tuner position][timestampindex]. the measured noise power in mW at the spectrum analyzer resolution bandwidth. Note that the spectrum analyzer's resolution bandwidth MUST be same used for measuring the gain-bandwidth product of the composite noise meter.
	NPDUT={}            # NPDUT[frequency MHz][type][timestampindex] where type is FmindB -> the minimum noise figure in dB, gammaopt-> the optimum noise reflection coefficient real+jimaginary, and Rn-> the noise resistance in ohms
	NFDUT={}            # noise figure (linear not dB) of DUT NFDUT[frequency MHz][tuner position][timestampindex] derived from measurements
	NFnmcalcfromNP={}   # noise figure (linear not dB) of the composite noise meter calculated from noise parameters of the composite noise meter NFnmcalcfromNP[frequency MHz][tuner position]
	DUTgammaout={}      # output reflection coefficient of the DUT DUTgammaout[frequencyMHz][tuner position][timestampindex]
	gammatunerMA={}     # reflection coefficient of composite tuner as presented to the DUT input gammatuner[frequencyMHz][tuner position] real+jangle (degrees)
	#DUTSparraw={}       # DUT S-parameters DUTSparraw[frequencyMHz][timestampindex]
	#Id={}
	#Vgs={}
	DUTSpar={}          # S-parameters of DUT, DUTSpar[frequencyMHz][tuner position][timestampindex]

	# measure DUT S-parameters if we are to use the PNA
	tuner.set_tuner_Z0()                     # set tuner to minimum reflections point because the PNA was calibrated in this state
	frequencies=sorted(list(set(map(int,list(tuner.tuner_data.keys()))) & set(frequenciesMHz) & set(nmgb_raw['frequenciesMHz']) & set(map(int,nmnp_raw.keys()))))         # intersect the frequency (MHz) sets from the tuner and the user-specified values of frequenciesMHz. frequencies is a list of ints
	tuner.resettuner()                                                 # set tuner to the reset position

	frequencies_str=list(map(str,sorted(frequencies)))                       # sort frequencies in ascending value and make them a list of str (MHz)

	# interpolate over selected frequencies (MHz) to obtain interpolated values of composite noise meter gain-bandwidth product nmgb[frequencyMHz]['GB'], composite noise meter input reflection coefficient nmgb[frequencyMHz]['gammanm']
	# and the cold diode or cold noise source termination reflection coefficient nmgb[frequencyMHz]['gammadcold']
	nmgb={str(frequencies[i]):{'GB':np.interp(frequencies[i],nmgb_raw['frequenciesMHz'],nmgb_raw['GB']),'gammanm':np.interp(frequencies[i],nmgb_raw['frequenciesMHz'],nmgb_raw['gammanm']),'gammadcold':np.interp(frequencies[i],nmgb_raw['frequenciesMHz'],nmgb_raw['gammadcold'])
	                           } for i in range(0,len(frequencies))}
	# interpolate noise parameters of the composite noise meter nmnp[frequency MHz][type] where type is one of 'GB' -> gain-bandwidth product of the noise meter, 'gammanm' -> input reflection coefficent of the noise meter, 'gammadcold'-> reflection coefficient of the noise source termination or diode in the off (cold) state
	nmnp={str(frequencies[i]):{'FmindB':np.interp(frequencies[i],list(map(int,list(nmnp_raw.keys()))),[nmnp_raw[f]['FmindB'] for f in nmnp_raw.keys()]),'gopt':np.interp(frequencies[i],list(map(int,list(nmnp_raw.keys()))),[nmnp_raw[f]['gopt'] for f in nmnp_raw.keys()]),
	                           'Rn':np.interp(frequencies[i],list(map(int,list(nmnp_raw.keys()))),[nmnp_raw[f]['Rn'] for f in nmnp_raw.keys()])} for i in range(0,len(frequencies))}
	# get tuner positions, spos, calculated from the selected reflection coefficients, self.reflectioncoefficients, for the lowest frequency. These positions will be used for all frequencies
	spos=[[int(tuner.getPOS_reflection(frequency=frequencies[0],gamma=complex(rr[0],rr[1]),gamma_format='ma')['pos'].split(",")[0]), int(tuner.getPOS_reflection(frequency=frequencies[0],gamma=complex(rr[0],rr[1]),gamma_format='ma')['pos'].split(",")[1])] for rr in reflectioncoefficients]          # get positions for selected reflection coefficients format int [[p11,p21],[p12,p22],.....,[p1n,p2n]]
	# sort reflection coefficients to speed tuning

	select_pos=sorted(spos, key=lambda x: (x[0],x[1]))       # sort all tuner positions from lowest to highest positions

	ps.output_off()     # first turn off Amrel DC power supply
	vgsgen.pulsetrainoff()              # turn off gate swept bias next
	vgsgen.ramp(period=sweepperiod,Vmin=Vsweptmin,Vmax=Vsweptmax,pulsegeneratoroutputZ='50')
	vgsgen.pulsetrainon()       # turn on swept gate bias
	err,drainstatus,Vconstbias,Idaverage = ps.setvoltage(Vset=abs(Vconstbias),compliance=DCcomp)   # turn on drain DC bias last
	if drainstatus!='N': raise ValueError("ERROR! drain reached compliance during get_NF_singlefrequency()")
	time.sleep(holdtime)            # soak bias to allow traps to settle prior to spectrum analyzer and PNA time measurements

	# sweep gate and gather Id and Vgs vs time data
	Vswepttimestamps_raw,Id_raw,Vswept_raw = ramped_sweep_gate(scope=scope, pulsegenerator=vgsgen, period=sweepperiod,Vgslow=Vsweptmin,Vgshigh=Vsweptmax,average=8,setupautoscale=True,volttocurrentcalibrationfactor=volttocurrentcalibrationfactor, scopetriggerHFfilteron=True)        # measure raw voltage and currents and save these for later

	for f in frequencies_str:               # loop through selected frequencies str representing the frequency in MHz
		noise[f]={}
		NFDUTnm[f]={}
		tunerdata[f]={}
		NFDUT[f]={}
		NPDUT[f]={}
		NFnmcalcfromNP[f]={}
		DUTgammaout[f]={}
		gammatunerMA[f]={}
		#Id[f]={}
		#Vgs[f]={}
		GaDUT[f]={}
		Id=None
		Vgs=None
	for f in frequencies_str:               # loop through selected frequencies str representing the frequency in MHz
		freqHz=1E6*round(float(f))          # frequency in Hz
		nptsPNA,sweeptimePNA=pna.get_max_npts(sweepperiod=sweepperiod,RFfrequency=freqHz,instrumentstate=pna_instrumentstate2port,calset=pna_calset2port)
		# get 2-port S-parameters in DUTSparraw[frequency MHz][timestampindex][2x2 matrix] format. PNA RF power is left off after the measurement
		sweeptimepna2p,timestampspna2p_raw,s11,s21,s12,s22=pna.getS_2port_time(frequency=freqHz,sweeptime=sweepperiod,navg=navgPNA,numberofpoints=nptsPNA,offsettime=pnaoffsettime2p,returnmatrixformat=False,instrumentstate=pna_instrumentstate2port,calset=pna_calset2port)
		DUTSpar[f]=None
		for p in select_pos:                  # loop through selected tuner positions. These tuner positions were selected based on selected reflection coefficients at f0, the lowest frequency analyzed
			tuner.setPOS(pos1=p[0],pos2=p[1])   # set the tuner position to select the tuner gamma
			# measure noise spectrum vs time. The noise spectrum, noise_raw_sa[timestampindex] is in mW not dBm
			tun=tuner.get_tuner_reflection_gain(frequency=f,position=",".join([str(p[0]),str(p[1])]))        # get tuner data at frequency f (MHz) and the tuner position defined by the selected reflection coefficient {"gamma_MA","gamma_RI","gain","Spar","frequency","pos"} gain is linear, not in dB
			pos=tun['pos']                       # get the tuner position x,y to use to index parameters format is str position1,position2

			satimestamps_raw,noise_raw_sa,frequency_sa,resolutionbandwidthactual,videobandwidthactual=spectrumanalyzer.measure_amplitude_waveform(frequency=1E6*round(float(f)),sweeptime=sweepperiod,resolutionbandwidth=spectrumanalyzerresolutionbandwidth,
			            videobandwidth=spectrumanalyzervideobandwidth,numberofaverages=NFaverage,preampon=True,autoscalespectrumanalyzer=False,attenuation=0,referencelevelguess=-50,outputtype='mW')
			tunerdata[f][pos]=tun                                           # tuner data vs frequency and tuner position, ['frequencyMHz']['pos']['type']
			mintimestamp=np.max([np.min(Vswepttimestamps_raw),np.min(satimestamps_raw),np.min(timestampspna2p_raw)])
			maxtimestamp=np.min([np.max(Vswepttimestamps_raw),np.max(satimestamps_raw),np.max(timestampspna2p_raw)])
			timestamps=np.linspace(start=mintimestamp,stop=maxtimestamp,num=128).tolist()        # Interpolate to give us 100 time points for the interpolated common timestamps

			if Id==None: Id=[np.interp(t,Vswepttimestamps_raw,Id_raw) for t in timestamps]
			if Vgs==None: Vgs=[np.interp(t,Vswepttimestamps_raw,Vswept_raw) for t in timestamps]
			#numptswindow=round(filterintervalfraction*len(noise_raw_sa))
			#if numptswindow<4: ValueError("ERROR! size of spectrum analyzer array is too small")
			#if numptswindow % 2==0: numptswindow+=1     # force number of points in window to be odd
			#nr_sa=savgol_filter(noise_raw_sa,numptswindow,3)
			#noise[f][pos]=[np.interp(t,satimestamps_raw,nr_sa) for t in timestamps]      # interpolate the spectrum analyzer noise vs time to the common timestamps.        noise is in mW NOT dBm
			nr=[np.interp(t,satimestamps_raw,noise_raw_sa) for t in timestamps]      # interpolate the spectrum analyzer noise vs time to the common timestamps.        noise is in mW NOT dBm
			nfd=fft.rfft(nr)
			for i in range(maxvideofreqindex,len(nfd)): nfd[i]=0+0j
			noise[f][pos]=fft.irfft(nfd)

			if DUTSpar[f]==None: # interpolate DUT S-parameters just once per frequency point since it does not depend on tuner position or tuner reflection coefficient
				DUTSpar[f]=[[[np.interp(timestamps[i],timestampspna2p_raw,s11),np.interp(timestamps[i],timestampspna2p_raw,s12)],[np.interp(timestamps[i],timestampspna2p_raw,s21),np.interp(timestamps[i],timestampspna2p_raw,s22)]] for i in range(0,len(timestamps)) ]

			gammatunerMA[f][pos]=tun['gamma_MA']                                # tuner reflection coefficient presented to DUT
			ga=calculate_gavail_timedomain(SDUT=DUTSpar[f],gammain=tun['gamma_RI'])
			GaDUT[f][pos]=ga['gavail']          # available gate from DUT, linear, not dB GaDUT[frequencyMHz][tuner position][timestampindex]
			DUTgammaout[f][pos]=ga['gammaDUTout']       # DUT output reflection coefficient DUTgammaout[frequencyMHz][tuner position][timestampindex]

			# find the noise figure of the DUT+composite noise meter NFDUTnm[frequencyMHz][pos]. This is linear, not dB
			NFDUTnm[f][pos]=[noise[f][pos][i]*np.square(abs(1-DUTSpar[f][i][0][0]*tunerdata[f][pos]['gamma_RI']))*np.square(abs(1-nmgb[f]['gammanm']*DUTgammaout[f][pos][i])) / (nmgb[f]['GB']*np.square(abs(DUTSpar[f][i][1][0]))*(1-np.square(abs(tunerdata[f][pos]['gamma_RI'])))) for i in range(0,len(timestamps))]
			NFnmcalcfromNP[f][pos]=[calculate_nffromnp(reflectioncoef=DUTgammaout[f][pos][i],noiseparameters=nmnp[f],typedBout=False) for i in range(0,len(timestamps))] # noise figure (linear not dB) of the composite noise meter calculated from noise parameters of the composite noise meter NFnmcalcfromNP[frequency MHz][tuner position]
			NFDUT[f][pos]=[NFDUTnm[f][pos][i]-(NFnmcalcfromNP[f][pos][i]-1)/GaDUT[f][pos][i]  for i in range(0,len(timestamps))]           # noise figure (linear not dB) of DUT NFDUT[frequency MHz][tuner position] derived from measurements

	tuner.resettuner()                                                 # set tuner to the reset position
	# now calculate noise parameters
	for f in frequencies_str:
		NPDUT[f]['FmindB'],NPDUT[f]['gopt'],NPDUT[f]['Rn']=solvefornoiseparameters_timedomain(NFDUT=NFDUT[f],tunerdata=tunerdata[f],type='weighted',maxdeltaNF=maxdeltaNF)        # get DUT noise parameters from DUT noise figures and tuner reflection coefficients all are arrays of time indices
		g=calculate_gavail_timedomain(SDUT=DUTSpar[f],gammain=NPDUT[f]['gopt'])
		NPDUT[f]['gassoc']=g['gassoc']              # get associated gain
		NPDUT[f]['gammainopt']=g['gammaDUTinopt']   # reflection coefficient at DUT input which gives a simultaneous conjugate match IF K>1 if K<1 then this is "None"
		NPDUT[f]['gammaoutopt']=g['gammaDUToutopt']   # reflection coefficient at DUT output which gives a simultaneous conjugate match IF K>1 if K<1 then this is "None"
		NPDUT[f]['K']=g['K']                        # unconditionally stable if K>1
		NPDUT[f]['MAG']=g['MAG']                    # Maximum stable gain if K<1 or maximum available gain if K>1, i.e. the DUT gain (linear not dB) obtained for a simultaneous conjugate match
	# noise figure (linear not dB) of the DUT calculated from DUT noise parameters NFDUTcalcfromNP[frequency MHz][tuner position], used to check consistency of noise parameters
	NFDUTcalcfromNP={f:{p:[calculate_nffromnp(reflectioncoef=tunerdata[f][p]['gamma_RI'],noiseparameters={'FmindB':NPDUT[f]['FmindB'][i],'gopt':NPDUT[f]['gopt'][i],'Rn':NPDUT[f]['Rn'][i]},typedBout=False) for i in range(0,len(timestamps))] for p in tunerdata[f].keys()} for f in frequencies_str}   # noise figure linear not dB of the DUT calculated from the DUT noise parameters NFDUTcalcfromNP[frequencyMHz][tuner position]
	return {'timestamps':timestamps,'NP':NPDUT,'NF':NFDUT,'NFcalcfromNP':NFDUTcalcfromNP,'gammatunerMA':gammatunerMA,'noise':noise,'videobandwidth':videobandwidthactual,'resolutionbandwidth':resolutionbandwidthactual,'Id':Id,'Vgs':Vgs}               # return the noise parameters vs frequency, deembedded DUT or system noise figure (dB), amd system+DUT or raw system noise figure in dB respectively
#####################################################################################################################################