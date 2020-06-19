# setup and usage of the Keithley 4200 semiconductor parameter analyzer
# input is the handle for the VISA resource manager
#from calculated_parameters import *
import time
import visa
from writefile_measured import *
import collections as col
#import timeit
from utilities import formatnum, floatequal
import numpy as np
import collections as c

settlingtime=0.2                                             # time we allow this semiconductor parameter analyzer to settle after changing voltages
class ParameterAnalyzer:
# set up of parameter analyzer
	def __init__(self,rm,LAN=True):                                  # setup of Keithley parameter analyzer
		self.__LAN=LAN
		try:
			if LAN:
				self.t=""
				self.__rm=rm
				self.__parameteranalyzer = self.__rm.open_resource('TCPIP0::192.168.1.12::1225::SOCKET') # LAN
				self.__parameteranalyzer.read_termination='\00'
				self.__parameteranalyzer.write_termination='\00'
				opt=self.__parameteranalyzer.query("*OPT?")
				print(opt)
			else:
				self.t=""
				self.__parameteranalyzer = rm.open_resource('GPIB0::2::INSTR')     # GPIB
		except:
			print ("ERROR on Keithley 4200 semiconductor parameter analyzer: Could not find on GPIB\n")
			print ("Check Keithley On?, GPIB=2?, and/or KXCI running on Keithley?")
		#self.__parameteranalyzer.query_delay=.0001            # set up query delay to prevent errors
		self.__parameteranalyzer.chunk_size=5000
		#self.__parameteranalyzer.term_chars="\0"
		#self.__parameteranalyzer.send_end=True
		print (self.__parameteranalyzer.query("ID"+self.t))
		#self.__parameteranalyzer.write("SRE 1")
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
# set constant bias and read drain and gate currents. This is useful for taking S-parameter measurements
	def fetbiason_topgate(self, Vgs=None, Vds=None, gatecomp=1.E-5, draincomp=0.1):                 # set constant bias and measure gate and drain currents. Bias is left on at exit
	# set up SMUs for drain and gate
		self.__parameteranalyzer.clear()
		if abs(Vds)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		if abs(Vgs)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs voltage to bias Tee and/or probes")
		Vdsrange = 1.1E-7
		Vgsrange = 1.1E-7
		self.Vgs_bias = Vgs														# eventually want to read Vgs from the instrument
		self.Vds_bias = Vds														# eventually want to read Vgs from the instrument
		self.__parameteranalyzer.write("EM 1,0"+self.t)								# set to 4200 mode
		self.__parameteranalyzer.write("IT1;BC;DR0"+self.t)                            # MUST be set to DR0 otherwise will mess up polling on measurements that call panpoll() because we don't call panpoll() here
		self.__parameteranalyzer.write("US DV1;SR1,0"+self.t)
		self.__parameteranalyzer.write("US DV2;SR2,0"+self.t)
		self.__parameteranalyzer.write("US DV3;SR3,0"+self.t)
		self.__parameteranalyzer.write("US DV4;SR4,0"+self.t)
		self.__parameteranalyzer.write("US DV1,0,"+str(Vgs)+","+str(gatecomp)+",;ST1,1"+self.t)           # set up gate voltage on SMU1
		self.__parameteranalyzer.write("RG 1,"+str(Vgsrange)+self.t)
		self.__parameteranalyzer.write("US DV2,0,"+str(Vds)+","+str(draincomp)+",;ST2,1"+self.t)          # set up drain voltage on SMU2
		self.__parameteranalyzer.write("RG 2,"+str(Vdsrange)+self.t)
		time.sleep(settlingtime)                                              # power supply settling time before measurement to allow charging of system etc...
		#self.__panpoll()
		Ialpha = self.__parameteranalyzer.query("TI2"+self.t)                       # measure drain current
#    print "Ialpha is ",Ialpha                                   # debug
		Id_bias = float(Ialpha[3:])                                     # read drain current by stripping off the first 3 characters
		drainstatus_bias = Ialpha[:1]                                    # read drain status flag
		Ialpha = self.__parameteranalyzer.query("TI1"+self.t)             # measure gate current
		Ig_bias = float(Ialpha[3:])                                     # read gate current by stripping off the first 3 characters
		gatestatus_bias = Ialpha[:1]                                    # read gate status flag
		time.sleep(settlingtime)                                              # power supply settling time before measurement to allow charging of system etc...
		return Id_bias, Ig_bias,drainstatus_bias,gatestatus_bias            # to be used to see if devices are worth measuring further
#removed all self. from variables, similar to fetbiason_dual_backgate (ahmad)
	# note that the bias is left on at exit
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
		if abs(Vds)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes"+self.t)
		Vdsrange = 1.1E-7
		Vgsrange = 1.1E-7
		self.Vgs_bias = Vgs														# eventually want to read Vgs from the instrument
		self.Vds_bias = Vds														# eventually want to read Vgs from the instrument
		self.__parameteranalyzer.write("EM 1,0"+self.t)								# set to 4200 mode
		#self.__parameteranalyzer.write("IT1;BC;DR1"+self.t)
		self.__parameteranalyzer.write("IT"+inttime+";BC;DR0"+self.t)                  # MUST be set to DR0 otherwise will mess up polling on measurements that call panpoll()
		self.__parameteranalyzer.write("US DV1;SR1,0"+self.t)
		self.__parameteranalyzer.write("US DV2;SR2,0"+self.t)
		self.__parameteranalyzer.write("US DV3;SR3,0"+self.t)
		self.__parameteranalyzer.write("US DV4;SR4,0"+self.t)
		self.__parameteranalyzer.write("US DV3,0,"+str(Vgs)+","+str(gatecomp)+",;ST3,1"+self.t)           # set up gate voltage on SMU3
		self.__parameteranalyzer.write("RG 3,"+str(Vgsrange)+self.t)
		self.__parameteranalyzer.write("US DV2,0,"+str(Vds)+","+str(draincomp)+",;ST2,1"+self.t)          # set up drain voltage on SMU2
		self.__parameteranalyzer.write("RG 2,"+str(Vdsrange)+self.t)
		time.sleep(settlingtime)                                              # power supply settling time before measurement to allow charging of system etc...
		#self.__panpoll()
		Ialpha = self.__parameteranalyzer.query("TI2"+self.t)                       # measure drain current
		self.Id_bias = float(Ialpha[3:])                                     # read drain current by stripping off the first 3 characters
		self.drainstatus_bias = Ialpha[:1]                                    # read drain status flag
		Ialpha = self.__parameteranalyzer.query("TI1"+self.t)             # measure gate current
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
	# set up SMUs for drain and gate
		self.__parameteranalyzer.clear()
		if abs(Vds0)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds0 voltage to bias Tee and/or probes")
		if abs(Vds1)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds1 voltage to bias Tee and/or probes")
		self.__parameteranalyzer.write("EM 1,0"+self.t)								# set to 4200 mode
		self.__parameteranalyzer.write("IT1;BC;DR0"+self.t)                            # MUST be set to DR0 otherwise will mess up polling on measurements that call panpoll()
		self.__parameteranalyzer.write("US DV1;SR1,0"+self.t)
		self.__parameteranalyzer.write("US DV2;SR2,0"+self.t)
		self.__parameteranalyzer.write("US DV3;SR3,0"+self.t)
		self.__parameteranalyzer.write("US DV4;SR4,0"+self.t)
		self.__parameteranalyzer.write("US DV3,0,"+str(Vgs)+","+str(gatecomp)+",;ST3,1"+self.t)           # set up gate voltage on SMU3
		self.__parameteranalyzer.write("RG 3,"+str(Vgsrange)+self.t)
		self.__parameteranalyzer.write("US DV1,0,"+str(Vds0)+","+str(draincomp0)+",;ST1,1"+self.t)           # set up drain0 voltage on SMU1
		self.__parameteranalyzer.write("RG 1,"+str(Vds0range)+self.t)
		self.__parameteranalyzer.write("US DV2,0,"+str(Vds1)+","+str(draincomp1)+",;ST2,1"+self.t)          # set up drain1 voltage on SMU2
		self.__parameteranalyzer.write("RG 2,"+str(Vds1range)+self.t)
		time.sleep(settlingtime)                                              # power supply settling time before measurement to allow charging of system etc...

		Ialpha = self.__parameteranalyzer.query("TI1"+self.t)                       # measure drain0 current
		Id0_bias = float(Ialpha[3:])                                     # read drain0 current by stripping off the first 3 characters
		drainstatus0_bias = Ialpha[:1]                                    # read drain0 status flag
		Ialpha = self.__parameteranalyzer.query("TI2"+self.t)                       # measure drain1 current
		Id1_bias = float(Ialpha[3:])                                     # read drain1 current by stripping off the first 3 characters
		drainstatus1_bias = Ialpha[:1]                                    # read drain status flag
		self.drainstatus1_bias = Ialpha[:1]                                    # read drain status flag
		Ialpha = self.__parameteranalyzer.query("TI3"+self.t)             			# measure gate current
		Ig_bias = float(Ialpha[3:])                                     # read gate current by stripping off the first 3 characters
		gatestatus_bias = Ialpha[:1]                                    # read gate status flag
		time.sleep(settlingtime)                                              # power supply settling time before measurement to allow charging of system etc...
		return Id0_bias, Id1_bias, Ig_bias, drainstatus0_bias, drainstatus1_bias, gatestatus_bias            # to be used to see if devices are worth measuring further
	# note that the bias is left on at exit
######################################################################################################################################################
# methods to return values from fetbiason

######################################################################################################################################################
# turn off all SMUs
	def fetbiasoff(self):                                               # turn off fet bias turns off all SMUs
		self.__parameteranalyzer.clear()
	# set up SMUs for drain and gate
		self.__parameteranalyzer.write("US DV1;SR1,0"+self.t)
		self.__parameteranalyzer.write("US DV2;SR2,0"+self.t)
		self.__parameteranalyzer.write("US DV3;SR3,0"+self.t)
		self.__parameteranalyzer.write("US DV4;SR4,0"+self.t)
		time.sleep(settlingtime)                                         # allow capacitances to discharge etc..
######################################################################################################################################################
# measure IV family of curves on topgated FET type structures
	def measure_ivfoc_topgate(self, inttime='2', Vds_start=None, Vds_stop=None, draincomp=None, Vds_npts=None, Vgs_start=None, Vgs_stop=None, gatecomp=None, Vgs_npts=None):
		self.__parameteranalyzer.clear()
		if abs(Vds_start)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds_start voltage to bias Tee and/or probes")
		if abs(Vds_stop)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds_stop voltage to bias Tee and/or probes")
		if abs(Vgs_start)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs_start voltage to bias Tee and/or probes")
		if abs(Vgs_stop)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vgs_stop voltage to bias Tee and/or probes")
		Vds_step = (Vds_stop-Vds_start)/(Vds_npts-1)
		if Vgs_npts>1: Vgs_step = float(Vgs_stop-Vgs_start)/float(Vgs_npts-1)
		else: Vgs_step=0.           # just one curve
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.write("IT"+inttime+";BC;DR1"+self.t)
		self.__parameteranalyzer.write("EM 1,1"+self.t)
# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE"+self.t)
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)                                               # first undefine all channels

		self.__parameteranalyzer.write("DE;CH1,'VG','IG',1,2"+self.t)                                                             # gate drive channel definition VAR2
		self.__parameteranalyzer.write("SS;VP "+str(Vgs_start)+","+str(Vgs_step)+","+str(Vgs_npts)+","+str(gatecomp)+self.t)         # gate drive
		self.__parameteranalyzer.write("DE;CH2,'VD','ID',1,1"+self.t)                                                              # drain drive channel definition VAR1
		self.__parameteranalyzer.write("SS;VR1,"+str(Vds_start)+","+str(Vds_stop)+","+str(Vds_step)+","+str(draincomp)+self.t)         # drain drive

		self.__parameteranalyzer.write("SM;DM1"+self.t)
		self.__parameteranalyzer.write("SM;LI 'VD','VG','ID','IG'"+self.t)
		self.__parameteranalyzer.write("SM;XN 'VD',1,-2.0,0."+self.t)                          # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID',1,-10u,0."+self.t)                          # configure Keithley 4200 display Y axis
		self.__parameteranalyzer.write("MD;ME1"+self.t)                                        # trigger for IV measurement

		self.__panpoll()

		Id_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'ID'"+self.t).split(',')]
		Ig_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')]
		Vgs_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')]
		Vds_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')]
		# find status of drain and gate bias e.g. detect compliance

		drainstatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')]
		gatestatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')]

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
					drainstatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')]
				self.drainstatus_foc[iVgs].append(drainstatus_foc1d[ii])
				while not (gatestatus_foc1d[ii]=='N' or gatestatus_foc1d[ii]=='L' or gatestatus_foc1d[ii]=='V'  or gatestatus_foc1d[ii]=='X'  or gatestatus_foc1d[ii]=='C' or gatestatus_foc1d[ii]=='T'):
					print ("WARNING! gatestatus_foc1d =", gatestatus_foc1d) #debug
					gatestatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')]
				self.gatestatus_foc[iVgs].append(gatestatus_foc1d[ii])
				# if not (drainstatus_foc1d[ii]=='N' or drainstatus_foc1d[ii]=='L' or drainstatus_foc1d[ii]=='V'  or drainstatus_foc1d[ii]=='X'  or drainstatus_foc1d[ii]=='C' or drainstatus_foc1d[ii]=='T'):
				# 	print ("drainstatus_foc1d =", drainstatus_foc1d) #debug
				# 	raise ValueError('ERROR drainstatus= '+drainstatus_foc1d)
				# self.drainstatus_foc[iVgs].append(drainstatus_foc1d[ii])
				# if not (gatestatus_foc1d[ii]=='N' or gatestatus_foc1d[ii]=='L' or gatestatus_foc1d[ii]=='V'  or gatestatus_foc1d[ii]=='X'  or gatestatus_foc1d[ii]=='C' or gatestatus_foc1d[ii]=='T'):
				# 	raise ValueError('ERROR gatestatus= '+gatestatus_foc1d)
				# self.gatestatus_foc[iVgs].append(gatestatus_foc1d[ii])

######################################################################################################################################################
######################################################################################################################################################
# measure IV family of curves on backgated FET type structures
	def measure_ivfoc_backgate(self, inttime='2', delayfactor=2,filterfactor=1,integrationtime=1, Vds_start=None, Vds_stop=None, draincomp=None, Vds_npts=None, Vgs_start=None, Vgs_stop=None, gatecomp=None, Vgs_npts=None):
		self.__parameteranalyzer.clear()
		if not(inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		if abs(Vds_start)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds_start voltage to bias Tee and/or probes")
		if abs(Vds_stop)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds_stop voltage to bias Tee and/or probes")

		Vds_step = (Vds_stop-Vds_start)/(Vds_npts-1)
		if Vgs_npts>1: Vgs_step = float(Vgs_stop-Vgs_start)/float(Vgs_npts-1)
		else: Vgs_step=0.           # just one curve
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.write("IT"+inttime+";BC;DR1"+self.t)
		self.__parameteranalyzer.write("EM 1,1"+self.t)
# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE"+self.t)
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)                                               # first undefine all channels

		self.__parameteranalyzer.write("DE;CH3,'VG','IG',1,2"+self.t)                                                             # gate drive channel definition VAR2 i.e. SMU3 for gate
		self.__parameteranalyzer.write("SS;VP "+str(Vgs_start)+","+str(Vgs_step)+","+str(Vgs_npts)+","+str(gatecomp)+self.t)         # gate drive
		self.__parameteranalyzer.write("DE;CH2,'VD','ID',1,1"+self.t)                                                              # drain drive channel definition VAR1 SMU2
		self.__parameteranalyzer.write("SS;VR1,"+str(Vds_start)+","+str(Vds_stop)+","+str(Vds_step)+","+str(draincomp)+self.t)         # drain drive

		self.__parameteranalyzer.write("SM;DM1"+self.t)
		self.__parameteranalyzer.write("SM;LI 'VD','VG','ID','IG'"+self.t)
		self.__parameteranalyzer.write("SM;XN 'VD',1,-2.0,0."+self.t)                          # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID',1,-10u,0."+self.t)                          # configure Keithley 4200 display Y axis
		self.__parameteranalyzer.write("MD;ME1"+self.t)                                        # trigger for IV measurement
		#self.__parameteranalyzer.write("DR1"+self.t)
		#self.__parameteranalyzer.wait_for_srq()                                         # wait for IV data sweep to complete
		#print "status byte1", self.__parameteranalyzer.read_stb()
		#print "status byte2", self.__parameteranalyzer.read_stb()
		# measured IV family of curves
		#print "status byte ready to read", self.__parameteranalyzer.read_stb()
		self.__panpoll()
		#while 1:
			#try:
		Id_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'ID'"+self.t).split(',')]
		Ig_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')]
		Vgs_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')]
		Vds_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')]
		# find status of drain and gate bias e.g. detect compliance

		drainstatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')]
		gatestatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')]

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
					drainstatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')]
				self.drainstatus_foc[iVgs].append(drainstatus_foc1d[ii])
				while not (gatestatus_foc1d[ii]=='N' or gatestatus_foc1d[ii]=='L' or gatestatus_foc1d[ii]=='V'  or gatestatus_foc1d[ii]=='X'  or gatestatus_foc1d[ii]=='C' or gatestatus_foc1d[ii]=='T'):
					print ("WARNING! gatestatus_foc1d =", gatestatus_foc1d) #debug
					gatestatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')]
				self.gatestatus_foc[iVgs].append(gatestatus_foc1d[ii])
######################################################################################################################################################
# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with sweep in one direction
	def measure_ivtransfer_topgate(self, inttime='2', delayfactor=2,filterfactor=1,integrationtime=1, Vds=None,draincomp=None, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=None):
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
		print ("IV tranfercurve start") # debug
		self.__parameteranalyzer.write("EM 1,0"+self.t)								# set to 4200 mode
		self.__parameteranalyzer.write("IT"+inttime+";BC;DR1"+self.t)
		self.__parameteranalyzer.write("SM;DM1"+self.t)

# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE"+self.t)
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)     # first undefine all channels

		self.__parameteranalyzer.write("DE;CH1,'VG','IG',1,1"+self.t)                          # gate drive channel definition set Vgs set to sweep VAR1
		self.__parameteranalyzer.write("SS;VR1,"+str(Vgs_start)+","+str(Vgs_stop)+","+str(Vgs_step)+","+str(gatecomp)+self.t)         # gate drive
		self.__parameteranalyzer.write("DE;CH2,'VD','ID',1,3"+self.t)                         # drain drive channel definition VAR1
		self.__parameteranalyzer.write("SS;VC2, "+str(Vds)+","+str(draincomp)+self.t)         # constant drain voltage drive

		self.__parameteranalyzer.write("SM;LI 'VD','VG','ID','IG'"+self.t)
		self.__parameteranalyzer.write("SM;XN 'VG',1,-2.0,0."+self.t)                          # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID',1,-10u,0."+self.t)                          # configure Keithley 4200 display Y axis
		self.__parameteranalyzer.write("MD;ME1"+self.t)                                        # trigger for transfer curve measurement
		#self.__parameteranalyzer.wait_for_srq(None)                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
#		print "IV data complete", bin(self.__parameteranalyzer.read_stb())

		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage
		reread = True
		while reread==True:
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')
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
			Idraw = self.__parameteranalyzer.query("DO 'ID'"+self.t).split(',')
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
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')
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
			Igraw = self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')
			self.gatestatus_t=[dat[:1] for dat in Igraw]
			reread=False
			for x in self.gatestatus_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Ig in single-swept transfer curve")
		self.Ig_t=[float(dat[1:]) for dat in Igraw]

######################################################################################################################################################
######################################################################################################################################################
# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with sweep in one direction
# for gate voltage applied to the chuck (SMU3)
	def measure_ivtransfer_backgate(self, inttime='2', Iautorange=True,delayfactor='2',filterfactor='1',integrationtime=1, Vds=None, draincomp=None, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=None):
		self.__parameteranalyzer.clear()
		if not(inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		if abs(Vds)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")

		print ("IV tranfercurve start") # debug
		self.__parameteranalyzer.write("EM 1,0"+self.t)								# set to 4200 mode
		self.__parameteranalyzer.write("IT"+inttime+";BC;DR1"+self.t)
		self.__parameteranalyzer.write("SM;DM1"+self.t)

# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE"+self.t)
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)     # first undefine all channels

		self.__parameteranalyzer.write("DE;CH3,'VG','IG',1,1"+self.t)                			# gate drive channel definition set to VAR1 sweep
		self.__parameteranalyzer.write("SS;VR1,"+str(Vgs_start)+","+str(Vgs_stop)+","+str(Vgs_step)+","+str(gatecomp)+self.t)         # gate drive
		self.__parameteranalyzer.write("DE;CH2,'VD','ID',1,3"+self.t)                         # drain drive channel definition VAR1
		self.__parameteranalyzer.write("SS;VC2, "+str(Vds)+","+str(draincomp)+self.t)         # constant drain voltage drive

		if custom == True and Iautorange == False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__parameteranalyzer.write("RI 2" + "," + str(draincomp) + "," + str(draincomp)+self.t)  # allow manual set of right device drain current range to turn off autoranging
			self.__parameteranalyzer.write("RI 3" + "," + str(gatecomp) + "," + str(gatecomp)+self.t)  # allow manual set of gate current range to turn off autoranging

		self.__parameteranalyzer.write("SM;LI 'VD','VG','ID','IG'"+self.t)
		self.__parameteranalyzer.write("SM;XN 'VG',1,-2.0,0."+self.t)                          # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID',1,-10u,0."+self.t)                          # configure Keithley 4200 display Y axis
		self.__parameteranalyzer.write("MD;ME1"+self.t)                                        # trigger for transfer curve measurement
		#self.__parameteranalyzer.wait_for_srq(None)                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
#		print "IV data complete", bin(self.__parameteranalyzer.read_stb())

		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage
		reread = True
		while reread==True:
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')
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
			Idraw = self.__parameteranalyzer.query("DO 'ID'"+self.t).split(',')
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
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')
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
			Igraw = self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')
			self.gatestatus_t=[dat[:1] for dat in Igraw]
			reread=False
			for x in self.gatestatus_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Ig in single-swept transfer curve")
		self.Ig_t=[float(dat[1:]) for dat in Igraw]

######################################################################################################################################################
		# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with a loop sweep e.g. sweep high to low then low to high
	def measure_ivtransferloop_topgate(self, inttime='2', Iautorange=True, delayfactor=2,filterfactor=0,integrationtime=1, sweepdelay=0.0,holdtime=0.0, Vds=None, draincomp=None, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=None):
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
		print ("IV tranferloop start") # debug
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		nVgs = int(abs((Vgs_stop-Vgs_start)/Vgs_step))+1							# number of gate bias for one direction of Vgs sweep
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
		self.__parameteranalyzer.write("EM 1,0"+self.t)								# set to 4200 mode
		self.__parameteranalyzer.write("IT"+inttime+";BC;DR1"+self.t)
		self.__parameteranalyzer.write("SM;DM1"+self.t)

# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE"+self.t)
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)				# first undefine all channels

