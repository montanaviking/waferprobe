__author__ = 'PMarsh Carbonics'
# wafer level analysis of DC IV and RF parameters
# produces wafer map text list of parameters
# major version change - device structures are now a dictionary March 7, 2016
import os
import re
import collections as col
from device_parameter_request import DeviceParameters       # to read IV and RF parameters for each device
from calculated_parameters import *                         # post process calculated parameters
#from utilities import getfilelisting, file_to_devicename, sub
from utilities import *
from read_testplan import *
from filter_defaults import *										# used to set default filters for parameters e.g. |Idmax| minimum and maximum etc....
#from device_parameter_Ron_TLM import Tlm
import copy
import multiprocessing as mp
import time
from sys import platform as _platform
#import affinity
invalidTLMorthdevice="SHORT"
class WaferData(object):
	#deviceFilterUpdated = QtCore.pyqtSignal(str)						# signal to indicate update of device filter
	def __init__(self,parent=None,pathname=None,wafername=None,fractVgsfit=None,Y_Ids_fitorder=None,fractftfit=None,fractfmaxfit=None,fractVdsfit_Ronfoc=None,devicetype=None,probeplanfile=None):
		self.waferparameters = []							# keep track of which wafer parameters are loaded
		self.parent=parent

		if pathname==None: raise ValueError("ERROR! must give a pathname")
		if wafername==None: raise ValueError("ERROR! must give a wafer name")
		#os.system("taskset -p 0xff %d" % os.getpid())
		os.system("taskset -p 0xfffff %d" % os.getpid())					# necessary for multiprocessing

		# parameters which are primarily fed to instantiations of
		# DeviceParameters()
		self.pathname=pathname
		self.wafername=wafername
		self.probeplanfile=probeplanfile							# name of the probe plan file to use to obtain parameters such as TLM length and device total gate width
		if fractVdsfit_Ronfoc==None: self.fractVdsfit_Ronfoc=0.1
		else: self.fractVdsfit_Ronfoc=fractVdsfit_Ronfoc
		if fractVgsfit==None: self.fractVgsfit=0.1
		else: self.fractVgsfit=fractVgsfit
		if Y_Ids_fitorder==None: self.order=7
		else: self.order=Y_Ids_fitorder
		if fractftfit==None: self.fractftfit=0.2
		else: self.fractftfit=fractftfit
		if fractfmaxfit==None: self.fractfmaxfit=0.2
		else: self.fractfmaxfit=fractfmaxfit
		if devicetype==None: self.devicetype='p'
		else: self.devicetype=devicetype

		# set up directory for the wafer-level data
		self.pathname_waferlevel = self.pathname+sub("WAFER")							# directory which accepts the wafer level data files to be written
		if not os.path.exists(self.pathname_waferlevel):								# if necessary, make the directory to contain the wafer level data
			os.makedirs(self.pathname_waferlevel)
		# defaults: can be explicitly set
		self.minTLMlength=0.						# default mask-defined minimum TLM length to analyze
		self.maxTLMlength = 1.E10								# default maximum TLM length considered is 0.6um
		#self.__mingm = 1.E-11									# minimum gm a device must have to consider for analysis in the TLM pattern
		self.__mingm=0.
		# default variable setups

		# device key arrays containing names (keys) of devices which have valid parameter data fpr cp

		# filters for selecting devices in analysis
		self.filtergatecompliance=True
		self.filterdraincompliance=True
		self.filter_gmmax_min=None
		self.filter_gmmax_max=None
		self.filter_RFgmmax_min = None
		self.filter_RFgmmax_max = None
		self.filter_Idmax_min=default_min_Idmax
		self.filter_Idmax_max=None
		self.filter_IdmaxFOC_min=None
		self.filter_IdmaxFOC_max=None
		self.filter_onoff_min=default_on_offratio_min
		self.filter_onoff_max=None
		self.filter_Ronmin_min=None
		self.filter_Ronmin_max=None
		self.filter_TLM_Rc_min=None
		self.filter_TLM_Rc_max=None
		self.filter_TLM_Rsh_min=None
		self.filter_TLM_Rsh_max=None
		self.filter_Igmax_min=None
		self.filter_Igmax_max=None
		self.devicenamefilter=None
		self.validdevices=None
		self.proberesistanceindex=None
		self.devicefilteredORTH=False							# devices were filtered?
		self.devicefilteredTLM = False  # devices were filtered?
		self.linearfitquality_request=None						# request value for quality of TLM linear fit
		self.havefocdata=True
		self.havetransferdata=False

		# variable defaults for histograms
		self.__minRon_hist = 0.
		self.__maxRon_hist = 1.E50
		self.__minRonstddev_hist=0.
		self.__maxRonstddev_hist=4.
		self.__binsizeRondev_hist = 0.1
		self.__binsizepolicy='Directly Set'
		self.__RG='R'
		self.__Vgs_selected=None							# to monitor changes to selected Vgs for __get_parametersDC() method
		self.__Vgs_selected_TLM=None						# to monitor changes to selected Vgs for __get_parametersTLM() method
		self.__Vgs_selected_ORTH=None						# to monitor changes to selected Vgs for __get_parametersORTH() method
		self.__fractVdsfit_TLM=None							# to monitor changes to the fraction of Vds to fit a line over to find Ron from the IV family of curves for method __get_parametersTLM()
		self.__fractVdsfit_ORTH=None						# to monitor changes to the fraction of Vds to fit a line over to find Ron from the IV family of curves for method __get_parametersORTH()
		self.__lowerfitTOI=0.								# fraction of TOI points to exclude on lower portion of TOI measurement linear fit
		self.__upperfitTOI=0.								# fraction of TOI points to exclude on upper portion of TOI measurement linear fit
		self.__transfercurve_smoothing_factor=.1          # transfer curve smoothing factor used to calculate Id(Vgs) curve to find Gm

		self.__includesRon_hist='foc'
		self._logplot=False
		# find index of first good device that has no gate measurements in compliance so we can get accurate gate voltages used in the measurements
		self.focfirstdevindex=None
		self.haveORTHdata=False
		#self.__eps=1.E-6			# used to compare real numbers
		# device geometry
		# get device properties i.e. device total gate widths, TLM lengths, and mates of orthogonal devices
		g=geometry(self.pathname)
		if g!=None:
			self.gatewidth=geometry(self.pathname)['gatewidth']
			self.tlmlength=geometry(self.pathname)['TLMlength']
			self.orthmate=geometry(self.pathname)['ORTHmate']
			self.leadresistance=geometry(self.pathname)['leadresistance']
		else:
			self.gatewidth=None
			self.tlmlength=None
			self.orthmate=None
			self.leadresistance=None

###################################.#####################################################################################
# write contact resistance of CFETs as a function of wafer location as calculated from the single-swept transfer curve using the Y-function
# the gm and Y-function are calculated from a polynomial fit of Id[Vgs] using a polynomial of the specifed order .get_orderfit()
# 	def write_waferparameter_Rc(self,type):
# 		self.__get_parametersDC()	# get DC IV measured and calculated parameters for all devices measured on the wafer
# 		if type=='T':
# 			# write header data to wafer data file
# 			filename = self.pathname_waferlevel+"/"+self.wafername+"_Rc_T_waferdata.xls"
# 			fwdat = open(filename,'w')
# 			fwdat.write('# Data from Id(Vgs) single-swept transfer curve\n')
# 			fwdat.write('# Contact resistance calculated via the Y-function method\n')
# 			fwdat.write('# wafername\t'+self.DCd[0].get_wafername()+'\n#\n')
# 			fwdat.write('# X (um)\tY (um)\tRc_T\t# datapoints at gate compliance\t# datapoints at drain compliance\tpolynomial order\tdelta Vgs for linear fit\tdevice name\n')
#
# 			for ii in range(len(self.DCd)):
# 				if self.DCd[ii].Rc_T() != "None":		# Data missing if "None" so write nothing if no data for this wafer location
# 					fwdat.write('%d\t%d\t%10.3E\t%d\t%d\t%d\t%10.3f\t%s\n' %(self.DCd[ii].x(),self.DCd[ii].y(),self.DCd[ii].Rc_T(),self.DCd[ii].gatestatus_no_T(),self.DCd[ii].drainstatus_no_T(),self.DCd[ii].get_orderfit(),self.DCd[ii].get_fractVgsfit(),self.DCd[ii].get_devicename()))
# 			fwdat.close()
# 		elif type=='TF':
# 			# write header data to wafer data file
# 			filename = self.pathname_waferlevel+"/"+self.wafername+"_Rc_TF_waferdata.xls"
# 			fwdat = open(filename,'w')
# 			fwdat.write('# Data from Id(Vgs) single-swept transfer curve\n')
# 			fwdat.write('# Contact resistance calculated via the Y-function method\n')
# 			fwdat.write('# wafername\t'+self.DCd[0].get_wafername()+'\n#\n')
# 			fwdat.write('# X (um)\tY (um)\tRc_TF\t# datapoints at gate compliance\t# datapoints at drain compliance\tpolynomial order\tdelta Vgs for linear fit\tdevice name\n')
#
# 			for ii in range(len(self.DCd)):
# 				if self.DCd[ii].Rc_TF() != "None":		# Data missing if "None" so write nothing if no data for this wafer location
# 					fwdat.write('%d\t%d\t%10.3E\t%d\t%d\t%d\t%10.3f\t%s\n' %(self.DCd[ii].x(),self.DCd[ii].y(),self.DCd[ii].Rc_TF(),self.DCd[ii].gatestatus_no_TF(),self.DCd[ii].drainstatus_no_TF(),self.DCd[ii].get_orderfit(),self.DCd[ii].get_fractVgsfit(),self.DCd[ii].get_devicename()))
# 			fwdat.close()
# 		elif type=='TR':
# 			# write header data to wafer data file
# 			filename = self.pathname_waferlevel+"/"+self.wafername+"_Rc_TR_waferdata.xls"
# 			fwdat = open(filename,'w')
# 			fwdat.write('# Data from Id(Vgs) single-swept transfer curve\n')
# 			fwdat.write('# Contact resistance calculated via the Y-function method\n')
# 			fwdat.write('# wafername\t'+self.DCd[0].get_wafername()+'\n#\n')
# 			fwdat.write('# X (um)\tY (um)\tRc_TR\t# datapoints at gate compliance\t# datapoints at drain compliance\tpolynomial order\tdelta Vgs for linear fit\tdevice name\n')
#
# 			for ii in range(len(self.DCd)):
# 				if self.DCd[ii].Rc_TR() != "None":		# Data missing if "None" so write nothing if no data for this wafer location
# 					fwdat.write('%d\t%d\t%10.3E\t%d\t%d\t%d\t%10.3f\t%s\n' %(self.DCd[ii].x(),self.DCd[ii].y(),self.DCd[ii].Rc_TR(),self.DCd[ii].gatestatus_no_TR(),self.DCd[ii].drainstatus_no_TR(),self.DCd[ii].get_orderfit(),self.DCd[ii].get_fractVgsfit(),self.DCd[ii].get_devicename()))
# 			fwdat.close()
# ########################################################################################################################
# # write the maximum gm of CFETs as a function of wafer location as calculated from the single-swept transfer curve using the Y-function
# # the gm is calculated from a polynomial fit of Id[Vgs] using a polynomial of the specifed order .get_orderfit()
# 	def write_waferparameter_maxgm(self,type):
# 		self.__get_parametersDC()	# get DC IV measured and calculated parameters for all devices measured on the wafer
# 		if type=='T':
# 			# write header data to wafer data file
# 			filename = self.pathname_waferlevel+"/"+self.wafername+"_max_gm_T_waferdata.xls"
# 			fwdat = open(filename,'w')
# 			fwdat.write('# Data from Id(Vgs) single-swept transfer curve\n')
# 			fwdat.write('# Max gm from polynomial curve fit of Id\n')
# 			fwdat.write('# drain voltage Vds\t%10.3f\n' %self.DCd[0].Vds_T())
# 			fwdat.write('# wafername\t'+self.DCd[0].get_wafername()+'\n#\n')
# 			fwdat.write('# X (um)\tY (um)\tmax gm (S)\t# datapoints at gate compliance\t# datapoints at drain compliance\tpolynomial order\tdelta Vgs for linear fit\tdevice name\n')
# 			for ii in range(len(self.DCd)):
# 				if self.DCd[ii].gmmax_T() != None:
# 					fwdat.write('%d\t%d\t%10.3E\t%d\t%d\t%d\t%10.3f\t%s\n' %(self.DCd[ii].x(),self.DCd[ii].y(),self.DCd[ii].gmmax_T()['G'],self.DCd[ii].gatestatus_no_T(),self.DCd[ii].drainstatus_no_T(),self.DCd[ii].get_orderfit(),self.DCd[ii].get_fractVgsfit(),self.DCd[ii].get_devicename()))
# 			fwdat.close()
# 		elif type=='TF':
# 			# write header data to wafer data file
# 			filename = self.pathname_waferlevel+"/"+self.wafername+"_max_gm_TF_waferdata.xls"
# 			fwdat = open(filename,'w')
# 			fwdat.write('# Data from Id(Vgs) single-swept transfer curve\n')
# 			fwdat.write('# Max gm from polynomial curve fit of Id\n')
# 			fwdat.write('# drain voltage Vds\t%10.3f\n' %self.DCd[0].Vds_TF())
# 			fwdat.write('# wafername\t'+self.DCd[0].get_wafername()+'\n#\n')
# 			fwdat.write('# X (um)\tY (um)\tmax gm (S)\t# datapoints at gate compliance\t# datapoints at drain compliance\tpolynomial order\tdelta Vgs for linear fit\tdevice name\n')
# 			for ii in range(len(self.DCd)):
# 				if self.DCd[ii].gmmax_TF() != None:
# 					fwdat.write('%d\t%d\t%10.3E\t%d\t%d\t%d\t%10.3f\t%s\n' %(self.DCd[ii].x(),self.DCd[ii].y(),self.DCd[ii].gmmax_TF()['G'],self.DCd[ii].gatestatus_no_TF(),self.DCd[ii].drainstatus_no_TF(),self.DCd[ii].get_orderfit(),self.DCd[ii].get_fractVgsfit(),self.DCd[ii].get_devicename()))
# 			fwdat.close()
# 		elif type=='TR':
# 			# write header data to wafer data file
# 			filename = self.pathname_waferlevel+"/"+self.wafername+"_max_gm_TR_waferdata.xls"
# 			fwdat = open(filename,'w')
# 			fwdat.write('# Data from Id(Vgs) single-swept transfer curve\n')
# 			fwdat.write('# Max gm from polynomial curve fit of Id\n')
# 			fwdat.write('# drain voltage Vds\t%10.3f\n' %self.DCd[0].Vds_TR())
# 			fwdat.write('# wafername\t'+self.DCd[0].get_wafername()+'\n#\n')
# 			fwdat.write('# X (um)\tY (um)\tmax gm (S)\t# datapoints at gate compliance\t# datapoints at drain compliance\tpolynomial order\tdelta Vgs for linear fit\tdevice name\n')
# 			for ii in range(len(self.DCd)):
# 				if self.DCd[ii].gmmax_TR() != None:
# 					fwdat.write('%d\t%d\t%10.3E\t%d\t%d\t%d\t%10.3f\t%s\n' %(self.DCd[ii].x(),self.DCd[ii].y(),self.DCd[ii].gmmax_TR()['G'],self.DCd[ii].gatestatus_no_TR(),self.DCd[ii].drainstatus_no_TR(),self.DCd[ii].get_orderfit(),self.DCd[ii].get_fractVgsfit(),self.DCd[ii].get_devicename()))
# 			fwdat.close()
# 		else:
# 			raise ValueError("ERROR! incorrect data type specified")
# ########################################################################################################################
# # write the threshold voltage of CFETs as a function of wafer location as calculated from the single-swept transfer curve using the Y-function
# # the gm is calculated from a polynomial fit of Id[Vgs] using a polynomial of the specifed order .get_orderfit()
# 	def write_waferparameter_Vth_T(self):
# 		self.__get_parametersDC()	# get DC IV measured and calculated parameters for all devices measured on the wafer
# 		# write header data to wafer data file
# 		filename = self.pathname_waferlevel+"/"+self.wafername+"_Vth_T_waferdata.xls"
# 		fwdat = open(filename,'w')
# 		fwdat.write('# Data from Id(Vgs) single-swept transfer curve\n')
# 		fwdat.write('# Max gm from polynomial curve fit of Id\n')
# 		fwdat.write('# drain voltage Vds\t%10.3f\n' %self.DCd[0].Vds_T())
# 		fwdat.write('# wafername\t'+self.DCd[0].get_wafername()+'\n#\n')
# 		fwdat.write('# X (um)\tY (um)\tVth\t# datapoints at gate compliance\t# datapoints at drain compliance\tpolynomial order\tdelta Vgs for linear fit\tdevice name\n')
# 		for ii in range(len(self.DCd)):
# 			if self.DCd[ii].Vth_YT() != "None":
# 				fwdat.write('%d\t%d\t%10.3f\t%d\t%d\t%d\t%10.3f\t%s\n' %(self.DCd[ii].x(),self.DCd[ii].y(),self.DCd[ii].Vth_YT(),self.DCd[ii].gatestatus_no_T(),self.DCd[ii].drainstatus_no_T(),self.DCd[ii].get_orderfit(),self.DCd[ii].get_fractVgsfit(),self.DCd[ii].get_devicename()))
# 		fwdat.close()
# ########################################################################################################################
# # write the on resistance values from the family of curves data as a function of Vgs (gate voltage)
# # assumes all devices on the wafer were measured with and same Vds and Vgs values
# # currently not used
# 	def write_waferparameter_Ron(self):
# 		self.__get_parametersDC()	# get DC IV measured and calculated parameters for all devices measured on the wafer
# 		# write header data to wafer data file
# 		filename = self.pathname_waferlevel+"/"+self.wafername+"_Ron_foc_waferdata.xls"
# 		fwdat = open(filename,'w')
# 		fwdat.write('# Data from Id[Vgs][Vds] family of curves for TLM devices\n')
# 		fwdat.write('# Maximum Vds in family of curves\t%10.3f\n' % max(self.DCd[self.focfirstdevindex].Id_foc()['Vds']))
# 		fwdat.write('# fraction of Vds over which a line is fit to obtain Ron\t%10.3f\n' % self.DCd[self.focfirstdevindex].get_fractVgsfit())		# note that get_fractVgsfit() is also the fraction of Vds used to calculate Ron
# 		fwdat.write('# wafername\t'+self.DCd[0].get_wafername()+'\n#\n')
# 		fwdat.write('# X (um)\tY (um)\ton resistance (ohms)\tfit quality\tnumber of bad readings (compliance, etc..)\tdevice name\n')
# 		for ig in range(0, len(self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'])):
# 			fwdat.write('# Vgs =\t%5.2f\n' %self.DCd[0].Ron_foc()['Vgs'][ig])				# assumes that the gate voltages are the same for all devices in the TLM array of devices
# 			for isite in range(len(self.DCd)):
# 				if self.DCd[isite].Ron_foc() != None:
# 					fwdat.write('%d\t%d\t%10.2E\t%5.1f\t%d\t%s\n' %(self.DCd[isite].x(),self.DCd[isite].y(),self.DCd[isite].Ron_foc()['R'][ig],self.DCd[isite].Ron_foc()['Q'][ig],self.DCd[isite].gatestatus_no_foc()+self.DCd[isite].drainstatus_no_foc(),self.DCd[isite].get_devicename()))
# 		fwdat.close()
# ########################################################################################################################
# # write the TLM contact resistance as a function of wafer location as calculated from the family of curves IV
# # currently not used
# 	def write_waferparameter_Rc_TLM(self):
# 		self.get_parametersTLM()	# get TLM parameters for all devices measured on the wafer indexed by [site]
# 		# write header data to wafer data file
# 		filename = self.pathname_waferlevel+"/"+self.wafername+"_Rc_TLM_waferdata.xls"
# 		fwdat = open(filename,'w')
# 		fwdat.write('# Data from Id[Vgs][Vds] family of curves for TLM devices\n')
# 		fwdat.write('# wafername\t'+self.TLMd[0].get_wafername()+'\n#\n')
# 		fwdat.write('# X (um)\tY (um)\tcontact resistance (ohms)\tfit quality\tsite name\n')
# 		for ig in range(0,len(self.TLMd[0].Rc()['Vgs'])):
# 			fwdat.write('# Vgs =\t%5.2f\n' %self.TLMd[0].Rc()['Vgs'][ig])				# assumes that the gate voltages are the same for all devices in the TLM array of devices
# 			for isite in range(len(self.TLMd)):
# 				if self.TLMd[isite].Rc() != None:
# 					fwdat.write('%d\t%d\t%10.2E\t%5.2f\t%s\n' %(self.TLMd[isite].x(),self.TLMd[isite].y(),self.TLMd[isite].Rc()['R'][ig],self.TLMd[isite].fitquality()['Q'][ig],self.TLMd[isite].get_sitename()))
# 		fwdat.close()
# ########################################################################################################################
# # write the TLM channel resistance/channel length as a function of wafer location as calculated from the family of curves IV
# 	# junk line for future reference ig = min(range(len(self.TLMd[isite].Rch()['Vgs'])), key=lambda i: abs(self.TLMd[isite].Rch()['Vgs'][i]-Vgs))	# index of gate voltage closest to that targeted (Vgs)
# # currently not used
# 	def write_waferparameter_Rsh_TLM(self):
# 		self.get_parametersTLM()	# get TLM parameters for all devices measured on the wafer indexed by [site]
# 		# write header data to wafer data file
# 		filename = self.pathname_waferlevel+"/"+self.wafername+"_Rsh_TLM_waferdata.xls"
# 		fwdat = open(filename,'w')
# 		fwdat.write('# Data from Id[Vgs][Vds] family of curves for TLM devices\n')
# 		fwdat.write('# Minimum mask TLM length used \t%5.1f\n' % self.minTLMlength)
# 		fwdat.write('# Maximum mask TLM length used \t%5.1f\n' % self.maxTLMlength)
# 		fwdat.write('# fraction of Vds range used to find Ron \t%5.1f\n' % self.fractVdsfit_Ronfoc)
# 		fwdat.write('# wafername\t'+self.TLMd[0].get_wafername()+'\n#\n')
# 		fwdat.write('# X (um)\tY (um)\tchannel sheet resistance (ohms/um)\tfit quality\tsite name\n')
# 		for ig in range(0,len(self.TLMd[0].Rch()['Vgs'])):
# 			fwdat.write('# Vgs =\t%5.2f\n' %self.TLMd[0].Rch()['Vgs'][ig])				# assumes that the gate voltages are the same for all devices in the TLM array of devices
# 			for isite in range(len(self.TLMd)):
# 				if self.TLMd[isite].Rch() != None:
# 					fwdat.write('%d\t%d\t%10.2E\t%5.2f\t%s\n' %(self.TLMd[isite].x(),self.TLMd[isite].y(),self.TLMd[isite].Rch()['R'][ig],self.TLMd[isite].fitquality()['Q'][ig],self.TLMd[isite].get_sitename()))
# 		fwdat.close()
########################################################################################################################
# set minimum gm allowed to screen devices to be analyzed as TLM data and later, perhaps, as a general device screen
#
	def set_mingm(self,mingm):
		self.__mingm=mingm
