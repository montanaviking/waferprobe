#__author__ = 'PMarsh Carbonics'
import os
import sys
#import re
import numpy as np
from scipy import stats as st
from PyQt5 import QtCore, QtGui, QtWidgets, Qt
import multiprocessing as mp
import warnings
import collections as col
from utilities import *

################################################################################
##############
# function to test probe resistance and clean if necessary for single device at a time only
# performs shorted pad test on shorted pad within reticle of the selected last tested device
# TODO:tested only in top gated mode at present
def proberesistanceclean_singleprobe_inreticle(backgated=False,iv=None,cascade=None,probeconstellations=None,reticlename=None,pathname=None,wafername_runno=None,totalnumbercleans=0,maxallowedproberesistance=None,maxcleaningtriesperprobe=3):
	maxallowedproberesistancedifference=maxallowedproberesistance/3.
	# get shorted probeing site
	shortprobeconstellation=probeconstellations.get_probing_constellations(devicesubstringnamelogic="and",devicesubstringnames=["SHORT",reticlename])[0]
	if shortprobeconstellation==None or len(shortprobeconstellation)==0: return totalnumbercleans          # just get out if this is not a proberesistance device
	cascade.move_XY(X=shortprobeconstellation["X"],Y=shortprobeconstellation["Y"])
	if backgated: Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=0.1, Vds=0.1, gatecomp=0.05, draincomp=0.05,maxtime=0.2,timeiter=0.2)
	else:   Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=0.1, Vds=0.1, gatecomp=0.05, draincomp=0.05,maxtime=0.2,timeiter=0.2)
	iv.fetbiasoff()
	proberesistance_drain=0.1/Idval
	proberesistance_gate=0.1/Igval
	#print ("testing proberesistance devices are: ",device_probetest)
	print("testing proberesistance_drain0 =",formatnum(proberesistance_drain,precision=2))
	print("testing proberesistance_gate0 =",formatnum(proberesistance_gate,precision=2))
	cleaniter=0
	while (proberesistance_drain>maxallowedproberesistance or proberesistance_gate>maxallowedproberesistance
	   or abs(proberesistance_drain-proberesistance_gate)>maxallowedproberesistancedifference) and cleaniter<maxcleaningtriesperprobe:
		if cleaniter==0: totalnumbercleans+=1               # keep track of total number of cleaning cycles
		drainresbefore=proberesistance_drain
		gateresbefore=proberesistance_gate
		cascade.cleanprobe(auxstagenumber=12, number_cleaning_contacts=2)          # clean on sticky probe cleaner first then dry abrasive probe cleaner pad 2nd
		if backgated: Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=0.1, Vds=0.1, gatecomp=0.05, draincomp=0.05,maxtime=0.2,timeiter=0.2)
		else: Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=0.1, Vds=0.1, gatecomp=0.05, draincomp=0.05,maxtime=0.2,timeiter=0.2)
		iv.fetbiasoff()
		proberesistance_drain=0.1/Idval
		proberesistance_gate=0.1/Igval

		print("cleaning loop proberesistance_drain =",formatnum(proberesistance_drain,precision=2))
		print("cleaning loop proberesistance_gate =",formatnum(proberesistance_gate,precision=2))

		cleaniter+=1
		iv.writefile_probecleanlog_topgate(pathname=pathname, devicename=shortprobeconstellation['name'], wafername=wafername_runno,
								   drain_beforeclean=drainresbefore, drain_afterclean=proberesistance_drain,
								   gate_beforeclean=drainresbefore, gate_afterclean=proberesistance_drain,
								   cleaniter=cleaniter)
	return totalnumbercleans
##############







