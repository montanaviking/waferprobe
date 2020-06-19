__author__ = 'PMarsh Carbonics'
from spectrum_analyzer import *
from rf_sythesizer import *
from writefile_measured import X_writefile_TOI
from utilities import *
import time

	# perform 3rd order intercept point measurement
	# Input parameters
	# sa is the spectrum analyzer handle
	# rflow is the synthesizer handle of the synthesizer tuned to the lower of the two-tone frequencies
	# saatten is the spectrum analyzer's attanuation setting - must be 0dB, 5dB, 10dB,...
	# rfhigh is synthesizer handle of the synthesizer tuned to the lower of the two-tone frequencies
	# plevelstart is the initial power level setting of the synthesizers' output levels
	# plevelmax is the maximum allowed power level setting of the sythesizers' outpout levels
	# pleveldel is the stepsize of the two-tone levels to determine the TOI
	# centfreq is the frequency point midway between the two tones
	# deltafreq is the frequency separation between the two tones
	# fractlinfit is the fraction of plevelmax-plevelstart that we fit the line to find the TOI points
	# sacalfactor is the dB difference between the power meter measured power at the spectrum analyzer input and that shown on the spectrum analyzer
	# sourcecalfactor is the dB difference between the power meter measured power and that set on the rf synthesizers
	# i.e. power meter power = ca
