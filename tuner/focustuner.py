# Focus tuner control. Sets Focus tuner gamma using internal interpolation of Focus Tuner

import socket as sock
import select
import numpy as np
from utilities import formatnum
from calculated_parameters import convertMAtoRI, convertRItoMA, cascadeS
from time import sleep
systimeout=10
timeoutflush=3
prompt="CCMT->"
errormessage="Result=-1"                    # error in instruction to tuner
initialization_complete="INIT: 0x00"
pos1max=7380        # maximum carriage position
pos2max=5420        # maximum slug position - higher number is closer to center conductor = higher reflection
minfreq=800         # minimum frequency of operation in MHz - limit set by tuner
maxfreq=6500        # maximum frequency of operation in MHz - limit set by tuner

# S1 is the 2-port to be cascaded with the tuner's port 1
# S2 is the 2-port to be cascaded with the tuner's port 2
class FocusTuner(object):
	def __init__(self,IP=("192.168.1.30",23),S1=None,S2=None,tunertype='load'):
		self.tunertype=tunertype.lower()
		self._focustuner=sock.socket()
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
		# parameters
		self.tunerfrequency=None # current tuner frequency in MHz rounded to nearest MHz
		Sfcascom=[]         # list of frequencies common to both cascaded 2-ports (on ports 1 and 2 of the tuner)
		if S1!=None and S2!=None and len(S1)>0 and len(S2)>0: Sfcascom=[int(f) for f in list(set(list(S1.keys()))&set(list(S2.keys())))]
		elif S1!=None and len(S1)>0: Sfcascom=[int(f) for f in list(S1.keys())]
		elif S2!=None and len(S2)>0: Sfcascom=[int(f) for f in list(S2.keys())]
		if len(Sfcascom)>0: self.allowedfrequencies=list(set(self.get_cal_list()[2])&set(Sfcascom))     # set allowed frequencies to be those common to the tuner calibrations and the cascaded 2-ports
		else: self.allowedfrequencies=self.get_cal_list()[2]
		self.S1=S1  # 2-port S-parameters cascaded to left side of tuner (port 1 of tuner) format S1[frequency]=[[s11,s12],[s21,s22]] (2x2 NumPy array) and frquency in MHz rounded to the nearest MHz
		self.S2=S2  # 2-port S-parameters cascaded to right side of tuner (port 2 of tuner) format S1[frequency]=[[s11,s12],[s21,s22]] (2x2 NumPy array) and frquency in MHz rounded to the nearest MHz
		self.tunerSpar=None
		self.p1=None     # tuner position of carriage
		self.p2=None     # tuner position of slug
	def __del__(self):
		self._focustuner.close()
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
# get tuner position
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
		if pos1!=None and pos2!=None and pos1>=0 and pos1<=pos1max and pos2>=0 and pos2<=pos2max:
			pos1=str(int(pos1))
			pos2=str(int(pos2))
			rcv=self._focussend("POS 1 "+pos1+" 2 "+pos2)
			while not ("JOB" in rcv and "completed" in rcv):           # polling loop - wait for JOB completed
				rcv=self._focusrcv()
			self.p1,self.p2=self.getPOS()
			if not (self.p1==int(pos1) and self.p2==int(pos2)):
				raise ValueError("ERROR! tuner not moving to prescribed position")
		else: raise ValueError("ERROR! Illegal value for pos1 and/or pos2")
		self.tunerfrequency=None        # force cascade next time gamma is set
###############################################################################################
	# def getstatus(self):
	# 	statusraw=self._focussend('status?')
	# 	if "JOB" in statusraw and "completed" in statusraw: return True
	# 	elif statusraw!=None and len(statusraw)>0:
	# 		s1=int(statusraw.split("S1=")[1].split("S2=")[0].strip())
	# 		s2=int(statusraw.split("S2=")[1][0].strip())
	# 		if s1+s2==0: return True
	# 	else: return False
#################################################################################################################
	# mechanical initialization of tuner
	def initializetuner(self,axis=0,nocascade=False):
		if int(axis)!=0 and int(axis)!=1 and int(axis)!=2: raise ValueError("ERROR! Illegal value for axis")
		rcv=self._focussend("init "+str(int(axis)))
		rcv=self._focussend("init?")                    # first time query for initialization complete signature
		while initialization_complete not in rcv:      # poll for initialization complete signal
			rcv=self._focussend("init?")                # continue to query for initialization complete signature
		self.p1,self.p2=self.getPOS()                 # p1 is carriage position and p2 is slug position
		if self.p1+self.p2!=0: raise ValueError("ERROR! tuner failed to initialize")
		if not nocascade: self._cascade_tuner(frequency=self.tunerfrequency)        # force cascade to maintain consistency of tuner state parameters
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
		if not nocascade: self._cascade_tuner(frequency=self.tunerfrequency)        # force cascade to maintain consistency of tuner state parameters
