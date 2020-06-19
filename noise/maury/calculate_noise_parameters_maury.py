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
# parameter SDUT is the DUT S-parameters having the format:
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
# parameter F is the linear corrected noise figure of the DUT for the given gammma = reflection coefficient
# parameter F and gamma are both 1-dimensional arrays of equal size
# parameter F is the actual DUT noise figure deembedded from the measured DUT+system noise figure
# parameter gamma is the real+jimaginary reflection coefficient presented to port 1 of the DUT
# uses the method of Lane with single valued decomposition techniques to evaluate noise parameters from an overdetermined matrix
# MUST use at least four values of F and gamma but should use at least eight values of each to get reasonable accuracy
# returns the three noise parameters FmindB, gammaopt, and Rn where FmindB is the optimum noise figure in dB obtained when the
# DUT has gammaopt presented to it's port 1
# gammaopt is the reflection coefficient, real+jimaginary, that when presented to port 1 of the DUT will give the minimum DUT noise figure of FmindB
# Rn is the noise resistance of the DUT
def solvefornoiseparameters(F=None,gamma=None):
	if len(F)!=len(gamma): raise ValueError("ERROR! number of gamma points is not equal to number of noise figure points")
	if len(F)<4: raise ValueError("ERROR! less than four values of noise figure and gamma")
	Y=[Y0*(1-g)/(1+g) for g in gamma]       # convert gamma to Y (admittance)
	M=[[1., Y[i].real+np.square(Y[i].imag)/Y[i].real, 1./Y[i].real, Y[i].imag/Y[i].real] for i in range(0,len(Y)) ]       # nx4 matrix
	ret=np.linalg.lstsq(M,F)                                                            # solve for A,B,C,D from Lane via least squares best fit
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
	print("from line 60 calculate_noise_parameters.py residue = ",ret[1],FmindB,gammaopt,Rn)
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
# tuner where tuner.tuner_data[frequency][pos]=[s] where [s] is the 2x2 tuner S-parameter matrix at frequency f MHz and tuner motor position pos
# NPnoisemeter which is the noise parameters of the noise meter (system)
#  NPDUTnoisemeter which is the noise parameters of the DUT+noisemeter combination
# SDUT which is the DUT S-parameters
# output: NPDUT which is the dictionary containing the DUT noise parameters
def calculate_NP_DUT(tuner=None, NPnoisemeter=None, NFDUTnoisemeterdB=None, SDUT=None):
	if tuner==None or NFDUTnoisemeterdB==None or NPnoisemeter==None: raise ValueError("ERROR! Missing parameter in NP_DUT()")
	frequencies=list(set(tuner.tuner_data.keys())&set(NPnoisemeter.keys())&set(NFDUTnoisemeterdB.keys())&set(SDUT.keys()))            # list of frequencies in MHz that are common to all data
	frequencies=[str(ff) for ff in sorted([int(f) for f in frequencies])]                                                           # sort frequencies into ascending order
	NPDUT={}
	NFDUT={}                # DUT noise figure vs frequency (MHz) and tuner position
	NPDUTnoisemeter={}
	for f in frequencies:           # frequencies in MHz as dict keys
		NPDUT[f]={}
		NPDUTnoisemeter[f]={}
		tunergammas=[]
		NFDUTnoisemeter=[]
		positions=list(set(tuner.tuner_data[f].keys())&set(NFDUTnoisemeterdB[f].keys()))
		# first find noise parameters of DUT+noisemeter from DUT+noisemeter noise figures vs frequency and tuner position
		for p in positions:                # loop thru tuner positions (which are tuner reflection coefficient settings)
			tunergammas.append(tuner.get_tuner_reflection(position=p,frequency=f))          # tuner reflection coefficient as presented to the DUT
			ga_tuner=tuner.get_tuner_availablegain_sourcepull(frequency=f,position=p,flipports=True)                                    # get available gain of tuner_data+cascaded elements (linear) (i.e. the available gain of the tuner with ports 1 and 2 flipped)
			NFDUTnoisemeterraw=np.power(10.,NFDUTnoisemeterdB[f][p]/10.)                        # raw measured noisefigure of DUT+noisemeter
			NFDUTnoisemeter.append(NFDUTnoisemeterraw*ga_tuner)                                 # DUT+noise meter noise figure in linear format
		NPDUTnoisemeter[f]['FmindB'],NPDUTnoisemeter[f]['gopt'],NPDUTnoisemeter[f]['Rn']=solvefornoiseparameters(F=NFDUTnoisemeter,gamma=tunergammas)                                 # calculated noise parameters for DUT+noisemeter
		tunergammas=[]
		# then find DUT noise parameters using the noisemeter noise parameters and the DUT+noisemeter noise figure parameters
		NFDUT[f]={}
		NFDUT_array=[]
		for p in positions:                # loop thru tuner positions (which are tuner reflection coefficient settings)
			tunergammas.append(tuner.get_tuner_reflection(position=p,frequency=f))          # tuner reflection coefficient as presented to the DUT
			ga_DUT,gammaDUTout,gaintype=calculate_gavail(SDUT=SDUT[f],gammain=tunergammas[-1])  # get DUT available gain when terminated with a conjugate matched output and the tuner reflection coefficient at the DUT input and the DUT output reflection coefficient when the input is terminated with the tuner
			NFnoisemeterfromNP=calculate_nffromnp(reflectioncoef=gammaDUTout,noiseparameters=NPnoisemeter[f],typedBout=False)      # noise figure (linear) of noise meter from its noise parameters when terminated with the DUT output reflection coefficient
			NFDUTnoisemeterfromNP=calculate_nffromnp(reflectioncoef=tunergammas[-1],noiseparameters=NPDUTnoisemeter[f],typedBout=False)                # noise figure (linear) of the DUT+noisemeter from the DUT+noisemeter noise parameter when terminated with the tuner reflection coefficient
			NFDUT_array.append(NFDUTnoisemeterfromNP-((NFnoisemeterfromNP-1.)/ga_DUT)) # extracted noise figure of the DUT
			NFDUT[f][p]=NFDUT_array[-1]                                    # extracted noise figure of the DUT
		NPDUT[f]['FmindB'],NPDUT[f]['gopt'],NPDUT[f]['Rn']=solvefornoiseparameters(F=NFDUT_array,gamma=tunergammas)               # noise parameters of DUT from extracted DUT noise figure
		ret=calculate_gavail(SDUT=SDUT[f],gammain=NPDUT[f]['gopt'])             # calculated associated gain for DUT
		NPDUT[f]['GassocdB']=10.*np.log10(ret[0])                                # associated gain in dB
		NPDUT[f]['gain_type']=ret[2]
		NPDUT[f]['gavaildB']=10.*np.log10(convertSRItoGMAX(SDUT[f][0,0],SDUT[f][1,0],SDUT[f][0,1],SDUT[f][1,1])['gain'])
	return NPDUT,NFDUT
