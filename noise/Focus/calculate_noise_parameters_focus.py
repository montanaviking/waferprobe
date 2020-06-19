# calculates noise parameters from tuned noise figure measurements version 2 with mods to tuner and S-parameter dictionary structures
# see /carbpnics/owncloudsync/documents/analysis/noise/noise_parameters_from_tuned_measurements.odp
# NF is the measured noise figure in dB
MAXALLOWEDNFdB=25.  #maximum allowed noisefigure to accept point when calculating noise parameters
minnumbergammanoise=5   # minimum number of reflection coefficients allowed to determine noise parameters
import numpy as np
#from scipy.optimize import lsq_linear
from scipy.optimize import least_squares
from utilities import floatequal, dBtolin, lintodB, formatnum
#from MauryTunerMT986_v2 import *
from calculated_parameters import cascadeS, convertSRItoGMAX, convertSRItoUMAX, convertRItoMA, convertMAtoRI, convertSRItoGMAX,convertSRItoK
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
# gammaDUTinopt is the DUT's simultaneous conjugate input match which maximizes gain. Note that this is valid ONLY for a DUT which is unconditionally stable
# gammaDUToutopt is the DUT's simultaneous conjugate output match which maximizes gain. Note that this is valid ONLY for a DUT which is unconditionally stable
def calculate_gavail(SDUT=None,gammain=None):
	s11=SDUT[0][0]
	s21=SDUT[1][0]
	s12=SDUT[0][1]
	s22=SDUT[1][1]
	gammaDUTout=s22+(s12*s21*gammain/(1-s11*gammain))
	ga_DUT=( (1.-np.square(abs(gammain)))/np.square(abs(1-s11*gammain)) )*np.square(abs(s21))/(1.-np.square(abs(gammaDUTout)))        # available gain of DUT in system. Linear NOT dB.
	#ga_DUT=( (1.-np.square(abs(gammain)))/np.square(abs(1-s11*gammain)) )*np.square(abs(s21))/(1.-np.square(abs(s22)))        # available gain of DUT in system. Linear NOT dB. from Dunlevy et. al.
	# calculate optimum input and output match
	K=convertSRItoK(s11=s11,s21=s21,s12=s12,s22=s22)
	mag=convertSRItoGMAX(s11=s11,s21=s21,s12=s12,s22=s22)
	if K<1:
		gammaDUTinopt=None
		gammaDUToutopt=None
	else:       # see ref d2096.pdf eq 13.5.1 - 13.5.2
		D=s11*s22-s12*s21
		B1=1+np.square(abs(s11))-np.square(abs(s22))-np.square(abs(D))
		B2=1+np.square(abs(s22))-np.square(abs(s11))-np.square(abs(D))
		C1=s11-D*np.conj(s22)
		C2=s22-D*np.conj(s11)
		#D1=np.square(abs(s11))-np.square(abs(D))
		#D2=np.square(abs(s22))-np.square(abs(D))
		# C1sq=np.square(abs(s12*s21))+(1-np.square(abs(s22)))*D1
		# C2sq=np.square(abs(s12*s21))+(1-np.square(abs(s11)))*D2
		if B1>0.:
			gammaDUTinopt=(B1-np.sqrt(np.square(B1)-4*np.square(abs(C1))))/(2.*C1)
		else:
			gammaDUTinopt=(B1+np.sqrt(np.square(B1)-4*np.square(abs(C1))))/(2.*C1)
		if B2>0.:
			gammaDUToutopt=(B2-np.sqrt(np.square(B2)-4*np.square(abs(C2))))/(2.*C2)
		else:
			gammaDUToutopt=(B2+np.sqrt(np.square(B2)-4*np.square(abs(C2))))/(2.*C2)
	return {'gavail':ga_DUT,'gassoc':ga_DUT,'gammaDUTout':gammaDUTout,'MAG':mag['gain'],'K':K,'gammaDUTinopt':gammaDUTinopt,'gammaDUToutopt':gammaDUToutopt}
