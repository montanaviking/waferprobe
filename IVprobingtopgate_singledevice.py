# main wafer probing routine
import visa
import time
from probing_utilities import *
from create_probeconstellations_devices.probe_constellations_map import *
from calculated_parameters import *
from pulsegenerator import *
#import mwavepy as mv

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from cascade import CascadeProbeStation                                                    # Cascade wafer prober
from IP3_Vgssweep import *

#pna = Pna(rm,16)                                                                    # setup network analyzer
#iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
#pulse=PulseGeneratorDG1022(rm)

# Vds_focstart = 0.
# Vds_focstop = -2.
# Vds_focnpts =21
Pin=-14
firsttime=True
Vds=-1
# common to both
gatecomp = 50E-6                                                                   # gate current compliance in A
draincomp = 0.01                                                                   # drain current compliance in A
#Vgs_bias = -10.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
goodIg=5E-5                          # gate current must be LESS than this amount to qualify device for further testing
# Vgs_validation = -2.0
# Vds_validation = -1.0
wafername="QH4"
runnumber=10
maskname="v6_2finger_single_singlereticl"
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno

cascade = CascadeProbeStation(rm=rm)         # setup Cascade NO probeplan file here! This also moves
probc=ConstellationsdB(maskname=maskname,wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probe_device_list=['C5_R5_T50_D32','C5_R5_B50_D13','C5_R5_B50_D33','C5_R5_B50_D23','C5_R5_B50_D12'])
IP3=IP3_Vgssweep(rm=rm, powerlevel_minimum=Pin, powerlevel_maximum=Pin, powerlevel_step=0, center_frequency=1.5E9, frequency_spread=4E6, Vgsmin=-2.5, Vgsmax=0, Vgsperiod=0.001)
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
	devicename=device["name"]
	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
	print ("probing devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"])
	#iv.fetbiasoff()
	# iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=-1., draincomp=draincomp, Vgs_start=-3, Vgs_stop=2, Vgs_step=0.1, gatecomp=gatecomp)
	# iv.writefile_ivtransfer(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=device["X"],yloc=device["Y"],devicenamemodifier='')
	IP3.measureTOI_gain(Pin=Pin,output_reflection=[0.45,20],Vds=Vds,noavg_dist=256,setup=firsttime,quickmeasurement=True)
	IP3.writefile_TOI_Vgssweep(pathname=pathname,wafername=wafername_runno,devicename=devicename,xloc=device['X'],yloc=device['Y'],devicenamemodifier='mag0.4ang20_Pin_'+formatnum(Pin,precision=2,nonexponential=True))
	#iv.fetbiason_topgate(Vgs=-2.5, Vds=-1., maxchangeId=.9,maxtime=10,gatecomp=gatecomp, draincomp=draincomp)
	#pulse.set_pulsesetup_continuous(pulsewidth=5E-6,period=50E-6,voltagelow=-1,voltagehigh=0)
	#pulse.ramppulses(period=1E-3,voltagequescent=0.,voltagemax=-1,pulsewidth=5E-6,dutycyclefraction=0.1)
	#pulse.pulsetrainon()
	#time.sleep(300)

#
#iv.measure_drainsweep_4device_backgate(inttime="2",sweepdelay=0.1,Vds_start=1, Vds_stop=-1, Vds_npts=21, draincomp=0.1)
# iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=-1., draincomp=draincomp, Vgs_start=-2, Vgs_stop=1.6, Vgs_step=0.1, gatecomp=gatecomp)
#iv.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername,xloc_probe=0,yloc_probe=0,devicenamemodifier='Vds_-1')
# # transfer curve loop controlled sweep rate

# # family of curves
# iv.measure_ivfoc_topgate(inttime='2', delaytime=0.2, Vds_start=5, Vds_stop=-5, draincomp=draincomp, Vds_npts=41, Vgs_start=0, Vgs_stop=0, gatecomp=gatecomp, Vgs_npts=1)
# iv.writefile_ivfoc(pathname,devicename=devicename,wafername=wafername,xloc=0,yloc=0,devicenamemodifier='')
#
# iv.measure_ivfoc_dual_backgate(inttime='2', sweepdelay=0.05, Vds_start=5, Vds_stop=-5, draincomp=draincomp, Vds_npts=Vds_focnpts, Vgs_start=0, Vgs_stop=0, gatecomp=gatecomp, Vgs_npts=1)
# iv.writefile_ivfoc_dual(pathname=pathname,devicenames=["leftprobe","rightprobe"],wafername=wafername,xloc_probe=0,yloc_probe=0)
print("done probing wafer")
cascade.move_separate()
cascade.unlockstage()
