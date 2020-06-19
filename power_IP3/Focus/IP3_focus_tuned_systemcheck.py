__author__ = 'PMarsh Carbonics'
import visa
from read_reflection_parametervsreflection import *
#from IP3_focus_tuned import IP3_Tuned
from loadpull_system_calibration import *
from IP3_Vgssweep import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

cas2=[[tuneroutputcable,'noflip']]
cas1=[[probefile,'flip']]
#perfect_thru="perfectthru_SRI.s2p"


navg=10                         # number of averages to form measured spectra
fcent = 1.5E9
fdelta = 4E6
#fspanf = 100E3                 # measurement span for each frequency component of the fundamentals

# ffa = fcent-fdelta/2
# ffb= fcent+fdelta/2
# fda = ffa-fdelta
# fdb = ffb+fdelta
atten = 10.
# #pwrstart = -25.
# #pwrstop = -8.
# pwrstart = -5.
# pwrstop = -15.
delpwr=5.
sysTOI=85.
Pin=-15
Vds=-1.2
dcomp=0.1
gcomp=0.0001

pathname = "C:/Users/test/power_IP3"
#reflections=read_reflection_coefficients(pathname+"/reflection_coefficients.csv")
# IP3tuned = IP3_Tuned(rm=rm, cascadefiles_port1=cas1, cascadefiles_port2=cas2, spectrum_analyzer_input_attenuation=atten, number_of_averages=navg, powerlevel_start=pwrstart ,powerlevel_stop=pwrstop ,powerlevel_step=delpwr, center_frequency=fcent, frequency_spread=fdelta,spectrum_analyzer_cal_factor=sacalfactor, source_calibration_factor=sourcecalfactor, system_TOI=sysTOI,powermetercalfactor=97.6)
# reflections=[[0.0,0.]]
# IP3tuned.measureTOI(output_reflection=reflections,plotgraphs=True)
#IP3tuned.writefile_TOI(pathname=pathname,wafername="",xloc=0,yloc=0,Id=0,Vds=0,Vgs=0,Ig=0,devicename="system")
##IP3m.writefile_TOI(pathname="C:/Users/test/python/waferprobe/data/Wf166meas3",wafername="system",xloc=27300,yloc=21650,Id=0,Vds=0,Vgs=0,Ig=0,devicename="system",)

IP3=IP3_Vgssweep(rm=rm, powerlevel_minimum=Pin, powerlevel_maximum=Pin, powerlevel_step=0, center_frequency=fcent, frequency_spread=fdelta, Vgsmin=-2.5, Vgsmax=0, Vgsperiod=0.001,syscheckonly=False,holdtime=20.)
IP3.measure_gainonly(output_reflection=[0.,0],Pin=Pin,draincomp=dcomp,Vds=Vds)
#IP3.writefile_gainonly_Vgssweep(pathname="C:/Users/test/python/data/TOI_swept_Vgs/",wafername='systest',devicename='systest',xloc=0,yloc=0,devicenamemodifier='10mS_gamma_0_ang0_Pin_'+formatnum(Pin,precision=2,nonexponential=True))
#IP3.measureTOI_gain(output_reflection=[0.,0],Pin=Pin,draincomp=dcomp,Vds=Vds,noavg_dist=256)
#IP3.writefile_TOI_Vgssweep(pathname="C:/Users/test/python/data/TOI_swept_Vgs/",wafername='systest',devicename='Oct24_2019',xloc=0,yloc=0,devicenamemodifier='10mS_gamma_0_ang0_Pin_'+formatnum(Pin,precision=2,nonexponential=True))
IP3.writefile_gainonly_Vgssweep(pathname="C:/Users/test/python/data/TOI_swept_Vgs/",wafername='systest',devicename='gainonlyOct24_2019',xloc=0,yloc=0,devicenamemodifier='10mS_gamma_0_ang0_Pin_'+formatnum(Pin,precision=2,nonexponential=True))