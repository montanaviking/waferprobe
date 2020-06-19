__author__ = 'PMarsh Carbonics'
import visa
from loadpull_system_calibration import *

from IP3_focus_tuned import *
from parameter_analyzer import *
from spectrum_analyzer import *
from read_reflection_parametervsreflection import *


rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())
from cascade import CascadeProbeStation
ps=ParameterAnalyzer(rm)


cas1=[[probefile,'flip']]
cas2=[[tuneroutputcable,'noflip']]

#Vgsbias = -2.
Vdsbias = -2.5
gcomp = 0.5E-6
dcomp = 0.03

navg=10                         # number of averages to form measured spectra
fcent = 1.5E9
fdelta = 4E6
#fspanf = 100E3                 # measurement span for each frequency component of the fundamentals

ffa = fcent-fdelta/2
ffb= fcent+fdelta/2
fda = ffa-fdelta
fdb = ffb+fdelta
atten = 30.

pwrstart = -20.
pwrstop = -10.
delpwr=5.

sysTOI=50

goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
goodIg=500E-9                          # gate current must be LESS than this amount to qualify device for further testing
Vgs_validation = -.5
Vds_validation = -.5

pathname = "C:/Users/test/python/data/Wf169meas11"
pr = CascadeProbeStation(rm,pathname=pathname,planname="Wf169meas11_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
pr.move_plan_index()					# move to first site
IP3tuned = IP3_Tuned(rm=rm, cascadefiles_port1=cas1, cascadefiles_port2=cas2, spectrum_analyser_input_attenuation=atten, number_of_averages=navg, powerlevel_start=pwrstart ,powerlevel_stop=pwrstop ,powerlevel_step=delpwr, center_frequency=fcent, frequency_spread=fdelta,spectrum_analyzer_cal_factor=sacalfactor, source_calibration_factor_lowerfreq=sourcecalfactorlowerfreq, source_calibration_factor_upperfreq=sourcecalfactorupperfreq,system_TOI=sysTOI)
#IP3 = IP3_Tuned(rm=rm, tunerfile=tunerfile, cascadefiles_port1=cas1, cascadefiles_port2=cas2, spectrum_analyser_input_attenuation=atten, number_of_averages=navg, powerlevel_start=pwrstart ,powerlevel_stop=pwrstop ,powerlevel_step=delpwr, center_frequency=fcent, frequency_spread=fdelta,spectrum_analyzer_cal_factor=sacalfactor, source_calibration_factor=sourcecalfactor,system_TOI=sysTOI)
#Cp=PowerCompressionTuned(rm=rm, tunerfile=tunerfile, cascadefiles_port1=cas1, cascadefiles_port2=cas2, spectrum_analyser_input_attenuation=atten, number_of_averages=navg, powerlevel_min=pwrstart ,powerlevel_max=pwrstop ,powerlevel_step=delpwr,spectrum_analyzer_cal_factor=sacalfactor,source_calibration_factor=sourcecalfactor)
#reflections=[[.85,40.],[.6,40.]]                  # reflection coefficients presented to DUT output during TOI tests
reflections=read_reflection_coefficients(pathname+"/TOIreflections.csv")
while pr.get_probingstatus()=="probing wafer":
	print("device ",pr.devicename())
	Idval,Igval,Idcompstatval,Igcompstatval=ps.fetbiason_topgate(Vgs=Vgs_validation, Vds=Vds_validation, gatecomp=gcomp, draincomp=dcomp)
	ps.fetbiasoff()
	print ( "Id= "+str(Idval)+ " Ig="+str(Igval)+" drain status "+str(Idcompstatval)+" gate status "+str(Igcompstatval))
	if abs(Idval)>goodId and Idcompstatval=="N" and Igcompstatval=="N":
		devicegood = True
	else:
		devicegood = False
		print("Bad device")
	#Vgsarray=np.arange(0.5,-3.1,-0.1)
	ps.measure_ivtransfer_topgate(inttime='2',Vds=Vdsbias, Vgs_start=-2.5, Vgs_stop=2, Vgs_step=0.2, gatecomp=gcomp, draincomp=dcomp)
	# ps.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier="")
	if devicegood:
		Vgsarray=[-0.4]
		for Vgsbias in Vgsarray:
			Id,Ig,drainstatus,gatestatus=ps.fetbiason_topgate(Vgs=Vgsbias, Vds=Vdsbias, gatecomp=gcomp, draincomp=dcomp,timeiter=1.,maxchangeId=0.01,maxtime=40.)				# bias device again to update currents etc..
			print("Vds, Vgs, Id, Ig, drain status gate status", Vdsbias, Vgsbias, Id, Ig,drainstatus,gatestatus)
			#TOIl,TOIh,DUTgain,pinDUT,pfund,pdl,pdh,noisefloor,ml,mh,poutm,bl,bh,r,reflectcoefactual= IP3tuned.measureTOI(output_reflection=reflections, fractlinfitlower=0., fractlinearfitupper=1., plotgraphs=True)
			#print("DUT gain dB is",DUTgain)
			IP3tuned.TOIsearch(initial_output_reflections=reflections, fractlinfitlower=0., fractlinearfitupper=1., plotgraphs=True,expected_gain=20.)
			ps.fetbiasoff()
			IP3tuned.writefile_TOI(pathname=pathname,wafername=pr.wafername(),xloc=pr.x(),yloc=pr.y(),Id=Id,Vds=Vdsbias,Vgs=Vgsbias,Ig=Ig,devicename=pr.devicename(),devicenamemodifier="_Vds"+formatnum(Vdsbias,precision=1)+"_Vgs"+formatnum(Vgsbias,precision=2))
	pr.move_nextsite()
pr.move_separate()
time.sleep(120)
print("done probing wafer")