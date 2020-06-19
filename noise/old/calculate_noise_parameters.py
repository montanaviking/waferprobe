# calculates noise parameters from tuned noise figure measurements
# see /carbpnics/owncloudsync/documents/analysis/noise/noise_parameters_from_tuned_measurements.odp
# NF is the measured noise figure in dB

import numpy as np
from utilities import floatequal
from calculated_parameters import cascadeS, convertSRItoGMAX, convertSRItoUMAX, convertRItoMA, convertMAtoRI, convertSRItoGMAX
Y0=1./50.
Z0=1/Y0
#############################################################################################################################################################################
# calculate the available DUT gain (linear) with the source reflection coefficient set to the optimum noise reflection coefficient or any reflection coefficient for that matter
# returns the maximum stable gain instead if conditionally stable AND the available DUT gain > MSG
# SDUT is the DUT S-parameters having the format:
# where SDUT[0,0] is S11 in real+jimaginary
# gammain is the input reflection coefficient presented to the amplifier and is given in real+jimaginary.
def calculate_gavail(SDUT=None,gammain=None):
	gammaDUTout=SDUT[1,1]+(SDUT[0,1]*SDUT[1,0]*gammain/(1-SDUT[0,0]*gammain))
	ga_DUT=( (1-np.square(abs(gammain)))/np.square(abs(1-SDUT[0,0]*gammain)) )*np.square(abs(SDUT[1,0]))/(1-np.square(abs(gammaDUTout)))        # available gain of DUT in system
	ret=convertSRItoGMAX(SDUT[0,0],SDUT[1,0],SDUT[0,1],SDUT[1,1])
	if ret['stability_factor']>1.: return ga_DUT,'gassoc'           # returns the available DUT gain if unconditionally stable
	elif ga_DUT>ret['gain'] and ret['stability_factor']<=1.: return ret['gain'],'MSG'   # returns the maximum stable gain if both conditionally stable and if ga_DUT>MSG
	else: return ga_DUT,'gassoc'
########################################################################################################
####################################################################################################
# F is the linear corrected noise figure of the DUT for the given gammma = reflection coefficient
# F and gamma are both 1-dimensional arrays of equal size
# F is the actual DUT noise figure deembedded from the measured DUT+system noise figure
# uses the method of Lane with single valued decomposition techniques to evaluate noise parameters from an overdetermined matrix
# MUST use at least four values of F and gamma but should use at least eight values of each to get reasonable accuracy
# returns the three noise parameters
def solvefornoiseparameters(F=None,gamma=None):
	if len(F)!=len(gamma): raise ValueError("ERROR! number of gamma points is not equal to number of noise figure points")
	if len(F)<4: raise ValueError("ERROR! less than four values of noise figure and gamma")
	Y=[Y0*(1-g)/(1+g) for g in gamma]       # convert gamma to Y (admittance)
	M=[[1., Y[i].real+np.square(Y[i].imag)/Y[i].real, 1./Y[i].real, Y[i].imag/Y[i].real] for i in range(0,len(Y)) ]       # nx4 matrix
	ret=np.linalg.lstsq(M,F)                                                            # solve for A,B,C,D from Lane via least squares best fit
	A=ret[0][0]
	B=ret[0][1]
	C=ret[0][2]
	D=ret[0][3]
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
	return(FmindB,gammaopt,Rn)
