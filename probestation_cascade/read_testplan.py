__author__ = 'PMarsh Carbonics'
# Read Hierarchical testplan from file
# the testplan is of the format
# Maskset name !
# Maskset revision number !
# Date of maskset !
# Wafer name !
##
#$$level 1
#name/location of device 1 ! dev nn nn
#name/location of device 2 ! dev nn nn
# .
# .
# .
##
#$$level 2
#name/location of #finger,s gate length*100nm, ungated region*10nm ! nn nn
#name/location of #finger,s gate length*100nm, ungated region*10nm ! nn nn
# .
# .
# .
##
#$$level 3
#name/location of rows columns ! 11 nn nn
#name/location of rows columns ! 12 nn nn
#name/location of rows columns ! 21 nn nn
#name/location of rows columns ! 22 nn nn
##
#$$level 4
#name/location of lower left subquadrant ! Q1 nn nn
#name/location of upper left subquadrant ! Q2 nn nn
#name/location of upper left subquadrant ! Q3 nn nn
#name/location of upper left subquadrant ! Q4 nn nn
#$$level 5
#name/location of lower left quadrant ! Q1 nn nn
#name/location of upper left quadrant ! Q2 nn nn
#name/location of upper left quadrant ! Q3 nn nn
#name/location of upper right quadrant ! Q4 nn nn
######################################
# the above represents an example.
# the $$level indicates a step to the next higher hierarchical level with increasing numerical levels being of increasing hierarchy
# the wafer 0,0 location should be set on the lower leftmost location on the wafer. In all cases above, nn nn refers to the relative x and y positions
# on the wafer. Positions at the highest level (in the above example - level 5 is the highest) are absolute positions relative to the (0,0) reference
# position set by the operator using Nucleus, on the wafer. All lower-level positions are given as relative offsets to the next highest level.
# Absolute probe position on the wafer is calculated as the sum of all current nn nn coordinates of all the levels.

