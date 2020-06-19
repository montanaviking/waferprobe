# main wafer probing routine
import visa
from time import sleep

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from cascade import CascadeProbeStation                                                    # Cascade wafer prober
#from old.plotSmeas import dataPlotter

#pna = Pna(rm,16)                                                                    # setup network analyzer
iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
#sp = dataPlotter()
# set up of IV and bias voltages
# family of curves
Vgs_focstart = -25
Vgs_focstop = 0
Vgs_focnpts =6
# Vgs_focstop = 5
# Vgs_focnpts = 15
probingsbetweencleans=30
Vds_focstart = 0.
Vds_focstop = -1.
Vds_focnpts =21

Vgs_trans_start=-25
Vgs_trans_stop=5
Vgs_trans_step=0.5
# Sparameters only
#Vgs_bias = -1.                                                                      # gate bias for S-parameters
# common to both
gatecomp = 50E-6                                                                   # gate current compliance in A
#gatecomp = 0.01
draincomp = 0.1                                                                   # drain current compliance in A
#Vgs_bias = -10.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
goodIg=50E-6                          # gate current must be LESS than this amount to qualify device for further testing
Vgs_validation = -20.
Vds_validation = -1.

#pathnameIV = "C:/Users/test/python/waferprobe/data"+sub("DC")
#pathnameRF = "C:/Users/test/python/waferprobe/data"+sub("SPAR")
pathname = "C:/Users/test/python/data/L6meas5"
#probe selected ORTH devices
# pr = CascadeProbeStation(rm,pathname=pathname,planname="L6meas5_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
# pr.move_plan_index()					# move to first site
# firsttime=True
# probingcount=0
# while pr.get_probingstatus()=="probing wafer":
# 	print ("probing device ", pr.wafername()+"_"+pr.devicename(),"xpos = ",pr.x(),"ypos =",pr.y())
# 	# test to see if the device is any good before committing to a full measurement
# 	Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=Vgs_validation, Vds=Vds_validation, gatecomp=gatecomp, draincomp=draincomp)
# 	print ( "Id= "+str(Idval)+ " Ig="+str(Igval)+" drain status "+str(Idcompstatval)+" gate status "+str(Igcompstatval))
# 	if abs(Idval)>goodId and Idcompstatval=="N" and Igcompstatval=="N":
# 		devicegood = True
# 	else:
# 		devicegood = False
# 		print("Bad device")
# 		iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicename(),devicenamemodifier="",xloc_probe=pr.x(), yloc_probe=pr.y())  # log bad devices
# 		firsttime=False
# 		#time.sleep(12)
# 	#devicegood=True
# 	print("The device name is ",pr.devicename())
# 	#time.sleep(5)
# 	if devicegood==True:		# measure only good devices
# 		probingcount+=1
# 		if probingcount>probingsbetweencleans:
# 			pr.cleanprobe(auxstagenumber=12,number_cleaning_contacts=2)          # clean on sticky probe cleaner first then dry abrasive probe cleaner pad 2nd
# 			probingcount=0

