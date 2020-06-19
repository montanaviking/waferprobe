# measure the preamp noise parameters
# input parameters:
from MauryTunerMT986_v2 import *
from HP8970B_noisemeter import *
from pna import *
from writefile_measured import X_writefile_noiseparameters_v2, X_writefile_noisefigure_v2
from utilities import floatequal
from read_write_spar_noise_v2 import read_noise_parameters, read_spar, spar_flip_ports
from calculate_noise_parameters_v2 import noise_parameters, calculate_nffromnp, calculate_gavail,calculate_NP_DUT,calculate_NP_noisemeter

eps=1E-6            # used to compare floating point numbers

class NoiseParameters(MauryTunerMT986,NoiseMeter,Pna):
	def __init__(self,rm=None,navgPNA=16,navgNF=16,usePNA=False,ENR=12.99,tunerfile=None,tunernumber=None,cascadefiles_port1=None,cascadefiles_port2=None,system_noiseparametersfile=None,reflectioncoefficients=None):
		super(NoiseParameters,self).__init__(rm=rm,tunerfile=tunerfile,tunernumber=tunernumber)           # set up the tuner with the tuner calibration file tunerfile and the noise meter with the ENR
		self.usePNA=usePNA
		self.navgPNA=navgPNA        # number of averages for PNA (S-parameter measurements)
		self.navgNF=navgNF          # number of averages (smoothing) of noisemeter
		#if self.usePNA:
		pnafound=True
		try: Pna.__init__(self,rm=rm,navg=navgPNA)           # try to initialize the PNA
		except:
			self.usePNA=False                       # no PNA found so do not use it
			pnafound=False
		if pnafound: self.pna_RF_onoff(RFon=False)                   # if possible, turn off PNA RF so as not to interfer with the noise measurements
		NoiseMeter.__init__(self,rm=rm,ENR=ENR,smoothing=self.navgNF)
		#############
		if tunerfile==None: raise ValueError("ERROR! No tuner specified or set up")
		if reflectioncoefficients==None: raise ValueError("ERROR! No reflection coefficients given for the noise parameter measurements")
		if system_noiseparametersfile!=None and len(system_noiseparametersfile)>0: self._npsys=read_noise_parameters(system_noiseparametersfile)           # get noise measurement system noise parameters
		else: self._npsys=None
		self.reflectioncoefficients=reflectioncoefficients                      # user-selected set reflection coefficients to be provided at the cascaded tuner 1 port during noise figure measurements of format [[mag,angle], [mag,angle], etc...]
		#cascade available 2port networks onto port1 of tuner
		if cascadefiles_port1!=None and len(cascadefiles_port1)>0:
			for c in cascadefiles_port1:
				if c[1]=='flip': casaded2port=spar_flip_ports(read_spar(c[0]))  # then flip ports 1 and 2 on this two-port
				else: casaded2port=read_spar(c[0])                              # don't flip ports
				self.cascade_tuner(1,casaded2port)                              # cascade 2-port onto tuner's port 1
		#cascade available 2port networks onto port2 of tuner
		if cascadefiles_port2!=None and len(cascadefiles_port2)>0:
			for c in cascadefiles_port2:
				if c[1]=='flip': casaded2port=spar_flip_ports(read_spar(c[0]))  # then flip ports 1 and 2 on this two-port
				else: casaded2port=read_spar(c[0])                              # don't flip ports
				self.cascade_tuner(2,casaded2port)                              # cascade 2-port onto tuner's port 2
