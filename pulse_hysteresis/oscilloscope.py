# pulse and acqusition of pulse data for hysteresis testing
# Oscilloscope control
#  Phil Marsh Carbonics Inc
# if shortoutput=True, then restrict number of points to 600
# else digitize the maximum number of points - i.e. 1megasamples single-channel and 0.5 megasamples dual-channel
import time
from utilities import *
import collections as c
class OscilloscopeDS1052E:
	def __init__(self,rm,shortoutput=False,filter=False):
		try: self.__oscilloscope = rm.open_resource('USB0::0x1AB1::0x0588::DS1ED121603918::INSTR')
		except: raise ValueError("ERROR! no oscilloscope found")
		self.__idel()
		self.__oscilloscope.write(":ACQ:TYPE NORMAL")
		self.__idel()
		self.__oscilloscope.write(":ACQ:MEMDepth LONG")
		self.__idel()
		self.__oscilloscope.query_delay=0.1         # necessary query delay to enable error free query statements
		self.__oscilloscope.timeout=20000.
		self._timefullscale=0.1                     # full scale time (horizontal scale)
		self._numberofaverages=4
		self._channel1on=True
		self._channel2on=False
		self._ch1_topscale=1.
		self._ch2_topscale=1.
		self._ch1_bottomscale=-1.
		self._ch2_bottomscale=-1.
		self._scopedualchannelsetup=False           # flag to see if we set up the scope channel in dual channel mode
		self._scopesinglechannel1setup=False
		self._scopesinglechannel2setup=False
		self._maxnumberpoints=1048566               # number of points returned by the scope
		self.__oscilloscope.chunk_size=10000000
		print(self.__oscilloscope.query("*IDN?"))
		self.__oscilloscope.write("*RST")
		self.__idel()
		self.__oscilloscope.write(":ACQUIRE:MODE RTIME")          # set to real time acquisition
		self.__idel()
		self.__oscilloscope.write(":ACQUIRE:TYPE NORMAL")
		self.__idel()
		self.__oscilloscope.write(":TIMEBASE:MODE MAIN")
		self.__idel()
		if not filter: # should we filter out high frequency components from the signal?
			self.__oscilloscope.write(":CHAN1:FILTER OFF")
			self.__idel()
			self.__oscilloscope.write(":CHAN2:FILTER OFF")
			self.__idel()
		else:
			self.__oscilloscope.write(":CHAN1:FILTER ON")
			self.__idel()
			self.__oscilloscope.write(":CHAN2:FILTER ON")
			self.__idel()
		if shortoutput:     # return just 600 digitized points
			self.__oscilloscope.write(":WAV:POIN:MODE RAW")
			self.__idel()
			self.__oscilloscope.write(":ACQUIRE:MEMD NORMAL")           # set for normal memory depth
			self.__idel()
		else:           # return maximum number of points
			self.__oscilloscope.write(":WAV:POIN:MODE RAW")
			self.__idel()
			self.__oscilloscope.write(":ACQUIRE:MEMD LONG")           # set for largest memory depth
			self.__idel()
	def reset(self):
		self.__oscilloscope.write("*RST")
		self.__idel()
