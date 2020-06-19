# Focus Tuner control, Uses no interpolation to set gamma. gamma set to nearest point calibrated Used for noise measurements
#
import socket as sock
import select
import numpy as np
import copy as cp
from utilities import formatnum, is_number
from calculated_parameters import convertMAtoRI, convertRItoMA, cascadeS
from time import sleep
systimeout=10
settlingtime=1                 # settling time in sec
timeoutflush=3
prompt="CCMT->"
errormessage="Result=-1"                    # error in instruction to tuner
initialization_complete="INIT: 0x00"
Xmax=7380        # maximum carriage position
#pos2max=5420        # maximum slug position - higher number is closer to center conductor = higher reflection
Ymax=5870        # maximum slug position - higher number is closer to center conductor = higher reflection
minfreq=800         # minimum frequency of operation in MHz - limit set by tuner
maxfreq=6500        # maximum frequency of operation in MHz - limit set by tuner

# S1 is the 2-port to be cascaded with the tuner's port 1
# S2 is the 2-port to be cascaded with the tuner's port 2
class FocusTuner(object):
	def __init__(self,IP=("192.168.1.30",23),S1=None,S2=None,tunercalfile=None, tunertype='load', term=complex(0.,0.)):
		self.tunertype=tunertype.lower()
		self._focustuner=sock.socket()
		self.tunerterm=term
		#print("from focustuner_pos.py debug IP=",IP)
		try: self._focustuner.connect(IP)           # try to establish socket connection to tuner
		except: raise ValueError("ERROR! cannot find Focus tuner. Check if tuner is on and/or connected to LAN and check the IP address")
		self.cascaded_port1_Spar=[]
		self.cascaded_port2_Spar=[]
		rcv=self._flush_tuner_LAN(timeout=timeoutflush)        # flush tuner output buffer and ignore error
		rcvinit=self._focussend('echo off')
		self.initializetuner(nocascade=True)
		if self.tunertype=='load': self._focussend('MODE LOAD')         # set tuner as a loadpull tuner (tune output of DUT)
		elif self.tunertype=='source': self._focussend('MODE SOURCE')   # set tuner as a sourcepull tuner (tune input of DUT)
		else: raise ValueError("ERROR! Invalid tuner type. Must be load or source")

		self._get_tuner_calibration(tunercalfile)              # get tuner calibration
		# cascade tuner with input and output circuits

		if S1!=None:
			self._cascade_tuner(port=1,S=S1)
		if S2!=None:
			self._cascade_tuner(port=2,S=S2)

	def __del__(self):
		#self._focustuner.close()
		del self
######################################################################################################################################################
	# send command to tuner via socket connection
	def _focussend(self,cmd,ignoreerror=False,timeout=systimeout):
		rcv=self._flush_tuner_LAN()
		self._focustuner.send((cmd+"\x0D").encode())
		rcv=self._focusrcv(ignoreerror=ignoreerror,timeout=timeout)
		if errormessage in rcv: raise ValueError("ERROR! instruction returned a Result=-1")
		return rcv
#############################################
	# read data from tuner via socket connection
	def _focusrcv(self,ignoreerror=False,timeout=systimeout):
		readable=select.select([self._focustuner],[],[],timeout)[0]
		rcv=""
		while len(readable)!=0 and prompt not in rcv:
			rcv="".join([rcv,self._focustuner.recv(2048).decode()])
			if prompt in rcv: break
			readable=select.select([self._focustuner],[],[],timeout)[0]
		if not ignoreerror and "Result=-1" in rcv: raise ValueError("ERROR! syntax error")
		return rcv                 # get all available data from tuner
#######################################################################################################################################################
############################################################################################
# get tuner position from focustuner.py
	def getPOS(self):
		rcv=self._focussend('POS?')
		if rcv!=None and rcv!="":
			try: p1=int(rcv.split('A1=')[1].split('A2=')[0].strip())
			except: raise ValueError("ERROR! could not get pos1")
			if "A3" not in rcv:
				try: p2=int(rcv.split('A2=')[1].split('\r')[0].strip())
				except: raise ValueError("ERROR! A1,A2 could not get pos2")
			else:
				try: p2=int(rcv.split('A2=')[1].split('A3=')[0].strip())
				except: raise ValueError("ERROR! A1,A2,A3 could not get pos2")
		return p1,p2        # p1 is carriage position and p2 is slug position

