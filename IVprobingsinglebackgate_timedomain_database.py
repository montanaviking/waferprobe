# main wafer probing routine
import visa
from utilities import formatnum
from create_probeconstellations_devices.probe_constellations_map import *
import collections as col

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from cascade import CascadeProbeStation                                                    # Cascade wafer prober

iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
maxallowedproberesistance=3.
maxallowedproberesistancedifference=1.

# set up of IV and bias voltages
# family of curves
Vgs_focstart = 0
Vgs_focstop = 0
Vgs_focnpts = 1

Vds_focstart = 1.
Vds_focstop = -1.
Vds_focnpts =21

Vgs_trans_start_ss=-10
Vgs_trans_stop_ss=-5.
Vgs_trans_step_ss=0.5


# common to both
#gatecomp = 5E-5                                                                   # gate current compliance in A
gatecomp = 50E-6                                                                   # gate current compliance in A
#gatecomp = 0.01
draincomp = 0.1                                                                   # drain current compliance in A

#Vgs_bias = -10.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
#goodIg=50.E-6                          # gate current must be LESS than this amount to qualify device for further testing
goodIg=50E-6                          # gate current must be LESS than this amount to qualify device for further testing
Vgs_validation = 0.
Vds0_validation = -1.
Vds1_validation = -1.



wafername="L6"
runnumber=6
maskname="L6"


# get probe constellations
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno
cascade = CascadeProbeStation(rm=rm)         # setup Cascade NO probeplan file here! This also moves
probc=ConstellationsdB(maskname="L6",wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probe_order_start=0,probe_order_stop=10000,probelistfilename="/".join([pathname,"sorteddevices.csv"]))
#firsttime=True
nodevbetweentest=30                        # number of devices probed between probe resistance tests
devcounterbetweentests=0               # counts number of devices probed since last probe resistance test
totalnumbercleans=0


##############
# function to test probe resistance and clean if necessary for single device at a time only
# TODO: works only in backgating mode at present
def proberesistanceclean_singleprobe(backgated=True,iv=None,cascade=None,probeconstellations=None,selectedprobeconstellation=None,totalnumbercleans=0,pathname=""):
	device_probetest=probeconstellations.get_probing_devices(constellation_name=selectedprobeconstellation["name"])[0]    # get name of device
	devicename_probetest=device_probetest["name"]
	if not ("resist" in devicename_probetest.lower() or "short" in devicename_probetest.lower()): return totalnumbercleans          # just get out if this is not a proberesistance device
	cascade.move_XY(X=selectedprobeconstellation["X"],Y=selectedprobeconstellation["Y"])
	Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=0.1, Vds=0.1, gatecomp=0.05, draincomp=0.05,maxtime=0.2,timeiter=0.2)
	iv.fetbiasoff()
	proberesistance_drain=0.1/Idval
	proberesistance_gate=0.1/Igval
	print ("testing proberesistance devices are: ",device_probetest)
	print("testing proberesistance_drain0 =",formatnum(proberesistance_drain,precision=2))
	print("testing proberesistance_gate0 =",formatnum(proberesistance_gate,precision=2))
	cleaniter=0
	while (proberesistance_drain>maxallowedproberesistance or proberesistance_gate>maxallowedproberesistance
	   or abs(proberesistance_drain-proberesistance_gate)>maxallowedproberesistancedifference) and cleaniter<3:
		if cleaniter==0: totalnumbercleans+=1               # keep track of total number of cleaning cycles
		drainresbefore=proberesistance_drain
		gateresbefore=proberesistance_gate
		cascade.cleanprobe(auxstagenumber=12, number_cleaning_contacts=2)          # clean on sticky probe cleaner first then dry abrasive probe cleaner pad 2nd
		Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=0.1, Vds=0.1, gatecomp=0.05, draincomp=0.05,maxtime=0.2,timeiter=0.2)
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
# TODO: works only in backgating mode at present
def proberesistanceclean_dualprobe(iv=None,cascade=None,probeconstellations=None,selectedprobeconstellation=None,totalnumbercleans=0,pathname=""):
	device_probetest=probeconstellations.get_probing_devices(constellation_name=selectedprobeconstellation["name"])[0]    # get name of device
	devicename_probetest=device_probetest["name"]
	if not ("resist" in devicename_probetest.lower() or "short" in devicename_probetest.lower()): return totalnumbercleans          # just get out if this is not a proberesistance device
	cascade.move_XY(X=selectedprobeconstellation["X"],Y=selectedprobeconstellation["Y"])
	Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=0.1, Vds1=0.1, gatecomp=gatecomp, draincomp0=0.05, draincomp1=0.05)
	iv.fetbiasoff()
	proberesistance0=0.1/Id0val
	proberesistance1=0.1/Id1val
	print("testing probe resistance0 =",formatnum(proberesistance0,precision=2))
	print("testing probe resistance1 =",formatnum(proberesistance1,precision=2))
	cleaniter=0
	while (proberesistance0>maxallowedproberesistance or proberesistance1>maxallowedproberesistance or abs(proberesistance1-proberesistance0)>maxallowedproberesistancedifference) and cleaniter<3:
		if cleaniter==0: totalnumbercleans+=1               # keep track of total number of cleaning cycles
		res0before=proberesistance0
		res1before=proberesistance1
		cascade.cleanprobe(auxstagenumber=12, number_cleaning_contacts=2)          # clean on sticky probe cleaner first then dry abrasive probe cleaner pad 2nd
		Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=0.1, Vds=0.1, gatecomp=0.05, draincomp=0.05,maxtime=0.2,timeiter=0.2)
		iv.fetbiasoff()
		proberesistance_drain=0.1/Idval
		proberesistance_gate=0.1/Igval

		print("cleaning loop proberesistance_drain =",formatnum(proberesistance_drain,precision=2))
		print("cleaning loop proberesistance_gate =",formatnum(proberesistance_gate,precision=2))

		cleaniter+=1
		iv.writefile_probecleanlog(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(),
			                           probe0resistance_beforeclean=res0before,probe0resistance_afterclean=proberesistance0,probe1resistance_beforeclean=res1before,probe1resistance_afterclean=proberesistance1,cleaniter=cleaniter)
	return totalnumbercleans




#######################################################################################################
## Transfer curve loops at low bias, Vds = -0.01 V 2 full loops, rate dependence
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if("resist" in devicename.lower() or "short" in devicename.lower()):
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probeconstellations,selectedprobeconstellation=pconst,totalnumbercleans=totalnumbercleans,pathname=pathname)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"])

		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=25., quiescenttime=0, startstopzero=True, Vds=-0.01,Vgs_start=-5,Vgs_stop=5,Vgs_step=.2,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc_probe=pconst["X"],yloc_probe=pconst["Y"],devicenamemodifier='slew25Vgs5Vds-0.01')
###############################


cascade.move_separate()

print("done probing wafer")