# wafer probing
# measure S-parameters vs time
import visa
from probing_utilities import *
from create_probeconstellations_devices.probe_constellations_map import *
from calculated_parameters import *
from writefile_measured import writefile_swept_Spar

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from pna import Pna                                                                 # network analyzer
from cascade import CascadeProbeStation                                                    # Cascade wafer prober
from IVplot import *
from swept_Spar import *

pna = Pna(rm,4)                                                                    # setup network analyzer


Vgs_minimum=-3.                                                   # Vgs array of gate biases for S-parameters
Vgs_maximum=0.
frequencies=[1200E6]

gatecomp = 10E-3                                                                   # gate current compliance in A
draincomp = 0.05                                                                   # drain current compliance in A

wafername="QH27"
runnumber=10
maskname="v6_2finger_single"
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno
devicelisttotestfile=pathname+"/selecteddevices.csv"

cascade = CascadeProbeStation(rm=rm)         # setup Cascade NO probeplan file here! This also moves
probc=ConstellationsdB(maskname=maskname,wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probelistfilename=devicelisttotestfile)

##########################################################################################################################
Vds_bias=0.

for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
	devicename=device["name"]
	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
	print ("probing devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"])

	for RFfreq in frequencies:
		timestamps,Vgsswept,Id,spar,gm_ex,go_ex,Cgs,Cgd,Cds=swept_Spar(rm=rm, gatesweep=True, PNAaverage=8192, sweepfrequency=1000., Vsweptmax=Vgs_maximum, Vsweptmin=Vgs_minimum, Vconstbias=Vds_bias, holdtime=1, RFfrequency_start=1200E6, RFfrequency_stop=1200E6, RFfrequency_step=100E6, DCcomp=.1,offsettime=.000056)
		writefile_swept_Spar(pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=device["X"],yloc=device["Y"],timestamps=timestamps,spar=spar,Id=Id,Vswept=Vgsswept,gm_ex=gm_ex,go_ex=go_ex,Cgs=Cgs,Cgd=Cgd,Cds=Cds,gatesweep=True,fileformat="freqtime",Vconstbias=Vds_bias,devicenamemodifier="Vgs-3_0_Vds=0_2")
##################################################################################################################################
#

cascade.move_separate()
cascade.unlockstage()
print("done probing wafer")