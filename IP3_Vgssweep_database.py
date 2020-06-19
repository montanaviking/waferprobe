# test of untuned Vgs swept TOI measurement
from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from IP3_Vgssweep import *
from compression_focus_tuned_Vgssweep import *
from loadpull_system_calibration import *
from cascade import CascadeProbeStation
from create_probeconstellations_devices.probe_constellations_map import *

rm=visa.ResourceManager()
wafername="QH27"
runnumber=10
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno

cascade = CascadeProbeStation(rm=rm)                                                               # setup Cascade
probc=ConstellationsdB(maskname="v6_2finger_single",wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probelistfilename=pathname+"/selecteddevices.csv")

gatecomp=100E-6
draincomp=.09

Pin=-30
frequency=1.5E9

##########################################################################################################################
Vds_bias=[-0.5,-1.0,-1.5]
Vgs_min=-3.
Vgs_max=0.
IP3=IP3_Vgssweep(rm=rm, tuner=True,powerlevel_minimum=Pin, powerlevel_maximum=Pin, powerlevel_step=0, center_frequency=frequency, frequency_spread=4E6, Vgsmin=Vgs_min, Vgsmax=Vgs_max, Vgsperiod=0.001,spectrum_analyser_input_attenuation=10,holdtime=60)
#Comp=Pcomp_Vgssweep(rm=rm, powerlevel_minimum=powerlevel_minimum,powerlevel_step=1,powerlevel_maximum=powerlevel_maximum,Vgsmin=-1.2,Vgsmax=-0.4,frequency=frequency, Vgsperiod=0.01,spectrum_analyser_input_attenuation=20.,holdtime=60,tuner=False)
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
	devicename=device["name"]
	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
	print ("probing good devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"])

	for Vds in Vds_bias:
		IP3.measure_gainonly(output_reflection=[0.95,180],Pin=Pin,draincomp=draincomp,Vds=Vds,Vgsmin=Vgs_min,Vgsmax=Vgs_max)
		IP3.writefile_gainonly_Vgssweep(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],devicenamemodifier='1mS_shorted_Vds_'+formatnum(abs(Vds),precision=2,nonexponential=True)+"_Vgs_"+formatnum(Vgs_min,precision=2,nonexponential=True)+"_"+formatnum(Vgs_max,precision=2,nonexponential=True))

Vgs_min=-2.
Vgs_max=0.
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
	devicename=device["name"]
	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
	print ("probing good devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"])

	for Vds in Vds_bias:
		IP3.measure_gainonly(output_reflection=[0.95,180],Pin=Pin,draincomp=draincomp,Vds=Vds,Vgsmin=Vgs_min,Vgsmax=Vgs_max)
		IP3.writefile_gainonly_Vgssweep(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],devicenamemodifier='1mS_shorted_Vds_'+formatnum(abs(Vds),precision=2,nonexponential=True)+"_Vgs_"+formatnum(Vgs_min,precision=2,nonexponential=True)+"_"+formatnum(Vgs_max,precision=2,nonexponential=True))

Vds_bias=[-0.1,-0.2,-0.3,-0.4,-0.5,-1.0,-1.5]
Vgs_min=-2.
Vgs_max=2.
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
	devicename=device["name"]
	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
	print ("probing good devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"])

	for Vds in Vds_bias:
		IP3.measure_gainonly(output_reflection=[0.95,180],Pin=Pin,draincomp=draincomp,Vds=Vds,Vgsmin=Vgs_min,Vgsmax=Vgs_max)
		IP3.writefile_gainonly_Vgssweep(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=pconst["X"],yloc=pconst["Y"],devicenamemodifier='1mS_shorted_Vds_'+formatnum(abs(Vds),precision=2,nonexponential=True)+"_Vgs_"+formatnum(Vgs_min,precision=2,nonexponential=True)+"_"+formatnum(Vgs_max,precision=2,nonexponential=True))
IP3.alloff()
cascade.move_separate()
cascade.unlockstage()
print("done probing wafer")

