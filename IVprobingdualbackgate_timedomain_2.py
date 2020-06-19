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
Vgs_focstart = 0
Vgs_focstop = 0
Vgs_focnpts = 1

Vds_focstart = 1.
Vds_focstop = -1.
Vds_focnpts =21

Vgs_trans_start_ss=-10
Vgs_trans_stop_ss=-5.
Vgs_trans_step_ss=0.5


# common to both
#gatecomp = 5E-5                                                                   # gate current compliance in A
gatecomp = 50E-6                                                                   # gate current compliance in A
#gatecomp = 0.01
draincomp = 0.1                                                                   # drain current compliance in A
# draincompmApermm=150.                                        # drain compliance in mA/mm used for loop hysteresis transfer curves and anything else which isn't autoranged
# draincompmApermmlow=15.                                        # drain compliance in mA/mm used for loop hysteresis transfer curves and anything else which isn't autoranged
#draincomplow = 0.001                                                                   # drain current compliance in A - this is for the low Vds test. Compliance is reduced to allow accurate Id measurement at low Vds and low expected currents

#Vgs_bias = -10.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
#goodIg=50.E-6                          # gate current must be LESS than this amount to qualify device for further testing
goodIg=50E-6                          # gate current must be LESS than this amount to qualify device for further testing
Vgs_validation = 0.
Vds0_validation = -1.
Vds1_validation = -1.
pathname = "C:/Users/test/python/data/Hf4meas3"

