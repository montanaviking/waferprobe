# Phil Marsh Carbonics Inc
# pulse generator control driver
# Rigol pulse generator

from utilities import *
import time
from sys import platform as _platform

Nvoltlevels=16383          # number of levels in the voltage output

class PulseGeneratorDG1022:
	def __init__(self,rm=None):
		self.delaytime=0.05                 # time allowed between instruction writes
		if 'win' in _platform:
			try: self.__pulsegenerator=rm.open_resource("USB0::0x1AB1::0x0588::DG1D123503444::INSTR")
			except: raise ValueError("ERROR! no pulse generator found, using Windows")
		elif 'linux' in _platform:
			try: self.__pulsegenerator=rm.open_resource("USB0::6833::1416::???::0::INSTR")
			except: raise ValueError("ERROR! no pulse generator found, using Linux")
		self.__idel()                         # follow all instruction writes with a delay for instrument processing
		#self.__pulsegenerator.write("*RST")
		self.__idel()
		self.__pulsegenerator.write("*IDN?")
		self.__idel()
		print(self.__pulsegenerator.read())
		# set up default conditions
		self.__pulsegenerator.write("OUTP:SYNC ON")             # turns on output sync for use by externally-triggered oscilloscope
		self.__idel()
		self.__pulsegenerator.write("OUTP:TRIG:SLOP POS")
		self.__idel()
		self.__pulsegenerator.write("OUTP:TRIG ON")
		self.__idel()
		self.havesinglepulsedsetup=False                        # have we set up the single pulsed mode?
		# variables
		# self.pulsetimehigh=None
		# self.pulsetimelow=None
		# self.voltage_high=None
		# self.voltage_low=None
		# self.period=None
		self.__pulsegenerator.write("SYST:BEEP:STAT ON")
	# set time delay to allow for processing of commands
	def __idel(self):
		time.sleep(0.5)

# set up single pulse for single pulse in burst mode
# a - polarity means that the pulse is negative-going and + means positive-going
# If the pulse is negative-going (-) then voltagehigh is the soak voltage (dominates the duty cycle) and voltagelow is the pulse voltage
#  If the pulse is positive-going (+) then voltagelow is the soak voltage (dominates the duty cycle) and voltagehigh is the pulse voltage
# In burst mode - the mode set up here, the quescent voltage is the soak voltage
	def set_pulsesetup_singlepulse(self,polarity="-",pulsewidth=None,period=None,voltagelow=0.,voltagehigh=0.,pulsegeneratoroutputZ="INF"):
		#period=2.*period                    # actual period prior to the waferform is 1/2 the total period and we're interested only in the soak portion prior to the pulse
		try: pulsegeneratoroutputZ=str(int(pulsegeneratoroutputZ))
		except: pulsegeneratoroutputZ=pulsegeneratoroutputZ.lower()
		if pulsegeneratoroutputZ=="50":
			self.__pulsegenerator.write("OUTP:LOAD 50")
			self.__idel()
		elif pulsegeneratoroutputZ.lower()=="inf":
			self.__pulsegenerator.write("OUTP:LOAD INF")
			self.__idel()
		else: raise ValueError("ERROR! No valid pulse generator output impedance setting was given")
		if period<=pulsewidth:raise ValueError("ERROR! period<=pulsewidth - NOT ALLOWED")
		self.singlepulsewidth=pulsewidth
		self.singlepulseperiod=period
		self.havesinglepulsedsetup=True
		self.__pulsegenerator.write("BURS:STAT ON")
		self.__idel()
		self.__pulsegenerator.write("BURS:NCYC 1")                      # set one pulse
		self.__idel()
		self.__pulsegenerator.write("TRIG:DEL 0.")
		self.__idel()
		self.__pulsegenerator.write("BURS:INT:PER "+str(period))
		self.__idel()
		self.__pulsegenerator.write("VOLT:LOW "+str(voltagelow))
		self.__idel()
		self.__pulsegenerator.write("VOLT:HIGH "+str(voltagehigh))
		self.__idel()
		self.__pulsegenerator.write("VOLT:LOW?")
		self.__idel()
		actualvoltagehigh=self.__pulsegenerator.read()
		#actualvoltagelow=self.__pulsegenerator.read()
		self.__pulsegenerator.write("VOLT:HIGH?")
		self.__idel()
		actualvoltagelow=self.__pulsegenerator.read()
		#actualvoltagehigh=self.__pulsegenerator.read()

		if polarity=="+":
			self.__pulsegenerator.write("OUTP:POL NORM")
			self.__idel()
		elif polarity=="-":
			self.__pulsegenerator.write("OUTP:POL INV")
			self.__idel()
		self.__pulsegenerator.write("PULS:PER "+str(period))
		self.__idel()
		self.__pulsegenerator.write("PULS:WIDT "+str(pulsewidth))
		self.__idel()
		self.__pulsegenerator.write("PULS:WIDT?")
		self.__idel()
		actualpulsewidth=float(self.__pulsegenerator.read())
		self.__idel()
		self.__pulsegenerator.write("BURS:INT:PER?")
		self.__idel()
		actualburstperiod=float(self.__pulsegenerator.read())
		self.__idel()
		self.__pulsegenerator.write("PULS:PER?")
		self.__idel()
		actualperiod=float(self.__pulsegenerator.read())
		self.__idel()
		if period!=actualburstperiod: print("warning! set period,actualburstperiod,actualperiod",period,actualburstperiod,actualperiod)
		return actualpulsewidth,actualvoltagelow,actualvoltagehigh
