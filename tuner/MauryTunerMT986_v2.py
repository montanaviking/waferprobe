# tuner driver version 2
# use Maury tuner_data to obtain noise parameters
import os
import numpy as np
import visa
import time
from calculated_parameters import cascadeS, convertSRItoGMAX, convertSRItoUMAX, convertRItoMA, convertMAtoRI
#from calculate_noise_parameters_v2 import calculate_gavail
#from read_write_spar_noise_v2 import spar_flip_ports
#import collections as c

class MauryTunerMT986(object):
	def __init__(self,rm=None,tunerfile=None,tunernumber=1):
		if tunerfile==None: raise ValueError("ERROR! no tuner_data calibration file given")
		self.tunerfile=tunerfile
		self._get_tuner_calibration()
		self.cascaded_port1_Spar=[]
		self.cascaded_port2_Spar=[]
		# set up tuner_data
		if rm==None: raise ValueError("ERROR! No VISA resource handle.")
		try: self.tuner_control = rm.open_resource('GPIB0::11::INSTR')
		except: ValueError("ERROR on tuner: Could not find on GPIB\n")
		#rm = visa.ResourceManager()                                                         # setup GPIB communications
		self.tuner_control = rm.open_resource('GPIB0::11::INSTR')
		self.tuner_control.query_delay=.2            # set up query delay to prevent errors
		#tuner_data.read_termination='\r'
		self.tuner_control.write_termination='\r'
		self.tunernumber=int(tunernumber)
		self._get_tuner_calibration()                                                       #read the tuner_data calibration file
######################################################################################################################################################
# polling loop for Maury tuner_data
	def _poll_movementonly(self):
		time.sleep(.1)
		starttime=time.time()
		while True:
			sb=self.tuner_control.read_stb()
			#print("movement_only status byte first loop ",sb)
			if (sb&16)==16: raise ValueError("ERROR in 1st loop poll_movementonly Tuner motor reached limit switch1")
			if (sb&8)==8: raise ValueError("ERROR in 1st loop poll_movementonly Tuner motor reached limit switch2")
			time.sleep(0.1)
			elapsedtime=time.time()-starttime
			if (sb&64)==64: break
			if elapsedtime>30:
				print("first loop timeout",sb)
				break
			continue
		starttime=time.time()
		while True:
			sb=self.tuner_control.read_stb()
			#print("movement_only status byte 2nd loop ",sb)
			if (sb&16)==16: raise ValueError("ERROR in 2nd loop poll_movementonly Tuner motor reached limit switch1")
			if (sb&8)==8: raise ValueError("ERROR in 2nd loop poll_movementonly Tuner motor reached limit switch2")
			#print("2nd loop",sb)
			time.sleep(0.1)
			elapsedtime=time.time()-starttime
			if (sb&32)==32: break
			if elapsedtime>30:
				print("2nd loop timeout",sb)
				break
			continue
		time.sleep(0.5)
###############################################
	def _poll_no_movement(self):
		time.sleep(0.05)
		while True:
			sb=self.tuner_control.read_stb()
			#print ("no_move before break in loop",sb)
			if int(sb&8)==8: raise ValueError("ERROR! from poll_no_movement of tuner: limit switch 2")
			elif int(sb&16)==16: raise ValueError("ERROR! from poll_no_movement of tuner: limit switch 1")
			if (int(sb&64)==64 and int(sb&32)==32) or int(sb&32): break
			sb=self.tuner_control.read_stb()
			#print ("no move after break",sb)
			time.sleep(0.05)
		time.sleep(.1)                                      # minimum time here to prevent read errors is 2sec
	#print("waiting for service request")