############################################################################################
# set tuner position
	def setPOS(self,pos1=None,pos2=None):       # p1 is carriage position and p2 is slug position
		if pos1!=None and pos2!=None and pos1>=0 and pos1<=Xmax and pos2>=0 and pos2<=Ymax:
			pos1=str(int(pos1))
			pos2=str(int(pos2))
			rcv=self._focussend("POS 1 "+pos1+" 2 "+pos2)
			while not ("JOB" in rcv and "completed" in rcv):           # polling loop - wait for JOB completed
				rcv=self._focusrcv()
			self.p1,self.p2=self.getPOS()
			if not (self.p1==int(pos1) and self.p2==int(pos2)):
				raise ValueError("ERROR! tuner not moving to prescribed position")
		else:
			print(pos1,pos2,Xmax,Ymax)
			raise ValueError("ERROR! Illegal value for pos1 and/or pos2")
		self.tunerfrequency=None        # force cascade next time gamma is set
		sleep(settlingtime)             # not sure if needed but I added this April 24, 2020 because there appeared to be "bad spots" for certain tuner positions
###############################################################################################
	# mechanical initialization of tuner
	def initializetuner(self,axis=0,nocascade=False):
		if int(axis)!=0 and int(axis)!=1 and int(axis)!=2: raise ValueError("ERROR! Illegal value for axis")
		rcv=self._focussend("init "+str(int(axis)))
		rcv=self._focussend("init?")                    # first time query for initialization complete signature
		while initialization_complete not in rcv:      # poll for initialization complete signal
			rcv=self._focussend("init?")                # continue to query for initialization complete signature
		self.p1,self.p2=self.getPOS()                 # p1 is carriage position and p2 is slug position
		if self.p1+self.p2!=0: raise ValueError("ERROR! tuner failed to initialize")
		sleep(settlingtime)             # not sure if needed but I added this April 24, 2020 because there appeared to be "bad spots" for certain tuner positions
#####################################################################################################################
# reset the tuner. Mechanically initializes tuner and also clears any cascaded networks
#
	def resettuner(self,ignoreerror=False,nocascade=False):
		rcv=self._focussend("reset",ignoreerror=ignoreerror)
		rcv=self._focussend("init?")                    # first time query for initialization complete signature
		while initialization_complete not in rcv:      # poll for initialization complete signal
			rcv=self._focussend("init?")                # continue to query for initialization complete signature
		self.p1,self.p2=self.getPOS()                 # p1 is carriage position and p2 is slug position
		if self.p1+self.p2!=0: raise ValueError("ERROR! tuner failed to initialize")
		sleep(settlingtime)             # not sure if needed but I added this April 24, 2020 because there appeared to be "bad spots" for certain tuner positions
#####################################################################################################################
# flush the tuner LAN output by reading until there's nothing left to read
	def _flush_tuner_LAN(self,timeout=0.1):
		rcv="x"
		#print("from line 129 in focustuner.py flush_tuner() rcv= ",rcv)
		while len(rcv)>0:
			rcv=self._focusrcv(ignoreerror=True,timeout=timeout)
			#print("from line 132 in focustuner.py flush_tuner() rcv= ",rcv)
		return rcv
