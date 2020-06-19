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
maxallowedproberesistance=3
maxallowedproberesistancedifference=2.

# set up of IV and bias voltages
# family of curves
Vgs_focstart = -8
Vgs_focstop = -8.
Vgs_focnpts = 1

Vds_focstart =-1
Vds_focstop = 0
Vds_focnpts =21

Vgs_trans_start_ss=-8
Vgs_trans_stop_ss=2
Vgs_trans_step_ss=0.2


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
nodevbetweentest=30                        # number of devices probed between probe resistance tests
#devcounterbetweentests=0               # counts number of devices probed since last probe resistance test
totalnumbercleans=0



########################################################################################################################
#
# Vds=-0.01
# Vgs=-8.0
# Vgsq=-4.0
# Tq=0.05

# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ########################################################################################################################
# Tq=0.1
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ########################################################################################################################
# Tq=0.5
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
#
# #######################################################################################################################
# Tq=5.
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ########################################################################################################################
# Tq=50.
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ##############################################################################################################################################
# #
# #
# #
#
#
#
#
#
#
#
#
#
#
#
#
# stopped here
# ########################################################################################################################
# # 3
# Vgsq=-4.0
# Vgs=4.0
# Tq=0.05
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ########################################################################################################################
# Tq=0.1
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ########################################################################################################################
# Tq=0.5
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
#
# ########################################################################################################################
# Tq=5.
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ########################################################################################################################
# Tq=50.
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ##############################################################################################################################################
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
# ########################################################################################################################
# # 4
# Vgsq=-8.0
# Vgs=4.0
# Tq=0.05
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ########################################################################################################################
# Tq=0.1
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ########################################################################################################################
# Tq=0.5
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
#
# ########################################################################################################################
# Tq=5.
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ########################################################################################################################
# Tq=50.
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ##############################################################################################################################################
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
# ########################################################################################################################
# # 5
# Vgsq=4.0
# Vgs=-8.0
# Tq=0.05
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ########################################################################################################################
# Tq=0.1
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ########################################################################################################################
# Tq=0.5
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
#
# ########################################################################################################################
# Tq=5.
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# #######################################################################################################################
# Tq=50.
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_dual_topgated(Vds=Vds,Vgsquiescent=Vgsq,timequiescent=Tq,timeend=40.,Vgs_start=Vgs,Vgs_stop=Vgs,Vgs_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc_probe=device[0]["X"],
# 			    yloc_probe=device[0]["Y"],xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgsq"+formatnum(Vgsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ##############################################################################################################################################
#
# #
# #
#




























################################################################################################################################################################################################
# pulsed drain time domain
##################################################################################################################################################################################################



########################################################################################################################
# pulsed drain
Vds=-0.01
Vgs=0.0
Vdsq=0.0
Tq=5.

for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		devicenames=[device[0]["name"],device[1]["name"]]
		if "short" not in devicenames[0].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
			iv.measure_hysteresistimedomain_pulseddrain_dual_topgated(Vgs=Vgs,Vdsquiescent=Vdsq,timequiescent=Tq,timeend=40.,Vds_start=Vds,Vds_stop=Vds,Vds_step=0,gatecomp=gatecomp,draincomp=draincomp)
			iv.writefile_pulsedtimedomain4200_pulseddrain_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vdsq"+formatnum(Vdsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
########################################################################################################################

#######################################################################################################################
# pulsed drain
Vds=-1.5

for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
	if len(device)>0:      # probe only if there is a device associated with the probe constellation
		if totalnumbercleans>50:
			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
			quit()
		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
		devicenames=[device[0]["name"],device[1]["name"]]
		if "short" not in devicenames[0].lower():
			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
			iv.measure_hysteresistimedomain_pulseddrain_dual_topgated(Vgs=Vgs,Vdsquiescent=Vdsq,timequiescent=Tq,timeend=40.,Vds_start=Vds,Vds_stop=Vds,Vds_step=0,gatecomp=gatecomp,draincomp=draincomp)
			iv.writefile_pulsedtimedomain4200_pulseddrain_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vdsq"+formatnum(Vdsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
########################################################################################################################

# #######################################################################################################################
# # pulsed drain
# Tq=0.5
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_pulseddrain_dual_topgated(Vgs=Vgs,Vdsquiescent=Vdsq,timequiescent=Tq,timeend=40.,Vds_start=Vds,Vds_stop=Vds,Vds_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_pulseddrain_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vdsq"+formatnum(Vdsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ########################################################################################################################
#
# #######################################################################################################################
# # pulsed drain
# Tq=5.0
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_pulseddrain_dual_topgated(Vgs=Vgs,Vdsquiescent=Vdsq,timequiescent=Tq,timeend=40.,Vds_start=Vds,Vds_stop=Vds,Vds_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_pulseddrain_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vdsq"+formatnum(Vdsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ########################################################################################################################
#
#
#
# #######################################################################################################################
# # pulsed drain
# Tq=50.0
#
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
# 	if len(device)>0:      # probe only if there is a device associated with the probe constellation
# 		if totalnumbercleans>50:
# 			print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
# 			quit()
# 		print("from line 69 in IVprobingdualTLM_database.py ", pconst["name"])
# 		proberesistanceclean_dualprobe(topgate=True,iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,
# 		                               wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 		devicenames=[device[0]["name"],device[1]["name"]]
# 		if "short" not in devicenames[0].lower():
#
# 			cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
#
# 			print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])
#
# 			iv.measure_hysteresistimedomain_pulseddrain_dual_topgated(Vgs=Vgs,Vdsquiescent=Vdsq,timequiescent=Tq,timeend=40.,Vds_start=Vds,Vds_stop=Vds,Vds_step=0,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_pulsedtimedomain4200_pulseddrain_dual(backgated=False,pathname=pathname,wafername=wafername_runno,xloc0=device[0]["X"],yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"],timepointsperdecade=30,devicenames=devicenames,
# 			    devicenamemodifier="Vds"+formatnum(Vds,precision=2,nonexponential=True)+"_Vdsq"+formatnum(Vdsq,precision=1,nonexponential=True)+"_Vgs"+formatnum(Vgs,precision=1,nonexponential=True)+"_Tq"+formatnum(Tq,precision=2,nonexponential=True))
# ########################################################################################################################




cascade.move_separate()
# #del cascade
print("done probing wafer")