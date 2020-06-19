# casacade 12K controller for database-driven probing
import time
from read_testplan import *
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import os

settlingtime = 0.5
class CascadeProbeStation:
	def __init__(self,rm=None,pathname=None,planname=None,opticalcorrectionon='correction off'):
		if rm==None: ValueError("No VISA resouces handle provided")
		if pathname==None or not os.path.isdir(pathname): raise ValueError("supplied directory for test plan is invalid or does not exist")
		else: self.pathname=pathname
		if planname==None or not os.path.isdir(pathname): raise ValueError("supplied test plan file is invalid or does not exist")
		else: self.planname=planname
		self.correctionon=opticalcorrectionon                   # use optical recognition to align chuck to pads if turned on
		try:
			self.__probe = rm.open_resource('GPIB0::28::INSTR')
		except:
			print ("ERROR on Cascade Probe station setup: Could not find the Cascade Probe station on the GPIB")
			print ("Check to make sure that the Cascade probe station computer is on and running Nucleus Stopping Now!")
			quit()
		self.__probe.query_delay=0.5            # set up query delay to prevent errors added June 15, 2017 9:30AM increased from 0.2 to 0.5 June 20, 2017
		# the following is to protect the probes from scraping the wafer/chuck should the user forget to adjust the probes in the contact state
		app=QtWidgets.QApplication(sys.argv)
		while "TRUE" in self.__probe.query(":MOVE:DOWN? 2"):
			message=QtWidgets.QMessageBox()
			message.setText("WARNING! USER MUST adjust probes in contact position and MUST start the probing with the probes in contact!\n Contact and adjust probes to proceed")
			message.exec_()
		self.userplan='yes'             # then user supplied probe plan
		# get waferprobe plan from file and instantiate test plan class tp
		self.tp=TestPlan(self.pathname,self.planname)
		# the following are the offset corrections used to correct for stage mechanical offsets which can happen
		# due to stage mechanical wear and other problems with stage positioning
		# Image recognition is used to provide these corrections to stage movements
		self.__offsetcorrectionX=0
		self.__offsetcorrectionY=0
		#probe.write("*RST")
		self.__probe.timeout = 5000
		self.__probe.write("$:SET:RESP OFF")
		self.__probe.write("$:SET:MODE SUMMIT")

		self.__probe.write(":SET:UNIT METRIC")
		self.__probe.write("*CLS")
		self.move_referencepos()							# move to reference position
		self.__probe.write(":PROB:REF 0 0")
		self.__probe.write(":PROB:ORIGIN 0 0")
		self.__probe.write(":SET:PRES 2 0 0")               # set the reference position to x=0 y=0 on the wafer
		self.move_contact()				# do this to find the correct Z-position
		self.__zpos_contact = int(self.__probe.query(":MOV:ABS? 2").split()[2])     # find and reuse correct Z position for contact
		self.__probe.write("*CLS")
		self.move_separate()
		self.lockstage()                                    # always lock stage to nearly eliminate stage x-y drift during probing
	####################################################################################################################
	def lockstage(self):            # locks stage to prevent manual motion via knobs - only auto motion allowed
		self.__probe.write(":SET:MANUAL 2 OFF")      # lock stage into AUTO MODE
	def unlockstage(self):          # unlocks stage permitting manual x-y motion with knobs. This is the opposite of lockstage()
		self.__probe.write(":SET:MANUAL 2 ON")      # lock stage into MANUAL MODE
	def wafername(self):			# gets the current wafer name (as read from the probe test plan file)
		return self.tp.wafername

	def x(self):                                        # find x coordinate in um for current probe position
		return (float(self.__probe.query(":mov:abs? 2").strip('\n').split(" ")[0]))

	def y(self):                                        # find y coordinate in um for current probe position
		return (float(self.__probe.query(":mov:abs? 2").strip('\n').split(" ")[1]))
####################################################################################################################
	# movement methods
	####################################################################################################################
	def move_contact(self):
		self.__probe.write("*CLS")
		self.__probe.write(":MOV:CONT 2;*OPC")                   # set probe to contact the probes
		self.__cascadehandshake(settlingtime)
	def get_isincontact(self):
		return self.__probe.query(":MOVE:DOWN? 2")

	def move_separate(self):
		self.__probe.write("*CLS")
		self.__probe.write(":MOV:SEP 2;*OPC")                   # separate probes from wafer
		self.__cascadehandshake(settlingtime)

	def move_align(self):
		self.__probe.write("*CLS")
		self.__probe.write(":MOV:ALIGN;*OPC")                   # set probe to reference start position on wafer
		self.__cascadehandshake(settlingtime)

	def move_referencepos(self):							# move back to reference position.
		self.__probe.write("*CLS")
		self.__probe.write(":MOV:ALIGN;*OPC")				# set probe to reference start position on wafer
		self.__cascadehandshake(settlingtime)
