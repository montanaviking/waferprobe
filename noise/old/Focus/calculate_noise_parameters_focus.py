# calculates noise parameters from tuned noise figure measurements version 2 with mods to tuner and S-parameter dictionary structures
# see /carbpnics/owncloudsync/documents/analysis/noise/noise_parameters_from_tuned_measurements.odp
# NF is the measured noise figure in dB

import numpy as np
#from scipy.optimize import lsq_linear
from utilities import floatequal
#from MauryTunerMT986_v2 import *
from calculated_parameters import cascadeS, convertSRItoGMAX, convertSRItoUMAX, convertRItoMA, convertMAtoRI, convertSRItoGMAX
Y0=1./50.
Z0=1/Y0
#############################################################################################################################################################################
# calculate the available DUT gain (linear) with the source reflection coefficient set to the optimum noise reflection coefficient or any reflection coefficient presented to port 1 of the DUT for that matter
# returns the maximum stable gain instead if conditionally stable AND the available DUT gain > MSG
# parameter SDUT is the DUT S-parameters having the format: [[S11,S12],[S21,S22]] where Sxx is a complex number Sxx.real+jSxx.imag
# where, for instance SDUT[0,0] is S11 in real+jimaginary and SDUT[1,0] is S21 in real+jimaginary
# parameter gammain is the input reflection coefficient presented to the DUT and is given in real+jimaginary.
# gammaDUTout is the DUT port 2 (output port) reflection coefficient when the reflection coefficient presented to port 1 of the DUT is gammain
# ga_DUT is the DUT's available gain with gammain presented to the DUT port 1. It is in linear format NOT dB
def calculate_gavail(SDUT=None,gammain=None):
	gammaDUTout=SDUT[1,1]+(SDUT[0,1]*SDUT[1,0]*gammain/(1-SDUT[0,0]*gammain))
	ga_DUT=( (1.-np.square(abs(gammain)))/np.square(abs(1-SDUT[0,0]*gammain)) )*np.square(abs(SDUT[1,0]))/(1.-np.square(abs(gammaDUTout)))        # available gain of DUT in system
	#ret=convertSRItoGMAX(SDUT[0,0],SDUT[1,0],SDUT[0,1],SDUT[1,1])
	# if ret['stability_factor']>1.: return ga_DUT,gammaDUTout,'gassoc'           # returns the available DUT gain if unconditionally stable
	# elif ga_DUT>ret['gain'] and ret['stability_factor']<=1.: return ret['gain'],gammaDUTout,'MSG'   # returns the maximum stable gain if both conditionally stable and if ga_DUT>MSG
	# else: return ga_DUT,gammaDUTout,'gassoc'
	return ga_DUT,gammaDUTout,'gassoc'
	#return ret['gain'],gammaDUTout,'gassoc'
