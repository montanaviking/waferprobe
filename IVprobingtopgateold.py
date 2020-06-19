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
Vds_focstop = -2.
Vds_focnpts =21

# common to both
gatecomp = 5E-5                                                                   # gate current compliance in A
draincomp = 0.1                                                                   # drain current compliance in A
#Vgs_bias = -10.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
goodIg=5E-5                          # gate current must be LESS than this amount to qualify device for further testing
Vgs_validation = -2.0
Vds_validation = -1.0

pathname = "C:/Users/test/python/data/Wf132meas1"   # Include local path up to wafer name folder

# first measure DV1 devices########################################################################
pr = CascadeProbeStation(rm=rm,pathname=pathname,planname="Wf132meas1_plan")                                                               # setup Cascade
pr.move_plan_index()					# move to first site
# #

while pr.get_probingstatus()=="probing wafer":
	if "proberesistancetest" in pr.devicenamesatlevel()[0]:         # then this is a probe resistance test device
		Id0val,Igval,Id0compstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=Vgs_validation, Vds=0.1, gatecomp=gatecomp, draincomp=draincomp)
		print("testing probe resistance1 =",0.1/Id0val)
		#print("testing probe resistance2 =",0.1/Id1val)
		iv.measure_ivfoc_dual_backgate('2', Vds_start=-0.1, Vds_stop=0.1, draincomp=0.1, Vds_npts=11, Vgs_start=0., Vgs_stop=0., gatecomp=gatecomp, Vgs_npts=1)
		iv.writefile_ivfoc_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="")
		#iv.measure_ivfoc_topgate(inttime='2',Vds_start=-0.1,Vds_stop=0.1,draincomp=0.1,Vds_npts=11,Vgs_start=0.,Vgs_stop=0.,gatecomp=gatecomp,Vgs_npts=1)
		#iv.writefile_ivfoc(pathname=pathname,devicename=cascade.devicenamesatlevel(),wafername=cascade.wafername())

	else:
		print ("probing devices ", pr.wafername()+"_"+pr.devicename())
		# # 	# test to see if the device is any good before committing to a full measurement
		Id0val,Igval,Id0compstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=Vgs_validation, Vds=Vds_validation, maxchangeId=.9,maxtime=0.01,gatecomp=gatecomp, draincomp=draincomp)
		print ("Id0= "+str(Id0val)+" Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" gate status "+str(Igcompstatval))
		if abs(Id0val)>goodId and (Id0compstatval=="N") and Igcompstatval=="N":
			devicegood = True
		else:
			devicegood = False
			print("Bad device")
		if devicegood==True:	# measure only good devices

			#app=QtGui.QApplication(sys.argv)
			# Id,Ig,b,c=iv.fetbiason_topgate(Vgs=-3.,Vds=-3.5,gatecomp=gatecomp,draincomp=draincomp,timeiter=1.,maxtime=30.)
			# time.sleep(30)
			# message=QtGui.QMessageBox()
			# message.setText("Bias on, Id="+formatnum(Id,2)+" Ig="+formatnum(Ig,2)+" Idstatus "+b+" Igstatus "+c )
			# message.exec_()

			iv.measure_ivtransferloop_controlledslew(backgated=False, Vgsslewrate=1., Vds=-1., Vgs_start=-3., Vgs_stop=3., Vgs_step=0.2, gatecomp=gatecomp, draincomp=draincomp)
			iv.writefile_ivtransferloop(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="Vds=-1V_slewrate=1V_sec")
			iv.measure_ivtransferloop_controlledslew(backgated=False, Vgsslewrate=10., Vds=-1., Vgs_start=-3., Vgs_stop=3., Vgs_step=0.2, gatecomp=gatecomp, draincomp=draincomp)
			iv.writefile_ivtransferloop(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="Vds=-1V_slewrate=10V_sec")

			iv.measure_ivtransferloop_controlledslew(backgated=False, Vgsslewrate=1., Vds=-0.1, Vgs_start=-3., Vgs_stop=3., Vgs_step=0.2, gatecomp=gatecomp, draincomp=draincomp)
			iv.writefile_ivtransferloop(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="Vds=-0.1V_slewrate=1V_sec")
			iv.measure_ivtransferloop_controlledslew(backgated=False, Vgsslewrate=10., Vds=-0.1, Vgs_start=-3., Vgs_stop=3., Vgs_step=0.2, gatecomp=gatecomp, draincomp=draincomp)
			iv.writefile_ivtransferloop(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="Vds=-0.1V_slewrate=10V_sec")

			# iv.measure_ivtransfer_topgate(inttime='2',Vds=-1., Vgs_start=-3., Vgs_stop=3., Vgs_step=0.2, gatecomp=gatecomp, draincomp=draincomp)
			# iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier="Vds=-1V")

			iv.measure_ivfoc_topgate(inttime="2", Vds_start=Vds_focstart, Vds_stop=Vds_focstop, draincomp=draincomp, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop,gatecomp=gatecomp, Vgs_npts=Vgs_focnpts)
			iv.writefile_ivfoc(pathname=pathname, devicename=pr.devicename(), wafername=pr.wafername(), xloc=pr.x(), yloc=pr.y(),devicenamemodifier="Vds=-1V")
	# iv.measure_hysteresistimedomain(backgated=False,Vds=-2.5,Vgsquiescent=0.,timestep=.01,timequiescent=10.,timeend=10.,Vgs_start=1.,Vgs_step=-0.25,Vgs_stop=-3.,draincomp=0.1,gatecomp=0.01)
	# iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername())
	# iv.writefile_pulsedtransfertimedomain4200(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),timepointsperdecade=20)
	pr.move_nextsite()
pr.move_separate()
print("done probing wafer")
