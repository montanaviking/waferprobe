#
pna=None
spectrumanalyzer=None
from setup_noise_coldsource import *
from calculate_noise_parameters_focus import solvefornoiseparameters, calculate_gavail

rm=visa.ResourceManager()
#noisesource=NoiseMeter(rm=rm,ENR=15,preset=True,turnonnoisesourceonly=True)               # ENR is bogus because the noise meter is being used only to drive the noise source
if spectrumanalyzer==None:
	spectrumanalyzer=SpectrumAnalyzer(rm=rm)
if pna==None:
	pna=Pna(rm=rm)

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

def get_DUTnoiseparameters_coldsource(cascadefiles_port1=None,cascadefiles_port2=None,system_noiseparametersfile=None,reflectioncoefficients=None,tunercalfile=None,tunerIP=("192.168.1.31",23),
                                      frequenciesMHz=None,pna_calset1port=None,pna_instrumentstate1port=None,pna_calset2port=None,pna_instrumentstate2port=None,navgPNA=4,
                                      spectrumanalyzerresolutionbandwidth=1E6,spectrumanalyzervideobandwidth=None,
                                      inputfile_noisemeterdiodedata=None,maxdeltaNF=None,Tamb=290):
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

	# Now measure DUT noise parameters if and only if both the DUT S-parameters are supplied AND the system noise parameters are provided. Otherwise, we assume that this is a system noise parameter measurement
	GaDUT={}              # Available gain of DUT (linear not dB)  GaDUT[frequencyMHz][pos]
	NFDUTnm={}              # noise figure (linear not dB) of  DUT + composite noise meter NFDUTnm[frequencyMHz][pos]
	tunerdata={}          # tuner data tunerdata[frequencyMHz][pos][type] where type is one of 'gamma_MA', 'gamma_RI', 'gain', 'Spar', 'frequency' (in MHz), 'pos'
						 # where gamma_MA is the composite tuner's reflection coefficient in mag+jangle and gamma_RI the same in real+jimaginary
						 # gain -> the composite tuner's available gain (linear not dB), Spar -> the 2x2 Sparameter matrix of the composite tuner, pos -> the tuner mechanical slug positions
	noise={}            # the measured noise power in mW at the spectrum analyzer resolution bandwidth. Note that the spectrum analyzer's resolution bandwidth MUST be same used for measuring the gain-bandwidth product of the composite noise meter
	NPDUT={}            # NPDUT[frequency MHz][type] where type is FmindB -> the minimum noise figure in dB, gammaopt-> the optimum noise reflection coefficient real+jimaginary, and Rn-> the noise resistance in ohms
	NFDUT={}            # noise figure (linear not dB) of DUT NFDUT[frequency MHz][tuner position] derived from measurements
	NFnmcalcfromNP={}   # noise figure (linear not dB) of the composite noise meter calculated from noise parameters of the composite noise meter NFnmcalcfromNP[frequency MHz][tuner position]
	DUTgammaout={}      # output reflection coefficient of the DUT DUTgammaout[frequencyMHz][tuner position]
	gammatunerMA={}     # reflection coefficient of composite tuner as presented to the DUT gammatuner[f][pos] real+jangle (degrees)
	#DUTingammaopt={}  # optimum input reflection coefficient of DUT when DUT is unconditionally stable DUTgaingammaopt[frequency MHz]


	# measure DUT S-parameters if we are to use the PNA
	tuner.set_tuner_Z0()                     # set tuner to minimum reflections point because the PNA was calibrated in this state
	frequencies=sorted(list(set(map(int,list(tuner.tuner_data.keys()))) & set(frequenciesMHz) & set(nmgb_raw['frequenciesMHz']) & set(map(int,nmnp_raw.keys()))))         # intersect the frequency (MHz) sets from the tuner and the user-specified values of frequenciesMHz. frequencies is a list of ints
	tuner.resettuner()                                                 # set tuner to the reset position
	S2DUTraw=pna.pna_getS_2port(navg=navgPNA,instrumentstate=pna_instrumentstate2port,calset=pna_calset2port)        # measure DUT 2-port S-parameters if we are using the PNA. RF port power is left off so as not to interfere with noise measurements. This returns a 2x2 S-parameter matrix
	if (max(frequenciesMHz) > max(S2DUTraw['frequenciesMHz'])) or (min(frequenciesMHz)<min(S2DUTraw['frequenciesMHz'])): raise ValueError("ERROR! selected range of frequencies outside range of network analyzer for 2-port DUT measurements")
	frequencies_str=list(map(str,sorted(frequencies)))                       # sort frequencies in ascending value and make them a list of str (MHz)
	#if (max(frequenciesMHz) > max(list(nmnp_raw.keys()))) or (min(frequenciesMHz)<min(list(nmnp_raw.keys()))): raise ValueError("ERROR! selected range of frequencies outside range of noise parameters of composite noise meter")
	# get DUT 2-port S-parameters format: DUTS2P[frequencyMHz][2x2 matrix]. Interpolate as necessary
	DUTS2P={str(frequencies[i]):[[np.interp(frequencies[i],S2DUTraw['frequenciesMHz'],S2DUTraw['S11']),np.interp(frequencies[i],S2DUTraw['frequenciesMHz'],S2DUTraw['S12'])],
	                            [np.interp(frequencies[i],S2DUTraw['frequenciesMHz'],S2DUTraw['S21']),np.interp(frequencies[i],S2DUTraw['frequenciesMHz'],S2DUTraw['S22'])]] for i in range(0,len(frequencies))}
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

	for f in frequencies_str:               # loop through selected frequencies str representing the frequency in MHz
		GaDUT[f]={}
		noise[f]={}
		NFDUTnm[f]={}
		tunerdata[f]={}
		NFDUT[f]={}
		NPDUT[f]={}
		NFnmcalcfromNP[f]={}
		DUTgammaout[f]={}
		gammatunerMA[f]={}

		noise_raw=get_cold_hot_spectrumanalyzer(spectrumanalyzer=spectrumanalyzer,resolutionbandwidthsetting=spectrumanalyzerresolutionbandwidth,videobandwidthsetting=spectrumanalyzervideobandwidth,average=1,frequenciesMHz=frequenciesMHz,measurehot=False,formatdB=False)

	for p in select_pos:                  # loop through selected tuner positions. These tuner positions were selected based on selected reflection coefficients at f0, the lowest frequency analyzed
		tuner.setPOS(pos1=p[0],pos2=p[1])   # set the tuner position to select the tuner gamma
		posset=str(p[0])+','+str(p[1])  # tuner set position
		 # get output DUT reflection coeffient as self.s22_oneport at the given tuner gamma setting, PNA RF port power is left off after this measurement so as not to interfere with noise measurements
		#S1DUTraw=pna.pna_get_S_oneport(navg=navgPNA,instrumentstate=pna_instrumentstate1port,calset=pna_calset1port)
		#if (max(frequencies) > max(S1DUTraw['frequenciesMHz'])) or (min(frequenciesMHz)<min(S1DUTraw['frequenciesMHz'])): raise ValueError("ERROR! selected range of frequencies outside range of network analyzer for 2-port DUT measurements")
		noise_raw=get_cold_hot_spectrumanalyzer(spectrumanalyzer=spectrumanalyzer,resolutionbandwidthsetting=spectrumanalyzerresolutionbandwidth,videobandwidthsetting=spectrumanalyzervideobandwidth,average=1,frequenciesMHz=frequenciesMHz,measurehot=False,formatdB=False)        # noise power in mW not dBm noise_raw['noisecold'][frequencyMHz] get noise power for all measurement frequencies
		videobandwidthactual=spectrumanalyzer.get_videobandwidth()            # get actual video bandwidth of the spectrum analyzer
		resolutionbandwidthactual=spectrumanalyzer.get_resolutionbandwidth()        # get actual resolution bandwidth of the spectrum analyzer
		for f in frequencies_str:               # loop through selected frequencies str representing the frequency in MHz
			tun=tuner.get_tuner_reflection_gain(frequency=f,position=",".join([str(p[0]),str(p[1])]))        # get tuner data at frequency f (MHz) and the tuner position defined by the selected reflection coefficient {"gamma_MA","gamma_RI","gain","Spar","frequency","pos"} gain is linear, not in dB
			pos=tun['pos']                       # get the tuner position x,y to use to index parameters format is str position1,position2
			noise[f][pos]=noise_raw['noisecold'][f]
			if pos!=posset: raise ValueError("ERROR! set tuner position does not match actual tuner position") # should never happen but sanity check
			#DUTgammaout[f][pos]=np.interp(int(f),S1DUTraw['frequenciesMHz'],S1DUTraw['gamma']) # interpolated DUT output reflection coefficient, DUTgammaout[frequency MHz][tuner position]
			tunerdata[f][pos]=tun           # tuner data formatted tunerdata[frequencyMHz][pos]['type'] where 'type' is one of: "gamma_MA","gamma_RI","gain","Spar","frequency","pos" gain is linear, not in d
			gammatunerMA[f][pos]=tun['gamma_MA']
			ga=calculate_gavail(SDUT=DUTS2P[f],gammain=tun['gamma_RI'])
			GaDUT[f][pos]=ga['gavail']
			#GaDUT[f][pos]=np.square(abs(DUTS2P[f][1][0]))*(1-np.square(abs(tun['gamma_RI'])))/(np.square(abs(1-DUTS2P[f][0][0]*tun['gamma_RI'])) * (1-np.square(abs(DUTgammaout[f][pos]))))     # available gain from the DUT, linear not dB
			DUTgammaout[f][pos]=ga['gammaDUTout']
			# find the noise figure of the DUT+composite noise meter NFDUTnm[frequencyMHz][pos]. This is linear, not dB
			NFDUTnm[f][pos]=noise[f][pos]*np.square(abs(1-DUTS2P[f][0][0]*tunerdata[f][pos]['gamma_RI']))*np.square(abs(1-nmgb[f]['gammanm']*DUTgammaout[f][pos])) / (nmgb[f]['GB']*np.square(abs(DUTS2P[f][1][0]))*(1-np.square(abs(tunerdata[f][pos]['gamma_RI'])))) - Tamb/T0 +1        # T0 is the reference temperature = 290K and Tamb is the lab ambient temperature K
			NFnmcalcfromNP[f][pos]=calculate_nffromnp(reflectioncoef=DUTgammaout[f][pos],noiseparameters=nmnp[f],typedBout=False) # noise figure (linear not dB) of the composite noise meter calculated from noise parameters of the composite noise meter NFnmcalcfromNP[frequency MHz][tuner position]
			NFDUT[f][pos]=NFDUTnm[f][pos]-(NFnmcalcfromNP[f][pos]-1)/GaDUT[f][pos]                 # noise figure (linear not dB) of DUT NFDUT[frequency MHz][tuner position] derived from measurements
			#print("debug from line 133 in get_DUTnoiseparameters_coldsource.py NF DUT+nm = "+formatnum(NFDUTnm[f][pos])+" DUT NF = "+formatnum(NFDUT[f][pos])+" nmNF = "+formatnum(NFnmcalcfromNP[f][pos]))
	tuner.resettuner()                                                 # set tuner to the reset position
	for f in frequencies_str:
		Fg=[[NFDUT[f][str(p[0])+','+str(p[1])],tunerdata[f][str(p[0])+','+str(p[1])]['gamma_RI']] for p in select_pos]              # put noise figure into proper format to solve for noise parameters
		NPDUT[f]['FmindB'],NPDUT[f]['gopt'],NPDUT[f]['Rn']=solvefornoiseparameters(Fg,type='weighted',maxdeltaNF=maxdeltaNF)        # get DUT noise parameters from DUT noise figures and tuner reflection coefficients
		g=calculate_gavail(SDUT=DUTS2P[f],gammain=NPDUT[f]['gopt'])
		NPDUT[f]['gassoc']=g['gassoc']              # get associated gain
		NPDUT[f]['gammainopt']=g['gammaDUTinopt']   # reflection coefficient at DUT input which gives a simultaneous conjugate match IF K>1 if K<1 then this is "None"
		NPDUT[f]['gammaoutopt']=g['gammaDUToutopt']   # reflection coefficient at DUT output which gives a simultaneous conjugate match IF K>1 if K<1 then this is "None"
		NPDUT[f]['K']=g['K']                        # unconditionally stable if K>1
		NPDUT[f]['MAG']=g['MAG']                    # Maximum stable gain if K<1 or maximum available gain if K>1, i.e. the DUT gain (linear not dB) obtained for a simultaneous conjugate match
	# noise figure (linear not dB) of the DUT calculated from DUT noise parameters NFDUTcalcfromNP[frequency MHz][tuner position], used to check consistency of noise parameters
	NFDUTcalcfromNP={f:{p:calculate_nffromnp(reflectioncoef=tunerdata[f][p]['gamma_RI'],noiseparameters=NPDUT[f]) for p in tunerdata[f].keys()} for f in frequencies_str}   # noise figure (dB) of the DUT calculated from the DUT noise parameters NFDUTcalcfromNP[frequencyMHz][tuner position]
	return {'NP':NPDUT,'NF':NFDUT,'NFcalcfromNP':NFDUTcalcfromNP,'gammatunerMA':gammatunerMA,'noise':noise,'videobandwidth':videobandwidthactual,'resolutionbandwidth':resolutionbandwidthactual}               # return the noise parameters vs frequency, deembedded DUT or system noise figure (dB), amd system+DUT or raw system noise figure in dB respectively
#####################################################################################################################################