import os
import collections as col
from utilities import sub
class TestPlan:
	def __init__(self,pathname,planname):            # the pathname is the full directory name (minus the devicename) and the planname is the probe plan name
		pathname = pathname+sub("TESTPLAN")
		self.probestatus = "probing wafer"
		self.probetestlevel=None									# could be set to a hierarchial level in which probes have their resistance tested
		self.selecteddevices=[]                                      # possible list of devices to be tested - to enable selection of testing only specific device e.g. champion devices
		self.selecteddevices_index=0                                # index of selected devices
		try: filelisting = os.listdir(pathname)
		except:
			print ("ERROR directory", pathname, "does not exist: returning from readtestplan in device_parameter_request.py")
			quit()
		for filetp in filelisting:
			if filetp.endswith("plan.csv") and planname in filetp:
				self.fullfilename = pathname+"/"+filetp				# form full devicename (path+devicename) of test plan file
				try: ftplan=open(self.fullfilename,'r')
				except:
					print ("ERROR from readtestplan() in read_testplan.py: cannot open file: ",self.fullfilename)
					fullfilename="cannot open file"
					quit()
		try: self.fullfilename
		except:
			raise ValueError("ERROR! no valid test plan file found!")
		tpfilelines = [a for a in ftplan.read().splitlines()]             # tpfilelines is a string array of the lines in the file
		self.devsizeX = col.deque()									# X size of device or reticle in um vs level
		self.devsizeY = col.deque()									# Y size of device or reticle in um vs level
		self.devactualX = col.deque()								# actual X location of device - defaults to self.tpx if not specified
		self.devactualY = col.deque()								# actual Y location of device - defaults to self.tpy if not specified
		# self.TLMlength = col.deque()								# actual TLM length in um - meaningful only at the device level (usually level 0)
		# self.devwidth = col.deque()									# device total gate width in um - meaningful only at the device level (usually level 0)

		self.tpname = col.deque()									# name of the device or division
		self.tpx = col.deque()										# x location of the device or division's probe pads or actual location if self.devactualX not specified
		self.tpy = col.deque()										# y location of the device or division's probe pads or actual location if self.devactualY not specified
		self.excluded_sites = col.deque()							# excluded sites' partial names. If a full device name contains an exclusion name, then it is not probed
		level=-1													# keep track of mask device level
		#if not "device list" in tpfilelines[0].lower()              # is this a
		for fileline in tpfilelines:
			if not "#" in fileline:
				if "maskset name" in fileline:
					self.maskname = fileline.split("!")[1].strip()
				elif "maskset revision number" in fileline:
					self.maskrevnumber = fileline.split("!")[1].strip()
				elif "maskset date" in fileline:
					self.maskyear = int(fileline.split("!")[1].split()[0])
					self.maskmonth = int(fileline.split("!")[1].split()[1])
					self.maskday = int(fileline.split("!")[1].split()[2])
				elif "wafer name" in fileline:
					self.wafername = fileline.split("!")[1].strip()

				# sites to be probed (provided they aren't specifically excluded
				elif ("$$" in fileline) and ("level" in fileline):				# now we are at a probe plan level
					# append a new probe plan level indicies are [level][device in current level]
					self.tpname.append([])
					self.tpx.append([])
					self.tpy.append([])
					self.devsizeX.append([])
					self.devsizeY.append([])
					self.devactualX.append([])
					self.devactualY.append([])
					level+=1												# move to next level in mask device hierarchy
				elif len(fileline.split())>2 and ("!" not in fileline) and ("$" not in fileline):		# does this line contain sufficient data? - at least three entries?
				# append probe devices or divisions on the current level
					#print("from line 112 in read_testplan.py fileline ", fileline)
					self.tpname[-1].append(fileline.split()[0].strip())				# Level or device name
					self.tpx[-1].append(int(fileline.split()[1].strip()))			# X location in um of level or device
					self.tpy[-1].append(int(fileline.split()[2].strip()))			# Y location in um of level or device
					if "sizex" in fileline and "sizey" in fileline:		# device sizes specified
						self.devsizeX[-1].append(int(fileline.split()[fileline.split().index('sizex')+1].strip()))
						self.devsizeY[-1].append(int(fileline.split()[fileline.split().index('sizey')+1].strip()))
					else:
						self.devsizeX[-1].append(0)
						self.devsizeY[-1].append(0)
					if "actualX" in fileline and "actualY" in fileline:	# these are the actual device locations in the hierarchy
						self.devactualX[-1].append(int(fileline.split()[fileline.split().index('actualX')+1].strip()))
						self.devactualY[-1].append(int(fileline.split()[fileline.split().index('actualY')+1].strip()))
					else:
						self.devactualX[-1].append(self.tpx[-1][-1])
						self.devactualY[-1].append(self.tpy[-1][-1])
					if "proberesistancetest" in fileline:							# then this is a probe resistance test
						self.probetestX=int(fileline.split()[1].strip())			# probe X relative position (in probetest level)
						self.probetestY=int(fileline.split()[2].strip())			# probe Y relative position (in probetest level)
						self.probetestlevel=level									# hierarchial mask level of probe test

				# sites (devices and/or levels) to be specifically excluded
				elif ("!" in fileline) and ("excluded" in fileline):
					self.excluded_sites.append([l.strip() for l in fileline.split("!")[1].split()])				# load name to be excluded from probing
				# list of devices to be tested. If any devices are in the list, then we test ONLY those devices, otherwise test all the devices specified by the wafer plan itself
				elif "select_device" in fileline.lower():                           # then we are in the mode of testing only selected devices and this line contains a selected device name
					self.selecteddevices.append(fileline.split()[1])                # get the name of the device selected for testing
		ftplan.close()

		if len(set(self.tpx[0]))==1 and len(set(self.tpy[0]))==1:			# look through all devices at level 0 to see if they all have the same probe location
			self.multiprobing=True			# have just one X Y coordinate pair for all devices in level 0, therefore we are probing all devices in level 0 simultaneously
		else: self.multiprobing=False

		self.leveldev = [0]*len(self.tpname)
		# find total number of sites to probe
		self.numberofsites=1
		for il in range(0,len(self.leveldev)):       # find total number of sites on wafer
			self.numberofsites *= len(self.tpname[il])
		# TODO: the following line might be redundent and might be eliminated in the future
		self.leveldev = [0]*len(self.tpname)				# set up a device level indexer (self.leveldev) of dimension = number of levels with all zeros (first device on wafer)
		return
