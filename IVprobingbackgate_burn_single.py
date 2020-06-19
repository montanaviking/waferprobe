# main wafer probing routine
# Measure single device
import visa

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from cascade import CascadeProbeStation                                                    # Cascade wafer prober
from old.plotSmeas import dataPlotter
from IVplot import *

#pna = Pna(rm,16)                                                                    # setup network analyzer
iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
sp = dataPlotter()

# set up of IV and bias voltages
# family of curves
Vds_focstart = 1.0
Vds_focstop = -1.0
Vds_focnpts = 21
Vgs_focstart = 4.0
Vgs_focstop = -12.0
Vgs_focnpts =9
# transfer curves
Vds_bias = -1.0                                                                     # also used for S-parameter drain bias
Vgs_transstart = 5
Vgs_transstop = -12
Vgs_transstep = -0.2
# Sparameters only
#Vgs_bias = -1.                                                                      # gate bias for S-parameters
# common to both
gatecomp = 5E-5                                                                   # gate current compliance in A
#gatecomp = 0.01
draincomp = 0.1                                                                   # drain current compliance in A
#Vgs_bias = -10.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
goodIg=100.E-9                          # gate current must be LESS than this amount to qualify device for further testing
Vgs_validation = -4.
Vds_validation = -1.

#pathnameIV = "C:/Users/test/python/waferprobe/data"+sub("DC")
#pathnameRF = "C:/Users/test/python/waferprobe/data"+sub("SPAR")
pathname = "C:/Users/test/python/waferprobe/data/FT4singlebreakdown"
#lotname = "test2"
#wafernumber=1
#device = "cfet"

#devicestoprobe=["_C7_R5_2ATLM_0.07","_C4_R5_2ATLM_0.1"]
#devicestoprobe=["C6_R2_2ATLM_0.07"]
devicestoprobe=["_C7_R5_2ATLM_0.07"]
pr = CascadeProbeStation(rm,pathname,"FT4singlebreakdown_TLM_plan","correction off")                                                               # setup Cascade

#cascade.move_plan_index()					# move to first site


while pr.get_probingstatus()=='probing wafer':
	# first find selected site in software
	for dev in devicestoprobe:
		if dev==pr.devicename():
			pr.move_plan_index()					# mechanically move to site specified by the software
			print ("probing device ", pr.wafername()+"_"+pr.devicename(),"xpos = ",pr.x(),"ypos =",pr.y())
			# run through tests
			Idmin,IgatIdmin,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=5., Vds=-1, gatecomp=gatecomp, draincomp=draincomp)               # first find miimum |Id| at pinchoff
			time.sleep(.05)
			iv.fetbiasoff()
			Idmax,IgatIdmax,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=-12., Vds=-1, gatecomp=gatecomp, draincomp=draincomp)               # find maximum |Id|
			time.sleep(.05)
			iv.fetbiasoff()
			onoffratio=abs(Idmax)/abs(Idmin)
			print("Initial Idmax= "+formatnum(Idmax,precision=2)+" Initial onoffratio = "+formatnum(onoffratio,precision=1))
			print("Initial Ig at Idmin= "+formatnum(IgatIdmin,precision=2)+ " Initial Ig at Idmax = "+formatnum(IgatIdmax,precision=2))
			onoffratio=abs(Idmax)/abs(Idmin)
			onoffratioprevious=onoffratio/2.            # artificial starting value to ensure at least one attempt to reduce leakage
			Vdsburn=-1.5
			#while onoffratio>1.05*onoffratioprevious and abs(Vdsburn)<5.:
			while abs(Vdsburn)<=4.5:
				# stress to attempt to burn out metallic nanotubes
				Idburn,IgatburnIdmin,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=5., Vds=Vdsburn, gatecomp=gatecomp, draincomp=draincomp)               # burn stress
				time.sleep(5)                       # burn time
				Idmin,IgatIdmin,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=5., Vds=Vdsburn, gatecomp=gatecomp, draincomp=draincomp)               # burn stress
				time.sleep(.05)
				iv.fetbiasoff()
				print("breakdown Idmin = "+formatnum(Idburn,precision=2)+" at Vds burn = "+formatnum(Vdsburn,precision=1))
				time.sleep(5)
				Idmin,IgatIdmin,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=5., Vds=-1, gatecomp=gatecomp, draincomp=draincomp)               # first find miimum |Id| at pinchoff
				time.sleep(.05)
				iv.fetbiasoff()
				time.sleep(5.)
				Idmax,IgatIdmax,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=-12., Vds=-1, gatecomp=gatecomp, draincomp=draincomp)               # find maximum |Id|
				time.sleep(.05)
				iv.fetbiasoff()
				time.sleep(.05)
				onoffratioprevious=onoffratio
				onoffratio=abs(Idmax)/abs(Idmin)
				print("burn Vds= "+formatnum(Vdsburn,precision=1))
				print("after burn Idmax= "+formatnum(Idmax,precision=2)+" after burn Idmin= "+formatnum(Idmin,precision=2)+" after burn onoffratio = "+formatnum(onoffratio,precision=1))
				print("afterburn Ig at Idmin= "+formatnum(IgatIdmin,precision=2)+ " after burn Ig at Idmax = "+formatnum(IgatIdmax,precision=2))
				Vdsburn+=-0.5
			# now get family of curves and single-swept transfer curve and loop transfer curve (double) after burn
			iv.measure_ivfoc_backgate(inttime='2', delayfactor=2,integrationtime=2, Vds_start=Vds_focstart, Vds_stop=Vds_focstop, draincomp=draincomp, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop, gatecomp=gatecomp, Vgs_npts=Vgs_focnpts)
			iv.writefile_ivfoc(pathname,pr.devicename(),pr.wafername(),pr.x(),pr.y())

			iv.measure_ivtransfer_backgate(inttime="2", Vds=Vds_bias, draincomp=draincomp, Vgs_start=Vgs_transstart, Vgs_stop=Vgs_transstop, Vgs_step=Vgs_transstep, gatecomp=gatecomp)
			iv.writefile_ivtransfer(pathname,pr.devicename(),pr.wafername(),pr.x(),pr.y())

			iv.measure_ivtransferloop_backgate(inttime="2", delayfactor='1', Vds=Vds_bias, draincomp=draincomp, Vgs_start=Vgs_transstart, Vgs_stop=Vgs_transstop, Vgs_step=Vgs_transstep, gatecomp=gatecomp)
			iv.writefile_ivtransferloop(pathname,pr.devicename(),pr.wafername(),pr.x(),pr.y())
	pr.tp.movenextsite()

	#cascade.tp.movenextsite()            # move probe index to next site (software move only without mechanical movement)
		# print ("before nextsite")#, cascade.get_probingstatus()
		# #cascade.move_nextsite()
		# print ("after nextsite")#, cascade.get_probingstatus()
		#plt.clf()
pr.move_separate()
print("done probing wafer")