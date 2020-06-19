# main wafer probing routine
import visa
from probing_utilities import *
from create_probeconstellations_devices.probe_constellations_map import *
from calculated_parameters import *
from measure_noiseparameters_focus import *
from read_write_spar_noise import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from pna import Pna                                                                 # network analyzer
from cascade import CascadeProbeStation                                                    # Cascade wafer prober
#from old.plotSmeas import dataPlotter
from IVplot import *

pna = Pna(rm,4)                                                                    # setup network analyzer
iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
#sp = dataPlotter()


# transfer curves

Vgs_bias=[-2.5,-2.,-1.75,-1.5,-1.25,-1.,-0.75,-0.5]                                                   # Vgs array of gate biases for S-parameters
#Vgs_bias=np.arange(-2.,-11.,-1.)                                                   # Vgs array of gate biases for S-parameters
#Vgs_bias=[-0.4]
# common to both
gatecomp = 10E-3                                                                   # gate current compliance in A
draincomp = 0.05                                                                   # drain current compliance in A

#validation to see if device warrents further testing
goodId=0.1E-4                        # drain current must exceed this to qualify device for further testing
goodIg=50E-6
goodonoff=5.                       # acceptable on-off ratio for S-parameter testing
Vgs_validation = -1.
Vds_validation = -1.
#Vgs_pinchoffval=1.                  # used for On-Off ratio validation

wafername="QH28"
runnumber=4
maskname="v6_2finger_single"
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno
devicelisttotestfile=pathname+"/selecteddevicesnoise.csv"

cascade = CascadeProbeStation(rm=rm)         # setup Cascade NO probeplan file here! This also moves
probc=ConstellationsdB(maskname=maskname,wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probelistfilename=devicelisttotestfile)

##########################################################################################################################
Vds_bias=-1.2
iv.fetbiasoff()
####################################
# noise
tundir="C:/Users/test/focus_setups/noise"
inputcircuitfile=tundir+"/RF/noise_biasteeinputcouplerisolator_oct11_2019_SRI.s2p"
tunercal=tundir+"/tuner1389source_1.2-1.5GHz_calibration_Sept20_2019.txt"
systemnoiseparameters=tundir+"/RF/system_probe_Oct14_2019_noiseparameter.xls"
#probefile=tundir+"/RF/JC2G4_Oct9_2019trl_SRI.s2p"           # this is the probe on the left side
probefile=tundir+"/RF/JC2G4_May4_2018_SRI.s2p"           # this is the probe on the left side
cas2=[[probefile,'noflip']]
cas1=[[inputcircuitfile,'noflip']]          # tuner cascade instructions
#requested_reflections =[ [0.012,141.785], [0.957,-0.129], [0.954,10.670], [0.881,3.632], [0.715,9.545], [0.714,-5.997], [0.818,-9.665], [0.933,-10.274], [0.814,27.795], [0.852,16.652], [0.595,49.457], [0.429,18.770], [0.456,-33.064], [0.929,41.530], [0.617,25.780], [0.928,22.839], [0.706,16.529], [0.797,52.267], [0.677,37.618], [0.686,-24.737] ]
requested_reflections =[ [0.990,-0.124], [0.986,-6.030], [0.990,7.729], [0.788,-0.859], [0.856,6.339], [0.869,-8.134], [0.838,15.575], [0.834,-20.147], [0.599,0.718], [0.700,-14.972], [0.660,16.397], [0.854,-38.666], [0.827,41.572], [0.372,-1.818] ]
frequencies=[1200]        # selected frequencies MHz
NP=NoiseParameters(rm=rm,ENR=15.07,tunerIP=("192.168.1.31",23),navgNF=8,navgPNA=2,usePNA=True,tunercalfile=tunercal,cascadefiles_port1=cas1,cascadefiles_port2=cas2,reflectioncoefficients=requested_reflections,system_noiseparametersfile=systemnoiseparameters,measureDUToutputgamma=True)
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
	devicename=device["name"]
	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
	print ("probing devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"])
	# test to see if the device is any good before committing to a full measurement
	Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=Vgs_validation, Vds=Vds_validation, gatecomp=0.05, draincomp=0.05,maxtime=0.2,timeiter=0.2)
	print ("Id= "+str(Idval)+" Ig="+str(Igval)+" drain status "+str(Idcompstatval)+" gate status "+str(Igcompstatval))
	if ( (abs(Idval)>goodId ) and (abs(Igval)<goodIg ) and (Igcompstatval=="N") and (Idcompstatval=="N") ):
		devicegood = True
	else:
		devicegood = False
		print("Bad device")
	if devicegood:
		iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=Vds_bias, Vgs_start=-3.0, Vgs_stop=1.0, Vgs_step=0.1, gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=device["X"],yloc=device["Y"],devicenamemodifier='1300MHz_beforenoiseparVds'+formatnum(Vds_bias,precision=2,nonexponential=True))
		for Vgs in Vgs_bias:
			Id,Ig,drainstatus,gatestatus=iv.fetbiason_topgate(Vgs, Vds_bias, gatecomp, draincomp,timeiter=10,maxchangeId=0.01,maxtime=40.)				# bias device
			print("Vgs,Vds,Id, Ig 1st",Vgs,Vds_bias,Id,Ig)
			NP.measure_noiseparameters_highspeed(frequenciesMHz=frequencies)
			NP.writefile_noiseparameters(pathname=pathname,wafername=wafername_runno,devicename=devicename,Vds=Vds_bias,Vgs=Vgs,Id=Id,Ig=Ig,devicenamemodifier="_1200MHz_Vds="+formatnum(Vds_bias,precision=2,nonexponential=True)+"_Vgs="+formatnum(Vgs,precision=2,nonexponential=True))
			NP.writefile_noisefigure(pathname=pathname,wafername=wafername_runno,devicename=devicename,Vds=Vds_bias,Vgs=Vgs,Id=Id,Ig=Ig,devicenamemodifier="_1200MHz_Vds="+formatnum(Vds_bias,precision=2,nonexponential=True)+"_Vgs="+formatnum(Vgs,precision=2,nonexponential=True))
iv.fetbiasoff()													# bias off
# ##################################################################################################################################

cascade.move_separate()
cascade.unlockstage()
print("done probing wafer")