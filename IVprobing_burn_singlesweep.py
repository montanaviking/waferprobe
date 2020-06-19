# main wafer probing routine
# Measure single device
import visa

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from cascade import CascadeProbeStation                                                    # Cascade wafer prober
#from old.plotSmeas import dataPlotter
from IVplot import *

#pna = Pna(rm,16)                                                                    # setup network analyzer
iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
#sp = dataPlotter()

# set up of IV and bias voltages
# family of curves
# Vds_focstart = 1.0
# Vds_focstop = -1.0
# Vds_focnpts = 21
# Vgs_focstart = 4.0
# Vgs_focstop = -12.0
# Vgs_focnpts =9
# transfer curves
Vds_bias = -1.0                                                                     # also used for S-parameter drain bias
Vgs_transstart = -5.
Vgs_transstop = 2.
Vgs_transstep = -0.2
# Sparameters only
#Vgs_bias = -1.                                                                      # gate bias for S-parameters
# common to both
gatecomp = 5E-7                                                                   # gate current compliance in A
draincomp = 0.1                                                                   # drain current compliance in A
#Vgs_bias = -10.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
goodIg=100.E-9                          # gate current must be LESS than this amount to qualify device for further testing
Vgs_validation = -4.
Vds_validation = -1.

deltaVdsburn=-0.1
Vdsburnmin=-1
Vdsburnmax=-7.0
Vgsburn=2.
Vdsburnarray=np.arange(Vdsburnmin,Vdsburnmax+deltaVdsburn,deltaVdsburn)

pathname = "C:/Users/test/python/data/Wf170meas4"

pr = CascadeProbeStation(rm,pathname,"Wf170meas4_plan","correction off")                                                               # setup Cascade

pr.move_plan_index()					# move to first site

while pr.get_probingstatus()=='probing wafer':
	pr.move_plan_index()					# mechanically move to site specified by the software
	print ("probing device ", pr.wafername()+"_"+pr.devicename(),"xpos = ",pr.x(),"ypos =",pr.y())
	# run through tests
	firstloop=True
	for Vdsburn in Vdsburnarray:
		# stress to attempt to burn out metallic nanotubes
		Idburn,Igatburn,Vdsburn,Vgsburn,drainstatusburn,gatestatusburn = iv.measure_burnonesweepVds(Vgs=Vgsburn,gatecomp=gatecomp, draincomp=draincomp, Vds_start=0.,Vds_stop=Vdsburn,Vds_step=deltaVdsburn)               # burn stress
		time.sleep(5)                       # cool time

		# On-Off ratio
		# Idmin,IgatIdmin,Idcompstatval,Igcompstatval = iv.fetbiason_backgate(Vgs=Vgsburn, Vds=-1, gatecomp=gatecomp, draincomp=draincomp)               # find maximum |Id|
		# Idmax,IgatIdmax,Idcompstatval,Igcompstatval = iv.fetbiason_backgate(Vgs=-10, Vds=-1, gatecomp=gatecomp, draincomp=draincomp)               # find maximum |Id|
		# time.sleep(.05)
		# iv.fetbiasoff()
		# time.sleep(.05)

		# onoffratio=abs(Idmax)/abs(Idmin)
		# print("burn Vds= "+formatnum(Vdsburn,precision=1))
		# print("after burn Idmax= "+formatnum(Idmax,precision=2)+" after burn Idmin= "+formatnum(Idmin,precision=2)+" after burn onoffratio = "+formatnum(onoffratio,precision=1))
		# print("afterburn Ig at Idmin= "+formatnum(IgatIdmin,precision=2)+ " after burn Ig at Idmax = "+formatnum(IgatIdmax,precision=2))

		iv.measure_ivtransfer_topgate(inttime="2", Vds=Vds_bias, draincomp=draincomp, Vgs_start=Vgs_transstart, Vgs_stop=Vgs_transstop, Vgs_step=Vgs_transstep, gatecomp=gatecomp)
		iv.writefile_ivtransfer(pathname,pr.devicename(),pr.wafername(),pr.x(),pr.y(),devicenamemodifier="Vdsburn"+formatnum(Vdsburn,precision=2))

		# iv.measure_ivtransferloop_backgate(inttime="2", Vds=Vds_bias, draincomp=draincomp, Vgs_start=Vgs_transstart, Vgs_stop=Vgs_transstop, Vgs_step=Vgs_transstep, gatecomp=gatecomp)
		# iv.writefile_ivtransferloop(pathname,cascade.devicename(),cascade.wafername(),cascade.x(),cascade.y(),devicenamemodifier="Vdsburn"+formatnum(Vdsburn,precision=2))
		# save burn curve to disk
		if firstloop:
			iv.writefile_burnonefinalvaluessweepVds(pathname=pathname,wafername=pr.wafername(),devicename=pr.devicename(),xloc=pr.x(),yloc=pr.y(),writeheader=True,newfile=True)             # write header with data since this is the first loop
			firstloop=False
		else:
			iv.writefile_burnonefinalvaluessweepVds(pathname=pathname,wafername=pr.wafername(),devicename=pr.devicename(),xloc=pr.x(),yloc=pr.y())
	pr.tp.movenextsite()    # move probe index to next site (software move only without mechanical movement)

pr.move_separate()
print("done probing wafer")