__author__ = 'PMarsh Carbonics'
import visa
import time
from read_reflection_parametervsreflection import *
from IP3_focus_tuned import IP3_Tuned
from loadpull_system_calibration import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

cas2=[[tuneroutputcable,'noflip']]
#cas1=[[inputcable,'noflip']]
cas1=[[probefile,'flip']]
#perfect_thru="perfectthru_SRI.s2p"


navg=10                         # number of averages to form measured spectra
fcent = 1.5E9
fdelta = 4E6

atten = 10.
#pwrstart = -25.
#pwrstop = -8.
pwrstart = -15.
pwrstop = -0.
delpwr=5.
sysTOI=85.

pathname = "C:/Users/test/power_IP3"
#reflections=read_reflection_coefficients(pathname+"/reflection_coefficients.csv")
IP3tuned = IP3_Tuned(rm=rm, cascadefiles_port1=cas1, cascadefiles_port2=cas2, spectrum_analyser_input_attenuation=atten, number_of_averages=navg,
    powerlevel_start=pwrstart ,powerlevel_stop=pwrstop ,powerlevel_step=delpwr, center_frequency=fcent, frequency_spread=fdelta,spectrum_analyzer_cal_factor=sacalfactor,
    source_calibration_factor_lowerfreq=sourcecalfactorlowerfreq, source_calibration_factor_upperfreq=sourcecalfactorupperfreq, system_TOI=sysTOI)
reflections=[[0.,0.]]
IP3tuned.measureTOI(output_reflection=reflections, fractlinfitlower=0., fractlinearfitupper=1., plotgraphs=True)
IP3tuned.writefile_TOI(pathname=pathname,wafername="",xloc=0,yloc=0,Id=0,Vds=0,Vgs=0,Ig=0,devicename="system_July18_2018")
#time.sleep(60)
##IP3m.writefile_TOI(pathname="C:/Users/test/python/waferprobe/data/Wf166meas3",wafername="system",xloc=27300,yloc=21650,Id=0,Vds=0,Vgs=0,Ig=0,devicename="system",)