################################################################################
##############
# function to test probe resistance and clean if necessary for single device at a time only
# verified topgated mode too
def proberesistanceclean_singleprobe(backgated=False,iv=None,resisttestdevicename="short",cascade=None,probeconstellations=None,selectedprobeconstellation=None,pathname="",wafername_runno=None,totalnumbercleans=0,maxallowedproberesistance=None,maxcleaningtriesperprobe=3):
	maxallowedproberesistancedifference=maxallowedproberesistance/3.
	device_probetest=probeconstellations.get_probing_devices(constellation_name=selectedprobeconstellation["name"])[0]    # get name of device
	devicename_probetest=device_probetest["name"]
	if not resisttestdevicename.lower() in devicename_probetest.lower(): return totalnumbercleans          # just get out if this is not a proberesistance device
	cascade.move_XY(X=selectedprobeconstellation["X"],Y=selectedprobeconstellation["Y"])
	if backgated: Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=0.1, Vds=0.1, gatecomp=0.05, draincomp=0.05,maxtime=0.2,timeiter=0.2)
	else:   Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=0.1, Vds=0.1, gatecomp=0.05, draincomp=0.05,maxtime=0.2,timeiter=0.2)
	iv.fetbiasoff()
	proberesistance_drain=0.1/Idval
	proberesistance_gate=0.1/Igval
	print ("testing proberesistance devices are: ",device_probetest)
	print("testing proberesistance_drain =",formatnum(proberesistance_drain,precision=2))
	print("testing proberesistance_gate =",formatnum(proberesistance_gate,precision=2))
	cleaniter=0
	while (proberesistance_drain>maxallowedproberesistance or proberesistance_gate>maxallowedproberesistance
	   or abs(proberesistance_drain-proberesistance_gate)>maxallowedproberesistancedifference) and cleaniter<maxcleaningtriesperprobe:
		if cleaniter==0: totalnumbercleans+=1               # keep track of total number of cleaning cycles
		drainresbefore=proberesistance_drain
		gateresbefore=proberesistance_gate
		cascade.cleanprobe(auxstagenumber=12, number_cleaning_contacts=2)          # clean on sticky probe cleaner first then dry abrasive probe cleaner pad 2nd
		if backgated: Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=0.1, Vds=0.1, gatecomp=0.05, draincomp=0.05,maxtime=0.2,timeiter=0.2)
		else: Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=0.1, Vds=0.1, gatecomp=0.05, draincomp=0.05,maxtime=0.2,timeiter=0.2)
		iv.fetbiasoff()
		proberesistance_drain=0.1/Idval
		proberesistance_gate=0.1/Igval

		print("cleaning loop proberesistance_drain =",formatnum(proberesistance_drain,precision=2))
		print("cleaning loop proberesistance_gate =",formatnum(proberesistance_gate,precision=2))

		cleaniter+=1
		iv.writefile_probecleanlog_topgate(pathname=pathname, devicename=devicename_probetest, wafername=wafername_runno,
								   drain_beforeclean=drainresbefore, drain_afterclean=proberesistance_drain,
								   gate_beforeclean=drainresbefore, gate_afterclean=proberesistance_drain,
								   cleaniter=cleaniter)
	return totalnumbercleans
