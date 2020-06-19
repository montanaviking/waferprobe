__author__ = 'PMarsh Carbonics'
import visa

from compression_focus_tuned_with_powermeter import PowerCompressionTunedFocus
from loadpull_system_calibration import *
rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

cas1=[[probefile,'flip']]
#cas2=[[tuneroutputcable,'noflip']]
cas2=None
perfect_thru="perfectthru_SRI.s2p"

Vgsbias = -2.
Vdsbias = -2.5
gcomp = 1e-5
dcomp = 50e-3

navg=10                         # number of averages to form measured spectra
fcent = 1500                    # frequency in MHz
fdelta = 4                    # frequency in MHz
#fspanf = 100E3                 # measurement span for each frequency component of the fundamentals

ffa = fcent-fdelta/2
ffb= fcent+fdelta/2
fda = ffa-fdelta
fdb = ffb+fdelta
atten = 20.
#pwrstart = -25.
#pwrstop = -8.
pwrstart = -10.
pwrstop = -5.
delpwr=2.


pathname = "C:/Users/test/python/data/focustest"
#SDUT=pathname+"/mismatch_Mar13_2017_SRI.s2p"
#SDUT=pathname+"/coaxthru_Mar22_2017_SRI.s2p"
Cp=PowerCompressionTunedFocus(rm=rm, tunertype='load', cascadefiles_port1=cas1, cascadefiles_port2=cas2, powerlevellinear_min=pwrstart, powerlevellinear_max=pwrstop, maxpower=9., comp_fillin_step=1, powerlevel_step=delpwr, source_calibration_factor=source_calibration_factor, input_sensor_calfactor=input_sensor_calfactor)
#reflections=[[0,0],[.4,0.],[.4,90.],[.5,0.],[.5,90.],[.6,0.],[.6,90.],[.6,180.],[.7,0.],[.7,90.],[.8,0],[.8,180],[.9,5]]
reflections=[[0,0]]
# Cp.gain_vs_outputreflection(output_reflection=reflections,RFinputpower=5,frequency=fcent)
# Cp.writefile_Pgain(pathname=pathname,wafername="",xloc=0,yloc=0,Id=0,Vds=0,Vgs=0,Ig=0,devicename="system")
Cp.measurePcomp(output_reflection=reflections,frequency=fcent,Vgs=0,Vds=0,draincomp=0.04,gatecomp=0.01,maxiterations=20)
# Cp.measurePcomp(output_reflection=reflections,frequency=fcent,maxiterations=20)
Cp.writefile_Pcompression_tuned(pathname=pathname,wafername="",xloc=0,yloc=0,devicename="systemIP3_Jan23_2018")

