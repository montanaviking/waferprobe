# test of untuned Vgs swept TOI measurement

from IP3_Vgssweep import *
from loadpull_system_calibration import *
from cascade import CascadeProbeStation
from create_probeconstellations_devices.probe_constellations_map import *

rm=visa.ResourceManager()
wafername="QW2"
runnumber=5
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno
cascade = CascadeProbeStation(rm=rm)                                                               # setup Cascade
probc=ConstellationsdB(maskname="v6_2finger_single",wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probe_device_list=["C4_R4_B50_D43"])

pconst=probeconstellations[0]
cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
devicename=device["name"]
print("device ", pconst["name"])

gcomp=0.001
dcomp=0.01
Vds=-1
Vgs=0.
output_reflection=[0,0]
Pin=-14
#ps=ParameterAnalyzer(rm)

#Idval,Igval,Idcompstatval,Igcompstatval=ps.fetbiason_topgate(Vgs=Vgs, Vds=Vds, gatecomp=gcomp, draincomp=dcomp)
IP3=IP3_Vgssweep(rm=rm, powerlevel_minimum=Pin, powerlevel_maximum=Pin, powerlevel_step=0, center_frequency=1.5E9, frequency_spread=4E6, Vgsmin=-2.5, Vgsmax=0, Vgsperiod=0.01)
# IP3.measureTOI_gain(output_reflection=output_reflection,Pin=Pin,draincomp=dcomp,gatecomp=gcomp,Vds=Vds,noavg_dist=256)
# IP3.writefile_TOI_Vgssweep(pathname="C:/Users/test/python/data/TOI_swept_Vgs/",wafername=wafername_runno,devicename=devicename,xloc=device['X'],yloc=device['Y'],devicenamemodifier='10mS_gamma_0_ang0_Pin_'+formatnum(Pin,precision=2,nonexponential=True))
IP3.TOIsearch(Vds=Vds,Pin=Pin,initial_output_reflections=[ [0.010,164.304], [0.201,91.344], [0.505,27.076], [0.469,-2.623] ])
IP3.writefile_Vgssweep_TOIsearch(pathname="C:/Users/test/python/data/TOI_swept_Vgs/",wafername=wafername_runno,devicename=devicename,xloc=device['X'],yloc=device['Y'],devicenamemodifier='both3rd_10mS_gamma_0_ang0_Pin_'+formatnum(Pin,precision=2,nonexponential=True))