#######################################################################
# outputs one trigger pulse per call of pulsetrainon()
# However, this produces an extraneous, unwanted pulse, halfway between the pulse voltage and quiescent voltage for about 120mS and therefore method set_singlepulsesetup() has
# set up a delay of one period to obtain a controlled soak voltage time of at least one period prior to the desired pulse - over which oscilloscope data will be taken
	def pulsetrainon(self):
		if not self.havesinglepulsedsetup:
			print("WARNING! Nothing done since single pulse mode is not set up!")
			return
		self.__pulsegenerator.write("TRIG:SOUR IMM")    # internal trigger
		self.__idel()
		self.__pulsegenerator.write("OUTPUT ON")
		self.__idel()
	def pulsetrainoff(self):
		self.__pulsegenerator.write("OUTPUT OFF")
		self.__idel()
		self.__pulsegenerator.write("TRIG:SOUR EXT")
		self.__idel()


	def set_polarity(self,channel="1",polarity="NORM"):
		if channel==None: raise ValueError("ERROR illegal pulse generator channel specified")
		if polarity.upper()!=None and polarity.upper()!="NORM" and polarity.upper()!="INV": raise ValueError("ERROR illegal pulse generator channel specified")
		if channel=="1":
			self.__pulsegenerator.write("OUTP:POL "+polarity.upper())
			self.__idel()
		else:
			self.__pulsegenerator.write("OUTP:POL:CH2 "+polarity.upper())
			self.__idel()

	def set_time(self,channel="1",pulsetimehigh=None,pulsetimelow=None):
		channel=str(channel)
		if pulsetimehigh==None or pulsetimelow==None: raise ValueError("ERROR illegal pulse times")
		if channel==None or (channel!="1" and channel!="2"): raise ValueError("ERROR illegal pulse generator channel specified")
		period=pulsetimelow+pulsetimehigh
		if channel=="1":
			self.__pulsegenerator.write("OUTP:POL?")
			self.__idel()
			outputpolarity=str(self.__pulsegenerator.read())
			if outputpolarity.strip()=='INV': pulsetimelow,pulsetimehigh=pulsetimehigh,pulsetimelow         # swap low and high times to ensure that "low time" is the timespan of low voltage and "high time" the timespan of high voltage
			self.__pulsegenerator.write("PULS:PER "+str(period))
			self.__idel()
			self.__pulsegenerator.write("PULS:WIDT "+str(pulsetimehigh))
			self.__idel()
			self.__pulsegenerator.write("PULS:PER?")
			self.__idel()
			pulseperiodactual=self.__pulsegenerator.read()
			self.__idel()
			self.__pulsegenerator.write("PULS:WIDT?")
			self.__idel()
			if outputpolarity.strip()=="NORM":
				pulsehighactual=self.__pulsegenerator.read()
				pulselowactual=float(pulseperiodactual)-float(pulsehighactual)
			else:
				pulselowactual=self.__pulsegenerator.read()
				pulsehighactual=float(pulseperiodactual)-float(pulselowactual)
		else:
			self.__pulsegenerator.write("OUTP:POL:CH2?")
			self.__idel()
			outputpolarity=str(self.__pulsegenerator.read())
			if outputpolarity.strip()=="INV": pulsetimelow,pulsetimehigh=pulsetimehigh,pulsetimelow         # swap low and high times to ensure that "low time" is the timespan of low voltage and "high time" the timespan of high voltage

			self.__pulsegenerator.write("PULS:PER:CH2 "+str(period))
			self.__idel()
			self.__pulsegenerator.write("PULS:WIDT:CH2 "+str(pulsetimehigh))
			self.__idel()
			self.__pulsegenerator.write("PULS:PER:CH2?")
			self.__idel()
			pulseperiodactual=self.__pulsegenerator.read()
			self.__idel()
			self.__pulsegenerator.write("PULS:WIDT:CH2?")
			self.__idel()
			if outputpolarity.strip()=="NORM":
				pulsehighactual=self.__pulsegenerator.read()
				pulselowactual=float(pulseperiodactual)-float(pulsehighactual)
			else:
				pulselowactual=self.__pulsegenerator.read()
				pulsehighactual=float(pulseperiodactual)-float(pulselowactual)
		return pulselowactual,pulsehighactual

	def set_voltage(self,channel="1",voltagehigh=0.,voltagelow=0.):
		if voltagelow==None or voltagehigh==None or voltagehigh<voltagelow: raise ValueError("ERROR illegal voltage value")
		if channel==None or (channel!="1" and channel!="2"): raise ValueError("ERROR illegal pulse generator channel specified")
		if channel=="1":
			self.__pulsegenerator.write("VOLT:LOW "+str(voltagelow))
			self.__idel()
			self.__pulsegenerator.write("VOLT:HIGH "+str(voltagehigh))
			self.__idel()
			self.__pulsegenerator.write("VOLT:LOW?")
			self.__idel()
			voltagelowactual=self.__pulsegenerator.read()
			self.__pulsegenerator.write("VOLT:HIGH?")
			self.__idel()
			voltagehighactual=self.__pulsegenerator.read()
		else:
			self.__pulsegenerator.write("VOLT:LOW:CH2 "+str(voltagelow))
			self.__idel()
			self.__pulsegenerator.write("VOLT:HIGH:CH2 "+str(voltagehigh))
			self.__idel()
			self.__pulsegenerator.write("VOLT:LOW:CH2?")
			self.__idel()
			voltagelowactual=self.__pulsegenerator.read()
			self.__pulsegenerator.write("VOLT:HIGH:CH2?")
			self.__idel()
			voltagehighactual=self.__pulsegenerator.read()
		return float(voltagelowactual),float(voltagehighactual)                       # return actual voltage setting