# configure for dual (loop) sweep
		self.__parameteranalyzer.write("DE;CH1,'VG','IG',1,1"+self.t)                # gate drive channel definition set Vgs = constant
		self.__parameteranalyzer.write("SS;VL1,1,"+str(gatecomp)+","+Vgssweeparray+self.t)         # gate drive for sweep
		self.__parameteranalyzer.write("DE;CH2,'VD','ID',1,3"+self.t)                         # drain drive channel definition VAR1
		self.__parameteranalyzer.write("SS;VC2, "+str(Vds)+","+str(draincomp)+self.t)         # constant drain voltage drive
		self.__parameteranalyzer.write("SS;DT ", str(sweepdelay)+self.t)
		self.__parameteranalyzer.write("SS;HT ", str(holdtime)+self.t)
		if custom==True and Iautorange==False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__parameteranalyzer.write("RI 2" + "," + str(draincomp) + "," + str(draincomp)+self.t)  # allow manual set of right device drain current range to turn off autoranging
			self.__parameteranalyzer.write("RI 1" + "," + str(gatecomp) + "," + str(gatecomp)+self.t)  # allow manual set of gate current range to turn off autoranging

		self.__parameteranalyzer.write("SM;LI 'VD','VG','ID','IG'"+self.t)
		self.__parameteranalyzer.write("SM;XN 'VG',1,-2.0,0."+self.t)                          # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID',1,-10u,0."+self.t)                          # configure Keithley 4200 display Y axis
		starttime = time.time()  # measure sweep time
		self.__parameteranalyzer.write("MD;ME1"+self.t)                                        # trigger for transfer curve measurement
		#self.__parameteranalyzer.wait_for_srq()                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
		endtime = time.time()-3
		self.elapsed_time=endtime-starttime
		self.Vgsslew = 2.*abs(Vgs_stop - Vgs_start)/(self.elapsed_time)
		print("elapsed time of topgate transferloop =" + formatnum(endtime - starttime) + " Vgs slew rate = " + formatnum(self.Vgsslew, precision=2) + " V/sec")
# get data from loop sweep
# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage
		reread = True
		while reread==True:
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')
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
			Idraw = self.__parameteranalyzer.query("DO 'ID'"+self.t).split(',')
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
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')
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
			Igraw = self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')
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
		for ii in range(0, nVgs):  # positive portion of sweep Vgs array
			Vgssweeparray += str(Vgs_start + ii * Vgs_step) + ","
		for ii in range(nVgs - 1, -1, -1):  # negative portion of sweep Vgs array
			if ii > 0:
				Vgssweeparray += str(Vgs_start + ii * Vgs_step) + ","
			else:
				Vgssweeparray += str(Vgs_start + ii * Vgs_step)  # last element
			#		print "Vgssweeparray is ",Vgssweeparray									# debug
		# self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.write("EM 1,0"+self.t)  # set to 4200 mode
		self.__parameteranalyzer.write("IT" + inttime + ";BC;DR1"+self.t)
		self.__parameteranalyzer.write("SM;DM1"+self.t)

		# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE"+self.t)
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)  # first undefine all channels

		# configure for dual (loop) sweep
		self.__parameteranalyzer.write("DE;CH1,'VG','IG',1,1"+self.t)  # gate drive channel definition set Vgs = constant
		self.__parameteranalyzer.write("SS;VL1,1," + str(gatecomp) + "," + Vgssweeparray+self.t)  # gate drive for sweep

		self.__parameteranalyzer.write("DE;CH3,'VB','IB',1,3"+self.t)  # backgate channel definition Vbackgate=constant
		self.__parameteranalyzer.write("SS;VC3, " + str(Vbackgate) + "," + str(backgatecomp)+self.t)  # constant backgate voltage drive

		self.__parameteranalyzer.write("DE;CH2,'VD','ID',1,3"+self.t)  # drain drive channel definition VAR1
		self.__parameteranalyzer.write("SS;VC2, " + str(Vds) + "," + str(draincomp)+self.t)  # constant drain voltage drive


		self.__parameteranalyzer.write("SS;DT ", str(sweepdelay)+self.t)
		self.__parameteranalyzer.write("SS;HT ", str(holdtime)+self.t)

		if custom == True and Iautorange == False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain, gate, and backgate current
			self.__parameteranalyzer.write("RI 3" + "," + str(backgatecomp) + "," + str(backgatecomp)+self.t)  # allow manual set of device backgate current range to turn off autoranging
			self.__parameteranalyzer.write("RI 2" + "," + str(draincomp) + "," + str(draincomp)+self.t)  # allow manual set of device drain current range to turn off autoranging
			self.__parameteranalyzer.write("RI 1" + "," + str(gatecomp) + "," + str(gatecomp)+self.t)  # allow manual set of gate current range to turn off autoranging

		self.__parameteranalyzer.write("SM;LI 'VD','VG','ID','IG'"+self.t)
		self.__parameteranalyzer.write("SM;XN 'VG',1,-2.0,0."+self.t)  # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID',1,-10u,0."+self.t)  # configure Keithley 4200 display Y axis
		starttime = time.time()  # measure sweep time
		self.__parameteranalyzer.write("MD;ME1"+self.t)  # trigger for transfer curve measurement
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
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')
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
			Idraw = self.__parameteranalyzer.query("DO 'ID'"+self.t).split(',')
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
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')
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
			Igraw = self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')
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
			Vbgraw = self.__parameteranalyzer.query("DO 'VB'"+self.t).split(',')
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
			Ibgraw = self.__parameteranalyzer.query("DO 'IB'"+self.t).split(',')
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
# Backgate devices use CH3, SMU3 as the gate while topgated devices use CH1, SMU1 as the gate. In all cases, CH2, SMU2 is used as the drain
	def measure_hysteresistimedomain(self, Vds=None, backgated=True, Vgsquiescent=0., timestep=0.01, timequiescent=1.,timeend=1.,Vgs_start=None, Vgs_stop=None, Vgs_step=None, draincomp=None, gatecomp=None):
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
			self.ntimepts = int(timeend / self.timestep)
			print("WARNING! Number of timepoints exceed that allowed for the 4200 so resetting end time to "+formatnum(timeend,precision=2)+" sec")
		# set up input Vgs array to sweep through all gate voltages
		nVgs = int(abs((Vgs_stop-Vgs_start)/Vgs_step))+1							# number of gate bias for one direction of Vgs sweep
		self.Vgssweeparray= c.deque()
		self.td=c.deque()                                                       # timestamps for time-domain points
		for ii in range(0,nVgs):												# positive portion of sweep Vgs array
			self.Vgssweeparray.append(Vgs_start+ii*Vgs_step)
			#self.td.append(ii+1*self.timestep)                                   # timestamps array for time-domain
		#self.__parameteranalyzer.clear()
		self.__parameteranalyzer.write("EM 1,0"+self.t)								# set to 4200 mode
		self.__parameteranalyzer.write("BC;DR1"+self.t)
		self.__parameteranalyzer.write("SM;DM1"+self.t)
		self.__parameteranalyzer.write("IT4,0,0,"+formatnum(PLC,precision=2,nonexponential=True))              # set filterfactor and delay factor both = 0.
		# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE"+self.t)
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)				# first undefine all channels

		if backgated: self.__parameteranalyzer.write("DE;CH3,'VG','IG',1,1"+self.t)                          # gate drive channel definition set Vgs = constant gate drive on SMU3 to chuck
		else: self.__parameteranalyzer.write("DE;CH1,'VG','IG',1,1"+self.t)                          # gate drive channel definition set Vgs = constant gate drive on SMU1 to left probe
		self.__parameteranalyzer.write("DE;CH2,'VD','ID',1,3"+self.t)                         # drain drive channel definition VAR1 on SMU2
		self.__parameteranalyzer.write("SS;VC2, "+str(self.Vdsset)+","+str(draincomp)+self.t)         # constant drain voltage drive
		self.__parameteranalyzer.write("SS;DT 0"+self.t)                              # set sweep delay=0
		self.__parameteranalyzer.write("SS;HT ",formatnum(holdtime,precision=4,nonexponential=True)+self.t)            # set holdtime to set quiescent time
		self.__parameteranalyzer.write("SM;WT 0"+self.t)
		self.__parameteranalyzer.write("SM;IN 0"+self.t)

		self.__parameteranalyzer.write("RI 2" + "," + formatnum(draincomp,precision=4,nonexponential=True) + "," + formatnum(draincomp,precision=4,nonexponential=True)+self.t)  # manual set of right device drain current range to turn off autoranging
		if backgated: self.__parameteranalyzer.write("RI 3" + "," + formatnum(gatecomp,precision=4,nonexponential=True) + "," + formatnum(gatecomp,precision=4,nonexponential=True)+self.t)  # manual set of gate current range to turn off autoranging
		else: self.__parameteranalyzer.write("RI 1" + "," + formatnum(gatecomp,precision=4,nonexponential=True) + "," + formatnum(gatecomp,precision=4,nonexponential=True)+self.t)  # manual set of gate current range to turn off autoranging
		self.__parameteranalyzer.write("SR 1,1"+self.t)
		self.__parameteranalyzer.write("SR 2,1"+self.t)
		self.__parameteranalyzer.write("SR 3,1"+self.t)
		self.__parameteranalyzer.write("SR 4,1"+self.t)

		self.td=c.deque()           # timestamp
		self.Vds_td=c.deque()
		self.Id_td=c.deque()
		self.Vgs_td=c.deque()
		self.Ig_td=c.deque()
		self.gatestatus_td=c.deque()
		self.drainstatus_td=c.deque()
		########### get time-domain Ids for each Vgs ##################################################
		for Vgs in self.Vgssweeparray:
			#Vgsconstantarray="".join([','+formatnum(ii*1,precision=1,nonexponential=True) for ii in range(1,11)] )           # test debug insert steps to test
			Vgsconstantarray="".join([','+formatnum(Vgs,precision=1,nonexponential=True)]*self.ntimepts)                        # constant-voltage time series for gate bias
			Vgsconstantarray=formatnum(self.Vgsquiescent,precision=2,nonexponential=True)+Vgsconstantarray                      # add quiescent point to time series for gate bias
			# configure for sweep
			if backgated:
				self.__parameteranalyzer.write("SS;VL3,1," + formatnum(gatecomp,precision=4,nonexponential=True) + "," + Vgsconstantarray+self.t)  # gate drive voltage step
				time.sleep(10*self.ntimepts/4090.)
				self.__parameteranalyzer.write("RI 3" + "," + formatnum(gatecomp, precision=4, nonexponential=True) + "," + formatnum(gatecomp, precision=4, nonexponential=True)+self.t)  # manual set of gate current range to turn off autoranging
				self.__parameteranalyzer.write("RG 3,0.1"+self.t)  # appears to get rid of autoscaling
			else:
				self.__parameteranalyzer.write("SS;VL1,1," + formatnum(gatecomp,precision=4,nonexponential=True) + "," + Vgsconstantarray+self.t)  # gate drive voltage step
				time.sleep(10*self.ntimepts/4090.)
				self.__parameteranalyzer.write("RI 1" + "," + formatnum(gatecomp, precision=4, nonexponential=True) + "," + formatnum(gatecomp, precision=4, nonexponential=True)+self.t)  # manual set of gate current range to turn off autoranging
				self.__parameteranalyzer.write("RG 1,0.1"+self.t)  # appears to get rid of autoscaling
			self.__parameteranalyzer.write("RI 2" + "," + formatnum(draincomp,precision=4,nonexponential=True) + "," + formatnum(draincomp,precision=4,nonexponential=True)+self.t)  # manual set of right device drain current range to turn off autoranging
			self.__parameteranalyzer.write("RG 2,0.1"+self.t)  # appears to get rid of autoscaling
			#if backgated: 			else: self.__parameteranalyzer.write("RI 1" + "," + formatnum(gatecomp,precision=4,nonexponential=True) + "," + formatnum(gatecomp,precision=4,nonexponential=True))  # manual set of gate current range to turn off autoranging
			self.__parameteranalyzer.write("SM;LI 'VD','VG','ID','IG'"+self.t)
			self.__parameteranalyzer.write("SM;XN 'VG',1,-2.0,0."+self.t)                          # configure Keithley 4200 display X axis
			self.__parameteranalyzer.write("SM;YA 'ID',1,-10u,0."+self.t)                          # configure Keithley 4200 display Y axis

			self.__parameteranalyzer.write("MD;ME1"+self.t)                                        # trigger for Id vs time measurement
			self.__panpoll()                                                                # wait for transfer curve data sweep to complete

			# get data from sweep
			# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
			# read drain voltage
			reread = True
			while reread == True:
				#self.__parameteranalyzer.write("DO 'VD'"+self.t)
				#Vdsraw = self.__parameteranalyzer.read().split(',')
				Vdsraw = self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')
				drainstatus = [dat[:1] for dat in Vdsraw]
				reread = False
				for x in drainstatus:
					if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
						reread = True
						print("WARNING re-read of Vds in time domain transfer curve")
			self.Vds_td.append([float(dat[1:]) for dat in Vdsraw])
			self.drainstatus_td.append(drainstatus)
			# read drain current
			reread = True
			while reread == True:
				Idraw = self.__parameteranalyzer.query("DO 'ID'"+self.t).split(',')
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
				Vgsraw = self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')
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
				Igraw = self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')
				gatestatus=[dat[:1] for dat in Igraw]
				reread = False
				for x in gatestatus:
					if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
						reread = True
						print("WARNING re-read of Ig in time domain transfer curve")
			self.Ig_td.append([float(dat[1:]) for dat in Igraw])
			#quit()