################
# same as calculate_gavail() except for time-domain swept gate data
# SDUT[timestampindex], gammain
# Return values:
# ga_DUT is the linear, NOT dB available gain of the SDUT parameters
def calculate_gavail_timedomain(SDUT=None,gammain=None):
	if gammain==None: raise ValueError("ERROR! no value for input reflection coefficient (presented by tuner)")
	if SDUT==None: raise ValueError("ERROR! no DUT S-parameters")
	ga_DUT=[]
	gammaDUTout=[]
	gammaDUTinopt=[]
	gammaDUToutopt=[]
	DUTMAG=[]
	DUTK=[]
	for it in range(0,len(SDUT)):
		if hasattr(gammain,"__len__"): g=calculate_gavail(SDUT=SDUT[it],gammain=gammain[it])
		else: g=calculate_gavail(SDUT=SDUT[it],gammain=gammain)
		ga_DUT.append(g['gassoc'])
		gammaDUTout.append(g['gammaDUTout'])
		gammaDUTinopt.append(g['gammaDUTinopt'])
		gammaDUToutopt.append(g['gammaDUToutopt'])
		DUTMAG.append(g['MAG'])
		DUTK.append(g['K'])
	return  {'gavail':ga_DUT,'gassoc':ga_DUT,'gammaDUTout':gammaDUTout,'MAG':DUTMAG,'K':DUTK,'gammaDUTinopt':gammaDUTinopt,'gammaDUToutopt':gammaDUToutopt}
