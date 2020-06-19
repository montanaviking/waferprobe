__author__ = 'PMarsh Carbonics'
# test of reading and execution of test plan
from read_testplan import TestPlan
import time



# def dvname():		# Return the devicename from the user-defined probe test plan IF and ONLY IF a user-defined probe test plan was loaded
# 		# return devicename built from probe test plan and current probe position
# 	devname = tp.tpname[0][tp.leveldev[0]]
# 	for il in range(1,len(tp.leveldev)):		# form devicename from all device levels
# 			# note that self.leveldev[il] contains the index of the current device under test (DUT) at the mask level index il
# 		devname+="_"+tp.tpname[il][tp.leveldev[il]]
# 	return devname



# Moves indices and absolute location to the next probe site
# Inputs:
# leveldev is an integer array which gives the current device/region index for each level, e.g. leveldev[1] is the current device/region index for the second level in the probing hierarchy
# name[il][devindex] is the name (string) of each device/region at level il, indexed by devindex at level il - 2D string array
# xrel[il][devindex] is the relative X probe position of the device/region indexed by devindex at level il - 2D float array
# yrel[il][devindex] is the relative Y probe position of the device/region indexed by devindex at level il
# returns/outputs:
# leveldev is the updated device/region current index for all levels (int array of length = number of hierarchical levels). This indicates the region/device to be probed for each and every hierarchical probing (mask) level
# xpos is the absolute X position, on the wafer, of the next probe location in um (int)
# ypos is the absolute X position, on the wafer, of the next probe location in um (int)
plandir = "/home/viking/test/T56/T56meas4"
planname = "T56meas4_plan.csv"
tp=TestPlan(plandir,planname)
#print("fullfilename",tp.fullfilename,"\nmaskname",tp.maskname,"\nmaskrev",tp.maskrevnumber,"\nmaskyear",tp.maskyear,"\nmaskmonth","\nmaskday",tp.maskday)

# probing simulation:

print ("the total number of sites on this wafer is",tp.numberofsites)

prstatus = "probing wafer"


# for ii in range(0,tp.get_nosites()):
# 	moveact=False
# 	while prstatus=='probing wafer':
# 		#print("device is: "+dvname()+" x= "+str(tp.x())+" y= "+str(tp.y()))
# 		mv= tp.movenextsite_map_level()		# move self.tp.leveldev[] index to the next probeable test site.
# 		# determine if the proposed move is to an excluded site or device?
# 		#if len(tp.get_exclusions())==0: moveact=True
# 		prstatus=mv['status']
# 		#moveact=True
# 		# for ex in tp.get_exclusions(): # ex is an array of level designators to exclude from measurements
# 		# 	dn = tp.devicename_map_level()
# 		# 	move=False
# 		# 	for tex in ex:		# look at each element of the exclusion all must match to exclude device
# 		# 		if tex not in dn: move=True # test to see if the devicename is among those excluded from testing
# 		# 	if move==False: moveact=False
# 		#if moveact==True and prstatus=='probing wafer': print("device is: "+dvname()+" x= "+str(tp.x())+" y= "+str(tp.y()))
# 		if prstatus=='probing wafer':
# 			print("changed level",mv['changedlevel'])
# 			print("device level 0: "+tp.devicename_map_level()+" x= "+str(tp.x())+" y= "+str(tp.y()))
# 			print("device level 1 ",tp.devicename_map_level(level=1),tp.get_posplan_map_level(level=1)['X'],tp.get_posplan_map_level(level=1)['Y'])
# 			print("device level 2 ",tp.devicename_map_level(level=2),tp.get_posplan_map_level(level=2)['X'],tp.get_posplan_map_level(level=2)['Y'])
# 			print("device level 3 ",tp.devicename_map_level(level=3),tp.get_posplan_map_level(level=3)['X'],tp.get_posplan_map_level(level=3)['Y'])
#

def nextsite(tp,level=0):
	donelevel=False
	while not donelevel:
		xloc=tp.get_posplan_map_level(level=level)['X']
		yloc=tp.get_posplan_map_level(level=level)['Y']
		print("level, devicename, sizex, sizey, posx, posy,",level,tp.devicename_map_level(level=level),tp.devicesize_map_level(level=level)['X'],tp.devicesize_map_level(level=level)['Y'],xloc,yloc)
		if level>0:					# then we are not at the device level (lowest level) and children exist
			chs=nextsite(tp,level=level-1)
			if chs['donelevel']:	s=tp.movenextsite_within_map_level(level=level)			# if the child level is done, then attempt to move to the next device
		else:	s=tp.movenextsite_within_map_level(level=0)
		donelevel=s['donelevel']
		#if 'done wafer'==s['status']: donewafer=True
	return s

donewafer=False
while not donewafer:
	s=nextsite(tp,level=4)
	if s['status']=='donewafer' or s['donelevel']: donewafer=True
print("level 0 device size X "+str(tp.devicearraysize_map_level(level=0)['X'])+" device size Y "+str(tp.devicearraysize_map_level(level=0)['Y']))
print("level 1 device size X "+str(tp.devicearraysize_map_level(level=1)['X'])+" device size Y "+str(tp.devicearraysize_map_level(level=1)['Y']))
print("level 2 device size X "+str(tp.devicearraysize_map_level(level=2)['X'])+" device size Y "+str(tp.devicearraysize_map_level(level=2)['Y']))
print("level 3 device size X "+str(tp.devicearraysize_map_level(level=3)['X'])+" device size Y "+str(tp.devicearraysize_map_level(level=3)['Y']))
print("level 4 device size X "+str(tp.devicearraysize_map_level(level=4)['X'])+" device size Y "+str(tp.devicearraysize_map_level(level=4)['Y']))

print("wafer size X= "+str(tp.sectionsize_map_level()['X'])+" wafer size Y= "+str(tp.sectionsize_map_level()['Y']))

#print("wafer size X= "+str(max([tp.devicearraysize_map_level(level=il)['X'] for il in range(len(tp.leveldev))]))+" wafer size Y= "+str(max([tp.devicearraysize_map_level(level=il)['Y'] for il in range(len(tp.leveldev))])))