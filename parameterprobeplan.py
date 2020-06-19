# main wafer probing routine
import visa

from untuned.IP3 import IP3

rm = visa.ResourceManager()                                                         # setup GPIB communications
print rm.list_resources()

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from cascade import CascadeProbeStation                                                    # Cascade wafer prober
from plot import dataPlotter
from device_parameter_request import DeviceParameters
from utilities import *
from IVplot import *

#pna = Pna(rm,16)                                                                    # setup network analyzer
iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
sp = dataPlotter()

# set up of IV and bias voltages
# family of curves
Vds_focstart = 0.
Vds_focstop = -2.
#Vds_focnpts = 21
Vds_focnpts = 21
Vgs_focstart = 0.5
Vgs_focstop = -2.5
#Vgs_focnpts = 31
Vgs_focnpts = 11
# transfer curves
Vds_bias = -2.                                                                      # also used for S-parameter drain bias
Vgs_transstart = 0.5
Vgs_transstop = -2.5
Vgs_transstep = -0.05
# common to both
gatecomp = 0.001                                                                   # gate current compliance in A
draincomp = 0.01                                                                   # drain current compliance in A
Vgs_bias = -2.                                                                      # gate bias for S-parameters

#pathnameIV = "C:/Users/test/python/waferprobe/data"+sub("DC")
#pathnameRF = "C:/Users/test/python/waferprobe/data"+sub("SPAR")
pathname = "C:/Users/test/python/waferprobe/data/wafer2"
#lotname = "test2"
#wafernumber=1
#device = "cfet"

pr = CascadeProbeStation(rm,pathname,"wafer2plan")                                                               # setup Cascade

pr.move_plan_index()					# move to first site

# input intercept point
navg=10                         # number of averages to form measured spectra
fcent = 1E9
fdelta = 100E6
fspanf = 100E3                 # measurement span for each frequency component of the fundamentals
fspand = 10E3                 # measurement span for each frequency component of the fundamentals
ffa = fcent-fdelta/2
ffb= fcent+fdelta/2
fda = ffa-fdelta
fdb = ffb+fdelta
atten = 0.
#pwrstart = -25.
#pwrstop = -8.
pwrstart = -4.
pwrstop = -0.
delpwr=2.
sourcecalfactor=-17.48
sacalfactor = 2.16
sysTOI=50.
fractlinfit=0.95
# sa = SpectrumAnalyzer(rm)
# rfA = Synthesizer(rm,"A")
# rfB= Synthesizer(rm,"B")

IP3m = IP3(rm,atten,navg,pwrstart,pwrstop,delpwr,fcent,fdelta,sacalfactor,sourcecalfactor,sysTOI)
#print "the number of testable die is", cascade.numberofdie()
#print "the number of testable subsites/die is", cascade.numberofsubsites()
#cascade.move_contact()                                       # contact wafer with probes
# step through all sites on wafer

#cascade.dryrun_alltestablesites(1.)                          # perform dry run first and dwell at each site

#nooftestablesites = cascade.numberofdie()*cascade.numberofsubsites()          # total number of testable sites
#print "Will test ",nooftestablesites," devices total"
while pr.get_probingstatus()=="probing wafer":
	print "probing device ", pr.wafername()+"_"+pr.devicename(),"xpos = ",pr.x(),"ypos =",pr.y()
	# probe IV
	iv.measure_ivtransfer_topgate("1", Vds_bias, draincomp, Vgs_transstart, Vgs_transstop, Vgs_transstep, gatecomp)
	fname=(iv.writefile_ivtransfer(pathname,pr.devicename(),pr.wafername(),pr.x(),pr.y()))[0]
	dev = DeviceParameters(pathname,pr.devicename(),'Y_Ids_fitorder 8')
	print abs(dev.Id_T()[-1])

	if abs(dev.Id_T()[-1])>1E-8:		# measure only good devices
		print ("just before TOI")
		IP3m.measureTOI(fractlinfit)
		iv.measure_ivtransferloop_topgate("1", Vds_bias, draincomp, Vgs_transstart, Vgs_transstop, Vgs_transstep, gatecomp)
		iv.writefile_ivtransferloop(pathname,pr.devicename(),pr.wafername(),pr.x(),pr.y())
		iv.measure_ivfoc_topgate("1", Vds_focstart, Vds_focstop, draincomp, Vds_focnpts, Vgs_focstart, Vgs_focstop, gatecomp, Vgs_focnpts)
		iv.writefile_ivfoc(pathname,pr.devicename(),pr.wafername(),pr.x(),pr.y())
		iv.fetbiason_topgate(Vgs_bias, Vds_bias, gatecomp, draincomp)
		#TOIl,TOIh,pfund,pdl,pdh,noisefloor,fitlx,fitly,fithx,fithy,r= IP3m.measureTOI(fractlinfit)

		iv.fetbiasoff()
# 		print ("lower TOI =",TOIl)
# 		print ("upper TOI =",TOIh)
# 		print ("noise floor =",noisefloor)
# 		plotTOI(pfund,pdl,fitlx,fitly,pdh,fithy,noisefloor)
# #	print "after writefile"
		del dev
		dev = DeviceParameters(pathname,pr.devicename(),'Y_Ids_fitorder 8')
		try:
			plotIV(dev,'Y_Ids_fitorder 8')
		except:
			print ("failure to plot "+pr.devicename())
		del dev
	else:
		os.remove(fname)			# remove the tranfer curve file if no good data
		del dev

#	print "after dev"
	# probe S-parameters
#	iv.fetbiason(Vgs_bias,Vds_bias,gatecomp,draincomp)				# bias device
#	pna.pna_getS(16)												# get the S-parameters
#	iv.fetbiason(Vgs_bias,Vds_bias,gatecomp,draincomp)				# bias device again to update currents etc..
#	iv.fetbiasoff()													# bias off
#	[sparf,devname]=pna.writefile_spar(pathname,cascade.devicename(),cascade.wafername(),cascade.x(),cascade.y(),iv.Vds_bias,iv.Id_bias,iv.drainstatus_bias,iv.Vgs_bias,iv.Ig_bias,iv.gatestatus_bias)
#	pl.figure(1,figsize=(8,20))
#	pl.clf()
#	wm = pl.get_current_fig_manager()
#	wm.window.attributes('-topmost',1)
#	sp.smithplotSpar(sparf,0,0)
#	sp.smithplotSpar(sparf,1,1)
#	para = DeviceParameters(pathname,devname)
#	[freqSDB,s11dB,s21dB,s12dB,s22dB]=para.twoport('SDB')
#	sp.spardBplot(freqSDB,s21dB,'S21 (dB)')
#	del para
#	time.sleep(2)
#	print "before nextsite", cascade.get_probingstatus()
	pr.move_nextsite()
#	print "after nextsite", cascade.get_probingstatus()
	plt.clf()
pr.move_separate()
print("done probing")