#######################################################################################################################################################
######################################################################################################################################################
# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with a loop sweep e.g. sweep high to low then low to high
# works for both topgated and backgated measurements
# Backgate devices use CH3, SMU3 as the gate while topgated devices use CH1, SMU1 as the gate. In all cases, CH2, SMU2 is used as the drain
	def measure_ivtransferloop_controlledslew(self, backgated=True, Vgsslewrate=None,Vds=None, draincomp=None, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=None):
		self.__parameteranalyzer.clear()
		self.Vdsset=Vds
		if abs(Vds) > self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")  # protect probe from overvoltage
		if not backgated and (abs(Vgs_start) > self.maxvoltageprobe or abs(Vgs_step) > self.maxvoltageprobe or abs(Vgs_stop) > self.maxvoltageprobe): raise ValueError("ERROR! Attempt to apply > safe Vgs voltage to bias Tee and/or probes")  # protect probe from overvoltage
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		nVgs = int(abs((Vgs_stop - Vgs_start) / Vgs_step)) + 1  # number of gate bias for one direction of Vgs sweep
		Vgssweeparray = ""
		for ii in range(0, nVgs):  # positive portion of sweep Vgs array
			Vgssweeparray += str(Vgs_start + ii * Vgs_step) + ","
		for ii in range(nVgs - 1, -1, -1):  # negative portion of sweep Vgs array
			if ii > 0: Vgssweeparray += str(Vgs_start + ii * Vgs_step) + ","
			else: Vgssweeparray += str(Vgs_start + ii * Vgs_step)  # last element

		nVgspts=len(Vgssweeparray.split(','))/2                                    # number of gate voltage points between the maximum and minimum gate voltages
		PLC,MT,self.Vgsslew=self.get_PLS_MT_fromslewrate(slewrate=Vgsslewrate,Vgsspan=abs(Vgs_stop-Vgs_start),nVgspts=nVgspts)        # get PLC which will give target slewrate if possible
		self.elapsed_time=nVgspts*MT        # total elapsed time of measurement
			#		print "Vgssweeparray is ",Vgssweeparray									# debug
		# self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.write("EM 1,0"+self.t)  # set to 4200 mode
		self.__parameteranalyzer.write("BC;DR1"+self.t)
		self.__parameteranalyzer.write("SM;DM1"+self.t)
		self.__parameteranalyzer.write("SS;DT 0."+self.t)
		self.__parameteranalyzer.write("SS;HT 0."+self.t)
		self.__parameteranalyzer.write("SM;WT 0."+self.t)
		self.__parameteranalyzer.write("SM;IN 0."+self.t)
		self.__parameteranalyzer.write("SR 1,0"+self.t)
		self.__parameteranalyzer.write("SR 2,0"+self.t)
		self.__parameteranalyzer.write("SR 3,0"+self.t)
		self.__parameteranalyzer.write("SR 4,0"+self.t)
		self.__parameteranalyzer.write("IT4,0.,0.,"+formatnum(PLC, precision=2, nonexponential=True))  # set filterfactor and delay factor both = 0.

		# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE"+self.t)
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)  # first undefine all channels

		# configure for dual (loop) sweep
		if backgated:
			self.__parameteranalyzer.write("DE;CH3,'VG','IG',1,1"+self.t)  # gate drive channel definition
			self.__parameteranalyzer.write("SS;VL3,1," + formatnum(gatecomp, precision=4, nonexponential=True) + "," + Vgssweeparray+self.t)  # gate drive voltage step
			time.sleep(20.*nVgs/4090.)
			self.__parameteranalyzer.write("RI 3" + "," + formatnum(gatecomp, precision=4, nonexponential=True) + "," + formatnum(gatecomp, precision=4, nonexponential=True)+self.t)  # manual set of gate current range to turn off autoranging
			self.__parameteranalyzer.write("RG 3,0.1"+self.t)  # manual set of gate current range to turn off autoranging
		else:
			self.__parameteranalyzer.write("DE;CH1,'VG','IG',1,1"+self.t)  # gate drive channel definition set Vgs = constant gate drive on SMU1 to left probe
			self.__parameteranalyzer.write("SS;VL1,1," + formatnum(gatecomp, precision=4, nonexponential=True) + "," + Vgssweeparray+self.t)  # gate drive voltage step
			time.sleep(20.*nVgs/4090.)
			self.__parameteranalyzer.write("RI 1" + "," + formatnum(gatecomp, precision=4, nonexponential=True) + "," + formatnum(gatecomp, precision=4, nonexponential=True)+self.t)  # manual set of gate current range to turn off autoranging
			self.__parameteranalyzer.write("RG 1,0.1"+self.t)  # manual set of gate current range to turn off autoranging
		self.__parameteranalyzer.write("RI 2" + "," + formatnum(draincomp, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=True)+self.t)  # manual set of right device drain current range to turn off autoranging
		self.__parameteranalyzer.write("RG 2,0.1"+self.t)                  # appears to get rid of autoscaling

		self.__parameteranalyzer.write("DE;CH2,'VD','ID',1,3"+self.t)  # drain drive channel definition VAR1 on SMU2
		self.__parameteranalyzer.write("SS;VC2, " + formatnum(self.Vdsset, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=True)+self.t)  # constant drain voltage drive

		self.__parameteranalyzer.write("SM;LI 'VD','VG','ID','IG'"+self.t)
		self.__parameteranalyzer.write("SM;XN 'VG',1,-2.0,0."+self.t)  # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID',1,-10u,0."+self.t)  # configure Keithley 4200 display Y axis
		self.__parameteranalyzer.write("MD;ME1"+self.t)  # trigger for transfer curve measurement
		# self.__parameteranalyzer.wait_for_srq()                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
		# get data from loop sweep
		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage
		reread = True
		while reread == True:
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')
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
			Idraw = self.__parameteranalyzer.query("DO 'ID'"+self.t).split(',')
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
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')
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
			Igraw = self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')
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
######################################################################################################################################################
# measure transfer curves i.e. Id vs Vgs for a constant drain voltage with a loop sweep e.g. sweep high to low then low to high
# works for both topgated and backgated measurements
# Backgate devices use CH3, SMU3 as the gate while topgated devices use CH1, SMU1 as the gate. In all cases, CH2, SMU2 is used as the drain
	def measure_ivtransferloop_4sweep_controlledslew(self, backgated=True, Vgsslewrate=None,Vds=None, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=None, draincomp=None):
		self.__parameteranalyzer.clear()
		self.Vdsset=Vds
		if abs(Vds) > self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")  # protect probe from overvoltage
		if not backgated and (abs(Vgs_start) > self.maxvoltageprobe or abs(Vgs_step) > self.maxvoltageprobe or abs(Vgs_stop) > self.maxvoltageprobe): raise ValueError("ERROR! Attempt to apply > safe Vgs voltage to bias Tee and/or probes")  # protect probe from overvoltage
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		nVgs = int(abs((Vgs_stop - Vgs_start) / Vgs_step)) + 1  # number of gate bias for one direction of Vgs sweep
		Vgssweeparray = ""
		for ii in range(0, nVgs): Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])                 # first sweep
		for ii in range(nVgs - 1, -1, -1): Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])        # 2nd sweep
		for ii in range(0, nVgs): Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])                 # 3rd sweep
		for ii in range(nVgs - 1, -1, -1):
			if ii > 0:Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])                             # 4th sweep
			else: Vgssweeparray += str(Vgs_start + ii * Vgs_step)  # last element

		nVgspts=len(Vgssweeparray.split(','))/2                                    # number of gate voltage points between the maximum and minimum gate voltages
		PLC,MT,self.Vgsslew=self.get_PLS_MT_fromslewrate(slewrate=Vgsslewrate,Vgsspan=abs(Vgs_stop-Vgs_start),nVgspts=nVgspts)        # get PLC which will give target slewrate if possible
		self.elapsed_time=nVgspts*MT        # total elapsed time of measurement
			#		print "Vgssweeparray is ",Vgssweeparray									# debug
		# self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.write("EM 1,0"+self.t)  # set to 4200 mode
		self.__parameteranalyzer.write("BC;DR1"+self.t)
		self.__parameteranalyzer.write("SM;DM1"+self.t)
		self.__parameteranalyzer.write("SS;DT 0."+self.t)
		self.__parameteranalyzer.write("SS;HT 0."+self.t)
		self.__parameteranalyzer.write("SM;WT 0."+self.t)
		self.__parameteranalyzer.write("SM;IN 0."+self.t)
		self.__parameteranalyzer.write("SR 1,0"+self.t)
		self.__parameteranalyzer.write("SR 2,0"+self.t)
		self.__parameteranalyzer.write("SR 3,0"+self.t)
		self.__parameteranalyzer.write("SR 4,0"+self.t)
		self.__parameteranalyzer.write("IT4,0.,0.,"+formatnum(PLC, precision=2, nonexponential=True)+self.t)  # set filterfactor and delay factor both = 0.

		# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE"+self.t)
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)  # first undefine all channels

		# configure for dual (loop) sweep
		if backgated:
			self.__parameteranalyzer.write("DE;CH3,'VG','IG',1,1"+self.t)  # gate drive channel definition
			self.__parameteranalyzer.write("SS;VL3,1," + formatnum(gatecomp, precision=4, nonexponential=True) + "," + Vgssweeparray+self.t)  # gate drive voltage step
			time.sleep(20.*nVgs/4090.)
			self.__parameteranalyzer.write("RI 3" + "," + formatnum(gatecomp, precision=4, nonexponential=True) + "," + formatnum(gatecomp, precision=4, nonexponential=True)+self.t)  # manual set of gate current range to turn off autoranging
			self.__parameteranalyzer.write("RG 3,0.1"+self.t)  # manual set of gate current range to turn off autoranging
		else:
			self.__parameteranalyzer.write("DE;CH1,'VG','IG',1,1"+self.t)  # gate drive channel definition set Vgs = constant gate drive on SMU1 to left probe
			self.__parameteranalyzer.write("SS;VL1,1," + formatnum(gatecomp, precision=4, nonexponential=True) + "," + Vgssweeparray+self.t)  # gate drive voltage step
			time.sleep(20.*nVgs/4090.)
			self.__parameteranalyzer.write("RI 1" + "," + formatnum(gatecomp, precision=4, nonexponential=True) + "," + formatnum(gatecomp, precision=4, nonexponential=True)+self.t)  # manual set of gate current range to turn off autoranging
			self.__parameteranalyzer.write("RG 1,0.1"+self.t)  # manual set of gate current range to turn off autoranging
		self.__parameteranalyzer.write("RI 2" + "," + formatnum(draincomp, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=True)+self.t)  # manual set of right device drain current range to turn off autoranging
		self.__parameteranalyzer.write("RG 2,0.1"+self.t)                  # appears to get rid of autoscaling

		self.__parameteranalyzer.write("DE;CH2,'VD','ID',1,3"+self.t)  # drain drive channel definition VAR1 on SMU2
		self.__parameteranalyzer.write("SS;VC2, " + formatnum(self.Vdsset, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=True)+self.t)  # constant drain voltage drive

		self.__parameteranalyzer.write("SM;LI 'VD','VG','ID','IG'"+self.t)
		self.__parameteranalyzer.write("SM;XN 'VG',1,-2.0,0."+self.t)  # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID',1,-10u,0."+self.t)  # configure Keithley 4200 display Y axis
		#self.__parameteranalyzer.write(""+self.t)
		self.__parameteranalyzer.write("MD;ME1"+self.t)  # trigger for transfer curve measurement
		# self.__parameteranalyzer.wait_for_srq()                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
		# get data from loop sweep
		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage
		reread = True
		while reread == True:
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')
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
			Idraw = self.__parameteranalyzer.query("DO 'ID'"+self.t).split(',')
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
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')
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
			Igraw = self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')
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
		Vgssweeparray = ""
		for ii in range(0, nVgs):  # positive portion of sweep Vgs array
			Vgssweeparray += str(Vgs_start + ii * Vgs_step) + ","
		for ii in range(nVgs - 1, -1, -1):  # negative portion of sweep Vgs array
			if ii > 0:
				Vgssweeparray += str(Vgs_start + ii * Vgs_step) + ","
			else:
				Vgssweeparray += str(Vgs_start + ii * Vgs_step)  # last element
			#		print "Vgssweeparray is ",Vgssweeparray									# debug
		# self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.write("EM 1,0"+self.t)  # set to 4200 mode
		self.__parameteranalyzer.write("BC;DR1"+self.t)
		self.__parameteranalyzer.write("IT" + inttime+self.t)
		self.__parameteranalyzer.write("SM;DM1"+self.t)

		# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE"+self.t)
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)  # first undefine all channels

		# configure for dual (loop) sweep
		self.__parameteranalyzer.write("DE;CH3,'VG','IG',1,1"+self.t)  # gate drive channel definition set Vgs = constant gate drive on SMU3 to chuck
		self.__parameteranalyzer.write("SS;VL3,1," + str(gatecomp) + "," + Vgssweeparray+self.t)  # gate drive for sweep
		self.__parameteranalyzer.write("DE;CH2,'VD','ID',1,3"+self.t)  # drain drive channel definition VAR1 on SMU2
		self.__parameteranalyzer.write("SS;VC2, " + str(Vds) + "," + str(draincomp)+self.t)  # constant drain voltage drive
		self.__parameteranalyzer.write("SS;DT ", str(sweepdelay)+self.t)
		self.__parameteranalyzer.write("SS;HT ", str(holdtime)+self.t)
		if custom==True and Iautorange==False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__parameteranalyzer.write("RI 2" + "," + str(draincomp) + "," + str(draincomp+self.t))  # allow manual set of right device drain current range to turn off autoranging
			self.__parameteranalyzer.write("RI 3" + "," + str(gatecomp) + "," + str(gatecomp)+self.t)  # allow manual set of gate current range to turn off autoranging

		self.__parameteranalyzer.write("SM;LI 'VD','VG','ID','IG'"+self.t)
		self.__parameteranalyzer.write("SM;XN 'VG',1,-2.0,0."+self.t)  # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID',1,-10u,0."+self.t)  # configure Keithley 4200 display Y axis
		starttime = time.time()  # measure sweep time
		self.__parameteranalyzer.write("MD;ME1"+self.t)  # trigger for transfer curve measurement
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
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')
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
			Idraw = self.__parameteranalyzer.query("DO 'ID'"+self.t).split(',')
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
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')
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
			Igraw = self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')
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
		if not(inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		if abs(Vds_start)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds_start voltage to bias Tee and/or probes")
		if abs(Vds_stop)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds_stop voltage to bias Tee and/or probes")

		Vds_step = (Vds_stop-Vds_start)/(Vds_npts-1)
		if Vgs_npts>1: Vgs_step = float(Vgs_stop-Vgs_start)/float(Vgs_npts-1)
		else: Vgs_step=0.           # just one curve

		self.__parameteranalyzer.write("IT"+inttime+";BC;DR1"+self.t)
		self.__parameteranalyzer.write("EM 1,1"+self.t)
# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE"+self.t)
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)                                               # first undefine all channels

		self.__parameteranalyzer.write("DE;CH3,'VG','IG',1,2"+self.t)                                                             # gate drive channel definition VAR2
		self.__parameteranalyzer.write("SS;VP "+str(Vgs_start)+","+str(Vgs_step)+","+str(Vgs_npts)+","+str(gatecomp)+self.t)         # gate drive
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients

		self.__parameteranalyzer.write("DE;CH2,'VD1','ID1',1,1"+self.t)                                                              # drain2 drive channel definition VAR1' locked to drain1 VAR1 sweep
		self.__parameteranalyzer.write("SS;VR1,"+str(Vds_start)+","+str(Vds_stop)+","+str(Vds_step)+","+str(draincomp)+self.t)         # drain2 drive
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients

		self.__parameteranalyzer.write("DE;CH1,'VD0','ID0',1,4"+self.t)                                                              # drain0 drive channel definition VAR1
		self.__parameteranalyzer.write("SS;RT 1.0"+self.t)         																	# drain0 drive
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients

		self.__parameteranalyzer.write("SM;DM1"+self.t)
		self.__parameteranalyzer.write("SM;LI 'VD0','VG','ID0','IG'"+self.t)
		self.__parameteranalyzer.write("SM;LI 'VD1','VG','ID1','IG'"+self.t)
		if custom==True and Iautorange==False:                               # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__parameteranalyzer.write("RI 1" + "," + str(draincomp) + "," + str(draincomp)+self.t)  # allow manual set of left device drain current range to turn off autoranging
			self.__parameteranalyzer.write("RI 2" + "," + str(draincomp) + "," + str(draincomp)+self.t)  # allow manual set of right device drain current range to turn off autoranging
			self.__parameteranalyzer.write("RI 3" + "," + str(gatecomp) + "," + str(gatecomp)+self.t)  # allow manual set of right device drain current range to turn off autoranging
		self.__parameteranalyzer.write("SM;XN 'VD0',1,-3.0,0."+self.t)                          # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID0',1,-10u,0."+self.t)                          # configure Keithley 4200 display Y1 axis
		self.__parameteranalyzer.write("SM;YB 'ID1',1,-10u,0."+self.t)                          # configure Keithley 4200 display Y2 axis
		self.__parameteranalyzer.write("MD;ME1"+self.t)                                        # trigger for IV measurement

		self.__panpoll()

		Id0_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'ID0'"+self.t).split(',')]
		Id1_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'ID1'"+self.t).split(',')]
		Ig_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')]
		Vgs_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')]
		Vds0_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'VD0'"+self.t).split(',')]
		Vds1_foc1d = [float(dat[1:]) for dat in self.__parameteranalyzer.query("DO 'VD1'"+self.t).split(',')]
		# find status of drain and gate bias e.g. detect compliance

		drainstatus0_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VD0'"+self.t).split(',')]
		drainstatus1_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VD1'"+self.t).split(',')]
		gatestatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')]

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
					drainstatus0_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VD0'"+self.t).split(',')]
				self.drainstatus0_foc[iVgs].append(drainstatus0_foc1d[ii])
				while not (drainstatus1_foc1d[ii]=='N' or drainstatus1_foc1d[ii]=='L' or drainstatus1_foc1d[ii]=='V'  or drainstatus1_foc1d[ii]=='X'  or drainstatus1_foc1d[ii]=='C' or drainstatus1_foc1d[ii]=='T'):		# correct HPIB reading errors
					print ("WARNING! drainstatus_foc1d =", drainstatus1_foc1d) #debug
					drainstatus1_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VD1'"+self.t).split(',')]
				self.drainstatus1_foc[iVgs].append(drainstatus1_foc1d[ii])
				while not (gatestatus_foc1d[ii]=='N' or gatestatus_foc1d[ii]=='L' or gatestatus_foc1d[ii]=='V'  or gatestatus_foc1d[ii]=='X'  or gatestatus_foc1d[ii]=='C' or gatestatus_foc1d[ii]=='T'):
					print ("WARNING! gatestatus_foc1d =", gatestatus_foc1d) #debug
					gatestatus_foc1d = [dat[:1] for dat in self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')]
				self.gatestatus_foc[iVgs].append(gatestatus_foc1d[ii])

######################################################################################################################################################
######################################################################################################################################################
# measure forward-swept (one direction only) single transfer curves for two FETs at once using two probes (SMU 1 and 2) as drains and SMU3 as the gate.
# both drains drain0 and drain1 have the same voltage values
# This is usually used for back-gated TLM structures
# CH1 (SMU1) and CH2 (SMU2) are drain1 and drain2 respectively while the gate is CH3 (SMU3)
	def measure_ivtransfer_dual_backgate(self, inttime="2", Iautorange=True, delayfactor=2,filterfactor=1,integrationtime=1, sweepdelay=0.,holdtime=0, Vds=None, draincomp=0.1, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=5E-5):
		self.__parameteranalyzer.clear()

		if not (inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		if abs(Vds)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		print ("IV tranfercurve dual device start") # debug
		self.__parameteranalyzer.write("EM 1,0"+self.t)								# set to 4200 mode
		self.__parameteranalyzer.write("IT"+inttime+";BC;DR1"+self.t)
		self.__parameteranalyzer.write("SM;DM1"+self.t)

# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE"+self.t)
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)     # first undefine all channels

		self.__parameteranalyzer.write("DE;CH3,'VG','IG',1,1"+self.t)                			# gate drive channel definition
		self.__parameteranalyzer.write("SS;VR1, "+"".join([str(Vgs_start), ",", str(Vgs_stop), ",", str(Vgs_step), ",", str(gatecomp)])+self.t)         # gate drive

		self.__parameteranalyzer.write("DE;CH1,'VD0','ID0',1,3"+self.t)                         # drain drive channel definition VAR1
		self.__parameteranalyzer.write("SS;VC1, "+"".join([str(Vds), ",", str(draincomp)])+self.t)         # constant drain voltage drive

		self.__parameteranalyzer.write("DE;CH2,'VD1','ID1',1,3"+self.t)                         # drain drive channel definition VAR1
		self.__parameteranalyzer.write("SS;VC2, "+"".join([str(Vds), ",", str(draincomp)])+self.t)         # constant drain voltage drive

		self.__parameteranalyzer.write("SS;DT ", str(sweepdelay)+self.t)
		self.__parameteranalyzer.write("SS;HT ", str(holdtime)+self.t)
		if custom==True and Iautorange==False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__parameteranalyzer.write("RI 1" + "," + str(draincomp) + "," + str(draincomp)+self.t)  # allow manual set of left device drain current range to turn off autoranging
			self.__parameteranalyzer.write("RI 2" + "," + str(draincomp) + "," + str(draincomp)+self.t)  # allow manual set of right device drain current range to turn off autoranging
			self.__parameteranalyzer.write("RI 3" + "," + str(gatecomp) + "," + str(gatecomp)+self.t)  # allow manual set of gate current range to turn off autoranging
		self.__parameteranalyzer.write("SM;LI 'VD0','VG','ID0','IG'"+self.t)
		self.__parameteranalyzer.write("SM;LI 'VD0','VG','ID1','IG'"+self.t)
		self.__parameteranalyzer.write("SM;XN 'VG',1,-3.0,0."+self.t)                          # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID0',1,-10u,0."+self.t)                          # configure Keithley 4200 display Y axis
		self.__parameteranalyzer.write("SM;YB 'ID1',1,-10u,0."+self.t)                          # configure Keithley 4200 display Y axis
		starttime=time.time()                                                      # measure sweep time
		self.__parameteranalyzer.write("MD;ME1"+self.t)                                        # trigger for transfer curve measurement
		#self.__parameteranalyzer.wait_for_srq(None)                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
		endtime=time.time()-3
		self.Vgsslew=abs(Vgs_stop-Vgs_start)/(endtime-starttime)
		self.elapsed_time=endtime-starttime
		print("elapsed time of dual backgate transferloop ="+formatnum(self.elapsed_time)+" Vgs slew rate = "+formatnum(self.Vgsslew,precision=2)+" V/sec")
#		print "IV data complete", bin(self.__parameteranalyzer.read_stb())

		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain 0 voltage
		reread = True
		while reread==True:
			Vds0raw = self.__parameteranalyzer.query("DO 'VD0'"+self.t).split(',')
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
			Id0raw = self.__parameteranalyzer.query("DO 'ID0'"+self.t).split(',')
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
			Vds1raw = self.__parameteranalyzer.query("DO 'VD1'"+self.t).split(',')
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
			Id1raw = self.__parameteranalyzer.query("DO 'ID1'"+self.t).split(',')
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
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')
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
			Igraw = self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')
			self.gatestatus_t=[dat[:1] for dat in Igraw]
			reread=False
			for x in self.gatestatus_t:
				if not (x=='N' or x=='L' or x=='V'  or x=='X'  or x=='C' or x=='T'):
					reread=True
					print("WARNING re-read of Ig in single-swept transfer curve")
		self.Ig_t=[float(dat[1:]) for dat in Igraw]

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
		self.__parameteranalyzer.write("EM 1,0"+self.t)								# set to 4200 mode
		self.__parameteranalyzer.write("IT"+inttime+";BC;DR1"+self.t)
		self.__parameteranalyzer.write("SM;DM1"+self.t)

# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE"+self.t)
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)				# first undefine all channels