######################################################################################################################################################
# read the tuner_data calibration file
# output is tuner_data[frequencyMHz][motorposition]=[s] which is a nested dictionary where [s] is a NumPy 2x2 matrix of S-parameters
# formatted as real+jimaginary and:
# S11=[0,0]
# S12=[0,1]
# S21=[1,0]
# S22=[1,1]
# and frequency, motorposition are keys of format MHz and motorx,motory,motorz tuner motor positions
	def _get_tuner_calibration(self):
		try: ftun=open(self.tunerfile,'r')
		except: raise ValueError("ERROR! cannot open tuner_data file")
		self.tuner_data={}
		flines=[l for l in ftun.read().splitlines()]
		readfirstfreq=False                     # have we read the first frequency point?
		npos=0                       # number of actual tuner_data positions tallied during reads within a frequency point this assignment is redundant but removes IDE warnings
		for fline in flines:
			if "Freq" in fline:
				# if we've already read a frequency point then compare number of read positions of the previous frequency point the the numbe actually read
				numberofpositions=int(fline.split('positions')[0].split(',')[1].strip())        # number of expected tuner_data positions for this frequency point read from the tuner file
				#if readfirstfreq==True and npos!=numberofpositions: raise ValueError("ERROR! inconsistent tuner_data file. Number of actual tuning points does not match expected number")
				npos=0                       # we are about to read another frequency point data so reset the number of actual tuner_data positions tallied prior to reading data for the next set of points
				frequencyMHz=str(int(1E3*float(fline.split('GHz')[0].split()[1].strip()))) # convert GHz frequency to MHz and use it as a dictionary key to add the S-parameter data for the series of motor positions which follow
				self.tuner_data[frequencyMHz]={}     # add the S-parameter vs position dictionary to this frequency point using the frequencyMHz as a key
				readfirstfreq=True          # we have read the first frequency point. Noting this is necessary since we check consistency of data based on previous frequency point data
			elif "Position" in fline:
				npos+=1                                                                         # reading a tuner_data position so increment number of actual tuner_data positions
				xp=fline.split('Position')[1].split(',')[0].strip().split()
				pos="".join([xp[0],',',xp[1],',',xp[2]])            # tuner_data position setting
			elif "Range" not in fline and len(fline.split())==8:                          # Skip over Range line
				self.tuner_data[frequencyMHz][pos]=np.empty((2, 2),complex)               # NumPy 2x2 s-parameter array definition
				self.tuner_data[frequencyMHz][pos][0,0]=complex(float(fline.split()[0]), float(fline.split()[1]))            # S11real,imaginary of tuner_data for the current position
				self.tuner_data[frequencyMHz][pos][1,0]=complex(float(fline.split()[2]), float(fline.split()[3]))            # S21real,imaginar of tuner_data for the current position
				self.tuner_data[frequencyMHz][pos][0,1]=complex(float(fline.split()[4]), float(fline.split()[5]))            # S12real,imaginar of tuner_data for the current position
				self.tuner_data[frequencyMHz][pos][1,1]=complex(float(fline.split()[6]), float(fline.split()[7]))            # S22real,imaginar of tuner_data for the current position
	###########################################################################################################################################################
	# cascade tuner_data S-parameters with a 2-port either on port 1 or port 2 of the tuner_data
	# the port number is the tuner_data port where the 2-port is to be attached legal values are 1 and 2 only
	# S is the 2-port S parameters in real+jimaginary format and is of the form of a dictionary: S where S['name'] is the full filename of the S-parameter data file,
	# S[frequency][s]= where frequency is the key of type str, in MHz and [s] is the 2x2 NumPy matrix of S-parameters in real+jimaginary format
	#
	# output is the cascaded 2port+tuner_data cascaded S-parameters vs frequency and position for ONLY those frequencies that occur in
	# BOTH the original tuner_data parameters AND the S-parameter 2-port dictionary
	#
	# parameter port is the port of the tuner on which the two port (S-parameter matrix = parameter S) is to be cascaded
	def cascade_tuner(self,port=1,S=None):
		if port!=1 and port!=2: raise ValueError("ERROR! Illegal value for cascade port number")
		if S==None:
			print("WARNING cascaded_tuner is unchanged since you provided no S-parameters")
			return
		if port!=1 and port!=2: raise ValueError("ERROR! no port number given!")
		cascaded_tuner={}
		freqtuner=list(self.tuner_data.keys())          # all frequencies of the original tuner
		freqS=list(S.keys())                            # all frequencies of the S-parameters of the two-port to be cascaded
		freq = list(set(freqtuner)&set(freqS))          # freq is the list of frequencies in MHz (str data type) which are in BOTH the S-parameters AND the original tuner
		for kf in freq:                                 # go through frequency points common to both the tuner and S-parameters of the two-port to be cascaded with the tuner
			cascaded_tuner[kf]={}               # add a positions dictionary
			for pos in self.tuner_data[kf].keys():          # cascade 2-port S-parameters with original tuner_data S-parameter at all tuner_data positions for this frequency point = kf
				if port==1: cascaded_tuner[kf][pos]=cascadeS(S[kf],self.tuner_data[kf][pos])                        # cascade S parameters to port 1 of the existing tuner
				else: cascaded_tuner[kf][pos]=cascadeS(self.tuner_data[kf][pos],S[kf])                              # cascade S parameters to port 2 of the existing tuner
		self.tuner_data=cascaded_tuner                  # replace the original tuner with the resultant cascaded tuner
		return