# toggle to burst mode
	def set_single(self,single=True):
		self.__pulsegenerator.write("BURS:NCYC 1")                      # set one pulse
		self.__idel()
		if single:
			self.__pulsegenerator.write("BURS:STAT ON")
			self.__idel()
		else:
			self.__pulsegenerator.write("BURS:STAT OFF")
			self.__idel()


# programmatically trigger the pulse generator
	def trigger(self):
		self.__pulsegenerator.write("TRIG:SOUR IMM")
		self.__idel()

#######################################################################
# set up signal generator to output a series of pulses having a linearly rising and falling amplitude, i.e. one ramp from voltagequescent to voltagemax
# followed by another ramp from voltagemax to voltagequescent
# with a set value of quiescent voltage
# pulsewidth is in sec, frequency in Hz
# number of pulses must
	def ramppulses(self, frequency=None, period=None, quiescentvoltage=None, pulsedvoltage=None, pulsewidth=None, dutycyclefraction=0.1, pulsegeneratoroutputZ="INF"):
		# generate up and down triangular ramp composed of short pulses
		if frequency==None and period==None: raise ValueError("ERROR! need to provide frequency (Hz) or period (sec) of ramp")
		elif frequency!=None and period!=None: raise ValueError("ERROR! must provide either a frequency (Hz) or period (sec) but not both")
		if frequency!=None: period=1/frequency
		if pulsegeneratoroutputZ=="50":
			self.__pulsegenerator.write("OUTP:LOAD 50")
			self.__idel()
		elif pulsegeneratoroutputZ.lower()=="inf":
			self.__pulsegenerator.write("OUTP:LOAD INF")
			self.__idel()
		else: raise ValueError("ERROR! No valid pulse generator output impedance setting was given")
		if period!=None: frequency=1/period
		self.__pulsegenerator.write("FUNC USER")
		self.__idel()
		self.__pulsegenerator.write("FREQ "+str(frequency))
		self.__idel()
		self.__pulsegenerator.write("VOLT:UNIT VPP")
		self.__idel()
		self.__pulsegenerator.write("BURS:STAT OFF")            # turn off burst mode because this is a continuous waveform
		self.__idel()
		self.__pulsegenerator.write("TRIG:DEL 0.")              # set zero trigger delay
		self.__idel()

		if dutycyclefraction>0.9: raise ValueError("ERROR! dutycycle > 0.9")
		if dutycyclefraction<0.01: raise ValueError("ERROR! dutycycle too small")

		npts=int(period/pulsewidth)+1                           # number of points in a period of the whole up and down ramp
		nptsq=int((1.-dutycyclefraction)/dutycyclefraction)         # number of points spent at the quescent voltage, the number of points spent at the pulsed voltage is always 1 (between two points)

		# construct rising ramp pulses going from quiescentvoltage to pulsedvoltage
		# voltnorm is from 0 to 1 and is the normalized voltage swing
		pulsevolt = []
		iq=nptsq+1           # points counter for quescent portions of time
		i=0                  # ramp time counter
		deltavnorm=int(2*Nvoltlevels/npts)
		normvoltage=0
		while i<=npts:
			if iq>nptsq:            # time for a pulse in the ramp
				iq=0                # zero quescent time counter since this is the start of a pulse which is followed by quescent time
				pulsevolt.append(normvoltage)
				i+=1
				pulsevolt.append(normvoltage)
			if i<int(npts/2):
				normvoltage+=deltavnorm     # normalized voltage i.e. digital levels corresponding to voltage
				if normvoltage<0: normvoltage=0
				if normvoltage>Nvoltlevels: normvoltage=Nvoltlevels
			else:
				normvoltage-=deltavnorm
				if normvoltage<0: normvoltage=0
				if normvoltage>Nvoltlevels: normvoltage=Nvoltlevels
			i+=1                    # count out time for ramp
			iq+=1                   # count out quescent time
			pulsevolt.append(0)    # normalized quescent voltage = 0 on normalized digital voltage level scale
		# # now ramp voltage from pulsedvoltage down to quiescentvoltage
		# iq=0           # points counter for quescent portions of time, start descending ramp with a quescent time
		# i=0                  # ramp time counter
		# while i<=npts:
		# 	if iq>nptsq:            # time for a pulse in the ramp
		# 		iq=0                # zero quescent time counter since this is the start of a pulse which is followed by quescent time
		# 		normvoltage=int(((npts-i)/npts)*Nvoltlevels)   # normalized voltage i.e. digital levels corresponding to voltage
		# 		pulsevolt.append(normvoltage)
		# 		i+=1
		# 		pulsevolt.append(normvoltage)
		# 	i+=1                    # count out time for ramp
		# 	iq+=1                   # count out quescent time
		# 	pulsevolt.append(0)    # normalized quescent voltage = 0 on normalized digital voltage level scale

		if pulsedvoltage<quiescentvoltage: # this is a negative-going ramp of pulses
			# construct waveform
			self.__pulsegenerator.write("VOLT:LOW " + str(pulsedvoltage))
			self.__idel()
			self.__pulsegenerator.write("VOLT:HIGH " + str(quiescentvoltage))
			self.__idel()
			self.__pulsegenerator.write("OUTP:POL INV")
			self.__idel()
		else: # this is a positive-going ramp of pulses
			# construct waveform
			self.__pulsegenerator.write("VOLT:LOW " + str(quiescentvoltage))
			self.__idel()
			self.__pulsegenerator.write("VOLT:HIGH " + str(pulsedvoltage))
			self.__idel()
			self.__pulsegenerator.write("OUTP:POL NORM")
			self.__idel()

		# renormalize voltage pulse array so it goes from 0 to Nvoltlevels
		scalefactor=Nvoltlevels/max(pulsevolt)
		pulsevoltstr=[]
		for pv in pulsevolt:
			v=scalefactor*pv
			if v>Nvoltlevels: v=Nvoltlevels
			pulsevoltstr.append(str(v))
		#pulsevoltstr=[str(scalefactor*pv) for pv in pulsevolt]      # convert normalized voltage time point series to string
		# now setup the pulse generator with the ramped waveform
		#self.__pulsegenerator.write("DATA:DEL VOLATILE")
		if len(pulsevolt)>4095: raise ValueError("ERROR! too many points exceeds 4095")
		#print("length of voltage waveform = ",len(pulsevolt))
		#time.sleep(5)
		self.__pulsegenerator.write("DATA:DAC VOLATILE,"+",".join(pulsevoltstr))
		time.sleep(5)
		self.__pulsegenerator.write("FUNC:USER VOLATILE")
		self.__idel()
		#time.sleep(5)
		#print(len(pulsevolt))
		#for pv in pulsevolt: print(pv)
		# self.__pulsegenerator.write("SYST:ERR")
		# self.__idel()
		# err=self.__pulsegenerator.read()
		# print(err)
		#self.__pulsegenerator.write("DATA:DAC VOLATILE,8192,8192,0,0")
		self.havesinglepulsedsetup=True