########################################################################################################################
# set maximum TLM length in um to be considered in the TLM analysis
#
	# def set_maxtlmlength(self,maxtlmlength):
	# 	self.maxTLMlength=maxtlmlength
########################################################################################################################
# set minimum TLM length in um to be considered in the TLM analysis
#
	def set_mintlmlength(self,mintlmlength):
		self.minTLMlength=mintlmlength
########################################################################################################################
# set minimum gm allowed to screen devices to be analyzed as TLM data
#
	def setTLM_mingm(self,mingm):
		self.__mingm=mingm
########################################################################################################################
#instantiate device parameters class for measured DC parameters and get RF linear and RF power data structure if such data exist
# NOTE and CAUTION
# changing the wafer plan file DOES NOT update the device gate widths and DOES NOT update the TLM lengths. You must reload the wafer to do this!
# major change March 7, 2016 Now device structures are contained in a dictionary with the devicenames as keys

# Note that as of April 12, 2016 four-sweep transfer curves are now handled EXCLUSIVE to dual-swept transfer curves We can have one or the other but not both in the same dataset
# because to process four swept transfer data, the first two sweeps are handled as forward and reverse transfer curve data respectively, which could overwrite
# data from dual swept transfer curves if processing of both types of data were allowed for the same dataset
# If processing of both data types becomes common, then we will need to add the capability
	def __get_parametersDC(self):
		if not hasattr(self,"DCd"): # calculate if the device parameters have not already been calculated i.e. instantiated
			fdc = getfilelisting(self.pathname+sub("DC"),".xls",self.wafername)
			dir_save = self.parent.dirname + sub('save')
			#try: datasettings=pick.load(open(dir_save+'/'+filesavesettings[0],"rb"))		# get last saved settings
			if fdc != None and len(fdc)>0:
				# check to see if we have both transferloop and transferloop4 data. If so, this is an error condition - until the program is modified to process both data sets, transferloop and transferloop4 together
				self.havetransfer=False
				havetransferloop=False
				havetransferloop4=False
				for f in fdc:
					if "transferloop" in f and not "transferloop4" in f: havetransferloop=True
					if "transfer." in f: self.havetransfer=True     # have single-swept transfer curve data, this will be used to notify the parent in actions_histogram.py to turn on the appropriate entries in the main GUI
					if "transferloop4" in f: havetransferloop4=True
				if havetransferloop and havetransferloop4: raise ValueError("ERROR! Have both transferloop and transferloop4 data which is NOT currently allowed")
				###
				devlistingDC = file_to_devicename(inputdevlisting=fdc,deleteendstrings=["_transfer","_transferloop","_transferloop4",".xls","_foc","_loopfoc","_loop4foc","_pulsedtimedomain","_pulsedtransfertimedomain","_pulseddraintimedomain"])
				self.DCd = {f:DeviceParameters(pathname=self.pathname,devicename=f,fractVgsfit=self.fractVgsfit,Y_Ids_fitorder=self.order,fractftfit=self.fractftfit,fractfmaxfit=self.fractfmaxfit,fractVdsfit_Ronfoc=self.fractVdsfit_Ronfoc,devicetype=self.devicetype)  for f in devlistingDC }		# get array of device parameters from each device represented by the file listing

				if 'linux' in _platform:                # then multiprocess i.e. use multiple cores only if this is Linux
					devlist = split_device_list(self.DCd.keys())  # split up device list according to number of cores on this machine
					qw = [mp.Queue() for i in range(0,len(devlist))]  # get queues for worker outputs
					workers = [mp.Process(target=getDC_multiprocess, args=(qw[i],self.DCd,devlist[i],self.gatewidth,self.tlmlength,self.leadresistance,self.parent.Vds_FOC.text())) for i in range(0,len(devlist))]  # get list of workers
					starttime = time.time()
					for iw in  range(len(workers)):
						workers[iw].start()

					#print("from line 349 in wafer_analysis.py")
					for iw in range(0, len(devlist)):
						self.DCd.update(qw[iw].get())
						workers[iw].join()

					print("elapsed time DC = ", time.time() - starttime)
					del workers
					del qw
				elif 'win' in _platform:            # avoid using multiprocessing in Windows because it's too slow - too much overhead from pickling
					cdret=getDC_multiprocess(None,self.DCd,self.DCd.keys(),self.gatewidth,self.tlmlength,self.leadresistance,self.parent.Vds_FOC.text())
					self.DCd.update(cdret)
				else: raise ValueError("ERROR! unknown operating system - neither Windows nor Linux")

				self.validdevices=c.deque(list(self.DCd.keys()))
				invalidVgs=False
				for devk in self.DCd:
					try: self._Vgsarray= self.DCd[devk].Ron_foc()['Vgs']
					except: invalidVgs=True
					# TODO: need to fix Vgs array generation in general - skipping over probe resistance test devices to form Vgs array
					if 'proberesistancetest' not in devk and not invalidVgs and self.DCd[devk].gatestatus_no_foc()==0 and self.DCd[devk].drainstatus_no_foc()==0:# iterate through measured family of curves data until we find a device with gate and drain not in compliance and with measured data
						print("Have good Vgs line 369 in wafer_analysis.py", devk) #debug
						break
					if 'proberesistancetest' in devk: self.proberesistanceindex=devk
					invalidVgs=False
				self.focfirstdevindex=devk										# this is the key, i.e. device name of the first device data read which holds valid family of curves data
				#print("from line 370 in wafer_analysis.py",devk,self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'])
				try: self._Vgsarray= self.DCd[self.focfirstdevindex].Ron_foc()['Vgs']				# get array of gate voltages used in family of curves measurements -assumes that all devices in the wafer were measured using the same gate voltages
				except:
					if self.proberesistanceindex!=None: self.focfirstdevindex=self.proberesistanceindex									# no valid family of curves data exist so set the index to 0
					#if self.focfirstdevindex==None: self.focfirstdevindex=
					print("from wafer_analysis.py line 374 NO family of curves valid data files")  #debug
					self.havefocdata=False
			else: # no DC measurements
				self.DCd={}
				self.validdevices=c.deque()
			# now form device templates for RF data #################################################################
			# will add RF power data later
			fSPAR=getfilelisting(self.pathname+sub("SPAR"),".s2p",self.wafername)													# get S-parameter filenames
			if fSPAR!=None and len(fSPAR)>0: fSPAR.extend(getfilelisting(self.pathname+sub("NOISE"),"noiseparameter.xls",self.wafername)) # add noise parameter filenames
			else: fSPAR=getfilelisting(self.pathname+sub("NOISE"),"noiseparameter.xls",self.wafername)													# get noise-parameter filenames

			DCdevk=self.DCd.keys()				# get all DC device keys
			if fSPAR!=None and len(fSPAR)>0:  # then we have S-parameter data
				devlistingSPAR = file_to_devicename(inputdevlisting=fSPAR, deleteendstrings=["_SRI","_SDB", ".s2p","_noise.xls","_noiseparameter.xls"])
				for devk in devlistingSPAR:
					if devk not in DCdevk:                  # does this device also have DC parameters?
						SPARdevicetype=devk.split("__")[1]                                      # get
						DCdevicemateofdevk="".join([self.wafername,"__",SPARdevicetype])
						if DCdevicemateofdevk in self.DCd:
							self.DCd[devk]=copy.copy(self.DCd[DCdevicemateofdevk])				# load DC parameters from the device into those to contain the S-parameters or noise parameters
							self.DCd[devk].devicename=devk							# keep the device name consistent (the same as) with the key name
						else: self.DCd[devk]=DeviceParameters(pathname=self.pathname,devicename=devk,fractVgsfit=self.fractVgsfit,Y_Ids_fitorder=self.order,fractftfit=self.fractftfit,fractfmaxfit=self.fractfmaxfit,fractVdsfit_Ronfoc=self.fractVdsfit_Ronfoc,devicetype=self.devicetype)	# add templates for devices which have RF data only
						self.validdevices.append(devk)  # initially add to valid devices
						if self.gatewidth != None:
							for gk in self.gatewidth:
								if gk in devk: self.DCd[devk].devwidth = self.gatewidth[gk]
						if self.tlmlength != None:
							for tk in self.tlmlength:
								if tk in devk: self.DCd[devk].tlmlength = self.tlmlength[tk]  # note that devk is the key and also the device name
					if self.DCd[devk].devicename != devk:    raise ValueError("ERROR inconsistent device name" + self.DCd[devk].devicename + " " + devk)
					self.DCd[devk].ft()  # get S-parameters for this device if available
					self.DCd[devk].get_NF50()   # get noise figure parameters as measured in a 50ohm system without tuner
					self.DCd[devk].get_noise_parameters()       # get tuned noise parameters
					if self.DCd[devk].devicename!=devk:	raise ValueError("ERROR inconsistent device name"+self.DCd[devk].devicename+" "+devk)
					#print("from line 417 in wafer_analysis.py fSpar",devk,self.DCd[devk].devicename)

			# now add third order intercept data if they exists
			fTOI=getfilelisting(self.pathname+sub("RF_power"),"TOI.xls",self.wafername)													# get S-parameter filenames
			if fTOI!=None and len(fTOI)>0:  # then we have RF third order intercept data
				devlistingTOI = file_to_devicename(inputdevlisting=fTOI, deleteendstrings=["_TOI.xls"])
				for devk in devlistingTOI:
					if devk not in DCdevk:
						TOIdevicetype=devk.split("__")[1]                                      # get
						DCdevicemateofdevk="".join([self.wafername,"__",TOIdevicetype])
						if DCdevicemateofdevk in self.DCd:
							self.DCd[devk]=copy.copy(self.DCd[DCdevicemateofdevk])				# load DC parameters from the device into those to contain the TOI
							self.DCd[devk].devicename=devk							# keep the device name consistent (the same as) with the key name
						else: self.DCd[devk]=DeviceParameters(pathname=self.pathname,devicename=devk,fractVgsfit=self.fractVgsfit,Y_Ids_fitorder=self.order,fractftfit=self.fractftfit,fractfmaxfit=self.fractfmaxfit,fractVdsfit_Ronfoc=self.fractVdsfit_Ronfoc,devicetype=self.devicetype)	# add templates for devices which have TOI data only
						self.validdevices.append(devk)  # initially add to valid devices
						if self.gatewidth != None:
							for gk in self.gatewidth:
								if gk in devk: self.DCd[devk].devwidth = self.gatewidth[gk]
						if self.tlmlength != None:
							for tk in self.tlmlength:
								if tk in devk: self.DCd[devk].tlmlength = self.tlmlength[tk]  # note that devk is the key and also the device name
					if self.DCd[devk].devicename != devk:    raise ValueError("ERROR inconsistent device name" + self.DCd[devk].devicename + " " + devk)
					self.DCd[devk].get_TOIoutmax()  # get TOI for this device if available
					if self.DCd[devk].devicename!=devk:	raise ValueError("ERROR inconsistent device name"+self.DCd[devk].devicename+" "+devk)

			# now add swept-Vgs third order intercept data, if they exist These data are measured with Vgs swept rapidly
			fTOI=getfilelisting(self.pathname+sub("RF_power"),"TOIVgssweepsearch.xls",self.wafername)													# get S-parameter filenames
			if fTOI!=None and len(fTOI)>0:  # then we have RF third order intercept data
				devlistingTOI = file_to_devicename(inputdevlisting=fTOI, deleteendstrings=["_TOIVgssweepsearch.xls"])
				for devk in devlistingTOI:
					if devk not in DCdevk:
						TOIdevicetype=devk.split("__")[1]                                      # get
						DCdevicemateofdevk="".join([self.wafername,"__",TOIdevicetype])
						if DCdevicemateofdevk in self.DCd:
							self.DCd[devk]=copy.copy(self.DCd[DCdevicemateofdevk])				# load DC parameters from the device into those to contain the TOI
							self.DCd[devk].devicename=devk							# keep the device name consistent (the same as) with the key name
						else: self.DCd[devk]=DeviceParameters(pathname=self.pathname,devicename=devk,fractVgsfit=self.fractVgsfit,Y_Ids_fitorder=self.order,fractftfit=self.fractftfit,fractfmaxfit=self.fractfmaxfit,fractVdsfit_Ronfoc=self.fractVdsfit_Ronfoc,devicetype=self.devicetype)	# add templates for devices which have TOI data only
						self.validdevices.append(devk)  # initially add to valid devices
						if self.gatewidth != None:
							for gk in self.gatewidth:
								if gk in devk: self.DCd[devk].devwidth = self.gatewidth[gk]
						if self.tlmlength != None:
							for tk in self.tlmlength:
								if tk in devk: self.DCd[devk].tlmlength = self.tlmlength[tk]  # note that devk is the key and also the device name
					if self.DCd[devk].devicename != devk:    raise ValueError("ERROR inconsistent device name" + self.DCd[devk].devicename + " " + devk)
					self.DCd[devk].get_TOImaxVgsswept()  # get Vgs swept TOI for this device if available
					if self.DCd[devk].devicename!=devk:	raise ValueError("ERROR inconsistent device name "+self.DCd[devk].devicename+" "+devk)

			# now add compression data
			fcompress=getfilelisting(self.pathname+sub("RF_power"),"PCOMPRESS.xls",self.wafername)													# get S-parameter filenames
			if fcompress!=None and len(fcompress)>0:  # then we have compression data
				devlistingcompress = file_to_devicename(inputdevlisting=fcompress, deleteendstrings=["_PCOMPRESS.xls"])
				for devk in devlistingcompress:
					if devk not in DCdevk:
						compressdevicetype=devk.split("__")[1]                                      # get
						DCdevicemateofdevk="".join([self.wafername,"__",compressdevicetype])
						if DCdevicemateofdevk in self.DCd:
							self.DCd[devk]=copy.copy(self.DCd[DCdevicemateofdevk])				# load DC parameters from the device into those to contain the compression data
							self.DCd[devk].devicename=devk							# keep the device name consistent (the same as) with the key name
						else: self.DCd[devk]=DeviceParameters(pathname=self.pathname,devicename=devk,fractVgsfit=self.fractVgsfit,Y_Ids_fitorder=self.order,fractftfit=self.fractftfit,fractfmaxfit=self.fractfmaxfit,fractVdsfit_Ronfoc=self.fractVdsfit_Ronfoc,devicetype=self.devicetype)	# add templates for devices which have compression data only
						self.validdevices.append(devk)  # initially add to valid devices
						if self.gatewidth != None:
							for gk in self.gatewidth:
								if gk in devk: self.DCd[devk].devwidth = self.gatewidth[gk]
						if self.tlmlength != None:
							for tk in self.tlmlength:
								if tk in devk: self.DCd[devk].tlmlength = self.tlmlength[tk]  # note that devk is the key and also the device name
					if self.DCd[devk].devicename != devk:    raise ValueError("ERROR inconsistent device name" + self.DCd[devk].devicename + " " + devk)
					self.DCd[devk].get_COMPRESSout()  # get compression for this device if available
					if self.DCd[devk].devicename!=devk:	raise ValueError("ERROR inconsistent device name"+self.DCd[devk].devicename+" "+devk)

			# add harmonic distortion data if it exists
			# fcompress=getfilelisting(self.pathname+sub("RF_power"),"harmdistortion.xls",self.wafername)													# get S-parameter filenames
			# if fcompress!=None and len(fcompress)>0:  # then we have compression data
			# 	devlistingharm = file_to_devicename(inputdevlisting=fcompress, deleteendstrings=["_harmdistortion.xls"])
			# 	for devk in devlistingharm:
			# 		if devk not in DCdevk:
			# 			harmdevicetype=devk.split("__")[1]                                      # get
			# 			DCdevicemateofdevk="".join([self.wafername,"__",harmdevicetype])
			# 			if DCdevicemateofdevk in self.DCd:
			# 				self.DCd[devk]=copy.copy(self.DCd[DCdevicemateofdevk])				# load DC parameters from the device into those to contain the compression data
			# 				self.DCd[devk].devicename=devk							# keep the device name consistent (the same as) with the key name
			# 			else: self.DCd[devk]=DeviceParameters(pathname=self.pathname,devicename=devk,fractVgsfit=self.fractVgsfit,Y_Ids_fitorder=self.order,fractftfit=self.fractftfit,fractfmaxfit=self.fractfmaxfit,fractVdsfit_Ronfoc=self.fractVdsfit_Ronfoc,devicetype=self.devicetype)	# add templates for devices which have harmonic data only
			# 			self.validdevices.append(devk)  # initially add to valid devices
			# 			if self.gatewidth != None:
			# 				for gk in self.gatewidth:
			# 					if gk in devk: self.DCd[devk].devwidth = self.gatewidth[gk]
			# 			if self.tlmlength != None:
			# 				for tk in self.tlmlength:
			# 					if tk in devk: self.DCd[devk].tlmlength = self.tlmlength[tk]  # note that devk is the key and also the device name
			# 		if self.DCd[devk].devicename != devk:    raise ValueError("ERROR inconsistent device name" + self.DCd[devk].devicename + " " + devk)
			# 		self.DCd[devk].get_COMPRESSout()  # get compression for this device if available
			# 		if self.DCd[devk].devicename!=devk:	raise ValueError("ERROR inconsistent device name"+self.DCd[devk].devicename+" "+devk)

			if (fdc==None or len(fdc)==0) and (fSPAR==None or len(fSPAR)==0) and (fTOI==None or len(fTOI)==0): return None
			else: return fdc,fSPAR