##############
# function to test probe resistance and clean if necessary for single device at a time only
# works for both top and backside probing
# called for each constellation probed and will perform probe resistance test ONLY if probing shorted devices (shorted probe pad test structures)
def proberesistanceclean_dualprobe(topgate=False,resisttestdevicename="short",iv=None,cascade=None,probeconstellations=None,selectedprobeconstellation=None,pathname="",wafername_runno=None,totalnumbercleans=0,maxallowedproberesistance=None,maxcleaningtriesperprobe=3):
	maxallowedproberesistancedifference=maxallowedproberesistance
	device_probetest=probeconstellations.get_probing_devices(constellation_name=selectedprobeconstellation["name"])    # get names of devices
	devicename_probetest0=device_probetest[0]["name"]
	devicename_probetest1=device_probetest[1]["name"]
	if not resisttestdevicename.lower() in devicename_probetest1.lower(): return totalnumbercleans          # just return from this function doing nothing, if this is not a probe resistance test pad device
	cascade.move_XY(X=selectedprobeconstellation["X"],Y=selectedprobeconstellation["Y"])                                                # move to probe resistance test pad location
	if not topgate:         # this is a dual backgated probing
		Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=0.1, Vds0=0.1, Vds1=0.1, gatecomp=0.05, draincomp0=0.05)
		iv.fetbiasoff()
		proberesistance0=0.1/Id0val
		proberesistance1=0.1/Id1val
		print("testing probe resistance0 =",formatnum(proberesistance0,precision=2))
		print("testing probe resistance1 =",formatnum(proberesistance1,precision=2))
		cleaniter=0
		while (proberesistance0>maxallowedproberesistance or proberesistance1>maxallowedproberesistance
		   or abs(proberesistance0-proberesistance1)>maxallowedproberesistancedifference) and cleaniter<maxcleaningtriesperprobe:
			if cleaniter==0: totalnumbercleans+=1               # keep track of total number of cleaning cycles
			resbefore0=proberesistance0
			resbefore1=proberesistance1
			cascade.cleanprobe(auxstagenumber=12, number_cleaning_contacts=2)          # clean on sticky probe cleaner first then dry abrasive probe cleaner pad 2nd
			Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=0.1, Vds0=0.1, Vds1=0.1, gatecomp=0.05, draincomp0=0.05)
			iv.fetbiasoff()
			proberesistance0=0.1/Id0val
			proberesistance1=0.1/Id1val

			print("cleaning probe resistance0 =",formatnum(proberesistance0,precision=2))
			print("cleaning probe resistance1 =",formatnum(proberesistance1,precision=2))
			cleaniter+=1
			iv.writefile_probecleanlog(pathname=pathname,devicenames=[devicename_probetest0,devicename_probetest1],wafername=wafername_runno,
			                           probe0resistance_beforeclean=resbefore0,probe0resistance_afterclean=proberesistance0,probe1resistance_beforeclean=resbefore1,probe1resistance_afterclean=proberesistance1,cleaniter=cleaniter)
	else:       # this is a dual topgate probe
		Id0val,Id1val,Ig0val,Ig1val,Id0compstatval,Id1compstatval,Ig0compstatval,Ig1compstatval=iv.fetbiason_dual_topgate(Vgs0=0.1,Vgs1=0.1, Vds0=0.1, Vds1=0.1, gatecomp0=0.05, gatecomp1=0.05, draincomp0=0.05, draincomp1=0.05)
		iv.fetbiasoff()
		proberesistance_drain0=0.1/Id0val
		proberesistance_drain1=0.1/Id1val
		proberesistance_gate0=0.1/Ig0val
		proberesistance_gate1=0.1/Ig1val
		print ("testing proberesistance devices are: ",device_probetest[0],device_probetest[1])
		print("testing proberesistance_drain0 =",formatnum(proberesistance_drain0,precision=2))
		print("testing proberesistance_drain1 =",formatnum(proberesistance_drain1,precision=2))
		print("testing proberesistance_gate0 =",formatnum(proberesistance_gate0,precision=2))
		print("testing proberesistance_gate1 =",formatnum(proberesistance_gate1,precision=2))
		cleaniter=0
		while (proberesistance_drain0>maxallowedproberesistance or proberesistance_drain1>maxallowedproberesistance or proberesistance_gate0>maxallowedproberesistance or proberesistance_gate1>maxallowedproberesistance
		   or abs(proberesistance_drain1-proberesistance_drain0)>maxallowedproberesistancedifference or abs(proberesistance_gate1-proberesistance_gate0)>maxallowedproberesistancedifference) and cleaniter<maxcleaningtriesperprobe:
			if cleaniter==0: totalnumbercleans+=1               # keep track of total number of cleaning cycles
			drainres0before=proberesistance_drain0
			drainres1before=proberesistance_drain1
			gateres0before=proberesistance_gate0
			gateres1before=proberesistance_gate1
			cascade.cleanprobe(auxstagenumber=12, number_cleaning_contacts=2)          # clean on sticky probe cleaner first then dry abrasive probe cleaner pad 2nd
			Id0val,Id1val,Ig0val,Ig1val,Id0compstatval,Id1compstatval,Ig0compstatval,Ig1compstatval=iv.fetbiason_dual_topgate(Vgs0=0.1,Vgs1=0.1, Vds0=0.1, Vds1=0.1, gatecomp0=0.05, gatecomp1=0.05, draincomp0=0.05, draincomp1=0.05)
			iv.fetbiasoff()
			proberesistance_drain0=0.1/Id0val
			proberesistance_drain1=0.1/Id1val
			proberesistance_gate0=0.1/Ig0val
			proberesistance_gate1=0.1/Ig1val

			print("cleaning loop proberesistance_drain0 =",formatnum(proberesistance_drain0,precision=2))
			print("cleaning loop proberesistance_drain1 =",formatnum(proberesistance_drain1,precision=2))
			print("cleaning loop proberesistance_gate0 =",formatnum(proberesistance_gate0,precision=2))
			print("cleaning loop proberesistance_gate1 =",formatnum(proberesistance_gate1,precision=2))
			cleaniter+=1
			iv.writefile_probecleanlog_dual_topgate(pathname=pathname, devicenames=[devicename_probetest0,devicename_probetest1], wafername=wafername_runno,
									   drain0_beforeclean=drainres0before, drain0_afterclean=proberesistance_drain0, drain1_beforeclean=drainres1before, drain1_afterclean=proberesistance_drain1,
									   gate0_beforeclean=gateres0before, gate0_afterclean=proberesistance_gate0, gate1_beforeclean=gateres1before, gate1_afterclean=proberesistance_gate1,
									   cleaniter=cleaniter)
	return totalnumbercleans

