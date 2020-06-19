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
maxallowedproberesistance=100.

# set up of IV and bias voltages
# family of curves


# Vgs_trans_start_ss=-30.
# Vgs_trans_stop_ss=5.
# Vgs_trans_step_ss=0.5


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
# Vgs_validation = 0.
# Vds0_validation = -1.
# Vds1_validation = -1.



wafername="L41"
runnumber=2
maskname="v6_2finger_dual_backside"


# get probe constellations
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno
cascade = CascadeProbeStation(rm=rm)         # setup Cascade NO probeplan file here! This also moves
probc=ConstellationsdB(maskname=maskname,wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(devicesubstringnamelogic='or',devicesubstringnames=['R5','R6'],startprobenumber=1679,stopprobenumber=10000)
#firsttime=True
nodevbetweentest=30                        # number of devices probed between probe resistance tests
devcounterbetweentests=0               # counts number of devices probed since last probe resistance test
totalnumbercleans=0

resisttestdevicename="SHORT"
#######################################################################################################
## Family of curves Vds=0V to -1V
Vgs_focstart = -30.
Vgs_focstop = 5.
Vgs_focnpts = 8

Vds_focstart = 0.
Vds_focstop = -1.
Vds_focnpts =21
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	totalnumbercleans=proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance,resisttestdevicename=resisttestdevicename)
	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
	print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
	if "SHORT" in devicenames[1]:
		iv.measure_ivfoc_dual_backgate('2', Vds_start=-0.1, Vds_stop=0.1, Vds_npts=21, Vgs_start=0, Vgs_stop=0, Vgs_npts=1, gatecomp=0.1,draincomp=0.1)
		iv.writefile_ivfoc_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
	else:
		iv.measure_ivfoc_dual_backgate('2', Vds_start=Vds_focstart, Vds_stop=Vds_focstop, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop, Vgs_npts=Vgs_focnpts, gatecomp=gatecomp,draincomp=0.1)
		iv.writefile_ivfoc_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
###############################


#######################################################################################################
## One member of Family of curves Vds=-1V
Vds_focstart=-1
Vds_focstop=1
Vds_focnpts=21
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	totalnumbercleans=proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance,resisttestdevicename=resisttestdevicename)
	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
	print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"],"test order ",pconst["testorder"])
	if "SHORT" in devicenames[1]:
		iv.measure_ivfoc_dual_backgate('2', Vds_start=-0.1, Vds_stop=0.1, Vds_npts=21, Vgs_start=0, Vgs_stop=0, Vgs_npts=1, gatecomp=0.1,draincomp=0.1)
		iv.writefile_ivfoc_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
	else:
		iv. measure_ivfoc_Vdsloop_4sweep_controlledslew_dual_backgated(startstopzero=True, Vdsslewrate=1., Vds_start=Vds_focstart, Vds_stop=Vds_focstop, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstart, Vgs_npts=1, gatecomp=gatecomp,draincomp=0.1)
		iv.writefile_ivfoc_Vds4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,devicenamemodifier="singleVgs",xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
##############################


#######################################################################################################
## Transfer curves
#
# Vgssweepdir=['+-']
# Vdssetting=[-0.1,-0.5,-1.0,-1.5]
Vgssweepdir=['-+']
Vdssetting=[-0.01]
for devmodifier in Vgssweepdir:
	if devmodifier=='-+':
		Vgs_trans_start_ss=-30.
		Vgs_trans_stop_ss=5.
		Vgs_trans_step_ss=0.5
	else:
		Vgs_trans_start_ss=5.
		Vgs_trans_stop_ss=-30.
		Vgs_trans_step_ss=-0.5
	for Vds in Vdssetting:
		totalnumbercleans=0
		for pconst in probeconstellations:
			if totalnumbercleans>50:
				print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
				quit()
			devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
			devicenames=[devices[0]["name"],devices[1]["name"]]
			totalnumbercleans=proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance,resisttestdevicename=resisttestdevicename)
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
			if "SHORT" in devicenames[1]:
				iv.measure_ivfoc_dual_backgate('2', Vds_start=-0.1, Vds_stop=0.1, Vds_npts=21, Vgs_start=0, Vgs_stop=0, Vgs_npts=1, gatecomp=0.1,draincomp=0.1)
				iv.writefile_ivfoc_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
			else:
				iv.measure_ivtransfer_dual_backgate(inttime=2,sweepdelay=0.05,Vds=Vds,Vgs_start=Vgs_trans_start_ss,Vgs_stop=Vgs_trans_stop_ss,Vgs_step=Vgs_trans_step_ss,gatecomp=gatecomp,draincomp=draincomp)
				iv.writefile_ivtransfer_dual(pathname=pathname,wafername=wafername_runno,devicenames=devicenames,devicenamemodifier=devmodifier+formatnum(Vds,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
###############################

cascade.move_separate()
cascade.unlockstage()

print("done probing wafer")