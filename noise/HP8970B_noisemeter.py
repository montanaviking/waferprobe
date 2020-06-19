import visa
from writefile_measured import X_writefile_noise
from utilities import dBtolin,lintodB
from read_write_spar_noise import *
from utilities import *
import numpy as np
from ctypes import c_ulong, create_string_buffer, byref
from collections import deque
rm = visa.ResourceManager()
import time
dt=1.5
class NoiseMeter(object):
# set up of parameter analyzer
	def __init__(self,rm=None,ENR=None,losstable=None,smoothing=16,preset=False,turnonnoisesourceonly=False):                                  # setup of Keithley parameter analyzer
		if rm==None: raise ValueError("ERROR! No VISA resource handle.")
		if ENR==None or ENR>20. or ENR<3.: raise ValueError("ERROR! Missing or illegal value for base ENR")
		try:
			self.__noisemeter = rm.open_resource('GPIB0::18::INSTR')         # use Keysight GPIB-USB interface having only the noise meter on this GPIB bus. The noisemeter doesn't appear to work when its GPIB bus has another instrument on it
			#print (self.__noisemeter.query("*IDN?"))
		except: raise ValueError("ERROR on HP8970B noise meter: Could not find on GPIB\n")
		self.__noisemeter.timeout=1000
		self.__noisemeter.query_delay=0.5            # set up query delay to prevent errors
		if preset: self.__noisemeter.write("PR")               # added April 3, 2020 to try
		self.__noisemeter.write("Q1")
		self.__changemodepoll()
		# sb=self.__noisemeter.read_stb()
		# print("before sleep sb= ",sb)
		# time.sleep(dt)
		# sb=self.__noisemeter.read_stb()
		# print("after sleep sb= ",sb)
		#self.__write("*SPE")
		self.__write("SPE")
		self.__write("RM")
		self.__write("RE")
		self.__write("OS")
		self.__write("L0")               # make sure loss compensation is off
		if(not turnonnoisesourceonly):
			# set up ENR table
			fL=None
			if losstable!=None:
				try: fL=open(losstable,'r')
				except: pass
			if fL==None and ENR!=None:
				self.__write("NE"+str(ENR)+"EN")
				self.__write("S1")                              # use the ENR entered for all frequencies
			if fL!=None:                # if the loss file exists, read it
				flines=[l for l in fL.read().splitlines()]
				if len(flines)<2: raise ValueError("ERROR! not enough data in ENR table")
				e=0.
				for l in flines:
					if "base_enr" in l.lower(): e=dBtolin(float(l.replace(',','\t').split('\t')[1]))      # read base ENR and convert it to a liinear number
				if e==0: raise ValueError("ERROR! No base ENR in input file")
				self.__write("NR")                                   # enter ENR table
				for l in flines:
					if not "#" in l:
						f=l.replace(',','\t').split()[0]                        # frequency in MHz
						loss=dBtolin(-float(l.replace(',','\t').split('\t')[1]))    # linear loss (actually as a gain)
						#ENReff=lintodB(e*loss+1.-loss)                          # effective ENR in dB accounting for input loss between noise source and DUT
						ENReff=lintodB(e*loss-1.+loss)                          # effective ENR in dB accounting for input loss between noise source and DUT
						self.__write(f+"EN"+str(ENReff)+"EN")
				self.__write("S0")                                   # use ENR table just entered
				self.__write("FR")

			#print("ENR dB = ",self.setENR(ENR))
			#self.__noisemeter.write("H1")
			self.__write("H1")
			self.__write("M2")
			em=self.getENR("error message")
			if not(em=="No error" or em=="DUT loss too high"): raise ValueError(em)
			if not(em=="No error" or em=="DUT loss too high"): raise ValueError(em)
			if int(smoothing)<1 or int(smoothing)>512: raise ValueError("ERROR! Illegal value of smoothing factor")
			sm="".join(["F",str(int(np.log2(int(smoothing))))])

			self.__write(sm)

		self.__noisemeter.write("Q0")           # disable SRQ line on GPIP so as to not interfere with other instruments on GPIB
		self.__changemodepoll()
		#time.sleep(dt)                          # because polling not working with polling off, must use delay time instead
	#######################################################################################
	# sweep
	# get gain and noise figures over all calibrated frequencies (in MHz) of the noise meter
	# if dB=True, then noise figure and gain (self.NF, self.gain) are in dB, if dB=False, then they are in linear
	def sweep(self,corrected=True,smoothing=8,dB=True):
		self.__noisemeter.write("Q1")           # enable SRQ line on GPIP so that polling works
		time.sleep(dt)                          # because polling not working with polling off, must use delay time instead
		self.__noisemeter.write("H1")			# enable read of frequency,noise figure, and gain in one reading
		if corrected==True:	self.__write("M2")			# set up to read corrected noise figure + gain
		else: self.__write("M1")
		em=self.__read("error message")
		if not(em=="No error" or em=="DUT loss too high"): raise ValueError(em)
		if int(smoothing)<1 or int(smoothing)>512: raise ValueError("ERROR! Illegal value of smoothing factor")
		sm="".join(["F",str(int(np.log2(int(smoothing))))])
		self.__noisemeter.write(sm)
		# self.freq=deque()
		# self.gain=deque()
		# self.NF=deque()
		self.gain={}
		self.NF={}
		self.__write("FB")
		em=self.__read("error message")
		if not(em=="No error" or em=="DUT loss too high"): raise ValueError(em)
		else: stopfrequency=self.__read("frequency")
		self.__write("FA")
		em=self.__read("error message")
		if not(em=="No error" or em=="DUT loss too high"): raise ValueError(em)
		else: frequency=self.__read("frequency")
		# append data for first frequency point since we've already measured this
		#self.freq.append(startfrequency)
		if dB:
			self.gain[formatnum(number=1E-6*frequency,type="int")]=self.__read("gain")
			self.NF[formatnum(number=1E-6*frequency,type="int")]=self.__read("noise figure")
		else:
			self.gain[formatnum(number=1E-6*frequency,type="int")]=dBtolin(self.__read("gain"))
			self.NF[formatnum(number=1E-6*frequency,type="int")]=dBtolin(self.__read("noise figure"))
		while frequency<stopfrequency:
			self.__write("UP")		# move one step up in frequency
			frequency=self.__read("frequency")      # get next frequency
			em=self.__read("error message")
			if not(em=="No error" or em=="DUT loss too high"): raise ValueError(em)
			if dB:
				self.gain[formatnum(number=1E-6*frequency,type="int")]=self.__read("gain")
				self.NF[formatnum(number=1E-6*frequency,type="int")]=self.__read("noise figure")
			else:
				self.gain[formatnum(number=1E-6*frequency,type="int")]=dBtolin(self.__read("gain"))
				self.NF[formatnum(number=1E-6*frequency,type="int")]=dBtolin(self.__read("noise figure"))
		self.__noisemeter.write("Q0")           # disable SRQ line on GPIP so as to not interfere with other instruments on GPIB
		time.sleep(dt)                          # because polling not working with polling off, must use delay time instead
		return(self.gain,self.NF)
