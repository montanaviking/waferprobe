# measure the preamp noise parameters
# input parameters:
from focustuner_pos import *
#from focustuner import  *
from HP8970B_noisemeter import *
from pna import *
from spectrum_analyzer import *
from writefile_measured import X_writefile_noiseparameters_v2, X_writefile_noisefigure_v2
from utilities import floatequal
from read_write_spar_noise import read_noise_parameters, read_spar, spar_flip_ports
from calculate_noise_parameters_focus import calculate_nffromnp, calculate_gavail,calculate_NP_DUT,calculate_NP_DUT_direct,calculate_NP_noisemeter
#from noise_system_constants_calfiles import *

eps=1E-6            # used to compare floating point numbers
# reflectioncoefficients is a list of reflection coefficients used to measure the noise parameters in the format mag,ang where ang is in degrees
class NoiseParameters(object):
	def __init__(self,rm=None,navgPNA=16,navgNF=8,usePNA=False,usespectrumanalyzer=False,cascadefiles_port1=None,cascadefiles_port2=None,system_noiseparametersfile=None,reflectioncoefficients=None,tunercalfile=None,tunerIP=("192.168.1.30",23)):
		#self.measureDUToutputgamma=measureDUToutputgamma            # if True then measure output DUT reflection coefficient directly, else calculate it from the DUT S-parameters along with the tuner gamma setting
		#self.usespectrumanalyzer=usespectrumanalyzer            # use the spectrum analyzer instead of the noise meter to read the raw noise figure
		self.usePNA=usePNA
		self.navgPNA=navgPNA        # number of averages for PNA (S-parameter measurements)
		self.navgNF=navgNF          # number of averages (smoothing) of noisemeter
		# set up intruments
		self._noisemeter = NoiseMeter(rm=rm,ENR=15,preset=True,turnonnoisesourceonly=True)               # ENR is bogus because the noise meter is being used only to drive the noise source

		if self.usePNA:
			self._pna=Pna(rm=rm)            # network analyzer
			self._pna.pna_RF_onoff(RFon=False)                   # if possible, turn off PNA RF so as not to interfer with the noise measurements
		if usespectrumanalyzer: self._spectrumanalyzer=SpectrumAnalyzer(rm=rm)      # use spectrum analyzer
		else: self._spectrumanalyzer=None           # use noise meter instead of spectrum analyzer
		cascaded2port1=None
		cascaded2port2=None

		#############
		if reflectioncoefficients==None: raise ValueError("ERROR! No reflection coefficients given for the noise parameter measurements")
		if system_noiseparametersfile!=None and len(system_noiseparametersfile)>0: self._npsys=read_noise_parameters(system_noiseparametersfile)           # get noise measurement system noise parameters
		else: self._npsys=None
		self.reflectioncoefficients=reflectioncoefficients                      # user-selected set reflection coefficients to be provided at the cascaded tuner 1 port during noise figure measurements of format [[mag,angle], [mag,angle], etc...]
		#cascade available 2port networks onto port1 of tuner
		if cascadefiles_port1!=None and len(cascadefiles_port1)>0:
			for c in cascadefiles_port1:
				if c[1]=='flip':
					cascaded2port1=spar_flip_ports(read_spar(c[0]))  # then flip ports 1 and 2 on this two-port
				else:
					cascaded2port1=read_spar(c[0])                              # don't flip ports
		#cascade available 2port networks onto port2 of tuner
		if cascadefiles_port2!=None and len(cascadefiles_port2)>0:
			for c in cascadefiles_port2:
				if c[1]=='flip':
					cascaded2port2=spar_flip_ports(read_spar(c[0]))  # then flip ports 1 and 2 on this two-port
				else:
					cascaded2port2=read_spar(c[0])                              # don't flip ports
		self._tuner=FocusTuner(IP=tunerIP,S1=cascaded2port1,S2=cascaded2port2,tunertype='source',tunercalfile=tunercalfile)           # set up the tuner with the tuner calibration file tunerfile and the noise meter with the ENR
		# if tunercalfile!=None: super(NoiseParameters,self).__init__(S1=casaded2port1,S2=casaded2port2,tunertype='source',tunercalfile=tunercalfile)           # set up the tuner with the tuner calibration file tunerfile and the noise meter with the ENR