########################################################################################################
####################################################################################################
# parameter Fgamma[][0] is the linear corrected noise figure of the DUT for the given Fgamma[1]=gamma = reflection coefficient
# parameter Fgamma[][0] is the actual DUT noise figure deembedded from the measured DUT+system noise figure
# parameter Fgamma[][1]=gamma is the real+jimaginary reflection coefficient presented to port 1 of the DUT
# uses the method of Lane with single valued decomposition techniques to evaluate noise parameters from an overdetermined matrix
# MUST use at least four values of F and gamma but should use at least eight values of each to get reasonable accuracy
# returns the three noise parameters FmindB, gammaopt, and Rn where FmindB is the optimum noise figure in dB obtained when the
# DUT has gammaopt presented to it's port 1
# gammaopt is the reflection coefficient, real+jimaginary, that when presented to port 1 of the DUT will give the minimum DUT noise figure of FmindB
# Rn is the noise resistance of the DUT
def solvefornoiseparameters(Fgamma=None):
	if len(Fgamma)<4: raise ValueError("ERROR! less than four values of noise figure and gamma")
	Y=[Y0*(1-Fg[1])/(1+Fg[1]) for Fg in Fgamma]       # convert gamma to Y (admittance)
	M=[[1., y.real+np.square(y.imag)/y.real, 1./y.real, y.imag/y.real] for y in Y]       # nx4 matrix
	ret=np.linalg.lstsq(M,[Fg[0] for Fg in Fgamma])                                                            # solve for A,B,C,D from Lane via least squares best fit
	#ret2=lsq_linear(M,F,([0.,0.,0.,-np.inf],[np.inf,np.inf,np.inf,np.inf]))
	A=ret[0][0]
	B=ret[0][1]
	C=ret[0][2]
	D=ret[0][3]
	# A=ret2['x'][0]
	# B=ret2['x'][1]
	# C=ret2['x'][2]
	# D=ret2['x'][3]
	Rn=B
	# if Rn>0.:
	FmindB=10*np.log10(A+np.sqrt(4*B*C-np.square(D)))                                   # convert linear noise figure to dB
	Yopt=complex(np.sqrt(4*B*C-np.square(D))/(2*B),-D/(2*B))

	# else:
	# 	print("WARNING! Rn<0= ",Rn)
	# 	B=abs(Rn)+1E-6
	# 	FmindB=10*np.log10(A+np.sqrt(4*B*C-np.square(D)))                                   # convert linear noise figure to dB
	# 	Yopt=complex(np.sqrt(4*B*C-np.square(D))/(2*B),-D/(2*B))
	gammaopt=(Y0-Yopt)/(Y0+Yopt)
	print("from line 65 calculate_noise_parameters_focus.py residue = ",ret[1],FmindB,gammaopt,Rn)
	return(FmindB,gammaopt,Rn)
#####################################################################################################
# solve for noise parameters for all measured frequencies and tuner_data positions where the noise figure was measured
# NF is the deembedded measured linear noise figure of the DUT vs frequency (Hz) and tuner_data position
# tuner_data is the tuner_data reflection coefficients vs frequency and tuner_data position
def noise_parameters(NF=None,tuner=None,SDUT=None):
	if NF==None or tuner==None: raise ValueError("ERROR! one or more parameters missing")
	# find list of frequencies common to NF and the tuner
	#frequencies=list(set([NF[i]['frequency'] for i in range(0,len(NF))]).intersection([tuner.tuner_data[i]['frequency'] for i in range(0,len(tuner.tuner_data))]))       # frequencies common to both the noise figure (NF) and the tuner data
	frequencies=list(set(NF.keys())&set(tuner.tuner_data.keys()))                       # frequencies common to both the noise figure (NF) and the tuner data str data type in MHz
	if SDUT!=None and len(SDUT)>0: frequencies=list(set(frequencies)&set(SDUT))          # frequencies common to all of the NF, tuner data, and DUT S-parameters
	noiseparameters={}                                                                  # declare noise parameters dictionary for the calculated noise parameters
	frequencies=list(map(str,sorted(list(map(int,frequencies)))))                       # sort frequencies in ascending value. Needed to use map() to sort frequencies since they are of type str
	for f in frequencies:
		positions= list(NF[f].keys())                      # get all tuner_data motor positions used to gather the noise figure data for the frequency under consideration = f (MHz)
		F=[]                                                    # linear noise figure list with one noise figure per tuner_data position at the frequency f (MHz)
		gam=[]                                              # tuner S11 (reflection coeffient presented to DUT) vs tuner motor positions
		noiseparameters[f]={}                               # add noise parameter data dictionary to this frequency point
		for p in positions:
			F.append(NF[f][p])                              # append noise figure (linear not dB)
			gam.append(tuner.tuner_data[f][p][0,0])         # get the DUT source reflections for all positions that the noise figure was measured, from the tuner_data
		noiseparameters[f]['FmindB'],noiseparameters[f]['gopt'],noiseparameters[f]['Rn']=solvefornoiseparameters(F=F,gamma=gam)                               # find the DUT noise parameters at the frequency point = f
		if SDUT!=None and len(SDUT)>0:          # then we have DUT S-parameters so also find the associated gain in dB
			rg=calculate_gavail(SDUT=SDUT[f],gammain=noiseparameters[f]['gopt'])        # get linear format associated gain of the DUT for the optimum noise match presented to the DUT input
			noiseparameters[f]['GassocdB']=10*np.log10(rg[0])              # convert associated gain to dB
			noiseparameters[f]['gain_type']=rg[1]                          # get the gain type, i.e. stability information about the associated gain
	return noiseparameters
