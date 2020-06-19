# main wafer probing routine for passive devices
import visa
from probing_utilities import *
from create_probeconstellations_devices.probe_constellations_map import *
from calculated_parameters import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from pna import Pna                                                                 # network analyzer
from cascade import CascadeProbeStation                                                    # Cascade wafer prober
#from old.plotSmeas import dataPlotter
from IVplot import *
from parameter_analyzer import ParameterAnalyzer                                    # IV and bias

pna = Pna(rm,1)                                                                    # setup network analyzer
iv=ParameterAnalyzer(rm)

Vbiasmax=-3.5
Vslew=1.
compliance=0.0001


wafername="WF134shuntcap"
runnumber=3
maskname="v8_shuntcap"
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno

cascade = CascadeProbeStation(rm=rm)         # setup Cascade NO probeplan file here! This also moves
probc=ConstellationsdB(maskname=maskname,wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations()

##########################################################################################################################

for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
	devicename=device["name"]
	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
	print ("probing device ",devicename)

	pna.pna_getS_2port(instrumentstate="2port_LF.sta",calset="CalSet_2",navg=2)												# get the S-parameters
	pna.writefile_spar(measurement_type="All_RI",pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=device["X"],yloc=device["Y"])
	iv.measure_leakage_controlledslew(Vbiasslewrate=Vslew, Vbias_stop=Vbiasmax, comp=compliance, Vbias_npts=10,series=True)
	iv.writefile_measure_leakage_controlledslew(pathname=pathname,devicename=devicename,wafername=wafername,xloc=device["X"],yloc=device["Y"])
##################################################################################################################################

cascade.move_separate()
cascade.unlockstage()
print("done probing wafer")