#####################################################################################################################
# flush the tuner LAN output by reading until there's nothing left to read
	def _flush_tuner_LAN(self,timeout=0.1):
		rcv="x"
		#print("from line 129 in focustuner.py flush_tuner() rcv= ",rcv)
		while len(rcv)>0:
			rcv=self._focusrcv(ignoreerror=True,timeout=timeout)
			#print("from line 132 in focustuner.py flush_tuner() rcv= ",rcv)
		return rcv
#####################################################################################################################
# load calibration at the frequency in MHz. Note that frequency is within 1MHz and must be in the legal range for this tuner AND the calibration must exist
# 	def loadcal(self,frequency=None):
# 		frequency=str(int(frequency))     # convert to string and to nearest MHz
# 		if frequency==None or frequency<minfreq or frequency>maxfreq: raise ValueError("ERROR! Illegal frequency")
# 		rcv=self._focussend('loadfreq '+frequency)
# 		if "no calbration" in rcv:
# 			print("WARNING! No calibration at given frequency NO CALIBRATION LOADED!")
# 		self._cascade_tuner(frequency=self.tunerfrequency)        # force cascade to maintain consistency of tuner state parameters
# 		return rcv
####################################################################################################################
# get reflection coefficient at DUT and tuner gain. frequency is in MHz. Tuner gain is linear and is always <1 because the tuner is a passive element
# The tuner is actually the composite of S1+tuner+S2 cascaded S-parameters were S1 is the S-parameters of the two-port connected to the tuner's port 1 i.e. the left hand side of the tuner
# and S2 is the S-parameters of the two-port connected to the tuner port 2 (right hand side of tuner)
# position is a string of format s1,s2 where s1 is the carriage position and s2 is the slug position
# the reflection coefficient is in complex(magnitude,jangle) (angle in degrees) and also complex(real,jimaginary)
# if format_gamma="ri" then the reflection coefficient is in real+jimaginary
# self.S1 is the 2-port S-parameters cascaded onto the left side of the tuner (port 1)
# self.S2 is the 2-port S-parameters cascaded onto the right side of the tuner (port 2)
# a tuner cascade operation is always performed so as to ensure data consistency against changes in tuner mechanical position and/or selected frequency
	def get_tuner_reflection_gain(self,frequency=None):
		# if self.p1!=self.getPOS()[0] or self.p2!=self.getPOS()[1]:
		# 	print("WARNING! actual tuner position does not agree with that saved")
		# 	self.p1,self.p2=self.getPOS()
		# 	self.tunerfrequency=None        # null out frequency to guarantee recalculation of cascaded tuner parameter because if there are inconsistencies then we cannot trust that the cascade has been done
		if self.tunerfrequency==None:  # then the frequency is specified by the user, so we need to update the internal frequency value self.tunerfrequency
			self.tunerfrequency=int(float(frequency))
		self._cascade_tuner(frequency=self.tunerfrequency)       # cascade tuner to ensure consistency of saved states
		rcv=self._focussend("gamma?")
		frequencyactual=int(float(rcv.split("MHz")[0].strip()))
		gam=rcv.split("Gamma:")[1].strip().split("Loss")[0].strip()             # gamma_magnitude gamma_angle string
		gammamag=float(gam.split()[0].strip())   # magnitude part of reflection coefficient
		gammaang=float(gam.split()[1].strip())   # angle (degrees) part of reflection coefficient
		if frequencyactual!=frequency: raise ValueError("ERROR! actual frequency is not that selected by the user")
		if self.tunertype=='source': tunergain=np.square(abs(self.tunerSpar[1,0]))/(1.-np.square(abs(self.tunerSpar[1,1])))
		elif self.tunertype=='load': tunergain=np.square(abs(self.tunerSpar[1,0]))/(1.-np.square(abs(self.tunerSpar[0,0])))
		else: raise ValueError("ERROR! Illegal tuner type. Should be source or load")
		p1,p2=self.getPOS()
		position="".join([str(p1),",",str(p2)])         # tuner position in string format p1,p2
		return {"gamma_MA":complex(gammamag,gammaang),"gamma_RI":convertMAtoRI(mag=gammamag,ang=gammaang),"gain":tunergain,"Spar":self.tunerSpar,"pos":position, "frequency":self.tunerfrequency}  # dictonary containing reflection coefficient (mag,angle,real+jimaginary, and tuner gain in dB all at the selected frequency
