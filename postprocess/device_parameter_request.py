__author__ = 'PMarsh Carbonics Inc'
#######################################################################################################################################
# request device parameters, DC and RF for a single device that was measured
# reads data files if necessary
#
# import cmath as cm
# import numpy as np
#from scipy import stats as st
import os
import re
#import datetime as dt
import collections as col
from calculated_parameters import *
#from writefile_calculated import *
from utilities import sub, swapindex, linfitminmax, floatequal
from scipy.interpolate import interp1d
#from utilities import *
#from readfiles import readIVtranfer
#from PyQt5 import QtCore, QtWidgets

minimumabovenoisefloor=3.       # minimum level which can be reliably measured relative to the noise floor

class DeviceParameters(object):
	#linfiterrornotifier=QtCore.pyqtSignal(str)
	def __init__(self,pathname=None,devicename=None,fractVgsfit=None,Y_Ids_fitorder=None,fractftfit=None,fractfmaxfit=None,fractVdsfit_Ronfoc=None,devicetype=None):       # the device name is the name of the device to be read
		#super(DeviceParameters,self).__init__()
		# default constants
		self.fractVgsfit = 0.1		# the default fraction of Vgs sweep that a line is fit to Y-function vs Vgs to calculate Rc and Vth
		self.order = 8				# the default order of polynomial used to fit Id(Vgs) transfer curves to calculate gm and Y-function

		self.fractfmaxfit = 0.8		# the default fraction of the total frequency sweep used to linearly extrapolate UMAX to get fmaxUMAX
		self.nopts_polyfit_foc = 50		# the default number of points in the polynomial fit curves, calculated from the family of curves for the polynomial fits of drain current, transconductance, Y, etc which are calculated from the family of curves
		self.devicetype="p"			# default device type is p-channel (as in carbon nanotube FETs)
		self.parameters = []		# setup of array used to indicate which parameters have been read from data files
		self.fractVdsfit_Ronfoc=self.fractVgsfit		# default fraction of Vds to fit lines to family of curves for Ron calculation
		self.TOI={}							# TOI parameters
		self.TOIVgsswept={}                 # TOI parameters measured with Vgs swept
		self.COMPRESS={}                 # compression parameters
		self.HARM={}                        # harmonics measurements into 50ohms

		self.Rc_TLM=None					# Contact resistance derived from TLM measurements - will be valid ONLY if the device is part of a TLM structure
		self.Rsh_TLM=None					# Sheet resistance derived from TLM measurements - will be valid ONLY if the device is part of a TLM structure
		self._smoothing_factor=None			# the smoothing factor used to fit the Id(Vgs) curve to a cubic spline
		self.deltaVgsplusthres=None         # user-defined voltage to add to threshold voltage to determine consistent Id and on resistance from transfer curve
		self.fit_TLM=None					# figure of merit for the quality of least-squares linear fit to TLM resistances vs TLM length to get the TLM Rc and Rsh
		self.TLMlengths=None				# device parameter list of TLM lengths in the device's TLM grouping. This will be used to draw the linear fit for the TLM
		self.TLM_Ron=None					# device parameter list of Ron's in the device's TLM grouping. This will be used to draw the linear fit for the TLM
		self.TLM_Vgs=None					# gate voltage where the TLM structure parameters are calculated (single number)
		self.noptsincompliance_TLM=None		# total number of gate + drain measurement points that are abnormal (probably in compliance) for the whole TLM structure that this device is a part of
		self.TLM_min_fitlength=None			# Minimum TLM length used to perform linear fit of TLM Ron vs TLM length
		self.TLM_max_fitlength=None			# Maximum TLM length used to perform linear fit of TLM Ron vs TLM length
		self.devwidth=None					# device total gate width in um
		self.tlmlength=None					# if this is a TLM device, this is the length of its source-drain spacing (space between metal contacts) in um
		self.unitsscaling=1.E6				# scale currents from A to mA/mm
		self.ratioIdmax=None				# ratio of |Idmax| (from single-swept transfer curve) for device aligned to cnts / |Idmax| for device 90 deg to cnts
		self.ratioIdmaxF = None  			# ratio of |Idmax| first sweep (from dual-swept transfer curve) for device aligned to cnts / |Idmax| first sweep for device 90 deg to cnts
		self.ratioIdmaxR = None  			# ratio of |Idmax| 2nd sweep (from dual-swept transfer curve) for device aligned to cnts / |Idmax| 2nd sweep for device 90 deg to cnts
		self.ratioRon=None					# ratio of Ron (from family of curves) for Ron for device 90 deg to cnts/device aligned to cnts
		self.ORTH_Vgs=None					# Vgs used to calculate orthogonal structure parameters
		#self.npolyorderIdtransfer=7         # order of polynomial used for spline fit
		self.Vgsslew_IVt=None                  # default Vgs slew rate for single-swept transfer curve indicating that no value has been set
		self.Vgsslew_IVtfr=None                  # default Vgs slew rate for loop transfer curve indicating that no value has been set
		self.Id_atthesholdplusdelta_t=None

		self.ORTHIdmax_totalnopointsincompliance = None		# total number of gate and drain measurement points that are abnormal for the ORTH Idmax ratio parameter (based on single-swept transfer curve
		self.ORTHRon_totalnopointsincompliance=None		# total number of gate and drain measurement points that are abnormal for the ORTH Ron ratio  parameter (based on the family of curves
		self.leadresistance=0.				# resistance of traces leading to and from device. This is used to correct the device resistance data but does not modify values internal to this class except for the value of self.leadresistance and self.TLM_Ron
		######
		# the following parameters self.Vgsgatethreshold, and self.Idatthresplusdelta_T are calculated from transfer curve data and used with the user-defined self.Vgsdelta to calculate the on resistance (Ron) using a drain current which is at a constant offset voltage from the threshold voltage
		# this is designed to reduce the effects of variable threshold voltage on the on resistance determination
		self.Vgsdelta=None                    # this is the gate voltage difference between the calculated threshold voltage (from the transfer curve) and the gate voltage where we measure drain current. This value is specified by the user at the GUI and is the same for all devices
		self.Vgsgatethreshold_T=None          # threshold voltage from the single-swept transfer curve
		self.Idatthresplusdelta_T=None        # drain current in mA/mm from the single-swept transfer curve measurement, at a gate voltage of self.Vgsdelta + self.Vgatethreshold
		##########
		if pathname==None: raise ValueError("ERROR! must give a pathname")
		if devicename==None: raise ValueError("ERROR! must give a device name")
		self.pathname=pathname
		self.devicename=devicename
		if fractVgsfit!=None: self.fractVgsfit=fractVgsfit

		if Y_Ids_fitorder!=None: self.order=Y_Ids_fitorder
		if fractftfit!=None: self.fractftfit=fractftfit
		else:
			self.fractftfit = 0.8		# the default fraction of the total frequency sweep used to linearly extrapolate h21 to get fth21
		if fractfmaxfit!=None: self.fractfmaxfit=fractfmaxfit
		if fractVdsfit_Ronfoc!=None: self.fractVdsfit_Ronfoc=fractVdsfit_Ronfoc
		if devicetype!=None: self.devicetype=devicetype
		# if self.fractftfit==0.1:		#debug
		# 	quit()
		# if len(args)>=2:
		# 	self.pathname = args[0]		# mandatory base pathname for the measurements of a wafer
		# 	self.devicename = args[1]	# manditory device name for the individual device under consideration (includes wafer name)
		# 	if len(args)==3:
		# 		if "fractVgsfit" in args[2]:
		# 			self.fractVgsfit=float(re.split(',| ',args[2])[ re.split(',| ',args[2]).index('fractVgsfit')+1] )
		# 		if "Y_Ids_fitorder" in args[2]:
		# 			self.order=float(re.split(',| ',args[2])[ re.split(',| ',args[2]).index('Y_Ids_fitorder')+1] )
		# 		if "fractftfit" in args[2]:
		# 			self.fractftfit = float(re.split(',| ',args[2])[ re.split(',| ',args[2]).index('fractftfit')+1] )
		# 		if "fractfmaxfit"in args[2]:
		# 			self.fractfmaxfit = float(re.split(',| ',args[2])[ re.split(',| ',args[2]).index('fractfmaxfit')+1] )
		# 		if "fractVdsfit_Ronfoc"in args[2]:
		# 			self.fractVdsfit_Ronfoc = float(re.split(',| ',args[2])[ re.split(',| ',args[2]).index('fractVdsfit_Ronfoc')+1] )
		# 		if "devicetype"in args[2]:
		# 			self.fractVdsfit_Ronfoc = str(re.split(',| ',args[2])[ re.split(',| ',args[2]).index('devicetype')+1] )
		# else:
		# 	raise ValueError('ERROR! from constructor of DeviceParameters in device_parameter_request.py: the number of arguments must be 2 or 3! You gave", len(args)')
		self.__epsilon=1.E-35		# very small number used for comparing floating point numbers so as to remove problems due to rounding errors
	####################################################################################################################################################################################################
# custom set data extraction curve fit parameters
# Also, perform calculations again if necessary
# Not used
#
	# def set_parameters_curvefit(self,pfit):
	# 	eps=1.E-15								# a small number set in order to determine differences between floating point numbers
	# 	IVtrans_parameterchanged = "no"
	# 	IVfoc_parameterchanged="no"
	#
	# 	if "fractVgsfit" in pfit:
	# 		p=float(re.split(',| ',pfit)[ re.split(',| ',pfit).index('fractVgsfit')+1] )
	# 		if abs(p-self.fractVgsfit) > eps:				# has this parameter effectively been changed?
	# 			self.fractVgsfit=p
	# 			IVtrans_parameterchanged = "yes"
	# 	if "Y_Ids_fitorder" in pfit:
	# 		p=int(re.split(',| ',pfit)[ re.split(',| ',pfit).index('Y_Ids_fitorder')+1] )
	# 		if abs(p-self.order) > 0.5:
	# 			self.order = p
	# 			IVtrans_parameterchanged="yes"
	# 	if "noptsfoc_fit" in pfit:				# then we are setting the number of points in the polynomial fit of Id, gm, Y-function, etc.. that are derived from the IV family of curves
	# 		p=float(re.split(',| ',pfit)[ re.split(',| ',pfit).index('noptsfoc_fit')+1] )
	# 		if p>2:			# must have a minimum of 3 points in the curve
	# 			self.nopts_polyfit_foc=p
	# 			IVfoc_parameterchanged="yes"
	# 		else: print('Warning! from set_parameters_curvefit() the number of points in the polynomial fits are not changed due to too few points specified! ')
	#
	# 	if "fractftfit" in pfit:
	# 		p=float(re.split(',| ',pfit)[ re.split(',| ',pfit).index('fractftfit')+1] )
	# 		if abs(p-self.fractftfit) > eps:
	# 			self.fractftfit = p
	#
	# 	if "fractfmaxfit"in pfit:
	# 		p = float(re.split(',| ',pfit)[ re.split(',| ',pfit).index('fractfmaxfit')+1] )
	# 		if abs(p-self.fractfmaxfit)>eps:
	# 			self.fractfmaxfit = p
	#
	# 	if IVtrans_parameterchanged=="yes":				# then we must calculate new transfer curve parameters if any of the parameters have change - regardless of whether calculations had already been done in the past
	# 		self.__calc_t("force calculation")
	# 		self.__calc_tf("force calculation")
	# 		self.__calc_tr("force calculation")
	# 		#self.__calc_Ronfoc(force_calculation=True)
	#
	# 	if IVfoc_parameterchanged=="yes":
	# 		self.__calc_IdVgsfoc("force calculation")
	# 		self.__calc_Ronfoc(force_calculation=True)
	#
	# 	return self.fractVgsfit, self.order, self.fractftfit, self.fractfmaxfit
####################################################################################################################################################################################################
# get X-location of the device on the wafer
#
	def __xyloc(self):
		# try reading all types of measured data files if necessary to get the X and Y wafer location
		try: self.x_location
		except:
			self.__readIVfoc()
			try: self.x_location
			except:
				self.__readIVtransfer()
				#print("from line 147 in device_parameter_request.py device name ", self.devicename)
				try: self.x_location
				except:
					self.__readIVtransferloop(type="transferloop")
					#print("from line 151 in device_parameter_request.py device name ", self.devicename)
					try: self.x_location
					except:
						self.__readIVtransferloop(type="transferloop4")
						try: self.x_location
						except:
							self.__readSpar()
							try: self.x_location
							except:
								self.__readloopfoc()
								try: self.x_location
								except:
									self.__readpulseVgs()
									try: self.x_location
									except:
										self.__readpulseVds()
										try: self.x_location
										except:
											raise ValueError("ERROR! from line 181 of device_parameter_request.py No X coordinate in device ",self.devicename)
		return self.x_location, self.y_location
	def x(self):
		return self.__xyloc()[0]
	def y(self):
		return self.__xyloc()[1]
####################################################################################################################################################################################################
# get device name (the device name includes wafer name within)
#
	def get_devicename(self):
		try: self.devicename
		except:
			self.__readIVfoc()
			try: self.devicename
			except:
				self.__readIVtransfer()
				try: self.devicename
				except:
					self.__readIVtransferloop()
					try: self.devicename
					except:
						self.__readSpar()
						try: self.devicename
						except:
							return "NO DEVICE NAME"
		return self.devicename						# device name as read from the data files
####################################################################################################################################################################################################
# get wafer name. Assumes the the wafer name is consistent with the measured data filenames and device names
#
	def get_wafername(self):
		try: self.wafer_name
		except:
			self.__readIVfoc()
			try: self.wafer_name
			except:
				self.__readIVtransfer()
				try: self.wafer_name
				except:
					self.__readIVtransferloop()
					try: self.wafer_name
					except:
						self.__readSpar()
						try: self.wafer_name
						except:
							return "NO WAFER NAME"
		return self.wafer_name						# device name as read from the data files
####################################################################################################################################################################################################
# request small-signal two-port parameters for device Not currently used any more
#
	# def twoport(self,parameterrequest):
	# 	try: dummy=self.parameters			# do S-parameters exist for this device?
	# 	except:								# No S complex S parameters loaded must read from file
	# 		self.__readSpar()					#  read S-parameters from the file
	# 	### have S-parameter file so convert to dB/angle (degrees)
	# 	if not("SRI" in self.parameters):	# might have parameters but not S parameter: then must read in measured RI S-parameter data
	# 		Sstatus = self.__readSpar()
	# 		if Sstatus != "success":				#  attempt to read S-parameters from the file
	# 			return (Sstatus)					# indicate no S-parameters found
	#
	# 	if parameterrequest is "SRI":			# requesting complex S-parameters (real,imaginary)
	# 		return [self.freq, self.s11, self.s21, self.s12, self.s22]
	# 	if parameterrequest is "SMA":									# requesting S-parameters of form linear magnitude, angle (degrees)
	# 		if not("SMA" in self.parameters):							# then calculate MA S-parameters from RI S-parameters
	# 			self.s11_MA = [convertRItoMA(s) for s in self.s11]
	# 			self.s21_MA = [convertRItoMA(s) for s in self.s21]
	# 			self.s12_MA = [convertRItoMA(s) for s in self.s12]
	# 			self.s22_MA = [convertRItoMA(s) for s in self.s22]
	# 			self.parameters.append("SMA")
	# 		return [self.freq, self.s11_MA, self.s21_MA, self.s12_MA, self.s22_MA]
	#
	# 	if parameterrequest is "SDB":									# requesting S-parameters of form magnitude dB, angle
	# 		if not ("SDB" in self.parameters):							# then calculate DB S-parameters from RI S-parameters
	# 			self.s11_DB = [convertRItodB(s) for s in self.s11]
	# 			self.s21_DB = [convertRItodB(s) for s in self.s21]
	# 			self.s12_DB = [convertRItodB(s) for s in self.s12]
	# 			self.s22_DB = [convertRItodB(s) for s in self.s22]
	# 			self.parameters.append("SDB")
	# 		return [self.freq, self.s11_DB, self.s21_DB, self.s12_DB, self.s22_DB]
	#
	# 	if parameterrequest is "UMAX":									# requesting maximum unilateral gain
	# 		if not ("UMAX" in self.parameters):							# then calculate DB S-parameters from RI S-parameters
	# 			self.UMAX = []
	# 			for ii in range(0,len(self.freq)):
	# 				if convertSRItoUMAX(self.s11[ii],self.s21[ii],self.s22[ii]) is "unstable":	# then the two-port S11 and/or S22 approaches unity, is unstable, and UMAX does not exist
	# 					self.parameters.append("NO UMAX UNSTABLE")
	# 					return "NO UMAX UNSTABLE"
	# 				self.UMAX.append(convertSRItoUMAX(self.s11[ii],self.s21[ii],self.s22[ii]))
	# 			self.parameters.append("UMAX")
	# 		return [self.freq, self.UMAX]
	#
	# 	if parameterrequest is "GMAX":									# then get GMAX or maximum stable gain
	# 		if not ("GMAX" in self.parameters):
	# 			self.GMAX = []
	# 			for ii in range(0,len(self.freq)):
	# 				self.GMAX.append(convertSRItoGMAX(self.s11[ii],self.s21[ii],self.s12[ii],self.s22[ii]))
	# 			self.parameters.append("GMAX")
	# 		return(self.freq,self.GMAX)
	#
	# 	if parameterrequest is "HRI":										# then get the 2-port H-parameters
	# 		if not ("HRI" in self.parameters):
	# 			self.h11 = []
	# 			self.h21 = []
	# 			self.h12 = []
	# 			self.h22 = []
	# 			for ii in range(0,len(self.freq)):
	# 				H11,H21,H12,H22 = convertSRItoH(self.s11[ii],self.s21[ii],self.s12[ii],self.s22[ii],self.Z0)
	# 				self.h11.append(H11)
	# 				self.h21.append(H21)
	# 				self.h12.append(H12)
	# 				self.h22.append(H22)
	# 			self.parameters.append("HRI")
	# 		return self.h11,self.h21,self.h12,self.h22
############################################################################################################################################################################
# Get S-parameters
# forceread==True would force a re-read of the S-parameters if desired
#
	def Spar(self,type,forceread=False):
		if forceread or not hasattr(self,"s11") or not hasattr(self,'s21') or not hasattr(self,'s12') or not hasattr(self,'s22') or not hasattr(self,'freq'):		# then must read S-parameters
			self.__readSpar()
			# need to delete all stale derived parameters if read is forced since data might be changed
			try: del self.s11_MA
			except: pass
			try: del self.s21_MA
			except: pass
			try: del self.s12_MA
			except: pass
			try: del self.s22_MA
			except: pass

			try: del self.s11_DB
			except: pass
			try: del self.s21_DB
			except: pass
			try: del self.s12_DB
			except: pass
			try: del self.s22_DB
			except: pass

			try: del self.freq
			except: pass

		if type.lower()=="s11":
			if not hasattr(self,"s11"):
				if "NO DIRECTORY" in self.__readSpar():
					return "NO DIRECTORY"
				elif "NO FILE" in self.__readSpar():
					return "NO FILE"
			else:							# was able to read S-parameters
				return self.s11
		elif type.lower()=="s21":
			if not hasattr(self,"s21"):
				if "NO DIRECTORY" in self.__readSpar():
					return "NO DIRECTORY"
				elif "NO FILE" in self.__readSpar():
					return "NO FILE"
			else:							# was able to read S-parameters
				return self.s21
		elif type.lower()=="s12":
			if not hasattr(self,"s12"):
				if "NO DIRECTORY" in self.__readSpar():
					return "NO DIRECTORY"
				elif "NO FILE" in self.__readSpar():
					return "NO FILE"
			else:							# was able to read S-parameters
				return self.s12
		elif type.lower()=="s22":
			if not hasattr(self,"s22"):
				if "NO DIRECTORY" in self.__readSpar():
					return "NO DIRECTORY"
				elif "NO FILE" in self.__readSpar():
					return "NO FILE"
			else:							# was able to read S-parameters
				return self.s22
		#### calculated S-parameters magnitude and angle (degrees) returned as frequency arrays of complex numbers with the real part as the magnitude and imaginary as the angle (degrees)
		elif type.lower()=="s11ma":
			if not hasattr(self,"s11_MA"): self.s11_MA = [convertRItoMA(s) for s in self.s11]
			return self.s11_MA
		elif type.lower()=="s21ma":
			if not hasattr(self,"s21_MA"): self.s21_MA = [convertRItoMA(s) for s in self.s21]
			return self.s21_MA
		elif type.lower()=="s12ma":
			if not hasattr(self,"s12_MA"): self.s12_MA = [convertRItoMA(s) for s in self.s12]
			return self.s12_MA
		elif type.lower()=="s22ma":
			if not hasattr(self,"s22_MA"): self.s22_MA = [convertRItoMA(s) for s in self.s22]
			return self.s22_MA
		#### calculated S-parameters magnitude and angle (degrees) returned as frequency arrays of complex numbers with the real part as the dB magnitude and imaginary as the angle (degrees)
		elif type.lower()=="s11db":
			if not hasattr(self,"s11_DB"): self.s11_DB = [convertRItodB(s) for s in self.s11]
			return self.s11_DB
		elif type.lower()=="s21db":
			if not hasattr(self,"s21_DB"): self.s21_DB = [convertRItodB(s) for s in self.s21]
			return self.s21_DB
		elif type.lower()=="s12db":
			if not hasattr(self,"s12_DB"): self.s12_DB = [convertRItodB(s) for s in self.s12]
			return self.s12_DB
		elif type.lower()=="s22db":
			if not hasattr(self,"s22_DB"): self.s22_DB = [convertRItodB(s) for s in self.s22]
			return self.s22_DB
############################################################################################################################################################################
# Get H-parameters
# forceread==True would force a re-read of the S-parameters if desired
#
#
	def Hpar(self,type,forceread=False,Z0=50.+0j):
		if forceread or not hasattr(self,"s11"):
			r=self.__readSpar()		# then must read S-parameters
			if r=="NO DIRECTORY":
				#print("from device_parameter_request line 337 Have no S-parameter directory")
				return "NO DIRECTORY"
			elif r=="NO FILE":
				#print(" from device_parameter_request.py line 340 Have no S-parameter data file for this device")
				return "NO FILE"
		if forceread or not hasattr(self,"h11") or abs(self.Z0-Z0)>self.__epsilon:		# need to produce H-parameters
			self.Z0=Z0
			#get real,imaginary H parameters
			#[self.h11,self.h21,self.h12,self.h22] = [convertSRItoH(s11=self.s11[ii],s21=self.s21[ii],s12=self.s12[ii],s22=self.s22[ii],Z0=self.Z0) for ii in range(0,len(self.freq))]
			# convert S-parameters to H-parameters
			R0=Z0.real
			self.h11=col.deque()
			self.h21=col.deque()
			self.h12=col.deque()
			self.h22=col.deque()
			for i in range(0,len(self.sfrequencies())):
				D = (1-self.s11[i])*(np.conj(Z0)+self.s22[i]*Z0)+self.s12[i]*self.s21[i]*Z0
				self.h11.append(((np.conj(Z0)+self.s11[i]*Z0)*(np.conj(Z0)+self.s22[i]*Z0)-self.s12[i]*self.s21[i]*Z0*Z0)/D)
				self.h21.append(-2.*self.s21[i]*R0/D)
				self.h12.append(2.*self.s12[i]*R0/D)
				self.h22.append(((1.-self.s11[i])*(1.-self.s22[i])-self.s12[i]*self.s21[i])/D)

			# now get dB magnitudes of H parameters
			self.h11_DB=[convertRItodB(h) for h in self.h11]
			self.h21_DB=[convertRItodB(h) for h in self.h21]
			self.h12_DB=[convertRItodB(h) for h in self.h12]
			self.h22_DB=[convertRItodB(h) for h in self.h22]
		#### calculated H-parameters real and imaginary portions returned as frequency arrays of complex numbers
		if type.lower()=="h11": return self.h11
		elif type.lower()=="h21": return self.h21
		elif type.lower()=="h12": return self.h12
		elif type.lower()=="h22": return self.h22
		elif type.lower()=="h11db": return self.h11_DB
		elif type.lower()=="h21db": return self.h21_DB
		elif type.lower()=="h12db": return self.h12_DB
		elif type.lower()=="h22db": return self.h22_DB
############################################################################################################################################################################
# Get Gmax, the maximum stable gain
# forceread==True would force a re-read of the S-parameters if desired
#
#
	def Gmax(self,type,forceread=False):
		if forceread or not hasattr(self,"s11"):
			r=self.__readSpar()		# then must read S-parameters
			if r=="NO DIRECTORY":
				#print("device_parameter_request.py line 376 Have no S-parameter directory")
				return "NO DIRECTORY"
			elif r=="NO FILE":
				print("device_parameter_request.py line 379 Have no S-parameter data file for this device")
				return "NO FILE"
		if forceread or not hasattr(self,"GMAX"):
			#get Gmax, the maximum available gain and stability factor Kfactor

			self.GMAX = [convertSRItoGMAX(self.s11[ii],self.s21[ii],self.s12[ii],self.s22[ii])['gain'] for ii in range(0,len(self.freq))]		# get maximum gain
			self.GMAX_DB=10.*np.log10(self.GMAX)				# produce a log magnitude (dB) scale data set
			self.Kfactor=[convertSRItoK(self.s11[ii],self.s21[ii],self.s12[ii],self.s22[ii]) for ii in range(0,len(self.freq))]					# get stability factor
		#### calculated GMAX and UMAX_DB data are arrays of linear and dB scale data with one point per frequency
		if type==None: return {'gain':self.GMAX,'stability_factor':self.Kfactor}
		elif type.lower()=="db": return {'gain':self.GMAX_DB,'stability_factor':self.Kfactor}
############################################################################################################################################################################
# Get Umax, the unilateral power gain
# forceread==True would force a re-read of the S-parameters if desired
#
#
	def Umax(self,type=None,forceread=False):
		if forceread or not hasattr(self,"s11"):
			r=self.__readSpar()		# then must read S-parameters
			if r=="NO DIRECTORY":
				#print("device_parameter_request.py line 397 Have no S-parameter directory")
				return "NO DIRECTORY"
			elif r=="NO FILE":
				print("device_parameter_request.py line 400 Have no S-parameter data file for this device")
				return "NO FILE"
		if forceread or not hasattr(self,"UMAX"):		# need to produce H-parameters
			#get Umax, the unilateral power gain
			self.UMAX = [convertSRItoUMAX(self.s11[ii],self.s21[ii],self.s22[ii]) for ii in range(0,len(self.freq))]
			# replace bad data points in UMAX with interpolated values
			fr=[self.freq[i] for i in range(0,len(self.freq)) if self.UMAX[i]>1E-10]
			U=[self.UMAX[i] for i in range(0,len(self.freq)) if self.UMAX[i]>1E-10]
			# print("from line 458 in device_parameter_request.py fr ",fr)
			# print("from line 459 in device_parameter_request.py U ",U)
			self.UMAX=[np.interp(f,fr,U) for f in self.freq]    # linear interpolation to fill in missing UMAX points
			print("from line 459 in device_parameter_request.py U ",len(self.UMAX),len(self.freq))
			self.UMAX_DB=10.*np.log10(self.UMAX)				# produce a log magnitude (dB) scale data set
		#### calculated UMAX and UMAX_DB data are arrays of linear and dB scale data with one point per frequency
		if type==None: return self.UMAX
		elif type.lower()=="db": return self.UMAX_DB

############################################################################################################################################################################
# RF Gm from S-parameters
	def RFGm(self,forceread=False):
		if forceread or not hasattr(self, "s11"):
			r = self.__readSpar()  # then must read S-parameters
			if r == "NO DIRECTORY":
				#print("device_parameter_request.py line 487 Have no S-parameter directory")
				return []
			elif r == "NO FILE":
				#print("device_parameter_request.py line 487 Have no S-parameter data file for this device")
				return []
		if forceread or not hasattr(self, "rfgm"):  # need to produce RF Gm
			self.rfgm = [convertSRItoRFGm(s11=self.s11[ii], s21=self.s21[ii], s12=self.s12[ii], s22=self.s22[ii]) for ii in range(0, len(self.freq))]
		#### calculated RFGm has one point per frequency
			if self.devwidth != None:  # apply scaling only if gate size is specified
				scalingfactor = self.unitsscaling / self.devwidth  # scale currents to mA/mm if device gate widths are provided
				self.rfgm=np.multiply(scalingfactor,self.rfgm)
		return self.rfgm
############################################################################################################################################################################
# RF output resistance, i.e. drain resistance and conductance from S22 of the S-parameters @ 1.5GHz
	def RFGo(self,forceread=False):
		if forceread or not hasattr(self,"s11"):
			r = self.__readSpar()  # then must read S-parameters
			if r == "NO DIRECTORY":
				#print("device_parameter_request.py line 452 Have no S-parameter directory")
				return []
			elif r == "NO FILE":
				#print("device_parameter_request.py line 455 Have no S-parameter data file for this device")
				return []
		if forceread or not hasattr(self, "rfgo"):  # need to produce RF Go
			self.rfgo = [convertSRItoRFGo(s22=self.s22[ii]) for ii in range(0, len(self.freq))]
			#### calculated RFGo has one point per frequency
			if self.devwidth != None:  # apply scaling only if gate size is specified
				scalingfactor = self.unitsscaling / self.devwidth  # scale currents to mA/mm if device gate widths are provided
				self.rfgo=np.multiply(scalingfactor,self.rfgo)
		return self.rfgo
############################################################################################################################################################################
#
# returns timestamp for S-parameters
	def time_Spar(self):
		try: dummy=self.parameters			# do S-parameters exist for this device?
		except:								# No S complex S parameters loaded must read from file
			self.__readSpar()					#  read S-parameters from the file
		if not("SRI" in self.parameters):	# then must read in measured RI S-parameter data
			self.__readSpar()					#  read S-parameters from the file
		return self.spar_year,self.spar_month,self.spar_day,self.spar_hour,self.spar_minute,self.spar_second
############################################################################################################################################################################
# returns frequency list for S-parameters
	def sfrequencies(self):
		if not hasattr(self,"freq"):			# then must read in measured RI S-parameter data
			self.__readSpar()					#  read S-parameters from the file
		if not hasattr(self,"freq"): return []
		return self.freq
