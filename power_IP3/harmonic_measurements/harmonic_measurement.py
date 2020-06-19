# measures output power of fundamental and harmonics using MS2719B spectrum analyzer
import numpy as np
from spectrum_analyzer import *
from rf_synthesizer import *
from parameter_analyzer import *
from writefile_measured import X_writefile_harmonicdistortion
# frequencies in Hz attenuation and calibration factors in dB
# input attenuation is the input attenuation setting of the spectrum analyzer
#
spandfund=2000.     # frequency span used to measure fundamental and harmonics
spandharm=1000.
maxitermeas=20      # maximum number of iterations to stabilize RF output power
thirdorderfromthirdharm=9.542      # TOI 3rd order products - 3rd harmonic (add this to third harmonic product to estimate the TOI products for the same fundamental power level - assuming that each fundamental power of the 2-tones is equal to that of the single-fundamental tone used to measure the 3rd harmonic
class Harmonic_distortion(object):
	def __init__(self,rm=None,sa=None,rf=None,dc=None,spectrum_analyser_input_attenuation=10.,
	             fundamental_frequency=None, source_calibration_factor_fundamental=None, SA_calibration_factor_fundamental=None, SA_calibration_factor_2nd_harmonic=None, SA_calibration_factor_3rd_harmonic=None):
		self.fundamental_frequency=fundamental_frequency
		self.sa_attenuationdB=spectrum_analyser_input_attenuation
		self.calfactor_source_fund=source_calibration_factor_fundamental        # =  power meter reading at DUT input at fundamental frequency - rf synthesizer power setting in dB
		self.calfactor_sa_fund=SA_calibration_factor_fundamental                # = power meter reading at DUT output at fundamental frequency - spectrum analyzer power reading in dB, includes output fixture and cable losses
		self.calfactor_sa_harm2=SA_calibration_factor_2nd_harmonic                   # = power meter reading at DUT output at harmonic frequency - spectrum analyzer power reading in dB, includes output fixture and cable losses
		self.calfactor_sa_harm3=SA_calibration_factor_3rd_harmonic                   # = power meter reading at DUT output at harmonic frequency - spectrum analyzer power reading in dB, includes output fixture and cable losses

		self.referencelevelfund=None                                            # spectrum analyzer reference level used when measuring the fundamental RF signal
		self.referencelevelharm2=None                                            # spectrum analyzer reference level used when measuring the 2nd harmonic RF signal
		self.referencelevelharm3=None                                            # spectrum analyzer reference level used when measuring the 3rd harmonic RF signal
		self.__sa=sa            # spectrum analyzer handle
		self.__rf=rf            # RF synthesizer handle
		self.__dc=dc            # semiconductor parameter analyzer handle

		if (self.__sa==None or self.__dc==None or self.__rf==None) and rm==None: raise ValueError("ERROR! needed to specify resource manager but none given")
		if self.__sa==None:
			try: self.__sa=SpectrumAnalyzer(rm)
			except: raise ValueError("ERROR! No spectrum analyzer found!")
		if self.__rf==None:
			try: self.__rf=Synthesizer(rm=rm,syn='A')
			except: raise ValueError("ERROR! No RF synthesizer found!")
		# if self.__dc==None:
		# 	try: self.__dc=ParameterAnalyzer(rm=rm,LAN=True)
		# 	except: raise ValueError("ERROR! No parameter analyzer found")

		self.__rf.off()         # turn off RF power
		self.__rf.set_frequency(self.fundamental_frequency)

		self.__sa.set_attenuation(att=self.sa_attenuationdB)
		self.__sa.set_sweepon()
		#self.__sa.set_numberaverages(self.numberofaverages)
		self.__sa.set_autoresolutionbandwidth('y')