# configure for dual (loop) sweep for two devices at once
		self.__parameteranalyzer.write("DE;CH3,'VG','IG',1,1"+self.t)                			# gate drive channel definition
		self.__parameteranalyzer.write("SS;VL3,1,"+"".join([str(gatecomp), ",", Vgssweeparray])+self.t)         # gate drive for sweep
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients

		self.__parameteranalyzer.write("DE;CH1,'VD0','ID0',1,3"+self.t)                         # drain0 drive channel definition
		self.__parameteranalyzer.write("SS;VC1, "+str(Vds)+","+str(draincomp)+self.t)         # constant drain voltage drive
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients

		self.__parameteranalyzer.write("DE;CH2,'VD1','ID1',1,3"+self.t)                         # drain1 drive channel definition
		self.__parameteranalyzer.write("SS;VC2, "+str(Vds)+","+str(draincomp)+self.t)         # constant drain voltage drive
		self.__parameteranalyzer.write("SS;DT ", str(sweepdelay)+self.t)
		self.__parameteranalyzer.write("SS;HT ", str(holdtime)+self.t)
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		if custom==True and Iautorange==False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__parameteranalyzer.write("RI 1" + "," + str(draincomp) + "," + str(draincomp)+self.t)  # allow manual set of left device drain current range to turn off autoranging
			self.__parameteranalyzer.write("RI 2" + "," + str(draincomp) + "," + str(draincomp)+self.t)  # allow manual set of right device drain current range to turn off autoranging
			self.__parameteranalyzer.write("RI 3" + "," + str(gatecomp) + "," + str(gatecomp)+self.t)  # allow manual set of gate current range to turn off autoranging
		self.__parameteranalyzer.write("SM;LI 'VD0','VG','ID0','IG'"+self.t)
		self.__parameteranalyzer.write("SM;LI 'VD1','VG','ID1','IG'"+self.t)
		self.__parameteranalyzer.write("SM;XN 'VG',1,-3.0,0."+self.t)                          # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID0',1,-10u,0."+self.t)                          # configure Keithley 4200 display Y1 axis
		self.__parameteranalyzer.write("SM;YB 'ID1',1,-10u,0."+self.t)                          # configure Keithley 4200 display Y2 axis
		starttime=time.time()                                                      # measure sweep time
		print("from line 986 parameter_analyzer.py triggering",starttime)
		self.__parameteranalyzer.write("MD;ME1"+self.t)                                        # trigger for transfer curve measurement
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
			Vds0raw = self.__parameteranalyzer.query("DO 'VD0'"+self.t).split(',')
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
			Id0raw = self.__parameteranalyzer.query("DO 'ID0'"+self.t).split(',')
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
			Vds1raw = self.__parameteranalyzer.query("DO 'VD1'"+self.t).split(',')
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
			Id1raw = self.__parameteranalyzer.query("DO 'ID1'"+self.t).split(',')
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
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')
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
			Igraw = self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')
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
	def measure_ivtransferloop_dual_controlledslew_backgated(self, Vgsslewrate=None, Vds=None, draincomp=None, Vgs_start=None, Vgs_stop=None, Vgs_step=None, gatecomp=None):
		self.__parameteranalyzer.chunk_size=10000000
		self.__parameteranalyzer.clear()
		self.Vdsset = Vds
		if abs(Vds) > self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes"+self.t)  # protect probe from overvoltage
		# set up input Vgs array to sweep through all gate voltages - forward sweep followed by a reverse sweep
		nVgs = int(abs((Vgs_stop-Vgs_start)/Vgs_step))+1							# number of gate bias for one direction of Vgs sweep
		Vgssweeparray= ""
		for ii in range(0,nVgs):												# positive portion of sweep Vgs array
			Vgssweeparray+=str(Vgs_start+ii*Vgs_step)+","
		for ii in range(nVgs-1,-1,-1):											# negative portion of sweep Vgs array
			if ii > 0: Vgssweeparray+=str(Vgs_start+ii*Vgs_step)+","
			else: Vgssweeparray+=str(Vgs_start+ii*Vgs_step)						# last element

		nVgspts = int(len(Vgssweeparray.split(','))/2.)  # number of gate voltage points between the maximum and minimum gate voltages
		PLC, MT, self.Vgsslew = self.get_PLS_MT_fromslewrate(slewrate=Vgsslewrate, Vgsspan=abs(Vgs_stop - Vgs_start), nVgspts=nVgspts)  # get PLC which will give target slewrate if possible
		print("from line 1698 in parameter_analyzer.py PLC MT",PLC,MT)
		self.elapsed_time=nVgspts*MT  # total elapsed time of measurement
		#		print "Vgssweeparray is ",Vgssweeparray									# debug
		# self.__write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		#self.__write("DCL"+self.t)
		self.__write("EM 1,0"+self.t)  # set to 4200 mode
		self.__write("BC;DR0"+self.t)
		self.__write("SM;DM1"+self.t)
		self.__write("SS;DT 0."+self.t)
		self.__write("SS;HT 0."+self.t)
		self.__write("SM;WT 0."+self.t)
		self.__write("SM;IN 0."+self.t)
		self.__write("SR 1,0"+self.t)
		self.__write("SR 2,0"+self.t)
		self.__write("SR 3,0"+self.t)
		self.__write("SR 4,0"+self.t)
		self.__write("IT4,0.,0.," + formatnum(PLC, precision=4, nonexponential=True)+self.t)  # set filterfactor and delay factor both = 0.
		#self.__write("BC")            # clear out "ACK"s from buffer
		# set up SMUs for drain and gate
		self.__write("DE"+self.t)
		self.__write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)  # first undefine all channels

		# configure for dual (loop) sweep
		self.__write("DE;CH3,'VG','IG',1,1"+self.t)  # gate drive channel definition
		self.__write("SS;VL3,1," + formatnum(gatecomp, precision=4, nonexponential=True) + "," + Vgssweeparray+self.t)  # gate drive voltage step
		#time.sleep(20.*nVgs/4090.)
		#self.__parameteranalyzer.read()
		self.__write("RI 3" + "," + formatnum(gatecomp, precision=4, nonexponential=True) + "," + formatnum(gatecomp, precision=4, nonexponential=True)+self.t)  # manual set of gate current range to turn off autoranging
		self.__write("RG 3,0.1"+self.t)  # manual set of gate current range to turn off autoranging

		#left drain
		self.__write("RI 1" + "," + formatnum(draincomp, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=True)+self.t)  # manual set of right device drain current range to turn off autoranging
		self.__write("RG 1,0.01"+self.t)  # appears to get rid of autoscaling
		self.__write("DE;CH1,'VD0','ID0',1,3"+self.t)  # drain drive channel definition VAR1 on SMU2
		self.__write("SS;VC1, " + formatnum(self.Vdsset, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=True)+self.t)  # constant drain voltage drive
		#self.__write("BC")            # clear out "ACK"s from buffer
		# right drain
		self.__write("RI 2" + "," + formatnum(draincomp, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=True)+self.t)  # manual set of right device drain current range to turn off autoranging
		self.__write("RG 2,0.01"+self.t)  # appears to get rid of autoscaling
		self.__write("DE;CH2,'VD1','ID1',1,3"+self.t)  # drain drive channel definition VAR1 on SMU2
		self.__write("SS;VC2, " + formatnum(self.Vdsset, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=True)+self.t)  # constant drain voltage drive

		self.__write("SM;LI 'VD0','VG','ID0','IG'"+self.t)
		self.__write("SM;LI 'VD1','VG','ID1','IG'"+self.t)
		self.__write("SM;XN 'VG',1,-3.0,0."+self.t)  # configure Keithley 4200 display X axis
		self.__write("SM;YA 'ID0',1,-10u,0."+self.t)  # configure Keithley 4200 display Y1 axis
		self.__write("SM;YB 'ID1',1,-10u,0."+self.t)  # configure Keithley 4200 display Y2 axis
		time.sleep(1.)
		#self.__rm.clear()
		#self.__write("BC")            # clear out "ACK"s from buffer
		self.__write("MD;ME1")
		#self.__write("ME1")
		#self.__write("MD;ME1"+self.t)  # trigger for transfer curve measurement
		# self.__parameteranalyzer.wait_for_srq()                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
		self.__parameteranalyzer.chunk_size=550000000
		# get data from loop sweep
		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage

		reread = True
		while reread == True:
			Vds0raw = self.__parameteranalyzer.query("DO 'VD0'"+self.t).split(',')
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
			Id0raw = self.__parameteranalyzer.query("DO 'ID0'"+self.t).split(',')
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
			Vds1raw = self.__parameteranalyzer.query("DO 'VD1'"+self.t).split(',')
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
			Id1raw = self.__parameteranalyzer.query("DO 'ID1'"+self.t).split(',')
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
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')
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
			Igraw = self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')
			gatestatus_transloop = [dat[:1] for dat in Igraw]
			reread = False
			for x in gatestatus_transloop:
				if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
					reread = True
					print("WARNING re-read of Ig in dual-swept transfer curve")
		Ig_transloop = [float(dat[1:]) for dat in Igraw]
		self.__parameteranalyzer.chunk_size=10000000
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
		Vgssweeparray = ""
		for ii in range(0, nVgs): Vgssweeparray = "".join([Vgssweeparray,str(Vgs_start + ii * Vgs_step),","]) 							# first sweep
		for ii in range(nVgs - 1, -1, -1): Vgssweeparray = "".join([Vgssweeparray,str(Vgs_start + ii * Vgs_step),","])					# 2nd sweep
		for ii in range(0, nVgs): Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])  						# 3rd sweep
		for ii in range(nVgs - 1, -1, -1):
			if ii>0: Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])  				                    # 4th sweep
			else: Vgssweeparray += str(Vgs_start + ii * Vgs_step)  # last element
			#		print "Vgssweeparray is ",Vgssweeparray									# debug
		# self.__parameteranalyzer.query("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.query("EM 1,0"+self.t)  # set to 4200 mode
		self.__parameteranalyzer.query("IT" + inttime + ";BC;DR1"+self.t)
		self.__parameteranalyzer.query("SM;DM1"+self.t)

		self.__parameteranalyzer.query("SS;DT ",str(sweepdelay)+self.t)
		self.__parameteranalyzer.query("SS;HT ",str(holdtime)+self.t)

		# set up SMUs for drain and gate
		self.__parameteranalyzer.query("DE"+self.t)
		self.__parameteranalyzer.query("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)  # first undefine all channels

		# configure for dual (loop) sweep for two devices at once
		self.__parameteranalyzer.query("DE;CH3,'VG','IG',1,1"+self.t)  # gate drive channel definition
		self.__parameteranalyzer.query("SS;VL3,1," + "".join([str(gatecomp), ",", Vgssweeparray])+self.t)  # gate drive for sweep
		# self.__parameteranalyzer.query("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients

		self.__parameteranalyzer.query("DE;CH1,'VD0','ID0',1,3"+self.t)  # drain0 drive channel definition
		self.__parameteranalyzer.query("SS;VC1, " + str(Vds) + "," + str(draincomp)+self.t)  # constant drain voltage drive
		# self.__parameteranalyzer.query("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients

		self.__parameteranalyzer.query("DE;CH2,'VD1','ID1',1,3"+self.t)  # drain1 drive channel definition
		self.__parameteranalyzer.query("SS;VC2, " + str(Vds) + "," + str(draincomp)+self.t)  # constant drain voltage drive
		# self.__parameteranalyzer.query("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		if custom==True and Iautorange == False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__parameteranalyzer.query("RI 1" + "," + str(draincomp) + "," + str(draincomp)+self.t)  # allow manual set of left device drain current range to turn off autoranging
			self.__parameteranalyzer.query("RI 2" + "," + str(draincomp) + "," + str(draincomp)+self.t)  # allow manual set of right device drain current range to turn off autoranging
			self.__parameteranalyzer.query("RI 3" + "," + str(gatecomp) + "," + str(gatecomp)+self.t)  # allow manual set of gate current range to turn off autoranging
		self.__parameteranalyzer.query("SM;LI 'VD0','VG','ID0','IG'"+self.t)
		self.__parameteranalyzer.query("SM;LI 'VD1','VG','ID1','IG'"+self.t)
		self.__parameteranalyzer.query("SM;XN 'VG',1,-3.0,0."+self.t)  # configure Keithley 4200 display X axis
		self.__parameteranalyzer.query("SM;YA 'ID0',1,-10u,0."+self.t)  # configure Keithley 4200 display Y1 axis
		self.__parameteranalyzer.query("SM;YB 'ID1',1,-10u,0."+self.t)  # configure Keithley 4200 display Y2 axis
		starttime = time.time()  # measure sweep time
		print("from line 986 parameter_analyzer.py triggering", starttime)
		self.__parameteranalyzer.query("MD;ME1"+self.t)  # trigger for transfer curve measurement
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
			Vds0raw = self.__parameteranalyzer.query("DO 'VD0'"+self.t).split(',')
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
			Id0raw = self.__parameteranalyzer.query("DO 'ID0'"+self.t).split(',')
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
			Vds1raw = self.__parameteranalyzer.query("DO 'VD1'"+self.t).split(',')
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
			Id1raw = self.__parameteranalyzer.query("DO 'ID1'"+self.t).split(',')
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
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')
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
			Igraw = self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')
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
		# self.__parameteranalyzer.query("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.query("EM 1,0"+self.t)  # set to 4200 mode
		self.__parameteranalyzer.query("BC;DR1"+self.t)
		self.__parameteranalyzer.query("SM;DM1"+self.t)
		self.__parameteranalyzer.query("SS;DT 0."+self.t)
		self.__parameteranalyzer.query("SS;HT 0."+self.t)
		self.__parameteranalyzer.query("SM;WT 0."+self.t)
		self.__parameteranalyzer.query("SM;IN 0."+self.t)
		self.__parameteranalyzer.query("SR 1,0"+self.t)
		self.__parameteranalyzer.query("SR 2,0"+self.t)
		self.__parameteranalyzer.query("SR 3,0"+self.t)
		self.__parameteranalyzer.query("SR 4,0"+self.t)
		self.__parameteranalyzer.query("IT4,0.,0.," + formatnum(PLC, precision=2, nonexponential=True)+self.t)  # set filterfactor and delay factor both = 0.

		# set up SMUs for drain and gate
		self.__parameteranalyzer.query("DE"+self.t)
		self.__parameteranalyzer.query("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)  # first undefine all channels

		# configure for dual (loop) sweep
		self.__parameteranalyzer.query("DE;CH3,'VG','IG',1,1"+self.t)  # gate drive channel definition
		self.__parameteranalyzer.query("SS;VL3,1," + formatnum(gatecomp, precision=4, nonexponential=True) + "," + Vgssweeparray+self.t)  # gate drive voltage step
		time.sleep(20.*nVgs/4090.)
		self.__parameteranalyzer.query("RI 3" + "," + formatnum(gatecomp, precision=4, nonexponential=True) + "," + formatnum(gatecomp, precision=4, nonexponential=True)+self.t)  # manual set of gate current range to turn off autoranging
		self.__parameteranalyzer.query("RG 3,0.1"+self.t)  # manual set of gate current range to turn off autoranging

		#left drain
		self.__parameteranalyzer.query("RI 1" + "," + formatnum(draincomp, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=True)+self.t)  # manual set of right device drain current range to turn off autoranging
		self.__parameteranalyzer.query("RG 1,0.01"+self.t)  # appears to get rid of autoscaling
		self.__parameteranalyzer.query("DE;CH1,'VD0','ID0',1,3"+self.t)  # drain drive channel definition VAR1 on SMU2
		self.__parameteranalyzer.query("SS;VC1, " + formatnum(self.Vdsset, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=True)+self.t)  # constant drain voltage drive

		# right drain
		self.__parameteranalyzer.query("RI 2" + "," + formatnum(draincomp, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=True)+self.t)  # manual set of right device drain current range to turn off autoranging
		self.__parameteranalyzer.query("RG 2,0.01"+self.t)  # appears to get rid of autoscaling
		self.__parameteranalyzer.query("DE;CH2,'VD1','ID1',1,3"+self.t)  # drain drive channel definition VAR1 on SMU2
		self.__parameteranalyzer.query("SS;VC2, " + formatnum(self.Vdsset, precision=4, nonexponential=True) + "," + formatnum(draincomp, precision=4, nonexponential=True)+self.t)  # constant drain voltage drive

		self.__parameteranalyzer.query("SM;LI 'VD0','VG','ID0','IG'"+self.t)
		self.__parameteranalyzer.query("SM;LI 'VD1','VG','ID1','IG'"+self.t)
		self.__parameteranalyzer.query("SM;XN 'VG',1,-3.0,0."+self.t)  # configure Keithley 4200 display X axis
		self.__parameteranalyzer.query("SM;YA 'ID0',1,-10u,0."+self.t)  # configure Keithley 4200 display Y1 axis
		self.__parameteranalyzer.query("SM;YB 'ID1',1,-10u,0."+self.t)  # configure Keithley 4200 display Y2 axis
		self.__parameteranalyzer.query("MD;ME1"+self.t)  # trigger for transfer curve measurement


		# self.__parameteranalyzer.wait_for_srq()                                         # wait for transfer curve data sweep to complete
		self.__panpoll()
		# get data from loop sweep
		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage

		reread = True
		while reread == True:
			Vds0raw = self.__parameteranalyzer.query("DO 'VD0'"+self.t).split(',')
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
			Id0raw = self.__parameteranalyzer.query("DO 'ID0'"+self.t).split(',')
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
			Vds1raw = self.__parameteranalyzer.query("DO 'VD1'"+self.t).split(',')
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
			Id1raw = self.__parameteranalyzer.query("DO 'ID1'"+self.t).split(',')
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
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')
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
			Igraw = self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')
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
		Vgssweeparray= ""
		for ii in range(0, nVgs): Vgssweeparray = "".join([Vgssweeparray,str(Vgs_start + ii * Vgs_step),","]) 							# first sweep
		for ii in range(nVgs - 1, -1, -1): Vgssweeparray = "".join([Vgssweeparray,str(Vgs_start + ii * Vgs_step),","])					# 2nd sweep
		for ii in range(0, nVgs): Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])  						# 3rd sweep
		for ii in range(nVgs - 1, -1, -1):
			if ii>0: Vgssweeparray = "".join([Vgssweeparray, str(Vgs_start + ii * Vgs_step), ","])  				                    # 4th sweep
			else: Vgssweeparray += str(Vgs_start + ii * Vgs_step)  # last element

