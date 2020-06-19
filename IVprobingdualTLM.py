# main wafer probing routine
import visa
from utilities import formatnum

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from cascade import CascadeProbeStation                                                    # Cascade wafer prober

iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
maxallowedproberesistance=3.
maxallowedproberesistancedifference=1.

# set up of IV and bias voltages
# family of curves
Vgs_focstart = -10
Vgs_focstop = -10
Vgs_focnpts = 1

Vds_focstart = 1.
Vds_focstop = -1.
Vds_focnpts =21

Vgs_trans_start_ss=-25
Vgs_trans_stop_ss=5
Vgs_trans_step_ss=0.5


# common to both
#gatecomp = 5E-5                                                                   # gate current compliance in A
gatecomp = 50E-6                                                                   # gate current compliance in A
#gatecomp = 0.01
draincomp = 0.1                                                                   # drain current compliance in A
draincompmApermm=150.                                        # drain compliance in mA/mm used for loop hysteresis transfer curves and anything else which isn't autoranged
draincompmApermmlow=15.                                        # drain compliance in mA/mm used for loop hysteresis transfer curves and anything else which isn't autoranged
#draincomplow = 0.001                                                                   # drain current compliance in A - this is for the low Vds test. Compliance is reduced to allow accurate Id measurement at low Vds and low expected currents

#Vgs_bias = -10.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
#goodIg=50.E-6                          # gate current must be LESS than this amount to qualify device for further testing
goodIg=50E-6                          # gate current must be LESS than this amount to qualify device for further testing
Vgs_validation = -2
Vds0_validation = -1.
Vds1_validation = -1.
pathname = "C:/Users/test/python/data/L16meas1"

