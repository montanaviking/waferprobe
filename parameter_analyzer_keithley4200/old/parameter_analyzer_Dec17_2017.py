# setup and usage of the Keithley 4200 semiconductor parameter analyzer
# input is the handle for the VISA resource manager
#from calculated_parameters import *
import time
from writefile_measured import *
import collections as col
#import timeit
from utilities import formatnum, floatequal
import numpy as np
import collections as c
smallfloat=1E-9
settlingtime=0.2                                             # time we allow this semiconductor parameter analyzer to settle after changing voltages
class ParameterAnalyzer:
# set up of parameter analyzer
	def __init__(self,rm,LAN=True):                                  # setup of Keithley parameter analyzer
		                                            # small number used to compare floating point numbers
		self.__LAN=LAN
		self.__largechunk=550000000                             # for large data reads and writes
		self.__midchunk=10000000                              # for small data reads and writes
		self.__smallchunk=10000                                  # for very small data writes and reads
		try:
			if LAN:
				self.__rm=rm
				self.__parameteranalyzer = self.__rm.open_resource('TCPIP0::192.168.1.12::1225::SOCKET') # LAN
				self.__parameteranalyzer.read_termination='\00'
				self.__parameteranalyzer.write_termination='\00'
				opt=self.__parameteranalyzer.query("*OPT?")
				self.__parameteranalyzer.query_delay=1.            # set up query delay to prevent errors
				print(opt)
			else:
				self.t=""
				self.__parameteranalyzer = rm.open_resource('GPIB0::2::INSTR')     # GPIB
		except:
			print ("ERROR on Keithley 4200 semiconductor parameter analyzer: Could not find on GPIB or LAN\n")
			print ("Check Keithley On?, GPIB=2?, and/or KXCI running on Keithley?")
		self.__parameteranalyzer.chunk_size=self.__smallchunk
		if not self.__LAN:
			self.__parameteranalyzer.write("DR1")
			self.__parameteranalyzer.query_delay=.5            # set up query delay to prevent errors
		print (self.__parameteranalyzer.query("ID"))
		self.delaytimemeas=0.01      # sweep delay time to allow settling prior to taking measurement to reduce the probability of Ig compliance at the first measurement point
		self.maxvoltageprobe=40.	# this is the maximum voltage to be appled to the probes or bias Tees

	def __del__(self):
		self.fetbiasoff()									# turn off parameter analyzer when closing out
######################################################################################################################################################
# convert measurement time to integration time in PLCs for 4200
# 0.01<PLC<10
# MT is the measurement time resolution in sec
	def convert_MT_to_PLC(self,MT=None):
		if MT==None: raise ValueError("ERROR! Must set MT")
		#PLC=(MT-0.00728)/0.0681                 # convertion of MT to PLC
		PLC=(MT-0.00675)/0.0671                 # convertion of MT to PLC
		if PLC<0.01:
			PLC=0.01
			print("WARNING! resetting PLC integration time to 0.01 because initial setting was <0.01")
		elif PLC>10.:
			PLC=10.
			print("WARNING! resetting PLC integration time to 10. because initial setting was > 10.")
		#MT=PLC*0.0681+0.00728
		MT=PLC*0.0671+0.00675
		return PLC,MT
######################################################################################################################################################
######################################################################################################################################################
# convert requested quiescent time to hold time setting for 4200
# must also input requested measurement time since the QT includes this
# 0.01<PLC<10
# MT is the measurement time resolution in sec
	def convert_QT_to_HT(self,QT=None,MT=None):
		offset=0.0195
		if MT==None: raise ValueError("ERROR! Must set MT")
		if QT==None: raise ValueError("ERROR! Must set QT")
		holdtime=QT-MT-offset                 # convertion of QT to holdtime
		if holdtime<0:
			holdtime=0.
			print("WARNING! resetting holdtime to 0 because initial setting was <0")
		QT=holdtime+MT+offset
		return holdtime,QT
######################################################################################################################################################
######################################################################################################################################################
# get an MT and PLC value (measurement time) for a given slew rate request (V/sec), Vgsmax-Vgsmin (Vgsspan) and number of Vgs points for the Keithley 4200
# assumes that holdtime, sweep delay, and delay time are all set to zero and also that there is NO autoranging i.e. autoranging is off
# 0.01<PLC<10
# MT is the measurement time resolution in sec
	def get_PLS_MT_fromslewrate(self,slewrate=None,Vgsspan=None,nVgspts=None):
		slewraterequested=slewrate
		if slewrate==None: raise ValueError("ERROR! must give a slewrate target")
		if Vgsspan == None: raise ValueError("ERROR! must give a Vgs span (V)")
		if nVgspts == None: raise ValueError("ERROR! must give a the number of gate bias points in the gate sweep")
		MT=Vgsspan/(float(nVgspts)*slewrate)
		PLC,MT=self.convert_MT_to_PLC(MT=MT)
		slewrate=Vgsspan/(MT*float(nVgspts))
		if not floatequal(slewraterequested,slewrate,0.05): print("WARNING: actual slewrate= "+formatnum(slewrate,precision=2)+"which is not the slewrate is not that requested due to machine constraints")
		return PLC,MT,slewrate                      # return the actual values of PLC, MT, and slewrate within what's possible for the 4200
######################################################################################################################################################
# set constant bias voltages and read drain and gate currents. This is useful for taking S-parameter measurements
# includes ability to allow DUT to stabilize under bias to compensate for drift due to hystersis effects. This can be turned off by setting maxtime=0 so that no hysteresis compensation is done and only one bias measurement is done
# maxchangeId is the maximum change allowed of |Id| between measurements so as to allow Id stabilization to compensate for hysteresis effects
# maxtime is the maximum time in seconds that we spend compensating for hysteresis
# timeiter is the time in seconds between measurements for hystersis compensation
	def fetbiason_topgate(self, Vgs=None, Vds=None, gatecomp=1.E-5, draincomp=0.1,maxchangeId=0.5,maxtime=1.,timeiter=0.2):                 # set constant bias and measure gate and drain currents. Bias is left on at exit
	# set up SMUs for drain and gate
		maxchangeId=abs(maxchangeId)
		self.Vgs_bias=Vgs
		self.Vds_bias=Vds
		if maxchangeId > 1. or maxchangeId < 0.: ValueError("ERROR! Illegal value for maxchangeId must be between 0 and 1")
		self.__parameteranalyzer.clear()
		if abs(Vds)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		if abs(Vgs)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs voltage to bias Tee and/or probes")
		Vdsrange = 1.1E-7
		Vgsrange = 1.1E-7
		self.Vgs_bias = Vgs														# eventually want to read Vgs from the instrument
		self.Vds_bias = Vds														# eventually want to read Vgs from the instrument
		self.__write("EM 1,0")								# set to 4200 mode
		self.__write("IT1;BC;DR0")                               # necessary to prevent problems with subsequent polling in other methods which are called later DR0 must be set!
		self.__write("US DV1;SR1,0")
		self.__write("US DV2;SR2,0")
		self.__write("US DV3;SR3,0")
		self.__write("US DV4;SR4,0")
		self.__write("US DV1,0,"+str(Vgs)+","+str(gatecomp)+",;ST1,1")           # set up gate voltage on SMU1
		self.__write("RG 1,"+str(Vgsrange))
		self.__write("US DV2,0,"+str(Vds)+","+str(draincomp)+",;ST2,1")          # set up drain voltage on SMU2
		self.__write("RG 2,"+str(Vdsrange))
		#time.sleep(timeon)                                              # power supply settling time before measurement to allow charging of system etc...
		#self.__panpoll()
		Id_bias_last=0.                                             # last Id current measured (initialized to zero)
		self.Id_bias=1.                                                  # current Id (initialized to 1 to ensure at least one measurement loop
		starttime = time.time()
		timemeas=starttime
		if maxtime>1E-6: maxtimeset=maxtime
		else: maxtimeset=0.
		while 2.*abs(self.Id_bias-Id_bias_last)/(abs(self.Id_bias)+abs(Id_bias_last)) > maxchangeId and ((timemeas-starttime)<maxtimeset or maxtimeset==0.):
			Id_bias_last=self.Id_bias
			Ialpha = self.__parameteranalyzer.query("TI2")                       # measure drain current
			self.Id_bias = float(Ialpha[3:])                                     # read drain current by stripping off the first 3 characters
			self.drainstatus_bias = Ialpha[:1]                                    # read drain status flag
			Ialpha = self.__parameteranalyzer.query("TI1")             # measure gate current
			self.Ig_bias = float(Ialpha[3:])                                     # read gate current by stripping off the first 3 characters
			self.gatestatus_bias = Ialpha[:1]                                    # read gate status flag
			time.sleep(timeiter)                                              # power supply settling time before measurement to allow charging of system etc...
			timemeas=time.time()                                        # time at measurement
			print("from line 141 parameter_analyzer.py self.Id_bias, Id_bias_last",self.Id_bias,Id_bias_last)
			if maxtimeset==0: break                             # do only one loop
		return self.Id_bias, self.Ig_bias,self.drainstatus_bias,self.gatestatus_bias            # to be used to see if devices are worth measuring further
