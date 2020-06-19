# PNA network analyzer driver class and functions for Agilent E8363B
# assumes that a GPIB handle is provided
from writefile_measured import X_writefile_spar
import time
import numpy as np
import socket as sock           # we will be bypassing PyVISA for LAN since the 4200SCS does not using a VISA-compatible protocol
import visa
settlingtime = 1.0

class Pna:
	def __init__(self, rm=None, navg=16,measurement_type='all'):
		# self.__largechunk = 550000000  # for large data reads and writes
		# self.__midchunk = 10000000  # for small data reads and writes
		# self.__smallchunk = 500  # for very small data writes and reads
		# self.__readsize = self.__smallchunk
		try:
			# self.__term = '\0'
			# self.__query_delay = 0.5  # set up query delay to prevent errors
			# self.__parameteranalyzer = sock.socket(sock.AF_INET, sock.SOCK_STREAM)  # LAN
			# self.__parameteranalyzer.connect(("192.168.1.12", 1225))  # connect to the 4200SCS
			#self.__PNA = rm.open_resource('GPIB0::3::INSTR')
			self.__PNA = rm.open_resource('TCPIP0::192.168.1.15::inst0::INSTR')
			# opt = self.__query(cmd="*OPT?")
			# print(opt)
		except:
			print("ERROR on Pna: Could not find the Pna on the GPIB")
			print("Check to make sure that the Pna is on and running the Pna application Stopping Now!")
			quit()
		self.__PNA.write("SYST:FPR")  # present the Pna
		# load the Pna's calibration and settings
		self.__PNA.write("SYST:UPR:LOAD 'default.csa'")  # this file contains the instrument settings and calibration. It's default location, on the Pna, is C:\Program Files\Agilent\Network Analyzer\Documents\default.csa
		self.__PNA.query("*OPC?")       # added July 8, 2017
		self.__PNA.write("SYST:UPR")  # actually set the Pna according to the default.csa file
		self.__PNA.query("*OPC?")
		self.__PNA.write("INIT:CONT ON")  # turn on data gathering for now
		self.__initdisplayPNA(navg=navg,measurement_type=measurement_type)			# initialize Pna display
	###########################################################################################################################################################
	# close Pna
	def __del__(self):
		self.__PNA.write("INIT:CONT ON")  # leave data sweeps on
		self.__PNA.close()
	###########################################################################################################################################################
	# get all four S-parameters using Pna
	# assumes that the Pna is set up with the correct parameters and calibrated
	def pna_getS(self, navg=16):
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
	#######################################################################################################################################################################
	# get S11 one-port from PNA
	def pna_getS11(self,navg=16):
		self.__PNA.query("*OPC?")  # allow Pna to catch up and clear its instruction queue
		self.__PNA.write("INIT:CONT OFF")  # turn off data gathering for now
		# turn on data averaging
		self.__PNA.write("SENS1:AVER ON")
		self.__PNA.write("SENS1:AVER:COUN " + str(navg))
		self.__PNA.write("SENS1:AVER:CLE")  # clear data buffer and old averages reset averages counter
		self.__PNA.query("*OPC?")
		self.__PNA.write("INIT:CONT ON")
		self.__PNA.query("*OPC?")  # allow Pna to catch up and clear its instruction queue
		while int(self.__PNA.query("STAT:OPER:AVER1:COND?")) == 0:  # Measure S-parameters and sweep until all averages are read
			continue
		self.__PNA.query("*OPC?")  # allow Pna to catch up and clear its instruction queue
		self.__PNA.write("INIT:CONT OFF")  # done gathering data so stop sweep
		self.__PNA.query("*OPC?")  # allow Pna to catch up and clear its instruction queue

		nfreq = int(self.__PNA.query("SENS1:SWE:POIN?"))  # get number of frequency points from the Pna setup
		#print "number of frequency points ", nfreq  # debug
		# read S11 from the Pna
		self.__PNA.write("CALC:PAR:SEL 'S11m'")
		self.__PNA.write("FORMAT:DATA ASCII")
		self.__PNA.query("*OPC?")
		dts = [float(a.strip('\n').strip('"')) for a in self.__PNA.query("CALC:DATA? SDATA").split(',')]  # raw S-parameter data
		self.s11 = []
		for ifr in range(0, len(dts), 2):  # convert S11 data format to a complex number array
			self.s11.append(complex(dts[ifr], dts[ifr+1]))
	#################### now have S-parameters
		###############
		# Next, read frequency points array
		self.freqstart = float(self.__PNA.query("SENS1:FREQ:STAR?").strip('\n'))
		self.freqstop = float(self.__PNA.query("SENS1:FREQ:STOP?").strip('\n'))
		self.__PNA.query("*OPC?")
		if nfreq > 1:
			self.freqstep = (self.freqstop - self.freqstart) / (nfreq - 1)
		else:
			self.freqstep = 0
		self.freq = []
		for ifr in range(0, nfreq):
			self.freq.append(self.freqstart + ifr * self.freqstep)
		## turn Pna sweep back on
		self.__PNA.write("SENS1:AVER ON")
		self.__PNA.write("SENS1:AVER:COUN " + str(navg))
		self.__PNA.write("SENS1:AVER:CLE")  # clear data buffer and old averages reset averages counter
		self.__PNA.query("*OPC?")
		self.__PNA.write("INIT:CONT ON")  # turn sweep back on
		self.__PNA.query("*OPC?")
	###################################################################################################################################################################
	#######################################################################################################################################################################
	# get S22 one-port from PNA
	def pna_getS22(self,navg=16):
		self.__PNA.query("*OPC?")  # allow Pna to catch up and clear its instruction queue
		self.__PNA.write("INIT:CONT OFF")  # turn off data gathering for now
		# turn on data averaging
		self.__PNA.write("SENS1:AVER ON")
		self.__PNA.write("SENS1:AVER:COUN " + str(navg))
		self.__PNA.write("SENS1:AVER:CLE")  # clear data buffer and old averages reset averages counter
		self.__PNA.query("*OPC?")
		self.__PNA.write("INIT:CONT ON")
		self.__PNA.query("*OPC?")  # allow Pna to catch up and clear its instruction queue
		while int(self.__PNA.query("STAT:OPER:AVER1:COND?")) == 0:  # Measure S-parameters and sweep until all averages are read
			continue
		self.__PNA.query("*OPC?")  # allow Pna to catch up and clear its instruction queue
		self.__PNA.write("INIT:CONT OFF")  # done gathering data so stop sweep
		self.__PNA.query("*OPC?")  # allow Pna to catch up and clear its instruction queue

		nfreq = int(self.__PNA.query("SENS1:SWE:POIN?"))  # get number of frequency points from the Pna setup
		#print "number of frequency points ", nfreq  # debug
		# read S22 from the Pna
		self.__PNA.write("CALC:PAR:SEL 'S22m'")
		self.__PNA.write("FORMAT:DATA ASCII")
		self.__PNA.query("*OPC?")
		dts = [float(a.strip('\n').strip('"')) for a in self.__PNA.query("CALC:DATA? SDATA").split(',')]  # raw S-parameter data
		self.s22 = []
		for ifr in range(0, len(dts), 2):  # convert S22 data format to a complex number array
			self.s22.append(complex(dts[ifr], dts[ifr+1]))
	#################### now have S-parameters
		###############
		# Next, read frequency points array
		self.freqstart = float(self.__PNA.query("SENS1:FREQ:STAR?").strip('\n'))
		self.freqstop = float(self.__PNA.query("SENS1:FREQ:STOP?").strip('\n'))
		self.__PNA.query("*OPC?")
		if nfreq > 1:
			self.freqstep = (self.freqstop - self.freqstart) / (nfreq - 1)
		else:
			self.freqstep = 0
		self.freq = []
		for ifr in range(0, nfreq):
			self.freq.append(self.freqstart + ifr * self.freqstep)
		## turn Pna sweep back on
		self.__PNA.write("SENS1:AVER ON")
		self.__PNA.write("SENS1:AVER:COUN " + str(navg))
		self.__PNA.write("SENS1:AVER:CLE")  # clear data buffer and old averages reset averages counter
		self.__PNA.query("*OPC?")
		self.__PNA.write("INIT:CONT ON")  # turn sweep back on
		self.__PNA.query("*OPC?")
	###################################################################################################################################################################
	# set up Pna front panel display (used during Pna setup only)
	# get a list of all enabled traces so we can disable them, then enable only one ones we want
	def __initdisplayPNA(self,navg=16,measurement_type='all'):
		trc = self.__PNA.query("DISP:WIND1:CAT?").split(",")
		# disable all traces so we can later assign traces to measurements without conflict
		for ii in range(0, len(trc)):
			#    print "DISP:WIND1:TRAC"+trc[ii].strip('\n').strip('"')+":DEL"          #debug
			self.__PNA.write("DISP:WIND1:TRAC" + trc[ii].strip('\n').strip('"') + ":DEL")  # disable displays to avoid assigning conflicts later
		if measurement_type.lower()=='all':
			# display all S-parameters on Pna, one per window
			self.__PNA.write("CALC:PAR:DEF 'S11m',S11")
			self.__PNA.write("CALC:PAR:DEF 'S21m',S21")
			self.__PNA.write("CALC:PAR:DEF 'S12m',S12")
			self.__PNA.write("CALC:PAR:DEF 'S22m',S22")
			self.__PNA.query("*OPC?")
			# self.__PNA.write("DISP:ENABLE ON")
			# self.__PNA.write("DISP:WIND1:STAT OFF")
			# self.__PNA.write("DISP:WIND1:STAT ON")
			# turn on windows to display each S-parameter in a different window
			self.__PNA.write("DISP:WIND2:STAT ON")
			self.__PNA.write("DISP:WIND3:STAT ON")
			self.__PNA.write("DISP:WIND4:STAT ON")
			self.__PNA.query("*OPC?")

			self.__PNA.write("DISP:WIND1:TRAC1:FEED 'S11m'")
			self.__PNA.write("DISP:WIND2:TRAC2:FEED 'S21m'")
			self.__PNA.write("DISP:WIND3:TRAC3:FEED 'S12m'")
			self.__PNA.write("DISP:WIND4:TRAC4:FEED 'S22m'")
			self.__PNA.query("*OPC?")

			self.__PNA.write("INIT:CONT ON")  # turn on data gathering for now
			# turn on data averaging
			self.__PNA.write("SENS:AVER ON")
			self.__PNA.write("SENS:AVER:COUN " + str(navg))
		elif measurement_type.lower()=="reflection_only" or measurement_type.lower()=="s11_only" or measurement_type.lower()=="s11":            # then we measured only s11
			self.__PNA.write("CALC:PAR:DEF 'S11m',S11")
			self.__PNA.query("*OPC?")
			self.__PNA.write("DISP:WIND1:STAT OFF")
			self.__PNA.write("DISP:WIND2:STAT OFF")
			self.__PNA.write("DISP:WIND3:STAT OFF")
			self.__PNA.write("DISP:WIND4:STAT OFF")
			self.__PNA.query("*OPC?")

			#self.__PNA.write("DISP:ARR:OVER")
			self.__PNA.write("DISP:WIND1:STAT ON")
			self.__PNA.write("DISP:WIND1:SIZE MAX")
			self.__PNA.query("*OPC?")
			#self.__PNA.write("DISP:WIND1:TRAC1:DEL")
			self.__PNA.write("DISP:WIND1:TRAC1:FEED 'S11m'")
			self.__PNA.write("CALC:FORM1 SMITH")
			self.__PNA.query("*OPC?")
			self.__PNA.write("INIT:CONT ON")  # turn on data gathering for now
			# turn on data averaging
			self.__PNA.write("SENS1:AVER ON")
			self.__PNA.write("SENS1:AVER:COUN " + str(navg))
		else: raise ValueError("ERROR! No valid measurement type specified")
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
	writefile_spar = X_writefile_spar						# method to write S-parameters to file