#######################################################################################################
# calculate the noisemeter (noise measurement system connected to the DUT output) noise parameters from the noisemeter noisefigure + tuner. The tuner data is the source for the reflection coefficients used to measure the
# NF_raw_measureddB[f][pos] is the raw measured noisefigure (dB) for a given frequency (MHz) and tuner position
# tuner is the tuner data
# output: NPDUT which is the dictionary containing the DUT noise parameters
def calculate_NP_noisemeter(tuner=None,NF_raw_measureddB=None):
	if tuner==None or NF_raw_measureddB==None: raise ValueError("ERROR! Missing parameter in calculate_NP_noisemeter()")
	frequencies=list(set(tuner.tuner_data.keys())&set(NF_raw_measureddB.keys()))            # list of frequencies in MHz that are common to all data
	frequencies=[str(ff) for ff in sorted([int(f) for f in frequencies])]                                                           # sort frequencies into ascending order
	NPnoisemeter={}
	NFnoisemeter={}
	for f in frequencies:           # frequencies in MHz as dict keys
		NPnoisemeter[f]={}
		NFnoisemeter[f]={}
		tunergammas=[]
		NFnoisemeter_array=[]
		positions=list(set(tuner.tuner_data[f].keys())&set(NF_raw_measureddB[f].keys()))      # tuner motor positions common to tuner calibration file and tuner positions where the noisemeter's noisefigure was measured
		for p in positions:                # loop thru tuner positions (which are tuner reflection coefficient settings)
			ga_tuner=tuner.get_tuner_availablegain_sourcepull(frequency=f,position=p,flipports=True)                                    # get available gain of tuner_data+cascaded elements (linear) (i.e. the available gain of the tuner with ports 1 and 2 flipped)
			tunergammas.append(tuner.get_tuner_reflection(position=p,frequency=f))          # tuner reflection coefficient as presented to the DUT
			NF_raw_measured=np.power(10,NF_raw_measureddB[f][p]/10)           # measured noisemeter noise figure in linear format (convert dB raw noisefigure to linear raw noisefigure)
			NFnoisemeter_array.append(NF_raw_measured*ga_tuner)                       # noisemeter noise figure (linear at frequency f (MHz)) and tuner motor position p)
			NFnoisemeter[f][p]=NFnoisemeter_array[-1]                       # noisemeter noise figure (linear at frequency f (MHz)) and tuner motor position p)
		NPnoisemeter[f]['FmindB'],NPnoisemeter[f]['gopt'],NPnoisemeter[f]['Rn']=solvefornoiseparameters(F=NFnoisemeter_array,gamma=tunergammas)                                 # calculated noise parameters for DUT at frequency f (MHz)
	return NPnoisemeter,NFnoisemeter