###############################################################################################
# move pointers and locations to the next probe site
# move to next device on level 0 IF the devices of level 0 ARE NOT all in the same mechanical probe location
# IF all the devices of level 0 are at the same mechanical probe location, then we are using multiple probe to simulataneously probe more than one device at a time
# In this case, we need to move pointers to the next site on level 1 instead
# move to next site on level=0 on the loaded probe plan
# if a list of devices to test is provided, via self.selecteddevices, then step through the plan to find the device and move to it
# if len(self.selecteddevices)>0:             # then probe ONLY the devices listed by name in self.selecteddevices. Step through wafer to select only devices in this list
# 			if self.selecteddevices_index<len(self.selecteddevices):        # are there still devices to test in the selected device list?
	def movenextsite(self):
		# self.leveldev is an integer array which gives the current device/region index for each level, e.g. self.leveldev[1] is the current device/region index for the second level in the probing hierarchy
		# il is the index of the hierarchical probing level under consideration
		if self.probestatus=="done wafer": return
		if self.multiprobing: il=1			# if self.multiprobing==True, then we are simultaneously probing several devices at once
		else: il=0
		#if len(self.selecteddevices)==0:        # then this is a standard wafer probing with no explicit list of devices to test
		self.leveldev[il]+=1              # attempt to move to next device on lowest (device) level
		while (il<len(self.leveldev) and self.leveldev[il]>=len(self.tpx[il]) ):     # Do we need to roll over this (the ilth) level's device/region counter (which is self.leveldev[il})
			self.leveldev[il]=0          # roll over device/region counter at this (ilth) level since we've exceed the maximum device/region
			il+=1                   # if we roll over on one level then increment the region on the next higher level
			if il<len(self.leveldev): self.leveldev[il]+=1         # since we rolled over on the present level, then increment to the next device/region on the next higher level i.e. this is similar to the "carry to the next digit" in arithmetic addition
			if self.leveldev[-1]>=len(self.tpy[-1]):        # looking at the highest level: are we done with the entire wafer? if not then update and return the location
				for il in range(0,len(self.leveldev)):self.leveldev[il]=0                  # set location indices back to start of wafer
				self.probestatus = "done wafer"          # done with entire wafer since we've incremented self.leveldev, at the highest level, beyond the end of its regions/devices
				break
		xloc,yloc=self.__getposplan()
		return self.probestatus,self.leveldev,xloc,yloc
		# else:     # we are testing only a list of devices whose names are provided in self.selecteddevices
		# 	if self.selecteddevices_index>=len(self.selecteddevices):
		# 		self.probestatus='done wafer'
		# 		return
		# 	while self.selecteddevices_index<len(self.selecteddevices):
		# 		while self.leveldev[-1]<len(self.tpy[-1]):        # looking at the highest level: are we done with the entire wafer? if not then continue loop
		# 			if self.selecteddevices[self.selecteddevices_index] in self.devicename_map_level(): # then we have a device to test
		# 				self.selecteddevices_index+=1
		# 				xloc,yloc=self.__getposplan()
		# 				return self.probestatus,self.leveldev,xloc,yloc
		# 			self.leveldev[il]+=1
		# 			while (il<len(self.leveldev) and self.leveldev[il]>=len(self.tpx[il]) ):     # Do we need to roll over this (the ilth) level's device/region counter (which is self.leveldev[il})
		# 				self.leveldev[il]=0          # roll over device/region counter at this (ilth) level since we've exceed the maximum device/region
		# 				il+=1                   # if we roll over on one level then increment the region on the next higher level
		# 				if il<len(self.leveldev): self.leveldev[il]+=1         # since we rolled over on the present level, then increment to the next device/region on the next higher level i.e. this is similar to the "carry to the next digit" in arithmetic addition
		# 		self.selecteddevices_index+=1
		#		for il in range(0,len(self.leveldev)): self.leveldev[il]=0                  # set location indices back to start of wafer
			#print "leveldev", self.leveldev[-1], self.tpy,len(self.tpx),len(self.tpy) #debug
			#return self.probestatus,self.leveldev,xloc,yloc