##########################################################################################################################
# set tuner reflection coefficient as seen by the DUT
# for parameter gamma_format='ma' the parameter gamma is a tuple of format (mag,angle) - both reals with the angle in degrees and for parameter_format='ri'
# the parameter gamma is of format complex(gammareal,jgammaimag)
# if format_gamma="ri" then the reflection coefficient input is specified as a complex number - real+jimaginary
# if format_gamma="ma" then the reflection coefficient input is specified as a complex(mag,jang) with the magnitude real and the angle imaginary
# the actual reflection coefficient is returned as a dictionary "gamma_MA":(mag,angle) and "gamma_RI":complex(real,jimaginary)
# the actual tuner gain is returned in the above returned dictionary as "gain":tunergaindB
# frequency is in MHz, truncated
	def set_tuner_reflection(self,frequency=None,gamma=None,gamma_format="ma"):
		if gamma==None: raise ValueError("ERROR! did not specify a value of gamma")
		if self.tunerfrequency==None:  # then the frequency is specified by the user, so we need to update the internal frequency value self.tunerfrequency
			self.tunerfrequency=int(float(frequency))
		self._cascade_tuner(frequency=self.tunerfrequency)       # start off by cascading tuner to ensure that we have the correct S-parameters of any two-ports connected to the tuner
		if gamma_format.lower()=="ma":
			gamma_mag=gamma.real
			gamma_ang=gamma.imag
		elif gamma_format.lower()=="ri": gamma_mag,gamma_ang = convertRItoMA(gamma).real,convertRItoMA(gamma).imag
		else: raise ValueError("ERROR! Illegal value for gamma_format")
		rcv=self._focussend("".join(["tuneto ",formatnum(gamma_mag,precision=3,nonexponential=True)," ",formatnum(gamma_ang,precision=3,nonexponential=True)]))     # set reflection coefficient of the S1+tuner+S2 composite tuner
		#print("from line 185 in focustuner.py set_tuner_reflection() rcv ",rcv)
		while not ("JOB" in rcv and "completed" in rcv):           # polling loop - wait for JOB completed
			#print("from line 191 in focustuner.py set_tuner_reflection() rcv ",rcv)
			rcv=self._focusrcv()
			#print("from line 189 in focustuner.py set_tuner_reflection() rcv ",rcv)
		#sleep(10)
		#print("from")
		ret=self.get_tuner_reflection_gain(frequency=self.tunerfrequency)       # get actual tuner reflection and gain
		return ret