#########################################################################################################################
# S-parameters multiprocessing
# 	def _getS_mulitprocess(self,que,cd,devicelist):
# 		for devk in devlistingSPAR:
# 			if devk not in DCdevk:
# 				SPARdevicetype = devk.split("__")[1]
# 				DCdevicemateofdevk = "".join([self.wafername, "__", SPARdevicetype])
# 				if DCdevicemateofdevk in self.DCd:
# 					# self.DCd[devk] = DeviceParameters(pathname=self.pathname, devicename=devk, fractVgsfit=self.fractVgsfit, Y_Ids_fitorder=self.order, fractftfit=self.fractftfit, fractfmaxfit=self.fractfmaxfit, fractVdsfit_Ronfoc=self.fractVdsfit_Ronfoc, devicetype=self.devicetype)  # add templates for devices which have RF data only
# 					self.DCd[devk] = copy.deepcopy(self.DCd[DCdevicemateofdevk])  # load DC parameters from the device into those to contain the S-parameters
# 					self.DCd[devk].devicename = devk  # keep the device name consistent (the same as) with the key name
# 				else:
# 					self.DCd[devk] = DeviceParameters(pathname=self.pathname, devicename=devk, fractVgsfit=self.fractVgsfit, Y_Ids_fitorder=self.order, fractftfit=self.fractftfit, fractfmaxfit=self.fractfmaxfit, fractVdsfit_Ronfoc=self.fractVdsfit_Ronfoc, devicetype=self.devicetype)  # add templates for devices which have RF data only
# 				self.validdevices.append(devk)  # initially add to valid devices
# 				if self.gatewidth != None:
# 					for gk in self.gatewidth:
# 						if gk in devk: self.DCd[devk].devwidth = self.gatewidth[gk]
# 				if self.tlmlength != None:
# 					for tk in self.tlmlength:
# 						if tk in devk: self.DCd[devk].tlmlength = self.tlmlength[tk]  # note that devk is the key and also the device name
# 			if self.DCd[devk].devicename != devk:    raise ValueError("ERROR inconsistent device name" + self.DCd[devk].devicename + " " + devk)
# 			self.DCd[devk].ft()  # get S-parameters for this device if available
# 			# self.DCd[devk].fmax()
# 			if self.DCd[devk].devicename != devk:    raise ValueError("ERROR inconsistent device name" + self.DCd[devk].devicename + " " + devk)
#########################################################################################################################
	#	multithread for forming device DC data
	# def _getDC_multiprocess(self,que,cd,devicelist):
	# 	DCd = {}
	# 	for devk in devicelist:  # now set the lead resistance for all the devices according to the values in the geometry file and also set the device as valid
	# 		# self.validdevices.append(devk)  # while we're at it, initially set devices as valid until the filter is applied
	# 		DCd[devk] = cd[devk]
	# 		DCd[devk].set_leadresistance(self.leadresistance)
	#
	# 		# iterate through measured data devices and set  lengths and device scaling. the key contains a portion of the name of the target devices
	# 		if self.gatewidth != None:
	# 			for gk in self.gatewidth:
	# 				if gk in devk: DCd[devk].devwidth = self.gatewidth[gk]
	# 		if self.tlmlength != None:
	# 			for tk in self.tlmlength:
	# 				if tk in devk: DCd[devk].tlmlength = self.tlmlength[tk]  # note that devk is the key and also the device name
	# 		# get all DC parameters
	# 		# DCd[devk].Id_foc()  ## Now read in family of curves data and calculate parameters derived from it
	# 		# DCd[devk].Id_T()
	# 		# DCd[devk].Id_TF()
	# 		# DCd[devk].Id_TR()
	# 		# DCd[devk].Id_T3()
	# 		# DCd[devk].Id_T4()
	# 		DCd[devk].Idmax_T()
	# 		DCd[devk].Idmax_TF()
	# 		DCd[devk].Idmax_TR()
	# 		DCd[devk].Idmax_T3()
	# 		DCd[devk].Idmax_T4()
	# 		DCd[devk].Idonoffratio_T()
	# 		DCd[devk].Idonoffratio_TF()
	# 		DCd[devk].Idonoffratio_TR()
	# 		DCd[devk].Idonoffratio_T3()
	# 		DCd[devk].Idonoffratio_T4()
	# 		DCd[devk].Ron_foc()
		# print("from line 453 in wafer_analysis.py DCd[devk].devwidth= ",devk,DCd[devk].tlmlength,DCd[devk].devwidth,DCd[devk].x_location,DCd[devk].Vds_IVt)
		#que.put(DCd)
		#return self