###########################################################################################################
###############################################################################################
# move pointers and locations to the next probe site
# similar to movenextsite() but this method includes provisions for probe testing e.g. test probe resistance with a shorted pad
# move to next device on level 0 IF the devices of level 0 ARE NOT all in the same mechanical probe location
# IF all the devices of level 0 are at the same mechanical probe location, then we are using multiple probe to simulataneously probe more than one device at a time
# In this case, we need to move pointers to the next site on level 1 instead
# move to next site on level=0 on the loaded probe plan
	def movenextsite_testprobes(self):
		# self.leveldev is an integer array which gives the current device/region index for each level, e.g. self.leveldev[1] is the current device/region index for the second level in the probing hierarchy
		# il is the index of the hierarchical probing level under consideration
		if self.probestatus=="done wafer": return
		#probestatus = "probing wafer"

		#if len(self.selecteddevices)==0:        # then this is a standard wafer probing with no explicit list of devices to test
		if "proberesistancetest" in self.devicename_map_level(): # then we are at a probe test so roll over at the probe mask level and set all lower levels = 0
			for ii in range(0,self.probetestlevel): self.leveldev[ii]=len(self.tpx[ii])-1	# since this is a probe resistance test do not probe devices "under it" rather roll all levels under the probe test level to their highest device numbers - to be rolled over in the following code
		if self.multiprobing: il=1			# if self.multiprobing==True, then we are simultaneously probing several devices at once
		else: il=0							# this is a regular move

		self.leveldev[il]+=1              # attempt to move to next device on lowest (device) level
		while (il<len(self.leveldev) and self.leveldev[il]>=len(self.tpx[il]) ):     # Do we need to roll over this (the ilth) level's device/region counter (which is self.leveldev[il})
			self.leveldev[il]=0          # roll over device/region counter at this (ilth) level since we've exceed the maximum device/region
			il+=1                   	# if we roll over on one level then increment the region on the next higher level
			if il<len(self.leveldev): self.leveldev[il]+=1         # since we rolled over on the present level, then increment to the next device/region on the next higher level i.e. this is similar to the "carry to the next digit" in arithmetic addition
			if self.leveldev[-1]>=len(self.tpy[-1]):        # looking at the highest level: are we done with the entire wafer? if not then update and return the location
				for il in range(0,len(self.leveldev)): self.leveldev[il]=0                  # set location indices back to start of wafer
				self.probestatus = "done wafer"          # done with entire wafer since we've incremented self.leveldev, at the highest level, beyond the end of its regions/devices
				break
		if "proberesistancetest" in self.devicename_map_level():					# then need to set position to probe test area
			xloc=self.get_posplan_map_level(level=self.probetestlevel)['X']
			yloc=self.get_posplan_map_level(level=self.probetestlevel)['Y']
		else: xloc,yloc=self.__getposplan()											# this is a regular move
		return self.probestatus,self.leveldev,xloc,yloc

		# else:     # we are testing only a list of devices whose names are provided in self.selecteddevices
		# 	if self.selecteddevices_index>=len(self.selecteddevices):
		# 		self.probestatus='done wafer'
		# 		return
		# 	for il in range(0,len(self.leveldev)): self.leveldev[il]=0                  # set location indices back to start of wafer so we can search the entire wafer for the next  device
		# 	throughwafer=False
		# 	while (self.selecteddevices_index<len(self.selecteddevices)) and not (self.selecteddevices[self.selecteddevices_index] in self.devicename_map_level()):
		# 		if "proberesistancetest" in self.devicename_map_level(): # then we are at a probe test so roll over at the probe mask level and set all lower levels = 0
		# 			for ii in range(0,self.probetestlevel): self.leveldev[ii]=len(self.tpx[ii])-1	# since this is a probe resistance test do not probe devices "under it" rather roll all levels under the probe test level to their highest device numbers - to be rolled over in the following code
		# 		if self.multiprobing: il=1			# if self.multiprobing==True, then we are simultaneously probing several devices at once
		# 		else: il=0							# this is a regular move
		# 		# attempt to move to next site
		# 		self.leveldev[il]+=1              # attempt to move to next device on lowest (device) level
		# 		while (il<len(self.leveldev) and self.leveldev[il]>=len(self.tpx[il]) ):     # Do we need to roll over this (the ilth) level's device/region counter (which is self.leveldev[il})
		# 			self.leveldev[il]=0          # roll over device/region counter at this (ilth) level since we've exceed the maximum device/region
		# 			il+=1                   	# if we roll over on one level then increment the region on the next higher level
		# 			if il<len(self.leveldev): self.leveldev[il]+=1         # since we rolled over on the present level, then increment to the next device/region on the next higher level i.e. this is similar to the "carry to the next digit" in arithmetic addition
		# 			if self.leveldev[-1]>=len(self.tpy[-1]):        # looking at the highest level: are we done with the entire wafer? if not then update and return the location
		# 				for il in range(0,len(self.leveldev)): self.leveldev[il]=0                  # set location indices back to start of wafer
		# 				throughwafer=True          # done searching the entire wafer since we've incremented self.leveldev, at the highest level, beyond the end of its regions/devices
		# 				break
		#
		# 		if self.selecteddevices[self.selecteddevices_index] in self.devicename_map_level():     # then we're at a selected device so leave this method and do the mechanical move and measurement
		# 			if "proberesistancetest" in self.devicename_map_level():					# then need to set position to probe test area since the selected device is a probe test
		# 				xloc=self.get_posplan_map_level(level=self.probetestlevel)['X']
		# 				yloc=self.get_posplan_map_level(level=self.probetestlevel)['Y']
		# 			else: xloc,yloc=self.__getposplan()											# this would be a regular move for a non-probetest device
		# 			self.selecteddevices_index+=1                                               # increment selected devices index to let us know we will probe a selected device and then to move onto the next selected device
		# 			if self.selecteddevices_index>=len(self.selecteddevices): self.probestatus="done wafer"
		# 			return self.probestatus,self.leveldev,xloc,yloc
		# 		if throughwafer: self.selecteddevices_index+=1                              # move to next selected device if done going through wafer whether or not it was found in the wafer