#######################################################################
# set up signal generator to output a continuous ramp a linearly rising and falling amplitude, i.e. one ramp from voltagequiescent to voltagemax
# followed by another ramp from voltagemax to voltagequiescent
# with a set value of quiescent voltage
# pulsewidth is in sec, frequency in Hz
# number of pulses must
	def ramp(self, frequency=None, period=None, Vmin=None,Vmax=None, pulsegeneratoroutputZ="INF"):
		# generate up and down continuous triangular ramp with peak voltages of Vmin and Vmax
		if frequency==None and period==None: raise ValueError("ERROR! need to provide frequency (Hz) or period (sec) of ramp")
		elif frequency!=None and period!=None: raise ValueError("ERROR! must provide either a frequency (Hz) or period (sec) but not both")
		if frequency!=None: period=1/frequency
		if pulsegeneratoroutputZ=="50":
			self.__pulsegenerator.write("OUTP:LOAD 50")
			self.__idel()
		elif pulsegeneratoroutputZ.lower()=="inf":
			self.__pulsegenerator.write("OUTP:LOAD INF")
			self.__idel()
		else: raise ValueError("ERROR! No valid pulse generator output impedance setting was given")
		if period!=None: frequency=1/period
		self.__pulsegenerator.write("FUNC USER")
		self.__idel()
		self.__pulsegenerator.write("FREQ "+str(frequency))
		self.__idel()
		self.__pulsegenerator.write("VOLT:UNIT VPP")
		self.__idel()
		self.__pulsegenerator.write("BURS:STAT OFF")            # turn off burst mode because this is a continuous waveform
		self.__idel()
		self.__pulsegenerator.write("TRIG:DEL 0.")              # set zero trigger delay
		self.__idel()

		# construct rising ramp pulses going from quiescentvoltage to pulsedvoltage
		# voltnorm is from 0 to 1 and is the normalized voltage swing
		if Vmax<Vmin: # this is a negative-going ramp of pulses
			# construct waveform
			self.__pulsegenerator.write("VOLT:LOW " + str(Vmax))
			self.__idel()
			self.__pulsegenerator.write("VOLT:HIGH " + str(Vmin))
			self.__idel()
			self.__pulsegenerator.write("OUTP:POL INV")
			self.__idel()
		else: # this is a positive-going ramp of pulses
			# construct waveform
			self.__pulsegenerator.write("VOLT:LOW " + str(Vmin))
			self.__idel()
			self.__pulsegenerator.write("VOLT:HIGH " + str(Vmax))
			self.__idel()
			self.__pulsegenerator.write("OUTP:POL NORM")
			self.__idel()
		self.__pulsegenerator.write("VOLT:LOW?")
		self.__idel()
		voltlow=self.__pulsegenerator.read()
		self.__idel()
		self.__pulsegenerator.write("VOLT:HIGH?")
		self.__idel()
		volthigh=self.__pulsegenerator.read()
		self.__idel()
		# renormalize voltage pulse array so it goes from 0 to Nvoltlevels
		cmd="DATA:DAC VOLATILE,"+",".join([str(int(Nvoltlevels/2)+1),str(Nvoltlevels),str(int(Nvoltlevels/2)+1),"0"])
		self.__pulsegenerator.write(cmd)
		time.sleep(5)
		self.__pulsegenerator.write("FUNC:USER VOLATILE")
		self.__idel()
		self.havesinglepulsedsetup=True