#Code for regular device characterization:
		# iv.measure_ivtransfer_backgate(inttime="2", Vds=-2, draincomp=draincomp, filterfactor=2, delaytime=0.05, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp)
		# iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds2')
		# iv.measure_ivfoc_backgate(inttime='2', Vds_start=Vds_focstart, delaytime=0.05, Vds_stop=Vds_focstop, draincomp=draincomp, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop, gatecomp=gatecomp, Vgs_npts=Vgs_focnpts)
		# iv.writefile_ivfoc(pathname,cascade.devicename(),cascade.wafername(),cascade.x(),cascade.y(),devicenamemodifier="")

		#single-sweep transfer curve low drain voltage

		#iv.measure_ivtransfer_backgate(inttime="2", Vds=-0.01, draincomp=draincomp, delaytime=0.05, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp)
		#iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_0.01')

		#iv.measure_ivtransfer_backgate(inttime="2", Vds=-1, draincomp=draincomp, delaytime=0.05, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp,Iautorange=False)
		#iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_1')

		#iv.measure_ivfoc_Vdsloop_controlledslew(backgated=True, Vdsslewrate=10, quiescenttime=10,startstopzero=True, Vds_start=Vds_focstart, Vds_stop=Vds_focstop, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop, Vgs_npts=Vgs_focnpts,gatecomp=gatecomp,draincomp=draincomp)
		#iv.writefile_ivfoc_Vdsloop(pathname=pathname,wafername=cascade.wafername(),devicename=cascade.devicename(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier="")

		# #Transfer curve loops at Vds=-0.01V:
		# iv.measure_ivtransferloop_controlledslew(backgated=True, quiescenttime=60, Vgsslewrate=1., Vds=-0.01,Vgs_start=-5,Vgs_stop=5,Vgs_step=0.2,gatecomp=gatecomp,draincomp=draincomp)
		# iv.writefile_ivtransferloop(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsslew1Vds0.01Vgs5')
		# iv.measure_ivtransferloop_controlledslew(backgated=True,quiescenttime=60, Vgsslewrate=10., Vds=-0.01,Vgs_start=-5,Vgs_stop=5,Vgs_step=0.2,gatecomp=gatecomp,draincomp=draincomp)
		# iv.writefile_ivtransferloop(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsslew10Vds0.01Vgs5')
		# iv.measure_ivtransferloop_controlledslew(backgated=True,quiescenttime=60, Vgsslewrate=25., Vds=-0.01,Vgs_start=-5,Vgs_stop=5,Vgs_step=0.2,gatecomp=gatecomp,draincomp=draincomp)
		# iv.writefile_ivtransferloop(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsslew25Vds0.01Vgs5')
		#
		# iv.measure_ivtransferloop_controlledslew(backgated=True,quiescenttime=60, Vgsslewrate=1., Vds=-0.01,Vgs_start=-10,Vgs_stop=10,Vgs_step=0.5,gatecomp=gatecomp,draincomp=draincomp)
		# iv.writefile_ivtransferloop(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsslew1Vds0.01Vgs10')
		# iv.measure_ivtransferloop_controlledslew(backgated=True,quiescenttime=60, Vgsslewrate=10., Vds=-0.01,Vgs_start=-10,Vgs_stop=10,Vgs_step=0.5,gatecomp=gatecomp,draincomp=draincomp)
		# iv.writefile_ivtransferloop(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsslew10Vds0.01Vgs10')
		# iv.measure_ivtransferloop_controlledslew(backgated=True,quiescenttime=60, Vgsslewrate=25., Vds=-0.01,Vgs_start=-10,Vgs_stop=10,Vgs_step=0.5,gatecomp=gatecomp,draincomp=draincomp)
		# iv.writefile_ivtransferloop(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsslew25Vds0.01Vgs10')
		#
		# iv.measure_ivtransferloop_controlledslew(backgated=True,quiescenttime=60, Vgsslewrate=1., Vds=-0.01,Vgs_start=-20,Vgs_stop=20,Vgs_step=1,gatecomp=gatecomp,draincomp=draincomp)
		# iv.writefile_ivtransferloop(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsslew1Vds0.01Vgs20')
		# iv.measure_ivtransferloop_controlledslew(backgated=True,quiescenttime=60, Vgsslewrate=10., Vds=-0.01,Vgs_start=-20,Vgs_stop=20,Vgs_step=1,gatecomp=gatecomp,draincomp=draincomp)
		# iv.writefile_ivtransferloop(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsslew10Vds0.01Vgs20')
		# iv.measure_ivtransferloop_controlledslew(backgated=True,quiescenttime=60, Vgsslewrate=25., Vds=-0.01,Vgs_start=-20,Vgs_stop=20,Vgs_step=1,gatecomp=gatecomp,draincomp=draincomp)
		# iv.writefile_ivtransferloop(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsslew25Vds0.01Vgs20')
		#Transfer curve loops at Vds=-1.5V:

		# iv.writefile_ivtransferloop(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='')
		# iv.measure_ivtransferloop_controlledslew(backgated=True,Vgsslewrate=1., Vds=-1.,Vgs_start=Vgs_trans_start,Vgs_stop=Vgs_trans_stop,Vgs_step=Vgs_trans_step,gatecomp=gatecomp,draincomp=draincomp)
		# iv.writefile_ivtransferloop(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='')

		#single-sweep transfer curves variable voltage
		#iv.measure_ivtransfer_backgate(inttime="4", Vds=-1, draincomp=draincomp, filterfactor=2, delaytime=0.05, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp,Iautorange=False)