###########################################################################################################
# get current probe plan position from wafer probe plan and current self.leveldev[] device/region plan index array values
	def __getposplan(self):
		xloc=0
		yloc=0
		for il in range(0,len(self.leveldev)):       # form the new absolute probe position
			xloc += self.tpx[il][self.leveldev[il]]
			yloc += self.tpy[il][self.leveldev[il]]
		return xloc,yloc
###########################################################################################################
# get the current position of the specified level. e.g. the default gives you the position of the device i.e. level=0.
# Usually, the level=1 is the reticle level but this can vary depending on the probe plan
	def get_posplan_map_level(self, level=0):
		xloc=0
		yloc=0
		actualxloc=0
		actualyloc=0
		for il in range(level,len(self.leveldev)):       # form the new absolute probe position
			xloc += self.tpx[il][self.leveldev[il]]					# location of device probe pads
			yloc += self.tpy[il][self.leveldev[il]]					# location of device probe pads
			actualxloc += self.devactualX[il][self.leveldev[il]]	# actual location of device
			actualyloc += self.devactualY[il][self.leveldev[il]]	# actual location of device
		return {'X':xloc,'Y':yloc,'actualX':actualxloc,'actualY':actualyloc}
	###########################################################################################################
	###########################################################################################################
	def x(self):				# get current X location (um) according to the probe plan and current values of self.leveldev[] device/region index values
		if "proberesistancetest" in self.devicename_map_level():					# then need to set position to probe test area
			xloc=self.get_posplan_map_level(level=self.probetestlevel)['X']
		else: xloc = self.__getposplan()[0]
		return xloc
	###########################################################################################################
	def y(self):				# get current Y location (um) according to the probe plan and current values of self.leveldev[] device/region plan index array values
		if "proberesistancetest" in self.devicename_map_level():					# then need to set position to probe test area
			yloc=self.get_posplan_map_level(level=self.probetestlevel)['Y']
		else: yloc = self.__getposplan()[1]
		return yloc
	##########################################################################################################
	def get_planindex(self):						# get current plan index array
		return self.leveldev
	###########################################################################################################
	def set_planindex(self,plindex):	# set plan index array - caution! need to know plan index dimensions BEFORE attempting to set!
		# check to see that the plan index to be set is consistent with the current plan index array
		if len(plindex)!= len(self.leveldev):			# inconsistent plan index arrays?
			print("ERROR! plan index array is not consistent with that being set i.e. a different number of levels! quitting")
			quit()
		for il in range(0,len(self.leveldev)):
			self.leveldev[il] = plindex[il]
	############################################################################################################
	def get_exclusions(self):			# get excluded names from probe plan
		return self.excluded_sites
	#######################################################################################
	def get_nosites(self):	# get number of potential test sites (including actively excluded sites)
		return self.numberofsites
	##########################################################################################
	def get_probestatus(self):		# are we still probing have we reached end of probing?
		return self.probestatus
	############################################################################################
	# the following methods are generally NOT used in wafer probing but rather wafer mapping
	############################################################################################
	# ilev is the mask hierachal level
	# idevindex is the index of a sublevel or device in the level ilev
	# returns the relative X location of the sublevel or device, in the coordinates of the next higher level given the indices of the level and index within that level
	def get_map_rel_X(self,ilev=0,idevindex=-1):
		return self.tpx[ilev][idevindex]
	###############################################################################################
	# ilev is the mask hierachal level
	# idevindex is the index of a sublevel or device in the level ilev
	# returns the relative Y location of the sublevel or device in the coordinates of the next higher level given the indices of the level and index within that level
	def get_map_rel_Y(self,ilev=0,idevindex=-1):
		return self.tpy[ilev][idevindex]
	############################################################################################
	# move to next site at masklevel level specified by the input parameter level and the probe plan file
	# this differs from the method movenextsite() in that movenextsite() moves to the next site at the lowest (device) level whereas movenextsite_map_level() moves to the next
	# site at the level specified.
	# for instance, if level=0 is the device level, then this method will move to the next device when called and xloc,yloc will contain the absolute x and y coordinates relative to the wafer
	# if, for example, level=1 is the die level, then a call to this method will move to the next die and return the wafer coordinates of the lower left edge of that die
	# the 'changedlevel' is the last level to be modified
	def movenextsite_map_level(self,level=0):
		# self.leveldev is an integer array which gives the current device/region index for each level, e.g. self.leveldev[1] is the current device/region index for the second level in the probing hierarchy
		# il is the index of the hierarchical probing level under consideration
		if self.probestatus=="done wafer": return
		il=level
		self.leveldev[il]+=1              # attempt to move to next device on lowest (device) level
		while (il<len(self.leveldev) and self.leveldev[il]>=len(self.tpx[il]) ):     # Do we need to roll over this (the ilth) level's device/region counter (which is self.leveldev[il})
			self.leveldev[il]=0          # roll over device/region counter at this (ilth) level since we've exceed the maximum device/region
			il+=1                   # if we roll over on one level then increment the region on the next higher level
			if il<len(self.leveldev): self.leveldev[il]+=1         # since we rolled over on the present level, then increment to the next device/region on the next higher level i.e. this is similar to the "carry to the next digit" in arithmetic addition
			if self.leveldev[-1]>=len(self.tpy[-1]):        # looking at the highest level: are we done with the entire wafer? if not then update and return the location
				for il in range(0,len(self.leveldev)):self.leveldev[il]=0                  # set location indices back to start of wafer
				self.probestatus = "done wafer"          # done with entire wafer since we've incremented self.leveldev, at the highest level, beyond the end of its regions/devices
				break
		xloc,yloc=self.__getposplan()
		return {'status':self.probestatus,'leveldev':self.leveldev,'X':xloc,'Y':yloc,'changedlevel':il}
