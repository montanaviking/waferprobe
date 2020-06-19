__author__ = 'PMarsh Carbonics'
import visa
from loadpull_system_calibration import *
# from pulsegenerator import *
#
# rm=visa.ResourceManager()
# pulse=PulseGeneratorDG1022(rm)

from IP3_focus_tuned import *
from parameter_analyzer import *
from spectrum_analyzer import *
from read_reflection_parametervsreflection import *
from create_probeconstellations_devices.probe_constellations_map import *
from cascade import CascadeProbeStation


rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

ps=ParameterAnalyzer(rm)


cas1=[[probefile,'flip']]
cas2=[[tuneroutputcable,'noflip']]

#Vgsbias = -2.
Vdsbias = -1.5
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
probc=ConstellationsdB(maskname="v6_2finger_single",wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probelistfilename="/".join([pathname,"selecteddevice_TOI_-1V.csv"]))
#IP3tuned = IP3_Tuned(rm=rm, cascadefiles_port1=cas1, cascadefiles_port2=cas2, spectrum_analyzer_input_attenuation=atten, number_of_averages=navg, powerlevel_start=pwrstart ,powerlevel_stop=pwrstop ,powerlevel_step=delpwr, center_frequency=fcent, frequency_spread=fdelta,spectrum_analyzer_cal_factor=sacalfactor, source_calibration_factor_lowerfreq=sourcecalfactorlowerfreq, source_calibration_factor_upperfreq=sourcecalfactorupperfreq,system_TOI=sysTOI)
IP3tuned = IP3_Tuned(rm=rm, cascadefiles_port1=cas1, cascadefiles_port2=cas2, spectrum_analyzer_input_attenuation=atten, number_of_averages=navg, powerlevel_start=pwrstart ,powerlevel_stop=pwrstop ,powerlevel_step=delpwr, center_frequency=fcent, frequency_spread=fdelta,spectrum_analyzer_cal_factor=sacalfactor, source_calibration_factor=sourcecalfactor,system_TOI=sysTOI,powermetercalfactor=97.6)

#Cp=PowerCompressionTuned(rm=rm, tunerfile=tunerfile, cascadefiles_port1=cas1, cascadefiles_port2=cas2, spectrum_analyser_input_attenuation=atten, number_of_averages=navg, powerlevel_min=pwrstart ,powerlevel_max=pwrstop ,powerlevel_step=delpwr,spectrum_analyzer_cal_factor=sacalfactor,source_calibration_factor=sourcecalfactor)
#reflections=[[.85,40.],[.6,40.]]                  # reflection coefficients presented to DUT output during TOI tests
Vgsarray=[-3.,-2.5,-2.,-1.5,-1,-0.75,-0.5]
#Vgsarray=[-2.]
reflections=read_reflection_coefficients(pathname+"/TOIreflections.csv")
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
	#Vgsarray=np.arange(0.5,-3.1,-0.1)
	if devicegood:
		ps.measure_ivtransfer_topgate(inttime='2',delaytime=0.05,Vds=-1.5, Vgs_start=-3, Vgs_stop=1, Vgs_step=0.2, gatecomp=gcomp, draincomp=dcomp)
		ps.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=device["X"],yloc=device["Y"],devicenamemodifier="test_TOIatVds-1.5V")
		for Vgsbias in Vgsarray:
			Id,Ig,drainstatus,gatestatus=ps.fetbiason_topgate(Vgs=Vgsbias, Vds=Vdsbias, gatecomp=gcomp, draincomp=dcomp,timeiter=10.,maxchangeId=0.01,maxtime=40.)				# bias device again to update currents etc..
			print("Vds, Vgs, Id, Ig, drain status gate status", Vdsbias, Vgsbias, Id, Ig,drainstatus,gatestatus)
			#TOIl,TOIh,DUTgain,pinDUT,pfund,pdl,pdh,noisefloor,ml,mh,poutm,bl,bh,r,reflectcoefactual= IP3tuned.measureTOI(output_reflection=reflections, fractlinfitlower=0., fractlinearfitupper=1., plotgraphs=True)
			#print("DUT gain dB is",DUTgain)
			##IP3tuned.TOIsearch(initial_output_reflections=reflections, fractlinfitlower=0., fractlinearfitupper=1., plotgraphs=True,expected_gain=10.)
			IP3tuned.TOIsearch(initial_output_reflections=reflections)
			#IP3tuned.measureTOI(output_reflection=[[0.53,23]])
			#ps.fetbiasoff()
			IP3tuned.writefile_TOI(pathname=pathname,wafername=wafername_runno,xloc=device["X"],yloc=device["Y"],Id=Id,Vds=Vdsbias,Vgs=Vgsbias,Ig=Ig,devicename=devicename,gatestatus=gatestatus,drainstatus=drainstatus,devicenamemodifier="_Vds"+formatnum(Vdsbias,precision=1)+"_Vgs"+formatnum(Vgsbias,precision=2))
cascade.move_separate()
cascade.unlockstage()
#time.sleep(120)
print("done probing wafer")