########################################################################################################################
#instantiate device parameters class for measured TLM parameters and related data
# gets the TLM data for a selected Vgs
# Vgs_selected is the Vgs closest to that measured to use when calculating the TLM parameters from the family of curves data
# linearfitquality_request is the requested value of the rval for the least-squares linear fit. This instructs the TLM Rc, Rsh calculator to remove outlier TLM resistance (Ron)
# points until the least squares linear fit as measured by its rval=0 to 1 is at least as good as requested
# Ron is in ohm*mm
	def get_parametersTLM(self, fractVdsfit=None, Vgs_selected=None, validdevices=None, minTLMlength=None, maxTLMlength=None, force_calculation=False,linearfitquality_request=None):#,filter_TLM_Rsh_min=None,filter_TLM_Rsh_max=None,filter_TLM_Rc_min=None,filter_TLM_Rc_max=None):
		if self.havefocdata and Vgs_selected!='' and Vgs_selected!=None: Vgs_selected=float(Vgs_selected)
		else: return False								# no TLM data so don't try to calculate
		if self.DCd[self.focfirstdevindex].Ron_foc()==None: return False
		if fractVdsfit!=None and is_number(fractVdsfit): fractVdsfit=float(fractVdsfit)
		if minTLMlength!=None and is_number(minTLMlength):
			minTLMlength=float(minTLMlength)
		else: minTLMlength=None
		if maxTLMlength!=None and is_number(maxTLMlength):
			maxTLMlength=float(maxTLMlength)
		else: maxTLMlength=None

		if validdevices == None or len(validdevices)<1: validdevices = self.validdevices
		if validdevices == None or len(validdevices)<1: validdevices = self.DCd.keys()
		if validdevices == None or len(validdevices)<1: raise ValueError("ERROR! no devices")

		haveTLMdata=True										# flag to determine presence of any TLM data
		if self.tlmlength==None: return False
		if self.__get_parametersDC()=='No Files Found': return False

		#if (self.minTLMlength==None or self.maxTLMlength==None) or ( (minTLMlength!=None and maxTLMlength!=None) and (not floatequal(self.minTLMlength, minTLMlength, 1.E-3) or not floatequal(maxTLMlength, self.maxTLMlength, 1.E-3)) ): # since the TLM minimum and maximum lengths are changed, we need to recalculate
		if (self.minTLMlength==None or self.maxTLMlength==None) or ( (minTLMlength!=None and maxTLMlength!=None) and (not floatequal(self.minTLMlength, minTLMlength, 1.E-3) or not floatequal(maxTLMlength, self.maxTLMlength, 1.E-3)) ): # since the TLM minimum and maximum lengths are changed, we need to recalculate
			force_calculation=True
			self.minTLMlength=minTLMlength
			self.maxTLMlength=maxTLMlength

		if self.minTLMlength == None or self.maxTLMlength == None: return False			# minimum and maximum TLM lengths must be set at some point or the TLM calculation will not proceed

		if self.devicefilteredTLM == True:  # were the devices filtered and acknowledged by this method?
			force_calculation = True
			self.devicefilteredTLM = False

		#if self.minTLMlength==None or self.maxTLMlength==None: return False
		if Vgs_selected!=None and not floatequal(Vgs_selected,self.__Vgs_selected_TLM,1.E-3):	# since the gate voltage where the TLM parameters are calculated has changed, we need to recalculate
			force_calculation=True
			self.__Vgs_selected=Vgs_selected
			self.__Vgs_selected_TLM=Vgs_selected
		if fractVdsfit!=None and not floatequal(self.__fractVdsfit_TLM,fractVdsfit,1.E-3):
			force_calculation=True
			self.fractVdsfit_Ronfoc=fractVdsfit
			self.__fractVdsfit_TLM=fractVdsfit
			for devk in self.DCd: self.DCd[devk].Ron_foc(fractVdsfit=self.__fractVdsfit_TLM)				# update linear fit to Id(Vds) curves if necessary i.e. if the fractVdsfit not nearly equal to that of the devices or if no Ron has been calculated

		if linearfitquality_request!=None and (self.linearfitquality_request==None or not floatequal(self.linearfitquality_request,linearfitquality_request,1.E-3)):					# must calculate new TLM parameters if fit quality requested has changed
			force_calculation=True
			self.linearfitquality_request=linearfitquality_request

		#force_calculation=True
		#print("line 544 in wafer_analysis.py force_calculation",force_calculation)
		if force_calculation==True:						#then redo the TLM calculations
			#print("from line 387 in wafer_analysis.py calculating TLM")
			haveTLMdata=False
			iVgs = min(range(len(self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'])),key=lambda i: abs(self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'][i]-self.__Vgs_selected_TLM))		# get the index of the requested gate voltage: assume that Vgs values are the same for all devices in the wafer self.focfirstdevindex is the device index of the first "good" family of curves IV measurement e.g. no measurements in compliance etc..
			self.iVgs_selected=iVgs             # This is the selected Vgs for the calculation of Ron
			Vgs=self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'][iVgs]					# actual Vgs used
			# first get site names
			TLMsitenames=list(set([d.split('TLM')[0] for d in self.DCd if 'TLM' in d and invalidTLMorthdevice not in d]))				# get the TLM site names i.e. unique names excluding the part of the name specific to the TLM devices within the site
			####TLMsitenames=list(set([d.split('TLM')[0] for d in self.DCd if 'TLM' in d and d in validdevices]))				# get the TLM site names i.e. unique names excluding the part of the name specific to the TLM devices within the site
			self.TLMdict = {s:[self.DCd[d] for d in validdevices if s in d and invalidTLMorthdevice not in d] for s in TLMsitenames}  # get dictionary TLMdict['TLMsitename'][TLMdeviceindex] which is a dictionary of devices with keys of the TLM site name.
			# print("from line 532 in wafer_analysis.py self.tlmlength",self.tlmlength)
			# #debug####################
			# for tsite in self.TLMdict:
			# 	for d in self.TLMdict[tsite]:
			# 		#d.devicename
			# 		if "0.7" in d.devicename:
			# 			print("from wafer_analysis.py line 533 TLM ",d.devicename.split(tsite)[1])
			# # for d in validdevices:
			# 	if "0.7" in d:
			# 		print("from wafer_analysis.py line 533 TLM ",d)
			################# end debug
			Rc={}
			TLMfit={}
			Rsh={}
			TLMlengths={}
			Ron={}
			totalnopointsincompliance={}
			for k in self.TLMdict:					# k is the TLM device site name i.e. name of a group of devices which form a TLM structure
				#TLMlen_=[self.tlmlength[d.devicename.split(k)[1]] for d in self.TLMdict[k] if d.devicename.split(k)[1] in self.tlmlength and len(d.Ron_foc())>0]
				#Ron_=[d.Ron_foc()['R'][iVgs] for d in self.TLMdict[k] if d.devicename.split(k)[1] in self.tlmlength and len(d.Ron_foc())>0 and len(d.Ron_foc()['R'])>iVgs]
				#print("from wafer_analysis.py line 634 k=",k,self.tlmlength)
				TLMlen_=[self.tlmlength[d.devicename.split(k)[1].split('_')[1]] for d in self.TLMdict[k] if (d.devicename.split(k)[1] in self.tlmlength or d.devicename.split(k)[1].split('_')[1] in self.tlmlength) and len(d.Ron_foc())>0]
				Ron_=[d.Ron_foc()['R'][iVgs] for d in self.TLMdict[k] if (d.devicename.split(k)[1] in self.tlmlength or d.devicename.split(k)[1].split('_')[1] in self.tlmlength) and len(d.Ron_foc())>0 and len(d.Ron_foc()['R'])>iVgs]
				# Ron_=[]
				# for d in self.TLMdict[k]:
				# 	if (d.devicename.split(k)[1] in self.tlmlength or d.devicename.split(k)[1].split('_')[1] in self.tlmlength) and len(d.Ron_foc())>0 and len(d.Ron_foc()['R'])>iVgs:
				# 		Ron_.append(d.Ron_foc()['R'][iVgs])
				if len(Ron_)>1:					# must have at least two devices in a TLM site to calculate TLM data
					para=sorted(zip(Ron_,TLMlen_),key=lambda tup: tup[1])					# sort by TLM lengths
					# unpack values lists
					#devnames=[p[0] for p in para]
					Ron[k]=[p[0] for p in para]
					TLMlengths[k]=[p[1] for p in para]
					r=calc_TLM(Ltlm=TLMlengths[k], Rtlm=Ron[k], minLtlm=self.minTLMlength, maxLtlm=self.maxTLMlength,linearfitquality_request=self.linearfitquality_request)			# calculate TLM parameters for this grouping of TLM devices (a single TLM site) r=None if have no TLM data here e.g. not enough good devices measured in this TLM group
					if r!=None: Rsh[k],Rc[k],TLMfit[k]=r							# add in TLM data only if it exists at this TLM site

					totalnopointsincompliance[k]=sum([d.gatestatus_no_foc()+d.drainstatus_no_foc() for d in self.TLMdict[k] if hasattr(d,'Ronfrom_foc') and d.Ron_foc()!=None and d.Ron_foc()!=None])			# total number of gate + drain measurement points that are abnormal (probably in compliance)

			# now translate the TLM subsite TLM data to the individual devices (where valid)
			#print("line 585 in wafer_analysis.py validdevices",validdevices)
			#deviceswithTLM=col.deque()			# array of all device names (keys) with valid TLM data
			for devk in validdevices:				# get TLM data for all TLM devices with valid data (data not filtered here)
				#if '_TLM' in devk:				# deal with ONLY devices which are part of a TLM structure
				#print("line 589 in wafer_analysis.py ")
				if 'TLM' in devk and invalidTLMorthdevice not in devk:				# deal with ONLY devices which are part of a TLM structure
					k=devk.split('TLM')[0]	# get k, the site name for this device - by trimming off the TLM individual (within site) name information from the device name. k will be used as a dictionary key to access the TLM data for a site
					if k in Rc and (self.filter_TLM_Rc_max==None or Rc[k]<=self.filter_TLM_Rc_max) and (self.filter_TLM_Rc_min==None or Rc[k]>=self.filter_TLM_Rc_min) and (self.filter_TLM_Rsh_max==None or Rsh[k]<=self.filter_TLM_Rsh_max) and (self.filter_TLM_Rsh_min==None or Rsh[k]>=self.filter_TLM_Rsh_min):											# be sure this device is part of a valid TLM site AND that the data are within a selected range
						#print("from line 591 in wafer_analysis.py ", self.DCd[devk].devicename, Rsh[k])
						#if "C6_R8_1ATLM_2" in self.DCd[devk].devicename: print("from line 591 in wafer_analysis.py for device C6_R8_1ATLM_2",self.DCd[devk].devicename,Rsh[k])
						self.DCd[devk].Rc_TLM=Rc[k]						# contact resistance in ohms if self.DCd[devk].devwidth (the device's width) is not specified otherwise it's in ohm*mm
						if self.DCd[devk].devwidth!=None and self.DCd[devk].devwidth>0: self.DCd[devk].Rsh_TLM=1000.*Rsh[k]						# set device parameter to sheet resistance for it's TLM grouping. Convert Kohm/square to ohms/square if device width is specified
						else: self.DCd[devk].Rsh_TLM=Rsh[k]
						self.DCd[devk].fit_TLM=TLMfit[k]				# set device parameter to the figure of merit for the least-squares linear fit to get Rc and Rsh for its TLM grouping
						self.DCd[devk].TLMlengths=TLMlengths[k]			# device parameter list of TLM lengths in the device's TLM grouping. This will be used to draw the linear fit for the TLM
						self.DCd[devk].TLM_Ron=Ron[k]					# device parameter list of Ron's in the device's TLM grouping. This will be used to draw the linear fit for the TLM
						self.DCd[devk].TLM_Vgs=Vgs						# gate voltage where the TLM structure parameters are calculated
						self.DCd[devk].TLM_min_fitlength=self.minTLMlength				# Minimum TLM length used to perform linear fit of TLM Ron vs TLM length
						self.DCd[devk].TLM_max_fitlength=self.maxTLMlength				# Minimum TLM length used to perform linear fit of TLM Ron vs TLM length
						self.DCd[devk].noptsincompliance_TLM=totalnopointsincompliance[k]			# total number of gate + drain measurement points that are abnormal (probably in compliance) for the whole TLM structure that this device is a part of
						haveTLMdata=True						# since we have TLM data for this device - append its name
					else:
						self.DCd[devk].Rc_TLM = None
						self.DCd[devk].Rsh_TLM=None
						self.DCd[devk].fit_TLM=None
						self.DCd[devk].TLMlengths=None
						self.DCd[devk].TLM_Ron=None
						self.DCd[devk].TLM_Vgs=None
						self.DCd[devk].TLM_min_fitlength=None
						self.DCd[devk].TLM_max_fitlength =None
						self.DCd[devk].noptsincompliance_TLM =None
		return haveTLMdata
########################################################################################################################