###########################################################################################################
	############################################################################################
	# move to next site at masklevel level specified by the input parameter level and the probe plan file
	# this differs from the method movenextsite() and movenextsite_map_level() in that it does not roll over the next level up but rather indicates that all devices in the selected level have been stepped into
	# for instance, if level=0 is the device level, then this method will move to the next device when called and xloc,yloc will contain the absolute x and y coordinates relative to the wafer
	# if, for example, level=1 is the die level, then a call to this method will move to the next die and return the wafer coordinates of the lower left edge of that die
	# Each call to this method increments the device on the level specified by the parameter "level". When all devices have been gone through, on this level, the counter rolls over to 0 and the donelevel flag is set True
	def movenextsite_within_map_level(self,level=0):
		# self.leveldev is an integer array which gives the current device/region index for each level, e.g. self.leveldev[1] is the current device/region index for the second level in the probing hierarchy
		# il is the index of the hierarchical probing level under consideration
		donelevel=False					# do we need to increment the next higher level?
		self.leveldev[level]+=1              # attempt to move to next device on this (level) level
		if self.leveldev[level]>=len(self.tpx[level]):
			donelevel=True				# covered all devices in this level
			self.leveldev[level]=0		# so roll over level counter to the 0th device on this level
		if self.leveldev[-1]>=len(self.tpy[-1]): probestatus = "done wafer"          # done with entire wafer since we've incremented self.leveldev, at the highest level, beyond the end of its regions/devices
		else: probestatus="probing wafer"
		xloc,yloc=self.__getposplan()												# get the X Y wafer location of this device
		return {'status': probestatus,'leveldev':self.leveldev,'X':xloc,'Y':yloc,'donelevel':donelevel}