#		print "Vgssweeparray is ",Vgssweeparray									# debug
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.write("EM 1,0"+self.t)								# set to 4200 mode
		self.__parameteranalyzer.write("IT"+inttime+";BC;DR1"+self.t)
		self.__parameteranalyzer.write("SM;DM1"+self.t)
		self.__parameteranalyzer.write("SS;DT ",str(sweepdelay)+self.t) #added by ahmad
		self.__parameteranalyzer.write("SS;HT ",str(holdtime)+self.t)   #added by ahmad
# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE"+self.t)
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)				# first undefine all channels

# configure for dual (loop) sweep
		self.__parameteranalyzer.write("DE;CH1,'VG','IG',1,1"+self.t)                # gate drive channel definition set Vgs = constant
		self.__parameteranalyzer.write("SS;VL1,1,"+str(gatecomp)+","+Vgssweeparray+self.t)         # gate drive for sweep
		self.__parameteranalyzer.write("DE;CH2,'VD','ID',1,3"+self.t)                         # drain drive channel definition VAR1
		self.__parameteranalyzer.write("SS;VC2, "+str(Vds)+","+str(draincomp)+self.t)         # constant drain voltage drive
		if custom==True and Iautorange == False:  # then NOT autoranging so set drain and gate compliance and range
			# set range and compliance of drain amd gate current
			self.__parameteranalyzer.write("RI 1" + "," + str(gatecomp) + "," + str(gatecomp)+self.t)  # allow manual set of gate current range to turn off autoranging
			self.__parameteranalyzer.write("RI 2" + "," + str(draincomp) + "," + str(draincomp)+self.t)  # allow manual set of right device drain current range to turn off autoranging

		self.__parameteranalyzer.write("SM;LI 'VD','VG','ID','IG'"+self.t)
		self.__parameteranalyzer.write("SM;XN 'VG',1,-2.0,0."+self.t)                          # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID',1,-10u,0."+self.t)                          # configure Keithley 4200 display Y axis
		self.__parameteranalyzer.write("MD;ME1"+self.t)                                        # trigger for transfer curve measurement
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
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')
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
			Idraw = self.__parameteranalyzer.query("DO 'ID'"+self.t).split(',')
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
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')
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
			Igraw = self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')
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
	def measure_burnsweepVds_backgate(self, inttime='2', currentrange=None,delayfactor='2',filterfactor='1',integrationtime=1, Vgs=None, draincomp=None, Vds_start=None, Vds_max=None, Vds_step=None, gatecomp=None):
		self.__parameteranalyzer.clear()
		self.Vgs_burn_set=Vgs
		if not(inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		if abs(Vds_max)>self.maxvoltageprobe or abs(Vds_start)>self.maxvoltageprobe or abs(Vds_step)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")
		print ("IV tranfercurve start") # debug
		self.__parameteranalyzer.write("EM 1,0"+self.t)								# set to 4200 mode
		self.__parameteranalyzer.write("IT"+inttime+";BC;DR0"+self.t)                  # setup delays and data acquision timing and averaging for noise reduction
		self.__parameteranalyzer.write("SM;DM1"+self.t)

# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE"+self.t)                                # set to channel definition page
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)     # first undefine all channels

		self.__parameteranalyzer.write("DE;CH3,'VG','IG',1,3"+self.t)                			# gate drive channel definition set Vgs = constant	SMU3
		self.__parameteranalyzer.write("SS;VC3,"+","+str(Vgs)+","+str(gatecomp)+self.t)         # gate drive
		self.__parameteranalyzer.write("DE;CH2,'VD','ID',1,1"+self.t)                         # drain drive channel definition VAR1
		if currentrange!=None: self.__parameteranalyzer.write("RI 2"+","+str(currentrange)+","+str(currentrange))               # allow user to set current range of drain i.e. SMU1

		Vds_stop_array=np.arange(Vds_start+Vds_step,Vds_max+Vds_step,Vds_step)            # get stop voltages for the many Vds sweeps
		self.Vds_burnfinal=c.deque()                 # last measured drain voltage of
		self.Vgs_burnfinal=c.deque()                 # last measured gate voltage
		self.Id_burnfinal=c.deque()                  # last measured drain current (A)
		self.Ig_burnfinal=c.deque()                  # last measured gate current (A)
		self.gatestatus_burnfinal=c.deque()          # append the gate status indicator to "C" if any gate status indictors are other than "N" for the current drain sweep
		self.drainstatus_burnfinal=c.deque()          # append the gate status indicator to "C" if any gate status indictors are other than "N" for the current drain sweep
		self.Vdsslewrate_burn=c.deque()

		for Vds_stop in Vds_stop_array:
			self.__parameteranalyzer.write("SS;VR1,"+str(Vds_start)+","+str(Vds_stop)+","+str(Vds_step)+","+str(draincomp)+self.t)         # stepped drain voltage drive setup
			# plot trace on the Keithley 4200 screen
			self.__parameteranalyzer.write("SM;LI 'VD','VG','ID','IG'"+self.t)
			self.__parameteranalyzer.write("SM;XN 'VD',1,-2.0,0."+self.t)                          # configure Keithley 4200 display X axis
			self.__parameteranalyzer.write("SM;YA 'ID',1,-10u,0."+self.t)                          # configure Keithley 4200 display Y axis
			starttime=time.time()
			self.__parameteranalyzer.write("MD;ME1"+self.t)                                        # trigger for transfer curve measurement
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
				Vdsraw = self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')
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
				Idraw = self.__parameteranalyzer.query("DO 'ID'"+self.t).split(',')
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
				Vgsraw = self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')
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
				Igraw = self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')
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
	def measure_burnonesweepVds_backgate(self, inttime='2', currentrange=None,delayfactor='2',filterfactor='1',integrationtime=1, Vgs=None, draincomp=None, Vds_start=None, Vds_stop=None, Vds_step=None, gatecomp=None):
		self.__parameteranalyzer.clear()
		self.Vgs_burn_set=Vgs
		if not(inttime!='1' or inttime!='2' or inttime!='3' or inttime!='4'): raise ValueError('ERROR! invalid inttime setting')
		if inttime=='4':  # custom timing setting
			inttime="".join(['4',',',str(delayfactor),',',str(filterfactor),',',str(integrationtime)])
			custom=True
		else: custom=False
		if abs(Vds_stop)>self.maxvoltageprobe or abs(Vds_start)>self.maxvoltageprobe or abs(Vds_step)>self.maxvoltageprobe: raise ValueError("ERROR! Attempt to apply > safe Vds voltage to bias Tee and/or probes")

		print ("IV tranfercurve start") # debug
		self.__parameteranalyzer.write("EM 1,0"+self.t)								# set to 4200 mode
		self.__parameteranalyzer.write("IT"+inttime+";BC;DR0"+self.t)                  # setup delays and data acquision timing and averaging for noise reduction
		self.__parameteranalyzer.write("SM;DM1"+self.t)