################################################################################################################
################################################################################################################
# set oscilloscope triggering
# slope is POS, NEG
# mode is "EDGE" (always for now)
# level is the trigger voltage level, if level is not set and source (the trigger source) is "EXT" then the level = 2 (TTL level for triggering)
# coupling is "AC" DC and this is almost always going to be set to the default of "DC". If coupling="HF" then reject high frequency signals > 150KHz on trigger circuit.
# holdoff is the trigger holdoff time in sec and this defaults to 0.
# source is the trigger source "EXT" is external trigger, CHAN1 is trigger from channel 1, and CHAN2 is trigger from channel 2
# sweep is the sweep type which is "AUTO" - sweep whether triggered or not, NORMAL - sweep only on trigger signal, SINGLE - sweep once on a trigger signal
#
	def set_trigger(self,slope="POS",mode="EDGE",level=None,coupling="DC",holdoff=0.,source="EXT",sweep=None):
		if slope==None or (slope.lower()!="positive" and slope.lower()!="pos" and slope.lower()!="negative" and slope.lower()!="neg"): raise ValueError("ERROR! Invalid trigger slope type")
		if mode==None or (mode.lower()!="edge" and mode.lower()!="pulse"): raise ValueError("ERROR! Invalid trigger mode type")
		if source==None or (source.lower()!="ext" and source.lower()!="chan1" and source.lower()!="chan2"): raise ValueError("ERROR! Invalid trigger source type")
		if coupling==None or (coupling.lower()!="dc" and coupling.lower()!="ac" and coupling.lower()!="hf" and coupling.lower()!="lf"): raise ValueError("ERROR! Invalid trigger coupling type")
		if (level==None or not is_number(level)) and source.lower()!="ext": raise ValueError("ERROR! Invalid trigger level")
		if sweep==None or (sweep.lower()!="auto" and sweep.lower()!="normal" and sweep.lower()!="norm" and sweep.lower()!="single" and sweep.lower()!="single"): raise ValueError("ERROR! Invalid trigger source type")
		if holdoff==None or not is_number(holdoff): raise ValueError("ERROR! Invalid trigger holdoff")
		# external triggering
		if source.lower()=="ext" and level==None: level=0.5                                # set to capture the TTL sync output of the pulse generator
		self.__oscilloscope.write(":TRIG:MODE "+mode.upper())
		self.__idel()
		self.__oscilloscope.write(":TRIG:"+mode.upper(),":SOURCE "+source.upper())
		self.__idel()
		self.__oscilloscope.write(":TRIG:"+mode.upper(),":LEV "+formatnum(level,precision=4))
		self.__idel()
		self.__oscilloscope.write(":TRIG:"+mode.upper(),":SWEEP "+sweep.upper())
		self.__idel()
		self.__oscilloscope.write(":TRIG:"+mode.upper(),":COUPLING "+coupling.upper())
		self.__idel()
		self.__oscilloscope.write(":TRIG:HOLD "+formatnum(holdoff,nonexponential=True))
		self.__idel()
		actualholdoff=float(self.__oscilloscope.query(":TRIG:HOLD?"))                              # get the actual trigger holdoff
		return actualholdoff
##################################################################################################################################
# get oscilloscope sweep status
# used to determine if oscilloscope is sweeping or stopped. Returned values are: RUN, STOP, T'D, WAIT or AUTO
	def get_trigger_status(self):
		self.__oscilloscope.write(":TRIG:STAT?")
		self.__idel()
		stat=self.__oscilloscope.read()
		self.__idel()
		return stat             # stat can be RUN, STOP, T'D, WAIT, or AUTO
##################################################################################################################################
	def set_average(self,numberofaverages=None):
		if numberofaverages==None: numberofaverages=self._numberofaverages
		else: self._numberofaverages=int(numberofaverages)
		if numberofaverages==None or not is_number(numberofaverages) or numberofaverages<1: raise ValueError("ERROR! Invalid number of averages setting")
		self.__oscilloscope.write(":ACQUIRE:AVERAGES "+formatnum(numberofaverages,type='int'))
		self.__idel()
		self.__oscilloscope.write(":ACQ:TYPE AVER")
		self.__idel()
		self.__oscilloscope.write(":ACQUIRE:TYPE?")
		self.__idel()
		# atype=self.__oscilloscope.read()
		# self.__idel()
		# print("oscilloscope acquire type is ",atype)
		# self.__idel()
###################################################################################################################################
# trigger scope on next signal
	def run(self):
		self.__oscilloscope.write(":RUN")
		#while "STOP"!=str(self.get_trigger_status()): pass
		self.__idel()
###################################################################################################################################
# force stop
	def stop(self):
		self.__oscilloscope.write(":STOP")
		self.__idel()
