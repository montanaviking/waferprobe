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
maxallowedproberesistance=3.

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
# Vgs_validation = 0.
# Vds0_validation = -1.
# Vds1_validation = -1.



wafername="L6_W"
runnumber=6
maskname="L6_W"


# get probe constellations
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno
cascade = CascadeProbeStation(rm=rm)         # setup Cascade NO probeplan file here! This also moves
probc=ConstellationsdB(maskname=maskname,wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probe_order_start=0,probe_order_stop=100000)
#firsttime=True
nodevbetweentest=30                        # number of devices probed between probe resistance tests
devcounterbetweentests=0               # counts number of devices probed since last probe resistance test
totalnumbercleans=0


#******************** start here
#######################################################################################################
## Transfer curve loops at low bias, Vds = -1.5 V 2 full loops, rate dependence
totalnumbercleans=0
for i in range(22,len(probeconstellations)):
	pconst=probeconstellations[i]
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=1., quiescenttime=0,startstopzero=True, Vds=-1.5,Vgs_start=-10,Vgs_stop=10,Vgs_step=.5,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc_probe=pconst["X"],yloc_probe=pconst["Y"],devicenamemodifier='slew1Vgs10Vds-1.5')
###############################


#######################################################################################################
## Transfer curve loops at low bias, Vds = -1.5 V 2 full loops, rate dependence
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=25., quiescenttime=0, startstopzero=True, Vds=-1.5,Vgs_start=-20,Vgs_stop=20,Vgs_step=1,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc_probe=pconst["X"],yloc_probe=pconst["Y"],devicenamemodifier='slew25Vgs20Vds-1.5')
###############################

#######################################################################################################
## Transfer curve loops at low bias, Vds = -1.5 V 2 full loops, rate dependence
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=10., quiescenttime=0, startstopzero=True, Vds=-1.5,Vgs_start=-20,Vgs_stop=20,Vgs_step=1,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc_probe=pconst["X"],yloc_probe=pconst["Y"],devicenamemodifier='slew10Vgs20Vds-1.5')
###############################

#######################################################################################################
## Transfer curve loops at low bias, Vds = -1.5 V 2 full loops, rate dependence
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=1., quiescenttime=0,startstopzero=True, Vds=-1.5,Vgs_start=-20,Vgs_stop=20,Vgs_step=1,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc_probe=pconst["X"],yloc_probe=pconst["Y"],devicenamemodifier='slew1Vgs20Vds-1.5')
###############################











