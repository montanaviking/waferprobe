# probing routine for single bias S-parameters
import visa

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from pna import Pna                                                                 # network analyzer
from cascade import CascadeProbeStation                                                    # Cascade wafer prober
from old.plotSmeas import dataPlotter
from IVplot import *

pna = Pna(rm,16)                                                                    # setup network analyzer
iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
sp = dataPlotter()


# transfer curves
Vds_bias = -0.1                                                                   # also used for S-parameter drain bias
Vgs_bias=-0.2                                                   # Vgs array of gate biases for S-parameters
# common to both
gatecomp = 5E-5                                                                   # gate current compliance in A
draincomp = 0.05                                                                   # drain current compliance in A

#validation to see if device warrents further testing
goodId=0.1E-4                        # drain current must exceed this to qualify device for further testing
goodonoff=5.                       # acceptable on-off ratio for S-parameter testing
Vgs_validation = -0.2
Vds_validation = -0.1
Vgs_pinchoffval=1.                  # used for On-Off ratio validation


pathname = "C:/Users/test/python/data/USC_Sept26_2019"

pr = CascadeProbeStation(rm=rm,pathname=pathname,planname="noisefiguretests_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
pr.move_plan_index()					# move to first site

while pr.get_probingstatus()=="probing wafer":
	print ("probing device ", pr.wafername()+"_"+pr.devicename(),"xpos = ",pr.x(),"ypos =",pr.y())
	# test to see if the device is any good before committing to a full measurement
	Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=Vgs_validation, Vds=Vds_validation,timeiter=1.,maxtime=0.1,gatecomp=gatecomp, draincomp=draincomp)
	iv.fetbiasoff()
	# Idvaloff,Igvaloff,Idcompstatvaloff,Igcompstatvaloff=iv.fetbiason_topgate(Vgs=Vgs_pinchoffval, Vds=Vds_validation, gatecomp=gatecomp, draincomp=draincomp,timeiter=1.,maxtime=0.1)
	# onoffrat=abs(Idval/Idvaloff)
	# print ("Idval, Idcompstatval, Igcompstatval On-Off ratio"+str(Idval)+" "+str(Idcompstatval)+" "+str(Igcompstatval)+" "+str(onoffrat))
	# if abs(Idval)>goodId and Idcompstatval=="N" and Igcompstatval=="N" and onoffrat>goodonoff:
	# 	devicegood = 'yes'
	# else:
	# 	devicegood = 'no'
	# 	print("Bad device")
	# if devicegood=='yes':		# measure only good devices

		# probe S-parameters
		Id,Ig,drainstatus,gatestatus=iv.fetbiason_topgate(Vgs_bias, Vds_bias, gatecomp, draincomp,timeiter=20.,maxchangeId=0.01,maxtime=40.)				# bias device
		print("Id, Ig 1st",Id,Ig)
		pna.pna_getS(16)												# get the S-parameters
		iv.fetbiasoff()													# bias off
		[sparf,devname]=pna.writefile_spar(measurement_type="All_dB",pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc=pr.x(),yloc=pr.y(),Vds=iv.Vds_bias,Vgs=iv.Vgs_bias,Id=Id,Ig=Ig,gatestatus=gatestatus,drainstatus=drainstatus,devicenamemodifier="Vds"+formatnum(iv.Vds_bias,precision=2)+"V_Vgs"+formatnum(iv.Vgs_bias,precision=2)+"V")
			# pl.figure(1,figsize=(8,20))
			# pl.clf()
			# wm = pl.get_current_fig_manager()
			# wm.window.attributes('-topmost',1)
			# sp.smithplotSpar(sparf,0,0)
			# sp.smithplotSpar(sparf,1,1)
			# para = DeviceParameters(pathname,devname)
			# sp.spardBplot(para.sfrequencies(),para.Spar('s21db'),'S21 (dB)')
			# del para
	pr.move_nextsite()
	plt.clf()
pr.move_separate()
pr.unlockstage()        # leave stage unlocked to keep motors cool after probing
print("done probing wafer")