############################################################################################################
# set noise meter to a single frequency (MHz)
# 	def set_frequency(self,frequency=None,corrected=True,smoothing=8):
# 		self.__noisemeter.write("H1")			# enable read of frequency,noise figure, and gain in one reading
# 		if corrected==True:	self.__write("M2")			# set up to read corrected noise figure + gain
# 		else: self.__write("M1")
# 		em=self.__read("error message")
# 		if not(em=="No error" or em=="DUT loss too high"): raise ValueError(em)
# 		if int(smoothing)<1 or int(smoothing)>512: raise ValueError("ERROR! Illegal value of smoothing factor")
# 		sm="".join(["F",str(int(np.log2(int(smoothing))))])
# 		# self.__noisemeter.write(sm)
# 		# self.__write("FB")
# 		# em=self.__read("error message")
# 		#if not(em=="No error" or em=="DUT loss too high"): raise ValueError(em)
# 		#else: maxfrequency=self.__read("frequency")/1E6                     # get maximum frequency of calibration in MHz
# 		#self.__write("FA")
# 		#em=self.__read("error message")
# 		#if not(em=="No error" or em=="DUT loss too high"): raise ValueError(em)
# 		#else: minfrequency=self.__read("frequency")/1E6                     # get minimum frequency of calibration in MHz
# 		if frequency==None: raise ValueError("ERROR! No valid frequency given")
# 		# if frequency<minfrequency: raise ValueError("ERROR! frequency below that of calibrated frequency range")
# 		# if frequency>maxfrequency: raise ValueError("ERROR! frequency above that of calibrated frequency range")
# 		self.__write("FR"+str(frequency)+"EN")  # set frequency of noise figure meter
# 		em=self.__read("error message")
# 		if not(em=="No error" or em=="DUT loss too high"): raise ValueError(em)
# 		return
############################################################################################################
# get noisefigure and gain at a single frequency (MHz)
# uses excess noise ratio, ENR (dB) interpolated from the ENR table in loadpull_system_calibration.py and the function is from utilities.py
#
	def get_NF_singlefrequency(self,frequency=None,ENR=None):
		if frequency==None: raise ValueError("ERROR! no frequency given")
		self.__noisemeter.write("Q1")           # enable SRQ line on GPIP so that polling works
		self.__changemodepoll()
		if ENR==None: ENR=ENRtablecubicspline(frequency)  # get interpolated ENR from table
		self.setENR(frequency=frequency,ENR=ENR)    # set ENR
		self.__changemodepoll()
		self.__write("FR"+str(frequency)+"EN")  # set frequency of noise figure meter
		gain=self.__read("gain")
		noisefiguredB=self.__read("noise figure")
		self.__noisemeter.write("Q0")           # disable SRQ line on GPIP so as to not interfere with other instruments on GPIB
		self.__changemodepoll()
		#time.sleep(dt)                          # because polling not working with polling off, must use delay time instead
		return gain,noisefiguredB
