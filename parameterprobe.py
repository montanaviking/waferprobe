# main wafer probing routine
import visa
import matplotlib.pyplot as plt
import time
import os
import numpy as np
import mwavepy as mv
import pylab as pl
import mwavepy as mv


rm = visa.ResourceManager()                                                         # setup GPIB communications
print rm.list_resources()

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from pna import Pna                                                                 # network analyzer
from cascade import CascadeProbeStation                                                    # Cascade wafer prober
from plot import dataPlotter
from device_parameter_request import DeviceParameters
from utilities import *
pr = CascadeProbeStation(rm)                                                               # setup Cascade wafer prober
pna = Pna(rm,16)                                                                    # setup network analyzer
iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
sp = dataPlotter()

# set up of IV and bias voltages
# family of curves
Vds_focstart = 0.
Vds_focstop = -2.
Vds_focnpts = 21
Vgs_focstart = 0.5
Vgs_focstop = -2.
Vgs_focnpts = 6
# transfer curves
Vds_bias = -2.                                                                      # also used for S-parameter drain bias
Vgs_transstart = 0.5
Vgs_transstop = -2.
Vgs_transstep = -0.05
# common to both
gatecomp = 0.001                                                                   # gate current compliance in A
draincomp = 0.01                                                                   # drain current compliance in A
Vgs_bias = -2.                                                                      # gate bias for S-parameters

#pathnameIV = "C:/Users/test/python/waferprobe/data/IV"
#pathnameRF = "C:/Users/test/python/waferprobe/data/RF"
pathname = "C:/Users/test/python/waferprobe/data"
lotname = "test1"
wafernumber=1
device = "cfet"



print "the number of testable die is", pr.numberofdie()
print "the number of testable subsites/die is", pr.numberofsubsites()
pr.move_contact()                                       # contact wafer with probes
# step through all sites on wafer

#cascade.dryrun_alltestablesites(1.)                          # perform dry run first and dwell at each site

nooftestablesites = pr.numberofdie()*pr.numberofsubsites()          # total number of testable sites
print "Will test ",nooftestablesites," devices total"
for isite in range(0,nooftestablesites):
	print "probing subsite ", pr.subsiteindex(),"in die number ",pr.dieindex()," die X index = ",pr.dieXindex()," die Y index = ",pr.dieYindex(),"xpos = ",pr.x(),"ypos =",pr.y()
	# probe IV
	iv.measure_ivfoc_topgate("1", Vds_focstart, Vds_focstop, draincomp, Vds_focnpts, Vgs_focstart, Vgs_focstop, gatecomp, Vgs_focnpts)
	iv.writefile_ivfoc(pathname,lotname,wafernumber,pr.dieXindex(),pr.dieYindex(),"cfet"+str(pr.subsiteindex()),pr.x(),pr.y())
	iv.measure_ivtransfer_topgate("1", Vds_bias, draincomp, Vgs_transstart, Vgs_transstop, Vgs_transstep, gatecomp)
	iv.writefile_ivtransfer(pathname,lotname,wafernumber,pr.dieXindex(),pr.dieYindex(),"cfet"+str(pr.subsiteindex()),pr.x(),pr.y())
	iv.measure_ivtransferloop_topgate("1", Vds_bias, draincomp, Vgs_transstart, Vgs_transstop, Vgs_transstep, gatecomp)
	iv.writefile_ivtransferloop(pathname,lotname,wafernumber,pr.dieXindex(),pr.dieYindex(),"cfet"+str(pr.subsiteindex()),pr.x(),pr.y())
	# probe S-parameters
	iv.fetbiason_topgate(Vgs_bias, Vds_bias, gatecomp, draincomp)				# bias device
	pna.pna_getS(16)												# get the S-parameters
	iv.fetbiason_topgate(Vgs_bias, Vds_bias, gatecomp, draincomp)				# bias device again to update currents etc..
	iv.fetbiasoff()													# bias off
	[sparf,devname]=pna.writefile_spar(pathname,lotname,wafernumber,pr.dieXindex(),pr.dieYindex(),"cfet"+str(pr.subsiteindex()),pr.x(),pr.y(),Vds_bias,iv.Id_bias,iv.drainstatus_bias,Vgs_bias,iv.Ig_bias,iv.gatestatus_bias)
	pl.figure(1,figsize=(8,20))
	pl.clf()
	wm = pl.get_current_fig_manager()
	wm.window.attributes('-topmost',1)
	sp.smithplotSpar(sparf,0,0)
	sp.smithplotSpar(sparf,1,1)
	para = DeviceParameters(pathname=pathname,devicename=devname)
	#[freqSDB,s11dB,s21dB,s12dB,s22dB]=para.twoport('SDB')

	sp.spardBplot(para.frequencies(),s21dB,'S21 (dB)')
	del para
	pr.move_nextsite()
pr.move_separate()
print("done probing")