###################################################
# move to absolute coordinates x,y
# x and y are wafer coordinates in um
	def move_abs_xy(self,x,y):
		# move to next site as commanded with probes in noncontact position
		self.move_separate()        # probes must be separated from wafer to perform autocorrection of alignment
		self.__zpos_noncontact = int(self.__probe.query(":MOV:ABS? 2").split()[2])     # find the Z position for probe separate position and set the probes to separate just after the move
		self.__probe.write("*CLS")
		self.__probe.write(":MOV:ABS 2 "+str(self.tp.x()+self.__offsetcorrectionX)+" "+str(self.tp.y()+self.__offsetcorrectionY)+" "+str(self.__zpos_noncontact)+";*OPC")
		self.__cascadehandshake(settlingtime)
		# set up to compensate stage for mechanical stage movement errors and/or thermal expansion at the site we just moved to IF SELECTED to do so
		# add correction into stage movement to correct for mechanical errors and/or thermal effects. Correction will be =0 if correction is not being used
		if self.correctionon.lower()=="on" or self.correctionon.lower()=="correction on" or self.correctionon.lower()=="yes" or self.correctionon.lower()=="correctionon":
			# then get offset of the alignment due to mechnical stage error from the microscope image. Must have set up image recognition and train image first!
			# try to acquire a lock on a recognized pattern for autoalignment correction
			deltaX,deltaY,self.__offsetcorrectionquality=map(float,self.__probe.query(":VIS:SEAR:TARG").split())
			notries=0
			while self.__offsetcorrectionquality<900 and notries<10:    # if necessary, try several times to register a good visual image match to target
				deltaX,deltaY,self.__offsetcorrectionquality=map(float,self.__probe.query(":VIS:SEAR:TARG").split())
				notries +=1
			if self.__offsetcorrectionquality<800.:        # is image recognition quality acceptable? (best = 1000, worst=0)
				deltaX=0.
				deltaY=0.
				print("WARNING! NO=ZERO change in offset correction applied for next stage move because could not recognize training pattern in field of view!!!!!!!!!!!")

			#print("dx dy match quality",deltaX,deltaY,self.__offsetcorrectionquality) # debug
			self.__offsetcorrectionX+=int(deltaX)       # set corrected coordinates for next probe site
			self.__offsetcorrectionY+=int(deltaY)       # set corrected coordinates for next probe site
			notries=0
			while (abs(deltaX)>5. or abs(deltaY)>5.) and notries<10:          # then too much error and must correct within the current probesite we get a set maximum number of tries
				# get new offsets based on machine vision results
				deltaX,deltaY,self.__offsetcorrectionquality=map(float,self.__probe.query(":VIS:SEAR:TARG").split())
				notries=0
				while self.__offsetcorrectionquality<900 and notries<10:        # if necessary, try several times to register a good visual image match to target
					deltaX,deltaY,self.__offsetcorrectionquality=map(float,self.__probe.query(":VIS:SEAR:TARG").split())
					notries +=1
				self.__probe.write("*CLS")
				self.__probe.write(":MOV:REL 2 "+str(deltaX)+" "+str(deltaY)+" 0;*OPC")         # move to the new offset to try to correct excessive offset problem
				self.__cascadehandshake(settlingtime)
				print("WARNING: relative move ",notries,deltaX,deltaY)          #debug
				notries +=1
			if abs(deltaX)>10. or abs(deltaY)>10. or self.__offsetcorrectionquality<800:      # error out if we still cannot correct misalignment
				raise ValueError("ERROR! autocorrection offset too large - may be locking on wrong pattern! Quitting!")
			print ("x and y offset correction",self.__offsetcorrectionX,self.__offsetcorrectionY) # debug
		else:   # set offset correction to zero because we are not using correction
			self.__offsetcorrectionX=0
			self.__offsetcorrectionY=0
		self.move_contact()     # be sure to leave probes in contact to enable measurements after the move
####################################################################################################################
	# handshaking and probestation settling
	# WARNING !!! WARNING !!! WARNING !!!!
	# Call this function ONLY immediately after performing a Cascade probe move. Calling it at any other time WILL result in an infinite loop
	def __cascadehandshake(self,settlingtime):
		while (int(self.__probe.query("*ESR?")) & 1) == 0:     # be sure that probe chuck is in final position before issuing another command
			continue
		time.sleep(settlingtime)