# ###########################################################################################################################################################
# # get effective available gain for tuner_data+any 2-ports already cascaded with the tuner. Note that the gain is linear (dB) and will always be <1 since these are assumed to be passive elements
# # Since the tuner_data and any cascaded devices are assumed to be passive, the noise figure (dB) is -gain (dB)
# # note that the frequency is in MHz (floating number) and the position is a string "aaa,bbb,ccc" indicating the tuner_data motor positions
# # NOTE! this method flips ports 1 and 2 of the tuner_data if flipports=True (default) of the tuner_data circuit unit before calculating the gain!
# # Parameter frequency is a str data type and is the frequency in MHz where the tuner's available gain is found
# # Parameter position is the tuner motor positions str data type at which to find the available gain
# 	def get_tuner_availablegain(self,frequency=None,position=None,flipports=True):
# 		frequency=str(int(frequency))           # expect frequency in MHz with smallest increment of 1MHz
# 		if flipports:           # then flip the tuner ports 1 with 2 to calculate gain
# 			#S=np.array([[self.tuner_data[frequency][position][1,1],self.tuner_data[frequency][position][1,0]],[self.tuner_data[frequency][position][0,1],self.tuner_data[frequency][position][0,0]]])
# 			#gain=calculate_gavail(SDUT=S,gammain=0.)[0]
# 			gain=convertSRItoGMAX(s11=self.tuner_data[frequency][position][1,1], s21=self.tuner_data[frequency][position][0,1], s12=self.tuner_data[frequency][position][1,0], s22=self.tuner_data[frequency][position][0,0])['gain']       # note reversal of ports 1 and 2 in tuner S-parameters
# 		else:                   # do not flip tuner ports to calculate gain
# 			#gain=calculate_gavail(SDUT=self.tuner_data[frequency][position],gammain=0.)[0]
# 			gain=convertSRItoGMAX(s11=self.tuner_data[frequency][position][0,0], s21=self.tuner_data[frequency][position][1,0], s12=self.tuner_data[frequency][position][0,1], s22=self.tuner_data[frequency][position][1,1])['gain']
# 		return gain
###########################################################################################################################################################
# get effective available gain for tuner_data+any 2-ports already cascaded with the tuner when the tuner is used for loadpull. Note that the gain is linear (dB) and will always be <1 since these are assumed to be passive elements
# Since the tuner_data and any cascaded devices are assumed to be passive, the noise figure (dB) is -gain (dB)
# note that the frequency is in MHz (floating number) and the position is a string "aaa,bbb,ccc" indicating the tuner_data motor positions
# NOTE! this method flips ports 1 and 2 of the tuner_data if flipports=True (default) of the tuner_data circuit unit before calculating the gain!
# Parameter frequency is a str data type and is the frequency in MHz where the tuner's available gain is found
# Parameter position is the tuner motor positions str data type at which to find the available gain
# this calculation differs from the above and is from the Focus tuner manual
# the loadreflection is the real+jimaginary reflection coefficient on the output port of the tuner - opposite the DUT. Normally this reflection is near zero
# Here, the tuner is assumed to be used as a loadpull tuner connected to the DUT output. When flipports==False, port 1 of the tuner is connected to the output (port 2) of the DUT
	def get_tuner_availablegain_loadpull(self,frequency=None,position=None,loadreflection=None,flipports=False):
		if loadreflection==None: loadreflection=complex(0.,0.)
		frequency=str(int(frequency))           # expect frequency in MHz with smallest increment of 1MHz
		if flipports:           # then flip the tuner ports 1 with 2 to calculate gain
			S=np.array([[self.tuner_data[frequency][position][1,1],self.tuner_data[frequency][position][1,0]],[self.tuner_data[frequency][position][0,1],self.tuner_data[frequency][position][0,0]]])
		else:                   # do not flip tuner ports to calculate gain
			S=np.array([[self.tuner_data[frequency][position][0,0],self.tuner_data[frequency][position][0,1]],[self.tuner_data[frequency][position][1,0],self.tuner_data[frequency][position][1,1]]])
		gam1=S[0,0]+(S[0,1]*S[1,0]*loadreflection/(1.-S[1,1]*loadreflection))
		gain=np.square(abs(S[1,0]))*(1.-np.square(abs(loadreflection)))/(np.square(abs(1.-loadreflection*S[1,1]))*(1.-np.square(abs(gam1))))
		return gain