#instantiate device parameters class for measured orthogonal structure current and Ron ratios parameters
# gets the ratio data for all Vgs
# Vgs_selected is the Vgs closest to that measured to use when calculating the TLM parameters from the family of curves data
# Ron is in ohm*mm
	def get_parametersORTHO(self, fractVdsfit=None, Vgs_selected=None, force_calculation=False,validdevices=None):										# flag to determine presence of any TLM data
		if fractVdsfit!=None and fractVdsfit!='': fractVdsfit=float(fractVdsfit)						# convert to float if given as string
		if Vgs_selected!='' and Vgs_selected!=None: Vgs_selected=float(Vgs_selected)
		else:
			Vgs_selected=None
			return False
		if validdevices==None: validdevices=self.validdevices
		elif validdevices==None: validdevices=self.DCd.keys()
		elif validdevices==None: raise ValueError("ERROR! no devices")
		self.haveORTHdata=True
		if self.orthmate==None:
			self.haveORTHdata=False
			return self.haveORTHdata
		if self.devicefilteredORTH==True: 					# were the devices filtered and acknowledged by this method?
			force_calculation=True
			self.devicefilteredORTH= False
		if Vgs_selected!=None and not floatequal(Vgs_selected,self.__Vgs_selected_ORTH,1.E-3):	# since the gate voltage where the TLM parameters are calculated has changed, we need to recalculate
			force_calculation=True
			self.__Vgs_selected_ORTH=Vgs_selected
			self.__Vgs_selected=Vgs_selected
		if fractVdsfit!=None and not floatequal(self.__fractVdsfit_ORTH,fractVdsfit,1.E-3):
			force_calculation=True
			self.fractVdsfit_Ronfoc=fractVdsfit
			self.__fractVdsfit_ORTH=fractVdsfit
			for devk in self.DCd:
				self.DCd[devk].Ron_foc(fractVdsfit=self.__fractVdsfit_ORTH)				# update linear fit to Id(Vds) curves if necessary i.e. if the fractVdsfit not nearly equal to that of the devices or if no Ron has been calculated
		orthpattern=re.compile(r'_[a-zA-Z0-9-]*ORTH[a-zA-Z0-9-]*_')            # used to match expressions for finding ORTH device names
		if force_calculation==True:						#then do the ratio calculations
			self.haveORTHdata=False
			if len(self.DCd[self.focfirstdevindex].Ron_foc())>0 and len(self.DCd[self.focfirstdevindex].Ron_foc())>0:
				iVgs = min(range(len(self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'])),key=lambda i: abs(self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'][i]-self.__Vgs_selected_ORTH))		# get the index of the requested gate voltage: assume that Vgs values are the same for all devices in the wafer self.focfirstdevindex is the device index of the first "good" family of curves IV measurement e.g. no measurements in compliance etc..
				Vgs=self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'][iVgs]					# actual Vgs used
			else:	# use default values if have no family of curves
				iVgs=0
				Vgs=None
			# first get site names
			#ORTHsitenames=list(set([d.split('_ORTH_')[0] for d in validdevices if '_ORTH_' in d ]))				# get the site names of all ORTH (orthogonal) devices i.e. unique names excluding the part of the name specific to the ORTHO devices within the site
			ORTHsitenames=list(set([re.split(orthpattern,d)[0] for d in validdevices if 'ORTH' in d and invalidTLMorthdevice not in d]))				# get the site names of all ORTH (orthogonal) devices i.e. unique names excluding the part of the name specific to the ORTHO devices within the site

			#print("from wafer_analysis.py line 467 self.pathname, __get_parametersORTHO ",self.pathname)			# debug

			# form dict of all ORTH sites
			#ORTHdict={s: {d.split('_ORTH_')[1]: self.DCd[d] for d in validdevices if s in d and "_ORTH_" in d} for s in ORTHsitenames}	# same as previous line but accounts for different naming scheme
			ORTHdict={s: {re.split(orthpattern,d)[1]: self.DCd[d] for d in validdevices if s in d and "ORTH" in d and invalidTLMorthdevice not in d} for s in ORTHsitenames}	# same as previous line but accounts for different naming scheme

			ratioIdmax={}
			ratioIdmaxF={}
			ratioIdmaxR={}
			ratioRon={}
			#print("line 491 wafer_analysis.py ",'H64meas1_+--+__C8_R6_ORTH_1A' in validdevices )
			#print("line 491 wafer_analysis.py ", 'H64meas1_+--+__C8_R6_ORTH_1B' in validdevices)
			#print("line 491 wafer_analysis.py ", 'H64meas1_+--+__C8_R6_ORTH_1A' in ORTHdict)
			#print("line 491 wafer_analysis.py ", 'H64meas1_+--+__C8_R6_ORTH_1B' in ORTHdict)
			for ksite in ORTHdict:
				for kdev in self.orthmate:
					#if kdev in ORTHdict[ksite] and self.orthmate[kdev] in ORTHdict[ksite]:				# does both the ORTH site and its mate actually exist (were they actually measured and did they give valid data)?
					if kdev in ORTHdict[ksite] and self.orthmate[kdev] in ORTHdict[ksite]: #and ORTHdict[ksite][self.orthmate[kdev]].devicename in validdevices:
						#print("line 491 wafer_analysis.py ", ORTHdict[ksite][kdev].devicename)
						# if ORTHdict[ksite] and len(ORTHdict[ksite][self.orthmate[kdev]].Ron_foc())>0 and len(ORTHdict[ksite][kdev].Ron_foc())>0:        # debug
						# 	print("line 671 wafer_analysis.py ",kdev,ORTHdict[ksite][self.orthmate[kdev]].devicename,ORTHdict[ksite][kdev].devicename)
						# 	print("from line 672 in wafer_analysis.py ",kdev, ORTHdict[ksite][kdev].Ron_foc()['R'][iVgs] )
						if ORTHdict[ksite] and len(ORTHdict[ksite][self.orthmate[kdev]].Ron_foc())>0 and len(ORTHdict[ksite][kdev].Ron_foc())>0 and ORTHdict[ksite][kdev].Ron_foc()['R'][iVgs] > 0.:
							ratioRon[ORTHdict[ksite][kdev].devicename] = ORTHdict[ksite][self.orthmate[kdev]].Ron_foc()['R'][iVgs]/ORTHdict[ksite][kdev].Ron_foc()['R'][iVgs]
							ratioRon[ORTHdict[ksite][self.orthmate[kdev]].devicename]=ratioRon[ORTHdict[ksite][kdev].devicename]					# data for mate device are the same
						if len(ORTHdict[ksite][self.orthmate[kdev]].Idmax_T())>0 and len(ORTHdict[ksite][kdev].Idmax_T())>0 and ORTHdict[ksite][self.orthmate[kdev]].Idmax_T()['I'] > 0.:
							ratioIdmax[ORTHdict[ksite][kdev].devicename]=ORTHdict[ksite][kdev].Idmax_T()['I']/ORTHdict[ksite][self.orthmate[kdev]].Idmax_T()['I']
							ratioIdmax[ORTHdict[ksite][self.orthmate[kdev]].devicename]=ratioIdmax[ORTHdict[ksite][kdev].devicename]				# data for mate device are the same
						if len(ORTHdict[ksite][self.orthmate[kdev]].Idmax_TF())>0 and len(ORTHdict[ksite][kdev].Idmax_TF())>0 and ORTHdict[ksite][self.orthmate[kdev]].Idmax_TF()['I'] > 0.:
							ratioIdmaxF[ORTHdict[ksite][kdev].devicename] =ORTHdict[ksite][kdev].Idmax_TF()['I']/ORTHdict[ksite][self.orthmate[kdev]].Idmax_TF()['I']
							ratioIdmaxF[ORTHdict[ksite][self.orthmate[kdev]].devicename] = ratioIdmaxF[ORTHdict[ksite][kdev].devicename]  # data for mate device are the same
						if len(ORTHdict[ksite][self.orthmate[kdev]].Idmax_TR())>0 and len(ORTHdict[ksite][kdev].Idmax_TR())>0 and ORTHdict[ksite][self.orthmate[kdev]].Idmax_TR()['I'] > 0.:
							ratioIdmaxR[ORTHdict[ksite][kdev].devicename] =ORTHdict[ksite][kdev].Idmax_TR()['I']/ORTHdict[ksite][self.orthmate[kdev]].Idmax_TR()['I']
							ratioIdmaxR[ORTHdict[ksite][self.orthmate[kdev]].devicename] = ratioIdmaxR[ORTHdict[ksite][kdev].devicename]  # data for mate device are the same
			# now translate the ORTH subsite ORTH data to the individual devices (where valid)
			havedevice=False
			for devk in validdevices:							# loop over all devices which made it through the device filter on wafer to add ORTH data to those which are ORTH devices
				if devk in ratioIdmax:
					self.DCd[devk].ratioIdmax=ratioIdmax[devk]			# deal with ONLY devices which are part of an ORTH structure and which have ratioImax data
					self.DCd[devk].ORTHIdmax_totalnopointsincompliance = self.DCd[devk].gatestatus_no_T()+self.DCd[devk].drainstatus_no_T()
				else:
					self.DCd[devk].ratioIdmax =None
					self.DCd[devk].ORTHIdmax_totalnopointsincompliance =None
				if devk in ratioIdmaxF:
					self.DCd[devk].ratioIdmaxF = ratioIdmaxF[devk]  # deal with ONLY devices which are part of an ORTH structure and which have ratioImax data
					self.DCd[devk].ORTHIdmaxF_totalnopointsincompliance = self.DCd[devk].gatestatus_no_TF() + self.DCd[devk].drainstatus_no_TF()
				else:
					self.DCd[devk].ratioIdmaxF =None
					self.DCd[devk].ORTHIdmaxF_totalnopointsincompliance =None
				if devk in ratioIdmaxR:
					self.DCd[devk].ratioIdmaxR = ratioIdmaxR[devk]  # deal with ONLY devices which are part of an ORTH structure and which have ratioImax data
					self.DCd[devk].ORTHIdmaxR_totalnopointsincompliance = self.DCd[devk].gatestatus_no_TR() + self.DCd[devk].drainstatus_no_TR()
				else:
					self.DCd[devk].ratioIdmaxR = None
					self.DCd[devk].ORTHIdmaxR_totalnopointsincompliance =None
				if devk in ratioRon:
					self.DCd[devk].ratioRon=ratioRon[devk]			# deal with ONLY devices which are part of an ORTH structure and which have ratioImax data
					self.DCd[devk].ORTHRon_totalnopointsincompliance = self.DCd[devk].gatestatus_no_foc()+self.DCd[devk].drainstatus_no_foc()
				else:
					self.DCd[devk].ratioRon = None
					self.DCd[devk].ORTHRon_totalnopointsincompliance =None
					#print("from line 489 in wafer_analysis.py device=",devk, self.DCd[devk].ratioRon, self.DCd[devk].Ronfrom_foc) # debug
				if devk in ratioIdmax or devk in ratioRon:
					self.DCd[devk].ORTH_Vgs=Vgs
					self.haveORTHdata=True
				else:
					self.DCd[devk].ORTH_Vgs = None
					self.haveORTHdata = None
		return self.haveORTHdata							# array of device keys of devices which are ORTH devices (a subset of all the valid devices)
########################################################################################################################
# get wafer name
	def get_wafername(self):
		return self.wafername

