__author__ = 'PMarsh Carbonics'
import visa
import time
import  numpy as np
from utilities import *
settlingtime=0.5
#minimumspan=100.        # minimum spectrum analyzer span settings
class SpectrumAnalyzer:
	def __init__(self,rm=None):
		try:
			self.__sa = rm.open_resource('TCPIP0::192.168.1.15::inst0::INSTR')
		except:
			raise ValueError("No spectrum analyzer found")
		self.__sa.timeout=1000000.
		self.__sa.query_delay=0.5            # set up query delay to prevent errors
		#self.__sa.lock(1000000)
		#message=self.__sa.query('*IDN?')
		print (self.__sa.query('*IDN?'))
		self.__sa.write(':SYST:PRES')               # reset system to default
		self.__sa.write(':INIT:CONT ON')         # continuous sweep
		self.__sa.write(':UNIT:POW DBM')        # set startup units to dBm
		self.__sa.write(':FORM:READ:DATA: ASC') # set output data format to be ASCII
		self.set_autoresolutionbandwidth('yes')     # set resolution bandwidth to be coupled to the frequency span
		self.set_autovideobandwidth('yes')          # set video bandwidth to be coupled to the resolution bandwidth
	def __del__(self):
		self.__sa.close()
########################################################################################################################
	# sets the start frequency, stop frequency in GHz
	def set_startstopfrequency(self,fstart=None,fstop=None,units='GHz'):
		if 'Hz' not in units and 'KHz' not in units and 'MHz' not in units and 'GHz' not in units:
			raise ValueError("units not correct")
		if fstart<0. or fstop<0. or fstart>=fstop:
			raise ValueError('frequency values are illegal')
		self.__sa.write(':SENS:FREQ:START '+str(fstart)+' '+units)
		self.__sa.write(':SENS:FREQ:STOP '+str(fstop)+' '+units)
		return int(self.__sa.query(':SENS:FREQ:START?')), int(self.__sa.query(':SENS:FREQ:STOP?'))  # frequencies are in H
	# ####################################################################################################################
	# # sets the frequency center and span
	def set_centerspanfrequency(self,fcenter=None,fspan=None,units="Hz"):
		if 'Hz' not in units and 'KHz' not in units and 'MHz' not in units and 'GHz' not in units:
			raise ValueError("units not correct")
		if (units=='Hz' and fcenter-fspan/2.<10E3) or (units=='KHz' and fcenter-fspan/2.<10) or (units=='MHz' and fcenter-fspan/2.<0.01) or (units=='GHz' and fcenter-fspan/2.<0.00001):
			raise ValueError('frequency values are illegal')
		self.__sa.write(':SENS:FREQ:CENT '+str(fcenter)+' '+units)
		self.__sa.write(':SENS:FREQ:SPAN '+str(fspan)+' '+units)
		return int(self.__sa.query(':SENS:FREQ:START?')), self.__sa.write(':SENS:BAND:RES:AUTO OFF')  # turn off auto resolution bandwidthint(self.__sa.query(':SENS:FREQ:STOP?'))  # frequencies are in Hz
	####################################################################################################################
	# get start, stop, and step frequencies in Hz
	def get_startstopfrequency(self):
		return int(self.__sa.query(':SENS:FREQ:START?')), int(self.__sa.query(':SENS:FREQ:STOP?'))  # frequencies are in Hz
	####################################################################################################################
	# get center frequency
	def get_centerfrequency(self):
		return float(self.__sa.query(':SENS:FREQ:CENT?'))    # frequency is in Hz
	####################################################################################################################
	# set resolution bandwidth
	# returns actual resolution bandwidth that is set
	# note that resolution bandwidth may be set only to discrete values e.g. 1,3,10,30,100,300Hz ...1,3,10KHz...etc..
	# and the resolution bandwidth settings are always rounded up to the next available discrete value e.g.
	# a setting of 1.1KHz gives an actual value of 3KHz for the resolution bandwidth
	# this function returns the actual effective resolution bandwidth setting
	def set_resolutionbandwidth(self,resolutionbandwidth=None,units='hz'):
		units=units.lower()
		if 'hz' not in units and 'khz' not in units and 'mhz' not in units:
			raise ValueError("units not correct")
		self.__sa.write(':SENS:BAND:RES:AUTO OFF')  # turn off auto resolution bandwidth
		self.__sa.write(':SENS:BAND:RES '+str(resolutionbandwidth)+' '+units)
		return int(self.__sa.query(':SENS:BAND:RES?'))            # frequency is always returned in Hz
	####################################################################################################################
	# increase resolution bandwidth by one increment
	# returns actual resolution bandwidth that is set
	# note that resolution bandwidth may be set only to discrete values e.g. 1,3,10,30,100,300Hz ...1,3,10KHz...etc..
	# and the resolution bandwidth settings are always rounded up to the next available discrete value e.g.
	# a setting of 1.1KHz gives an actual value of 3KHz for the resolution bandwidth
	# this function returns the actual effective resolution bandwidth setting
	def increase_resolutionbandwidth(self):
		rb = self.get_resolutionbandwidth()
		rb *=2.8
		self.__sa.write(':SENS:BAND:RES:AUTO OFF')  # turn off auto resolution bandwidth
		self.__sa.write(':SENS:BAND:RES '+str(rb))
		return int(self.__sa.query(':SENS:BAND:RES?'))            # frequency is always returned in Hz
	####################################################################################################################
	# decrease resolution bandwidth by one increment
	# returns actual resolution bandwidth that is set
	# note that resolution bandwidth may be set only to discrete values e.g. 1,3,10,30,100,300Hz ...1,3,10KHz...etc..
	# and the resolution bandwidth settings are always rounded up to the next available discrete value e.g.
	# a setting of 1.1KHz gives an actual value of 3KHz for the resolution bandwidth
	# this function returns the actual effective resolution bandwidth setting
	def decrease_resolutionbandwidth(self):
		rb = self.get_resolutionbandwidth()
		rb = rb/3.5
		self.__sa.write(':SENS:BAND:RES:AUTO OFF')  # turn off auto resolution bandwidth
		self.__sa.write(':SENS:BAND:RES '+str(rb))
		return int(self.__sa.query(':SENS:BAND:RES?'))            # frequency is always returned in Hz
	####################################################################################################################
	# get resolution bandwidth
	# returns actual resolution bandwidth that is set in Hz
	def get_resolutionbandwidth(self):
		return int(self.__sa.query(':SENS:BAND:RES?'))            # frequency is always returned in Hz
	####################################################################################################################
	# set video bandwidth
	# returns actual video bandwidth that is set
	# note that the video bandwidth may be set only to discrete values e.g. 1,3,10,30,100,300Hz ...1,3,10KHz...etc..
	# and the video bandwidth settings are always rounded up to the next available discrete value e.g.
	# a setting of 1.1KHz gives an actual value of 3KHz for the video bandwidth
	# this function returns the actual effective video bandwidth setting
	def set_videobandwidth(self,videobandwidth=None,units="Hz"):
		if 'hz' not in units.lower() and 'khz' not in units.lower() and 'mhz' not in units.lower(): # case insensitive compare
			raise ValueError("units not correct")
		self.__sa.write(':SENS:BAND:VID:AUTO OFF')  # turn off auto video bandwidth
		self.__sa.write(':SENS:BAND:VID '+str(videobandwidth)+' '+units)
		return int(self.__sa.query(':SENS:BAND:VID?'))            # frequency is always returned in Hz
	####################################################################################################################
	# get video bandwidth
	# returns actual video bandwidth that is set
	def get_videobandwidth(self):
		return int(self.__sa.query(':SENS:BAND:VID?'))            # frequency is always returned in Hz
	####################################################################################################################
	# set the number of traces to average to obtain the spectrum analyzer data
	# no return value
	def set_numberaverages(self,*args):
		if len(args)==1:
			if args[0]>1:
				self.__sa.write(':SENS:AVER:TYPE SCAL')     # default is to average data
			if args[0]==0 or args[0]==1:
				self.__sa.write(':SENS:AVER:TYPE NONE')      # 0 averages means averaging turned off (should be same as 1)
		elif len(args)==2:
			tp=args[1]
			if 'none' not in tp.lower and 'average' not in tp.lower() and 'minimum' not in tp.lower() and 'maximum' not in tp.lower(): # case insensitive compare
				raise ValueError('illegal type of average')
			if 'none'== tp.lower(): tp='NONE'       # averaging turned off
			if 'average'== tp.lower(): tp='SCAL'    # navg traces are averaged
			if 'minimum'== tp.lower(): tp='MIN'     # find minimum of data
			if 'maximum'== tp.lower(): tp='MAX'     # find maximum of data
			self.__sa.write(':SENS:AVER:TYPE '+tp)
		else:   raise ValueError("ERROR! wrong number of parameters!")
		noavg=args[0]
		if args[0]>1:
			self.__sa.write(':SENS:AVER:COUN '+str(noavg))    # set number of averages
		#print "number of averages set is", self.__sa.query(":SENS:AVER:COUN?")      # debug
	####################################################################################################################
	# turn off continuous sweep to use for automated measurements
	def set_sweepoff(self):
		#print "sweep off" # debug
		time.sleep(settlingtime)
		self.__sa.write(':ABORT')              # this is apparently needed to prevent jamming at the next query
		time.sleep(settlingtime)
		self.__sa.write(':INIT:CONT OFF')
		time.sleep(settlingtime)
		self.__sa.write(':SENS:AVER:TYPE NONE')
		time.sleep(settlingtime)
		#self.__sa.write(':INIT:CONT OFF')
		self.__sa.write(':SENS:AVER:TYPE SCAL')
		time.sleep(settlingtime)
		#self.__sa.write(':ABORT')              # this is apparently needed to prevent jamming at the next query
		#print "sweep off done" # debug
		#time.sleep(1.)
		#self.__poll()
		#print "_poll sweepoff" # debug
		#return self.__sa.query(':INIT:CONT?')   # appears to lock up system
	####################################################################################################################
	# turn on continuous sweep to use for manual measurements
	def set_sweepon(self):
		time.sleep(settlingtime)
		self.__sa.write(':ABORT')              # this might be needed to improve reliability (not sure -did run without this)
		time.sleep(settlingtime)
		self.__sa.write(':INIT:CONT ON')
		time.sleep(settlingtime)
		return self.__sa.query(':INIT:CONT?')
	####################################################################################################################
	# Set RF input attenuation
	# RF attenuation must be set to obtain the best trade-off between the noise floor and the spectrum analyzer
	# internally-generated distortion
	# attenuation is given in dB
	def set_attenuation(self,att):
		self.__sa.write(':SENS:POW:RF:ATT '+str(att))
		return self.__sa.query(':SENS:POW:RF:ATT?')
		####################################################################################################################
	# Get RF input attenuation
	# attenuation is given in dB
	def get_attenuation(self):
		return self.__sa.query(':SENS:POW:RF:ATT?')
	####################################################################################################################
	# set the video bandwidth to be linked or not linked to the resolution bandwidth
	def set_autovideobandwidth(self,yn):
		if yn.lower()=='yes' or yn.lower()=='y':
			self.__sa.write(":SENS:BAND:VID:AUTO ON")
		elif yn.lower()=='no' or yn.lower()=='n':
			self.__sa.write(":SENS:BAND:VID:AUTO OFF")
		#self.__poll()
		return int(self.__sa.query(":SENS:BAND:VID:AUTO?"))
	####################################################################################################################
	# set the resolution bandwidth to be linked or not linked to the frequency span
	def set_autoresolutionbandwidth(self,yn):
		if yn.lower()=='yes' or yn.lower()=='y':
			self.__sa.write(":SENS:BAND:RES:AUTO ON")
		elif yn.lower()=='no' or yn.lower()=='n':
			self.__sa.write(":SENS:BAND:RES:AUTO OFF")
		return int(self.__sa.query(":SENS:BAND:RES:AUTO?"))
	####################################################################################################################
	# trigger delay is a percentage (0-100%) of the sweep time
	def set_triggerdelay(self,delay=0.):
		if delay<-100 or delay>100: raise ValueError("Invalid trigger delay percentage, must be between -100 and 100")
		self.__sa.write(":TRIG:VID:POS "+str(float(delay)))
		ret=self.__sa.query(":TRIG:VID:POS?")
		return float(ret)
	####################################################################################################################
	# measure the spectrum
	# centfreq is the center frequency in Hz
	# span is the frequency span in Hz
	def measure_spectrum(self,centfreq=None,span=None,returnspectrum=True,resolutionbandwidth=None,videobandwidth=None,numberofaverages=1,attenuation=10,preamp=False,referencelevel=None):
		if span==None: raise ValueError("ERROR! did not specify valid span")
		if span==0: span=videobandwidth            # set minimum span for cases where we are testing a narrow frequency range
		#if span<0.5*resolutionbandwidth: span=0.5*resolutionbandwidth # set minimum span for cases where we are testing a narrow frequency range
		if centfreq==None: raise ValueError("ERROR! did not specify valid center frequency")
		if referencelevel==None: raise ValueError("ERROR! did not specify valid reference level setting")
		# set internal triggering
		self.__sa.write(":ABORT")
		time.sleep(settlingtime)
		self.__sa.write(":INIT:CONT OFF")
		time.sleep(settlingtime)
		self.__sa.write(":TRIG:SOUR IMM")       # set internal trigger.
		time.sleep(settlingtime)
		self.set_sweepoff()                 # freezes intermittently here
		time.sleep(settlingtime)
		self.set_referencelevel(referencelevel)
		self.set_numberaverages(numberofaverages)    # set number of averages
		if resolutionbandwidth==None or videobandwidth==None:   # then set auto resolution bandwidth and video bandwidth
			self.set_autoresolutionbandwidth('y')
			self.set_autovideobandwidth('y')
		else:
			actualvideobandwidth=self.set_videobandwidth(videobandwidth)
			actualresolutionbandwidth=self.set_resolutionbandwidth(resolutionbandwidth)
		self.set_startstopfrequency(centfreq-span/2.,centfreq+span/2.,'Hz')
		#print "at end of set frequency"
		self.__sa.write(':CONF:SPEC:SING')
		time.sleep(settlingtime)
		self.__sa.write(':INIT') # this is unreliable
		#self.__sa.write(':ABORT;:INIT') # this is unreliable but had worked in past
		time.sleep(4)
		#print (" line 199 in spectrum_analyzer.py before poll") # debug
		if preamp:
			self.set_attenuation(0)                                 # set no attenuation when using preamp
			self.__sa.write(":SENSE:POWER:RF:GAIN:STATE ON")       # turn on preamp. Useful for noise figure measurements
		else:
			self.__sa.write(":SENSE:POWER:RF:GAIN:STATE OFF")                 # turn off preamp
			self.set_attenuation(attenuation)
		self.__poll()
		#print (" line 201 in spectrum_analyzer.py after poll") # debug
		rawpdata=(self.__sa.query(':TRAC:DATA?')).strip(',').strip()
		#print rawpdata  #debug
		#print "preamble ",self.__sa.query(':TRAC:PRE?')
		nocharfront=int(rawpdata[1])            # number of characters for the data size (in bytes) indicator
		rawpdata = rawpdata[2+nocharfront:]     # remove the data size indicator from the front of the data
		rawpdata = rawpdata.split(',')          # convert spectrum analyzer data to an ASCII list of data
		pdata = [float(d.strip()) for d in rawpdata]        # convert spectrum power data to floating point
		# get frequency array associated with the spectrum power data
		freq = np.linspace(self.get_startstopfrequency()[0],self.get_startstopfrequency()[1],len(pdata))
		# get maximum signal level and its frequency (dBm and Hz)
		maxsig=max(pdata)
		maxfreq=freq[pdata.index(max(pdata))]
		self.set_sweepon()                      # leave the sweep free-running
		if returnspectrum: return maxfreq,maxsig,freq,pdata # freq is in Hz
		else: return maxfreq,maxsig               # return only the maximum signal level (dBm) and its frequency (Hz)
	####################################################################################################################
	# measure the noise floor - assumes that there are no discrete signals present!
	# centfreq is the center frequency in Hz
	# span is the frequency span in Hz
	def measure_noisefloor(self,centfreq=None,span=None,nospec=None):
		self.set_sweepoff()
		self.set_startstopfrequency(centfreq-span/2.,centfreq+span/2.,'Hz')
		self.__sa.write(':CONF:SPEC:SING')
		self.__sa.write(':ABORT;:INIT')
		self.__poll()
		rawpdata=(self.__sa.query(':TRAC:DATA?')).strip(',').strip()
		#print "preamble ",self.__sa.query(':TRAC:PRE?')
		nocharfront=int(rawpdata[1])            # number of characters for the data size (in bytes) indicator
		rawpdata = rawpdata[2+nocharfront:]     # remove the data size indicator from the front of the data
		rawpdata = rawpdata.split(',')          # convert spectrum analyzer data to an ASCII list of data
		pdata = [float(d.strip()) for d in rawpdata]        # convert spectrum power data to floating point
		# get frequency array associated with the spectrum power data
		freq = np.linspace(self.get_startstopfrequency()[0],self.get_startstopfrequency()[1],len(pdata))
		# get maximum signal level and its frequency (dBm and Hz)
		maxsig=max(pdata)
		#maxfreq=freq[pdata.index(max(pdata))]
		nofreq = len(pdata) # number of frequency and data points
		noisefloor=0.
		for d in pdata: noisefloor += pow(10.,d/10.)
		noisefloor = noisefloor/float(nofreq)
		noisefloor = 10.*np.log10(noisefloor)   # average noisefloor in dBm
		self.set_sweepon()                      # leave the sweep free-running
		if nospec.lower()=='spectrum':
			return noisefloor,maxsig,freq,pdata
		else:
			return noisefloor,maxsig   # return the maximum signal level (dBm) and its frequency (Hz), and the maximum signal level (to check for discrete frequency signal contamination)
	####################################################################################################################
	# adjust reference level so that the input signal is not saturating the spectrum analyzer's input A/D convertor
	# frequency span and frequency are in Hz
	# referenclevel is the first guess at the reference level in dBm
	# measurement done in frequency domain
	def measure_peak_level_autoscale(self,referencelevel=None,frequency=None,frequencyspan=None,resolutionbandwidth=None,averages=4,measurenoise=False,videobandwidth=None,attenuation=10):
		maxrefleveladjusttries=10
		if frequencyspan==0: frequencyspan=2*videobandwidth
		reftries=0
		reflevelOK=False
		while reftries<maxrefleveladjusttries and not reflevelOK:      #loop to find reference level which doesn't saturate spectrum analyzer input
			reflevelOK=True
			try: measuredfrequency,measuredpowerlevel=self.measure_spectrum(referencelevel=referencelevel,resolutionbandwidth=resolutionbandwidth,videobandwidth=videobandwidth,numberofaverages=averages,centfreq=frequency,span=frequencyspan,returnspectrum=False,attenuation=attenuation)     #measure signal level
			except:
				reflevelOK=False
				referencelevel+=30.         # increase reference level by 30dB to attempt to get out of saturation
				#self.set_referencelevel(referencelevel)
			reftries+=1
			print("from line 314 in spectrum_analyzer.py reftries=",reftries)
		if reftries>=maxrefleveladjusttries:
			print("from line 316 in spectrum_analyzer.py WARNING number of retries exceeded")
		reftries=0
		actualresolutionbandwidth=self.set_resolutionbandwidth(resolutionbandwidth=resolutionbandwidth)
		frequencyspan=min(frequencyspan,100*actualresolutionbandwidth)

		if not measurenoise:
			frequencyaccurate=False                 # flag for whether frequency of peak is accurate enough. Ignore if measuring noise only
			if resolutionbandwidth!=None:
				self.set_autoresolutionbandwidth('n')
				self.set_videobandwidth(10)
				measuredfrequencylast=0                 #ensure at least one iteration to get correct center frequency on spectrum analyzer
				reftries=0
		else: frequencyaccurate=True                                # do not measure frequency accuracy if measuring noise
		while (measuredpowerlevel>referencelevel or not reflevelOK or not frequencyaccurate  and reftries<maxrefleveladjusttries):
			reflevelOK=True
			if not measurenoise: frequencyaccurate=abs(measuredfrequency-measuredfrequencylast)>actualresolutionbandwidth/20        # determine frequency accuracy ONLY if not measuring noise spectrum
			else: frequencyaccurate=True
			if measuredpowerlevel>referencelevel: referencelevel+=20.
			self.set_referencelevel(referencelevel)
			measuredfrequencylast=measuredfrequency
			try: measuredfrequency,measuredpowerlevel=self.measure_spectrum(referencelevel=referencelevel,resolutionbandwidth=resolutionbandwidth,videobandwidth=videobandwidth,numberofaverages=averages,centfreq=frequency,span=frequencyspan,returnspectrum=False,attenuation=attenuation)     #measure signal level
			except:
				reflevelOK=False
				referencelevel+=30.         # increase reference level by 30dB to attempt to get out of saturation
				self.set_referencelevel(referencelevel)
			frequencyspan=min(frequencyspan,20*actualresolutionbandwidth)
			reftries+=1
			print("from line 341 in spectrum_analyzer.py reftries=",reftries)
		if reftries>=maxrefleveladjusttries:
			print("from line 343 in spectrum_analyzer.py WARNING number of retries exceeded")
		return referencelevel,measuredfrequency,measuredpowerlevel
	####################################################################################################################
	# set display reference level in dBm
	def set_referencelevel(self,rlevel):
		if rlevel>30.:rlevel=30.
		self.__sa.write(":DISP:WIND:TRAC:Y:SCAL:RLEV "+str(rlevel))
	def get_referencelevel(self):
		return float(self.__sa.query(":DISP:WIND:TRAC:Y:SCAL:RLEV?"))
	####################################################################################################################
	# measure amplitude waveform at zero frequency span
	#
	# uses
	# assumes that the reference level guess has been properly set
	# assumes that the waveform generator is running and triggering the spectrum analyzer
	# video bandwidth in Hz, resolution bandwidth in Hz, sweep time in seconds which is the total timespan swept
	# outputtype controls whether output is in Watts or dBm vs time in sec.
	# frequency in Hz, bandwidths in Hz
	# if preampon == True, then turn on the spectrum analyzer's preamp. This is primarily used to measure noise
	# pout is output spectrum in dBm
	def measure_amplitude_waveform(self,frequency=None, sweeptime=None,resolutionbandwidth=None,videobandwidth=None,numberofaverages=1,attenuation=None,referencelevelguess=-70,outputtype='dBm',numberofaverages_reflevelsetting=1,triggerdelay=-2.,preampon=False,measurenoise=False,autoscalespectrumanalyzer=True):
		if attenuation!=None: self.set_attenuation(attenuation)
		else: attenuation=self.get_attenuation()
		if frequency==None: raise ValueError("ERROR! no center frequency provided")
		# set narrow bandwidth to autoscale
		frequencyspan=max(5*resolutionbandwidth,10E3)
		if autoscalespectrumanalyzer:
			referencelevelsetting,measuredfrequency,measuredpower=self.measure_peak_level_autoscale(referencelevel=referencelevelguess,frequency=frequency,frequencyspan=frequencyspan,resolutionbandwidth=resolutionbandwidth,videobandwidth=resolutionbandwidth,averages=numberofaverages_reflevelsetting,measurenoise=measurenoise,attenuation=attenuation)
			if measuredpower+15.>referencelevelsetting: self.set_referencelevel(referencelevelsetting+10.)
			if frequency!=None: self.set_centerspanfrequency(fcenter=measuredfrequency,fspan=0)         # set center frequency, then set span to 0 to measure power at the center frequency vs time
		else:
			self.set_referencelevel(referencelevelguess)
			if frequency!=None: self.set_centerspanfrequency(fcenter=frequency,fspan=0)         # set center frequency, then set span to 0 to measure power at the center frequency vs time
		self.set_sweepoff()
		triggerdelayactual=self.set_triggerdelay(triggerdelay)
		if resolutionbandwidth!=None: actualresolutionbandwidth=self.set_resolutionbandwidth(resolutionbandwidth)
		else: raise ValueError("ERROR! no resolution bandwidth specified")
		if videobandwidth!=None: actualvideobandwidth=self.set_videobandwidth(videobandwidth)
		else: raise ValueError("ERROR! no video bandwidth specified")
		# set averaging for data acquistion
		if numberofaverages>1 and numberofaverages!=None: self.set_numberaverages(numberofaverages)    # set number of averages
		else: self.set_numberaverages(1)                     # turn averaging off
		if sweeptime==None: raise ValueError("ERROR! must specify sweeptime")
		self.__sa.write(":SENS:SWE:TIME "+formatnum(sweeptime,precision=8,nonexponential=True))
		time.sleep(settlingtime)
		self.__sa.write(":ABORT")
		time.sleep(settlingtime)
		self.__sa.write(":INIT:CONT OFF")
		time.sleep(settlingtime)
		self.__sa.write(":TRIG:SOUR EXT")       # set external trigger. This sychronizes the spectrum analyzer's time sweep with that of the voltage (gate or drain) bias sweep
		time.sleep(settlingtime)
		if preampon: self.__sa.write(":SENSE:POWER:RF:GAIN:STATE ON")       # turn on preamp. Useful for noise figure measurements
		else: self.__sa.write(":SENSE:POWER:RF:GAIN:STATE OFF")
		time.sleep(settlingtime)
		#print("from line 367 spectrum_analyzer.py before init")
		self.__sa.write(":INIT")
		#print("from line 369 spectrum_analyzer.py before poll after init")
		self.__poll()
		#print("from line 371 spectrum_analyzer.py after poll")
		rawpdata=(self.__sa.query(':TRAC:DATA?')).strip(',').strip()
		nocharfront=int(rawpdata[1])            # number of characters for the data size (in bytes) indicator
		rawpdata = rawpdata[2+nocharfront:]     # remove the data size indicator from the front of the data
		rawpdata = rawpdata.split(',')          # convert spectrum analyzer data to an ASCII list of data
		pdata = [float(d.strip()) for d in rawpdata]        # convert spectrum power data to floating point
		sweeptimeactual=float(self.__sa.query(":SENS:SWE:TIME?"))      # get actual sweep time in sec
		# get frequency array associated with the spectrum power data
		timestamps = np.linspace(0.,sweeptimeactual,len(pdata))
		if outputtype.lower()=='watt' or outputtype.lower()=='watts': pout=[pow(10.,(p-30.)/10.) for p in pdata ]
		elif outputtype.lower()=='dbm': pout=[p for p in pdata ]
		elif outputtype.lower()=='mw':  pout=[pow(10.,p/10.) for p in pdata ]       # output power in milliwatts
		else: raise ValueError("ERROR! must specify valid power type, mW, Watts or dBm")
		if autoscalespectrumanalyzer: return(timestamps,pout,measuredfrequency,actualresolutionbandwidth,actualvideobandwidth)
		else: return(timestamps,pout,frequency,actualresolutionbandwidth,actualvideobandwidth)
	####################################################################################################################
	# polling loop for spectrum analyzer
	def __poll(self):
		while True:
			time.sleep(3*settlingtime)
			sb=256&int(self.__sa.query(':STAT:OPER?'))     # get bit 8 to see if the sweep is complete
			print('spectrum analyzer polling ',sb)     # debug
			if sb>0: break
		# while True:
		# 	sb=256&int(self.__sa.query(':STAT:OPER?'))     # get bit 8 to see if the sweep is complete
		# 	print('spectrum analyzer polling 2nd ',sb)     # debug
		# 	if sb==0: break
		time.sleep(settlingtime)