###########################################################################################################################################################
# get effective available gain for tuner_data+any 2-ports already cascaded with the tuner when the tuner is used for sourcepull. Note that the gain is linear (dB) and will always be <1 since these are assumed to be passive elements
# Since the tuner_data and any cascaded devices are assumed to be passive, the noise figure (dB) is -gain (dB)
# note that the frequency is in MHz (floating number) and the position is a string "aaa,bbb,ccc" indicating the tuner_data motor positions
# NOTE! this method flips ports 1 and 2 of the tuner_data if flipports=True (default) of the tuner_data circuit unit before calculating the gain!
# Parameter frequency is a str data type and is the frequency in MHz where the tuner's available gain is found
# Parameter position is the tuner motor positions str data type at which to find the available gain
# this calculation differs from the above and is from the Focus tuner manual
# the loadreflection is the real+jimaginary reflection coefficient on the output port of the tuner - opposite the DUT. Normally this reflection is near zero
# Here, the tuner is assumed to be used as a sourcepull tuner connected to the DUT input. When flipports==False, port 1 of the tuner is connected to the input (port 1) of the DUT
	def get_tuner_availablegain_sourcepull(self,frequency=None,position=None,sourcereflection=None,flipports=False):
		if sourcereflection==None: sourcereflection=complex(0.,0.)
		frequency=str(int(frequency))           # expect frequency in MHz with smallest increment of 1MHz
		if flipports:           # then flip the tuner ports 1 with 2 to calculate gain
			S=np.array([[self.tuner_data[frequency][position][1,1],self.tuner_data[frequency][position][1,0]],[self.tuner_data[frequency][position][0,1],self.tuner_data[frequency][position][0,0]]])
		else:                   # do not flip tuner ports to calculate gain
			S=np.array([[self.tuner_data[frequency][position][0,0],self.tuner_data[frequency][position][0,1]],[self.tuner_data[frequency][position][1,0],self.tuner_data[frequency][position][1,1]]])
		gam1=S[1,1]+(S[1,0]*S[0,1]*sourcereflection/(1.-S[0,0]*sourcereflection))
		gain=np.square(abs(S[1,0]))*(1.-np.square(abs(sourcereflection)))/(np.square(abs(1.-sourcereflection*S[0,0]))*(1.-np.square(abs(gam1))))
		return gain
###########################################################################################################################################################
# get tuner_data reflection coefficient in real+jimaginary format on port 1 of the tuner
# remember that the tuner_data could have been cascaded with various 2-ports
# frequency is of str data type and is in MHz. frequency is converted to str if if isn't that type already
# position is in the format "xxxxx,yyyyyy,zzzzz" and is the positions of the three tuner_data motors
	def get_tuner_reflection(self,frequency=None,position=None):
		frequency=str(frequency)
		if self.tuner_data==None or len(self.tuner_data)==0: raise ValueError("ERROR! no tuner_data data provided")
		reflection_coefficient=self.tuner_data[frequency][position][0,0]
		return reflection_coefficient
#############################
# get power gain of tuner_data+cascaded 2-ports on tuner_data when tuner_data is in a 50ohm system
# remember that the tuner_data could have been cascaded with various 2-ports
# frequency is of str data type and is in MHz
# position is in the format "xxxxx,yyyyyy,zzzzz" and is the positions of the three tuner_data motors
# NOTE! this method flips ports 1 and 2 of the tuner_data if flipports=True (default) of the tuner_data circuit unit before calculating the gain!
	def get_tuner50gain(self,frequency=None,position=None,flipports=True):
		frequency=str(int(frequency))
		if self.tuner_data==None or len(self.tuner_data)==0: raise ValueError("ERROR! no tuner_data data provided")
		if flipports: # then flip the tuner ports 1 with 2 to calculate gain
			g=20*np.log10(abs(self.tuner_data[frequency][position][0,1]))
		else:         # then calculate gain without fliping tuner ports
			g=20*np.log10(abs(self.tuner_data[frequency][position][1,0]))
		return g