## now probe devices
pr = CascadeProbeStation(rm=rm,pathname=pathname,planname="L16meas1_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
pr.move_plan_index()					# move to first site
firsttime=True
totalnumbercleans=0
while pr.get_probingstatus()=="probing wafer":
	if totalnumbercleans>30:
		print("Total number of cleaning cycles >30 so we have poor contacts quitting!")
		quit()
	print("from line 58 in IVprobingdualTLM.py ", pr.devicenamesatlevel()[0])
	if "proberesistancetest" in pr.devicenamesatlevel()[0]:         # then this is a probe resistance test device
		Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=0.1, Vds1=0.1, gatecomp=gatecomp, draincomp0=0.05, draincomp1=0.05)
		iv.fetbiasoff()
		proberesistance0=0.1/Id0val
		proberesistance1=0.1/Id1val
		print("testing probe resistance0 =",formatnum(proberesistance0,precision=2))
		print("testing probe resistance1 =",formatnum(proberesistance1,precision=2))
		cleaniter=0
		while (proberesistance0>maxallowedproberesistance or proberesistance1>maxallowedproberesistance or abs(proberesistance1-proberesistance0)>maxallowedproberesistancedifference) and cleaniter<3:
		#while proberesistance1>maxallowedproberesistance  and cleaniter<3:
			if cleaniter==0: totalnumbercleans+=1               # keep track of total number of cleaning cycles
			res0before=proberesistance0
			res1before=proberesistance1
			pr.cleanprobe(auxstagenumber=12,number_cleaning_contacts=2)          # clean on sticky probe cleaner first then dry abrasive probe cleaner pad 2nd
			Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=0.1, Vds1=0.1, gatecomp=gatecomp, draincomp0=0.05, draincomp1=0.05)
			iv.fetbiasoff()
			proberesistance0=0.1/Id0val
			proberesistance1=0.1/Id1val
			print("cleaning loop probe resistance0 =",formatnum(proberesistance0,precision=2))
			print("cleaning loop probe resistance1 =",formatnum(proberesistance1,precision=2))
			cleaniter+=1
			iv.writefile_probecleanlog(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(),
			                           probe0resistance_beforeclean=res0before,probe0resistance_afterclean=proberesistance0,probe1resistance_beforeclean=res1before,probe1resistance_afterclean=proberesistance1,cleaniter=cleaniter)

		iv.measure_ivfoc_dual_backgate('2', Vds_start=-0.1, Vds_stop=0.1, draincomp=0.1, Vds_npts=11, Vgs_start=0., Vgs_stop=0., gatecomp=gatecomp, Vgs_npts=1)
		iv.writefile_ivfoc_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
		#iv.fetbiason_dual_backgate(Vgs=0., Vds0=0., Vds1=0., gatecomp=gatecomp, draincomp0=0.05, draincomp1=0.05)           # hard set DC bias to zero prior to probing next device to ensure no charge buildup
	else:
		print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		devicegood=True
		# test to see if the device is any good before committing to a full measurement
		Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=.1, draincomp1=.1)
		print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		if ( (abs(Id0val)>goodId or abs(Id1val)>goodId) and abs(Igval)<goodIg and Igcompstatval=="N" and (Id0compstatval=="N" or Id1compstatval=="N") ):
			devicegood = True
		else:
			devicegood = False
			print("Bad device")
			iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(),devicenamemodifier="",xloc_probe=pr.x(),xloc1=pr.x()+3000, yloc_probe=pr.y(), yloc1=pr.y())  # log bad devices
			firsttime=False
		if devicegood==True:	# measure only good devices
			#if 'W2x40' not in cascade.devicenamesatlevel()[0]:       # we already probed transfer curve for W2x40 in meas1
			# iv.measure_ivtransferloop_dual_controlledslew_backgated(Vgsslewrate=1., Vds=-1, Vgs_start=Vgs_trans_start_ss, Vgs_stop=Vgs_trans_stop_ss, Vgs_step=Vgs_trans_step_ss, gatecomp=gatecomp,draincomp=draincomp,startstopatzero=False)
			# iv.writefile_ivtransferloop_dual(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(), devicenamemodifier="",xloc_probe=pr.x(), yloc_probe=pr.y())
			iv.measure_ivtransfer_dual_backgate(inttime="2", Iautorange=True, delayfactor=2,filterfactor=2,integrationtime=1, sweepdelay=0.05,holdtime=0, Vds=-1, Vgs_start=Vgs_trans_start_ss, Vgs_stop=Vgs_trans_stop_ss, Vgs_step=Vgs_trans_step_ss, gatecomp=gatecomp, draincomp=draincomp)
			iv.writefile_ivtransfer_dual(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(), devicenamemodifier="",xloc_probe=pr.x(), yloc_probe=pr.y())
			#iv.measure_ivfoc_dual_backgate(inttime='2', sweepdelay=0.05, Vds_start=Vds_focstart, Vds_stop=Vds_focstop, draincomp=draincomp, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop, gatecomp=gatecomp, Vgs_npts=Vgs_focnpts)
			# iv.writefile_ivfoc_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
			#iv.fetbiason_dual_backgate(Vgs=0., Vds0=0., Vds1=0., gatecomp=gatecomp, draincomp0=0.05, draincomp1=0.05)           # hard set DC bias to zero prior to probing next device to ensure no charge buildup
			# iv.measure_ivfoc_Vdsloop_controlledslew_dual_backgated(startstopzero=True,quiescenttime=0.,Vdsslewrate=1.,Vds_start=Vds_focstart,Vds_stop=Vds_focstop,draincomp=draincomp,gatecomp=gatecomp,Vds_npts=Vds_focnpts,
			#                                                        Vgs_start=Vgs_focstart,Vgs_stop=Vgs_focstop,Vgs_npts=Vgs_focnpts)
			# iv.writefile_ivfoc_Vdsloop_dual(pathname=pathname,wafername=pr.wafername(),devicenames=pr.devicenamesatlevel(),devicenamemodifier="",xloc_probe=pr.x(),yloc_probe=pr.y())
	pr.move_nextsite()

pr.move_separate()
# #del cascade
print("done probing wafer")