# set up SMUs for drain and gate
		self.__parameteranalyzer.write("DE"+self.t)                                # set to channel definition page
		#self.__parameteranalyzer.write("DT "+str(self.delaytimemeas))           # add delay time to aid settling and reduce propability of compliance due to charging transients
		self.__parameteranalyzer.write("CH1;CH2;CH3;CH4;VS1;VS2;VM1;VM2"+self.t)     # first undefine all channels

		self.__parameteranalyzer.write("DE;CH2,'VD','ID',1,1"+self.t)                         # drain drive channel definition VAR1
		self.__parameteranalyzer.write("SS;VR1,"+str(Vds_start)+","+str(Vds_stop)+","+str(Vds_step)+","+str(draincomp)+self.t)         # stepped drain voltage drive setup
		self.__parameteranalyzer.write("DE;CH3,'VG','IG',1,3"+self.t)                			# gate drive channel definition set Vgs = constant	SMU3
		self.__parameteranalyzer.write("SS;VC3,"+str(Vgs)+","+str(gatecomp)+self.t)         # gate drive

		if currentrange!=None: self.__parameteranalyzer.write("RI 2"+","+str(currentrange)+","+str(currentrange))               # allow user to set current range of drain i.e. SMU1
		# plot trace on the Keithley 4200 screen
		self.__parameteranalyzer.write("SM;LI 'VD','VG','ID','IG'"+self.t)
		self.__parameteranalyzer.write("SM;XN 'VD',1,-2.0,0."+self.t)                          # configure Keithley 4200 display X axis
		self.__parameteranalyzer.write("SM;YA 'ID',1,-10u,0."+self.t)                          # configure Keithley 4200 display Y axis
		starttime=time.time()
		self.__parameteranalyzer.write("MD;ME1"+self.t)                                        # trigger for transfer curve measurement
		self.__panpoll()                    # wait for sweep to complete
		endtime = time.time()
		self.Vdsslew_burn = abs(Vds_stop - Vds_start) / (endtime - starttime)
		self.elapsed_time_burn = endtime - starttime
		print("elapsed time of burn sweep= " + formatnum(self.elapsed_time_burn) + " Vds slew rate = " + formatnum(self.Vdsslew_burn, precision=2) + " V/sec")
		print("Vds_start, Vds_stop", Vds_start, Vds_stop)

		# find status of drain and gate bias e.g. detect compliance First check to be sure data read is good and re-read it if not
		# read drain voltage
		reread = True
		while reread==True:
			Vdsraw = self.__parameteranalyzer.query("DO 'VD'"+self.t).split(',')
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
			Idraw = self.__parameteranalyzer.query("DO 'ID'"+self.t).split(',')
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
			Vgsraw = self.__parameteranalyzer.query("DO 'VG'"+self.t).split(',')
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
			Igraw = self.__parameteranalyzer.query("DO 'IG'"+self.t).split(',')
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
		Ig_burnfinal=self.Ig_burn[-1]                                           # append the last measured gate current of the Vds swee
		return Id_burnfinal,Ig_burnfinal,Vds_burnfinal,Vgs_burnfinal,drainstatus_burnfinal,gatestatus_burnfinal
