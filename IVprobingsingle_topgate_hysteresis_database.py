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
# Vgs_focstart = -8
# Vgs_focstop = -8.
# Vgs_focnpts = 1

# Vds_focstart =-1
# Vds_focstop = 0
# Vds_focnpts =21



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



#######################################################################################################################

# Vds=-0.01
# Vgs_start=-0.9
# Vgs_stop=0.9
# Vgs_step=0.1
# Vgsslewrate=17.
Vdslist=[-0.01,-1.5]
Vgsslewratelist=[11.7,5.,1.]
Vgslist=[{'Vgs_start':-0.9,'Vgs_stop':0.9,'Vgs_step':0.1},{'Vgs_start':-1.8,'Vgs_stop':1.8,'Vgs_step':0.2},{'Vgs_start':-3.,'Vgs_stop':2.,'Vgs_step':0.2}]
for Vds in Vdslist:
	for Vgs in Vgslist:
		for Vgsslew in Vgsslewratelist:
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
						iv.measure_ivtransferloop_4sweep_controlledslew(backgated=False,startstopzero=True,Vgsslewrate=Vgsslew,Vds=Vds,Vgs_start=Vgs['Vgs_start'],Vgs_stop=Vgs['Vgs_stop'],Vgs_step=Vgs['Vgs_step'],gatecomp=gatecomp,draincomp=draincomp)
						iv.writefile_ivtransferloop_4sweep(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],
						     devicenamemodifier="Vds_"+formatnum(Vds,precision=2,nonexponential=True)+"_Vgs_"+formatnum(abs(Vgs['Vgs_start']),precision=2,nonexponential=True)+"_Vgsslewrate_"+formatnum(iv.Vgsslew,precision=1,nonexponential=True))















cascade.move_separate()
cascade.unlockstage()
# #del cascade
print("done probing wafer")