#######################################################################################################
#######################################################################################################
# calculate DUT noise figure from raw measured noise figure by removal of the system noise
# note that tuner.tuner_data is the tuner_data reflection coefficient (at tuner_data port 1) for all frequencies and tuner_data motor positions measured
# parameter NF_raw_measureddB is the sytem+DUT noise figure in dB as a function of frequency (MHz) and tuner motor positions
# parameter tuner is the tuner data from which the tuner reflection coefficient is obtained from the tuner motor positions and frequency
# parameter SDUT is the DUT S-parameters as a function of frequency (MHz)
# parameter systemnoiseparameters is the noise parameters (function of frequency) of the portion of the noise measurement system which follows the DUT. We need to know the system noise figure vs DUT S-parameters because
# the system noise figure depends on the reflection coefficient on the DUT output as presentted to the noise measurement system. systemnoiseparameters are the noise parameters of the noise meter or that of a preamp used to feed the noise meter
# returned value F is the dembedded noise figure in linear format (rather than dB)
def deembed_noise_figure(NF_raw_measureddB=None,tuner=None,SDUT=None,systemnoiseparameters=None):
	F={}
	if SDUT!=None and len(SDUT)==0:
		SDUT=None
		systemnoiseparameters=None
	if systemnoiseparameters!=None and len(systemnoiseparameters)==0:
		systemnoiseparameters=None
		SDUT=None
	# get frequencies at which the deembeded noise figure will be calculated. Any frequency to be considered must be included in all the input data which are used
	if SDUT!=None and systemnoiseparameters!=None: frequencies=list(set(NF_raw_measureddB.keys())&set(tuner.tuner_data.keys())&set(systemnoiseparameters.keys())&set(SDUT.keys()))                       # frequencies common to the raw noise figure (NF), the DUT S-parameters, and the tuner data str data type in MHz
	else: frequencies=list(set(NF_raw_measureddB.keys())&set(tuner.tuner_data.keys()))                       # frequencies common to the raw noise figure (NF) and the tuner data str data type in MHz
	for f in frequencies:                   # loop through all frequency points which are common to all the data
		if SDUT!=None and len(SDUT)>0:
			Fmin_sys=np.power(10, systemnoiseparameters[f]['FmindB']/10)           # convert noise measurement system's input minimum noise figure from dB to linear format at the frequency f. Used only if there is a DUT being measured
		positions=NF_raw_measureddB[f].keys()                      # get tuner_data motor positions, under which the system+DUT noise figures were measured at the frequency under consideration = f in MHz
		# Standard DUT measurement a preamplifier and/or output circuit is used and we must and have supplied the DUT S-parameters
		F[f]={}                     # positions dict, for this frequency point, to deembedded noise figure
		for p in positions:         # iterate through the tuner_data positions at the frequency point f
			ga_tuner=tuner.get_tuner_availablegain_sourcepull(frequency=f,position=p,flipports=True)                                    # get available gain of tuner_data+cascaded elements (linear) (i.e. the available gain of the tuner with ports 1 and 2 flipped)
			NF_raw_measured=np.power(10,NF_raw_measureddB[f][p]/10)           # measured system+DUT noise figure in linear format (convert dB to linear)
			if systemnoiseparameters!=None and SDUT!=None and len(SDUT)>0:                  # we have measured a DUT so the calculated deembedded noise figure output F are those of the DUT, otherwise F is the deembedded noise figure (linear) of the noisemeter or preamp (if preamp is used)
				gammatuner=tuner.get_tuner_reflection(frequency=f,position=p)                                       # get the tuner's reflection coefficient which is presented to the DUT input
				#gammaDUTout=S22DUT+(S12DUT*S21DUT*gammatuner/(1-S11DUT*gammatuner))                                 # DUT output (DUT port 2) reflection coefficient with the tuner presenting gammatuner to the DUT input (port 1 of the DUT)
				ga_DUT,gammaDUTout,gaintype=calculate_gavail(SDUT=SDUT[f],gammain=gammatuner)
				NF_raw_measured=np.power(10,NF_raw_measureddB[f][p]/10)           # measured system+DUT noise figure in linear format (convert dB raw noisefigure to linear raw noisefigure)
				Fsys= Fmin_sys+(4*systemnoiseparameters[f]['Rn']/Z0)*np.square(abs(systemnoiseparameters[f]['gopt']-gammaDUTout))/(np.square(abs(1+systemnoiseparameters[f]['gopt']))*(1-np.square(abs(gammaDUTout)))) # preamp noise figure (linear) within the noise measurement system
				F[f][p]=(NF_raw_measured*ga_tuner)-((Fsys-1)/ga_DUT)             # deembedded DUT linear noise figure
				print("from line 132 in calculate_noise_parameters_maury.py FDUT, NF_raw_measured*ga_tuner, ga_DUT, (Fsys-1)/ga_DUT ",F[f][p],NF_raw_measured*ga_tuner, (Fsys-1)/ga_DUT )
			else:                       # we didn't get DUT S-parameters, therefore we are calculating and returning the noise figure F which is the noise figure of the noise meter or the preamp used on the input of the noise meter
				F[f][p]=NF_raw_measured*ga_tuner                                    # get deembeddednoise figure (linear) measured at a single frequency and single tuner_data position p
	return F                                                                         # deembedded linear noise figures dictionaries vs frequency(MHz) and tuner motor position