########################################################################################################
####################################################################################################
# parameter Fgamma[][0] is the linear corrected noise figure (not dB) of the DUT for the given Fgamma[1]=gamma = reflection coefficient. F[tuner position index][0] = linear (not dB) noise figure vs tuner position, F[tuner position index][1]=tuner reflection coefficient (real + jimaginary) for the tuner position index
# parameter Fgamma[][0] is the actual linear DUT noise figure deembedded from the measured DUT+system noise figure
# parameter Fgamma[][1]=gamma is the real+jimaginary reflection coefficient presented to port 1, i.e. the input of the DUT
# uses the method of Lane with single valued decomposition techniques to evaluate noise parameters from an overdetermined matrix
# MUST use at least four values of F and gamma but should use at least eight values of each to get reasonable accuracy
# returns the three noise parameters FmindB, gammaopt, and Rn where FmindB is the optimum noise figure in dB obtained when the
# DUT has gammaopt presented to it's port 1
# gammaopt is the reflection coefficient, real+jimaginary, that when presented to port 1 of the DUT will give the minimum DUT noise figure of FmindB
# Rn is the noise resistance of the DUT
# if type=='weighted' then apply weighting to reduce errors and improve numerical stability
# as of Oct 14, 2019 bad noise figure points points (noise figure > MAXALLOWEDNFdB and below 1 (nonphysical)) are rejected from the noise parameter calculations
# as of April 28, 2020
# maxdeltaNF  = !=None and len(Fgamma)>=minnumbergammanoise: Then calculate deltaNF[i]=abs(NFfromnoiseparameters-Fgamma[i][0]) and remove all Fgamma[i] points for which deltaNF[i]>maxdeltaNF. This should improve quality of noise parameter fit and reduce errors due to "bad" data points
def solvefornoiseparameters(Fgamma=None,type='unweighted',maxdeltaNF=None):
	Fgamma=[Fgamma[i] for i in range(0,len(Fgamma)) if Fgamma[i][0]>1. and lintodB(Fgamma[i][0])<MAXALLOWEDNFdB]   # remove bad noisefigure points
	if len(Fgamma)<minnumbergammanoise: raise ValueError("ERROR! less than the required "+str(minnumbergammanoise)+" values of noise figure and gamma, len(Fgamma)= "+str(len(Fgamma)))
	if maxdeltaNF==None:
		looponce=True        # do just one loop
		maxdeltaNF=0.       # eliminate noise figure measurements which fail the test
	else: looponce=False
	maxNFpmNFm=1000000.     # This is the maximum allowed discrepancy between the measured noisefigure and that calculated from the calculated noise parameters. Start with a bogus value to ensure we do at least one loop
	while looponce or (len(Fgamma)>=minnumbergammanoise and maxdeltaNF!=None and maxdeltaNF<maxNFpmNFm):        # loop at least once
		looponce=False
		Y=[Y0*(1-Fg[1])/(1+Fg[1]) for Fg in Fgamma]       # convert gamma to Y (admittance)
		if type!='weighted':
			M=[[1., y.real+np.square(y.imag)/y.real, 1./y.real, y.imag/y.real] for y in Y]       # nx4 matrix
			ret=np.linalg.lstsq(M,[Fg[0] for Fg in Fgamma])                                                            # solve for A,B,C,D from Lane via least squares best fit
		else:   # apply weighting to the measured reflection coefficient points to improve numerical stability and accuracy
			print("from line 51 in calculate_noise_parameters_focus.py - weighted")
			weight=[(1.-np.square(abs(Fg[1])))/np.square(Fg[0]) for Fg in Fgamma]           # weighting factors = (1-|gamma|**2)/F**2
			M=[[weight[i], weight[i]*(Y[i].real+np.square(Y[i].imag)/Y[i].real), weight[i]/Y[i].real, weight[i]*Y[i].imag/Y[i].real] for i in range(0,len(Fgamma))]       # nx4 matrix
			ret=np.linalg.lstsq(M,[weight[i]*Fgamma[i][0] for i in range(0,len(Fgamma))],rcond=None)                                                         # solve for A,B,C,D from Lane via least squares best fit
		A=ret[0][0]
		B=ret[0][1]
		C=ret[0][2]
		D=ret[0][3]
		Rn=B
		Yopt=complex(np.sqrt(abs(4*B*C-np.square(D)))/(2*B),-D/(2*B))
		FmindB=10*np.log10(A+np.sqrt(abs(4*B*C-np.square(D))))                                   # calculate linear minimum noise figure in dB
		gammaopt=(Y0-Yopt)/(Y0+Yopt)
		##########
		#maxNFpmNFm=np.max([calculate_nffromnp(Fgamma[i][1],{'FmindB':lintodB(Fgamma[i][0]),'Rn':Rn,'gopt':Yopt},typedBout=True) for i in range(0,len(Fgamma))])     # Find maximum discrepancy between the measured noisefigure and that calculated from the
		imax=max(range(len(Fgamma)), key = lambda i:abs(calculate_nffromnp(Fgamma[i][1],{'FmindB':FmindB,'Rn':Rn,'gopt':gammaopt},typedBout=True)-lintodB(Fgamma[i][0])))
		maxdiscrepancy=abs(calculate_nffromnp(Fgamma[imax][1],{'FmindB':FmindB,'Rn':Rn,'gopt':gammaopt},typedBout=True)-lintodB(Fgamma[imax][0]))
		if len(Fgamma)>minnumbergammanoise and maxdiscrepancy>maxdeltaNF:
			print("from line 121 in calculate_noise_parameters_focus.py removing noise data point NF="+formatnum(lintodB(Fgamma[imax][0]),precision=2,nonexponential=True)+"dB discrepancy = "+formatnum(maxdiscrepancy,precision=2,nonexponential=True))
			del(Fgamma[imax])       # remove element with high discrepancy
		else: break
		print("from line 124 in calculate_noise_parameters_focus.py calculate_noise_parameters_focus.py residue = ",ret[1],FmindB,gammaopt,Rn)
		if maxNFpmNFm!=None: print("from line 104 number of remaining noise figure gammas "+str(len(Fgamma))+" largest delta = "+formatnum(precision=2,number=maxNFpmNFm,nonexponential=True))
		# if 4*B*C-np.square(D)<0:            # then must use nonlinear optimizer
		# 	np, = least_squares(fun=noiseeq())
	return(FmindB,gammaopt,Rn)