###################################################################################################################################
# set the fullscale time#############################
	def set_fulltimescale(self,fullscale=None,offset=0.):
		if fullscale==None: fullscale=self._timefullscale
		else:
			fullscale=float(fullscale)
			self._timefullscale=fullscale
		if fullscale==None or not is_number(fullscale): raise ValueError("ERROR! Invalid time scale")
		self.__set_timescale(formatnum(fullscale/12.,nonexponential=True))
		actualfulltimescale=self.get_fulltimescale()
		#print("from line 95 in test_pulse.py actualfulltimescale ", actualfulltimescale)
		if actualfulltimescale>fullscale:
			while actualfulltimescale<fullscale:
				fullscale=fullscale*11./12.
				self.__set_timescale(formatnum(fullscale/12.,nonexponential=True))
				actualfulltimescale=self.get_fulltimescale()
				#print("from line 101 in test_pulse.py loop actualfulltimescale ",actualfulltimescale)
		if actualfulltimescale<fullscale:                       # iterate to get timescale just slighly greater than that requested
			while actualfulltimescale<fullscale:
				fullscale=fullscale*13./12.
				self.__set_timescale(formatnum(fullscale/12.,nonexponential=True))
				actualfulltimescale=self.get_fulltimescale()
				#print("from line 104 in test_pulse.py loop actualfulltimescale ",actualfulltimescale)
		self.__idel()
		timeoffset=actualfulltimescale/2.+offset
		#timeoffset=offset
		#samplerate=float(self.__oscilloscope.query(":ACQ:SAMP?"))          # get scope sample rate
		#timeoffset=self._maxnumberpoints/(2.*samplerate)
		self.__oscilloscope.write(":TIM:OFFS "+formatnum(timeoffset,nonexponential=True))
		# self.__oscilloscope.write(":TIM:OFFS 0.")
		self.__idel()
		actualtimeoffset=self.__oscilloscope.query(":TIM:OFFS?")
		self.__idel()
		# actualtimeoffset=float(self.__oscilloscope.read())
		return self.get_fulltimescale(),actualtimeoffset                     # return the actual full time scale
	###############################
	# return the full-scale time
	def get_fulltimescale(self):
		ts=float(self.__oscilloscope.query(":TIM:SCAL?"))
		# self.__idel()
		# ts=float(self.__oscilloscope.read())
		self.__idel()
		return 12.*ts
#############################################################################################################################################################
# get scope voltage scale v/div
	def get_voltagescale(self,channel=1):
		return self.__oscilloscope.query(":CHANNEL"+str(channel)+":SCALE?")
#############################################################################################################################################################
# set up a single scope channel vertical setup to read voltage
###############################################
	def set_channel(self,displaychannel=True,channel=None,coupling="DC",bottomscale=None,topscale=None,invert=False,averages=1,probeattenuation=1):
		minscale=False
		if channel==None: raise ValueError("ERROR! No channel specified")
		chan=formatnum(channel,type='int')    # make channel number an alphanumeric
		if displaychannel:
			self.__oscilloscope.write(":CHANNEL"+chan+":DISPLAY ON")
			self.__idel()
		elif not displaychannel:
			self.__oscilloscope.write(":CHANNEL"+chan+":DISPLAY OFF")
			self.__idel()
			return
		if invert==True:
			self.__oscilloscope.write(":CHANNEL"+chan+":INVERT ON")
			self.__idel()
		elif invert==False:
			self.__oscilloscope.write(":CHANNEL"+chan+":INVERT OFF")
			self.__idel()
		else: raise ValueError("ERROR! invalid value for channel "+chan+" invert")
		if probeattenuation!=1 and probeattenuation!=10 and probeattenuation!=100: raise ValueError("ERROR! Invalid value for channel "+chan+" probe attenuation")
		else:
			self.__oscilloscope.write(":CHANNEL"+chan+":PROBE "+formatnum(probeattenuation,type='int'))
			self.__idel()
		if coupling==None or not(coupling.lower()=="dc" or coupling.lower()=="ac" or coupling.lower()!="gnd"): raise ValueError("ERROR! Channel "+chan+" invalid value for coupling")
		self.__oscilloscope.write(":CHANNEL"+chan+":COUPLING "+coupling.upper())
		self.__idel()
		if (topscale-bottomscale)/8.<0.002:
			print("WARNING: scale too small. Reset to minimum allowed")
			minscale=True
			scale=probeattenuation*0.0021
		else: scale=(topscale-bottomscale)/8.
		offset=-(bottomscale+topscale)/2.
		self.__oscilloscope.write(":CHANNEL"+chan+":SCALE "+formatnum(scale,precision=5,nonexponential=True))
		self.__idel()
		self.__oscilloscope.write(":CHANNEL"+chan+":OFFSET "+formatnum(offset,precision=8,nonexponential=True))
		self.__idel()
		offsetactual=float(self.__oscilloscope.query(":CHANNEL"+chan+":OFFSET?"))
		self.__idel()
		self.set_average(numberofaverages=averages)                 # set number of averages
		#print("from line 185 in oscilloscope.py offsetactual= ",offsetactual)
		# if cannot set offset then increase the scale to allow setting of offset
		# while(not floatequal(offsetactual,offset,1E-1)):
		# 	scale=0.7*scale
		# 	self.__oscilloscope.write(":CHANNEL"+chan+":SCALE "+formatnum(scale,precision=5,nonexponential=True))
		# 	self.__idel()
		offseterror=True
		maxiter=10
		iter=0
		scaleset=scale
		while(offseterror and iter<maxiter):
			iter+=1
			if not floatequal(offsetactual,offset,1E-1):
				offseterror=True
				scaleset=1.5*scaleset
				print("actual offset, set offset ",offsetactual,offset)
				if iter==maxiter and offseterror:
					raise ValueError("ERROR! actual offset differs from set offset and exceeded number of iterations")
				self.__oscilloscope.write(":CHANNEL"+chan+":SCALE "+formatnum(scaleset,precision=5,nonexponential=True))
				self.__idel()
				offsetactual=float(self.__oscilloscope.query(":CHANNEL"+chan+":OFFSET?"))
				self.__idel()
			else: offseterror=False


		if int(channel)==1: self._scopesinglechannel1setup=True
		elif int(channel)==2: self._scopesinglechannel2setup=True
		return minscale
