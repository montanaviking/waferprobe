# main wafer probing routine
import pylab as pl
import visa
from utilities import formatnum

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from pna import Pna                                                                 # network analyzer
#from old.plotSmeas import dataPlotter
from device_parameter_request import DeviceParameters

pna = Pna(rm,16)                                                                    # setup network analyzer
#iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
#sp = dataPlotter()

# bias
#Vds_bias = 10.                                                                   # also used for S-parameter drain bias
gatecomp = 5E-4                                                                   # gate current compliance in A
draincomp = 0.1                                                                   # drain current compliance in A
#Vgs_bias = 0.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
goodId=0.1E-4                        # drain current must exceed this to qualify device for further testing
goodonoff=10.                       # acceptable on-off ratio for S-parameter testing
Vgs_validation = -2.
Vds_validation = -1.
Vgs_pinchoffval=1.



pathname = "C:/Users/test/python/data/TOIsysApril27_2018"
#pathname="C:/Users/test/python/data/QH5teststructures"
#pathname = "C:/Users/test/focus_setups/power/Jan23_2018"
#lotname = "test2"
#wafernumber=1
wafername=""
#basedevicename = "C6_R5_DV6_D21_Vgs_1V_Vds_-3V"
#devicenamebase="input_cable+circulator+biastee"
X=22750
Y=21650

Vgs_bias=-2.2
Vds_bias=10.
wafername="compressiontest"
devname="biastee_isolator_amp_May8_2018"
#iv.fetbiasoff()
#
# iv.measure_ivtransferloop_controlledslew(backgated=False,Vgsslewrate=1.,Vds=Vds_bias,Vgs_start=-4,Vgs_stop=-2,Vgs_step=0.05,gatecomp=gatecomp,draincomp=draincomp)
# iv.writefile_ivtransferloop(pathname=pathname,devicename=devname,wafername=wafername,xloc_probe=0,yloc_probe=0,devicenamemodifier=formatnum(Vds_bias,precision=2)+'_')
# Id,Ig,drainstatus,gatestatus=iv.fetbiason_topgate(Vds=Vds_bias, Vgs=Vgs_bias, gatecomp=gatecomp, draincomp=draincomp,timeiter=10,maxchangeId=0.01,maxtime=40.)				# bias device
# print("Vds, Vgs, Id, Ig",Vds_bias,Vgs_bias,Id,Ig)

#pna.pna_RF_onoff(on=True)
pna.pna_getS(4)												# get the S-parameters
			#Id,Ig,ds,gs=iv.fetbiason_topgate(Vgs_bias, Vds_bias, gatecomp, draincomp)				# bias device again to update currents etc..
			#print("Vds, Vgs, Id, Ig",Vds_bias,Vgs_bias,Id,Ig)
#iv.fetbiasoff()													# bias off
pna.writefile_spar(measurement_type="All_RI",pathname=pathname,devicename=devname,wafername=wafername,xloc=0,yloc=0,Vds=0,Vgs=0,Id=0,Ig=0,gatestatus='',drainstatus='',devicenamemodifier="")
pna.writefile_spar(measurement_type="All_DB",pathname=pathname,devicename=devname,wafername=wafername,xloc=0,yloc=0,Vds=0,Vgs=0,Id=0,Ig=0,gatestatus='',drainstatus='',devicenamemodifier="")

# pl.figure(1,figsize=(8,20))
# pl.clf()
# wm = pl.get_current_fig_manager()
# wm.window.attributes('-topmost',1)
# sp.smithplotSpar(sparf,0,0)
# sp.smithplotSpar(sparf,1,1)
# para = DeviceParameters(pathname,"")
# #[freqSDB,s11dB,s21dB,s12dB,s22dB]=para.Spar('s21db')
#
#sp.spardBplot(para.sfrequencies(),sparf,'S21 (dB)')
	#time.sleep(10)
	#del para
