# Cascade probestation control classes
# assumes that VISA has been set up
# output is VISA handle for Cascade 12000 probe station with Nucleus 4.1

#import visa
import time
from read_testplan import *
import sys
import os
from PyQt5 import QtCore, QtGui, QtWidgets
import random as r
settlingtime = 0.5


# auxiliary stage positions
aux1stageposX=85117
aux1stageposY=85969
#aux1stageposZ=4912
aux2stageposX=87496
aux2stageposY=-90917
#aux2stageposZ=5094
auxmaxdeltaxrange=4000
auxmaxdeltayrange=2700

class CascadeProbeStation:
	def __init__(self,rm=None,pathname=None,planname=None,dryrun=False,opticalcorrectionon='correction off'):
		if rm==None: ValueError("No VISA resouces handle provided")
		if pathname==None or not os.path.isdir(pathname): print("WARNING! supplied directory for test plan is invalid or does not exist")
		self.pathname=pathname
		if planname==None or not os.path.isdir(pathname): print("WARNING! supplied test plan file is invalid or does not exist")
		self.planname=planname
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
		while "TRUE" in self.__probe.query(":MOVE:DOWN? 2") and dryrun==False:
			message=QtWidgets.QMessageBox()
			message.setText("WARNING! USER MUST adjust probes in contact position and MUST start the probing with the probes in contact!\n Contact and adjust probes to proceed")
			message.exec_()
		self.userplan='yes'             # then user supplied probe plan
		# get waferprobe plan from file and instantiate test plan class tp
		if self.pathname!=None and self.planname!=None: self.tp=TestPlan(self.pathname,self.planname)
		# the following are the offset corrections used to correct for stage mechanical offsets which can happen
		# due to stage mechanical wear and other problems with stage positioning
		# Image recognition is used to provide these corrections to stage movements
		self.__offsetcorrectionX=0
		self.__offsetcorrectionY=0

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

	def dieindex(self):                                 # Find index of current die position of probes
		if self.userplan == "no":
			return (int(self.__probe.query(":MOV:PROBEPLAN:ABSOLUTE:INDEX?").strip('\n').split(" ")[0]))
		else:
			raise ValueError("ERROR! Cannot get die index because the probe plan is user defined")

	def dieXindex(self):                                 # Find X index of current die position of probes
		if self.userplan == "no":
			return (int(self.__probe.query(":MOV:PROBEPLAN:ABSOLUTE:DIE?").strip('\n').split(" ")[0]))
		else:
			raise ValueError("ERROR! Cannot get die X index because the probe plan is user defined")

	def dieYindex(self):                                 # Find Y index of current die position of probes
		if self.userplan == "no":
			return (int(self.__probe.query(":MOV:PROBEPLAN:ABSOLUTE:DIE?").strip('\n').split(" ")[1]))
		else:
			raise ValueError("ERROR! Cannot get die Y index because the probe plan is user defined")

	def subsiteindex(self):                                 # Find index of subsite position of probes
		if self.userplan == "no":
			return (int(self.__probe.query(":MOV:PROBEPLAN:ABSOLUTE:SUBSITE?").strip('\n')))
		else:
			raise ValueError("ERROR! Cannot get sub site index because the probe plan is user defined")


	def numberofdie(self):                                 # Find number of testable die
		if self.userplan == "no":
			return (int(self.__probe.query(":PROBEPLAN:NTES?").strip('\n')))
		else:
			raise ValueError("ERROR! Cannot get the number of die because the probe plan is user defined")

	def numberofsubsites(self):                                 # Find number of subsites in each die
		if self.userplan == "no":
			return (int(self.__probe.query(":PROBEPLAN:NSUB?").strip('\n')))
		else:
			raise ValueError("ERROR! Cannot get the number of subsites because the probe plan is user defined")

	def get_probingstatus(self):			# are we still probing the wafer or are we finished?
		if self.userplan=="no":
			if self.subsiteindex()>=self.numberofsubsites() and self.dieindex()>=self.numberofdie():
				return "done wafer"
			else:
				return "probing wafer"
		else:
			return self.tp.probestatus
	####################################################################################################################
	# movement methods
	####################################################################################################################
	# move to absolute X and Y wafer user coordinates
	def move_XY(self,X=None,Y=None):				#	Move to location specified by the current plan device/region index array, self.tp.leveldev[]
		self.move_separate()        # probes must be separated from wafer to perform autocorrection of alignment
		#self.__zpos_noncontact = int(self.__probe.query(":MOV:ABS? 2").split()[2])     # find the Z position for probe separate position and set the probes to separate just after the move
		self.__probe.write("*CLS")
		self.__probe.write(":MOV:ABS 2 "+str(int(X))+" "+str(int(Y))+" none"+";*OPC")
		self.__cascadehandshake(settlingtime)		# set up to compensate stage for mechanical stage movement errors and/or thermal expansion at the site we just moved to IF SELECTED to do so
		# add correction into stage movement to correct for mechanical errors and/or thermal effects. Correction will be =0 if correction is not being used
		# if self.correctionon.lower()=="on" or self.correctionon.lower()=="correction on" or self.correctionon.lower()=="yes" or self.correctionon.lower()=="correctionon":
		# 	# then get offset of the alignment due to mechnical stage error from the microscope image. Must have set up image recognition and train image first!
		# 	#self.move_separate()        # probes must be separated from wafer to perform autocorrection of alignment
		# 	# try to acquire a lock on a recognized pattern for autoalignment correction
		# 	deltaX,deltaY,self.__offsetcorrectionquality=map(float,self.__probe.query(":VIS:SEAR:TARG").split())
		# 	notries=0
		# 	while self.__offsetcorrectionquality<900 and notries<10:    # if necessary, try several times to register a good visual image match to target
		# 		deltaX,deltaY,self.__offsetcorrectionquality=map(float,self.__probe.query(":VIS:SEAR:TARG").split())
		# 		notries +=1
		# 	if self.__offsetcorrectionquality<800.:        # is image recognition quality acceptable? (best = 1000, worst=0)
		# 		deltaX=0.
		# 		deltaY=0.
		# 		print("WARNING! NO=ZERO change in offset correction applied for next stage move because could not recognize training pattern in field of view!!!!!!!!!!!")
		#
		# 	#print("dx dy match quality",deltaX,deltaY,self.__offsetcorrectionquality) # debug
		# 	self.__offsetcorrectionX+=int(deltaX)       # set corrected coordinates for next probe site
		# 	self.__offsetcorrectionY+=int(deltaY)       # set corrected coordinates for next probe site
		# 	notries=0
		# 	while (abs(deltaX)>5. or abs(deltaY)>5.) and notries<10:          # then too much error and must correct within the current probesite we get a set maximum number of tries
		# 		# get new offsets based on machine vision results
		# 		deltaX,deltaY,self.__offsetcorrectionquality=map(float,self.__probe.query(":VIS:SEAR:TARG").split())
		# 		notries=0
		# 		while self.__offsetcorrectionquality<900 and notries<10:        # if necessary, try several times to register a good visual image match to target
		# 			deltaX,deltaY,self.__offsetcorrectionquality=map(float,self.__probe.query(":VIS:SEAR:TARG").split())
		# 			notries +=1
		# 		self.__probe.write("*CLS")
		# 		self.__probe.write(":MOV:REL 2 "+str(deltaX)+" "+str(deltaY)+" 0;*OPC")         # move to the new offset to try to correct excessive offset problem
		# 		self.__cascadehandshake(settlingtime)
		# 		print("WARNING: relative move ",notries,deltaX,deltaY)          #debug
		# 		notries +=1
		# 	if abs(deltaX)>10. or abs(deltaY)>10. or self.__offsetcorrectionquality<800:      # error out if we still cannot correct misalignment
		# 		raise ValueError("ERROR! autocorrection offset too large - may be locking on wrong pattern! Quitting!")
		# 	print ("x and y offset correction",self.__offsetcorrectionX,self.__offsetcorrectionY) # debug
		# else:   # set offset correction to zero because we are not using correction
		# 	self.__offsetcorrectionX=0
		# 	self.__offsetcorrectionY=0
		self.move_contact()     # be sure to leave probes in contact to enable measurements after the move
	####################################################################################################################