####################################################################################################################
# get reflection coefficient at DUT and tuner gain as a function of tuner position and frequency in MHz. Tuner gain is linear and is always <1 because the tuner is a passive element
# The tuner is actually the composite of S1+tuner+S2 cascaded S-parameters were S1 is the S-parameters of the two-port connected to the tuner's port 1 i.e. the left hand side of the tuner
# and S2 is the S-parameters of the two-port connected to the tuner port 2 (right hand side of tuner)
# position is a string of format s1,s2 where s1 is the carriage position and s2 is the slug position
# the reflection coefficient is in complex(magnitude,jangle) (angle in degrees) and also complex(real,jimaginary)
# if format_gamma="ri" then the reflection coefficient is in real+jimaginary
# self.S1 is the 2-port S-parameters cascaded onto the left side of the tuner (port 1)
# self.S2 is the 2-port S-parameters cascaded onto the right side of the tuner (port 2)
# a tuner cascade operation is always performed so as to ensure data consistency against changes in tuner mechanical position and/or selected frequency
# gamma_MA is complex gamma_mag.real+jgamma_angle.imag where gamma_angle is in degrees
# gamma_RI is complex gamma.real+jgamma.imag
# gain is linear, not dB and always < 1. since the tuner is a passive device
	def get_tuner_reflection_gain(self,frequency=None,position=None):
		frequency=str(int(frequency))           # expect frequency in MHz with smallest increment of 1MHz
		S=np.array([[self.tuner_data[frequency][position][0,0],self.tuner_data[frequency][position][0,1]],[self.tuner_data[frequency][position][1,0],self.tuner_data[frequency][position][1,1]]])
		if self.tunertype=='source':           # the tuner is used as a source-pull tuner e.g. noise parameter measurement
			gamma=S[1,1]+(S[1,0]*S[0,1]*self.tunerterm/(1.-S[0,0]*self.tunerterm))
			tunergain=np.square(abs(S[1,0]))*(1.-np.square(abs(self.tunerterm)))/(np.square(abs(1.-self.tunerterm*S[0,0]))*(1.-np.square(abs(gamma)))) # linear tuner power gain NOT in dB
		elif self.tunertype=='load':    # the tuner is used as a load pull tuner e.g. power testing and distortion testing
			gamma=S[0,0]+(S[0,1]*S[1,0]*self.tunerterm/(1.-S[1,1]*self.tunerterm))
			tunergain=np.square(abs(S[1,0]))*(1.-np.square(abs(self.tunerterm)))/(np.square(abs(1.-self.tunerterm*S[1,1]))*(1.-np.square(abs(gamma))))  # linear tuner power gain NOT in dB
		else: raise ValueError("Illegal tuner type must be source or load")
		return {"gamma_MA":convertRItoMA(gamma),"gamma_RI":gamma,"gain":tunergain,"Spar":S,"frequency":frequency,"pos":position}  # dictonary containing reflection coefficient (mag,angle,real+jimaginary, and tuner gain linear, not in dB all at the selected frequency
##########################################################################################################################
# get tuner position in p1,p2 where p1 and p2 are ints that are the positions of the carriage and slug respectively
# input is the reflection coefficient in real+jimaginary or magnitude+jangle and the reflection type = "ma" or "ri"
# return "pos": tuner position p1,p2 is found which gives the closest possible reflection coefficient relative to that requested
# return "gamma": the actual gamma according to the tuner calibration data (of the composite tuner)

##########################################################################################################################
# set tuner reflection coefficient (gamma) as seen by the DUT, to that discrete calibration point closest to the desired gamma from the constellation of tuner calibration points
# for a source type tuner, we find the closest gamma= tuner S22 and for a load type tuner, we find the closest gamma = S11.
# the tuned values should be reasonably close to the requested value if and only if the tuner port opposite the DUT has a low-reflection load on it.
# for parameter gamma_format='ma' the parameter gamma is a tuple of format (mag,angle) - both reals with the angle in degrees and for parameter_format='ri'
# the parameter gamma is of format complex(gammareal,jgammaimag)
# if format_gamma="ri" then the reflection coefficient input is specified as a complex number - real+jimaginary
# if format_gamma="ma" then the reflection coefficient input is specified as a complex(mag,jang) with the magnitude real and the angle imaginary
# the actual reflection coefficient is returned as a dictionary "gamma_MA":(mag,angle) and "gamma_RI":complex(real,jimaginary)
# the actual tuner gain is returned in the above returned dictionary as a linear value
# frequency is in MHz, truncated
	def set_tuner_reflection(self,frequency=None,gamma=None,gamma_format="ma"):
		frequency=str(frequency)
		#self._focussend("LOADFREQ "+frequency)
		if gamma==None: raise ValueError("ERROR! did not specify a value of gamma")
		if gamma_format.lower()=="ma":
			gamma=convertMAtoRI(mag=gamma.real,ang=gamma.imag)
		elif gamma_format.lower()!="ri": raise ValueError("ERROR! Illegal value for gamma_format")
		if self.tunertype=='source': pos=min(self.tuner_data[frequency],key=lambda p:abs(self.tuner_data[frequency][p][1,1]-gamma))             # find tuner motor positions which give an available tuner reflection coefficient closest to the one requested
		elif self.tunertype=='load': pos=min(self.tuner_data[frequency],key=lambda p:abs(self.tuner_data[frequency][p][0,0]-gamma))             # find tuner motor positions which give an available tuner reflection coefficient closest to the one requested
		else: raise ValueError("ERROR! Illegal tuner type. Must be load or source")
		self.setPOS(int(pos.split(",")[0]),int(pos.split(",")[1]))
		ret=self.get_tuner_reflection_gain(frequency=frequency,position=pos)       # get actual tuner reflection and gain of composite tuner
		return ret