##################################################################################################################################
# get noise parameters at requested frequencies
# inputs are the self.tuner_data[frequencyMHz][motor position]=[s] where [s] is the 2x2 array of tuner S-parameters (real+jimaginary) at the frequency = frequencyMHz (MHz) and tuner motor position specified
# parameter frequenciesMHz is the user-selected set of proposed frequencies to measure. The frequencies actually measured are those which occur in the self.tuner_data, parameter DUTSpar, and the parameter frequenciesMHz
# DUTSpar is a set of previously-measured DUT S-parameters
# similar to the measure_noiseparameters() method except that the requested reflections are only for the lowest frequency, hereafter called f0, in the frequency sequence
# tuner positions are set according to the requested reflections at f0. Noise figure is measured at all the frequencies only for those tuner positions specified for f0. This allows measurement of all frequencies without moving the tuner for each
# specified tuner position.
# REQUIRES always both a 2-port PNA calibration AND a 1-port s22 PNA calibration if self.usePNA is True
# if usespectrumanalyzer==True, then use the spectrum anaylyzer to read the raw noisefigures. If usespectrumanalyzer=False, then rather use the noise meter to obtain the raw noisefigures
	def measure_noiseparameters_highspeed(self,frequenciesMHz=None,DUTSpar=None,pna_calset1port=None,pna_instrumentstate1port=None,pna_calset2port=None,pna_instrumentstate2port=None,spectrumanalyzerresolutionbandwidth=None,spectrumanalyzervideobandwidth=None,autoscalespectrumanalyzer=True,maxdeltaNF=None):
		frequencies=None
		if frequenciesMHz!=None and len(frequenciesMHz)>0:          # did we include the list of user-selected frequencies (frequenciesMHz type is a list of int)
			frequencies=[str(int(f)) for f in frequenciesMHz]    # round frequencies to int then convert to str list

		if pna_calset2port==None or pna_instrumentstate2port==None: self.usePNA=False          # then DO NOT use the pna since the calkit and/or instrumentstate have not been provided

		if (not self.usePNA) or pna_calset1port==None or pna_instrumentstate1port==None: measureDUToutputgamma=False        # do we measure the DUT output gamma?
		else: measureDUToutputgamma=True

		if (not self.usePNA) and DUTSpar!=None and len(DUTSpar)>0:            # if we are NOT using the pna and
			frequencies=[str(int(f)) for f in list(set(DUTSpar.keys())&set(list(self._tuner.tuner_data.keys()))&set(frequenciesMHz))]          # frequencies units is MHz
			if DUTSpar==None:   raise ValueError("ERROR! pna not used and no DUT S-parameters supplied")
		# Now measure DUT noise parameters if and only if both the DUT S-parameters are supplied AND the system noise parameters are provided. Otherwise, we assume that this is a system noise parameter measurement
		self.GaDUT={}
		self.NFraw={}                                                                                              # noise figure (dB) of system+DUT
		self.Gatuner={}
		self.tunerdata={}
		DUT_outputgamma={}
		self.noisecold={}
		self.noisehot={}
		# measure DUT S-parameters if we are to use the PNA
		if self.usePNA:                 # use the PNA to read the DUT S-parameters if requested to do so
			self._tuner.set_tuner_Z0()                     # set tuner to minimum reflections point because the PNA was calibrated in this state
			DUTSpar={}
			self._pna.pna_getS_2port(navg=self.navgPNA,instrumentstate=pna_instrumentstate2port,calset=pna_calset2port)        # measure DUT 2-port S-parameters if we are using the PNA. RF port power is left off so as not to interfere with noise measurements. This returns self.s11, self.s21,self.s12,self.s22
			fSpara=[str(int(1E-6*f)) for f in list(self._pna.get_pna_frequencies())]             # get the list of DUT S-parameter frequencies in MHz from the PNA in MHz as a list of type str
			if frequencies==None: frequencies=list(set(fSpara)&set(list(self._tuner.tuner_data.keys())))           # use all frequencies from PNA and intersect the frequency sets from the tuner and the pna. frequencies is a list of str
			else: frequencies=list(set(fSpara)&set(list(self._tuner.tuner_data.keys()))&set(frequencies))          # use only the intersection of the sets of frequencies specified AND the set of frequencies available from the PNA. frequencies is a list of str
		else:
			measureDUToutputgamma=False        # did not use PNA so cannot read DUT output reflection coefficient and don't try to measure DUT output reflection

		# build dictionaries
		frequencies=list(map(str,sorted(list(map(int,[int(float(f)) for f in frequencies])))))                       # sort frequencies in ascending value. Needed to use map() to sort frequencies since they are of type str
		#frequencies=[str(int(float(f))) for f in frequencies]                  # convert frequencies to strings
		for f in frequencies:       # f is a string representing the frequency in MHz
			self.GaDUT[f]={}
			self.NFraw[f]={}
			self.Gatuner[f]={}
			self.tunerdata[f]={}
			DUT_outputgamma[f]={}                 # reflection coefficient measured at output of DUT with the tuner(at the input of the DUT) set to the selected tuner gamma
			self.noisecold[f]={}
			self.noisehot[f]={}
			# find tuner positions for all selected reflection coefficients at the lowest frequency (f0)
		# get tuner positions, spos, calculated from the selected reflection coefficients, self.reflectioncoefficients, for the lowest frequency. These positions will be used for all frequencies
		spos=[[int(self._tuner.getPOS_reflection(frequency=frequencies[0],gamma=complex(rr[0],rr[1]),gamma_format='ma')['pos'].split(",")[0]), int(self._tuner.getPOS_reflection(frequency=frequencies[0],gamma=complex(rr[0],rr[1]),gamma_format='ma')['pos'].split(",")[1])] for rr in self.reflectioncoefficients]          # get positions for selected reflection coefficients format int p1,p2
		# sort reflection coefficients to speed tuning
		select_pos=sorted(spos, key=lambda x: (x[0],x[1]))       # sort all tuner positions from lowest to highest positions
		# if the spectrum analyzer is used to read the raw noise figure, then get
		#firstloop=True
		for p in select_pos:                  # loop through selected tuner positions. These tuner positions were selected based on selected reflection coefficients at f0, the lowest frequency analyzed
			self._tuner.setPOS(pos1=p[0],pos2=p[1])   # set the tuner position to select the tuner gamma
			if measureDUToutputgamma:           # then we want to measured the DUT output reflection coefficient directly when the tuner is set to the selected gamma, else we will calculate the DUT output reflection coefficient from DUT S-parameters + tuner gamma
				self._pna.pna_get_S_oneport(navg=self.navgPNA,instrumentstate=pna_instrumentstate1port,calset=pna_calset1port)      # get output DUT reflection coeffient as self.s22_oneport at the given tuner gamma setting, PNA RF port power is left off after this measurement so as not to interfere with noise measurements
			# if the spectrum analyzer is used to read the raw noise figure, then get the system+DUT noise figure in dB for all the frequencies for the given reflection coefficient established by the tuner at position p
			if not (self._spectrumanalyzer==None or spectrumanalyzerresolutionbandwidth==None or spectrumanalyzervideobandwidth==None):     # we are using the spectrum analyzer to measure raw noisefigure, rather than the noise meter
				frequenciesint=list(map(int,map(float,frequencies)))        # convert frequencies (MHz) from list of strings to list of ints
				self.get_NF_DUTandsystem_spectrumanalyzer(NFaverage=self.navgNF,startfrequencyMHz=frequenciesint[0],stopfrequencyMHz=frequenciesint[-1],resolutionbandwidthsetting=spectrumanalyzerresolutionbandwidth,videobandwidthsetting=spectrumanalyzervideobandwidth,autoscalereflevel=autoscalespectrumanalyzer)        # self.NFdB_sa contains the spectrum analyzer raw noisefigures vs frequency index of self.frequenciescold_sa
			for f in frequencies:               # loop through selected frequencies str representing the frequency in MHz
				tun=self._tuner.get_tuner_reflection_gain(frequency=f,position=",".join([str(p[0]),str(p[1])]))        # get tuner data at frequency f (MHz) and the tuner position defined by the selected reflection coefficient {"gamma_MA","gamma_RI","gain","Spar","frequency","pos"} gain is linear, not in dB
				pos=tun['pos']                       # get the tuner position x,y to use to index parameters such as self.GaDUT
				self.Gatuner[f][pos]=tun['gain']        # tuner gain at this position, in linear (not dB)
				self.tunerdata[f][pos]=tun                                           # tuner data vs frequency and tuner position

				if not (self._spectrumanalyzer==None or spectrumanalyzerresolutionbandwidth==None or spectrumanalyzervideobandwidth==None):     # we are using the spectrum analyzer to measure raw noisefigure, rather than the noise meter
					ifs=min(range(len(self.frequenciescold_sa)), key=lambda i:abs(int(float(f))-int(self.frequenciescold_sa[i])))            # find index of frequency closest to f. self.frequenciescold_sa[] was from self.get_NF_DUTandsystem_spectrumanalyzer()
					self.NFraw[f][pos]=self.NFdB_sa[ifs]        # self.NFdb_sa # [] was from self.get_NF_DUTandsystem_spectrumanalyzer()
					self.noisecold[f][pos]=self.noisecold_sa[ifs]    # spectral noise in dBm with noise diode off
					self.noisehot[f][pos]=self.noisehot_sa[ifs]      # spectral noise in dBm with noise diode on
				else:   # we are using the noise meter, rather than the spectrum analyzer, to measure the raw noisefigure of the DUT+system
					gain,self.NFraw[f][pos] = self._noisemeter.get_NF_singlefrequency(f)            # measure and get the raw system+DUT noisefigure in dB from the noise meter since we are NOT using the spectrum analyzer, the returned value gain, is not used

				if self.usePNA:                 # use the PNA to read the DUT S-parameters if requested to do so
					ifs=min(range(len(self._pna.freq)), key=lambda i:abs(int(f)-int(1E-6*self._pna.freq[i])))            # find index of frequency for the network analyzer. note that self.freq is the float equivalent of fSpara which is of type str. ifs is the frequency index chosen so that the frequency of the PNA S-parameters = f
					DUTSpar[f]=np.array([[self._pna.s11[ifs],self._pna.s12[ifs]],[self._pna.s21[ifs],self._pna.s22[ifs]]])         # put measured S-parameters into compatible format for noise parameter calculations from self.pna_getS_2port(navg=self.navgPNA)
					self.GaDUT[f][pos]=calculate_gavail(SDUT=DUTSpar[f],gammain=tun['gamma_RI'])['gavail']         # get DUT available gain if DUT is used, i.e. if this is NOT a noise system characterization
					if measureDUToutputgamma: # then we want to measured the DUT output reflection coefficient directly when the tuner is set to the selected gamma, else we will calculate the DUT output reflection coefficient from DUT S-parameters + tuner gamma
						DUT_outputgamma[f][pos]=self._pna.s22_oneport[ifs]         # directly measured 1-port DUT output reflection coefficient when DUT input is terminated in the selected tuner gamma

		if DUTSpar!=None and self._npsys!=None and len(DUTSpar)>0 and len(self._npsys)>0:               # then we are extracting the NP (noise parameters) of a DUT. self._npsys are the system noise parameters (when available)
			if measureDUToutputgamma:
				self.NP,self.NF = calculate_NP_DUT_direct(tunerdata=self.tunerdata,NPnoisemeter=self._npsys,NFDUTnoisemeterdB=self.NFraw,SDUT=DUTSpar,DUToutputreflectioncoefficient=DUT_outputgamma,maxdeltaNF=maxdeltaNF)        # use directly-measured 1-port DUT output reflection coefficient
			else:
				self.NP,self.NF = calculate_NP_DUT_direct(tunerdata=self.tunerdata,NPnoisemeter=self._npsys,NFDUTnoisemeterdB=self.NFraw,SDUT=DUTSpar,maxdeltaNF=maxdeltaNF)               # use DUT output reflection coefficient calculated from 2-port DUT S-parameters + tuner gamma
		else:       # since no DUT S-parameters and/or no system noise parameters are supplied, assume that we want instead to find the system noise parameters, i.e. the noise parameters of the noise measurement system components which would be connected to a DUT output
			self.NP,self.NF = calculate_NP_noisemeter(tunerdata=self.tunerdata,NF_raw_measureddB=self.NFraw)

		self.NFcalcfromNP={f:{p:calculate_nffromnp(reflectioncoef=self.tunerdata[f][p]['gamma_RI'],noiseparameters=self.NP[f]) for p in self.tunerdata[f].keys()} for f in frequencies}   # calculate the noise figures in dB expected from the noise parameters as a check on the noise parameters
		self._tuner.resettuner()                                                 # set tuner to the reset position
		return self.NP,self.NF,self.NFraw,self.NFcalcfromNP,self.noisecold,self.noisehot               # return the noise parameters vs frequency, deembedded DUT or system noise figure (dB), amd system+DUT or raw system noise figure in dB respectively