#########################################################################################################################################################################
# set up a double scope channel to read both channels
# No invert setting
# coupling is assumed to be DC on both probes
########################################################
	def set_dualchannel(self,ch1_bottomscale=None,ch1_topscale=None,ch2_bottomscale=None,ch2_topscale=None,ch1_probeattenuation=1,ch2_probeattenuation=1):
		if ch1_probeattenuation!=1 and ch1_probeattenuation!=10 and ch1_probeattenuation!=100: raise ValueError("ERROR! Invalid value for channel 1 probe attenuation")
		else:
			self.__oscilloscope.write(":CHANNEL1:PROBE "+formatnum(ch1_probeattenuation,type='int'))
			self.__idel()
		if ch2_probeattenuation!=1 and ch2_probeattenuation!=10 and ch2_probeattenuation!=100: raise ValueError("ERROR! Invalid value for channel 2 probe attenuation")
		else:
			self.__oscilloscope.write(":CHANNEL2:PROBE "+formatnum(ch1_probeattenuation,type='int'))
			self.__idel()
		self.__oscilloscope.write(":CHANNEL1:INVERT OFF")
		self.__idel()
		self.__oscilloscope.write(":CHANNEL2:INVERT OFF")
		self.__idel()
		if ch1_bottomscale==None: ch1_bottomscale=self._ch1_bottomscale
		else: self._ch1_bottomscale=ch1_bottomscale
		if ch1_topscale==None: ch1_topscale=self._ch1_topscale
		else: self._ch1_topscale=ch1_topscale
		if ch2_bottomscale==None: ch2_bottomscale=self._ch2_bottomscale
		else: self._ch2_bottomscale=ch2_bottomscale
		if ch2_topscale==None: ch2_topscale=self._ch2_topscale
		else: self._ch2_topscale=ch2_topscale
		# turn on both channels
		self.__oscilloscope.write(":CHANNEL1:DISPLAY ON")
		self.__idel()
		self.__oscilloscope.write(":CHANNEL2:DISPLAY ON")
		self.__idel()
		self.__oscilloscope.write(":CHANNEL1:COUPLING DC")
		self.__idel()
		self.__oscilloscope.write(":CHANNEL2:COUPLING DC")
		self.__idel()
		# set vertical scales
		# if (ch1_topscale-ch1_bottomscale)/8.<ch1_probeattenuation*0.002: raise ValueError("ERROR! Oscilloscope channel 1 scale too small - or negative")
		# if (ch2_topscale-ch2_bottomscale)/8.<ch2_probeattenuation*0.002: raise ValueError("ERROR! Oscilloscope channel 2 scale too small - or negative")
		self.__oscilloscope.write(":CHANNEL1:SCALE "+formatnum((ch1_topscale-ch1_bottomscale)/8.,precision=5,nonexponential=True))
		self.__idel()
		self.__oscilloscope.write(":CHANNEL1:OFFSET "+formatnum(-(ch1_bottomscale+ch1_topscale)/2.,precision=5,nonexponential=True))
		self.__idel()
		self.__oscilloscope.write(":CHANNEL2:SCALE "+formatnum((ch2_topscale-ch2_bottomscale)/8.,precision=5,nonexponential=True))
		self.__idel()
		self.__oscilloscope.write(":CHANNEL2:OFFSET "+formatnum(-(ch2_bottomscale+ch2_topscale)/2.,precision=5,nonexponential=True))
		self.__idel()
		self.__oscilloscope.write(":CHANNEL1:INVERT OFF")
		self.__idel()
		self.__oscilloscope.write(":CHANNEL2:INVERT OFF")
		self.__idel()
		# set up probe multipliers (probe attenuation values)
		self.__oscilloscope.write(":CHANNEL1:PROBE "+formatnum(ch1_probeattenuation,type='int'))
		self.__idel()
		self.__oscilloscope.write(":CHANNEL2:PROBE "+formatnum(ch2_probeattenuation,type='int'))
		self.__idel()
		self._scopedualchannelsetup=True