###############################################################################################################################################################
# find tuner_data position which gives an reflection coefficient closest to that selected
# requested_reflection is the desired reflection coefficient (complex data type always) to be requested in:  real+jimaginary if reflection_type='RI' or magnitude and jangle where angle is in degrees if reflection type='MA'
# frequency is in MHz and is of type str because it's used as a dictionary key
# returns tuner_data position xxxxx,yyyyy,zzzzzz and actual reflection coefficient in real+jimaginary and magnitude+angle
	def get_tuner_position_from_reflection(self, frequency=None, requested_reflection=None, reflection_type='RI'):
		if 'complex' not in str(type(requested_reflection)): raise ValueError("ERROR! requested_reflection is not complex and must be complex")
		if frequency==None: raise ValueError("ERROR! no frequency given")
		if reflection_type!='MA' and reflection_type!='RI': raise ValueError("ERROR! no valid reflection type given")
		if reflection_type=='MA': requested_reflection=convertMAtoRI(requested_reflection.real,requested_reflection.imag)           # convert the magnitude and angle requested_reflection to real+jimaginary
		frequency=str(int(frequency))
		pos=min(self.tuner_data[frequency],key=lambda p:abs(self.tuner_data[frequency][p][0,0]-requested_reflection))             # find tuner motor positions which give an available tuner reflection coefficient closest to the one requested
		actual_reflectionRI=self.tuner_data[frequency][pos][0,0]                                                                    # actual reflection coefficient (real+jimaginary) = S11 of the tuner
		actual_reflectionMA=convertRItoMA(self.tuner_data[frequency][pos][0,0])                                                     # actual reflection coefficient where the real part is the magnitude and the imaginary part the angle in degrees
		return pos,actual_reflectionRI,actual_reflectionMA
###############################################################################################################################################################
# sets tuner_data position safely
# you MUST initialize tuner BEFORE calling this method!!!!!!!!!
# default position is the obtain Z0
# control of the second slug position not tested yet
# tunernumber tells which controller port the tuner_data is plugged into Legal values are 1 and 2
	def set_tuner_position(self,position="100,5000,5000"):
		#
		if self.tunernumber==1:
			car="M0"        # tuner carriage control motor
			p1="M1"         # tuner slug 1 motor
			p2="M2"         # tuner slug 2 motor
		elif self.tunernumber==2:
			car="M3"         # tuner carriage control motor
			p1="M4"         # tuner slug 1 motor
			p2="M5"         # tuner slug 2 motor
		else: raise ValueError("ERROR! Illegal tuner motor position number")
		# get requested tuner motor positions
		carposrq=int(position.split(',')[0])
		p1posrq=int(position.split(',')[1])
		p2posrq=int(position.split(',')[2])
		# now set tuner motor positions
		if carposrq!=self._get_tuner_motor_position(car):        # move carriage only if the requested position is not equal to the current position
			carpos=self._set_tuner_motor_position(requested_position=carposrq,motorID=car)
		if p1posrq!=self._get_tuner_motor_position(p1):
			p1pos=self._set_tuner_motor_position(requested_position=p1posrq,motorID=p1)
		if p2posrq!=self._get_tuner_motor_position(p2):
			p2pos=self._set_tuner_motor_position(requested_position=p2posrq,motorID=p2)