#		iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_0.01')
#		iv.measure_ivtransfer_backgate(inttime="4", Vds=-0.1, draincomp=draincomp, filterfactor=2,  delaytime=0.05, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, #gatecomp=gatecomp,Iautorange=False)
#		iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_0.1')
#		iv.measure_ivtransfer_backgate(inttime="4", Vds=-0.5, draincomp=draincomp, filterfactor=2, delaytime=0.05, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp,Iautorange=False)
	#	iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_0.5')
	#
	#	iv.measure_ivtransfer_backgate(inttime="4", Vds=-1.5, draincomp=draincomp, filterfactor=2, delaytime=0.05, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, #gatecomp=gatecomp,Iautorange=False)
	#	iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_1.5')

		# 		# family of curves
		# iv.measure_ivfoc_backgate(inttime='2', Vds_start=Vds_focstart, delaytime=0.05, Vds_stop=Vds_focstop, draincomp=draincomp, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop, gatecomp=gatecomp, Vgs_npts=Vgs_focnpts)
		# iv.writefile_ivfoc(pathname,cascade.devicename(),cascade.wafername(),cascade.x(),cascade.y(),devicenamemodifier="")

		# # controlled slew rate family of curves
		# iv.measure_ivfoc_Vdsloop_controlledslew(back7ated=True, Vdsslewrate=0.25, Vds_start=Vds_focstart, Vds_stop=Vds_focstop, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop, Vgs_npts=Vgs_focnpts,gatecomp=gatecomp,draincomp=draincomp)
		# iv.writefile_ivfoc_Vdsloop(pathname=pathname,wafername=cascade.wafername(),devicename=cascade.devicename(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier="VgsVds+-")

#Code for full hysteresis characterization:
		# transfer curve loop controlled sweep rate 2 loops, |Vgs|<5 V, |Vgs|<10 V, |Vgs|<20 V, faster loops first
		#Vds=10mV 2 loops transfer curves controlled slew
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=25., quiescenttime=60, startstopzero=True, Vds=-0.01,Vgs_start=-5,Vgs_stop=5,Vgs_step=.2,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew25Vgs5Vds-0.01')
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=10., quiescenttime=60, startstopzero=True, Vds=-0.01,Vgs_start=-5,Vgs_stop=5,Vgs_step=.2,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew10Vgs5Vds-0.01')
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=1, quiescenttime=60,startstopzero=True, Vds=-0.01,Vgs_start=-5,Vgs_stop=5,Vgs_step=0.2,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew1Vgs5Vds-0.01')
# 		#
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=25., quiescenttime=60, startstopzero=True, Vds=-0.01,Vgs_start=-10,Vgs_stop=10,Vgs_step=.5,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew25Vgs10Vds-0.01')
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=10., quiescenttime=60, startstopzero=True, Vds=-0.01,Vgs_start=-10,Vgs_stop=10,Vgs_step=.5,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew10Vgs10Vds-0.01')
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=1., quiescenttime=60,startstopzero=True, Vds=-0.01,Vgs_start=-10,Vgs_stop=10,Vgs_step=.5,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew1Vgs10Vds-0.01')
		#
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=25., quiescenttime=60, startstopzero=True, Vds=-0.01,Vgs_start=-20,Vgs_stop=20,Vgs_step=1,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew25Vgs20Vds-0.01')
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=10., quiescenttime=60,startstopzero=True, Vds=-0.01,Vgs_start=-20,Vgs_stop=20,Vgs_step=1,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew10Vgs20Vds-0.01')
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=1., quiescenttime=60,startstopzero=True, Vds=-0.01,Vgs_start=-20,Vgs_stop=20,Vgs_step=.5,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew1Vgs20Vds-0.01')
#
# 		# #Vds=-1.5V 2 loops transfer curves controlled slew
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=25., quiescenttime=60, startstopzero=True, Vds=-1.5,Vgs_start=-5,Vgs_stop=5,Vgs_step=.2,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew25Vgs5Vds-1.5')
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=10., quiescenttime=60, startstopzero=True, Vds=-1.5,Vgs_start=-5,Vgs_stop=5,Vgs_step=.2,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew10Vgs5Vds-1.5')
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=1, quiescenttime=60,startstopzero=True, Vds=-1.5,Vgs_start=-5,Vgs_stop=5,Vgs_step=0.2,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew1Vgs5Vds-1.5')
# 		#
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=25., quiescenttime=60, startstopzero=True, Vds=-1.5,Vgs_start=-10,Vgs_stop=10,Vgs_step=.5,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew25Vgs10Vds-1.5')
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=10., quiescenttime=60, startstopzero=True, Vds=-1.5,Vgs_start=-10,Vgs_stop=10,Vgs_step=.5,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew10Vgs10Vds-1.5')
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=1., quiescenttime=60,startstopzero=True, Vds=-1.5,Vgs_start=-10,Vgs_stop=10,Vgs_step=.5,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew1Vgs10Vds-1.5')
# 		#
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=25., quiescenttime=60, startstopzero=True, Vds=-1.5,Vgs_start=-20,Vgs_stop=20,Vgs_step=1,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew25Vgs20Vds-1.5')
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=10., quiescenttime=60,startstopzero=True, Vds=-1.5,Vgs_start=-20,Vgs_stop=20,Vgs_step=1,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew10Vgs20Vds-1.5')
		iv.measure_ivtransferloop_4sweep_controlledslew(backgated=True,Vgsslewrate=1., quiescenttime=60,startstopzero=True, Vds=-1.5,Vgs_start=-20,Vgs_stop=20,Vgs_step=.5,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='slew1Vgs20Vds-1.5')
