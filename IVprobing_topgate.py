# main wafer probing routine
import visa
import time

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from cascade import CascadeProbeStation                                                    # Cascade wafer prober
from harmonic_measurement import *                                                  # harmonic distortion measurement
from pna import *
#from old.plotSmeas import dataPlotter

#pna = Pna(rm,16)                                                                    # setup network analyzer
iv = ParameterAnalyzer(rm)                                                          # setup IV and bias

#dist=Harmonic_distortion(rm=rm,dc=iv,spectrum_analyser_input_attenuation=20., fundamental_frequency=200E6,source_calibration_factor_fundamental=-21.76,SA_calibration_factor_fundamental=1.28,SA_calibration_factor_2nd_harmonic=1.7,SA_calibration_factor_3rd_harmonic=1.85)

#sp = dataPlotter()
# set up of IV and bias voltages
# family of curves
# Vgs_focstart = -10
# Vgs_focstop = 4.
# Vgs_focnpts = 8
#
# Vds_focstart = 0.
# Vds_focstop = -2.
# Vds_focnpts =21
#

Vgs_trans_start=-1.5
Vgs_trans_stop=1
Vgs_trans_step=0.2
Vds_trans=-2.
# Sparameters only
#Vgs_bias = -1.                                                                      # gate bias for S-parameters
# common to both
gatecomp = 5e-6                                                                   # gate current compliance in A
#gatecomp = 0.01
draincomp = 0.1                                                                   # drain current compliance in A
#Vgs_bias = -10.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
goodIg=5E-6                          # gate current must be LESS than this amount to qualify device for further testing
Vgs_validation = -0.5
Vds_validation = -.5

pna = Pna(rm,16)                                                                    # setup network analyzer

#Vgs_bias=np.arange(0.6,-2.2,-0.2)                                                   # Vgs array of gate biases for S-parameters
Vgs_bias=[-1.]

pathname = "C:/Users/test/python/data/Wf169meas13"
#probe selected ORTH devices
pr = CascadeProbeStation(rm,pathname=pathname,planname="Wf169meas13_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
pr.move_plan_index()					# move to first site
firsttime=True
while pr.get_probingstatus()=="probing wafer":
	# if "proberesistancetest" in pr.devicenamesatlevel()[0]:         # then this is a probe resistance test device
	# 	Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=Vgs_validation, Vds=0.1, gatecomp=gatecomp, draincomp=draincomp)
	# 	print("testing probe resistance1 =",0.1/Idval)
	# 	iv.measure_ivfoc_dual_backgate('2', Vds_start=-0.1, Vds_stop=0.1, draincomp=0.1, Vds_npts=11, Vgs_start=0., Vgs_stop=0., gatecomp=gatecomp, Vgs_npts=1)
	# 	resdevices=[pr.devicename()[:-3]+'_left',pr.devicename()[:-3]+'_right']
	# 	iv.writefile_ivfoc_dual(pathname=pathname,devicenames=resdevices,wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="")
	# else:
	# 	print ("probing device ", pr.wafername()+"_"+pr.devicename(),"xpos = ",pr.x(),"ypos =",pr.y())
	# 	# test to see if the device is any good before committing to a full measurement
	# 	Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=Vgs_validation, Vds=Vds_validation, gatecomp=gatecomp, draincomp=draincomp)
	# 	iv.fetbiasoff()
	# 	print ( "Id= "+str(Idval)+ " Ig="+str(Igval)+" drain status "+str(Idcompstatval)+" gate status "+str(Igcompstatval))
	# 	if abs(Idval)>goodId and Idcompstatval=="N" and Igcompstatval=="N":
	# 		devicegood = True
	# 	else:
	# 		devicegood = False
	# 		print("Bad device")
	# 		iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicename(),devicenamemodifier="",xloc_probe=pr.x(), yloc_probe=pr.y())  # log bad devices
	# 		firsttime=False

		#devicegood=True
	print("The device name is ",pr.devicename())
	#time.sleep(5)
	devicegood=True
	if devicegood==True:		# measure only good devices
		# dist.get_harmonic_fundamental(powerlevel=-15., Vds=-1.5,Vgs_start=0.6,Vgs_stop=-2.,Vgs_step=.2,gatecomp=gatecomp,draincomp=draincomp)
		# dist.writefile_harmonicdistortion(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='-15dBm')
		# dist.get_harmonic_fundamental(powerlevel=-10., Vds=-1.5,Vgs_start=0.6,Vgs_stop=-2.,Vgs_step=.2,gatecomp=gatecomp,draincomp=draincomp)
		# dist.writefile_harmonicdistortion(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='-10dBm')
		# dist.get_harmonic_fundamental(powerlevel=-5., Vds=-1.5,Vgs_start=0.6,Vgs_stop=-2.,Vgs_step=.2,gatecomp=gatecomp,draincomp=draincomp)
		# dist.writefile_harmonicdistortion(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='-5dBm')
		iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=Vds_trans, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp, draincomp=draincomp)
		iv.writefile_ivtransfer(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='')
		for Vgs in Vgs_bias:
			Id,Ig,drainstatus,gatestatus=iv.fetbiason_topgate(Vgs, Vds_trans, gatecomp, draincomp,timeiter=10,maxchangeId=0.01,maxtime=40.)				# bias device
			print("Vgs,Vds,Id, Ig 1st",Vgs,Vds_trans,Id,Ig)
			pna.pna_getS(2)												# get the S-parameters
			#pna.writefile_spar(measurement_type="All_RI",pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc=pr.x(),yloc=pr.y(),Vds=iv.Vds_bias,Vgs=iv.Vgs_bias,Id=Id,Ig=Ig,gatestatus=gatestatus,drainstatus=drainstatus,
			 #                  devicenamemodifier="Vds"+formatnum(iv.Vds_bias,precision=2)+"V_Vgs"+formatnum(iv.Vgs_bias,precision=2)+"Vds1.5")
			pna.writefile_spar(measurement_type="All_RI",pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc=pr.x(),yloc=pr.y(),Vds=iv.Vds_bias,Vgs=iv.Vgs_bias,Id=Id,Ig=Ig,gatestatus=gatestatus,drainstatus=drainstatus,
			                   devicenamemodifier="Vds"+formatnum(iv.Vds_bias,precision=2)+"V_Vgs"+formatnum(iv.Vgs_bias,precision=2))
			# transfer curve loop controlled sweep rate