#############################################################################################################
	def getENR(self,returnparameter):
		#test0=self.__noisemeter.read()
		self.__write("SE")                               # get current ENR in dB
		#test1=self.__noisemeter.read()
		#test2=self.__noisemeter.read()
		#test3=self.__noisemeter.read()
		#test4=self.__noisemeter.read()
		r = self.__noisemeter.read().split(",")
		if float(r[1])>8E6:  # we have an error so process the error
			errornumber = int(r[1].split("90")[1].split("E+06")[0])
			error_message = self.__errormessagefromnumber(errornumber)
			print("WARNING! Noise Figure Meter ERROR = " + str(error_message))
			if errornumber==0:              # this means that the DUT attenuation is too high to measure gain and noise figure
				error_message = "DUT loss too high"
				if returnparameter.lower()=="ENR": return(float(r[0]))
				else: return (error_message)
		else: error_message = "No error"
		if returnparameter.lower()=="error message": return(error_message)
		elif returnparameter.lower()=="ENR": return(float(r[0]))
		else: return (error_message, float(r[0]))
###########################################################################################################################################
	def setENR(self,frequency=None,ENR=None):
		if ENR==None: raise ValueError("ERROR in HP8970B_noisemeter.py setENR(), Must supply ENR value")
		elif frequency==None: raise ValueError("ERROR in HP8970B_noisemeter.py setENR(), Must supply frequency in MHz value")
		else: self.__write("".join(["NE",str(ENR),"EN"]))      # enter and use spot ENR (ENR read from noise source)
		self.__write("SE"+str(ENR)+"EN")