##########################################################################################################################
# Bin Ron data and return histogram
# Inputs:
# minRon, maxRon are respectively the minimum and maximum Ron values to be considered (optional) defaults = 0 and near infinity respectively
# minRonstddev is the minimum Ron value to be considered as a multiple of the standard deviation for each population (optional default=0.)
#		The minimum Ron considered will be the greater of that determined by minRon and minRonstddev
# the mean Ron of the population is the maximum Ron value to be considered as a multiple of the standard deviation for each population (optional default=10.)
#		The maximum Ron considered will be maxRon
# binsizeRondev is an alternative method to specify the bin size, i.e. as a fraction of the standard deviation of Ron at each gate voltage measured
# binsizeRondev is the bin size as a fraction of the standard deviation of the population's value
# includes is a string containing all strings which MUST be present in the device name for that device to be considered in the distribution
# includes allows one to specify devices by gate length etc... to be in the histogram. The specifications in includes are separated by commas or spaces.
# fractVdsfit_Ronfoc optionally allows one to specify the range of Vds - in terms of a fraction of the maximum Vds in the family of curves, that the linear fit to determine Ron is performed over - starting from Vds=0V
# recalc is used to force a recalculation of data
# Vgs_selected is the Vgs at which the data are measured
# RG indicates the type of data on which the histogram is found
# TLMnegRshreject Reject TLM site when its sheet resistance is <= 0
#
# Outputs
# Data calculated are __Ronhist[ib][idev], __X_Ron_hist[ib][idev], __Y_Ron_hist[ib][idev],  __Vgs_Ron_hist[iVg]
# __binmin_Ron_hist[ib] and __binmax_Ron_hist[ib] are the respective minimum and maximum bin values at bin index ib
# where ib is the bin index, and idev is the device index
# __Ronhist[ib] are the binned Ron data and __Ronhist_devicename[ib][idev] an array of the corresponding device names list where
# idev is the device index of the list of names in each bin
# method Ron_histogram() is used to obtain the binned data test
	def Ron_Gon_histogram(self,minRon=None,maxRon=None,binsizeRondev=None,binsizepolicy=None,includes=None,fractVdsfit_Ronfoc=None,recalc='no',Vgs_selected=None,RG=None,TLMnegRshreject=False,minTLMlength=None,maxTLMlength=None,linearfitquality_request=None,transfercurve_smoothing_factor=None,logplot=None):
		if parse_rpn(expression=includes, targetfilename="") == "illegal":  # check for syntax errors in Boolean statement
			print("from line 739 in wafer_analysis.py clear", includes)
			self.parent.set_includes.clear()  # clear text of Boolean selector
		if Vgs_selected!='' and Vgs_selected!=None: Vgs_selected=float(Vgs_selected)
		else: Vgs_selected=None
		if recalc!='yes':	# but should we actually recalculate? If not, then we
			# should the histogram be calculated?
			if minRon!=None and self.__minRon_hist!=minRon:
				self.__minRon_hist=minRon
				recalc='yes'

			if minTLMlength!=None and self.minTLMlength!=minTLMlength:
				#self.minTLMlength=minTLMlength
				recalc='yes'

			if maxTLMlength!=None and self.maxTLMlength!=maxTLMlength:
				#self.maxTLMlength=maxTLMlength
				recalc='yes'

			if maxRon!=None and self.__maxRon_hist!=maxRon:
				self.__maxRon_hist=maxRon
				recalc='yes'

			if logplot!=None and self._logplot!=logplot:
				self._logplot=logplot
				recalc='yes'

			if binsizeRondev!=None and self.__binsizeRondev_hist != binsizeRondev:
				self.__binsizeRondev_hist = binsizeRondev
				recalc='yes'

			if binsizepolicy!=None and self.__binsizepolicy != binsizepolicy:
				self.__binsizepolicy = binsizepolicy
				recalc='yes'

			if includes!=None and self.__includesRon_hist!=includes:
				self.__includesRon_hist=includes
				recalc='yes'

			if fractVdsfit_Ronfoc!=None and self.fractVdsfit_Ronfoc!=fractVdsfit_Ronfoc:
				#self.__fractVdsfit_Ronfoc=self.DCd[0].get_fractVdsfit_Ronfoc()
				self.fractVdsfit_Ronfoc=fractVdsfit_Ronfoc
				recalc='yes'

			if Vgs_selected!=None and self.__Vgs_selected!=Vgs_selected:
				self.__Vgs_selected=Vgs_selected
				recalc='yes'

			if RG!=None and self.__RG!=RG:
				self.__RG=RG
				recalc='yes'

			if transfercurve_smoothing_factor!=None and self.__transfercurve_smoothing_factor!=transfercurve_smoothing_factor:
				self.__transfercurve_smoothing_factor=transfercurve_smoothing_factor
				recalc='yes'


		if recalc=='yes':	# recalculate Ron histogram
			if minRon!=None:
				self.__minRon_hist=minRon

			if maxRon!=None:
				self.__maxRon_hist=maxRon

			if binsizeRondev!=None:
				self.__binsizeRondev_hist = binsizeRondev

			if binsizepolicy!=None:
				self.__binsizepolicy = binsizepolicy

			if includes!=None:
				self.__includesRon_hist=includes

			if fractVdsfit_Ronfoc!=None:
				self.fractVdsfit_Ronfoc=fractVdsfit_Ronfoc
			else:
				self.fractVdsfit_Ronfoc=self.DCd[self.focfirstdevindex].get_fractVdsfit_Ronfoc()

			if Vgs_selected!=None:
				self.__Vgs_selected=Vgs_selected

			if RG!=None:
				self.__RG=RG

			if recalc=='yes':
				# set up output data arrays
				self.__devicename_Ron_hist =[]
				self.__X_Ron_hist = []
				self.__Y_Ron_hist = []
				self.__Ron_hist = []
				self.__binmin_Ron_hist = []
				self.__binmax_Ron_hist=[]


				if self.__get_parametersDC()=="No Files Found":	# get DC IV measured and calculated parameters for all devices measured on the wafer
					return "No Files Found"
				if self.focfirstdevindex!=None and hasattr(self.DCd[self.focfirstdevindex],'Ronfrom_foc'): have_foc=True				# we have some family of curves data
				else: have_foc=False
				#print(self.DCd[0].Ron_foc()['Vgs']) # debug
				if have_foc:
					try: iVgs = min(range(len(self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'])), key=lambda i: abs(self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'][i] - self.__Vgs_selected))		# assumes that all devices in this wafer were measured at the same gate voltages
					except: return "No data"
				else: have_foc=False
				#iVgs = min(range(len(self.DCd[0].Ron_foc()['Vgs'])),key=lambda i: abs(self.DCd[0].Ron_foc()['Vgs'][i]-self.__Vgs_selected))		# assumes that all devices in this wafer were measured at the same gate voltages

				#for iVgs in range(0,len(self.DCd[0].Ron_foc()['Vgs'])):		# assume all devices on the wafer were measured using the same value of Vgs
				# set up intermediate arrays
				####
				_dev=col.deque()
				_x=col.deque()
				_y=col.deque()
				_Ron=col.deque()
				width=col.deque()

				##### Ron data #############################################################################3
				if self.__RG=='Ron':
					if have_foc:
						for devk in self.validdevices:
							r=self.DCd[devk].Ron_foc(fractVdsfit=self.fractVdsfit_Ronfoc)
							if len(r)>0:
								#print("from line 616 in wafer_analysis.py iVgs,r,device",iVgs,r,devk)
								if len(r['R'])==1:	_Ron.append(r['R'][0])						# then this is likely a probe test
								else: _Ron.append(r['R'][iVgs])
								_dev.append(devk)				# device name
								_x.append(self.DCd[devk].x())
								_y.append(self.DCd[devk].y())
								width.append(self.DCd[devk].devwidth)
						if len(_Ron)<1: return "No data"
					else: return "No data"
				######################################################################################
				# Gon data
				elif self.__RG=='Gon':
					if have_foc:
						baddata=False
						# first must look at all devices because the Ron changes might affect whether a device passes the filters
						for devk in self.validdevices:
							if floatequal(self.DCd[devk].get_fractVdsfit_Ronfoc(), self.fractVdsfit_Ronfoc, 1.E-3):		# did the fractVdsfit change?
								self.DCd[devk].Ron_foc(fractVdsfit=self.fractVdsfit_Ronfoc)
							if floatequal(self.DCd[devk].get_fractVdsfit_Ronfoc(), self.fractVdsfit_Ronfoc, 1.E-3):		# did the fractVdsfit change?
								r=self.DCd[devk].Ron_foc(fractVdsfit=self.fractVdsfit_Ronfoc)
							else: r=self.DCd[devk].Ron_foc()
							if len(r)>0:
								if len(r['R'])==1:	# then this is likely a probe test
									try: g=1./r['R'][0]
									except: baddata=True				# resistance approaches zero
								else:
									try: g=1./r['R'][iVgs]
									except: baddata=True				# resistance approaches zero
								if baddata==False:
									_Ron.append(g)
									_dev.append(devk)				# device name
									_x.append(self.DCd[devk].x())
									_y.append(self.DCd[devk].y())
									width.append(self.DCd[devk].devwidth)
						if len(_Ron)<1: return "No data"
					else: return "No data"
				######################################################################################

				###################### Ron_max data##################################################
				elif self.__RG=='Rmax':
					if not hasattr(self,'Ronmax'): return  "No data"
					if have_foc:
						for devk in self.validdevices:
							r=self.DCd[devk].Ron_max_foc()
							if len(r)>0:
								if len(r['R'])==1:	_Ron.append(r['R'][0])						# then this is likely a probe test
								else: _Ron.append(r['R'][iVgs])
								_dev.append(devk)				# device name
								_x.append(self.DCd[devk].x())
								_y.append(self.DCd[devk].y())
								width.append(self.DCd[devk].devwidth)
						if len(_Ron)<1: return "No data"
					else: return "No data"
				######################################################################################
				###################### Gon_max data (which is the reciprocal of Ron_max)##################################################
				elif self.__RG=='Gmax':
					if have_foc:
						baddata=False
						for devk in self.validdevices:
							r=self.DCd[devk].Ron_max_foc()
							if len(r)>0:
								try: g=1./r['R'][iVgs]
								except: baddata=True				# resistance approaches zero
								if baddata==False:
									_Ron.append(g)
									_dev.append(devk)				# device name
									_x.append(self.DCd[devk].x())
									_y.append(self.DCd[devk].y())
									width.append(self.DCd[devk].devwidth)
						if len(_Ron)<1: return "No data"
					else: return "No data"
				######################################################################################
				############### on off ratio single-swept transfer curve ##########################################################
				elif self.__RG=="On-Off ratio single":
					for devk in self.validdevices:
							r=self.DCd[devk].Idonoffratio_T()
							if len(r)>0:
								_Ron.append(r['Ir'])
								_dev.append(devk)				# device name
								_x.append(self.DCd[devk].x())
								_y.append(self.DCd[devk].y())
								width.append(self.DCd[devk].devwidth)
					if len(_Ron)<1: return "No data"
				#######################################################################################
				############### on off ratio first sweep (forward) of dual-swept transfer curve##########################################################
				elif self.__RG=="On-Off ratio dual 1st":
					for devk in self.validdevices:
							r=self.DCd[devk].Idonoffratio_TF()
							if len(r)>0:
								_Ron.append(r['Ir'])
								_dev.append(devk)				# device name
								_x.append(self.DCd[devk].x())
								_y.append(self.DCd[devk].y())
								width.append(self.DCd[devk].devwidth)
					if len(_Ron)<1: return "No data"
				#######################################################################################
				############### on off ratio second sweep (reverse) of dual-swept transfer curve##########################################################
				elif self.__RG=="On-Off ratio dual 2nd":
					for devk in self.validdevices:
							r=self.DCd[devk].Idonoffratio_TR()
							if len(r)>0:
								_Ron.append(r['Ir'])
								_dev.append(devk)				# device name
								_x.append(self.DCd[devk].x())
								_y.append(self.DCd[devk].y())
								width.append(self.DCd[devk].devwidth)
					if len(_Ron)<1: return "No data"
				#######################################################################################
				############### Idleak is the minimum drain current from the polynomial or spline fit of Id(Vgs) ################################################################
				elif 'Idleak_T' in self.__RG:
					for devk in self.validdevices:
							r=self.DCd[devk].Idleak_T()
							if len(r)>0:
								_Ron.append(r['I'])
								_dev.append(devk)				# device name
								_x.append(self.DCd[devk].x())
								_y.append(self.DCd[devk].y())
								width.append(self.DCd[devk].devwidth)
					if len(_Ron)<1: return "No data"
				#######################################################################################
				########## Idmax (maximum |drain current| from single-swept transfer curve
				elif self.__RG=="|Idmax| single":
					for devk in self.validdevices:
							r=self.DCd[devk].Idmax_T()
							if len(r)>0:
								_Ron.append(r['I'])
								_dev.append(devk)				# device name
								_x.append(self.DCd[devk].x())
								_y.append(self.DCd[devk].y())
								width.append(self.DCd[devk].devwidth)
					if len(_Ron)<1: return "No data"
				#######################################################################################
				########## Idmax (maximum |drain current| first (forward) curve from dual-swept transfer curve
				elif self.__RG=='|Idmax| dual 1st':
					for devk in self.validdevices:
							r=self.DCd[devk].Idmax_TF()
							if len(r)>0:
								_Ron.append(r['I'])
								_dev.append(devk)				# device name
								_x.append(self.DCd[devk].x())
								_y.append(self.DCd[devk].y())
								width.append(self.DCd[devk].devwidth)
					if len(_Ron)<1: return "No data"
				#######################################################################################
				########## Idmax (maximum |drain current| first (forward) curve from dual-swept transfer curve
				elif self.__RG=='|Idmax| dual 2nd':
					for devk in self.validdevices:
							r=self.DCd[devk].Idmax_TR()
							if len(r)>0:
								_Ron.append(r['I'])
								_dev.append(devk)				# device name
								_x.append(self.DCd[devk].x())
								_y.append(self.DCd[devk].y())
								width.append(self.DCd[devk].devwidth)
					if len(_Ron)<1: return "No data"
				#######################################################################################
				##########  Idmin is the minimum measured drain current from the single-swept transfer curve Id(Vgs)
				elif self.__RG=='Idmin_T':
					for devk in self.validdevices:
							r=self.DCd[devk].Idmin_T()
							if len(r)>0:
								_Ron.append(r['I'])
								_dev.append(devk)				# device name
								_x.append(self.DCd[devk].x())
								_y.append(self.DCd[devk].y())
								width.append(self.DCd[devk].devwidth)
					if len(_Ron)<1: return "No data"
				############ TLM contact resistance data##################################################################
				elif self.__RG=='Rc TLM':
					if not have_foc: return "No data"
					if not self.get_parametersTLM(fractVdsfit=fractVdsfit_Ronfoc, Vgs_selected=Vgs_selected, minTLMlength=minTLMlength, maxTLMlength=maxTLMlength,linearfitquality_request=linearfitquality_request): return "No data"
					_Rsh=col.deque()
					for devk in self.validdevices:
						if self.DCd[devk].Rc_TLM!=None:
							_Rsh.append(self.DCd[devk].Rsh_TLM)
							_Ron.append(self.DCd[devk].Rc_TLM)
							_dev.append(devk)				# device name
							_x.append(self.DCd[devk].x())
							_y.append(self.DCd[devk].y())
							width.append(self.DCd[devk].devwidth)
					if len(_Ron)<1: return "No data"
				############## TLM sheet resistance data ################################################################################
				elif self.__RG=='Rsh TLM':
					if not have_foc: return "No data"
					if not self.get_parametersTLM(fractVdsfit=fractVdsfit_Ronfoc, Vgs_selected=Vgs_selected, minTLMlength=minTLMlength, maxTLMlength=maxTLMlength,linearfitquality_request=linearfitquality_request): return "No data"
					_Rsh=col.deque()
					for devk in self.validdevices:
						if self.DCd[devk].Rc_TLM!=None:
							_Rsh.append(self.DCd[devk].Rsh_TLM)
							_Ron.append(self.DCd[devk].Rsh_TLM)
							_dev.append(devk)				# device name
							_x.append(self.DCd[devk].x())
							_y.append(self.DCd[devk].y())
							width.append(self.DCd[devk].devwidth)
					if len(_Ron)<1: return "No data"
				###################################################################
				# orthogonal device maximum Id ratios
				elif self.__RG=="ORTHRatio |Idmax| single":
					#if not have_foc: return "No data"
					if not self.get_parametersORTHO(fractVdsfit=fractVdsfit_Ronfoc, Vgs_selected=Vgs_selected): return "No data"
					for devk in self.validdevices:
						if self.DCd[devk].ratioIdmax!=None:
								_Ron.append(self.DCd[devk].ratioIdmax)
								_dev.append(devk)				# device name
								_x.append(self.DCd[devk].x())
								_y.append(self.DCd[devk].y())
								width.append(self.DCd[devk].devwidth)
					if len(_Ron)<1: return "No data"
				######################################################################
				# orthogonal device maximum Id ratios first sweep on dual swept transfer curve
				elif self.__RG == "ORTHRatio |Idmax| dual 1st":
					#if not have_foc: return "No data"
					if not self.get_parametersORTHO(fractVdsfit=fractVdsfit_Ronfoc,Vgs_selected=Vgs_selected): return "No data"
					for devk in self.validdevices:
						if self.DCd[devk].ratioIdmaxF!=None:
							_Ron.append(self.DCd[devk].ratioIdmaxF)
							_dev.append(devk)  # device name
							_x.append(self.DCd[devk].x())
							_y.append(self.DCd[devk].y())
							width.append(self.DCd[devk].devwidth)
					if len(_Ron) < 1: return "No data"
				######################################################################
				# orthogonal device maximum Id ratios first sweep on dual swept transfer curve
				elif self.__RG == "ORTHRatio |Idmax| dual 2nd":
					#if not have_foc: return "No data"
					if not self.get_parametersORTHO(fractVdsfit=fractVdsfit_Ronfoc,Vgs_selected=Vgs_selected): return "No data"
					for devk in self.validdevices:
						if self.DCd[devk].ratioIdmaxR!=None:
							_Ron.append(self.DCd[devk].ratioIdmaxR)
							_dev.append(devk)  # device name
							_x.append(self.DCd[devk].x())
							_y.append(self.DCd[devk].y())
							width.append(self.DCd[devk].devwidth)
					if len(_Ron) < 1: return "No data"
				######################################################################
				##### orthogonal device Ron ratios
				elif self.__RG=="ORTHRatio Ron":
					if not have_foc: return "No data"
					if not self.get_parametersORTHO(fractVdsfit=fractVdsfit_Ronfoc, Vgs_selected=Vgs_selected): return "No data"
					for devk in self.validdevices:
						if self.DCd[devk].ratioRon!=None:
								_Ron.append(self.DCd[devk].ratioRon)
								_dev.append(devk)				# device name
								_x.append(self.DCd[devk].x())
								_y.append(self.DCd[devk].y())
								width.append(self.DCd[devk].devwidth)
					if len(_Ron)<1: return "No data"
				########################################################################
				##### hysteresis data from first and second sweeps of transfer curves
				elif self.__RG == 'hysteresis voltage 12':
					for devk in self.validdevices:
						r= self.DCd[devk].Vhyst12()
						if r!=None:
							_Ron.append(r)
							_dev.append(devk)  # device name
							_x.append(self.DCd[devk].x())
							_y.append(self.DCd[devk].y())
							width.append(self.DCd[devk].devwidth)
					if len(_Ron) < 1: return "No data"
				########################################################################
				##### |Id(Vds)| for Vgs set to maximize |Id|
				elif self.__RG == '|Idmax(Vds)|FOC':
					for devk in self.validdevices:
						r=self.DCd[devk].Idmax_foc(Vds=self.parent.Vds_FOC.text())
						if r!=None:
							r= self.DCd[devk].Idmaxfoc_Vds
							_Ron.append(r)
							_dev.append(devk)  # device name
							_x.append(self.DCd[devk].x())
							_y.append(self.DCd[devk].y())
							width.append(self.DCd[devk].devwidth)
					if len(_Ron) < 1: return "No data"
				########################################################################
				##### hysteresis current from bi-directional Vds sweep during family of curves measurement
				elif self.__RG == 'FOC hysteresis current':
					for devk in self.validdevices:
						r=self.DCd[devk].get_Idhystfocmax()
						if r!=None:
							#r= self.DCd[devk].Idmaxfoc_Vds
							_Ron.append(r)
							_dev.append(devk)  # device name
							_x.append(self.DCd[devk].x())
							_y.append(self.DCd[devk].y())
							width.append(self.DCd[devk].devwidth)
					if len(_Ron) < 1: return "No data"
				########################################################################
				else:
					print("ERROR from line 1130 in wafer_analysis.py self.__RG = ",self.__RG)
					raise ValueError("ERROR: No valid request for data type (RG)")

				# filter devices by name and select only those specified by type as specified by strings in includes ##################
				dev=[]
				x=[]
				y=[]
				Ron=[]

				# go through Ron measured devices and select them according to device name (type of device)
				for idev in range(0,len(_Ron)):
					valid=True
					if not parse_rpn(expression=includes,targetfilename=_dev[idev],parentwidget=self.parent.set_includes): valid=False			# does this device name meet the Boolean name filter?
					# if include_in_name != 'all':
					# 	for inc in include_in_name:
					# 		if inc not in _dev[idev]: v='not valid'			# device name must contain all designators in includes to be counted in the histogram
					if _Ron[idev]<self.__minRon_hist or _Ron[idev]>self.__maxRon_hist: valid=False # filter by value
					if TLMnegRshreject==True and self.__RG=='Rc TLM' and _Rsh<=0.: valid=False		# reject TLMs with negative sheet resistance
					if TLMnegRshreject==True and self.__RG=='Rsh TLM' and _Ron<=0.: valid=False		# reject TLMs with negative sheet resistance
					if valid==True and not np.isnan(_Ron[idev]):		# idev is the device index, if the device is of the selected type, include it in the population to be considered Also, consider this data point only if it's a number
						dev.append(_dev[idev])		# device name in selected population
						x.append(_x[idev])			# X-location on wafer in selected population
						y.append(_y[idev])			# Y-location on wafer in selected population
						if logplot: Ron.append(np.log10(np.abs(_Ron[idev]))) # log10 statistical data
						else: Ron.append(_Ron[idev])		# statistical data

				if len(Ron)<2:		# not enough values to perform statistics so return with None
					print("WARNING No data") #debug
					return "No data"
				# now find the bin size of the Ron population at this gate voltage#############################################
				# then the bin sizes are related to the standard deviation at each gate voltage
				if logplot:
					if self.__minRon_hist<1E-30: self.__minRon_hist=1E-30
					if self.__maxRon_hist<1E-30: self.__maxRon_hist=1E-30
					bins_maxRon_hist=np.log10(self.__maxRon_hist)
					bins_minRon_hist=np.log10(self.__minRon_hist)
				else:
					bins_maxRon_hist=self.__maxRon_hist
					bins_minRon_hist=self.__minRon_hist

				stdev_bin=np.std(Ron)		# standard deviation, of the selected filtered population (linear or log10) for the purposes of calculating bin size
				if self.__binsizepolicy=='Directly Set':		# the bin size is user set to a given number of standard deviations
					binsizeRon = self.__binsizeRondev_hist*stdev_bin # relate binsize to the standard deviation of Ron at the specified gate voltage
				elif self.__binsizepolicy=='Scott':
					binsizeRon = 3.49*stdev_bin*np.power(float(len(Ron)),-1./3.)
				elif self.__binsizepolicy=='Sturges':
					binsizeRon = (min(bins_maxRon_hist,max(Ron))-max(bins_minRon_hist,min(Ron)))/(1+np.log2(len(Ron)))
				else: raise ValueError('ERROR no legal binsize policy specified')
				if math.isinf(max(Ron)): print("from line 1193 wafer_analysis.py max(Ron) is inf")
				#print("from 1181 in wafer_analysis is nan",np.isnan(Ron).any(), np.isnan(max(Ron)), np.isnan(min(Ron)), np.isnan(bins_maxRon_hist), np.isnan(bins_minRon_hist), np.isnan(binsizeRon))
				#print("from 1181 in wafer_analysis self.__RG=",self.__RG)
				# TODO seeing bug here Ron contains nan
				nbins = int((min(bins_maxRon_hist,max(Ron))-max(bins_minRon_hist,min(Ron)))/binsizeRon)+2	# number of bins
				#print("from 1181 in wafer_analysis is nan",np.isnan(Ron).any(), np.isnan(max(Ron)), np.isnan(min(Ron)), np.isnan(bins_maxRon_hist), np.isnan(bins_minRon_hist), np.isnan(binsizeRon))

				if nbins<2:
					print("from line 1211, number of bins<2 return None")
					return "No data"
				for ib in range(0,nbins):		# set up bins' minimum and maximum Ron values for each bin at the given gate voltage
					self.__binmin_Ron_hist.append(float(ib)*binsizeRon+max(bins_minRon_hist,min(Ron)))			# beginning values of bins
					self.__binmax_Ron_hist.append(float(ib+1)*binsizeRon+max(bins_minRon_hist,min(Ron)))		# ending values of bins
					#print("from wafer_analysis.py line 839 binmin binmax", self.__binmin_Ron_hist[-1],self.__binmax_Ron_hist[-1]) # debug

				#print("from line 849 wafer_analysis.py Gate Voltage, Number of devices ",self.DCd[0].Ron_foc()['Vgs'][iVgs],len(Ron)) #debug
				if logplot:
					self.__Ron_average=np.power(10.,np.average(Ron))			# antilog(average of log10(data))
					self.__Ron_stddev=self.__Ron_average*np.power(10,np.std(Ron))				# antilog(standard deviation of log10(data)))
				else:
					self.__Ron_average=np.average(Ron)			# average of Ron
					self.__Ron_stddev=np.std(Ron)				# standard deviation of Ron (or Gon)
				self.__Ron_numberofdevices=len(Ron)			# number of devices which passed screening

				for ib in range(0,nbins):		# bin the values for this Vgs
					# first append the device array for each bin as each bin has an array of devices contained therein
					self.__devicename_Ron_hist.append([])
					self.__X_Ron_hist.append([])
					self.__Y_Ron_hist.append([])
					self.__Ron_hist.append([])
					#print("len(Ron)",len(Ron)
					for idev in range(0,len(Ron)):		# go through all devices to run by bins
						if Ron[idev]>= self.__binmin_Ron_hist[ib] and Ron[idev]<self.__binmax_Ron_hist[ib]:		# fill this bin - index ib - with devices having Ron values that lie within it
							self.__devicename_Ron_hist[ib].append(dev[idev])
							self.__X_Ron_hist[ib].append(x[idev])
							self.__Y_Ron_hist[ib].append(y[idev])
							if logplot: self.__Ron_hist[ib].append(np.power(10.,Ron[idev]))				# statistics performed on log data so convert back to linear data
							else: self.__Ron_hist[ib].append(Ron[idev])
				# if we performed statistics with log data then must convert lower and upper bin bounds back to linear
				if logplot:
					self.__binmin_Ron_hist=list(np.power(10.,self.__binmin_Ron_hist))
					self.__binmax_Ron_hist=list(np.power(10.,self.__binmax_Ron_hist))
					self.__Ron_hist=list(self.__Ron_hist)
				#print("from wafer_analysis.py line 868 binmin",self.__binmin_Ron_hist)T
				#print("from wafer_analysis.py line 868 binmax",self.__binmax_Ron_hist)
			if len(self.__devicename_Ron_hist)>0:
				if have_foc:
					try: iVgs = min(range(len(self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'])), key=lambda i: abs(self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'][i] - self.__Vgs_selected))		# assumes that all devices in this wafer were measured at the same gate voltages
					except: return "No data"
					if not 'iVgs' in locals(): iVgs = min(range(len(self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'])), key=lambda i: abs(self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'][i] - self.__Vgs_selected))		# assumes that all devices in this wafer were measured at the same gate voltages
					Vgs_actual=self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'][iVgs]
				else:	Vgs_actual=None		# No Vgs specified since there are no measurements which use this parameter e.g. no family of curves data
				return{'N':self.__Ron_numberofdevices,'stddev':self.__Ron_stddev,'average':self.__Ron_average,'R':self.__Ron_hist,'D':self.__devicename_Ron_hist,'X':self.__X_Ron_hist,'Y':self.__Y_Ron_hist,'Vgs':Vgs_actual, 'binmin':self.__binmin_Ron_hist, 'binmax':self.__binmax_Ron_hist}

			else:
				print("from wafer_analysis.py line 874: no device names, len(Ron), nbins", len(Ron),nbins,) #debug
				return None
		else:
			try: self.__Ron_hist	# did we get results before?
			except:
				print("from wafer_analysis.py line 879: no self.__Ron_hist") #debug
				return None
		if hasattr(self.DCd[self.focfirstdevindex],'Ronfrom_foc'):
			if not 'iVgs' in locals(): iVgs = min(range(len(self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'])), key=lambda i: abs(self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'][i] - self.__Vgs_selected))		# assumes that all devices in this wafer were measured at the same gate voltages
			Vgs_actual=self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'][iVgs]
		else: Vgs_actual=None	# No Vgs specified since there are no measurements which use this parameter e.g. no family of curves data
		return {'N':self.__Ron_numberofdevices,'stddev':self.__Ron_stddev,'average':self.__Ron_average,'R':self.__Ron_hist,'D':self.__devicename_Ron_hist,'X':self.__X_Ron_hist,'Y':self.__Y_Ron_hist,'Vgs':Vgs_actual, 'binmin':self.__binmin_Ron_hist, 'binmax':self.__binmax_Ron_hist} # return previous results we already had