#############################################################################################################
# get fundamental and 2nd and 3rd harmonic levels vs gate voltage Vgs sweep
# all frequencies in Hz
	def get_harmonic_fundamental(self,powerlevel=0.,referencelevel=-30.,harmonicnumber=None,Vds=None,Vgs_start=None,Vgs_stop=None,Vgs_step=None,maxdeltapower=None,gatecomp=None,draincomp=None):
		if  not (Vds==None or Vgs_start==None or Vgs_stop==None or Vgs_step==None) and Vgs_step!=0.: npts=int(abs((Vgs_stop-Vgs_start)/Vgs_step))+1
		else: npts=1

		self.Id=[]
		self.Ig=[]
		self.Vgs=[]
		self.Vds=Vds
		self.gatestatus=[]
		self.drainstatus=[]
		self.pfund=[]       # fundamental output RF power (dBm) referenced to the DUT output
		self.pharm2=[]       # 2nd harmonic output RF power (dBm) referenced to the DUT output
		self.pharm3=[]       # 3rd harmonic output RF power (dBm) referenced to the DUT output
		self.thirdorderprod=[]  # estimated third order product
		self.pharm3TOI=[]       # estimated third order output intercept point
		self.noisefloor_fund=[]     # noise floor (dBm) at the same bandwidth used to measure the fundamental
		self.noisefloor_2nd=[]  # noise floor (dBm) at the same bandwidth used to measure the 2nd harmonic
		self.noisefloor_3rd=[]  # noise floor (dBm) at the same bandwidth used to measure the 3rd harmonic

		if self.referencelevelfund==None:
			self.referencelevelfund=referencelevel          # if we haven't called this method, use the supplied referencelevel as a guess

		if Vds==None or Vgs_start==None or Vgs_stop==None or Vgs_step==None:
			Vgslist=[0.]
		else:
			Vgslist=np.linspace(start=Vgs_start,stop=Vgs_stop,num=npts)

		self.input_powerlevel_fundamental=powerlevel                                              # fundamental RF power level set at DUT input and referred to DUT input in dBm
		corrected_RFpowersetting= self.input_powerlevel_fundamental-self.calfactor_source_fund
		if self.__rf.set_power(corrected_RFpowersetting)=='unleveled':
			raise ValueError("ERROR! RF synthesizer unleveled")
		firstmeasurement=True
		for Vgs in Vgslist:
			if not (Vds==None or Vgs_start==None or Vgs_stop==None or Vgs_step==None):
				Id_,Ig_,drainstatus_,gatestatus_=self.__dc.fetbiason_topgate(Vds=Vds, Vgs=Vgs, gatecomp=gatecomp, draincomp=draincomp,timeiter=10,maxchangeId=0.01,maxtime=40.)				# bias device on
				self.Id.append(Id_)
				self.Ig.append(Ig_)
				self.gatestatus.append(gatestatus_)
				self.drainstatus.append(drainstatus_)
				self.Vgs.append(Vgs)
			else:
				self.Id.append(0)
				self.Ig.append(0)
				self.gatestatus.append('N')
				self.drainstatus.append('N')
				self.Vgs.append(0)
			RFpowerrawlast=-99999.
			self.referencelevelfund,self.fundamental_frequency,RFpowerraw=self.__sa.measure_peak_level_autoscale(referencelevel=self.referencelevelfund,frequency=self.fundamental_frequency,frequencyspan=spandfund,averages=1)    # measure RF power of the fundamental using the spectrum analyzer
			self.harmonic_frequency2=2.*self.fundamental_frequency # fine tune spectrum analyzer harmonic frequencies
			self.harmonic_frequency3=3.*self.fundamental_frequency
			i=0
			while abs(RFpowerraw-RFpowerrawlast)>maxdeltapower and i<maxitermeas:
				RFpowerrawlast=RFpowerraw
				self.referencelevelfund,self.fundamental_frequency,RFpowerraw=self.__sa.measure_peak_level_autoscale(referencelevel=self.referencelevelfund,frequency=self.fundamental_frequency,frequencyspan=spandfund,averages=1)    # measure RF power of the fundamental using the spectrum analyzer
				i+=1
			if i>=maxitermeas: print("WARNING! maximum number of fundamental output power readings exceeded")
			RFpowercorrected=RFpowerraw+self.calfactor_sa_fund
			self.pfund.append(RFpowercorrected)              # measured fundamental RF power in dBm
			print("from line 97 in harmonic_measurement.py: RFpower fundamental =",RFpowercorrected)
			if self.referencelevelharm2==None: self.referencelevelharm2=self.referencelevelfund-80.
			if self.referencelevelharm3==None: self.referencelevelharm3=self.referencelevelfund-80.
			self.__rf.off()
			f,s,fr,nspect=self.__sa.measure_spectrum(centfreq=self.fundamental_frequency, span=spandfund,returnspectrum=True)			# get raw measured noise floor
			self.__rf.on()
			noisefloor_sa=dBaverage(nspect)                  # get noise floor as measured directly at the spectrum analyzer without correction, averaged over all the spanned frequencies
			self.noisefloor_fund.append(noisefloor_sa+self.calfactor_sa_fund)       # noise floor as referenced to the DUT output and measured using the same resolution bandwidth as that used to measure the fundamental
			if harmonicnumber==2 or harmonicnumber==None:
				self.referencelevelharm2,self.harmonic_frequency2,RFpowerraw=self.__sa.measure_peak_level_autoscale(referencelevel=self.referencelevelharm2,frequency=self.harmonic_frequency2,frequencyspan=spandharm,averages=8)    # measure RF power of the harmonic using the spectrum analyzer
				RFpowercorrected=RFpowerraw+self.calfactor_sa_harm2
				#print("from line 106 in harmonic_measurement.py: RFpower 2nd harmonic =",RFpowercorrected)
				self.pharm2.append(RFpowercorrected)              # measured 2nd harmonic RF power in dBm
				self.__rf.off()
				f,s,fr,nspect=self.__sa.measure_spectrum(centfreq=self.harmonic_frequency2, span=spandharm,returnspectrum=True)			# get raw measured noise floor
				self.__rf.on()
				noisefloor_sa=dBaverage(nspect)                  # get noise floor as measured directly at the spectrum analyzer without correction, averaged over all the spanned frequencies
				self.noisefloor_2nd.append(noisefloor_sa+self.calfactor_sa_harm2)       # noise floor as referenced to the DUT output and measured using the same resolution bandwidth as that used to measure the 2nd harmonic
				print("from line 121 in harmonic_measurement.py the 2nd harmonic and 2nd harmonic noisefloor are ",RFpowercorrected,noisefloor_sa+self.calfactor_sa_harm2)
			if harmonicnumber==3 or harmonicnumber==None:
				self.referencelevelharm3,self.harmonic_frequency3,RFpowerraw=self.__sa.measure_peak_level_autoscale(referencelevel=self.referencelevelharm3,frequency=self.harmonic_frequency3,frequencyspan=spandharm,averages=8)    # measure RF power of the harmonic using the spectrum analyzer
				RFpowercorrected=RFpowerraw+self.calfactor_sa_harm3
				print("from line 114 in harmonic_measurement.py: RFpower 3rd harmonic =",RFpowercorrected)
				self.pharm3.append(RFpowercorrected)              # measured 3rd harmonic RF power in dBm
				self.__rf.off()
				f,s,fr,nspect=self.__sa.measure_spectrum(centfreq=self.harmonic_frequency3, span=spandharm,returnspectrum=True)			# get raw measured noise floor
				self.__rf.on()
				noisefloor_sa=dBaverage(nspect)                  # get noise floor as measured directly at the spectrum analyzer without correction, averaged over all the spanned frequencies
				self.noisefloor_3rd.append(noisefloor_sa+self.calfactor_sa_harm3)       # noise floor as referenced to the DUT output and measured using the same resolution bandwidth as that used to measure the 3rd harmonic
				self.thirdorderprod.append(self.pharm3[-1]+thirdorderfromthirdharm)
				self.pharm3TOI.append((self.pfund[-1]-self.thirdorderprod[-1])/2. + self.pfund[-1])         # estimate of 2-tone third order intercept from third harmonic
				print("from line 130 in harmonic_measurement.py the 3rd harmonic and 3rd harmonic noisefloor are ",RFpowercorrected,noisefloor_sa+self.calfactor_sa_harm3)
			if not (harmonicnumber==2 or harmonicnumber==3 or harmonicnumber==None): raise ValueError("ERROR! Invalid setting of harmonicnumber")
		self.__rf.off()
	########################################################################################################
	# methods to write data
	writefile_harmonicdistortion=X_writefile_harmonicdistortion