##############################################################################################################################
##########################################################################################################################
# get tuner position p1,p2 which gives a reflection coefficient, close as possible, to that requested
# inputs:
# frequency is in MHz
# gamma is the requested reflection coefficient. If gamma_format=="ma" then the reflection coefficient is complex with the real part as the magnitude and imaginary part as the phase in degrees
# returns the tuner position as a string, p1,p2; actual reflection coefficient, from the tuner calibration; tuner available gain; S-parameters
# DOES NOT set the tuner to the requested reflection coefficient - this method only reports the reflection coefficient f

	def getPOS_reflection(self,frequency=None,gamma=None,gamma_format="ma"):
		frequency=str(frequency)
		#self._focussend("LOADFREQ "+frequency)
		if gamma==None: raise ValueError("ERROR! did not specify a value of gamma")
		if gamma_format.lower()=="ma":
			gamma=convertMAtoRI(mag=gamma.real,ang=gamma.imag)
		elif gamma_format.lower()!="ri": raise ValueError("ERROR! Illegal value for gamma_format")
		if self.tunertype=='source': pos=min(self.tuner_data[frequency],key=lambda p:abs(self.tuner_data[frequency][p][1,1]-gamma))             # find tuner motor positions which give an available tuner reflection coefficient closest to the one requested
		elif self.tunertype=='load': pos=min(self.tuner_data[frequency],key=lambda p:abs(self.tuner_data[frequency][p][0,0]-gamma))             # find tuner motor positions which give an available tuner reflection coefficient closest to the one requested
		else: raise ValueError("ERROR! Illegal tuner type. Must be load or source")
		ret=self.get_tuner_reflection_gain(frequency=frequency,position=pos)       # get actual tuner reflection and gain of composite tuner
		print("from line 220 focustuner_pos.py debug ",ret)
		return ret
##############################################################################################################################
# get list of tuner frequencies which have calibration points
	def get_cal_list(self):
		rcv=self._focussend("dir")
		freq=[]
		ID=[]
		Nbr=[]
		for l in rcv.splitlines():
			if len(l)>0 and '#'==l[0]:
				Nbr.append(int(l.split('#')[1].split(':')[0].strip()))
				ID.append(int(l.split(':')[1].strip().split()[0].strip()))
				freq.append(int(1000*float(l.split(':')[1].strip().split()[1].strip())))        # frequency in MHz
		return Nbr,ID,freq
###############################################################################################################################
# set tuner to PNA calibration position ~ 50ohms
	def set_tuner_Z0(self):
		self.setPOS(pos1=0,pos2=0)
