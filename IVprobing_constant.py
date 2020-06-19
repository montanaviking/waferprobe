# main wafer probing routine
import visa

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
#from plot import dataPlotter
from IVplot import *

#pna = Pna(rm,16)                                                                    # setup network analyzer
iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
#sp = dataPlotter()

# set up of IV and bias voltages
# family of curves
Vds_focstart = 0.
Vds_focstop = -1.
Vds_focnpts = 21
Vgs_focstart = 4.
Vgs_focstop = -4.
Vgs_focnpts =9
# transfer curves
Vds_bias = -2.                                                                      # also used for S-parameter drain bias
Vgs_transstart = -3.0
Vgs_transstop = 1.0
Vgs_transstep = 0.1
# common to both
gatecomp = 5E-6                                                                   # gate current compliance in A
draincomp = 0.1                                                                   # drain current compliance in A
#Vgs_bias = -10.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
Vgs_validation = -1.
Vds_validation = -1.


#pathnameIV = "C:/Users/test/python/waferprobe/data"+sub("DC")
#pathnameRF = "C:/Users/test/python/waferprobe/data"+sub("SPAR")
pathname = "C:/Users/test/python/waferprobe/data/Wf167_dietomicroQ"

wafername="test"
devicename="test"
# test to see if the device is any good before committing to a full measurement test
# 	devicegood = 'yes'
#else: devicegood = 'no'

iv.measure_ivtransfer_topgate(inttime="4", delayfactor=10, filterfactor=1, integrationtime=1,Vds=Vds_bias, draincomp=draincomp, Vgs_start=Vgs_transstart, Vgs_stop=Vgs_transstop, Vgs_step=Vgs_transstep, gatecomp=gatecomp)
#fname,dname=iv.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername)
# iv.measure_ivtransferloop_topgate(inttime="4", delayfactor=10, filterfactor=10, integrationtime=1,Vds=Vds_bias, draincomp=draincomp, Vgs_start=Vgs_transstart, Vgs_stop=Vgs_transstop, Vgs_step=Vgs_transstep, gatecomp=gatecomp)
#iv.writefile_ivtransferloop(pathname,devicename,wafername,22750,25750)
#iv.measure_ivfoc("1",Vds_focstart,Vds_focstop,draincomp,Vds_focnpts,Vgs_focstart,Vgs_focstop,gatecomp,Vgs_focnpts)
#iv.writefile_ivfoc(pathname,devicename,wafername,0,0)
# app=QtGui.QApplication(sys.argv)
# Id,Ig,b,c=iv.fetbiason_topgate(Vgs=-0.5,Vds=-2.5,gatecomp=gatecomp,draincomp=draincomp,timeiter=1.,maxtime=30.)
# message=QtGui.QMessageBox()
# message.setText("Bias on, Id="+formatnum(Id,2)+" Ig="+formatnum(Ig,2)+" Idstatus "+b+" Igstatus "+c )
# message.exec_()
#iv.fetbiasoff()
#TOIl,TOIh,pfund,pdl,pdh,noisefloor,fitlx,fitly,fithx,fithy,r= IP3m.measureTOI(fractlinfit)

#dev = DeviceParameters(pathname,devicename,Y_Ids_fitorder=8)
#plotIV(dev,'Y_Ids_fitorder 8')
