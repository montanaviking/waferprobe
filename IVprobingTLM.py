# main wafer probing routine
import visa

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from cascade import CascadeProbeStation                                                    # Cascade wafer prober
from old.plotSmeas import dataPlotter

#pna = Pna(rm,16)                                                                    # setup network analyzer
iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
sp = dataPlotter()

# set up of IV and bias voltages
# family of curves
Vds_focstart = 1.0
Vds_focstop = -3.
Vds_focnpts = 41
Vgs_focstart = 1
Vgs_focstop = -3
Vgs_focnpts =9
# transfer curves
Vds_bias = -1.                                                                     # also used for S-parameter drain bias
Vgs_transstart = 1.
Vgs_transstop = -3.
Vgs_transstep = -0.1
# Sparameters only
#Vgs_bias = -1.                                                                      # gate bias for S-parameters
# common to both
gatecomp = 5E-5                                                                   # gate current compliance in A
#gatecomp = 0.01
draincomp = 0.1                                                                   # drain current compliance in A
#Vgs_bias = -10.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
goodIg=100.E-9                          # gate current must be LESS than this amount to qualify device for further testing
Vgs_validation = -2
Vds_validation = -1

#pathnameIV = "C:/Users/test/python/waferprobe/data"+sub("DC")
#pathnameRF = "C:/Users/test/python/waferprobe/data"+sub("SPAR")
pathname = "C:/Users/test/python/data/A94meas1"
#lotname = "test2"
#wafernumber=1
#device = "cfet"

pr = CascadeProbeStation(rm,pathname,"A94meas1_plan","correction off")                                                               # setup Cascade

pr.move_plan_index()					# move to first site

while pr.get_probingstatus()=="probing wafer":
	if "proberesistancetest" in pr.devicenamesatlevel()[0]:         # then this is a probe resistance test device
		Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=0., Vds0=0.1, Vds1=0.1, gatecomp=gatecomp, draincomp0=0.05, draincomp1=0.05)
		print("testing probe resistance1 =",0.1/Id0val)
		print("testing probe resistance2 =",0.1/Id1val)
		iv.measure_ivfoc_dual_backgate('2', Vds_start=-0.1, Vds_stop=0.1, draincomp=0.1, Vds_npts=11, Vgs_start=0., Vgs_stop=0., gatecomp=gatecomp, Vgs_npts=1)
		iv.writefile_ivfoc_dual(pathname=pathname,devicenames=[pr.devicename()+"gate",pr.devicename()+"drain"],wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())
	else:
		print ("probing device ", pr.wafername()+"_"+pr.devicename(),"xpos = ",pr.x(),"ypos =",pr.y())
		# test to see if the device is any good before committing to a full measurement
		Idval,Igval,Idcompstatval,Igcompstatval=iv.fetbiason_topgate(Vgs_validation, Vds_validation, gatecomp, draincomp)
		print ("Idval, Igval, Idcompstatval, Igcompstatval "+str(Idval)+" "+str(Igval)+" "+Idcompstatval+" "+Igcompstatval)
		if abs(Idval)>goodId and Idcompstatval=="N" and Igcompstatval=="N" and abs(Igval)<goodIg:
			devicegood = True
		else:
			devicegood = False
			print("Bad device")
			#time.sleep(12)
		#devicegood=True
		if devicegood==True:		# measure only good devices
			iv.measure_ivtransferloop_4sweep_topgate(inttime="4",delayfactor=2,filterfactor=2,integrationtime=1, Vds=-0.01, draincomp=draincomp, Vgs_start=Vgs_transstart, Vgs_stop=Vgs_transstop, Vgs_step=Vgs_transstep, gatecomp=gatecomp)
			iv.writefile_ivtransferloop(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y(),devicenamemodifier="Vds-0.01")

			iv.measure_ivtransferloop_4sweep_topgate(inttime="2", Vds=-1.0, draincomp=draincomp, Vgs_start=Vgs_transstart, Vgs_stop=Vgs_transstop, Vgs_step=Vgs_transstep, gatecomp=gatecomp)
			iv.writefile_ivtransferloop(pathname=pathname,devicename=pr.devicename(),wafername=pr.wafername(),xloc_probe=pr.x(),yloc_probe=pr.y())

			iv.measure_ivfoc_backgate(inttime="2", Vds_start=Vds_focstart, Vds_stop=Vds_focstop, draincomp=draincomp, Vds_npts=Vds_focnpts, Vgs_start=Vgs_focstart, Vgs_stop=Vgs_focstop, gatecomp=gatecomp, Vgs_npts=Vgs_focnpts)
			iv.writefile_ivfoc(pathname,pr.devicename(),pr.wafername(),pr.x(),pr.y())

			#iv.fetbiason(Vgs_bias,Vds_bias,gatecomp,draincomp)
			#TOIl,TOIh,pfund,pdl,pdh,noisefloor,fitlx,fitly,fithx,fithy,r= IP3m.measureTOI(fractlinfit)

			# dev = DeviceParameters(pathname=pathname,devicename=cascade.wafername()+"_"+cascade.devicename(),fractVdsfit_Ronfoc=0.1,Y_Ids_fitorder=8)
			# plotIV(dev,'Y_Ids_fitorder 8')
			# try:
			# 	plotIV(dev,'Y_Ids_fitorder 8')
			# except:
			# 	print ("failure to plot "+cascade.devicename())
			# del dev
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
	#print ("before nextsite")#, cascade.get_probingstatus()
	pr.move_nextsite()
	#print ("after nextsite")#, cascade.get_probingstatus()
		#plt.clf()
pr.move_separate()
print("done probing wafer")