###########################################################################################################
####################################################################################################################
# Return the devicename from the user-defined probe test plan, at the specified level
# if the level=0, then this returns the full device name.
# if the level=1, and if the level=1 corresponds to the reticle level, then return the reticle name
# note that self.leveldev[il] contains the index of the current device under consideration at the mask level index il
	def devicename_map_level(self,level=0):
	# return devicename built from probe test plan and current probe position
		devname=""
		for il in range(len(self.leveldev)-1,level-1,-1):		# form devicename from all device levels including and above the parameter level
			#print "tp.tpname, il",self.tpname[il][self.leveldev[il]],il #debug
			devname+="_"+self.tpname[il][self.leveldev[il]]
		return devname				# device name at specified level
	####################################################################################################################
####################################################################################################################
# Return the device size from the user-defined probe test plan, at the specified level
# if the level=0, then this returns the full device name.
# if the level=1, and if the level=1 corresponds to the reticle level, then return the reticle name
# note that self.leveldev[il] contains the index of the current device under consideration at the mask level index il
	def devicesize_map_level(self,level=0):
	# return device size built from probe test plan and current probe position
		return {'X':self.devsizeX[level][self.leveldev[level]],'Y':self.devsizeY[level][self.leveldev[level]]}				# device size at specified level
	####################################################################################################################
##########################################################################################################################
# Return the maximum possible X and Y size of the array of devices in a given level according to location coordinates
# data are derived from device locations and also user-specified device size, unlike the method devicesize_map_level()

	def devicearraysize_map_level(self,level=0):
		if len(self.tpx[level])==1:					# just one element in this level so estimate size on user-supplied size in test plan
			xarraysize=self.devsizeX[level][0]
			yarraysize=self.devsizeY[level][0]
		else:
			#dxmax=max([abs(self.tpx[level][il]-self.tpx[level][il-1]) for il in range(1,len(self.tpx[level]))])			# find the maximum spacing between devices on this level
			#xend = max(max(self.devsizeX[level]),dxmax)
			xarraysize=abs(max(self.tpx[level])-min(self.tpx[level]))+max(self.devsizeX[level])
			#dymax=max([abs(self.tpy[level][il]-self.tpy[level][il-1]) for il in range(1,len(self.tpy[level]))])			# find the maximum spacing between devices on this level
			#yend = max(max(self.devsizeY[level]),dymax)
			yarraysize=abs(max(self.tpy[level])-min(self.tpy[level]))+max(self.devsizeY[level])
		return {'X':xarraysize,'Y':yarraysize }
##########################################################################################################################
##########################################################################################################################
# Return the maximum possible X and Y size of the wafer section at the given level
#

	def sectionsize_map_level(self,level=None):
		if level==None:	level=len(self.leveldev)				# set default to entire wafer size
		elif (level+1)>len(self.leveldev) or level<0: raise ValueError("ERROR! invalid level specified")
		else: level+=1
		return {'X':max([self.devicearraysize_map_level(level=il)['X'] for il in range(level)]),'Y':max([self.devicearraysize_map_level(level=il)['Y'] for il in range(level)]) }
##########################################################################################################################
# resets pointer back to first device on wafer
	def reset_to_first_site(self):
		for il in range(0,len(self.leveldev)): self.leveldev[il]=0