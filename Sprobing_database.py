# main wafer probing routine
import visa
from probing_utilities import *
from create_probeconstellations_devices.probe_constellations_map import *
from calculated_parameters import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from pna import Pna                                                                 # network analyzer
from cascade import CascadeProbeStation                                                    # Cascade wafer prober
#from old.plotSmeas import dataPlotter
from IVplot import *

pna = Pna(rm,4)                                                                    # setup network analyzer
iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
#sp = dataPlotter()


# transfer curves

#Vgs_bias=[-2.5,-2.,-1.75,-1.5,-1.25,-1.,-0.75,-0.5]                                                   # Vgs array of gate biases for S-parameters
#Vgs_bias=np.arange(-2.,-11.,-1.)                                                   # Vgs array of gate biases for S-parameters
#Vgs_bias=[-0.4]
# common to both
gatecomp = 10E-3                                                                   # gate current compliance in A
draincomp = 0.05                                                                   # drain current compliance in A

#validation to see if device warrents further testing
goodId=0.1E-4                        # drain current must exceed this to qualify device for further testing
goodIg=50E-6
goodonoff=5.                       # acceptable on-off ratio for S-parameter testing
Vgs_validation = -1.
Vds_validation = -1.
#Vgs_pinchoffval=1.                  # used for On-Off ratio validation

wafername="QH28"
runnumber=4
maskname="v6_2finger_single"
wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno
devicelisttotestfile=pathname+"/selecteddevices2.csv"

cascade = CascadeProbeStation(rm=rm)         # setup Cascade NO probeplan file here! This also moves
probc=ConstellationsdB(maskname=maskname,wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probelistfilename=devicelisttotestfile)

##########################################################################################################################
Vds_bias=-1.2
iv.fetbiasoff()
for pconst in probeconstellations:
	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
	devicename=device["name"]
	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
	print ("probing devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"])
	# test to see if the device is any good before committing to a full measurement
	Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=Vgs_validation, Vds=Vds_validation, gatecomp=0.05, draincomp=0.05,maxtime=0.2,timeiter=0.2)
	print ("Id= "+str(Idval)+" Ig="+str(Igval)+" drain status "+str(Idcompstatval)+" gate status "+str(Igcompstatval))
	if ( (abs(Idval)>goodId ) and (abs(Igval)<goodIg ) and (Igcompstatval=="N") and (Idcompstatval=="N") ):
		devicegood = True
	else:
		devicegood = False
		print("Bad device")
	if devicegood:
		iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=Vds_bias, Vgs_start=-3.0, Vgs_stop=1.0, Vgs_step=0.1, gatecomp=gatecomp,draincomp=draincomp)
		iv.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=device["X"],yloc=device["Y"],devicenamemodifier='beforeSparVds'+formatnum(Vds_bias,precision=2,nonexponential=True))
		for Vgs in Vgs_bias:
			Id,Ig,drainstatus,gatestatus=iv.fetbiason_topgate(Vgs, Vds_bias, gatecomp, draincomp,timeiter=10,maxchangeId=0.01,maxtime=40.)				# bias device
			print("Vgs,Vds,Id, Ig 1st",Vgs,Vds_bias,Id,Ig)
			pna.pna_getS(2)												# get the S-parameters
			#MSGlast.append(lintodB(convertSRItoGMAX(pna.s11[i],pna.s21[i],pna.s12[i],pna.s22[i])["gain"]))
			S21last=[lintodB(abs(pna.s21[i])*abs(pna.s21[i])) for i in range(0,len(pna.s21))]    # S21 in dB
			maxdiff=10000.                                          # ensure at least one loop
			noiter=0
			while (maxdiff>0.2 and noiter<10):
				noiter+=1
				pna.pna_getS(2)												# get the S-parameters
				#MSG.append(lintodB(convertSRItoGMAX(pna.s11[i],pna.s21[i],pna.s12[i],pna.s22[i])["gain"]))
				S21=[lintodB(abs(pna.s21[i])*abs(pna.s21[i])) for i in range(0,len(pna.s21))]
				maxdiff=max([abs(S21[i]-S21last[i]) for i in range(0,len(S21))])
				S21last=[m for m in S21]
				print("maxdiff= ",maxdiff,"dB")
			pna.writefile_spar(measurement_type="All_RI",pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=device["X"],yloc=device["Y"],Vds=Vds_bias,Vgs=Vgs,Id=Id,Ig=Ig,gatestatus=gatestatus,drainstatus=drainstatus,devicenamemodifier='Vds_'+formatnum(Vds_bias,precision=2,nonexponential=True)+'_Vgs_'+formatnum(Vgs,precision=2,nonexponential=True))
	iv.fetbiasoff()													# bias off
