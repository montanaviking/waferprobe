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


Vgs_trans_start_ss=-25.
Vgs_trans_stop_ss=5.
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


wafername="L5"
runnumber=6
maskname="v4_TLM"



# get probe constellations
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno
cascade = CascadeProbeStation(rm=rm)         # setup Cascade NO probeplan file here! This also moves
probc=ConstellationsdB(maskname=maskname,wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(devicesubstringnamelogic="or",devicesubstringnames=["C14_R12","C15_R12","C16_R12","C17_R12"],startprobenumber=0,stopprobenumber=10000)
#firsttime=True
nodevbetweentest=30                        # number of devices probed between probe resistance tests
devcounterbetweentests=0               # counts number of devices probed since last probe resistance test
totalnumbercleans=0

#######################################################################################################
## Transfer curve loops at low Vds=-0.01V
# ###########################
# Vds=-0.01
# Vgs=5
# Vgs_step=0.2
# slewrate=20
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# ##############################
# ###########################
# slewrate=10
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# ##############################
# ###########################
# slewrate=1
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# ########################################################################
#
#
#
# ###########################
# Vgs=10
# Vgs_step=0.5
# slewrate=20
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# ##############################
# ###########################
# slewrate=10
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# ##############################
# ###########################
# slewrate=1
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# #######################################################################
#
#
#
#
# ###########################
# Vgs=20
# Vgs_step=1.0
# slewrate=20
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# ##############################
# ###########################
# slewrate=10
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# ##############################
# ###########################
# slewrate=1
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# ########################################################################
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
# ###########################
# # transfer curves loops at high Vds = -1.5V
# ###########################
# ###########################
# Vds=-1.5
# Vgs=5
# Vgs_step=0.2
# slewrate=20
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# ##############################
# ###########################
# slewrate=10
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# ##############################
# ###########################
# slewrate=1
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# ########################################################################
#
#
#
# ###########################
# Vgs=10
# Vgs_step=0.5
# slewrate=20
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# ##############################
# ###########################
# slewrate=10
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# ##############################
# ###########################
# slewrate=1
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# #######################################################################
#
#
#
#
# ###########################
# Vgs=20
# Vgs_step=1.0
# slewrate=20
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# ##############################
# ###########################
# slewrate=10
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
# ##############################
# ###########################
# slewrate=1
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivtransferloop_4sweep_controlledslew_dual_backgated(Vgsslewrate=slewrate, quiescenttime=0., startstopzero=True, Vds=Vds,Vgs_start=-Vgs,Vgs_stop=Vgs,Vgs_step=Vgs_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier='slewrate'+formatnum(iv.Vgsslew,precision=1)+"Vgs"+formatnum(Vgs,precision=1)+"Vds"+formatnum(Vds,precision=1))
########################################################################






#
#
#
#
# ################################################
# # foc Vds hysteresis at Vgs=0V (one foc)
# # #######################################################################################################
# # ## drain hysteresis Vds from 0->-1->+1->0V at slew rate of 1V/sec
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivfoc_Vdsloop_controlledslew_dual_backgated(Vdsslewrate=1, quiescenttime=0,startstopzero=True, Vds_start=-1, Vds_stop=1, Vds_npts=21, Vgs_start=0, Vgs_stop=0, Vgs_npts=1,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivfoc_Vdsloop_dual(pathname=pathname,wafername=wafername_runno,devicenames=devicenames,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier="Vgs0Vds1+-+-")
# # ###############################
#  #######################################################################################################
# # ## drain hysteresis Vds from 0->-1.5->+1.5->0V at slew rate of 1V/sec
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivfoc_Vdsloop_controlledslew_dual_backgated(Vdsslewrate=1, quiescenttime=0,startstopzero=True, Vds_start=-1.5, Vds_stop=1.5, Vds_npts=21, Vgs_start=0, Vgs_stop=0, Vgs_npts=1,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivfoc_Vdsloop_dual(pathname=pathname,wafername=wafername_runno,devicenames=devicenames,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier="Vgs0Vds1.5+-+")
# # ###############################

#  #######################################################################################################
# # ## drain hysteresis Vds from 0->-1->+1->0V at slew rate of 1V/sec
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_ivfoc_Vdsloop_4sweep_controlledslew_dual_backgated(Vdsslewrate=1, startstopzero=True, Vds_start=-1, Vds_stop=1, Vds_npts=21, Vgs_start=-20, Vgs_stop=10, Vgs_npts=7,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivfoc_Vds4sweep_dual(pathname=pathname,wafername=wafername_runno,devicenames=devicenames,xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"],devicenamemodifier="2loopfull")
# # ###############################
















# #####################################################################################################
# # time domain
# ###################################################################################################
# Vds=-0.01
# Vgs=0.
# ## time domain stability test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=0.,timestep=.01,timequiescent=0.,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='stability_Vds-0.01VgsQ0Vgs0',xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]['X'],xloc1=devices[0]['Y'],yloc0=devices[1]['X'],yloc1=devices[1]['Y'])
# ###############################

# #################################################################################################################################################################################################################
# time domain Vds=-0.01V
# #####################################################
# timequiescent=0.5
# Vgsquiescent=20.
# Vds=-0.01
# Vgs=0.
#
# ## time domain test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=Vgsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
# 		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VgsQ'+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
# ###############################
# #####################################################
#
# Vgs=-15.
#
# ## time domain test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=Vgsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
# 		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VgsQ'+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
# ###############################
#
# Vgsquiescent=-20
# Vgs=0
# ## time domain test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=Vgsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
# 		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VgsQ'+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
# ###############################
# #####################################################
#
# Vgs=-15.
#
# ## time domain test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=Vgsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
# 		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VgsQ'+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
# ###############################
#
#
#
#
#
# ###############################
# timequiescent=5
# Vgsquiescent=20
# Vgs=0
# ## time domain test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=Vgsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
# 		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VgsQ'+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
# ###############################
# #####################################################
#
# Vgs=-15.
#
# ## time domain test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=Vgsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
# 		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VgsQ'+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
# ###############################
#
#
#
#
# ###############################
#
# Vgsquiescent=-20
# Vgs=0
# ## time domain test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=Vgsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
# 		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VgsQ'+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
# ###############################
# #####################################################
#
# Vgs=-15.
#
# ## time domain test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=Vgsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
# 		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VgsQ'+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
# ###############################
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
# # #################################################################################################################################################################################################################
# # time domain Vds=-1.5V
# #####################################################
# ## time domain stability test ############################################################################
# Vds=-1.5
#
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=0.,timestep=.01,timequiescent=0.,timeend=40.,Vgs_start=0.,Vgs_step=0,Vgs_stop=0,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_0.Vds-0.01VgsQ0Vgs0',xloc_probe=pconst["X"],yloc_probe=pconst["Y"])
# ###############################
# timequiescent=0.5
# Vgsquiescent=20.
# Vgs=0.
#
# ## time domain test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=Vgsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
# 		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VgsQ'+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
# ###############################
# #####################################################
#
# Vgs=-15.
#
# ## time domain test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=Vgsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
# 		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VgsQ'+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
# ###############################
#
# Vgsquiescent=-20
# Vgs=0
# ## time domain test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=Vgsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
# 		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VgsQ'+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
# ###############################
# #####################################################
#
# Vgs=-15.
#
# ## time domain test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=Vgsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
# 		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VgsQ'+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
# ###############################
#
#
#
#
#
# ###############################
# timequiescent=5
# Vgsquiescent=20
# Vgs=0
# ## time domain test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=Vgsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
# 		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VgsQ'+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
# ###############################
# #####################################################
#
# Vgs=-15.
#
# ## time domain test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=Vgsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
# 		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VgsQ'+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
# ###############################
#
#
#
#
# ###############################
#
# Vgsquiescent=-20
# Vgs=0
# ## time domain test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=Vgsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
# 		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VgsQ'+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
# ###############################
# #####################################################
#
# Vgs=-15.
#
# ## time domain test ############################################################################
# totalnumbercleans=0
# for pconst in probeconstellations:
# 	if totalnumbercleans>50:
# 		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
# 		quit()
# 	devices=[d for d in probc.get_probing_devices(constellation_name=pconst["name"])]    # get names list of all devices in this probe constellation
# 	devicenames=[devices[0]["name"],devices[1]["name"]]
# 	if("resist" in devicenames[0].lower() or "short" in devicenames[0].lower()):
# 		proberesistanceclean_dualprobe(iv=iv,cascade=cascade,probeconstellations=probc,selectedprobeconstellation=pconst,pathname=pathname,wafername_runno=wafername_runno,totalnumbercleans=totalnumbercleans,maxallowedproberesistance=maxallowedproberesistance)
# 	else:
# 		cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 		print ("probing devices ",devicenames," ", " x0, y0 = ", devices[0]["X"]," ",devices[0]["Y"])
#
# 		iv.measure_hysteresistimedomain_dual_backgated(Vds=Vds,Vgsquiescent=Vgsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vgs_start=Vgs,Vgs_step=0,Vgs_stop=Vgs,draincomp=draincomp,gatecomp=gatecomp)
# 		iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
# 		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VgsQ'+formatnum(Vgsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc_probe=pconst["X"],yloc_probe=pconst["Y"],xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
# ###############################
#
#
#
#
#











Vdsquiescent=0
timequiescent=5
Vds=-1.5
Vgs=0.

# pulsed drain time domain
## time domain test ############################################################################
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

		iv.measure_hysteresistimedomain_pulseddrain_dual_backgated(Vgs=Vgs,Vdsquiescent=Vdsquiescent,timestep=.01,timequiescent=timequiescent,timeend=40.,Vds_start=Vds,Vds_step=0,Vds_stop=Vds,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200_pulseddrain_dual(pathname=pathname,devicenames=devicenames,wafername=wafername_runno, timepointsperdecade=20, devicenamemodifier='Tq_'+formatnum(timequiescent,precision=1)+
		                'Vds'+formatnum(Vds,precision=2,nonexponential=True)+'VdsQ'+formatnum(Vdsquiescent,1)+'Vgs'+formatnum(Vgs,precision=2,nonexponential=True),xloc0=devices[0]["X"],yloc0=devices[0]["Y"],xloc1=devices[1]["X"],yloc1=devices[1]["Y"])
###############################













































cascade.move_separate()

print("done probing wafer")