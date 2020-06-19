# main wafer probing routine
import visa
# import matplotlib.pyplot as plt
# import time
# import os
# import numpy as np
# #import mwavepy as mv
# import pylab as pl
# from IP3_measure import IP3
# from spectrum_analyzer import *
#from rf_sythesizer import *
from parameter_analyzer import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())
iv = ParameterAnalyzer(rm)

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from harmonic_measurement import *                                                  # harmonic distortion measurement

#pna = Pna(rm,16)                                                                    # setup network analyzer
#iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
#sp = dataPlotter()

# set up of IV and bias voltages
# family of curves
# Vgs_focstart = -3.
# Vgs_focstop = 3.
# Vgs_focnpts = 7
#
# Vds_focstart = 1.
# Vds_focstop = -1.
# Vds_focnpts =21
#
# Vgs_trans_start=-3.
# Vgs_trans_stop=3.
# Vgs_trans_step=0.01
Vds=-1.2
Vgs=-0.9

# common to both
gatecomp = 0.1                                                                   # gate current compliance in A
#gatecomp = 0.01
draincomp = 0.05  # drain current compliance in A
wafername="QH10meas11"
pathname="C:/Users/test/python/data/"+wafername
iv.fetbiasoff()
quit()
#devicename="ditherdevice"
devicename="C9_R5_T100_D33"
iv.fetbiason_topgate(Vgs=Vgs,Vds=Vds,gatecomp=0.01,draincomp=.1,maxchangeId=0.1,maxtime=300.,timeiter=300.)
#Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs=0, Vds=-1, gatecomp=.1, draincomp=.1)
time.sleep(300)
iv.fetbiasoff()
# iv.measure_ivtransfer_topgate(inttime="2", delaytime=0.2, Vds=-1.2, Vgs_start=-3, Vgs_stop=0, Vgs_step=.1, gatecomp=gatecomp, draincomp=draincomp)
# iv.writefile_ivtransfer(pathname=pathname,devicename=devicename,wafername=wafername,xloc=0,yloc=0,devicenamemodifier='afterwirebonding_-1.2V')
#beforewirebondingaftermount