#####################################################################################################
# solve for noise parameters for all measured frequencies and tuner_data positions where the noise figure was measured
# NF is the deembedded measured linear noise figure of the DUT vs frequency (Hz) and tuner_data position
# tuner_data is the tuner_data reflection coefficients vs frequency and tuner_data position
def noise_parameters(NF=None,tuner=None,SDUT=None):
	if NF==None or tuner==None: raise ValueError("ERROR! one or more parameters missing")
	# find list of frequencies common to NF and the tuner
	frequencies=list(set([NF[i]['frequency'] for i in range(0,len(NF))]).intersection([tuner.tuner_data[i]['frequency'] for i in range(0,len(tuner.tuner_data))]))       # frequencies common to both the noise figure (NF) and the tuner data
	if SDUT!=None and len(SDUT)>0: frequencies=list(set(frequencies).intersection(SDUT['frequency']))          # frequencies common to all of the NF, tuner data, and DUT S-parameters
	noiseparameters=[]
	frequencies.sort()
	for f in frequencies:
		ift=min(range(len(tuner.tuner_data)), key=lambda i:abs(tuner.tuner_data[i]['frequency']-f))                # find index of tuner_data frequency that is closest to that for the common frequencies
		ifn=min(range(len(NF)), key=lambda i:abs(NF[i]['frequency']-f))                                             # find index of noise figure data that is closest to that for the common frequencies
		if SDUT!=None: ifs=min(range(len(SDUT['frequency'])), key=lambda i:abs(SDUT['frequency'][i]-f))                                             # find index of noise figure data that is closest to that for the common frequencies
		# are the closest common frequencies of the NF, and tuner_data acceptably close in value?
		# in order to add a frequency point to the noise parameters, the frequencies tuner_data[ift]['frequency'] must be very close to the NF[ifn]['frequency']
		#if floatequal(NF[ifn]['frequency'],tuner.tuner_data[ift]['frequency'],0.0001):        # calculate noise parameters only when the frequencies of the NF, SDUT, and tuner_data are close enough
		positions=[p for p in NF[ifn].keys() if p!='frequency']                      # get tuner_data positions from measured noise figure
		F=[]                    # linear noise figure list with one noise figure per tuner_data position at the frequency NF[ifn]['frequency']
		gam=[]                  # tuner_data
		noiseparameters.append({})
		for p in positions:
			F.append(NF[ifn][p])
			gam.append(tuner.tuner_data[ift][p][0,0])                                            # get the DUT source reflections for all positions that the noise figure was measured, from the tuner_data
		noiseparameters[-1]['frequency']=NF[ifn]['frequency']
		noiseparameters[-1]['FmindB'],noiseparameters[-1]['gopt'],noiseparameters[-1]['Rn']=solvefornoiseparameters(F=F,gamma=gam)                               # find the DUT noise parameters at the ifreq th frequency point
		if SDUT!=None and len(SDUT)>0:          # then we have DUT S-parameters so find the associated gain in dB
			rg=calculate_gavail(SDUT=SDUT['s'][ifs],gammain=noiseparameters[-1]['gopt'])
			noiseparameters[-1]['GassocdB']=10*np.log10(rg[0])              # convert associated gain to dB
			noiseparameters[-1]['gain_type']=rg[1]                          # get the gain type, i.e. stability information about the associated gain
	return noiseparameters