#####################################################################################################################################
##########################################################################################################################################################################################################
# get system noisefigure vs frequency using the spectrum analyzer in the frequency domain
# this is used to get the noise figure of the noise measurement system "noisemeter" for system calibration purposes
# this uses the swept-measurement sweepfrequency (Hz) to set the resolution and video bandwidths so as to mimic the spectrum analyzer settings for the time-domain measurements
	def get_NF_DUTandsystem_spectrumanalyzer(self,NFaverage=16,sweepfrequency=None,startfrequencyMHz=1000,stopfrequencyMHz=1600,resolutionbandwidthsetting=10E6,videobandwidthsetting=10E3,preamp=True,referencelevelguess=-60.,autoscalereflevel=True):
		referencelevelsetting=referencelevelguess           # used to set value of reference level if not using self._spectrumanalyzer.measure_peak_level_autoscale()
		#self.preamp=preamp
		if sweepfrequency!=None:                # then use the sweepfrequency to set the resolution and video bandwidths of the spectrum analyzer
			sweepperiod=1/sweepfrequency
			resolutionbandwidthsetting=50./sweepperiod          # in Hz
			#resolutionbandwidthsetting_autoscale=4./sweepperiod # in Hz
			videobandwidthsetting=resolutionbandwidthsetting/2  # in Hz
		centfreq=int((startfrequencyMHz+stopfrequencyMHz)/2.)*1E6       # center frequency Hz
		span=abs(int(stopfrequencyMHz-startfrequencyMHz)*1E6)       # frequency span frequency Hz

		# cold noise measurement (noise source off)#####################
		self._noisemeter.noise_sourceonoff(on=False)     # turn off noise source
		print("From line 173 in measure_noiseparameters_focus.py")
		if autoscalereflevel:
			referencelevelsetting,measuredfrequency,measuredpower=self._spectrumanalyzer.measure_peak_level_autoscale(referencelevel=referencelevelguess,frequency=centfreq,frequencyspan=span,averages=1,measurenoise=True)       # perform autoscaling IF requested
			if measuredpower+15.>referencelevelsetting: referencelevelsetting=referencelevelsetting+10.
		maxfreqcold,maxsigcold,self.frequenciescold_sa,self.noisecold_sa=self._spectrumanalyzer.measure_spectrum(numberofaverages=NFaverage,centfreq=centfreq,span=span,videobandwidth=videobandwidthsetting,resolutionbandwidth=resolutionbandwidthsetting,referencelevel=referencelevelsetting,attenuation=0,preamp=True)
		self.frequenciescold_sa=[1E-6*f for f in self.frequenciescold_sa]# convert frequencies from Hz to MHz

		# hot noise measurement (noise source on)###########################
		self._noisemeter.noise_sourceonoff(on=True)     # turn on noise source)
		if autoscalereflevel:
			referencelevelsetting,measuredfrequency,measuredpower=self._spectrumanalyzer.measure_peak_level_autoscale(referencelevel=referencelevelguess,frequency=centfreq,frequencyspan=span,averages=1,measurenoise=True)       # perform autoscaling IF requested
			if measuredpower+15.>referencelevelsetting: referencelevelsetting=referencelevelsetting+10.
		maxfreqhot,maxsighot,frequencieshot,self.noisehot_sa=           self._spectrumanalyzer.measure_spectrum(numberofaverages=NFaverage,centfreq=centfreq,span=span,videobandwidth=videobandwidthsetting,resolutionbandwidth=resolutionbandwidthsetting,referencelevel=referencelevelsetting,attenuation=0,preamp=True)
		frequencieshot=[1E-6*f for f in frequencieshot]# convert frequencies from Hz to MHz

		## post process #############
		# calculate raw system+DUT noise figure, dB, vs frequency (MHz) using the Y factor technique applied to all measured frequencies
		if(len(self.frequenciescold_sa) != len(frequencieshot)): raise ValueError("Internal ERROR!, Bug! number of cold measurement frequencies does not match the number of hot measurement frequencies")
		self.YfactdB=[self.noisehot_sa[i]-self.noisecold_sa[i] for i in range(0,len(self.frequenciescold_sa))]        # calculate Y-factor in dB vs frequency MHz
		Yfact = [dBtolin(y) for y in self.YfactdB]                           # convert dB to linear
		self.ENR=[ENRtablecubicspline(f) for f in self.frequenciescold_sa]          # get ENR (dB) from the cubic spline fit of the ENR table in loadpull_system_calibration.py, self.frequenciescold is in MHz
		self.NFdB_sa=[self.ENR[i]-lintodB(Yfact[i]-1) for i in range(0,len(self.frequenciescold_sa))]          # noisefigure, dB, of DUT+measurement system vs frequency in MHz, Yfact is linear
		self.actualresolutionbandwidth=self._spectrumanalyzer.get_resolutionbandwidth()             # get actual resolution bandwidth in Hz
		#self.noisecold_sa = [n-lintodB(self.actualresolutionbandwidth) for n in self.noisecold_sa]     # convert cold noise to dBm/Hz
		#self.noisehot_sa = [n-lintodB(self.actualresolutionbandwidth) for n in self.noisehot_sa]     # convert hot noise to dBm/Hz
		return self.frequenciescold_sa,self.NFdB_sa,self.noisecold_sa,self.noisehot_sa     # self.frequenciescold_sa is a list of int frequencies in MHz
##########################################################################################################################################################################################################
	writefile_noiseparameters = X_writefile_noiseparameters_v2
	writefile_noisefigure = X_writefile_noisefigure_v2