######################################################################################################################################################
# set requested Id. Preforms a search routine to find the Vgs required to set the requested drain current Id. calls fetbiason_topgate()
# includes ability to allow DUT to stabilize under bias to compensate for drift due to hystersis effects. This can be turned off by setting maxtime=0 so that no hysteresis compensation is done and only one bias measurement is done
# Idrequested_frac is the requested drain current, |Id|, as a fraction of the |Id| measured at the gate voltage VgsatIdmax
# maxchangeId is the maximum change allowed of |Id| between measurements so as to allow Id stabilization to compensate for hysteresis effects. It also determines loop termination, i.e. when the last measured |Id| is within 2*maxchangeId (fraction of last |Id|) the loop terminates
# maxtime is the maximum time in seconds that we spend compensating for hysteresis
# timeiter is the time in seconds between measurements for hystersis compensation
# DUT is assumed to be a P-channel FET type device
# WARNING not yet tested
	def fetbiason_setId_topgate(self, Idrequested_frac=0.9, VgsatIdmax=None, Vgsguess=0.,Vgsmin=None, Vgsmax=None, Vds=None, gatecomp=1.E-5, draincomp=0.1, maxchangeId=0.05,maxtime=10.,timeiter=0.2):                 # set constant bias and measure gate and drain currents. Bias is left on at exit
	# set up SMUs for drain and gate
		if Idrequested_frac==None or VgsatIdmax==None or Vgsmin==None or Vgsmax==None: raise ValueError("ERROR! from fetbiason_setId_topgate() in parameter_analyzer.py, necessary parameters for fetbiason_setId_topgate not specified")
		if Vgsguess<Vgsmin or Vgsguess>Vgsmax: raise ValueError("ERROR! from fetbiason_setId_topgate() in parameter_analyzer.py, Vgsguess outside allowed range")
		maxchangeId=abs(maxchangeId)
		if maxchangeId > 1. or maxchangeId < 0.: ValueError("ERROR! from fetbiason_setId_topgate() in parameter_analyzer.py, Illegal value for maxchangeId must be between 0 and 1")
		self.__parameteranalyzer.clear()
		if abs(Vds)>self.maxvoltageprobe: raise ValueError("ERROR! from fetbiason_setId_topgate() in parameter_analyzer.py, Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		if abs(Vgsmin)>self.maxvoltageprobe or abs(Vgsmax)>self.maxvoltageprobe: raise ValueError("ERROR! from fetbiason_setId_topgate() in parameter_analyzer.py, Attempt to apply > safe Vgs voltage to bias Tee and/or probes")

		Idmax,Ig,drainstatus,gatestatus=self.fetbiason(Vgs=Vgsmin,Vds=Vds,gatecomp=gatecomp,draincomp=draincomp,maxchangeId=maxchangeId,maxtime=maxtime,timeiter=timeiter)         # find max Id=Idmax assuming this is a P-channel FET-type device
		if drainstatus!="N": print("WARNING! from fetbiason_setId_topgate() in parameter_analyzer.py, drain is reaching compliance on |Idmax|")
		if gatestatus!="N": print("WARNING! from fetbiason_setId_topgate() in parameter_analyzer.py, gate is reaching compliance on |Idmax|")
		Idreq=Idrequested_frac*Idmax                            # this is the requested drain current in A
		Id_measured,Ig,drainstatus,gatestatus=self.fetbiason(Vgs=Vgsguess,Vds=Vds,gatecomp=gatecomp,draincomp=draincomp,maxchangeId=maxchangeId,maxtime=maxtime,timeiter=timeiter)         # find max Id at the Vgsguess assuming this is a P-channel FET-type device
		if drainstatus!="N": print("WARNING! from fetbiason_setId_topgate() in parameter_analyzer.py, drain is reaching compliance")
		if gatestatus!="N": print("WARNING! from fetbiason_setId_topgate() in parameter_analyzer.py, gate is reaching compliance")
		#
		VgsId_slope=(Vgsguess-Vgsmin)/(Id_measured-Idmax)
		Vgs_last=Vgsguess
		Vgs=VgsId_slope*(Idreq-Id_measured)+Vgs_last

		while abs(2.*(Id_measured-Idreq)/(Id_measured+Idreq)) > 2.*maxchangeId:
			Id_measured,Ig,drainstatus,gatestatus=self.fetbiason(Vgs=Vgs,Vds=Vds,gatecomp=gatecomp,draincomp=draincomp,maxchangeId=maxchangeId,maxtime=maxtime,timeiter=timeiter)         # find max Id at the Vgsguess assuming this is a P-channel FET-type device
			if drainstatus!="N": print("WARNING! from fetbiason_setId_topgate() loop in parameter_analyzer.py, drain is reaching compliance")
			if gatestatus!="N": print("WARNING! from fetbiason_setId_topgate() loop in parameter_analyzer.py, gate is reaching compliance")
			VgsId_slope=(Vgs-Vgs_last)/(Idreq-Id_measured)
			Vgs_last=Vgs
			Vgs=VgsId_slope*(Idreq-Id_measured)+Vgs_last
			if Vgs>Vgsmax:
				print("WARNING! from fetbiason_setId_topgate() loop in parameter_analyzer.py, Vgs>Vgsmax, break out of loop")
				break
			if Vgs<Vgsmax:
				print("WARNING! from fetbiason_setId_topgate() loop in parameter_analyzer.py, Vgs<Vgsmax, break out of loop")
				break
		return Id_measured,Ig,drainstatus,gatestatus,Vgs_last
######################################################################################################################################################
######################################################################################################################################################
# set constant bias and read drain and gate currents. This is useful for taking S-parameter measurements
# This is set up to backgate devices
	def fetbiason_backgate(self,inttime='2', delayfactor=2,filterfactor=1,integrationtime=20, Vgs=None, Vds=None, gatecomp=1.E-5, draincomp=0.1):                 # set constant bias and measure gate and drain currents. Bias is left on at exit
	# set up SMUs for drain and gate
		if not(inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		self.__parameteranalyzer.clear()
		if abs(Vds)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		Vdsrange = 1.1E-7
		Vgsrange = 1.1E-7
		self.Vgs_bias = Vgs														# eventually want to read Vgs from the instrument
		self.Vds_bias = Vds														# eventually want to read Vgs from the instrument
		self.__write("EM 1,0")								# set to 4200 mode
		#self.__write("IT1;BC;DR0")
		self.__write("IT"+inttime+";BC;DR0")                  # necessary to prevent problems with subsequent polling in other methods which are called later DR0 must be set!
		self.__write("US DV1;SR1,0")
		self.__write("US DV2;SR2,0")
		self.__write("US DV3;SR3,0")
		self.__write("US DV4;SR4,0")
		self.__write("US DV3,0,"+str(Vgs)+","+str(gatecomp)+",;ST3,1")           # set up gate voltage on SMU3
		self.__write("RG 3,"+str(Vgsrange))
		self.__write("US DV2,0,"+str(Vds)+","+str(draincomp)+",;ST2,1")          # set up drain voltage on SMU2
		self.__write("RG 2,"+str(Vdsrange))
		time.sleep(settlingtime)                                              # power supply settling time before measurement to allow charging of system etc...
		#self.__panpoll()
		Ialpha = self.__parameteranalyzer.query("TI2")                       # measure drain current
		self.Id_bias = float(Ialpha[3:])                                     # read drain current by stripping off the first 3 characters
		self.drainstatus_bias = Ialpha[:1]                                    # read drain status flag
		Ialpha = self.__parameteranalyzer.query("TI1")             # measure gate current
		self.Ig_bias = float(Ialpha[3:])                                     # read gate current by stripping off the first 3 characters
		self.gatestatus_bias = Ialpha[:1]                                    # read gate status flag
		time.sleep(settlingtime)                                              # power supply settling time before measurement to allow charging of system etc...
		return self.Id_bias, self.Ig_bias,self.drainstatus_bias,self.gatestatus_bias            # to be used to see if devices are worth measuring further
	# note that the bias is left on at exit
######################################################################################################################################################
######################################################################################################################################################
# DC constant bias for two back-gated FETs at once
# SMU3 is set as the gate bias and should be connected to the chuck
# SMU1 is the FET0 drain bias
# SMU2 is the FET1 drain bias
# set constant bias and read drain and gate currents. This is useful for initial evaluation to determine if FETs should be measured further
	def fetbiason_dual_backgate(self, Vgs=None, Vds0=None, Vds1=None, gatecomp=1E-6, draincomp0=0.1, draincomp1=0.1, Vgsrange=1.1E-7, Vds0range=1.1E-7, Vds1range=1.1E-7):                 # set constant bias and measure gate and drain currents. Bias is left on at exit
		self.Vds0_set=Vds0
		self.Vds1_set=Vds1
		self.Vgs_set=Vgs
	# set up SMUs for drain and gate
		self.__parameteranalyzer.clear()
		if abs(Vds0)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds0 voltage to bias Tee and/or probes")
		if abs(Vds1)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds1 voltage to bias Tee and/or probes")
		self.__write("EM 1,0")								# set to 4200 mode
		self.__write("IT1;BC;DR0")                            # necessary to prevent problems with subsequent polling in other methods which are called later DR0 must be set!
		self.__write("IT1")
		self.__write("US DV1;SR1,0")
		self.__write("US DV2;SR2,0")
		self.__write("US DV3;SR3,0")
		self.__write("US DV4;SR4,0")
		self.__write("US DV3,0,"+str(Vgs)+","+str(gatecomp)+",;ST3,1")           # set up gate voltage on SMU3
		self.__write("RG 3,"+str(Vgsrange))
		self.__write("US DV1,0,"+str(Vds0)+","+str(draincomp0)+",;ST1,1")           # set up drain0 voltage on SMU1
		self.__write("RG 1,"+str(Vds0range))
		self.__write("US DV2,0,"+str(Vds1)+","+str(draincomp1)+",;ST2,1")          # set up drain1 voltage on SMU2
		self.__write("RG 2,"+str(Vds1range))
		time.sleep(settlingtime)                                              # power supply settling time before measurement to allow charging of system etc...

		Ialpha = self.__parameteranalyzer.query("TI1")                       # measure drain0 current
		self.Id0_bias = float(Ialpha[3:])                                     # read drain0 current by stripping off the first 3 characters
		self.drainstatus0_bias = Ialpha[:1]                                    # read drain0 status flag
		Ialpha = self.__parameteranalyzer.query("TI2")                       # measure drain1 current
		self.Id1_bias = float(Ialpha[3:])                                     # read drain1 current by stripping off the first 3 characters
		self.drainstatus1_bias = Ialpha[:1]                                    # read drain status flag
		Ialpha = self.__parameteranalyzer.query("TI3")             			# measure gate current
		self.Ig_bias = float(Ialpha[3:])                                     # read gate current by stripping off the first 3 characters
		self.gatestatus_bias = Ialpha[:1]                                    # read gate status flag
		time.sleep(settlingtime)                                              # power supply settling time before measurement to allow charging of system etc...
		return self.Id0_bias, self.Id1_bias, self.Ig_bias, self.drainstatus0_bias, self.drainstatus1_bias, self.gatestatus_bias            # to be used to see if devices are worth measuring further
	# note that the bias is left on at exit
######################################################################################################################################################
# methods to return values from fetbiason

######################################################################################################################################################
# turn off all SMUs
	def fetbiasoff(self):                                               # turn off fet bias turns off all SMUs
		self.__parameteranalyzer.clear()
	# set up SMUs for drain and gate
		self.__write("US DV1;SR1,0")
		self.__write("US DV2;SR2,0")
		self.__write("US DV3;SR3,0")
		self.__write("US DV4;SR4,0")
		time.sleep(settlingtime)                                         # allow capacitances to discharge etc..
######################################################################################################################################################
# measure IV family of curves on topgated FET type structures
	def measure_ivfoc_topgate(self, inttime='2', delaytime=0.02, Vds_start=None, Vds_stop=None, draincomp=None, gatecomp=None, Vds_npts=None, Vgs_start=None, Vgs_stop=None, Vgs_npts=None, Vgslist=None):
		self.__parameteranalyzer.clear()
		self.__parameteranalyzer.chunk_size=self.__midchunk
		if abs(Vds_start)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds_start voltage to bias Tee and/or probes")
		if abs(Vds_stop)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds_stop voltage to bias Tee and/or probes")
		if abs(Vgs_start)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs_start voltage to bias Tee and/or probes")
		if abs(Vgs_stop)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs_stop voltage to bias Tee and/or probes")
		if Vgslist!=None and max(np.abs(Vgslist))>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs list voltage to bias Tee and/or probes")
		Vds_step = (Vds_stop-Vds_start)/(Vds_npts-1)
		if Vgs_npts>1: Vgs_step = float(Vgs_stop-Vgs_start)/float(Vgs_npts-1)
		else: Vgs_step=0.01           # just one curve but the Vgs step must be > 0 to avoid machine errors

		self.__write("IT"+inttime+";BC;DR1")
		self.__write("EM 1,1")
# set up SMUs for drain and gate
		self.__write("DE")
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")                                               # first undefine all channels

		self.__write("DE;CH1,'VG','IG',1,2")                                                             # gate drive channel definition VAR2
		if Vgslist==None or len(Vgslist)<1:
			self.__write("SS;VP "+formatnum(number=Vgs_start,precision=2)+","+formatnum(number=Vgs_step,precision=2)+","+formatnum(number=Vgs_npts,type='int')+","+formatnum(number=gatecomp,precision=2,nonexponential=False))         # gate drive use standard
		else:       # gate drive from list
			Vgsstrlist=",".join([formatnum(number=l,precision=4,nonexponential=True) for l in Vgslist])     # convert list of gate drive voltage values to one string with gate voltage values separated by ','
			self.__write("SS;VL1,1,"+formatnum(gatecomp,precision=4,nonexponential=False)+","+Vgsstrlist)
		self.__write("DE;CH2,'VD','ID',1,1")                                                              # drain drive channel definition VAR1
		self.__write("SS;VR1,"+formatnum(number=Vds_start,precision=2)+","+formatnum(number=Vds_stop,precision=4,nonexponential=True)+","+formatnum(number=Vds_step,precision=4,nonexponential=False)+","+formatnum(number=draincomp,precision=4,nonexponential=False))         # drain drive
		self.__write(" ".join(["SS;DT",str(delaytime)]))            # add delay time to aid settling and reduce probability of compliance due to charging transients

		self.__write("SM;DM1")
		self.__write("SM;LI 'VD','VG','ID','IG'")
		self.__write("SM;XN 'VD',1,-2.0,0.")                          # configure Keithley 4200 display X axis
		self.__write("SM;YA 'ID',1,-0.1m,0.")                          # configure Keithley 4200 display Y axis
		self.__write("MD;ME1")                                        # trigger for IV measurement
		#self.__write("DR1")
		#self.__parameteranalyzer.wait_for_srq()                                         # wait for IV data sweep to complete
		#print "status byte1", self.__parameteranalyzer.read_stb()
		#print "status byte2", self.__parameteranalyzer.read_stb()
		# measured IV family of curves
		#print "status byte ready to read", self.__parameteranalyzer.read_stb()
		self.__panpoll()

		self.__parameteranalyzer.chunk_size=self.__largechunk
		Id_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'ID'").split(',')]
		Ig_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'IG'").split(',')]
		Vgs_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'VG'").split(',')]
		Vds_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'VD'").split(',')]
		# find status of drain and gate bias e.g. detect compliance

		drainstatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VD'").split(',')]
		gatestatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VG'").split(',')]

		# now split IV curves - make 2D arrays with one index the gate voltage and the second, the drain voltage
		self.Id_foc = []
		self.Ig_foc = []
		self.Vgs_foc = []
		self.Vds_foc = []
		self.drainstatus_foc = []
		self.gatestatus_foc = []
		for iVgs in range(0, Vgs_npts):
			self.Id_foc.append([])
			self.Ig_foc.append([])
			self.Vds_foc.append([])
			self.Vgs_foc.append([])
			self.drainstatus_foc.append([])
			self.gatestatus_foc.append([])
			for iVds in range(0, Vds_npts):
				ii = iVgs*Vds_npts+iVds
				self.Id_foc[iVgs].append(Id_foc1d[ii])
				self.Ig_foc[iVgs].append(Ig_foc1d[ii])
				self.Vds_foc[iVgs].append(Vds_foc1d[ii])
				self.Vgs_foc[iVgs].append(Vgs_foc1d[ii])
				while not (drainstatus_foc1d[ii]=='N' or drainstatus_foc1d[ii]=='L' or drainstatus_foc1d[ii]=='V'  or drainstatus_foc1d[ii]=='X'  or drainstatus_foc1d[ii]=='C' or drainstatus_foc1d[ii]=='T'):
					print ("WARNING! drainstatus_foc1d =", drainstatus_foc1d) #debug
					drainstatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VD'").split(',')]
				self.drainstatus_foc[iVgs].append(drainstatus_foc1d[ii])
				while not (gatestatus_foc1d[ii]=='N' or gatestatus_foc1d[ii]=='L' or gatestatus_foc1d[ii]=='V'  or gatestatus_foc1d[ii]=='X'  or gatestatus_foc1d[ii]=='C' or gatestatus_foc1d[ii]=='T'):
					print ("WARNING! gatestatus_foc1d =", gatestatus_foc1d) #debug
					gatestatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VG'").split(',')]
				self.gatestatus_foc[iVgs].append(gatestatus_foc1d[ii])
				# if not (drainstatus_foc1d[ii]=='N' or drainstatus_foc1d[ii]=='L' or drainstatus_foc1d[ii]=='V'  or drainstatus_foc1d[ii]=='X'  or drainstatus_foc1d[ii]=='C' or drainstatus_foc1d[ii]=='T'):
				# 	print ("drainstatus_foc1d =", drainstatus_foc1d) #debug
				# 	raise ValueError('ERROR drainstatus= '+drainstatus_foc1d)
				# self.drainstatus_foc[iVgs].append(drainstatus_foc1d[ii])
				# if not (gatestatus_foc1d[ii]=='N' or gatestatus_foc1d[ii]=='L' or gatestatus_foc1d[ii]=='V'  or gatestatus_foc1d[ii]=='X'  or gatestatus_foc1d[ii]=='C' or gatestatus_foc1d[ii]=='T'):
				# 	raise ValueError('ERROR gatestatus= '+gatestatus_foc1d)
				# self.gatestatus_foc[iVgs].append(gatestatus_foc1d[ii])
		self.__parameteranalyzer.chunk_size=self.__smallchunk
######################################################################################################################################################
######################################################################################################################################################
# measure IV family of curves on backgated FET type structures
	def measure_ivfoc_backgate(self, inttime='2', delaytime=0.02, delayfactor=2,filterfactor=1,integrationtime=1, Vds_start=None, Vds_stop=None, draincomp=None, Vds_npts=None, Vgs_start=None, Vgs_stop=None, gatecomp=None, Vgs_npts=None):
		self.__parameteranalyzer.clear()
		self.__parameteranalyzer.chunk_size=self.__midchunk
		if not(inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		if abs(Vds_start)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds_start voltage to bias Tee and/or probes")
		if abs(Vds_stop)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds_stop voltage to bias Tee and/or probes")

		Vds_step = (Vds_stop-Vds_start)/(Vds_npts-1)
		if Vgs_npts>1: Vgs_step = float(Vgs_stop-Vgs_start)/float(Vgs_npts-1)
		else: Vgs_step=0.01           # just one curve Vgs step must be > 0 to avoid machine errors
		#self.__write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__write("IT"+inttime+";BC;DR1")
		self.__write("EM 1,1")
# set up SMUs for drain and gate
		self.__write("DE")
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")                                               # first undefine all channels

		self.__write("DE;CH3,'VG','IG',1,2")                                                             # gate drive channel definition VAR2 i.e. SMU3 for gate
		self.__write("SS;VP "+str(Vgs_start)+","+str(Vgs_step)+","+str(Vgs_npts)+","+str(gatecomp))         # gate drive
		self.__write("DE;CH2,'VD','ID',1,1")                                                              # drain drive channel definition VAR1 SMU2
		self.__write("SS;VR1,"+str(Vds_start)+","+str(Vds_stop)+","+str(Vds_step)+","+str(draincomp))         # drain drive
		self.__write(" ".join(["SS;DT",str(delaytime)]))            # add delay time to aid settling and reduce probability of compliance due to charging transients

		self.__write("SM;DM1")
		self.__write("SM;LI 'VD','VG','ID','IG'")
		self.__write("SM;XN 'VD',1,-2.0,0.")                          # configure Keithley 4200 display X axis
		self.__write("SM;YA 'ID',1,-10u,0.")                          # configure Keithley 4200 display Y axis
		self.__write("MD;ME1")                                        # trigger for IV measurement

		self.__panpoll()
		self.__parameteranalyzer.chunk_size=self.__largechunk
		#while 1:
			#try:
		Id_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'ID'").split(',')]
		Ig_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'IG'").split(',')]
		Vgs_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'VG'").split(',')]
		Vds_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'VD'").split(',')]
		# find status of drain and gate bias e.g. detect compliance

		drainstatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VD'").split(',')]
		gatestatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VG'").split(',')]

		# now split IV curves - make 2D arrays with one index the gate voltage and the second, the drain voltage
		self.Id_foc = []
		self.Ig_foc = []
		self.Vgs_foc = []
		self.Vds_foc = []
		self.drainstatus_foc = []
		self.gatestatus_foc = []
		for iVgs in range(0, Vgs_npts):
			self.Id_foc.append([])
			self.Ig_foc.append([])
			self.Vds_foc.append([])
			self.Vgs_foc.append([])
			self.drainstatus_foc.append([])
			self.gatestatus_foc.append([])
			for iVds in range(0, Vds_npts):
				ii = iVgs*Vds_npts+iVds
				self.Id_foc[iVgs].append(Id_foc1d[ii])
				self.Ig_foc[iVgs].append(Ig_foc1d[ii])
				self.Vds_foc[iVgs].append(Vds_foc1d[ii])
				self.Vgs_foc[iVgs].append(Vgs_foc1d[ii])
				while not (drainstatus_foc1d[ii]=='N' or drainstatus_foc1d[ii]=='L' or drainstatus_foc1d[ii]=='V'  or drainstatus_foc1d[ii]=='X'  or drainstatus_foc1d[ii]=='C' or drainstatus_foc1d[ii]=='T'):
					print ("WARNING! drainstatus_foc1d =", drainstatus_foc1d) #debug
					drainstatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VD'").split(',')]
				self.drainstatus_foc[iVgs].append(drainstatus_foc1d[ii])
				while not (gatestatus_foc1d[ii]=='N' or gatestatus_foc1d[ii]=='L' or gatestatus_foc1d[ii]=='V'  or gatestatus_foc1d[ii]=='X'  or gatestatus_foc1d[ii]=='C' or gatestatus_foc1d[ii]=='T'):
					print ("WARNING! gatestatus_foc1d =", gatestatus_foc1d) #debug
					gatestatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VG'").split(',')]
				self.gatestatus_foc[iVgs].append(gatestatus_foc1d[ii])
		self.__parameteranalyzer.chunk_size=self.__smallchunk
######################################################################################################################################################
# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with sweep in one direction
	def measure_ivtransfer_topgate(self, inttime='2', delaytime=0.05, delayfactor=2,filterfactor=1,integrationtime=1, Vds=None,draincomp=None, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=None):
		self.__parameteranalyzer.clear()
		self.__parameteranalyzer.chunk_size=self.__midchunk
		if Vgs_start>=Vgs_stop:
			Vgs_step=-abs(Vgs_step)
		else:
			Vgs_step=abs(Vgs_step)
		# be sure that we are not sweeping Vgs outside of specified range
		# if float(Vgs_start)>=float(Vgs_stop) and Vgs_step>0.:
		# 	raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start>=Vgs_stop. Check parameters")
		# if float(Vgs_start)<float(Vgs_stop) and Vgs_step<0.:
		# 	raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start<Vgs_stop. Check parameters")

		if not(inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		if abs(Vds)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		if abs(Vgs_start)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs_start voltage to bias Tee and/or probes")
		if abs(Vgs_stop)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs_stop voltage to bias Tee and/or probes")
		if abs(Vgs_step)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs_step voltage to bias Tee and/or probes")
		print ("IV tranfercurve start") # debug
		self.__write("EM 1,0")								# set to 4200 mode
		self.__write("IT"+inttime+";BC;DR1")
		self.__write("SM;DM1")

# set up SMUs for drain and gate
		self.__write("DE")
		#self.__write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")     # first undefine all channels

		self.__write("DE;CH1,'VG','IG',1,1")                          # gate drive channel definition set Vgs set to sweep VAR1
		self.__write("SS;VR1,"+",".join([formatnum(number=Vgs_start,precision=4,nonexponential=True),formatnum(Vgs_stop,precision=4,nonexponential=True),formatnum(number=Vgs_step,precision=4,nonexponential=True),formatnum(number=gatecomp,precision=2,nonexponential=False)]))         # gate drive
		self.__write("DE;CH2,'VD','ID',1,3")                         # drain drive channel definition
		self.__write("SS;VC2, "+str(Vds)+","+str(draincomp))         # constant drain voltage drive
		self.__write(" ".join(["SS;DT",str(delaytime)]))

		self.__write("SM;LI 'VD','VG','ID','IG'")
		self.__write("SM;XN 'VG',1,-3.0,0.")                          # configure Keithley 4200 display X axis
		self.__write("SM;YA 'ID',1,-1E-3,0.")                          # configure Keithley 4200 display Y axis
		self.__write("MD;ME1")                                        # trigger for transfer curve measurement
		#self.__parameteranalyzer.wait_for_srq(None)                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
#		print "IV data complete", bin(self.__parameteranalyzer.read_stb())

		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage
		self.__parameteranalyzer.chunk_size=self.__largechunk
		reread = True
		while reread==True:
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'").split(',')
			self.drainstatus_t=[dat[:1] for dat in Vdsraw]
			reread=False
			for x in self.drainstatus_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vds in single-swept transfer curve")
		self.Vds_t=[float(dat[1:]) for dat in Vdsraw]
		# read drain current
		reread=True
		while reread==True:
			Idraw = self.__parameteranalyzer.query("DO 'ID'").split(',')
			self.drainstatus_t=[dat[:1] for dat in Idraw]
			reread=False
			for x in self.drainstatus_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Id in single-swept transfer curve")
		self.Id_t=[float(dat[1:]) for dat in Idraw]
		# read gate voltage
		reread=True
		while reread==True:
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
			self.gatestatus_t=[dat[:1] for dat in Vgsraw]
			reread=False
			for x in self.gatestatus_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vgs in single-swept transfer curve")
		self.Vgs_t=[float(dat[1:]) for dat in Vgsraw]
		# read gate current
		reread=True
		while reread==True:
			Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
			self.gatestatus_t=[dat[:1] for dat in Igraw]
			reread=False
			for x in self.gatestatus_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Ig in single-swept transfer curve")
		self.Ig_t=[float(dat[1:]) for dat in Igraw]
		self.__parameteranalyzer.chunk_size=self.__smallchunk
######################################################################################################################################################
######################################################################################################################################################
# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with sweep in one direction
# for gate voltage applied to the chuck (SMU3)
	def measure_ivtransfer_backgate(self, inttime='2', delaytime=0.02, Iautorange=True,delayfactor='2',filterfactor='1',integrationtime=1, Vds=None, draincomp=None, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=None):
		self.__parameteranalyzer.clear()
		self.__parameteranalyzer.chunk_size=self.__midchunk

		# be sure that we are not sweeping Vgs outside of specified range
		if float(Vgs_start)>=float(Vgs_stop) and Vgs_step>0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start>=Vgs_stop. Check parameters")
		if float(Vgs_start)<float(Vgs_stop) and Vgs_step<0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start<Vgs_stop. Check parameters")

		if not(inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		if abs(Vds)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")

		print ("IV tranfercurve start") # debug
		self.__write("EM 1,0")								# set to 4200 mode
		self.__write("IT"+inttime+";BC;DR1")
		self.__write("SM;DM1")
		self.__write(" ".join(["SS;DT",str(delaytime)]))            # add delay time to aid settling and reduce probability of compliance due to charging transients
# set up SMUs for drain and gate
		self.__write("DE")
		#self.__write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")     # first undefine all channels

		self.__write("DE;CH3,'VG','IG',1,1")                			# gate drive channel definition set to VAR1 sweep
		self.__write("SS;VR1,"+str(Vgs_start)+","+str(Vgs_stop)+","+str(Vgs_step)+","+str(gatecomp))         # gate drive
		self.__write("DE;CH2,'VD','ID',1,3")                         # drain drive channel definition VAR1
		self.__write("SS;VC2, "+str(Vds)+","+str(draincomp))         # constant drain voltage drive

		if custom == True and Iautorange == False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__write("RI 2" + "," + str(draincomp) + "," + str(draincomp))  # allow manual set of right device drain current range to turn off autoranging
			self.__write("RI 3" + "," + str(gatecomp) + "," + str(gatecomp))  # allow manual set of gate current range to turn off autoranging

		self.__write("SM;LI 'VD','VG','ID','IG'")
		self.__write("SM;XN 'VG',1,-2.0,0.")                          # configure Keithley 4200 display X axis
		self.__write("SM;YA 'ID',1,-10u,0.")                          # configure Keithley 4200 display Y axis
		self.__write("MD;ME1")                                        # trigger for transfer curve measurement
		#self.__parameteranalyzer.wait_for_srq(None)                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
		self.__parameteranalyzer.chunk_size=self.__largechunk
#		print "IV data complete", bin(self.__parameteranalyzer.read_stb())

		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage
		reread = True
		while reread==True:
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'").split(',')
			self.drainstatus_t=[dat[:1] for dat in Vdsraw]
			reread=False
			for x in self.drainstatus_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vds in single-swept transfer curve")
		self.Vds_t=[float(dat[1:]) for dat in Vdsraw]
		# read drain current
		reread=True
		while reread==True:
			Idraw = self.__parameteranalyzer.query("DO 'ID'").split(',')
			self.drainstatus_t=[dat[:1] for dat in Idraw]
			reread=False
			for x in self.drainstatus_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Id in single-swept transfer curve")
		self.Id_t=[float(dat[1:]) for dat in Idraw]
		# read gate voltage
		reread=True
		while reread==True:
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
			self.gatestatus_t=[dat[:1] for dat in Vgsraw]
			reread=False
			for x in self.gatestatus_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vgs in single-swept transfer curve")
		self.Vgs_t=[float(dat[1:]) for dat in Vgsraw]
		# read gate current
		reread=True
		while reread==True:
			Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
			self.gatestatus_t=[dat[:1] for dat in Igraw]
			reread=False
			for x in self.gatestatus_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Ig in single-swept transfer curve")
		self.Ig_t=[float(dat[1:]) for dat in Igraw]
		self.__parameteranalyzer.chunk_size=self.__smallchunk
######################################################################################################################################################
		# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with a loop sweep e.g. sweep high to low then low to high
	def measure_ivtransferloop_topgate(self, inttime='2', Iautorange=True, delayfactor=2,filterfactor=0,integrationtime=1, sweepdelay=0.0,holdtime=0.0, Vds=None, draincomp=None, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=None):
		self.__parameteranalyzer.clear()
		self.__parameteranalyzer.chunk_size=self.__midchunk
		if not(inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		if abs(Vds)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		if abs(Vgs_start)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs_start voltage to bias Tee and/or probes")
		if abs(Vgs_stop)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs_stop voltage to bias Tee and/or probes")
		if abs(Vgs_step)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs_step voltage to bias Tee and/or probes")
		print ("IV tranferloop start") # debug
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		nVgs = int(abs((Vgs_stop-Vgs_start)/Vgs_step))+1							# number of gate bias for one direction of Vgs sweep

		# be sure that we are not sweeping Vgs outside of specified range
		if float(Vgs_start)>=float(Vgs_stop) and Vgs_step>0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start>=Vgs_stop. Check parameters")
		if float(Vgs_start)<float(Vgs_stop) and Vgs_step<0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start<Vgs_stop. Check parameters")

		Vgssweeparray= ""
		for ii in range(0,nVgs):												# positive portion of sweep Vgs array
			Vgssweeparray+=str(Vgs_start+ii*Vgs_step)+","
		for ii in range(nVgs-1,-1,-1):											# negative portion of sweep Vgs array
			if ii > 0:
				Vgssweeparray+=str(Vgs_start+ii*Vgs_step)+","
			else:												
				Vgssweeparray+=str(Vgs_start+ii*Vgs_step)						# last element
#		print "Vgssweeparray is ",Vgssweeparray									# debug
		#self.__write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__write("EM 1,0")								# set to 4200 mode
		self.__write("IT"+inttime+";BC;DR1")
		self.__write("SM;DM1")

# set up SMUs for drain and gate
		self.__write("DE")
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")				# first undefine all channels

# configure for dual (loop) sweep
		self.__write("DE;CH1,'VG','IG',1,1")                # gate drive channel definition set Vgs = constant
		self.__write("SS;VL1,1,"+str(gatecomp)+","+Vgssweeparray)         # gate drive for sweep
		self.__write("DE;CH2,'VD','ID',1,3")                         # drain drive channel definition VAR1
		self.__write("SS;VC2, "+str(Vds)+","+str(draincomp))         # constant drain voltage drive
		self.__write("SS;DT ", str(sweepdelay))
		self.__write("SS;HT ", str(holdtime))
		if custom==True and Iautorange==False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__write("RI 2" + "," + str(draincomp) + "," + str(draincomp))  # allow manual set of right device drain current range to turn off autoranging
			self.__write("RI 1" + "," + str(gatecomp) + "," + str(gatecomp))  # allow manual set of gate current range to turn off autoranging

		self.__write("SM;LI 'VD','VG','ID','IG'")
		self.__write("SM;XN 'VG',1,-2.0,0.")                          # configure Keithley 4200 display X axis
		self.__write("SM;YA 'ID',1,-10u,0.")                          # configure Keithley 4200 display Y axis
		starttime = time.time()  # measure sweep time
		self.__write("MD;ME1")                                        # trigger for transfer curve measurement
		#self.__parameteranalyzer.wait_for_srq()                                         # wait for transfer curve data sweep to complete
		self.__panpoll()

		self.__parameteranalyzer.chunk_size=self.__largechunk
		endtime = time.time()-3
		self.elapsed_time=endtime-starttime
		self.Vgsslew = 2.*abs(Vgs_stop - Vgs_start)/(self.elapsed_time)
		print("elapsed time of topgate transferloop =" + formatnum(endtime - starttime) + " Vgs slew rate = " + formatnum(self.Vgsslew, precision=2) + " V/sec")
# get data from loop sweep
# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage
		reread = True
		while reread==True:
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'").split(',')
			print("Vdsraw",Vdsraw)
			drainstatus_transloop=[dat[:1] for dat in Vdsraw]
			reread=False
			for x in drainstatus_transloop:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vds in dual-swept transfer curve")
		Vds_transloop=[float(dat[1:]) for dat in Vdsraw]
		# read drain current
		reread=True
		while reread==True:
			Idraw = self.__parameteranalyzer.query("DO 'ID'").split(',')
			drainstatus_transloop=[dat[:1] for dat in Idraw]
			reread=False
			for x in drainstatus_transloop:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Id in dual-swept transfer curve")
		Id_transloop=[float(dat[1:]) for dat in Idraw]
		# read gate voltage
		reread=True
		while reread==True:
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
			gatestatus_transloop=[dat[:1] for dat in Vgsraw]
			reread=False
			for x in gatestatus_transloop:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vgs in dual-swept transfer curve")
		Vgs_transloop=[float(dat[1:]) for dat in Vgsraw]
		# read gate current
		reread=True
		while reread==True:
			Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
			gatestatus_transloop=[dat[:1] for dat in Igraw]
			reread=False
			for x in gatestatus_transloop:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True

					print("WARNING re-read of Ig in dual-swept transfer curve")
		Ig_transloop=[float(dat[1:]) for dat in Igraw]

		####### now separate out forward and reverse sweeps
		self.Id_tf = []
		self.Ig_tf = []
		self.Vgs_tf = []
		self.Vds_tf = []
		self.drainstatus_tf = []
		self.gatestatus_tf = []
		for ii in range(0,nVgs):												# positive portion of Vgs sweep
			self.Id_tf.append(Id_transloop[ii])
			self.Ig_tf.append(Ig_transloop[ii])
			self.Vgs_tf.append(Vgs_transloop[ii])
			self.Vds_tf.append(Vds_transloop[ii])
			self.drainstatus_tf.append(drainstatus_transloop[ii])
			self.gatestatus_tf.append(gatestatus_transloop[ii])
		self.Id_tr = []
		self.Ig_tr = []
		self.Vgs_tr = []
		self.Vds_tr = []
		self.drainstatus_tr = []
		self.gatestatus_tr = []
		for ii in range(nVgs,len(Id_transloop)):											# negative sweep of Vgs
			self.Id_tr.append(Id_transloop[ii])
			self.Ig_tr.append(Ig_transloop[ii])
			self.Vgs_tr.append(Vgs_transloop[ii])
			self.Vds_tr.append(Vds_transloop[ii])
			self.drainstatus_tr.append(drainstatus_transloop[ii])
			self.gatestatus_tr.append(gatestatus_transloop[ii])
		self.__parameteranalyzer.chunk_size=self.__smallchunk
#######################################################################################################################################################
######################################################################################################################################################
# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with a loop sweep e.g. sweep high to low then low to high
# this allows application of a constant backgate bias when measuring a frontgate transfer curve
	def measure_ivtransferloop_topgate_backgatebias(self, inttime='2', Iautorange=True, delayfactor=2, filterfactor=0, integrationtime=1, sweepdelay=0.0, holdtime=0.0, Vds=None,Vbackgate=0.,  Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=None, draincomp=None, backgatecomp=None):
		self.__parameteranalyzer.clear()
		self.Vbackgate=Vbackgate                        # requested constant backgate voltage
		if not (inttime != '1' or inttime != '2' or inttime != '3' or inttime != '4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime == '4':  # custom timing setting
			inttime = "".join(['4', ',', str(delayfactor), ',', str(filterfactor), ',', str(integrationtime)])
			custom = True
		else:
			custom = False
		if abs(Vds) > self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		if abs(Vgs_start) > self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs_start voltage to bias Tee and/or probes")
		if abs(Vgs_stop) > self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs_stop voltage to bias Tee and/or probes")
		if abs(Vgs_step) > self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs_step voltage to bias Tee and/or probes")
		print("IV tranferloop start")  # debug
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		nVgs = int(abs((Vgs_stop - Vgs_start) / Vgs_step)) + 1  # number of gate bias for one direction of Vgs sweep
		Vgssweeparray = ""

		# be sure that we are not sweeping Vgs outside of specified range
		if float(Vgs_start)>=float(Vgs_stop) and Vgs_step>0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start>=Vgs_stop. Check parameters")
		if float(Vgs_start)<float(Vgs_stop) and Vgs_step<0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start<Vgs_stop. Check parameters")

		for ii in range(0, nVgs):  # positive portion of sweep Vgs array
			Vgssweeparray += str(Vgs_start + ii * Vgs_step) + ","
		for ii in range(nVgs - 1, -1, -1):  # negative portion of sweep Vgs array
			if ii > 0:
				Vgssweeparray += str(Vgs_start + ii * Vgs_step) + ","
			else:
				Vgssweeparray += str(Vgs_start + ii * Vgs_step)  # last element
			#		print "Vgssweeparray is ",Vgssweeparray									# debug
		# self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.write("EM 1,0")  # set to 4200 mode
		self.__parameteranalyzer.write("IT" + inttime + ";BC;DR1")
		self.__parameteranalyzer.write("SM;DM1")

		# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE")
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")  # first undefine all channels

		# configure for dual (loop) sweep
		self.__parameteranalyzer.write("DE;CH1,'VG','IG',1,1")  # gate drive channel definition set Vgs = constant
		self.__parameteranalyzer.write("SS;VL1,1," + str(gatecomp) + "," + Vgssweeparray)  # gate drive for sweep

		self.__parameteranalyzer.write("DE;CH3,'VB','IB',1,3")  # backgate channel definition Vbackgate=constant
		self.__parameteranalyzer.write("SS;VC3, " + str(Vbackgate) + "," + str(backgatecomp))  # constant backgate voltage drive

		self.__parameteranalyzer.write("DE;CH2,'VD','ID',1,3")  # drain drive channel definition VAR1
		self.__parameteranalyzer.write("SS;VC2, " + str(Vds) + "," + str(draincomp))  # constant drain voltage drive


		self.__parameteranalyzer.write("SS;DT ", str(sweepdelay))
		self.__parameteranalyzer.write("SS;HT ", str(holdtime))

		if custom == True and Iautorange == False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain, gate, and backgate current
			self.__parameteranalyzer.write("RI 3" + "," + str(backgatecomp) + "," + str(backgatecomp))  # allow manual set of device backgate current range to turn off autoranging
			self.__parameteranalyzer.write("RI 2" + "," + str(draincomp) + "," + str(draincomp))  # allow manual set of device drain current range to turn off autoranging
			self.__parameteranalyzer.write("RI 1" + "," + str(gatecomp) + "," + str(gatecomp))  # allow manual set of gate current range to turn off autoranging

		self.__parameteranalyzer.write("SM;LI 'VD','VG','ID','IG'")
		self.__parameteranalyzer.write("SM;XN 'VG',1,-2.0,0.")  # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID',1,-10u,0.")  # configure Keithley 4200 display Y axis
		starttime = time.time()  # measure sweep time
		self.__parameteranalyzer.write("MD;ME1")  # trigger for transfer curve measurement
		# self.__parameteranalyzer.wait_for_srq()                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
		endtime = time.time() - 3
		self.elapsed_time = endtime - starttime
		self.Vgsslew = 2. * abs(Vgs_stop - Vgs_start) / (self.elapsed_time)
		print("elapsed time of topgate transferloop =" + formatnum(endtime - starttime) + " Vgs slew rate = " + formatnum(self.Vgsslew, precision=2) + " V/sec")
		# get data from loop sweep
		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage
		reread = True
		while reread == True:
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'").split(',')
			print("from line 689 parameter_analyzer.py Vdsraw", Vdsraw)
			drainstatus_transloop = [dat[:1] for dat in Vdsraw]
			reread = False
			for x in drainstatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vds in dual-swept transfer curve")
		Vds_transloop = [float(dat[1:]) for dat in Vdsraw]
		# read drain current
		reread = True
		while reread == True:
			Idraw = self.__parameteranalyzer.query("DO 'ID'").split(',')
			drainstatus_transloop = [dat[:1] for dat in Idraw]
			reread = False
			for x in drainstatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Id in dual-swept transfer curve")
		Id_transloop = [float(dat[1:]) for dat in Idraw]

		#################
		# read gate voltage
		reread = True
		while reread == True:
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
			gatestatus_transloop = [dat[:1] for dat in Vgsraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vgs in dual-swept transfer curve")
		Vgs_transloop = [float(dat[1:]) for dat in Vgsraw]
		# read gate current
		reread = True
		while reread == True:
			Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
			print("from line 724 parameter_analyzer.py Igraw", Igraw)
			gatestatus_transloop = [dat[:1] for dat in Igraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Ig in dual-swept transfer curve")
		Ig_transloop = [float(dat[1:]) for dat in Igraw]
		########################
		# read backgate voltage
		reread = True
		while reread == True:
			Vbgraw = self.__parameteranalyzer.query("DO 'VB'").split(',')
			print("from line 737 parameter_analyzer.py Vbgraw", Vbgraw)
			backgatestatus_transloop = [dat[:1] for dat in Vbgraw]
			reread = False
			for x in backgatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vbackgate in dual-swept transfer curve")
		Vbg_transloop = [float(dat[1:]) for dat in Vbgraw]
		# read backgate current
		reread = True
		while reread == True:
			Ibgraw = self.__parameteranalyzer.query("DO 'IB'").split(',')
			print("from line 749 parameter_analyzer.py Ibgraw", Ibgraw)
			gatestatus_transloop = [dat[:1] for dat in Ibgraw]
			reread = False
			for x in backgatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Ibackgate in dual-swept transfer curve")
		Ibg_transloop = [float(dat[1:]) for dat in Ibgraw]

		####### now separate out forward and reverse sweeps
		self.Id_tf = []
		self.Ig_tf = []
		self.Ibg_tf=[]
		self.Vgs_tf = []
		self.Vds_tf = []
		self.Vbg_tf=[]
		self.drainstatus_tf = []
		self.gatestatus_tf = []
		self.backgatestatus_tf=[]
		for ii in range(0, nVgs):  # positive portion of Vgs sweep
			self.Id_tf.append(Id_transloop[ii])
			self.Ig_tf.append(Ig_transloop[ii])
			self.Ibg_tf.append(Ibg_transloop[ii])
			self.Vgs_tf.append(Vgs_transloop[ii])
			self.Vds_tf.append(Vds_transloop[ii])
			self.Vbg_tf.append(Vbg_transloop[ii])
			self.drainstatus_tf.append(drainstatus_transloop[ii])
			self.gatestatus_tf.append(gatestatus_transloop[ii])
			self.backgatestatus_tf.append(backgatestatus_transloop[ii])
		self.Id_tr = []
		self.Ig_tr = []
		self.Ibg_tr = []
		self.Vgs_tr = []
		self.Vds_tr = []
		self.Vbg_tr = []
		self.drainstatus_tr = []
		self.gatestatus_tr = []
		self.backgatestatus_tr = []
		for ii in range(nVgs, len(Id_transloop)):  # negative sweep of Vgs
			self.Id_tr.append(Id_transloop[ii])
			self.Ig_tr.append(Ig_transloop[ii])
			self.Ibg_tr.append(Ibg_transloop[ii])
			self.Vgs_tr.append(Vgs_transloop[ii])
			self.Vds_tr.append(Vds_transloop[ii])
			self.Vbg_tr.append(Vbg_transloop[ii])
			self.drainstatus_tr.append(drainstatus_transloop[ii])
			self.gatestatus_tr.append(gatestatus_transloop[ii])
			self.backgatestatus_tr.append(backgatestatus_transloop[ii])
######################################################################################################################################################
# measure hysteresis time domain for a given quiescent time, quiescent voltage, current range can be set
# for both backgate and top gate devices
# Vgsarray is a set of gate voltages to run the test over
# Backgate devices use CH3, SMU3 as the gate while topgated devices use CH1, SMU1 as the gate. In all cases, CH2, SMU2 is used as the drain
	def measure_hysteresistimedomain(self, Vds=None, backgated=True, Vgsquiescent=0., timestep=0.01, timequiescent=1.,timeend=1.,Vgs_start=None, Vgs_stop=None, Vgs_step=None, draincomp=None, gatecomp=None):
		self.__parameteranalyzer.clear()
		self.__parameteranalyzer.chunk_size=self.__largechunk
		if abs(Vds) > self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")        # protect probe from overvoltage
		if backgated==False and (abs(Vgs_start)>self.maxvoltageprobe or abs(Vgs_step)>self.maxvoltageprobe or abs(Vgs_stop)>self.maxvoltageprobe): raise ValueError("ERROR! Attempt to apply > safe Vgs voltage to bias Tee and/or probes")        # protect probe from overvoltage
		self.__parameteranalyzer.clear()
		self.Vdsset=Vds
		self.Vgsquiescent=Vgsquiescent
		PLC,self.timestep = self.convert_MT_to_PLC(MT=timestep)                     # convert timestep (sec) to integration time in PLC (power line cycles) for 4200, self.timestep is the actual timestep whereas timestep is that requested
		holdtime,self.timequiescent=self.convert_QT_to_HT(MT=self.timestep,QT=timequiescent)

		print("from line 829 parameter_analyzer.py, PLC,timestep,holdtime,timequiescent ",PLC,self.timestep,holdtime,self.timequiescent)
		self.ntimepts=int(timeend/self.timestep)                                # find number of time points
		if self.ntimepts>4090:                                                  # maximum allowed number of points in a list sweep is 4096 but set to 4090 to be safe and to allow for the leading time point
			self.ntimepts=4090
			timeend=self.timestep*self.ntimepts
			self.ntimepts = int(timeend/self.timestep)
			print("WARNING! Number of timepoints exceed that allowed for the 4200 so resetting end time to "+formatnum(timeend,precision=2)+" sec")
		# set up input Vgs array to sweep through all gate voltages
		if abs(Vgs_start-Vgs_stop)<=smallfloat or abs(Vgs_step)<=smallfloat:         # then Vgs_start==Vgs_stop so this is just one step
			nVgs=1
		else:
			nVgs = int(abs((Vgs_stop-Vgs_start)/Vgs_step))+1							# number of gate bias for one direction of Vgs sweep
		self.Vgssweeparray= c.deque()
		for ii in range(0,nVgs):												# positive portion of sweep Vgs array
			self.Vgssweeparray.append(Vgs_start+float(ii)*Vgs_step)
		#self.__parameteranalyzer.clear()
		self.__write("EM 1,0")								# set to 4200 mode
		self.__write("BC;DR1")
		self.__write("SM;DM1")
		self.__write("IT4,0,0,"+formatnum(PLC,precision=2,nonexponential=True))              # set filterfactor and delay factor both = 0.
		# set up SMUs for drain and gate
		self.__write("DE")
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")				# first undefine all channels

		if backgated: self.__write("DE;CH3,'VG','IG',1,1")                          # gate drive channel definition set Vgs = constant gate drive on SMU3 to chuck
		else: self.__write("DE;CH1,'VG','IG',1,1")                          # gate drive channel definition set Vgs = constant gate drive on SMU1 to left probe
		self.__write("DE;CH2,'VD','ID',1,3")                         # drain drive channel definition VAR1 on SMU2
		self.__write("SM;WT 0")
		self.__write("SM;IN 0")
		self.__write("SS;VC2, "+str(self.Vdsset)+","+str(draincomp))         # constant drain voltage drive
		self.__write("SS;DT 0")                              # set sweep delay=0
		self.__write("SS;HT "+formatnum(holdtime,precision=1,nonexponential=True))            # set holdtime to set quiescent time
		self.__write("RI 2" + "," + formatnum(draincomp,precision=4,nonexponential=False) + "," + formatnum(draincomp,precision=4,nonexponential=False))  # manual set of right device drain current range to turn off autoranging
		if backgated: self.__write("RI 3" + "," + formatnum(gatecomp,precision=4,nonexponential=False) + "," + formatnum(gatecomp,precision=4,nonexponential=False))  # manual set of gate current range to turn off autoranging
		else: self.__write("RI 1" + "," + formatnum(gatecomp,precision=4,nonexponential=False) + "," + formatnum(gatecomp,precision=4,nonexponential=False))  # manual set of gate current range to turn off autoranging
		self.__write("SR 1,1")
		self.__write("SR 2,1")
		self.__write("SR 3,1")
		self.__write("SR 4,1")

		self.Vds_td=c.deque()
		self.Id_td=c.deque()
		self.Vgs_td=c.deque()
		self.Ig_td=c.deque()
		self.gatestatus_td=c.deque()
		self.drainstatus_td=c.deque()
		self.timestamp_td=c.deque()           # measured and read timestamps for time-domain points (read from the parameter analyzer)
		########### get time-domain Ids for each Vgs ##################################################
		for Vgs in self.Vgssweeparray:
			#Vgsconstantarray="".join([','+formatnum(ii*.2,precision=1,nonexponential=True) for ii in range(1,11)] )           # test debug
			Vgsconstantarray="".join([','+formatnum(Vgs,precision=1,nonexponential=True)]*self.ntimepts)                        # constant-voltage time series for gate bias
			Vgsconstantarray=formatnum(self.Vgsquiescent,precision=2,nonexponential=True)+Vgsconstantarray                      # add quiescent point to time series for gate bias
			#print(" Array")
			# configure for sweep
			if backgated:
				self.__write("SS;VL3,1," + formatnum(gatecomp,precision=4,nonexponential=False) + "," + Vgsconstantarray)  # gate drive voltage step
				#time.sleep(40*self.ntimepts/4090.)
				self.__write("RI 3" + "," + formatnum(gatecomp, precision=4, nonexponential=False) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
				self.__write("RG 3,"+str(gatecomp))  # appears to get rid of autoscaling
			else:
				self.__write("SS;VL1,1," + formatnum(gatecomp,precision=4,nonexponential=False) + "," + Vgsconstantarray)  # gate drive voltage step
				#time.sleep(40*self.ntimepts/4090.)
				self.__write("RI 1" + "," + formatnum(gatecomp, precision=4, nonexponential=False) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
				self.__write("RG 1,"+str(gatecomp))  # appears to get rid of autoscaling
			self.__write("RI 2" + "," + formatnum(draincomp,precision=4,nonexponential=False) + "," + formatnum(draincomp,precision=4,nonexponential=False))  # manual set of right device drain current range to turn off autoranging
			self.__write("RG 2,0.01")  # appears to get rid of autoscaling
			#if backgated: 			else: self.__write("RI 1" + "," + formatnum(gatecomp,precision=4,nonexponential=False) + "," + formatnum(gatecomp,precision=4,nonexponential=False))  # manual set of gate current range to turn off autoranging
			self.__write("SM;LI 'VD','VG','ID','IG'")
			self.__write("SM;XN 'VG',1,-2.0,0.")                          # configure Keithley 4200 display X axis
			self.__write("SM;YA 'ID',1,-10u,0.")                          # configure Keithley 4200 display Y axis
			self.__write("BC")
			self.__write("MD;ME1")                                        # trigger for Id vs time measurement
			pollingtime=2.5*(timequiescent+timeend)                         # total amount of time to wait for data, used sleep rather than true polling due to polling problems
			self.__panpoll(waittime=pollingtime)                                                                # wait for transfer curve data sweep to complete
			#time.sleep(3.)
			# get data from sweep
			# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
			# read drain voltage and timestamps
			reread = True
			while reread == True:
				Vdsraw = self.__parameteranalyzer.query("DO 'VD'").split(',')
				timestampraw = self.__parameteranalyzer.query("DO 'CH2T'").split(',')           # get timestamp data. Assumed that CH2 is always a drain
				drainstatus = [dat[:1] for dat in Vdsraw]
				reread = False
				for x in drainstatus:
					if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
						reread = True
						print("WARNING re-read of Vds in time domain transfer curve")
			self.timestamp_td.append([float(dat)-float(timestampraw[0]) for dat in timestampraw])                      # [iVgs][it] array (Vgs index then time index)
			self.Vds_td.append([float(dat[1:]) for dat in Vdsraw])                              # [iVgs][it] array (Vgs index then time index)
			self.drainstatus_td.append(drainstatus)
			# read drain current
			reread = True
			while reread == True:
				Idraw = self.__parameteranalyzer.query("DO 'ID'").split(',')
				drainstatus=[dat[:1] for dat in Idraw]
				reread = False
				for x in drainstatus:
					if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
						reread = True
						print("WARNING re-read of Id in time domain transfer curve")
			self.Id_td.append([float(dat[1:]) for dat in Idraw])
			# read gate voltage
			reread = True
			while reread == True:
				Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
				gatestatus = [dat[:1] for dat in Vgsraw]
				reread = False
				for x in gatestatus:
					if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
						reread = True
						print("WARNING re-read of Vgs in time domain transfer curve")
			self.Vgs_td.append([float(dat[1:]) for dat in Vgsraw])
			self.gatestatus_td.append(gatestatus)
			# read gate current
			reread = True
			while reread == True:
				Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
				gatestatus=[dat[:1] for dat in Igraw]
				reread = False
				for x in gatestatus:
					if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
						reread = True
						print("WARNING re-read of Ig in time domain transfer curve")
			self.Ig_td.append([float(dat[1:]) for dat in Igraw])
		self.__parameteranalyzer.chunk_size=self.__smallchunk
#######################################################################################################################################################
######################################################################################################################################################
# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with a loop sweep e.g. sweep high to low then low to high
# works for both topgated and backgated measurements
# Backgate devices use CH3, SMU3 as the gate while topgated devices use CH1, SMU1 as the gate. In all cases, CH2, SMU2 is used as the drain
# startstopzero =True - then start at Vgs=0V go to Vgs_start -> Vgs_stop -> Vgs=0V
# if startstopzero=False, then start at Vgs_start and stop at Vgs_stop for the Vgs sweep
	def measure_ivtransferloop_controlledslew(self, backgated=True, startstopzero=False, Vgsslewrate=None, quiescenttime=0., Vds=None, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=None,draincomp=None):
		self.__parameteranalyzer.clear()
		self.startstopzero=startstopzero
		self.quiescenttime=quiescenttime            # minimum quiescent time prior to starting a Vgs sweep, Vds = 0V for this quiescent time too
		Vgs_step = abs(Vgs_step)
		self.__parameteranalyzer.chunk_size=self.__largechunk
		self.Vdsset=Vds
		if abs(Vds) > self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")  # protect probe from overvoltage
		if not backgated and (abs(Vgs_start) > self.maxvoltageprobe or abs(Vgs_step) > self.maxvoltageprobe or abs(Vgs_stop) > self.maxvoltageprobe): raise ValueError("ERROR! Attempt to apply > safe Vgs voltage to bias Tee and/or probes")  # protect probe from overvoltage
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		nVgs = int(abs((Vgs_stop-Vgs_start)/Vgs_step)) + 1  # number of gate bias for one direction of Vgs sweep
		self.fetbiasoff()
		time.sleep(self.quiescenttime)

		# be sure that we are not sweeping Vgs outside of specified range
		# if float(Vgs_start)>=float(Vgs_stop) and Vgs_step>0.:
		# 	raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start>=Vgs_stop. Check parameters")
		# if float(Vgs_start)<float(Vgs_stop) and Vgs_step<0.:
		# 	raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start<Vgs_stop. Check parameters")

		#Vgssweeparray = ""
		if not startstopzero:
			Vgssweeparray1st=[formatnum(v,precision=3) for v in np.linspace(start=Vgs_start,stop=Vgs_stop,num=nVgs)]
			Vgssweeparray2nd=[formatnum(v,precision=3) for v in np.linspace(start=Vgs_stop,stop=Vgs_start,num=nVgs)]
			Vgssweeparray = ",".join([",".join(Vgssweeparray1st),",".join(Vgssweeparray2nd)])

		elif startstopzero:
			if int(abs(Vgs_start)/Vgs_step)-abs(Vgs_start)/Vgs_step > smallfloat or int(abs(Vgs_stop)/Vgs_step)-abs(Vgs_stop)/Vgs_step > smallfloat: raise ValueError("ERROR in Vgs_stop-Vgs_start vs Vgs_step Vgs values must be chosen to include zero and must divide into equal intervals")
			if abs(Vgs_start)/Vgs_start + abs(Vgs_stop)/Vgs_stop > smallfloat: raise ValueError("ERROR! Vgs_start and Vgs_stop must have opposite sign for Vgs sweeps set to start and stop on Vgs=0V where Vgs visits both + and - ranges")
			nVgsstart=int(abs(Vgs_start/Vgs_step))+1
			nVgsstop=int(abs(Vgs_stop/Vgs_step))+1
			Vgssweeparray1st=[formatnum(v,precision=3) for v in np.linspace(start=0.,stop=Vgs_start,num=nVgsstart)]
			Vgssweeparray2nd=[formatnum(v,precision=3) for v in np.linspace(start=Vgs_start,stop=0.,num=nVgsstart)]
			Vgssweeparray3rd=[formatnum(v,precision=3) for v in np.linspace(start=0,stop=Vgs_stop,num=nVgsstop)]
			del Vgssweeparray3rd[0]
			Vgssweeparray4th=[formatnum(v,precision=3) for v in np.linspace(start=Vgs_stop,stop=0.,num=nVgsstop)]
			Vgssweeparray = ",".join([",".join(Vgssweeparray1st),",".join(Vgssweeparray2nd),",".join(Vgssweeparray3rd),",".join(Vgssweeparray4th)])
		else: raise ValueError("ERROR! Illegal value for startstopzero")

		nVgspts=len(Vgssweeparray.split(','))/2                                    # number of gate voltage points between the maximum and minimum gate voltages
		PLC,MT,Vgsslew_notused=self.get_PLS_MT_fromslewrate(slewrate=Vgsslewrate,Vgsspan=abs(Vgs_stop-Vgs_start),nVgspts=nVgspts)        # get PLC which will give target slewrate if possible
		#self.elapsed_time=nVgspts*MT        # total elapsed time of measurement
		self.__write("EM 1,0")  # set to 4200 mode
		self.__write("BC;DR1")
		self.__write("SM;DM1")
		self.__write("SS;DT 0.")
		self.__write("SS;HT 0.")
		self.__write("SM;WT 0.")
		self.__write("SM;IN 0.")
		self.__write("SR 1,0")
		self.__write("SR 2,0")
		self.__write("SR 3,0")
		self.__write("SR 4,0")
		self.__write("IT4,0.,0.,"+formatnum(PLC, precision=2, nonexponential=True))  # set filterfactor and delay factor both = 0.

		# set up SMUs for drain and gate
		self.__write("DE")
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")  # first undefine all channels

		# configure for dual (loop) sweep
		if backgated:
			self.__write("DE;CH3,'VG','IG',1,1")  # gate drive channel definition
			self.__write("SS;VL3,1," + formatnum(gatecomp, precision=4, nonexponential=False) + "," + Vgssweeparray)  # gate drive voltage step
			time.sleep(40.*nVgspts/4090.)
			self.__write("RI 3" + "," + formatnum(gatecomp, precision=4, nonexponential=False) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
			self.__write("RG 3,"+formatnum(number=gatecomp,precision=4,nonexponential=False))  # manual set of gate current range to turn off autoranging
		else:
			self.__write("DE;CH1,'VG','IG',1,1")  # gate drive channel definition set Vgs = constant gate drive on SMU1 to left probe
			self.__write("SS;VL1,1,"+formatnum(gatecomp, precision=4, nonexponential=False) + "," + Vgssweeparray)  # gate drive voltage step
			#time.sleep(20.*nVgs/4090.)
			time.sleep(40.*nVgspts/4090.)
			self.__write("RI 1" + "," + formatnum(gatecomp, precision=4, nonexponential=False) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
			self.__write("RG 1,"+formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
		self.__write("RI 2" + "," + formatnum(number=draincomp, precision=4, nonexponential=False) + "," + formatnum(draincomp, precision=4, nonexponential=False))  # manual set of device drain current range to turn off autoranging
		self.__write("RG 2,"+formatnum(number=draincomp, precision=4, nonexponential=False))                  # appears to get rid of autoscaling

		self.__write("DE;CH2,'VD','ID',1,3")  # drain drive channel definition VAR1 on SMU2
		self.__write("SS;VC2, " + formatnum(self.Vdsset, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=False))  # constant drain voltage drive

		self.__write("SM;LI 'VD','VG','ID','IG'")
		self.__write("SM;XN 'VG',1,-2.0,0.")  # configure Keithley 4200 display X axis
		self.__write("SM;YA 'ID',1,-10u,0.")  # configure Keithley 4200 display Y axis
		#self.__write("BC;DR1")
		self.__write("MD;ME1")  # trigger for transfer curve measurement
		# self.__parameteranalyzer.wait_for_srq()                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
		self.__parameteranalyzer.chunk_size=self.__largechunk
		# get data from loop sweep
		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read timestamp
		# reread = True
		# while reread == True:
		# 	timestamp = self.__parameteranalyzer.query("DO 'CH2T'").split(',')
		# 	print("timestampw", timestamp)
		# 	drainstatus_transloop = [dat[:1] for dat in timestamp]
		# 	reread = False
		# 	for x in drainstatus_transloop:
		# 		if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
		# 			reread = True
		# 			print("WARNING re-read of timestamp in dual-swept transfer curve")
		# timestamp_transloop = [float(dat[1:]) for dat in timestamp]
		# read drain voltage
		reread = True
		while reread == True:
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'").split(',')
			timestampraw = self.__parameteranalyzer.query("DO 'CH2T'").split(',')           # get timestamp data. Assumed that CH2 is always used
			print("Vdsraw", Vdsraw)
			drainstatus_transloop = [dat[:1] for dat in Vdsraw]
			reread = False
			for x in drainstatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vds in dual-swept transfer curve")
		Vds_transloop = [float(dat[1:]) for dat in Vdsraw]
		ts=[float(dat) for dat in timestampraw]
		# read drain current
		reread = True
		while reread == True:
			Idraw = self.__parameteranalyzer.query("DO 'ID'").split(',')
			drainstatus_transloop = [dat[:1] for dat in Idraw]
			reread = False
			for x in drainstatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Id in dual-swept transfer curve")
		Id_transloop = [float(dat[1:]) for dat in Idraw]
		# read gate voltage
		reread = True
		while reread == True:
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
			gatestatus_transloop = [dat[:1] for dat in Vgsraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vgs in dual-swept transfer curve")
		Vgs_transloop = [float(dat[1:]) for dat in Vgsraw]
		# read gate current
		reread = True
		while reread == True:
			Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
			gatestatus_transloop = [dat[:1] for dat in Igraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Ig in dual-swept transfer curve")
		Ig_transloop = [float(dat[1:]) for dat in Igraw]

		####### now separate out forward and reverse sweeps
		self.Id_tf = []
		self.Ig_tf = []
		self.Vgs_tf = []
		self.Vds_tf = []
		self.drainstatus_tf = []
		self.gatestatus_tf = []
		self.timestamp_tf=[]
		self.Id_tr = []
		self.Ig_tr = []
		self.Vgs_tr = []
		self.Vds_tr = []
		self.drainstatus_tr = []
		self.gatestatus_tr = []
		self.timestamp_tr=[]
		if not startstopzero:
			for ii in range(0, nVgs):  # forward portion of Vgs sweep
				self.Id_tf.append(Id_transloop[ii])
				self.Ig_tf.append(Ig_transloop[ii])
				self.Vgs_tf.append(Vgs_transloop[ii])
				self.Vds_tf.append(Vds_transloop[ii])
				self.drainstatus_tf.append(drainstatus_transloop[ii])
				self.gatestatus_tf.append(gatestatus_transloop[ii])
				self.timestamp_tf.append(ts[ii])

			for ii in range(nVgs, len(Id_transloop)):  # reverse sweep of Vgs
				self.Id_tr.append(Id_transloop[ii])
				self.Ig_tr.append(Ig_transloop[ii])
				self.Vgs_tr.append(Vgs_transloop[ii])
				self.Vds_tr.append(Vds_transloop[ii])
				self.drainstatus_tr.append(drainstatus_transloop[ii])
				self.gatestatus_tr.append(gatestatus_transloop[ii])
				self.timestamp_tr.append(ts[ii])
		elif startstopzero:
			for ii in range(len(Vgssweeparray1st), len(Vgssweeparray1st)+len(Vgssweeparray2nd)+len(Vgssweeparray3rd)):  # reverse section of Vgs sweep
				self.Id_tr.append(Id_transloop[ii])
				self.Ig_tr.append(Ig_transloop[ii])
				self.Vgs_tr.append(Vgs_transloop[ii])
				self.Vds_tr.append(Vds_transloop[ii])
				self.drainstatus_tr.append(drainstatus_transloop[ii])
				self.gatestatus_tr.append(gatestatus_transloop[ii])
				self.timestamp_tr.append(ts[ii])

			for ii in range(len(Vgssweeparray1st)+len(Vgssweeparray2nd)+len(Vgssweeparray3rd), len(Id_transloop)):  # 2nd forward section of Vgs sweep
				self.Id_tf.append(Id_transloop[ii])
				self.Ig_tf.append(Ig_transloop[ii])
				self.Vgs_tf.append(Vgs_transloop[ii])
				self.Vds_tf.append(Vds_transloop[ii])
				self.drainstatus_tf.append(drainstatus_transloop[ii])
				self.gatestatus_tf.append(gatestatus_transloop[ii])
				self.timestamp_tf.append(ts[ii])
			for ii in range(0, len(Vgssweeparray1st)):  # 1st forward section of Vgs sweep
				self.Id_tf.append(Id_transloop[ii])
				self.Ig_tf.append(Ig_transloop[ii])
				self.Vgs_tf.append(Vgs_transloop[ii])
				self.Vds_tf.append(Vds_transloop[ii])
				self.drainstatus_tf.append(drainstatus_transloop[ii])
				self.gatestatus_tf.append(gatestatus_transloop[ii])
				self.timestamp_tf.append(ts[ii])
		else: raise ValueError("ERROR! Illegal value for startstopzero")
		self.elapsed_time=max(max(self.timestamp_tf),max(self.timestamp_tr))            # measured total elapsed time of this measurement in sec
		self.Vgsslew=2.*abs(Vgs_stop-Vgs_start)/self.elapsed_time                       # actual measured slew rate in V/sec
		self.__parameteranalyzer.chunk_size=self.__smallchunk
#######################################################################################################################################################
######################################################################################################################################################
# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with a loop sweep e.g. sweep high to low then low to high
# works for both topgated and backgated measurements
# Backgate devices use CH3, SMU3 as the gate while topgated devices use CH1, SMU1 as the gate. In all cases, CH2, SMU2 is used as the drain
# modified Oct 26, 2017 to allow starting and stopping at Vgs=0V
	def measure_ivtransferloop_4sweep_controlledslew(self, backgated=True, quiescenttime=0., startstopzero=False, Vgsslewrate=None,Vds=None, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=None, draincomp=None):
		self.__parameteranalyzer.clear()
		self.__parameteranalyzer.chunk_size=self.__largechunk
		self.Vdsset=Vds
		self.quiescenttime=quiescenttime
		if Vgs_start<=Vgs_stop:
			Vgs_step=abs(Vgs_step)
		else:
			Vgs_step=-abs(Vgs_step)
		if abs(Vds) > self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")  # protect probe from overvoltage
		if not backgated and (abs(Vgs_start) > self.maxvoltageprobe or abs(Vgs_step) > self.maxvoltageprobe or abs(Vgs_stop) > self.maxvoltageprobe): raise ValueError("ERROR! Attempt to apply > safe Vgs voltage to bias Tee and/or probes")  # protect probe from overvoltage
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		nVgs = int(abs((Vgs_stop - Vgs_start) / Vgs_step)) + 1  # number of gate bias for one direction of Vgs sweep
		self.fetbiasoff()
		time.sleep(self.quiescenttime)
		# be sure that we are not sweeping Vgs outside of specified range
		if float(Vgs_start)>=float(Vgs_stop) and Vgs_step>0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start>=Vgs_stop. Check parameters")
		if float(Vgs_start)<float(Vgs_stop) and Vgs_step<0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start<Vgs_stop. Check parameters")
		if not startstopzero:
			Vgssweeparray = ""
			for ii in range(0, nVgs): Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])                 # first sweep
			for ii in range(nVgs - 1, -1, -1): Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])        # 2nd sweep
			for ii in range(0, nVgs): Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])                 # 3rd sweep
			for ii in range(nVgs - 1, -1, -1):
				if ii > 0:Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])                             # 4th sweep
				else: Vgssweeparray += str(Vgs_start + ii * Vgs_step)  # last element
		elif startstopzero:
			if int(abs(Vgs_start)/Vgs_step)-abs(Vgs_start)/Vgs_step > smallfloat or int(abs(Vgs_stop)/Vgs_step)-abs(Vgs_stop)/Vgs_step > smallfloat: raise ValueError("ERROR in Vgs_stop-Vgs_start vs Vgs_step Vgs values must be chosen to include zero and must divide into equal intervals")
			if abs(Vgs_start)/Vgs_start + abs(Vgs_stop)/Vgs_stop > smallfloat: raise ValueError("ERROR! Vgs_start and Vgs_stop must have opposite sign for Vgs sweeps set to start and stop on Vgs=0V where Vgs visits both + and - ranges")
			nVgsstart=int(abs(Vgs_start/Vgs_step))+1
			nVgsstop=int(abs(Vgs_stop/Vgs_step))+1
			Vgssweeparray1st=[formatnum(v,precision=3) for v in np.linspace(start=0.,stop=Vgs_start,num=nVgsstart)]
			Vgssweeparray2nd=[formatnum(v,precision=3) for v in np.linspace(start=Vgs_start,stop=0.,num=nVgsstart)]
			Vgssweeparray3rd=[formatnum(v,precision=3) for v in np.linspace(start=0,stop=Vgs_stop,num=nVgsstop)]
			del Vgssweeparray3rd[0]
			Vgssweeparray4th=[formatnum(v,precision=3) for v in np.linspace(start=Vgs_stop,stop=0.,num=nVgsstop)]
			Vgssweeparray = ",".join([",".join(Vgssweeparray1st),",".join(Vgssweeparray2nd),",".join(Vgssweeparray3rd),",".join(Vgssweeparray4th)])
			# add on a second loop
			del Vgssweeparray1st[0]
			Vgssweeparray = ",".join([Vgssweeparray,",".join(Vgssweeparray1st),",".join(Vgssweeparray2nd),",".join(Vgssweeparray3rd),",".join(Vgssweeparray4th)])
		else: raise ValueError("ERROR! Illegal value for startstopzero")

		nVgspts=int(len(Vgssweeparray.split(','))/4)                                    # number of gate voltage points between the maximum and minimum gate voltages
		PLC,MT,Vgsslewnotused=self.get_PLS_MT_fromslewrate(slewrate=Vgsslewrate,Vgsspan=abs(Vgs_stop-Vgs_start),nVgspts=nVgspts)        # get PLC which will give target slewrate if possible
		#self.elapsed_time=nVgspts*MT        # total elapsed time of measurement
			#		print "Vgssweeparray is ",Vgssweeparray									# debug
		# self.__write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__write("EM 1,0")  # set to 4200 mode
		self.__write("BC;DR1")
		self.__write("SM;DM1")
		self.__write("SS;DT 0.")
		self.__write("SS;HT 0.")
		self.__write("SM;WT 0.")
		self.__write("SM;IN 0.")
		self.__write("SR 1,0")
		self.__write("SR 2,0")
		self.__write("SR 3,0")
		self.__write("SR 4,0")
		self.__write("IT4,0.,0.,"+formatnum(PLC, precision=2, nonexponential=True))  # set filterfactor and delay factor both = 0.

		# set up SMUs for drain and gate
		self.__write("DE")
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")  # first undefine all channels

		# configure for dual (loop) sweep
		if backgated:
			self.__write("DE;CH3,'VG','IG',1,1")  # gate drive channel definition
			self.__write("SS;VL3,1," + formatnum(gatecomp, precision=4, nonexponential=False) + "," + Vgssweeparray)  # gate drive voltage step
			time.sleep(40.*nVgs/4090.)
			self.__write("RI 3" + "," + formatnum(gatecomp, precision=4, nonexponential=False) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
			self.__write("RG 3,"+formatnum(number=gatecomp,precision=4,nonexponential=False))  # manual set of gate current range to turn off autoranging
		else:
			self.__write("DE;CH1,'VG','IG',1,1")  # gate drive channel definition set Vgs = constant gate drive on SMU1 to left probe
			self.__write("SS;VL1,1," + formatnum(gatecomp, precision=4, nonexponential=False) + "," + Vgssweeparray)  # gate drive voltage step
			time.sleep(40.*nVgs/4090.)
			self.__write("RI 1" + "," + formatnum(gatecomp, precision=4, nonexponential=False) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
			self.__write("RG 1,"+formatnum(number=gatecomp,precision=4,nonexponential=False))  # manual set of gate current range to turn off autoranging
		self.__write("RI 2" + "," + formatnum(draincomp, precision=4, nonexponential=False) + "," + formatnum(draincomp, precision=4, nonexponential=False))  # manual set of right device drain current range to turn off autoranging
		self.__write("RG 2,"+formatnum(number=draincomp, precision=4, nonexponential=False))                  # appears to get rid of autoscaling

		self.__write("DE;CH2,'VD','ID',1,3")  # drain drive channel definition VAR1 on SMU2
		self.__write("SS;VC2, " + formatnum(self.Vdsset, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=False))  # constant drain voltage drive

		self.__write("SM;LI 'VD','VG','ID','IG'")
		self.__write("SM;XN 'VG',1,-10.0,10.0")  # configure Keithley 4200 display X axis
		self.__write("SM;YA 'ID',1,-6E-5,0.")  # configure Keithley 4200 display Y axis
		sb=self.__parameteranalyzer.query("SP")
		print("status byte before trigger =",sb)
		self.__write("BC")
		self.__write("DR1")

		# sb=self.__parameteranalyzer.read_stb()
		# print("status byte",sb)
		# time.sleep(0.2)
		# if int(sb)&2: print("WARNING from line 1423 parameter_analyzer.py syntax error")
		self.__write("MD;ME1")  # trigger for transfer curve measurement
		# self.__parameteranalyzer.wait_for_srq()                                         # wait for transfer curve data sweep to complete
		self.__panpoll()


		# get data from loop sweep
		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read timestamp
		# reread = True
		# while reread == True:
		# 	timestamp = self.__parameteranalyzer.query("DO 'CH2T'").split(',')
		# 	print("timestampw", timestamp)
		# 	drainstatus_transloop = [dat[:1] for dat in timestamp]
		# 	reread = False
		# 	for x in drainstatus_transloop:
		# 		if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
		# 			reread = True
		# 			print("WARNING re-read of timestamp in dual-swept transfer curve")
		# timestamp_transloop = [float(dat[1:]) for dat in timestamp]
		# read drain voltage
		reread = True
		while reread == True:
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'").split(',')
			timestampraw = self.__parameteranalyzer.query("DO 'CH2T'").split(',')           # get timestamp data. Assumed that CH2 is always used
			print("Vdsraw", Vdsraw)
			drainstatus_transloop = [dat[:1] for dat in Vdsraw]
			reread = False
			for x in drainstatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vds in 4-swept transfer curve")
		Vds_transloop = [float(dat[1:]) for dat in Vdsraw]
		ts=[float(dat) for dat in timestampraw]
		# read drain current
		reread = True
		while reread == True:
			Idraw = self.__parameteranalyzer.query("DO 'ID'").split(',')
			drainstatus_transloop = [dat[:1] for dat in Idraw]
			reread = False
			for x in drainstatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Id in 4-swept transfer curve")
		Id_transloop = [float(dat[1:]) for dat in Idraw]
		# read gate voltage
		reread = True
		while reread == True:
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
			gatestatus_transloop = [dat[:1] for dat in Vgsraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vgs in 4-swept transfer curve")
		Vgs_transloop = [float(dat[1:]) for dat in Vgsraw]
		# read gate current
		reread = True
		while reread == True:
			Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
			gatestatus_transloop = [dat[:1] for dat in Igraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Ig in 4-swept transfer curve")
		Ig_transloop = [float(dat[1:]) for dat in Igraw]

		self.Id_t1 = []
		self.Ig_t1 = []
		self.Vgs_t1 = []
		self.Vds_t1 = []
		self.drainstatus_t1 = []
		self.gatestatus_t1 = []
		self.timestamp_t1=[]

		self.Id_t2 = []
		self.Ig_t2 = []
		self.Vgs_t2 = []
		self.Vds_t2 = []
		self.drainstatus_t2 = []
		self.gatestatus_t2 = []
		self.timestamp_t2=[]

		self.Id_t3 = []
		self.Ig_t3 = []
		self.Vgs_t3 = []
		self.Vds_t3 = []
		self.drainstatus_t3 = []
		self.gatestatus_t3 = []
		self.timestamp_t3=[]

		self.Id_t4 = []
		self.Ig_t4 = []
		self.Vgs_t4 = []
		self.Vds_t4 = []
		self.drainstatus_t4 = []
		self.gatestatus_t4 = []
		self.timestamp_t4=[]

		####### now separate out different numbered sweeps
		# first sweep of loop
		if not startstopzero:
			for ii in range(0, nVgs):  # 1st Vgs sweep
				self.Id_t1.append(Id_transloop[ii])
				self.Ig_t1.append(Ig_transloop[ii])
				self.Vgs_t1.append(Vgs_transloop[ii])
				self.Vds_t1.append(Vds_transloop[ii])
				self.drainstatus_t1.append(drainstatus_transloop[ii])
				self.gatestatus_t1.append(gatestatus_transloop[ii])
				self.timestamp_t1.append(ts[ii])
			# second sweep of loop

			for ii in range(nVgs, 2*nVgs):  # 2nd sweep of Vgs
				self.Id_t2.append(Id_transloop[ii])
				self.Ig_t2.append(Ig_transloop[ii])
				self.Vgs_t2.append(Vgs_transloop[ii])
				self.Vds_t2.append(Vds_transloop[ii])
				self.drainstatus_t2.append(drainstatus_transloop[ii])
				self.gatestatus_t2.append(gatestatus_transloop[ii])
				self.timestamp_t2.append(ts[ii])
			##### 3rd sweep of loop

			for ii in range(2*nVgs, 3*nVgs):  # 3rd sweep of Vgs
				self.Id_t3.append(Id_transloop[ii])
				self.Ig_t3.append(Ig_transloop[ii])
				self.Vgs_t3.append(Vgs_transloop[ii])
				self.Vds_t3.append(Vds_transloop[ii])
				self.drainstatus_t3.append(drainstatus_transloop[ii])
				self.gatestatus_t3.append(gatestatus_transloop[ii])
				self.timestamp_t3.append(ts[ii])
			##### 4th sweep of loop

			for ii in range(3*nVgs,4*nVgs):  # 4th sweep of Vgs
				self.Id_t4.append(Id_transloop[ii])
				self.Ig_t4.append(Ig_transloop[ii])
				self.Vgs_t4.append(Vgs_transloop[ii])
				self.Vds_t4.append(Vds_transloop[ii])
				self.drainstatus_t4.append(drainstatus_transloop[ii])
				self.gatestatus_t4.append(gatestatus_transloop[ii])
				self.timestamp_t4.append(ts[ii])
		elif startstopzero:       # started and stopped sweep at Vgs=0V
			lenVgssweeparray1st=len(Vgssweeparray1st)+1
			istart2ndloop=lenVgssweeparray1st+len(Vgssweeparray2nd)+len(Vgssweeparray3rd)+len(Vgssweeparray4th)-1
			for ii in range(lenVgssweeparray1st, lenVgssweeparray1st+len(Vgssweeparray2nd)+len(Vgssweeparray3rd)):  # 1st loop voltage swept from start to zero, i.e. 2nd sweep
				self.Id_t2.append(Id_transloop[ii])
				self.Ig_t2.append(Ig_transloop[ii])
				self.Vgs_t2.append(Vgs_transloop[ii])
				self.Vds_t2.append(Vds_transloop[ii])
				self.drainstatus_t2.append(drainstatus_transloop[ii])
				self.gatestatus_t2.append(gatestatus_transloop[ii])
				self.timestamp_t2.append(ts[ii])
			#for ii in range(lenVgssweeparray1st+len(Vgssweeparray2nd)+len(Vgssweeparray3rd), istart2ndloop):  # first loop, 2nd section
			for ii in range(istart2ndloop+lenVgssweeparray1st+len(Vgssweeparray2nd)+len(Vgssweeparray3rd), istart2ndloop+lenVgssweeparray1st+len(Vgssweeparray2nd)+len(Vgssweeparray3rd) + len(Vgssweeparray4th)):  # final half sweep Vgsstop to 0V
				self.Id_t1.append(Id_transloop[ii])
				self.Ig_t1.append(Ig_transloop[ii])
				self.Vgs_t1.append(Vgs_transloop[ii])
				self.Vds_t1.append(Vds_transloop[ii])
				self.drainstatus_t1.append(drainstatus_transloop[ii])
				self.gatestatus_t1.append(gatestatus_transloop[ii])
				self.timestamp_t1.append(ts[ii])
			for ii in range(0, lenVgssweeparray1st):  #  # 1st loop Vds sweep, 1st section
				self.Id_t1.append(Id_transloop[ii])
				self.Ig_t1.append(Ig_transloop[ii])
				self.Vgs_t1.append(Vgs_transloop[ii])
				self.Vds_t1.append(Vds_transloop[ii])
				self.drainstatus_t1.append(drainstatus_transloop[ii])
				self.gatestatus_t1.append(gatestatus_transloop[ii])
				self.timestamp_t1.append(ts[ii])
			# 2nd loop
			for ii in range(istart2ndloop+lenVgssweeparray1st, istart2ndloop+lenVgssweeparray1st+len(Vgssweeparray2nd)+len(Vgssweeparray3rd)):  # 2nd loop 1st section sweep from Vgsstart to Vgsstop
				self.Id_t4.append(Id_transloop[ii])
				self.Ig_t4.append(Ig_transloop[ii])
				self.Vgs_t4.append(Vgs_transloop[ii])
				self.Vds_t4.append(Vds_transloop[ii])
				self.drainstatus_t4.append(drainstatus_transloop[ii])
				self.gatestatus_t4.append(gatestatus_transloop[ii])
				self.timestamp_t4.append(ts[ii])
			#for ii in range(istart2ndloop+lenVgssweeparray1st+len(Vgssweeparray2nd)+len(Vgssweeparray3rd), len(Id_transloop)):  # 2nd reverse Vds sweep, 2nd section
			for ii in range(lenVgssweeparray1st+len(Vgssweeparray2nd)+len(Vgssweeparray3rd), istart2ndloop):  # reverse Vds sweep, 2nd section
				self.Id_t3.append(Id_transloop[ii])
				self.Ig_t3.append(Ig_transloop[ii])
				self.Vgs_t3.append(Vgs_transloop[ii])
				self.Vds_t3.append(Vds_transloop[ii])
				self.drainstatus_t3.append(drainstatus_transloop[ii])
				self.gatestatus_t3.append(gatestatus_transloop[ii])
				self.timestamp_t3.append(ts[ii])
			for ii in range(istart2ndloop+1, istart2ndloop+lenVgssweeparray1st):  #  # 2nd reverse Vds sweep, 1st section
				self.Id_t3.append(Id_transloop[ii])
				self.Ig_t3.append(Ig_transloop[ii])
				self.Vgs_t3.append(Vgs_transloop[ii])
				self.Vds_t3.append(Vds_transloop[ii])
				self.drainstatus_t3.append(drainstatus_transloop[ii])
				self.gatestatus_t3.append(gatestatus_transloop[ii])
				self.timestamp_t3.append(ts[ii])
		else: raise ValueError("ERROR! Illegal value for startstopzero")
		self.elapsed_time=max(max(self.timestamp_t1),max(self.timestamp_t2),max(self.timestamp_t3),max(self.timestamp_t4))            # measured total elapsed time of this measurement in sec
		self.Vgsslew=4.*abs(Vgs_stop-Vgs_start)/self.elapsed_time                       # actual measured slew rate in V/sec
		self.__parameteranalyzer.chunk_size=self.__smallchunk
#######################################################################################################################################################
######################################################################################################################################################
# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with a loop sweep e.g. sweep high to low then low to high
# only for devices which require the gate voltage to be appled on the chuck
	def measure_ivtransferloop_backgate(self, inttime=None, Iautorange=True, delayfactor=2, filterfactor=0, integrationtime=1, sweepdelay=0.0,holdtime=0.0, Vds=None, draincomp=None, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=None):
		self.__parameteranalyzer.clear()
		if inttime == '4':  # custom timing setting
			custom=True
			inttime = "".join(['4', ',', str(delayfactor), ',', str(filterfactor), ',', str(integrationtime)])
		else: custom=False
		if abs(Vds) > self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		print("IV tranferloop start")  # debug
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		nVgs = int(abs((Vgs_stop - Vgs_start) / Vgs_step)) + 1  # number of gate bias for one direction of Vgs sweep

		# be sure that we are not sweeping Vgs outside of specified range
		if float(Vgs_start)>=float(Vgs_stop) and Vgs_step>0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start>=Vgs_stop. Check parameters")
		if float(Vgs_start)<float(Vgs_stop) and Vgs_step<0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start<Vgs_stop. Check parameters")

		Vgssweeparray = ""
		for ii in range(0, nVgs):  # positive portion of sweep Vgs array
			Vgssweeparray += str(Vgs_start + ii * Vgs_step) + ","
		for ii in range(nVgs - 1, -1, -1):  # negative portion of sweep Vgs array
			if ii > 0:
				Vgssweeparray += str(Vgs_start + ii * Vgs_step) + ","
			else:
				Vgssweeparray += str(Vgs_start + ii * Vgs_step)  # last element
			#		print "Vgssweeparray is ",Vgssweeparray									# debug
		# self.__write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__write("EM 1,0")  # set to 4200 mode
		self.__write("BC;DR1")
		self.__write("IT" + inttime)
		self.__write("SM;DM1")

		# set up SMUs for drain and gate
		self.__write("DE")
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")  # first undefine all channels

		# configure for dual (loop) sweep
		self.__write("DE;CH3,'VG','IG',1,1")  # gate drive channel definition set Vgs = constant gate drive on SMU3 to chuck
		self.__write("SS;VL3,1," + str(gatecomp) + "," + Vgssweeparray)  # gate drive for sweep
		self.__write("DE;CH2,'VD','ID',1,3")  # drain drive channel definition VAR1 on SMU2
		self.__write("SS;VC2, " + str(Vds) + "," + str(draincomp))  # constant drain voltage drive
		self.__write("SS;DT ", str(sweepdelay))
		self.__write("SS;HT ", str(holdtime))
		if custom==True and Iautorange==False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__write("RI 2" + "," + str(draincomp) + "," + str(draincomp))  # allow manual set of right device drain current range to turn off autoranging
			self.__write("RI 3" + "," + str(gatecomp) + "," + str(gatecomp))  # allow manual set of gate current range to turn off autoranging

		self.__write("SM;LI 'VD','VG','ID','IG'")
		self.__write("SM;XN 'VG',1,-2.0,0.")  # configure Keithley 4200 display X axis
		self.__write("SM;YA 'ID',1,-10u,0.")  # configure Keithley 4200 display Y axis
		starttime = time.time()  # measure sweep time
		self.__write("MD;ME1")  # trigger for transfer curve measurement
		# self.__parameteranalyzer.wait_for_srq()                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
		endtime = time.time()-3
		self.elapsed_time=endtime-starttime
		self.Vgsslew = 2.*abs(Vgs_stop - Vgs_start)/(self.elapsed_time)
		print("elapsed time of backgate transferloop =" + formatnum(endtime - starttime) + " Vgs slew rate = " + formatnum(self.Vgsslew, precision=2) + " V/sec")
		# get data from loop sweep
		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage
		reread = True
		while reread == True:
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'").split(',')
			print("Vdsraw", Vdsraw)
			drainstatus_transloop = [dat[:1] for dat in Vdsraw]
			reread = False
			for x in drainstatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vds in dual-swept transfer curve")
		Vds_transloop = [float(dat[1:]) for dat in Vdsraw]
		# read drain current
		reread = True
		while reread == True:
			Idraw = self.__parameteranalyzer.query("DO 'ID'").split(',')
			drainstatus_transloop = [dat[:1] for dat in Idraw]
			reread = False
			for x in drainstatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Id in dual-swept transfer curve")
		Id_transloop = [float(dat[1:]) for dat in Idraw]
		# read gate voltage
		reread = True
		while reread == True:
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
			gatestatus_transloop = [dat[:1] for dat in Vgsraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vgs in dual-swept transfer curve")
		Vgs_transloop = [float(dat[1:]) for dat in Vgsraw]
		# read gate current
		reread = True
		while reread == True:
			Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
			gatestatus_transloop = [dat[:1] for dat in Igraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Ig in dual-swept transfer curve")
		Ig_transloop = [float(dat[1:]) for dat in Igraw]

		####### now separate out forward and reverse sweeps
		self.Id_tf = []
		self.Ig_tf = []
		self.Vgs_tf = []
		self.Vds_tf = []
		self.drainstatus_tf = []
		self.gatestatus_tf = []
		for ii in range(0, nVgs):  # positive portion of Vgs sweep
			self.Id_tf.append(Id_transloop[ii])
			self.Ig_tf.append(Ig_transloop[ii])
			self.Vgs_tf.append(Vgs_transloop[ii])
			self.Vds_tf.append(Vds_transloop[ii])
			self.drainstatus_tf.append(drainstatus_transloop[ii])
			self.gatestatus_tf.append(gatestatus_transloop[ii])
		self.Id_tr = []
		self.Ig_tr = []
		self.Vgs_tr = []
		self.Vds_tr = []
		self.drainstatus_tr = []
		self.gatestatus_tr = []
		for ii in range(nVgs, len(Id_transloop)):  # negative sweep of Vgs
			self.Id_tr.append(Id_transloop[ii])
			self.Ig_tr.append(Ig_transloop[ii])
			self.Vgs_tr.append(Vgs_transloop[ii])
			self.Vds_tr.append(Vds_transloop[ii])
			self.drainstatus_tr.append(drainstatus_transloop[ii])
			self.gatestatus_tr.append(gatestatus_transloop[ii])

		#######################################################################################################################################################
# methods to read measured and input parameters for the reverse sweep on a dual-swept transfer curve (might be added)
########################################################################################
######################################################################################################################################################
# measure IV family of curves of two FETs at once using two probes (SMU 1 and 2) as drains and SMU3 as the gate.
# This is usually used for back-gated TLM structures
# CH1 (SMU1) and CH2 (SMU2) are drain1 and drain2 respectively while the gate is CH3 (SMU3)
	def measure_ivfoc_dual_backgate(self, inttime='2', Iautorange=True, delayfactor=2,filterfactor=1,integrationtime=1, Vds_start=None, Vds_stop=None, draincomp=0.1, Vds_npts=None, Vgs_start=None, Vgs_stop=None, gatecomp=5E-5, Vgs_npts=None):
		self.__parameteranalyzer.clear()
		self.__parameteranalyzer.chunk_size=self.__midchunk
		if not(inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		if abs(Vds_start)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds_start voltage to bias Tee and/or probes")
		if abs(Vds_stop)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds_stop voltage to bias Tee and/or probes")

		Vds_step = (Vds_stop-Vds_start)/(Vds_npts-1)
		if Vgs_npts>1: Vgs_step = float(Vgs_stop-Vgs_start)/float(Vgs_npts-1)
		else: Vgs_step=0.01           # just one curve Vgs step must be > 0 to avoid machine errors
		self.__write("IT"+inttime+";BC;DR1")
		self.__write("EM 1,1")
# set up SMUs for drain and gate
		self.__write("DE")
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")                                               # first undefine all channels

		self.__write("DE;CH3,'VG','IG',1,2")                                                             # gate drive channel definition VAR2
		self.__write("SS;VP "+str(Vgs_start)+","+str(Vgs_step)+","+str(Vgs_npts)+","+str(gatecomp))         # gate drive
		#self.__write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients

		self.__write("DE;CH2,'VD1','ID1',1,1")                                                              # drain2 drive channel definition VAR1' locked to drain1 VAR1 sweep
		self.__write("SS;VR1,"+str(Vds_start)+","+str(Vds_stop)+","+str(Vds_step)+","+str(draincomp))         # drain2 drive
		#self.__write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients

		self.__write("DE;CH1,'VD0','ID0',1,4")                                                              # drain0 drive channel definition VAR1
		self.__write("SS;RT 1.0")         																	# drain0 drive
		#self.__write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients

		self.__write("SM;DM1")
		self.__write("SM;LI 'VD0','VG','ID0','IG'")
		self.__write("SM;LI 'VD1','VG','ID1','IG'")
		if custom==True and Iautorange==False:                               # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__write("RI 1" + "," + str(draincomp) + "," + str(draincomp))  # allow manual set of left device drain current range to turn off autoranging
			self.__write("RI 2" + "," + str(draincomp) + "," + str(draincomp))  # allow manual set of right device drain current range to turn off autoranging
			self.__write("RI 3" + "," + str(gatecomp) + "," + str(gatecomp))  # allow manual set of right device drain current range to turn off autoranging
		self.__write("SM;XN 'VD0',1,-3.0,0.")                          # configure Keithley 4200 display X axis
		self.__write("SM;YA 'ID0',1,-10u,0.")                          # configure Keithley 4200 display Y1 axis
		self.__write("SM;YB 'ID1',1,-10u,0.")                          # configure Keithley 4200 display Y2 axis

		self.__write("IT"+inttime+";BC;DR1")
		self.__write("MD;ME1")                                        # trigger for IV measurement

		self.__panpoll()
		self.__parameteranalyzer.chunk_size=self.__largechunk
		Id0_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'ID0'").split(',')]
		Id1_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'ID1'").split(',')]
		Ig_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'IG'").split(',')]
		Vgs_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'VG'").split(',')]
		Vds0_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'VD0'").split(',')]
		Vds1_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'VD1'").split(',')]
		# find status of drain and gate bias e.g. detect compliance

		drainstatus0_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VD0'").split(',')]
		drainstatus1_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VD1'").split(',')]
		gatestatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VG'").split(',')]

		# now split IV curves - make 2D arrays with one index the gate voltage and the second, the drain voltage
		self.Id0_foc = col.deque()
		self.Id1_foc = col.deque()
		self.Ig_foc = col.deque()
		self.Vgs_foc = col.deque()
		self.Vds0_foc = col.deque()
		self.Vds1_foc = col.deque()
		self.drainstatus0_foc = col.deque()
		self.drainstatus1_foc = col.deque()
		self.gatestatus_foc = col.deque()
		for iVgs in range(0, Vgs_npts):
			self.Id0_foc.append([])
			self.Id1_foc.append([])
			self.Ig_foc.append([])
			self.Vds0_foc.append([])
			self.Vds1_foc.append([])
			self.Vgs_foc.append([])
			self.drainstatus0_foc.append([])
			self.drainstatus1_foc.append([])
			self.gatestatus_foc.append([])
			for iVds in range(0, Vds_npts):
				ii = iVgs*Vds_npts+iVds
				self.Id0_foc[iVgs].append(Id0_foc1d[ii])
				self.Id1_foc[iVgs].append(Id1_foc1d[ii])
				self.Ig_foc[iVgs].append(Ig_foc1d[ii])
				self.Vds0_foc[iVgs].append(Vds0_foc1d[ii])
				self.Vds1_foc[iVgs].append(Vds1_foc1d[ii])
				self.Vgs_foc[iVgs].append(Vgs_foc1d[ii])
				while not (drainstatus0_foc1d[ii]=='N' or drainstatus0_foc1d[ii]=='L' or drainstatus0_foc1d[ii]=='V'  or drainstatus0_foc1d[ii]=='X'  or drainstatus0_foc1d[ii]=='C' or drainstatus0_foc1d[ii]=='T'):		# correct HPIB reading errors
					print ("WARNING! drainstatus_foc1d =", drainstatus0_foc1d) #debug
					drainstatus0_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VD0'").split(',')]
				self.drainstatus0_foc[iVgs].append(drainstatus0_foc1d[ii])
				while not (drainstatus1_foc1d[ii]=='N' or drainstatus1_foc1d[ii]=='L' or drainstatus1_foc1d[ii]=='V'  or drainstatus1_foc1d[ii]=='X'  or drainstatus1_foc1d[ii]=='C' or drainstatus1_foc1d[ii]=='T'):		# correct HPIB reading errors
					print ("WARNING! drainstatus_foc1d =", drainstatus1_foc1d) #debug
					drainstatus1_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VD1'").split(',')]
				self.drainstatus1_foc[iVgs].append(drainstatus1_foc1d[ii])
				while not (gatestatus_foc1d[ii]=='N' or gatestatus_foc1d[ii]=='L' or gatestatus_foc1d[ii]=='V'  or gatestatus_foc1d[ii]=='X'  or gatestatus_foc1d[ii]=='C' or gatestatus_foc1d[ii]=='T'):
					print ("WARNING! gatestatus_foc1d =", gatestatus_foc1d) #debug
					gatestatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VG'").split(',')]
				self.gatestatus_foc[iVgs].append(gatestatus_foc1d[ii])
		self.__parameteranalyzer.chunk_size=self.__smallchunk
######################################################################################################################################################
######################################################################################################################################################
# measure forward-swept (one direction only) single transfer curves for two FETs at once using two probes (SMU 1 and 2) as drains and SMU3 as the gate.
# both drains drain0 and drain1 have the same voltage values
# This is usually used for back-gated TLM structures
# CH1 (SMU1) and CH2 (SMU2) are drain1 and drain2 respectively while the gate is CH3 (SMU3)
	def measure_ivtransfer_dual_backgate(self, inttime="2", Iautorange=True, delayfactor=2,filterfactor=1,integrationtime=1, sweepdelay=0.,holdtime=0, Vds=None, draincomp=0.1, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=5E-5):
		self.__parameteranalyzer.clear()
		self.__parameteranalyzer.chunk_size=self.__largechunk

		# be sure that we are not sweeping Vgs outside of specified range
		if float(Vgs_start)>=float(Vgs_stop) and Vgs_step>0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start>=Vgs_stop. Check parameters")
		if float(Vgs_start)<float(Vgs_stop) and Vgs_step<0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start<Vgs_stop. Check parameters")

		if not (inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		if abs(Vds)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		print ("IV tranfercurve dual device start") # debug
		self.__write("EM 1,0")								# set to 4200 mode
		self.__write("IT"+inttime+";BC;DR1")
		self.__write("SM;DM1")

# set up SMUs for drain and gate
		self.__write("DE")
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")     # first undefine all channels

		self.__write("DE;CH3,'VG','IG',1,1")                			# gate drive channel definition
		self.__write("SS;VR1, "+"".join([str(Vgs_start), ",", str(Vgs_stop), ",", str(Vgs_step), ",", str(gatecomp)]))         # gate drive

		self.__write("DE;CH1,'VD0','ID0',1,3")                         # drain drive channel definition VAR1
		self.__write("SS;VC1, "+"".join([str(Vds), ",", str(draincomp)]))         # constant drain voltage drive

		self.__write("DE;CH2,'VD1','ID1',1,3")                         # drain drive channel definition VAR1
		self.__write("SS;VC2, "+"".join([str(Vds), ",", str(draincomp)]))         # constant drain voltage drive

		self.__write("SS;DT ", str(sweepdelay))
		self.__write("SS;HT ", str(holdtime))
		if custom==True and Iautorange==False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__write("RI 1" + "," + str(draincomp) + "," + str(draincomp))  # allow manual set of left device drain current range to turn off autoranging
			self.__write("RI 2" + "," + str(draincomp) + "," + str(draincomp))  # allow manual set of right device drain current range to turn off autoranging
			self.__write("RI 3" + "," + str(gatecomp) + "," + str(gatecomp))  # allow manual set of gate current range to turn off autoranging
		# else:
		# 	self.__parameteranalyzer.write("US;DV3,0")             # set to current measurement autorange for channel 3 (gate)
		# 	self.__parameteranalyzer.write("US;DV1,0")             # set to current measurement autorange for channel 1 (Id0)
		# 	self.__parameteranalyzer.write("US;DV2,0")             # set to current measurement autorange for channel 2 (Id1)

		self.__write("SM;LI 'VD0','VG','ID0','IG'")
		self.__write("SM;LI 'VD0','VG','ID1','IG'")
		self.__write("SM;XN 'VG',1,-3.0,0.")                          # configure Keithley 4200 display X axis
		self.__write("SM;YA 'ID0',1,-10u,0.")                          # configure Keithley 4200 display Y axis
		self.__write("SM;YB 'ID1',1,-10u,0.")                          # configure Keithley 4200 display Y axis
		self.__write("IT"+inttime+";BC;DR1")
		starttime=time.time()                                                      # measure sweep time
		self.__write("MD;ME1")                                        # trigger for transfer curve measurement
		#self.__parameteranalyzer.wait_for_srq(None)                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
		self.__parameteranalyzer.chunk_size=self.__largechunk
		endtime=time.time()-3
		self.Vgsslew=abs(Vgs_stop-Vgs_start)/(endtime-starttime)
		self.elapsed_time=endtime-starttime
		print("elapsed time of dual backgate transferloop ="+formatnum(self.elapsed_time)+" Vgs slew rate = "+formatnum(self.Vgsslew,precision=2)+" V/sec")
#		print "IV data complete", bin(self.__parameteranalyzer.read_stb())

		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain 0 voltage
		reread = True
		while reread==True:
			Vds0raw = self.__parameteranalyzer.query("DO 'VD0'").split(',')
			self.drain0status_t=[dat[:1] for dat in Vds0raw]
			reread=False
			for x in self.drain0status_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vds0 in single-swept transfer curve")
		self.Vds0_t=[float(dat[1:]) for dat in Vds0raw]
		# read drain 0 current
		reread=True
		while reread==True:
			Id0raw = self.__parameteranalyzer.query("DO 'ID0'").split(',')
			self.drain0status_t=[dat[:1] for dat in Id0raw]
			reread=False
			for x in self.drain0status_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Id0 in single-swept transfer curve")
		self.Id0_t=[float(dat[1:]) for dat in Id0raw]
		# read drain 1 voltage
		reread = True
		while reread==True:
			Vds1raw = self.__parameteranalyzer.query("DO 'VD1'").split(',')
			self.drain1status_t=[dat[:1] for dat in Vds1raw]
			reread=False
			for x in self.drain1status_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vds1 in single-swept transfer curve")
		self.Vds1_t=[float(dat[1:]) for dat in Vds1raw]
		# read drain 1 current
		reread=True
		while reread==True:
			Id1raw = self.__parameteranalyzer.query("DO 'ID1'").split(',')
			self.drain1status_t=[dat[:1] for dat in Id1raw]
			reread=False
			for x in self.drain1status_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Id1 in single-swept transfer curve")
		self.Id1_t=[float(dat[1:]) for dat in Id1raw]
		# read gate voltage
		reread=True
		while reread==True:
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
			self.gatestatus_t=[dat[:1] for dat in Vgsraw]
			reread=False
			for x in self.gatestatus_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vgs in single-swept transfer curve")
		self.Vgs_t=[float(dat[1:]) for dat in Vgsraw]
		# read gate current
		reread=True
		while reread==True:
			Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
			self.gatestatus_t=[dat[:1] for dat in Igraw]
			reread=False
			for x in self.gatestatus_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Ig in single-swept transfer curve")
		self.Ig_t=[float(dat[1:]) for dat in Igraw]
		self.__parameteranalyzer.chunk_size=self.__smallchunk
######################################################################################################################################################
######################################################################################################################################################
# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with a loop sweep e.g. sweep high to low then low to high
# both drains drain0 and drain1 have the same voltage values
# This is usually used for back-gated TLM structures
# CH1 (SMU1) and CH2 (SMU2) are drain1 and drain2 respectively while the gate is CH3 (SMU3)
	def measure_ivtransferloop_dual_backgate(self, inttime="2", Iautorange=True, delayfactor=2, filterfactor=1,integrationtime=1, sweepdelay=0.,holdtime=0, Vds=None, draincomp=0.1, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=5E-5):
		self.__parameteranalyzer.clear()

		if not(inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		if abs(Vds)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		print ("IV tranferloop dual device start") # debug
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		nVgs = int(abs((Vgs_stop-Vgs_start)/Vgs_step))+1							# number of gate bias for one direction of Vgs sweep

		# be sure that we are not sweeping Vgs outside of specified range
		if float(Vgs_start)>=float(Vgs_stop) and Vgs_step>0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start>=Vgs_stop. Check parameters")
		if float(Vgs_start)<float(Vgs_stop) and Vgs_step<0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start<Vgs_stop. Check parameters")

		Vgssweeparray= ""
		for ii in range(0,nVgs):												# positive portion of sweep Vgs array
			Vgssweeparray+=str(Vgs_start+ii*Vgs_step)+","
		for ii in range(nVgs-1,-1,-1):											# negative portion of sweep Vgs array
			if ii > 0:
				Vgssweeparray+=str(Vgs_start+ii*Vgs_step)+","
			else:
				Vgssweeparray+=str(Vgs_start+ii*Vgs_step)						# last element
#		print "Vgssweeparray is ",Vgssweeparray									# debug
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.write("EM 1,0")								# set to 4200 mode
		self.__parameteranalyzer.write("IT"+inttime+";BC;DR1")
		self.__parameteranalyzer.write("SM;DM1")

# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE")
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")				# first undefine all channels

# configure for dual (loop) sweep for two devices at once
		self.__parameteranalyzer.write("DE;CH3,'VG','IG',1,1")                			# gate drive channel definition
		self.__parameteranalyzer.write("SS;VL3,1,"+"".join([str(gatecomp), ",", Vgssweeparray]))         # gate drive for sweep
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients

		self.__parameteranalyzer.write("DE;CH1,'VD0','ID0',1,3")                         # drain0 drive channel definition
		self.__parameteranalyzer.write("SS;VC1, "+str(Vds)+","+str(draincomp))         # constant drain voltage drive
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients

		self.__parameteranalyzer.write("DE;CH2,'VD1','ID1',1,3")                         # drain1 drive channel definition
		self.__parameteranalyzer.write("SS;VC2, "+str(Vds)+","+str(draincomp))         # constant drain voltage drive
		self.__parameteranalyzer.write("SS;DT ", str(sweepdelay))
		self.__parameteranalyzer.write("SS;HT ", str(holdtime))
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		if custom==True and Iautorange==False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__parameteranalyzer.write("RI 1" + "," + str(draincomp) + "," + str(draincomp))  # allow manual set of left device drain current range to turn off autoranging
			self.__parameteranalyzer.write("RI 2" + "," + str(draincomp) + "," + str(draincomp))  # allow manual set of right device drain current range to turn off autoranging
			self.__parameteranalyzer.write("RI 3" + "," + str(gatecomp) + "," + str(gatecomp))  # allow manual set of gate current range to turn off autoranging
		else:
			self.__parameteranalyzer.write("US;DI3,0")             # set to current measurement autorange for channel 3 (gate)
			self.__parameteranalyzer.write("US;DI1,0")             # set to current measurement autorange for channel 1 (Id0)
			self.__parameteranalyzer.write("US;DI2,0")             # set to current measurement autorange for channel 2 (Id1)
		self.__parameteranalyzer.write("SM;LI 'VD0','VG','ID0','IG'")
		self.__parameteranalyzer.write("SM;LI 'VD1','VG','ID1','IG'")
		self.__parameteranalyzer.write("SM;XN 'VG',1,-3.0,0.")                          # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID0',1,-10u,0.")                          # configure Keithley 4200 display Y1 axis
		self.__parameteranalyzer.write("SM;YB 'ID1',1,-10u,0.")                          # configure Keithley 4200 display Y2 axis
		starttime=time.time()                                                      # measure sweep time
		print("from line 986 parameter_analyzer.py triggering",starttime)
		self.__parameteranalyzer.write("MD;ME1")                                        # trigger for transfer curve measurement
		#self.__parameteranalyzer.wait_for_srq()                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
		endtime=time.time()-3
		print("from line 986 parameter_analyzer.py endmeasure",endtime)
		self.Vgsslew=2.*abs(Vgs_stop-Vgs_start)/(endtime-starttime)
		self.elapsed_time=endtime-starttime
		print("elapsed time of ivtransferloop_dual_backgate() ="+formatnum(self.elapsed_time)+" Vgs slew rate = "+formatnum(self.Vgsslew,precision=2)+" V/sec")
		print("Vgs_start, Vgs_stop",Vgs_start,Vgs_stop)
# get data from loop sweep
# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain0 voltage
		reread = True
		while reread==True:
			Vds0raw = self.__parameteranalyzer.query("DO 'VD0'").split(',')
			print("Vds0raw",Vds0raw)
			drain0status_transloop=[dat[:1] for dat in Vds0raw]
			reread=False
			for x in drain0status_transloop:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vds0 in dual-swept transfer curve")
		Vds0_transloop=[float(dat[1:]) for dat in Vds0raw]
		# read drain0 current
		reread=True
		while reread==True:
			Id0raw = self.__parameteranalyzer.query("DO 'ID0'").split(',')
			drain0status_transloop=[dat[:1] for dat in Id0raw]
			reread=False
			for x in drain0status_transloop:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Id0 in dual-swept transfer curve")
		Id0_transloop=[float(dat[1:]) for dat in Id0raw]

		# read drain1 voltage
		reread = True
		while reread==True:
			Vds1raw = self.__parameteranalyzer.query("DO 'VD1'").split(',')
			print("Vds1raw",Vds1raw)
			drain1status_transloop=[dat[:1] for dat in Vds1raw]
			reread=False
			for x in drain1status_transloop:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vds0 in dual-swept transfer curve")
		Vds1_transloop=[float(dat[1:]) for dat in Vds1raw]
		# read drain1 current
		reread=True
		while reread==True:
			Id1raw = self.__parameteranalyzer.query("DO 'ID1'").split(',')
			drain1status_transloop=[dat[:1] for dat in Id1raw]
			reread=False
			for x in drain1status_transloop:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Id1 in dual-swept transfer curve")
		Id1_transloop=[float(dat[1:]) for dat in Id1raw]

		# read gate voltage
		reread=True
		while reread==True:
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
			gatestatus_transloop=[dat[:1] for dat in Vgsraw]
			reread=False
			for x in gatestatus_transloop:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vgs in dual-swept transfer curve")
		Vgs_transloop=[float(dat[1:]) for dat in Vgsraw]
		# read gate current
		reread=True
		while reread==True:
			Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
			gatestatus_transloop=[dat[:1] for dat in Igraw]
			reread=False
			for x in gatestatus_transloop:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Ig in dual-swept transfer curve")
		Ig_transloop=[float(dat[1:]) for dat in Igraw]

		####### now separate out forward and reverse sweeps
		self.Id0_tf = []
		self.Id1_tf = []
		self.Ig_tf = []
		self.Vgs_tf = []
		self.Vds0_tf = []
		self.Vds1_tf = []
		self.drain0status_tf = []
		self.drain1status_tf = []
		self.gatestatus_tf = []
		for ii in range(0,nVgs):												# positive portion of Vgs sweep
			self.Id0_tf.append(Id0_transloop[ii])
			self.Id1_tf.append(Id1_transloop[ii])
			self.Ig_tf.append(Ig_transloop[ii])
			self.Vgs_tf.append(Vgs_transloop[ii])
			self.Vds0_tf.append(Vds0_transloop[ii])
			self.drain0status_tf.append(drain0status_transloop[ii])
			self.Vds1_tf.append(Vds1_transloop[ii])
			self.drain1status_tf.append(drain1status_transloop[ii])
			self.gatestatus_tf.append(gatestatus_transloop[ii])
		self.Id0_tr = []
		self.Id1_tr = []
		self.Ig_tr = []
		self.Vgs_tr = []
		self.Vds0_tr = []
		self.Vds1_tr = []
		self.drain0status_tr = []
		self.drain1status_tr = []
		self.gatestatus_tr = []
		for ii in range(nVgs,len(Id0_transloop)):											# negative sweep of Vgs
			self.Id0_tr.append(Id0_transloop[ii])
			self.Id1_tr.append(Id1_transloop[ii])
			self.Ig_tr.append(Ig_transloop[ii])
			self.Vgs_tr.append(Vgs_transloop[ii])
			self.Vds0_tr.append(Vds0_transloop[ii])
			self.drain0status_tr.append(drain0status_transloop[ii])
			self.Vds1_tr.append(Vds1_transloop[ii])
			self.drain1status_tr.append(drain1status_transloop[ii])
			self.gatestatus_tr.append(gatestatus_transloop[ii])

#######################################################################################################################################################
######################################################################################################################################################
# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with a loop sweep e.g. sweep high to low then low to high
# works for backgated measurements only
# Backgate devices use CH3, SMU3 as the gate  CH1 SMU1 and CH2, SMU2 are used as the drains
	def measure_ivtransferloop_dual_controlledslew_backgated(self, Vgsslewrate=None, Vds=None, draincomp=None, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=None,startstopatzero=False):
		self.__parameteranalyzer.clear()
		self.__parameteranalyzer.chunk_size=self.__midchunk
		self.Vdsset = Vds
		if abs(Vds) > self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")  # protect probe from overvoltage
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		nVgs = int(abs((Vgs_stop-Vgs_start)/Vgs_step))+1							# number of gate bias for one direction of Vgs sweep

		# be sure that we are not sweeping Vgs outside of specified range
		if float(Vgs_start)>=float(Vgs_stop) and Vgs_step>0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start>=Vgs_stop. Check parameters")
		if float(Vgs_start)<float(Vgs_stop) and Vgs_step<0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start<Vgs_stop. Check parameters")

		Vgssweeparray= ""
		if not startstopatzero:  # if startstopatzero is True then we start and stop the sweep as near to Vgs=0 as possible
			for ii in range(0,nVgs):												# positive portion of sweep Vgs array
				#Vgssweeparray+=str(Vgs_start+ii*Vgs_step)+","
				Vgssweeparray="".join([Vgssweeparray,str(Vgs_start+ii*Vgs_step),","])
			for ii in range(nVgs-1,-1,-1):											# negative portion of sweep Vgs array
				if ii > 0:
					#Vgssweeparray+=str(Vgs_start+ii*Vgs_step)+","
					Vgssweeparray="".join([Vgssweeparray,str(Vgs_start+ii*Vgs_step),","])
				else:
					#Vgssweeparray+=str(Vgs_start+ii*Vgs_step)						# last element
					Vgssweeparray="".join([Vgssweeparray,str(Vgs_start+ii*Vgs_step)]) # last element
		else:           # start and stop the Vgs sweep at the Vgs points closest to Vgs=0
			vgssweep=c.deque([Vgs_start+ii*Vgs_step for ii in range(0,nVgs)])
			vgssweep.extend([Vgs_start+ii*Vgs_step for ii in range(nVgs-1,-1,-1)])
			#imin=list(vgssweep).index(min(np.abs(vgssweep)))             # find the index of the minimum of |Vgs| ( Vgs closest to 0V)
			imin=min(range(len(vgssweep)), key=lambda i: abs(vgssweep[i]))             # find the index of the minimum of |Vgs| ( Vgs closest to 0V)
			vgssweep.rotate(-imin-1)                   # rotate the Vgs array to place the index of minimum |Vgs| at the start and end of the Vgs sweep

			Vgssweeparray=str(vgssweep[0])          # first Vgs value
			for ii in range(1,len(vgssweep)):
				Vgssweeparray="".join([Vgssweeparray,",",str(vgssweep[ii])])    # subsequent Vgs values to Vgs concatenated string

		nVgspts = int(len(Vgssweeparray.split(','))/2.)  # number of gate voltage points between the maximum and minimum gate voltages
		PLC, MT, self.Vgsslew = self.get_PLS_MT_fromslewrate(slewrate=Vgsslewrate, Vgsspan=abs(Vgs_stop - Vgs_start), nVgspts=nVgspts)  # get PLC which will give target slewrate if possible
		print("from line 1698 in parameter_analyzer.py PLC MT",PLC,MT)
		self.elapsed_time=nVgspts*MT  # total elapsed time of measurement
		#		print "Vgssweeparray is ",Vgssweeparray									# debug
		# self.__write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__write("EM 1,0")  # set to 4200 mode
		self.__write("BC;DR1")
		self.__write("SM;DM1")
		self.__write("SS;DT 0.")
		self.__write("SS;HT 0.")
		self.__write("SM;WT 0.")
		self.__write("SM;IN 0.")
		self.__write("SR 1,0")
		self.__write("SR 2,0")
		self.__write("SR 3,0")
		self.__write("SR 4,0")
		self.__write("IT4,0.,0.," + formatnum(PLC, precision=4, nonexponential=True))  # set filterfactor and delay factor both = 0.

		# set up SMUs for drain and gate
		self.__write("DE")
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")  # first undefine all channels

		# configure for dual (loop) sweep
		self.__write("DE;CH3,'VG','IG',1,1")  # gate drive channel definition
		self.__write("SS;VL3,1," + formatnum(gatecomp, precision=4, nonexponential=False) + "," + Vgssweeparray)  # gate drive voltage step
		#time.sleep(20.*nVgs/4090.)
		self.__write("RI 3" + "," + formatnum(gatecomp, precision=4, nonexponential=False) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
		self.__write("RG 3,0.1")  # manual set of gate current range to turn off autoranging

		#left drain
		self.__write("RI 1" + "," + formatnum(draincomp, precision=4, nonexponential=False) + "," + formatnum(draincomp, precision=4, nonexponential=False))  # manual set of right device drain current range to turn off autoranging
		self.__write("RG 1,0.01")  # appears to get rid of autoscaling
		self.__write("DE;CH1,'VD0','ID0',1,3")  # drain drive channel definition VAR1 on SMU2
		self.__write("SS;VC1, " + formatnum(self.Vdsset, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=False))  # constant drain voltage drive

		# right drain
		self.__write("RI 2" + "," + formatnum(draincomp, precision=4, nonexponential=False) + "," + formatnum(draincomp, precision=4, nonexponential=False))  # manual set of right device drain current range to turn off autoranging
		self.__write("RG 2,0.01")  # appears to get rid of autoscaling
		self.__write("DE;CH2,'VD1','ID1',1,3")  # drain drive channel definition VAR1 on SMU2
		self.__write("SS;VC2, " + formatnum(self.Vdsset, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=False))  # constant drain voltage drive

		self.__write("SM;LI 'VD0','VG','ID0','IG'")
		self.__write("SM;LI 'VD1','VG','ID1','IG'")
		self.__write("SM;XN 'VG',1,-3.0,0.")  # configure Keithley 4200 display X axis
		self.__write("SM;YA 'ID0',1,-10u,0.")  # configure Keithley 4200 display Y1 axis
		self.__write("SM;YB 'ID1',1,-10u,0.")  # configure Keithley 4200 display Y2 axis
		self.__write("MD;ME1")  # trigger for transfer curve measurement
		# self.__parameteranalyzer.wait_for_srq()                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
		self.__parameteranalyzer.chunk_size=self.__largechunk
		# get data from loop sweep
		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage

		reread = True
		while reread == True:
			Vds0raw = self.__parameteranalyzer.query("DO 'VD0'").split(',')
			print("Vds0raw", Vds0raw)
			drain0status_transloop = [dat[:1] for dat in Vds0raw]
			reread = False
			for x in drain0status_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vds0 in dual-swept transfer curve")
		Vds0_transloop = [float(dat[1:]) for dat in Vds0raw]
		# read drain0 current
		reread = True
		while reread == True:
			Id0raw = self.__parameteranalyzer.query("DO 'ID0'").split(',')
			drain0status_transloop = [dat[:1] for dat in Id0raw]
			reread = False
			for x in drain0status_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Id0 in dual-swept transfer curve")
		Id0_transloop = [float(dat[1:]) for dat in Id0raw]

		# read drain1 voltage
		reread = True
		while reread == True:
			Vds1raw = self.__parameteranalyzer.query("DO 'VD1'").split(',')
			print("Vds1raw", Vds1raw)
			drain1status_transloop = [dat[:1] for dat in Vds1raw]
			reread = False
			for x in drain1status_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vds0 in dual-swept transfer curve")
		Vds1_transloop = [float(dat[1:]) for dat in Vds1raw]
		# read drain1 current
		reread = True
		while reread == True:
			Id1raw = self.__parameteranalyzer.query("DO 'ID1'").split(',')
			drain1status_transloop = [dat[:1] for dat in Id1raw]
			reread = False
			for x in drain1status_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Id1 in dual-swept transfer curve")
		Id1_transloop = [float(dat[1:]) for dat in Id1raw]

		# read gate voltage
		reread = True
		while reread == True:
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
			gatestatus_transloop = [dat[:1] for dat in Vgsraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vgs in dual-swept transfer curve")
		Vgs_transloop = [float(dat[1:]) for dat in Vgsraw]
		# read gate current
		reread = True
		while reread == True:
			Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
			gatestatus_transloop = [dat[:1] for dat in Igraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Ig in dual-swept transfer curve")
		Ig_transloop = [float(dat[1:]) for dat in Igraw]

####### now separate out forward and reverse sweeps
		self.Id0_tf = []
		self.Id1_tf = []
		self.Ig_tf = []
		self.Vgs_tf = []
		self.Vds0_tf = []
		self.Vds1_tf = []
		self.drain0status_tf = []
		self.drain1status_tf = []
		self.gatestatus_tf = []
		for ii in range(0,nVgs):												# positive portion of Vgs sweep
			self.Id0_tf.append(Id0_transloop[ii])
			self.Id1_tf.append(Id1_transloop[ii])
			self.Ig_tf.append(Ig_transloop[ii])
			self.Vgs_tf.append(Vgs_transloop[ii])
			self.Vds0_tf.append(Vds0_transloop[ii])
			self.drain0status_tf.append(drain0status_transloop[ii])
			self.Vds1_tf.append(Vds1_transloop[ii])
			self.drain1status_tf.append(drain1status_transloop[ii])
			self.gatestatus_tf.append(gatestatus_transloop[ii])
		self.Id0_tr = []
		self.Id1_tr = []
		self.Ig_tr = []
		self.Vgs_tr = []
		self.Vds0_tr = []
		self.Vds1_tr = []
		self.drain0status_tr = []
		self.drain1status_tr = []
		self.gatestatus_tr = []
		for ii in range(nVgs,len(Id0_transloop)):											# negative sweep of Vgs
			self.Id0_tr.append(Id0_transloop[ii])
			self.Id1_tr.append(Id1_transloop[ii])
			self.Ig_tr.append(Ig_transloop[ii])
			self.Vgs_tr.append(Vgs_transloop[ii])
			self.Vds0_tr.append(Vds0_transloop[ii])
			self.drain0status_tr.append(drain0status_transloop[ii])
			self.Vds1_tr.append(Vds1_transloop[ii])
			self.drain1status_tr.append(drain1status_transloop[ii])
			self.gatestatus_tr.append(gatestatus_transloop[ii])
		self.__parameteranalyzer.chunk_size=self.__smallchunk
#######################################################################################################################################################
######################################################################################################################################################
# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with four sweeps +-+-+
# both drains drain0 and drain1 have the same voltage values
# This is usually used for back-gated TLM structures
# CH1 (SMU1) and CH2 (SMU2) are drain1 and drain2 respectively while the gate is CH3 (SMU3)
	def measure_ivtransferloop_4sweep_dual_backgate(self, inttime="2", Iautorange=True, delayfactor=2, filterfactor=1,integrationtime=1,sweepdelay=0.,holdtime=0, Vds=None, draincomp=0.1,Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=5E-5):
		self.__parameteranalyzer.clear()

		if not (inttime != '1' or inttime != '2' or inttime != '3' or inttime != '4'): raise ValueError(
			'ERROR! invalid inttime setting')
		if inttime == '4':  # custom timing setting
			inttime = "".join(['4', ',', str(delayfactor), ',', str(filterfactor), ',', str(integrationtime)])
			custom=True
		else: custom=False
		if abs(Vds) > self.maxvoltageprobe: raise ValueError(
			"ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		print("IV tranferloop dual device start")  # debug
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		nVgs = int(abs((Vgs_stop - Vgs_start) / Vgs_step))+1  # number of gate bias for one direction of Vgs sweep

		# be sure that we are not sweeping Vgs outside of specified range
		if float(Vgs_start)>=float(Vgs_stop) and Vgs_step>0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start>=Vgs_stop. Check parameters")
		if float(Vgs_start)<float(Vgs_stop) and Vgs_step<0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start<Vgs_stop. Check parameters")


		Vgssweeparray = ""
		for ii in range(0, nVgs): Vgssweeparray = "".join([Vgssweeparray,str(Vgs_start + ii * Vgs_step),","]) 							# first sweep
		for ii in range(nVgs - 1, -1, -1): Vgssweeparray = "".join([Vgssweeparray,str(Vgs_start + ii * Vgs_step),","])					# 2nd sweep
		for ii in range(0, nVgs): Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])  						# 3rd sweep
		for ii in range(nVgs - 1, -1, -1):
			if ii>0: Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])  				                    # 4th sweep
			else: Vgssweeparray += str(Vgs_start + ii * Vgs_step)  # last element
			#		print "Vgssweeparray is ",Vgssweeparray									# debug
		# self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.write("EM 1,0")  # set to 4200 mode
		self.__parameteranalyzer.write("IT" + inttime + ";BC;DR1")
		self.__parameteranalyzer.write("SM;DM1")

		self.__parameteranalyzer.write("SS;DT ",str(sweepdelay))
		self.__parameteranalyzer.write("SS;HT ",str(holdtime))

		# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE")
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")  # first undefine all channels

		# configure for dual (loop) sweep for two devices at once
		self.__parameteranalyzer.write("DE;CH3,'VG','IG',1,1")  # gate drive channel definition
		self.__parameteranalyzer.write(
			"SS;VL3,1," + "".join([str(gatecomp), ",", Vgssweeparray]))  # gate drive for sweep
		# self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients

		self.__parameteranalyzer.write("DE;CH1,'VD0','ID0',1,3")  # drain0 drive channel definition
		self.__parameteranalyzer.write("SS;VC1, " + str(Vds) + "," + str(draincomp))  # constant drain voltage drive
		# self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients

		self.__parameteranalyzer.write("DE;CH2,'VD1','ID1',1,3")  # drain1 drive channel definition
		self.__parameteranalyzer.write("SS;VC2, " + str(Vds) + "," + str(draincomp))  # constant drain voltage drive
		# self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		if custom==True and Iautorange == False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__parameteranalyzer.write("RI 1" + "," + str(draincomp) + "," + str(draincomp))  # allow manual set of left device drain current range to turn off autoranging
			self.__parameteranalyzer.write("RI 2" + "," + str(draincomp) + "," + str(draincomp))  # allow manual set of right device drain current range to turn off autoranging
			self.__parameteranalyzer.write("RI 3" + "," + str(gatecomp) + "," + str(gatecomp))  # allow manual set of gate current range to turn off autoranging
		self.__parameteranalyzer.write("SM;LI 'VD0','VG','ID0','IG'")
		self.__parameteranalyzer.write("SM;LI 'VD1','VG','ID1','IG'")
		self.__parameteranalyzer.write("SM;XN 'VG',1,-3.0,0.")  # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID0',1,-10u,0.")  # configure Keithley 4200 display Y1 axis
		self.__parameteranalyzer.write("SM;YB 'ID1',1,-10u,0.")  # configure Keithley 4200 display Y2 axis
		starttime = time.time()  # measure sweep time
		print("from line 986 parameter_analyzer.py triggering", starttime)
		self.__parameteranalyzer.write("MD;ME1")  # trigger for transfer curve measurement
		# self.__parameteranalyzer.wait_for_srq()                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
		endtime = time.time()-3
		print("from line 986 parameter_analyzer.py endmeasure", endtime)
		self.Vgsslew = 4.*abs(Vgs_stop-Vgs_start)/(endtime-starttime)
		self.elapsed_time = endtime - starttime
		print("elapsed time of ivtransferloop_dual_backgate() =" + formatnum(self.elapsed_time) + " Vgs slew rate = " + formatnum(self.Vgsslew, precision=2) + " V/sec")
		print("Vgs_start, Vgs_stop", Vgs_start, Vgs_stop)
		# get data from loop sweep
		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain0 voltage
		reread = True
		while reread == True:
			Vds0raw = self.__parameteranalyzer.query("DO 'VD0'").split(',')
			print("Vds0raw", Vds0raw)
			drain0status_transloop = [dat[:1] for dat in Vds0raw]
			reread = False
			for x in drain0status_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vds0 in dual-swept transfer curve")
		Vds0_transloop = [float(dat[1:]) for dat in Vds0raw]
		# read drain0 current
		reread = True
		while reread == True:
			Id0raw = self.__parameteranalyzer.query("DO 'ID0'").split(',')
			drain0status_transloop = [dat[:1] for dat in Id0raw]
			reread = False
			for x in drain0status_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Id0 in dual-swept transfer curve")
		Id0_transloop = [float(dat[1:]) for dat in Id0raw]

		# read drain1 voltage
		reread = True
		while reread == True:
			Vds1raw = self.__parameteranalyzer.query("DO 'VD1'").split(',')
			print("Vds1raw", Vds1raw)
			drain1status_transloop = [dat[:1] for dat in Vds1raw]
			reread = False
			for x in drain1status_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vds0 in dual-swept transfer curve")
		Vds1_transloop = [float(dat[1:]) for dat in Vds1raw]
		# read drain1 current
		reread = True
		while reread == True:
			Id1raw = self.__parameteranalyzer.query("DO 'ID1'").split(',')
			drain1status_transloop = [dat[:1] for dat in Id1raw]
			reread = False
			for x in drain1status_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Id1 in dual-swept transfer curve")
		Id1_transloop = [float(dat[1:]) for dat in Id1raw]

		# read gate voltage
		reread = True
		while reread == True:
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
			gatestatus_transloop = [dat[:1] for dat in Vgsraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vgs in dual-swept transfer curve")
		Vgs_transloop = [float(dat[1:]) for dat in Vgsraw]
		# read gate current
		reread = True
		while reread == True:
			Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
			gatestatus_transloop = [dat[:1] for dat in Igraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Ig in dual-swept transfer curve")
		Ig_transloop = [float(dat[1:]) for dat in Igraw]

		####### now separate out different numbered sweeps
		# first sweep of loop
		self.Id0_t1 = []
		self.Id1_t1 = []
		self.Ig_t1 = []
		self.Vgs_t1 = []
		self.Vds0_t1 = []
		self.Vds1_t1 = []
		self.drain0status_t1 = []
		self.drain1status_t1 = []
		self.gatestatus_t1 = []
		for ii in range(0, nVgs):  # 1st Vgs sweep
			self.Id0_t1.append(Id0_transloop[ii])
			self.Id1_t1.append(Id1_transloop[ii])
			self.Ig_t1.append(Ig_transloop[ii])
			self.Vgs_t1.append(Vgs_transloop[ii])
			self.Vds0_t1.append(Vds0_transloop[ii])
			self.drain0status_t1.append(drain0status_transloop[ii])
			self.Vds1_t1.append(Vds1_transloop[ii])
			self.drain1status_t1.append(drain1status_transloop[ii])
			self.gatestatus_t1.append(gatestatus_transloop[ii])
		# second sweep of loop
		self.Id0_t2 = []
		self.Id1_t2 = []
		self.Ig_t2 = []
		self.Vgs_t2 = []
		self.Vds0_t2 = []
		self.Vds1_t2 = []
		self.drain0status_t2 = []
		self.drain1status_t2 = []
		self.gatestatus_t2 = []
		for ii in range(nVgs, 2*nVgs):  # 2nd sweep of Vgs
			self.Id0_t2.append(Id0_transloop[ii])
			self.Id1_t2.append(Id1_transloop[ii])
			self.Ig_t2.append(Ig_transloop[ii])
			self.Vgs_t2.append(Vgs_transloop[ii])
			self.Vds0_t2.append(Vds0_transloop[ii])
			self.drain0status_t2.append(drain0status_transloop[ii])
			self.Vds1_t2.append(Vds1_transloop[ii])
			self.drain1status_t2.append(drain1status_transloop[ii])
			self.gatestatus_t2.append(gatestatus_transloop[ii])
		##### 3rd sweep of loop
		self.Id0_t3 = []
		self.Id1_t3 = []
		self.Ig_t3 = []
		self.Vgs_t3 = []
		self.Vds0_t3 = []
		self.Vds1_t3 = []
		self.drain0status_t3 = []
		self.drain1status_t3 = []
		self.gatestatus_t3 = []
		for ii in range(2*nVgs, 3*nVgs):  # 2nd sweep of Vgs
			self.Id0_t3.append(Id0_transloop[ii])
			self.Id1_t3.append(Id1_transloop[ii])
			self.Ig_t3.append(Ig_transloop[ii])
			self.Vgs_t3.append(Vgs_transloop[ii])
			self.Vds0_t3.append(Vds0_transloop[ii])
			self.drain0status_t3.append(drain0status_transloop[ii])
			self.Vds1_t3.append(Vds1_transloop[ii])
			self.drain1status_t3.append(drain1status_transloop[ii])
			self.gatestatus_t3.append(gatestatus_transloop[ii])
		##### 4th sweep of loop
		self.Id0_t4 = []
		self.Id1_t4 = []
		self.Ig_t4 = []
		self.Vgs_t4 = []
		self.Vds0_t4 = []
		self.Vds1_t4 = []
		self.drain0status_t4 = []
		self.drain1status_t4 = []
		self.gatestatus_t4 = []
		for ii in range(3*nVgs,4*nVgs):  # 2nd sweep of Vgs
			self.Id0_t4.append(Id0_transloop[ii])
			self.Id1_t4.append(Id1_transloop[ii])
			self.Ig_t4.append(Ig_transloop[ii])
			self.Vgs_t4.append(Vgs_transloop[ii])
			self.Vds0_t4.append(Vds0_transloop[ii])
			self.drain0status_t4.append(drain0status_transloop[ii])
			self.Vds1_t4.append(Vds1_transloop[ii])
			self.drain1status_t4.append(drain1status_transloop[ii])
			self.gatestatus_t4.append(gatestatus_transloop[ii])
#######################################################################################################################################################
######################################################################################################################################################
# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with a loop sweep e.g. sweep high to low then low to high
# works for only backgated measurements
# Backgate devices use CH3, SMU3 as the gate CH1 SMU1, CH2, SMU2 are used as the drains
	def measure_ivtransferloop_4sweep_dual_controlledslew_backgated(self, Vgsslewrate=None, Vds=None, draincomp=None, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=None):
		self.__parameteranalyzer.clear()
		self.Vdsset = Vds
		if abs(Vds) > self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")  # protect probe from overvoltage
		if abs(Vgs_start) > self.maxvoltageprobe or abs(Vgs_step) > self.maxvoltageprobe or abs(Vgs_stop) > self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs voltage to bias Tee and/or probes")  # protect probe from overvoltage
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		nVgs = int(abs((Vgs_stop - Vgs_start) / Vgs_step)) + 1  # number of gate bias for one direction of Vgs sweep

		# be sure that we are not sweeping Vgs outside of specified range
		if float(Vgs_start)>=float(Vgs_stop) and Vgs_step>0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start>=Vgs_stop. Check parameters")
		if float(Vgs_start)<float(Vgs_stop) and Vgs_step<0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start<Vgs_stop. Check parameters")

		Vgssweeparray = ""
		for ii in range(0, nVgs): Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])  # first sweep
		for ii in range(nVgs - 1, -1, -1): Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])  # 2nd sweep
		for ii in range(0, nVgs): Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])  # 3rd sweep
		for ii in range(nVgs - 1, -1, -1):
			if ii > 0:Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])  # 4th sweep
			else: Vgssweeparray += str(Vgs_start + ii * Vgs_step)  # last element

		nVgspts = int(len(Vgssweeparray.split(','))/4.)  # number of gate voltage points between the maximum and minimum gate voltages
		PLC, MT, self.Vgsslew = self.get_PLS_MT_fromslewrate(slewrate=Vgsslewrate, Vgsspan=abs(Vgs_stop - Vgs_start), nVgspts=nVgspts)  # get PLC which will give target slewrate if possible
		self.elapsed_time=nVgspts*MT  # total elapsed time of measurement
		#		print "Vgssweeparray is ",Vgssweeparray									# debug
		# self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.write("EM 1,0")  # set to 4200 mode
		self.__parameteranalyzer.write("BC;DR1")
		self.__parameteranalyzer.write("SM;DM1")
		self.__parameteranalyzer.write("SS;DT 0.")
		self.__parameteranalyzer.write("SS;HT 0.")
		self.__parameteranalyzer.write("SM;WT 0.")
		self.__parameteranalyzer.write("SM;IN 0.")
		self.__parameteranalyzer.write("SR 1,0")
		self.__parameteranalyzer.write("SR 2,0")
		self.__parameteranalyzer.write("SR 3,0")
		self.__parameteranalyzer.write("SR 4,0")
		self.__parameteranalyzer.write("IT4,0.,0.," + formatnum(PLC, precision=2, nonexponential=True))  # set filterfactor and delay factor both = 0.

		# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE")
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")  # first undefine all channels

		# configure for dual (loop) sweep
		self.__parameteranalyzer.write("DE;CH3,'VG','IG',1,1")  # gate drive channel definition
		self.__parameteranalyzer.write("SS;VL3,1," + formatnum(gatecomp, precision=4, nonexponential=False) + "," + Vgssweeparray)  # gate drive voltage step
		time.sleep(20.*nVgs/4090.)
		self.__parameteranalyzer.write("RI 3" + "," + formatnum(gatecomp, precision=4, nonexponential=False) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
		self.__parameteranalyzer.write("RG 3,0.1")  # manual set of gate current range to turn off autoranging

		#left drain
		self.__parameteranalyzer.write("RI 1" + "," + formatnum(draincomp, precision=4, nonexponential=False) + "," + formatnum(draincomp, precision=4, nonexponential=False))  # manual set of right device drain current range to turn off autoranging
		self.__parameteranalyzer.write("RG 1,0.01")  # appears to get rid of autoscaling
		self.__parameteranalyzer.write("DE;CH1,'VD0','ID0',1,3")  # drain drive channel definition VAR1 on SMU2
		self.__parameteranalyzer.write("SS;VC1, " + formatnum(self.Vdsset, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=False))  # constant drain voltage drive

		# right drain
		self.__parameteranalyzer.write("RI 2" + "," + formatnum(draincomp, precision=4, nonexponential=False) + "," + formatnum(draincomp, precision=4, nonexponential=False))  # manual set of right device drain current range to turn off autoranging
		self.__parameteranalyzer.write("RG 2,0.01")  # appears to get rid of autoscaling
		self.__parameteranalyzer.write("DE;CH2,'VD1','ID1',1,3")  # drain drive channel definition VAR1 on SMU2
		self.__parameteranalyzer.write("SS;VC2, " + formatnum(self.Vdsset, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=False))  # constant drain voltage drive

		self.__parameteranalyzer.write("SM;LI 'VD0','VG','ID0','IG'")
		self.__parameteranalyzer.write("SM;LI 'VD1','VG','ID1','IG'")
		self.__parameteranalyzer.write("SM;XN 'VG',1,-3.0,0.")  # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID0',1,-10u,0.")  # configure Keithley 4200 display Y1 axis
		self.__parameteranalyzer.write("SM;YB 'ID1',1,-10u,0.")  # configure Keithley 4200 display Y2 axis

		self.__parameteranalyzer.write("MD;ME1")  # trigger for transfer curve measurement
		# self.__parameteranalyzer.wait_for_srq()                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
		# get data from loop sweep
		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage

		reread = True
		while reread == True:
			Vds0raw = self.__parameteranalyzer.query("DO 'VD0'").split(',')
			print("Vds0raw", Vds0raw)
			drain0status_transloop = [dat[:1] for dat in Vds0raw]
			reread = False
			for x in drain0status_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vds0 in dual-swept transfer curve")
		Vds0_transloop = [float(dat[1:]) for dat in Vds0raw]
		# read drain0 current
		reread = True
		while reread == True:
			Id0raw = self.__parameteranalyzer.query("DO 'ID0'").split(',')
			drain0status_transloop = [dat[:1] for dat in Id0raw]
			reread = False
			for x in drain0status_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Id0 in dual-swept transfer curve")
		Id0_transloop = [float(dat[1:]) for dat in Id0raw]

		# read drain1 voltage
		reread = True
		while reread == True:
			Vds1raw = self.__parameteranalyzer.query("DO 'VD1'").split(',')
			print("Vds1raw", Vds1raw)
			drain1status_transloop = [dat[:1] for dat in Vds1raw]
			reread = False
			for x in drain1status_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vds0 in dual-swept transfer curve")
		Vds1_transloop = [float(dat[1:]) for dat in Vds1raw]
		# read drain1 current
		reread = True
		while reread == True:
			Id1raw = self.__parameteranalyzer.query("DO 'ID1'").split(',')
			drain1status_transloop = [dat[:1] for dat in Id1raw]
			reread = False
			for x in drain1status_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Id1 in dual-swept transfer curve")
		Id1_transloop = [float(dat[1:]) for dat in Id1raw]

		# read gate voltage
		reread = True
		while reread == True:
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
			gatestatus_transloop = [dat[:1] for dat in Vgsraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vgs in dual-swept transfer curve")
		Vgs_transloop = [float(dat[1:]) for dat in Vgsraw]
		# read gate current
		reread = True
		while reread == True:
			Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
			gatestatus_transloop = [dat[:1] for dat in Igraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Ig in dual-swept transfer curve")
		Ig_transloop = [float(dat[1:]) for dat in Igraw]

		####### now separate out different numbered sweeps
		# first sweep of loop
		self.Id0_t1 = []
		self.Id1_t1 = []
		self.Ig_t1 = []
		self.Vgs_t1 = []
		self.Vds0_t1 = []
		self.Vds1_t1 = []
		self.drain0status_t1 = []
		self.drain1status_t1 = []
		self.gatestatus_t1 = []
		for ii in range(0, nVgs):  # 1st Vgs sweep
			self.Id0_t1.append(Id0_transloop[ii])
			self.Id1_t1.append(Id1_transloop[ii])
			self.Ig_t1.append(Ig_transloop[ii])
			self.Vgs_t1.append(Vgs_transloop[ii])
			self.Vds0_t1.append(Vds0_transloop[ii])
			self.drain0status_t1.append(drain0status_transloop[ii])
			self.Vds1_t1.append(Vds1_transloop[ii])
			self.drain1status_t1.append(drain1status_transloop[ii])
			self.gatestatus_t1.append(gatestatus_transloop[ii])
		# second sweep of loop
		self.Id0_t2 = []
		self.Id1_t2 = []
		self.Ig_t2 = []
		self.Vgs_t2 = []
		self.Vds0_t2 = []
		self.Vds1_t2 = []
		self.drain0status_t2 = []
		self.drain1status_t2 = []
		self.gatestatus_t2 = []
		for ii in range(nVgs, 2 * nVgs):  # 2nd sweep of Vgs
			self.Id0_t2.append(Id0_transloop[ii])
			self.Id1_t2.append(Id1_transloop[ii])
			self.Ig_t2.append(Ig_transloop[ii])
			self.Vgs_t2.append(Vgs_transloop[ii])
			self.Vds0_t2.append(Vds0_transloop[ii])
			self.drain0status_t2.append(drain0status_transloop[ii])
			self.Vds1_t2.append(Vds1_transloop[ii])
			self.drain1status_t2.append(drain1status_transloop[ii])
			self.gatestatus_t2.append(gatestatus_transloop[ii])
		##### 3rd sweep of loop
		self.Id0_t3 = []
		self.Id1_t3 = []
		self.Ig_t3 = []
		self.Vgs_t3 = []
		self.Vds0_t3 = []
		self.Vds1_t3 = []
		self.drain0status_t3 = []
		self.drain1status_t3 = []
		self.gatestatus_t3 = []
		for ii in range(2 * nVgs, 3 * nVgs):  # 2nd sweep of Vgs
			self.Id0_t3.append(Id0_transloop[ii])
			self.Id1_t3.append(Id1_transloop[ii])
			self.Ig_t3.append(Ig_transloop[ii])
			self.Vgs_t3.append(Vgs_transloop[ii])
			self.Vds0_t3.append(Vds0_transloop[ii])
			self.drain0status_t3.append(drain0status_transloop[ii])
			self.Vds1_t3.append(Vds1_transloop[ii])
			self.drain1status_t3.append(drain1status_transloop[ii])
			self.gatestatus_t3.append(gatestatus_transloop[ii])
		##### 4th sweep of loop
		self.Id0_t4 = []
		self.Id1_t4 = []
		self.Ig_t4 = []
		self.Vgs_t4 = []
		self.Vds0_t4 = []
		self.Vds1_t4 = []
		self.drain0status_t4 = []
		self.drain1status_t4 = []
		self.gatestatus_t4 = []
		for ii in range(3 * nVgs, 4 * nVgs):  # 2nd sweep of Vgs
			self.Id0_t4.append(Id0_transloop[ii])
			self.Id1_t4.append(Id1_transloop[ii])
			self.Ig_t4.append(Ig_transloop[ii])
			self.Vgs_t4.append(Vgs_transloop[ii])
			self.Vds0_t4.append(Vds0_transloop[ii])
			self.drain0status_t4.append(drain0status_transloop[ii])
			self.Vds1_t4.append(Vds1_transloop[ii])
			self.drain1status_t4.append(drain1status_transloop[ii])
			self.gatestatus_t4.append(gatestatus_transloop[ii])
#######################################################################################################################################################
######################################################################################################################################################
		# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with a loop sweep e.g. sweep high to low then low to high
	def measure_ivtransferloop_4sweep_topgate(self, inttime='2', delayfactor=2, Iautorange=True, filterfactor=1,integrationtime=1, sweepdelay=0., holdtime=0., Vds=None, draincomp=None, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=None):
		self.__parameteranalyzer.clear()
		if not(inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		if abs(Vds)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		if abs(Vgs_start)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs_start voltage to bias Tee and/or probes")
		if abs(Vgs_stop)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs_stop voltage to bias Tee and/or probes")
		if abs(Vgs_step)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs_step voltage to bias Tee and/or probes")
		print ("IV tranferloop4 start") # debug
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		nVgs = int(abs((Vgs_stop-Vgs_start)/Vgs_step))+1							# number of gate bias for one direction of Vgs sweep

		# be sure that we are not sweeping Vgs outside of specified range
		if float(Vgs_start)>=float(Vgs_stop) and Vgs_step>0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start>=Vgs_stop. Check parameters")
		if float(Vgs_start)<float(Vgs_stop) and Vgs_step<0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start<Vgs_stop. Check parameters")

		Vgssweeparray= ""
		for ii in range(0, nVgs): Vgssweeparray = "".join([Vgssweeparray,str(Vgs_start + ii * Vgs_step),","]) 							# first sweep
		for ii in range(nVgs - 1, -1, -1): Vgssweeparray = "".join([Vgssweeparray,str(Vgs_start + ii * Vgs_step),","])					# 2nd sweep
		for ii in range(0, nVgs): Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])  						# 3rd sweep
		for ii in range(nVgs - 1, -1, -1):
			if ii>0: Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])  				                    # 4th sweep
			else: Vgssweeparray += str(Vgs_start + ii * Vgs_step)  # last element

#		print "Vgssweeparray is ",Vgssweeparray									# debug
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.write("EM 1,0")								# set to 4200 mode
		self.__parameteranalyzer.write("IT"+inttime+";BC;DR1")
		self.__parameteranalyzer.write("SM;DM1")
		self.__parameteranalyzer.write("SS;DT ",str(sweepdelay)) #added by ahmad
		self.__parameteranalyzer.write("SS;HT ",str(holdtime))   #added by ahmad
# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE")
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")				# first undefine all channels

# configure for dual (loop) sweep
		self.__parameteranalyzer.write("DE;CH1,'VG','IG',1,1")                # gate drive channel definition set Vgs = constant
		self.__parameteranalyzer.write("SS;VL1,1,"+str(gatecomp)+","+Vgssweeparray)         # gate drive for sweep
		self.__parameteranalyzer.write("DE;CH2,'VD','ID',1,3")                         # drain drive channel definition VAR1
		self.__parameteranalyzer.write("SS;VC2, "+str(Vds)+","+str(draincomp))         # constant drain voltage drive
		if custom==True and Iautorange == False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__parameteranalyzer.write("RI 1" + "," + str(gatecomp) + "," + str(gatecomp))  # allow manual set of gate current range to turn off autoranging
			self.__parameteranalyzer.write("RI 2" + "," + str(draincomp) + "," + str(draincomp))  # allow manual set of right device drain current range to turn off autoranging

		self.__parameteranalyzer.write("SM;LI 'VD','VG','ID','IG'")
		self.__parameteranalyzer.write("SM;XN 'VG',1,-2.0,0.")                          # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID',1,-10u,0.")                          # configure Keithley 4200 display Y axis
		self.__parameteranalyzer.write("MD;ME1")                                        # trigger for transfer curve measurement
		#self.__parameteranalyzer.wait_for_srq()                                         # wait for transfer curve data sweep to complete
		starttime = time.time()  # measure sweep time
		self.__panpoll()
# get data from loop sweep
		endtime = time.time()-3
		print("from line 1395 parameter_analyzer.py endmeasure", endtime)
		self.Vgsslew = 4.*abs(Vgs_stop-Vgs_start)/(endtime-starttime)
		self.elapsed_time = endtime - starttime
		print("elapsed time of ivtransferloop_4topdate=" + formatnum(self.elapsed_time) + " Vgs slew rate = " + formatnum(self.Vgsslew, precision=2) + " V/sec")
		print("Vgs_start, Vgs_stop", Vgs_start, Vgs_stop)
		# get data from loop sweep
		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain0 voltage
		reread = True
		while reread == True:
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'").split(',')
			print("Vdsraw", Vdsraw)
			drainstatus_transloop = [dat[:1] for dat in Vdsraw]
			reread = False
			for x in drainstatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vds in 4-swept transfer curve")
		Vds_transloop = [float(dat[1:]) for dat in Vdsraw]
		# read drain current
		reread = True
		while reread == True:
			Idraw = self.__parameteranalyzer.query("DO 'ID'").split(',')
			drainstatus_transloop = [dat[:1] for dat in Idraw]
			reread = False
			for x in drainstatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Id0 in dual-swept transfer curve")
		Id_transloop = [float(dat[1:]) for dat in Idraw]

		# read gate voltage
		reread = True
		while reread == True:
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
			gatestatus_transloop = [dat[:1] for dat in Vgsraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Vgs in dual-swept transfer curve")
		Vgs_transloop = [float(dat[1:]) for dat in Vgsraw]
		# read gate current
		reread = True
		while reread == True:
			Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
			gatestatus_transloop = [dat[:1] for dat in Igraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Ig in dual-swept transfer curve")
		Ig_transloop = [float(dat[1:]) for dat in Igraw]

		####### now separate out different numbered sweeps
		# first sweep of loop
		self.Id_t1 = []
		self.Ig_t1 = []
		self.Vgs_t1 = []
		self.Vds_t1 = []
		self.drainstatus_t1 = []
		self.gatestatus_t1 = []
		for ii in range(0, nVgs):  # 1st Vgs sweep
			self.Id_t1.append(Id_transloop[ii])
			self.Ig_t1.append(Ig_transloop[ii])
			self.Vgs_t1.append(Vgs_transloop[ii])
			self.Vds_t1.append(Vds_transloop[ii])
			self.drainstatus_t1.append(drainstatus_transloop[ii])
			self.gatestatus_t1.append(gatestatus_transloop[ii])
		# second sweep of loop
		self.Id_t2 = []
		self.Ig_t2 = []
		self.Vgs_t2 = []
		self.Vds_t2 = []
		self.drainstatus_t2 = []
		self.gatestatus_t2 = []
		for ii in range(nVgs, 2*nVgs):  # 2nd sweep of Vgs
			self.Id_t2.append(Id_transloop[ii])
			self.Ig_t2.append(Ig_transloop[ii])
			self.Vgs_t2.append(Vgs_transloop[ii])
			self.Vds_t2.append(Vds_transloop[ii])
			self.drainstatus_t2.append(drainstatus_transloop[ii])
			self.gatestatus_t2.append(gatestatus_transloop[ii])
		##### 3rd sweep of loop
		self.Id_t3 = []
		self.Ig_t3 = []
		self.Vgs_t3 = []
		self.Vds_t3 = []
		self.drainstatus_t3 = []
		self.gatestatus_t3 = []
		for ii in range(2*nVgs, 3*nVgs):  # 3rd sweep of Vgs
			self.Id_t3.append(Id_transloop[ii])
			self.Ig_t3.append(Ig_transloop[ii])
			self.Vgs_t3.append(Vgs_transloop[ii])
			self.Vds_t3.append(Vds_transloop[ii])
			self.drainstatus_t3.append(drainstatus_transloop[ii])
			self.gatestatus_t3.append(gatestatus_transloop[ii])
		##### 4th sweep of loop
		self.Id_t4 = []
		self.Ig_t4 = []
		self.Vgs_t4 = []
		self.Vds_t4 = []
		self.drainstatus_t4 = []
		self.gatestatus_t4 = []
		for ii in range(3*nVgs,4*nVgs):  # 4th sweep of Vgs
			self.Id_t4.append(Id_transloop[ii])
			self.Ig_t4.append(Ig_transloop[ii])
			self.Vgs_t4.append(Vgs_transloop[ii])
			self.Vds_t4.append(Vds_transloop[ii])
			self.drainstatus_t4.append(drainstatus_transloop[ii])
			self.gatestatus_t4.append(gatestatus_transloop[ii])
#######################################################################################################################################################
#####################################################################################################################################################################################################################
# sweeps at one gate voltage and increasing maximum drain voltage
# the constant gate voltage is applied to the chuck (SMU3)
# swept drain voltage is applied to SMU2
# NOT IN USEABLE STATE
	def measure_burnsweepVds_backgate(self, inttime='2', backgated=False, currentrange=None,delayfactor='2',filterfactor='1',integrationtime=1, delaytime=0.02, Vgs=None, draincomp=None, Vds_start=None, Vds_max=None, Vds_step=None, gatecomp=None):
		self.__parameteranalyzer.clear()
		self.Vgs_burn_set=Vgs
		if not(inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		if backgated:
			if abs(Vgs)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		if abs(Vds_max)>self.maxvoltageprobe or abs(Vds_start)>self.maxvoltageprobe or abs(Vds_step)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		print ("IV tranfercurve start") # debug
		self.__write("EM 1,0")								# set to 4200 mode
		self.__write(" ".join(["SS;DT",str(delaytime)]))            # add delay time to aid settling and reduce probability of compliance due to charging transients

		self.__write("IT"+inttime+";BC;DR1")                  # setup delays and data acquision timing and averaging for noise reduction
		self.__write("SM;DM1")
# set up SMUs for drain and gate
		self.__write("DE")                                # set to channel definition page
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")     # first undefine all channels

		if backgated: self.__write("DE;CH3,'VG','IG',1,3")                			# gate drive channel definition set Vgs = constant	SMU3
		else: self.__write("DE;CH1,'VG','IG',1,3")                			# gate drive channel definition set Vgs = constant	SMU1
		self.__write("SS;VC3,"+","+str(Vgs)+","+str(gatecomp))         # gate drive
		self.__write("DE;CH2,'VD','ID',1,1")                         # drain drive channel definition VAR2
		if currentrange!=None: self.__write("RI 2"+","+str(currentrange)+","+str(currentrange))               # allow user to set current range of drain i.e. SMU2, here, currentrange=drain compliance

		Vds_stop_array=np.arange(Vds_start+Vds_step,Vds_max+Vds_step,Vds_step)            # get stop voltages for the many Vds sweeps
		self.Vds_burnfinal=c.deque()                 # last measured drain voltage of
		self.Vgs_burnfinal=c.deque()                 # last measured gate voltage
		self.Id_burnfinal=c.deque()                  # last measured drain current (A)
		self.Ig_burnfinal=c.deque()                  # last measured gate current (A)
		self.gatestatus_burnfinal=c.deque()          # append the gate status indicator to "C" if any gate status indictors are other than "N" for the current drain sweep
		self.drainstatus_burnfinal=c.deque()          # append the gate status indicator to "C" if any gate status indictors are other than "N" for the current drain sweep
		self.Vdsslewrate_burn=c.deque()

		for Vds_stop in Vds_stop_array:
			self.__parameteranalyzer.write("SS;VR1,"+str(Vds_start)+","+str(Vds_stop)+","+str(Vds_step)+","+str(draincomp))         # stepped drain voltage drive setup
			# plot trace on the Keithley 4200 screen
			self.__parameteranalyzer.write("SM;LI 'VD','VG','ID','IG'")
			self.__parameteranalyzer.write("SM;XN 'VD',1,-2.0,0.")                          # configure Keithley 4200 display X axis
			self.__parameteranalyzer.write("SM;YA 'ID',1,-10u,0.")                          # configure Keithley 4200 display Y axis
			starttime=time.time()
			self.__parameteranalyzer.write("MD;ME1")                                        # trigger for transfer curve measurement
			self.__panpoll()                    # wait for sweep to complete
			endtime = time.time()
			Vdsslew_burn = abs(Vds_stop - Vds_start) / (endtime - starttime)
			elapsed_time_burn = endtime - starttime
			print("elapsed time of burn sweep= " + formatnum(elapsed_time_burn) + " Vds slew rate = " + formatnum(self.Vdsslew_burn, precision=2) + " V/sec")
			print("Vds_start, Vds_stop", Vds_start, Vds_stop)

			# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
			# read drain voltage
			reread = True
			while reread==True:
				Vdsraw = self.__parameteranalyzer.query("DO 'VD'").split(',')
				drainstatus_burn=[dat[:1] for dat in Vdsraw]
				reread=False
				for x in drainstatus_burn:
					if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
						reread=True
						print("WARNING re-read of Vds in single-swept transfer curve")
			Vds_burn=[float(dat[1:]) for dat in Vdsraw]
			# read drain current
			reread=True
			while reread==True:
				Idraw = self.__parameteranalyzer.query("DO 'ID'").split(',')
				drainstatus_burn=[dat[:1] for dat in Idraw]
				reread=False
				for x in drainstatus_burn:
					if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
						reread=True
						print("WARNING re-read of Id in single-swept transfer curve")
			Id_burn=[float(dat[1:]) for dat in Idraw]
			# read gate voltage
			reread=True
			while reread==True:
				Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
				gatestatus_burn=[dat[:1] for dat in Vgsraw]
				reread=False
				for x in gatestatus_burn:
					if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
						reread=True
						print("WARNING re-read of Vgs in single-swept transfer curve")
			Vgs_burn=[float(dat[1:]) for dat in Vgsraw]
			# read gate current
			reread=True
			while reread==True:
				Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
				gatestatus_burn=[dat[:1] for dat in Igraw]
				reread=False
				for x in gatestatus_burn:
					if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
						reread=True
						print("WARNING re-read of Ig in single-swept transfer curve")
			Ig_burn=[float(dat[1:]) for dat in Igraw]
			# Append the last values measured in the above drain voltage sweep
			if "C" in gatestatus_burn: self.gatestatus_burnfinal.append("C")                # if this sweep shows gate compliance ANYWHERE in the sweep, then indicate compliance for this sweep
			if "C" in drainstatus_burn: self.drainstatus_burnfinal.append("C")              # if this sweep shows drain compliance ANYWHERE in the sweep, then indicate compliance for this sweep
			self.Vds_burnfinal.append(Vds_burn[-1])                                         # append the last measured Vds of the Vds sweep
			self.Vgs_burnfinal.append(Vgs_burn[-1])                                         # append the last measured Vgs of the Vds sweep
			self.Id_burnfinal.append(Id_burn[-1])                                           # append the last measured drain current of the Vds sweep
			self.Ig_burnfinal.append(Ig_burn[-1])                                           # append the last measured gate current of the Vds swee
			self.Vdsslewrate_burn.append(Vdsslew_burn)                                      # rate of drain voltage sweep in V/sec

#####################################################################################################################################################################################################################
# sweeps at one gate voltage and one sweep of drain voltage
# the constant gate voltage is applied to the chuck (SMU3)
# swept drain voltage is applied to SMU2
	def measure_burnonesweepVds(self, inttime='2', backgated=False, currentrange=None,delayfactor='2',filterfactor='1',delaytime=0.02,integrationtime=1, Vgs=None, draincomp=None, Vds_start=None, Vds_stop=None, Vds_step=None, gatecomp=None):
		self.__parameteranalyzer.clear()
		self.__parameteranalyzer.chunk_size=self.__midchunk
		if backgated and abs(Vgs)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")  # protect probe from overvoltage
		if abs(Vds_start)>self.maxvoltageprobe or abs(Vds_step)>self.maxvoltageprobe or abs(Vds_stop)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")  # protect probe from overvoltage
		self.Vgs_burn_set=Vgs
		if Vds_start>=Vds_stop: Vds_step=-abs(Vds_step)
		else: Vds_step=abs(Vds_step)
		if not(inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		self.__write(" ".join(["SS;DT",str(delaytime)]))            # add delay time to aid settling and reduce probability of compliance due to charging transients
		print ("IV tranfercurve start") # debug
		self.__write("EM 1,0")								# set to 4200 mode
		self.__write("IT"+inttime+";BC;DR1")                  # setup delays and data acquision timing and averaging for noise reduction
		self.__write("SM;DM1")
# set up SMUs for drain and gate
		self.__write("DE")                                # set to channel definition page
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")     # first undefine all channels

		self.__write("DE;CH2,'VD','ID',1,1")                         # drain drive channel definition VAR1
		self.__write("SS;VR1,"+str(Vds_start)+","+str(Vds_stop)+","+str(Vds_step)+","+str(draincomp))         # stepped drain voltage drive setup
		if backgated:
			self.__write("DE;CH3,'VG','IG',1,3")                			# gate drive channel definition set Vgs = constant	SMU3
			self.__write("SS;VC3,"+str(Vgs)+","+str(gatecomp))         # constant gate drive
		else:
			self.__write("DE;CH1,'VG','IG',1,3")                			# gate drive channel definition set Vgs = constant	SMU1
			self.__write("SS;VC1,"+str(Vgs)+","+str(gatecomp))         # constant gate drive

		if currentrange!=None: self.__write("RI 2"+","+str(currentrange)+","+str(currentrange))               # allow user to set current range of drain i.e. SMU1
		# plot trace on the Keithley 4200 screen
		self.__write("SM;LI 'VD','VG','ID','IG'")
		self.__write("SM;XN 'VD',1,-2.0,0.")                          # configure Keithley 4200 display X axis
		self.__write("SM;YA 'ID',1,-10u,0.")                          # configure Keithley 4200 display Y axis
		starttime=time.time()
		self.__write("MD;ME1")                                        # trigger for transfer curve measurement
		self.__panpoll()                    # wait for sweep to complete
		endtime = time.time()
		self.__parameteranalyzer.chunk_size=self.__largechunk
		self.Vdsslew_burn = abs(Vds_stop - Vds_start)/(endtime - starttime)
		self.elapsed_time_burn = endtime-starttime
		print("elapsed time of burn sweep= " + formatnum(self.elapsed_time_burn) + " Vds slew rate = " + formatnum(self.Vdsslew_burn, precision=2) + " V/sec")
		print("Vds_start, Vds_stop", Vds_start, Vds_stop)

		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage
		reread = True
		while reread==True:
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'").split(',')
			self.drainstatus_burn=[dat[:1] for dat in Vdsraw]
			reread=False
			for x in self.drainstatus_burn:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vds in burn curve")
		self.Vds_burn=[float(dat[1:]) for dat in Vdsraw]
		# read drain current
		reread=True
		while reread==True:
			Idraw = self.__parameteranalyzer.query("DO 'ID'").split(',')
			self.drainstatus_burn=[dat[:1] for dat in Idraw]
			reread=False
			for x in self.drainstatus_burn:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Id in burn curve")
		self.Id_burn=[float(dat[1:]) for dat in Idraw]
		# read gate voltage
		reread=True
		while reread==True:
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
			self.gatestatus_burn=[dat[:1] for dat in Vgsraw]
			reread=False
			for x in self.gatestatus_burn:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vgs in burn curve")
		self.Vgs_burn=[float(dat[1:]) for dat in Vgsraw]
		# read gate current
		reread=True
		while reread==True:
			Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
			self.gatestatus_burn=[dat[:1] for dat in Igraw]
			reread=False
			for x in self.gatestatus_burn:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Ig in burn curve")
		self.Ig_burn=[float(dat[1:]) for dat in Igraw]
		# Append the last values measured in the above drain voltage sweep
		if "C" in self.gatestatus_burn: gatestatus_burnfinal="C"                # if this sweep shows gate compliance ANYWHERE in the sweep, then indicate compliance for this sweep
		else: gatestatus_burnfinal="N"
		if "C" in self.drainstatus_burn: drainstatus_burnfinal="C"              # if this sweep shows drain compliance ANYWHERE in the sweep, then indicate compliance for this sweep
		else: drainstatus_burnfinal="N"
		Vds_burnfinal=self.Vds_burn[-1]                                         # append the last measured Vds of the Vds sweep
		Vgs_burnfinal=self.Vgs_burn[-1]                                         # append the last measured Vgs of the Vds sweep
		Id_burnfinal=self.Id_burn[-1]                                         # append the last measured drain current of the Vds sweep
		Ig_burnfinal=self.Ig_burn[-1]                                           # append the last measured gate current of the Vds sweep
		self.__parameteranalyzer.chunk_size=self.__smallchunk
		return Id_burnfinal,Ig_burnfinal,Vds_burnfinal,Vgs_burnfinal,drainstatus_burnfinal,gatestatus_burnfinal
######################################################################################################################################################
# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with sweep in one direction
# measured top-gated FETs two at a time
# both drains drain0 and drain1 have the same voltage values
# CH1 (SMU1) and CH2 (SMU2) are drain1 and drain2 respectively while the gate is CH3 (SMU3)
	def measure_ivtransfer_dual_topgate(self, inttime="2", Iautorange=True, delayfactor=2,filterfactor=1,integrationtime=1, sweepdelay=0.,holdtime=0, Vds=None, draincomp=0.1, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=5E-5):
		self.__parameteranalyzer.clear()
		self.__parameteranalyzer.chunk_size=self.__midchunk

		# be sure that we are not sweeping Vgs outside of specified range
		if float(Vgs_start)>=float(Vgs_stop) and Vgs_step>0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start>=Vgs_stop. Check parameters")
		if float(Vgs_start)<float(Vgs_stop) and Vgs_step<0.:
			raise ValueError("ERROR! Vgs sweep outside of specified range because Vgs_step>0 when Vgs_start<Vgs_stop. Check parameters")

		if not (inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		if abs(Vds)>self.maxvoltageprobe or abs(Vgs_start)>self.maxvoltageprobe or abs(Vgs_stop)>self.maxvoltageprobe or abs(Vgs_step)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		print ("IV tranfercurve dual device start") # debug
		self.__write("EM 1,0")								# set to 4200 mode
		self.__write("IT"+inttime+";BC;DR1")
		self.__write("SM;DM1")

# set up SMUs for drain and gate
		self.__write("DE")
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")     # first undefine all channels

		self.__write("DE;CH1,'VG0','IG0',1,1")                			# gate0 drive channel definition on channel CH1 voltage source,var1
		self.__write("DE;CH2,'VG1','IG1',1,1")                			# gate1 drive channel definition on channel CH2
		self.__write("SS;VR1, "+",".join([formatnum(number=Vgs_start,precision=4,nonexponential=True),formatnum(Vgs_stop,precision=4,nonexponential=True),
		                                  formatnum(number=Vgs_step,precision=4,nonexponential=True),formatnum(number=gatecomp,precision=2,nonexponential=False)]))         # gate sweep setup var1 voltage sweep
		self.__write("DE;CH3,'VD0','ID0',1,3")                         # drain0 drive channel definition constant
		self.__write("SS;VC1, "+",".join([formatnum(number=Vds,precision=4,nonexponential=True), formatnum(number=draincomp,precision=2,nonexponential=False)]))         # constant drain0 voltage drive

		self.__write("DE;CH4,'VD1','ID1',1,3")                         # drain1 drive channel definition constant
		self.__write("SS;VC2, "+",".join([formatnum(number=Vds,precision=4,nonexponential=True),formatnum(number=draincomp,precision=2,nonexponential=False)]))         # constant drain1 voltage drive

		self.__write("SS;DT ", str(sweepdelay))
		self.__write("SS;HT ", str(holdtime))
		if custom==True and Iautorange==False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__write(",".join(["RI 1",formatnum(number=gatecomp,precision=2,nonexponential=False),formatnum(number=gatecomp,precision=2,nonexponential=False)]))  # allow manual set of drain0 current range to turn off autoranging
			self.__write(",".join(["RI 2",formatnum(number=gatecomp,precision=2,nonexponential=False),formatnum(number=gatecomp,precision=2,nonexponential=False)]))  # allow manual set of drain1 current range to turn off autoranging
			self.__write(",".join(["RI 3",formatnum(number=draincomp,precision=2,nonexponential=False),formatnum(number=draincomp,precision=2,nonexponential=False)]))  # allow manual set of drain1 current range to turn off autoranging
			self.__write(",".join(["RI 4",formatnum(number=draincomp,precision=2,nonexponential=False),formatnum(number=draincomp,precision=2,nonexponential=False)]))  # allow manual set of drain1 current range to turn off autoranging

		self.__write("SM;LI 'VD0','VG0','ID0','IG0'")
		self.__write("SM;LI 'VD0','VG0','ID1','IG1'")
		self.__write("SM;XN 'VG',1,-3.0,0.")                          # configure Keithley 4200 display X axis
		self.__write("SM;YA 'ID0',1,-10u,0.")                          # configure Keithley 4200 display Y axis
		self.__write("SM;YB 'ID1',1,-10u,0.")                          # configure Keithley 4200 display Y axis
		starttime=time.time()                                                      # measure sweep time
		self.__write("MD;ME1")                                        # trigger for transfer curve measurement
		#self.__parameteranalyzer.wait_for_srq(None)                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
		self.__parameteranalyzer.chunk_size=self.__largechunk
		endtime=time.time()-3
		self.Vgsslew=abs(Vgs_stop-Vgs_start)/(endtime-starttime)
		self.elapsed_time=endtime-starttime
		print("elapsed time of dual backgate transferloop ="+formatnum(self.elapsed_time)+" Vgs slew rate = "+formatnum(self.Vgsslew,precision=2)+" V/sec")
#		print "IV data complete", bin(self.__parameteranalyzer.read_stb())

		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain 0 voltage
		reread = True
		while reread==True:
			Vds0raw = self.__parameteranalyzer.query("DO 'VD0'").split(',')
			self.drain0status_t=[dat[:1] for dat in Vds0raw]
			reread=False
			for x in self.drain0status_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vds0 in single-swept transfer curve")
		self.Vds0_t=[float(dat[1:]) for dat in Vds0raw]
		# read drain 0 current
		reread=True
		while reread==True:
			Id0raw = self.__parameteranalyzer.query("DO 'ID0'").split(',')
			self.drain0status_t=[dat[:1] for dat in Id0raw]
			reread=False
			for x in self.drain0status_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Id0 in single-swept transfer curve")
		self.Id0_t=[float(dat[1:]) for dat in Id0raw]
		# read drain 1 voltage
		reread = True
		while reread==True:
			Vds1raw = self.__parameteranalyzer.query("DO 'VD1'").split(',')
			self.drain1status_t=[dat[:1] for dat in Vds1raw]
			reread=False
			for x in self.drain1status_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vds1 in single-swept transfer curve")
		self.Vds1_t=[float(dat[1:]) for dat in Vds1raw]
		# read drain 1 current
		reread=True
		while reread==True:
			Id1raw = self.__parameteranalyzer.query("DO 'ID1'").split(',')
			self.drain1status_t=[dat[:1] for dat in Id1raw]
			reread=False
			for x in self.drain1status_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Id1 in single-swept transfer curve")
		self.Id1_t=[float(dat[1:]) for dat in Id1raw]
		# read gate0 voltage
		reread=True
		while reread==True:
			Vgs0raw = self.__parameteranalyzer.query("DO 'VG0'").split(',')
			self.gate0status_t=[dat[:1] for dat in Vgs0raw]
			reread=False
			for x in self.gate0status_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vgs0 in single-swept transfer curve")
		self.Vgs0_t=[float(dat[1:]) for dat in Vgs0raw]
		# read gate0 current
		reread=True
		while reread==True:
			Ig0raw = self.__parameteranalyzer.query("DO 'IG0'").split(',')
			self.gate0status_t=[dat[:1] for dat in Ig0raw]
			reread=False
			for x in self.gate0status_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Ig0 in single-swept transfer curve")
		self.Ig0_t=[float(dat[1:]) for dat in Ig0raw]
		# read gate1 voltage
		reread=True
		while reread==True:
			Vgs1raw = self.__parameteranalyzer.query("DO 'VG1'").split(',')
			self.gate1status_t=[dat[:1] for dat in Vgs1raw]
			reread=False
			for x in self.gate1status_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Vgs1 in single-swept transfer curve")
		self.Vgs1_t=[float(dat[1:]) for dat in Vgs1raw]
		# read gate1 current
		reread=True
		while reread==True:
			Ig1raw = self.__parameteranalyzer.query("DO 'IG1'").split(',')
			self.gate1status_t=[dat[:1] for dat in Ig1raw]
			reread=False
			for x in self.gate1status_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Ig1 in single-swept transfer curve")
		self.Ig1_t=[float(dat[1:]) for dat in Ig1raw]
		self.__parameteranalyzer.chunk_size=self.__smallchunk
######################################################################################################################################################
######################################################################################################################################################
# This method oscillates the gate voltage about the final value to remove hysteresis effects
# This assumes that the 4200 is appropriately setup to allow accurate control of the timesteps and does this here
# the gatevoltagechannel is the channel (1,2,3...to max SMU channel number) designated for the gate bias
# Vgs is the final desired, steady-state gate voltage
# Vgsmin is the minimum Vgs setting for the voltage dither
# Vgsmax is the maximum Vgs setting for the voltage dither
# dithertime is the time in sec that the dither oscillations take place over
# timestep is the time that the gate voltage is held at any one step of the dither oscillations
# the dither voltage is an oscillating series of gate voltages whose amplitude shrinks linearly with time over the dither time so as to reduce or eliminate hysteresis effects at the steady-state gate voltage
# not debugged yet
	def ditherVgsvoltage(self,gatevoltagechannel=None,gatecomp=None,Vgs=None,Vgsmax=None,Vgsmin=None,dithertime=None,timestep=0.01):
		self.__parameteranalyzer.clear()
		self.__parameteranalyzer.chunk_size=self.__midchunk

		npts=int(dithertime/timestep)  # assume the minimum timestep of 10mS, self.timestep = self.convert_MT_to_PLC(MT=timestep)  # convert timestep (sec) to integration time in PLC (power line cycles) for 4200, self.timestep is the actual timestep whereas timestep is that requested
		if npts>4090:
			npts=4090
			print("WARNING: number of points exceeds maximum of 4090, increasing timestep")
			timestep=dithertime/npts
			print("new timestep = ",timestep)

		PLC=self.convert_MT_to_PLC(MT=timestep)[0]  # convert timestep (sec) to integration time in PLC (power line cycles) for 4200, self.timestep is the actual timestep whereas timestep is that requested
		self.__write("SS;DT 0")  # set sweep delay=0
		self.__write("SS;HT 0")  # set holdtime to set quiescent time
		self.__write("SM;WT 0")
		self.__write("SM;IN 0")
		Vgsditherfactor=[1.-float(i)/float(npts) for i in range(0,npts)]
		Vgsdither="".join([formatnum(Vgs-Vgsmin*f,precision=2,nonexponential=True)+","+formatnum(Vgs+Vgsmax*f,precision=2,nonexponential=True)+"," for f in Vgsditherfactor ])
		Vgsdither="".join([Vgsdither,formatnum(Vgs,precision=2,nonexponential=True)])
		self.__write("IT4,0,0," + formatnum(PLC, precision=2, nonexponential=True))  # set filterfactor and delay factor both = 0.
		self.__write("SS;VL"+str(gatevoltagechannel)+",1"+formatnum(gatecomp,precision=4,nonexponential=False) + "," + Vgsdither)
		time.sleep(10*npts/4090.)
		self.__write("RI "+str(gatevoltagechannel)+","+formatnum(gatecomp, precision=4, nonexponential=False) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
		self.__write("RG "+str(gatevoltagechannel)+",0.01")  # appears to get rid of autoscaling
		self.__write("MD;ME1")  # trigger
		self.__panpoll()  # wait for transfer curve data sweep to complete
		self.__write("BC")            # throw away data
		self.__parameteranalyzer.chunk_size=self.__smallchunk
#######################################################################################################################################################
# dithers gate voltage prior to setting constant FET Vgs and Vds bias
# This assumes that the 4200 is appropriately setup to allow accurate control of the timesteps and does this here
# the gatevoltagechannel is the channel (1,2,3...to max SMU channel number) designated for the gate bias
# Vgs is the final desired, steady-state gate voltage
# Vgsmin is the minimum Vgs setting for the voltage dither
# Vgsmax is the maximum Vgs setting for the voltage dither
# dithertime is the time in sec that the dither oscillations take place over
# timestep is the time that the gate voltage is held at any one step of the dither oscillations
# the dither voltage is an oscillating series of gate voltages whose amplitude shrinks linearly with time over the dither time so as to reduce or eliminate hysteresis effects at the steady-state gate voltage
# not debugged yet!
	def ditherVgsFETbiason(self,backgated=True,Vds=None,Vgs=None,gatecomp=None,draincomp=None,Vgsmax=None,Vgsmin=None,dithertime=None,timestep=0.01):
		#self.__parameteranalyzer.clear()
		if Vgs<Vgsmin or Vgs>Vgsmax: raise ValueError("ERROR! Vgs out of range")
		Vgsdeltalow=Vgs-Vgsmin
		Vgsdeltahigh=Vgsmax-Vgs
		self.__parameteranalyzer.chunk_size=self.__largechunk
		if abs(Vds) > self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")        # protect probe from overvoltage
		if backgated==False and (abs(Vgsmin)>self.maxvoltageprobe or abs(Vgsmax)>self.maxvoltageprobe or abs(Vgs)>self.maxvoltageprobe): raise ValueError("ERROR! Attempt to apply > safe Vgs voltage to bias Tee and/or probes")        # protect probe from overvoltage
		self.__parameteranalyzer.clear()
		PLC,timestepactual = self.convert_MT_to_PLC(MT=timestep)                     # convert timestep (sec) to integration time in PLC (power line cycles) for 4200, self.timestep is the actual timestep whereas timestep is that requested
		print("from line 829 parameter_analyzer.py, PLC,timestep",PLC,timestepactual)
		ntimepts=int(dithertime/(2*timestep))                                # find number of time points
		if ntimepts>4090:                                                  # maximum allowed number of points in a list sweep is 4096 but set to 4090 to be safe and to allow for the leading time point
			ntimepts=4090
			timestep=dithertime/ntimepts
			print("WARNING! Number of timepoints exceed that allowed for the 4200 so resetting dither timestep to "+formatnum(timestep,precision=2)+" sec")

		#Vgsditherfactor=[1.-float(i)/float(ntimepts) if i%2==0 else -(1.-float(i)/float(ntimepts))  for i in range(0,ntimepts)]
		Vgsditherfactor=[1.-float(i)/float(ntimepts) for i in range(0,ntimepts)]
		# generate Vgs time sequence dither voltage
		Vgsdither="".join([formatnum(Vgs-Vgsdeltalow*f,precision=2,nonexponential=True)+","+formatnum(Vgs+Vgsdeltahigh*f,precision=2,nonexponential=True)+"," for f in Vgsditherfactor ])
		Vgsdither="".join([Vgsdither,formatnum(Vgs,precision=2,nonexponential=True)])

		self.__write("EM 1,0")  # set to 4200 mode
		self.__write("BC;DR1")
		self.__write("SM;DM1")
		self.__write("SS;DT 0.")
		self.__write("SS;HT 0.")
		self.__write("SM;WT 0.")
		self.__write("SM;IN 0.")
		self.__write("SR 1,0")
		self.__write("SR 2,0")
		self.__write("SR 3,0")
		self.__write("SR 4,0")
		self.__write("IT4,0.,0.,"+formatnum(PLC, precision=2, nonexponential=True))  # set filterfactor and delay factor both = 0.
		# set up SMUs for drain and gate
		self.__write("DE")
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")  # first undefine all channels

		if backgated:                        # gate drive channel definition set Vgs = constant gate drive on SMU3 to chuck
			self.__write("DE;CH3,'VG','IG',1,1")  # gate drive channel definition
			self.__write("SS;VL3,1," + formatnum(gatecomp, precision=4, nonexponential=False) + "," + Vgsdither)  # gate drive voltage step
			time.sleep(20.*ntimepts/4090.)
			self.__write("RI 3" + "," + formatnum(gatecomp, precision=4, nonexponential=False) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
			self.__write("RG 3,"+formatnum(number=gatecomp,precision=4,nonexponential=False))  # manual set of gate current range to turn off autoranging
		else:
			self.__write("DE;CH1,'VG','IG',1,1")  # gate drive channel definition set Vgs = constant gate drive on SMU1 to left probe
			self.__write("SS;VL1,1,"+formatnum(gatecomp, precision=4, nonexponential=False) + "," + Vgsdither)  # gate drive voltage step
			#time.sleep(20.*nVgs/4090.)
			self.__write("RI 1" + "," + formatnum(gatecomp, precision=4, nonexponential=False) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
			self.__write("RG 1,"+formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
		self.__write("RI 2" + "," + formatnum(number=draincomp, precision=4, nonexponential=False) + "," + formatnum(draincomp, precision=4, nonexponential=False))  # manual set of device drain current range to turn off autoranging
		self.__write("RG 2,"+formatnum(number=draincomp, precision=4, nonexponential=False))                  # appears to get rid of autoscaling

		self.__write("DE;CH2,'VD','ID',1,3")  # drain drive channel definition VAR1 on SMU2
		self.__write("SS;VC2, " + formatnum(Vds, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=False))  # constant drain voltage drive

		self.__write("SM;LI 'VD','VG','ID','IG'")
		self.__write("SM;XN 'VG',1,-2.0,0.")  # configure Keithley 4200 display X axis
		self.__write("SM;YA 'ID',1,-10u,0.")  # configure Keithley 4200 display Y axis
		self.__write("MD;ME1")  # trigger for transfer curve measurement
		self.__panpoll()
		# if backgated:
		# 	self.__write("US DV3,0,"+str(Vgs)+","+str(gatecomp)+",;ST3,1")           # set up constant gate voltage on SMU1
		# 	self.__write("US DV2,0,"+str(Vds)+","+str(draincomp)+",;ST2,1")          # set up drain voltage on SMU2
		# else:
		# 	self.__write("US DV1,0,"+str(Vgs)+","+str(gatecomp)+",;ST1,1")           # set up gate voltage on SMU1
		# 	self.__write("US DV2,0,"+str(Vds)+","+str(draincomp)+",;ST2,1")          # set up drain voltage on SMU2
		# time.sleep(5)

		# VG=self.__parameteranalyzer.query("DO 'VG'")
		# IG=self.__parameteranalyzer.query("DO 'IG'")
		# VD=self.__parameteranalyzer.query("DO 'VD'")
		# ID=self.__parameteranalyzer.query("DO 'ID'")
		self.__write("BC")            # throw away data
		self.__parameteranalyzer.chunk_size=self.__smallchunk
######################################################################################################################################################
# measure IV family of curves on topgated FET type structures using loop sweep (Vds swept two directions)
# drain is swept while gate is stepped as a constant voltage changed at each gate step
	def measure_ivfoc_Vdsloop_controlledslew(self,backgated=True, startstopzero=False, quiescenttime=0., Vdsslewrate=None, Vds_start=None, Vds_stop=None, draincomp=None, gatecomp=None, Vds_npts=None, Vgs_start=None, Vgs_stop=None, Vgs_npts=None, Vgslist=None):
		self.__parameteranalyzer.clear()
		self.startstopzero=startstopzero
		self.quiescenttime=quiescenttime            # minimum quiescent time prior to starting a Vgs sweep, Vds = 0V for this quiescent time too
		self.__parameteranalyzer.chunk_size=self.__largechunk
		if abs(Vds_start)>self.maxvoltageprobe or abs(Vds_stop)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")  # protect probe from overvoltage
		if not backgated and (abs(Vgs_start) > self.maxvoltageprobe or abs(Vgs_stop) > self.maxvoltageprobe): raise ValueError("ERROR! Attempt to apply > safe Vgs voltage to bias Tee and/or probes")  # protect probe from overvoltage
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		if Vgs_npts>1: Vgs_step=(Vgs_stop-Vgs_start)/(Vgs_npts-1)
		else: Vgs_step=0.
		if Vds_npts>1: Vds_step=(Vds_stop-Vds_start)/(Vds_npts-1)
		else: Vds_step=0.

		if Vgslist==None or len(Vgslist)<1:
			Vgslist=[Vgs_start+Vgs_step*i for i in range(0,Vgs_npts)]

		if not startstopzero:
			Vdssweep1=[Vds_start+Vds_step*i for i in range(0,Vds_npts)]
			Vdssweep2=[Vds_stop-Vds_step*i for i in range(0,Vds_npts)]
			Vdsarr1=",".join([formatnum(Vds,precision=4,nonexponential=True) for Vds in Vdssweep1])
			Vdsarr2=",".join([formatnum(Vds,precision=4,nonexponential=True) for Vds in Vdssweep2])
			Vdssweeparray=",".join([Vdsarr1,Vdsarr2])
		elif startstopzero:
			if int(abs(Vds_start)/Vds_step)-abs(Vds_start)/Vds_step > smallfloat or int(abs(Vds_stop)/Vds_step)-abs(Vds_stop)/Vds_step > smallfloat: raise ValueError("ERROR in Vds_stop-Vds_start vs Vds_step Vgs values must be chosen to include zero and must divide into equal intervals")
			#if abs(Vds_start)/Vds_start + abs(Vds_stop)/Vds_stop > smallfloat: raise ValueError("ERROR! Vds_start and Vds_stop must have opposite sign for Vgs sweeps set to start and stop on Vgs=0V where Vgs visits both + and - ranges")
			nVdsstart=int(abs(Vds_start/Vds_step))+1
			nVdsstop=int(abs(Vds_stop/Vds_step))+1
			Vdssweeparray1st=[formatnum(v,precision=3) for v in np.linspace(start=0.,stop=Vds_start,num=nVdsstart)]
			Vdssweeparray2nd=[formatnum(v,precision=3) for v in np.linspace(start=Vds_start,stop=0.,num=nVdsstart)]
			Vdssweeparray3rd=[formatnum(v,precision=3) for v in np.linspace(start=0,stop=Vds_stop,num=nVdsstop)]
			del Vdssweeparray3rd[0]
			Vdssweeparray4th=[formatnum(v,precision=3) for v in np.linspace(start=Vds_stop,stop=0.,num=nVdsstop)]
			Vdssweeparray = ",".join([",".join(Vdssweeparray1st),",".join(Vdssweeparray2nd),",".join(Vdssweeparray3rd),",".join(Vdssweeparray4th)])
			# if Vds_start!=0: Vdssweeparray = ",".join([",".join(Vdssweeparray1st),",".join(Vdssweeparray2nd),",".join(Vdssweeparray3rd),",".join(Vdssweeparray4th)])
			# else: Vdssweeparray = ",".join(["0.",",".join(Vdssweeparray3rd),",".join(Vdssweeparray4th)])
		else: raise ValueError("ERROR! Illegal value for startstopzero")

		Vds_npts=len(Vdssweeparray.split(','))/2                                    # number of gate voltage points between the maximum and minimum gate voltages
		PLC,MT,Vdsslewnotused=self.get_PLS_MT_fromslewrate(slewrate=Vdsslewrate,Vgsspan=abs(Vds_stop-Vds_start),nVgspts=Vds_npts)        # get PLC which will give target slewrate if possible
		#self.elapsed_time=2*Vds_npts*MT        # total elapsed time of measurement of one drain voltage sweep loop (2x accounts for the up and back)
		self.__write("EM 1,0")  # set to 4200 mode
		self.__write("BC;DR1")
		self.__write("SM;DM1")
		self.__write("SS;DT 0.")
		self.__write("SS;HT 0.")
		self.__write("SM;WT 0.")
		self.__write("SM;IN 0.")
		self.__write("SR 1,0")
		self.__write("SR 2,0")
		self.__write("SR 3,0")
		self.__write("SR 4,0")
		self.__write("IT4,0.,0.,"+formatnum(PLC, precision=2, nonexponential=True))  # set filterfactor and delay factor both = 0.

		# set up SMUs for drain and gate
		self.__write("DE")
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")  # first undefine all channels

		# configure for dual (loop) sweep on drain
		self.__write("DE;CH2,'VD','ID',1,1")  # drain drive channel definition VAR1 on SMU2
		self.__write(",".join(["SS;VL2,1",formatnum(draincomp, precision=4, nonexponential=False),Vdssweeparray]))  # drain drive voltage list
		time.sleep(40.*Vds_npts/4090.)
		self.__write("RG 2,"+formatnum(number=draincomp, precision=4))                  # appears to get rid of autoscaling
		self.__write(",".join(["RI 2",formatnum(number=draincomp, precision=4), formatnum(number=draincomp, precision=4)]))  # manual set of device drain current range to turn off autoranging
		self.__parameteranalyzer.chunk_size=self.__largechunk

		self.Id_loopfoc1 = []
		self.Ig_loopfoc1 = []
		self.Vgs_loopfoc1 = []
		self.Vds_loopfoc1 = []
		self.drainstatus_loopfoc1 = []
		self.gatestatus_loopfoc1 = []
		self.timestamp_loopfoc1=[]
		self.Id_loopfoc2 = []
		self.Ig_loopfoc2 = []
		self.Vgs_loopfoc2 = []
		self.Vds_loopfoc2 = []
		self.drainstatus_loopfoc2 = []
		self.gatestatus_loopfoc2 = []
		self.timestamp_loopfoc2=[]

		for iVgs in range (0, len(Vgslist)):
			if backgated:
				self.__write("DE;CH3,'VG','IG',1,3")                                                                                     # gate drive channel definition SMU 3 voltage source, constant
				self.__write(",".join(["SS;VC3",formatnum(Vgslist[iVgs],precision=4),formatnum(gatecomp,precision=4,nonexponential=False)]))    # gate drive set to constant voltage source
				self.__write("RI 3" + "," + formatnum(gatecomp, precision=4) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
				self.__write("RG 3,"+formatnum(number=gatecomp,precision=4))  # manual set of gate current range to turn off autoranging
			else:
				self.__write("DE;CH1,'VG','IG',1,3")                                                             # gate drive channel definition SMU 1 voltage source, constant
				self.__write(",".join(["SS;VC1",formatnum(Vgslist[iVgs],precision=4),formatnum(gatecomp,precision=4,nonexponential=False)]))    # gate drive set to constant voltage source
				self.__write("RI 1" + "," + formatnum(gatecomp, precision=4) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
				self.__write("RG 1,"+formatnum(gatecomp, precision=4))  # manual set of gate current range to turn off autoranging

			self.__write("SM;LI 'VD','VG','ID','IG'")
			self.__write("SM;XN 'VD',1,-2.0,0.")  # configure Keithley 4200 display X axis
			self.__write("SM;YA 'ID',1,-10u,0.")  # configure Keithley 4200 display Y axis
			self.__write("BC")
			self.__write("MD;ME1")  # trigger for transfer curve measurement
			self.__panpoll()

		# get data from loop sweep
		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage
			reread = True
			while reread == True:
				Vdsraw = self.__parameteranalyzer.query("DO 'VD'").split(',')
				timestampraw = self.__parameteranalyzer.query("DO 'CH2T'").split(',')           # get timestamp data. Assumed that CH2 is always used
				drainstatus_transloop = [dat[:1] for dat in Vdsraw]
				reread = False
				for x in drainstatus_transloop:
					if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
						reread = True
						print("WARNING re-read of Vds in dual-swept transfer curve")
			Vds_transloop = [float(dat[1:]) for dat in Vdsraw]
			ts=[float(dat) for dat in timestampraw]
			# read drain current
			reread = True
			while reread == True:
				Idraw = self.__parameteranalyzer.query("DO 'ID'").split(',')
				drainstatus_transloop = [dat[:1] for dat in Idraw]
				reread = False
				for x in drainstatus_transloop:
					if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
						reread = True
						print("WARNING re-read of Id in dual-swept transfer curve")
			Id_transloop = [float(dat[1:]) for dat in Idraw]
			# read gate voltage
			reread = True
			while reread == True:
				Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
				gatestatus_transloop = [dat[:1] for dat in Vgsraw]
				reread = False
				for x in gatestatus_transloop:
					if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
						reread = True
						print("WARNING re-read of Vgs in dual-swept transfer curve")
			Vgs_transloop = [float(dat[1:]) for dat in Vgsraw]
			# read gate current
			reread = True
			while reread == True:
				Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
				gatestatus_transloop = [dat[:1] for dat in Igraw]
				reread = False
				for x in gatestatus_transloop:
					if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
						reread = True
						print("WARNING re-read of Ig in dual-swept transfer curve")
			Ig_transloop = [float(dat[1:]) for dat in Igraw]

			####### now separate out forward and reverse Vds sweep	if not startstopzero:
			self.Id_loopfoc1.append([])
			self.Ig_loopfoc1.append([])
			self.Vgs_loopfoc1.append([])
			self.Vds_loopfoc1.append([])
			self.drainstatus_loopfoc1.append([])
			self.gatestatus_loopfoc1.append([])
			self.timestamp_loopfoc1.append([])
			self.Id_loopfoc2.append([])
			self.Ig_loopfoc2.append([])
			self.Vgs_loopfoc2.append([])
			self.Vds_loopfoc2.append([])
			self.drainstatus_loopfoc2.append([])
			self.gatestatus_loopfoc2.append([])
			self.timestamp_loopfoc2.append([])

			if not startstopzero:
				for ii in range(0, len(Vdssweep1)):  # first Vds sweep
					self.Id_loopfoc1[-1].append(Id_transloop[ii])
					self.Ig_loopfoc1[-1].append(Ig_transloop[ii])
					self.Vgs_loopfoc1[-1].append(Vgs_transloop[ii])
					self.Vds_loopfoc1[-1].append(Vds_transloop[ii])
					self.drainstatus_loopfoc1[-1].append(drainstatus_transloop[ii])
					self.gatestatus_loopfoc1[-1].append(gatestatus_transloop[ii])
					self.timestamp_loopfoc1[-1].append(ts[ii])
				for ii in range(len(Vdssweep1), len(Vdssweep1)+len(Vdssweep2)):  # return (2nd) sweep of Vds
					self.Id_loopfoc2[-1].append(Id_transloop[ii])
					self.Ig_loopfoc2[-1].append(Ig_transloop[ii])
					self.Vgs_loopfoc2[-1].append(Vgs_transloop[ii])
					self.Vds_loopfoc2[-1].append(Vds_transloop[ii])
					self.drainstatus_loopfoc2[-1].append(drainstatus_transloop[ii])
					self.gatestatus_loopfoc2[-1].append(gatestatus_transloop[ii])
					self.timestamp_loopfoc2[-1].append(ts[ii])
			elif startstopzero:
				for ii in range(len(Vdssweeparray1st), len(Vdssweeparray1st)+len(Vdssweeparray2nd)+len(Vdssweeparray3rd)):  # 1st reverse section of Vds sweep
					self.Id_loopfoc2[-1].append(Id_transloop[ii])
					self.Ig_loopfoc2[-1].append(Ig_transloop[ii])
					self.Vgs_loopfoc2[-1].append(Vgs_transloop[ii])
					self.Vds_loopfoc2[-1].append(Vds_transloop[ii])
					self.drainstatus_loopfoc2[-1].append(drainstatus_transloop[ii])
					self.gatestatus_loopfoc2[-1].append(gatestatus_transloop[ii])
					self.timestamp_loopfoc2[-1].append(ts[ii])
				for ii in range(len(Vdssweeparray1st)+len(Vdssweeparray2nd)+len(Vdssweeparray3rd), len(Id_transloop)):  # 2nd forward section of Vds sweep
					self.Id_loopfoc1[-1].append(Id_transloop[ii])
					self.Ig_loopfoc1[-1].append(Ig_transloop[ii])
					self.Vgs_loopfoc1[-1].append(Vgs_transloop[ii])
					self.Vds_loopfoc1[-1].append(Vds_transloop[ii])
					self.drainstatus_loopfoc1[-1].append(drainstatus_transloop[ii])
					self.gatestatus_loopfoc1[-1].append(gatestatus_transloop[ii])
					self.timestamp_loopfoc1[-1].append(ts[ii])
				for ii in range(0, len(Vdssweeparray1st)):  # 1st forward section of Vds sweep
					self.Id_loopfoc1[-1].append(Id_transloop[ii])
					self.Ig_loopfoc1[-1].append(Ig_transloop[ii])
					self.Vgs_loopfoc1[-1].append(Vgs_transloop[ii])
					self.Vds_loopfoc1[-1].append(Vds_transloop[ii])
					self.drainstatus_loopfoc1[-1].append(drainstatus_transloop[ii])
					self.gatestatus_loopfoc1[-1].append(gatestatus_transloop[ii])
					self.timestamp_loopfoc1[-1].append(ts[ii])
			else: raise ValueError("ERROR! Illegal value for startstopzero")
		self.elapsed_time=max(ts)            # measured total elapsed time of this measurement in sec
		self.Vdsslew=2.*abs(Vds_stop-Vds_start)/self.elapsed_time                       # actual measured slew rate in V/sec
		self.__parameteranalyzer.chunk_size=self.__smallchunk
######################################################################################################################################################
######################################################################################################################################################
# measure IV family of curves on topgated FET type structures using loop sweep (Vds swept two directions)
# drain is swept while gate is stepped as a constant voltage changed at each gate step
# sweeps two loops
# TODO "Warning! Only the startstopzero option is presently working!
	def measure_ivfoc_Vdsloop_4sweep_controlledslew(self,backgated=True, startstopzero=False, quiescenttime=0., Vdsslewrate=None, Vds_start=None, Vds_stop=None, draincomp=None, gatecomp=None, Vds_npts=None, Vgs_start=None, Vgs_stop=None, Vgs_npts=None, Vgslist=None):
		self.__parameteranalyzer.clear()
		if startstopzero==False: raise ValueError("ERROR! startstopzero=False is NOT available yet, presently must start and stop sweep at Vds=0V")
		self.startstopzero=startstopzero
		self.quiescenttime=quiescenttime            # minimum quiescent time prior to starting a Vgs sweep, Vds = 0V for this quiescent time too
		self.__parameteranalyzer.chunk_size=self.__largechunk
		if abs(Vds_start)>self.maxvoltageprobe or abs(Vds_stop)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")  # protect probe from overvoltage
		if not backgated and (abs(Vgs_start) > self.maxvoltageprobe or abs(Vgs_stop) > self.maxvoltageprobe): raise ValueError("ERROR! Attempt to apply > safe Vgs voltage to bias Tee and/or probes")  # protect probe from overvoltage
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		if Vgs_npts>1: Vgs_step=(Vgs_stop-Vgs_start)/(Vgs_npts-1)
		else: Vgs_step=0.
		if Vds_npts>1: Vds_step=(Vds_stop-Vds_start)/(Vds_npts-1)
		else: Vds_step=0.

		if Vgslist==None or len(Vgslist)<1:
			Vgslist=[Vgs_start+Vgs_step*i for i in range(0,Vgs_npts)]

		if not startstopzero:
			Vdssweep1=[Vds_start+Vds_step*i for i in range(0,Vds_npts)]
			Vdssweep2=[Vds_stop-Vds_step*i for i in range(0,Vds_npts)]
			Vdsarr1=",".join([formatnum(Vds,precision=4,nonexponential=True) for Vds in Vdssweep1])
			Vdsarr2=",".join([formatnum(Vds,precision=4,nonexponential=True) for Vds in Vdssweep2])
			Vdssweeparray=",".join([Vdsarr1,Vdsarr2])
		elif startstopzero:
			if int(abs(Vds_start)/Vds_step)-abs(Vds_start)/Vds_step > smallfloat or int(abs(Vds_stop)/Vds_step)-abs(Vds_stop)/Vds_step > smallfloat: raise ValueError("ERROR in Vds_stop-Vds_start vs Vds_step Vds values must be chosen to include zero and must divide into equal intervals")
			if abs(Vds_start)/Vds_start + abs(Vds_stop)/Vds_stop > smallfloat: raise ValueError("ERROR! Vds_start and Vds_stop must have opposite sign for Vds sweeps set to start and stop on Vds=0V where Vds visits both + and - ranges")
			nVdsstart=int(abs(Vds_start/Vds_step))+1
			nVdsstop=int(abs(Vds_stop/Vds_step))+1
			Vdssweeparray1st=[formatnum(v,precision=3) for v in np.linspace(start=0.,stop=Vds_start,num=nVdsstart)]
			Vdssweeparray2nd=[formatnum(v,precision=3) for v in np.linspace(start=Vds_start,stop=0.,num=nVdsstart)]
			Vdssweeparray3rd=[formatnum(v,precision=3) for v in np.linspace(start=0,stop=Vds_stop,num=nVdsstop)]
			del Vdssweeparray3rd[0]
			Vdssweeparray4th=[formatnum(v,precision=3) for v in np.linspace(start=Vds_stop,stop=0.,num=nVdsstop)]
			Vdssweeparray = ",".join([",".join(Vdssweeparray1st),",".join(Vdssweeparray2nd),",".join(Vdssweeparray3rd),",".join(Vdssweeparray4th)])
			# add on a second loop
			del Vdssweeparray1st[0]
			Vdssweeparray = ",".join([Vdssweeparray,",".join(Vdssweeparray1st),",".join(Vdssweeparray2nd),",".join(Vdssweeparray3rd),",".join(Vdssweeparray4th)])
		else: raise ValueError("ERROR! Illegal value for startstopzero")

		Vds_npts=len(Vdssweeparray.split(','))/4                                    # number of gate voltage points between the maximum and minimum gate voltages
		PLC,MT,Vdsslewnotused=self.get_PLS_MT_fromslewrate(slewrate=Vdsslewrate,Vgsspan=abs(Vds_stop-Vds_start),nVgspts=Vds_npts)        # get PLC which will give target slewrate if possible
		#self.elapsed_time=2*Vds_npts*MT        # total elapsed time of measurement of one drain voltage sweep loop (2x accounts for the up and back)
		self.__write("EM 1,0")  # set to 4200 mode
		self.__write("BC;DR1")
		self.__write("SM;DM1")
		self.__write("SS;DT 0.")
		self.__write("SS;HT 0.")
		self.__write("SM;WT 0.")
		self.__write("SM;IN 0.")
		self.__write("SR 1,0")
		self.__write("SR 2,0")
		self.__write("SR 3,0")
		self.__write("SR 4,0")
		self.__write("IT4,0.,0.,"+formatnum(PLC, precision=2, nonexponential=True))  # set filterfactor and delay factor both = 0.

		# set up SMUs for drain and gate
		self.__write("DE")
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")  # first undefine all channels

		# configure for dual (loop) sweep on drain
		self.__write("DE;CH2,'VD','ID',1,1")  # drain drive channel definition VAR1 on SMU2
		self.__write(",".join(["SS;VL2,1",formatnum(draincomp, precision=4, nonexponential=False),Vdssweeparray]))  # drain drive voltage list
		time.sleep(40.*Vds_npts/4090.)
		self.__write("RG 2,"+formatnum(number=draincomp, precision=4))                  # appears to get rid of autoscaling
		self.__write(",".join(["RI 2",formatnum(number=draincomp, precision=4), formatnum(number=draincomp, precision=4)]))  # manual set of device drain current range to turn off autoranging
		self.__parameteranalyzer.chunk_size=self.__largechunk

		self.Id_loopfoc1 = []
		self.Ig_loopfoc1 = []
		self.Vgs_loopfoc1 = []
		self.Vds_loopfoc1 = []
		self.drainstatus_loopfoc1 = []
		self.gatestatus_loopfoc1 = []
		self.timestamp_loopfoc1=[]
		self.Id_loopfoc2 = []
		self.Ig_loopfoc2 = []
		self.Vgs_loopfoc2 = []
		self.Vds_loopfoc2 = []
		self.drainstatus_loopfoc2 = []
		self.gatestatus_loopfoc2 = []
		self.timestamp_loopfoc2=[]
		self.Id_loopfoc3 = []
		self.Ig_loopfoc3 = []
		self.Vgs_loopfoc3 = []
		self.Vds_loopfoc3 = []
		self.drainstatus_loopfoc3 = []
		self.gatestatus_loopfoc3 = []
		self.timestamp_loopfoc3=[]
		self.Id_loopfoc4 = []
		self.Ig_loopfoc4 = []
		self.Vgs_loopfoc4 = []
		self.Vds_loopfoc4 = []
		self.drainstatus_loopfoc4 = []
		self.gatestatus_loopfoc4 = []
		self.timestamp_loopfoc4=[]

		for iVgs in range (0, len(Vgslist)):
			if backgated:
				self.__write("DE;CH3,'VG','IG',1,3")                                                                                     # gate drive channel definition SMU 3 voltage source, constant
				self.__write(",".join(["SS;VC3",formatnum(Vgslist[iVgs],precision=4),formatnum(gatecomp,precision=4,nonexponential=False)]))    # gate drive set to constant voltage source
				self.__write("RI 3" + "," + formatnum(gatecomp, precision=4) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
				self.__write("RG 3,"+formatnum(number=gatecomp,precision=4))  # manual set of gate current range to turn off autoranging
			else:
				self.__write("DE;CH1,'VG','IG',1,3")                                                             # gate drive channel definition SMU 1 voltage source, constant
				self.__write(",".join(["SS;VC1",formatnum(Vgslist[iVgs],precision=4),formatnum(gatecomp,precision=4,nonexponential=False)]))    # gate drive set to constant voltage source
				self.__write("RI 1" + "," + formatnum(gatecomp, precision=4) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
				self.__write("RG 1,"+formatnum(gatecomp, precision=4))  # manual set of gate current range to turn off autoranging

			self.__write("SM;LI 'VD','VG','ID','IG'")
			self.__write("SM;XN 'VD',1,-2.0,2.")  # configure Keithley 4200 display X axis
			self.__write("SM;YA 'ID',1,-3E-4,5E-4")  # configure Keithley 4200 display Y axis
			self.__write("BC")
			self.__write("MD;ME1")  # trigger for transfer curve measurement

			self.__panpoll()

		# get data from loop sweep
		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage
			reread = True
			while reread == True:
				Vdsraw = self.__parameteranalyzer.query("DO 'VD'").split(',')
				timestampraw = self.__parameteranalyzer.query("DO 'CH2T'").split(',')           # get timestamp data. Assumed that CH2 is always used
				drainstatus_transloop = [dat[:1] for dat in Vdsraw]
				reread = False
				for x in drainstatus_transloop:
					if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
						reread = True
						print("WARNING re-read of Vds in 4-swept transfer curve")
			Vds_transloop = [float(dat[1:]) for dat in Vdsraw]
			ts=[float(dat) for dat in timestampraw]
			# read drain current
			reread = True
			while reread == True:
				Idraw = self.__parameteranalyzer.query("DO 'ID'").split(',')
				drainstatus_transloop = [dat[:1] for dat in Idraw]
				reread = False
				for x in drainstatus_transloop:
					if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
						reread = True
						print("WARNING re-read of Id in 4-swept transfer curve")
			Id_transloop = [float(dat[1:]) for dat in Idraw]
			# read gate voltage
			reread = True
			while reread == True:
				Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
				gatestatus_transloop = [dat[:1] for dat in Vgsraw]
				reread = False
				for x in gatestatus_transloop:
					if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
						reread = True
						print("WARNING re-read of Vgs in 4-swept transfer curve")
			Vgs_transloop = [float(dat[1:]) for dat in Vgsraw]
			# read gate current
			reread = True
			while reread == True:
				Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
				gatestatus_transloop = [dat[:1] for dat in Igraw]
				reread = False
				for x in gatestatus_transloop:
					if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
						reread = True
						print("WARNING re-read of Ig in 4-swept transfer curve")
			Ig_transloop = [float(dat[1:]) for dat in Igraw]

			####### now separate out the four Vds sweeps
			self.Id_loopfoc1.append([])
			self.Ig_loopfoc1.append([])
			self.Vgs_loopfoc1.append([])
			self.Vds_loopfoc1.append([])
			self.drainstatus_loopfoc1.append([])
			self.gatestatus_loopfoc1.append([])
			self.timestamp_loopfoc1.append([])
			self.Id_loopfoc2.append([])
			self.Ig_loopfoc2.append([])
			self.Vgs_loopfoc2.append([])
			self.Vds_loopfoc2.append([])
			self.drainstatus_loopfoc2.append([])
			self.gatestatus_loopfoc2.append([])
			self.timestamp_loopfoc2.append([])
			self.Id_loopfoc3.append([])
			self.Ig_loopfoc3.append([])
			self.Vgs_loopfoc3.append([])
			self.Vds_loopfoc3.append([])
			self.drainstatus_loopfoc3.append([])
			self.gatestatus_loopfoc3.append([])
			self.timestamp_loopfoc3.append([])
			self.Id_loopfoc4.append([])
			self.Ig_loopfoc4.append([])
			self.Vgs_loopfoc4.append([])
			self.Vds_loopfoc4.append([])
			self.drainstatus_loopfoc4.append([])
			self.gatestatus_loopfoc4.append([])
			self.timestamp_loopfoc4.append([])
			# dumi1=[]
			# dumi2=[]
			# dumi3=[]
			# dumi4=[]
			if not startstopzero:
				for ii in range(0, len(Vdssweep1)):  # first Vds sweep
					self.Id_loopfoc1[-1].append(Id_transloop[ii])
					self.Ig_loopfoc1[-1].append(Ig_transloop[ii])
					self.Vgs_loopfoc1[-1].append(Vgs_transloop[ii])
					self.Vds_loopfoc1[-1].append(Vds_transloop[ii])
					self.drainstatus_loopfoc1[-1].append(drainstatus_transloop[ii])
					self.gatestatus_loopfoc1[-1].append(gatestatus_transloop[ii])
					self.timestamp_loopfoc1[-1].append(ts[ii])
				for ii in range(len(Vdssweep1), len(Vdssweep1)+len(Vdssweep2)):  # return (2nd) sweep of Vds
					self.Id_loopfoc2[-1].append(Id_transloop[ii])
					self.Ig_loopfoc2[-1].append(Ig_transloop[ii])
					self.Vgs_loopfoc2[-1].append(Vgs_transloop[ii])
					self.Vds_loopfoc2[-1].append(Vds_transloop[ii])
					self.drainstatus_loopfoc2[-1].append(drainstatus_transloop[ii])
					self.gatestatus_loopfoc2[-1].append(gatestatus_transloop[ii])
					self.timestamp_loopfoc2[-1].append(ts[ii])
			elif startstopzero:
				lenVdssweeparray1st=len(Vdssweeparray1st)+1
				istart2ndloop=lenVdssweeparray1st+len(Vdssweeparray2nd)+len(Vdssweeparray3rd)+len(Vdssweeparray4th)-1
				#for ii in range(lenVdssweeparray1st, lenVdssweeparray1st+len(Vdssweeparray2nd)+len(Vdssweeparray3rd)):  # 1st forward Vds sweep
				for ii in range(lenVdssweeparray1st, lenVdssweeparray1st+len(Vdssweeparray2nd)+len(Vdssweeparray3rd)):  # 1st loop voltage swept from start to zero, i.e. 2nd sweep
					self.Id_loopfoc2[-1].append(Id_transloop[ii])
					self.Ig_loopfoc2[-1].append(Ig_transloop[ii])
					self.Vgs_loopfoc2[-1].append(Vgs_transloop[ii])
					self.Vds_loopfoc2[-1].append(Vds_transloop[ii])
					self.drainstatus_loopfoc2[-1].append(drainstatus_transloop[ii])
					self.gatestatus_loopfoc2[-1].append(gatestatus_transloop[ii])
					self.timestamp_loopfoc2[-1].append(ts[ii])
				#for ii in range(lenVdssweeparray1st+len(Vdssweeparray2nd)+len(Vdssweeparray3rd), istart2ndloop):  # 1st reverse Vds sweep, 2nd section
				for ii in range(istart2ndloop+lenVdssweeparray1st+len(Vdssweeparray2nd)+len(Vdssweeparray3rd), istart2ndloop+lenVdssweeparray1st+len(Vdssweeparray2nd)+len(Vdssweeparray3rd) + len(Vdssweeparray4th)):  # final half sweep Vgsstop to 0V
					self.Id_loopfoc1[-1].append(Id_transloop[ii])
					self.Ig_loopfoc1[-1].append(Ig_transloop[ii])
					self.Vgs_loopfoc1[-1].append(Vgs_transloop[ii])
					self.Vds_loopfoc1[-1].append(Vds_transloop[ii])
					self.drainstatus_loopfoc1[-1].append(drainstatus_transloop[ii])
					self.gatestatus_loopfoc1[-1].append(gatestatus_transloop[ii])
					self.timestamp_loopfoc1[-1].append(ts[ii])
				for ii in range(0, lenVdssweeparray1st):  #  # 1st reverse Vds sweep, 1st section
					self.Id_loopfoc1[-1].append(Id_transloop[ii])
					self.Ig_loopfoc1[-1].append(Ig_transloop[ii])
					self.Vgs_loopfoc1[-1].append(Vgs_transloop[ii])
					self.Vds_loopfoc1[-1].append(Vds_transloop[ii])
					self.drainstatus_loopfoc1[-1].append(drainstatus_transloop[ii])
					self.gatestatus_loopfoc1[-1].append(gatestatus_transloop[ii])
					self.timestamp_loopfoc1[-1].append(ts[ii])
				# 2nd loop
				for ii in range(istart2ndloop+lenVdssweeparray1st, istart2ndloop+lenVdssweeparray1st+len(Vdssweeparray2nd)+len(Vdssweeparray3rd)):  # 2nd forward Vds sweep
					self.Id_loopfoc4[-1].append(Id_transloop[ii])
					self.Ig_loopfoc4[-1].append(Ig_transloop[ii])
					self.Vgs_loopfoc4[-1].append(Vgs_transloop[ii])
					self.Vds_loopfoc4[-1].append(Vds_transloop[ii])
					self.drainstatus_loopfoc4[-1].append(drainstatus_transloop[ii])
					self.gatestatus_loopfoc4[-1].append(gatestatus_transloop[ii])
					self.timestamp_loopfoc4[-1].append(ts[ii])
				#for ii in range(istart2ndloop+lenVdssweeparray1st+len(Vdssweeparray2nd)+len(Vdssweeparray3rd), len(Id_transloop)):  # 2nd reverse Vds sweep, 2nd section
				for ii in range(lenVdssweeparray1st+len(Vdssweeparray2nd)+len(Vdssweeparray3rd), istart2ndloop):  # reverse Vds sweep, 2nd section
					self.Id_loopfoc3[-1].append(Id_transloop[ii])
					self.Ig_loopfoc3[-1].append(Ig_transloop[ii])
					self.Vgs_loopfoc3[-1].append(Vgs_transloop[ii])
					self.Vds_loopfoc3[-1].append(Vds_transloop[ii])
					self.drainstatus_loopfoc3[-1].append(drainstatus_transloop[ii])
					self.gatestatus_loopfoc3[-1].append(gatestatus_transloop[ii])
					self.timestamp_loopfoc3[-1].append(ts[ii])
				for ii in range(istart2ndloop+1, istart2ndloop+lenVdssweeparray1st):  #  # 2nd reverse Vds sweep, 1st section
					# dumi3.append(ii)
					self.Id_loopfoc3[-1].append(Id_transloop[ii])
					self.Ig_loopfoc3[-1].append(Ig_transloop[ii])
					self.Vgs_loopfoc3[-1].append(Vgs_transloop[ii])
					self.Vds_loopfoc3[-1].append(Vds_transloop[ii])
					self.drainstatus_loopfoc3[-1].append(drainstatus_transloop[ii])
					self.gatestatus_loopfoc3[-1].append(gatestatus_transloop[ii])
					self.timestamp_loopfoc3[-1].append(ts[ii])
			else: raise ValueError("ERROR! Illegal value for startstopzero")
		self.elapsed_time=max(ts)            # measured total elapsed time of this measurement in sec
		self.Vdsslew=4.*abs(Vds_stop-Vds_start)/self.elapsed_time                       # actual measured slew rate in V/sec
		self.__parameteranalyzer.chunk_size=self.__smallchunk
######################################################################################################################################################

#####################################################################################################################################################
# measure transfer curve with Vgs dither prior to each Id, Ig measurement while stepping Vgs in each direction (two Vgs stepping sequences)
# drain voltage Vds is held constant during this test
# for each measurement, Vgs is dithered between Vgsmindither and Vgsmaxdither with timestep/dither voltage = dithertimestep then, at the final dither point, the measurements are taken
# the final delay time = soaktime, which is a final soaktime, is the time between the end of the dither sequence and the time of measurement. During this time Vgs and Vds are held constant, at their measurement values
	def measure_tranfer_Vgsdither(self,backgated=True, Vds=None,gatecomp=None,draincomp=None,Vgsmaxdither=None,Vgsmindither=None,dithertime=None,Vgs_start=None,Vgs_stop=None,Vgs_step=None,dithertimestep=0.01,soaktime=0):
		self.__parameteranalyzer.clear()
		self.__parameteranalyzer.chunk_size=self.__largechunk
		self.dithertime=dithertime
		self.dithertimestep=dithertimestep
		self.soaktime=soaktime
		Vgs_npts=1+int(abs((Vgs_stop-Vgs_start)/Vgs_step))
		Vgssteps=np.linspace(Vgs_start,Vgs_stop,Vgs_npts)

		if abs(Vds)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")  # protect probe from overvoltage
		if not backgated and (abs(Vgs_start) > self.maxvoltageprobe or abs(Vgs_stop) > self.maxvoltageprobe): raise ValueError("ERROR! Attempt to apply > safe Vgs voltage to bias Tee and/or probes")  # protect probe from overvoltage
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		if Vgs_npts>1: Vgs_step=(Vgs_stop-Vgs_start)/(Vgs_npts-1)
		else: Vgs_step=0.
		# set up dither timesteps
		ntimepts=1+int(dithertime/dithertimestep)                                # find number of time points in the dither sequence
		nptssoak=1+int(soaktime/dithertimestep)                           # number of time points in the final delay prior to measurement - i.e. final soak time
		if ntimepts+nptssoak>4090:                                                  # maximum allowed number of points in a list sweep is 4096 but set to 4090 to be safe and to allow for the leading time point
			ntimepts=4090-nptssoak
			timestep=dithertime/ntimepts
			print("WARNING! Number of timepoints exceed that allowed for the 4200 so resetting dither timestep to "+formatnum(timestep,precision=2)+" sec")

		PLC,timestepactual = self.convert_MT_to_PLC(MT=dithertimestep)                     # convert timestep (sec) to integration time in PLC (power line cycles) for 4200, self.timestep is the actual timestep whereas timestep is that requested
		print("from line 3543 parameter_analyzer.py, PLC,timestep",PLC,timestepactual)

		self.__write("EM 1,0")  # set to 4200 mode
		self.__write("BC;DR1")
		self.__write("SM;DM1")
		self.__write("SS;DT 0.")
		self.__write("SS;HT 0.")
		self.__write("SM;WT 0.")
		self.__write("SM;IN 0.")
		self.__write("SR 1,0")
		self.__write("SR 2,0")
		self.__write("SR 3,0")
		self.__write("SR 4,0")
		self.__write("IT4,0.,0.,"+formatnum(PLC, precision=2, nonexponential=True))  # set filterfactor and delay factor both = 0.

		# set up SMUs for drain and gate
		self.__write("DE")
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2")  # first undefine all channels

		if backgated:
			self.__write("DE;CH3,'VG','IG',1,1")  # gate drive channel definition VAR1 on SMU1
			self.__write("RG 3,"+formatnum(number=gatecomp,precision=4))  # manual set of gate current range to turn off autoranging
			self.__write("RI 3" + "," + formatnum(gatecomp, precision=4) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
		else:
			self.__write("DE;CH1,'VG','IG',1,1")  # gate drive channel definition VAR1 on SMU3
			self.__write("RG 1,"+formatnum(number=gatecomp,precision=4))  # manual set of gate current range to turn off autoranging
			self.__write("RI 1" + "," + formatnum(gatecomp, precision=4) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging

		self.__write("DE;CH2,'VD','ID',1,3")           # drain channel definition voltage source, constant on SMU2
		self.__write(",".join(["SS;VC2",formatnum(Vds,precision=4),formatnum(draincomp,precision=4,nonexponential=False)]))
		self.__write(",".join(["RI 2",formatnum(number=draincomp, precision=4), formatnum(number=draincomp, precision=4)]))  # manual set of device drain current range to turn off autoranging
		self.__write("RG 2,"+formatnum(number=draincomp, precision=4))                  # appears to get rid of autoscaling
		self.__parameteranalyzer.chunk_size=self.__largechunk

		self.Id_t= []
		self.Ig_t = []
		self.Vgs_t = []
		self.Vds_t = []
		self.drainstatus_t = []
		self.gatestatus_t = []
		validstatus={'N','L','V','X','C','T'}
		for Vgs in Vgssteps:
		# configure for dither list on gate
			Vgsdeltalow=Vgs-Vgsmindither
			Vgsdeltahigh=Vgsmaxdither-Vgs
			Vgsditherfactor=[1.-float(i)/float(ntimepts) for i in range(0,ntimepts)]
			# generate Vgs time sequence dither voltage
			Vgsdither=",".join([",".join([formatnum(Vgs-Vgsdeltalow*f,precision=2,nonexponential=True),formatnum(Vgs+Vgsdeltahigh*f,precision=2,nonexponential=True)]) for f in Vgsditherfactor ])      # create dither Vgs sequence
			Vgsfinal=",".join([formatnum(Vgs,precision=2) for i in range(0,nptssoak)])        # create final Vgs soak
			Vgsdither=",".join([Vgsdither,Vgsfinal])       # add final Vgs soak to end of dither
			self.__write(",".join(["RI 2",formatnum(number=draincomp, precision=4), formatnum(number=draincomp, precision=4)]))  # manual set of device drain current range to turn off autoranging
			self.__write("RG 2,"+formatnum(number=draincomp, precision=4))                  # appears to get rid of autoscaling
			if backgated:
				self.__write(",".join(["SS;VL3,1",formatnum(draincomp, precision=4, nonexponential=False),Vgsdither]))  # channel 3 gate drive voltage list for dither + measure
				self.__write("RG 3,"+formatnum(number=gatecomp,precision=4))  # manual set of gate current range to turn off autoranging
				self.__write("RI 3" + "," + formatnum(gatecomp, precision=4) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
			else:
				self.__write(",".join(["SS;VL1,1",formatnum(draincomp, precision=4, nonexponential=False),Vgsdither]))  # channel 1 gate drive voltage list for dither + measure
				self.__write("RG 1,"+formatnum(number=gatecomp,precision=4))  # manual set of gate current range to turn off autoranging
				self.__write("RI 1" + "," + formatnum(gatecomp, precision=4) + "," + formatnum(gatecomp, precision=4, nonexponential=False))  # manual set of gate current range to turn off autoranging
			time.sleep(40.*ntimepts/4090.)          # to allow time to load Vgs time series points

			self.__write("SM;LI 'VD','VG','ID','IG'")
			#self.__write("SM;XN 'VD',1,-2.0,0.")  # configure Keithley 4200 display X axis
			self.__write(",".join(["SM;XT 0.",formatnum(dithertime+soaktime)]))
			self.__write("SM;YA 'VG',1,-4,1")  # configure Keithley 4200 display Y axis
			self.__write("MD;ME1")  # trigger for transfer curve measurement
			self.__panpoll()

			# read last point of data, i.e. the data at the end of the Vgs soak time
			reread = True
			while reread == True:
				Vdsraw = self.__parameteranalyzer.query("DO 'VD'").split(',')
				#print("Vdsraw", Vdsraw)
				drainstatus = [dat[:1] for dat in Vdsraw]
				reread = False
				if not set(drainstatus).issubset(validstatus):
					reread = True
					print("WARNING re-read of Vds in dither Vgs transfer curve")
			self.Vds_t.append(float(Vdsraw[-1][1:]))       # take last point of Vgs dither sequence i.e. last data point in Vgs soak
			self.drainstatus_t.append(drainstatus[-1])
			# read drain current
			reread = True
			while reread == True:
				Idraw = self.__parameteranalyzer.query("DO 'ID'").split(',')
				drainstatus = [dat[:1] for dat in Idraw]
				reread = False
				if not set(drainstatus).issubset(validstatus):
					reread = True
					print("WARNING re-read of Id in dither Vgs transfer curve")
			self.Id_t.append(float(Idraw[-1][1:]))
			# read gate voltage
			reread = True
			while reread == True:
				Vgsraw = self.__parameteranalyzer.query("DO 'VG'").split(',')
				gatestatus = [dat[:1] for dat in Vgsraw]
				reread = False
				if not set(gatestatus).issubset(validstatus):
					reread = True
					print("WARNING re-read of Vgs in dither Vgs transfer curve")
			self.Vgs_t.append(float(Vgsraw[-1][1:]))
			self.gatestatus_t.append(gatestatus[-1])
			# read gate current
			reread = True
			while reread == True:
				Igraw = self.__parameteranalyzer.query("DO 'IG'").split(',')
				gatestatus = [dat[:1] for dat in Igraw]
				reread = False
				if not set(gatestatus).issubset(validstatus):
					reread = True
					print("WARNING re-read of Ig in dither Vgs transfer curve")
			self.Ig_t.append(float(Igraw[-1][1:]))
		#self.__write("ST 3")
		self.__parameteranalyzer.chunk_size=self.__smallchunk
######################################################################################################################################################
#######################################################################################################################################################
#	__calculate_gm = X_calculate_gm
#	__calculate_gmloop = X_calculate_gmloop
	writefile_ivfoc = X_writefile_ivfoc
	writefile_ivfoc_dual = X_writefile_ivfoc_dual
	writefile_ivtransfer = X_writefile_ivtransfer
	writefile_ivtransfer_dual = X_writefile_ivtransfer_dual
	writefile_ivtransferloop = X_writefile_ivtransferloop
	writefile_ivtransferloop_dual = X_writefile_ivtransferloop_dual
	writefile_ivtransferloop_4sweep_dual = X_writefile_ivtransferloop_4sweep_dual
	writefile_ivtransferloop_4sweep = X_writefile_ivtransferloop_4sweep
	writefile_burnsweepVds=X_writefile_burnsweepVds
	writefile_burnonesweepVds=X_writefile_burnonesweepVds
	writefile_burnonefinalvaluessweepVds=X_writefile_burnonefinalvaluessweepVds
	writefile_pulsedtransfertimedomain4200=X_writefile_pulsedtransfertimedomain4200
	writefile_pulsedtimedomain4200=X_writefile_pulsedtimedomain4200
	writefile_baddeviceslist = X_writefile_baddeviceslist
	writefile_ivfoc_Vdsloop = X_writefile_ivfoc_Vdsloop
	writefile_ivfoc_Vds4sweep = X_writefile_ivfoc_Vds4sweep
	writefile_probecleanlog = X_writefile_probecleanlog
######################################################################################################################################################
# WARNING! BC,DR1 must be executed as a setup OR this polling WILL NOT WORK
# setting waittime>0 makes the polling loop a timeout loop instead where the program just sleeps for the time specified by waittime in seconds
	def __panpoll(self,waittime=None):
		if waittime!=None and waittime>0.:
			time.sleep(waittime)
			return
		time.sleep(0.5)
		if self.__LAN:                  # is the parameter analyzer interfaced via LAN?
			donemeasuring=False
			while not donemeasuring:
				sb=self.__parameteranalyzer.query("SP")
				#print("in loop sb = ",sb)
				time.sleep(2.)
				if int(sb)&2: #raise ValueError("ERROR! from __panpoll() syntax error")
					print("WARNING from line 4160 panpoll() parameter_analyzer.py syntax error")
				if (int(sb)&1 and int(sb)&64) and not (int(sb)&16): donemeasuring=True      # done on status bit #1 which indicates data read is complete
				else: donemeasuring=False

				#if (int(sb)&1 and int(sb)&64) and not (int(sb)&16): donemeasuring=True      # done on status bit #1 which indicates data read is complete
				# if (int(sb)&1 and int(sb)&64) and not (int(sb)&16):
				# 	sb1=self.__parameteranalyzer.query("SP")
				# 	time.sleep(0.5)
				# 	sb2=self.__parameteranalyzer.query("SP")
				# 	time.sleep(0.5)
				# 	if ((int(sb1)&1 and int(sb1)&64) and not (int(sb1)&16)) and ((int(sb2)&1 and int(sb2)&64) and not (int(sb2)&16)): donemeasuring=True
			#print ("after break sp",sb)

			while 1:        # read status byte until = 0
				time.sleep(0.2)
				print("before sb read")
				sb=self.__parameteranalyzer.query("SP")
				time.sleep(0.2)
				print("after read again sb =",sb)
				if int(sb)==0:
					print("break out of final polling loop")
					break
			time.sleep(0.2)
			#self.__parameteranalyzer.write("BC")
		else:                           # GPIB
			while True:
				try: sb=self.__parameteranalyzer.read_stb()
				except:
					print ("error in sb read retry")
					continue
				if int(sb)==65: break
				time.sleep(0.4)
		time.sleep(.5)                                      # minimum time here to prevent read errors is 2sec
#########################################################################################################################################################
# modifed write for LAN or GPIB
	def __write(self,cmd,*args):
		if self.__LAN:
			if args==None or len(args)==0: self.__parameteranalyzer.write(cmd)
			elif len(args)==1: self.__parameteranalyzer.write(cmd,args[0])
			elif len(args)==2: self.__parameteranalyzer.write(cmd,args[0],args[1])
			elif len(args)>2: raise ValueError("ERROR line 2947 in parameter_analyzer.py Too many arguments for instruction (>2)")
			notACK=True
			ack=""
			time.sleep(0.1)  #added Dec 12, 2017
			while notACK and (args==None or len(args)==0):       # account for acknowledgement delays i.e. for long write of data up to 4200
				try: ack=self.__parameteranalyzer.read()
				except: pass
				time.sleep(0.1)  #added Nov 9, 2017
				if ack=="ACK": notACK=False
		else:   # GPIB
			self.__parameteranalyzer.write(cmd)
#######################################################################################################################################################