#####################################################################################################################################################################
# private method to set individual motor positions
	def _set_tuner_motor_position(self,requested_position=100,motorID=None):
		requested_position=int(requested_position)
		if motorID==None: raise ValueError("ERROR: must give tuner motor designator")
		if self.tunernumber==1:
			car="M0"        # tuner carriage control motor
			p1="M1"         # tuner slug 1 motor
			p2="M2"         # tuner slug 2 motor
		elif self.tunernumber==2:
			car="M3"         # tuner carriage control motor
			p1="M4"         # tuner slug 1 motor
			p2="M5"         # tuner slug 2 motor
		else: raise ValueError("ERROR! no legal tuner number given")
		### move carriage
		if motorID==car:  # this is the carriage motor so treat accordingly to prevent damage to the tuner , i.e. DO NOT MOVE carriage until slugs are positioned >= 100
			p1_pos=self._get_tuner_motor_position(p1)
			if p1_pos<100:  # then must ensure that slug position is set to a minimum of 100 BEFORE moving carriage
				self._setup_motor_position(motor=p1,pos=100)
				p1_pos=self._get_tuner_motor_position(p1)
				if p1_pos!=100: raise ValueError("ERROR! failed to move slug 1 to 100")
			# now set the 2nd slug to a safe position prior to moving carriage
			p2_pos=self._get_tuner_motor_position(p2)  # get slug #2 initial position (prior to move)
			if p2_pos<100:  # then must ensure that slug position is set to a minimum of 100 BEFORE moving carriage
				self._setup_motor_position(motor=p2,pos=100)
				p2_pos=self._get_tuner_motor_position(p2)
				if p2_pos!=100: raise ValueError("ERROR! failed to move slug 2 to 100")
			# now finally ready to move carriage
			#car_pos=self._get_tuner_motor_position(car)         # get initial carriage position
			if requested_position<100:
				self._setup_motor_position(motor=car,pos=0)
				car_pos=self._get_tuner_motor_position(car)
				if car_pos!=0: raise ValueError("ERROR! failed to move carriage to 0 for start of move")
			else:
				self._setup_motor_position(motor=car,pos=requested_position-100)
				car_pos=self._get_tuner_motor_position(car)
				if car_pos!=requested_position-100: raise ("ERROR! failed to move carriage to requested position for start of move")
			self._setup_motor_position(motor=car,pos=requested_position)
			car_pos=self._get_tuner_motor_position(car)
			if car_pos!=requested_position: raise ValueError("ERROR! failed to move carriage to requested position")
			pos=car_pos
		### move slug 1
		elif motorID==p1:
			p1_pos=self._get_tuner_motor_position(p1)
			if requested_position<100:
				self._setup_motor_position(motor=p1,pos=0)
				p1_pos=self._get_tuner_motor_position(p1)
				if p1_pos!=0: raise ValueError("ERROR! failed to move slug 1 to 0")
			else:
				self._setup_motor_position(motor=p1,pos=requested_position-100)
				p1_pos=self._get_tuner_motor_position(p1)
				if p1_pos!=requested_position-100: raise ("ERROR! failed to move slug 1 to requested position "+str(requested_position)+"-100")
			self._setup_motor_position(motor=p1,pos=requested_position)
			p1_pos=self._get_tuner_motor_position(p1)
			if p1_pos!=requested_position: raise ValueError("ERROR! failed to move slug 1 to requested position "+str(requested_position))
			pos=p1_pos
		### move slug 2
		elif motorID==p2:
			p2_pos=self._get_tuner_motor_position(p1)
			if requested_position<100:
				self._setup_motor_position(motor=p2,pos=0)
				p2_pos=self._get_tuner_motor_position(p2)
				if p2_pos!=0: raise ValueError("ERROR! failed to move slug 2 to 0")
			else:
				self._setup_motor_position(motor=p2,pos=requested_position-100)
				p2_pos=self._get_tuner_motor_position(p2)
				if p2_pos!=requested_position-100: raise ("ERROR! failed to move slug 2 to requested position "+str(requested_position)+"-100")
			self._setup_motor_position(motor=p2,pos=requested_position)
			p2_pos=self._get_tuner_motor_position(p2)
			if p2_pos!=requested_position: raise ValueError("ERROR! failed to move slug 2 to requested position "+str(requested_position))
			pos=p2_pos
		else: raise ValueError("ERROR! No legal motor designator given")
		return pos              # actual motor position of selected motor

# this following method is called only in self._set_tuner_motor_position()
	def _setup_motor_position(self, motor=None, pos=None):    # sets tuner motors' ramp and speed to best values (as used by Maury in their software)
		if motor==None: raise ValueError("ERROR! no motor specified")
		if pos==None: raise ValueError("ERROR! no motor position specified")
		pos=int(pos)
		if pos<0: raise ValueError("ERROR! requested position < 0")
		self.tuner_control.write(motor)
		self._poll_no_movement()
		self.tuner_control.write("I")
		self._poll_no_movement()
		self.tuner_control.write("F 5")
		self._poll_no_movement()
		self.tuner_control.write("S 225")
		self._poll_no_movement()
		self.tuner_control.write("R 80")
		self._poll_no_movement()
		self.tuner_control.write("Z 1")
		self._poll_no_movement()
		self.tuner_control.write("P "+str(pos))
		self._poll_movementonly()
		self.tuner_control.write("I")
		self._poll_no_movement()
####################################################################################################################################################################
# get current tuner motor position
	def _get_tuner_motor_position(self,motor=None):
		if motor==None: raise ValueError("ERROR! no motor specified")
		self.tuner_control.write(motor)
		self._poll_no_movement()
		self.tuner_control.write("I")
		self._poll_no_movement()
		ret=self.tuner_control.query("V 0")
		self._poll_no_movement()
		actualmotor=ret[:2] # this is the actual motor used
		if actualmotor!=motor: raise ValueError("ERROR! actual motor does not match that requested")
		motorpos=int(ret[3:])
		return motorpos
#####################################################################################################################################################################
# set tuner to minimize reflection coefficient (set to Z0)
	def set_tuner_Z0(self):
		self.set_tuner_position(position="100,5000,5000")
#####################################################################################################################################################################