###########################################################################################################
# get data from oscilloscope
	def get_data(self,channel=1,timerange=None,referencevoltage=0.,R=None):
		if int(channel)!=1 and int(channel)!=2: raise ValueError("ERROR! Illegal channel specifier")
		if int(channel)==1 and not self._scopesinglechannel1setup: raise ValueError("ERROR! have not set up single scope channel 1")
		if int(channel)==2 and not self._scopesinglechannel2setup: raise ValueError("ERROR! have not set up single scope channel 2")
		chan=formatnum(channel,type='int')
		self.__readrawdata(channel=channel)            # throw away data from first read since the second read provides the full dataset
		waveformdataraw=self.__readrawdata(channel=channel)
		waveformdata_unscaled=np.frombuffer(waveformdataraw,'B')[10:]       # remove first 10 bytes as this is just information about the real data to follow
		if min(waveformdata_unscaled)<25: vuppperlimit=True                 # top of display=25 bottom of display = 225
		else: vuppperlimit=False
		if max(waveformdata_unscaled)>225: vlowerlimit=True
		else: vlowerlimit=False

		# get time array
		npts=len(waveformdata_unscaled)
		#print("from line 297 npts",npts)
		timeoffset=float(self.__oscilloscope.query(":TIM:OFFS?"))
		deltatime=1./float(self.__oscilloscope.query(":ACQ:SAMP? "+"CHAN"+str(channel)))           # get the sample rate in samples/sec
		#print("total time/2",npts*deltatime/2.,float(self.__oscilloscope.query(":ACQ:SAMP?")))
		timearray=[(timeoffset-npts*deltatime/2)+i*deltatime for i in range(npts)]
		#timearray=[i*deltatime for i in range(npts)]
		# get voltage waveform
		voffset=float(self.__oscilloscope.query(":CHANNEL"+chan+":OFFSET?"))
		vscale=float(self.__oscilloscope.query(":CHANNEL"+chan+":SCALE?"))
		waveformdata=[(240.-v)*(vscale/25.)-(voffset+4.6*vscale) for v in waveformdata_unscaled]
		# now get actual time series after throwing away excess time points as specified
		Vt=c.deque()                # measured voltage - reference voltage
		timestamp=c.deque()         # selected timestamp array
		Ip=c.deque()                # current
		for ii in range(len(timearray)):
			if timearray[ii]>=0.:                   # reject negative times since they occur prior to the trigger and are of no interest
				timestamp.append(timearray[ii])
				Vt.append(waveformdata[ii])            # time-domain waveform for selected timestamps only
				if R!=None: Ip.append((waveformdata[ii]-referencevoltage)/R)            # current through resistor of value R
			if timerange!=None and timearray[ii]>timerange: break
		# debug
		# for i in range(0,len(timestamp)):
		# 	print(i,timestamp[i],Vt[i])
		return {"t":timestamp,"Vt":Vt,"Ip":Ip,"vlowerlimit":vlowerlimit,"vupperlimit":vuppperlimit}
