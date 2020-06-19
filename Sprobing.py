# main wafer probing routine
import visa
from probing_utilities import *
from create_probeconstellations_devices.probe_constellations_map import *
rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from pna import Pna                                                                 # network analyzer
from cascade import CascadeProbeStation                                                    # Cascade wafer prober
#from old.plotSmeas import dataPlotter
from IVplot import *

pna = Pna(rm,16)                                                                    # setup network analyzer
iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
#sp = dataPlotter()


# transfer curves
Vds_bias = -1                                                                   # also used for S-parameter drain bias
Vgs_bias=np.arange(-3,-1,0.2)                                                   # Vgs array of gate biases for S-parameters
#Vgs_bias=np.arange(-2.,-11.,-1.)                                                   # Vgs array of gate biases for S-parameters
#Vgs_bias=[-0.4]
# common to both
gatecomp = 10E-5                                                                   # gate current compliance in A
draincomp = 0.05                                                                   # drain current compliance in A

#validation to see if device warrents further testing
goodId=0.1E-4                        # drain current must exceed this to qualify device for further testing
goodonoff=5.                       # acceptable on-off ratio for S-parameter testing
Vgs_validation = -0.4
Vds_validation = -1.
Vgs_pinchoffval=1.                  # used for On-Off ratio validation







wafername="QW2"
runnumber=1
maskname="v6_2finger_single"
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno
devicelisttotestfile=pathname+"/devicesRFtest.csv"


pathname = "C:/Users/test/python/data/"+wafername_runno
cascade = CascadeProbeStation(rm=rm)         # setup Cascade NO probeplan file here! This also moves
probc=ConstellationsdB(maskname=maskname,wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probelistfilename=devicelisttotestfile)

iv.fetbiasoff()

#pr = CascadeProbeStation(rm=rm,pathname=pathname,planname="Wf169meas11_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
#pr.move_plan_index()					# move to first site

for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
	devicename=device["name"]
	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
	print ("probing devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"])
	for Vgs in Vgs_bias:
	# probe S-parameters
		iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=Vds_bias, Vgs_start=-3.0, Vgs_stop=2.0, Vgs_step=0.1, gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransfer(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='Vds_'+formatnum(Vds_bias,precision=1,nonexponential=True)+'_Vgs_'+formatnum(Vgs,precision=1,nonexponential=True))
		Id,Ig,drainstatus,gatestatus=iv.fetbiason_topgate(Vgs, Vds_bias, gatecomp, draincomp,timeiter=10,maxchangeId=0.01,maxtime=40.)				# bias device
		print("Vgs,Vds,Id, Ig 1st",Vgs,Vds_bias,Id,Ig)
		pna.pna_getS(4)												# get the S-parameters

		pna.writefile_spar(measurement_type="All_RI",pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc=pr.x(),yloc=pr.y(),Vds=iv.Vds_bias,Vgs=iv.Vgs_bias,Id=Id,Ig=Ig,gatestatus=gatestatus,drainstatus=drainstatus,devicenamemodifier='Vds_'+formatnum(Vds_bias,                      precision=1,nonexponential=True)+'_Vgs_'+formatnum(Vgs,precision=1,nonexponential=True))

	iv.fetbiasoff()													# bias off
	pr.move_nextsite()
	#print ("after nextsite")#, cascade.get_probingstatus()
	#plt.clf()
pr.move_separate()
print("done probing wafer")