class IP3(object):
	def __init__(self,rm,saatten,navg,plevelstart,plevelmax,pleveldel,centfreq,deltafreq,sacalfactor,sourcecalfactor,sysTOI):
		try: self.__sa=SpectrumAnalyzer(rm)
		except: raise ValueError("ERROR! No spectrum analyzer found!")
		try: self.__rflow=Synthesizer(rm,"A")
		except: raise ValueError("ERROR! No lower frequency RF source found for two-tone!")
		try: self.__rfhigh=Synthesizer(rm,"B")
		except: raise ValueError("ERROR! No upper frequency RF source found for two-tone!")
		#self.__sa=sa
		#self.__rfhigh=rfhigh                # handle to control the upper-frequency RF source
		#self.__rflow=rflow                  # handle to control the lower-frequency RF source
		self.__saatten=saatten
		self.__navg=navg
		self.__plevelstart=plevelstart
		self.__plevelmax=plevelmax
		self.__pleveldel=pleveldel
		self.__centfreq=centfreq
		self.__deltafreq=deltafreq
		self.__sacalfactor=sacalfactor
		self.__sourcecalfactor=sourcecalfactor
		self.__sysTOI=sysTOI                      # system third order intercept point


	#########################################################################################################################
	# fractlinfit is the fraction of the input two-tone power range to use to linear fit the distortion product power vs input power
	# in order to find the third order intercept point
	def measureTOI(self,fractlinfit):

		plevelstart = self.__plevelstart-self.__sourcecalfactor
		plevelmax=self.__plevelmax-self.__sourcecalfactor

		flow = self.__centfreq-self.__deltafreq/2.           # lower fundamental frequency of the two-tone
		fhigh = self.__centfreq+self.__deltafreq/2.          # upper fundamental frequency of the two-tone
		spanfund = 100.E3                      # measurement span about the fundamentals
		spand=10.E3                             # measurement span about the distortion products
		resbwfund = 1000.                       # resolution bandwidth used to measure fundamental two-tone components
		# turn off synthesizers to measure noise floor
		self.__rflow.off()
		self.__rfhigh.off()
		#return()    #debug
		self.__sa.set_attenuation(self.__saatten)                      # set attenuation level of spectrum analyzer
		self.__sa.set_numberaverages(self.__navg)                   # set number of averages
		# first measure noise floor for lower distortion product - expected to be the same as for upper frequency product as well
		# decrease resolution bandwidth by one increment for distortion product measurements

		f,p=self.__sa.measure_spectrum(flow-self.__deltafreq,spand,'nospectrum')
		self.__sa.set_autoresolutionbandwidth('yes')
		self.__resbwdistortion=self.__sa.decrease_resolutionbandwidth()
		f,p=self.__sa.measure_spectrum(flow-self.__deltafreq,spand,'nospectrum')

		self.__noisefloor=np.average(p)                    # get noise floor
		noisefloorlin = pow(10.,self.__noisefloor/10.)     # noisefloor in mW
		#bad here

		# set two-tone synthesizer frequencies
		self.__rflow.set_frequency(self.__centfreq-self.__deltafreq/2.)  # set lower frequency of two-tone
		self.__rfhigh.set_frequency(self.__centfreq+self.__deltafreq/2.) # set upper frequency of two-tone
		self.__rflow.set_power(plevelmax)
		self.__rfhigh.set_power(plevelmax)
		#bad here
		while self.__rflow.set_power(plevelmax)=='unleveled' or self.__rfhigh.set_power(plevelmax)=='unleveled':
			# power level setting is beyond at least one of the synthesizer's capability so reduce the maximum requested power
			#plevelmax=plevelmax-self.__pleveldel
			print ("Warning: maximum requested synthesizer power beyond capability so reducing maximum power set at synthesizers to", plevelmax)
			plevelmax=plevelmax-1.1*self.__pleveldel
		print ("plevelmax = ",plevelmax)
		print ("sourcecalfactor", self.__sourcecalfactor)
		print("plevelmax setting actual",self.__plevelmax)

		plevel = plevelstart
		self.__ptt = []                                    # two-tone power level array
		self.__pdl = []                                    # power level array of the lower third order distortion product
		self.__pdh = []                                    # power level array of the upper third order distortion product
		self.__sys = []                                   # third order product due to system IP3
		delpowm=0.
		while plevel <= plevelmax:
			print("plevel setting in loop ",plevel)
			#print "set res 1"
			reflevel=10.*int((plevel+self.__sourcecalfactor)/10.)     # set spectrum analyzer reference level to nearest increment of 10dB
			self.__sa.set_referencelevel(reflevel)                 # set reference level of spectrum analyzer
			self.__sa.set_resolutionbandwidth(resbwfund)       # set resolution bandwidth to lock to span for fundamental measurements
			#print "set res 2"
			pwrhigh = plevel-delpowm                # attempt to correct for errors on two tone signal levels to attempt to make both of the two tone have the same levels
			self.__rfhigh.set_power(pwrhigh)
			if self.__rfhigh.set_power(pwrhigh)!='ok': raise ValueError('ERROR high 1 power set too high on upper-frequency synthesizer')
			self.__rflow.set_power(plevel)
			if self.__rflow.set_power(plevel)!='ok': raise ValueError('ERROR low power set too high on lower-frequency synthesizer')

			#print "set res 2b"
			# iterate synthesizer power levels to produce the same level in both of the two-tones as measured by the spectrum analyzer
			while True:
				#print "set res 3" #debug
				flowm,plowm=self.__sa.measure_spectrum(flow,spanfund,'nospectrum')     #measure lower fundamental of two tone input
				fhighm,phighm=self.__sa.measure_spectrum(fhigh,spanfund,'nospectrum')  #measure upper fundamental of two tone input
				#print "set res 5" #debug
				delpowm = phighm-plowm
				if abs(delpowm)<0.1: break                       # iterate power adjustment until power difference between fundamentals is acceptably low
				pwrhigh=self.__rfhigh.get_power()-delpowm               # set power to even out fundamental power levels
				self.__rfhigh.set_power(pwrhigh)
				if self.__rfhigh.set_power(pwrhigh)!='ok': raise ValueError('ERROR high 2 power set too high on upper-frequency synthesizer')

			pfundaverage = dBaverage(self.__sacalfactor+plowm,self.__sacalfactor+phighm) # average of the two-tone lower and upper frequency powers
			self.__ptt.append(pfundaverage)                                              #measured fundamental power level
			self.__sa.set_resolutionbandwidth(self.__resbwdistortion)                                 # set the resolution bandwidth to measure distortion product
			reflevel=90.+10.*int(self.__noisefloor/10.)     # set spectrum analyzer reference level to nearest increment of 10dB
			self.__sa.set_referencelevel(reflevel)                 # set reference level of spectrum analyzer
			#print "set res 6" #debug
			f,p=self.__sa.measure_spectrum(flowm-self.__deltafreq,spand,'nospectrum')       # measure lower frequency 3rd order product power level
			p = self.__sacalfactor+10.*np.log10(abs(pow(10.,p/10.)-noisefloorlin))      # calibrate to power meter readings and subtract out noise floor
			print ("lower =",p) #debug
			self.__pdl.append(p)
			self.__sa.set_resolutionbandwidth(self.__resbwdistortion)                                 # set the resolution bandwidth to measure distortion product
			f,p=self.__sa.measure_spectrum(fhighm+self.__deltafreq,spand,'nospectrum')       # measure upper frequency 3rd order product power level
			#print "high side attenuation =", sa.get_attenuation() #debug
			#print "set res 8" #debug
			p = self.__sacalfactor+10.*np.log10(abs(pow(10.,p/10.)-noisefloorlin))      # calibrate to power meter readings and subtract out noise floor

			print ("upper =",p) #debug
			self.__pdh.append(p)
			self.__sys.append(3.*pfundaverage-2.*self.__sysTOI)     # find third order product due to TOI of system

			plevel += self.__pleveldel                     # increment power level of the fundamental two-tones
			self.__rflow.vclear()
			self.__rfhigh.vclear()
		self.__rflow.off()
		self.__rfhigh.off()

		# find both 3rd order intercept points, corrected power levels at the spectrum analyzer input, and corrected linear fits
		# first get only TOIs
		x1,y1,ml,bl,rl = linfitbest(self.__ptt,self.__pdl,self.__ptt[0],max(self.__ptt),fractlinfit)  # distortion product linear fit for lower distortion product to find TOI
		x2,y2,mh,bh,rh = linfitbest(self.__ptt,self.__pdh,self.__ptt[0],max(self.__ptt),fractlinfit)  # distortion product linear fit for upper distortion product to find TOI
		# find TOIs
		self.__TOIl=bl/(1.-ml) # third order intercept point as determined from lower frequency 3rd order product
		self.__TOIh=bh/(1.-mh) # third order intercept point as determined from upper frequency 3rd order product
		# now find linear fits to distortion products vs input fundamental two-tone powers
		self.__fitlx,self.__fitly,ml,bl,rl=linfitbest(self.__ptt,self.__pdl,self.__ptt[0],max([self.__TOIl,self.__TOIh])+2.,fractlinfit) # distortion product linear fit for lower distortion product to return extrapolated linear fit of TOI products
		self.__fithx,self.__fithy,mh,bh,rh=linfitbest(self.__ptt,self.__pdh,self.__ptt[0],max([self.__TOIl,self.__TOIh])+2.,fractlinfit) # distortion product linear fit for upper distortion product to return extrapolated linear fit of TOI products
		self.__r = max([rl,rh])    # find worst-case fitting "goodness" parameter
		return self.__TOIl,self.__TOIh,self.__ptt,self.__pdl,self.__pdh,self.__noisefloor,self.__fitlx,self.__fitly,self.__fithx,self.__fithy,self.__r
	####################################################################################################################
	# write TOI data to file
	writefile_TOI=X_writefile_TOI