###########################################################################################################
# get differential voltage data from oscilloscope i.e. channel2 voltage - channel 1 voltage
# also if R is specified, get the I (current) waveform through the resistance R from I=(channel2 voltage - channel 1 voltage)/R
	def get_dual_data(self,R=None,timerange=None):
		#if not self._scopedualchannelsetup: raise ValueError("ERROR! dual channels not set up")
		# get channel 1 data
		self.__readrawdata(channel=1)                                 # throw away short form data that we get on first read
		waveformdataraw=self.__readrawdata(channel=1)
		ch1_waveformdata_unscaled=np.frombuffer(waveformdataraw,'B')[10:]    # convert channel 1 raw data to numbers and strip off first 10 bytes
		# get channel 2 data
		self.__readrawdata(channel=2)                                 # throw away short form data that we get on first read
		waveformdataraw=self.__readrawdata(channel=2)
		ch2_waveformdata_unscaled=np.frombuffer(waveformdataraw,'B')[10:]    # convert channel 2 raw data to numbers and strip off first 10 bytes
		# set flags for lower and upper channel offscale voltage indicators if the voltages go offscale
		if min(ch1_waveformdata_unscaled)<25: ch1_vuppperlimit=True                 # top of display=25 bottom of display = 225
		else: ch1_vuppperlimit=False
		if max(ch1_waveformdata_unscaled)>225: ch1_vlowerlimit=True
		else: ch1_vlowerlimit=False
		if min(ch2_waveformdata_unscaled)<25: ch2_vuppperlimit=True                 # top of display=25 bottom of display = 225
		else: ch2_vuppperlimit=False
		if max(ch2_waveformdata_unscaled)>225: ch2_vlowerlimit=True
		else: ch2_vlowerlimit=False

		#timescale=self.__oscilloscope.query(":TIM:SCAL?")
		timeoffset=float(self.__oscilloscope.query(":TIM:OFFS?"))
		self.__idel()
		ch1_voffset=float(self.__oscilloscope.query(":CHANNEL1:OFFSET?"))
		self.__idel()
		ch1_vscale=float(self.__oscilloscope.query(":CHANNEL1:SCALE?"))
		self.__idel()
		ch2_voffset=float(self.__oscilloscope.query(":CHANNEL2:OFFSET?"))
		self.__idel()
		ch2_vscale=float(self.__oscilloscope.query(":CHANNEL2:SCALE?"))
		self.__idel()
		# find time array
		npts=len(ch1_waveformdata_unscaled)                                    # number of time points
		deltatime=1./float(self.__oscilloscope.query(":ACQ:SAMP?"))           # get the sample rate in samples/sec
		timearray=[(timeoffset-npts*deltatime/2)+i*deltatime for i in range(npts)]
		# find voltage waveform arrays for channel 1 and 2
		ch1_waveformdata=[(240.-v)*(ch1_vscale/25.)-(ch1_voffset+4.6*ch1_vscale) for v in ch1_waveformdata_unscaled]
		ch2_waveformdata=[(240.-v)*(ch2_vscale/25.)-(ch2_voffset+4.6*ch2_vscale) for v in ch2_waveformdata_unscaled]
		timestamp=c.deque()
		Vch1=c.deque()
		Vch2=c.deque()
		for ii in range(len(timearray)):
			if timearray[ii]>=0.:
				timestamp.append(timearray[ii])
				Vch1.append(ch1_waveformdata[ii])
				Vch2.append(ch2_waveformdata[ii])
			if timerange!=None and timearray[ii]>timerange: break
		# vdiff=np.subtract(Vch2,Vch1)        # differential voltage between channel 2 and channel 1
		if R>0. and R!=None:        # then get the current waveform too
			#IDUT=np.divide(vdiff,R)
			IDUT=np.divide(Vch1,R)
		else: IDUT=None

		return {"t":timestamp,"Vch1":Vch1,"Vch2":Vch2,"I":IDUT,"ch1_lowerlimit":ch1_vlowerlimit,"ch1_upperlimit":ch1_vuppperlimit,"ch2_lowerlimit":ch2_vlowerlimit,"ch2_upperlimit":ch2_vuppperlimit}
############################################################################################################
	def __set_timescale(self,timescale):
		self.__oscilloscope.write(":TIM:SCAL "+timescale)
		self.__idel()
#############################################################################################################
# capture 2nd pulse
	def capture2ndpulse(self):
		self.stop()
		self.run()
		while "STOP"!=str(self.get_trigger_status()): continue
		self.run()
		starttime=time.time()
		while "STOP"!=str(self.get_trigger_status()): continue
		stoptime=time.time()
		return stoptime-starttime
