__author__ = 'PMarsh Carbonics'
import visa

from compression_focus_tuned_with_powermeter import *
from parameter_analyzer import *
from spectrum_analyzer import *
from loadpull_system_calibration import *
from create_probeconstellations_devices.probe_constellations_map import *
from read_reflection_parametervsreflection import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())
from cascade import CascadeProbeStation
ps=ParameterAnalyzer(rm)

cas1=[[probefile,'flip']]
cas2=[[tuneroutputcable,'noflip']]

#Vgsbias = -1.
Vdsbias = -1.5
gcomp = 1e-3
dcomp = 50e-3

navg=10                         # number of averages to form measured spectra
fcent = 1500                    # center frequency in MHz

pwrstart = -16.
pwrstop = 5.
delpwr=2.

wafername="QH11"
runnumber=3
wafername_runno=wafername+"meas"+str(runnumber)

pathname = "C:/Users/test/python/data/"+wafername_runno
cascade = CascadeProbeStation(rm=rm)                                                               # setup Cascade
probc=ConstellationsdB(maskname="v6_2finger_single",wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probelistfilename=pathname+"/"+"selecteddevices_P1dB_-1.5Vds.csv"
#probc=ConstellationsdB(maskname="QH5_single",wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probelistfilename=probelistfilename)
#probeconstellations=probc.get_probing_constellations(probelistfilename="/".join([pathname,"sorteddevices.csv"]))

Cp=PowerCompressionTunedFocus(rm=rm, frequency=1500., cascadefiles_port1=cas1, cascadefiles_port2=cas2, minpower=pwrstart, maxpower=pwrstop, comp_fillin_step=0.5, steppower=delpwr, source_calibration_factor=sourcecalfactor,estimated_gain=-10,synthesizerpowersetmaximum=0.,synthesizerpowersetforcalibration=-15.)

# get device names to probe along with their corresponding Vgs and output reflections used in the compression testing
try: pl=open(probelistfilename,"r")
except: raise ValueError("ERROR! could not find devices list file for devices to probe")
lines=pl.read().splitlines()
probe_device_list=[l.split()[0] for l in lines]
probe_device_reflection=[[float(l.split()[1]),float(l.split()[2])] for l in lines]
probe_device_Vgs=[float(l.split()[3]) for l in lines]

# old version Cp=PowerCompressionTunedFocus(rm=rm, tunertype='load', cascadefiles_port1=cas1, cascadefiles_port2=cas2, powerlevellinear_min=pwrstart, powerlevellinear_max=pwrstop, maxpower=9., comp_fillin_step=1, powerlevel_step=delpwr, source_calibration_factor=source_calibration_factor, input_sensor_calfactor=input_sensor_calfactor)
#reflections=[ [0.770,5.618], [0.710,10.443], [0.536,5.990], [0.620,23.772], [0.808,28.112], [0.878,18.196], [0.752,16.288], [0.884,7.099], [0.878,-1.093], [0.776,-0.521], [0.669,0.641], [0.616,-12.482], [0.420,32.513], [0.694,35.198], [0.430,-20.750], [0.638,-25.376], [0.706,-5.301], [0.866,-7.865], [0.821,-19.113], [0.772,-11.751], [0.497,-40.422], [0.233,4.222], [0.547,46.264], [0.824,-30.166], [0.296,-36.634], [0.7536051384879188,-1.58] ]                # reflection coefficients presented to DUT output during compression tests
#reflections=read_reflection_coefficients(pathname+"/TOIreflections.csv")
for pconst in probeconstellations:
	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	print("device ", pconst["name"])
	ps.measure_ivtransfer_topgate(inttime='2',Vds=Vdsbias, Vgs_start=-3, Vgs_stop=2, Vgs_step=0.2, gatecomp=gcomp, draincomp=dcomp)
	ps.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=device["X"],yloc=device["Y"],devicenamemodifier="compressionatVds-1.5V")
	i=probe_device_list.index(devicename)
	Vgsbias=probe_device_Vgs[i]
	output_reflection=[probe_device_reflection[i]]    # magnitude and angle of applied output reflection coefficient
	Id,Ig,drainstatus,gatestatus=ps.fetbiason_topgate(Vgs=Vgsbias, Vds=Vdsbias, gatecomp=gcomp, draincomp=dcomp,timeiter=10.,maxchangeId=0.01,maxtime=40.)				# bias device again to update currents etc..
	print("Vds, Vgs, Id, Ig, drain status gate status", Vdsbias, Vgsbias, Id, Ig,drainstatus,gatestatus)
	Cp.measurePcomp(output_reflection=output_reflection,Vgs=Vgsbias,Vds=Vdsbias,draincomp=0.1,gatecomp=50E-6)
	Cp.writefile_Pcompression_tuned(pathname=pathname,wafername=wafername_runno,xloc=device["X"],yloc=device["Y"],devicename=devicename,devicenamemodifier="_Vds"+formatnum(Vdsbias,precision=1)+"_Vgs"+formatnum(Vgsbias,precision=2))
cascade.move_separate()
print("done probing wafer")