###############################################################################################################################################################################
# function to filter out "bad" devices based on their calculated parameters
# returns a list of keys self.validdevices[] which are the device keys (also the device names) which have "survived" the filter process
# Inputs are all the criteria i.e. minima and maxima of the parameters to be filtered as well as the device name filter which is implemented as parse_rpn()
# This filter is called every time the filter parameters are changed in the device filter
# Test criteria that are None are not applied test
# selected_devices allows one to filter according to a list of devices if and only if it's not empty i.e. != None. If selected_devices!=None then in order to be included in the analysis, a device must both be in the
# selected_devices list and also pass all the other criteria imposed by devfilter()

	def devfilter(self,selected_devices=None,booleanfilter=None,fractVdsfit=None,Vgs_selected=None,minTLMlength=None,maxTLMlength=None):
		if fractVdsfit!=None and fractVdsfit!='':
			fractVdsfit=float(fractVdsfit)
			self.fractVdsfit_Ronfoc=fractVdsfit
		else: fractVdsfit=self.fractVdsfit_Ronfoc
		if Vgs_selected!='' and Vgs_selected!=None:
			Vgs_selected=float(Vgs_selected)
			self.Vgs_selected=Vgs_selected
		else: Vgs_selected=self.__Vgs_selected
		if is_number(minTLMlength) and is_number(maxTLMlength):
			minTLMlength=float(minTLMlength)
			maxTLMlength=float(maxTLMlength)

		self.devicenamefilter = booleanfilter
		validdevices_previous=self.validdevices			# to compare to see if anything has, in fact, been updated
		self.validdevices=col.deque()
		if not Vgs_selected<-999 and Vgs_selected!=None:
			haveTLMdata=self.get_parametersTLM(fractVdsfit=fractVdsfit, Vgs_selected=Vgs_selected, minTLMlength=minTLMlength, maxTLMlength=maxTLMlength, linearfitquality_request=self.linearfitquality_request)		# might need to re-calculate TLM data if input parameters have changed
		else: haveTLMdata=False

		if parse_rpn(expression=self.devicenamefilter, targetfilename="")=='illegal':		# check for syntax errors in Boolean statement
			print("from line 1302 in wafer_analysis.py clear")
			self.parent.set_includes.clear()										# clear text of Boolean selector
			self.devicenamefilter=""

		if 'linux' in _platform:                                # use multiprocessing ONLY for linux
			if selected_devices!=None and len(selected_devices)>1:
				devlist=split_device_list(selected_devices)								# use selected devices to start filter
			else: devlist=split_device_list(self.DCd.keys())		# split up device list according to number of cores on this machine

			qw = [mp.Queue() for i in range(0, len(devlist))]  # get queues for worker outputs
			workers = [mp.Process(target=filter_multiprocess, args=(self.DCd, qw[i], devlist[i], self.devicenamefilter, self.filtergatecompliance, self.filterdraincompliance, haveTLMdata, fractVdsfit,
																	self.filter_gmmax_min, self.filter_gmmax_max, self.filter_Idmax_min, self.filter_Idmax_max, self.filter_onoff_min, self.filter_onoff_max,
																	self.filter_TLM_Rc_min, self.filter_TLM_Rc_max, self.filter_TLM_Rsh_min, self.filter_TLM_Rsh_max, self.filter_Ronmin_min, self.filter_Ronmin_max,
																	self.filter_Igmax_min, self.filter_Igmax_max, self.filter_IdmaxFOC_min, self.filter_IdmaxFOC_max))
					                                                for i in range(0, len(devlist))]  # get list of workers
			#starttime=time.time()
			for w in workers:
				w.start()

			#print("elapsed time = ",starttime-time.time())
			#for iw in range(0,len(devlist)):
			for que_w in qw:
				#ret=qw[iw].get()               # use this for Queue()
				ret=que_w.get()
				#ret=que_w.recv()               # use this for Pipe()
				#print(len(ret))
				self.validdevices.extend(ret)
			for w in workers:
				w.join()
			del workers
			del qw
		elif 'win' in _platform:                                       # this is Windows so DON'T multiprocess - too slow due to overhead
			if selected_devices!=None and len(selected_devices)>1: devlist_no_multiprocessing=selected_devices								# use selected devices to start filter
			else: devlist_no_multiprocessing=self.DCd.keys()
			# filter devices
			self.validdevices=filter_multiprocess(self.DCd, None, devlist_no_multiprocessing, self.devicenamefilter, self.filtergatecompliance, self.filterdraincompliance, haveTLMdata, fractVdsfit,
												self.filter_gmmax_min, self.filter_gmmax_max, self.filter_Idmax_min, self.filter_Idmax_max, self.filter_onoff_min, self.filter_onoff_max,
												self.filter_TLM_Rc_min, self.filter_TLM_Rc_max, self.filter_TLM_Rsh_min, self.filter_TLM_Rsh_max, self.filter_Ronmin_min, self.filter_Ronmin_max,
												self.filter_Igmax_min, self.filter_Igmax_max, self.filter_IdmaxFOC_min, self.filter_IdmaxFOC_max)
		else: raise ValueError("ERROR! unknown operating system - neither Windows nor Linux")


		if self.validdevices!=None and len(self.validdevices)>0 and validdevices_previous==None:
			self.devicefilteredORTH=True
			self.devicefilteredTLM = True
			return True
		if set(validdevices_previous)!=set(self.validdevices):
			self.devicefilteredORTH=True
			self.devicefilteredTLM=True
			return True