#######################################################################################################
## 4 sweep drain loop family of curves
pr = CascadeProbeStation(rm,pathname,"Hf4meas3_plan","correction off")                                                               # setup Cascade
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
		# print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# devicegood=True
		# # test to see if the device is any good before committing to a full measurement
		# Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=.1, draincomp1=.1)
		# print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		# if ( (abs(Id0val)>goodId or abs(Id1val)>goodId) and abs(Igval)<goodIg and Igcompstatval=="N" and (Id0compstatval=="N" or Id1compstatval=="N") ):
		# 	devicegood = True
		# else:
		# 	devicegood = False
		# 	print("Bad device")
		# 	iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(),devicenamemodifier="",xloc_probe=pr.x(),xloc1=pr.x()+1750, yloc_probe=pr.y(), yloc1=pr.y())  # log bad devices
		# 	firsttime=False
		devicegood=True
		if devicegood==True:	# measure only good devices
			iv.measure_ivfoc_Vdsloop_4sweep_controlledslew_dual_backgated(Vdsslewrate=1, startstopzero=True, Vds_start=-1, Vds_stop=1, Vds_npts=21, Vgs_start=10, Vgs_stop=-10, Vgs_npts=6, gatecomp=gatecomp,draincomp=draincomp)
			iv.writefile_ivfoc_Vds4sweep_dual(pathname=pathname,wafername=pr.wafername(),devicenames=pr.devicenamesatlevel(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="Vds1")
	pr.move_nextsite()
###############################

## time domain Vds=-0.01V ############################################################################
pr = CascadeProbeStation(rm,pathname,"Hf4meas3_plan","correction off")                                                               # setup Cascade
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
		# print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# devicegood=True
		# # test to see if the device is any good before committing to a full measurement
		# Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=.1, draincomp1=.1)
		# print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		# if ( (abs(Id0val)>goodId or abs(Id1val)>goodId) and abs(Igval)<goodIg and Igcompstatval=="N" and (Id0compstatval=="N" or Id1compstatval=="N") ):
		# 	devicegood = True
		# else:
		# 	devicegood = False
		# 	print("Bad device")
		# 	iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(),devicenamemodifier="",xloc_probe=pr.x(),xloc1=pr.x()+1750, yloc_probe=pr.y(), yloc1=pr.y())  # log bad devices
		# 	firsttime=False
		devicegood=True
		if devicegood==True:	# measure only good devices
			iv.measure_hysteresistimedomain_dual_backgated(Vds=-0.01,Vgsquiescent=0.,timestep=.01,timequiescent=0.1,timeend=40.,Vgs_start=-10.,Vgs_step=0,Vgs_stop=-10,draincomp=draincomp,gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.1Vds-0.01VgsQ0Vgs-10')
	pr.move_nextsite()

## time domain #VgsQ=+20V Vgs=0V ############################################################################
pr = CascadeProbeStation(rm,pathname,"Hf4meas3_plan","correction off")                                                               # setup Cascade
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
		# print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# devicegood=True
		# # test to see if the device is any good before committing to a full measurement
		# Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=.1, draincomp1=.1)
		# print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		# if ( (abs(Id0val)>goodId or abs(Id1val)>goodId) and abs(Igval)<goodIg and Igcompstatval=="N" and (Id0compstatval=="N" or Id1compstatval=="N") ):
		# 	devicegood = True
		# else:
		# 	devicegood = False
		# 	print("Bad device")
		# 	iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(),devicenamemodifier="",xloc_probe=pr.x(),xloc1=pr.x()+1750, yloc_probe=pr.y(), yloc1=pr.y())  # log bad devices
		# 	firsttime=False
		devicegood=True
		if devicegood==True:	# measure only good devices
			iv.measure_hysteresistimedomain_dual_backgated(Vds=-0.01,Vgsquiescent=10.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=-10.,Vgs_step=0,Vgs_stop=-10,draincomp=draincomp,gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-0.01VgsQ+10Vgs-10')
	pr.move_nextsite()

## time domain VgsQ=+20V Vgs=-15V ############################################################################
pr = CascadeProbeStation(rm,pathname,"Hf4meas3_plan","correction off")                                                               # setup Cascade
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
		# print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# devicegood=True
		# # test to see if the device is any good before committing to a full measurement
		# Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=.1, draincomp1=.1)
		# print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		# if ( (abs(Id0val)>goodId or abs(Id1val)>goodId) and abs(Igval)<goodIg and Igcompstatval=="N" and (Id0compstatval=="N" or Id1compstatval=="N") ):
		# 	devicegood = True
		# else:
		# 	devicegood = False
		# 	print("Bad device")
		# 	iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(),devicenamemodifier="",xloc_probe=pr.x(),xloc1=pr.x()+1750, yloc_probe=pr.y(), yloc1=pr.y())  # log bad devices
		# 	firsttime=False
		devicegood=True
		if devicegood==True:	# measure only good devices
			iv.measure_hysteresistimedomain_dual_backgated(Vds=-0.01,Vgsquiescent=10.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=-10.,Vgs_step=0,Vgs_stop=-10,draincomp=draincomp,gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-0.01VgsQ+10Vgs-10')
	pr.move_nextsite()

## time domain VgsQ=-20V Vgs=0V ############################################################################
pr = CascadeProbeStation(rm,pathname,"Hf4meas3_plan","correction off")                                                               # setup Cascade
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
		# print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# devicegood=True
		# # test to see if the device is any good before committing to a full measurement
		# Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=.1, draincomp1=.1)
		# print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		# if ( (abs(Id0val)>goodId or abs(Id1val)>goodId) and abs(Igval)<goodIg and Igcompstatval=="N" and (Id0compstatval=="N" or Id1compstatval=="N") ):
		# 	devicegood = True
		# else:
		# 	devicegood = False
		# 	print("Bad device")
		# 	iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(),devicenamemodifier="",xloc_probe=pr.x(),xloc1=pr.x()+1750, yloc_probe=pr.y(), yloc1=pr.y())  # log bad devices
		# 	firsttime=False
		devicegood=True
		if devicegood==True:	# measure only good devices
			iv.measure_hysteresistimedomain_dual_backgated(Vds=-0.01,Vgsquiescent=-10.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=10.,Vgs_step=0,Vgs_stop=10,draincomp=draincomp,gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-0.01VgsQ-10Vgs+10')
	pr.move_nextsite()

## time domain VgsQ=-20V Vgs=-15V ############################################################################
pr = CascadeProbeStation(rm,pathname,"Hf4meas3_plan","correction off")                                                               # setup Cascade
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
		# print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# devicegood=True
		# # test to see if the device is any good before committing to a full measurement
		# Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=.1, draincomp1=.1)
		# print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		# if ( (abs(Id0val)>goodId or abs(Id1val)>goodId) and abs(Igval)<goodIg and Igcompstatval=="N" and (Id0compstatval=="N" or Id1compstatval=="N") ):
		# 	devicegood = True
		# else:
		# 	devicegood = False
		# 	print("Bad device")
		# 	iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(),devicenamemodifier="",xloc_probe=pr.x(),xloc1=pr.x()+1750, yloc_probe=pr.y(), yloc1=pr.y())  # log bad devices
		# 	firsttime=False
		devicegood=True
		if devicegood==True:	# measure only good devices
			iv.measure_hysteresistimedomain_dual_backgated(Vds=-0.01,Vgsquiescent=-10.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=-5.,Vgs_step=0,Vgs_stop=-5,draincomp=draincomp,gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-0.01VgsQ-10Vgs-5')
	pr.move_nextsite()

# time domain bias stress tests Vds=-0.01V ##############################################################
# VgsQ=+20V Vgs=0V
pr = CascadeProbeStation(rm,pathname,"Hf4meas3_plan","correction off")                                                               # setup Cascade
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
		# print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# devicegood=True
		# # test to see if the device is any good before committing to a full measurement
		# Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=.1, draincomp1=.1)
		# print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		# if ( (abs(Id0val)>goodId or abs(Id1val)>goodId) and abs(Igval)<goodIg and Igcompstatval=="N" and (Id0compstatval=="N" or Id1compstatval=="N") ):
		# 	devicegood = True
		# else:
		# 	devicegood = False
		# 	print("Bad device")
		# 	iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(),devicenamemodifier="",xloc_probe=pr.x(),xloc1=pr.x()+1750, yloc_probe=pr.y(), yloc1=pr.y())  # log bad devices
		# 	firsttime=False
		devicegood=True
		if devicegood==True:	# measure only good devices
			iv.measure_hysteresistimedomain_dual_backgated(Vds=-0.01,Vgsquiescent=10.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=-5.,Vgs_step=0,Vgs_stop=-5,draincomp=draincomp,gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_5Vds-0.01VgsQ+10Vgs-5')
	pr.move_nextsite()



# time domain bias stress tests Vds=-0.01V ##############################################################
# VgsQ=+20V Vgs=-15V
pr = CascadeProbeStation(rm,pathname,"Hf4meas3_plan","correction off")                                                               # setup Cascade
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
		# print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# devicegood=True
		# # test to see if the device is any good before committing to a full measurement
		# Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=.1, draincomp1=.1)
		# print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		# if ( (abs(Id0val)>goodId or abs(Id1val)>goodId) and abs(Igval)<goodIg and Igcompstatval=="N" and (Id0compstatval=="N" or Id1compstatval=="N") ):
		# 	devicegood = True
		# else:
		# 	devicegood = False
		# 	print("Bad device")
		# 	iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(),devicenamemodifier="",xloc_probe=pr.x(),xloc1=pr.x()+1750, yloc_probe=pr.y(), yloc1=pr.y())  # log bad devices
		# 	firsttime=False
		devicegood=True
		if devicegood==True:	# measure only good devices
			iv.measure_hysteresistimedomain_dual_backgated(Vds=-0.01,Vgsquiescent=10.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=-5.,Vgs_step=0,Vgs_stop=-5,draincomp=draincomp,gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_5Vds-0.01VgsQ+10Vgs-5')
	pr.move_nextsite()


# time domain bias stress tests Vds=-0.01V ##############################################################
# #VgsQ=-20V Vgs=-15V
pr = CascadeProbeStation(rm,pathname,"Hf4meas3_plan","correction off")                                                               # setup Cascade
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
		# print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# devicegood=True
		# # test to see if the device is any good before committing to a full measurement
		# Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=.1, draincomp1=.1)
		# print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		# if ( (abs(Id0val)>goodId or abs(Id1val)>goodId) and abs(Igval)<goodIg and Igcompstatval=="N" and (Id0compstatval=="N" or Id1compstatval=="N") ):
		# 	devicegood = True
		# else:
		# 	devicegood = False
		# 	print("Bad device")
		# 	iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(),devicenamemodifier="",xloc_probe=pr.x(),xloc1=pr.x()+1750, yloc_probe=pr.y(), yloc1=pr.y())  # log bad devices
		# 	firsttime=False
		devicegood=True
		if devicegood==True:	# measure only good devices
			iv.measure_hysteresistimedomain_dual_backgated(Vds=-0.01,Vgsquiescent=-10.,timestep=.01,timequiescent=5,timeend=40.,Vgs_start=-5.,Vgs_step=0,Vgs_stop=-5,draincomp=draincomp,gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_5Vds-0.01VgsQ-10Vgs-5')
	pr.move_nextsite()

#time domain Vds=-2V ######################################################
# VgsQ=0V Vgs=0V
pr = CascadeProbeStation(rm,pathname,"Hf4meas3_plan","correction off")                                                               # setup Cascade
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
		# print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# devicegood=True
		# # test to see if the device is any good before committing to a full measurement
		# Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=.1, draincomp1=.1)
		# print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		# if ( (abs(Id0val)>goodId or abs(Id1val)>goodId) and abs(Igval)<goodIg and Igcompstatval=="N" and (Id0compstatval=="N" or Id1compstatval=="N") ):
		# 	devicegood = True
		# else:
		# 	devicegood = False
		# 	print("Bad device")
		# 	iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(),devicenamemodifier="",xloc_probe=pr.x(),xloc1=pr.x()+1750, yloc_probe=pr.y(), yloc1=pr.y())  # log bad devices
		# 	firsttime=False
		devicegood=True
		if devicegood==True:	# measure only good devices
			iv.measure_hysteresistimedomain_dual_backgated(Vds=-1,Vgsquiescent=0.,timestep=.01,timequiescent=0.1,timeend=40.,Vgs_start=-10.,Vgs_step=0,Vgs_stop=-10,draincomp=draincomp,gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.1Vds-1VgsQ0Vgs-10')
	pr.move_nextsite()

#time domain Vds=-2V ######################################################
# VgsQ=+20V Vgs=0V
pr = CascadeProbeStation(rm,pathname,"Hf4meas3_plan","correction off")                                                               # setup Cascade
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
		# print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# devicegood=True
		# # test to see if the device is any good before committing to a full measurement
		# Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=.1, draincomp1=.1)
		# print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		# if ( (abs(Id0val)>goodId or abs(Id1val)>goodId) and abs(Igval)<goodIg and Igcompstatval=="N" and (Id0compstatval=="N" or Id1compstatval=="N") ):
		# 	devicegood = True
		# else:
		# 	devicegood = False
		# 	print("Bad device")
		# 	iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(),devicenamemodifier="",xloc_probe=pr.x(),xloc1=pr.x()+1750, yloc_probe=pr.y(), yloc1=pr.y())  # log bad devices
		# 	firsttime=False
		devicegood=True
		if devicegood==True:	# measure only good devices
			iv.measure_hysteresistimedomain_dual_backgated(Vds=-1,Vgsquiescent=10.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=-10.,Vgs_step=0,Vgs_stop=-10,draincomp=draincomp,gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-1VgsQ+10Vgs-10')
	pr.move_nextsite()

#time domain Vds=-2V ######################################################
# VgsQ=+20V Vgs=-15V
pr = CascadeProbeStation(rm,pathname,"Hf4meas3_plan","correction off")                                                               # setup Cascade
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
		# print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# devicegood=True
		# # test to see if the device is any good before committing to a full measurement
		# Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=.1, draincomp1=.1)
		# print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		# if ( (abs(Id0val)>goodId or abs(Id1val)>goodId) and abs(Igval)<goodIg and Igcompstatval=="N" and (Id0compstatval=="N" or Id1compstatval=="N") ):
		# 	devicegood = True
		# else:
		# 	devicegood = False
		# 	print("Bad device")
		# 	iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(),devicenamemodifier="",xloc_probe=pr.x(),xloc1=pr.x()+1750, yloc_probe=pr.y(), yloc1=pr.y())  # log bad devices
		# 	firsttime=False
		devicegood=True
		if devicegood==True:	# measure only good devices
			iv.measure_hysteresistimedomain_dual_backgated(Vds=-1,Vgsquiescent=10.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=-5.,Vgs_step=0,Vgs_stop=-5,draincomp=draincomp,gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-1VgsQ+10Vgs-5')
	pr.move_nextsite()

#time domain Vds=-2V ######################################################
# VgsQ=-20V Vgs=0V
pr = CascadeProbeStation(rm,pathname,"Hf4meas3_plan","correction off")                                                               # setup Cascade
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
		# print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# devicegood=True
		# # test to see if the device is any good before committing to a full measurement
		# Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=.1, draincomp1=.1)
		# print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		# if ( (abs(Id0val)>goodId or abs(Id1val)>goodId) and abs(Igval)<goodIg and Igcompstatval=="N" and (Id0compstatval=="N" or Id1compstatval=="N") ):
		# 	devicegood = True
		# else:
		# 	devicegood = False
		# 	print("Bad device")
		# 	iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(),devicenamemodifier="",xloc_probe=pr.x(),xloc1=pr.x()+1750, yloc_probe=pr.y(), yloc1=pr.y())  # log bad devices
		# 	firsttime=False
		devicegood=True
		if devicegood==True:	# measure only good devices
			iv.measure_hysteresistimedomain_dual_backgated(Vds=-1,Vgsquiescent=-10.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=0.,Vgs_step=0,Vgs_stop=0,draincomp=draincomp,gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-1VgsQ-10Vgs0')
	pr.move_nextsite()

#time domain Vds=-2V ######################################################
# VgsQ=-20V Vgs=-15V
pr = CascadeProbeStation(rm,pathname,"Hf4meas3_plan","correction off")                                                               # setup Cascade
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
		# print ("probing devices ", pr.wafername()+"_"+pr.devicenamesatlevel()[0]+" "+pr.wafername()+"_"+pr.devicenamesatlevel()[1],"xpos = ",pr.x(),"ypos =",pr.y())
		# devicegood=True
		# # test to see if the device is any good before committing to a full measurement
		# Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=Vds0_validation, Vds1=Vds1_validation, gatecomp=gatecomp, draincomp0=.1, draincomp1=.1)
		# print ("Id0= "+str(Id0val)+" Id1= "+str(Id1val)+ " Ig="+str(Igval)+" drain0 status "+str(Id0compstatval)+" drain1 status "+str(Id1compstatval)+" gate status "+str(Igcompstatval))
		# if ( (abs(Id0val)>goodId or abs(Id1val)>goodId) and abs(Igval)<goodIg and Igcompstatval=="N" and (Id0compstatval=="N" or Id1compstatval=="N") ):
		# 	devicegood = True
		# else:
		# 	devicegood = False
		# 	print("Bad device")
		# 	iv.writefile_baddeviceslist(pathname=pathname, wafername=pr.wafername(), devicenames=pr.devicenamesatlevel(),devicenamemodifier="",xloc_probe=pr.x(),xloc1=pr.x()+1750, yloc_probe=pr.y(), yloc1=pr.y())  # log bad devices
		# 	firsttime=False
		devicegood=True
		if devicegood==True:	# measure only good devices
			iv.measure_hysteresistimedomain_dual_backgated(Vds=-1,Vgsquiescent=-10.,timestep=.01,timequiescent=0.5,timeend=40.,Vgs_start=-5.,Vgs_step=0,Vgs_stop=-5,draincomp=draincomp,gatecomp=gatecomp)
			iv.writefile_pulsedtimedomain4200_dual(pathname=pathname,devicenames=pr.devicenamesatlevel(),wafername=pr.wafername(), timepointsperdecade=20, devicenamemodifier='Tq_0.5Vds-1VgsQ-10Vgs-5')
	pr.move_nextsite()

pr.move_separate()
# #del cascade
print("done probing wafer")