######################################################################################################################################################
# This method oscillates the gate voltage about the final value to remove hysteresis effects
# This assumes that the 4200 is appropriately setup to allow accurate control of the timesteps and does this here
# the gatevoltagechannel is the channel (1,2,3...to max SMU channel number) designated for the gate bias
# Vgs is the final desired, steady-state gate voltage
# Vgsmin is the minimum Vgs setting for the voltage dither
# Vgsmax is the maximum Vgs setting for the voltage dither
# dithertime is the time in sec that the dither oscillations take place over
# the dither voltage is an oscillating series of gate voltages whose amplitude shrinks linearly with time over the dither time so as to reduce or eliminate hysteresis effects at the steady-state gate voltage
	def ditherVgsvoltage(self,gatevoltagechannel=None,gatecomp=None,Vgs=None,Vgspos=None,Vgsneg=None,dithertime=None):
		npts=int(dithertime/0.01)               # assume the minimum timestep of 10mS, self.timestep = self.convert_MT_to_PLC(MT=timestep)  # convert timestep (sec) to integration time in PLC (power line cycles) for 4200, self.timestep is the actual timestep whereas timestep is that requested
		PLC=self.convert_MT_to_PLC(MT=0.01)[0]  # convert timestep (sec) to integration time in PLC (power line cycles) for 4200, self.timestep is the actual timestep whereas timestep is that requested
		self.__parameteranalyzer.write("SS;DT 0"+self.t)  # set sweep delay=0
		self.__parameteranalyzer.write("SS;HT 0"+self.t)  # set holdtime to set quiescent time
		self.__parameteranalyzer.write("SM;WT 0"+self.t)
		self.__parameteranalyzer.write("SM;IN 0"+self.t)
		Vgsditherfactor=[1.-float(i)/float(npts) for i in range(0,npts)]
		Vgsdither="".join([formatnum(Vgs-Vgsneg*f,precision=2,nonexponential=True)+","+formatnum(Vgs+Vgspos*f,precision=2,nonexponential=True)+"," for f in Vgsditherfactor ])
		Vgsdither="".join([Vgsdither,formatnum(Vgs,precision=2,nonexponential=True)])
		self.__parameteranalyzer.write("IT4,0,0," + formatnum(PLC, precision=2, nonexponential=True)+self.t)  # set filterfactor and delay factor both = 0.
		self.__parameteranalyzer.write("SS;VL"+str(gatevoltagechannel)+",1"+formatnum(gatecomp,precision=4,nonexponential=True) + "," + Vgsdither+self.t)
		time.sleep(10*npts/4090.)
		self.__parameteranalyzer.write("RI "+str(gatevoltagechannel)+","+formatnum(gatecomp, precision=4, nonexponential=True) + "," + formatnum(gatecomp, precision=4, nonexponential=True)+self.t)  # manual set of gate current range to turn off autoranging
		self.__parameteranalyzer.write("RG "+str(gatevoltagechannel)+",0.01"+self.t)  # appears to get rid of autoscaling
		self.__parameteranalyzer.write("MD;ME1"+self.t)  # trigger for Id vs time measurement
		self.__panpoll()  # wait for transfer curve data sweep to complete
		self.__parameteranalyzer.write("BC"+self.t)            # throw away data
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
######################################################################################################################################################
	def __panpoll(self):
		# reread = True
		# while reread == True:
		# 	time.sleep(0.2)
		# 	Vds0raw = self.__parameteranalyzer.query("DO 'VD0'"+self.t).split(',')
		# 	print("Vds0raw", Vds0raw)
		# 	drain0status_transloop = [dat[:1] for dat in Vds0raw]
		# 	reread = False
		# 	for x in drain0status_transloop:
		# 		if not (x == 'N' or x == 'L' or x == 'V' or x == 'X' or x == 'C' or x == 'T'):
		# 			reread = True
		# 			print("polling not ready yet")
		# time.sleep(.2)
		# print("ready for read")
		# return

		# if self.t=="":          # using GPIB
		# 	while True:
		# 		try: sb=self.__parameteranalyzer.read_stb()
		# 		except:
		# 			print ("error in sb read retry")
		# 			continue
		# 		#print ("before break in loop"), sb
		# 		if int(sb)==65: break
		# 		#print ("after break"), sb
		# 		#time.sleep(settlingtime)
		# 		time.sleep(0.3)
		# 	time.sleep(2)                                      # minimum time here to prevent read errors is 2sec
		# else:               # using LAN
		time.sleep(.2)
		#print(self.__parameteranalyzer.read())
		donemeasuring=False
		while not donemeasuring:
			sb=self.__parameteranalyzer.query("SP")
			if (int(sb)&1): donemeasuring=True      # done on status bit #1 which indicates data read is complete
			print ("after break sp",sb)
			#time.sleep(settlingtime)
		time.sleep(0.01)
			#time.sleep(2)                                      # minimum time here to prevent read errors is 2sec
		#print("waiting for service request")
######################################
# # clear ACKs from output LAN buffer
# 	def __clearACK(self):
# 		hasack=True
# 		while hasack:
# 			try: buf=self.__parameteranalyzer.read()
# 			except: hasack=False
# 			print("buffer is ",buf)
# 			if buf!="ACK": hasack=False
###########################
# modified write to customize for LAN or GPIB
# 	def __write(self,cmd):
# 		if self.__LAN:          # If we have  a LAN interface, use that
# 			notACK=True
# 			while notACK:
# 				ack=self.__parameteranalyzer.query(cmd)
# 				#ackread=False
# 				# while(not ackread):
# 				# 	ackread=True
# 				# 	try: ack=self.__parameteranalyzer.query(cmd)
# 				# 	except: ackread=False
# 				#
# 				# print("ACK is",ack)
# 				if(ack=="ACK"): notACK=False
# 		else:
# 			self.__parameteranalyzer.write(cmd)
#
	def __write(self,cmd):
		if self.__LAN:
			self.__parameteranalyzer.write(cmd)
			notACK=True
			ack=""
			while notACK:
				try: ack=self.__parameteranalyzer.read()
				except: pass
				if ack=="ACK": notACK=False