#######################################################################################################
# calculates the noise figure in dB of a two-port given the two-port's noise parameters and the reflection coefficient presented to port 1 of the two-port
#
# parameter reflectioncoef is given in real+jimaginary and Z0 is assumed to be 50ohms
# parameter noiseparameters are the two-port's noise parameters and is of the form:
# noiseparameters['gammaopt':g,'FmindB':fmin,'Rn':rn,'GassocdB':gassoc} where fmin is the minimum noise figure  in dB, g is the optimum source reflection coefficient (which is complex),
# rn is the noise resistance, and gassoc is the associated two-port gain in dB.
def calculate_nffromnp(reflectioncoef=None,noiseparameters=None,typedBout=True):
	if reflectioncoef==None or noiseparameters==None: raise ValueError("ERROR! input parameters missing!")
	Fmin=np.power(10.,noiseparameters['FmindB']/10.)                     # convert noisefigure dB to linear if data are in dB
	F=Fmin+4.*(noiseparameters['Rn']/Z0)*np.square(abs(noiseparameters['gopt']-reflectioncoef))/(np.square(abs(1.+noiseparameters['gopt']))*(1.-np.square(abs(reflectioncoef))))
	if typedBout: return 10.*np.log10(F)   # return dB noise figure
	else: return F                      # return linear noise figure
