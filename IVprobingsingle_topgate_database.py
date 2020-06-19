# main wafer probing routine
import visa
from utilities import formatnum
from probing_utilities import *
from create_probeconstellations_devices.probe_constellations_map import *
#from writedatabase_measured import *
import collections as col

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from cascade import CascadeProbeStation                                                    # Cascade wafer prober

iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
maxallowedproberesistance=15
maxallowedproberesistancedifference=8.

# set up of IV and bias voltages
# family of curves





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
#goodIg=50.E-6                          # gate current must be LESS than this amount to qualify device for further testing
goodIg=50E-6                          # gate current must be LESS than this amount to qualify device for further testing
Vgs_validation = -0.5
Vds0_validation = -0.5
Vds1_validation = -0.5

wafername="QH27"
runnumber=10
maskname="v6_2finger_single"
wafername_runno=wafername+"meas"+str(runnumber)

pathname = "C:/Users/test/python/data/"+wafername_runno
cascade = CascadeProbeStation(rm=rm)         # setup Cascade NO probeplan file here! This also moves
probc=ConstellationsdB(maskname=maskname,wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
#reticlestoprobe=["C4_R5","C5_R5","C6_R5","C8_R5"]       # reticles to probe


# probe_resistancetest=ConstellationsdB(maskname="QH5_probetest_single",wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
# probeconstellations_test=col.deque(probe_resistancetest.get_probing_constellations(probe_order_start=0,probe_order_stop=10000))
firsttime=True
nodevbetweentest=30                        # number of devices probed between probe resistance tests
devcounterbetweentests=0               # counts number of devices probed since last probe resistance test
#devicelisttotestfile=pathname+"/devicestest.csv"
#
#devtoprobeVds=pathname+"/selectedmeas.csv"
probeconstellations=probc.get_probing_constellations(probelistfilename=pathname+"/selecteddevices.csv")

##############################################################################################################################################################################################################################################
#family of curves
Vds_focstart = -1.
Vds_focstop = 0.
Vds_focnpts =31

Vgs_focstart=-3.
Vgs_focstop=0.
Vgs_focnpts=7

Vds_bias_array=[-0.3,-0.4,-0.5,-1.0]
#totalnumbercleans=0
# transfer curve
Vgs_trans_start_ss=-3.
Vgs_trans_stop_ss=2.
Vgs_trans_step_ss=0.1
for Vds in Vds_bias_array:
	for pconst in probeconstellations:
		device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
		devicename=device["name"]
		testorder=pconst["testorder"]
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"],"testorder =",testorder)
		iv.measure_ivtransfer_topgate(sweepdelay=0.1,Vds=Vds,Vgs_start=Vgs_trans_start_ss, Vgs_stop=Vgs_trans_stop_ss, Vgs_step=Vgs_trans_step_ss,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransfer(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=device["X"],yloc=device["Y"],devicenamemodifier="Vds_"+formatnum(number=Vds,precision=2,nonexponential=True)+"_-+")
		# iv.measure_ivfoc_topgate(sweepdelay=0.05,Vds_start=Vds_focstart,Vds_stop=Vds_focstop,Vds_npts=Vds_focnpts,Vgs_start=Vgs_focstart,Vgs_stop=Vgs_focstop,Vgs_npts=Vgs_focnpts,draincomp=draincomp,gatecomp=gatecomp)
		# iv.writefile_ivfoc(pathname=pathname,wafername=wafername_runno,devicename=devicename,devicenamemodifier="",xloc=device["X"],yloc=device["Y"])

Vds_bias_array=[-0.01,-0.05,-0.1,-0.15,-0.2,-0.3,-0.4,-0.5,-1.0]
Vgs_trans_start_ss=2.
Vgs_trans_stop_ss=-3.
Vgs_trans_step_ss=-0.2
for Vds in Vds_bias_array:
	for pconst in probeconstellations:
		device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
		devicename=device["name"]
		testorder=pconst["testorder"]
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"],"testorder =",testorder)
		iv.measure_ivtransfer_topgate(sweepdelay=0.1,Vds=Vds,Vgs_start=Vgs_trans_start_ss, Vgs_stop=Vgs_trans_stop_ss, Vgs_step=Vgs_trans_step_ss,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransfer(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=device["X"],yloc=device["Y"],devicenamemodifier="Vds_"+formatnum(number=Vds,precision=2,nonexponential=True)+"_+-")
		# iv.measure_ivfoc_topgate(sweepdelay=0.05,Vds_start=Vds_focstart,Vds_stop=Vds_focstop,Vds_npts=Vds_focnpts,Vgs_start=Vgs_focstart,Vgs_stop=Vgs_focstop,Vgs_npts=Vgs_focnpts,draincomp=draincomp,gatecomp=gatecomp)
		# iv.writefile_ivfoc(pathname=pathname,wafername=wafername_runno,devicename=devicename,devicenamemodifier="",xloc=device["X"],yloc=device["Y"])


# Vds_focstart = 0.
# Vds_focstop = -1.5
# Vds_focnpts =31
#
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
# 	devicename=device["name"]
# 	testorder=pconst["testorder"]
# 	totalnumbercleans=proberesistanceclean_singleprobe(iv=iv,resisttestdevicename="short",cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 	print ("probing devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"],"testorder =",testorder)
# 	iv.measure_ivfoc_topgate(sweepdelay=0.05,Vds_start=Vds_focstart,Vds_stop=Vds_focstop,Vds_npts=Vds_focnpts,Vgs_start=Vgs_focstart,Vgs_stop=Vgs_focstop,Vgs_npts=Vgs_focnpts,draincomp=draincomp,gatecomp=gatecomp)
# 	iv.writefile_ivfoc(pathname=pathname,wafername=wafername_runno,devicename=devicename,devicenamemodifier="Vds+-",xloc=device["X"],yloc=device["Y"])

# Vds_focstart = 0.
# Vds_focstop = -1.5
# Vds_focnpts =31
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
# 	devicename=device["name"]
# 	testorder=pconst["testorder"]
# 	totalnumbercleans=proberesistanceclean_singleprobe(iv=iv,resisttestdevicename="short",cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 	print ("probing devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"],"testorder =",testorder)
# 	iv.measure_ivfoc_topgate(sweepdelay=0.05,Vds_start=Vds_focstart,Vds_stop=Vds_focstop,Vds_npts=Vds_focnpts,Vgs_start=Vgs_focstart,Vgs_stop=Vgs_focstop,Vgs_npts=Vgs_focnpts,draincomp=draincomp,gatecomp=gatecomp)
# 	iv.writefile_ivfoc(pathname=pathname,wafername=wafername_runno,devicename=devicename,devicenamemodifier="Vds+-",xloc=device["X"],yloc=device["Y"])
###############################################################################################################################################################################################################################################

# Vdssetting=[-0.01,-0.1,-0.5,-1.0,-1.5]
# Vgssweepdir=['-+','+-']
#
# for devmodifier in Vgssweepdir:
# 	if devmodifier=='-+':
# 		Vgs_trans_start_ss=-3.
# 		Vgs_trans_stop_ss=2.
# 		Vgs_trans_step_ss=0.1
# 	else:
# 		Vgs_trans_start_ss=2.
# 		Vgs_trans_stop_ss=-3.
# 		Vgs_trans_step_ss=-0.1
# 	for Vds in Vdssetting:
# 		totalnumbercleans=0
# 		for pconst in probeconstellations:
# 			if totalnumbercleans>50:
# 				print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 				quit()
# 			device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
# 			devicename=device["name"]
# 			testorder=pconst["testorder"]
# 			totalnumbercleans=proberesistanceclean_singleprobe(iv=iv,resisttestdevicename="short",cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 			print ("probing devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"],"testorder =",testorder)
# 			iv.measure_ivtransfer_topgate(sweepdelay=0.1,Vds=Vds,Vgs_start=Vgs_trans_start_ss, Vgs_stop=Vgs_trans_stop_ss, Vgs_step=Vgs_trans_step_ss,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_ivtransfer(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=device["X"],yloc=device["Y"],devicenamemodifier=devmodifier+formatnum(Vds,precision=2,nonexponential=True))


# ###############################################################################################################################################################################################################################################
cascade.unlockstage()
cascade.move_separate()
# #del cascade
print("done probing wafer")