__author__ = 'PMarsh Carbonics'
import visa

from compression_focus_tuned_with_powermeter import PowerCompressionTunedFocus
from parameter_analyzer import *
from spectrum_analyzer import *
from read_reflection_parametervsreflection import *
from loadpull_system_calibration import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())
#from cascade import CascadeProbeStation
ps=ParameterAnalyzer(rm)

cas1=[[probefile,'flip']]
cas2=[[tuneroutputcable,'noflip']]


Vgsbias = -2
Vdsbias = 1.
gcomp = 1e-4
dcomp = 100e-3

navg=10                         # number of averages to form measured spectra
fcent = 1.5E9
fdelta = 10E6
#fspanf = 100E3                 # measurement span for each frequency component of the fundamentals

atten = 20.

pwrstart = -14.
pwrstop = -8
delpwr=1.

RFinputpower_gain=0.

pathname = "C:/Users/test/python/data/GaN_July2018"                                                              # setup Cascade
#pr = CascadeProbeStation(rm,pathname=pathname,planname="Wf167meas10_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
wafername="compression"
devicename="July31_2018_50ohm"

Cp=PowerCompressionTunedFocus(rm=rm, tunertype='load', frequency=1500., cascadefiles_port1=cas1, cascadefiles_port2=cas2, minpower=pwrstart, maxpower=pwrstop, comp_fillin_step=0.5, steppower=delpwr, source_calibration_factor=sourcecalfactor,estimated_gain=-10)

#ps.measure_ivtransferloop_controlledslew(backgated=False,Vgsslewrate=1.,Vds=Vdsbias,Vgs_start=-3,Vgs_stop=0,Vgs_step=0.1,gatecomp=0.5E-6,draincomp=0.02)
ps.measure_ivtransfer_topgate(inttime='2',Vds=Vdsbias, Vgs_start=-4, Vgs_stop=-2, Vgs_step=0.1, gatecomp=gcomp, draincomp=dcomp)

reflections=[[0,0]]
# ps.measure_ivtransfer_topgate(inttime='2',Vds=-1., Vgs_start=-2., Vgs_stop=1., Vgs_step=0.1, gatecomp=50E-6, draincomp=0.02)
# ps.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername,xloc_probe=0,yloc_probe=0,devicenamemodifier="")
Vgsarray=[-2.3]
for Vgsbias in Vgsarray:
	Id,Ig,drainstatus,gatestatus=ps.fetbiason_topgate(Vgs=Vgsbias, Vds=Vdsbias, gatecomp=gcomp, draincomp=dcomp,timeiter=10.,maxchangeId=0.01,maxtime=40.)				# bias device again to update currents etc..
	print("Vds, Vgs, Id, Ig, drain status gate status", Vdsbias, Vgsbias, Id, Ig,drainstatus,gatestatus)
	Cp.measurePcomp(output_reflection=[[0,0]],Vgs=0,Vds=0,draincomp=0.04,gatecomp=0.01)
	ps.fetbiasoff()
	#Cp.writefile_Pcompression_tuned(pathname=pathname,wafername=wafername,xloc=0,yloc=0,devicename=devicename,devicenamemodifier="_Vds"+formatnum(Vdsbias,precision=1)+"_Vgs"+formatnum(Vgsbias,precision=2))
	Cp.writefile_Pcompression_tuned(pathname=pathname,wafername=wafername,xloc=0,yloc=0,devicename=devicename,devicenamemodifier="_Vds"+formatnum(Vdsbias,precision=1)+"_Vgs"+formatnum(Vgsbias,precision=2))
	time.sleep(120)
print("done probing wafer")