############################################################################################################
#  get minimum and maximum voltage displayed on scope
	def get_voltagerange(self,channel=1):
		if channel==1:
			voffset=float(self.__oscilloscope.query(":CHANNEL1:OFFSET?"))
			vscale=float(self.__oscilloscope.query(":CHANNEL1:SCALE?"))
		elif channel==2:
			voffset=float(self.__oscilloscope.query(":CHANNEL2:OFFSET?"))
			vscale=float(self.__oscilloscope.query(":CHANNEL2:SCALE?"))
		else: raise ValueError("ERROR! no valid channel specified")
		vrangemin=-4.*vscale-voffset
		vrangemax=4.*vscale-voffset
		return vrangemin,vrangemax
############################################################################################################
# set time delay to allow for processing of commands
	def __idel(self):
		time.sleep(0.1)
############################################################################################################
# safely read data from scope
# re-read data if a read times out
	def __readrawdata(self,channel=1):
		# if longdata==True then we need to read twice to capture the long-form, high-resolution data set
		#self.__oscilloscope.query_delay=6.         # necessary query delay to enable error free query statements
		#self.__oscilloscope.delay=6.
		self.__oscilloscope.chunk_size=10000000
		readerror=True
		maxreadtries=20
		readtries=0
		time.sleep(1.)
		#print("entering read of raw data")
		timetoreadstart=time.time()

		while readerror and readtries<maxreadtries:
			self.__oscilloscope.write(":WAV:DATA? CHANNEL"+formatnum(channel,type='int'))
			#waveformdataraw=self.__oscilloscope.query_binary_values(":WAV:DATA? CHANNEL"+formatnum(channel,type='int'))
			#time.sleep(0.1)                 # allow this time for reading to minimize the need for re-reads of the data
			readtries+=1
			#self.__oscilloscope.clear()
			#time.sleep(10.)
			#waveformdataraw=self.__oscilloscope.read_raw()
			time.sleep(1)
			try: waveformdataraw=self.__oscilloscope.read_raw(100000000)
			except:
				print("have a read error, retrying")
				readerror=True
				continue
			readerror=False
			#time.sleep(0.2)
		timetoreadend=time.time()
		print("from line 447 in oscilloscope.py time to read raw data=",timetoreadend-timetoreadstart)
		self.__idel()
		self.__oscilloscope.query_delay=0.1         # necessary query delay to enable error free query statements
		self.__oscilloscope.delay=0.1
		if readerror: raise ValueError("ERROR! cannot read scope")
		else: return waveformdataraw
############################################################################################################
# get the upper or lower smooth voltage of a pulsed waveform
	def get_minmaxvoltage(self, channel=1, top=False):
		chan=formatnum(channel,type='int')
		if channel==1 and not self._scopesinglechannel1setup and not self._scopedualchannelsetup: raise ValueError("ERROR! scope not set up")
		if channel==2 and not self._scopesinglechannel2setup and not self._scopedualchannelsetup: raise ValueError("ERROR! scope not set up")
		if top:
			vtb=self.__oscilloscope.query(":MEAS:VMAX? CHANNEL"+chan)
			self.__idel()
		else:
			vtb=self.__oscilloscope.query(":MEAS:VMIN? CHANNEL"+chan)
			self.__idel()
		return float(vtb)
###############################################################################################################
# get the sample rate
	def get_samplerate(self,channel=1):
		rate=int(self.__oscilloscope.query(":ACQ:SAMP? CHAN"+str(channel)))
		self.__idel()
		return rate
###############################################################################################################
###############################################################################################################
# get the memory size
	def get_memorydepth(self):
		md=int(self.__oscilloscope.query(":ACQ:MEMD?"))
		self.__idel()
		return md
###############################################################################################################
###############################################################################################################
# set the memory size
	def set_memorydepth(self,memorydepth="long"):
		if memorydepth.upper()!="LONG" or memorydepth.upper()!="SHORT": raise ValueError("ERROR! incorrect setting for memorydepth, must be LONG or NORM")
		self.__oscilloscope.write(":ACQ:MEMD "+memorydepth.upper())
		self.__idel()
		return self.get_memorydepth()
###############################################################################################################