###############################################################################################################################
######################################################################################################################################################
# read the tuner_data calibration file
# output is tuner_data[frequencyMHz][motorposition]=[s] which is a nested dictionary where [s] is a NumPy 2x2 matrix of S-parameters
# formatted as real+jimaginary and:
# S11=[0,0]
# S12=[0,1]
# S21=[1,0]
# S22=[1,1]
# and frequency, motorposition are keys of format MHz and motorx,motory, tuner motor positions
	def _get_tuner_calibration(self,tunerfile):
		try: ftun=open(tunerfile,'r')
		except: raise ValueError("ERROR! cannot open tuner_data file")
		self.tuner_data={}
		flines=[l for l in ftun.read().splitlines()]
		for fline in flines:
			if not "!" in fline:
				frequencyMHz=str(int(float(fline.split()[1].strip())*1000))               # frequency in MHz
				pos=",".join([fline.split()[3].strip(),fline.split()[4].strip()])           # tuner mechanical position for this calibration point
				if frequencyMHz not in self.tuner_data.keys(): self.tuner_data[frequencyMHz]={}       # add position point ONLY if it doesn't already exist
				self.tuner_data[frequencyMHz][pos]=np.empty((2, 2),complex)               # NumPy 2x2 s-parameter array definition
				self.tuner_data[frequencyMHz][pos][0,0]=convertMAtoRI(float(fline.split()[5]), float(fline.split()[6]))           # S11real,imaginary of tuner_data for the current position
				self.tuner_data[frequencyMHz][pos][0,1]=convertMAtoRI(float(fline.split()[7]), float(fline.split()[8]))           # S21real,imaginary of tuner_data for the current position
				self.tuner_data[frequencyMHz][pos][1,0]=convertMAtoRI(float(fline.split()[9]), float(fline.split()[10]))          # S12real,imaginary of tuner_data for the current position
				self.tuner_data[frequencyMHz][pos][1,1]=convertMAtoRI(float(fline.split()[11]), float(fline.split()[12]))         # S22real,imaginary of tuner_data for the current position
############################################################################################################################################################
	###########################################################################################################################################################
	# cascade tuner_data S-parameters with a 2-port either on port 1 or port 2 of the tuner_data to form a composite tuner
	# the port number is the tuner_data port where the 2-port is to be attached legal values are 1 and 2 only
	# S is the 2-port S parameters in real+jimaginary format and is of the form of a dictionary: S where S['name'] is the full filename of the S-parameter data file,
	# S[frequency][s]= where frequency is the key of type str, in MHz and [s] is the 2x2 NumPy matrix of S-parameters in real+jimaginary format
	#
	# output is the cascaded 2port+tuner_data cascaded S-parameters vs frequency and position for ONLY those frequencies that occur in
	# BOTH the original tuner_data parameters AND the S-parameter 2-port dictionary
	#
	# parameter port is the port of the tuner on which the two port (S-parameter matrix = parameter S) is to be cascaded
	def _cascade_tuner(self,port=None,S=None):
		if S==None:
			print("WARNING cascaded_tuner is unchanged since you provided no S-parameters")
			return
		if port!=1 and port!=2: raise ValueError("ERROR! no port number given or illegal port number! Port number must be 1 or 2")
		cascaded_tuner={}
		freqtuner=list(self.tuner_data.keys())          # all frequencies of the original tuner
		freqS=list(S.keys())                            # all frequencies of the S-parameters of the two-port to be cascaded
		freq = list(set(freqtuner)&set(freqS))          # freq is the list of frequencies in MHz (str data type) which are in BOTH the S-parameters AND the original tuner
		for kf in freq:                                 # go through frequency points common to both the tuner and S-parameters of the two-port to be cascaded with the tuner
			cascaded_tuner[kf]={}               # add a positions dictionary
			for pos in self.tuner_data[kf].keys():          # cascade 2-port S-parameters with original tuner_data S-parameter at all tuner_data positions for this frequency point = kf
				if port==1:
					cascaded_tuner[kf][pos]=cascadeS(S[kf],self.tuner_data[kf][pos])                        # cascade S parameters to port 1 of the existing tuner
				else:
					cascaded_tuner[kf][pos]=cascadeS(self.tuner_data[kf][pos],S[kf])                              # cascade S parameters to port 2 of the existing tuner\
		# S21tunercasdebug=convertRItoMA(cascaded_tuner['1250']['3200,5019'][1][0])
		# S22tunercasdebug=convertRItoMA(cascaded_tuner['1250']['3200,5019'][1][1])
		# self.setPOS(3200,5019)
		# S21tunerorigdebug=convertRItoMA(self.tuner_data['1250']['3200,5019'][1][0])
		# S22tunerorigdebug=convertRItoMA(self.tuner_data['1250']['3200,5019'][1][1])
		# a=3
		del self.tuner_data
		self.tuner_data=cp.deepcopy(cascaded_tuner)                  # replace the original tuner with the resultant cascaded tuner
		return
# ###########################################################################################################################################################