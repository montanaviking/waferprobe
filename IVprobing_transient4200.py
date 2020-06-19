# main wafer probing routine
import visa

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from cascade import CascadeProbeStation                                                    # Cascade wafer prober
#from plot import dataPlotter

#pna = Pna(rm,16)                                                                    # setup network analyzer
iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
#sp = dataPlotter()

# set up of IV and bias voltages
# family of curves
Vds_focstart = 0.
Vds_focstop = -2.
Vds_focnpts = 51
Vgs_focstart = 1.0
Vgs_focstop = -3.
Vgs_focnpts =17
# transfer curves
Vds_bias = -1.5                                                                      # also used for S-parameter drain bias
Vgs_transstart = -3.
Vgs_transstop = -0.5
Vgs_transstep = 0.1
# common to both
gatecomp = 5E-6                                                                   # gate current compliance in A
draincomp = 0.02                                                                 # drain current compliance in A

#validation to see if device warrents further testing
goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
Vgs_validation = -0.5
Vds_validation = -1


#pathnameIV = "C:/Users/test/python/waferprobe/data"+sub("DC")
#pathnameRF = "C:/Users/test/python/waferprobe/data"+sub("SPAR")
pathname = "C:/Users/test/python/data/Wf167meas3"

wafername="Wf167meas3"
#devicename="C6_R5_DV6_D23_PLC_0.01"
# devicename="Tq_40_Vq_70__C7_R7_DV1_D32"
# devicenames=[]
# devicenames.append("LP")
# devicenames.append("C7_R7_DV1_D32")
#devicenames.append("test")

# test to see if the device is any good before committing to a full measurement
# 	devicegood = 'yes'
#else: devicegood = 'no'

#iv.measure_ivtransferloop_dual_controlledslew_backgated(Vgsslewrate=10,Vds=-1.,draincomp=draincomp,gatecomp=gatecomp,Vgs_start=70,Vgs_stop=-70,Vgs_step=-2)
#iv.writefile_ivtransferloop_dual(pathname=pathname,wafername=wafername,devicenames=devicenames,xloc_probe=xp,yloc_probe=yp,devicenamemodifier="slew1V_sec")

pr = CascadeProbeStation(rm=rm,pathname=pathname,planname="Wf167meas3_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
pr.move_plan_index()					# move to first site

while pr.get_probingstatus()=="probing wafer":
	# iv.measure_ivtransferloop_controlledslew(backgated=False,Vgsslewrate=1.,Vds=Vds_bias, draincomp=draincomp, Vgs_start=Vgs_transstart, Vgs_stop=Vgs_transstop, Vgs_step=Vgs_transstep, gatecomp=gatecomp)
	# iv.writefile_ivtransferloop(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername())

	iv.measure_hysteresistimedomain(backgated=False,Vds=Vds_bias,Vgsquiescent=0.,timestep=.01,timequiescent=40.,timeend=40.,Vgs_start=-3.,Vgs_step=0.2,Vgs_stop=-.2,draincomp=draincomp,gatecomp=gatecomp)
	iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername())
	iv.writefile_pulsedtransfertimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),timepointsperdecade=10)

	pr.move_nextsite()
pr.move_separate()
print("done probing wafer")
