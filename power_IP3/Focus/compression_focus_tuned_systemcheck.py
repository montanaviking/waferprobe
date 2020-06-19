__author__ = 'PMarsh Carbonics'
import visa

#from compression_focus_tuned_with_powermeter import *
from compression_focus_tuned_Vgssweep import *
from loadpull_system_calibration import *
rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

cas1=[[probefile,'flip']]
cas2=[[tuneroutputcable,'noflip']]
#perfect_thru="perfectthru_SRI.s2p"

Vgsbias = -1.5
Vdsbias = -1
gcomp = 1e-5
dcomp = 50e-3

navg=10                         # number of averages to form measured spectra
fcent = 1500                    # frequency in MHz
fdelta = 100                    # frequency in MHz
#fspanf = 100E3                 # measurement span for each frequency component of the fundamentals

ffa = fcent-fdelta/2
ffb= fcent+fdelta/2
fda = ffa-fdelta
fdb = ffb+fdelta
atten = 10.
#pwrstart = -25.
#pwrstop = -8.
pwrstart = -16.
pwrstop = 5.
delpwr=2.


pathname = "C:/Users/test/python/data/focustest"
#SDUT=pathname+"/mismatch_Mar13_2017_SRI.s2p"
#SDUT=pathname+"/waferthru_July24_2018_SRI.s2p"
#Cp=PowerCompressionTunedFocus(rm=rm, tunertype='load', frequency=fcent, cascadefiles_port1=cas1, cascadefiles_port2=cas2, minpower=pwrstart, maxpower=pwrstop, comp_fillin_step=0.5, steppower=delpwr, source_calibration_factor=sourcecalfactor,estimated_gain=-10,synthesizerpowersetmaximum=0)
Cp=Pcomp_Vgssweep(rm=rm,powerlevel_minimum=-14,powerlevel_maximum=-8,powerlevel_step=1,frequency=1.5E9,Vgsperiod=0.001,Vgsmin=-2.5,Vgsmax=0)
# old version Cp=PowerCompressionTunedFocus(rm=rm, tunertype='load', cascadefiles_port1=cas1, cascadefiles_port2=cas2, powerlevellinear_min=pwrstart, powerlevellinear_max=pwrstop, maxpower=9., comp_fillin_step=1, powerlevel_step=delpwr, source_calibration_factor=sourcecalfactor)
#reflections=[[0,0],[.4,0.],[.4,90.],[.5,0.],[.5,90.],[.6,0.],[.6,90.],[.6,180.],[.7,0.],[.7,90.],[.8,0],[.8,180]]
reflections=[[0.,-0]]
#old version Cp.gain_vs_outputreflection(output_reflection=reflections,RFinputpower=0,frequency=fcent,DUTSparfile=SDUT)
#Cp.gain_vs_outputreflection(output_reflection=reflections,RFinputpower=0.)
#Cp.writefile_Pgain(pathname=pathname,wafername="",xloc=0,yloc=0,Id=0,Vds=0,Vgs=0,Ig=0,devicename="system")
# old Cp.measurePcomp(output_reflection=reflections,frequency=fcent,Vgs=0,Vds=0,draincomp=0.04,gatecomp=0.01,maxiterations=20)
#Cp.measure_gainonly(Pin=-10,output_reflection=[0,0],Vds=0)
Cp.measurePcomp(output_reflection=[0,0])
#Cp.writefile_Pcompression_tuned(pathname=pathname,wafername="",xloc=0,yloc=0,devicename="systemfull")