############################################################################################################################################################################
# returns the drain voltage bias used for the S-parameters
	def Vds_Spar(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No S complex S parameters loaded must read from file
			self.__readSpar()					#  read S-parameters from the file
		### have S-parameter file so convert to dB/angle (degrees)
		if not("SRI" in self.parameters):	# then must read in measured RI S-parameter data
			self.__readSpar()					#  read S-parameters from the file
		return self.Vds_spar
############################################################################################################################################################################
# returns the gate voltage bias used for the S-parameters
	def Vgs_Spar(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No S complex S parameters loaded must read from file
			self.__readSpar()					#  read S-parameters from the file

		if not("SRI" in self.parameters):	# then must read in measured RI S-parameter data
			self.__readSpar()					#  read S-parameters from the file
		return self.Vgs_spar
############################################################################################################################################################################
# returns the drain current measured for the S-parameters
	def Id_Spar(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No S complex S parameters loaded must read from file
			self.__readSpar()					#  read S-parameters from the file
		if not("SRI" in self.parameters):	# then must read in measured RI S-parameter data
			self.__readSpar()					#  read S-parameters from the file
		return self.Id_spar
############################################################################################################################################################################
# returns the gate current measured for the S-parameters
	def Ig_Spar(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No S complex S parameters loaded must read from file
			self.__readSpar()					#  read S-parameters from the file
		if not("SRI" in self.parameters):	# then must read in measured RI S-parameter data
			self.__readSpar()					#  read S-parameters from the file
		return self.Ig_spar
############################################################################################################################################################################
# returns the drain status measured for the S-parameters
	def drainstatus_Spar(self,forceread=True):
		if forceread or not hasattr(self,"drainstatus_spar"):
			self.__readSpar()					#  read S-parameters from the file
		if not hasattr(self,"drainstatus_spar"): return None
		else: return self.drainstatus_spar
############################################################################################################################################################################
# returns the gate status measured for the S-parameters
# forceread is False = read S-parameter data only if they are not loaded
# forceread is True = always read S-parameter data
	def gatestatus_Spar(self,forceread=False):
		if forceread or not hasattr(self,"gatestatus_spar"):
			self.__readSpar()					#  read S-parameters from the file
		if not hasattr(self,"gatestatus_spar"): return None
		else: return self.gatestatus_spar
############################################################################################################################################################################
# returns fth21 for device, i.e. the frequency ft at which the current gain drops to unity
# if forceread=True, then fresh H parameters are evaluated from a fresh S-parameter read
# 	def __ft(self,forceread=False):
# 		if "NO" in self.Hpar("h11",forceread=forceread): return None			# have no S-parameter data for this device
# 		deltanpts = int(self.fractftfit*len(self.freq))		# get number of points in linear frequency extrapolation
# 		#print("from device_parameter_request.py line 492, fractftfit",self.fractftfit) # debug
# 		try: m,b,rval,pval,stderr = st.linregress(np.log10(self.freq[:deltanpts]), np.real(self.h21_DB[:deltanpts]))
# 		except: self.fth21=0.
# 		if abs(m)>epsilon:	self.fth21 = pow(10.,-b/m)
# 		else:	self.fth21=0
# 		self.h21_ftextrapolation = [m*np.log10(f)+b for f in self.freq]			# self.h21_ftextrapolation is a dB value
# 		self.h21_ext_m=m			# use to generate linear extrapolation of h21 on log-log plot,
# 		self.h21_ext_b=b			# use to generate linear extrapolation of h21 on log-log plot
# 		if self.fth21 != None and self.fth21>1.E20: self.fth21=None
# 	#######################################
##########################################################################################################################################################################
# OBSOLETE! do not use! This does a least-squares linear fit on H21 but this is not accurate because H21 should be fit to a -20dB/dec slope
#returns fth21 for device, i.e. the frequency ft at which the current gain drops to unity
#if forceread=True, then fresh H parameters are evaluated from a fresh S-parameter read
# This version of ft is derived from the point where actual H21 crosses zero if possible
	def __ft_linearatend(self,forceread=False):
		if "NO" in self.Hpar("h11",forceread=forceread): return None			# have no S-parameter data for this device
		deltanpts = int(self.fractftfit*len(self.freq))		# get number of points in linear frequency extrapolation
		if deltanpts<2:
			deltanpts=2
			print("Warning from line 567 in device_parameter_request.py __ft() deltanpts too small, set = 2")
		# first determine if the device is good
		if max(np.real(self.h21_DB))>=0. and min(np.real(self.h21_DB))<0.:						# then the |h21| crosses 0dB
			iu=None
			for i in range(0,len(self.freq)-1):
				if self.h21_DB[i].real>0. and self.h21_DB[i+1].real<0.: iu=i				# find 0dB crossing real part is dB
			if iu==None:																	# h21 is probably showing unphysical behavior i.e. increasing with frequency across the whole frequency range so this is likely a bad device
				self.fth21=None
				self.fmaxUMAX=None															# return no data since this is most likely a bad device
				return
			iupper = int(min(iu+deltanpts/2,len(self.freq)-1))								# upper index of UMAX for linear fit
			ilower = iupper-deltanpts													# lower index of UMAX for linear fit
			if ilower<0:
				ilower=0
				iupper=ilower+deltanpts
			if iupper>=len(self.freq):
				ilower=len(self.freq)-deltanpts-1
				iupper=len(self.freq)-1
			m,b,rval,pval,stderr = st.linregress(np.log10(self.freq[ilower:iupper]),np.real(self.h21_DB[ilower:iupper]))
			if abs(m)>epsilon:	self.fth21 = pow(10.,-b/m)
			else:	self.fth21=None
			#print("from device_parameter_request.py line 566",min(self.Umax()),max(self.Umax()),self.fmaxUMAX) #debug
		elif min(np.real(self.h21_DB))>=0.:					# then |H21| is always greater than 0dB for all frequencies measured
													# Therefore extrapolate h21 beyond the measured frequency range to estimate fth21
			# find the linear regression of dB UMAX vs log10 of frequency over the self.frequencies[max index] to self.frequencies[max index - deltanpts] frequency range
			# i.e. extrapolate at the upper range of measured frequencies
			m,b,rval,pval,stderr = st.linregress(np.log10(self.freq[len(self.freq)-deltanpts:len(self.freq)]), np.real(self.h21_DB[len(self.freq)-deltanpts:len(self.freq)]))
			if abs(m)>epsilon:	self.fth21 =pow(10.,-b/m)
			else:	self.fth21=None
			self.h21_ftextrapolation = [np.power((m*np.log10(f)+b)/10.,10.) for f in self.freq]			# this is the h21 log linear extrapolated fit for __ft
		if max(np.real(self.h21_DB))<0.:							# then there is no |H21|dB>0. measured so attempt to linearly extrapolate frequency downward to find __ft
			# find the linear regression of dB H21 vs log10 of frequency over the self.frequencies[0] to self.frequencies[deltanpts] frequency range
			m,b,rval,pval,stderr = st.linregress(np.log10(self.freq[:deltanpts]),np.real(self.h21_DB[:deltanpts]))
			if abs(m)>epsilon:	self.fth21= pow(10.,-b/m)
			else:	self.fth21=None
		if self.fth21!=None and self.fth21>1.E20: self.fth21=None									# fmax is too large so set it to None
		# return fit parameters for the linear extrapolation of h21dB
		self.h21_ext_m=m			# use to generate linear extrapolation of UMAX on log-log plot
		self.h21_ext_b=b			# use to generate linear extrapolation of UMAX on log-log plot
		if self.h21_ext_m>0.:		# then the |H21| vs frequency slope is positive and these are bad data
			self.fth21=None
			self.fmaxUMAX=None
###########################################################################################################################
##########################################################################################################################################################################
#returns fth21 for device, i.e. the frequency ft at which the current gain drops to unity
#if forceread=True, then fresh H parameters are evaluated from a fresh S-parameter read
# This version of ft is derived from the point where actual H21 crosses zero if possible
	def __ft(self,forceread=False):
		if "NO" in self.Hpar("h11",forceread=forceread): return None			# have no S-parameter data for this device
		deltanpts = int(self.fractftfit*len(self.freq))		# get number of points in linear frequency extrapolation
		#print("from line 661 in device_parameter_request.py self.fractfmaxfit, deltapts",self.fractfmaxfit,deltanpts)
		if deltanpts<2:
			raise ValueError("ERROR! number of points to fit for ft is too small")
		iupper=len(self.freq)-1
		ilower=iupper-deltanpts
		if ilower<0:
			ilower=0
			iupper=ilower+deltanpts
		if iupper>=len(self.freq):
			ilower=len(self.freq)-deltanpts-1
			iupper=len(self.freq)-1
		#devname=self.devicename
		logfreq=np.log10(self.freq[ilower:iupper])          # log10 frequency
		m=-20.          # force constant slope = -20dB/decade of frequency
		b=np.average(np.subtract(np.real(self.h21_DB[ilower:iupper]),np.multiply(m,logfreq)))       # find  x intercept. This is the least-squares fit of a -20dB/decade line to h21_DB Note that self.h21_DB is complex with the real portion as dB magnitude and imaginary portion as the angle
		self.fth21 = pow(10.,-b/m)
		if self.fth21!=None and self.fth21>1.E20: self.fth21=None									# fmax is too large so set it to None
		# return fit parameters for the linear extrapolation of h21dB
		self.h21_ext_m=m			# use to generate linear extrapolation of UMAX on log-log plot
		self.h21_ext_b=b			# use to generate linear extrapolation of UMAX on log-log plot
		if self.h21_ext_m>0.:		# then the |H21| vs frequency slope is positive and these are bad data
			self.fth21=None
			self.fmaxUMAX=None
###########################################################################################################################

	# get ft, forceread=True forces fresh read of S-parameters and evaluation of a fresh ft from them
	def ft(self,forceread=False):				# get fth21
		self.__ft(forceread=forceread)
		if not hasattr(self,"fth21"): return None
		else: return self.fth21
	#######################################
	# get fmax, forceread=True forces fresh read of S-parameters and evaluation of a fresh fmax from them
	def ftextrapolation(self,forceread=False):				# get linear extrapolation of h21_DB on a log frequency scale, used to derive fmaxUMAX
		if forceread or not hasattr(self,'h21_ext_m'): self.__fmax(forceread=True)
		if hasattr(self,'h21_ext_m'): return {"m": self.h21_ext_m, "b":self.h21_ext_b}
		else: return {"m":None, "b":None}
############################################################################################################################################################################
# WARNING! do not use as this is obsolete
# returns __fmax for device. __fmax is the frequency where UMAX approaches unity
# this version of the function linearly extrapolates UMAX near the end of the measured frequency range
# However, this function has been superceded by __fmax() which calculates fmax from a least squares linear fit with slope set to -20dB
# forceread=True forces fresh read of S-parameters and fresh evaluation of self.Umax
# calculates self.fmaxUMAX where self.fmaxUMAX is the linear extrapolation of the unilateral power gain vs frequency from measured S parameters
# self.fmaxUMAX is extrapolated from self.UMAX from the uppermost frequency down to a fraction of the total frequency range determined by self.fractfmaxfit
# the linear extrapolation of UMAX to find fmax is calculated as
# self.UMAX_ext_m			# slope of the dB scale of the extrapolated UMAX
# self.UMAX_ext_b			# intercept of the dB scale of the extrapolated UMAX
	def __fmax_linearatend(self,forceread=False):
		minmaxUMAXdB=6.			# TODO: set minimum allowed max(UMAX(f)) as a stopgap measure against bad data. Will have to fix later.
		if 'NO' in self.Umax(type='db',forceread=forceread): return None						# have no UMAX data for this device
		deltanpts = int(self.fractfmaxfit*len(self.freq))		# get number of points in linear frequency extrapolation
		# first determine if the device is good
		if max(self.Umax())>=1. and min(self.Umax())<1.:										# find fmax from log linear UMAX fit to find the frequency where the measured UMAX reaches unity
			for i in range(0,len(self.freq)-1):
				if self.UMAX[i]>1 and self.UMAX[i+1]<=1:
					iu=i										# find first unity-crossing value of Umax
					break
				else: iu=len(self.UMAX)-1
			iu=len(self.freq)-1
				#TODO need to fix this to properly account for fmax when measurements don't show a zero crossing
			#iu = min(range(len(self.freq)), key=lambda i: abs(self.UMAX[i]-1.))				# iu is the index of the frequency closest to fmax
			#iupper = int(min(iu+deltanpts/2,len(self.freq)-1))								# upper index of UMAX for linear fit
			#ilower = iupper-deltanpts													# lower index of UMAX for linear fit
			iupper=iu
			ilower=iu-deltanpts
			if ilower<0:
				ilower=0
				iupper=ilower+deltanpts
			if iupper>=len(self.freq):
				ilower=len(self.freq)-deltanpts-1
				iupper=len(self.freq)-1
			#print("from device_parameter_request.py line 557 ",self.devicename,iupper,ilower,len(np.log10(self.freq[ilower:iupper])),len(self.UMAX_DB[ilower:iupper])) # debug
			devname=self.devicename
			m,b,rval,pval,stderr = st.linregress(np.log10(self.freq[ilower:iupper]),self.UMAX_DB[ilower:iupper])
			if abs(m)>epsilon:	self.fmaxUMAX = pow(10.,-b/m)
			else:	self.fmaxUMAX=None
			#print("from device_parameter_request.py line 566",min(self.Umax()),max(self.Umax()),self.fmaxUMAX) #debug
		elif min(self.Umax())>=1.:					# then UMAX is always greater than unity for all frequencies measured
													# Therefore extrapolate Umax beyond the measured frequency range to estimate fmaxUMAX
			# find the linear regression of dB UMAX vs log10 of frequency over the self.frequencies[max index] to self.frequencies[max index - deltanpts] frequency range
			# i.e. extrapolate at the upper range of measured frequencies
			m,b,rval,pval,stderr = st.linregress(np.log10(self.freq[len(self.freq)-deltanpts:len(self.freq)]), self.UMAX_DB[len(self.freq)-deltanpts:len(self.freq)])
			if abs(m)>epsilon:	self.fmaxUMAX = pow(10.,-b/m)
			else:	self.fmaxUMAX=None
			self.UMAX_fmaxextrapolation = [np.power((m*np.log10(f)+b)/10.,10.) for f in self.freq]			# this is the UMAX log linear extrapolated fit for __fmax
		if max(self.Umax())<1.:							# then there is no UMAX>1. measured so attempt to linearly extrapolate frequency downward to find __fmax
			# find the linear regression of dB UMAX vs log10 of frequency over the self.frequencies[0] to self.frequencies[deltanpts] frequency range
			m,b,rval,pval,stderr = st.linregress(np.log10(self.freq[:deltanpts]),self.UMAX_DB[:deltanpts])
			if abs(m)>epsilon:	self.fmaxUMAX = pow(10.,-b/m)
			else:	self.fmaxUMAX=None
		if self.fmaxUMAX!=None and self.fmaxUMAX>1.E20: self.fmaxUMAX=None									# fmax is too large so set it to None
			#self.UMAX_fmaxextrapolation = [np.power((m*np.log10(f)+b)/10.,10.) for f in self.freq]			# this is the UMAX log linear extrapolated fit for __fmax
		# return fit parameters for the linear extrapolation of UMAX
		self.UMAX_ext_m=m			# use to generate linear extrapolation of UMAX on log-log plot
		self.UMAX_ext_b=b			# use to generate linear extrapolation of UMAX on log-log plot
		if self.UMAX_ext_m>0. or max(self.UMAX_DB)<minmaxUMAXdB:		# then the Umax vs frequency slope is positive and these are bad data
			self.fmaxUMAX=None
			self.fth21=None
		#######################################
	def fmax(self):				# get fth21
		if not hasattr(self,'fmaxUMAX'): self.__fmax()		# calculate fth21 if we don't have it already
		if hasattr(self,'fmaxUMAX'): return self.fmaxUMAX
		else: return None
	#######################################
	def fmaxextrapolation(self):				# get linear extrapolation of UMAX_DB on a log frequency scale, used to derive fmaxUMAX
		if not hasattr(self,'UMAX_ext_m'): self.__fmax()
		if hasattr(self,'UMAX_ext_m'): return {"m": self.UMAX_ext_m, "b":self.UMAX_ext_b}
		else: return {"m":None, "b":None}
############################################################################################################################################################################
############################################################################################################################################################################
# returns __fmax for device. __fmax is the frequency where UMAX approaches unity
# this is a least-squares fit to UMAX which assumes -20dB/decade
# this version of the function linearly extrapolates UMAX from the last self.fractfmaxfit fraction of the frequencies
# However, this function has been superceded by __fmax() which calculates fmax from a least squares linear fit with slope set to -20dB
# forceread=True forces fresh read of S-parameters and fresh evaluation of self.Umax
# calculates self.fmaxUMAX where self.fmaxUMAX is the linear extrapolation of the unilateral power gain vs frequency from measured S parameters
# self.fmaxUMAX is extrapolated from self.UMAX from the uppermost frequency down to a fraction of the total frequency range determined by self.fractfmaxfit
# the linear extrapolation of UMAX to find fmax is calculated as
# self.UMAX_ext_m			# slope of the dB scale of the extrapolated UMAX
# self.UMAX_ext_b			# intercept of the dB scale of the extrapolated UMAX
	def __fmax(self,forceread=False):
		minmaxUMAXdB=6.			# TODO: set minimum allowed max(UMAX(f)) as a stopgap measure against bad data. Will have to fix later.
		if 'NO' in self.Umax(type='db',forceread=forceread): return None						# have no UMAX data for this device
		deltanpts = int(self.fractfmaxfit*len(self.freq))		# get number of points in linear frequency extrapolation
		#print("from line 785 in device_parameter_request.py self.fractfmaxfit, deltapts",self.fractfmaxfit,deltanpts)
		iupper=len(self.freq)-1
		ilower=iupper-deltanpts
		if ilower<0:
			ilower=0
			iupper=ilower+deltanpts
		if iupper>=len(self.freq):
			ilower=len(self.freq)-deltanpts-1
			iupper=len(self.freq)-1
		logfreq=np.log10(self.freq[ilower:iupper])          # log10 frequency
		m=-20.          # force constant slope = -20dB/decade of frequency
		b=np.average(np.subtract(self.UMAX_DB[ilower:iupper],np.multiply(m,logfreq)))       # find  x intercept. This is the least-squares fit of a -20dB/decade line to UMAX_dB
		self.fmaxUMAX = pow(10.,-b/m)
		if self.fmaxUMAX!=None and self.fmaxUMAX>1.E20: self.fmaxUMAX=None									# fmax is too large so set it to None
		# return fit parameters for the linear extrapolation of UMAX
		self.UMAX_ext_m=m			# use to generate linear extrapolation of UMAX on log-log plot
		self.UMAX_ext_b=b			# use to generate linear extrapolation of UMAX on log-log plot
		if self.UMAX_ext_m>0. or max(self.UMAX_DB)<minmaxUMAXdB:		# then the Umax vs frequency slope is positive and these are bad data
			self.fmaxUMAX=None
			self.fth21=None
############################################################################################################################################################################









############################################################################################################################################################################
#	Outputs S parameters as complex numbers real and imaginary
# 	Frequency output is in Hz
# always reads the S-parameters when called
	def __readSpar(self):
		self.pathname_spar = self.pathname+sub("SPAR")
		if self.devwidth!=None: scalingfactor=self.unitsscaling/self.devwidth								# scale currents to mA/mm
		else: scalingfactor=1.
		try: filelisting = os.listdir(self.pathname_spar)
		except:
			#print "ERROR directory", self.pathname_spar, "does not exist: returning from __readSpar() in device_parameter_request.py"
			return "NO DIRECTORY"
		nodevices=0
		for fileS in filelisting:
			if fileS.endswith('SRI.s2p'): targetSparameterdevicename=fileS.replace('_SRI.s2p','')
			elif fileS.endswith('SDB.s2p'): targetSparameterdevicename=fileS.replace('_SDB.s2p','')
			elif fileS.endswith('SMA.s2p'): targetSparameterdevicename=fileS.replace('_SMA.s2p','')
			else: targetSparameterdevicename=''
			#print("from line 668 in device_parameter_request.py ", nodevices, self.devicename, targetSparameterdevicename)  # debug
			#if fileS.endswith(".s2p") and (self.devicename in fileS):
			sfilesnotunique=col.deque()
			if self.devicename==targetSparameterdevicename:
				#print("from line 672 in device_parameter_request.py ", nodevices, self.devicename, targetSparameterdevicename,fileS) # debug
				self.fullfilenameSRI = self.pathname_spar+"/"+fileS				# form full devicename (path+devicename) of complex S-parameter file
				sfilesnotunique.append(fileS)
				nodevices+=1
				if nodevices > 1: print("from line 701 in device_parameter_request.py ", nodevices, self.devicename, targetSparameterdevicename)
		if nodevices>1:
			for sf in sfilesnotunique: print("Devices are not unique: ",fileS)
			raise ValueError('ERROR device not unique!')
		try: fspar=open(self.fullfilenameSRI,'r')
		except:
			#print "WARNING from __readSpar in device_parameter_request.py: cannot open file: "
			self.fullfilenameSRI="cannot open file"
			return "NO FILE"

		sfilelines = [a for a in fspar.read().splitlines()]             # sfilelines is a string array of the lines in the file
		for fileline in sfilelines:
			# get timestamp
			if "year" in fileline:
				self.spar_year=fileline.split('\t')[1].lstrip()
			elif "month" in fileline:
				self.spar_month=fileline.split('\t')[1].lstrip()
			elif "day" in fileline:
				self.spar_day=fileline.split('\t')[1].lstrip()
			elif "hour" in fileline:
				self.spar_hour=fileline.split('\t')[1].lstrip()
			elif "minute" in fileline:
				self.spar_minute=fileline.split('\t')[1].lstrip()
			elif "second" in fileline:
				self.spar_second=fileline.split('\t')[1].lstrip()
			# get devicename and location on wafer
			elif "wafer name" in fileline:
				self.wafer_name=fileline.split('\t')[1].lstrip()
			elif "device name" in fileline:
				if self.devicename!=fileline.split('\t')[1].lstrip(): raise ValueError("ERROR! inconsistent filename")
				#self.devicename=fileline.split('\t')[1].lstrip()
			elif "x location" in fileline:
				self.x_location=int(fileline.split('\t')[1].lstrip())
			elif "y location" in fileline:
				self.y_location=int(fileline.split('\t')[1].lstrip())
			elif "Vds" in fileline:
				self.Vds_spar=float(fileline.split('\t')[1].lstrip())
			elif "Id" in fileline:
				self.Id_spar=float(fileline.split('\t')[1].lstrip())*scalingfactor			# scale current to mA/mm if device width was given
			elif "drain status" in fileline:
				self.drainstatus_spar=fileline.split('\t')[1].lstrip()
			elif "Vgs" in fileline:
				self.Vgs_spar=float(fileline.split('\t')[1].lstrip())
			elif "Ig" in fileline:
				self.Ig_spar=float(fileline.split('\t')[1].lstrip())*scalingfactor			# scale current to mA/mm if device width was given
			elif "gate status" in fileline:
				self.gatestatus_spar=fileline.split('\t')[1].lstrip()
		# now load in S-parameter data itself (complex)
		for fileline in sfilelines:                 # find type of file
			if (("#" in fileline) and (' S ' in fileline)):                         # this is the datatype specifier
				if (' RI ' in fileline):
					Sparameter_type = 'SRI'                      # these are complex 2-port S-parameter data
				elif (' DB ' in fileline or ' dB' in fileline or ' db' in fileline or ' Db' in fileline):
					Sparameter_type= 'SDB'                      # these are S-parameter data dB magnitude and angle in degrees
				elif (' MA ' in fileline):
					Sparameter_type = 'SMA'                      # these are S-parameter data magnitude and angle in degrees
				if ('GHZ' in fileline):
					Sfrequency_multiplier= 1E9
				elif ('MHZ' in fileline):
					Sfrequency_multiplier= 1E6
				elif ('KHZ' in fileline):
					Sfrequency_multiplier= 1E3
				else:
					Sfrequency_multiplier= 1.0
				self.Z0 = float(fileline[re.search("R ",fileline).start()+2:])           # read characteristic impedance

	# now read data from file and output complex (RI) S-parameters ##############
		self.s11 = []
		self.s21 = []
		self.s12 = []
		self.s22 = []
		self.freq = []
		for fileline in sfilelines:                                                 # load lines from the data file
			if not(('!' in fileline) or ('#' in fileline)):                       # then this line are data
				self.freq.append(Sfrequency_multiplier*float(fileline.split()[0]))                    # read the frequency
				#self.frequencies[-1]*self.deviceparameter['frequency multiplier']      # scale frequency to Hz
				if Sparameter_type is 'SRI':                 # these are complex S-parameter data
					#print "fileline =",fileline                                 # debug
					self.s11.append(complex(float(fileline.split()[1]),float(fileline.split()[2])))
					self.s21.append(complex(float(fileline.split()[3]),float(fileline.split()[4])))
					self.s12.append(complex(float(fileline.split()[5]),float(fileline.split()[6])))
					self.s22.append(complex(float(fileline.split()[7]),float(fileline.split()[8])))
				if Sparameter_type is 'SDB':                 					# these are dB/angle S-parameter data convert to complex
					sparm = float(fileline.split()[1])            					# read magnitude (dB)
					spara = float(fileline.split()[2])			                   # read angle (degrees)
					self.s11.append(convertdBtoRI(sparm,spara))                     # append real and imaginary to S-parameter array

					sparm = float(fileline.split()[3])					            # these are dB/angle S-parameter data convert to complex
					spara = float(fileline.split()[4])	                   			# read angle (degrees)
					self.s21.append(convertdBtoRI(sparm,spara))                     # append real and imaginary to S-parameter array

					sparm = float(fileline.split()[5])            					# these are dB/angle S-parameter data convert to complex
					spara = float(fileline.split()[6])                   			# read angle (degrees)
					self.s12.append(convertdBtoRI(sparm,spara))                     # append real and imaginary to S-parameter array

					sparm = float(fileline.split()[7])            					# these are dB/angle S-parameter data convert to complex
					spara = float(fileline.split()[8])                   			# read angle (degrees)
					self.s22.append(convertdBtoRI(sparm,spara))                     # append real and imaginary to S-parameter array

				if Sparameter_type is 'SMA':                 					# these are linear/angle (degrees) S-parameter data convert to complex
					sparm = float(fileline.split()[1])                              # read magnitude (linear)
					spara = float(fileline.split()[2])				                # read angle (degrees)
					self.s11.append(convertMAtoRI(sparm,spara))                     # append real and imaginary to S-parameter array

					sparm = float(fileline.split()[3])                              # read magnitude (linear)
					spara = float(fileline.split()[4])				                # read angle (degrees)
					self.s21.append(convertMAtoRI(sparm,spara))                     # append real and imaginary to S-parameter array

					sparm = float(fileline.split()[5])                              # read magnitude (linear)
					spara = float(fileline.split()[6])				                # read angle (degrees)
					self.s12.append(convertMAtoRI(sparm,spara))                     # append real and imaginary to S-parameter array

					sparm = float(fileline.split()[7])                              # read magnitude (linear)
					spara = float(fileline.split()[8])				                # read angle (degrees)
					self.s22.append(convertMAtoRI(sparm,spara))                     # append real and imaginary to S-parameter array
		fspar.close()
		try: self.parameters.append("SRI")											# we now have at complex S-parameters so set the indicator
		except:
			self.parameters = []
			self.parameters.append("SRI")
		return "success"
############################################################################################################################################################################
#	Read and output gain and noise figure as read by noise figure meter and stored on file
# 	Frequency output is in Hz
# always reads the S-parameters when called
	def __readnoise50ohm(self):
		pathname = self.pathname+sub("NOISE")
		if self.devwidth!=None: scalingfactor=self.unitsscaling/self.devwidth								# scale currents to mA/mm
		else: scalingfactor=1.
		try: filelisting = os.listdir(pathname)
		except:
			#print "ERROR directory", self.pathname_spar, "does not exist: returning from __readSpar() in device_parameter_request.py"
			return "NO DIRECTORY"
		nodevices=0
		for file in filelisting:
			if file.endswith('noise.xls'):targetdevicename=file.replace('_noise.xls','')
			else: targetdevicename=''
			filesnotunique=col.deque()
			if self.devicename==targetdevicename:
				self.fullfilename= pathname+"/"+file				# form full devicename (path+devicename) of complex S-parameter file
				filesnotunique.append(file)
				nodevices+=1
				if nodevices > 1: print("from line 701 in device_parameter_request.py ", nodevices, self.devicename, targetdevicename)
		if nodevices>1:
			for f in filesnotunique: print("Devices are not unique: ",f)
			raise ValueError('ERROR device not unique!')
		try: fpar=open(self.fullfilename,'r')
		except:
			self.fullfilename="cannot open file"
			return "NO FILE"
		filelines = [a for a in fpar.read().splitlines()]             # sfilelines is a string array of the lines in the file
		for fileline in filelines:
			# get timestamp
			if "year" in fileline:
				self.noise50_year=fileline.split('\t')[1].lstrip()
			elif "month" in fileline:
				self.noise50_month=fileline.split('\t')[1].lstrip()
			elif "day" in fileline:
				self.noise50_day=fileline.split('\t')[1].lstrip()
			elif "hour" in fileline:
				self.noise50_hour=fileline.split('\t')[1].lstrip()
			elif "minute" in fileline:
				self.noise50_minute=fileline.split('\t')[1].lstrip()
			elif "second" in fileline:
				self.noise50_second=fileline.split('\t')[1].lstrip()
			# get devicename and location on wafer
			elif "wafer name" in fileline:
				self.wafer_name=fileline.split('\t')[1].lstrip()
			elif "device name" in fileline:
				if self.devicename!=fileline.split('\t')[1].lstrip(): raise ValueError("ERROR! inconsistent filename")
			elif "x location" in fileline:
				self.x_location=int(fileline.split('\t')[1].lstrip())
			elif "y location" in fileline:
				self.y_location=int(fileline.split('\t')[1].lstrip())
			elif "Vds" in fileline:
				self.Vds_noise50=float(fileline.split('\t')[1].lstrip())
			elif "Id" in fileline:
				self.Id_noise50=float(fileline.split('\t')[1].lstrip())*scalingfactor			# scale current to mA/mm if device width was given
			elif "drain status" in fileline:
				self.drainstatus_noise50=fileline.split('\t')[1].lstrip()
			elif "Vgs" in fileline:
				self.Vgs_noise50=float(fileline.split('\t')[1].lstrip())
			elif "Ig" in fileline:
				self.Ig_noise50=float(fileline.split('\t')[1].lstrip())*scalingfactor			# scale current to mA/mm if device width was given
			elif "gate status" in fileline:
				self.gatestatus_noise50=fileline.split('\t')[1].lstrip()
		# now load in 50ohm noise data itself
		for fileline in filelines:                 # find type of file
			if (("#" in fileline) and ('frequency' in fileline)):                         # this is the datatype specifier
				if ('ghz' in fileline.lower()):
					frequency_multiplier= 1E9
				elif ('mhz' in fileline.lower()):
					frequency_multiplier= 1E6
				elif ('khz' in fileline.lower()):
					frequency_multiplier= 1E3
				else:
					frequency_multiplier= 1.0

	# now read data from file and output noise50 noise figure (dB) and gain50 (dB) ##############
		self.freqnoise50 = []
		self.gain50 = []
		self.NF50 = []
		for fileline in filelines:                                                 # load lines from the data file
			if not(('!' in fileline) or ('#' in fileline)):                       # then this line are data
				self.freqnoise50.append(frequency_multiplier*float(fileline.split()[0]))                    # read the frequency
				self.gain50.append(float(fileline.split()[1]))                     # append gain dB
				self.NF50.append(float(fileline.split()[2]))                       # append noisefigure in 50ohm system dB
		fpar.close()
		return "success"
############################################################################################################################################################################
	###################################################################################################################################################################
# Fmin50=_calc_Fmin50(Sfreq,Spar,Nfreq,NF)
# where Sfreq and Spar are the Sparameter frequency array and Sparameter array respectively. Nfreq is the noise frequency array used to measure the noise figure (at 50ohms) and NF is the noise figure measured at 50ohms array corresponding to the  noise frequency array.
# Fmin50 is the calculated minimum noise figure from interpolated S11 and S21 data, used to calculate the Fmin (in dB) at each of the Nfreq noise frequency array points. Fmin50 is an array with the same size as Nfreq.
# self.freq[] are the S-parameter measurement frequencies in Hz, self.freqnoise50[] are the noise measurement frequencies (50 ohm noise measurement).
	def __calc_Fmin50(self):
		self.sfrequencies()             # read S-parameters if necessary
		self.__readnoise50ohm()		# read noise noise as measured in a 50 ohm system
		if not (hasattr(self,"freq") and hasattr(self,"s11") and self.freq!=None and self.s11!=None):
			#print("WARNING no S-parameters.  device_parameter_request.py Nothing calculated")
			return("no data")
		if not (hasattr(self,"NF50") and self.NF50!=None):
			#print("no noise parameters")
			return("no data")
		if len(self.freqnoise50)!=len(self.NF50):
			print("ERROR from 939 in device_parameter_request.py! noise figure array size not equal to noise figure frequency array size in device_parameter_request.py. Nothing calculated")
			return("inconsistent")
		if max(self.freqnoise50)>max(self.freq):
			print("WARNING! from __calc_Fmin50 in  device_parameter_request.py noise measurement frequencies outside that of Sparameter frequencies. Nothing calculated")
			return("inconsistent")

		NF50linear_m1=np.subtract(dBtolin(self.NF50),1.)                   # find the linear measured 50ohm noise figure -1 from the dB noise figure measured in a 50ohm system, over the noise figure measured frequency points
	# find  (1-S11**2) and from that the optimum DUT gain for conjugate input match over the S-parameter frequency points and interpolate these data to the noise measurement frequency points
		inputmissmatchfactor_sfreq=np.subtract(1.,np.square(np.abs(self.s11)))               # this is 1-|S11|**2 over the S-parameter frequencies
		GassocFmin50_sfreq=np.divide(np.square(np.abs(self.s21)),inputmissmatchfactor_sfreq)          # this is the DUT power gain (linear) for a 50ohm output  load and a conjugate match at the input over the S-parameter frequencies
		# interpolate data from S-parameter frequency points to the noise measurement frequency points
		fGassocFmin=interp1d(x=self.freq,y=GassocFmin50_sfreq)                                  # find GassocFmin50_sfreq interpolated at the noise measurement frequencies (linear)
		finputmissmatchfactor=interp1d(x=self.freq,y=inputmissmatchfactor_sfreq)                # find (1-|S11|**2) interpolated at the noise measurement frequencies

		self.gainFmin50=list(lintodB(fGassocFmin(self.freqnoise50)))                  # associated DUT gain (dB) with S11* matched input and 50ohm output at the measurement
		self.Fmin50=list(lintodB(np.add(np.multiply(finputmissmatchfactor(self.freqnoise50),NF50linear_m1),1.)))      # minimum noise figure (dB) approximation using only 50ohm data assumes optimum noise match = S11*
		self.gainFmin50average=np.average(self.gainFmin50)									# average associated gain across all measured frequencies
		self.Fmin50average=np.average(self.Fmin50)
		self.Fmin50lowest=np.min(self.Fmin50)
		self.gainFmin50lowest=self.gainFmin50[self.Fmin50.index(self.Fmin50lowest)]
		self.freqFmin50lowest=self.freqnoise50[self.Fmin50.index(self.Fmin50lowest)]
		self.NF50avg=np.average(self.NF50)
		self.NF50lowest=np.min(self.NF50)
		self.freqNF50lowest=self.freqnoise50[self.NF50.index(self.NF50lowest)]
		#print("from 956 device_parameter_request.py have noise parameters")
		return("success")              # return optimum gain for input match only and noise figure at the optimum input match both in dB
############################################################################################################################################################################
############################################################################################################################################################################
#	Read and output gain and noise figure as read by noise figure meter and stored on file
# 	Frequency output is in Hz
# always reads the S-parameters when called
	def __read_noise_parameters(self):
		pathname = self.pathname+sub("NOISE")
		if self.devwidth!=None: scalingfactor=self.unitsscaling/self.devwidth								# scale currents to mA/mm
		else: scalingfactor=1.
		try: filelisting = os.listdir(pathname)
		except:
			#print "ERROR directory", self.pathname_spar, "does not exist: returning from __readSpar() in device_parameter_request.py"
			return "NO DIRECTORY"
		nodevices=0
		for file in filelisting:
			if file.endswith('noiseparameter.xls'):targetdevicename=file.replace('_noiseparameter.xls','')
			else: targetdevicename=''
			filesnotunique=col.deque()
			if self.devicename==targetdevicename:
				self.fullfilename= pathname+"/"+file				# form full devicename (path+devicename) of complex S-parameter file
				filesnotunique.append(file)
				nodevices+=1
				if nodevices > 1: print("from line 701 in device_parameter_request.py ", nodevices, self.devicename, targetdevicename)
		if nodevices>1:
			for f in filesnotunique: print("Devices are not unique: ",f)
			raise ValueError('ERROR device not unique!')
		try: fpar=open(self.fullfilename,'r')
		except:
			self.fullfilename="cannot open file"
			return "NO FILE"

		filelines = [a for a in fpar.read().splitlines()]             # sfilelines is a string array of the lines in the file
		for fileline in filelines:
			# get timestamp
			if "year" in fileline:
				self.year_noise_parameters=fileline.split('\t')[1].lstrip()
			elif "month" in fileline:
				self.month_noise_parameters=fileline.split('\t')[1].lstrip()
			elif "day" in fileline:
				self.day_noise_parameters=fileline.split('\t')[1].lstrip()
			elif "hour" in fileline:
				self.hour_noise_parameters=fileline.split('\t')[1].lstrip()
			elif "minute" in fileline:
				self.minute_noise_parameters=fileline.split('\t')[1].lstrip()
			elif "second" in fileline:
				self.second_noise_parameters=fileline.split('\t')[1].lstrip()
			# get devicename and location on wafer
			elif "wafer name" in fileline:
				self.wafer_name=fileline.split('\t')[1].lstrip()
			elif "device name" in fileline:
				self.devicename=fileline.split('\t')[1].strip()
				if self.devicename!=fileline.split('\t')[1].lstrip(): raise ValueError("ERROR! inconsistent filename")
			elif "x location" in fileline:
				self.x_location=int(fileline.split('\t')[1].lstrip())
			elif "y location" in fileline:
				self.y_location=int(fileline.split('\t')[1].lstrip())
			elif "Vds" in fileline:
				self.Vds_noise_parameters=float(fileline.split('\t')[1].lstrip())
			elif "Id" in fileline:
				self.Id_noise_parameters=float(fileline.split('\t')[1].lstrip())*scalingfactor			# scale current to mA/mm if device width was given
			elif "drain status" in fileline:
				self.drainstatus__noise_parameters=fileline.split('\t')[1].lstrip()
			elif "Vgs" in fileline:
				self.Vgs_noise_parameters=float(fileline.split('\t')[1].lstrip())
			elif "Ig" in fileline:
				self.Ig_noise_parameters=float(fileline.split('\t')[1].lstrip())*scalingfactor			# scale current to mA/mm if device width was given
			elif "gate status" in fileline:
				self.gatestatus_noise_parameters=fileline.split('\t')[1].lstrip()
		# now load in 50ohm noise data itself
		for fileline in filelines:                 # find type of file
			if (("#" in fileline) and ('frequency' in fileline)):                         # this is the datatype specifier
				if ('ghz' in fileline.lower()):
					frequency_multiplier= 1E9
				elif ('mhz' in fileline.lower()):
					frequency_multiplier= 1E6
				elif ('khz' in fileline.lower()):
					frequency_multiplier= 1E3
				else:
					frequency_multiplier= 1.0

	# now read data from file and output noise50 noise figure (dB) and gain50 (dB) ##############
		self.noise_parameters=[]
		for fileline in filelines:                                                 # load lines from the data file
			if not(('!' in fileline) or ('#' in fileline)):                       # then this line are data
				self.noise_parameters.append({})
				self.noise_parameters[-1]['frequency']=frequency_multiplier*float(fileline.split()[0])                   # read the frequency in Hz
				self.noise_parameters[-1]['FmindB']=float(fileline.split()[1])                                           # minimum noise figure in dB
				self.noise_parameters[-1]['gopt']=convertMAtoRI(float(fileline.split()[2]),float(fileline.split()[3]))      # optimum noise source reflection coefficient in real+jimaginary
				self.noise_parameters[-1]['Rn']=float(fileline.split()[4])                                              # noise resistance in ohms
				self.noise_parameters[-1]['GassocdB']=float(fileline.split()[5])                                        # Associated gain in dB
		fpar.close()
		return "success"
############################################################################################################################################################################
# Read third order intercept point data
# #
# 	def __readTOI(self):
# 		if self.devwidth!=None: scalingfactor=self.unitsscaling/self.devwidth								# scale currents to mA/mm
# 		else: scalingfactor=1.
# 		self.pathname_TOI = self.pathname+sub("RF_power")
# 		try: filelisting = os.listdir(self.pathname_TOI)
# 		except: return "NO DIRECTORY"
# 		nodevices=0
# 		for fileTOI in filelisting:
# 			if fileTOI.endswith('TOI.xls'):
# 				targetTOIdevicename=fileTOI.replace('_TOI.xls','')
# 				if self.devicename==targetTOIdevicename:
# 					self.fullfilenameTOI = self.pathname_TOI+"/"+fileTOI				# form full devicename (path+devicename) of complex S-parameter file
# 					nodevices+=1
# 		if nodevices>1: raise ValueError('ERROR device not unique!')
# 		try: fTOI=open(self.fullfilenameTOI,'r')
# 		except:
# 			#print "WARNING from __readSpar in device_parameter_request.py: cannot open file: "
# 			self.fullfilenameTOI="cannot open file"
# 			return "NO FILE"
#
# 		TOIfilelines = [a for a in fTOI.read().splitlines()]             # sfilelines is a string array of the lines in the file
# 		for fileline in TOIfilelines:
# 			# get timestamp
# 			if "year" in fileline:
# 				self.TOI['year']=fileline.split('\t')[1].lstrip()
# 			elif "month" in fileline:
# 				self.TOI['month']=fileline.split('\t')[1].lstrip()
# 			elif "day" in fileline:
# 				self.TOI['day']=fileline.split('\t')[1].lstrip()
# 			elif "hour" in fileline:
# 				self.TOI['hour']=fileline.split('\t')[1].lstrip()
# 			elif "minute" in fileline:
# 				self.TOI['minute']=fileline.split('\t')[1].lstrip()
# 			elif "second" in fileline:
# 				self.TOI['second']=fileline.split('\t')[1].lstrip()
# 			# get devicename and location on wafer
# 			elif "wafer name" in fileline:
# 				self.wafer_name=fileline.split('\t')[1].lstrip()
# 			elif "device name" in fileline:
# 				self.devicename=fileline.split('\t')[1].lstrip()
# 				# now get the maskname of the device i.e. the portion of the device name which indicates the device's mask layout name
# 				devicename_maskC="".join(['C',self.devicename.split('__')[1].split('_C')[1]])
# 				devicename_maskR="".join(['R',self.devicename.split('__')[1].split('_R')[1]])
# 				if len(devicename_maskC)>=len(devicename_maskR): #
# 					self.devicename_TOImask=devicename_maskC
# 				else:
# 					self.devicename_TOImask=devicename_maskR
#
# 			elif "x location" in fileline:
# 				self.x_location=int(fileline.split('\t')[1].lstrip())
# 			elif "y location" in fileline:
# 				self.y_location=int(fileline.split('\t')[1].lstrip())
# 			elif "Vds" in fileline:
# 				self.TOI['Vds']=float(fileline.split('\t')[1].lstrip())
# 			elif "Id" in fileline:
# 				self.TOI['Id']=float(fileline.split('\t')[1].lstrip())*scalingfactor			# scale current to mA/mm if device width was given
# 			elif "drain status" in fileline:
# 				self.TOI['drainstatus']=fileline.split('\t')[1].lstrip()
# 			elif "Vgs" in fileline:
# 				self.TOI['Vgs']=float(fileline.split('\t')[1].lstrip())
# 			elif "Ig" in fileline:
# 				self.TOI['Ig']=float(fileline.split('\t')[1].lstrip())*scalingfactor			# scale current to mA/mm if device width was given
# 			elif "gate status" in fileline:
# 				self.TOI['gatestatus']=fileline.split('\t')[1].lstrip()
# 			elif "Center frequency in Hz" in fileline:
# 				self.TOI['centfreq']=float(fileline.split('\t')[1].lstrip().split('.')[0])
# 			elif "Frequency spacing between two tones in Hz" in fileline:
# 				self.TOI['freqspacing']=float(fileline.split('\t')[1].lstrip())
# 			elif "Resolution Bandwidth Hz for distortion products measurements" in fileline:
# 				self.TOI['resolutionbandwidth']=float(fileline.split('\t')[1].lstrip())
# 			elif "Noise Floor dBm for distortion products measurements" in fileline:
# 				self.TOI['noisefloor']=float(fileline.split('\t')[1].lstrip())
# 			elif "System TOI dBm" in fileline:
# 				self.TOI['sysTOI']=float(fileline.split('\t')[1].lstrip())
# 			elif "Lower frequency measured TOI dBm" in fileline:
# 				self.TOI['TOI_lower']=float(fileline.split('\t')[1].lstrip())
# 			elif "Upper frequency measured TOI dBm" in fileline:
# 				self.TOI['TOI_upper']=float(fileline.split('\t')[1].lstrip())
#
# 			elif "slope of linear fit of lower distortion tone" in fileline:
# 				self.TOI['lowerslope']=float(fileline.split('\t')[1].lstrip())
# 			elif "intercept of linear fit of lower distortion tone" in fileline:
# 				self.TOI['lowerintercept']=float(fileline.split('\t')[1].lstrip())
# 			elif "slope of linear fit of upper distortion tone" in fileline:
# 				self.TOI['upperslope']=float(fileline.split('\t')[1].lstrip())
# 			elif "intercept of linear fit of upper distortion tone" in fileline:
# 				self.TOI['upperintercept']=float(fileline.split('\t')[1].lstrip())
#
# 		self.TOI['reflect_mag']=col.deque()			# Magnitude of the output reflection coefficient
# 		self.TOI['reflect_ang']=col.deque()			# angle of the output reflection coefficient
# 		self.TOI['TOIout']=col.deque()			# average of the output 3rd order intercept point (dBm)
# 		self.TOI['TOIDUTgain']=col.deque()			# DUT gain in dB
#
# 		TOIvsreflectiondata=False
# 		for fileline in TOIfilelines:                                              # load lines from the data file
# 			if 'sorted averaged TOI' in fileline: TOIvsreflectiondata=True
# 			if TOIvsreflectiondata and not(('!' in fileline) or ('#' in fileline)):                       # then this line are data
# 				self.TOI['reflect_mag'].append(float(fileline.split()[1]))
# 				self.TOI['reflect_ang'].append(float(fileline.split()[2]))
# 				self.TOI['TOIout'].append(float(fileline.split()[3]))
# 				self.TOI['TOIDUTgain'].append(float(fileline.split()[4]))
# 		fTOI.close()
# 		self.TOI['reflect_mag_maxTOI']=self.TOI['reflect_mag'][self.TOI['TOIout'].index(max(self.TOI['TOIout']))]       # output reflection coefficient magnitude which gives the maximum TOI
# 		self.TOI['reflect_ang_maxTOI']=self.TOI['reflect_ang'][self.TOI['TOIout'].index(max(self.TOI['TOIout']))]       # output reflection coefficient angle degrees which gives the maximum TOI
# 		self.TOI['reflect_mag_maxgainTOI']=self.TOI['reflect_mag'][self.TOI['TOIDUTgain'].index(max(self.TOI['TOIDUTgain']))]   # output reflection coefficient magnitude which gives the maximum gain
# 		self.TOI['reflect_ang_maxgainTOI']=self.TOI['reflect_ang'][self.TOI['TOIDUTgain'].index(max(self.TOI['TOIDUTgain']))]   # output reflection coefficient angle degrees which gives the maximum gain
#
# 		self.TOI['TOIoutmax']=self.TOI['TOIout'][self.TOI['TOIout'].index(max(self.TOI['TOIout']))]     # maximum TOI
# 		self.TOI['TOImaxgain']=self.TOI['TOIDUTgain'][self.TOI['TOIDUTgain'].index(max(self.TOI['TOIDUTgain']))]    # max gain for TOI measurement
# 		self.TOI['DUTmaxgainTOI']=self.TOI['TOIDUTgain'][self.TOI['TOIout'].index(max(self.TOI['TOIout']))]     # Gain at maximum TOI
#
# 		try: self.parameters.append("SRI")											# we now have at complex S-parameters so set the indicator
# 		except:
# 			self.parameters = []
# 			self.parameters.append("SRI")
# 		return "success"
############################################################################################################################################################################
# Read third order intercept point data
#
	def __readTOI(self):
		if self.devwidth!=None: scalingfactor=self.unitsscaling/self.devwidth								# scale currents to mA/mm
		else: scalingfactor=1.
		self.pathname_TOI = self.pathname+sub("RF_power")
		try: filelisting = os.listdir(self.pathname_TOI)
		except: return "NO DIRECTORY"
		nodevices=0
		for fileTOI in filelisting:
			if fileTOI.endswith('TOI.xls'):
				targetTOIdevicename=fileTOI.replace('_TOI.xls','')
				if self.devicename==targetTOIdevicename:
					fullfilenameTOI = self.pathname_TOI+"/"+fileTOI				# form full devicename (path+devicename) of complex S-parameter file
					nodevices+=1
		if nodevices>1: raise ValueError('ERROR device not unique!')
		try: fTOI=open(fullfilenameTOI,'r')
		except:
			#print "WARNING from __readSpar in device_parameter_request.py: cannot open file: "
			fullfilenameTOI="cannot open file"
			return "NO FILE"

		TOIfilelines = [a for a in fTOI.read().splitlines()]             # sfilelines is a string array of the lines in the file
		for fileline in TOIfilelines:
			# get timestamp
			if "year" in fileline:
				self.TOI['year']=fileline.split('\t')[1].lstrip()
			elif "month" in fileline:
				self.TOI['month']=fileline.split('\t')[1].lstrip()
			elif "day" in fileline:
				self.TOI['day']=fileline.split('\t')[1].lstrip()
			elif "hour" in fileline:
				self.TOI['hour']=fileline.split('\t')[1].lstrip()
			elif "minute" in fileline:
				self.TOI['minute']=fileline.split('\t')[1].lstrip()
			elif "second" in fileline:
				self.TOI['second']=fileline.split('\t')[1].lstrip()
			# get devicename and location on wafer
			elif "wafer name" in fileline:
				self.wafer_name=fileline.split('\t')[1].lstrip()
			elif "device name" in fileline:
				self.devicename=fileline.split('\t')[1].lstrip()
				# now get the maskname of the device i.e. the portion of the device name which indicates the device's mask layout name
				# devicename_maskC="".join(['C',self.devicename.split('__')[1].split('_C')[1]])
				# devicename_maskR="".join(['R',self.devicename.split('__')[1].split('_R')[1]])
				# if len(devicename_maskC)>=len(devicename_maskR): #
				# 	self.devicename_TOImask=devicename_maskC
				# else:
				# 	self.devicename_TOImask=devicename_maskR

			elif "x location" in fileline:
				self.x_location=int(fileline.split('\t')[1].lstrip())
			elif "y location" in fileline:
				self.y_location=int(fileline.split('\t')[1].lstrip())
			elif "Vds" in fileline:
				self.TOI['Vds']=float(fileline.split('\t')[1].lstrip())
			elif "Id" in fileline:
				self.TOI['Id']=float(fileline.split('\t')[1].lstrip())*scalingfactor			# scale current to mA/mm if device width was given
			elif "drain status" in fileline:
				self.TOI['drainstatus']=fileline.split('\t')[1].lstrip()
			elif "Vgs" in fileline:
				self.TOI['Vgs']=float(fileline.split('\t')[1].lstrip())
			elif "Ig" in fileline:
				self.TOI['Ig']=float(fileline.split('\t')[1].lstrip())*scalingfactor			# scale current to mA/mm if device width was given
			elif "gate status" in fileline:
				self.TOI['gatestatus']=fileline.split('\t')[1].lstrip()
			elif "Center frequency in Hz" in fileline:
				self.TOI['centfreq']=float(fileline.split('\t')[1].lstrip().split('.')[0])
			elif "Frequency spacing between two tones in Hz" in fileline:
				self.TOI['freqspacing']=float(fileline.split('\t')[1].lstrip())
			elif "Resolution Bandwidth Hz for distortion products measurements" in fileline:
				self.TOI['resolutionbandwidth']=float(fileline.split('\t')[1].lstrip())
			elif "Noise Floor dBm for distortion products measurements" in fileline:
				self.TOI['noisefloor']=float(fileline.split('\t')[1].lstrip())
			elif "System TOI dBm" in fileline:
				self.TOI['sysTOI']=float(fileline.split('\t')[1].lstrip())
			elif "Lower frequency measured TOI dBm" in fileline:
				self.TOI['TOI_lower']=float(fileline.split('\t')[1].lstrip())
			elif "Upper frequency measured TOI dBm" in fileline:
				self.TOI['TOI_upper']=float(fileline.split('\t')[1].lstrip())

			elif "slope of linear fit of lower distortion tone" in fileline:
				self.TOI['lowerslope']=float(fileline.split('\t')[1].lstrip())
			elif "intercept of linear fit of lower distortion tone" in fileline:
				self.TOI['lowerintercept']=float(fileline.split('\t')[1].lstrip())
			elif "slope of linear fit of upper distortion tone" in fileline:
				self.TOI['upperslope']=float(fileline.split('\t')[1].lstrip())
			elif "intercept of linear fit of upper distortion tone" in fileline:
				self.TOI['upperintercept']=float(fileline.split('\t')[1].lstrip())

		#self.TOI['tunermotorposition']=col.deque()  # tuner motor tuner position
		self.TOI['reflect_mag']=col.deque()			# Magnitude of the output reflection coefficient at the best reflection coefficient for TOI
		self.TOI['reflect_ang']=col.deque()			# angle of the output reflection coefficient at the best reflection coefficient for TOI
		self.TOI['TOIout']=col.deque()			# maximum of the minimum TOI for all pairs of third order products. This represents the minimum of the pair of TOI values measured for the tuner position which
												# gives the highest TOI
		self.TOI['TOIDUTgain']=col.deque()			# associated DUT gain in dB for the output tuner position which gives the highest output TOI
# get TOI output reflection and gain data for all tested tuner impedances
		i=0
		while i<len(TOIfilelines):
			if "tuner motor position" in TOIfilelines[i].split('\t')[0]:        # data for a tuner position and impedance follow
				#self.TOI['tunermotorposition'].append(TOIfilelines[i].split('\t')[1])                              # tuner motor position
				self.TOI['reflect_mag'].append(TOIfilelines[i].split('\t')[3].split()[0])
				self.TOI['reflect_ang'].append(TOIfilelines[i].split('\t')[3].split()[1])
			elif "DUT gain" in TOIfilelines[i].split('\t')[0]:
				self.TOI['TOIDUTgain'].append(float(TOIfilelines[i].split('\t')[1]))
			elif "fundamental DUT input power dBm" in TOIfilelines[i].split('\t')[0]:
				i+=1        # get data from following line
				l=TOIfilelines[i].split('\t')
				self.TOI['TOIout'].append(min(float(l[4]),float(l[5])))     # get the minimum of the upper sideband and lower sideband output TOI
			i+=1
############

		# TOIvsreflectiondata=False
		# for fileline in TOIfilelines:                                              # load lines from the data file
		# 	if 'sorted averaged TOI' in fileline: TOIvsreflectiondata=True
		# 	if TOIvsreflectiondata and not(('!' in fileline) or ('#' in fileline)):                       # then this line are data
		# 		self.TOI['tunermotorposition'].append(fileline.split('\t')[0])                              # tuner motor position
		# 		self.TOI['reflect_mag'].append(float(fileline.split()[1]))
		# 		self.TOI['reflect_ang'].append(float(fileline.split()[2]))
		# 		self.TOI['TOIout'].append(float(fileline.split()[3]))                                   # average output TOI
		# 		self.TOI['TOIDUTgain'].append(float(fileline.split()[4]))                               # DUT gain a the given output reflection coefficient
		fTOI.close()
		self.TOI['reflect_mag_maxTOI']=self.TOI['reflect_mag'][self.TOI['TOIout'].index(max(self.TOI['TOIout']))]       # output reflection coefficient magnitude which gives the maximum TOI
		self.TOI['reflect_ang_maxTOI']=self.TOI['reflect_ang'][self.TOI['TOIout'].index(max(self.TOI['TOIout']))]       # output reflection coefficient angle degrees which gives the maximum TOI
		self.TOI['reflect_mag_maxgainTOI']=self.TOI['reflect_mag'][self.TOI['TOIDUTgain'].index(max(self.TOI['TOIDUTgain']))]   # output reflection coefficient magnitude which gives the maximum gain
		self.TOI['reflect_ang_maxgainTOI']=self.TOI['reflect_ang'][self.TOI['TOIDUTgain'].index(max(self.TOI['TOIDUTgain']))]   # output reflection coefficient angle degrees which gives the maximum gain

		self.TOI['TOIoutmax']=self.TOI['TOIout'][self.TOI['TOIout'].index(max(self.TOI['TOIout']))]     # maximum of the average upper and lower sideband TOI
		#self.TOI['motoratmaxTOI']=self.TOI['tunermotorposition'][self.TOI['TOIout'].index(max(self.TOI['TOIout']))]     # tuner motor position at maximum averaged TOI
		self.TOI['TOImaxgain']=self.TOI['TOIDUTgain'][self.TOI['TOIDUTgain'].index(max(self.TOI['TOIDUTgain']))]    # max gain for TOI measurement
		self.TOI['DUTmaxgainTOI']=self.TOI['TOIDUTgain'][self.TOI['TOIout'].index(max(self.TOI['TOIout']))]     # Associated Gain at maximum of the average USB,LSB TOI

		# self.TOI['TOIoutmaxmin']=len(self.TOI['TOIout'])*[None]                # Over all the output tuning points, take the minimum TOI
		# for fileline in TOIfilelines:
		# 	if ""

		try: self.parameters.append("TOI")											# we now have at complex S-parameters so set the indicator
		except:
			self.parameters = []
			self.parameters.append("TOI")
		return "success"
############################################################################################################################################################################
############################################################################################################################################################################
# Read third order intercept point data taken with swept Vgs
#
	def __readTOIVgsswept(self):
		if self.devwidth!=None: scalingfactor=self.unitsscaling/self.devwidth								# scale currents to mA/mm
		else: scalingfactor=1.
		self.pathname_TOI = self.pathname+sub("RF_power")
		try: filelisting = os.listdir(self.pathname_TOI)
		except: return "NO DIRECTORY"
		nodevices=0
		for fileTOI in filelisting:
			if fileTOI.endswith('TOIVgssweepsearch.xls'):
				targetTOIdevicename=fileTOI.replace('_TOIVgssweepsearch.xls','')
				if self.devicename==targetTOIdevicename:
					fullfilenameTOI = self.pathname_TOI+"/"+fileTOI				# form full devicename (path+devicename) of complex S-parameter file
					nodevices+=1
		if nodevices>1: raise ValueError('ERROR device not unique!')
		try: fTOI=open(fullfilenameTOI,'r')
		except:
			fullfilenameTOI="cannot open file"
			return "NO FILE"

		TOIfilelines = [a for a in fTOI.read().splitlines()]             # sfilelines is a string array of the lines in the file
		for fileline in TOIfilelines:
			# get timestamp
			if "year" in fileline:
				self.TOIVgsswept['year']=fileline.split('\t')[1].lstrip()
			elif "month" in fileline:
				self.TOIVgsswept['month']=fileline.split('\t')[1].lstrip()
			elif "day" in fileline:
				self.TOIVgsswept['day']=fileline.split('\t')[1].lstrip()
			elif "hour" in fileline:
				self.TOIVgsswept['hour']=fileline.split('\t')[1].lstrip()
			elif "minute" in fileline:
				self.TOIVgsswept['minute']=fileline.split('\t')[1].lstrip()
			elif "second" in fileline:
				self.TOIVgsswept['second']=fileline.split('\t')[1].lstrip()
			# get devicename and location on wafer
			elif "wafer name" in fileline:
				self.wafer_name=fileline.split('\t')[1].lstrip()
			elif "device name" in fileline:
				self.devicename=fileline.split('\t')[1].lstrip()

			elif "x location" in fileline:
				self.x_location=int(fileline.split('\t')[1].lstrip())
			elif "y location" in fileline:
				self.y_location=int(fileline.split('\t')[1].lstrip())
			elif "Vds" in fileline:
				self.TOIVgsswept['Vds']=float(fileline.split('\t')[1].lstrip())
			elif "Center frequency in Hz" in fileline:
				self.TOIVgsswept['centfreq']=float(fileline.split('\t')[1].lstrip().split('.')[0])
			elif "Frequency spacing between two tones in Hz" in fileline:
				self.TOIVgsswept['freqspacing']=float(fileline.split('\t')[1].lstrip())
			elif "Resolution Bandwidth Hz for distortion products measurements" in fileline:
				self.TOIVgsswept['resolutionbandwidth']=float(fileline.split('\t')[1].lstrip())
			elif "Gate sweep period" in fileline:       # gate sweep period in seconds
				self.TOIVgsswept['gatesweepperiod']=float(fileline.split('\t')[1].lstrip())
			elif "Max overall TOI-Pdc (dB)" in fileline:
				self.TOIVgsswept['Max_TOI-Pdc']=float(fileline.split('\t')[1].lstrip())

		self.TOIVgsswept['reflect_mag']=col.deque()			# Magnitude of the output reflection coefficient  for TOI
		self.TOIVgsswept['reflect_ang']=col.deque()			# angle of the output reflection coefficient for TOI
		self.TOIVgsswept['TOIout']=col.deque()			# maximum of the minimum TOI for all pairs of third order products vs output reflection coefficient
		self.TOIVgsswept['TOIgain']=col.deque()			# associated DUT gain in dB vs output reflection coefficient

		self.TOIVgsswept['timestamps']=col.deque()
		self.TOIVgsswept['Vgs_time']=col.deque()
		self.TOIVgsswept['Id_time']=col.deque()
		self.TOIVgsswept['pfund_time']=col.deque()
		self.TOIVgsswept['p3rdlower_time']=col.deque()
		self.TOIVgsswept['p3rdupper_time']=col.deque()
		self.TOIVgsswept['TOIlower_time']=col.deque()
		self.TOIVgsswept['TOIupper_time']=col.deque()
		self.TOIVgsswept['TOI_time']=col.deque()
		self.TOIVgsswept['TOIgain_time']=col.deque()
		self.TOIVgsswept['TOI-Pdc_time']=col.deque()

			# best measured TOI data for this device over the range of tested output reflection coefficients
		i=0
		while True:
			if "parameters vs output reflection coefficient" in TOIfilelines[i]: break
			i+=1
		startline=i+2
		i=startline
		while("!" not in TOIfilelines[i] and len(TOIfilelines[i])>0):          # now read maximum TOIs vs output reflection coefficients
			self.TOIVgsswept['reflect_mag'].append(TOIfilelines[i].split('\t')[1].split()[0])
			self.TOIVgsswept['reflect_ang'].append(TOIfilelines[i].split('\t')[1].split()[1])
			self.TOIVgsswept['TOIout'].append(TOIfilelines[i].split('\t')[2])
			self.TOIVgsswept['TOIgain'].append(TOIfilelines[i].split('\t')[3])
			i+=1
		startline=i
		# get maximum TOI vs output reflection coefficient - this is the last entry of TOI vs output reflection coefficient listing
		self.TOIVgsswept['reflect_mag_maxTOI']=self.TOIVgsswept['reflect_mag'][-1]  # output reflection coefficient magnitude which maximizes the maximum output TOI over gate sweep
		self.TOIVgsswept['reflect_ang_maxTOI']=self.TOIVgsswept['reflect_ang'][-1]  # output reflection coefficient angle which maximizes the maximum output TOI over gate sweep
		self.TOIVgsswept['TOImax']=self.TOIVgsswept['TOIout'][-1]                         # output TOI which is maximum for both all the measured tuning positions and the Vgs sweep
		self.TOIVgsswept['gainatmaxTOI']=self.TOIVgsswept['TOIgain'][-1]                     # associated gain for self.TOIVgsswept['TOImax']
# now read TOI data vs time for the Vgs sweep
		for i in range(startline,len(TOIfilelines)):
			if "!" not in TOIfilelines[i] and len(TOIfilelines[i])>0:
				self.TOIVgsswept['timestamps'].append(float(TOIfilelines[i].split('\t')[0]))
				self.TOIVgsswept['Vgs_time'].append(float(TOIfilelines[i].split('\t')[1]))
				self.TOIVgsswept['Id_time'].append(float(TOIfilelines[i].split('\t')[2]))
				self.TOIVgsswept['pfund_time'].append(float(TOIfilelines[i].split('\t')[3]))
				self.TOIVgsswept['p3rdupper_time'].append(float(TOIfilelines[i].split('\t')[4]))
				self.TOIVgsswept['p3rdlower_time'].append(float(TOIfilelines[i].split('\t')[5]))
				self.TOIVgsswept['TOIupper_time'].append(float(TOIfilelines[i].split('\t')[6]))
				self.TOIVgsswept['TOIlower_time'].append(float(TOIfilelines[i].split('\t')[7]))
				self.TOIVgsswept['TOI_time'].append(float(TOIfilelines[i].split('\t')[8]))
				self.TOIVgsswept['TOIgain_time'].append(float(TOIfilelines[i].split('\t')[9]))
				try: self.TOIVgsswept['TOI-Pdc_time'].append(float(TOIfilelines[i].split('\t')[10]))
				except:         # must calculate TOI-Pdc because earlier versions of data save didn't calculate this directly
					self.TOIVgsswept['TOI-Pdc_time'].append(self.TOIVgsswept['TOI_time'][-1]-10*np.log10(self.TOIVgsswept['Id_time'][-1]*self.TOIVgsswept['Vds'])-30.)

		fTOI.close()
		if 'Max_TOI-Pdc' not in self.TOIVgsswept.keys():                # for backward compatibility of older software then must read maximum TOI-Pdc from data vs time at optimum gamma
			self.TOIVgsswept['Max_TOI-Pdc']=str(max([float(p) for p in self.TOIVgsswept['TOI-Pdc_time']]))
		try: self.parameters.append("TOIvsswept")											# we now have at complex S-parameters so set the indicator
		except:
			self.parameters = []
			self.parameters.append("TOIvsswept")
		return "success"
############################################################################################################################################################################


############################################################################################################################################################################
# Read compression data
#
	def __readCOMPRESS(self):
		if self.devwidth!=None: scalingfactor=self.unitsscaling/self.devwidth								# scale currents to mA/mm
		else: scalingfactor=1.
		self.pathname_COMPRESS = self.pathname+sub("RF_power")
		try: filelisting = os.listdir(self.pathname_COMPRESS)
		except: return "NO DIRECTORY"
		nodevices=0
		for fileCOMPRESS in filelisting:
			if fileCOMPRESS.endswith('PCOMPRESS.xls'):
				targetCOMPRESSdevicename=fileCOMPRESS.replace('_PCOMPRESS.xls','')
				if self.devicename==targetCOMPRESSdevicename:
					self.fullfilenameCOMPRESS = self.pathname_COMPRESS+"/"+fileCOMPRESS				# form full devicename (path+devicename) of complex S-parameter file
					nodevices+=1
		if nodevices>1: raise ValueError('ERROR device not unique!')
		try: fCOMPRESS=open(self.fullfilenameCOMPRESS,'r')
		except:
			#print "WARNING from __readSpar in device_parameter_request.py: cannot open file: "
			self.fullfilenameCOMPRESS="cannot open file"
			return "NO FILE"

		COMPRESSfilelines = [a for a in fCOMPRESS.read().splitlines()]             # sfilelines is a string array of the lines in the file
		for fileline in COMPRESSfilelines:
			# get timestamp
			if "year" in fileline:
				self.COMPRESS['year']=fileline.split('\t')[1].lstrip()
			elif "month" in fileline:
				self.COMPRESS['month']=fileline.split('\t')[1].lstrip()
			elif "day" in fileline:
				self.COMPRESS['day']=fileline.split('\t')[1].lstrip()
			elif "hour" in fileline:
				self.COMPRESS['hour']=fileline.split('\t')[1].lstrip()
			elif "minute" in fileline:
				self.COMPRESS['minute']=fileline.split('\t')[1].lstrip()
			elif "second" in fileline:
				self.COMPRESS['second']=fileline.split('\t')[1].lstrip()
			# get devicename and location on wafer
			elif "wafer name" in fileline:
				self.wafer_name=fileline.split('\t')[1].lstrip()
			elif "device name" in fileline:
				self.devicename=fileline.split('\t')[1].lstrip()
				# now get the maskname of the device i.e. the portion of the device name which indicates the device's mask layout name
				devicename_maskC="".join(['C',self.devicename.split('__')[1].split('_C')[1]])
				devicename_maskR="".join(['R',self.devicename.split('__')[1].split('_R')[1]])
				if len(devicename_maskC)>=len(devicename_maskR): #
					self.devicename_COMPRESSmask=devicename_maskC
				else:
					self.devicename_COMPRESSmask=devicename_maskR

			elif "x location" in fileline:
				self.x_location=int(fileline.split('\t')[1].lstrip())
			elif "y location" in fileline:
				self.y_location=int(fileline.split('\t')[1].lstrip())
			elif "Vds" in fileline:
				self.COMPRESS['Vds']=float(fileline.split('\t')[1].lstrip())
			elif "Id" in fileline:
				self.COMPRESS['Id']=float(fileline.split('\t')[1].lstrip())*scalingfactor			# scale current to mA/mm if device width was given
			elif "drain status" in fileline:
				self.COMPRESS['drainstatus']=fileline.split('\t')[1].lstrip()
			elif "Vgs" in fileline:
				self.COMPRESS['Vgs']=float(fileline.split('\t')[1].lstrip())
			elif "Ig" in fileline:
				self.COMPRESS['Ig']=float(fileline.split('\t')[1].lstrip())*scalingfactor			# scale current to mA/mm if device width was given
			elif "gate status" in fileline:
				self.COMPRESS['gatestatus']=fileline.split('\t')[1].lstrip()
			# elif "Center frequency in Hz" in fileline:
			# 	self.COMPRESS['centfreq']=float(fileline.split('\t')[1].lstrip().split('.')[0])



		self.COMPRESS['reflect_mag']=[]			# Magnitude of the output reflection coefficient at the best reflection coefficient for COMPRESS
		self.COMPRESS['reflect_ang']=[]			# angle of the output reflection coefficient at the best reflection coefficient for COMPRESS
		self.COMPRESS['Pin']=[]               # input power (spline fit) vs input power for compression test in dBm
		self.COMPRESS['Pout']=[]			# output power (spline fit) vs input power for compression test in dBm
		self.COMPRESS['gain']=[]           # gain (dB) vs input power

# get compression output reflection and gain data for all tested tuner impedances
		readcompressdata=False
		for l in COMPRESSfilelines:
			if "tuner motor position" in l.split('\t')[0]:        # data for a tuner position and impedance follow
				self.COMPRESS['reflect_mag'].append(l.split('\t')[3].split()[0])
				self.COMPRESS['reflect_ang'].append(l.split('\t')[3].split()[1])
			elif "Spline fit" in l.split('\t')[0]:           # we are reaching compression spline fit data
				readcompressdata=True
			if readcompressdata and "!" not in l.split('\t')[0]:              # then we have reached split fit data
				Pin=float(l.split('\t')[0])
				self.COMPRESS['Pin'].append(Pin)
				Pout=float(l.split('\t')[1])
				self.COMPRESS['Pout'].append(Pout)
				gain=float(l.split('\t')[2])
				self.COMPRESS['gain'].append(gain)
		fCOMPRESS.close()

		# now find 1dB compression input and output power levels
		index_maxgain=np.argmax(self.COMPRESS['gain'])
		self.COMPRESS['maxgain']=self.COMPRESS['gain'][index_maxgain]          # maximum small-signal gain for compression power sweep
		# find 1dB compression point
		index1dB=np.argmax(np.array(self.COMPRESS['gain'][index_maxgain:])<(self.COMPRESS['maxgain']-1.))+index_maxgain            # find index point of 1dB compression
		if index1dB==index_maxgain:
			self.COMPRESS['COMPRESSout']=None
			return "fail"
		else:
			self.COMPRESS['COMPRESSout']=self.COMPRESS['Pout'][index1dB]        # output power at 1dB gain compression


			try: self.parameters.append("COMPRESS")											# we now have compression data
			except:
				self.parameters = []
				self.parameters.append("COMPRESS")
			return "success"
############################################################################################################################################################################
############################################################################################################################################################################
# Read harmonic distortion data
#
	def __readHARM(self):
		if self.devwidth!=None: scalingfactor=self.unitsscaling/self.devwidth								# scale currents to mA/mm
		else: scalingfactor=1.
		pathname = self.pathname+sub("RF_power")
		try: filelisting = os.listdir(pathname)
		except: return "NO DIRECTORY"
		nodevices=0
		for f in filelisting:
			if f.endswith('harmdistortion.xls'):
				targetdevicename=f.replace('_harmdistortion.xls','')
				if self.devicename==targetdevicename:
					fullfilename = pathname+"/"+f				# form full devicename (path+devicename) of complex S-parameter file
					nodevices+=1
		if nodevices>1: raise ValueError('ERROR device not unique!')
		try: ff=open(fullfilename,'r')
		except:
			return "NO FILE"

		lines = [a for a in ff.read().splitlines()]             # sfilelines is a string array of the lines in the file
		ff.close()
		for fl in lines:
			# get timestamp
			if "year" in fl:
				self.HARM['year']=fl.split('\t')[1].lstrip()
			elif "month" in fl:
				self.HARM['month']=fl.split('\t')[1].lstrip()
			elif "day" in fl:
				self.HARM['day']=fl.split('\t')[1].lstrip()
			elif "hour" in fl:
				self.HARM['hour']=fl.split('\t')[1].lstrip()
			elif "minute" in fl:
				self.HARM['minute']=fl.split('\t')[1].lstrip()
			elif "second" in fl:
				self.HARM['second']=fl.split('\t')[1].lstrip()
			# get devicename and location on wafer
			elif "wafer name" in fl:
				self.wafer_name=fl.split('\t')[1].lstrip()
			elif "device name" in fl:
				self.devicename=fl.split('\t')[1].lstrip()
				# now get the maskname of the device i.e. the portion of the device name which indicates the device's mask layout name
				devicename_maskC="".join(['C',self.devicename.split('__')[1].split('_C')[1]])
				devicename_maskR="".join(['R',self.devicename.split('__')[1].split('_R')[1]])
				if len(devicename_maskC)>=len(devicename_maskR): #
					self.devicename_HARMmask=devicename_maskC
				else:
					self.devicename_HARMmask=devicename_maskR

			elif "x location" in fl:
				self.x_location=int(fl.split('\t')[1].lstrip())
			elif "y location" in fl:
				self.y_location=int(fl.split('\t')[1].lstrip())
			elif "Vds" in fl:
				self.HARM['Vds']=float(fl.split('\t')[1].lstrip())
			elif "Id" in fl:
				self.HARM['Id']=float(fl.split('\t')[1].lstrip())*scalingfactor			# scale current to mA/mm if device width was given
			elif "drain status" in fl:
				self.HARM['drainstatus']=fl.split('\t')[1].lstrip()
			elif "Vgs" in fl:
				self.HARM['Vgs']=float(fl.split('\t')[1].lstrip())
			elif "Ig" in fl:
				self.HARM['Ig']=float(fl.split('\t')[1].lstrip())*scalingfactor			# scale current to mA/mm if device width was given
			elif "gate status" in fl:
				self.HARM['gatestatus']=fl.split('\t')[1].lstrip()
			elif "Fundamental frequency" in fl:
				self.HARM['frequency']=1E6*float(fl.split('\t')[1].lstrip())                   # fundamental frequency (single-tone) in MHz converted to Hz
			elif "Fundamental DUT power input dBm" in fl:
				self.HARM['Pin']=float(fl.split('\t')[1].lstrip())                   # input RF power (dBm)




		self.HARM['Vgs']=[]               # gate voltage array used in harmonic measurement
		self.HARM['Id']=[]               # drain current (mA/mm) vs Vgs
		self.HARM['Ig']=[]               # gate current (mA/mm) vs Vgs
		self.HARM['gain']=[]                # DUT gain harmonic measurement vs Vgs
		self.HARM['Pout']=[]			# output fundamental power in dBm vs Vgs
		self.HARM['P3out']=[]           # output third harmonic power in dBm vs Vgs
		self.HARM['P2out']=[]           # output 2nd harmonic power in dBm vs Vgs
		self.HARM['gain']=[]           # gain (dB) vs Vgs
		self.HARM['TOI']=[]             # third order intercept point calculated from third harmonic measurement vs Vgs
		self.HARM['gatestatus']=[]      # gate status vs Vgs
		self.HARM['drainstatus']=[]     # drain status vs Vgs
		self.HARM['noisefund']=[]         # noise floor at fundamental frequency at measurement bandwidth (dBm) vs Vgs
		self.HARM['noise3rd']=[]         # noise floor at 3rd harmonic frequency at measurement bandwidth (dBm) vs Vgs

# get harmonic data for all values of Vgs
		readdata=False
		for fl in lines:
			if "Gain" in fl: readdata=True      # lines following this line contain measured data
			if readdata and not ("!" in fl):    # then we have reached data
				self.HARM['noisefund'].append(float(fl.split('\t')[8]))
				self.HARM['noise3rd'].append(float(fl.split('\t')[9]))
				self.HARM['Vgs'].append(float(fl.split('\t')[0]))
				self.HARM['gain'].append(float(fl.split('\t')[1]))
				Pout=float(fl.split('\t')[2])
				if Pout-self.HARM['noisefund'][-1]>minimumabovenoisefloor:      # is this above the noise floor?
					self.HARM['Pout'].append(Pout)
				else:
					self.HARM['Pout'].append(-999)
				self.HARM['P2out'].append(float(fl.split('\t')[3]))
				P3out=float(fl.split('\t')[4])
				if P3out-self.HARM['noise3rd']>minimumabovenoisefloor:
					self.HARM['P3out'].append(P3out)
				else:
					self.HARM['P3out'].append(-999)
				TOI=float(fl.split('\t')[7])
				if self.HARM['Pout'][-1]!=-999 and self.HARM['P3out']!=-999:
					self.HARM['TOI'].append(TOI)
				else:
					self.HARM['TOI'].append(-999)

				self.HARM['Id'].append(scalingfactor*float(fl.split('\t')[11]))      # mA/mm if gate width given otherwise A
				self.HARM['Ig'].append(scalingfactor*float(fl.split('\t')[12]))     # mA/mm if gate width given otherwise A
				self.HARM['drainstatus'].append(float(fl.split('\t')[13]))
				self.HARM['gatestatus'].append(float(fl.split('\t')[14]))


		# find maximum TOI calculated from 3rd harmonic measurement
		indexmaxTOI=np.argmax(self.HARM['TOI'])            # find index point of 1dB compression
		self.HARM['TOImax']=self.HARM['TOI'][indexmaxTOI]       # maximum of TOI from TOI vs Vgs
		self.HARM['VgsTOImax']=self.HARM['Vgs'][indexmaxTOI]       # Vgs which gives the maximum TOI
		self.HARM['gainTOImax']=self.HARM['gain'][indexmaxTOI]       # DUT gain at the maximum TOI
		self.HARM['IdTOImax']=self.HARM['Id'][indexmaxTOI]       # Id at the maximum TOI
		self.HARM['IgTOImax']=self.HARM['Id'][indexmaxTOI]       # Ig at the maximum TOI

		try: self.parameters.append("HARM")											# we now have harmonic data
		except:
			self.parameters = []
			self.parameters.append("HARM")
		return "success"
############################################################################################################################################################################
############################################################################################################################################################################
#
###############################################################################################################################################################################################################
# DC parameters reading
###############################################################################################################################################################################################################
########################################################################################################################################################################################
# read family of curves parameters
########################################################################################################################################################################################
# IV family of curves time stamp from measured data
	def time_foc(self):																# get the timestamp for the family of curves
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No IV family of curves loaded must read from file
			self.__readIVfoc()					#  read IV family of curves from the file
		if not("IVfoc" in self.parameters):	# then must read in measured IV family of curves data
			self.__readIVfoc()					#  read IV family of curves from the file
		try: self.IVfoc_year
		except: return []
		return self.IVfoc_year,self.IVfoc_month,self.IVfoc_day,self.IVfoc_hour,self.IVfoc_minute,self.IVfoc_second
########################################################################################################################################################################################
# IV family of curves drain current array from measured data
	def IdIV_foc(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No IV family of curves loaded must read from file
			self.__readIVfoc()					#  read IV family of curves from the file
		if not("IVfoc" in self.parameters):	# then must read in measured IV family of curves data
			self.__readIVfoc()					#  read IV family of curves from the file
		try: self.Id_IVfoc
		except: return []
		return self.Id_IVfoc
########################################################################################################################################################################################
# IV family of curves gate current array from measured data
	def IgIV_foc(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No IV family of curves loaded must read from file
			self.__readIVfoc()					#  read IV family of curves from the file
		if not("IVfoc" in self.parameters):	# then must read in measured IV family of curves data
			self.__readIVfoc()					#  read IV family of curves from the file
		try: self.Ig_IVfoc
		except: return []
		return self.Ig_IVfoc
########################################################################################################################################################################################
# IV family of curves drain voltage array from measured data
	def VdsIV_foc(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No IV family of curves loaded must read from file
			self.__readIVfoc()					#  read IV family of curves from the file
		if not("IVfoc" in self.parameters):	# then must read in measured IV family of curves data
			self.__readIVfoc()					#  read IV family of curves from the file
		try: self.Vds_IVfoc
		except: return []
		return self.Vds_IVfoc
########################################################################################################################################################################################
# IV family of curves gate voltage array from measured data
	def VgsIV_foc(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No IV family of curves loaded must read from file
			self.__readIVfoc()					#  read IV family of curves from the file
		if not("IVfoc" in self.parameters):	# then must read in measured IV family of curves data
			self.__readIVfoc()					#  read IV family of curves from the file
		try: self.Vgs_IVfoc
		except: return []
		return self.Vgs_IVfoc
########################################################################################################################################################################################
# IV family of curves drain status array from measured data
	def drainstatus_foc(self):
		if not hasattr(self,'Id_IVfoc'): self.__readIVfoc()					#  read IV family of curves from the file
		try: self.drainstatus_IVfoc
		except: return []
		return self.drainstatus_IVfoc
########################################################################################################################################################################################
# IV family of curves gate status array from measured data
	def gatestatus_foc(self):
		# TODO: Big time sink here need to eliminate unnecessary repeat calculations
		if not hasattr(self,'Id_IVfoc'): self.__readIVfoc()		# No IV family of curves loaded must read from file
		try: self.gatestatus_IVfoc
		except: return []
		return self.gatestatus_IVfoc
########################################################################################################################################################################################
# obtain gm Id(Vgs), Y, Rc, etc... from the family of curves (foc) data
# this data is basically from Id vs Vgs at all the values of Vds measured in the foc
	def __calc_IdVgsfoc(self,*args):
		if len(args)>0:
			fcalc = args[0]								# optional flag to force calculation
		else: fcalc=""
		r=self.__readIVfoc()								#  read IV family of curves from the file if necessary
		if not("IVfoc" in self.parameters):												# can we even get the transfer curve parameters?
			return r
		if ("IdVgsfoc" not in self.parameters) or fcalc=="force calculation": 			# then must calculate parameters
			# need to first form 2-dimensional arrays having the Vgs and Vds indices reversed from those of the measured foc values

			# note that each return value is a list with each point corresponding to a gate voltage in the family of curves with id the drain voltage index
			# the return values are indexed e.g. self.Rcfrom_foc[id] where id is the drain voltage index
			ret = [find_Vth_Rc_gm(swapindex(self.Vds_IVfoc)[id][0],swapindex(self.Id_IVfoc)[id],swapindex(self.Vgs_IVfoc)[id],self.order,self.fractVgsfit,self.nopts_polyfit_foc) for id in range(0,len(self.Vgs_IVfoc[0])) if abs(self.Vds_IVfoc[0][id])>epsilon]
			self.Rcfrom_foc =[]
			self.Vth_Yfrom_foc = []
			# Vth_Idfrom_foc=[]
			self.Idfitfrom_foc=[]
			#Idlinfrom_foc
			self.Idleakfrom_foc=[]
			self.Idminfrom_foc=[]
			self.VgsIdleakfrom_foc=[]
			self.VgsIdminfrom_foc=[]
			self.Idmaxfrom_foc=[]
			self.VgsIdmaxfrom_foc=[]
			self.Idonoffratiofrom_foc=[]
			self.gmfrom_foc=[]
			self.Yffrom_foc=[]
			self.Yflinfrom_foc=[]
			self.Vgsfitfrom_foc=[]
			for id in range(0,len(ret)):
				self.Rcfrom_foc.append(ret[id][0])
				self.Vth_Yfrom_foc.append(ret[id][1])
				self.Idfitfrom_foc.append(ret[id][3])
				self.Idleakfrom_foc.append(ret[id][5])
				self.Idminfrom_foc.append(ret[id][6])
				self.VgsIdleakfrom_foc.append(ret[id][7])
				self.VgsIdminfrom_foc.append(ret[id][8])
				self.Idmaxfrom_foc.append(ret[id][9])
				self.VgsIdmaxfrom_foc.append(ret[id][10])
				self.Idonoffratiofrom_foc.append(ret[id][11])
				self.gmfrom_foc.append(ret[id][12])
				self.Yffrom_foc.append(ret[id][13])
				self.Yflinfrom_foc.append(ret[id][14])
				self.Vgsfitfrom_foc.append(ret[id][15])
			self.gmmaxfrom_foc =[max(self.gmfrom_foc[id]) for id in range(0,len(self.gmfrom_foc))]				# get the maximum positive value of gm
			if ("IdVgsfoc" not in self.parameters): self.parameters+="IdVgsfoc"
########################################################################################################################################################################################
# return values calculated from the IV family of curves measurements
# estimate of contact resistance from Y-function at low Vds and vs Vgs. Return values are 1-D arrays Rc[id] and Vds[id] for all effectively nonzero Vds
# Note that the return data is indexed data[id] where id is the drain voltage index
# Vds[id] is the array of drain voltages from the IV family of curves for all abs(Vds[id])> eps i.e. Vds points very near zero are excluded
# Rc_foc['R'] is the array of

	def Rc_foc(self):
		self.__calc_IdVgsfoc()
		try: self.Rcfrom_foc
		except: return {}
		return {'Vds': [self.Vds_IVfoc[0][id] for id in range(0,len(self.Vds_IVfoc[0])) if abs(self.Vds_IVfoc[0][id])>epsilon], 'R':self.Rcfrom_foc} # avoid Vds = 0 point
########################################################################################################################################################################################
# return values from the IV family of curves measurements
# estimate of threshold voltage from Y-function at low Vds and vs Vgs.
# Note that the return data is indexed data[id] where id is the drain voltage index
	def VthY_foc(self):
		self.__calc_IdVgsfoc()
		try: self.Vth_Yfrom_foc
		except: return {}
		return {'Vds': [self.Vds_IVfoc[0][id] for id in range(0,len(self.Vds_IVfoc[0])) if abs(self.Vds_IVfoc[0][id])>epsilon], 'V':self.Vth_Yfrom_foc} # avoid Vds = 0 point
########################################################################################################################################################################################
# return values from the IV family of curves measurements
# leakage drain current i.e. Idfit where |Idfit| is a minimum from polynomal fit of measured Id. Array size is same as the number of Vds values in the IV foc
# Note that the return data are indexed self.VgsIdleakfrom_foc[id] and  Idleakfrom_foc[id] where id is the drain voltage index
	def Idleak_foc(self):
		self.__calc_IdVgsfoc()
		try: self.Idleakfrom_foc
		except: return {}
		return {'Vgs':self.VgsIdleakfrom_foc, 'I':self.Idleakfrom_foc}
########################################################################################################################################################################################
# get maximum absolute value of the drain current at all gate and drain voltages measured in family of curves for this device if no Vds is given
# If we specify Vds then get the maximum absolute value of the |drain current| at the minimum Vgs (for p-type FETs) or maximum Vgs (for n-type FETs) closest to the specified drain voltage measured in family of curves for this device
	def Idmax_foc(self,devicetype='p',Vds=None):

		if Vds==None:
			if len(self.IdIV_foc())>0:
				self.Idmaxfoc_Vds = np.max(np.abs(self.IdIV_foc()))
				return self.Idmaxfoc_Vds
			else:
				self.Idmaxfoc_Vds=None
				return None
		else:
			Vds=float(Vds)
			if not hasattr(self,'VdsatIdmax') or not hasattr(self,'Idmaxfoc_Vds') or Vds!=self.VdsatIdmax_foc:      # recalculate ONLY if Vds has changed
				self.VdsatIdmax_foc=Vds

				self.__readIVfoc()          # read IV family of curves if we don't already have it
				if not hasattr(self,'Id_IVfoc'):
					self.Idmaxfoc_Vds=None
					return None
				if devicetype.lower()=='p':     # p-type FET
					iVgs=min(range(len(self.Vgs_IVfoc)), key=lambda i: self.Vgs_IVfoc[i][0]) # find the index of the minimum gate voltage (maximum turn-on of FET)
				elif devicetype.lower()=='n':   # n-type FET
					iVgs=max(range(len(self.Vgs_IVfoc)), key=lambda i: self.Vgs_IVfoc[i][0]) # find the index of the maximum gate voltage (maximum turn-on of FET)
				else: raise ValueError("ERROR! invalid devicetype")

				Vdsdiff=np.diff(self.Vds_IVfoc[iVgs])
				Vdsdiffmed=np.median(Vdsdiff)
				if Vdsdiffmed<0. and np.all([d<0. for d in Vdsdiff]):        # Vds trends negative
					Vdsd=np.flipud(self.Vds_IVfoc[iVgs])
					Idd=np.flipud(self.Id_IVfoc[iVgs])
					if len(Vdsd)<4:
						self.Idmaxfoc_Vds=None
						return None
					#IdvsVdsfunc=UnivariateSpline(Vdsd,Idd, k=3)
					IdvsVdsfunc=interp1d(Vdsd,Idd,kind='cubic')
				elif Vdsdiffmed>0. and np.all([d>0. for d in Vdsdiff]):     # Vds trends positive
					Vdsd=np.flipud(self.Vds_IVfoc[iVgs])
					Idd=np.flipud(self.Id_IVfoc[iVgs])
					if len(Vdsd)<4:
						self.Idmaxfoc_Vds=None
						return None
					#IdvsVdsfunc=UnivariateSpline(Vdsd,Idd, k=3)
					IdvsVdsfunc=interp1d(Vdsd,Idd,kind='cubic')
				else:
					self.Idmaxfoc_Vds=None
					return None
				#print("from line 1347 in device_parameter_request.py ",Vds)
				if Vds>max(self.Vds_IVfoc[iVgs]) or Vds<min(self.Vds_IVfoc[iVgs]):      # then requested Vds is outside of measured range so result is invalid
					self.Idmaxfoc_Vds=None
					return None
				self.Idmaxfoc_Vds=abs(IdvsVdsfunc(Vds))
			return self.Idmaxfoc_Vds        # return absolute value of maximum drain current at the maximum FET gate turn-on and the given drain voltage Vds This is from the interpolated IV curve

########################################################################################################################################################################################
# return values from the IV family of curves measurements
# On-off Id ratio i.e. maximum Id/minimum |Idfit| vs Vgs from polynomal fit of Id. Array size is same as the number of Vds values in the IV foc
# Note that the return data are indexed self.VgsIdminfrom_foc[id], self.VgsIdmaxfrom_foc[id] and  Idonoffratiofrom_foc[id] where id is the drain voltage index
#	WARNING! NOTE that this is calculated using the polynomial fit of the measured Id for Imax and the MEASURED value of Id for the Imin
	def Idonoffratio_foc(self):
		self.__calc_IdVgsfoc()
		try: self.Idonoffratiofrom_foc
		except: return {}
		return {'VgsIdleak':self.VgsIdleakfrom_foc,'VgsIdmax':self.VgsIdmaxfrom_foc, 'Ir':self.Idonoffratiofrom_foc}
########################################################################################################################################################################################
# return values from the IV family of curves measurements
# maximum gm calculated from family of curves. Array size is same as the number of Vds values in the IV foc
# Note that the return data is indexed data[id] where id is the drain voltage index
	def gmmax_foc(self):
		self.__calc_IdVgsfoc()
		try: self.gmmaxfrom_foc
		except: return {}
		return {'Vds': [self.Vds_IVfoc[0][id] for id in range(0,len(self.Vds_IVfoc[0])) if abs(self.Vds_IVfoc[0][id])>epsilon], 'G':self.gmmaxfrom_foc}
########################################################################################################################################################################################
# return values from the IV family of curves measurements
# gm calculated from family of curves
# Note that the return data is indexed data[id][ig] where id and ig are the drain and gate voltage indices respectively
	def gm_foc(self):
		self.__calc_IdVgsfoc()
		try: self.gmfrom_foc
		except: return {}
		return {'Vds': [self.Vds_IVfoc[0][id] for id in range(0,len(self.Vds_IVfoc[0])) if abs(self.Vds_IVfoc[0][id])>epsilon], 'Vgs':self.Vgsfitfrom_foc, 'G':self.gmfrom_foc}
########################################################################################################################################################################################
# return values from the IV family of curves measurements
# Y function calculated from family of curves
# Note that the return data is indexed data[id][ig] where id and ig are the drain and gate voltage indices respectively
	def Yf_foc(self):
		self.__calc_IdVgsfoc()
		try: self.Yffrom_foc
		except: return {}
		return {'Vds': [self.Vds_IVfoc[0][id] for id in range(0,len(self.Vds_IVfoc[0])) if abs(self.Vds_IVfoc[0][id])>epsilon], 'Vgs':self.Vgsfitfrom_foc[0], 'Y':self.Yffrom_foc}
########################################################################################################################################################################################
# return values from the IV family of curves measurements
# polynomial smoothed and fit Id calculated from family of curves.
# Note that the return data is indexed data[id][ig] where id and ig are the drain and gate voltage indices respectively
# value at Vds=0 has been eliminated
	def Idfit_foc(self):
		self.__calc_IdVgsfoc()
		try: self.Idfitfrom_foc
		except: return {}
		return {'Vds': [self.Vds_IVfoc[0][id] for id in range(0,len(self.Vds_IVfoc[0])) if abs(self.Vds_IVfoc[0][id])>epsilon],'Vgs':self.Vgsfitfrom_foc[0], 'I':self.Idfitfrom_foc}
########################################################################################################################################################################################
# return values from the IV family of curves measurements
# Id[iVds][iVgs] unsmoothed raw measured data from the IV family of curves where id is the drain voltage index and ig the gate voltage index.
# same data as IdIV_foc except gate and drain indices are swapped and the Vds=0 datapoint is eliminated
# Note that the return data are indexed data[iVds][iVgs] where iVds and iVgs are the drain and gate voltage indices respectively
	def Id_foc(self,swapindx=True):
		self.__readIVfoc()
		if not hasattr(self,'Id_IVfoc'): return {}
		#return {'Vds':self.Vds_IVfoc[0],'Vgs':swapindex(self.Vgs_IVfoc)[0], 'I':swapindex(self.Id_IVfoc)}
		if not hasattr(self,'Vgs_IVfocfirstVds'): self.Vgs_IVfocfirstVds=[self.Vgs_IVfoc[ig][0] for ig in range(0,len(self.Vgs_IVfoc))]		# get gate voltage setting for each of the Vds sweeps of the foc as the gate voltage at the start of the sweep
		if swapindx: return {'Vds':self.Vds_IVfoc[0],'Vgs':self.Vgs_IVfocfirstVds, 'I':swapindex(self.Id_IVfoc)}    # index [iVds][iVgs]
		else: return {'Vds':self.Vds_IVfoc[0],'Vgs':self.Vgs_IVfocfirstVds, 'I':self.Id_IVfoc}                      # index [iVgs][iVds]
########################################################################################################################################################################################
# return values from the IV family of curves measurements
# linear extrapolation of Y function calculated from family of curves over the Vgs interval of self.fractVgsfit*(max(Vgs)-min(Vgs)) and with the Y function fit to a polynomial of order self.order
# Note that the return data is indexed data[id][ig] where id and ig are the drain and gate voltage indices respectively
	def Yflin_foc(self):
		self.__calc_IdVgsfoc()
		try: self.Yflinfrom_foc
		except: return {}
		return {'Vds': [self.Vds_IVfoc[0][id] for id in range(0,len(self.Vds_IVfoc[0])) if abs(self.Vds_IVfoc[0][id])>epsilon],'Vgs':self.Vgsfitfrom_foc[0], 'Y':self.Yflinfrom_foc}
########################################################################################################################################################################################
# return values from the IV family of curves measurements
# Vgs array values used for the polynomial fit calculation of Idfit, gmfit, Y function calculated from family of curves
# Note that the return data is indexed data[ig] where ig are is the gate voltage index and the gate voltage data array are assumed to be the same for all Vds sweeps in the family of curves
	def Vgsfit_foc(self):
		self.__calc_IdVgsfoc()
		try: self.Vgsfitfrom_foc
		except: return []
		return self.Vgsfitfrom_foc
########################################################################################################################################################################################
# return values from the IV family of curves measurements
# return the number of points used to perform polynomial fits to Id, gm, Y, etc... for the data derived from the family of curves. e.g. this = len(self.Vgsfit_foc())
	def get_nopolyfit_foc(self):
		return self.nopts_polyfit_foc
########################################################################################################################################################################################
# Get the fraction of Vds in the family of curves, used to fit a line to calculate Ron from the family of curves
#
	def get_fractVdsfit_Ronfoc(self):
		return self.fractVdsfit_Ronfoc
########################################################################################################################################################################################
# obtain on resistance near Vds = 0V from the family of curves
# the Ron values are all calculated near Vds = 0V using the self.fractVdsfit to fit the linear extrapolation of Id vs Vds curve (one curve for each Vgs measured) over self.fractVgsfit*(range of Vds measured)
# if the device width self.width is given, then self.Ronfrom_foc is given in ohm*mm. Otherwise it's just ohms
	def __calc_Ronfoc(self,force_calculation=False,fractVdsfit=None):
		if fractVdsfit!=None:
			if abs(self.fractVdsfit_Ronfoc-fractVdsfit)>self.__epsilon:	# then have new value for self.fractVdsfit_Ron which is different from that already set so we need to recalculate Ronfoc because it depends on fractVdsfit
				self.fractVdsfit_Ronfoc=fractVdsfit						# set to new specified value of self.fractVdsfit
				force_calculation=True									# force recalculation of Ron because fractVdsfit has changed!
		if ("IVfoc" not in self.parameters):
			rt=self.__readIVfoc()								#  read IV family of curves from the file if necessary
			if not("IVfoc" in self.parameters):												# can we even get the transfer curve parameters?
				return rt										# will return no data message from self.__readIVfoc() if there are no measured family of curves data
		#if "Ronfoc" not in self.parameters or force_calculation==True:
		if not hasattr(self,'Ronfrom_foc') or force_calculation==True:		# then calculate new Ron parameters
			# find Ron from least-squares linear fit of family of curves near Vds=0V and covering the Vds fractional range specified by self.fractVdsfit_Ronfoc
			# Ron is found for each gate voltage
			#print("from line 1484  __calc_Ronfoc in device_parameter_request.py devicename = ",self.devicename) # debug

			retv = [linfitminmax(x=self.Vds_IVfoc[ig],y=self.Id_IVfoc[ig],fractrange=self.fractVdsfit_Ronfoc,minmax="min") for ig in range(0,len(self.Vgs_IVfoc))]      # get Ron for each gate voltage in the family of curves
			self.Vgs_IVfocfirstVds=[self.Vgs_IVfoc[ig][0] for ig in range(0,len(self.Vgs_IVfoc))]		# get gate voltage setting for each of the Vds sweeps of the foc as the gate voltage at the start of the Vds sweep
			# ig is the index of gate voltages for the measured family of curves
			self.IdRonlinfrom_foc = col.deque()
			self.Ronfrom_foc = col.deque()
			self.Ronfrom_foc_linfitqual=col.deque()
			for ig in range(0,len(retv)):
				if retv[ig][1]>self.__epsilon:
					self.IdRonlinfrom_foc.append(retv[ig][0])
					self.Ronfrom_foc.append(1./retv[ig][1])
					self.Ronfrom_foc_linfitqual.append(retv[ig][3])		# quality of linear fit 1=perfect
				else:
					self.IdRonlinfrom_foc.append(retv[ig][0])
					self.Ronfrom_foc.append(1./self.__epsilon)
					self.Ronfrom_foc_linfitqual.append(retv[ig][3])		# quality of linear fit 1=perfect

				# else:
				# 	self.IdRonlinfrom_foc.append(None)
				# 	self.Ronfrom_foc.append(None)
				# 	self.Ronfrom_foc_linfitqual.append(None)		# quality of linear fit 1=perfect
			if self.devwidth!=None and self.devwidth>0 and len(self.Ronfrom_foc)>0: self.Ronfrom_foc=np.multiply(1000.,self.Ronfrom_foc)	# if the device width self.devwidth is given, then the currents are in mA/mm multiply X 1000 to get ohm*mm
			if "Ronfoc" not in self.parameters:
				self.parameters.append("Ronfoc")
########################################################################################################################################################################################
# obtain on resistance calculated via
# Ron_max[iVgs] = Vds_max[iVgs]/Ids[iVgs] and Vds_max is either the minimum Vds (p-channel devices e.g. carbon nanotube FETS) or the maximum Vds for m-channel devices
# the Ron_max is calculated from the family of curves at each Vgs value measured where iVgs is the index of Vgs
# Inputs: if force_calculation = "force_calculation" then re-read the family of curves and perform the calculations under any circumstance
# devicetype = "n"  this is an n-channel device so use the maximum of Vds to calculate the on resistance
# devicetype = "p" this is a p-channel device so use the minimum of Vds to calculate the on resistance
# the resistance is given in ohm*mm if self.devwidth is specified and >0 otherwise the resistance is given in ohms
	def __calc_Ronmaxfoc(self,force_calculation=False,devicetype=None):
		if devicetype==None: devicetype=self.devicetype		# use default or pre-set device type if one is not given
		elif devicetype != "n" or devicetype !="p": raise ValueError("ERROR: Invalid device type - must be p or n")		# invalid device type given so error out
		if self.devicetype!=devicetype:	# then the device type has changed!? or been specified
			self.devicetype=devicetype		# if the device type is given, then re-set the system default
			force_calculation=True			# so we need to recalculate data
		if (force_calculation==True) or ("IVfoc" not in self.parameters):
			rt=self.__readIVfoc()								#  read IV family of curves from the file if necessary
			if not("IVfoc" in self.parameters):												# can we even get the transfer curve parameters?
				#print("from device_parameter_request.py line 1188 No IVfoc",self.parameters) # debug
				return rt
		if "Ronmaxfoc" not in self.parameters:
			self.parameters.append("Ronmaxfoc")
			# find the minimum (p-channel) or maximum (n-channel) Vds' index The assumption is that the drain voltage array is the same for all gate voltages
			if devicetype=="p": iVds = min(range(len(self.Vds_IVfoc[0])),key=lambda i: self.Vds_IVfoc[0][i])		# p-channel device
			elif devicetype=="n": iVds = max(range(len(self.Vds_IVfoc[0])),key=lambda i: self.Vds_IVfoc[0][i])		# n-channel device
			self._Ronmax_foc = [self.Vds_IVfoc[ig][iVds] / self.Id_IVfoc[ig][iVds] for ig in range(0, len(self.Vds_IVfoc))] # ig is index of gate voltages
			if hasattr(self,'Ronmax_foc') and self.devwidth!=None and self.devwidth>0 and len(self.Ronmax_foc)>0: self.Ronmax_foc=np.multiply(1000.,self.Ronmax_foc)	# if the device width self.devwidth is given, then the currents are in mA/mm multiply X 1000 to get ohm*mm
			# TODO check calculation of Vgs
			#self.Vgs_IVfocfirstVds=[self.Vgs_IVfoc[ig][0] for ig in range(0,len(self.Vgs_IVfoc))]
#########################################################################################################################################################################################
# obtain on resistance near Vds = 0V vs Vgs from the family of curves indexed by gate voltage Vgs
# This is the only way to set a new value of the range of the linear fit of Id vs Vds = self.fractVdsfit_Ronfoc
# self.fractVdsfit_Ronfoc is the fractional range of the linear fit to Id over Vds
# A recalculation will be guaranteed by self.__calc_Ronfoc() if fractVdsfit does not match the previously-set value i.e. self.fractVdsfit_Ronfoc and/OR if force_calculation==True
# if the device width is specifed, it is in um and Ron is given in ohm*mm
	def Ron_foc(self,force_calculation=False,fractVdsfit=None):
		self.__calc_Ronfoc(force_calculation=force_calculation,fractVdsfit=fractVdsfit)
		if not hasattr(self,"Vgs_IVfoc") or not hasattr(self,"Ronfrom_foc"):	# new value specified directly for the linear fitting range to determine on resistance which will force a calculation IF
				# and only if necessary i.e. fractVdsfit is not equal to self.fractVdsfit
			return {}
		else:
			return {'Vgs':self.Vgs_IVfocfirstVds,'R':self.Ronfrom_foc,'Q':self.Ronfrom_foc_linfitqual,'fractlinfit':self.fractVdsfit_Ronfoc}
#########################################################################################################################################################################################
# obtain linear fit of Id vs Vds from family of curves near Vds = 0 This is a list of dimension two i.e. having indices IdRonlin_foc[ig][id] where ig is the foc gate voltage index and
# id is the foc drain voltage index
	def IdRonlin_foc(self,force_calculation=False,fractVdsfit=None):
		self.__calc_Ronfoc(force_calculation=force_calculation,fractVdsfit=fractVdsfit)
		try: self.IdRonlinfrom_foc
		except: return []
		return self.IdRonlinfrom_foc
#########################################################################################################################################################################################
# obtain on resistance calculated via
# Ron_max[iVgs] = Vds_max[iVgs]/Ids[iVgs] and Vds_max is either the minimum Vds (p-channel devices e.g. carbon nanotube FETS) or the maximum Vds for m-channel devices
# Inputs: if force_calculation = "force_calculation" then re-read the family of curves and perform the calculations under any circumstance
# devicetype = "n"  this is an n-channel device so use the maximum of Vds to calculate the on resistance
# devicetype = "p" this is a p-channel device so use the minimum of Vds to calculate the on resistance
	def Ron_max_foc(self,force_calculation=True,devicetype=None):
		if force_calculation==True:
			self.__calc_Ronmaxfoc(force_calculation=True,devicetype=devicetype)
		else:
			self.__calc_Ronmaxfoc(devicetype==devicetype)
		if not hasattr(self,'_Ronmax_foc'):
			#print("from device_parameter_request.py line 871 device is", self.get_devicename(),self.parameters)
			return {}
		else:
			return {'Vgs':self.Vgs_IVfocfirstVds,'R':self._Ronmax_foc}
#########################################################################################################################################################################################
# get the device type setting (n or p) for n or p - channel respectively
	def get_devicetype(self):
		return self.devicetype
#########################################################################################################################################################################################
# set the device type setting (n or p) for n or p - channel respectively
	def set_devicetype(self,type):
		if type=='n' or type=='p': self.devicetype=type
		else: raise ValueError("ERROR! devicetype must be n or p")
########################################################################################################################################################################################
# read single sweep IV transfer curves parameters
########################################################################################################################################################################################
# Single and dual sweep IV transfer curve fraction of Vgs used to fit line for extracting Y-function Rc and Vth
#
	def get_fractVgsfit(self):
		try: self.fractVgsfit
		except: return []
		return self.fractVgsfit
########################################################################################################################################################################################
# Single and dual sweep IV transfer curve order of the polynomial used to fit to Id(Vgs) and the Y-function from measured data
#
	def get_orderfit(self):
		try: self.order
		except: return []
		return self.order
########################################################################################################################################################################################
# Single sweep IV transfer curve time stamp from measured data
	def time_T(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No single sweep transfer curve loaded must read from file
			self.__readIVtransfer()					#  read single sweep transfer curve from the file
		if not("IVt" in self.parameters):	# then must read in measured single sweep transfer curve data
			self.__readIVtransfer()					#  read single sweep transfer curve from the file
		try: self.IVt_year
		except: return []
		return self.IVt_year, self.IVt_month, self.IVt_day, self.IVt_hour, self.IVt_minute, self.IVt_second
########################################################################################################################################################################################
# Single sweep IV transfer curve drain current array (Id vs Vgs) from measured data
	def Id_T(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No single sweep transfer curve loaded must read from file
			self.__readIVtransfer()					#  read single sweep transfer curve from the file
		if not("IVt" in self.parameters):	# then must read in measured single sweep transfer curve data
			self.__readIVtransfer()					#  read single sweep transfer curve from the file
		try: self.Id_IVt
		except: return []
		return self.Id_IVt
########################################################################################################################################################################################
# Single sweep IV transfer curve gate current array (Ig vs Vgs) from measured data
	def Ig_T(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No single sweep transfer curve loaded must read from file
			self.__readIVtransfer()					#  read single sweep transfer curve from the file
		if not("IVt" in self.parameters):	# then must read in measured single sweep transfer curve data
			self.__readIVtransfer()					#  read single sweep transfer curve from the file
		try: self.Ig_IVt
		except: return []
		return self.Ig_IVt
########################################################################################################################################################################################
#  gate current at Vgs where the measured |Id| is at a minimum
# from single swept transfer curves
	def Ig_atIdmin_T(self):
		self.__calc_t()
		if hasattr(self, "IgatIdmin_t"): return self.IgatIdmin_t
		else:return None
########################################################################################################################################################################################
########################################################################################################################################################################################
#  gate current at Vgs where the measured |Ig| is at a maximum for single-swept transfer curve
# from single swept transfer curves
	def Igmax_T(self):
		self.__calc_t()
		if hasattr(self, "Igmax_t"): return self.Igmax_t
		else: return None
########################################################################################################################################################################################
########################################################################################################################################################################################
#  gate current at Vgs where the measured |Ig| is at a maximum for dual-swept transfer curve for the first sweep
# from single swept transfer curves
	def Igmax_TF(self):
		self.__calc_t()
		if hasattr(self, "Igmax_tf"): return self.Igmax_tf
		else: return None
########################################################################################################################################################################################
########################################################################################################################################################################################
#  gate current at Vgs where the measured |Ig| is at a maximum for dual-swept transfer curve for the first sweep
# from single swept transfer curves
	def Igmax_TR(self):
		self.__calc_t()
		if hasattr(self, "Igmax_tr"): return self.Igmax_tr
		else: return None
########################################################################################################################################################################################
# Single sweep IV transfer curve drain voltage from measured data
	def Vds_T(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No single sweep transfer curve loaded must read from file
			self.__readIVtransfer()					#  read single sweep transfer curve from the file
		if not("IVt" in self.parameters):	# then must read in measured single sweep transfer curve data
			self.__readIVtransfer()					#  read single sweep transfer curve from the file
		try: self.Vds_IVt
		except: return []
		return self.Vds_IVt
########################################################################################################################################################################################
# Single sweep IV transfer curve gate voltage array from measured data
	def Vgs_T(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No single sweep transfer curve loaded must read from file
			self.__readIVtransfer()					#  read single sweep transfer curve from the file
		if not("IVt" in self.parameters):	# then must read in measured single sweep transfer curve data
			self.__readIVtransfer()					#  read single sweep transfer curve from the file
		try: self.Vgs_IVt
		except: return []
		return self.Vgs_IVt
########################################################################################################################################################################################
# Single sweep IV transfer curve drain status array from measured data
	def drainstatus_T(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No single sweep transfer curve loaded must read from file
			self.__readIVtransfer()					#  read single sweep transfer curve from the file
		if not("IVt" in self.parameters):	# then must read in measured single sweep transfer curve data
			self.__readIVtransfer()					#  read single sweep transfer curve from the file
		try: self.drainstatus_IVt
		except: return []
		return self.drainstatus_IVt
########################################################################################################################################################################################
# Single sweep IV transfer curve gate status array from measured data
	def gatestatus_T(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No single sweep transfer curve loaded must read from file
			self.__readIVtransfer()					#  read single sweep transfer curve from the file
		if not("IVt" in self.parameters):	# then must read in measured single sweep transfer curve data
			self.__readIVtransfer()					#  read single sweep transfer curve from the file
		try: self.gatestatus_IVt
		except: return []
		return self.gatestatus_IVt
########################################################################################################################################################################################
# Single sweep IV transfer curve calculated parameters from measured data
	def __calc_t(self,force_calculation=False,smoothing_factor=None,deltaVgsplusthres=None,fractVgsfit=None,performYf=False):
		if smoothing_factor!=None:
			force_calculation=True
			self._smoothing_factor=smoothing_factor
		if deltaVgsplusthres!=None:
			if self.deltaVgsplusthres!=deltaVgsplusthres:       # was deltaVgsplusthres supplied and did deltaVgsplusthres change? if so, then update the Y-factor and threshold calculations
				force_calculation=True
				self.deltaVgsplusthres=deltaVgsplusthres
		if fractVgsfit!=None:
			#print("from line 2374 in device_parameter_request.py fractVgsfit=",fractVgsfit)
			if self.fractVgsfit!=fractVgsfit:
				force_calculation=True
				self.fractVgsfit=fractVgsfit
		if not hasattr(self,'Id_IVt'): self.__readIVtransfer()
		if not hasattr(self,'Id_IVt'): return "no single-swept tranfer parameters"
		if not hasattr(self,'gm_t') or not hasattr(self,'Id_atthesholdplusdelta_t') or force_calculation==True: 			# then must calculate parameters
			dat=find_Vth_Rc_gm_spline(Vds=self.Vds_IVt,Ig=self.Ig_T(),Id=self.Id_IVt,Vgs=self.Vgs_IVt,npolyorder=7,fractVgsfit=self.fractVgsfit,sf=self._smoothing_factor,deltaVgsplusthres=self.deltaVgsplusthres,performYf=performYf)
			if dat==None: return []
			self.Rc_t,self.Vth_Yt,self.Vth_Idt,self.Idfit_t,self.Idlin_t,self.Idleak_t,self.Idmin_t,self.VgsIdleak_t,self.VgsIdmin_t,self.Idmax_t,self.VgsIdmax_t,self.Idonoffratio_t,self.gm_t,self.Yf_t,self.Yflin_t,self.Vgsfit_t, self.IgatIdmin_t, self.Igmax, self.Id_atthesholdplusdelta_t= dat
			#  0          1           2            3            4            5             6            7                8               9            10              11                 12         13       14           15			16
			self.gmmax_t = max(self.gm_t)				# get the maximum positive value of gm
		if not ("gm_T" in self.parameters): 			# indicate that we have the parameters
			self.parameters.append("Rc_T")				# contact resistance derived from the Y function
			self.parameters.append("Vth_YT")			# threshold voltage derived from the Y function
			self.parameters.append("Idfit_T")			# fit to drain current vs Vgs using polynomial of order order
			self.parameters.append("gm_T")				# gm derived from above drain current
			self.parameters.append("Y_T")				# Y function derived from above drain current and gm
			self.parameters.append("YL_T")				# linear fit of the above Y function over the fraction of Vgs as specified by fractVgsfit
		return "have data"
########################################################################################################################################################################################
# read calculated transfer curve parameters derived from the single-swept tranfer curve, Id(Vgs)
# 	single swept transfer curve
# 	contact resistance for  as derived from the Y-function fit
	def Rc_T(self):
		self.__calc_t()
		try: self.Rc_t
		except: return []
		return self.Rc_t
########################################################################################################################################################################################
# single swept transfer curve
# 	threshold voltage as derived from the Y-function fit
	def Vth_YT(self):
		self.__calc_t()
		try: self.Vth_Yt
		except: return None
		return self.Vth_Yt
########################################################################################################################################################################################
#	single swept transfer curve
#	threshold voltage as derived from a linear fit of the Id
	def Vth_IdT(self):
		self.__calc_t()
		try: self.Vth_Idt
		except: return None
		return self.Vth_Idt
########################################################################################################################################################################################
#	single swept transfer curve
#	Id fit to polynomial or spline
	def Idfit_T(self):
		self.__calc_t()
		try: self.Idfit_t
		except: return {}
		return {'Vgs':self.Vgsfit_t,'I':self.Idfit_t}
########################################################################################################################################################################################
#	single swept transfer curve
#	Id linear extrapolation fit
	def Idlin_T(self):
		self.__calc_t()
		try: self.Idlin_t
		except: return {}
		return {'Vgs':self.Vgsfit_t,'I':self.Idlin_t}
########################################################################################################################################################################################
#	single swept transfer curve
#	Leakage Id as calculated from the minimum absolute value of the Id fit to a polynomial
	def Idleak_T(self):
		self.__calc_t()
		try: self.Idleak_t
		except: return {}
		return{'Vgs':self.VgsIdleak_t,'I':self.Idleak_t}
		#return self.Idleak_t
########################################################################################################################################################################################
#	single swept transfer curve
#	Leakage Id as calculated from the minimum absolute value of the Id fit to a polynomial
	def Idmin_T(self):
		self.__calc_t()
		try: self.Idmin_t
		except: return {}
		return{'Vgs':self.VgsIdmin_t,'I':self.Idmin_t}
########################################################################################################################################################################################
#	single swept transfer curve
#	Maximum |Idfit| as calculated from the maximum absolute value of the Idfit which is measured Id fit to a polynomial across Vds
#
	def Idmax_T(self):
		self.__calc_t()
		try: self.Idmax_t
		except: return {}
		return {'Vgs':self.VgsIdmax_t,'I':self.Idmax_t}
########################################################################################################################################################################################
#	single swept transfer curve
#	Imax/Imin ratio as calculated from the maximum absolute value of the Id fit to a polynomial across Vds
#	WARNING! NOTE that this is calculated using the polynomial fit of the measured Id for Imax and the MEASURED value of Id for the Imin
	def Idonoffratio_T(self):
		self.__calc_t()
		try: self.Idonoffratio_t
		except: return {}
		return {'VgsIdleak':self.VgsIdleak_t,'VgsIdmax':self.VgsIdmax_t,'VgsIdmin':self.VgsIdmin_t, 'Ir':self.Idonoffratio_t}
########################################################################################################################################################################################
#	single swept transfer curve
#	transconductance as calculated from the polynomial or spline fit of Id
	def gm_T(self,smoothing_factor=None):
		self.__calc_t(smoothing_factor=smoothing_factor)
		try: self.gm_t
		except: return {}
		return {'Vgs':self.Vgsfit_t,'G':self.gm_t,'gatestatus':self.gatestatus_T(),'drainstatus':self.drainstatus_T(),'Vds':self.Vds_T()}
########################################################################################################################################################################################
#	maximum Gm (transconductance) from single swept transfer curve
#	maximum positive value of transconductance as calculated from the polynomial or spline fit of Id
# Vds is a single point - i.e. the single applied drain voltage for the transfer curve measurement
	def gmmax_T(self,smoothing_factor=None):
		self.__calc_t(smoothing_factor=smoothing_factor)
		if hasattr(self,'gm_t'):
			iVgs_gmmax = max(range(0,len(self.gm_t)), key=lambda iiVgs: self.gm_t[iiVgs] )
			Vgs=self.Vgs_IVt[iVgs_gmmax]
		try: self.gmmax_t
		except: return {}
		return {'G':self.gmmax_t,'Vgs':Vgs,'Vds':self.Vds_IVt,'Id': self.Id_IVt[iVgs_gmmax],'Ig': self.Ig_IVt[iVgs_gmmax]}
########################################################################################################################################################################################
#	single swept transfer curve
#	Y-function as calculated from gm and Idfit_T Y is a function of Vgs
# 	gatestatus and drainstatus are one of "N" (normal measurement), 'C" (compliance), or another letter indicating abnormal measurement - one value per gate voltage
	def Yf_T(self):
		self.__calc_t(performYf=True)
		try: self.Yf_t
		except: return {}
		return {'Vgs':self.Vgsfit_t,'Y':self.Yf_t,'gatestatus':self.gatestatus_T(),'drainstatus':self.drainstatus_T(),'Vds':self.Vds_T()}
########################################################################################################################################################################################
#	single swept transfer curve
#	Y-function as calculated from gm and Idfit_T Y is a function of Vgs
	def Yflin_T(self):
		self.__calc_t(performYf=True)
		try: self.Yflin_t
		except: return {}
		print("from line 2504 in device_parameter_request.py len(self.Vgsfit), len(self.Yflin_t",len(self.Vgsfit_t),len(self.Yflin_t))
		return {'Vgs':self.Vgsfit_t,'Y':self.Yflin_t}
########################################################################################################################################################################################
#	single swept transfer curve
#	get drain current at the specified delta Vgs above the threshold voltage
#
	def Id_atthesholdplusdelta_T_Ronatthesholdplusdelta_T(self, deltaVgsplusthres=None, fractVgsfit=None):
		self.__calc_t(deltaVgsplusthres=deltaVgsplusthres,fractVgsfit=fractVgsfit,performYf=True)
		if self.Id_atthesholdplusdelta_t!=None:
			self.Ron_VthpdeltaVgs_t=self.Vds_IVt/self.Id_atthesholdplusdelta_t          # On resistance from transfer curve at Vgs = deltaVgsplusthres + threshold voltage
			return {'Id':self.Id_atthesholdplusdelta_t,'Ron':self.Ron_VthpdeltaVgs_t}
		else:
			return None
########################################################################################################################################################################################
#	single swept transfer curve
#	find number of data points with compliance or other measurement issues
	def gatestatus_no_T(self):
		if len(self.gatestatus_T())==0: return None
		nobadsites=0
		for s in self.gatestatus_T():
			if s!='N': nobadsites+=1		# then there was a gate compliance problem
		return  nobadsites

	def drainstatus_no_T(self):
		if len(self.drainstatus_T())==0: return None
		nobadsites=0
		for s in self.drainstatus_T():
			if s!='N': nobadsites+=1		# then there was a drain compliance problem
		return  nobadsites
########################################################################################################################################################################################
# forward sweep IV transfer curves for loop i.e. dual swept transfer curves
########################################################################################################################################################################################
# Forward swept IV transfer curve time stamp from measured data
	def time_TF(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		if not("IVtf" in self.parameters):	# then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		try: self.IVtfr_year
		except: return []
		return self.IVtfr_year, self.IVtfr_month, self.IVtfr_day, self.IVtfr_hour, self.IVtfr_minute, self.IVtfr_second
########################################################################################################################################################################################
# Forward swept IV transfer curve drain current array (Id vs Vgs) from measured data
	def Id_TF(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		if not("IVtf" in self.parameters):	# then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		try: self.Id_IVtf
		except: return []
		return self.Id_IVtf

########################################################################################################################################################################################
# four sweep transfer curve drain current array 3rd sweep (Id vs Vgs) from measured data
	def Id_T3(self):
		try:
			dummy = self.parameters  # do any parameters exist for this device?
		except:  # No fourswept transfer curve loaded must read from file
			self.__readIVtransferloop()  # read four swept transfer curve from the file
		if not ("IVt3" in self.parameters):  # then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()  # read four swept transfer curve from the file
		try:self.Id_IVt3
		except: return []
		return self.Id_IVt3
########################################################################################################################################################################################
# four sweep transfer curve drain current array 4th sweep (Id vs Vgs) from measured data
	def Id_T4(self):
		try:
			dummy = self.parameters  # do any parameters exist for this device?
		except:  # No four swept transfer curve loaded must read from file
			self.__readIVtransferloop()  # read four swept transfer curve from the file
		if not ("IVt4" in self.parameters):  # then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()  # read four swept transfer curve from the file
		try: self.Id_IVt4
		except: return []
		return self.Id_IVt4
########################################################################################################################################################################################
# Forward swept IV transfer curve gate current array (Ig vs Vgs) from measured data
	def Ig_TF(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		if not("IVtf" in self.parameters):	# then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		try: self.Ig_IVtf
		except: return []
		return self.Ig_IVtf
########################################################################################################################################################################################
#  gate current at Vgs where the measured |Id| is at a minimum
# from 1st of dual swept transfer curves
	def Ig_atIdmin_TF(self):
		self.__calc_tf()
		if hasattr(self,"IgatIdmin_tf"): return self.IgatIdmin_tf
		else: return None
########################################################################################################################################################################################
# Forward swept IV transfer curve drain voltage from measured data
	def Vds_TF(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		if not("IVtf" in self.parameters):	# then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		try: self.Vds_IVtfr
		except: return []
		return self.Vds_IVtfr
########################################################################################################################################################################################
# 3rd sweep four swept IV transfer curve drain voltage from measured data
	def Vds_T3(self):
		try:
			dummy = self.parameters  # do any parameters exist for this device?
		except:  # No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()  # read dual swept transfer curve from the file
		if not ("IVt3" in self.parameters):  # then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()  # read dual swept transfer curve from the file
		try: self.Vds_IVtfr
		except: return []
		return self.Vds_IVtfr
########################################################################################################################################################################################
# 3rd sweep four swept IV transfer curve drain voltage from measured data
	def Vds_T4(self):
		try:
			dummy = self.parameters  # do any parameters exist for this device?
		except:  # No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()  # read dual swept transfer curve from the file
		if not ("IVt4" in self.parameters):  # then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()  # read dual swept transfer curve from the file
		try: self.Vds_IVtfr
		except: return []
		return self.Vds_IVtfr
########################################################################################################################################################################################
# Forward swept IV transfer curve gate voltage array from measured data
	def Vgs_TF(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		if not("IVtf" in self.parameters):	# then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		try: self.Vgs_IVtf
		except: return []
		return self.Vgs_IVtf

########################################################################################################################################################################################
# four swept IV transfer curve 3rd sweep gate voltage array from measured data
	def Vgs_T3(self):
		try:
			dummy = self.parameters  # do any parameters exist for this device?
		except:  # No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()  # read dual swept transfer curve from the file
		if not ("IVt3" in self.parameters):  # then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()  # read dual swept transfer curve from the file
		try:
			self.Vgs_IVt3
		except:
			return []
		return self.Vgs_IVt3

########################################################################################################################################################################################
# four swept IV transfer curve 4th sweep gate voltage array from measured data
	def Vgs_T4(self):
		try:
			dummy = self.parameters  # do any parameters exist for this device?
		except:  # No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()  # read dual swept transfer curve from the file
		if not ("IVt4" in self.parameters):  # then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()  # read dual swept transfer curve from the file
		try:
			self.Vgs_IVt4
		except:
			return []
		return self.Vgs_IVt4
########################################################################################################################################################################################
# Forward swept IV transfer curve drain status array from measured data
	def drainstatus_TF(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		if not("IVtf" in self.parameters):	# then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		try: self.drainstatus_IVtf
		except: return []
		return self.drainstatus_IVtf
########################################################################################################################################################################################
# Forward swept IV transfer curve gate status array from measured data
	def gatestatus_TF(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		if not("IVtf" in self.parameters):	# then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		try: self.gatestatus_IVtf
		except: return []
		return self.gatestatus_IVtf
########################################################################################################################################################################################
# Double sweep IV forward transfer curve calculated parameters from measured data
	def __calc_tf(self,force_calculation=False,smoothing_factor=None):
		if smoothing_factor!=None:
			self._smoothing_factor=smoothing_factor
			force_calculation=True
		if not hasattr(self,'Id_IVtf'): self.__readIVtransferloop(type="transferloop")
		if not hasattr(self,'Id_IVtf'): return "no dual-swept tranfer parameters"
		if not hasattr(self,'gm_tf') or force_calculation==True: 			# then must calculate parameters
			dat=find_Vth_Rc_gm_spline(Vds=self.Vds_IVtfr,Id=self.Id_IVtf,Ig=self.Ig_TF(),Vgs=self.Vgs_IVtf,npolyorder=7,fractVgsfit=self.fractVgsfit,sf=self._smoothing_factor)
			if dat==None: return []
			self.Rc_tf,self.Vth_Ytf,self.Vth_Idtf,self.Idfit_tf,self.Idlin_tf,self.Idleak_tf,self.Idmin_tf,self.VgsIdleak_tf,self.VgsIdmin_tf,self.Idmax_tf,self.VgsIdmax_tf,self.Idonoffratio_tf,self.gm_tf,self.Yf_tf,self.Yflin_tf,self.Vgsfit_tf,self.IgatIdmin_tf, self.Igmax_tf= dat
			#  0          1             2            3            4              5              6              7                 8               9            10                 11                  12         13          14           15					16
			self.gmmax_tf = max(self.gm_tf)				# get the maximum positive value of gm
		if not ("gm_TF" in self.parameters ):			# indicate that we have the parameters
			self.parameters.append("Rc_TF")				# contact resistance derived from the Y function
			self.parameters.append("Rc_YTF")			# threshold voltage derived from the Y function
			self.parameters.append("Idfit_TF")			# fit to drain current vs Vgs using polynomial of order order
			self.parameters.append("gm_TF")				# gm derived from above drain current
			self.parameters.append("Y_TF")				# Y function derived from above drain current and gm
			self.parameters.append("YL_TF")				# linear fit of the above Y function over the fraction of Vgs as specified by fractVgsfit
		return ("have data")

#######################################################################################################################################################################################
# 4-sweep 1st transfer curve calculated parameters from measured data
# not used yet - used __calc_tf instead
	def __calc_t1(self, force_calculation=False,smoothing_factor=None):
		if smoothing_factor!=None:
			self._smoothing_factor=smoothing_factor
			force_calculation=True
		if not hasattr(self, 'Id_IVt1'): self.__readIVtransferloop(type="transferloop4")
		if not hasattr(self, 'Id_IVt1'): return []
		if not hasattr(self, 'gm_t1') or force_calculation == True:  # then must calculate parameters
			dat = find_Vth_Rc_gm_spline(Vds=self.Vds_IVtfr, Id=self.Id_IVt1, Ig=self.Ig_TF(), Vgs=self.Vgs_IVt1, npolyorder=7, fractVgsfit=self.fractVgsfit,sf=self._smoothing_factor)
			if dat == None: return []
			self.Rc_t1, self.Vth_Yt1, self.Vth_Idt1, self.Idfit_t1, self.Idlin_t1, self.Idleak_t1, self.Idmin_t1, self.VgsIdleak_t1, self.VgsIdmin_t1, self.Idmax_t1, self.VgsIdmax_t1, self.Idonoffratio_t1, self.gm_t1, self.Yf_t1, self.Yflin_t1, self.Vgsfit_t1, self.IgatIdmin_t1, self.Igmax_t1 = dat
			#  0          1             2            3            4              5              6              7                 8               9            10                 11                  12         13          14           15					16
			self.gmmax_t1 = max(self.gm_t1)  # get the maximum positive value of gm
		if not ("gm_T3" in self.parameters):  # indicate that we have the parameters
			self.parameters.append("Rc_T3")  # contact resistance derived from the Y function
			self.parameters.append("Rc_YT3")  # threshold voltage derived from the Y function
			self.parameters.append("Idfit_T3")  # fit to drain current vs Vgs using polynomial of order order
			self.parameters.append("gm_T3")  # gm derived from above drain current
			self.parameters.append("Y_T3")  # Y function derived from above drain current and gm
			self.parameters.append("YL_T3")  # linear fit of the above Y function over the fraction of Vgs as specified by fractVgsfit
		return ("have data")
#######################################################################################################################################################################################
# 4-sweep 2nd transfer curve calculated parameters from measured data
	# not used yet - used __calc_tr instead
	def __calc_t2(self, force_calculation=False,smoothing_factor=None):
		if smoothing_factor!=None:
			self._smoothing_factor=smoothing_factor
			force_calculation=True
		if not hasattr(self, 'Id_IVt2'): self.__readIVtransferloop(type="transferloop4")
		if not hasattr(self, 'Id_IVt2'): return []
		if not hasattr(self, 'gm_t2') or force_calculation == True:  # then must calculate parameters
			dat = find_Vth_Rc_gm_spline(Vds=self.Vds_IVtfr, Id=self.Id_IVt2, Ig=self.Ig_TF(), Vgs=self.Vgs_IVt2, npolyorder=7, fractVgsfit=self.fractVgsfit,sf=self._smoothing_factor)
			if dat == None: return []
			self.Rc_t2, self.Vth_Yt2, self.Vth_Idt2, self.Idfit_t2, self.Idlin_t2, self.Idleak_t2, self.Idmin_t2, self.VgsIdleak_t2, self.VgsIdmin_t2, self.Idmax_t2, self.VgsIdmax_t2, self.Idonoffratio_t2, self.gm_t2, self.Yf_t2, self.Yflin_t2, self.Vgsfit_t2, self.IgatIdmin_t2, self.Igmax_t2 = dat
			#  0          1             2            3            4              5              6              7                 8               9            10                 11                  12         13          14           15					16
			self.gmmax_t2 = max(self.gm_t2)  # get the maximum positive value of gm
		if not ("gm_T3" in self.parameters):  # indicate that we have the parameters
			self.parameters.append("Rc_T3")  # contact resistance derived from the Y function
			self.parameters.append("Rc_YT3")  # threshold voltage derived from the Y function
			self.parameters.append("Idfit_T3")  # fit to drain current vs Vgs using polynomial of order order
			self.parameters.append("gm_T3")  # gm derived from above drain current
			self.parameters.append("Y_T3")  # Y function derived from above drain current and gm
			self.parameters.append("YL_T3")  # linear fit of the above Y function over the fraction of Vgs as specified by fractVgsfit
		return ("have data")
#######################################################################################################################################################################################
	# 4-sweep 3rd transfer curve calculated parameters from measured data
	def __calc_t3(self, force_calculation=False,smoothing_factor=None):
		if smoothing_factor!=None:
			self._smoothing_factor=smoothing_factor
			force_calculation=True
		if not hasattr(self, 'Id_IVt3'): self.__readIVtransferloop(type="transferloop4")
		if not hasattr(self, 'Id_IVt3'): return []
		if not hasattr(self, 'gm_t3') or force_calculation == True:  # then must calculate parameters
			dat = find_Vth_Rc_gm_spline(Vds=self.Vds_IVtfr, Id=self.Id_IVt3, Ig=self.Ig_TF(), Vgs=self.Vgs_IVt3, npolyorder=7, fractVgsfit=self.fractVgsfit,sf=self._smoothing_factor)
			if dat == None: return []
			self.Rc_t3, self.Vth_Yt3, self.Vth_Idt3, self.Idfit_t3, self.Idlin_t3, self.Idleak_t3, self.Idmin_t3, self.VgsIdleak_t3, self.VgsIdmin_t3, self.Idmax_t3, self.VgsIdmax_t3, self.Idonoffratio_t3, self.gm_t3, self.Yf_t3, self.Yflin_t3, self.Vgsfit_t3, self.IgatIdmin_t3,self.Igmax_t3 = dat
			#  0          1             2            3            4              5              6              7                 8               9            10                 11                  12         13          14           15					16
			self.gmmax_t3 = max(self.gm_t3)  # get the maximum positive value of gm
		if not ("gm_T3" in self.parameters):  # indicate that we have the parameters
			self.parameters.append("Rc_T3")  # contact resistance derived from the Y function
			self.parameters.append("Rc_YT3")  # threshold voltage derived from the Y function
			self.parameters.append("Idfit_T3")  # fit to drain current vs Vgs using polynomial of order order
			self.parameters.append("gm_T3")  # gm derived from above drain current
			self.parameters.append("Y_T3")  # Y function derived from above drain current and gm
			self.parameters.append("YL_T3")  # linear fit of the above Y function over the fraction of Vgs as specified by fractVgsfit
		return ("have data")
#######################################################################################################################################################################################
# 4-sweep 4th transfer curve calculated parameters from measured data
	def __calc_t4(self, force_calculation=False,smoothing_factor=None):
		if smoothing_factor!=None:
			self._smoothing_factor=smoothing_factor
			force_calculation=True
		if not hasattr(self, 'Id_IVt4'): self.__readIVtransferloop(type="transferloop4")
		if not hasattr(self, 'Id_IVt4'): return []
		if not hasattr(self, 'gm_t4') or force_calculation == True:  # then must calculate parameters
			dat = find_Vth_Rc_gm_spline(Vds=self.Vds_IVtfr, Id=self.Id_IVt4, Ig=self.Ig_TF(), Vgs=self.Vgs_IVt4, npolyorder=7, fractVgsfit=self.fractVgsfit,sf=self._smoothing_factor)
			if dat == None: return []
			self.Rc_t4, self.Vth_Yt4, self.Vth_Idt4, self.Idfit_t4, self.Idlin_t4, self.Idleak_t4, self.Idmin_t4, self.VgsIdleak_t4, self.VgsIdmin_t4, self.Idmax_t4, self.VgsIdmax_t4, self.Idonoffratio_t4, self.gm_t4, self.Yf_t4, self.Yflin_t4, self.Vgsfit_t4, self.IgatIdmin_t4, self.Igmax_t4 = dat
			#  0          1             2            3            4              5              6              7                 8               9            10                 11                  12         13          14           15					16
			self.gmmax_t4 = max(self.gm_t4)  # get the maximum positive value of gm
		if not ("gm_T3" in self.parameters):  # indicate that we have the parameters
			self.parameters.append("Rc_T3")  # contact resistance derived from the Y function
			self.parameters.append("Rc_YT3")  # threshold voltage derived from the Y function
			self.parameters.append("Idfit_T3")  # fit to drain current vs Vgs using polynomial of order order
			self.parameters.append("gm_T3")  # gm derived from above drain current
			self.parameters.append("Y_T3")  # Y function derived from above drain current and gm
			self.parameters.append("YL_T3")  # linear fit of the above Y function over the fraction of Vgs as specified by fractVgsfit
		return ("have data")
########################################################################################################################################################################################
# read calculated parameters derived from the forward portion of the dual-swept tranfer curve, Id(Vgs)
# 	forward portion of dual swept transfer curve
# 	contact resistance for  as derived from the Y-function fit
	def Rc_TF(self):
		self.__calc_tf()
		try: self.Rc_tf
		except: return []
		return self.Rc_tf
########################################################################################################################################################################################
# forward portion of dual swept transfer curve
# 	threshold voltage as derived from the Y-function fit
	def Vth_YTF(self):
		self.__calc_tf()
		try: self.Vth_Ytf
		except: return []
		return self.Vth_Ytf
########################################################################################################################################################################################
#	forward portion of dual swept transfer curve
#	threshold voltage as derived from a linear fit of the Id
	def Vth_IdTF(self):
		self.__calc_tf()
		try: self.Vth_Idtf
		except: return []
		return self.Vth_Idtf
########################################################################################################################################################################################
#	forward portion of dual swept transfer curve
#	Id fit to polynomial or spline
	def Idfit_TF(self):
		self.__calc_tf()
		try: self.Idfit_tf
		except: return []
		return {'Vgs':self.Vgsfit_tf,'I':self.Idfit_tf}

########################################################################################################################################################################################
#	3rd sweep portion of four swept transfer curve
#	Id fit to polynomial or spline
	def Idfit_T3(self):
		self.__calc_t3()
		try: self.Idfit_t3
		except: return {}
		return {'Vgs': self.Vgsfit_t3, 'I': self.Idfit_t3}

########################################################################################################################################################################################
#	4th sweep portion of four swept transfer curve
#	Id fit to polynomial or spline
	def Idfit_T4(self):
		self.__calc_t4()
		try: self.Idfit_t4
		except: return {}
		return {'Vgs': self.Vgsfit_t4, 'I': self.Idfit_t4}
########################################################################################################################################################################################
#	forward portion of dual swept transfer curve
#	Id linear extrapolation fit
	def Idlin_TF(self):
		self.__calc_tf()
		try: self.Idlin_tf
		except: return {}
		return {'Vgs':self.Vgsfit_tf,'I':self.Idlin_tf}
########################################################################################################################################################################################
#	forward portion of dual swept transfer curve
#	Leakage Id as calculated from the minimum absolute value of Id polynomial fit
	def Idleak_TF(self):
		self.__calc_tf()
		try: self.Idleak_tf
		except: return {}
		return{'Vgs':self.VgsIdleak_tf,'I':self.Idleak_tf}
########################################################################################################################################################################################
#	forward portion of dual swept transfer curve
#	Idmax/Idmin as calculated from the minimum absolute value of Id polynomial fit
# WARNING! NOTE that this is calculated using the polynomial fit of the measured Id for Imax and the MEASURED value of Id for the Imin
	def Idonoffratio_TF(self):
		self.__calc_tf()
		try: self.Idonoffratio_tf
		except: return {}
		return {'VgsIdleak':self.VgsIdleak_tf,'VgsIdmax':self.VgsIdmax_tf, 'Ir':self.Idonoffratio_tf}
########################################################################################################################################################################################
#	3rd swept portion of 4 swept transfer curve
#	Idmax/Idmin as calculated from the minimum absolute value of Id polynomial fit
# WARNING! NOTE that this is calculated using the polynomial fit of the measured Id for Imax and the MEASURED value of Id for the Imin
	def Idonoffratio_T3(self):
		self.__calc_t3()
		try: self.Idonoffratio_t3
		except:return {}
		return {'VgsIdleak': self.VgsIdleak_t3, 'VgsIdmax': self.VgsIdmax_t3, 'Ir': self.Idonoffratio_t3}
########################################################################################################################################################################################
#	4th swept portion of 4 swept transfer curve
#	Idmax/Idmin as calculated from the minimum absolute value of Id polynomial fit
# WARNING! NOTE that this is calculated using the polynomial fit of the measured Id for Imax and the MEASURED value of Id for the Imin
	def Idonoffratio_T4(self):
		self.__calc_t4()
		try: self.Idonoffratio_t4
		except:return {}
		return {'VgsIdleak': self.VgsIdleak_t4, 'VgsIdmax': self.VgsIdmax_t4, 'Ir': self.Idonoffratio_t4}
########################################################################################################################################################################################
#	dual swept transfer curve 1st sweep derived data
#	Leakage Id as calculated from the actual measured data
	def Idmin_TF(self):
		self.__calc_tf()
		try: self.Idmin_tf
		except: return {}
		return {'Vgs': self.VgsIdmin_tf, 'I': self.Idmin_tf}

########################################################################################################################################################################################
#	four swept transfer curve 1st sweep derived data
#	Leakage Id as calculated from the actual measured data
	def Idmin_T1(self):
		self.__calc_t1()
		try: self.Idmin_t1
		except: return {}
		return {'Vgs': self.VgsIdmin_t1, 'I': self.Idmin_t1}

########################################################################################################################################################################################
#	four swept transfer curve 2nd sweep derived data
#	Leakage Id as calculated from the actual measured data
	def Idmin_T2(self):
		self.__calc_t2()
		try:
			self.Idmin_t2
		except:
			return {}
		return {'Vgs': self.VgsIdmin_t2, 'I': self.Idmin_t2}
########################################################################################################################################################################################
#	four swept transfer curve 3st sweep derived data
#	Leakage Id as calculated from the actual measured data
	def Idmin_T3(self):
		self.__calc_t3()
		try:self.Idmin_t3
		except: return {}
		return {'Vgs': self.VgsIdmin_t3, 'I': self.Idmin_t3}
########################################################################################################################################################################################
#	four swept transfer curve 4th sweep derived data
#	Leakage Id as calculated from the actual measured data
	def Idmin_T4(self):
		self.__calc_t4()
		try: self.Idmin_t4
		except: return {}
		return {'Vgs': self.VgsIdmin_t4, 'I': self.Idmin_t4}
########################################################################################################################################################################################
#	forward portion of dual swept transfer curve
#	Maximum |Idfit| as calculated from the minimum absolute value of Id polynomial fit
	def Idmax_TF(self):
		self.__calc_tf()
		try: self.Idmax_tf
		except: return {}
		return {'Vgs':self.VgsIdmax_tf,'I':self.Idmax_tf}
########################################################################################################################################################################################
#	3rd swept portion of 4 swept transfer curve
#	Maximum |Idfit| as calculated from the minimum absolute value of Id polynomial fit
	def Idmax_T3(self):
		self.__calc_t3()
		try:
			self.Idmax_t3
		except:
			return {}
		return {'Vgs': self.VgsIdmax_t3, 'I': self.Idmax_t3}
# #######################################################################################################################################################################################
# 	4th swept portion of 4 swept transfer curve
# 	Maximum |Idfit| as calculated from the minimum absolute value of Id polynomial fit
	def Idmax_T4(self):
		self.__calc_t4()
		try:
			self.Idmax_t4
		except:
			return {}
		return {'Vgs': self.VgsIdmax_t4, 'I': self.Idmax_t4}
########################################################################################################################################################################################
#	forward portion of dual swept transfer curve
#	transconductance as calculated from the polynomial or spline fit of Id
	def gm_TF(self,smoothing_factor=None):
		self.__calc_tf(smoothing_factor=smoothing_factor)
		try: self.gm_tf
		except: return {}
		return {'Vgs':self.Vgsfit_tf,'G':self.gm_tf}

########################################################################################################################################################################################
#	3rd swept portion of four swept transfer curve
#	transconductance as calculated from the polynomial or spline fit of Id
	def gm_T3(self,smoothing_factor=None):
		self.__calc_t3(smoothing_factor=smoothing_factor)
		try:
			self.gm_t3
		except:
			return {}
		return {'Vgs': self.Vgsfit_t3, 'G': self.gm_t3}

########################################################################################################################################################################################
#	4th swept portion of four swept transfer curve
#	transconductance as calculated from the polynomial or spline fit of Id
	def gm_T4(self,smoothing_factor=None):
		self.__calc_t4(smoothing_factor=smoothing_factor)
		try:
			self.gm_t4
		except:
			return {}
		return {'Vgs': self.Vgsfit_t4, 'G': self.gm_t4}
########################################################################################################################################################################################
#	forward portion of dual swept transfer curve
#	maximum positive transconductance as calculated from the polynomial or spline fit of Id
	def gmmax_TF(self,smoothing_factor=None):
		self.__calc_tf(smoothing_factor=smoothing_factor)
		if hasattr(self,'gm_tf'):
			iVgs_gmmax = max(range(0,len(self.gm_tf)), key=lambda iiVgs: self.gm_tf[iiVgs] )
			Vgs=self.Vgs_IVtf[iVgs_gmmax]
		try: self.gmmax_tf
		except: return {}
		return {'G':self.gmmax_tf,'Vgs':Vgs,'Vds':self.Vds_IVtfr, 'Id': self.Id_IVtf[iVgs_gmmax], 'Ig': self.Ig_IVtf[iVgs_gmmax]}
########################################################################################################################################################################################
#	forward portion of dual swept transfer curve
#	Y-function as calculated from gm and Idfit_T Y is a function of Vgs
	def Yf_TF(self):
		self.__calc_tf()
		return {'Vgs':self.Vgsfit_tf,'I':self.Yf_tf}
########################################################################################################################################################################################
#	forward portion of dual swept transfer curve
#	Y-function as calculated from gm and Idfit_T Y is a function of Vgs
	def Yflin_TF(self):
		self.__calc_tf()
		try: self.Yflin_tf
		except: return {}
		return {'Vgs':self.Vgsfit_tf,'I':self.Yflin_tf}
########################################################################################################################################################################################
#	forward portion of dual swept transfer curve
#	find number of data points with compliance or other measurement issues
	def gatestatus_no_TF(self):
		if len(self.gatestatus_TF())>0:
			nobadsites=0
			for s in self.gatestatus_TF():
				if s != 'N': nobadsites += 1  # then there was a gate compliance problem
			return nobadsites
		else: return None
	def drainstatus_no_TF(self):
		if len(self.drainstatus_TF())>0:
			nobadsites=0
			for s in self.drainstatus_TF():
				if s != 'N': nobadsites += 1  # then there was a drain compliance problem
			return  nobadsites
		else: return None
########################################################################################################################################################################################
# Reverse swept IV transfer curves for loop i.e. dual swept transfer curves
########################################################################################################################################################################################
# Reverse swept IV transfer curve time stamp from measured data
	def time_TR(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		if not("IVtr" in self.parameters):	# then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		try: self.IVtfr_year
		except: return []
		return self.IVtfr_year, self.IVtfr_month, self.IVtfr_day, self.IVtfr_hour, self.IVtfr_minute, self.IVtfr_second
########################################################################################################################################################################################
# Reverse swept IV transfer curve drain current array (Id vs Vgs) from measured data
	def Id_TR(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		if not("IVtr" in self.parameters):	# then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		try: self.Id_IVtr
		except: return []
		return self.Id_IVtr
########################################################################################################################################################################################
# Reverse swept IV transfer curve gate current array (Ig vs Vgs) from measured data
	def Ig_TR(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		if not("IVtr" in self.parameters):	# then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		try: self.Ig_IVtr
		except: return []
		return self.Ig_IVtr

########################################################################################################################################################################################
#	dual swept transfer curve 1st sweep derived data
#	Leakage Id as calculated from the actual measured data
	def Idmin_TR(self):
		self.__calc_tr()
		try:
			self.Idmin_tr
		except:
			return {}
		return {'Vgs': self.VgsIdmin_tr, 'I': self.Idmin_tr}
########################################################################################################################################################################################
#  gate current at Vgs where the measured |Id| is at a minimum
# from 2nd of dual swept transfer curves
	def Ig_atIdmin_TR(self):
		self.__calc_tr()
		if hasattr(self,"IgatIdmin_tr"): return self.IgatIdmin_tr
		else: return None

########################################################################################################################################################################################
#  gate current at Vgs where the measured |Id| is at a minimum
# from 2nd of dual swept transfer curves
# 	def Ig_over_Id_TR(self):
# 		self.__calc_tr()
# 		if hasattr(self, "Ig_TR") and hasattr(self,"Id_IVtr"):
# 			if len(self.Ig_tr)!=len(self.Id_IVtr):
#
# 			return self.IgatIdmin_tr
# 		else:
#			return []
########################################################################################################################################################################################
# Reverse swept IV transfer curve drain voltage from measured data
	def Vds_TR(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		if not("IVtr" in self.parameters):	# then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		try: self.Vds_IVtfr
		except: return []
		return self.Vds_IVtfr
########################################################################################################################################################################################
# Reverse swept IV transfer curve gate voltage array from measured data
	def Vgs_TR(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		if not("IVtr" in self.parameters):	# then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		try: self.Vgs_IVtr
		except: return []
		return self.Vgs_IVtr
########################################################################################################################################################################################
# Reverse swept IV transfer curve drain status array from measured data
	def drainstatus_TR(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		if not("IVtr" in self.parameters):	# then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		try: self.drainstatus_IVtr
		except: return []
		return self.drainstatus_IVtr
########################################################################################################################################################################################
# Reverse swept IV transfer curve gate status array from measured data
	def gatestatus_TR(self):
		try: dummy=self.parameters			# do any parameters exist for this device?
		except:								# No dual swept transfer curve loaded must read from file
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		if not("IVtr" in self.parameters):	# then must read in measured dual swept transfer curve data
			self.__readIVtransferloop()					#  read dual swept transfer curve from the file
		try: self.gatestatus_IVtr
		except: return []
		return self.gatestatus_IVtr
########################################################################################################################################################################################
# Double sweep IV reverse transfer curve calculated parameters from measured data
	def __calc_tr(self,force_calculation=False,smoothing_factor=None):
		if smoothing_factor!=None:
			self._smoothing_factor=smoothing_factor
			force_calculation = True
		if not hasattr(self,'Id_IVtr'): self.__readIVtransferloop(type="transferloop")					#  read single sweep transfer curve from the file if we don't already have the data
		if not hasattr(self,'Id_IVtr'):				# can we even get the transfer curve parameters?
			return "no dual-swept tranfer parameters"
		if not hasattr(self,'gm_tr') or force_calculation==True: 			# then must calculate parameters
			#print("from line 1802 device_parameter_request.py device name =", self.devicename)
			dat=find_Vth_Rc_gm_spline(Vds=self.Vds_IVtfr,Id=self.Id_IVtr,Ig=self.Ig_TR(),Vgs=self.Vgs_IVtr,npolyorder=7,fractVgsfit=self.fractVgsfit,sf=self._smoothing_factor)
			if dat==None: return []
			self.Rc_tr,self.Vth_Ytr,self.Vth_Idtr,self.Idfit_tr,self.Idlin_tr,self.Idleak_tr,self.Idmin_tr,self.VgsIdleak_tr,self.VgsIdmin_tr,self.Idmax_tr,self.VgsIdmax_tr,self.Idonoffratio_tr,self.gm_tr,self.Yf_tr,self.Yflin_tr,self.Vgsfit_tr,self.IgatIdmin_tr, self.Igmax_tr= dat
			#  0          1             2            3            4              5              6              7                 8               9            10                 11                  12         13          14           15				16
			self.gmmax_tr = max(self.gm_tr)				# get the maximum positive value of gm
			#iVgs = min(range(len(self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'])), key=lambda i: abs(self.DCd[self.focfirstdevindex].Ron_foc()['Vgs'][i] - self.__Vgs_selected))
			self.Ig_over_Id_tr = [abs(self.Ig_IVtr[i]/self.Id_IVtr[i]) for i in range(0,len(self.Ig_IVtr))]
			iiVgs = max(range(len(self.Id_IVtr)), key=lambda i: np.abs(self.Id_IVtr[i]))						# find the Vgs index of the maximum |drain current| (|Id|)
			self.Ig_over_Idmax_tr=self.Ig_over_Id_tr[iiVgs]
		if not ("gm_TR" in self.parameters):			# indicate that we have the parameters
			self.parameters.append("Rc_TR")				# contact resistance derived from the Y function
			self.parameters.append("Vth_YTR")			# threshold voltage derived from the Y function
			self.parameters.append("Idfit_TR")			# fit to drain current vs Vgs using polynomial of order order
			self.parameters.append("gm_TR")				# gm derived from above drain current
			self.parameters.append("Y_TR")				# Y function derived from above drain current and gm
			self.parameters.append("YL_TR")				# linear fit of the above Y function over the fraction of Vgs as specified by fractVgsfit
		return ("have data")
########################################################################################################################################################################################
#######################################################################################################################################################################################
# Calculate cubic spline fit of each of the family of curves ONLY for point in families of curves (FOC) showing NO compliance on gate or drain for all measurements
# inputs:
#   smoothfactor is the smoothing factor
#   Vds_Id is the drain voltage used to obtain the Id (drain current) using the spline fit for each Vgs
# Outputs:
# IdvsVdsspline[iVgs](Vds) are the spline-fit functions which return Id (mA/mm) for a given gate voltage index [iVgs] and drain voltage Vds
# not debugged!
# 	def __calc_foc_spline(self,force_calculation=False,smoothfactor=None,Vds_Id=None):
#
# 		# Are there any points in compliance?
# 		if not hasattr(self,'IdsvsVdsfunc') or force_calculation==True:
# 			if not hasattr(self,'Id_foc') or force_calculation==True: self.__readIVfoc()
# 			if not hasattr(self,'Id_foc') or len(self.Id_foc)<2: return None
# 			if 'C' in [g for gs in self.gatestatus_IVfoc for g in gs] or 'C' in [d for ds in self.drainstatus_IVfoc for d in ds]:           # any points in current compliance?
# 				return None
# 			if self.Vds_IVfoc[0]<self.Vds_IVfoc[-1]:    # ascending Vds
# 				self.IdvsVdsfunc=[UnivariateSpline(self.Vds_IVfoc[iVgs],self.Id_IVfoc[iVgs],s=smoothfactor, k=3) for iVgs in range(0,len(self.Vds_IVfoc))]   # IdvsVdsfunc[iVgs]
# 			else:   # decending Vds
# 				self.IdvsVdsfunc=[UnivariateSpline(np.fliplr(self.Vds_IVfoc[iVgs]),np.fliplr(self.Id_IVfoc[iVgs]),s=smoothfactor, k=3) for iVgs in range(0,len(self.Vds_IVfoc))]   # IdvsVdsfunc[iVgs]
#
# 		# calculate Id for the given Vds_Id
# 		# first find out if the requested Vds_Id is within the set of measured Vds for the Vgs curve with the maximum Id
#
# 		Idarray=np.abs(self.Id_IVfoc)
#
# 		iVgs,iVds=np.unravel_index(Idarray.argmax(),Idarray.shape)      # get indices of largest |Id| from the family of curves
# 		self.VdsatIdmax_foc=self.Vds_IVfoc[iVgs][iVds]                  # Vds measured (corrected for lead resistance) at the largest |Id|
#
#
# 		Idspline=[funcIdspline(Vds_Id) for funcIdspline in self.IdvsVdsfunc]        # calculate Idspline[iVgs] for Vds=Vds_Id supplied
# 		self.focsplineatVds={'Id':Idspline, 'Vgs':self.Vgs_IVfoc}

########################################################################################################################################################################################
# Reverse swept IV transfer curves for loop i.e. dual swept transfer curves
########################################################################################################################################################################################
# read calculated parameters derived from the reverse portion of the dual-swept tranfer curve, Id(Vgs)
# 	reverse portion of dual swept transfer curve
# 	contact resistance for  as derived from the Y-function fit
	def Rc_TR(self):
		self.__calc_tr()
		try: self.Rc_tr
		except: return []
		return self.Rc_tr
########################################################################################################################################################################################
# reverse portion of dual swept transfer curve
# 	threshold voltage as derived from the Y-function fit
	def Vth_YTR(self):
		self.__calc_tr()
		try: self.Vth_Ytr
		except: return None
		return self.Vth_Ytr
########################################################################################################################################################################################
#	reverse portion of dual swept transfer curve
#	threshold voltage as derived from a linear fit of the Id
	def Vth_IdTR(self):
		self.__calc_tr()
		try: self.Vth_Idtr
		except: return None
		return self.Vth_Idtr
########################################################################################################################################################################################
#	reverse portion of dual swept transfer curve
#	Id fit to polynomial or spline
	def Idfit_TR(self):
		self.__calc_tr()
		try: self.Idfit_tr
		except: return {}
		return {'Vgs':self.Vgsfit_tr,'I':self.Idfit_tr}
########################################################################################################################################################################################
#	reverse portion of dual swept transfer curve
#	Id linear extrapolation fit
	def Idlin_TR(self):
		self.__calc_tr()
		try: self.Idlin_tr
		except: return {}
		return {'Vgs':self.Vgsfit_tr,'I':self.Idlin_tr}
########################################################################################################################################################################################
#	reverse portion of dual swept transfer curve
#	Leakage Id as calculated from the minimum absolute value of Id from the polynomial fit of Id
	def Idleak_TR(self):
		self.__calc_tr()
		try: self.Idleak_tr
		except: return {}
		return{'Vgs':self.VgsIdleak_tr,'I':self.Idleak_tr}
		#return self.Idleak_tr
########################################################################################################################################################################################
#	reverse portion of dual swept transfer curve
#	Maximum |Idfit| as calculated from the maximum absolute value of Id from the polynomial fit of Id
	def Idmax_TR(self):
		self.__calc_tr()
		try: self.Idmax_tr
		except: return {}
		return {'Vgs':self.VgsIdmax_tr,'I':self.Idmax_tr}
		#return self.Idmax_tr
########################################################################################################################################################################################
#	reverse portion of dual swept transfer curve
#	Idmax/Idmin as calculated from the maximum absolute value of Id from the polynomial fit of Id
#	WARNING! NOTE that this is calculated using the polynomial fit of the measured Id for Imax and the MEASURED value of Id for the Imin
	def Idonoffratio_TR(self):
		self.__calc_tr()
		try: self.Idonoffratio_tr
		except: return {}
		return {'VgsIdleak':self.VgsIdleak_tr,'VgsIdmax':self.VgsIdmax_tr, 'Ir':self.Idonoffratio_tr}
########################################################################################################################################################################################
#	reverse portion of dual swept transfer curve
#	transconductance as calculated from the polynomial or spline fit of Id
	def gm_TR(self,smoothing_factor=None):
		self.__calc_tr(smoothing_factor=smoothing_factor)
		try: self.gm_tr
		except: return {}
		return {'Vgs':self.Vgsfit_tr,'G':self.gm_tr}
########################################################################################################################################################################################
#	reverse portion of dual swept transfer curve
#	maximum positive transconductance as calculated from the polynomial or spline fit of Id
	def gmmax_TR(self,smoothing_factor=None):
		self.__calc_tr(smoothing_factor=smoothing_factor)
		self.__calc_tf(smoothing_factor=smoothing_factor)
		if hasattr(self,'gm_tf'):
			iVgs_gmmax = max(range(0,len(self.gm_tr)), key=lambda iiVgs: self.gm_tr[iiVgs] )
			Vgs=self.Vgs_IVtr[iVgs_gmmax]
		try: self.gmmax_tr
		except: return {}
		return {'G':self.gmmax_tr,'Vgs':Vgs,'Vds':self.Vds_IVtfr, 'Id': self.Id_IVtr[iVgs_gmmax], 'Ig': self.Ig_IVtr[iVgs_gmmax]}
########################################################################################################################################################################################
#	reverse portion of dual swept transfer curve
#	Y-function as calculated from gm and Idfit_T Y is a function of Vgs
	def Yf_TR(self):
		self.__calc_tr()
		try: self.Yf_tf
		except: return {}
		return {'Vgs':self.Vgsfit_tr,'I':self.Yf_tr}
########################################################################################################################################################################################
#	reverse portion of dual swept transfer curve
#	Y-function as calculated from gm and Idfit_T Y is a function of Vgs
	def Yflin_TR(self):
		self.__calc_tr()
		try: self.Yflin_tr
		except: return {}
		return {'Vgs':self.Vgsfit_tr,'I':self.Idlin_tr}
########################################################################################################################################################################################
# return the hysteresis loop voltage for the first two sweeps of the transfer curve
	def Vhyst12(self,force_calculation=False):
		# attempt to get 1st and 2nd sweeps of the transfer curve (must have dual or quad transfer loop data)
		if hasattr(self,"_Vhyst12") and self._Vhyst12!=None and force_calculation==False: return self._Vhyst12
		else:
			if len(self.Id_TF())>0 and len(self.Id_TR())>0:
				self._Vhyst12=calc_xdiff(self.Vgs_IVtf,self.Vgs_IVtr,self.Id_IVtf,self.Id_IVtr)
				return self._Vhyst12
			else: return None
########################################################################################################################################################################################
########################################################################################################################################################################################
# return the worst-case hysteresis loop  delta Id of all the sweeps of the looped transfer curves
	def get_Idhystfocmax(self,force_calculation=False):
		# attempt to family of curves loop data
		if hasattr(self,"Idhystfocmax") and self.Idhystfocmax!=None and force_calculation==False: return self.Idhystfocmax
		else:
			self.__readloopfoc(type="loopfoc")    # get loop family of curves if not already read
			if hasattr(self,"Id_loopfoc1") and len(self.Id_loopfoc1)>0 and len(self.Id_loopfoc2)>0:
				self.Idhystfocmax=max([calc_ydiff(self.Vds_loopfoc1[iVgs],self.Vds_loopfoc2[iVgs],self.Id_loopfoc1[iVgs],self.Id_loopfoc2[iVgs]) for iVgs in range(0,len(self.Id_loopfoc1))])
				return self.Idhystfocmax
			else: return None
########################################################################################################################################################################################
#	reverse portion of dual swept transfer curve
#	find number of data points with compliance or other measurement issues
	def gatestatus_no_TR(self):
		if len(self.gatestatus_TR())>0:
			nobadsites=0
			for s in self.gatestatus_TR():
				if s != 'N': nobadsites += 1  # then there was a gate compliance problem
			return nobadsites
		else: return None
	def drainstatus_no_TR(self):
		if len(self.drainstatus_TR())>0:
			nobadsites=0
			for s in self.drainstatus_TR():
				if s != 'N': nobadsites += 1  # then there was a drain compliance problem
			return  nobadsites
		else: return None
########################################################################################################################################################################################
# Read IV single-sweep transfer curves
#
# read transfer curves (Id vs Vgs) from a datafile
# Inputs: pathname is the directory path and devicename
# returns: Ig, Id, drainstatus, gatestatus vs Vgs. Also returns device parameters
# get devicename from directory
	def __readIVtransfer(self):
		if hasattr(self,'Id_IVt'): return								# then we already have the IV transfer curve so no need to read it again
		if self.devwidth!=None: scalingfactor=self.unitsscaling/self.devwidth								# scale currents to mA/mm
		self.pathname_IV = self.pathname+sub("DC")
		# if not hasattr(self,'filelistingDC'):							# then need to get the file listing for DC parameters (family of curves, single, and dual-swept transfer curves)
		# 	try: self.filelistingDC = os.listdir(self.pathname_IV)			# get the file listing for
		# 	except:
		# 		#print "ERROR directory", self.pathname_IV, "does not exist: returning from readIVtransfer in device_parameter_request.py"
		# 		return "NO DIRECTORY"
		# nodevices=0							# number of files found with the target devicename=self.devicename should be no more than one!
		# for fileIV in self.filelistingDC:
		# 	fileIV.strip()
		# 	if fileIV.endswith("transfer.xls"):
		# 		targettransferdevicename=fileIV.replace('_transfer.xls','')
		# 		if self.devicename==targettransferdevicename:
		# 		#if fileIV.endswith(".xls") and (self.devicename in fileIV) and ("transfer." in fileIV):
		# 			fullfilenameIVt = self.pathname_IV+"/"+fileIV				# form full devicename (path+devicename) of data file
		# 			nodevices+=1
		# if nodevices>1: raise ValueError('ERROR device not unique!')
		fullfilenameIVt="".join([self.pathname_IV,"/",self.devicename,"_transfer.xls"])				# form full devicename (path+devicename) of  transfer curve
		try: fIVt=open(fullfilenameIVt,'r')
		except:
			#print "ERROR from __readIVtransfer in device_parameter_request.py: cannot open file: ",fullfilenameIVt
			return "NO FILE"

		IVfilelines = [a for a in fIVt.read().splitlines()]             # sfilelines is a string array of the lines in the file

		for fileline in IVfilelines:
			# get timestamp
			if "year" in fileline:
				self.IVt_year=fileline.split('\t')[1].lstrip()
			elif "month" in fileline:
				self.IVt_month=fileline.split('\t')[1].lstrip()
			elif "day" in fileline:
				self.IVt_day=fileline.split('\t')[1].lstrip()
			elif "hour" in fileline:
				self.IVt_hour=fileline.split('\t')[1].lstrip()
			elif "minute" in fileline:
				self.IVt_minute=fileline.split('\t')[1].lstrip()
			elif "second" in fileline:
				self.IVt_second=fileline.split('\t')[1].lstrip()
			# get lot and device on wafer
			elif "wafer name" in fileline:
				self.wafer_name=fileline.split('\t')[1].lstrip()
			elif "device name" in fileline:
				self.devicename=fileline.split('\t')[1].lstrip()
			elif "x " in fileline:
				self.x_location=int(fileline.split('\t')[1].lstrip())
			elif "y " in fileline:
				self.y_location=int(fileline.split('\t')[1].lstrip())
			elif "Vds" in fileline:
				self.Vds_IVt=float(fileline.split('\t')[1].lstrip())
			elif "Vgs rate of change" in fileline:                  # Vgs slew rate
				self.Vgsslew_IVt=float(fileline.split('\t')[1].lstrip())
		# now read Vgs, Id, Ig, drainstatus, and gate status
		self.Vgs_IVt = []
		self.Id_IVt = []
		self.Ig_IVt = []
		self.drainstatus_IVt = []
		self.gatestatus_IVt = []
		for fileline in IVfilelines:                                               # load lines from the data file
			if not(('!' in fileline) or ('#' in fileline)):                       # then this line are data
				self.Vgs_IVt.append(float(fileline.split()[0]))
				self.Id_IVt.append(float(fileline.split()[1]))
				self.Ig_IVt.append(float(fileline.split()[2]))
				try: self.drainstatus_IVt.append(fileline.split()[3])
				except:
					print(self.get_devicename())
					raise ValueError("failed read")
				try: self.gatestatus_IVt.append(fileline.split()[4])
				except:
					print(self.get_devicename())
					raise ValueError("failed read")
		if self.devwidth!=None:												# apply scaling only if gate size is specified
			#self.Vds_IVt=np.subtract(self.Vds_IVt,np.multiply(self.leadresistance,self.Id_IVt))				# compensate Vds for lead resistance assuming all lead resistance is in the drain and none in the source
			self.Id_IVt=np.multiply(scalingfactor,self.Id_IVt)
			self.Ig_IVt=np.multiply(scalingfactor,self.Ig_IVt)
		self.parameters.append("IVt")
		fIVt.close()
		return
########################################################################################################################################################################################
# Read IV double-sweep or four-sweep transfer curves
#
# read forward and reverse transfer curves (Id vs Vgs) from a datafile
# Inputs: pathname is the directory path and devicename
# returns: Ig, Id, drainstatus, gatestatus vs Vgs. Also returns device parameters
# get devicename from directory
#
	def __readIVtransferloop(self,type="transferloop"):
		if type=="transferloop" and hasattr(self,'Id_IVtf') and len(self.Id_IVtf)>0: return						# then we already have the first two (forward and reverse) transfer loop parameters
		if type == "transferloop4" and hasattr(self, 'Id_IVt3') and len(self.Id_IVt3) > 0: return  				# this is a four-sweep (two loop) transfer curve and we already have the 3rd and 4th transfer loop parameters
		if self.devwidth!=None: scalingfactor=self.unitsscaling/self.devwidth								# scale currents to mA/mm
		self.pathname_IV = self.pathname+sub("DC")
		if type=="transferloop": fullfilenameIVtfr="".join([self.pathname_IV,"/",self.devicename,"_transferloop.xls"])				# form full devicename (path+devicename) of  transfer curve
		elif type=="transferloop4": fullfilenameIVtfr="".join([self.pathname_IV,"/",self.devicename,"_transferloop4.xls"])				# form full devicename (path+devicename) of  transfer curve for the four-sweep (dual-loop) transfer curve
		try: fIVtfr=open(fullfilenameIVtfr,'r')
		except: return "NO FILE"
			# if type=="transferloop":			# then we are reading the 1st or 2nd transfer curve of a transferloop4 file and there is no tranferloop file so look for a transferloop4 file instead
			# 	fullfilenameIVtfr = "".join([self.pathname_IV, "/", self.devicename, "_transferloop4.xls"])			# no transferloop file so try for transferloop4 file
			# 	try: fIVtfr=open(fullfilenameIVtfr,'r')
			# 	except: return "NO FILE"
			#else: return "NO FILE"
		IVfilelines = [a for a in fIVtfr.read().splitlines()]             # sfilelines is a string array of the lines in the file
		#print("from line 2061 device_parameter_request.py",self.devicename)	# debug
		for fileline in IVfilelines:
			# get timestamp
			if "year" in fileline:
				self.IVtfr_year=fileline.split('\t')[1].lstrip()
			elif "month" in fileline:
				self.IVtfr_month=fileline.split('\t')[1].lstrip()
			elif "day" in fileline:
				self.IVtfr_day=fileline.split('\t')[1].lstrip()
			elif "hour" in fileline:
				self.IVtfr_hour=fileline.split('\t')[1].lstrip()
			elif "minute" in fileline:
				self.IVtfr_minute=fileline.split('\t')[1].lstrip()
			elif "second" in fileline:
				self.IVtfr_second=fileline.split('\t')[1].lstrip()
			# get lot and device on wafer
			elif "wafer name" in fileline:
				self.wafer_name=fileline.split('\t')[1].lstrip()
			elif "device name" in fileline:
				self.devicename=fileline.split('\t')[1].lstrip()
			elif "x " in fileline:
				self.x_location=int(fileline.split('\t')[1].lstrip())
			elif "y " in fileline:
				self.y_location=int(fileline.split('\t')[1].lstrip())
			elif "Vds" in fileline and "drain voltage" in fileline:
				self.Vds_IVtfr=float(fileline.split('\t')[1].lstrip())
			elif "Vgs rate of change" in fileline:                  # Vgs slew rate
				if type=="transferloop":
					self.Vgsslew_IVtfr=float(fileline.split('\t')[1].lstrip())
				elif type=="transferloop4":
					self.Vgsslew_IVt2loop=float(fileline.split('\t')[1].lstrip())

		# now read Vgs, Id, Ig, drainstatus, and gate status for the forward swept transfer curve

		if type=="transferloop" or type=="transferloop4":
			# first sweep
			self.Vgs_IVtf = col.deque()
			self.Id_IVtf = col.deque()
			self.Ig_IVtf = col.deque()
			self.drainstatus_IVtf = col.deque()
			self.gatestatus_IVtf = col.deque()
			# 2nd sweep (reverse Vgs direction relative to first sweep)
			self.Vgs_IVtr = col.deque()
			self.Id_IVtr = col.deque()
			self.Ig_IVtr = col.deque()
			self.drainstatus_IVtr = col.deque()
			self.gatestatus_IVtr = col.deque()

		if type=="transferloop4":
			# 3rd sweep (same Vgs direction as first sweep)
			self.Vgs_IVt3 = col.deque()
			self.Id_IVt3 = col.deque()
			self.Ig_IVt3 = col.deque()
			self.drainstatus_IVt3 = col.deque()
			self.gatestatus_IVt3 = col.deque()
			# 4th sweep (reverse Vgs direction as first sweep)
			self.Vgs_IVt4 = col.deque()
			self.Id_IVt4 = col.deque()
			self.Ig_IVt4 = col.deque()
			self.drainstatus_IVt4 = col.deque()
			self.gatestatus_IVt4 = col.deque()

		for fileline in IVfilelines:                                               # load lines from the data file
			if (type=="transferloop" or type=="transferloop4") and ("#" in fileline) and (("forward" in fileline) or ("1st Vgs sweep" in fileline)) and ("sweep" in fileline):				# first sweep
				forwardreverse = "forwardsweep"
			elif (type=="transferloop" or type=="transferloop4") and ("#" in fileline) and (("reverse" in fileline) or ("2nd Vgs sweep" in fileline)) and ("sweep" in fileline):			# 2nd sweep (reverse Vgs direction relative to first sweep)
				forwardreverse = "reversesweep"
			elif type=="transferloop4" and ("#" in fileline) and ("3rd Vgs sweep" in fileline) and ("sweep" in fileline):			# 3rd sweep (same Vgs direction as first sweep)
				forwardreverse = "3rdsweep"
			elif type=="transferloop4" and ("#" in fileline) and ("4th Vgs sweep" in fileline) and ("sweep" in fileline):  		# 4th sweep (reverse Vgs direction as first sweep)
				forwardreverse = "4thsweep"
			elif not(('!' in fileline) or ('#' in fileline)) and (forwardreverse == "forwardsweep"):                       # then this line are data
				self.Vgs_IVtf.append(float(fileline.split()[0]))
				self.Id_IVtf.append(float(fileline.split()[1]))
				self.Ig_IVtf.append(float(fileline.split()[2]))

				try: self.drainstatus_IVtf.append(fileline.split()[3])
				except:
					print(self.get_devicename())
					raise ValueError("failed read")
				try: self.gatestatus_IVtf.append(fileline.split()[4])
				except:
					print(self.get_devicename())
					raise ValueError("failed read")
			elif not(('!' in fileline) or ('#' in fileline)) and (forwardreverse == "reversesweep"):                       # then this line are data
				self.Vgs_IVtr.append(float(fileline.split()[0]))
				self.Id_IVtr.append(float(fileline.split()[1]))
				self.Ig_IVtr.append(float(fileline.split()[2]))
				try: self.drainstatus_IVtr.append(fileline.split()[3])
				except:
					print(self.get_devicename())
					raise ValueError("failed read")
				try: self.gatestatus_IVtr.append(fileline.split()[4])
				except:
					print(self.get_devicename())
					raise ValueError("failed read")
			elif not (('!' in fileline) or ('#' in fileline)) and (forwardreverse == "3rdsweep"):  # then this line are data
				self.Vgs_IVt3.append(float(fileline.split()[0]))
				self.Id_IVt3.append(float(fileline.split()[1]))
				self.Ig_IVt3.append(float(fileline.split()[2]))
				try:
					self.drainstatus_IVt3.append(fileline.split()[3])
				except:
					print(self.get_devicename())
					raise ValueError("failed read")
				try:
					self.gatestatus_IVt3.append(fileline.split()[4])
				except:
					print(self.get_devicename())
					raise ValueError("failed read")
			elif not (('!' in fileline) or ('#' in fileline)) and (forwardreverse == "4thsweep"):  # then this line are data
				self.Vgs_IVt4.append(float(fileline.split()[0]))
				self.Id_IVt4.append(float(fileline.split()[1]))
				self.Ig_IVt4.append(float(fileline.split()[2]))
				try:
					self.drainstatus_IVt4.append(fileline.split()[3])
				except:
					print(self.get_devicename())
					raise ValueError("failed read")
				try:
					self.gatestatus_IVt4.append(fileline.split()[4])
				except:
					print(self.get_devicename())
					raise ValueError("failed read")
		if self.devwidth!=None:												# apply scaling only if gate size is specified
			#self.Vds_IVtfr=np.subtract(Vds_IVtfr, np.multiply(self.leadresistance, self.Id_IVtf))				# compensate Vds for lead resistance assuming all lead resistance is in the drain and none in the source
			#self.Vds_IVtfr=np.subtract(Vds_IVtfr, np.multiply(self.leadresistance, self.Id_IVtr))				# compensate Vds for lead resistance assuming all lead resistance is in the drain and none in the source
			if len(self.Id_IVtf)>0:
				self.Id_IVtf=np.multiply(scalingfactor,self.Id_IVtf)
				self.Ig_IVtf=np.multiply(scalingfactor,self.Ig_IVtf)
			if len(self.Id_IVtr)>0:
				self.Id_IVtr=np.multiply(scalingfactor,self.Id_IVtr)
				self.Ig_IVtr=np.multiply(scalingfactor,self.Ig_IVtr)
			if type=="transferloop4" and len(self.Id_IVt3) > 0:
				self.Id_IVt3 = np.multiply(scalingfactor, self.Id_IVt3)
				self.Ig_IVt3 = np.multiply(scalingfactor, self.Ig_IVt3)
			if type=="transferloop4" and len(self.Id_IVt4) > 0:
				self.Id_IVt4 = np.multiply(scalingfactor, self.Id_IVt4)
				self.Ig_IVt4 = np.multiply(scalingfactor, self.Ig_IVt4)

		if type=="transferloop" and len(self.Id_IVtf) > 0: self.parameters.append("IVtf")
		if type=="transferloop" and len(self.Id_IVtr) > 0: self.parameters.append("IVtr")
		if type=="transferloop4" and len(self.Id_IVt3) > 0: self.parameters.append("IVt3")
		if type=="transferloop4" and len(self.Id_IVt4) > 0: self.parameters.append("IVt4")
		fIVtfr.close()
		return
########################################################################################################################################################################################
# read the IV family of curves
# The currents are scaled to the total gate width IF it's available. Else NO scaling is performed
# Drain voltage is modified according to the lead resistance (if given) which acts to reduce the drain voltage applied AT THE DEVICE itself. All lead resistance is assumed to be in the drain and none in the source
# data indices are [iVgs][iVds]
	def __readIVfoc(self):
		#if "IVfoc" in self.parameters:
		if hasattr(self,'Id_IVfoc'): return						# then we have the family of curves and do not need to read it from the file
		#print("from device_parameter_request.py line 2036 _readIVfoc()",self.devicename)
		if self.devwidth!=None: scalingfactor=self.unitsscaling/self.devwidth								# scale currents to mA/mm
		self.pathname_IV = self.pathname+sub("DC")
		fullfilenameIVfoc = "".join([self.pathname_IV,"/",self.devicename,"_foc.xls"])				# form full devicename (path+devicename) of family of curves file
		try: fIVfoc=open(fullfilenameIVfoc,'r')
		except:
			#print "ERROR from __readIVfoc() in device_parameter_request.py: cannot open file: ",self.pathname_IV+"/"+fileIV
			return "NO FILE"
		IVfilelines = [a for a in fIVfoc.read().splitlines()]             # sfilelines is a string array of the lines in the file

		for fileline in IVfilelines:
			# get timestamp
			if "year" in fileline:
				self.IVfoc_year=fileline.split('\t')[1].lstrip()
			elif "month" in fileline:
				self.IVfoc_month=fileline.split('\t')[1].lstrip()
			elif "day" in fileline:
				self.IVfoc_day=fileline.split('\t')[1].lstrip()
			elif "hour" in fileline:
				self.IVfoc_hour=fileline.split('\t')[1].lstrip()
			elif "minute" in fileline:
				self.IVfoc_minute=fileline.split('\t')[1].lstrip()
			elif "second" in fileline:
				self.IVfoc_second=fileline.split('\t')[1].lstrip()
			# get lot and device on wafer
			elif "wafer name" in fileline:
				self.wafer_name=fileline.split('\t')[1].lstrip()
			elif "device name" in fileline:
				self.devicename=fileline.split('\t')[1].lstrip()
			elif "x " in fileline:
				self.x_location=int(fileline.split('\t')[1].lstrip())
			elif "y " in fileline:
				self.y_location=int(fileline.split('\t')[1].lstrip())
		# now read Vgs, Id, Ig, drainstatus, and gate status for the forward swept transfer curve
		self.Vgs_IVfoc = col.deque()
		self.Vds_IVfoc =col.deque()
		self.Id_IVfoc = col.deque()
		self.Ig_IVfoc = col.deque()
		self.drainstatus_IVfoc = col.deque()
		self.gatestatus_IVfoc = col.deque()

		for fileline in IVfilelines:                                               # load lines from the data file
			if not(('!' in fileline) or ('#' in fileline)):                       # then this line are data
				#print("from device_parameter_request.py line 2648",fileline,float(fileline.split()[0]),len(self.Vgs_IVfoc))
				#print("from device_parameter_request.py line 2649",self.devicename)
				self.Vgs_IVfoc[-1].append(float(fileline.split()[0]))
				#print("from device_parameter_request.py line 2649 len(Vgs_IVfoc)= ",len(self.Vgs_IVfoc))
				#print("from line 1793 in device_parameter_request.py self.Vgs_IVfoc",float(fileline.split()[0]),self.Vgs_IVfoc[-1] )
				self.Vds_IVfoc[-1].append(float(fileline.split()[1]))
				self.Id_IVfoc[-1].append(float(fileline.split()[2]))
				self.Ig_IVfoc[-1].append(float(fileline.split()[3]))
				self.drainstatus_IVfoc[-1].append(fileline.split()[4])
				try:
					self.gatestatus_IVfoc[-1].append(fileline.split()[5])
				except:
					raise ValueError("ERROR! in reading gatestatus")
					#print ("from read foc error",fileline)
			elif (('!' in fileline) or ('#' in fileline)) and ("Vgs" in fileline) and ("=" in fileline):               # then move to the next gate voltage
				self.Vgs_IVfoc.append([])
				self.Vds_IVfoc.append([])
				self.Id_IVfoc.append([])
				self.Ig_IVfoc.append([])
				self.drainstatus_IVfoc.append([])
				self.gatestatus_IVfoc.append([])
		if self.devwidth!=None:												# apply scaling only if gate size is specified
			#if "SHORT" in self.devicename: print("from line 3014 in device_parameter_request.py ", self.devicename, self.Id_IVfoc,self.Vds_IVfoc)
			self.Vds_IVfoc=np.subtract(self.Vds_IVfoc,np.multiply(self.leadresistance,self.Id_IVfoc))				# compensate Vds for lead resistance assuming all lead resistance is in the drain and none in the source
			self.Id_IVfoc=np.multiply(scalingfactor,self.Id_IVfoc)
			self.Ig_IVfoc=np.multiply(scalingfactor,self.Ig_IVfoc)
			#if "SHORT" in self.devicename: print("from line 3018 in device_parameter_request.py ", self.devicename, self.leadresistance)
		self.parameters.append("IVfoc")
		fIVfoc.close()
		return
########################################################################################################################
# get number of times that the drain current reading is not normal in a family of curves IV
# "not normal" means that the data cannot be trusted due to current compliance or other problems
	def drainstatus_no_foc(self):
		if len(self.drainstatus_foc())==None: return None
		if not hasattr(self,"nobaddrainsites"):		# then and only then do we need to calculate the number of bad sites
			self.nobaddrainsites=0
			#for igate in range(0,len(self.drainstatus_foc())):
				# for idrain in range(0,len(self.drainstatus_foc()[igate])):
				# 	if self.drainstatus_foc()[igate][idrain] != "N":			# then there was a gate compliance problem
				# 		self.nobaddrainsites +=1
			for igate in range(0, len(self.drainstatus_foc())):					# iterate through gate bias points
				for d in self.drainstatus_foc()[igate]:							# iterate through drain bias points
					if d !="N": self.nobaddrainsites +=1
		return  self.nobaddrainsites
########################################################################################################################
# get number of times that the gate current reading is not normal in a family of curves IV
# "not normal" means that the data cannot be trusted due to current compliance or other problems
	def gatestatus_no_foc(self):
		if len(self.gatestatus_foc())==0: return None
		if not hasattr(self,"nobadgatesites"):	# then and only then do we need to calculate the number of bad sites
			self.nobadgatesites=0
			# for igate in range(0,len(self.gatestatus_foc())):
			# 	for idrain in range(0,len(self.gatestatus_foc()[igate])):
			# 		if self.gatestatus_foc()[igate][idrain] != "N":			# then there was a gate compliance problem
			# 			self.nobadgatesites +=1
			for igate in range(0, len(self.gatestatus_foc())):
				for d in self.gatestatus_foc()[igate]:  # iterate through drain bias points
					if d != "N": self.nobadgatesites += 1
		return  self.nobadgatesites
########################################################################################################################################################################################
########################################################################################################################################################################################
# read the IV family of curves which has been measured with both a forward and reverse Vds sweep to observe hysteresis on the drain voltage (2 sweeps, one loop) OR with 4-sweeps of Vds (two-loops)
# The currents are scaled to the total gate width IF it's available. Else NO scaling is performed
# Drain voltage is modified according to the lead resistance (if given) which acts to reduce the drain voltage applied AT THE DEVICE itself. All lead resistance is assumed to be in the drain and none in the source
	def __readloopfoc(self,forceread=False,type="loopfoc"):
		if (not forceread) and ((type=="loopfoc" and hasattr(self,'Id_loopfoc1')) or (type=="loop4foc" and hasattr(self,'Id_4loopfoc1'))): return						# then we have the family of curves and do not need to read it from the file unless the user forces a read
		if self.devwidth!=None: scalingfactor=self.unitsscaling/self.devwidth								# scale currents to mA/mm
		self.pathname_IV = self.pathname+sub("DC")
		fullfilenameIVfoc = "".join([self.pathname_IV,"/",self.devicename,"_"+type+".xls"])				# form full devicename (path+devicename) of family of curves file
		try: fIVfoc=open(fullfilenameIVfoc,'r')
		except:
			return "NO FILE"
		IVfilelines = [a for a in fIVfoc.read().splitlines()]             # sfilelines is a string array of the lines in the file

		for fileline in IVfilelines:
			# get timestamp
			if "year" in fileline:
				self.loopfoc_year=fileline.split('\t')[1].lstrip()
			elif "month" in fileline:
				self.loopfoc_month=fileline.split('\t')[1].lstrip()
			elif "day" in fileline:
				self.loopfoc_day=fileline.split('\t')[1].lstrip()
			elif "hour" in fileline:
				self.loopfoc_hour=fileline.split('\t')[1].lstrip()
			elif "minute" in fileline:
				self.loopfoc_minute=fileline.split('\t')[1].lstrip()
			elif "second" in fileline:
				self.loopfoc_second=fileline.split('\t')[1].lstrip()
			# get lot and device on wafer
			elif "wafer name" in fileline:
				self.wafer_name=fileline.split('\t')[1].lstrip()
			elif "device name" in fileline:
				self.devicename=fileline.split('\t')[1].lstrip()
			elif "x " in fileline:
				self.x_location=int(fileline.split('\t')[1].lstrip())
			elif "y " in fileline:
				self.y_location=int(fileline.split('\t')[1].lstrip())
		# now read Vgs, Id, Ig, drainstatus, and gate status for the forward swept transfer curve
		# first Vds sweep
		if type=="loopfoc":
			self.Vgs_loopfoc1 = col.deque()
			self.Vds_loopfoc1 =col.deque()
			self.Id_loopfoc1 = col.deque()
			self.Ig_loopfoc1 = col.deque()
			self.drainstatus_loopfoc1 = col.deque()
			self.gatestatus_loopfoc1 = col.deque()
			# 2nd Vds sweep
			self.Vgs_loopfoc2 = col.deque()
			self.Vds_loopfoc2 =col.deque()
			self.Id_loopfoc2 = col.deque()
			self.Ig_loopfoc2 = col.deque()
			self.drainstatus_loopfoc2 = col.deque()
			self.gatestatus_loopfoc2 = col.deque()
		elif type=="loop4foc":
			self.Vgs_4loopfoc1 = col.deque()
			self.Vds_4loopfoc1 =col.deque()
			self.Id_4loopfoc1 = col.deque()
			self.Ig_4loopfoc1 = col.deque()
			self.drainstatus_4loopfoc1 = col.deque()
			self.gatestatus_4loopfoc1 = col.deque()
			# 2nd Vds sweep
			self.Vgs_4loopfoc2 = col.deque()
			self.Vds_4loopfoc2 =col.deque()
			self.Id_4loopfoc2 = col.deque()
			self.Ig_4loopfoc2 = col.deque()
			self.drainstatus_4loopfoc2 = col.deque()
			self.gatestatus_4loopfoc2 = col.deque()
			# 3rd Vds sweep
			self.Vgs_4loopfoc3 = col.deque()
			self.Vds_4loopfoc3 =col.deque()
			self.Id_4loopfoc3 = col.deque()
			self.Ig_4loopfoc3 = col.deque()
			self.drainstatus_4loopfoc3 = col.deque()
			self.gatestatus_4loopfoc3 = col.deque()
			# 4th Vds sweep
			self.Vgs_4loopfoc4 = col.deque()
			self.Vds_4loopfoc4 =col.deque()
			self.Id_4loopfoc4 = col.deque()
			self.Ig_4loopfoc4 = col.deque()
			self.drainstatus_4loopfoc4 = col.deque()
			self.gatestatus_4loopfoc4 = col.deque()
		for fileline in IVfilelines:                                               # load lines from the data file
			if type=="loopfoc":
				if (('!' in fileline) or ('#' in fileline)) and ("Vgs" in fileline) and ("=" in fileline):               # then move to the next gate voltage
					if "sweep 1" in fileline:
						sweepno=1
						self.Vgs_loopfoc1.append([])
						self.Vds_loopfoc1.append([])
						self.Id_loopfoc1.append([])
						self.Ig_loopfoc1.append([])
						self.drainstatus_loopfoc1.append([])
						self.gatestatus_loopfoc1.append([])
					elif "sweep 2" in fileline:
						sweepno=2
						self.Vgs_loopfoc2.append([])
						self.Vds_loopfoc2.append([])
						self.Id_loopfoc2.append([])
						self.Ig_loopfoc2.append([])
						self.drainstatus_loopfoc2.append([])
						self.gatestatus_loopfoc2.append([])

				elif not(('!' in fileline) or ('#' in fileline)):                       # then this line are data [iVgs][iVds]
					if sweepno==1:  # sweep 1 of Vds
						self.Vgs_loopfoc1[-1].append(float(fileline.split()[0]))
						self.Vds_loopfoc1[-1].append(float(fileline.split()[1]))
						self.Id_loopfoc1[-1].append(float(fileline.split()[2]))
						self.Ig_loopfoc1[-1].append(float(fileline.split()[3]))
						self.drainstatus_loopfoc1[-1].append(fileline.split()[4])
						try:
							self.gatestatus_loopfoc1[-1].append(fileline.split()[5])
						except:
							raise ValueError("ERROR! in reading gatestatus1")
					elif sweepno==2:       # sweep 2 of Vds
						self.Vgs_loopfoc2[-1].append(float(fileline.split()[0]))
						self.Vds_loopfoc2[-1].append(float(fileline.split()[1]))
						self.Id_loopfoc2[-1].append(float(fileline.split()[2]))
						self.Ig_loopfoc2[-1].append(float(fileline.split()[3]))
						self.drainstatus_loopfoc2[-1].append(fileline.split()[4])
						try:
							self.gatestatus_loopfoc2[-1].append(fileline.split()[5])
						except:
							raise ValueError("ERROR! in reading gatestatus2")
				#else: raise ValueError("ERROR! no data match type")
			elif type=="loop4foc":
				if (('!' in fileline) or ('#' in fileline)) and ("Vgs" in fileline) and ("=" in fileline):               # then move to the next gate voltage
					if "sweep 1" in fileline:
						sweepno=1
						self.Vgs_4loopfoc1.append([])
						self.Vds_4loopfoc1.append([])
						self.Id_4loopfoc1.append([])
						self.Ig_4loopfoc1.append([])
						self.drainstatus_4loopfoc1.append([])
						self.gatestatus_4loopfoc1.append([])
					elif "sweep 2" in fileline:
						sweepno=2
						self.Vgs_4loopfoc2.append([])
						self.Vds_4loopfoc2.append([])
						self.Id_4loopfoc2.append([])
						self.Ig_4loopfoc2.append([])
						self.drainstatus_4loopfoc2.append([])
						self.gatestatus_4loopfoc2.append([])
					elif "sweep 3" in fileline:
						sweepno=3
						self.Vgs_4loopfoc3.append([])
						self.Vds_4loopfoc3.append([])
						self.Id_4loopfoc3.append([])
						self.Ig_4loopfoc3.append([])
						self.drainstatus_4loopfoc3.append([])
						self.gatestatus_4loopfoc3.append([])
					elif "sweep 4" in fileline:
						sweepno=4
						self.Vgs_4loopfoc4.append([])
						self.Vds_4loopfoc4.append([])
						self.Id_4loopfoc4.append([])
						self.Ig_4loopfoc4.append([])
						self.drainstatus_4loopfoc4.append([])
						self.gatestatus_4loopfoc4.append([])

				elif not(('!' in fileline) or ('#' in fileline)):                       # then this line are data [iVgs][iVds]
					if sweepno==1:  # sweep 1 of Vds
						self.Vgs_4loopfoc1[-1].append(float(fileline.split()[0]))
						self.Vds_4loopfoc1[-1].append(float(fileline.split()[1]))
						self.Id_4loopfoc1[-1].append(float(fileline.split()[2]))
						self.Ig_4loopfoc1[-1].append(float(fileline.split()[3]))
						self.drainstatus_4loopfoc1[-1].append(fileline.split()[4])
						try:
							self.gatestatus_4loopfoc1[-1].append(fileline.split()[5])
						except:
							raise ValueError("ERROR! in reading gatestatus1")
					elif sweepno==2:       # sweep 2 of Vds
						self.Vgs_4loopfoc2[-1].append(float(fileline.split()[0]))
						self.Vds_4loopfoc2[-1].append(float(fileline.split()[1]))
						self.Id_4loopfoc2[-1].append(float(fileline.split()[2]))
						self.Ig_4loopfoc2[-1].append(float(fileline.split()[3]))
						self.drainstatus_4loopfoc2[-1].append(fileline.split()[4])
						try:
							self.gatestatus_4loopfoc2[-1].append(fileline.split()[5])
						except:
							raise ValueError("ERROR! in reading gatestatus2")
					elif sweepno==3:       # sweep 3 of Vds
						self.Vgs_4loopfoc3[-1].append(float(fileline.split()[0]))
						self.Vds_4loopfoc3[-1].append(float(fileline.split()[1]))
						self.Id_4loopfoc3[-1].append(float(fileline.split()[2]))
						self.Ig_4loopfoc3[-1].append(float(fileline.split()[3]))
						self.drainstatus_4loopfoc3[-1].append(fileline.split()[4])
						try:
							self.gatestatus_4loopfoc3[-1].append(fileline.split()[5])
						except:
							raise ValueError("ERROR! in reading gatestatus3")
					elif sweepno==4:       # sweep 4 of Vds
						self.Vgs_4loopfoc4[-1].append(float(fileline.split()[0]))
						self.Vds_4loopfoc4[-1].append(float(fileline.split()[1]))
						self.Id_4loopfoc4[-1].append(float(fileline.split()[2]))
						self.Ig_4loopfoc4[-1].append(float(fileline.split()[3]))
						self.drainstatus_4loopfoc4[-1].append(fileline.split()[4])
						try:
							self.gatestatus_4loopfoc4[-1].append(fileline.split()[5])
						except:
							raise ValueError("ERROR! in reading gatestatus4")
				#else: raise ValueError("ERROR! no data match type for Vds 4-sweep")

		if self.devwidth!=None:												# apply scaling only if gate size is specified
			if type=="loopfoc":
				self.Vds_loopfoc1=np.subtract(self.Vds_loopfoc1,np.multiply(self.leadresistance,self.Id_loopfoc1))				# compensate Vds for lead resistance assuming all lead resistance is in the drain and none in the source
				self.Id_loopfoc1=np.multiply(scalingfactor,self.Id_loopfoc1)
				self.Ig_loopfoc1=np.multiply(scalingfactor,self.Ig_loopfoc1)
				self.Vds_loopfoc2=np.subtract(self.Vds_loopfoc2,np.multiply(self.leadresistance,self.Id_loopfoc2))				# compensate Vds for lead resistance assuming all lead resistance is in the drain and none in the source
				self.Id_loopfoc2=np.multiply(scalingfactor,self.Id_loopfoc2)
				self.Ig_loopfoc2=np.multiply(scalingfactor,self.Ig_loopfoc2)
			elif type=="loop4foc":
				self.Vds_4loopfoc1=np.subtract(self.Vds_4loopfoc1,np.multiply(self.leadresistance,self.Id_4loopfoc1))				# compensate Vds for lead resistance assuming all lead resistance is in the drain and none in the source
				self.Id_4loopfoc1=np.multiply(scalingfactor,self.Id_4loopfoc1)
				self.Ig_4loopfoc1=np.multiply(scalingfactor,self.Ig_4loopfoc1)

				self.Vds_4loopfoc2=np.subtract(self.Vds_4loopfoc2,np.multiply(self.leadresistance,self.Id_4loopfoc2))				# compensate Vds for lead resistance assuming all lead resistance is in the drain and none in the source
				self.Id_4loopfoc2=np.multiply(scalingfactor,self.Id_4loopfoc2)
				self.Ig_4loopfoc2=np.multiply(scalingfactor,self.Ig_4loopfoc2)

				self.Vds_4loopfoc3=np.subtract(self.Vds_4loopfoc3,np.multiply(self.leadresistance,self.Id_4loopfoc3))				# compensate Vds for lead resistance assuming all lead resistance is in the drain and none in the source
				self.Id_4loopfoc3=np.multiply(scalingfactor,self.Id_4loopfoc3)
				self.Ig_4loopfoc3=np.multiply(scalingfactor,self.Ig_4loopfoc3)

				self.Vds_4loopfoc4=np.subtract(self.Vds_4loopfoc4,np.multiply(self.leadresistance,self.Id_4loopfoc4))				# compensate Vds for lead resistance assuming all lead resistance is in the drain and none in the source
				self.Id_4loopfoc4=np.multiply(scalingfactor,self.Id_4loopfoc4)
				self.Ig_4loopfoc4=np.multiply(scalingfactor,self.Ig_4loopfoc4)
			else: raise ValueError("ERROR! no datatypes match for Vds loop FOC")
		#self.parameters.append("loopfoc")
		fIVfoc.close()
		return
########################################################################################################################
########################################################################################################################################################################################
# return values from the IV family of curves measurements which use a controlled slew rate sweep of Vds to capture hysteresis in the drain voltage
# if swapI is True then Id[iVds][iVgs] unsmoothed raw measured data from the IV family of curves where iVds is the drain voltage index and iVgs the gate voltage index.
# else: if swapI is False then Id[iVgs][iVds] unsmoothed raw measured data from the IV family of curves where iVds is the drain voltage index and iVgs the gate voltage index.
# same data as IdIV_foc except gate and drain indices are swapped and the Vds=0 datapoint is eliminated
# Note that if swapindx==True then the return data are indexed data[iVds][iVgs] where iVds and iVgs are the drain and gate voltage indices respectively, else data are indexed as [iVgs][iVds]
	def get_Id_loopfoc1(self,swapindx=True):
		self.__readloopfoc(type="loopfoc")
		if not hasattr(self,'Id_loopfoc1'): return {}
		if not hasattr(self,'Vgs_loopfocfirstVds'): self.Vgs_loopfocfirstVds=[Vgs[0] for Vgs in self.Vgs_loopfoc1]		# get gate voltage setting for each of the Vds sweeps of the foc as the gate voltage at the start of the sweep
		if swapindx: return {'Vds':swapindex(self.Vds_loopfoc1), 'Vgs':swapindex(self.Vgs_loopfoc1), 'Vgs_loopfocfirstVds':self.Vgs_loopfocfirstVds, 'Id':swapindex(self.Id_loopfoc1), 'Ig':swapindex(self.Ig_loopfoc1), \
							 'gatestatus':swapindex(self.gatestatus_loopfoc1), 'drainstatus':swapindex(self.drainstatus_loopfoc1)}
		else: return {'Vds':self.Vds_loopfoc1[0],'Vgs':self.Vgs_loopfoc1,'Vgs_loopfocfirstVds':self.Vgs_loopfocfirstVds, 'Id':self.Id_loopfoc1,'Ig':self.Ig_loopfoc1, 'gatestatus':self.gatestatus_loopfoc1, 'drainstatus':self.drainstatus_loopfoc1}
########################################################################################################################################################################################
########################################################################################################################################################################################
# return values from the IV family of curves measurements which use a controlled slew rate sweep of Vds to capture hysteresis in the drain voltage
# if swapI is True then Id[iVds][iVgs] unsmoothed raw measured data from the IV family of curves where iVds is the drain voltage index and iVgs the gate voltage index.
# else: if swapI is False then Id[iVgs][iVds] unsmoothed raw measured data from the IV family of curves where iVds is the drain voltage index and iVgs the gate voltage index.
# same data as IdIV_foc except gate and drain indices are swapped and the Vds=0 datapoint is eliminated
# Note that the return data are indexed data[iVds][iVgs] where iVds and iVgs are the drain and gate voltage indices respectively
	def get_Id_loopfoc2(self,swapindx=True):
		self.__readloopfoc(type="loopfoc")
		if not hasattr(self,'Id_loopfoc2'): return {}
		if not hasattr(self,'Vgs_loopfocfirstVds'): self.Vgs_loopfocfirstVds=[Vgs[0] for Vgs in self.Vgs_loopfoc2]		# get gate voltage setting for each of the Vds sweeps of the foc as the gate voltage at the start of the sweep
		if swapindx: return {'Vds':swapindex(self.Vds_loopfoc2), 'Vgs':swapindex(self.Vgs_loopfoc2), 'Vgs_loopfocfirstVds':self.Vgs_loopfocfirstVds, 'Id':swapindex(self.Id_loopfoc2), 'Ig':swapindex(self.Ig_loopfoc2), \
							 'gatestatus':swapindex(self.gatestatus_loopfoc2), 'drainstatus':swapindex(self.drainstatus_loopfoc2)}
		else: return {'Vds':self.Vds_loopfoc2[0],'Vgs':self.Vgs_loopfoc2,'Vgs_loopfocfirstVds':self.Vgs_loopfocfirstVds, 'Id':self.Id_loopfoc2,'Ig':self.Ig_loopfoc2, 'gatestatus':self.gatestatus_loopfoc2, 'drainstatus':self.drainstatus_loopfoc2}
########################################################################################################################################################################################
########################################################################################################################################################################################
# return values from the IV family of curves measurements which use a controlled slew rate sweep of Vds to capture hysteresis in the drain voltage
# if swapI is True then Id[iVds][iVgs] unsmoothed raw measured data from the IV family of curves where iVds is the drain voltage index and iVgs the gate voltage index.
# else: if swapI is False then Id[iVgs][iVds] unsmoothed raw measured data from the IV family of curves where iVds is the drain voltage index and iVgs the gate voltage index.
# same data as IdIV_foc except gate and drain indices are swapped and the Vds=0 datapoint is eliminated
# Note that the return data are indexed data[iVds][iVgs] where iVds and iVgs are the drain and gate voltage indices respectively
	def get_Id_4loopfoc1(self,swapindx=True):
		self.__readloopfoc(type="loop4foc")
		if not hasattr(self,'Id_4loopfoc1'): return {}
		if not hasattr(self,'Vgs_4loopfocfirstVds'): self.Vgs_4loopfocfirstVds=[Vgs[0] for Vgs in self.Vgs_4loopfoc1]		# get gate voltage setting for each of the Vds sweeps of the foc as the gate voltage at the start of the sweep
		if swapindx: return {'Vds':swapindex(self.Vds_4loopfoc1), 'Vgs':swapindex(self.Vgs_4loopfoc1), 'Vgs_4loopfocfirstVds':self.Vgs_4loopfocfirstVds, 'Id':swapindex(self.Id_4loopfoc1), 'Ig':swapindex(self.Ig_4loopfoc1), \
							 'gatestatus':swapindex(self.gatestatus_4loopfoc1), 'drainstatus':swapindex(self.drainstatus_4loopfoc1)}
		else: return {'Vds':self.Vds_4loopfoc1[0],'Vgs':self.Vgs_4loopfoc1,'Vgs_loopfocfirstVds':self.Vgs_4loopfocfirstVds, 'Id':self.Id_4loopfoc1,'Ig':self.Ig_4loopfoc1, 'gatestatus':self.gatestatus_4loopfoc1, 'drainstatus':self.drainstatus_4loopfoc1}
########################################################################################################################################################################################
########################################################################################################################################################################################
# return values from the IV family of curves measurements which use a controlled slew rate sweep of Vds to capture hysteresis in the drain voltage
# if swapI is True then Id[iVds][iVgs] unsmoothed raw measured data from the IV family of curves where iVds is the drain voltage index and iVgs the gate voltage index.
# else: if swapI is False then Id[iVgs][iVds] unsmoothed raw measured data from the IV family of curves where iVds is the drain voltage index and iVgs the gate voltage index.
# same data as IdIV_foc except gate and drain indices are swapped and the Vds=0 datapoint is eliminated
# Note that the return data are indexed data[iVds][iVgs] where iVds and iVgs are the drain and gate voltage indices respectively
	def get_Id_4loopfoc2(self,swapindx=True):
		self.__readloopfoc(type="loop4foc")
		if not hasattr(self,'Id_4loopfoc2'): return {}
		#if not hasattr(self,'Vgs_4loopfocfirstVds'): self.Vgs_4loopfocfirstVds=[Vgs[0] for Vgs in self.Vgs_4loopfoc2]		# get gate voltage setting for each of the Vds sweeps of the foc as the gate voltage at the start of the sweep
		if swapindx: return {'Vds':swapindex(self.Vds_4loopfoc2), 'Vgs':swapindex(self.Vgs_4loopfoc2), 'Vgs_loopfocfirstVds':self.Vgs_4loopfocfirstVds, 'Id':swapindex(self.Id_4loopfoc2), 'Ig':swapindex(self.Ig_4loopfoc2), \
							 'gatestatus':swapindex(self.gatestatus_4loopfoc2), 'drainstatus':swapindex(self.drainstatus_4loopfoc2)}
		else: return {'Vds':self.Vds_4loopfoc2[0],'Vgs':self.Vgs_4loopfoc2,'Vgs_loopfocfirstVds':self.Vgs_4loopfocfirstVds, 'Id':self.Id_4loopfoc2,'Ig':self.Ig_4loopfoc2, 'gatestatus':self.gatestatus_4loopfoc2, 'drainstatus':self.drainstatus_4loopfoc2}
########################################################################################################################################################################################
########################################################################################################################################################################################
# return values from the IV family of curves measurements which use a controlled slew rate sweep of Vds to capture hysteresis in the drain voltage
# if swapI is True then Id[iVds][iVgs] unsmoothed raw measured data from the IV family of curves where iVds is the drain voltage index and iVgs the gate voltage index.
# else: if swapI is False then Id[iVgs][iVds] unsmoothed raw measured data from the IV family of curves where iVds is the drain voltage index and iVgs the gate voltage index.
# same data as IdIV_foc except gate and drain indices are swapped and the Vds=0 datapoint is eliminated
# Note that the return data are indexed data[iVds][iVgs] where iVds and iVgs are the drain and gate voltage indices respectively
	def get_Id_4loopfoc3(self,swapindx=True):
		self.__readloopfoc(type="loop4foc")
		if not hasattr(self,'Id_4loopfoc3'): return {}
		#if not hasattr(self,'Vgs_4loopfocfirstVds'): self.Vgs_4loopfocfirstVds=[Vgs[0] for Vgs in self.Vgs_4loopfoc3]		# get gate voltage setting for each of the Vds sweeps of the foc as the gate voltage at the start of the sweep
		if swapindx: return {'Vds':swapindex(self.Vds_4loopfoc3), 'Vgs':swapindex(self.Vgs_4loopfoc3), 'Vgs_loopfocfirstVds':self.Vgs_4loopfocfirstVds, 'Id':swapindex(self.Id_4loopfoc3), 'Ig':swapindex(self.Ig_4loopfoc3), \
							 'gatestatus':swapindex(self.gatestatus_4loopfoc3), 'drainstatus':swapindex(self.drainstatus_4loopfoc3)}
		else: return {'Vds':self.Vds_4loopfoc3[0],'Vgs':self.Vgs_4loopfoc3,'Vgs_loopfocfirstVds':self.Vgs_4loopfocfirstVds, 'Id':self.Id_4loopfoc3,'Ig':self.Ig_4loopfoc3, 'gatestatus':self.gatestatus_4loopfoc3, 'drainstatus':self.drainstatus_4loopfoc3}
########################################################################################################################################################################################
########################################################################################################################################################################################
# return values from the IV family of curves measurements which use a controlled slew rate sweep of Vds to capture hysteresis in the drain voltage
# if swapI is True then Id[iVds][iVgs] unsmoothed raw measured data from the IV family of curves where iVds is the drain voltage index and iVgs the gate voltage index.
# else: if swapI is False then Id[iVgs][iVds] unsmoothed raw measured data from the IV family of curves where iVds is the drain voltage index and iVgs the gate voltage index.
# same data as IdIV_foc except gate and drain indices are swapped and the Vds=0 datapoint is eliminated
# Note that the return data are indexed data[iVds][iVgs] where iVds and iVgs are the drain and gate voltage indices respectively
	def get_Id_4loopfoc4(self,swapindx=True):
		self.__readloopfoc(type="loop4foc")
		if not hasattr(self,'Id_4loopfoc4'): return {}
		if not hasattr(self,'Vgs_loopfocfirstVds'): self.Vgs_loopfocfirstVds=[Vgs[0] for Vgs in self.Vgs_4loopfoc4]		# get gate voltage setting for each of the Vds sweeps of the foc as the gate voltage at the start of the sweep
		if swapindx: return {'Vds':swapindex(self.Vds_4loopfoc4), 'Vgs':swapindex(self.Vgs_4loopfoc4), 'Vgs_loopfocfirstVds':self.Vgs_loopfocfirstVds, 'Id':swapindex(self.Id_4loopfoc4), 'Ig':swapindex(self.Ig_4loopfoc4), \
							 'gatestatus':swapindex(self.gatestatus_4loopfoc4), 'drainstatus':swapindex(self.drainstatus_4loopfoc4)}
		else:
			print("from line 3371 in device_parameter_request.py debug self.Vds_4loopfoc4 = ",self.Vds_4loopfoc4,self.Id_4loopfoc4,)
			return {'Vds':self.Vds_4loopfoc4[0],'Vgs':self.Vgs_4loopfoc4,'Vgs_loopfocfirstVds':self.Vgs_loopfocfirstVds, 'Id':self.Id_4loopfoc4,'Ig':self.Ig_4loopfoc4, 'gatestatus':self.gatestatus_4loopfoc4, 'drainstatus':self.drainstatus_4loopfoc4}
########################################################################################################################################################################################
########################################################################################################################################################################################
# methods to write calculated parameters to files
########################################################################################################################################################################################
# calculated data file data writing functions
# data here are calculated from the directly measured data
# note that the subsitename is the name of the particular subsite - i.e. a descriptive name of the device at a subsite for all die
# the devicename is a unique name given to a device that is tested under a certain condition. One device can have many devicenames - one devicename per condition e.g. bias,
# temperature - etc.. which would cause the device to have different measured parameters.
######################################################################################################################################################

######################################################################################################################################################
# write current IV transfer curves and gm results to a file
# Inputs:
# pathname
#
# 	def writefile_ivtransfercalc(self):
# 		self.__calc_t()																		# calculate single-swept IV transfer curve parameters
# 		self.__calc_tf()																		# calculate dual-swept forward IV transfer curve parameters
# 		self.__calc_tr()																		# calculate dual-swept reverse IV transfer curve parameters
# 		self.pathname_IV = self.pathname+sub("CALDC")									# write calculated results to this subdirectory
# 		if not os.path.exists(self.pathname_IV):											# if necessary, make the directory to contain the data
# 			os.makedirs(self.pathname_IV)
# 			#timestamp
#
# 		filename = self.pathname_IV+"/"+self.devicename+"_calculated_transfer.xls"
# 		#print "devicename =",devicename #debug
# 		# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
# 		ftransfer = open(filename,'w')
# 		#timestamp for single-swept transfer curve data
# 		ftransfer.write('# year single-sweep\t'+str(self.IVt_year)+'\n')
# 		ftransfer.write('# month single-sweep\t'+str(self.IVt_month)+'\n')
# 		ftransfer.write('# day single-sweep\t'+str(self.IVt_day)+'\n')
# 		ftransfer.write('# hour single-sweep\t'+str(self.IVt_hour)+'\n')
# 		ftransfer.write('# minute single-sweep\t'+str(self.IVt_minute)+'\n')
# 		ftransfer.write('# second single-sweep\t'+str(self.IVt_second)+'\n')
#
# 		#timestamp for dual-swept transfer curve data
# 		ftransfer.write('# year dual-sweep\t'+str(self.IVtfr_year)+'\n')
# 		ftransfer.write('# month dual-sweep\t'+str(self.IVtfr_month)+'\n')
# 		ftransfer.write('# day dual-sweep\t'+str(self.IVtfr_day)+'\n')
# 		ftransfer.write('# hour dual-sweep\t'+str(self.IVtfr_hour)+'\n')
# 		ftransfer.write('# minute dual-sweep\t'+str(self.IVtfr_minute)+'\n')
# 		ftransfer.write('# second dual-sweep\t'+str(self.IVtfr_second)+'\n')
#
# 		#parameters
# 		ftransfer.write('# wafer name\t'+self.wafer_name+'\n')
# 		ftransfer.write('# device name\t'+self.devicename+'\n')
# 		ftransfer.write('# x location um\t%d\n' %(int(self.x_location)))
# 		ftransfer.write('# y location um\t%d\n' %(int(self.y_location)))
# 		ftransfer.write('# drain voltage for single-swept transfer curve, Vds (V)\t%10.2f\n' %(self.Vds_IVt))
# 		ftransfer.write('# drain voltage for dual-swept forward transfer curve is\t%10.2f and reverse transfer curve is\t%10.2f\n' % (self.Vds_IVtfr, self.Vds_IVtfr))
# 		ftransfer.write('# order of polynomal to fit Ids\t%d\n' %self.order)
# 		ftransfer.write('# fraction of Vgs range to fit Y function over\t%10.3f\n' %self.fractVgsfit)
# 		ftransfer.write('#\n')
# 		ftransfer.write('# Results ###################\n')
# 		ftransfer.write('#\n')
# 		ftransfer.write('# Results single-sweep\n')
# 		ftransfer.write('# threshold voltage (V) from Y single swept\t%10.3f\n' % self.__calc_t()['VthY'])		# Note that a call to self.__calc_t method gets all the parameters printed to the file
# 		ftransfer.write('# threshold voltage (V) from Idfit single swept\t%10.3f\n' % self.__calc_t()['VthId'])
# 		ftransfer.write('# contact resistance (ohms) single swept\t%10.3f\n' % self.__calc_t()['Rc'])
# 		ftransfer.write('# Idleakage (A) single swept\t%10.2E\n' % self.__calc_t()['Idleak'])
# 		ftransfer.write('#\n')
# 		ftransfer.write('# Results dual-sweep forward\n')
# 		ftransfer.write('# threshold voltage (V) from Y forward swept \t%10.3f\n' % self.__calc_tf()['VthY'])		# Note that a call to self.__calc_tf method gets all the parameters printed to the file
# 		ftransfer.write('# threshold voltage (V) from Idfit forward swept\t%10.3f\n' % self.__calc_tf()['VthId'])
# 		ftransfer.write('# contact resistance forward swept (ohms)\t%10.3f\n' % self.__calc_tf()['Rc'])
# 		ftransfer.write('# Idleakage forward swept (A)\t%10.2E\n' % self.__calc_tf()['Idleak'])
# 		ftransfer.write('#\n')
# 		ftransfer.write('# Results dual-sweep reverse\n')
# 		ftransfer.write('# threshold voltage (V) from Y reverse swept \t%10.3f\n' % self.__calc_tr()['VthY'])		# Note that a call to self.__calc_tr method gets all the parameters printed to the file
# 		ftransfer.write('# threshold voltage (V) from Idfit reverse swept\t%10.3f\n' % self.__calc_tr()['VthId'])
# 		ftransfer.write('# contact resistance reverse swept (ohms)\t%10.3f\n' % self.__calc_tr()['Rc'])
# 		ftransfer.write('# Idleakage reverse swept (A)\t%10.2E\n' % self.__calc_tr()['Idleak'])
# 		ftransfer.write('#\n')
# 		#data
# 		# transfer curve data
# 		ftransfer.write('# single-swept transfer curve data\n')
# 		ftransfer.write('# Vgs\tId measured-Idleak\tId fit(A)\tIdlin(A)\tgm from Id fit\tY\tYlin\tIg\tdrainstatus\tgatestatus\n')
# 		for ii in range(0,len(self.Vgs_IVt)):				# write single swept transfer curve parameters
# 			ftransfer.write('%10.2f\t%10.2E\t%10.2E\t%10.2E\t%10.2E\t%10.2E\t%10.2E\t%10.2E\t%s\t%s\n' %(self.Vgs_IVt[ii],self.Id_IVt[ii]-self.Idleak_t,self.Idfit_t[ii],self.Idlin_t[ii],self.gm_t[ii],self.Yf_t[ii],self.Yflin_t[ii],self.Ig_IVt[ii],self.drainstatus_IVt[ii],self.gatestatus_IVt[ii]))
# 		ftransfer.write("#\n# dual-swept transfer curve forward swept data\n")
# 		ftransfer.write('# Vgs\tforward Id measured-Idleak\tforward Id fit(A)\tforward Idlin(A)\tforward gm from Id fit\tforward Y\tforward Ylin\tIg\tdrainstatus\tgatestatus\n')
# 		for ii in range(0,len(self.Vgs_IVtf)):				# write single swept transfer curve parameters
# 			ftransfer.write('%10.2f\t%10.2E\t%10.2E\t%10.2E\t%10.2E\t%10.2E\t%10.2E\t%10.2E\t%s\t%s\n' %(self.Vgs_IVtf[ii],self.Id_IVtf[ii]-self.Idleak_tf,self.Idfit_tf[ii],self.Idlin_tf[ii],self.gm_tf[ii],self.Yf_tf[ii],self.Yflin_tf[ii],self.Ig_IVtf[ii],self.drainstatus_IVtf[ii],self.gatestatus_IVtf[ii]))
# 		ftransfer.write("#\n# dual-swept transfer curve reverse swept data\n")
# 		ftransfer.write('# Vgs\treverse Id measured-Idleak\treverse Id fit(A)\treverse Idlin(A)\treverse gm from Id fit\treverse Y\treverse Ylin\tIg\tdrainstatus\tgatestatus\n')
# 		for ii in range(0,len(self.Vgs_IVtr)):				# write single swept transfer curve parameters
# 			ftransfer.write('%10.2f\t%10.2E\t%10.2E\t%10.2E\t%10.2E\t%10.2E\t%10.2E\t%10.2E\t%s\t%s\n' %(self.Vgs_IVtr[ii],self.Id_IVtr[ii]-self.Idleak_tr,self.Idfit_tr[ii],self.Idlin_tr[ii],self.gm_tr[ii],self.Yf_tr[ii],self.Yflin_tr[ii],self.Ig_IVtf[ii],self.drainstatus_IVtr[ii],self.gatestatus_IVtr[ii]))
# 		ftransfer.close()
# 		return [filename,self.devicename]
##########################################################################################################################################################################
# obsolete function!!
# # sets lead resistance to compensate IV and family of curves data for nonzero resistance in the metal traces leading to the devices
# # resistances are removed from a devices as specified in the geometry.csv file
# # lead resistance is assumed to be entirely in the drain of affected devices
# 	def set_leadresistance(self,leadresistance):
# 		if leadresistance==None: return
# 		# if self.devwidth!=None: scalingfactor=self.unitsscaling/self.devwidth								# scale currents to mA/mm according to the device gate width self.devwidth (in um)
# 		# else: scalingfactor=1000.						# no device width given so use no scaling - just measured currents i.e. assume gate width to be 1mm
# 		for k in leadresistance:			# leadresistance is a dictionary with key k and the key will contain a portion of the device name
# 			#if k in self.devicename: self.leadresistance=1000.*leadresistance[k]/scalingfactor
# 			# TODO: This is a major ERROR and will conflate TLM names
# 			if k in self.devicename: self.leadresistance=leadresistance[k]				# don't scale according to device gate width because lead resistance compensation is to be applied to the unscaled raw IV data
##########################################################################################################################################################################
##########################################################################################################################################################################
# rewrite of function to prevent errors due to conflation of things such as TLM_0.5 with TLM_0.55 in the keys of leadresistance
# sets lead resistance to compensate IV and family of curves data for nonzero resistance in the metal traces leading to the devices
# resistances are removed from a devices as specified in the geometry.csv file
# lead resistance is assumed to be entirely in the drain of affected devices
	def set_leadresistance(self,leadresistance):
		if leadresistance==None: return
		# prevent conflation of device types e.g. TLM_0.5 with TLM_0.55
		for k in leadresistance:			# leadresistance is a dictionary with key k and the key will contain a portion of the device name
			#if "".join([k,"t"]) in "".join([self.devicename,"t"]): self.leadresistance=leadresistance[k]				# don't scale according to device gate width because lead resistance compensation is to be applied to the unscaled raw IV data
			if k in self.devicename.split('_'): self.leadresistance=leadresistance[k]
##########################################################################################################################################################################
# Noise parameters from 50ohm measurements (no tuner)
	def get_NF50(self):
		if not (hasattr(self,"NF50") and len(self.NF50)>0):                 # do not have noise data so read noise data
			message_calc=self.__calc_Fmin50()
			if message_calc!="success":
				#print("from line 2965 device_parameter_request.py No noise data for", message_calc,self.devicename)
				return {}
		return {'freqnoise50':self.freqnoise50,'freqNF50lowest':self.freqNF50lowest,'gain50':self.gain50,'gainFmin50':self.gainFmin50,'Fmin50':self.Fmin50,'Fmin50average':self.Fmin50average,'Fmin50lowest':self.Fmin50lowest,'freqFmin50lowest':self.freqNF50lowest,'NF50avg':self.NF50avg,'NF50lowest':self.NF50lowest}
##########################################################################################################################################################################
##########################################################################################################################################################################
# Noise parameters from tuned measurements
	def get_noise_parameters(self):
		if not (hasattr(self,"noise_parameters") and len(self.noise_parameters)>0):                 # go to the work of reading the noise parameter data ONLY if we don't have it already
			message_calc=self.__read_noise_parameters()
			if message_calc=="success":
				ifmin=min(range(len(self.noise_parameters)),key=lambda  i:self.noise_parameters[i]['FmindB'])       # find frequency index for the minimum FmindB across the frequencies measured for noise parameters
				self.NPmin=self.noise_parameters[ifmin]                                                      # noise parameters for the frequency having the minimum FmindB
				# find average noise parameters over noise parameter measurement frequency range
				self.NPavg={'gopt':np.average([self.noise_parameters[i]['gopt'] for i in range(0,len(self.noise_parameters))]),
							'FmindB':np.average([self.noise_parameters[i]['FmindB'] for i in range(0,len(self.noise_parameters))]),
							'Rn':np.average([self.noise_parameters[i]['Rn'] for i in range(0,len(self.noise_parameters))]),
							'GassocdB':np.average([self.noise_parameters[i]['GassocdB'] for i in range(0,len(self.noise_parameters))]),
							}
			else: return []
		return self.NPmin,self.NPavg
##########################################################################################################################################################################
########################################################################################################################################################################################
# Read pulsed time-domain data Id, Ig after step of Vgs
#
	def __readpulseVgs(self):
		if self.devwidth!=None: scalingfactor=self.unitsscaling/self.devwidth								# scale currents to mA/mm
		else: scalingfactor=1.                                                                      # no gate width given so scale currents to unity (no scaling)
		self.pathname_IV = self.pathname+sub("DC")
		fullfilename_pulsedVgs="".join([self.pathname_IV,"/",self.devicename,"_pulsedtimedomain.xls"])				# form full devicename (path+devicename) of pulsed time-domain data

		try: fpulsedVgs=open(fullfilename_pulsedVgs,'r')
		except: return "NO FILE"

		pulsedVgslines = [a for a in fpulsedVgs.read().splitlines()]             # sfilelines is a string array of the lines in the file
		fpulsedVgs.close()
		for fileline in pulsedVgslines:
			# get timestamp
			if "year" in fileline:
				self.pulsedVgs_year=fileline.split('\t')[1].lstrip()
			elif "month" in fileline:
				self.pulsedVgs_month=fileline.split('\t')[1].lstrip()
			elif "day" in fileline:
				self.pulsedVgs_day=fileline.split('\t')[1].lstrip()
			elif "hour" in fileline:
				self.pulsedVgs_hour=fileline.split('\t')[1].lstrip()
			elif "minute" in fileline:
				self.pulsedVgs_minute=fileline.split('\t')[1].lstrip()
			elif "second" in fileline:
				self.pulsedVgs_second=fileline.split('\t')[1].lstrip()
			# get lot and device on wafer and wafer location in um
			elif "wafer name" in fileline:
				self.wafer_name=fileline.split('\t')[1].lstrip()
			elif "device name" in fileline:
				self.devicename=fileline.split('\t')[1].lstrip()
			elif "x " in fileline:
				self.x_location=int(fileline.split('\t')[1].lstrip())
			elif "y " in fileline:
				self.y_location=int(fileline.split('\t')[1].lstrip())
			# now read parameter settings for this measurement
			elif "Vds" in fileline:
				self.Vds_pulsedVgs=float(fileline.split('\t')[1].lstrip())
			elif "quiescent time" in fileline:
				self.quiescent_time_pulsedVgs=float(fileline.split('\t')[1].lstrip())
			elif "gate quiescent voltage" in fileline:                  # Vgs slew rate
				self.quiescent_Vgs_pulsedVgs=float(fileline.split('\t')[1].lstrip())

		self.timestamp_pulsedVgs = col.deque()
		self.Id_pulsedVgs = col.deque()
		self.Ig_pulsedVgs = col.deque()
		self.Vgs_pulsedVgs = col.deque()
		self.drainstatus_pulsedVgs = col.deque()
		self.gatestatus_pulsedVgs = col.deque()

		# now read data
		for fileline in pulsedVgslines:                                               # load lines from the data file
			if "# Vgs" in fileline:				                    # Add a gate voltage and read the gate voltage for the following data set
				self.Vgs_pulsedVgs.append(fileline.split("\t")[1])
				self.timestamp_pulsedVgs.append([])
				self.Id_pulsedVgs.append([])
				self.Ig_pulsedVgs.append([])
				self.drainstatus_pulsedVgs.append([])
				self.gatestatus_pulsedVgs.append([])
			elif not(('!' in fileline) or ('#' in fileline)):                       # then this line is the dataset for the last-read Vgs
				self.timestamp_pulsedVgs[-1].append(float(fileline.split()[0]))
				self.Id_pulsedVgs[-1].append(float(fileline.split()[1]))
				self.Ig_pulsedVgs[-1].append(float(fileline.split()[2]))
				try: self.drainstatus_pulsedVgs[-1].append(fileline.split()[3])
				except:
					print(self.get_devicename())
					raise ValueError("failed read of drainstatus")
				try: self.gatestatus_pulsedVgs[-1].append(fileline.split()[4])
				except:
					print(self.get_devicename())
					raise ValueError("failed read of gatestatus")

		# done reading data from pulsedVgslines buffer
		if self.devwidth!=None:												# apply scaling only if gate size is specified
			if len(self.Id_pulsedVgs)>0:
				self.Id_pulsedVgs=np.multiply(scalingfactor,self.Id_pulsedVgs)
				self.Ig_pulsedVgs=np.multiply(scalingfactor,self.Ig_pulsedVgs)
		return
########################################################################################################################################################################################
########################################################################################################################################################################################
# Read pulsed time-domain data Id, Ig after step of Vds from
#
	def __readpulseVds(self):
		if self.devwidth!=None: scalingfactor=self.unitsscaling/self.devwidth								# scale currents to mA/mm
		else: scalingfactor=1.                                                                      # no gate width given so scale currents to unity (no scaling)
		self.pathname_IV = self.pathname+sub("DC")
		fullfilename_pulsedVds="".join([self.pathname_IV,"/",self.devicename,"_pulsedtimedomaindrain.xls"]) 				# form full devicename (path+devicename) of pulsed time-domain data
		try: fpulsedVds=open(fullfilename_pulsedVds,'r')
		except:
			fullfilename_pulsedVds="".join([self.pathname_IV,"/",self.devicename,"_pulseddraintimedomain.xls"])				# try the other form if the above doesn't work form full devicename (path+devicename) of pulsed time-domain data
			try: fpulsedVds=open(fullfilename_pulsedVds,'r')
			except: return "NO FILE"

		pulsedVdslines = [a for a in fpulsedVds.read().splitlines()]             # sfilelines is a string array of the lines in the file
		fpulsedVds.close()
		for fileline in pulsedVdslines:
			# get timestamp
			if "year" in fileline:
				self.pulsedVds_year=fileline.split('\t')[1].lstrip()
			elif "month" in fileline:
				self.pulsedVds_month=fileline.split('\t')[1].lstrip()
			elif "day" in fileline:
				self.pulsedVds_day=fileline.split('\t')[1].lstrip()
			elif "hour" in fileline:
				self.pulsedVds_hour=fileline.split('\t')[1].lstrip()
			elif "minute" in fileline:
				self.pulsedVds_minute=fileline.split('\t')[1].lstrip()
			elif "second" in fileline:
				self.pulsedVds_second=fileline.split('\t')[1].lstrip()
			# get lot and device on wafer and wafer location in um
			elif "wafer name" in fileline:
				self.wafer_name=fileline.split('\t')[1].lstrip()
			elif "device name" in fileline:
				self.devicename=fileline.split('\t')[1].lstrip()
			elif "x " in fileline:
				self.x_location=int(fileline.split('\t')[1].lstrip())
			elif "y " in fileline:
				self.y_location=int(fileline.split('\t')[1].lstrip())
			# now read parameter settings for this measurement
			elif "Vgs" in fileline:
				self.Vgs_pulsedVds=float(fileline.split('\t')[1].lstrip())
			elif "quiescent time" in fileline:
				self.quiescent_time_pulsedVds=float(fileline.split('\t')[1].lstrip())
			elif "drain quiescent voltage" in fileline:                  # Vds slew rate
				self.quiescent_Vds_pulsedVds=float(fileline.split('\t')[1].lstrip())

		self.timestamp_pulsedVds = col.deque()
		self.Id_pulsedVds = col.deque()
		self.Ig_pulsedVds = col.deque()
		self.Vds_pulsedVds = col.deque()
		self.drainstatus_pulsedVds = col.deque()
		self.gatestatus_pulsedVds = col.deque()

		# now read data
		for fileline in pulsedVdslines:                                               # load lines from the data file
			if "# Vds" in fileline:				                    # Add a drain voltage and read the drain voltage for the following data set
				self.Vds_pulsedVds.append(fileline.split("\t")[1])
				self.timestamp_pulsedVds.append([])
				self.Id_pulsedVds.append([])
				self.Ig_pulsedVds.append([])
				self.drainstatus_pulsedVds.append([])
				self.gatestatus_pulsedVds.append([])
			elif not(('!' in fileline) or ('#' in fileline)):                       # then this line is the dataset for the last-read Vds
				self.timestamp_pulsedVds[-1].append(float(fileline.split()[0]))
				self.Id_pulsedVds[-1].append(float(fileline.split()[1]))
				self.Ig_pulsedVds[-1].append(float(fileline.split()[2]))
				try: self.drainstatus_pulsedVds[-1].append(fileline.split()[3])
				except:
					print(self.get_devicename())
					raise ValueError("failed read of drainstatus")
				try: self.gatestatus_pulsedVds[-1].append(fileline.split()[4])
				except:
					print(self.get_devicename())
					raise ValueError("failed read of gatestatus")

		# done reading data from pulsedVdslines buffer
		if self.devwidth!=None:												# apply scaling only if gate size is specified
			if len(self.Id_pulsedVds)>0:
				self.Id_pulsedVds=np.multiply(scalingfactor,self.Id_pulsedVds)
				self.Ig_pulsedVds=np.multiply(scalingfactor,self.Ig_pulsedVds)
		return
########################################################################################################################################################################################
########################################################################################################################################################################################
# reads Id(t) i.e. drain current vs time, for constant drain voltage (Vds) and a pulsed gate voltage (Vgs)

# Note that the return data are indexed data[iVgs][itime] for all data except Vgs which has only the index [iVgs], and Vds which has no index because it's constant;
#  where itime and iVgs are the timestamp, for the time-domain response, and pulsed gate voltage indices respectively
# self.Vds_pulsedVgs
# self.Vgs_pulsedVgs[iVgs]
# self.Id_pulsedVgs[iVgs][itime]
# self.Ig_pulsedVgs[iVgs][itime]
# self.gatestatus_pulsedVgs[iVgs][itime]
# self.drainstatus_pulsedVgs[iVgs][itime]
# self.timestamp_pulsedVgs[iVgs][itime]
	def get_pulsedVgs(self):
		if not hasattr(self,"Id_pulsedVgs"): self.__readpulseVgs()
		if not hasattr(self,"Id_pulsedVgs"): return {}      # tried reading but still no data
		else: return {'Vds':self.Vds_pulsedVgs,'Vgs':self.Vgs_pulsedVgs, 'Id':self.Id_pulsedVgs,'Ig':self.Ig_pulsedVgs, 'timestamp':self.timestamp_pulsedVgs, 'gatestatus':self.gatestatus_pulsedVgs, 'drainstatus':self.drainstatus_pulsedVgs}
#######################################################################################################################################################################################
########################################################################################################################################################################################
# reads Id(t) i.e. drain current vs time, for constant gate voltage (Vgs) and a pulsed drain voltage (Vds)

# Note that the return data are indexed data[iVds][itime] for all data except Vds which has only the index [iVds], and Vgs which has no index because it's constant;
#  where itime and iVds are the timestamp, for the time-domain response, and pulsed drain voltage indices respectively
# self.Vgs_pulsedVds
# self.Vds_pulsedVds[iVds]
# self.Id_pulsedVds[iVds][itime]
# self.Ig_pulsedVds[iVds][itime]
# self.gatestatus_pulsedVds[iVds][itime]
# self.drainstatus_pulsedVds[iVds][itime]
# self.timestamp_pulsedVds[iVds][itime]
	def get_pulsedVds(self):
		if not hasattr(self,"Id_pulsedVds"): self.__readpulseVds()
		if not hasattr(self,"Id_pulsedVds"): return {}      # tried reading but still no data
		else: return {'Vds':self.Vds_pulsedVds,'Vgs':self.Vgs_pulsedVds, 'Id':self.Id_pulsedVds,'Ig':self.Ig_pulsedVds, 'timestamp':self.timestamp_pulsedVds, 'gatestatus':self.gatestatus_pulsedVds, 'drainstatus':self.drainstatus_pulsedVds}
#######################################################################################################################################################################################
# gets the gate compliance information for the time domain pulsed gate, i.e. the timestamps of the data points in gate compliance
	def get_pulsedVgs_gatecompliance(self):
		if not hasattr(self,"Id_pulsedVgs"): self.__readpulseVgs()
		if not hasattr(self,"Id_pulsedVgs"): return []      # tried reading but still no data
		else:
			r= [[self.timestamp_pulsedVgs[j][i] for i in range(0,len(self.timestamp_pulsedVgs[j])) if self.gatestatus_pulsedVgs[j][i].lower()=='c'] for j in range(0,len(self.timestamp_pulsedVgs))]
			if len(r[0])==0 and len(r)<2:
				return []
			else: return r
#######################################################################################################################################################################################
# gets the drain compliance information for the time domain pulsed gate, i.e. the timestamps of the data points in gate compliance
	def get_pulsedVgs_draincompliance(self):
		if not hasattr(self,"Id_pulsedVgs"): self.__readpulseVgs()
		if not hasattr(self,"Id_pulsedVgs"): return []      # tried reading but still no data
		else:
			r= [[self.timestamp_pulsedVgs[j][i] for i in range(0,len(self.timestamp_pulsedVgs[j])) if self.drainstatus_pulsedVgs[j][i].lower()=='c'] for j in range(0,len(self.timestamp_pulsedVgs)) ]
			if len(r[0])==0 and len(r)<2:
				return []
			else: return r
#######################################################################################################################################################################################
# gets the drain compliance information for the time domain pulsed gate, i.e. the timestamps of the data points in gate compliance
	def get_pulsedVds_gatecompliance(self):
		if not hasattr(self,"Id_pulsedVds"): self.__readpulseVds()
		if not hasattr(self,"Id_pulsedVds"): return []      # tried reading but still no data
		else:
			r=[[self.timestamp_pulsedVds[j][i] for i in range(0,len(self.timestamp_pulsedVds[j])) if self.gatestatus_pulsedVds[j][i].lower()=='c'] for j in range(0,len(self.timestamp_pulsedVds))]
			if len(r[0])==0 and len(r)<2:
				return []
			else: return r
#######################################################################################################################################################################################
# gets the drain compliance information for the time domain pulsed gate, i.e. the timestamps of the data points in gate compliance
	def get_pulsedVds_draincompliance(self):
		if not hasattr(self,"Id_pulsedVds"): self.__readpulseVds()
		if not hasattr(self,"Id_pulsedVds"): return []      # tried reading but still no data
		else:
			r= [[self.timestamp_pulsedVds[j][i] for i in range(0,len(self.timestamp_pulsedVds[j])) if self.drainstatus_pulsedVds[j][i].lower()=='c'] for j in range(0,len(self.timestamp_pulsedVds))]
			if len(r[0])==0 and len(r)<2:
				return []
			else: return r
###########################################################################################################################################################################################


# tuned third order intercept point
#######################################################################################################################################################################################
# output reflection coefficient magnitude which gives the maximum TOI
	def get_reflect_maxTOI(self):
		if not "reflect_mag_maxTOI" in self.TOI.keys(): self.__readTOI()
		if not "reflect_mag_maxTOI" in self.TOI.keys(): return None      # tried reading but still no data
		else:
			return self.TOI['reflect_mag_maxTOI'],self.TOI['reflect_ang_maxTOI']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# output reflection coefficient magnitude which gives the maximum gain during the TOI measurement
	def get_reflect_maxgainTOI(self):
		if not "reflect_mag_maxTOI" in self.TOI.keys(): self.__readTOI()
		if not "reflect_mag_maxTOI" in self.TOI.keys(): return None      # tried reading but still no data
		else:
			return self.TOI['reflect_mag_maxgainTOI'],self.TOI['reflect_ang_maxgainTOI']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# Maximum output TOI in dBm
	def get_TOIoutmax(self):
		if not "TOIoutmax" in self.TOI.keys(): self.__readTOI()
		if not "TOIoutmax" in self.TOI.keys(): return None      # tried reading but still no data
		else:
			return self.TOI['TOIoutmax']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
#  TOI dBm at maximum gain
	def get_TOImaxgain(self):
		if not "TOImaxgain" in self.TOI.keys(): self.__readTOI()
		if not "TOImaxgain" in self.TOI.keys(): return None      # tried reading but still no data
		else:
			return self.TOI['TOImaxgain']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# Gain dB at maximum TOI
	def get_DUTmaxgainTOI(self):
		if not "DUTmaxgainTOI" in self.TOI.keys(): self.__readTOI()
		if not "DUTmaxgainTOI" in self.TOI.keys(): return None      # tried reading but still no data
		else:
			return self.TOI['DUTmaxgainTOI']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# Vgs for TOI measurement
	def get_VgsTOI(self):
		if not "Vgs" in self.TOI.keys(): self.__readTOI()
		if not "Vgs" in self.TOI.keys(): return None      # tried reading but still no data
		else:
			return self.TOI['Vgs']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# Vds for TOI measurement
	def get_VdsTOI(self):
		if not "Vds" in self.TOI.keys(): self.__readTOI()
		if not "Vds" in self.TOI.keys(): return None      # tried reading but still no data
		else:
			return self.TOI['Vds']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# Id for TOI measurement
	def get_IdTOI(self):
		if not "Id" in self.TOI.keys(): self.__readTOI()
		if not "Id" in self.TOI.keys(): return None      # tried reading but still no data
		else:
			return self.TOI['Id']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# Ig for TOI measurement
	def get_IgTOI(self):
		if not "Ig" in self.TOI.keys(): self.__readTOI()
		if not "Ig" in self.TOI.keys(): return None      # tried reading but still no data
		else:
			return self.TOI['Ig']
###########################################################################################################################################################################################

# TOI with swept Vgs
# tuned third order intercept point measured while sweeping Vgs
#######################################################################################################################################################################################
# output reflection coefficient magnitude which gives the maximum TOI
	def get_reflect_maxTOIVgsswept(self):
		if not "reflect_mag_maxTOI" in self.TOIVgsswept.keys(): self.__readTOIVgsswept()
		if not "reflect_mag_maxTOI" in self.TOIVgsswept.keys(): return None      # tried reading but still no data
		else:
			return self.TOIVgsswept['reflect_mag_maxTOI'],self.TOIVgsswept['reflect_ang_maxTOI']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# output reflection coefficient magnitude which gives the maximum gain during the TOI measurement
	def get_reflect_maxgainTOIVgsswept(self):
		if not "reflect_mag_maxTOI" in self.TOIVgsswept.keys(): self.__readTOIVgsswept()
		if not "reflect_mag_maxTOI" in self.TOIVgsswept.keys(): return None      # tried reading but still no data
		else:
			return self.TOIVgsswept['reflect_mag_maxgainTOI'],self.TOIVgsswept['reflect_ang_maxgainTOI']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# Maximum output TOI in dBm for all measured reflection coefficients and over all of the swept Vgs
	def get_TOImaxVgsswept(self):
		if not "TOImax" in self.TOIVgsswept.keys(): self.__readTOIVgsswept()
		if not "TOImax" in self.TOIVgsswept.keys(): return None      # tried reading but still no data
		else:
			return self.TOIVgsswept['TOImax']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# Associated Gain dB at maximum TOI
	def get_DUTmaxgainTOIVgsswept(self):
		if not "gainatmaxTOI" in self.TOIVgsswept.keys(): self.__readTOIVgsswept()
		if not "gainatmaxTOI" in self.TOIVgsswept.keys(): return None      # tried reading but still no data
		else:
			return self.TOIVgsswept['gainatmaxTOI']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# Vgs vs sweep time for swept Vgs TOI measurement
	def get_VgsTOIVgsswept(self):
		if not "Vgs_time" in self.TOIVgsswept.keys(): self.__readTOIVgsswept()
		if not "Vgs_time" in self.TOIVgsswept.keys(): return None      # tried reading but still no data
		else:
			return self.TOIVgsswept['Vgs_time']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# Vds for TOI measurement
	def get_VdsTOIVgsswept(self):
		if not "Vds" in self.TOIVgsswept.keys(): self.__readTOIVgsswept()
		if not "Vds" in self.TOIVgsswept.keys(): return None      # tried reading but still no data
		else:
			return self.TOIVgsswept['Vds']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# Id for TOI measurement
	def get_IdTOIVgsswept(self):
		if not "Id_time" in self.TOIVgsswept.keys(): self.__readTOIVgsswept()
		if not "Id_time" in self.TOIVgsswept.keys(): return None      # tried reading but still no data
		else:
			return self.TOIVgsswept['Id_time']
###########################################################################################################################################################################################



# compression
#######################################################################################################################################################################################
# output reflection coefficient magnitude which gives the maximum 1dB COMPRESS
	def get_reflect_COMPRESS(self):
		if not "reflect_mag_maxCOMPRESS" in self.COMPRESS.keys(): self.__readCOMPRESS()
		if not "reflect_mag_maxCOMPRESS" in self.COMPRESS.keys(): return None      # tried reading but still no data
		else:
			return self.COMPRESS['reflect_mag_COMPRESS'],self.COMPRESS['reflect_ang_COMPRESS']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# 1dB output COMPRESS in dBm
	def get_COMPRESSout(self):
		if not "COMPRESSout" in self.COMPRESS.keys(): self.__readCOMPRESS()
		if not "COMPRESSout" in self.COMPRESS.keys(): return None      # tried reading but still no data
		else:
			return self.COMPRESS['COMPRESSout']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# Vgs for COMPRESS measurement
	def get_VgsCOMPRESS(self):
		if not "Vgs" in self.COMPRESS.keys(): self.__readCOMPRESS()
		if not "Vgs" in self.COMPRESS.keys(): return None      # tried reading but still no data
		else:
			return self.COMPRESS['Vgs']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# Vds for COMPRESS measurement
	def get_VdsCOMPRESS(self):
		if not "Vds" in self.COMPRESS.keys(): self.__readCOMPRESS()
		if not "Vds" in self.COMPRESS.keys(): return None      # tried reading but still no data
		else:
			return self.COMPRESS['Vds']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# Id for COMPRESS measurement
	def get_IdCOMPRESS(self):
		if not "Id" in self.COMPRESS.keys(): self.__readCOMPRESS()
		if not "Id" in self.COMPRESS.keys(): return None      # tried reading but still no data
		else:
			return self.COMPRESS['Id']
###########################################################################################################################################################################################
#######################################################################################################################################################################################
# gain for COMPRESS measurement, which is the maximum gain for the compression measurement
	def get_gainCOMPRESS(self):
		if not "Id" in self.COMPRESS.keys(): self.__readCOMPRESS()
		if not "Id" in self.COMPRESS.keys(): return None      # tried reading but still no data
		else:
			return self.COMPRESS['gain']
###########################################################################################################################################################################################


# 3rd harmonic measurements
# also used to estimate third order intercept point at 50ohms output
# harmonic distortion is measured at a single Vds over an array of Vgs at low single-tone fundamental RF frequency, usually 170MHz
###########################################################################################################################################################################################
# Vgs for 3rdharmonic measurement (array)
	def get_VgsHARM(self):
		if not "Vgs" in self.HARM.keys(): self.__readHARM()
		if not "Vgs" in self.HARM.keys(): return None
		else:
			return self.HARM['Vgs']
###########################################################################################################################################################################################
###########################################################################################################################################################################################
# Vds for 3rdharmonic measurement (single value)
	def get_VdsHARM(self):
		if not "Vds" in self.HARM.keys(): self.__readHARM()
		if not "Vds" in self.HARM.keys(): return None
		else:
			return self.HARM['Vds']
###########################################################################################################################################################################################
###########################################################################################################################################################################################
# Id for 3rdharmonic measurement (array vs Vgs)
	def get_IdHARM(self):
		if not "Id" in self.HARM.keys(): self.__readHARM()
		if not "Id" in self.HARM.keys(): return None
		else:
			return self.HARM['Id']
###########################################################################################################################################################################################
###########################################################################################################################################################################################
# fundamental input power (dBm) for 3rdharmonic measurement (single value)
	def get_PfundinHARM(self):
		if not "Pin" in self.HARM.keys(): self.__readHARM()
		if not "Pin" in self.HARM.keys(): return None
		else:
			return self.HARM['Pin']
###########################################################################################################################################################################################
###########################################################################################################################################################################################
# fundamental output power (dBm) for 3rdharmonic measurement (array vs Vgs)
	def get_PfundoutHARM(self):
		if not "Pout" in self.HARM.keys(): self.__readHARM()
		if not "Pout" in self.HARM.keys(): return None
		else:
			return self.HARM['Pout']
###########################################################################################################################################################################################
###########################################################################################################################################################################################
# third harmonic output power (dBm) for 3rdharmonic measurement (array vs Vgs)
	def get_P3rdHARM(self):
		if not "P3out" in self.HARM.keys(): self.__readHARM()
		if not "P3out" in self.HARM.keys(): return None
		else:
			return self.HARM['P3out']
###########################################################################################################################################################################################
###########################################################################################################################################################################################
# estimated third order output intercept point at 50ohms (dBm) calculated from 3rdharmonic measurement (array vs Vgs)
	def get_TOIHARM(self):
		if not "TOI" in self.HARM.keys(): self.__readHARM()
		if not "TOI" in self.HARM.keys(): return None
		else:
			return self.HARM['TOI']
###########################################################################################################################################################################################
###########################################################################################################################################################################################
# frequency (Hz) of fundamental single tone.
	def get_freqHARM(self):
		if not "frequency" in self.HARM.keys(): self.__readHARM()
		if not "frequency" in self.HARM.keys(): return None
		else:
			return self.HARM['frequency']
###########################################################################################################################################################################################
###########################################################################################################################################################################################
# frequency (Hz) of fundamental single tone.
	def get_TOImaxHARM(self):
		if not "TOImax" in self.HARM.keys(): self.__readHARM()
		if not "TOImax" in self.HARM.keys(): return None
		else:
			return self.HARM['TOImax']
###########################################################################################################################################################################################