################################################
# foc Vds hysteresis at Vgs=0V (one foc)
#######################################################################################################
## drain hysteresis Vds from 0->-1->+1->0V at slew rate of 1V/sec
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_ivfoc_Vdsloop_controlledslew_dual_backgated(Vdsslewrate=1, quiescenttime=0,startstopzero=True, Vds_start=-1, Vds_stop=1, Vds_npts=21, Vgs_start=0, Vgs_stop=0, Vgs_npts=1,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivfoc_Vdsloop_dual(pathname=pathname,wafername=wafername_runno,devicenames=devicenames,xloc_probe=pconst["X"],yloc_probe=pconst["Y"],devicenamemodifier="Vgs0Vds1+-+-")
###############################

#######################################################################################################
## drain hysteresis Vds from 0->-2->+2->0V at slew rate of 1V/sec
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_ivfoc_Vdsloop_controlledslew_dual_backgated(Vdsslewrate=1, quiescenttime=0,startstopzero=True, Vds_start=-2, Vds_stop=2, Vds_npts=21, Vgs_start=0, Vgs_stop=0, Vgs_npts=1,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivfoc_Vdsloop_dual(pathname=pathname,wafername=wafername_runno,devicenames=devicenames,xloc_probe=pconst["X"],yloc_probe=pconst["Y"],devicenamemodifier="Vgs0Vds2+-+-")
###############################

#######################################################################################################
## drain hysteresis Vds from 0->-2->+2->0V at slew rate of 1V/sec
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_ivfoc_Vdsloop_4sweep_controlledslew_dual_backgated(Vdsslewrate=1, startstopzero=True, Vds_start=-1, Vds_stop=1, Vds_npts=21, Vgs_start=10, Vgs_stop=-20, Vgs_npts=7, gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivfoc_Vds4sweep_dual(pathname=pathname,wafername=wafername_runno,devicenames=devicenames,xloc_probe=pconst["X"],yloc_probe=pconst["Y"],devicenamemodifier="Vds1")
###############################

#################################################################################################################################################################################################################
# time domain Vds=-0.01V
#####################################################

## time domain stability test ############################################################################
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_hysteresistimedomain_dual_backgated(Vds=-0.01,Vgsquiescent=0.,timestep=.01,timequiescent=0.,timeend=40.,Vgs_start=0.,Vgs_step=0,Vgs_stop=0,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_0.Vds-0.01VgsQ0Vgs0')
###############################



## time domain Vds=-0.01V  positive quiescent voltage Vgs=0V############################################################################
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_hysteresistimedomain_dual_backgated(Vds=-0.01,Vgsquiescent=20.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=0.,Vgs_step=0.,Vgs_stop=0.,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-0.01VgsQ20Vgs0')
###############################

## time domain Vds=-0.01V  positive quiescent voltage Vgs=-15V############################################################################
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_hysteresistimedomain_dual_backgated(Vds=-0.01,Vgsquiescent=20.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=-15.,Vgs_step=0.,Vgs_stop=-15.,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-0.01VgsQ20Vgs-15')
#########################################################################################################



## time domain Vds=-0.01V negative quiescent voltage Vgs=0V ############################################################################
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_hysteresistimedomain_dual_backgated(Vds=-0.01,Vgsquiescent=-20.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=0.,Vgs_step=0,Vgs_stop=0,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-0.01VgsQ-20Vgs0')
###############################

## time domain Vds=-0.01V negative quiescent voltage Vgs=-15V ############################################################################
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_hysteresistimedomain_dual_backgated(Vds=-0.01,Vgsquiescent=-20.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=-15.,Vgs_step=0,Vgs_stop=-15,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-0.01VgsQ-20Vgs-15')
###############################


## time domain Vds=-0.01V VgsQ=+20V Vgs=0V bias stress tests ############################################################################
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_hysteresistimedomain_dual_backgated(Vds=-0.01,Vgsquiescent=20.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=0.,Vgs_step=0,Vgs_stop=0,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_5Vds-0.01VgsQ+20Vgs0')
###############################

## time domain Vds=-0.01V VgsQ=+20V Vgs=-15V bias stress tests ############################################################################
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_hysteresistimedomain_dual_backgated(Vds=-0.01,Vgsquiescent=20.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=-15.,Vgs_step=0,Vgs_stop=-15,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_5Vds-0.01VgsQ+20Vgs-15')
###############################
##################################################################################################################################################################################################


################## time domain Vds=-2V

## time domain stability test ############################################################################
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_hysteresistimedomain_dual_backgated(Vds=-2.,Vgsquiescent=0.,timestep=.01,timequiescent=0.,timeend=40.,Vgs_start=0.,Vgs_step=0,Vgs_stop=0,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_0.Vds-2VgsQ0Vgs0')
###############################



## time domain Vds=-2.V  positive quiescent voltage Vgs=0V############################################################################
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_hysteresistimedomain_dual_backgated(Vds=-2.,Vgsquiescent=20.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=0.,Vgs_step=0.,Vgs_stop=0.,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-2VgsQ20Vgs0')
###############################

## time domain Vds=-2.V  positive quiescent voltage Vgs=-15V############################################################################
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_hysteresistimedomain_dual_backgated(Vds=-2.,Vgsquiescent=20.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=-15.,Vgs_step=0.,Vgs_stop=-15.,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-2VgsQ20Vgs-15')
#########################################################################################################



## time domain Vds=-2.V negative quiescent voltage Vgs=0V ############################################################################
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_hysteresistimedomain_dual_backgated(Vds=-2.,Vgsquiescent=-20.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=0.,Vgs_step=0,Vgs_stop=0,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-2VgsQ-20Vgs0')
###############################

## time domain Vds=-2.V negative quiescent voltage Vgs=-15V ############################################################################
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_hysteresistimedomain_dual_backgated(Vds=-2.,Vgsquiescent=-20.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=-15.,Vgs_step=0,Vgs_stop=-15,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-2VgsQ-20Vgs-15')
###############################


## time domain Vds=-2.V VgsQ=+20V Vgs=0V bias stress tests ############################################################################
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_hysteresistimedomain_dual_backgated(Vds=-2.,Vgsquiescent=20.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=0.,Vgs_step=0,Vgs_stop=0,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_5Vds-2VgsQ+20Vgs0')
###############################

## time domain Vds=-2.V VgsQ=+20V Vgs=-15V bias stress tests ############################################################################
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
	devicenames=[devices[0]["name"],devices[1]["name"]]
	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
	else:
		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])

		iv.measure_hysteresistimedomain_dual_backgated(Vds=-2.,Vgsquiescent=20.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=-15.,Vgs_step=0,Vgs_stop=-15,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_5Vds-2VgsQ+20Vgs-15')
###############################











cascade.move_separate()

print("done probing wafer")