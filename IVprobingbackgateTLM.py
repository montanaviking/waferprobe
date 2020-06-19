# main wafer probing routine
import visa
from time import sleep
from utilities import formatnum

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
Vgs_focstop = -25
Vgs_focnpts =1
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
pathname = "C:/Users/test/python/data/L4meas3"
#probe selected ORTH devices
pr = CascadeProbeStation(rm,pathname=pathname,planname="L4meas3_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
pr.move_plan_index()					# move to first site
firsttime=True
maxallowedproberesistance=4.
probingcount=0
totalnumbercleans=0
while pr.get_probingstatus()=="probing wafer":
	if totalnumbercleans>40:
		print("Total number of cleaning cycles >20 so we have poor contacts quitting!")
		quit()
	if totalnumbercleans>20: print("WARNING! total number of cleans = ",totalnumbercleans)
	if "SHORT" in pr.devicename():         # then this is a probe resistance test device
		Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=Vgs_validation, Vds=0.1, gatecomp=gatecomp, draincomp=0.05)
		iv.fetbiasoff()
		proberesistance=0.1/Idval
		print("testing probe resistance =",formatnum(proberesistance,precision=2))
		cleaniter=0
		while proberesistance>maxallowedproberesistance and cleaniter<3:
			if cleaniter==0: totalnumbercleans+=1               # keep track of total number of cleaning cycles
			resbefore=proberesistance
			pr.cleanprobe(auxstagenumber=12,number_cleaning_contacts=2)          # clean on sticky probe cleaner first then dry abrasive probe cleaner pad 2nd
			Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=Vgs_validation, Vds=0.1, gatecomp=gatecomp, draincomp=0.05)
			iv.fetbiasoff()
			proberesistance=0.1/Idval
			print("cleaning loop probe resistance =",formatnum(proberesistance,precision=2))
			cleaniter+=1
			iv.writefile_probecleanlog(pathname=pathname,devicenames=[pr.devicename(),""],wafername=pr.wafername(),
			                           probe0resistance_beforeclean=resbefore,probe0resistance_afterclean=proberesistance,probe1resistance_beforeclean=-9999,probe1resistance_afterclean=-9999,cleaniter=cleaniter)
		iv.measure_ivfoc_backgate('2', Vds_start=-0.1, Vds_stop=0.1, draincomp=0.1, Vds_npts=11, Vgs_start=0., Vgs_stop=0., gatecomp=gatecomp, Vgs_npts=1)
		iv.writefile_ivfoc(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc=pr.x(),yloc=pr.y())
		iv.fetbiason_backgate(Vgs=0., Vds=0., gatecomp=gatecomp, draincomp=draincomp)           # hard-set Vds and Vgs to 0V before next measurement
	else:
		print ("probing device ", pr.wafername()+"_"+pr.devicename(),"xpos = ",pr.x(),"ypos =",pr.y())
		# test to see if the device is any good before committing to a full measurement
		Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_backgate(Vgs=Vgs_validation, Vds=Vds_validation, gatecomp=gatecomp, draincomp=draincomp)
		print ( "Id= "+str(Idval)+ " Ig="+str(Igval)+" drain status "+str(Idcompstatval)+" gate status "+str(Igcompstatval))
		if abs(Idval)>goodId and Idcompstatval=="N" and Igcompstatval=="N":
			devicegood = True
		else:
			devicegood = False
			print("Bad device")
			iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicename(),devicenamemodifier="",xloc_probe=pr.x(), yloc_probe=pr.y(),firsttime=firsttime)  # log bad devices
			firsttime=False
		#devicegood=True
		print("The device name is ",pr.devicename())
		#time.sleep(5)
		if devicegood==True:		# measure only good devices
			# measure transfer curves
			iv.measure_ivtransfer_backgate(inttime="2", Vds=-1, draincomp=draincomp, filterfactor=2, delaytime=0.05, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp)
			iv.writefile_ivtransfer(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='')
			iv.measure_ivfoc_backgate(inttime='2', Vds_start=Vds_focstart, delaytime=0.05, Vds_stop=Vds_focstop, draincomp=draincomp, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop, gatecomp=gatecomp, Vgs_npts=Vgs_focnpts)
			iv.writefile_ivfoc(pathname,pr.devicename(),pr.wafername(),pr.x(),pr.y(),devicenamemodifier="")
		#iv.fetbiasoff()
		iv.fetbiason_backgate(Vgs=0., Vds=0., gatecomp=gatecomp, draincomp=draincomp)           # hard-set Vds and Vgs to 0V
	pr.move_nextsite()

pr.move_separate()
# #del cascade
print("done probing wafer")



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