###########################################################################################################################################
	# query noise meter (read and write in one command)
	def __query(self,cmd=None,returnparameter="noise figure"):
		self.__noisemeter.write(cmd)
		self.__readpoll()
		return(self.__read(returnparameter))
###########################################################################################################################################
	# safe write to noise meter
	def __write(self,cmd):
		self.__noisemeter.write(cmd)
		self.__readpoll()
###########################################################################################################################################
	# read from noise meter
	def __read(self,returnparameter):
		#self.__write("T2")
		r = self.__noisemeter.read().split(",")
		if float(r[1]) > 8E6:  # we might have an error so process the error
			errornumber = int(r[1].split("90")[1].split("E+06")[0])
			error_message = self.__errormessagefromnumber(errornumber)
			print("WARNING! from __read() Noise Figure Meter ERROR = " + str(error_message))
			if errornumber==0:              # this means that the DUT attenuation is too high to measure gain and noise figure
				error_message = "DUT loss too high"
				if returnparameter.lower()=="frequency": return(float(r[0]))
				elif returnparameter.lower()=="gain": return(-99.)
				elif returnparameter.lower()=="noise figure": return(99)
				elif returnparameter.lower()=="error message": return(error_message)
				else: return (error_message, int(r[0]/1E6),float(r[1]),float(r[2]))
		else: error_message = "No error"
		if returnparameter.lower()=="frequency": return(float(r[0]))
		elif returnparameter.lower()=="gain": return(float(r[1]))
		elif returnparameter.lower()=="noise figure": return(float(r[2]))
		elif returnparameter.lower()=="error message": return(error_message)
		else: return (error_message, int(r[0]/1E6),float(r[1]),float(r[2]))
######################################################################################################################################
	# translates error numbers into error messages
	def __errormessagefromnumber(self,errornumber):
		if errornumber==20: return("Not Calibrated")
		elif errornumber==21: return("Frequency point not calibrated")
		elif errornumber==22: return("Current RF attenuation not calibrated")
		elif errornumber==26: return ("Internal IF attenuators not calibrated")
		elif errornumber==30: return ("Start frequency is > stop frequency or lower frequency limit is > upper frequency limit")
		elif errornumber==31: return("Number of calibration points > 181")
		elif errornumber==36: return("Undefined special function")
		elif errornumber==40:return ("Undefined HP-IB code")
		elif errornumber==39: return("The number of plot points > 251")
		elif errornumber==41: return("Undefined HP-IB characters")
		#elif errornumber==0: return("error 0")
		else: return int(errornumber)
	######################################################################################################################################
	# polls instrument to loop until valid read
	#def __readpoll(self):
		# loop=True
		# while(loop):
		# 	loop=False
		# 	try: x=self.__noisemeter.read()
		# 	except: loop=True
		# time.sleep(0.5)
		# return
		# while True:
		# 	sb=self.__noisemeter.read_stb()
		# 	print("status byte = ",sb)
		# 	if (sb&1)==1: break
		# time.sleep(0.1)
	def __readpoll(self):
		self.__noisemeter.wait_for_srq()
		sb=self.__noisemeter.read_stb()
		x=self.__noisemeter.read()
		#print("waiting for srq done ",x,sb)
		time.sleep(.1)
		return
	def __changemodepoll(self):
		while True:
			sb=self.__noisemeter.read_stb()
			#print("before noisemeter status byte= ",sb)
			if sb==65: break
			#print("after noisemeter status byte= ",sb)
			time.sleep(.1)
		time.sleep(0.3)
