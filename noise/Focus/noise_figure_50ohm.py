from writefile_measured import X_writefile_noiseparameters_v2, X_writefile_noisefigure_v2
from HP8970B_noisemeter import *
#from parameter_analyzer import *
from read_write_spar_noise import *
rm=visa.ResourceManager()
wafername="RFamptests"
runno="1"
devicename="ZX60-2522M-S+_SN-F517501621"
wafername=wafername+runno
pathname="c:/Users/test/python/data/"+wafername
nm=NoiseMeter(rm=rm,ENR=15.39)     # ENR for 1.5GHz
Vds_bias=0
Vgs_bias=np.linspace(-2,-0.5,16)
#iv = ParameterAnalyzer(rm,includeAMREL=False,ptype=True)                                                          # setup IV and bias
# iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=Vds_bias, Vgs_start=-2.5, Vgs_stop=0, Vgs_step=.1, gatecomp=0.01, draincomp=0.1)
# iv.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername,xloc=0,yloc=0,devicenamemodifier='RFamp_noise_sept4_2019_Vds'+formatnum(Vds_bias,precision=2)+'V')

# for Vgs in Vgs_bias:
# 	Id,Ig,drainstatus,gatestatus=iv.fetbiason_topgate(Vds=Vds_bias, Vgs=Vgs, gatecomp=0.01, draincomp=0.1,timeiter=30,maxchangeId=0.5,maxtime=30.)				# bias device
# 	print("Vgs Vds Id, Ig 1st",Vgs,Vds_bias,Id,Ig)
# 	time.sleep(30)
#S=read_spar(pathname+"/systest/RF/tuner_SRI.s2p")
#nm.get_noise_figure_50ohm(smoothing=32, DUTsparfilename=pathname+"/systest/RF/tuner___SRI.s2p",nmsparfilename=pathname+"/systest/RF/isolator_SRI.s2p")
nm.get_noise_figure_50ohm(smoothing=8)
# gain,NF=nm.sweep(smoothing=32)
nm.writefile_noise(pathname=pathname,devicename=devicename,wafername=wafername,Vds=Vds_bias,Vgs=0,devicenamemodifier="")
#iv.fetbiasoff()