##############################################################################################################
##############################################################################################################
# set up continuous pulse output
# a - polarity means that the pulse is negative-going and + means positive-going
# If the pulse is negative-going (-) then voltagehigh is the soak voltage (dominates the duty cycle) and voltagelow is the pulse voltage
#  If the pulse is positive-going (+) then voltagelow is the soak voltage (dominates the duty cycle) and voltagehigh is the pulse voltage
#
	def set_pulsesetup_continuous(self,polarity="-",pulsewidth=None,period=None,voltagelow=0.,voltagehigh=0.,pulsegeneratoroutputZ="INF"):
		try: pulsegeneratoroutputZ=str(int(pulsegeneratoroutputZ))
		except: pulsegeneratoroutputZ=pulsegeneratoroutputZ.lower()
		if pulsegeneratoroutputZ=="50":
			self.__pulsegenerator.write("OUTP:LOAD 50")
			self.__idel()
		elif pulsegeneratoroutputZ.lower()=="inf":
			self.__pulsegenerator.write("OUTP:LOAD INF")
			self.__idel()
		else: raise ValueError("ERROR! No valid pulse generator output impedance setting was given")
		if period<=pulsewidth:raise ValueError("ERROR! period<=pulsewidth - NOT ALLOWED")
		self.singlepulsewidth=pulsewidth
		self.singlepulseperiod=period
		self.havesinglepulsedsetup=True
		self.__pulsegenerator.write("BURS:STAT OFF")            # set burst off since we want a continuous pulse train
		self.__idel()
		self.__pulsegenerator.write("TRIG:DEL 0.")              # set zero trigger delay
		self.__idel()
		self.__pulsegenerator.write("VOLT:LOW "+str(voltagelow))
		self.__idel()
		self.__pulsegenerator.write("VOLT:HIGH "+str(voltagehigh))
		self.__idel()
		self.__pulsegenerator.write("VOLT:LOW?")
		self.__idel()
		actualvoltagelow=self.__pulsegenerator.read()
		self.__pulsegenerator.write("VOLT:HIGH?")
		self.__idel()
		actualvoltagehigh=self.__pulsegenerator.read()

		if polarity=="+":
			self.__pulsegenerator.write("OUTP:POL NORM")
			self.__idel()
		elif polarity=="-":
			self.__pulsegenerator.write("OUTP:POL INV")
			self.__idel()

		self.__pulsegenerator.write("PULS:PER "+str(period))
		self.__idel()
		self.__pulsegenerator.write("PULS:WIDT "+str(pulsewidth))
		self.__idel()
		self.__pulsegenerator.write("PULS:WIDT?")
		self.__idel()
		actualpulsewidth=float(self.__pulsegenerator.read())
		self.__idel()
		self.__pulsegenerator.write("PULS:PER?")
		self.__idel()
		actualperiod=float(self.__pulsegenerator.read())
		self.__idel()
		if period!=actualperiod: print("warning! set period,actualburstperiod,actualperiod",period,actualperiod,actualperiod)
		return actualpulsewidth,actualvoltagelow,actualvoltagehigh