#######################################################################################################
# calculate DUT noise parameters from a DUT+noisemeter noise parameters + noisemeter noise parameters + DUT S-parameters + tuner
# this deembeds the DUT noise parameters from the DUT+noisemeter noise parameters. NPnoisemeter is loaded from a file of previously-measured noise paramters whereas NPDUTnoisemeter is recently measured
# note that the noisemeter is the noise measurement system following port 2 (output port) of the DUT and might optionally include a preamplifier and other circuitry on the noisemeter's input
# Parameters:
# tunerdata is a dictionary of dictionaries i.e. tunerdata[f][p] where f is the frequency in MHz and p the x,y tuner position. The data therein are from the Focus tuner cascaded with possible two-ports on the input and/or output of the tuner:
# gamma_MA -> magnitude+jangle (deg), complex number type reflection coefficient
# gamma_RI -> real+jimag complex number type
# gain -> linear (not dB) power gain of the tuner (always < 1 since the tuner always exhibits loss) with it's cascaded circuits (composite tuner)
# pos -> tuner position, x,y (string type) used as an index     -> should be the same as dictionary index p above
# NPnoisemeter which is the noise parameters of the noise meter (system)
#  NPDUTnoisemeter which is the noise parameters of the DUT+noisemeter combination
# SDUT which is the DUT S-parameters
# output: NPDUT which is the dictionary containing the DUT noise parameters
def calculate_NP_DUT(tunerdata=None, NPnoisemeter=None, NFDUTnoisemeterdB=None, SDUT=None):
	if tunerdata==None or NFDUTnoisemeterdB==None or NPnoisemeter==None: raise ValueError("ERROR! Missing parameter in NP_DUT()")
	frequencies=list(set(tunerdata.keys())&set(NPnoisemeter.keys())&set(NFDUTnoisemeterdB.keys())&set(SDUT.keys()))            # list of frequencies in MHz that are common to all data
	frequencies=[str(ff) for ff in sorted([int(f) for f in frequencies])]                                                           # sort frequencies into ascending order
	NPDUT={}
	NFDUT={}                # DUT noise figure vs frequency (MHz) and tuner position
	NPDUTnoisemeter={}

	# first find noise parameters of DUT+noisemeter from DUT+noisemeter noise figures vs frequency and tuner position
	for f in frequencies:                # loop thru tuner data frequencies (frequencies in MHz)
		Fgam=[[np.power(10.,NFDUTnoisemeterdB[f][p]/10.)*tunerdata[f][p]['gain'],tunerdata[f][p]['gamma_MA']] for p in tunerdata[f].keys()]
		NPDUTnoisemeter[f]['FmindB'],NPDUTnoisemeter[f]['gopt'],NPDUTnoisemeter[f]['Rn'] = solvefornoiseparameters(Fgamma=Fgam)    # calculated noise parameters for DUT+noisemeter together. Use this to extract the DUT noise parameters later in this code

	# then find DUT noise parameters using the previously-measured noisemeter noise parameters and the DUT+noisemeter noise figure parameters
		for p in tunerdata[f].keys():
			NFDUT[f]={}
			ga_DUT,gammaDUTout,gaintype = calculate_gavail(SDUT=SDUT[f],gammain=tunerdata[f][p]['gamma_MA'])  # get DUT available gain when terminated with a conjugate matched output and the tuner reflection coefficient at the DUT input and the DUT output reflection coefficient when the input is terminated with the tuner
			NFnoisemeterfromNP = calculate_nffromnp(reflectioncoef=gammaDUTout,noiseparameters=NPnoisemeter[f],typedBout=False)      # noise figure (linear) of noise meter from its noise parameters when terminated with the DUT output reflection coefficient
			NFDUTnoisemeterfromNP = calculate_nffromnp(reflectioncoef=tunerdata[f][p]['gamma_MA'],noiseparameters=NPDUTnoisemeter[f],typedBout=False)                # noise figure (linear) of the measured DUT+noisemeter from the DUT+noisemeter noise parameter when terminated with the tuner reflection coefficient
			NFDUT[f][p] = NFDUTnoisemeterfromNP-((NFnoisemeterfromNP-1.)/ga_DUT) # extracted noise figure of the DUT

		NPDUT[f]['FmindB'],NPDUT[f]['gopt'],NPDUT[f]['Rn'] = solvefornoiseparameters(Fgamma=[[NFDUT[f][p],tunerdata[f][p]['gamma_MA']] for p in tunerdata[f].keys()])               # noise parameters of DUT from extracted DUT noise figure
		ret=calculate_gavail(SDUT=SDUT[f],gammain=NPDUT[f]['gopt'])             # calculated associated gain for DUT
		NPDUT[f]['GassocdB']=10.*np.log10(ret[0])                                # associated gain in dB
		NPDUT[f]['gain_type']=ret[2]
		NPDUT[f]['gavaildB']=10.*np.log10(convertSRItoGMAX(SDUT[f][0,0],SDUT[f][1,0],SDUT[f][0,1],SDUT[f][1,1])['gain'])
	return NPDUT,NFDUT
