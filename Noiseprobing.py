# main wafer probing routine
import visa

from measure_noiseparameters_focus import *
from read_write_spar_noise import *
#from IP3_measure import IP3
#from spectrum_analyzer import *
#from rf_sythesizer import *
rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from cascade import CascadeProbeStation                                                    # Cascade wafer prober


from IVplot import *
tundir="C:/Users/test/focus_setups"
pathname = "C:/Users/test/python/data/Wf169meas10"
systemnoiseparameters=tundir+"/system_probe_Aug14_2017_noiseparameter.xls"
# directories
tunercal="c:/Users/test/focus_setups/calibration_S1tunerS2_Aug14_2017.txt"
probefile=tundir+"/cascade_JC23F_1-1.6GHz_Aug14_2017_RI.s2p"
cas2=[[probefile,'noflip']]



#pna = Pna(rm,16)                                                                    # setup network analyzer
iv = ParameterAnalyzer(rm)                                                          # setup IV and bias

requested_reflections=[ [0.854,2.454], [0.849,12.382], [0.774,10.656], [0.652,4.923], [0.792,19.501], [0.685,18.385], [0.776,1.627], [0.855,-6.989], [0.668,-6.022], [0.766,-6.703], [0.563,11.184], [0.546,-5.838], [0.776,28.977], [0.654,26.197], [0.529,23.525], [0.651,-14.429], [0.775,-14.279], [0.432,0.994] ]

NP=NoiseParameters(rm=rm,ENR=14.79,navgNF=32,navgPNA=32,usePNA=True,tunercalfile=tunercal,cascadefiles_port1=None,cascadefiles_port2=cas2,reflectioncoefficients=requested_reflections,system_noiseparametersfile=systemnoiseparameters)
# transfer curves
Vds_bias = -1.                                                                   # also used for S-parameter drain bias

Vgs_bias=np.arange(-0.5,-0.6,-0.1)                                                   # Vgs array of gate biases for S-parameters
# common to both
gatecomp = 5E-5                                                                   # gate current compliance in A
draincomp = 0.05                                                                   # drain current compliance in A

#validation to see if device warrents further testing
goodId=0.1E-4                        # drain current must exceed this to qualify device for further testing
goodonoff=5.                       # acceptable on-off ratio for S-parameter testing
Vgs_validation = -2.
Vds_validation = -1.
Vgs_pinchoffval=1.                  # used for On-Off ratio validation

pr = CascadeProbeStation(rm=rm,pathname=pathname,planname="Wf169meas10_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
pr.move_plan_index()					# move to first site

while pr.get_probingstatus()=="probing wafer":
	print ("probing device ", pr.wafername()+"_"+pr.devicename(),"xpos = ",pr.x(),"ypos =",pr.y())
	# test to see if the device is any good before committing to a full measurement
	Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=Vgs_validation, Vds=Vds_validation,timeiter=1.,maxtime=0.1,gatecomp=gatecomp, draincomp=draincomp)
	iv.fetbiasoff()
	Idvaloff,Igvaloff,Idcompstatvaloff,Igcompstatvaloff=iv.fetbiason_topgate(Vgs=Vgs_pinchoffval, Vds=Vds_validation, gatecomp=gatecomp, draincomp=draincomp,timeiter=1.,maxtime=0.1)
	onoffrat=abs(Idval/Idvaloff)
	print ("Idval, Idcompstatval, Igcompstatval On-Off ratio"+str(Idval)+" "+str(Idcompstatval)+" "+str(Igcompstatval)+" "+str(onoffrat))
	if abs(Idval)>goodId and Idcompstatval=="N" and Igcompstatval=="N" and onoffrat>goodonoff:
		devicegood = 'yes'
	else:
		devicegood = 'no'
		print("Bad device")
	if devicegood=='yes':		# measure only good devices
		#iv.measure_ivtransfer_topgate(inttime='2',Vds=-1., Vgs_start=-3., Vgs_stop=3., Vgs_step=0.2, gatecomp=gatecomp, draincomp=draincomp)
		#iv.writefile_ivtransfer(pathname=pathname,devicename=cascade.devicename(),wafername=cascade.wafername(),xloc_probe=cascade.x(),yloc_probe=cascade.y(),devicenamemodifier="Vds=-1V")
		#for Vgs in Vgs_bias:
		# probe noise parameters
		Vgs=0
		Vds_bias=0
		#Id,Ig,drainstatus,gatestatus=iv.fetbiason_topgate(Vgs, Vds_bias, gatecomp, draincomp,timeiter=20.,maxchangeId=0.01,maxtime=40.)				# bias device
		Id=0
		Ig=0
		gatestatus='N'
		drainstatus='N'
		#print("Id, Ig 1st",Id,Ig)
		iv.fetbiasoff()
		NP.measure_noiseparameters(frequenciesMHz=[1300])
		NP.writefile_noiseparameters(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc=pr.x(),yloc=pr.y(),Vds=iv.Vds_bias,Vgs=iv.Vgs_bias,Id=Id,Ig=Ig,gatestatus=gatestatus,drainstatus=drainstatus,devicenamemodifier="Vds"+formatnum(iv.Vds_bias,precision=2)+"V_Vgs"+formatnum(iv.Vgs_bias,precision=2)+"V")
		NP.writefile_noisefigure(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc=pr.x(),yloc=pr.y(),Vds=iv.Vds_bias,Vgs=iv.Vgs_bias,Id=Id,Ig=Ig,gatestatus=gatestatus,drainstatus=drainstatus,devicenamemodifier="Vds"+formatnum(iv.Vds_bias,precision=2)+"V_Vgs"+formatnum(iv.Vgs_bias,precision=2)+"V")
		NP.pna_getS(navg=64)
		[sparf,devname]=NP.writefile_spar(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc=pr.x(),yloc=pr.y(),Vds=iv.Vds_bias,Vgs=iv.Vgs_bias,Id=Id,Ig=Ig,gatestatus=gatestatus,drainstatus=drainstatus,devicenamemodifier="Vds"+formatnum(iv.Vds_bias,precision=2)+"V_Vgs"+formatnum(iv.Vgs_bias,precision=2)+"V",measurement_type='db')
		print("device "+pr.devicename()+" Vgs "+str(iv.Vgs_bias))
		iv.fetbiasoff()													# bias off
	pr.move_nextsite()
pr.move_separate()
print("done probing wafer")