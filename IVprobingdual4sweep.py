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
Vgs_focstop = 3.
Vgs_focnpts = 7

Vds_focstart = 0.
Vds_focstop = -1.
Vds_focnpts =51

Vgs_start=-3.
Vgs_stop=3.
Vgs_step=-0.2

# common to both
gatecomp = 5E-5                                                                   # gate current compliance in A
#gatecomp = 0.01
draincomp = 0.1                                                                   # drain current compliance in A
#Vgs_bias = -10.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
goodIg=5E-5                          # gate current must be LESS than this amount to qualify device for further testing
Vgs_validation = -3.0
Vds0_validation = -1.0
Vds1_validation = -1.0
pathname = "C:/Users/test/python/data/FL16meas2"

# first measure DVx devices########################################################################
pr = CascadeProbeStation(rm=rm,pathname=pathname,planname="FL16meas2_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
pr.move_plan_index()					# move to first site
# #
while pr.get_probingstatus()=="probing wafer":
	if "proberesistancetest" in pr.devicenamesatlevel()[0]:         # then this is a probe resistance test device
		# this is a shorted device to test probe resistance
		Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=0., Vds0=0.1, Vds1=0.1, gatecomp=gatecomp, draincomp0=0.05, draincomp1=0.05)
		print("testing probe resistance1 =",0.1/Id0val)
		print("testing probe resistance2 =",0.1/Id1val)
		iv.measure_ivfoc_dual_backgate('2', Vds_start=-0.1, Vds_stop=0.1, draincomp=0.1, Vds_npts=11, Vgs_start=0., Vgs_stop=0., gatecomp=gatecomp, Vgs_npts=1)
		iv.writefile_ivfoc_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="DVprobing")
	else:   # these are a real pair of devices to be measured
		print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# test to see if the device is any good before committing to a full measurement
		Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=draincomp, draincomp1=draincomp)
		print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		if abs(Id0val)>goodId or abs(Id1val)>goodId and (Id0compstatval=="N" or Id1compstatval=="N") and Igcompstatval=="N" and abs(Igval)<goodIg:
			devicegood = 'yes'
		else:
			devicegood = 'no'
			print("Bad device")
		if devicegood=='yes':	# measure only good devices
			# controlled-slew rate transferloop Vds=-1V
			iv.measure_ivtransferloop_4sweep_dual_controlledslew_backgated(Vgsslewrate=1., Vds=-1,draincomp=draincomp, Vgs_start=Vgs_start, Vgs_stop=Vgs_stop, Vgs_step=Vgs_step, gatecomp=gatecomp)
			iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),devicenamemodifier='Vds_-1V_Vgsslew_1',wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
			iv.measure_ivtransferloop_4sweep_dual_controlledslew_backgated(Vgsslewrate=10., Vds=-1,draincomp=draincomp, Vgs_start=Vgs_start, Vgs_stop=Vgs_stop, Vgs_step=Vgs_step, gatecomp=gatecomp)
			iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),devicenamemodifier='Vds_-1V_Vgsslew_10',wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
			# controlled-slew rate transferloop Vds=-0.1V
			iv.measure_ivtransferloop_4sweep_dual_controlledslew_backgated(Vgsslewrate=1., Vds=-0.1,draincomp=draincomp, Vgs_start=Vgs_start, Vgs_stop=Vgs_stop, Vgs_step=Vgs_step, gatecomp=gatecomp)
			iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),devicenamemodifier='Vds_-0.1V_Vgsslew_1',wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
			iv.measure_ivtransferloop_4sweep_dual_controlledslew_backgated(Vgsslewrate=10., Vds=-0.1,draincomp=draincomp, Vgs_start=Vgs_start, Vgs_stop=Vgs_stop, Vgs_step=Vgs_step, gatecomp=gatecomp)
			iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),devicenamemodifier='Vds_-0.1V_Vgsslew_10',wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
			# # regular transferloop
			# iv.measure_ivtransferloop_4sweep_dual_backgate(inttime="2", delayfactor='2', filterfactor='1', integrationtime='1', Vds=-1.,sweepdelay=0.1,holdtime=1., draincomp=draincomp, Vgs_start=3., Vgs_stop=-3., Vgs_step=-0.1, gatecomp=gatecomp)
			# iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=cascade.devicenamesatlevel(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y())
			# single-swept transfer
			iv.measure_ivtransfer_backgate(inttime="2", Vds=-1., draincomp=draincomp, Vgs_start=Vgs_start, Vgs_stop=Vgs_stop, Vgs_step=Vgs_step, gatecomp=gatecomp)
			iv.writefile_ivtransfer(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
			# family of curves
			iv.measure_ivfoc_dual_backgate(inttime='2', Vds_start=Vds_focstart, Vds_stop=Vds_focstop, draincomp=draincomp, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop, gatecomp=gatecomp, Vgs_npts=Vgs_focnpts)
			iv.writefile_ivfoc_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
	pr.move_nextsite()
pr.move_separate()
del pr

###############################################
# Now measure TLM devices
pr = CascadeProbeStation(rm,pathname,"FL14meas2_dualTLM_plan","correction off")                                                               # setup Cascade
pr.move_plan_index()					# move to first site

while pr.get_probingstatus()=="probing wafer":
	if "proberesistancetest" in pr.devicenamesatlevel()[0]:         # then this is a probe resistance test device
		Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=0.1, Vds1=0.1, gatecomp=gatecomp, draincomp0=0.05, draincomp1=0.05)
		print("testing probe resistance1 =",0.1/Id0val)
		print("testing probe resistance2 =",0.1/Id1val)
		iv.measure_ivfoc_dual_backgate('2', Vds_start=-0.1, Vds_stop=0.1, draincomp=0.1, Vds_npts=11, Vgs_start=0., Vgs_stop=0., gatecomp=gatecomp, Vgs_npts=1)
		iv.writefile_ivfoc_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="TMprobing")
	else:
		print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# test to see if the device is any good before committing to a full measurement
		Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=draincomp, draincomp1=draincomp)
		print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		if abs(Id0val)>goodId or abs(Id1val)>goodId and (Id0compstatval=="N" or Id1compstatval=="N") and Igcompstatval=="N" and abs(Igval)<goodIg:
			devicegood = 'yes'
		else:
			devicegood = 'no'
			print("Bad device")
		#devicegood='yes'
		if devicegood=='yes':	# measure only good devices
			# controlled-slew rate transferloop Vds=-1V
			iv.measure_ivtransferloop_4sweep_dual_controlledslew_backgated(Vgsslewrate=1., Vds=-1,draincomp=draincomp, Vgs_start=Vgs_start, Vgs_stop=Vgs_stop, Vgs_step=Vgs_step, gatecomp=gatecomp)
			iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),devicenamemodifier='Vds_-1V_Vgsslew_1',wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
			iv.measure_ivtransferloop_4sweep_dual_controlledslew_backgated(Vgsslewrate=10., Vds=-1,draincomp=draincomp, Vgs_start=Vgs_start, Vgs_stop=Vgs_stop, Vgs_step=Vgs_step, gatecomp=gatecomp)
			iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),devicenamemodifier='Vds_-1V_Vgsslew_10',wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
			# controlled-slew rate transferloop Vds=-0.1V
			iv.measure_ivtransferloop_4sweep_dual_controlledslew_backgated(Vgsslewrate=1., Vds=-0.1,draincomp=draincomp, Vgs_start=Vgs_start, Vgs_stop=Vgs_stop, Vgs_step=Vgs_step, gatecomp=gatecomp)
			iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),devicenamemodifier='Vds_-0.1V_Vgsslew_1',wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
			iv.measure_ivtransferloop_4sweep_dual_controlledslew_backgated(Vgsslewrate=10., Vds=-0.1,draincomp=draincomp, Vgs_start=Vgs_start, Vgs_stop=Vgs_stop, Vgs_step=Vgs_step, gatecomp=gatecomp)
			iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),devicenamemodifier='Vds_-0.1V_Vgsslew_10',wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
			# single-swept transfer
			iv.measure_ivtransfer_backgate(inttime="2", Vds=-1., draincomp=draincomp, Vgs_start=Vgs_start, Vgs_stop=Vgs_stop, Vgs_step=Vgs_step, gatecomp=gatecomp)
			iv.writefile_ivtransfer(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
			# family of curves
			iv.measure_ivfoc_dual_backgate(inttime='2', Vds_start=Vds_focstart, Vds_stop=Vds_focstop, draincomp=draincomp, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop, gatecomp=gatecomp, Vgs_npts=Vgs_focnpts)
			iv.writefile_ivfoc_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
	pr.move_nextsite()

###############################################
# Measure ORTH devices
pr = CascadeProbeStation(rm,pathname,"FL14meas2_dualORTH_plan","correction off")                                                               # setup Cascade
pr.move_plan_index()					# move to first site

while pr.get_probingstatus()=="probing wafer":
	if "proberesistancetest" in pr.devicenamesatlevel()[0]:         # then this is a probe resistance test device
		Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=0.1, Vds1=0.1, gatecomp=gatecomp, draincomp0=0.05, draincomp1=0.05)
		print("testing probe resistance1 =",0.1/Id0val)
		print("testing probe resistance2 =",0.1/Id1val)
		iv.measure_ivfoc_dual_backgate('2', Vds_start=-0.1, Vds_stop=0.1, draincomp=0.1, Vds_npts=11, Vgs_start=0., Vgs_stop=0., gatecomp=gatecomp, Vgs_npts=1)
		iv.writefile_ivfoc_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="TMprobing")
	else:
		print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# test to see if the device is any good before committing to a full measurement
		Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=draincomp, draincomp1=draincomp)
		print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		if abs(Id0val)>goodId or abs(Id1val)>goodId and (Id0compstatval=="N" or Id1compstatval=="N") and Igcompstatval=="N" and abs(Igval)<goodIg:
			devicegood = 'yes'
		else:
			devicegood = 'no'
			print("Bad device")
		#devicegood='yes'
		if devicegood=='yes':	# measure only good devices
			# controlled-slew rate transferloop Vds=-1V
			iv.measure_ivtransferloop_4sweep_dual_controlledslew_backgated(Vgsslewrate=1., Vds=-1,draincomp=draincomp, Vgs_start=Vgs_start, Vgs_stop=Vgs_stop, Vgs_step=Vgs_step, gatecomp=gatecomp)
			iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),devicenamemodifier='Vds_-1V_Vgsslew_1',wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
			iv.measure_ivtransferloop_4sweep_dual_controlledslew_backgated(Vgsslewrate=10., Vds=-1,draincomp=draincomp, Vgs_start=Vgs_start, Vgs_stop=Vgs_stop, Vgs_step=Vgs_step, gatecomp=gatecomp)
			iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),devicenamemodifier='Vds_-1V_Vgsslew_10',wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
			# controlled-slew rate transferloop Vds=-0.1V
			iv.measure_ivtransferloop_4sweep_dual_controlledslew_backgated(Vgsslewrate=1., Vds=-0.1,draincomp=draincomp, Vgs_start=Vgs_start, Vgs_stop=Vgs_stop, Vgs_step=Vgs_step, gatecomp=gatecomp)
			iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),devicenamemodifier='Vds_-0.1V_Vgsslew_1',wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
			iv.measure_ivtransferloop_4sweep_dual_controlledslew_backgated(Vgsslewrate=10., Vds=-0.1,draincomp=draincomp, Vgs_start=Vgs_start, Vgs_stop=Vgs_stop, Vgs_step=Vgs_step, gatecomp=gatecomp)
			iv.writefile_ivtransferloop_4sweep_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),devicenamemodifier='Vds_-0.1V_Vgsslew_10',wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
			# single-swept transfer
			iv.measure_ivtransfer_backgate(inttime="2", Vds=-1., draincomp=draincomp, Vgs_start=Vgs_start, Vgs_stop=Vgs_stop, Vgs_step=Vgs_step, gatecomp=gatecomp)
			iv.writefile_ivtransfer(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
			# family of curves
			iv.measure_ivfoc_dual_backgate(inttime='2', Vds_start=Vds_focstart, Vds_stop=Vds_focstop, draincomp=draincomp, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop, gatecomp=gatecomp, Vgs_npts=Vgs_focnpts)
			iv.writefile_ivfoc_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
	pr.move_nextsite()
pr.move_separate()
print("done probing wafer")