#############
# same as solvefornoiseparameters() except this solves for time-domain noiseparameters at one frequency
# NFDUT[p][timestampindex] are the DUT noise figures vs frequencyMHz, tuner position, and timestamp index
# tunerdata[p]['gamma_RI'] are the tuner reflection coefficients vs frequencyMHz and tuner position
# returns:
# NPDUT['type'][timestampindex] are the DUT noise parameters where f is frequencyMHz, 'type' is one of FmindB, the minimum noise figure in dB; gopt, the optimum noise match in real+jimaginary; or Rn, the noise resistance in ohms
def solvefornoiseparameters_timedomain(NFDUT=None,tunerdata=None,type='unweighted',maxdeltaNF=None):
	if NFDUT==None: raise ValueError("ERROR! no DUT noise figure data")
	if maxdeltaNF==None: raise ValueError("No maxdeltaNF given")
	notimestamps=len(NFDUT[list(NFDUT.keys())[0]])    # assumed that the number of timestamps is the same for every tuner position
	FmindB=[]
	gammaopt=[]
	Rn=[]
	for it in range(0,notimestamps):
		f,g,r=solvefornoiseparameters([[NFDUT[p][it],tunerdata[p]['gamma_RI']] for p in NFDUT.keys()],type=type,maxdeltaNF=maxdeltaNF)
		FmindB.append(f)
		gammaopt.append(g)
		Rn.append(r)
	return(FmindB,gammaopt,Rn)      # all are indexed by timestampindex
#####################################################################################################
#######################################################################################################
# calculates the noise figure in dB of a two-port given the two-port's noise parameters and the reflection coefficient presented to port 1 of the two-port
#
# parameter reflectioncoef is given in real+jimaginary and Z0 is assumed to be 50ohms
# parameter noiseparameters are the two-port's noise parameters and is of the form:
# noiseparameters['gammaopt':g,'FmindB':fmin,'Rn':rn,'GassocdB':gassoc} where fmin is the minimum noise figure  in dB, g is the optimum source reflection coefficient (which is complex),
# rn is the noise resistance, and gassoc is the associated two-port gain in dB.
def calculate_nffromnp(reflectioncoef=None,noiseparameters=None,typedBout=True):
	if reflectioncoef==None or noiseparameters==None: raise ValueError("ERROR! input parameters missing!")
	Fmin=dBtolin(noiseparameters['FmindB'])                     # convert noisefigure dB to linear if data are in dB
	F=Fmin+4.*(noiseparameters['Rn']/Z0)*np.square(abs(noiseparameters['gopt']-reflectioncoef))/(np.square(abs(1.+noiseparameters['gopt']))*(1.-np.square(abs(reflectioncoef))))
	if typedBout: return  lintodB(F)  # return dB noise figure
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
# output: NFDUT which is the dictionary containing the DUT noise figure (linear not dB) ['f']['p'] a dict of dicts where 'f' is the frequency in MHz (type str) and 'p' is the tuner position (type str)
# output: NPDUT which is the dictionary containing the DUT noise parameters ['f']['noiseparameter'] a dict of dicts
# maxdeltaNF is the maximum in dB, discrepancy between the noisefigure calculated from the noise parameter compared to that measured. If it's too high, then recalculate the noise parameters sans this data point
def calculate_NP_DUT(tunerdata=None, NPnoisemeter=None, NFDUTnoisemeterdB=None, SDUT=None,maxdeltaNF=0.2):
	if tunerdata==None or NFDUTnoisemeterdB==None or NPnoisemeter==None: raise ValueError("ERROR! Missing parameter in NP_DUT()")
	frequencies=list(set(tunerdata.keys())&set(NPnoisemeter.keys())&set(NFDUTnoisemeterdB.keys())&set(SDUT.keys()))            # list of frequencies in MHz that are common to all data
	frequencies=[str(ff) for ff in sorted([int(f) for f in frequencies])]                                                           # sort frequencies into ascending order
	NPDUT={}
	NFDUT={}                # DUT noise figure vs frequency (MHz) and tuner position
	NPDUTnoisemeter={}

	# first find noise parameters of DUT+noisemeter from DUT+noisemeter noise figures vs frequency and tuner position
	for f in frequencies:                # loop thru tuner data frequencies (frequencies in MHz)
		NPDUTnoisemeter[f]={}
		Fgam=[[dBtolin(NFDUTnoisemeterdB[f][p])*tunerdata[f][p]['gain'],tunerdata[f][p]['gamma_RI']] for p in tunerdata[f].keys()]
		NPDUTnoisemeter[f]['FmindB'],NPDUTnoisemeter[f]['gopt'],NPDUTnoisemeter[f]['Rn'] = solvefornoiseparameters(Fgamma=Fgam,type='weighted',maxdeltaNF=maxdeltaNF)    # calculated noise parameters for DUT+noisemeter together. Use this to extract the DUT noise parameters later in this code
		NPDUT[f]={}
	# then find DUT noise parameters using the previously-measured noisemeter noise parameters and the DUT+noisemeter noise figure parameters
		NFDUT[f]={}
		for p in tunerdata[f].keys():
			g=calculate_gavail(SDUT=SDUT[f],gammain=tunerdata[f][p]['gamma_RI'])  # get DUT available gain (linear) when terminated with a conjugate matched output and the tuner reflection coefficient at the DUT input and the DUT output reflection coefficient (real+Jimag) when the input is terminated with the tuner
			#ga_DUT,gammaDUTout,gammaDUTinopt,gammaDUToutopt,gaintype = calculate_gavail(SDUT=SDUT[f],gammain=tunerdata[f][p]['gamma_RI'])  # get DUT available gain (linear) when terminated with a conjugate matched output and the tuner reflection coefficient at the DUT input and the DUT output reflection coefficient (real+Jimag) when the input is terminated with the tuner
			print("from line 180 in ")
			NFnoisemeterfromNP = calculate_nffromnp(reflectioncoef=g['gammaDUTout'],noiseparameters=NPnoisemeter[f],typedBout=False)      # noise figure (linear) of noise meter from its noise parameters when terminated with the DUT output reflection coefficient
			NFDUTnoisemeterfromNP = calculate_nffromnp(reflectioncoef=tunerdata[f][p]['gamma_RI'],noiseparameters=NPDUTnoisemeter[f],typedBout=False)                # noise figure (linear) of the measured DUT+noisemeter from the DUT+noisemeter noise parameter when terminated with the tuner reflection coefficient
			NFDUT[f][p] = NFDUTnoisemeterfromNP-((NFnoisemeterfromNP-1.)/g['gavail']) # extracted noise figure of the DUT

		NPDUT[f]['FmindB'],NPDUT[f]['gopt'],NPDUT[f]['Rn'] = solvefornoiseparameters_timedomain(Fgamma=[[NFDUT[f][p],tunerdata[f][p]['gamma_RI']] for p in tunerdata[f].keys()],type='weighted',maxdeltaNF=maxdeltaNF)               # noise parameters of DUT from extracted DUT noise figure
		ret=calculate_gavail(SDUT=SDUT[f],gammain=NPDUT[f]['gopt'])             # calculated associated gain for DUT
		NPDUT[f]['GassocdB']=lintodB(ret['gassoc'])                                # associated gain in dB
		NPDUT[f]['gain_type']='gassoc'
		NPDUT[f]['gavaildB']=lintodB(convertSRItoGMAX(SDUT[f][0,0],SDUT[f][1,0],SDUT[f][0,1],SDUT[f][1,1])['gain'])
		NPDUT[f]['gammainopt']=ret['gammainopt']
		NPDUT[f]['gammaoutopt']=ret['gammaoutopt']
	return NPDUT,NFDUT
