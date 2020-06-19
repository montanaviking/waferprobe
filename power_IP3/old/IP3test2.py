__author__ = 'PMarsh Carbonics'
import visa
import time
#import skrf as rf
from parameter_analyzer import *
from spectrum_analyzer import *
from rf_sythesizer import *
from IVplot import plotTOI
from IP3 import IP3

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())
from cascade import CascadeProbeStation
ps=ParameterAnalyzer(rm)

Vgsbias = -2.
Vdsbias = -2.
gcomp = 1e-5
dcomp = 50e-3



navg=10                         # number of averages to form measured spectra
fcent = 1.5E9
fdelta = 100E6
#fspanf = 100E3                 # measurement span for each frequency component of the fundamentals

ffa = fcent-fdelta/2
ffb= fcent+fdelta/2
fda = ffa-fdelta
fdb = ffb+fdelta
atten = 20.
#pwrstart = -25.
#pwrstop = -8.
pwrstart = -15.
pwrstop = -5.
delpwr=5.
sourcecalfactor=-8.22   # sourcecalfactor is the dB difference between the power meter measured power and that set on the rf synthesizer (A) = dB power meter - dB synthesizer setting (usually negative dB)
sacalfactor = 2.62       # sacalfactor is dB power meter - dB spectrum analyzer display - loss, according to the spectrum analyzer display from the DUT output to the spectrum analyzer - a positive number
#sourcecalfactor=-8.27   # sourcecalfactor is the dB difference between the power meter measured power and that set on the rf synthesizers (A) = dB power meter - dB synthesizer setting (usually negative dB)
#sacalfactor = 3.3       # sacalfactor is dB power meter - dB spectrum analyzer display
sysTOI=45.
#fractlinfit=0.6


Vgsarray=np.arange(0.5,-3.25,-0.25)
pathname = "C:/Users/test/python/data/Wf169meas2"
pr = CascadeProbeStation(rm=rm,pathname=pathname,planname="Wf169meas2_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
pr.move_plan_index()					# move to first site

while pr.get_probingstatus()=="probing wafer":

	IP3m = IP3(rm=rm,spectrum_analyser_input_attenuation=atten,number_of_averages=navg,powerlevel_start=pwrstart,powerlevel_stop=pwrstop,powerlevel_step=delpwr,center_frequency=fcent,frequency_spread=fdelta,spectrum_analyzer_cal_factor=sacalfactor,source_calibration_factor=sourcecalfactor,system_TOI=sysTOI)

	Vgsarray=np.arange(0.5,-3.25,-0.1)
	for Vgsbias in Vgsarray:
		Id,Ig,drainstatus,gatestatus=ps.fetbiason_topgate(Vgsbias, Vdsbias, gcomp, dcomp,maxchangeId=0.05)				# bias device again to update currents etc..
		time.sleep(10.)
		print("Vds, Vgs, Id, Ig, drain status gate status", Vdsbias, Vgsbias, Id, Ig,drainstatus,gatestatus)
		TOIl,TOIh,DUTgain,pinDUT,pfund,pdl,pdh,noisefloor,ml,mh,bl,bh,bf,r=IP3m.measureTOI(fractlinfitlower=0.,fractlinearfitupper=1.0)
		ps.fetbiasoff()
		IP3m.writefile_TOI(pathname=pathname,wafername=pr.wafername(),xloc=pr.x(),yloc=pr.y(),Id=Id,Vds=Vdsbias,Vgs=Vgsbias,Ig=Ig,devicename=pr.devicename(),devicenamemodifier="_Vds"+formatnum(Vdsbias,precision=1)+"_Vgs"+formatnum(Vgsbias,precision=2))
		##"GaNHEMT2Vgs_-2V"
		##IP3m.writefile_TOI(pathname="C:/Users/test/python/waferprobe/data/Wf166meas3",wafername="system",xloc=27300,yloc=21650,Id=0,Vds=0,Vgs=0,Ig=0,devicename="system",)
		print ("output lower TOI =",TOIl)
		print ("output upper TOI =",TOIh)
		print ("output noise floor =",noisefloor)
		print("plotting")
		plotTOI(pfund_in=IP3m.pinDUT,pfund_out=IP3m.TOIptt, ptoiL=IP3m.TOIpdl, ptoiH=IP3m.TOIpdh, noisefloor=IP3m.noisefloor, gain=IP3m.DUTgain, ml=IP3m.TOIml, bl=IP3m.TOIbl, mh=IP3m.TOImh, bh=IP3m.TOIbh, mpout=IP3m.poutm, plotfundmax=-IP3m.DUTgain+IP3m.TOIh + 1., plotfundmin=-IP3m.DUTgain+IP3m.TOIh - ((IP3m.TOIh-IP3m.noisefloor)/3.)-1.)
	pr.move_nextsite()
pr.move_separate()
print("done probing wafer")