##############
# function to test probe resistance and clean if necessary for single device at a time only
# topgate single device probed
# called from main probing program
# TODO works only in topgated mode
# def proberesistanceclean_singleprobe_topgate(iv=None,cascade=None,probeconstellationsdB=None,probeconstellations_test=None, pathname="",wafername_runno=None,totalnumbercleans=0,maxallowedproberesistance=None):
# 	#probeconstellations_test=col.deque(probeconstellationsdB.get_probing_constellations(probe_order_start=0,probe_order_stop=10000))
# 	maxallowedproberesistancedifference=maxallowedproberesistance/3.
# 	pconsttest=probeconstellations_test[0]              # set probes to move to probe resistance test device
# 	cascade.move_XY(X=pconsttest["X"], Y=pconsttest["Y"])                       # move to DUT to probe resistance test
# 	device_probetest=probeconstellationsdB.get_probing_devices(constellation_name=pconsttest["name"])[0]    # get name of device at probe position = 0 which is also the only device name since only one device is being probed at a time
# 	devicename=device_probetest["name"]
# 	Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=0.1, Vds=0.1, gatecomp=0.05, draincomp=0.05,maxtime=0.2,timeiter=0.2)
# 	iv.fetbiasoff()
# 	proberesistance_drain=0.1/Idval
# 	proberesistance_gate=0.1/Igval
#
# 	print ("testing proberesistance devices are: ",device_probetest)
# 	print("testing proberesistance_drain0 =",formatnum(proberesistance_drain,precision=2))
#
# 	print("testing proberesistance_gate0 =",formatnum(proberesistance_gate,precision=2))
# 	cleaniter=0
# 	while (proberesistance_drain>maxallowedproberesistance or proberesistance_gate>maxallowedproberesistance
# 	   or abs(proberesistance_drain-proberesistance_gate)>maxallowedproberesistancedifference) and cleaniter<3:
# 		if cleaniter==0: totalnumbercleans+=1               # keep track of total number of cleaning cycles
# 		drainresbefore=proberesistance_drain
# 		gateresbefore=proberesistance_gate
# 		cascade.cleanprobe(auxstagenumber=12, number_cleaning_contacts=2)          # clean on sticky probe cleaner first then dry abrasive probe cleaner pad 2nd
# 		Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=0.1, Vds=0.1, gatecomp=0.05, draincomp=0.05,maxtime=0.2,timeiter=0.2)
# 		iv.fetbiasoff()
# 		proberesistance_drain=0.1/Idval
# 		proberesistance_gate=0.1/Igval
#
# 		print("cleaning loop proberesistance_drain =",formatnum(proberesistance_drain,precision=2))
# 		print("cleaning loop proberesistance_gate =",formatnum(proberesistance_gate,precision=2))
#
# 		cleaniter+=1
# 		iv.writefile_probecleanlog_topgate(pathname=pathname, devicename=devicename, wafername=wafername_runno,
# 								   drain_beforeclean=drainresbefore, drain_afterclean=proberesistance_drain,
# 								   gate_beforeclean=drainresbefore, gate_afterclean=proberesistance_drain,
# 								   cleaniter=cleaniter)
# 		return totalnumbercleans