#######################################################################
#######################################################################
# set up signal generator to output pulses which have controlled rise and fall ramp rates. All times are given in seconds
# period is the total period of the pulse waveform
# risefalltimenpts is the number of points in the rising and falling portions of the waveform. A risefalltimenpts=0 gives rise and fall times = pulse width
# slewtime is the rise and fall time of the pulse, i.e. the time taken to move from the low voltage to the high voltage and from the high voltage back to the low voltage
# nptsinpulse is the number of points in a pulse
	def pulsewaveform_controlledslew(self,period=None,voltagequescent=None,voltagepulse=None,pulsewidth=None,risefalltimenpts=1,nptsinpulse=1,pulsegeneratoroutputZ="inf"):
		# generate up and down triangular ramp composed of short pulses
		if period==None: raise ValueError("ERROR! need to provide period (sec) of the pulsed waveform")
		if voltagequescent==None: raise ValueError("ERROR! need to provide the quescent voltage of the pulsed waveform")
		if voltagepulse==None: raise ValueError("ERROR! need to provide the pulse voltage of the pulsed waveform")
		if pulsewidth==None: raise ValueError("ERROR! need to provide the pulse width of the pulsed waveform")
		if risefalltimenpts==None: raise ValueError("ERROR! need to provide the risetime/falltime of the pulsed waveform")
		if risefalltimenpts==0: risefalltimenpts=1
		if pulsegeneratoroutputZ=="50":
			self.__pulsegenerator.write("OUTP:LOAD 50")
			self.__idel()
		elif pulsegeneratoroutputZ.lower()=="inf":
			self.__pulsegenerator.write("OUTP:LOAD INF")
			self.__idel()
		else: raise ValueError("ERROR! No valid pulse generator output impedance setting was given")
		frequency=1/period
		self.__pulsegenerator.write("FUNC USER")
		self.__idel()
		self.__pulsegenerator.write("FREQ "+str(frequency))
		self.__idel()
		self.__pulsegenerator.write("VOLT:UNIT VPP")
		self.__idel()
		self.__pulsegenerator.write("TRIG:DEL 0.")              # set zero trigger delay
		self.__idel()
		self.__pulsegenerator.write("BURS:STAT OFF")            # turn off burst mode because this is a continuous waveform
		self.__idel()

		#risefalltime=pulsewidth*risefalltimenpts
		#dutycyclefraction=(pulsewidth+2*risefalltime)/period
		dutycyclefraction=pulsewidth/period

		if dutycyclefraction>0.9: raise ValueError("ERROR! dutycycle > 0.9")
		#if dutycyclefraction<0.01: raise ValueError("ERROR! dutycycle too small")

		#npts=int(period/pulsewidth)+1                           # number of points in a half period (rising or falling ramp)
		nptsq=int(nptsinpulse*int((1.-dutycyclefraction)/dutycyclefraction))         # number of points spent at the quescent voltage, the number of points spent at the pulsed voltage is always 1 (between two points)

		pulsevolt= []
		deltav=int(Nvoltlevels/risefalltimenpts)            # the change in voltage for each step in the rising and falling voltage ramps
		# start with a pulse
		# ramp up to pulsed voltage
		for irf in range(0,risefalltimenpts+1):
			pulsevolt.append(irf*deltav)
			if pulsevolt[-1]>Nvoltlevels: pulsevolt[-1]=Nvoltlevels
		# form pulse
		for ip in range(0,nptsinpulse-2):
			pulsevolt.append(Nvoltlevels)
		# ramp down to quiescent voltage
		for irf in range(0,risefalltimenpts+1):
			pulsevolt.append(Nvoltlevels-irf*deltav)
			if pulsevolt[-1]<0: pulsevolt[-1]=0
		for iq in range(0,nptsq):   # insert pulse voltages at the quescent voltage for the remaining time of the period which is the quescent time of the waveform
			pulsevolt.append(0)

		### set up voltages of the pulse waveform
		if voltagepulse<voltagequescent: # this is a negative-going pulse
			# construct waveform
			self.__pulsegenerator.write("VOLT:LOW "+str(voltagepulse))
			self.__idel()
			self.__pulsegenerator.write("VOLT:HIGH "+str(voltagequescent))
			self.__idel()
			self.__pulsegenerator.write("OUTP:POL INV")
			self.__idel()
		else: # this is a positive-going pulse
			# construct waveform
			self.__pulsegenerator.write("VOLT:LOW "+str(voltagequescent))
			self.__idel()
			self.__pulsegenerator.write("VOLT:HIGH "+str(voltagepulse))
			self.__idel()
			self.__pulsegenerator.write("OUTP:POL NORM")
			self.__idel()
		pulsevoltstr=[str(pv) for pv in pulsevolt]      # convert normalized voltage time point series to string
		# now setup the pulse generator with the ramped waveform
		#self.__pulsegenerator.write("DATA:DEL VOLATILE")
		if len(pulsevolt)>4095: raise ValueError("ERROR! too many points exceeds 4095")
		#time.sleep(5)
		self.__pulsegenerator.write("DATA:DAC VOLATILE,"+",".join(pulsevoltstr))
		time.sleep(5)
		self.__pulsegenerator.write("FUNC:USER VOLATILE")
		self.__idel()
		#time.sleep(5)
		#print(len(pulsevolt))
		#for pv in pulsevolt: print(pv)
		# self.__pulsegenerator.write("SYST:ERR")
		# self.__idel()
		# err=self.__pulsegenerator.read()
		# print(err)
		#self.__pulsegenerator.write("DATA:DAC VOLATILE,8192,8192,0,0")
		self.havesinglepulsedsetup=True
##############################################################################################################
# set invert pulse output
	def invert(self):
		self.__pulsegenerator.write("OUTP:POL INV")
		self.__idel()
##############################################################################################################
# set normal pulse output
	def normal(self):
		self.__pulsegenerator.write("OUTP:POL NORM")
		self.__idel()
##############################################################################################################