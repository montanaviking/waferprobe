# measure the preamp noise parameters
# input parameters:
from HP8970B_noisemeter import *
from old.MauryTunerMT986 import *
from old.calculate_noise_parameters import deembed_noise_figure, noise_parameters, calculate_nffromnp
from old.read_write_spar_noise import read_noise_parameters, read_spar, spar_flip_ports
from pna import *
from writefile_measured import X_writefile_noiseparameters, X_writefile_noisefigure

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
		self.reflectioncoefficients=reflectioncoefficients                      # selected reflection coefficients to be provided at the cascaded tuner 1 port during noise figure measurements
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
	def measure_noiseparameters(self,frequenciesGHz=None,DUTSpar=None):
		if self.usePNA:         # then will replace the DUTSpar provided in the parameter list with those measured from the PNA
			DUTSpar={}
			DUTSpar['frequency']=list(self.get_pna_frequencies())             # get the list of PNA frequencies in Hz
		if frequenciesGHz==None or len(frequenciesGHz)==0:  # then have no specified frequencies so use those in self._tuner and DUTSpar
			frequencies=[self.tuner_data[i]['frequency'] for i in range(0,len(self.tuner_data))]        # then use tuner frequencies if none provided
		else:
			frequencies=np.multiply(1E9,frequenciesGHz)
			frequencies=list(set(frequencies).intersection([self.tuner_data[i]['frequency'] for i in range(0,len(self.tuner_data))]))       # frequencies common to both the selected list and the tuner data
		if DUTSpar!=None and len(DUTSpar)>0:
			frequencies=list(set(frequencies).intersection(DUTSpar['frequency']))                                                           # frequencies common to the selected list + tuner data + S-parameter data of DUT
		# Now measure DUT noise parameters if and only if both the DUT S-parameters are supplied AND the system noise parameters are provided. Otherwise, we assume that this is a system noise parameter measurement
		self.NFraw=[]                                                                                                # noise figure (dB) of system+DUT
		frequencies.sort()
		for f in frequencies:                                                   # frequency f is in Hz
			if self.usePNA:                 # use the PNA to read the DUT S-parameters
				self.set_tuner_Z0()                     # set tuner to minimum reflections point because the PNA is calibrated in this state
				self.pna_getS(navg=self.navgPNA)        # measure DUT S-parameters if we are using the PNA
				self.pna_RF_onoff(RFon=False)            # turn off PNA RF so as not to interfer with the noise measurements
				DUTSpar['s']=[np.array([[self.s11[i],self.s12[i]],[self.s21[i],self.s22[i]]]) for i in range(0,len(self.freq))]         # put measured S-parameters into compatible format for noise parameter calculations
			self.NFraw.append({})            # append a frequency point on the raw noise figure
			#self.set_frequency(1E-6*f,smoothing=self.navgNF)        # set noisemeter frequency and smoothing
			for rr in self.reflectioncoefficients:                  # loop through selected reflection coefficients
				pos,rRI,rMA=self.get_tuner_position_from_reflection(frequency=f,requested_reflection=convertMAtoRI(rr[0],rr[1]))
				#pos is the tuner position required to get as close as possible to the requested reflection coefficient, rr whereas rRI and rMA is the actual reflection coefficient obtained from the tuner calibration data+cascaded 2-ports
				self.set_tuner_position(position=pos)               # set the tuner position mechanically
				gain,nfraw=self.get_NF_singlefrequency(frequency=1E-6*f)            # get the raw system+DUT noisefigure in dB from the noise meter
				self.NFraw[-1]['frequency']=f
				self.NFraw[-1][pos]=nfraw                      # raw noise figure dB measured for DUT+noise measurement system, at this tuner position
				print("frequency GHz "+str(1E-9*f)+"tuner position "+str(pos)+" tuner reflection coefficient mag "+str(rMA.real)+" angle deg "+str(rMA.imag)+" system+DUT noise figure and gain "+str(nfraw)+" dB, "+str(gain)+" dB")
		if DUTSpar!=None and self._npsys!=None and len(DUTSpar)>0 and len(self._npsys)>0:               # then we are measuring a DUT
			self.NF=deembed_noise_figure(NF_raw_measureddB=self.NFraw,tuner=self,SDUT=DUTSpar,systemnoiseparameters=self._npsys)        # find deembedded linear noise figure of DUT
			self.NP=noise_parameters(NF=self.NF,tuner=self,SDUT=DUTSpar)                                                                           # calculate DUT noise parameters
		else:       # since no DUT S-parameters and/or no system noise parameters are supplied, assume that we want instead to find the system noise parameters
			self.NF=deembed_noise_figure(NF_raw_measureddB=self.NFraw,tuner=self)        # find deembedded linear noise figure of the system
			self.NP=noise_parameters(NF=self.NF,tuner=self)                                                                           # calculate system noise parameters
		# calculate the noise figures expected from the noise parameters as a check on the noise parameters
		self.NFcalcfromNP=[]
		for f in frequencies:
			self.NFcalcfromNP.append({})
			for rr in self.reflectioncoefficients:                  # loop through selected reflection coefficients
				pos,rRI,rMA=self.get_tuner_position_from_reflection(frequency=f,requested_reflection=convertMAtoRI(rr[0],rr[1]))
				self.NFcalcfromNP[-1]['frequency']=f
				self.NFcalcfromNP[-1][pos]=calculate_nffromnp(frequencyGHz=1E-9*f,reflectioncoef=rRI,noiseparameters=self.NP)       # noise figure (dB) calculated from noise parameters - should be close as possible to self.NF
		return self.NP,self.NF,self.NFraw,self.NFcalcfromNP               # return the noise parameters vs frequency, deembedded DUT or system noise figure (dB), amd system+DUT or raw system noise figure in dB respectively
#####################################################################################################################################
	writefile_noiseparameters = X_writefile_noiseparameters
	writefile_noisefigure = X_writefile_noisefigure