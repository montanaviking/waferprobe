# main wafer probing routine
import visa
from utilities import formatnum
from create_probeconstellations_devices.probe_constellations_map import *
from create_probeconstellations_devices.waferdevice_map_v2 import *
from probing_utilities import proberesistanceclean_singleprobe_inreticle
import collections as col
from probing_utilities import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from cascade import CascadeProbeStation                                                    # Cascade wafer prober

iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
maxallowedproberesistance=5
maxallowedproberesistancedifference=3.

# set up of IV and bias voltages
# family of curves
Vgs_focstart = -8.
Vgs_focstop = 2.
Vgs_focnpts = 11

Vds_focstart =-1.
Vds_focstop = 0.
Vds_focnpts =20

Vds_focstart_loop =-1.
Vds_focstop_loop = 1.
Vds_focnpts_loop =20

Vgs_trans_start_ss=-8.0
Vgs_trans_stop_ss=2.0
Vgs_trans_step_ss=0.1


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
Vgs_validation = -2.
Vds0_validation = -0.5
Vds1_validation = -0.5

wafername="QW2"
runnumber=6
maskname="v6_2finger_single"

wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno
devicelisttotestfile=pathname+"/devicestest.csv"

cascade = CascadeProbeStation(rm=rm)         # setup Cascade NO probeplan file here! This also moves
probc=ConstellationsdB(maskname=maskname,wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probelistfilename=devicelisttotestfile,startprobenumber=0,stopprobenumber=100000)

firsttime=True
nodevbetweentest=20                        # number of devices probed between probe resistance tests
devcounterbetweentests=0               # counts number of devices probed since last probe resistance test
totalnumbercleans=0
maximumallowedcleans=50
###################################################################################################################################
################



# Vds=-0.01V
###################
#stability test
#####################################################
Vds=-0.01
Vgsquiescent=0.
Vgs=0.
timequiescent=0.1

## time domain test ############################################################################
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################

#Positive quiescent voltage:
#####################################################
Vgsquiescent=2.
Vgs=0.
timequiescent=0.5
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################
#####################################################
Vgs=-2.
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################
################################################################################################################################################################################################################################################################################################




#Negative quiescent voltage:
#####################################################
Vgsquiescent=-3.
Vgs=0.
timequiescent=0.5
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################
#####################################################
Vgs=-2.
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################
################################################################################################################################################################################################################################################################################################




#Bias stress tests:
#####################################################
Vgsquiescent=2.
Vgs=0.
timequiescent=5.
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################
#####################################################
Vgs=-2.
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################
#####################################################
Vgsquiescent=-3.
Vgs=0.
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################
#####################################################
Vgs=-2.
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################
################################################################################################################################################################################################################################################################################################







































# Vds=-1.5V
###################
#stability test
#####################################################
Vds=-1.5
Vgsquiescent=0.
Vgs=0.
timequiescent=0.1

## time domain test ############################################################################
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################

#Positive quiescent voltage:
#####################################################
Vgsquiescent=2.
Vgs=0.
timequiescent=0.5
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################
#####################################################
Vgs=-2.
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################
################################################################################################################################################################################################################################################################################################




#Negative quiescent voltage:
#####################################################
Vgsquiescent=-3.
Vgs=0.
timequiescent=0.5
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################
#####################################################
Vgs=-2.
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################
################################################################################################################################################################################################################################################################################################




#Bias stress tests:
#####################################################
Vgsquiescent=2.
Vgs=0.
timequiescent=5.
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################
#####################################################
Vgs=-2.
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################
#####################################################
Vgsquiescent=-3.
Vgs=0.
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################
#####################################################
Vgs=-2.
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain(Vds=Vds, backgated=False, Vgsquiescent=Vgsquiescent, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs, Vgs_stop=Vgs, Vgs_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VgsQ_"+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,1))
###############################
################################################################################################################################################################################################################################################################################################


































# pulsed drain
#####################################################
Vds=-1.5
VdsQ=0.
Vgs=0.
timequiescent=0.1
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("in IVprobingdual_topgate_hysteresis_database.py ", pconst["name"])
		proberesistanceclean_singleprobe(backgated=False,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		if "short" not in device["name"].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing device ",devicename, " x0, y0 = ", device["X"]," ",device["Y"])
			iv.measure_hysteresistimedomain_pulseddrain(Vgs=Vgs,backgated=False, Vdsquiescent=VdsQ, timestep=0.01, timequiescent=timequiescent,timeend=40.,Vds_start=Vds, Vds_stop=Vds, Vds_step=0, draincomp=draincomp, gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200_pulseddrain(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],timepointsperdecade=20,devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_VdsQ_"+formatnum(VdsQ,1)+'Vgs'+formatnum(Vgs,1))
###############################
################################################################################################################################################################################################################################################################################################




cascade.move_separate()
cascade.unlockstage()
# #del cascade
print("done probing wafer")