#######################################################################################################
# similar to the function calculate_NP_DUT()
# except that this function calculates the noisefigure of the DUT directly from the noise parameters of the noisemeter and directly from the measured noise figures of the DUT+noisemeter
# maxdeltaNF is the maximum in dB, discrepancy between the noisefigure calculated from the noise parameter compared to that measured. If it's too high, then recalculate the noise parameters sans this data point
# Parameters:
# tunerdata has the form: tunerdata[frequencyMHz][tuner position]['type'] where type is 'gamma_MA','gamma_RI', 'gain', 'Spar', 'frequency', 'pos'
# where 'gamma_MA' is mag+jangle, gamma_RI is real+jimaginary, gain is the tuner available gain, linear not dB and <1, frequency is in MHz
# and Spar are the composite tuner's S-parameter in a 2x2 array
# NPnoisemeter are the noise parameters of the noise meter, i.e. the noise measurement system which all the equipment connected to the output of the DUT
# NPnoisemeter[frequency MHz]['type'] where 'type' is FmindB, the minimum noise figure in dB, 'Rn', the noise resistance in ohms, 'gopt' the optimum reflection coefficient real+jimaginary presented to the input of the noise meter
# SDUT are the DUT S-parameters SDUT['frequency MHz'] and are a 2x2 array
# DUToutputreflectioncoefficient is the DUT output reflection coefficient presented to the noise meter input DUToutputreflectioncoefficient[frequency MHz][tuner position] which is real+jimaginary
def calculate_NP_DUT_direct(tunerdata=None, NPnoisemeter=None, NFDUTnoisemeterdB=None, SDUT=None,DUToutputreflectioncoefficient=None,maxdeltaNF=0.1):
	if tunerdata==None or NFDUTnoisemeterdB==None or NPnoisemeter==None: raise ValueError("ERROR! Missing parameter in NP_DUT_direct()")
	frequencies=list(set(tunerdata.keys())&set(NPnoisemeter.keys())&set(NFDUTnoisemeterdB.keys())&set(SDUT.keys()))            # list of frequencies in MHz that are common to all data
	frequencies=[str(ff) for ff in sorted([int(f) for f in frequencies])]                                                           # sort frequencies into ascending order
	NPDUT={}
	NFDUT={}                # DUT noise figure vs frequency (MHz) and tuner position
	NPDUTnoisemeter={}
	# first find noise parameters of DUT+noisemeter from DUT+noisemeter noise figures vs frequency and tuner position
	for f in frequencies:                # loop thru tuner data frequencies (frequencies in MHz)
		NPDUTnoisemeter[f]={}
		Fgam=[[dBtolin(NFDUTnoisemeterdB[f][p])*tunerdata[f][p]['gain'],tunerdata[f][p]['gamma_RI']] for p in tunerdata[f].keys()]
		NPDUT[f]={}
	# then find DUT noise parameters using the previously-measured noisemeter noise parameters and the DUT+noisemeter noise figure parameters
		NFDUT[f]={}
		for p in tunerdata[f].keys():
			#ga_DUT,gammaDUTout,gammaDUTinopt,gammaDUToutopt,gaintype = calculate_gavail(SDUT=SDUT[f],gammain=tunerdata[f][p]['gamma_RI'])  # get DUT available gain (linear) when terminated with a conjugate matched output and the tuner reflection coefficient at the DUT input and the DUT output reflection coefficient (real+Jimag) when the input is terminated with the tuner
			g= calculate_gavail(SDUT=SDUT[f],gammain=tunerdata[f][p]['gamma_RI'])  # get DUT available gain (linear) when terminated with a conjugate matched output and the tuner reflection coefficient at the DUT input and the DUT output reflection coefficient (real+Jimag) when the input is terminated with the tuner
			if DUToutputreflectioncoefficient!=None: # use directly-measured DUT output reflection coefficient
				NFnoisemeterfromNP = calculate_nffromnp(reflectioncoef=DUToutputreflectioncoefficient[f][p],noiseparameters=NPnoisemeter[f],typedBout=False)      # noise figure (linear) of noise meter from its noise parameters when terminated with the DUT output reflection coefficient
			else:       # use DUT output reflection coefficient calculated from the DUT S-parameters + tuner gamma
				NFnoisemeterfromNP = calculate_nffromnp(reflectioncoef=g['gammaDUTout'],noiseparameters=NPnoisemeter[f],typedBout=False)      # noise figure (linear) of noise meter from its noise parameters when terminated with the DUT output reflection coefficient
			NFDUT[f][p] = dBtolin(NFDUTnoisemeterdB[f][p])*tunerdata[f][p]['gain']-((NFnoisemeterfromNP-1.)/g['gavail']) # deembedded noise figure of the DUT linear not dB
		NPDUT[f]['FmindB'],NPDUT[f]['gopt'],NPDUT[f]['Rn'] = solvefornoiseparameters(Fgamma=[[NFDUT[f][p],tunerdata[f][p]['gamma_RI']] for p in tunerdata[f].keys()],type='weighted',maxdeltaNF=maxdeltaNF)               # noise parameters of DUT from extracted DUT noise figure linear NOT dB
		# Now filter out "bad" noise measurements
		ret=calculate_gavail(SDUT=SDUT[f],gammain=NPDUT[f]['gopt'])             # calculated associated gain for DUT which is the available gain for of the DUT with its input port loaded at the optimum noise impedance
		NPDUT[f]['GassocdB']=lintodB(ret['gassoc'])                                # associated gain in dB
		NPDUT[f]['gain_type']='gassoc'
		NPDUT[f]['gavaildB']=lintodB(convertSRItoGMAX(SDUT[f][0,0],SDUT[f][1,0],SDUT[f][0,1],SDUT[f][1,1])['gain'])
		NPDUT[f]['gammainopt']=ret['gammainopt']
		NPDUT[f]['gammaoutopt']=ret['gammaoutopt']
	return NPDUT,NFDUT