####################################################################################################################
	# move to absolute X and Y wafer user coordinates without contacting wafer. Used for dry run tests
	def move_XY_nocontact(self,X=None,Y=None):				#	Move to location specified by the current plan. Do not contact wafer
		self.move_separate()        # probes must be separated from wafer to perform autocorrection of alignment
		#self.__zpos_noncontact = int(self.__probe.query(":MOV:ABS? 2").split()[2])     # find the Z position for probe separate position and set the probes to separate just after the move
		self.__probe.write("*CLS")
		self.__probe.write(":MOV:ABS 2 "+str(int(X))+" "+str(int(Y))+" none"+";*OPC")
		self.__cascadehandshake(settlingtime)		# set up to compensate stage for mechanical stage movement errors and/or thermal expansion at the site we just moved to IF SELECTED to do so
		#self.move_separate()     # be sure to leave probes in contact to enable measurements after the move
	####################################################################################################################
	# move to absolute X and Y wafer chuck coordinates
	def move_XY_chuck(self,X=None,Y=None):				#	Move to location specified by the current plan device/region index array, self.tp.leveldev[]
		self.move_separate()        # probes must be separated from wafer to perform autocorrection of alignment
		self.__probe.write("*CLS")
		self.__probe.write(":MOV:ABS:OPT 2 "+str(int(X))+" "+str(int(Y))+" none stage on on"+";*OPC")
		self.__cascadehandshake(settlingtime)		# set up to compensate stage for mechanical stage movement errors and/or thermal expansion at the site we just moved to IF SELECTED to do so
		self.move_contact()     # be sure to leave probes in contact to enable measurements after the move
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

	def move_firstdie(self):                                        # move to the first testable site on the wafer
		if self.userplan=="yes":									# has the user defined a probe plan?
			for il in range(0,len(self.tp.leveldev)):				# send plan index to all zeros
				self.tp.leveldev[il]=0
			self.move_plan_index()									# now move probes
		else:														# if not, then use the plan supplied by Cascade Nucleus
			self.__probe.write("*CLS")
			self.__probe.write(":MOV:PROBEPLAN:FIRST:DIE 2;*OPC")                   # set probe to move to the next die on the wafer
		self.__cascadehandshake(settlingtime)

	def move_nextdie(self):                                 # move to next testable die on the wafer Nucleus ONLY!
		if self.userplan=="no":
			self.__probe.write("*CLS")
			self.__probe.write(":MOV:PROBEPLAN:NEXT:DIE 2;*OPC")                   # set probe to move to the next die on the wafer
			self.__cascadehandshake(settlingtime)
		else:
			print("WARNING! No move done via move_nextdie() because this is a Nucleus only move and you have loaded a test plan file!")

	def move_firstsub(self):                                 # move to first testable subsite on the current die on the wafer
		if self.userplan=="no":
			self.__probe.write("*CLS")
			self.__probe.write(":MOV:PROBEPLAN:FIRST:SUBSITE 2;*OPC")                   # set probe to move to the next die on the wafer
			self.__cascadehandshake(settlingtime)
		else:
			print("WARNING! No move done via move_firstsub() because this is a Nucleus only move and you have loaded a test plan file!")


	def move_nextsub(self):                                 # move to next testable subsite on the current die on the wafer
		if self.userplan=="no":								# no means no user-defined test probe plan loaded Use Nucleus
			self.__probe.write("*CLS")
			self.__probe.write(":MOV:PROBEPLAN:NEXT:SUBSITE 2;*OPC")                   # set probe to move to the next die on the wafer
			self.__cascadehandshake(settlingtime)
		else:
			print("WARNING! No move done via move_nextsub() because this is a Nucleus only move and you have loaded a test plan file!")

	def move_nextsite(self):                 # move to next testable device on the current die on the wafer
		if self.userplan=="yes":				# has the user defined a probe plan?
			if self.tp.probetestlevel!=None: r= self.tp.movenextsite_testprobes()		# attempt to move self.tp.leveldev[] index to the next probeable test site.
			else: r= self.tp.movenextsite()		# attempt to move self.tp.leveldev[] index to the next probeable test site.
			self.move_plan_index()				# actually perform the mechanical move according to the new self.tp.leveldev[] index values
			return
		else:
			self.__probe.write("*CLS")
			self.__probe.write(":MOV:PROBEPLAN:NEXT:SITE 2;*OPC")    # set probe to move to the next die on the wafer
			self.__cascadehandshake(settlingtime)
			return

	def move_referencepos(self):							# move back to reference position.
		self.__probe.write("*CLS")
		self.__probe.write(":MOV:ALIGN;*OPC")				# set probe to reference start position on wafer
		self.__cascadehandshake(settlingtime)
	###################################################################################################
	def move_plan_index(self):				#	Move to location specified by the current plan device/region index array, self.tp.leveldev[]
		if self.userplan == "yes":
			move=False
			#### skip over actively excluded sites
			if len(self.tp.selecteddevices)>0:
				self.tp.reset_to_first_site()                       # reset pointer to first device site so we can scan entire wafer for the next selected devices
				self.tp.probestatus="probing wafer"
			while move==False and self.tp.get_probestatus()=='probing wafer':				# keep jumping the move pointer, i.e. wafer device locations until we hit a valid move
				if self.devicename()[0]=="_": devicen=self.devicename()[1:]          # remove leading _ from devicename if it exists
				else: devicen=self.devicename()
				move=True
				if len(self.tp.selecteddevices)>0:
					if self.tp.selecteddevices_index>=len(self.tp.selecteddevices):         # then we are done probing
						self.tp.probestatus="done wafer"
					elif self.tp.selecteddevices[self.tp.selecteddevices_index]!=devicen:
					#elif self.tp.selecteddevices[self.tp.selecteddevices_index] not in devicen:     # is the selected device either the device itself or a parent device? All the devices under the parent are selected
						#print(self.devicename(),devicen)
						move=False
						self.tp.movenextsite()              # move pointer to next site - this is NOT a mechanical move, just a pointer move
						if not self.tp.get_probestatus()=='probing wafer': # move to the next selected device if we've exhausted the wafer map search
							self.tp.selecteddevices_index+=1
						self.tp.probestatus="probing wafer"
					else:
						move=True
						self.tp.selecteddevices_index+=1

				#r= self.tp.movenextsite()		# move self.tp.leveldev[] index to the next probeable test site.
				# determine if the proposed move is to an excluded site or device?

				for ex in self.tp.get_exclusions(): # ex is an array of level designators to exclude from measurements
					# if self.devicename()[0]=="_": devicen=self.devicename()[1:]          # remove leading _ from devicename if it exists
					# else: devicen=self.devicename()
					mvf=False
					for tex in ex:		# look at each element of the exclusion all must match to exclude device
						if tex not in self.devicename(): mvf=True # test to see if the devicename is among those excluded from probing
					if mvf==False:
						move=False		# if the proposed move fits any one of the exclusions then move the counter to the next site without moving or probing
						r= self.tp.movenextsite()		# move self.tp.leveldev[] index to the next probeable test site.
			if self.tp.get_probestatus()!='probing wafer':
				return	# no valid sites left to probe
			##### end of skip actively excluded sites
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
				#self.move_separate()        # probes must be separated from wafer to perform autocorrection of alignment
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
			#quit()						#debug
			self.move_contact()     # be sure to leave probes in contact to enable measurements after the move
		else:
			print("WARNING: NO MOVEMENT DONE because there is no user-defined probeplan (from move_plan_index() in cascade.py)")
	####################################################################################################################
	def devicename(self):		# Return the devicename from the user-defined probe test plan IF and ONLY IF a user-defined probe test plan was loaded
		if self.userplan == "no":				# do we have a user-defined probe test plan loaded?
			print("ERROR! No user defined probe test plan file is loaded No devicename will be returned!")
			return "NONE"
		else:
		# return devicename built from probe test plan and current probe position
			#devname = self.tp.tpname[-1][self.tp.leveldev[1]]
			devname=""
			for il in range(len(self.tp.leveldev)-1,-1,-1):		# form devicename from all device levels
			# note that self.leveldev[il] contains the index of the current device under test (DUT) at the mask level index il
				#print "tp.tpname, il",self.tp.tpname[il][self.tp.leveldev[il]],il #debug
				devname+="_"+self.tp.tpname[il][self.tp.leveldev[il]]
			return devname
	####################################################################################################################
	####################################################################################################################
	# this method is used to obtain a list of the devicenames of the level level-1
	# in particular, it's used with the default value of level-1 to return all the device names of devices that are simultaneously probed
	def devicenamesatlevel(self,level=1):		# Return the devicenames under the level specified from the user-defined probe test plan IF and ONLY IF a user-defined probe test plan was loaded
		if self.userplan == "no":				# do we have a user-defined probe test plan loaded?
			print("ERROR! No user defined probe test plan file is loaded No devicename will be returned!")
			return "NONE"
		else:
			#if level<1: raise ValueError("ERROR! level<1 level specified must be >1 usually it's 1")
		# return devicenames built from probe test plan and current probe position
			#devname = self.tp.tpname[-1][self.tp.leveldev[1]]
			devnamelevel=""
			for il in range(len(self.tp.leveldev)-1,level-1,-1):		# form devicename at the specified level
			# note that self.leveldev[il] contains the index of the current device under test (DUT) at the mask level index il
				#print "tp.tpname, il",self.tp.tpname[il][self.tp.leveldev[il]],il #debug
				devnamelevel+="_"+self.tp.tpname[il][self.tp.leveldev[il]]
			devnames=["".join([devnamelevel,"_",n]) for n in self.tp.tpname[level-1]]
			return devnames
	####################################################################################################################
	# this function is NOT YET READY DO NOT USE YET!
	def dryrun_alltestablesites(self,timeatsite):						# run through all testable sites to be sure probing is OK
		self.move_referencepos()										# move to reference position
		numberofsites = int(self.numberofdie()*self.numberofsubsites())
		print ("The total number of sites is:",numberofsites)
		for ii in range(0,numberofsites):
			print ("probing subsite ", self.subsiteindex(),"in die number ",self.dieindex()," die X index = ",self.dieXindex()," die Y index = ",self.dieYindex(),"xpos = ",self.x(),"ypos =",self.y())
			time.sleep(timeatsite)
			self.move_nextsite()
		self.move_referencepos()
		print("done probing dry run, setup for actual test")
		try: input("Press Enter when ready to start real test")
		except SyntaxError:
			pass
	####################################################################################################################
	# handshaking and probestation settling
	# WARNING !!! WARNING !!! WARNING !!!!
	# Call this function ONLY immediately after performing a Cascade probe move. Calling it at any other time WILL result in an infinite loop
	def __cascadehandshake(self,settlingtime):
		while (int(self.__probe.query("*ESR?")) & 1) == 0:     # be sure that probe chuck is in final position before issuing another command
			continue
		time.sleep(settlingtime)

	#########################################################################################################################
	# probe clean operation
	# operator MUST set up correct Z-contact positions for each of the two aux positions using Nucleus
	# aux1 is sticky cleaner aux1stageposX=85117, aux1stageposY=85969, aux1stageposZ=4912
	# aux2 is abrasive cleaner at aux2stageposX=87496, aux2stageposY=-90917, aux2stageposZ=5094
	# deltaxrange is the +- random offset in the x-direction for the probe contact point on the cleaning substrate
	# deltayrange is the +- random offset in the y-direction for the probe contact point on the cleaning substrate
	# number_cleaning_contacts is the number of probe contacts performed on the aux substrate to clean the probe tips
	def cleanprobe(self,auxstagenumber=1,number_cleaning_contacts=3,deltaxrange=auxmaxdeltaxrange,deltayrange=auxmaxdeltayrange):
		deltaxrange=abs(deltaxrange)
		deltayrange=abs(deltayrange)
		if deltaxrange>auxmaxdeltaxrange: raise ValueError("ERROR! aux random range of X too large")
		if deltayrange>auxmaxdeltayrange: raise ValueError("ERROR! aux random range of Y too large")
		posintX,posintY,posintZ=initialstagepos=self.__probe.query(":MOVE:ABS? 2").split()            # get user coordinate position prior to the probe clean to use when returning to the wafer
		randomdeltax=deltaxrange*2.*(r.random()-0.5)
		randomdeltay=deltayrange*2.*(r.random()-0.5)

		if auxstagenumber==1:           # this is the auxiliary stage #1 (stage closest to the front of the prober
			self.move_XY_chuck(X=aux1stageposX+randomdeltax,Y=aux1stageposY+randomdeltay)     # move stage to contact aux1 cleaning pad
			for i in range(0,number_cleaning_contacts-1):       # perform contact-separate cleaning motions to clean probe tips
				self.move_separate()
				self.move_contact()
		elif auxstagenumber==2:           # this is the auxiliary stage #2 (stage near the back of the prober
			self.move_XY_chuck(X=aux2stageposX+randomdeltax,Y=aux2stageposY+randomdeltay)     # move stage to contact aux2 cleaning pad
			for i in range(0,number_cleaning_contacts-1):       # perform contact-separate cleaning motions to clean probe tips
				self.move_separate()
				self.move_contact()
		elif auxstagenumber==12:        # clean on aux1 then aux2 stages in sequence
			self.move_XY_chuck(X=aux1stageposX+randomdeltax,Y=aux1stageposY+randomdeltay)     # move stage to contact aux1 cleaning pad
			for i in range(0,number_cleaning_contacts-1):       # perform contact-separate cleaning motions to clean probe tips
				self.move_separate()
				self.move_contact()
			self.move_XY_chuck(X=aux2stageposX+randomdeltax,Y=aux2stageposY+randomdeltay)     # move stage to contact aux2 cleaning pad
			for i in range(0,number_cleaning_contacts-1):       # perform contact-separate cleaning motions to clean probe tips
				self.move_separate()
				self.move_contact()
		elif auxstagenumber==21:        # clean on aux1 then aux2 stages in sequence
			self.move_XY_chuck(X=aux2stageposX+randomdeltax,Y=aux2stageposY+randomdeltay)     # move stage to contact aux1 cleaning pad
			for i in range(0,number_cleaning_contacts-1):       # perform contact-separate cleaning motions to clean probe tips
				self.move_separate()
				self.move_contact()
			self.move_XY_chuck(X=aux1stageposX+randomdeltax,Y=aux1stageposY+randomdeltay)     # move stage to contact aux2 cleaning pad
			for i in range(0,number_cleaning_contacts-1):       # perform contact-separate cleaning motions to clean probe tips
				self.move_separate()
				self.move_contact()
		else: raise ValueError("ERROR! Illegal aux number")
		self.move_XY(X=posintX,Y=posintY)                   # move stage back to wafer at current wafer probe position
		return posintX,posintY
	###############################################################################################################################


