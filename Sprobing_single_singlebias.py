# main wafer probing routine
import pylab as pl
import visa
import numpy as np
from utilities import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from pna import Pna
from parameter_analyzer import ParameterAnalyzer                                    # IV and bias

# network analyzer
#from plotSmeas import dataPlotter
from device_parameter_request import DeviceParameters
from IVplot import *
iv = ParameterAnalyzer(rm,includeAMREL=False,ptype=True)                                                          # setup IV and bias
pna = Pna(rm,2)                                                                    # setup network analyzer
#iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
#sp = dataPlotter()


gatecomp = 0.01                                                                   # gate current compliance in A
draincomp = 0.1                                                                   # drain current compliance in A

Vds_bias=-1.
wafername="QH10meas13"
pathname="C:/Users/test/python/data/"+wafername
devicename="C9_R5_T100_D23"
iv.fetbiasoff()
Vgs_bias=np.linspace(-1,0,11)
#Vgs_bias=np.linspace(-0.6,0,4)
#Vgs_bias=[-3.,-2.8,-2.5,-2.2,-2.,-1.8,-1.5,-1.]                                                   # Vgs array of gate biases for S-parameters
#Vgs_bias=[-2.2,-1.8]
X=0
Y=0
noitermax=10
#iv.fetbiasoff()
#quit()
iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=Vds_bias, Vgs_start=-1., Vgs_stop=0, Vgs_step=.1, gatecomp=gatecomp, draincomp=draincomp)
iv.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername,xloc=0,yloc=0,devicenamemodifier='RFamp_Aug19_2019'+formatnum(Vds_bias,precision=2)+'V')
#quit()
for Vgs in Vgs_bias:
	Id,Ig,drainstatus,gatestatus=iv.fetbiason_topgate(Vds=Vds_bias, Vgs=Vgs, gatecomp=gatecomp, draincomp=draincomp,timeiter=0.2,maxchangeId=0.5,maxtime=1.)				# bias device
	print("Vgs Vds Id, Ig 1st",Vgs,Vds_bias,Id,Ig)
	pna.pna_getS_2port(1)												# get the S-parameters
	S21last=[lintodB(abs(pna.s21[i])*abs(pna.s21[i])) for i in range(0,len(pna.s21))]    # S21 in dB
	maxdiff=10000.                                          # ensure at least one loop
	noiter=0
	while (maxdiff>0.2 and noiter<noitermax):
		noiter+=1
		pna.pna_getS_2port(2)												# get the S-parameters
		S21=[lintodB(abs(pna.s21[i])*abs(pna.s21[i])) for i in range(0,len(pna.s21))]
		maxdiff=max([abs(S21[i]-S21last[i]) for i in range(0,len(S21))])
		S21last=[m for m in S21]
		print("maxdiff= ",maxdiff,"dB")
		print("maxS21dB= ",max(S21),"dB")
	#pna.writefile_spar(measurement_type="All_RI",pathname=pathname,devicename=devicename,wafername=wafername,xloc=0,yloc=0,Vds=Vds_bias,Vgs=Vgs,Id=Id,Ig=Ig,gatestatus=gatestatus,drainstatus=drainstatus,devicenamemodifier="RFamp_gatecoil2_13t_draincoil_8t_Vds"+formatnum(Vds_bias,precision=2)+"V_Vgs"+formatnum(Vgs,precision=2))
	pna.writefile_spar(measurement_type="All_RI",pathname=pathname,devicename=devicename,wafername=wafername,xloc=0,yloc=0,Vds=Vds_bias,Vgs=Vgs,Id=Id,Ig=Ig,gatestatus=gatestatus,drainstatus=drainstatus,devicenamemodifier="RFampAug19_2019Vds"+formatnum(Vds_bias,precision=2)+"V_Vgs"+formatnum(Vgs,precision=2))
	pna.writefile_spar(measurement_type="All_dB",pathname=pathname,devicename=devicename,wafername=wafername,xloc=0,yloc=0,Vds=Vds_bias,Vgs=Vgs,Id=Id,Ig=Ig,gatestatus=gatestatus,drainstatus=drainstatus,devicenamemodifier="RFampAug19_2019Vds"+formatnum(Vds_bias,precision=2)+"V_Vgs"+formatnum(Vgs,precision=2))
iv.fetbiasoff()

#Id,Ig,ds,gs=iv.fetbiason_topgate(Vgs_bias, Vds_bias, gatecomp, draincomp)				# bias device again to update currents etc..
#print("Vds, Vgs, Id, Ig",Vds_bias,Vgs_bias,Id,Ig)
#iv.fetbiasoff()													# bias off

#pl.figure(1,figsize=(8,20))
#pl.clf()
#wm = pl.get_current_fig_manager()
#wm.window.attributes('-topmost',1)
#sp.smithplotSpar(sparf,0,0)
#sp.smithplotSpar(sparf,1,1)
#para = DeviceParameters(pathname,devname)
	#[freqSDB,s11dB,s21dB,s12dB,s22dB]=para.twoport('SDB')

#sp.spardBplot(para.sfrequencies(),para.Spar('s21db'),'S21 (dB)')
#time.sleep(20)
	#del para