##########################################################################################################################
# form a "composite tuner" by cascading the tuner with two-port S-parameters on the port given by 1 (left side of tuner) or 2 (right side of tuner)
# the left side of the tuner is that to your left when facing the tuner window
# if the tuner mode is "source" (for sourcepull):
#           and port=1, cascade the two-port, specified by S1, on the tuner side opposite the DUT
#           and port=2, cascade the two-port, specified by S2, on the tuner DUT side, between the tuner and DUT. This uses the built-in tuner command "adaptor"
# else if the tuner mode is "load" (for loadpull):
#           and port=1, cascade the two-port, specified by S1, on the tuner DUT side, between the tuner and DUT. This uses the built-in tuner command "adaptor"
#           and port=2, cascade the two-port, specified by S2, on the tuner side opposite the DUT
# This method cascades the tuner for just one of the calibrated frequencies - the frequency is in MHz, rounded to the nearest MHz
# frequency is in MHz
# self.S1[frequency] and self.S2[frequency] are 2x2 Numpy arrays where S[0,0]=S11, S[0,1]=S12, S[1,0]=S21, S[1,1]=S22
# returns dictionary were ['S'] is the composite tuner S-parameters in a 2x2 NumPy array of real+jimaginary and ['G'] is the tuner gain in dB, which is always <0 since the tuner is a passive element
	def _cascade_tuner(self,frequency=None):
		if frequency not in self.allowedfrequencies: raise ValueError("ERROR! selected frequency NOT in the set of allowed frequencies - has no calibration or not in the 2-port cascaded element S-parameters")
		self.tunerfrequency=int(float(frequency))                  # set tuner frequency (MHz rounded to nearest MHz)
		f=str(self.tunerfrequency)                          # tuner frequency in string MHz
		rcv1=self._focussend("loadfreq "+f)                      # load calibration at the given frequency of interest
		rcv2=self._focussend("".join(["adapter 1 ",str(0)," ",str(0)," ",str(1)," ",str(0)," ",str(1)," ",str(0)," ",str(0)," ",str(0)]))     # cascade tuner with ideal thru to clear any previous cascade
		sp=self._focussend("spar?")                     # get S-parameters of tuner without any cascaded 2-ports
		#print("from line 212 in focustuner.py sp= ",sp)
		st11=convertMAtoRI(mag=float(sp.split()[1]),ang=float(sp.split()[2]))
		st12=convertMAtoRI(mag=float(sp.split()[3]),ang=float(sp.split()[4]))
		st21=convertMAtoRI(mag=float(sp.split()[5]),ang=float(sp.split()[6]))
		st22=convertMAtoRI(mag=float(sp.split()[7]),ang=float(sp.split()[8]))
		ST=np.array([[st11,st12],[st21,st22]])          # convert S-parameters of tuner to NumPy 2x2 S-parameter array
		self.tunerSpar=ST        # intially set tuner S-parameters to those measured for the tuner alone. If there are cascaded 2-ports, then self.tunerSpar will be updated accordingly

		if self.tunertype=='source':                        # this is a source-pull tuner setup
			if self.S2!=None:                                       # Is there a 2-port on port 2 of the tuner, between the tuner and DUT?
				s11=convertRItoMA(self.S2[f][0,0])        #convert to mag+jang where ang is in degrees
				s12=convertRItoMA(self.S2[f][0,1])
				s21=convertRItoMA(self.S2[f][1,0])
				s22=convertRItoMA(self.S2[f][1,1])
				# cascade the 2-port on port 2 to the tuner port 2 to get tuner+S2
				self._focussend("".join(["adapter 1 ",str(s11.real)," ",str(s11.imag)," ",str(s12.real)," ",str(s12.imag)," ",str(s21.real)," ",str(s21.imag)," ",str(s22.real)," ",str(s22.imag)])) # cascade tuner+self.S2 to be stored in tuner memory for the purpose of setting reflection coefficient
				self.tunerSpar=cascadeS(ST,self.S2[f])                 # cascade tuner+S2 for this method's tuner S-parameter data. ST is the S-parameters of the intrinsic tuner itself at the frequency of interest
			if self.S1!=None:
				self.tunerSpar=cascadeS(self.S1[f],self.tunerSpar)         # find S-parameters at the frequency of interest of the composite tuner, S1+tuner+S2, where S1 is the 2-port on tuner port 1 and S2 is the 2-port on tuner port 2
				term=convertRItoMA(self.S1[f][1,1])            # set composite tuner port 1 termination assuming that the two-port on the tuner port 1, S1, has a perfect match on its input
			else: term=complex(0,0)                     # no 2-port on port 2 of tuner so assume perfect load on port 2 of tuner
			self._focussend("".join(["term 1 ",str(term.real)," ",str(term.imag)]))     # set tuner+S2 source termination (mag is real and angle is imag) at the input of the composite tuner to allow proper setting of tuner reflection coefficient presented to DUT

		elif self.tunertype=='load':                         # this is a load-pull tuner setup
			if self.S1!=None:           # then self.S1 is the S-parameter two-port between the DUT and tuner
				s11=convertRItoMA(self.S1[f][0,0])        #convert to mag+jang where ang is in degrees
				s12=convertRItoMA(self.S1[f][0,1])
				s21=convertRItoMA(self.S1[f][1,0])
				s22=convertRItoMA(self.S1[f][1,1])
				# cascade S-parameters of the 2-port on tuner port 1 with the tuner to get the composite tuner, S1+tuner
				self._focussend("".join(["adapter 1 ",str(s11.real)," ",str(s11.imag)," ",str(s12.real)," ",str(s12.imag)," ",str(s21.real)," ",str(s21.imag)," ",str(s22.real)," ",str(s22.imag)]))    # cascade self.S1+tuner to be stored in tuner memory for the purpose of setting reflection coefficient
				self.tunerSpar=cascadeS(self.S1[f],ST)                 # cascade S1+tuner for this method's tuner S-parameter data. ST is the S-parameters of the intrinsic tuner itself
			if self.S2!=None:
				self.tunerSpar=cascadeS(self.tunerSpar,self.S2[f])             # find S-parameters at the frequency of interest the composite tuner, S1+tuner+S2 where S1 is the 2-port on tuner port 1 and S2 is the 2-port on tuner port 2
				term=convertRItoMA(self.S2[f][0,0])            # set tuner port 2 termination assumes that the two-port on the tuner output, S2, has a perfect match on its output
			else: term=complex(0,0)                     # no 2-port on port 2 of tuner so assume perfect load on port 2 of tuner
			self._focussend("".join(["term 1 ",str(term.real)," ",str(term.imag)]))     # set S1+tuner load termination (mag is real and angle is imag) at the output of the composite tuner to allow proper setting of tuner reflection coefficient presented to DUT
		else: raise ValueError("ERROR! Illegal value for tuner type")
		return
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