__author__ = 'PMarsh Carbonics'
import visa

from compression_focus_tuned_with_powermeter import PowerCompressionTunedFocus
from parameter_analyzer import *
from spectrum_analyzer import *
from loadpull_system_calibration import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())
from cascade import CascadeProbeStation
ps=ParameterAnalyzer(rm)

cas1=[[probefile,'flip']]
cas2=None

#Vgsbias = -1.
Vdsbias = -1.5
gcomp = 1e-5
dcomp = 50e-3

navg=10                         # number of averages to form measured spectra
fcent = 1500                    # center frequency in MHz
#fdelta = 2                   # frequency difference between two-tones in MHz
#fspanf = 100E3                 # measurement span for each frequency component of the fundamentals

#atten = 20.

pwrstart = -12.
pwrstop = -8.
delpwr=1.

pathname = "C:/Users/test/python/data/Wf169meas10"
pr = CascadeProbeStation(rm=rm,pathname=pathname,planname="Wf169meas10_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
pr.move_plan_index()					# move to first site
#IP3 = IP3_Tuned(rm=rm, tunerfile=tunerfile, cascadefiles_port1=cas1, cascadefiles_port2=cas2, spectrum_analyser_input_attenuation=atten, number_of_averages=navg, powerlevel_start=pwrstart ,powerlevel_stop=pwrstop ,powerlevel_step=delpwr, center_frequency=fcent, frequency_spread=fdelta,spectrum_analyzer_cal_factor=sacalfactor, source_calibration_factor=sourcecalfactor,system_TOI=sysTOI)
#Cp=PowerCompressionTunedMaury(rm=rm, tunerfile=tunerfile, cascadefiles_port1=cas1, cascadefiles_port2=cas2, powerlevellinear_min=pwrstart, powerlevellinear_max=pwrstop, maxpower=9., comp_fillin_step=1, powerlevel_step=delpwr, source_calibration_factor=sourcecalfactor)
#Cp=PowerCompressionTunedFocus(rm=rm, tunertype='load', cascadefiles_port1=cas1, cascadefiles_port2=cas2, powerlevellinear_min=pwrstart, powerlevellinear_max=pwrstop, maxpower=3., comp_fillin_step=1, powerlevel_step=delpwr, source_calibration_factor=sourcecalfactor)
Cp=PowerCompressionTunedFocus(rm=rm, tunertype='load', cascadefiles_port1=cas1, cascadefiles_port2=cas2, powerlevellinear_min=pwrstart, powerlevellinear_max=pwrstop, maxpower=9., comp_fillin_step=1, powerlevel_step=delpwr, source_calibration_factor=source_calibration_factor, input_sensor_calfactor=input_sensor_calfactor)
#reflections=[ [0.770,5.618], [0.710,10.443], [0.536,5.990], [0.620,23.772], [0.808,28.112], [0.878,18.196], [0.752,16.288], [0.884,7.099], [0.878,-1.093], [0.776,-0.521], [0.669,0.641], [0.616,-12.482], [0.420,32.513], [0.694,35.198], [0.430,-20.750], [0.638,-25.376], [0.706,-5.301], [0.866,-7.865], [0.821,-19.113], [0.772,-11.751], [0.497,-40.422], [0.233,4.222], [0.547,46.264], [0.824,-30.166], [0.296,-36.634], [0.7536051384879188,-1.58] ]                # reflection coefficients presented to DUT output during compression tests
reflections=[[0.8,15]]
while pr.get_probingstatus()=="probing wafer":
	print("device ",pr.devicename())
	#Vgsarray=np.arange(0.5,-3.1,-0.1)
	#ps.measure_ivtransfer_topgate(inttime='2',delaytime=0.05,Vds=Vdsbias, Vgs_start=-2., Vgs_stop=.5, Vgs_step=0.2, gatecomp=50E-6, draincomp=0.02)
	#ps.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier="")
	Vgsarray=[-1]
	for Vgsbias in Vgsarray:
		Id,Ig,drainstatus,gatestatus=ps.fetbiason_topgate(Vgs=Vgsbias, Vds=Vdsbias, gatecomp=gcomp, draincomp=dcomp,timeiter=10.,maxchangeId=0.01,maxtime=40.)				# bias device again to update currents etc..
		print("Vds, Vgs, Id, Ig, drain status gate status", Vdsbias, Vgsbias, Id, Ig,drainstatus,gatestatus)
		#TOIl,TOIh,DUTgain,pinDUT,pfund,pdl,pdh,noisefloor,ml,mh,bl,bh,bf,r=
		#IP3.measureTOI(output_reflection=reflections, fractlinfitlower=0., fractlinearfitupper=1., plotgraphs=True)
		#Cp.gain_vs_outputreflection(output_reflection=reflections,RFinputpower=8,frequency=fcent)
		#Cp.writefile_Pgain(pathname=pathname,wafername=cascade.wafername(),xloc=cascade.x(),yloc=cascade.y(),devicename=cascade.devicename(),Id=0,Vds=Vdsbias,Vgs=Vgsbias,devicenamemodifier="_Vds"+formatnum(Vdsbias,precision=1)+"_Vgs"+formatnum(Vgsbias,precision=2))
		#IP3.writefile_TOI(pathname=pathname,wafername=cascade.wafername(),xloc=cascade.x(),yloc=cascade.y(),Id=Id,Vds=Vdsbias,Vgs=Vgsbias,Ig=Ig,devicename=cascade.devicename(),devicenamemodifier="_Vds"+formatnum(Vdsbias,precision=1)+"_Vgs"+formatnum(Vgsbias,precision=2)
		Cp.measurePcomp(ps=ps,output_reflection=reflections,frequency=fcent,Vgs=Vgsbias,Vds=Vdsbias,draincomp=0.04,gatecomp=50E-6)
		Cp.writefile_Pcompression_tuned(pathname=pathname,wafername=pr.wafername(),xloc=pr.x(),yloc=pr.y(),devicename=pr.devicename(),devicenamemodifier="_Vds"+formatnum(Vdsbias,precision=1)+"_Vgs"+formatnum(Vgsbias,precision=2))
		ps.fetbiasoff()
	pr.move_nextsite()
pr.move_separate()
print("done probing wafer")