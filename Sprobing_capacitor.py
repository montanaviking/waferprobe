# main wafer probing routine
import visa

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from pna import Pna                                                                 # network analyzer
from old.plotSmeas import dataPlotter
from IVplot import *

pna = Pna(rm=rm,navg=32,measurement_type='s11')                                                                    # setup network analyzer
iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
sp = dataPlotter()


# transfer curves
Vds_bias = 0.                                                                   # also used for S-parameter drain bias
#Vgs_bias=np.arange(0.5,-3.5,-0.5)                                                   # Vgs array of gate biases for S-parameters
Vgs_bias=np.arange(10.,-10.,-0.1)                                                   # Vgs array of gate biases for S-parameters
# common to both
gatecomp = 5E-5                                                                   # gate current compliance in A
draincomp = 0.05                                                                   # drain current compliance in A

#validation to see if device warrents further testing
goodId=0.1E-4                        # drain current must exceed this to qualify device for further testing
goodonoff=10.                       # acceptable on-off ratio for S-parameter testing
# Vgs_validation = -3.
# Vds_validation = -1.
# Vgs_pinchoffval=1.                  # used for On-Off ratio validation


pathname = "C:/Users/test/python/data/FL15CV4"
#
# cascade = CascadeProbeStation(rm,pathname,"Wf137meas1RF_plan","correction off")                                                               # setup Cascade
# cascade.move_plan_index()					# move to first site

# while cascade.get_probingstatus()=="probing wafer":
# 	print ("probing device ", cascade.wafername()+"_"+cascade.devicename(),"xpos = ",cascade.x(),"ypos =",cascade.y())
# 	# test to see if the device is any good before committing to a full measurement
# 	Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs_validation, Vds_validation, gatecomp, draincomp)
# 	iv.fetbiasoff()
# 	time.sleep(0.2)
# 	Idvaloff,Igvaloff,Idcompstatvaloff,Igcompstatvaloff=iv.fetbiason_topgate(Vgs_pinchoffval, Vds_validation, gatecomp, draincomp)
# 	onoffrat=abs(Idval/Idvaloff)
# 	print ("Idval, Idcompstatval, Igcompstatval On-Off ratio"+str(Idval)+" "+str(Idcompstatval)+" "+str(Igcompstatval)+" "+str(onoffrat))
# 	if abs(Idval)>goodId and Idcompstatval=="N" and Igcompstatval=="N" and onoffrat>goodonoff:
# 		devicegood = 'yes'
# 	else:
# 		devicegood = 'no'
# 		print("Bad device")
#
# 	if devicegood=='yes':		# measure only good devices
for Vgs in Vgs_bias:
# probe S-parameters
	iv.fetbiason_backgate(Vgs=0., Vds=Vgs, gatecomp=gatecomp, draincomp=draincomp)				# bias device
	print("Vgs Ig",iv.Vds_bias,iv.Id_bias)
	pna.pna_getS11(navg=32)												# get S11
	iv.fetbiasoff()													# bias off
	[sparf,devname]=pna.writefile_spar(measurement_type="s11_only",pathname=pathname,devicename="FL15CV4__opentopside",wafername="",xloc=0,yloc=0,Vds=iv.Vds_bias,Vgs=iv.Vgs_bias,Id=iv.Id_bias,Ig=iv.Ig_bias,gatestatus=iv.gatestatus_bias,drainstatus=iv.drainstatus_bias,devicenamemodifier="Vgs"+formatnum(iv.Vds_bias,precision=2)+"V")
	# pl.figure(1,figsize=(8,20))
	# pl.clf()
	# wm = pl.get_current_fig_manager()
	# wm.window.attributes('-topmost',1)
	# sp.smithplotSpar(sparf,0,0)
	# sp.smithplotSpar(sparf,1,1)
	# para = DeviceParameters(pathname,devname)
	# sp.spardBplot(para.sfrequencies(),para.Spar('s21db'),'S21 (dB)')
	# del para
#	time.sleep(2)
	#print ("before nextsite")#, cascade.get_probingstatus()
	#cascade.move_nextsite()
	#print ("after nextsite")#, cascade.get_probingstatus()
	plt.clf()
#cascade.move_separate()
print("done probing wafer")