# 			iv.measure_ivtransferloop_4sweep_controlledslew(backgated=False,startstopzero=True, quiescenttime=10., Vgsslewrate=1.,Vds=-0.01,Vgs_start=-0.5,Vgs_stop=0.5,Vgs_step=0.05,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='slew1Vds-.01Vgs0.5')
#
# 			iv.measure_ivtransferloop_4sweep_controlledslew(backgated=False,startstopzero=True, quiescenttime=10., Vgsslewrate=1.,Vds=-0.01,Vgs_start=-1.,Vgs_stop=1.,Vgs_step=0.1,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='slew1Vds-.01Vgs1')
#
# 			iv.measure_ivtransferloop_4sweep_controlledslew(backgated=False,startstopzero=True, quiescenttime=10., Vgsslewrate=1.,Vds=-0.01,Vgs_start=-2.,Vgs_stop=2.,Vgs_step=0.2,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='slew1Vds-.01Vgs2')
#
# 			iv.measure_ivtransferloop_4sweep_controlledslew(backgated=False,startstopzero=True, quiescenttime=10., Vgsslewrate=10.,Vds=-0.01,Vgs_start=-2.,Vgs_stop=2.,Vgs_step=0.2,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='slew10Vds-.01Vgs2')
# #
#
# 			iv.measure_ivtransferloop_4sweep_controlledslew(backgated=False,startstopzero=True, quiescenttime=10., Vgsslewrate=1.,Vds=-1.5,Vgs_start=-0.5,Vgs_stop=0.5,Vgs_step=0.05,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='slew1Vds-1.5Vgs0.5')
#
# 			iv.measure_ivtransferloop_4sweep_controlledslew(backgated=False,startstopzero=True, quiescenttime=10., Vgsslewrate=1.,Vds=-1.5,Vgs_start=-1.,Vgs_stop=1.,Vgs_step=0.1,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='slew1Vds-1.5Vgs1')
#
# 			iv.measure_ivtransferloop_4sweep_controlledslew(backgated=False,startstopzero=True, quiescenttime=10., Vgsslewrate=1.,Vds=-1.5,Vgs_start=-2.,Vgs_stop=2.,Vgs_step=0.2,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='slew1Vds-1.5Vgs2')
#
# 			iv.measure_ivtransferloop_4sweep_controlledslew(backgated=False,startstopzero=True, quiescenttime=10., Vgsslewrate=10.,Vds=-1.5,Vgs_start=-2.,Vgs_stop=2.,Vgs_step=0.2,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='slew10Vds-1.5Vgs2')
# #
#
# 			iv.measure_ivtransferloop_4sweep_controlledslew(backgated=False,startstopzero=True, quiescenttime=10., Vgsslewrate=25.,Vds=-0.01,Vgs_start=-0.5,Vgs_stop=0.5,Vgs_step=0.05,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='slew25Vds-.01Vgs0.5')
#
# 			iv.measure_ivtransferloop_4sweep_controlledslew(backgated=False,startstopzero=True, quiescenttime=10., Vgsslewrate=25.,Vds=-0.01,Vgs_start=-1.,Vgs_stop=1.,Vgs_step=0.1,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='slew25Vds-.01Vgs1')
#
# 			iv.measure_ivtransferloop_4sweep_controlledslew(backgated=False,startstopzero=True, quiescenttime=10., Vgsslewrate=25.,Vds=-0.01,Vgs_start=-2.,Vgs_stop=2.,Vgs_step=0.2,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='slew25Vds-.01Vgs2')
# #
#
# 			iv.measure_ivtransferloop_4sweep_controlledslew(backgated=False,startstopzero=True, quiescenttime=10., Vgsslewrate=25.,Vds=-1.5,Vgs_start=-0.5,Vgs_stop=0.5,Vgs_step=0.05,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='slew25Vds-1.5Vgs0.5')
#
# 			iv.measure_ivtransferloop_4sweep_controlledslew(backgated=False,startstopzero=True, quiescenttime=10., Vgsslewrate=25.,Vds=-1.5,Vgs_start=-1.,Vgs_stop=1.,Vgs_step=0.1,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='slew25Vds-1.5Vgs1')
#
# 			iv.measure_ivtransferloop_4sweep_controlledslew(backgated=False,startstopzero=True, quiescenttime=10., Vgsslewrate=25.,Vds=-1.5,Vgs_start=-2.,Vgs_stop=2.,Vgs_step=0.2,gatecomp=gatecomp,draincomp=draincomp)
# 			iv.writefile_ivtransferloop_4sweep(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='slew25Vds-1.5Vgs2')



			# #
			# iv.measure_ivfoc_Vdsloop_controlledslew(backgated=False, startstopzero=True, quiescenttime=10., Vdsslewrate=1., Vds_start=-1., Vds_stop=1., Vds_npts=21, Vgs_start=0., Vgs_stop=0., Vgs_npts=1,gatecomp=gatecomp,draincomp=draincomp)
			# iv.writefile_ivfoc_Vdsloop(pathname=pathname,wafername=cascade.wafername(),devicename=cascade.devicename(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier="Vds1")
			# # FOC Vds loops
			# iv.measure_ivfoc_Vdsloop_controlledslew(backgated=False, startstopzero=True, quiescenttime=10., Vdsslewrate=1., Vds_start=-2., Vds_stop=2., Vds_npts=41, Vgs_start=0., Vgs_stop=0., Vgs_npts=1,gatecomp=gatecomp,draincomp=draincomp)
			# iv.writefile_ivfoc_Vdsloop(pathname=pathname,wafername=cascade.wafername(),devicename=cascade.devicename(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier="Vds2")
			# #
			# iv.measure_ivfoc_Vdsloop_4sweep_controlledslew(backgated=False, startstopzero=True, Vdsslewrate=1, Vds_start=-1, Vds_stop=1., Vds_npts=21, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop, Vgs_npts=Vgs_focnpts,gatecomp=gatecomp,draincomp=draincomp)
			# iv.writefile_ivfoc_Vds4sweep(pathname=pathname,wafername=cascade.wafername(),devicename=cascade.devicename(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier="")
			#

			# time domain
			# gatecomptd=50e-6
			# iv.measure_hysteresistimedomain(backgated=False,Vds=-1.5,Vgsquiescent=2.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=-1.,Vgs_step=-0.5,Vgs_stop=-1.5,draincomp=draincomp,gatecomp=gatecomptd)
			# iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsq2tq0.5',timepointsperdecade=10)
			# iv.writefile_pulsedtransfertimedomain4200(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsq2tq0.5',timepointsperdecade=10)
			#
			# iv.measure_hysteresistimedomain(backgated=False,Vds=-1.5,Vgsquiescent=-2.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=-1.5,Vgs_step=0.5,Vgs_stop=-1.,draincomp=draincomp,gatecomp=gatecomptd)
			# iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsq-2tq0.5',timepointsperdecade=10)
			# iv.writefile_pulsedtransfertimedomain4200(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsq-2tq0.5',timepointsperdecade=10)
			#
			# iv.measure_hysteresistimedomain(backgated=False,Vds=-1.5,Vgsquiescent=2.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=-1.,Vgs_step=-0.5,Vgs_stop=-1.5,draincomp=draincomp,gatecomp=gatecomptd)
			# iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsq2tq5',timepointsperdecade=10)
			# iv.writefile_pulsedtransfertimedomain4200(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsq2tq5',timepointsperdecade=10)
			#
			# iv.measure_hysteresistimedomain(backgated=False,Vds=-1.5,Vgsquiescent=-2.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=-1.,Vgs_step=-0.5,Vgs_stop=-1.5,draincomp=draincomp,gatecomp=gatecomptd)
			# iv.writefile_pulsedtimedomain4200(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsq-2tq5',timepointsperdecade=10)
			# iv.writefile_pulsedtransfertimedomain4200(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vgsq-2tq5',timepointsperdecade=10)

			# # # single-sweep transfer curve
			# iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=-1.5, draincomp=0.05, Vgs_start=2, Vgs_stop=-3, Vgs_step=-0.1, gatecomp=100E-6)
			# iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='')
			# iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=-0.01, draincomp=0.05, Vgs_start=0, Vgs_stop=-20, Vgs_step=-0.1, gatecomp=100E-6)
			# iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='neg_gate_breakdown')
			# iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=-0.1, draincomp=draincomp, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp)
			# iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_-0.1')
			# iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=-0.5, draincomp=draincomp, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp)
			# iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_-0.5')
			# iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.1, Vds=-1.5, draincomp=draincomp, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp)
			# iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_-1.5')
			# Id,Ig,drainstatus,gatestatus=iv.fetbiason_topgate(Vds=-1.5, Vgs=-3, gatecomp=gatecomp, draincomp=draincomp,timeiter=10,maxchangeId=0.01,maxtime=40.)				# bias device
			# print("Vds, Vgs, Id, Ig",-1.5,-3,Id,Ig)
			# time.sleep(500)
			# iv.fetbiasoff()
			# iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=-1.5, draincomp=draincomp, Vgs_start=Vgs_trans_start, Vgs_stop=Vgs_trans_stop, Vgs_step=Vgs_trans_step, gatecomp=gatecomp)
			# iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier='Vds_-1.5')
			# iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=-1.5, draincomp=draincomp, Vgs_start=-2, Vgs_stop=1, Vgs_step=0.1, gatecomp=gatecomp)
			# iv.writefile_ivtransfer(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier='Vds_-2')
			# # # transfer curve loop controlled sweep rate
			#
			# # # family of curves
			# iv.measure_ivfoc_topgate(inttime='2', delaytime=0.2, Vds_start=-1.5, Vds_stop=0, draincomp=draincomp, Vds_npts=16, Vgs_start=-2, Vgs_stop=1, gatecomp=gatecomp, Vgs_npts=7)
			# iv.writefile_ivfoc(pathname,pr.devicename(),pr.wafername(),pr.x(),pr.y(),devicenamemodifier='')
	pr.move_nextsite()
iv.fetbiasoff()
pr.move_separate()
print("done probing wafer")