###############################################################################################################################################################################
# this is the multiprocessed function called from method devfilter()
def filter_multiprocess(DCd,que,devlist,devicenamefilter,filtergatecompliance,filterdraincompliance,haveTLMdata,fractVdsfit,
		filter_gmmax_min,filter_gmmax_max, filter_Idmax_min,filter_Idmax_max,filter_onoff_min,filter_onoff_max, filter_TLM_Rc_min, filter_TLM_Rc_max,filter_TLM_Rsh_min,filter_TLM_Rsh_max,filter_Ronmin_min, filter_Ronmin_max,
		filter_Igmax_min, filter_Igmax_max, filter_IdmaxFOC_min, filter_IdmaxFOC_max):
	validdevices = c.deque()
	for devk in devlist:  # go through each and every device to see if it passes the filters
		devicegood = True
		if devicenamefilter != None and not parse_rpn(expression=devicenamefilter, targetfilename=devk):
			devicegood = False

		# filter gate compliance
		elif filtergatecompliance == True and len(DCd[devk].gatestatus_foc())>0 and DCd[devk].gatestatus_no_foc() > 0:
			devicegood = False
		elif filtergatecompliance == True and DCd[devk].gatestatus_no_T() != None and DCd[devk].gatestatus_no_T() > 0:
			devicegood = False
		elif filtergatecompliance == True and DCd[devk].gatestatus_no_TF() != None and DCd[devk].gatestatus_no_TF() > 0:
			devicegood = False
		elif filtergatecompliance == True and ( (len(DCd[devk].get_pulsedVgs())>0 and len(DCd[devk].get_pulsedVgs_gatecompliance())>0) or (len(DCd[devk].get_pulsedVds())>0 and len(DCd[devk].get_pulsedVds_gatecompliance())>0) ):
			devicegood = False

		# filter drain compliance
		elif filterdraincompliance == True and DCd[devk].drainstatus_no_foc() != None and DCd[devk].drainstatus_no_foc() > 0:
			devicegood = False
		elif filterdraincompliance == True and DCd[devk].drainstatus_no_T() != None and DCd[devk].drainstatus_no_T() > 0:
			devicegood = False
		elif filterdraincompliance == True and DCd[devk].drainstatus_no_TF() != None and DCd[devk].drainstatus_no_TF() > 0:
			devicegood = False
		elif filterdraincompliance == True and ( (len(DCd[devk].get_pulsedVgs())>0 and len(DCd[devk].get_pulsedVgs_draincompliance())>0) or (len(DCd[devk].get_pulsedVds())>0 and len(DCd[devk].get_pulsedVds_draincompliance())>0) ):
			devicegood = False

		# filter gm
		elif filter_gmmax_min != None and len(DCd[devk].gmmax_T())>0 and filter_gmmax_min > DCd[devk].gmmax_T()['G']:
			devicegood = False
		elif filter_gmmax_max != None and len(DCd[devk].gmmax_T())>0 and filter_gmmax_max < DCd[devk].gmmax_T()['G']:
			devicegood = False
		# filter |Idmax| from transfer curves
		elif filter_Idmax_min != None and len(DCd[devk].Idmax_T())>0 and filter_Idmax_min > DCd[devk].Idmax_T()['I']:
			devicegood = False
		elif filter_Idmax_max != None and len(DCd[devk].Idmax_T())>0 and filter_Idmax_max < DCd[devk].Idmax_T()['I']:
			devicegood = False
		elif filter_Idmax_min != None and len(DCd[devk].Idmax_TF())>0 and filter_Idmax_min > DCd[devk].Idmax_TF()['I']:
			devicegood = False
		elif filter_Idmax_max != None and len(DCd[devk].Idmax_TF())>0 and filter_Idmax_max < DCd[devk].Idmax_TF()['I']:
			devicegood = False
		elif filter_Idmax_min != None and len(DCd[devk].Idmax_TR())>0 and filter_Idmax_min > DCd[devk].Idmax_TR()['I']:
			devicegood = False
		elif filter_Idmax_max != None and len(DCd[devk].Idmax_TR())>0 and filter_Idmax_max < DCd[devk].Idmax_TR()['I']:
			devicegood = False
		# |Idmax|FOC
		elif filter_IdmaxFOC_max != None and DCd[devk].Idmaxfoc_Vds!=None and filter_IdmaxFOC_max < DCd[devk].Idmaxfoc_Vds:
			devicegood = False
		elif filter_IdmaxFOC_min != None and DCd[devk].Idmaxfoc_Vds!=None and filter_IdmaxFOC_min > DCd[devk].Idmaxfoc_Vds:
			devicegood = False

		# filter |Igmax|
		elif filter_Igmax_min != None and DCd[devk].Igmax_T()!=None and filter_Igmax_min > DCd[devk].Igmax_T():
			devicegood = False
		elif filter_Igmax_max != None and DCd[devk].Igmax_T()!=None and filter_Igmax_max < DCd[devk].Igmax_T():
			devicegood = False
		elif filter_Igmax_min != None and DCd[devk].Igmax_TF()!=None and filter_Igmax_min > DCd[devk].Igmax_TF():
			devicegood = False
		elif filter_Igmax_max != None and DCd[devk].Igmax_TF()!=None and filter_Igmax_max < DCd[devk].Igmax_TF():
			devicegood = False
		elif filter_Igmax_min != None and DCd[devk].Igmax_TR()!=None and filter_Igmax_min > DCd[devk].Igmax_TR():
			devicegood = False
		elif filter_Igmax_max != None and DCd[devk].Igmax_TR()!=None and filter_Igmax_max < DCd[devk].Igmax_TR():
			devicegood = False

		# filter On-Off ratio
		elif filter_onoff_min != None and len(DCd[devk].Idonoffratio_T())>0 and filter_onoff_min > DCd[devk].Idonoffratio_T()['Ir']:
			devicegood = False
		elif filter_onoff_max != None and len(DCd[devk].Idonoffratio_T())>0 and filter_onoff_max < DCd[devk].Idonoffratio_T()['Ir']:
			devicegood = False
		elif filter_onoff_min != None and len(DCd[devk].Idonoffratio_TF())>0 and filter_onoff_min > DCd[devk].Idonoffratio_TF()['Ir']:
			devicegood = False
		elif filter_onoff_max != None and len(DCd[devk].Idonoffratio_TF())>0 and filter_onoff_max < DCd[devk].Idonoffratio_TF()['Ir']:
			devicegood = False
		elif filter_onoff_min != None and len(DCd[devk].Idonoffratio_TR())>0 and filter_onoff_min > DCd[devk].Idonoffratio_TR()['Ir']:
			devicegood = False
		elif filter_onoff_max != None and len(DCd[devk].Idonoffratio_TR())>0 and filter_onoff_max < DCd[devk].Idonoffratio_TR()['Ir']:
			devicegood = False

		elif filter_TLM_Rc_min != None and DCd[devk].Rc_TLM != None and filter_TLM_Rc_min > DCd[devk].Rc_TLM:
			devicegood = False
		elif filter_TLM_Rc_max != None and DCd[devk].Rc_TLM != None and filter_TLM_Rc_max < DCd[devk].Rc_TLM:
			devicegood = False
		elif haveTLMdata and filter_TLM_Rsh_min != None and DCd[devk].Rsh_TLM != None and filter_TLM_Rsh_min > DCd[devk].Rsh_TLM:
			devicegood = False
		elif haveTLMdata and filter_TLM_Rsh_max != None and DCd[devk].Rsh_TLM != None and filter_TLM_Rsh_max < DCd[devk].Rsh_TLM:
			devicegood = False

		elif len(DCd[devk].Ron_foc())>0:
			if filter_Ronmin_min != None:
				if min(DCd[devk].Ron_foc(fractVdsfit=fractVdsfit)['R']) < filter_Ronmin_min: devicegood = False
			if filter_Ronmin_max != None:
				if min(DCd[devk].Ron_foc(fractVdsfit=fractVdsfit)['R']) > filter_Ronmin_max: devicegood = False
		# devicegood=True
		if devicegood: validdevices.append(devk)  # append to list of valid devices
	if que==None: return validdevices
	else:
		que.put(validdevices)          # use this for Queue()
		#que.send(validdevices)
		del validdevices
		del DCd
	return

###############################################################################################################################################################################
#	multithread for forming device DC data
def getDC_multiprocess(que,cd,devicelist,gatewidth,tlmlength,leadresistance,Vds):
	#print("from line 1477 in wafer_analysis.py begin multiprocessing")
	cdret={}
	#print("from line 1479 in wafer_analysis.py begin multiprocessing")
	#test[0]=100

	for devk in devicelist:  # now set the lead resistance for all the devices according to the values in the geometry file and also set the device as valid
		#self.validdevices.append(devk)  # while we're at it, initially set devices as valid until the filter is applied
		cdret[devk]=cd[devk]
		cdret[devk].set_leadresistance(leadresistance)

		# iterate through measured data devices and set TLM lengths and device scaling. the key contains a portion of the name of the target devices
		if gatewidth != None:
			for gk in gatewidth:
				if gk in devk: cdret[devk].devwidth = gatewidth[gk]
		if tlmlength != None:
			for tk in tlmlength:
				if tk in devk: cdret[devk].tlmlength = tlmlength[tk]  # note that devk is the key and also the device name
		# get all DC parameters
		# self.cdret[devk].Id_foc()  ## Now read in family of curves data and calculate parameters derived from it
		# self.cdret[devk].Id_T()
		# self.cdret[devk].Id_TF()
		# self.cdret[devk].Id_TR()
		# self.cdret[devk].Id_T3()
		# self.cdret[devk].Id_T4()
		cdret[devk].Idmax_T()
		cdret[devk].Idmax_TF()
		#if cdret[devk].Idmax_TF()==None: print("None line 1392")
		cdret[devk].Idmax_TR()
		cdret[devk].Idmax_T3()
		cdret[devk].Idmax_T4()
		cdret[devk].Idonoffratio_T()
		cdret[devk].Idonoffratio_TF()
		cdret[devk].Idonoffratio_TR()
		cdret[devk].Idonoffratio_T3()
		cdret[devk].Idonoffratio_T4()
		cdret[devk].Ron_foc()
		cdret[devk].Idmax_foc(Vds=Vds)
		cdret[devk].get_Id_loopfoc1(swapindx=True)
		cdret[devk].get_Idhystfocmax()
		cdret[devk].get_Id_4loopfoc1()
		cdret[devk].get_pulsedVgs()         # Id(t) -> drain current and other parameters vs time for constant drain voltage and pulsed gate voltage
		cdret[devk].get_pulsedVds()         # Id(t) -> drain current and other parameters vs time for constant gate voltage and pulsed drain voltage
	if que!=None: que.put(cdret)
	else: return cdret
########################################################################################################################
	#	multithread for forming TLM data not used yet
def getTLM_multiprocess(que, cd, devicelist, Rc, Rsh, TLMfit, TLMlengths,minTLMlength,maxTLMlength, Ron, Vgs, totalnopointsincompliance):
	DCd = {}
	haveTLMdata = False
	for devk in devicelist:  # now set the lead resistance for all the devices according to the values in the geometry file and also set the device as valid
		# self.validdevices.append(devk)  # while we're at it, initially set devices as valid until the filter is applied
		DCd[devk] = cd[devk]
		if 'TLM' in devk:  # deal with ONLY devices which are part of a TLM structure
			k = devk.split('TLM')[0]  # get k, the site name for this device - by trimming off the TLM individual (within site) name information from the device name. k will be used as a dictionary key to access the TLM data for a site
			if k in Rc:  # be sure this device is part of a valid TLM site
				DCd[devk].Rc_TLM = Rc[k]  # contact resistance in ohms if self.DCd[devk].devwidth (the device's width) is not specified otherwise it's in ohm*mm
				if DCd[devk].devwidth != None and DCd[devk].devwidth > 0:
					DCd[devk].Rsh_TLM = 1000.*Rsh[k]  # set device parameter to sheet resistance for it's TLM grouping. Convert Kohm/square to ohms/square if device width is specified
				else:
					DCd[devk].Rsh_TLM = Rsh[k]
				DCd[devk].fit_TLM = TLMfit[k]  # set device parameter to the figure of merit for the least-squares linear fit to get Rc and Rsh for it's TLM grouping
				DCd[devk].TLMlengths = TLMlengths[k]  # device parameter list of TLM lengths in the device's TLM grouping. This will be used to draw the linear fit for the TLM
				DCd[devk].TLM_Ron = Ron[k]  # device parameter list of Ron's in the device's TLM grouping. This will be used to draw the linear fit for the TLM
				DCd[devk].TLM_Vgs = Vgs  # gate voltage where the TLM structure parameters are calculated
				DCd[devk].TLM_min_fitlength = minTLMlength  # Minimum TLM length used to perform linear fit of TLM Ron vs TLM length
				DCd[devk].TLM_max_fitlength = maxTLMlength  # Minimum TLM length used to perform linear fit of TLM Ron vs TLM length
				DCd[devk].noptsincompliance_TLM = totalnopointsincompliance[k]  # total number of gate + drain measurement points that are abnormal (probably in compliance) for the whole TLM structure that this device is a part of
				haveTLMdata = True  # since we have TLM data for this device - append its name
	# print("from line 453 in wafer_analysis.py DCd[devk].devwidth= ",devk,DCd[devk].tlmlength,DCd[devk].devwidth,DCd[devk].x_location,DCd[devk].Vds_IVt)
	if que!=None: que.put([haveTLMdata, DCd])
	else: return haveTLMdata,DCd
########################################################################################################################
# class DCd_multiprocessing(object):
# 	def __init__(self,parent=None,devicelist=None):
# 		self.parent=parent
# 		self.devicelist=devicelist
# 	def run(self,):
# 		self.DCd = {}
# 		for devk in self.devicelist:  # now set the lead resistance for all the devices according to the values in the geometry file and also set the device as valid
# 			# self.validdevices.append(devk)  # while we're at it, initially set devices as valid until the filter is applied
# 			self.DCd[devk] = self.parent.DCd[devk]
# 			self.DCd[devk].set_leadresistance(self.parent.leadresistance)
#
# 			# iterate through measured data devices and set TLM lengths and device scaling. the key contains a portion of the name of the target devices
# 			if self.parent.gatewidth != None:
# 				for gk in self.parent.gatewidth:
# 					if gk in devk: self.DCd[devk].devwidth = self.parent.gatewidth[gk]
# 			if self.parent.tlmlength != None:
# 				for tk in self.parent.tlmlength:
# 					if tk in devk: self.DCd[devk].tlmlength = self.parent.tlmlength[tk]  # note that devk is the key and also the device name
# 			# get all DC parameters
# 			# self.DCd[devk].Id_foc()  ## Now read in family of curves data and calculate parameters derived from it
# 			# self.DCd[devk].Id_T()
# 			# self.DCd[devk].Id_TF()
# 			# self.DCd[devk].Id_TR()
# 			# self.DCd[devk].Id_T3()
# 			# self.DCd[devk].Id_T4()
# 			self.DCd[devk].Idmax_T()
# 			self.DCd[devk].Idmax_TF()
# 			self.DCd[devk].Idmax_TR()
# 			self.DCd[devk].Idmax_T3()
# 			self.DCd[devk].Idmax_T4()
# 			self.DCd[devk].Idonoffratio_T()
# 			self.DCd[devk].Idonoffratio_TF()
# 			self.DCd[devk].Idonoffratio_TR()
# 			self.DCd[devk].Idonoffratio_T3()
# 			self.DCd[devk].Idonoffratio_T4()
# 			self.DCd[devk].Ron_foc()
# 			print("from line 453 in wafer_analysis.py self.DCd[devk].devwidth= ",devk,self.DCd[devk].tlmlength,self.DCd[devk].devwidth,self.DCd[devk].x_location)
# 		#que.put(self.DCd)
#
# 			########################################################################################################################