###################################################################################
######################################################################################################################################
# read S-parameter file
# 	def read_spar_device(self,sparfilename=None):
# 		self.S=read_spar(sparfilename=sparfilename)
########################################################################################################################################
# get noise figure of DUT in a 50ohm system
# assume that we are using an isolator followed by an LNA or just an isolator at the input of the noise meter
# noise meter calibration is performed including the isolator+LNA on the input of the noise meter so that the composite noise meter i.e. NM is the isolator+LNA
# The DUT input is fed from the noise source while DUT output is fed into the isolator for the measurement
# In general, the DUT output is mismatched and we need to account for this
# Therefore, the total noise figure, Fsys of DUT+NM is measured.
# noise figure of the composite noise meter (NM) with a mismatch (assuming that the isolator provides a perfect match) is FNM=1/(1-|S22DUT|**2)
# where S22DUT is the S22 of the DUT
# the noise figure of the DUT, FDUT=FSYS-(FNM-1)/|S21DUT|**2
# where S21DUT is the S21 of the DUT
# S-
	def get_noise_figure_50ohm(self,DUTsparfilename=None,nmsparfilename=None,smoothing=8):
		if DUTsparfilename==None or nmsparfilename==None:  getrawnoise=True     # just read the noise meter to get the DUT noise figure at 50ohms
		else: getrawnoise=False
		self.sweep(smoothing=smoothing,dB=False)                   # get DUT + composite noise meter noise figures vs frequency (MHz) the results are in self.NF and self.gain where self.NF and self.gain linear
		freqNF=list(self.NF.keys())
		if not getrawnoise:
			SDUT=read_spar(sparfilename=DUTsparfilename)     # DUT S-parameters in format SDUT[frequencyinMHz][n,m] where for instance at 1GHz, S11=SDUT['1000'][0,0], S22=SDUT['1000'][1,1], S21=SDUT['1000'][1,0]
			Snm=read_spar(sparfilename=nmsparfilename)      # noise meter S-parameters. Usually is the isolator +cable at the input circuit of the noise meter
			freqSDUT=list(SDUT.keys())
			freqNM = list(Snm.keys())
			frequencies=[f for f in freqNF if (f in freqSDUT and f in freqNM)]            # find frequencies common to both the DUT S-parameters and the noise figure
			FDUT={}
			ga={}
			FNM={}
			for freq in frequencies:
			#FNM[freq]=(1/(1-pow(abs(SDUT[freq][1,1]),2))) + ((1/pow(abs(Snm[freq][1,0]),2)) -1)*(1-pow(abs(SDUT[freq][1,1]),2))
				FNM[freq]=(1/(1-pow(abs(SDUT[freq][1,1]),2))) + ((1/pow(abs(Snm[freq][1,0]),2)) -1)
				ga[freq]=pow(abs(SDUT[freq][1,0]),2)/(1-pow(abs(SDUT[freq][1,1]),2))           # magnitude DUT available gain from DUT S-parameters
				FDUT[freq]=self.NF[freq]-((FNM[freq]-1)/ga[freq])
			self.gainDUT={f:lintodB(pow(abs(SDUT[f][1,0]),2)) for f in FDUT.keys()}
			self.gaDUT={f:lintodB(ga[f]) for f in FDUT.keys()}
			self.NFDUT={f:lintodB(FDUT[f]) for f in FDUT.keys()}
		else:
			frequencies=[f for f in freqNF]
		# Find the DUT noise figure from the measured noise figure assuming an isolator at the input of the noise meter and that the isolator offers a perfect match to the DUT
			self.NFDUT={f:lintodB(self.NF[f]) for f in self.NF.keys()}
			self.gainDUT={f:lintodB(self.gain[f]) for f in self.gain.keys()}
			self.gaDUT=None
		return
######################################################################################################################################################
# turn noise source on or off
	def noise_sourceonoff(self,on=True):
		self.__noisemeter.write("T1")                   # Trigger hold on. This forces the noise source to not pulse but either be on or off
		if on==True: self.__noisemeter.write("VH")
		else: self.__noisemeter.write("VC")
		return
########################################################################################## ##############################################
	# write data to file function in file writefile_measured.py
	writefile_noise = X_writefile_noise
########################################################################################################################################
