# PNA network analyzer driver class and functions for Agilent E8363B
# assumes that a GPIB handle is provided
from writefile_measured import X_writefile_spar, X_writefile_swfactors
from utilities import formatnum, is_number
import time
import numpy as np
settlingtime = 1.0

calset2port="CalSet_2"          # default calset for two-port measurements
calsetS22="CalSet_2"          # default calset for one-port S22 (port #2) measurements
calsetS11="CalSet_3"          # default calset for one-port S11 (port #1) measurements

#instrumentstate_2port="2port_HF.sta"
#instrumentstate_2port="swfHF.sta"
#instrumentstate_2port_time="2port_time.sta"
instrumentstate_S22="S22.sta"
instrumentstate_S11="S11.sta"

class Pna(object):
	def __init__(self, rm=None, navg=1 ):
		try:
			self.__PNA = rm.open_resource('GPIB0::3::INSTR')
			self.__PNA.query_delay=1
			self.__PNA.timeout=5000     # 5 sec timeout
			#print self.__PNA.query("*ID?")
		except:
			print("ERROR on Pna: Could not find the Pna on the GPIB")
			print("Check to make sure that the Pna is on and running the Pna application Stopping Now!")
			quit()
		self.__PNA = rm.open_resource('GPIB0::3::INSTR')
		self._CWfrequency=None
		#self._measurement_type=measurement_type
		self._navg=navg
		# if ports.lower()=="2port":              # then perform 2-port measurement
		# 	self.__pnawrite("SYST:FPR")  # present the Pna
		# 	self.__pnawrite("SYST:UPR")  # actually set the Pna according to the default.csa file
		# 	self.__initdisplayPNA()			# initialize Pna display
		# else:
		self.__pnawrite("SYST:FPR")  # present the Pna
		self.pna_RF_onoff(RFon=False)
		#self.pna_load_instrumentstate(instrumentstatename="2port.sta")

			# self.__pnawrite("SYST:UPR:LOAD \'2port.sta\'")
			# # self.__pnawrite("SYST:UPR")  # actually set the Pna according to the default.csa file
			# # self.__pnawrite("SYST:UPR:LOAD \'2port.sta\'")
			# self.__pnawrite("SYST:UPR")  # actually set the Pna according to the default.csa file
		# self.pna_RF_onoff(RFon=True)
		# self.__PNA.write("INIT:CONT ON")  # turn on data gathering for now
			#self.__initdisplayPNA()			# initialize Pna display
		#self.__PNA.query("*OPC?")


	###########################################################################################################################################################
	# close Pna
	def __del__(self):
		self.__PNA.write("INIT:CONT ON")  # leave data sweeps on
		self.__PNA.close()
	###########################################################################################################################################################
	# set up PNA to measure S-parameters vs time at one frequency
	# NOT READY
	# def setsweepcw(self,frequencyGHz=1.5,sweeptime=None,bandwidth=40000):
	# 	if frequencyGHz not in list(self.get_pna_frequencies()):
	# 		raise ValueError("ERROR! selected frequency is not a calibrated frequency")
	# 	self.__PNA.write("TRIG:SOUR EXT")           # external trigger
	# 	self.__PNA.write("SENS:SWE:TYPE CW")        # set frequency for measurement
	# 	self.__PNA.write("SENS:FREQ:CW "+formatnum(1E9*float(frequencyGHz),precision=2))
	# 	self.__PNA.write("SENS:SWE:TRIG:MODE CHANNEL")
	# 	self.__PNA.write("SENS:SWE:TRIG:POIN OFF")
	# 	self.__PNA.write("SENS:SWE:TIME "+formatnum(sweeptime,precision=2))
	# 	self.__PNA.write("SENS1:BANDWIDTH:RESOLUTION "+formatnum(bandwidth,precision=1,nonexponential=True))            # set IF bandwidth
	# 	self.__PNA.write("SENS1:BANDWIDTH:TRACK 0")                     # do not adjust bandwidth lower at lower frequencies
	# 	self.__PNA.write("SENS1:COUPLE NONE")                     # alternate sweeps measure reflection and transmission on alternate sweeps
	###########################################################################################################################################################
	#
	def getS22_time(self,frequency=1.5E9,sweepfrequency=None,navg=None,instrumentstate="",calset="",numberofpoints=20,ifbandwidth=40E3,offsettime=0.2E-3):
		# set up for externally-triggered gathering of time-domain S-parameters
		# CW frequency in Hz
		sweeptime=1/sweepfrequency
		self.pna_load_instrumentstate(instrumentstate=instrumentstate,calset=calset,type='s22')   # get proper instrument state and calibration kit
		self.pna_RF_onoff(RFon=True)        # make sure PNA RF is on before measuring
		self.__pnawrite("TRIG:PREF:AIGL 1")
		self.__pnawrite("SENSE1:CORR:CSET:ACT \""+calset+"\" ,ON")          # load and apply cal set
		self.__pnawrite("SENS1:SWE:TYPE CW")  # set PNA to CW (time-domain) S-parameter mode
		if frequency!=None: self._CWfrequency=frequency
		if navg!=None: self._navg=navg

		#self.__pnawrite("SOURCE1:POW:LEV "+formatnum(power,precision=1))
		#self.__pnawrite("SOURCE1:POW:LEV:SLOPE:STATE OFF")

		self.__pnawrite("SENS1:FREQ:CW "+formatnum(self._CWfrequency,precision=2))        # set PNA CW frequency in Hz
		self.__pnawrite("SENS1:SWE:MODE CONT")             # set continuous sweep as default
		self.__pnawrite("SENS1:SWE:POIN "+formatnum(numberofpoints,type="int"))           # number of time points
		self.__pnawrite("SENS1:SWE:GEN ANALOG")
		self.__pnawrite("SENS1:BWID "+formatnum(ifbandwidth,precision=1))
		self.__pnawrite("SENS1:BWID:TRAC OFF")
		self.__pnawrite("SENS1:COUP ALL")               # sweep mode set to chopped. We are using only one channel (port)
		#self.__pnawrite("SENS:SWE:GEN STEP")           # set sweep as stepped (for reduced errors)
		self.__pnawrite("SENS1:SWE:TIME "+formatnum(sweeptime,precision=4))

		self.__pnawrite("SENS1:SWE:TRIG:MODE SWEEP")
		self.__pnawrite("TRIG:SOUR EXT")           # external trigger
		self.__pnawrite("CONT:SIGN BNC1,TIEPOSITIVE")
		self.__pnawrite("DISPLAY:WIND1:STAT OFF")
		self.__pnawrite("DISPLAY:WIND1:STAT ON")
		self.__pnawrite("CALC:PAR:DEF:EXT 'S22m','S22'")
		self.__pnawrite("DISP:WIND1:TRAC1:FEED 'S22m'")
		# done with setup now get data
		#self.__pnawrite("INIT:CONT OFF")  # turn off data gathering for now
		self.__pnawrite("SENS:AVER ON")
		self.__pnawrite("SENS:AVER:COUN " + str(self._navg))
		self.__pnawrite("SENS:AVER:CLE")  # clear data buffer and old averages reset averages counter
		#self.__pnawrite("INIT:CONT ON") # gather data
		#self.__pnawrite("SENS:SWE:GEN STEP")           # set sweep as stepped (for reduced errors)
		while int(self.__PNA.query("STAT:OPER:AVER1:COND?")) == 0:  # Measure S-parameters and sweep until all averages are read
			pass
			#print(int(self.__PNA.query("STAT:OPER:AVER1:COND?")))
		self.__pnawrite("INIT:CONT OFF")  # turn off data gathering for now
		#nfreq = int(self.__pnaquery("SENS:SWE:POIN?"))  # get number of frequency points from the Pna setup
		self.__pnawrite("CALC:PAR:SEL 'S22m'")
		self.__pnawrite("FORMAT:DATA ASCII")
		dts = [float(a.strip('\n').strip('"')) for a in self.__pnaquery("CALC:DATA? SDATA").split(',')]  # raw S22 data
		self.s22_timeoneport=[complex(dts[i],dts[i+1]) for i in range(0, len(dts), 2) ]
		# read time points array
		sweeptime=float(self.__PNA.query("SENS1:SWE:TIME?"))
		notimepts=int(self.__PNA.query("SENS1:SWE:POIN?"))
		self.timepts_oneport=np.linspace(start=offsettime, stop=sweeptime+offsettime,num=notimepts)
		self.pna_RF_onoff(RFon=False)   # leave RF port power off after measurements
		return self.timepts_oneport,self.s22_timeoneport
	###########################################################################################################################################################
	# read all four S-parameters vs time
	# 41 points with an IF bandwidth of 40KHz gives a minimum sweep time of 0.98mS
	def getS_2port_time(self,frequency=1.5E9,instrumentstate="",sweeptime='MIN',navg=None,calset=calset2port,numberofpoints=41,ifbandwidth=40E3,offsettime=0.,returnmatrixformat=False):
		# set up for externally-triggered gathering of time-domain S-parameters
		# CW frequency in Hz
		self.pna_load_instrumentstate(instrumentstate=instrumentstate,calset=calset,type='all')   # get proper instrument state and calibration kit
		self.pna_RF_onoff(RFon=True)        # make sure PNA RF is on before measuring
		#self.__pnawrite("TRIG:PREF:AIGL 1")
		self.__pnawrite("SENSE1:SWE:GEN ANAL")            # set sweep to be continuous not stepped
		self.__pnawrite("SENSE1:CORR:INT ON")       # turn on interpolation to allow calset to apply to CW
		#self.__pnawrite("SENSE1:CORR:CSET:ACT \""+calset+"\" ,ON")          # load and apply cal set
		self.__pnawrite("SENS1:SWE:TYPE CW")  # set PNA to CW (time-domain) S-parameter mode
		if frequency!=None: self._CWfrequency=frequency
		if navg!=None: self._navg=navg

		#self.__pnawrite("SOURCE1:POW:LEV "+formatnum(power,precision=1))
		self.__pnawrite("SOURCE1:POW:LEV:SLOPE:STATE OFF")

		self.__pnawrite("SENS1:FREQ:CW "+formatnum(self._CWfrequency,precision=2))        # set PNA CW frequency in Hz
		self.__pnawrite("SENS1:SWE:MODE CONT")             # set continuous sweep as default
		self.__pnawrite("SENS1:SWE:POIN "+formatnum(numberofpoints,type="int"))           # number of time points
		self.__pnawrite("SENS1:SWE:GEN ANALOG")
		self.__pnawrite("SENS1:BWID "+formatnum(ifbandwidth,precision=1))
		self.__pnawrite("SENS1:BWID:TRAC OFF")

		self.__pnawrite("SENS1:COUP NONE")               # sweep mode set to alternate. Each trace (S-parameter) gets its own sweep
		self.__pnawrite("SENS1:COUP:PAR:STAT on")

		if is_number(str(sweeptime)): self.__pnawrite("SENS1:SWE:TIME "+formatnum(sweeptime,precision=4))
		else: self.__pnawrite("SENS1:SWE:TIME "+sweeptime)

		self.__pnawrite("SENS1:SWE:TRIG:MODE SWEEP")
		self.__pnawrite("TRIG:SOUR EXT")           # external trigger
		self.__pnawrite("CONT:SIGN BNC1,TIEPOSITIVE")   # external trigger on positive edge and into the BNC connector in back
		# autoscale
		self.__pnawrite("DISP:WIND1:TRAC1:Y:AUTO")
		self.__pnawrite("DISP:WIND2:TRAC2:Y:AUTO")
		self.__pnawrite("DISP:WIND3:TRAC3:Y:AUTO")
		self.__pnawrite("DISP:WIND4:TRAC4:Y:AUTO")
		# trigger delay
		#if triggerdelay>=0.: self.__pnawrite("TRIG:DEL "+formatnum(triggerdelay,precision=7,nonexponential=True))
		#####
		# done with setup now get data
		self.__pnawrite("SENS:AVER ON")
		self.__pnawrite("SENS:AVER:COUN " + str(self._navg))
		self.__pnawrite("SENS:AVER:CLE")  # clear data buffer and old averages reset averages counter

		while int(self.__PNA.query("STAT:OPER:AVER1:COND?")) == 0: pass # Measure S-parameters and sweep until all averages are read

		# autoscale
		self.__pnawrite("DISP:WIND1:TRAC1:Y:AUTO")
		self.__pnawrite("DISP:WIND2:TRAC2:Y:AUTO")
		self.__pnawrite("DISP:WIND3:TRAC3:Y:AUTO")
		self.__pnawrite("DISP:WIND4:TRAC4:Y:AUTO")
		#####
		self.__pnawrite("INIT:CONT OFF")  # turn off data gathering to read data
		# get S11
		self.__pnawrite("CALC:PAR:SEL 'S11m'")
		self.__pnawrite("FORMAT:DATA ASCII")
		dts = [float(a.strip('\n').strip('"')) for a in self.__pnaquery("CALC:DATA? SDATA").split(',')]  # raw S11 data
		s11=[complex(dts[i],dts[i+1]) for i in range(0, len(dts), 2) ]

		# get S21
		self.__pnawrite("CALC:PAR:SEL 'S21m'")
		self.__pnawrite("FORMAT:DATA ASCII")
		dts = [float(a.strip('\n').strip('"')) for a in self.__pnaquery("CALC:DATA? SDATA").split(',')]  # raw S21 data
		s21=[complex(dts[i],dts[i+1]) for i in range(0, len(dts), 2) ]

		# get S12
		self.__pnawrite("CALC:PAR:SEL 'S12m'")
		self.__pnawrite("FORMAT:DATA ASCII")
		dts = [float(a.strip('\n').strip('"')) for a in self.__pnaquery("CALC:DATA? SDATA").split(',')]  # raw S12 data
		s12=[complex(dts[i],dts[i+1]) for i in range(0, len(dts), 2) ]

		# get S22
		self.__pnawrite("CALC:PAR:SEL 'S22m'")
		self.__pnawrite("FORMAT:DATA ASCII")
		dts = [float(a.strip('\n').strip('"')) for a in self.__pnaquery("CALC:DATA? SDATA").split(',')]  # raw S22 data
		s22=[complex(dts[i],dts[i+1]) for i in range(0, len(dts), 2) ]

		# read time points array
		actualsweeptime=float(self.__pnaquery("SENS1:SWE:TIME?"))       #actual sweep time
		notimepts=int(self.__pnaquery("SENS1:SWE:POIN?"))
		timepts=np.linspace(start=offsettime, stop=actualsweeptime+offsettime,num=notimepts)
		if len(timepts) != len(s11): raise ValueError("INTERNAL ERROR! the length of the S-parameter array does not match that of the timestamps")           # sanity check for bugs
		self.pna_RF_onoff(RFon=False)   # leave RF port power off after measurements
		if not returnmatrixformat: return actualsweeptime,timepts,s11,s21,s12,s22
		else: # put S-parameters in format: S[timestampindex][2x2 matrix]
			S=[[[s11[i],s12[i]],[s21[i],s22[i]]] for i in range(0,len(s11))]
			return actualsweeptime,timepts,S
	###########################################################################################################################################################
	# get all four S-parameters using Pna
	# assumes that the Pna is set up with the correct parameters and calibrated
	def pna_getS_2port(self, instrumentstate="",navg=16,calset=""):
		# get instrument state: Note that this assumes that the PNA has been properly set up for the 2-port measurement
		self.pna_load_instrumentstate(instrumentstate=instrumentstate,calset=calset,type='all')
		self.pna_RF_onoff(RFon=True)        # make sure PNA RF is on before measuring
		self.__PNA.query("*OPC?")  # allow Pna to catch up and clear its instruction queue
		self.__PNA.write("INIT:CONT OFF")  # turn off data gathering for now
		# turn on data averaging
		self.__PNA.write("SENS:AVER ON")
		self.__PNA.write("SENS:AVER:COUN " + str(navg))
		self.__PNA.write("SENS:AVER:CLE")  # clear data buffer and old averages reset averages counter
		self.__PNA.query("*OPC?")
		self.__PNA.write("INIT:CONT ON")
		self.__PNA.query("*OPC?")  # allow Pna to catch up and clear its instruction queue
		self.__PNA.write("SENS:SWE:GEN STEP")           # set sweep as stepped (for reduced errors)
		self.__PNA.query("*OPC?")  # allow Pna to catch up and clear its instruction queue
		while int(self.__PNA.query("STAT:OPER:AVER1:COND?")) == 0:  # Measure S-parameters and sweep until all averages are read
			continue
		self.__PNA.query("*OPC?")  # allow Pna to catch up and clear its instruction queue
		self.__PNA.write("INIT:CONT OFF")  # done gathering data so stop sweep
		self.__PNA.query("*OPC?")  # allow Pna to catch up and clear its instruction queue

		nfreq = int(self.__PNA.query("SENS:SWE:POIN?"))  # get number of frequency points from the Pna setup
		#print "number of frequency points ", nfreq  # debug
		# read S11 from the Pna
		self.__PNA.write("CALC:PAR:SEL 'S11m'")
		self.__PNA.write("FORMAT:DATA ASCII")
		self.__PNA.query("*OPC?")
		dts = [float(a.strip('\n').strip('"')) for a in self.__PNA.query("CALC:DATA? SDATA").split(',')]  # raw S-parameter data
		self.s11 = []
		for ifr in range(0, len(dts), 2):  # convert S11 data format to a complex number array
			self.s11.append(complex(dts[ifr], dts[ifr+1]))
		#print "here are S11 data", self.s11  # debug

		# read S21 from the Pna
		self.__PNA.write("CALC:PAR:SEL 'S21m'")
		self.__PNA.write("FORMAT:DATA ASCII")
		self.__PNA.query("*OPC?")
		dts = [float(a.strip('\n').strip('"')) for a in self.__PNA.query("CALC:DATA? SDATA").split(',')]  # raw S-parameter data
		self.s21 = []
		for ifr in range(0, len(dts), 2):  # convert S21 data format to a complex number array
			self.s21.append(complex(dts[ifr], dts[ifr+1]))
		#print "here are S21 data", self.s21  # debug

		# read S12 from the Pna
		self.__PNA.write("CALC:PAR:SEL 'S12m'")
		self.__PNA.write("FORMAT:DATA ASCII")
		self.__PNA.query("*OPC?")
		dts = [float(a.strip('\n').strip('"')) for a in self.__PNA.query("CALC:DATA? SDATA").split(',')]  # raw S-parameter data
		self.s12 = []
		for ifr in range(0,len(dts),2):  # convert S12 data format to a complex number array
			self.s12.append(complex(dts[ifr], dts[ifr+1]))
		#print "here are S12 data", self.s12  # debug

		# read S22 from the Pna
		self.__PNA.write("CALC:PAR:SEL 'S22m'")
		self.__PNA.write("FORMAT:DATA ASCII")
		self.__PNA.query("*OPC?")
		dts = [float(a.strip('\n').strip('"')) for a in self.__PNA.query("CALC:DATA? SDATA").split(',')]  # raw S-parameter data
		self.s22 = []
		for ifr in range(0, len(dts), 2):  # convert S12 data format to a complex number array
			self.s22.append(complex(dts[ifr],dts[ifr + 1]))
		#print "here are S22 data", self.s22

		#################### now have S-parameters
		# read frequency points array
		self.freqstart = float(self.__PNA.query("SENS:FREQ:STAR?").strip('\n'))
		self.freqstop = float(self.__PNA.query("SENS:FREQ:STOP?").strip('\n'))
		self.__PNA.query("*OPC?")
		if nfreq > 1:
			self.freqstep = (self.freqstop - self.freqstart) / (nfreq - 1)
		else:
			self.freqstep = 0
		self.freq = []
		for ifr in range(0, nfreq):
			self.freq.append(self.freqstart + ifr * self.freqstep)
		## turn Pna sweep back on
		self.__PNA.write("SENS:AVER ON")
		self.__PNA.write("SENS:AVER:COUN " + str(navg))
		self.__PNA.write("SENS:AVER:CLE")  # clear data buffer and old averages reset averages counter
		self.__PNA.query("*OPC?")
		self.__PNA.write("INIT:CONT ON")  # turn sweep back on
		self.__PNA.query("*OPC?")
		self.pna_RF_onoff(RFon=False)   # leave RF port power off after measurements
		frequenciesMHz=[1E-6*f for f in self.freq]       # get frequencies in MHz NOTE: NOT rounded to nearest MHz
		return {'frequenciesMHz':frequenciesMHz,'S11':self.s11,'S12':self.s12,'S21':self.s21,'S22':self.s22}
	#######################################################################################################################################################################

	#######################################################################################################################################################################
	# get S22 one-port from PNA
	def pna_get_S_oneport(self,navg=16,instrumentstate="",calset="",type="s22"):
		self.pna_load_instrumentstate(instrumentstate=instrumentstate,calset=calset,type=type)
		self.pna_RF_onoff(RFon=True)                # turn on PNA RF port power
		self.__pnawrite("INIT:CONT OFF")  # turn off data gathering for now
		# turn on data averaging
		self.__pnawrite("SENS1:AVER ON")
		self.__pnawrite("SENS1:AVER:COUN " + str(navg))
		self.__pnawrite("SENS1:AVER:CLE")  # clear data buffer and old averages reset averages counter
		self.__pnawrite("INIT:CONT ON")
		while int(self.__pnaquery("STAT:OPER:AVER1:COND?")) == 0:  # Measure S-parameters and sweep until all averages are read
			continue
		self.__pnawrite("INIT:CONT OFF")  # done gathering data so stop sweep

		nfreq = int(self.__pnaquery("SENS1:SWE:POIN?"))  # get number of frequency points from the Pna setup

		self.s11_oneport = []
		self.s22_oneport = []
		if type.lower()=='s11':
			self.__pnawrite("CALC:PAR:SEL 'S11m'")      # read S11 from the Pna
			testdata=self.__pnaquery("CALC:DATA? SDATA").split(',')
			dts = [float(a.strip('\n').strip('"')) for a in self.__pnaquery("CALC:DATA? SDATA").split(',')]  # raw S-parameter data
			for ifr in range(0, len(dts), 2):  # convert S22 data format to a complex number array
				self.s11_oneport.append(complex(dts[ifr], dts[ifr+1]))
		if type.lower()=='s22':
			self.__pnawrite("CALC:PAR:SEL 'S22m'")      # read S22 from the Pna
			dts = [float(a.strip('\n').strip('"')) for a in self.__pnaquery("CALC:DATA? SDATA").split(',')]  # raw S-parameter data
			for ifr in range(0, len(dts), 2):  # convert S22 data format to a complex number array
				self.s22_oneport.append(complex(dts[ifr], dts[ifr+1]))
	#################### now have S-parameters
		###############
		# Next, read frequency points array
		self.freqstart = float(self.__pnaquery("SENS1:FREQ:STAR?").strip('\n'))
		self.freqstop = float(self.__pnaquery("SENS1:FREQ:STOP?").strip('\n'))
		if nfreq > 1:
			self.freqstep = (self.freqstop - self.freqstart) / (nfreq - 1)
		else:
			self.freqstep = 0
		self.freq = []
		for ifr in range(0, nfreq):
			self.freq.append(self.freqstart + ifr * self.freqstep)
		## turn Pna sweep back on
		self.__pnawrite("SENS1:AVER ON")
		self.__pnawrite("SENS1:AVER:COUN " + str(navg))
		self.__pnawrite("SENS1:AVER:CLE")  # clear data buffer and old averages reset averages counter
		self.__pnawrite("INIT:CONT ON")  # turn sweep back on
		self.pna_RF_onoff(RFon=False)                # leave PNA RF port power off
		frequenciesMHz=[1E-6*f for f in self.freq]       # get frequencies in MHz NOT rounded
		return {'frequenciesMHz':frequenciesMHz,'gamma':self.s22_oneport}         # reflection coefficient in real+jimaginary format
	###################################################################################################################################################################
	# set up Pna front panel display (used during Pna setup only)
	# get a list of all enabled traces so we can disable them, then enable only one ones we want
	def __initdisplayPNA(self,type='all'):
		wind= self.__pnaquery("DISP:CAT?").split("\"")[1].split(",")
		for w in wind:
			trc = self.__pnaquery("DISP:WIND"+w+":CAT?").split("\"")[1].split(",")
			# disable all traces so we can later assign traces to measurements without conflict
			for t in trc:
				#    print "DISP:WIND1:TRAC"+trc[ii].strip('\n').strip('"')+":DEL"          #debug
				self.__pnawrite("DISP:WIND"+w+":TRAC"+t+":DEL")  # disable displays to avoid assigning conflicts later
		self.__pnawrite("CALC:PAR:DEL:ALL")
		if type.lower()=='all' and self._CWfrequency==None:
			# display all S-parameters on Pna, one per window
			self.__pnawrite("CALC:PAR:DEF 'S11m',S11")
			self.__pnawrite("CALC:PAR:DEF 'S21m',S21")
			self.__pnawrite("CALC:PAR:DEF 'S12m',S12")
			self.__pnawrite("CALC:PAR:DEF 'S22m',S22")
			#self.__PNA.query("*OPC?")

			# turn on windows to display each S-parameter in a different window
			# self.__pnawrite("DISP:WIND2:STAT ON")
			# self.__pnawrite("DISP:WIND3:STAT ON")
			# self.__pnawrite("DISP:WIND4:STAT ON")
			# self.__PNA.query("*OPC?")
			#
			self.__pnawrite("DISP:WIND1:TRAC1:FEED 'S11m'")
			self.__pnawrite("DISP:WIND2:TRAC2:FEED 'S21m'")
			self.__pnawrite("DISP:WIND3:TRAC3:FEED 'S12m'")
			self.__pnawrite("DISP:WIND4:TRAC4:FEED 'S22m'")
			#self.__PNA.query("*OPC?")

			self.__pnawrite("INIT:CONT ON")  # turn on data gathering for now
			# turn on data averaging
			self.__pnawrite("SENS:AVER ON")
			self.__pnawrite("SENS:AVER:COUN " + str(self._navg))
		elif type.lower()=="s11_only" or type.lower()=="s11":            # then we measured only s11
			self.__pnawrite("CALC:PAR:DEF 'S11m',S11")
			self.__pnawrite("DISP:WIND1:STAT OFF")
			self.__pnawrite("DISP:WIND1:STAT ON")
			self.__pnawrite("DISP:WIND1:SIZE MAX")
			self.__pnawrite("DISP:WIND1:TRAC1:FEED 'S11m'")
			self.__pnawrite("CALC:FORM1 SMITH")
			self.__PNA.query("*OPC?")
			self.__pnawrite("INIT:CONT ON")  # turn on data gathering for now
			# turn on data averaging
			self.__pnawrite("SENS1:AVER ON")
			self.__pnawrite("SENS1:AVER:COUN " + str(self._navg))

		elif type.lower()=="s22_only" or type.lower()=="s22":            # then we measured only s11
			self.__pnawrite("CALC:PAR:DEF 'S22m',S22")
			self.__pnawrite("DISP:WIND1:STAT OFF")
			self.__pnawrite("DISP:WIND1:STAT ON")
			self.__pnawrite("DISP:WIND1:SIZE MAX")
			self.__pnawrite("DISP:WIND1:TRAC1:FEED 'S22m'")
			self.__pnawrite("CALC:FORM1 SMITH")
			self.__PNA.query("*OPC?")
			self.__pnawrite("INIT:CONT ON")  # turn on data gathering for now
			# turn on data averaging
			self.__pnawrite("SENS1:AVER ON")
			self.__pnawrite("SENS1:AVER:COUN " + str(self._navg))

		else: raise ValueError("ERROR! No valid measurement type specified")
	###################################################################################################################################################################
	###################################################################################################################################################################
	# set up Pna to measure switching factors b1/a1 and b2/a2
	# assumes that the PNA sweep is set up with number of points, frequency range, and power from the saved instrumentstate
	def getswitchtermsPNA(self,average=16,instrumentstatefilename=None):
		if instrumentstatefilename==None:
			print("ERROR! no instrument state file specified!")
			quit(1)
		insts="\""+instrumentstatefilename+"\""
		self.__pnawrite("SYST:UPR:LOAD "+insts)       # load instrument state
		self.__pnawrite("SYST:UPR")
		self.pna_RF_onoff(RFon=True)


		if average!=None and average>0:
			self._navg=average
		wind= self.__pnaquery("DISP:CAT?").split("\"")[1].split(",")
		for w in wind:
			trc = self.__pnaquery("DISP:WIND"+w+":CAT?").split("\"")[1].split(",")
			# disable all traces so we can later assign traces to measurements without conflict
			for t in trc:
				#    print "DISP:WIND1:TRAC"+trc[ii].strip('\n').strip('"')+":DEL"          #debug
				self.__pnawrite("DISP:WIND"+w+":TRAC"+t+":DEL")  # disable displays to avoid assigning conflicts later
				self.__pnawrite("DISP:WIND"+w+" OFF")
		self.__pnawrite("CALC:PAR:DEL:ALL")
		self.__pnawrite("DISP:WIND1:STAT ON")
		#self.__pnawrite("DISP:WIND1:SIZE MAX")
		self.__pnawrite("DISP:WIND2:STAT ON")
		#self.__pnawrite("DISP:WIND2:SIZE MAX")
		# display all S-parameters on Pna, one per window
		self.__pnawrite("CALC:PAR:DEF:EXT 'SWTa2/b2','a2/b2,1'")      # define switch term a2/b2
		self.__pnawrite("CALC:PAR:DEF:EXT 'SWTa1/b1','a1/b1,2'")      # define switch term a1/b1)
		self.__pnawrite("DISP:WIND1:TRAC1:FEED 'SWTa1/b1'")     # display switch term a1/b1
		self.__pnawrite("DISP:WIND2:TRAC2:FEED 'SWTa2/b2'")     # display switch term a2/b2

		self.__pnawrite("INIT:CONT OFF")  # turn on data gathering for now
		self.__pnawrite("SENS:SWE:GEN STEP")           # set sweep as stepped (for reduced errors)
		# turn on data averaging
		self.__pnawrite("SENS1:AVER ON")
		self.__pnawrite("SENS1:AVER:COUN " + str(self._navg))
		self.__pnawrite("SENS1:AVER:CLE")  # clear data buffer and old averages reset averages counter
		self.__pnawrite("INIT:CONT ON")
		#loopend=int(self.__pnaquery("STAT:OPER:AVER1:COND?"))
		# while loopend ==0 :  # Measure S-parameters and sweep until all averages are read
		# 	loopend=int(self.__pnaquery("STAT:OPER:AVER1:COND?"))
		# 	print(loopend)
		# 	continue
		while int(self.__pnaquery("STAT:OPER:AVER1:COND?")) !=6: continue
		# #time.sleep(1)
		# while int(self.__pnaquery("STAT:OPER:AVER:COND?")) == 0:  # Measure S-parameters and sweep until all averages are read
		# 	continue
		self.__pnawrite("INIT:CONT OFF")  # done gathering data so stop sweep
		# read frequency points array
		nfreq = int(self.__pnaquery("SENS:SWE:POIN?"))  # get number of frequency points from the Pna setup
		self.swt_a1overb1=[]
		self.swt_a2overb2=[]
	# now read switching factors
		self.__pnawrite("CALC:PAR:SEL 'SWTa1/b1'")      # read switching parameter
		self.__pnawrite("FORMAT:DATA ASCII")
		dts1 = [float(a.strip('\n').strip('"')) for a in self.__pnaquery("CALC:DATA? SDATA").split(',')]  # raw switching factor data
		for ifr in range(0, len(dts1), 2):  # convert switch factor data format to a complex number array
			self.swt_a1overb1.append(complex(dts1[ifr], dts1[ifr+1]))

		self.__pnawrite("CALC:PAR:SEL 'SWTa2/b2'")      # read switching parameter
		self.__pnawrite("FORMAT:DATA ASCII")
		dts2 = [float(a.strip('\n').strip('"')) for a in self.__pnaquery("CALC:DATA? SDATA").split(',')]  # raw switching factor data
		for ifr in range(0, len(dts2), 2):  # convert switch factor data format to a complex number array
			self.swt_a2overb2.append(complex(dts2[ifr], dts2[ifr+1]))
		#################### now have switching factors
		# read frequency points array ###########
		self.freqstart = float(self.__PNA.query("SENS:FREQ:STAR?").strip('\n'))
		self.freqstop = float(self.__PNA.query("SENS:FREQ:STOP?").strip('\n'))
		self.__PNA.query("*OPC?")
		if nfreq > 1:
			self.freqstep = (self.freqstop - self.freqstart) / (nfreq - 1)
		else:
			self.freqstep = 0
		self.freq = []
		for ifr in range(0, nfreq):
			self.freq.append(self.freqstart + ifr * self.freqstep)
		###############
		self.pna_RF_onoff(RFon=False)   # leave RF port power off after measurements
		return

	###################################################################################################################################################################
	# set active calibration set
	def pna_set_calset(self,calsetname=calset2port):
		cals="\""+calsetname+"\""
		self.__PNA.write("SENS:CORR:CSET:ACT "+cals+",1")
		#self.__PNA.query("*OPC?")
		calset=self.__PNA.query("SENS:CORR:CSET:ACT?")
		return calset
	###################################################################################################################################################################
	###################################################################################################################################################################
	# set active calibration set
	#
	def pna_load_instrumentstate(self,instrumentstate="",calset="",type="all"):
		insts="\""+instrumentstate+"\""
		if instrumentstate==None or instrumentstate=="": ValueError("ERROR! no instrument state specified")
		self.__pnawrite("SYST:UPR:LOAD "+insts)     # load specified instrument state
		self.__pnawrite("SYST:UPR")
		self.__PNA.query("*OPC?")
		self.__initdisplayPNA(type=type)			# initialize Pna display
		# if (calsetname==calsetS11) or (calset==calsetS22) or (calsetname==calset2port):
		if calset!="" and calset!=None:
			cals="\""+calset+"\""
			self.__pnawrite("SENS:CORR:CSET:ACT "+cals+",1")
		else:
			self.__pnawrite("SENS:CORR:STAT:OFF")       # no cal kit supplied so turn off correction
		#else: raise ValueError("ERROR from line 459 in pna.py: No valid calsetname given")
		self.pna_RF_onoff(RFon=False)           # leave RF power off
		return
	###################################################################################################################################################################
	# turn RF power on and off
	def pna_RF_onoff(self,RFon=True):
		if RFon==True:
			self.__PNA.write("OUTPUT:STATE ON")
			self.__PNA.query("*OPC?")
		else:
			self.__PNA.write("OUTPUT:STATE OFF")
			self.__PNA.query("*OPC?")
		time.sleep(settlingtime)
	###################################################################################################################################################################
	# get swept frequency array
	def get_pna_frequencies(self):
		# Read frequency points array
		nfreq = int(self.__PNA.query("SENS1:SWE:POIN?"))  # get number of frequency points from the Pna setup
		self.freqstart = float(self.__PNA.query("SENS1:FREQ:STAR?").strip('\n'))
		self.freqstop = float(self.__PNA.query("SENS1:FREQ:STOP?").strip('\n'))
		self.__PNA.query("*OPC?")
		if nfreq > 1: self.freqstep = (self.freqstop - self.freqstart) / (nfreq - 1)
		else: self.freqstep = 0
		self.freq = np.linspace(self.freqstart,self.freqstop,nfreq)
		return self.freq
	###################################################################################################################################################################
	# get maximum number of points for CW time sweep which is just less than the sweep period. Assumes a 2-port S-parameter CW sweep
	# RFfrequency is in Hz
	def get_max_npts(self,nptsguess=2,sweepperiod=1E-3,RFfrequency=1.5E9,ifbandwidth=40E3,instrumentstate="",calset=""):
		self.pna_load_instrumentstate(instrumentstate=instrumentstate,calset=calset,type='all')   # get proper instrument state
		self.pna_RF_onoff(RFon=False)        # turn off PNA RF power since it's not needed here
		self.__pnawrite("SENSE1:SWE:GEN ANAL")            # set sweep to be continuous not stepped
		self.__pnawrite("SENSE1:CORR:INT ON")       # turn on interpolation to allow calset to apply to CW
		#self.__pnawrite("SENSE1:CORR:CSET:ACT \""+calset+"\" ,ON")          # load and apply cal set
		self.__pnawrite("SENS1:SWE:TYPE CW")  # set PNA to CW (time-domain) S-parameter mode
		self.__pnawrite("SOURCE1:POW:LEV:SLOPE:STATE OFF")

		self.__pnawrite("SENS1:FREQ:CW "+formatnum(RFfrequency,precision=2))        # set PNA CW frequency in Hz
		self.__pnawrite("SENS1:SWE:MODE CONT")             # set continuous sweep as default
		self.__pnawrite("SENS1:SWE:GEN ANALOG")
		self.__pnawrite("SENS1:BWID "+formatnum(ifbandwidth,precision=1))
		self.__pnawrite("SENS1:BWID:TRAC OFF")

		self.__pnawrite("SENS1:COUP NONE")               # sweep mode set to alternate. Each trace (S-parameter) gets its own sweep
		self.__pnawrite("SENS1:COUP:PAR:STAT on")
		self.__pnawrite("SENS1:SWE:TIME MIN")           # set the minimum sweep time

		self.__pnawrite("SENS1:SWE:TRIG:MODE SWEEP")
		self.__pnawrite("TRIG:SOUR IMM")           # internal trigger
		self.__pnawrite("SENS1:AVER OFF")            # turn off averaging since no measurements are done here
		self.__pnawrite("SENS1:SWE:POIN "+formatnum(nptsguess,type="int"))           # initial number of time points to try
		actualsweeptime=float(self.__pnaquery("SENS1:SWE:TIME?"))       #actual sweep time

		# increase number of time points until the actual sweep time is just barely less than the sweepperiod
		while(actualsweeptime<sweepperiod):
			nptsguess+=1
			self.__pnawrite("SENS1:SWE:POIN "+formatnum(nptsguess,type="int"))  # try
			self.__pnawrite("SENS1:SWE:TIME MIN")           # set the minimum sweep time
			actualsweeptime=float(self.__pnaquery("SENS1:SWE:TIME?"))       #actual sweep time
			print("number of points = ",nptsguess," sweep time = ",actualsweeptime)
		# back off one point to get actualsweeptime just under sweepperiod
		nptsguess-=1
		self.__pnawrite("SENS1:SWE:POIN "+formatnum(nptsguess,type="int"))  # try
		self.__pnawrite("SENS1:SWE:TIME MIN")           # set the minimum sweep time
		actualsweeptime=float(self.__pnaquery("SENS1:SWE:TIME?"))       #actual sweep time
		print("number of points = ",nptsguess," sweep time = ",actualsweeptime)
		return(nptsguess,actualsweeptime)
	###################################################################################################################################################################
	def __pnawrite(self,instruct=""):
		self.__PNA.write(instruct)
		while int(self.__PNA.query("*OPC?").strip())==0: pass
		#time.sleep(.5)

	def __pnaquery(self,instruct=""):
		ret=self.__PNA.query(instruct)
		while int(self.__PNA.query("*OPC?").strip())==0: pass
		#time.sleep(.5)
		return ret
	#######################################################################################################################################################################











	writefile_spar = X_writefile_spar						# method to write S-parameters to file
	writefile_swfactors = X_writefile_swfactors             # method to write pna's switch factors to files. Used for TRL calibrations