##########################################################################################################################################################################################
# similar to the function calculate_NP_DUT_direct()
# except that this function calculates the DUT noise parameters and noise figures for all timesteps
# maxdeltaNF is the maximum in dB, discrepancy between the noisefigure calculated from the noise parameter compared to that measured. If it's too high, then recalculate the noise parameters sans this data point
# Parameters:
# tunerdata has the form: tunerdata[frequencyMHz][tuner position]['type'] where type is 'gamma_MA','gamma_RI', 'gain', 'Spar', 'frequency', 'pos'
# where 'gamma_MA' is mag+jangle, gamma_RI is real+jimaginary, gain is the tuner available gain, linear not dB and <1, frequency is in MHz
# and Spar are the composite tuner's S-parameter in a 2x2 array
# NPnoisemeter are the noise parameters of the noise meter, i.e. the noise measurement system which all the equipment connected to the output of the DUT
# NPnoisemeter[frequency MHz]['type'] where 'type' is FmindB, the minimum noise figure in dB, 'Rn', the noise resistance in ohms, 'gopt' the optimum reflection coefficient real+jimaginary presented to the input of the noise meter
# SDUT are the DUT S-parameters SDUT['frequency MHz'][timestamp index] and are a 2x2 array
# NFDUTnoisemeterdB is the noise meter + DUT measured noise figures NFDUTnoisemeterdB[frequency MHz][tuner position][timestampindex]
# NPDUT are the DUT noise parameters NPDUT[frequency MHz]['type'][timestampindex] where type is one of FmindB, minimum noise figure in dB; gopt, optimum tuner reflection coefficient in real+jimaginary
#       Rn, the DUT noise resistance in ohms; GassocdB, DUT associated gain, i.e. DUT available gain with DUT input terminated in gopt; gain
# DUToutputreflectioncoefficient is the DUT output reflection coefficient presented to the noise meter input DUToutputreflectioncoefficient[frequency MHz][tuner position][timestamp index] which is real+jimaginary
def calculate_NP_DUT_direct_timedomain(tunerdata=None, NPnoisemeter=None, NFDUTnoisemeterdB=None, SDUT=None,DUToutputreflectioncoefficient=None,maxdeltaNF=None):
	if maxdeltaNF==None: raise ValueError("ERROR! maxdeltaNF not specified")
	if tunerdata==None or NFDUTnoisemeterdB==None or NPnoisemeter==None: raise ValueError("ERROR! Missing parameter in NP_DUT_direct_timedomain()")
	frequencies=list(set(tunerdata.keys())&set(NPnoisemeter.keys())&set(NFDUTnoisemeterdB.keys())&set(SDUT.keys()))            # list of frequencies in MHz that are common to all data
	frequencies=[str(ff) for ff in sorted([int(f) for f in frequencies])]                                                           # sort frequencies into ascending order
	NPDUT={}
	NFDUT={}                # DUT noise figure vs frequency (MHz) and tuner position
	NPDUTnoisemeter={}
	# sanity check
	# first find noise parameters of DUT+noisemeter from DUT+noisemeter noise figures vs frequency and tuner position
	for f in frequencies:                # loop thru frequencies (frequencies in MHz)
		NPDUTnoisemeter[f]={}
		NPDUT[f]={}
	# then find DUT noise parameters using the previously-measured noisemeter noise parameters and the DUT+noisemeter noise figure parameters
		NFDUT[f]={}
		for p in tunerdata[f].keys():       # step through tuner gamma values (p = tuner position)
			if(len(NFDUTnoisemeterdB[f][p])!=len(SDUT[f])): raise ValueError("ERROR! different number of timestamps in NFDUTnoisemeterdB[f][p] as compared to SDUT[f]")
			NFDUT[f][p]=[]
			for it in range(0,len(NFDUTnoisemeterdB[f][p])):        # step through timestamps
				ga_DUT,gammaDUTout,gammaDUTinopt,gammaDUToutopt,gaintype = calculate_gavail(SDUT=SDUT[f][it],gammain=tunerdata[f][p]['gamma_RI'])  # get DUT available gain (linear) when terminated with a conjugate matched output and the tuner reflection coefficient at the DUT input and the DUT output reflection coefficient (real+Jimag) when the input is terminated with the tuner
				if DUToutputreflectioncoefficient!=None: # use directly-measured DUT output reflection coefficient
					NFnoisemeterfromNP = calculate_nffromnp(reflectioncoef=DUToutputreflectioncoefficient[f][p]['gamma'][it],noiseparameters=NPnoisemeter[f],typedBout=False)      # noise figure (linear) of noise meter from its noise parameters when terminated with the DUT output reflection coefficient
				else:       # use DUT output reflection coefficient calculated from the DUT S-parameters + tuner gamma
					NFnoisemeterfromNP = calculate_nffromnp(reflectioncoef=gammaDUTout,noiseparameters=NPnoisemeter[f],typedBout=False)      # noise figure (linear) of noise meter from its noise parameters when terminated with the DUT output reflection coefficient
				NFDUT[f][p].append(dBtolin(NFDUTnoisemeterdB[f][p][it])*tunerdata[f][p]['gain']-((NFnoisemeterfromNP-1.)/ga_DUT)) # deembedded noise figure of the DUT linear not dB
		NPDUT[f]['FmindB'],NPDUT[f]['gopt'],NPDUT[f]['Rn']=solvefornoiseparameters_timedomain(NFDUT=NFDUT[f],tunerdata=tunerdata[f],type='weighted',maxdeltaNF=maxdeltaNF)           # noise parameters of DUT from extracted DUT noise figure linear NOT dB, filters out "bad" noise measurements, Return values are functions of timestampindex
		#NPDUT[f]['GassocdB'],go,NPDUT[f]['gammainopt'],NPDUT[f]['gammaoutopt'],NPDUT[f]['gain_type']=calculate_gavail_timedomain(SDUT=SDUT[f],gammain=NPDUT[f]['gopt'])           # calculated associated gain for DUT which is the available gain for of the DUT with its input port loaded at the optimum noise impedance
		g=calculate_gavail_timedomain(SDUT=SDUT[f],gammain=NPDUT[f]['gopt'])           # calculated associated gain for DUT which is the available gain for of the DUT with its input port loaded at the optimum noise impedance
		NPDUT[f]['GassocdB']=[lintodB(ga) for ga in g['gassoc'] ]
		NPDUT[f]['gammainopt']=list(g['gammaDUTinopt'])
		NPDUT[f]['gammaoutopt']=list(g['gammaDUToutopt'])
		NPDUT[f]['gain_type']='gassoc'
	return NPDUT,NFDUT
##################################################################################################################################################################################
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
			NF_raw_measured=dBtolin(NF_raw_measureddB[f][p])           # convert measured noisemeter noise figure from dB to linear format (convert dB raw noisefigure to linear raw noisefigure)
			NFnoisemeter[f][p]=NF_raw_measured*tunerdata[f][p]['gain']                       # noisemeter noise figure (linear at frequency f (MHz)) and tuner motor position p)
		NPnoisemeter[f]['FmindB'],NPnoisemeter[f]['gopt'],NPnoisemeter[f]['Rn'] = solvefornoiseparameters(Fgamma=[[NFnoisemeter[f][p],tunerdata[f][p]['gamma_RI']] for p in tunerdata[f].keys()],type='weighted')                                 # calculated noise parameters for DUT at frequency f (MHz)
	return NPnoisemeter,NFnoisemeter