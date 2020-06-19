# main wafer probing routine
import visa
from utilities import formatnum
from create_probeconstellations_devices.probe_constellations_map import *
import collections as col
from probing_utilities import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from cascade import CascadeProbeStation                                                    # Cascade wafer prober

iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
maxallowedproberesistance=8.
maxallowedproberesistancedifference=8.



# common to both
#gatecomp = 5E-5                                                                   # gate current compliance in A
gatecomp = 50E-6                                                                   # gate current compliance in A
#gatecomp = 0.01
draincomp = 0.1                                                                   # drain current compliance in A
# draincompmApermm=150.                                        # drain compliance in mA/mm used for loop hysteresis transfer curves and anything else which isn't autoranged
# draincompmApermmlow=15.                                        # drain compliance in mA/mm used for loop hysteresis transfer curves and anything else which isn't autoranged
#draincomplow = 0.001                                                                   # drain current compliance in A - this is for the low Vds test. Compliance is reduced to allow accurate Id measurement at low Vds and low expected currents

#Vgs_bias = -10.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
goodIg=50.E-6                          # gate current must be LESS than this amount to qualify device for further testing
#goodIg=50E-6                          # gate current must be LESS than this amount to qualify device for further testing
Vgs_validation = -0.5
Vds0_validation = -0.5
Vds1_validation = -0.5

wafername="QH28"
runnumber=3
maskname="v6_2finger_dual"
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno
cascade = CascadeProbeStation(rm=rm)         # setup Cascade NO probeplan file here! This also moves
probc=ConstellationsdB(maskname=maskname,wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
#probeconstellations=probc.get_probing_constellations(devicesubstringnamelogic="or",devicesubstringnames=["C4_R5","C5_R5","C6_R5","C8_R5"],startprobenumber=1128,stopprobenumber=100000)

firsttime=True
#nodevbetweentest=30                        # number of devices probed between probe resistance tests
#devcounterbetweentests=0               # counts number of devices probed since last probe resistance test
totalnumbercleans=0

###############################################################################################################################################################################################################################################
probeconstellations=probc.get_probing_constellations(devicesubstringnamelogic="nor",devicesubstringnames=["C1","C2","R1","R2"],startprobenumber=1985,stopprobenumber=10000)
###############################################################################################################################################################################################################################################

Vgsstart=-3
Vgsstop=2.
deltaVgs=0.1
Vds=-1
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("from line 66 in IVprobingdual_topgate_database.py ", pconst["name"], "testorder",pconst["testorder"])
		totalnumbercleans=proberesistanceclean_dualprobe(topgate=True,resisttestdevicename="short",iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance,maxcleaningtriesperprobe=1)
		devicenames=[device[0]["name"],device[1]["name"]]

		if not "short" in device[0]["name"].lower() :     # don't reprobe shorted test pads
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
			iv.measure_ivtransfer_dual_topgate(sweepdelay=0.05, Vds=Vds,Vgs_start=Vgsstart, Vgs_stop=Vgsstop, Vgs_step=deltaVgs,gatecomp=gatecomp,draincomp=draincomp)
			iv.writefile_ivtransfer_dual_topgate(pathname=pathname,wafername=wafername_runno,devicenames=devicenames, devicenamemodifier="",xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"])
##############################################################################################################################################################################################################################################


###############################################################################################################################################################################################################################################
probeconstellations=probc.get_probing_constellations(devicesubstringnamelogic="nor",devicesubstringnames=["C1","C2","R1","R2"],startprobenumber=0,stopprobenumber=10000)
###############################################################################################################################################################################################################################################

###############################################################################################################################################################################################################################################
Vdsfoc_start=0
Vdsfoc_stop=-1.0
Vdsfoc_npts=21
Vgsfoc_start=-3.
Vgsfoc_stop=-3.
Vgsfoc_npts=1

for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("from line 97 in IVprobingdual_topgate_database.py ", pconst["name"], "testorder",pconst["testorder"])
		totalnumbercleans=proberesistanceclean_dualprobe(topgate=True,resisttestdevicename="short",iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance,maxcleaningtriesperprobe=1)
		devicenames=[device[0]["name"],device[1]["name"]]
		# if "short" in device[0]["name"].lower() :     # record probe resistance test pad's resistances
		# 	iv.measure_ivfoc_dual_backgate(sweepdelay=0.05,Vds_start=-0.1,Vds_stop=0.1,Vds_npts=11,Vgs_start=0, Vgs_stop=0, Vgs_npts=1,gatecomp=0.1,draincomp=0.1)      # measure probe pad probing resistance on both
		if not "short" in device[0]["name"].lower() :     # don't reprobe shorted test pads
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
			iv.measure_ivfoc_dual_topgate(sweepdelay=0.05,Vds_start=Vdsfoc_start,Vds_stop=Vdsfoc_stop,Vds_npts=Vdsfoc_npts,Vgs_start=Vgsfoc_start, Vgs_stop=Vgsfoc_stop,Vgs_npts=Vgsfoc_npts,gatecomp=gatecomp,draincomp=draincomp)
			iv.writefile_ivfoc_dual(backgated=False,pathname=pathname,wafername=wafername_runno,devicenames=devicenames, devicenamemodifier="",xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"])
###############################################################################################################################################################################################################################################


cascade.move_separate()
cascade.unlockstage()
# #del cascade
print("done probing wafer")