#
# 		# # drain voltage hysteresis loops
		iv.measure_ivfoc_Vdsloop_controlledslew(backgated=True, Vdsslewrate=1, quiescenttime=60,startstopzero=True, Vds_start=-1, Vds_stop=1, Vds_npts=21, Vgs_start=0, Vgs_stop=0, Vgs_npts=1,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivfoc_Vdsloop(pathname=pathname,wafername=pr.wafername(),devicename=pr.devicename(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="Vgs0Vds1+-+-")
		iv.measure_ivfoc_Vdsloop_controlledslew(backgated=True, Vdsslewrate=1, quiescenttime=60,startstopzero=True, Vds_start=-2, Vds_stop=2, Vds_npts=21, Vgs_start=0, Vgs_stop=0, Vgs_npts=1,gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivfoc_Vdsloop(pathname=pathname,wafername=pr.wafername(),devicename=pr.devicename(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="Vgs0Vds2+-+-")
# 		## drain voltage hysteresis full FOC gate bias stress test
		iv.measure_ivfoc_Vdsloop_4sweep_controlledslew(backgated=True, Vdsslewrate=1, quiescenttime=60, startstopzero=True, Vds_start=-1, Vds_stop=1, Vds_npts=21, Vgs_start=10, Vgs_stop=-20, Vgs_npts=7, gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivfoc_Vds4sweep(pathname=pathname,wafername=pr.wafername(),devicename=pr.devicename(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="Vds1")
#
#
# # #
# # # 		# #time domain Vds=-0.01V
		#1
		sleep(60)
		iv.measure_hysteresistimedomain(backgated=True,Vds=-0.01,Vgsquiescent=0.,timestep=.01,timequiescent=0.1,timeend=40.,Vgs_start=0.,Vgs_step=0,Vgs_stop=0,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.1Vds-0.01VgsQ0Vgs0')
		iv.fetbiasoff()
		sleep(60)
		#VgsQ=+20V Vgs=0V
		iv.measure_hysteresistimedomain(backgated=True,Vds=-0.01,Vgsquiescent=20.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=0.,Vgs_step=0,Vgs_stop=0,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-0.01VgsQ+20Vgs0')
		iv.fetbiasoff()
		sleep(60)
		#VgsQ=+20V Vgs=-15V
		iv.measure_hysteresistimedomain(backgated=True,Vds=-0.01,Vgsquiescent=20.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=-15.,Vgs_step=0,Vgs_stop=-15,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-0.01VgsQ+20Vgs-15')
		iv.fetbiasoff()
		sleep(60)
		#VgsQ=-20V Vgs=0V
		iv.measure_hysteresistimedomain(backgated=True,Vds=-0.01,Vgsquiescent=-20.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=0.,Vgs_step=0,Vgs_stop=0,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-0.01VgsQ-20Vgs0')
		iv.fetbiasoff()
		sleep(60)
		# VgsQ=-20V Vgs=-15V
		iv.measure_hysteresistimedomain(backgated=True,Vds=-0.01,Vgsquiescent=-20.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=-15.,Vgs_step=0,Vgs_stop=-15,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-0.01VgsQ-20Vgs-15')
		iv.fetbiasoff()
		sleep(60)
		# time domain bias stress tests Vds=-0.01V
		# VgsQ=+20V Vgs=0V
		iv.measure_hysteresistimedomain(backgated=True,Vds=-0.01,Vgsquiescent=20.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=0.,Vgs_step=0,Vgs_stop=0,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_5Vds-0.01VgsQ+20Vgs0')
		iv.fetbiasoff()
		sleep(60)
		#VgsQ=+20V Vgs=-15V
		iv.measure_hysteresistimedomain(backgated=True,Vds=-0.01,Vgsquiescent=20.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=-15.,Vgs_step=0,Vgs_stop=-15,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_5Vds-0.01VgsQ+20Vgs-15')
		iv.fetbiasoff()
		sleep(60)
		#VgsQ=-20V Vgs=0V
		iv.measure_hysteresistimedomain(backgated=True,Vds=-0.01,Vgsquiescent=-20.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=0.,Vgs_step=0,Vgs_stop=0,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_5Vds-0.01VgsQ-20Vgs0')
		iv.fetbiasoff()
		sleep(60)
		#VgsQ=-20V Vgs=-15V
		iv.measure_hysteresistimedomain(backgated=True,Vds=-0.01,Vgsquiescent=-20.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=-15.,Vgs_step=0,Vgs_stop=-15,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_5Vds-0.01VgsQ-20Vgs-15')
		iv.fetbiasoff()


		# #time domain Vds=-2V
		# VgsQ=0V Vgs=0V
		sleep(60)
		iv.measure_hysteresistimedomain(backgated=True,Vds=-2,Vgsquiescent=0.,timestep=.01,timequiescent=0.1,timeend=40.,Vgs_start=0.,Vgs_step=0,Vgs_stop=0,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.1Vds-2VgsQ0Vgs0')
		iv.fetbiasoff()
		sleep(60)
		# VgsQ=+20V Vgs=0V
		iv.measure_hysteresistimedomain(backgated=True,Vds=-2,Vgsquiescent=20.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=0.,Vgs_step=0,Vgs_stop=0,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-2VgsQ+20Vgs0')
		iv.fetbiasoff()
		sleep(60)
		# VgsQ=+20V Vgs=-15V
		iv.measure_hysteresistimedomain(backgated=True,Vds=-2,Vgsquiescent=20.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=-15.,Vgs_step=0,Vgs_stop=-15,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-2VgsQ+20Vgs-15')
		iv.fetbiasoff()
		sleep(60)
		# VgsQ=-20V Vgs=0V
		iv.measure_hysteresistimedomain(backgated=True,Vds=-2,Vgsquiescent=-20.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=0.,Vgs_step=0,Vgs_stop=0,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-2VgsQ-20Vgs0')
		iv.fetbiasoff()
		sleep(60)
		# VgsQ=-20V Vgs=-15V
		iv.measure_hysteresistimedomain(backgated=True,Vds=-2,Vgsquiescent=-20.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=-15.,Vgs_step=0,Vgs_stop=-15,draincomp=draincomp,gatecomp=gatecomp)
		iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-2VgsQ-20Vgs-15')
		iv.fetbiasoff()
		# time domain bias stress tests Vds=-1.5V
		# sleep(60)
		# iv.measure_hysteresistimedomain(backgated=True,Vds=-1.5,Vgsquiescent=20.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=-10.,Vgs_step=0,Vgs_stop=-10,draincomp=draincomp,gatecomp=gatecomp)
		# iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_5Vds-1.5VgsQ+20Vgs-10')
		# iv.fetbiasoff()
		# sleep(60)
		# iv.measure_hysteresistimedomain(backgated=True,Vds=-1.5,Vgsquiescent=20.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=-15.,Vgs_step=0,Vgs_stop=-15,draincomp=draincomp,gatecomp=gatecomp)
		# iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_5Vds-1.5VgsQ+20Vgs-15')
		# iv.fetbiasoff()
		# sleep(60)
		# iv.measure_hysteresistimedomain(backgated=True,Vds=-1.5,Vgsquiescent=-20.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=-10.,Vgs_step=0,Vgs_stop=-10,draincomp=draincomp,gatecomp=gatecomp)
		# iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_5Vds-1.5VgsQ-20Vgs-10')
		# iv.fetbiasoff()
		# sleep(60)
		# iv.measure_hysteresistimedomain(backgated=True,Vds=-1.5,Vgsquiescent=-20.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=-15.,Vgs_step=0,Vgs_stop=-15,draincomp=draincomp,gatecomp=gatecomp)
		# iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_5Vds-1.5VgsQ-20Vgs-15')
		# iv.fetbiasoff()
	pr.move_nextsite()

# cascade = CascadeProbeStation(rm,pathname=pathname,planname="L12meas3_TLM_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
# cascade.move_plan_index()					# move to first site
# firsttime=True
# probingcount=0
# while cascade.get_probingstatus()=="probing wafer":
# 	print ("probing device ", cascade.wafername()+"_"+cascade.devicename(),"xpos = ",cascade.x(),"ypos =",cascade.y())
# 	# test to see if the device is any good before committing to a full measurement
# 	Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=Vgs_validation, Vds=Vds_validation, gatecomp=gatecomp, draincomp=draincomp)
# 	print ( "Id= "+str(Idval)+ " Ig="+str(Igval)+" drain status "+str(Idcompstatval)+" gate status "+str(Igcompstatval))
# 	if abs(Idval)>goodId and Idcompstatval=="N" and Igcompstatval=="N":
# 		devicegood = True
# 	else:
# 		devicegood = False
# 		print("Bad device")
# 		iv.writefile_baddeviceslist(pathname=pathname, wafername=cascade.wafername(), devicenames=cascade.devicename(),devicenamemodifier="",xloc_probe=cascade.x(), yloc_probe=cascade.y(),firsttime=firsttime)  # log bad devices
# 		firsttime=False
# 		#time.sleep(12)
# 	#devicegood=True
# 	print("The device name is ",cascade.devicename())
# 	#time.sleep(5)
# 	if devicegood==True:		# measure only good devices
# 		#single-sweep transfer curve low drain voltage
# 		probingcount+=1
# 		if probingcount>probingsbetweencleans:
# 			cascade.cleanprobe(auxstagenumber=12,number_cleaning_contacts=2)          # clean on sticky probe cleaner first then dry abrasive probe cleaner pad 2nd
# 			probingcount=0
# 		iv.measure_ivtransfer_backgate(inttime="2", Vds=-0.01, draincomp=draincomp, delaytime=0.1, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp)
# 		iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_0.01')
# 		iv.measure_ivtransferloop_controlledslew(backgated=True,Vgsslewrate=1., Vds=-1.,Vgs_start=Vgs_trans_start,Vgs_stop=Vgs_trans_stop,Vgs_step=Vgs_trans_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='')
# 		# single-sweep transfer curves variable voltage
# 		# iv.measure_ivtransfer_backgate(inttime="4", Vds=-0.01, draincomp=draincomp, filterfactor=2, delaytime=0.05, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp,Iautorange=False)
# 		# iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_0.01')
# 		# iv.measure_ivtransfer_backgate(inttime="4", Vds=-0.1, draincomp=draincomp, filterfactor=2,  delaytime=0.05, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp,Iautorange=False)
# 		# iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_0.1')
# 		# iv.measure_ivtransfer_backgate(inttime="4", Vds=-0.5, draincomp=draincomp, filterfactor=2, delaytime=0.05, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp,Iautorange=False)
# 		# iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_0.5')
# 		# iv.measure_ivtransfer_backgate(inttime="4", Vds=-1, draincomp=draincomp, filterfactor=2, delaytime=0.05, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp,Iautorange=False)
# 		# iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_1')
# 		# iv.measure_ivtransfer_backgate(inttime="4", Vds=-1.5, draincomp=draincomp, filterfactor=2, delaytime=0.05, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp,Iautorange=False)
# 		# iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_1.5')
# 		# 		# family of curves
# 		iv.measure_ivfoc_backgate(inttime='2', Vds_start=Vds_focstart, delaytime=0.05, Vds_stop=Vds_focstop, draincomp=draincomp, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop, gatecomp=gatecomp, Vgs_npts=Vgs_focnpts)
# 		iv.writefile_ivfoc(pathname,cascade.devicename(),cascade.wafername(),cascade.x(),cascade.y(),devicenamemodifier="")
# 	cascade.move_nextsite()

















# probe selected TLM devices
# cascade = CascadeProbeStation(rm,pathname=pathname,planname="L2meas3_TLM_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
# cascade.move_plan_index()					# move to first site
# while cascade.get_probingstatus()=="probing wafer":
# 	print ("probing device ", cascade.wafername()+"_"+cascade.devicename(),"xpos = ",cascade.x(),"ypos =",cascade.y())
# 	# test to see if the device is any good before committing to a full measurement
# 	Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=Vgs_validation, Vds=Vds_validation, gatecomp=gatecomp, draincomp=draincomp)
# 	print ( "Id= "+str(Idval)+ " Ig="+str(Igval)+" drain status "+str(Idcompstatval)+" gate status "+str(Igcompstatval))
# 	if abs(Idval)>goodId and Idcompstatval=="N" and Igcompstatval=="N":
# 		devicegood = True
# 	else:
# 		devicegood = False
# 		print("Bad device")
# 		iv.writefile_baddeviceslist(pathname=pathname, wafername=cascade.wafername(), devicenames=cascade.devicename(),devicenamemodifier="",xloc_probe=cascade.x(), yloc_probe=cascade.y(),firsttime=firsttime)  # log bad devices
# 		firsttime=False
# 		#time.sleep(12)
# 	#devicegood=True
# 	print("The device name is ",cascade.devicename())
# 	#time.sleep(5)
# 	if devicegood==True:		# measure only good devices
# 		#single-sweep transfer curve low voltage
# 		# iv.measure_ivtransfer_backgate(inttime="2", Vds=-0.01, draincomp=draincomp, delaytime=0.1, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp)
# 		# iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_0.01')
# 		# # iv.measure_ivtransfer_backgate(inttime="2", Vds=-0.2, draincomp=draincomp, delaytime=0.1, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp)
# 		# # iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_0.2')
# 		# # iv.measure_ivtransfer_backgate(inttime="2", Vds=-1, draincomp=draincomp, delaytime=0.1, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp)
# 		# # iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='')
# 		# # transfer curve loop controlled sweep rate
# 		iv.measure_ivtransferloop_controlledslew(backgated=True,Vgsslewrate=1., Vds=-1.,Vgs_start=Vgs_trans_start,Vgs_stop=Vgs_trans_stop,Vgs_step=Vgs_trans_step,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransferloop(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='')
# 		# # family of curves
# 		# iv.measure_ivfoc_backgate(inttime='2', Vds_start=Vds_focstart, delaytime=0.05, Vds_stop=Vds_focstop, draincomp=draincomp, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop, gatecomp=gatecomp, Vgs_npts=Vgs_focnpts)
# 		# iv.writefile_ivfoc(pathname,cascade.devicename(),cascade.wafername(),cascade.x(),cascade.y(),devicenamemodifier="")
# 		# controlled slew rate family of curves
# 		iv.measure_ivfoc_Vdsloop_controlledslew(backgated=True, Vdsslewrate=0.25, Vds_start=Vds_focstart, Vds_stop=Vds_focstop, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop, Vgs_npts=Vgs_focnpts,gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivfoc_Vdsloop(pathname=pathname,wafername=cascade.wafername(),devicename=cascade.devicename(),devicenamemodifier="VgsVds+-")
# 	cascade.move_nextsite()
pr.move_separate()
print("done probing wafer")