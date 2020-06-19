# measure the preamp noise parameters
# input parameters:
from focustuner import *
from HP8970B_noisemeter import *
from pna import *
from writefile_measured import X_writefile_noiseparameters_v2, X_writefile_noisefigure_v2
from utilities import floatequal
from read_write_spar_noise import read_noise_parameters, read_spar, spar_flip_ports
from calculate_noise_parameters_focus import noise_parameters, calculate_nffromnp, calculate_gavail,calculate_NP_DUT,calculate_NP_noisemeter

eps=1E-6            # used to compare floating point numbers
# reflectioncoefficients is a list of reflection coefficients used to measure the noise parameters in the format mag,ang where ang is in degrees
class NoiseParameters(FocusTuner,NoiseMeter,Pna):
	def __init__(self,rm=None,navgPNA=16,navgNF=16,usePNA=False,ENR=12.99,cascadefiles_port1=None,cascadefiles_port2=None,system_noiseparametersfile=None,reflectioncoefficients=None):

		self.usePNA=usePNA
		self.navgPNA=navgPNA        # number of averages for PNA (S-parameter measurements)
		self.navgNF=navgNF          # number of averages (smoothing) of noisemeter
		pnafound=True
		try: Pna.__init__(self,rm=rm,navg=navgPNA)           # try to initialize the PNA
		except:
			self.usePNA=False                       # no PNA found so do not use it
			pnafound=False
		if pnafound: self.pna_RF_onoff(RFon=False)                   # if possible, turn off PNA RF so as not to interfer with the noise measurements
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
				if c[1]=='flip': casaded2port1=spar_flip_ports(read_spar(c[0]))  # then flip ports 1 and 2 on this two-port
				else: casaded2port1=read_spar(c[0])                              # don't flip ports
		#cascade available 2port networks onto port2 of tuner
		if cascadefiles_port2!=None and len(cascadefiles_port2)>0:
			for c in cascadefiles_port2:
				if c[1]=='flip': casaded2port2=spar_flip_ports(read_spar(c[0]))  # then flip ports 1 and 2 on this two-port
				else: casaded2port2=read_spar(c[0])                              # don't flip ports
		super(NoiseParameters,self).__init__(S1=casaded2port1,S2=casaded2port2,tunertype='source')           # set up the tuner with the tuner calibration file tunerfile and the noise meter with the ENR
		NoiseMeter.__init__(self,rm=rm,ENR=ENR,smoothing=self.navgNF)       # set up noise meter
