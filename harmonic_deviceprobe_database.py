__author__ = 'PMarsh Carbonics'
import visa
from loadpull_system_calibration import *
from rf_synthesizer import *
from harmonic_measurement import *
from IP3_focus_tuned import *
from parameter_analyzer import *
from spectrum_analyzer import *
from read_reflection_parametervsreflection import *
from create_probeconstellations_devices.probe_constellations_map import *


rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())
from cascade import CascadeProbeStation
ps=ParameterAnalyzer(rm)

#Vgsbias = -2.
Vdsbias = -1.
gcomp = 1E-3
dcomp = 0.1

navg=32                         # number of averages to form measured spectra
fcent = 1.5E9
fdelta = 4E6
#fspanf = 100E3                 # measurement span for each frequency component of the fundamentals

ffa = fcent-fdelta/2
ffb= fcent+fdelta/2
fda = ffa-fdelta
fdb = ffb+fdelta
atten = 10.

pwrstart = -14.
pwrstop = -14.
delpwr=0

sysTOI=30

goodId=1.E-6                        # drain current must exceed this to qualify device for further testing
goodIg=5E-6                          # gate current must be LESS than this amount to qualify device for further testing
Vgs_validation = -1
Vds_validation = -1

wafername="QW2"
runnumber=5
wafername_runno=wafername+"meas"+str(runnumber)

pathname = "C:/Users/test/python/data/"+wafername_runno
cascade = CascadeProbeStation(rm=rm)                                                               # setup Cascade
sa=SpectrumAnalyzer(rm=rm)
rf=Synthesizer(rm=rm,maximumpowersetting=14)

probc=ConstellationsdB(maskname="v6_2finger_single",wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probelistfilename="/".join([pathname,"devicesharmtest.csv"]))
dist=Harmonic_distortion(rm=rm, sa=sa, rf=rf, dc=ps, spectrum_analyser_input_attenuation=10, fundamental_frequency=170E6, source_calibration_factor_fundamental=sourcecalfactorharmonic, SA_calibration_factor_fundamental=outputcalfactorharmonic_1st,
                         SA_calibration_factor_2nd_harmonic=outputcalfactorharmonic_2nd, SA_calibration_factor_3rd_harmonic=outputcalfactorharmonic_3rd)


#Vgsarray=[-3.,-2.75,-2.5,2.25,-2.,-1.75,-1.5,-1.25,-1.,-0.75,-.5]
#Vgsarray=[-2.]

for pconst in probeconstellations:
	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	print("device ", pconst["name"])
	Idval,Igval,Idcompstatval,Igcompstatval=ps.fetbiason_topgate(Vgs=Vgs_validation, Vds=Vds_validation, gatecomp=gcomp, draincomp=dcomp)
	ps.fetbiasoff()
	print ( "Id= "+str(Idval)+ " Ig="+str(Igval)+" drain status "+str(Idcompstatval)+" gate status "+str(Igcompstatval))
	if abs(Idval)>goodId and Idcompstatval=="N" and Igcompstatval=="N":
		devicegood = True
	else:
		devicegood = False
		print("Bad device")
	if devicegood:
		ps.measure_ivtransfer_topgate(inttime='2',delaytime=0.05,Vds=Vdsbias, Vgs_start=-3, Vgs_stop=2, Vgs_step=0.2, gatecomp=gcomp, draincomp=dcomp)
		ps.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=device["X"],yloc=device["Y"],devicenamemodifier="harmonictest-1V")
		dist.get_harmonic_fundamental(powerlevel=-15.,Vds=Vdsbias,Vgs_start=-3.,Vgs_stop=-1.5,Vgs_step=0.1,maxdeltapower=0.2,gatecomp=1E-5,draincomp=0.1)
		dist.writefile_harmonicdistortion(pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=device["X"],yloc=device["Y"],devicenamemodifier="")


Vdsbias=-1.5
probeconstellations=probc.get_probing_constellations(probelistfilename="/".join([pathname,"devicesharmtest_original.csv"]))
for pconst in probeconstellations:
	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]    # get names list of all devices in this probe constellation
	devicename=device["name"]
	print("device ", pconst["name"])
	Idval,Igval,Idcompstatval,Igcompstatval=ps.fetbiason_topgate(Vgs=Vgs_validation, Vds=Vds_validation, gatecomp=gcomp, draincomp=dcomp)
	ps.fetbiasoff()
	print ( "Id= "+str(Idval)+ " Ig="+str(Igval)+" drain status "+str(Idcompstatval)+" gate status "+str(Igcompstatval))
	if abs(Idval)>goodId and Idcompstatval=="N" and Igcompstatval=="N":
		devicegood = True
	else:
		devicegood = False
		print("Bad device")
	if devicegood:
		ps.measure_ivtransfer_topgate(inttime='2',delaytime=0.05,Vds=Vdsbias, Vgs_start=-3, Vgs_stop=2, Vgs_step=0.2, gatecomp=gcomp, draincomp=dcomp)
		ps.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=device["X"],yloc=device["Y"],devicenamemodifier="harmonictest-1.5")
		dist.get_harmonic_fundamental(powerlevel=-15.,Vds=Vdsbias,Vgs_start=-3.,Vgs_stop=-1.5,Vgs_step=0.1,maxdeltapower=0.2,gatecomp=1E-5,draincomp=0.1)
		dist.writefile_harmonicdistortion(pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=device["X"],yloc=device["Y"],devicenamemodifier="Vds_-1.5")
cascade.move_separate()
cascade.unlockstage()
#time.sleep(120)
print("done probing wafer")