__author__ = 'PMarsh Carbonics'
import visa

from IP3_focus_tuned import *
from parameter_analyzer import *
from spectrum_analyzer import *
from read_reflection_parametervsreflection import *
from loadpull_system_calibration import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())
from cascade import CascadeProbeStation

ps=ParameterAnalyzer(rm)

cas1=[[probefile,'flip']]
cas2=[[tuneroutputcable,'noflip']]

Vdsbias = 3
# gcomp = 1e-5
# dcomp = 50e-3

navg=10                         # number of averages to form measured spectra
fcent = 1.5E9
fdelta = 4E6
#fspanf = 100E3                 # measurement span for each frequency component of the fundamentals

ffa = fcent-fdelta/2
ffb= fcent+fdelta/2
fda = ffa-fdelta
fdb = ffb+fdelta
atten = 20.

pwrstart = -25.
pwrstop = -15.
delpwr=5.

sysTOI=50.
#pathname = "C:/Users/test/python/data/GaNpower_Sept26_2017"                                                              # setup Cascade
#wafername="QorvoGaNX5"
#devicename="D12"

pathname = "C:/Users/test/python/data/GaN_Jan25_2018"                                                              # setup Cascade

#ps.measure_ivtransferloop_controlledslew(backgated=False,Vgsslewrate=1.,Vds=Vdsbias,Vgs_start=-3,Vgs_stop=0,Vgs_step=0.1,gatecomp=0.5E-6,draincomp=0.02)

IP3tuned = IP3_Tuned(rm=rm, cascadefiles_port1=cas1, cascadefiles_port2=cas2, spectrum_analyser_input_attenuation=atten, number_of_averages=navg, powerlevel_start=pwrstart ,powerlevel_stop=pwrstop ,powerlevel_step=delpwr, center_frequency=fcent, frequency_spread=fdelta,spectrum_analyzer_cal_factor=sacalfactor, source_calibration_factor_lowerfreq=sourcecalfactorlowerfreq, source_calibration_factor_upperfreq=sourcecalfactorupperfreq, system_TOI=sysTOI)
reflections=read_reflection_coefficients(pathname+"/TOIreflections.csv")

#Vgsarray=np.arange(0.5,-3.1,-0.1)


Vgsarray=[-2.4]
for Vgsbias in Vgsarray:
	Id,Ig,drainstatus,gatestatus=ps.fetbiason_topgate(Vgs=Vgsbias, Vds=Vdsbias, gatecomp=0.5E-3, draincomp=0.1,timeiter=1.,maxchangeId=0.01,maxtime=40.)				# bias device again to update currents etc..
	print("Vds, Vgs, Id, Ig, drain status gate status", Vdsbias, Vgsbias, Id, Ig,drainstatus,gatestatus)
	IP3tuned.TOIsearch(initial_output_reflections=reflections, fractlinfitlower=0., fractlinearfitupper=1., plotgraphs=True,expected_gain=20.)
	ps.fetbiasoff()

	#TOIl,TOIh,DUTgain,pinDUT,pfund,pdl,pdh,noisefloor,ml,mh,poutm,bl,bh,r,reflectcoefactual= IP3tuned.measureTOI(output_reflection=reflections, fractlinfitlower=0., fractlinearfitupper=1., plotgraphs=True)
	#IP3tuned.writefile_TOI(pathname=pathname,wafername=cascade.wafername(),xloc=cascade.x(),yloc=cascade.y(),Id=Id,Vds=Vdsbias,Vgs=Vgsbias,Ig=Ig,devicename=cascade.devicename(),devicenamemodifier="_Vds"+formatnum(Vdsbias,precision=1)+"_Vgs"+formatnum(Vgsbias,precision=2))
	IP3tuned.writefile_TOI(pathname=pathname,wafername="Qorvo_GaN",xloc=0,yloc=0,Id=0,Vds=Vdsbias,Vgs=Vgsbias,Ig=0,devicename="GaNNX5")
print("done probing wafer")