#######################################################################################################
# calculate DUT noise figure from raw measured noise figure
# note that tuner_data.tuner_data is the tuner_data reflection coefficient (at tuner_data port 1) for all frequencies and tuner_data positions measured
# returned parameter dembedded noise figure F is in linear form
def deembed_noise_figure(NF_raw_measureddB=None,tuner=None,SDUT=None,systemnoiseparameters=None):
	F=[]
	if SDUT!=None and len(SDUT)==0:
		SDUT=None
		systemnoiseparameters=None
	if systemnoiseparameters!=None and len(systemnoiseparameters)==0:
		systemnoiseparameters=None
		SDUT=None

	for ifn in range(0,len(NF_raw_measureddB)):
		ift=min(range(len(tuner.tuner_data)), key=lambda i:abs(tuner.tuner_data[i]['frequency']-NF_raw_measureddB[ifn]['frequency']))                # find index of tuner_data frequency that is closest to that for the noise figure data

		# Standard DUT measurement a preamplifier and/or output circuit is used and we must and have supplied the DUT S-parameters
		if systemnoiseparameters!=None and SDUT!=None:
			ifp=min(range(len(systemnoiseparameters)), key=lambda i:abs(systemnoiseparameters[i]['frequency'] - NF_raw_measureddB[ifn]['frequency']))             # find index of preamp noise parameter frequency that is closest to that for the noise figure data
			ifs=min(range(len(SDUT['frequency'])), key=lambda i:abs(SDUT['frequency'][i]-NF_raw_measureddB[ifn]['frequency']))                # find index of DUT S-parameter frequency that is closest to that for the noise figure data
			if floatequal(NF_raw_measureddB[ifn]['frequency'],tuner.tuner_data[ift]['frequency'],0.0001) and floatequal(NF_raw_measureddB[ifn]['frequency'],SDUT['frequency'][ifs],0.0001) \
				and (systemnoiseparameters==None or floatequal(NF_raw_measureddB[ifn]['frequency'], systemnoiseparameters[ifp]['frequency'], 0.0001)):        # calculate noise parameters only when the frequencies of the NF, SDUT, and tuner_data are close enough
				positions=[p for p in NF_raw_measureddB[ifn].keys() if p!='frequency']                      # get tuner_data positions from measured noise figure
				S11DUT=SDUT['s'][ifs][0,0]
				S12DUT=SDUT['s'][ifs][0,1]
				S21DUT=SDUT['s'][ifs][1,0]
				S22DUT=SDUT['s'][ifs][1,1]
				Fmin_preamp=np.power(10,systemnoiseparameters[ifp]['FmindB']/10)           # preamp minimum noise figure in linear format (convert dB to linear)
				F.append({})
				F[-1]['frequency']=NF_raw_measureddB[ifn]['frequency']                  # frequency of raw noise figures
				#ga_DUT=convertSRItoGMAX(s11=SDUT['s'][ifs][0,0],s21=SDUT['s'][ifs][1,0],s12=SDUT['s'][ifs][0,1],s22=SDUT['s'][ifs][1,1])         # get available gain of preamplifier    (linear)
				for p in positions:                    # iterate through the tuner_data positions where the raw noise figure was measured
					ga_tuner=tuner.get_tuner_availablegain(frequency=NF_raw_measureddB[ifn]['frequency'],position=p)                                    # get available gain of tuner_data+cascaded elements (linear)
					gammatuner=tuner.get_tuner_reflection(frequency=NF_raw_measureddB[ifn]['frequency'],position=p)
					gammaDUTout=S22DUT+(S12DUT*S21DUT*gammatuner/(1-S11DUT*gammatuner))
					ga_DUT=( (1-np.square(abs(gammatuner)))/np.square(abs(1-S11DUT*gammatuner)) )*np.square(abs(S21DUT))/(1-np.square(abs(gammaDUTout)))        # available gain of DUT in system
					NF_raw_measured=np.power(10,NF_raw_measureddB[ifn][p]/10)           # measured system+DUT noise figure in linear format (convert dB raw noisefigure to linear raw noisefigure)
					Fpreamp=Fmin_preamp+(4*systemnoiseparameters[ifp]['Rn']/Z0)*np.square(abs(systemnoiseparameters[ifp]['gopt']-gammaDUTout))/(np.square(abs(1+systemnoiseparameters[ifp]['gopt']))*(1-np.square(abs(gammaDUTout)))) # preamp noise figure (linear) within the noise measurement system
					F[-1][p]=(NF_raw_measured*ga_tuner)-((Fpreamp-1)/ga_DUT)             # deembedded DUT linear noise figure
		# no preamp considered in noise measurement system as this measurement is to characterize the preamp itself
		elif floatequal(NF_raw_measureddB[ifn]['frequency'],tuner.tuner_data[ift]['frequency'],0.0001):
			positions=[p for p in NF_raw_measureddB[ifn].keys() if p!='frequency']                      # get tuner_data positions from measured noise figure
			F.append({})
			F[-1]['frequency']=NF_raw_measureddB[ifn]['frequency']                  # frequency of raw noise figures
			for p in positions:                    # iterate through the tuner_data positions where the raw noise figure was measured
				ga_tuner=tuner.get_tuner_availablegain(frequency=NF_raw_measureddB[ifn]['frequency'],position=p)                                    # get available gain of tuner_data+cascaded elements (linear)
				NF_raw_measured=np.power(10,NF_raw_measureddB[ifn][p]/10)           # measured system+DUT noise figure in linear format (convert dB to linear)
				F[-1][p]=NF_raw_measured*ga_tuner                                    # add deembeddednoise figure (linear) measured at a single frequency and single tuner_data position p
	return F                                                                         # list of deembedded linear noise figures dictionaries one per frequency point
#######################################################################################################
# calculates the noise figure in dB given noise parameters and tuner_data position or reflection coefficient
# the reflection coefficient is given in real+jimaginary and Z0 is assumed to be 50ohms
def calculate_nffromnp(frequencyGHz=None,reflectioncoef=None,noiseparameters=None):
	if frequencyGHz==None or reflectioncoef==None or noiseparameters==None: raise ValueError("ERROR! input parameters missing!")
	frequency=frequencyGHz*1E9
	ifn=min(range(len(noiseparameters)), key=lambda i:abs(noiseparameters[i]['frequency']-frequency))             # find index of preamp noise parameter frequency that is closest to that requested
	Fmin=np.power(10.,noiseparameters[ifn]['FmindB']/10.)                     # convert noisefigure dB to linear
	F=Fmin+4.*(noiseparameters[ifn]['Rn']/Z0)*np.square(abs(noiseparameters[ifn]['gopt']-reflectioncoef))/((np.square(abs(1.+noiseparameters[ifn]['gopt'])))*(1.-np.square(abs(reflectioncoef))))
	return 10.*np.log10(F)
#######################################################################################################
