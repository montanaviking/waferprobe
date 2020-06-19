# Vgs tuned swept measurement on a single device
from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from IP3_Vgssweep import *
from compression_focus_tuned_Vgssweep import *
from loadpull_system_calibration import *
from cascade import CascadeProbeStation
from create_probeconstellations_devices.probe_constellations_map import *

rm=visa.ResourceManager()
wafername="GaN"
pathname = "C:/Users/test/python/data/GaN_April5_2019"
devicename="GaNgain"


gatecomp=100E-6
draincomp=0.45

Pin=-18
frequency=1.5E9
##########################################################################################################################
Vds=2.0
firsttime=True
IP3=IP3_Vgssweep(rm=rm, powerlevel_minimum=Pin, powerlevel_maximum=Pin, powerlevel_step=0, center_frequency=1.5E9, frequency_spread=4E6, Vgsmin=-3., Vgsmax=0, Vgsperiod=0.001)

# iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=Vds, Vgs_start=-3.0, Vgs_stop=1.0, Vgs_step=0.1, gatecomp=gatecomp,draincomp=draincomp)
# iv.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=device["X"],yloc=device["Y"],devicenamemodifier='before_mag0.15ang30_Vds'+formatnum(Vds,precision=1,nonexponential=True))

IP3.TOIsearch(Vds=Vds,draincomp=draincomp,Pin=Pin,initial_output_reflections=[ [0.364,58.846], [0.530,34.794], [0.195,19.620], [0.440,8.563] ],noavgdist=256)
# if IP3.drainstatus!='N': continue
IP3.writefile_Vgssweep_TOIsearch(pathname=pathname,wafername=wafername,devicename=devicename,xloc=0,yloc=0,devicenamemodifier='1mS_Pin_'+formatnum(Pin,precision=2,nonexponential=True)+' Vds_'+formatnum(Vds,precision=2,nonexponential=True)+'_')
	#
#IP3.measureTOI_gain(Pin=Pin,output_reflection=[0.2,20],Vds=Vds,noavg_dist=256,setup=firsttime,quickmeasurement=True)
#IP3.writefile_TOI_Vgssweep(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=device['X'],yloc=device['Y'],devicenamemodifier='gamma_0.2_Pin_'+formatnum(Pin,precision=2,nonexponential=True)+' Vds_'+formatnum(Vds,precision=2,nonexponential=True))

# IP3.measure_gainonly(Vds=Vds,Pin=Pin,output_reflection=[0.95,180],draincomp=.45)
# IP3.writefile_gainonly_Vgssweep(pathname=pathname,wafername=wafername,devicename=devicename,xloc=0,yloc=0,devicenamemodifier='RFshortlowonoffratio_1mS_Pin_'+formatnum(Pin,precision=2,nonexponential=True)+' Vds_'+formatnum(Vds,precision=2,nonexponential=True)+'_')

#frequency=Comp.measurePcomp(output_reflection=[0.15,30],powerlevel_maximum=2,powerlevel_minimum=-16,powerlevel_step=2,Vds=Vds,frequency=frequency)
#Comp.writefile_Pcompression_tuned_Vgssweep(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=device['X'],yloc=device['Y'],devicenamemodifier='Vds_'+formatnum(Vds,precision=2,nonexponential=True))
# else:
# 	print ("bad device ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"])
# 	print("Idval =",Idval," Idcompstat ",Idcompstatval," Igcompstat ",Igcompstatval, " onoff ratio ",abs(Idval/Idvaloff))
#Comp.alloff()
IP3.alloff()

print("done probing wafer")