##################################################################################################################################
# get noise parameters at requested frequencies
# inputs are the self.tuner_data[frequencyMHz][motor position]=[s] where [s] is the 2x2 array of tuner S-parameters (real+jimaginary) at the frequency = frequencyMHz (MHz) and tuner motor position specified
# parameter frequenciesMHz is the user-selected set of proposed frequencies to measure. The frequencies actually measured are those which occur in the self.tuner_data, parameter DUTSpar, and the parameter frequenciesMHz
	def measure_noiseparameters(self,frequenciesMHz=None,DUTSpar=None):
		frequenciesMHz=[str(int(f)) for f in frequenciesMHz]    # convert to str list
		if DUTSpar!=None and len(DUTSpar)>0:
			frequencies=list(DUTSpar.keys())
		elif self.usePNA:         # then will replace the DUTSpar provided in the parameter list with those measured from the PNA
			DUTSpar={}
			fSpara=[str(int(1E-6*f)) for f in list(self.get_pna_frequencies())]             # get the list of DUT S-parameter frequencies from the PNA in MHz as a list of type str
			frequencies=list(set(frequenciesMHz)&set(fSpara))
		else: frequencies=None

		if (frequenciesMHz==None or len(frequenciesMHz)==0) and frequencies==None:  # then have no specified frequencies so use those in self._tuner and DUTSpar
			frequencies=list(self.tuner_data.keys()) # then use tuner frequencies (in MHz) if no DUT S-parameters are provided
		else: frequencies=list(set(frequenciesMHz)&set(self.tuner_data.keys()))
		frequencies=list(map(str,sorted(list(map(int,frequencies)))))                       # sort frequencies in ascending value. Needed to use map() to sort frequencies since they are of type str
		# Now measure DUT noise parameters if and only if both the DUT S-parameters are supplied AND the system noise parameters are provided. Otherwise, we assume that this is a system noise parameter measurement
		self.GaDUT={}
		self.NFraw={}                                                                                              # noise figure (dB) of system+DUT
		self.Gatuner={}
		for f in frequencies:                                                   # frequency f is in Hz
			if self.usePNA:                 # use the PNA to read the DUT S-parameters
				self.set_tuner_Z0()                     # set tuner to minimum reflections point because the PNA is calibrated in this state
				self.pna_getS(navg=self.navgPNA)        # measure DUT S-parameters if we are using the PNA
				self.pna_RF_onoff(RFon=False)            # turn off PNA RF so as not to interfer with the noise measurements
				ifs=min(range(len(self.freq)), key=lambda i:abs(int(f)-int(1E-6*self.freq[i])))            # note that self.freq is the float equivalent of fSpara which is of type str. ifs is the frequency index chosen so that the frequency of the PNA S-parameters = f
				DUTSpar[f]=np.array([[self.s11[ifs],self.s12[ifs]],[self.s21[ifs],self.s22[ifs]]])         # put measured S-parameters into compatible format for noise parameter calculations
			self.NFraw[f]={}            # append a frequency point on the raw noise figure
			if DUTSpar!=None and len(DUTSpar)>0: self.GaDUT[f]={}
			self.Gatuner[f]={}
			for rr in self.reflectioncoefficients:                  # loop through selected reflection coefficients
				pos,rRI,rMA=self.get_tuner_position_from_reflection(frequency=f,requested_reflection=convertMAtoRI(rr[0],rr[1]))
				#pos is the tuner position required to get as close as possible to the requested reflection coefficient, rr whereas rRI and rMA is the actual reflection coefficient obtained from the tuner calibration data+cascaded 2-ports
				if DUTSpar!=None and len(DUTSpar)>0 and len(self._npsys)>0:               # then we are measuring a DUT so get its available gain
					self.GaDUT[f][pos]=calculate_gavail(SDUT=DUTSpar[f],gammain=self.get_tuner_reflection(frequency=f,position=pos))[0]         # get DUT available gain if DUT is used, i.e. if this is NOT a noise system characterization
				self.Gatuner[f][pos]=self.get_tuner_availablegain_sourcepull(frequency=f,position=pos,flipports=True)             # get tuner available gain (linear)
				self.set_tuner_position(position=pos)               # set the tuner position mechanically
				gain,nfraw=self.get_NF_singlefrequency(f)            # get the raw system+DUT noisefigure in dB from the noise meter
				self.NFraw[f][pos]=nfraw                      # raw noise figure dB measured for DUT+noise measurement system, at this tuner position
				print("frequency GHz "+str(f)+" tuner position "+str(pos)+" tuner reflection coefficient mag "+str(rMA.real)+" angle deg "+str(rMA.imag)+" system+DUT noise figure and gain "+str(nfraw)+" dB, "+str(gain)+" dB")
		if DUTSpar!=None and self._npsys!=None and len(DUTSpar)>0 and len(self._npsys)>0:               # then we are measuring a DUT
			self.NP,self.NF=calculate_NP_DUT(tuner=self,NPnoisemeter=self._npsys,NFDUTnoisemeterdB=self.NFraw,SDUT=DUTSpar)
		else:       # since no DUT S-parameters and/or no system noise parameters are supplied, assume that we want instead to find the system noise parameters
			self.NP,self.NF=calculate_NP_noisemeter(tuner=self,NF_raw_measureddB=self.NFraw)
		# calculate the noise figures expected from the noise parameters as a check on the noise parameters
		self.NFcalcfromNP={}
		for f in frequencies:
			self.NFcalcfromNP[f]={}
			for rr in self.reflectioncoefficients:                  # loop through selected reflection coefficients
				pos,rRI,rMA=self.get_tuner_position_from_reflection(frequency=f,requested_reflection=convertMAtoRI(rr[0],rr[1]))
				self.NFcalcfromNP[f][pos]=calculate_nffromnp(reflectioncoef=rRI,noiseparameters=self.NP[f])       # noise figure (dB) calculated from noise parameters - should be close as possible to self.NF
		self.set_tuner_Z0()                                                 # set tuner reflection to a minimum
		return self.NP,self.NF,self.NFraw,self.NFcalcfromNP               # return the noise parameters vs frequency, deembedded DUT or system noise figure (dB), amd system+DUT or raw system noise figure in dB respectively
#####################################################################################################################################
	writefile_noiseparameters = X_writefile_noiseparameters_v2
	writefile_noisefigure = X_writefile_noisefigure_v2