##################################################################################################################################
# ##########################################################################################################################
# Vds_bias=-1.0
# iv.fetbiasoff()
# for pconst in probeconstellations:
# 	device=probc.get_probing_devices(constellation_name=pconst["name"])[0]   # get names list of all devices in this probe constellation
# 	devicename=device["name"]
# 	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
# 	print ("probing devices ",devicename," ", " x0, y0 = ", device["X"]," ",device["Y"])
# 	# test to see if the device is any good before committing to a full measurement
# 	Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=Vgs_validation, Vds=Vds_validation, gatecomp=0.05, draincomp=0.05,maxtime=0.2,timeiter=0.2)
# 	print ("Id= "+str(Idval)+" Ig="+str(Igval)+" drain status "+str(Idcompstatval)+" gate status "+str(Igcompstatval))
# 	if ( (abs(Idval)>goodId ) and (abs(Igval)<goodIg ) and (Igcompstatval=="N") and (Idcompstatval=="N") ):
# 		devicegood = True
# 	else:
# 		devicegood = False
# 		print("Bad device")
# 	if devicegood:
# 		iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=Vds_bias, Vgs_start=-3.0, Vgs_stop=2.0, Vgs_step=0.1, gatecomp=gatecomp,draincomp=draincomp)
# 		iv.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=device["X"],yloc=device["Y"],devicenamemodifier='Vds_'+formatnum(Vds_bias,precision=1,nonexponential=True))
# 		for Vgs in Vgs_bias:
# 			Id,Ig,drainstatus,gatestatus=iv.fetbiason_topgate(Vgs, Vds_bias, gatecomp, draincomp,timeiter=10,maxchangeId=0.01,maxtime=40.)				# bias device
# 			print("Vgs,Vds,Id, Ig 1st",Vgs,Vds_bias,Id,Ig)
# 			pna.pna_getS(4)												# get the S-parameters
# 			#MSGlast.append(lintodB(convertSRItoGMAX(pna.s11[i],pna.s21[i],pna.s12[i],pna.s22[i])["gain"]))
# 			S21last=[lintodB(abs(pna.s21[i])*abs(pna.s21[i])) for i in range(0,len(pna.s21))]    # S21 in dB
# 			maxdiff=10000.                                          # ensure at least one loop
# 			while (maxdiff>1):
# 				pna.pna_getS(4)												# get the S-parameters
# 				#MSG.append(lintodB(convertSRItoGMAX(pna.s11[i],pna.s21[i],pna.s12[i],pna.s22[i])["gain"]))
# 				S21=[lintodB(abs(pna.s21[i])*abs(pna.s21[i])) for i in range(0,len(pna.s21))]
# 				maxdiff=max([abs(S21[i]-S21last[i]) for i in range(0,len(S21))])
# 				S21last=[m for m in S21]
# 				print("maxdiff= ",maxdiff,"dB")
# 			pna.writefile_spar(measurement_type="All_RI",pathname=pathname,devicename=devicename,wafername=wafername_runno,xloc=device["X"],yloc=device["Y"],Vds=iv.Vds_bias,Vgs=iv.Vgs_bias,Id=Id,Ig=Ig,gatestatus=gatestatus,drainstatus=drainstatus,devicenamemodifier='Vds_'+formatnum(Vds_bias,precision=1,nonexponential=True)+'_Vgs_'+formatnum(Vgs,precision=1,nonexponential=True))
# 	iv.fetbiasoff()													# bias off
# ##################################################################################################################################



# 	iv.fetbiasoff()													# bias off
# ##################################################################################################################################

cascade.move_separate()
cascade.unlockstage()
print("done probing wafer")