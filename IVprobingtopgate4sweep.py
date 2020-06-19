# main wafer probing routine
import visa

#import mwavepy as mv

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from cascade import CascadeProbeStation                                                    # Cascade wafer prober


#pna = Pna(rm,16)                                                                    # setup network analyzer
iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
#sp = dataPlotter()

# set up of IV and bias voltages
# family of curves
Vgs_focstart = -3.
Vgs_focstop = 2.
Vgs_focnpts = 6

Vds_focstart = 0.
Vds_focstop = -2.
Vds_focnpts =41

# common to both
gatecomp = 5E-5                                                                   # gate current compliance in A
draincomp = 0.1                                                                   # drain current compliance in A
#Vgs_bias = -10.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
goodIg=5E-5                          # gate current must be LESS than this amount to qualify device for further testing
Vgs_validation = -3.0
Vds_validation = -1.0

pathname = "C:/Users/test/python/data/Wf169meas1"

# first measure DV1 devices########################################################################
pr = CascadeProbeStation(rm=rm,pathname=pathname,planname="Wf169meas1_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
pr.move_plan_index()					# move to first site
# #

while pr.get_probingstatus()=="probing wafer":
	if "proberesistancetest" in pr.devicenamesatlevel()[0]:         # then this is a probe resistance test device
		Id0val,Igval,Id0compstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=Vgs_validation, Vds=0.1, gatecomp=gatecomp, draincomp=draincomp)
		print("testing probe resistance1 =",0.1/Id0val)
		#print("testing probe resistance2 =",0.1/Id1val)
		iv.measure_ivfoc_dual_backgate('2', Vds_start=-0.1, Vds_stop=0.1, draincomp=0.1, Vds_npts=11, Vgs_start=0., Vgs_stop=0., gatecomp=gatecomp, Vgs_npts=1)
	 	iv.writefile_ivfoc_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="DVprobing")
	 	#iv.measure_ivfoc_topgate(inttime='2',Vds_start=-0.1,Vds_stop=0.1,draincomp=0.1,Vds_npts=11,Vgs_start=0.,Vgs_stop=0.,gatecomp=gatecomp,Vgs_npts=1)
		#iv.writefile_ivfoc(pathname=pathname,devicename=cascade.devicenamesatlevel(),wafername=cascade.wafername())
		#iv.writefile_ivfoc(pathname, cascade.devicename(), cascade.wafername(), cascade.x(), cascade.y())
	else:
		print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
	# 	# test to see if the device is any good before committing to a full measurement
		Id0val,Igval,Id0compstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=Vgs_validation, Vds=Vds_validation, gatecomp=gatecomp, draincomp=draincomp)
		print ("Id0= "+str(Id0val)+" Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" gate status "+str(Igcompstatval))
		if abs(Id0val)>goodId and (Id0compstatval=="N") and Igcompstatval=="N":
			devicegood = 'yes'
		else:
			devicegood = 'no'
			print("Bad device")
		if devicegood=='yes':	# measure only good devices

# while cascade.get_probingstatus()=="probing wafer":
# 	if "proberesistancetest" in cascade.devicenamesatlevel()[0]:         # then this is a probe resistance test device
# 		Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=0.1, Vds1=0.1, gatecomp=gatecomp, draincomp0=0.05, draincomp1=0.05)
# 		print("testing probe resistance1 =",0.1/Id0val)
# 		print("testing probe resistance2 =",0.1/Id1val)
# 		iv.measure_ivfoc_dual_backgate('2', Vds_start=-0.1, Vds_stop=0.1, draincomp=0.1, Vds_npts=11, Vgs_start=0., Vgs_stop=0., gatecomp=gatecomp, Vgs_npts=1)
# 		iv.writefile_ivfoc_dual(pathname=pathname,devicenames=cascade.devicenamesatlevel(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier="DVprobing")
# 	else:
# 		print ("probing devices "+cascade.wafername()+"_"+cascade.devicename()+", xpos = "+cascade.x()+" ypos = "+cascade.y())
# 		# test to see if the device is any good before committing to a full measurement
# 		Idval, Igval, Idcompstatval, Igcompstatval = iv.fetbiason_topgate(Vgs_validation, Vds_validation, gatecomp,draincomp)
# 		print ("Id0= "+str(Idval)+ " Ig="+str(Igval)+" drain status "+str(Idcompstatval)+" drain1 status "+" gate status "+str(Igcompstatval))
# 		if abs(Idval)>goodId and Idcompstatval=="N" and Igcompstatval=="N" and abs(Igval)<goodIg:
# 			devicegood = 'yes'
# 		else:
# 			devicegood = 'no'
# 			print("Bad device")
#
# 		if devicegood=='yes':	# measure only good devices
			iv.measure_ivtransferloop_4sweep_controlledslew(backgated=False,Vgsslewrate=1,Vds=-1, Vgs_start=3., Vgs_stop=-3., Vgs_step=-0.2, gatecomp=gatecomp, draincomp=draincomp)
			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="Vds_-1V_Vgsslew_1V")

			iv.measure_ivtransferloop_4sweep_topgate(inttime="2", delayfactor='2', filterfactor='2', integrationtime='1', Vds=-1., Vgs_start=3., Vgs_stop=-3., Vgs_step=-0.2, gatecomp=gatecomp, draincomp=draincomp)
			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())

			iv.measure_ivtransferloop_4sweep_topgate(inttime="2", delayfactor='2', filterfactor='2', integrationtime='1', Vds=-0.03, Vgs_start=3., Vgs_stop=-3., Vgs_step=-0.2, gatecomp=gatecomp, draincomp=draincomp)
			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="Vds_-0.03V")

			iv.measure_ivfoc_topgate(inttime="2", Vds_start=Vds_focstart, Vds_stop=Vds_focstop, draincomp=draincomp, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop,gatecomp=gatecomp, Vgs_npts=Vgs_focnpts)
			iv.writefile_ivfoc(pathname, pr.devicename(), pr.wafername(), pr.x(), pr.y())
	pr.move_nextsite()
pr.move_separate()
print("done probing wafer")