##################################################################################################################################
# get noise parameters at requested frequencies
# inputs are the self.tuner_data[frequencyMHz][motor position]=[s] where [s] is the 2x2 array of tuner S-parameters (real+jimaginary) at the frequency = frequencyMHz (MHz) and tuner motor position specified
# parameter frequenciesMHz is the user-selected set of proposed frequencies to measure. The frequencies actually measured are those which occur in the self.tuner_data, parameter DUTSpar, and the parameter frequenciesMHz
# DUTSpar is a set of previously-measured DUT S-parameters
	def measure_noiseparameters(self,frequenciesMHz=None,DUTSpar=None):
		frequencies=None
		if frequenciesMHz!=None and len(frequenciesMHz)>0:
			frequencies=frequenciesMHz    # convert to str list
			if DUTSpar!=None and len(DUTSpar)>0:
				frequencies=list(set(DUTSpar.keys())&set(self.allowedfrequencies)&set(frequenciesMHz))
		elif self.usePNA:         # then will replace the DUTSpar provided in the parameter list with those measured from the PNA
			DUTSpar={}
			fSpara=[str(int(1E-6*f)) for f in list(self.get_pna_frequencies())]             # get the list of DUT S-parameter frequencies from the PNA in MHz as a list of type str
			if frequencies==None: frequencies=list(set(fSpara)&set(self.allowedfrequencies))
			else: frequencies=list(set(fSpara)&set(self.allowedfrequencies)&set(frequencies))

		frequencies=list(map(str,sorted(list(map(int,frequencies)))))                       # sort frequencies in ascending value. Needed to use map() to sort frequencies since they are of type str
		frequencies=[str(int(f)) for f in frequencies]                  # convert frequencies to strings
		# Now measure DUT noise parameters if and only if both the DUT S-parameters are supplied AND the system noise parameters are provided. Otherwise, we assume that this is a system noise parameter measurement
		self.GaDUT={}
		self.NFraw={}                                                                                              # noise figure (dB) of system+DUT
		self.Gatuner={}
		tunerdata={}
		# build dictionaries
		for f in frequencies:
			self.GaDUT[f]={}
			self.NFraw[f]={}
			self.Gatuner[f]={}
			tunerdata[f]={}

		for rr in self.reflectioncoefficients:                  # loop through selected reflection coefficients
			for f in frequencies:                                                   # frequency f is in MHz
				tun=self.set_tuner_reflection(frequency=f,gamma=complex(rr[0],rr[1]),gamma_format='ma')         # get tuner data at frequency f (MHz) and the tuner position defined by the selected reflection coefficient
				pos=tun['pos']                       # get the tuner position x,y to use to index parameters such as self.GaDUT
				tunerdata[f][pos]=tun                                           # tuner data vs frequency and tuner position
				gain,self.NFraw[f][pos] = self.get_NF_singlefrequency(f)            # measure and get the raw system+DUT noisefigure in dB from the noise meter
				if self.usePNA:                 # use the PNA to read the DUT S-parameters if requested to do so
					self.set_tuner_Z0()                     # set tuner to minimum reflections point because the PNA is calibrated in this state
					self.pna_getS(navg=self.navgPNA)        # measure DUT S-parameters if we are using the PNA
					self.pna_RF_onoff(RFon=False)            # turn off PNA RF so as not to interfer with the noise measurements
					ifs=min(range(len(self.freq)), key=lambda i:abs(int(f)-int(1E-6*self.freq[i])))            # note that self.freq is the float equivalent of fSpara which is of type str. ifs is the frequency index chosen so that the frequency of the PNA S-parameters = f
					DUTSpar[f]=np.array([[self.s11[ifs],self.s12[ifs]],[self.s21[ifs],self.s22[ifs]]])         # put measured S-parameters into compatible format for noise parameter calculations
					self.GaDUT[f][pos]=calculate_gavail(SDUT=DUTSpar[f],gammain=tun['gamma_RI'])[0]         # get DUT available gain if DUT is used, i.e. if this is NOT a noise system characterization
				print("frequency GHz "+str(f)+" tuner position "+str(pos)+" tuner reflection coefficient mag "+str(rr[0])+" angle deg "+str(rr[1])+" system+DUT noise figure and gain "+str(self.NFraw[f][pos])+" dB, "+str(gain)+" dB")

		if DUTSpar!=None and self._npsys!=None and len(DUTSpar)>0 and len(self._npsys)>0:               # then we are extracting the NP (noise parameters) of a DUT
			self.NP,self.NF = calculate_NP_DUT(tunerdata=tunerdata,NPnoisemeter=self._npsys,NFDUTnoisemeterdB=self.NFraw,SDUT=DUTSpar)
		else:       # since no DUT S-parameters and/or no system noise parameters are supplied, assume that we want instead to find the system noise parameters, i.e. the noise parameters of the noise measurement system components which would be connected to a DUT output
			self.NP,self.NF = calculate_NP_noisemeter(tunerdata=tunerdata,NF_raw_measureddB=self.NFraw)

		self.NFcalcfromNP={f:{p:calculate_nffromnp(reflectioncoef=tunerdata[f][p]['gamma_RI'],noiseparameters=self.NP[f]) for p in tunerdata[f].keys()} for f in frequencies}   # calculate the noise figures in dB expected from the noise parameters as a check on the noise parameters
		self.set_tuner_Z0()                                                 # set tuner reflection to a minimum
		return self.NP,self.NF,self.NFraw,self.NFcalcfromNP               # return the noise parameters vs frequency, deembedded DUT or system noise figure (dB), amd system+DUT or raw system noise figure in dB respectively
#####################################################################################################################################
	writefile_noiseparameters = X_writefile_noiseparameters_v2
	writefile_noisefigure = X_writefile_noisefigure_v2