#######################################################################################################
# calculate the noisemeter (noise measurement system connected to the DUT output) noise parameters from the noisemeter + tuner noisefigures vs frequency (MHz) and tuner positions. The tuner data is the source for the reflection coefficients used to measure the
# NF_raw_measureddB[f][p] is the raw measured noisefigure (dB) for a given frequency (MHz) and tuner position p. The noisemeter is usually the composite of the circuit connected to the DUT output, e.g. bias Tee -> coupler -> LNA -> noisemeter input
# Inputs:
# tunerdata is a dictionary of dictionaries i.e. tunerdata[f][p] where f is the frequency in MHz and p the x,y tuner position. The data therein are from the Focus tuner cascaded with possible two-ports on the input and/or output of the tuner:
# gamma_MA -> magnitude+jangle (deg), complex number type reflection coefficient
# gamma_RI -> real+jimag complex number type
# gain -> linear (not dB) power gain of the tuner (always < 1 since the tuner always exhibits loss) with it's cascaded circuits (composite tuner)
# pos -> tuner position, x,y (string type) used as an index     -> should be the same as dictionary index p above
# NF_raw_measureddB[f] which is a dictionary data type using f (frequency in MHz) as the key and is the dB measured noise figure of the whole noise measurement system e.g. noise source -> input circuit->tuner-> input probe -> thru -> output probe -> bias tee -> coupler -> LNA -> noise meter
# NF_raw is a noise figure measurement with the noise system calibrated from the noise source to the noise meter
# NFnoisemeter is the linear noise figure (not dB) of the noisemeter at frequency f (MHz) and is a dictionary data type with key f
# Outputs: NPnoisemeter which is the dictionary containing noisemeter noise parameters
def calculate_NP_noisemeter(tunerdata=None,NF_raw_measureddB=None):
	if tunerdata==None or NF_raw_measureddB==None: raise ValueError("ERROR! Missing parameter in calculate_NP_noisemeter()")
	frequencies=list(set(tunerdata.keys())&set(NF_raw_measureddB.keys()))            # list of frequencies in MHz that are common to all data
	frequencies=[str(ff) for ff in sorted([int(f) for f in frequencies])]                                                           # sort frequencies into ascending order
	NPnoisemeter={}
	NFnoisemeter={}
	for f in frequencies:           # frequencies in MHz as dict keys
		NPnoisemeter[f]={}
		NFnoisemeter[f]={}
		for p in tunerdata[f].keys():                # loop thru tuner positions (which are tuner reflection coefficient settings)
			NF_raw_measured=np.power(10,NF_raw_measureddB[f][p]/10)           # convert measured noisemeter noise figure from dB to linear format (convert dB raw noisefigure to linear raw noisefigure)
			NFnoisemeter[f][p]=NF_raw_measured*tunerdata[f][p]['gain']                       # noisemeter noise figure (linear at frequency f (MHz)) and tuner motor position p)
		NPnoisemeter[f]['FmindB'],NPnoisemeter[f]['gopt'],NPnoisemeter[f]['Rn'] = solvefornoiseparameters(Fgamma=[[NFnoisemeter[f][p],tunerdata[f][p]['gamma_MA']] for p in tunerdata[f].keys()])                                 # calculated noise parameters for DUT at frequency f (MHz)
	return NPnoisemeter,NFnoisemeter