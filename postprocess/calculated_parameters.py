__author__ = 'Phil Marsh Carbonics'

# post measurement conversion functions
######################################################################################################################################################

#import os
import numpy as np
import cmath as cm
import math
from scipy import stats as st
#from scipy import interpolate as intp
from scipy.interpolate import UnivariateSpline
from scipy.interpolate import InterpolatedUnivariateSpline
from scipy.interpolate import interp1d
import  collections as c
from utilities import *
#import matplotlib.pyplot as plt

epsilon = 1.E-10							# a very small number used to deal with uncertainty of floating point numbers

# calculate transconductance gmloop from an Id vs Vg curve for a two-directional transfer curve sweep (loop)
# Inputs:
# pathname
def X_calculate_gmloop(self):
	try: self.Id_transloop					# does the transfer curve exist?
	except:
		print ("ERROR! No loop transfer curve exists! No gmloop will be calculated!")
		return
	if len(self.Id_transloop)<8:
		print ("ERROR! Not enough points in loop transfer curve to calculate gmloop! No gmloop will be calculated!")
		return
	self.gmloop = []
	self.gmloop.append(0.)
	for ii in range(1,len(self.Id_transloop)-1):
		try:
			self.gmloop.append((self.Id_transloop[ii+1]-self.Id_transloop[ii-1])/(self.Vgs_transloop[ii+1]-self.Vgs_transloop[ii-1]))
		except ZeroDivisionError:
			print ("divide by zero ERROR calculating gmloop - probably bad device!")
			self.gmloop.append(0.)
	# now set the gmloop endpoints using linear extrapolations from neighboring points
	try:
		self.gmloop[0]=self.gmloop[1]-(self.Vgs_transloop[1]-self.Vgs_transloop[0])*(self.gmloop[2]-self.gmloop[1])/(self.Vgs_transloop[2]-self.Vgs_transloop[1])		# linear extrapolation
	except:
		print ("divide by zero ERROR calculating gmloop at zeroth endpoint- probably bad device!")
		self.gmloop[0]=0.
	endpt = len(self.Id_transloop)-1
	try:
		self.gmloop.append(self.gmloop[endpt-1]+(self.Vgs_transloop[endpt]-self.Vgs_transloop[endpt-1])*(self.gmloop[endpt-1]-self.gmloop[endpt-2])/(self.Vgs_transloop[endpt-1]-self.Vgs_transloop[endpt-2]))
	except ZeroDivisionError:
		print ("divide by zero ERROR calculating gmloop at max endpoint- probably bad device!")
		self.gmloop.append(0.)
######################################################################################################################################################
# calculate transconductance gm from an Id vs Vg curve for one-directional transfer curve sweep
# Inputs:
# pathname
def X_calculate_gm(self):
	try: self.Id_t					# does the transfer curve exist?
	except:
		print ("ERROR! No transfer curve exists! No gm will be calculated!")
		return
	if len(self.Id_t)<4:
		print ("ERROR! Not enough points in transfer curve to calculate gm! No gm will be calculated!")
		return
	self.gm = []
	self.gm.append(0.)
	for ii in range(1,len(self.Id_t)-1):
		try:
			self.gm.append((self.Id_t[ii+1]-self.Id_t[ii-1])/(self.Vgs_t[ii+1]-self.Vgs_t[ii-1]))
		except ZeroDivisionError:
			print ("divide by zero ERROR calculating gm - probably bad device!")
			self.gm.append(0.)
	# now set the gm endpoints using linear extrapolations from neighboring points
	try:
		self.gm[0]=self.gm[1]-(self.Vgs_t[1]-self.Vgs_t[0])*(self.gm[2]-self.gm[1])/(self.Vgs_t[2]-self.Vgs_t[1])		# linear extrapolation
	except ZeroDivisionError:
		print ("divide by zero ERROR calculating gm at zeroth endpoint- probably bad device!")
		self.gm[0]=0.
	endpt = len(self.Id_t)-1
	try:
		self.gm.append(self.gm[endpt-1]+(self.Vgs_t[endpt]-self.Vgs_t[endpt-1])*(self.gm[endpt-1]-self.gm[endpt-2])/(self.Vgs_t[endpt-1]-self.Vgs_t[endpt-2]))
	except ZeroDivisionError:
		print ("divide by zero ERROR calculating gm at max endpoint- probably bad device!")
		self.gm.append(0.)


#########################################################################################################################################################################################
# RF parameter conversion functions
#########################################################################################################################################################################################
# converts a complex number para (real and imaginary) to  a returned linear polar coordinates where the real part is the magnitude and the imaginary part is the angle in degrees
#
def convertRItoMA(para):
	return complex(cm.polar(para)[0],180.*cm.polar(para)[1]/np.pi)
#########################################################################################################################################################################################
# converts a magnitude and angle (in degrees) to complex number para (real and imaginary)
#
def convertMAtoRI(mag,ang):
	return complex(cm.rect(mag,ang*np.pi/180.))
#########################################################################################################################################################################################
# converts a magnitude in dB and angle (in degrees) to complex number para (real and imaginary)
#
def convertdBtoRI(magdB,ang):
	return complex(cm.rect(np.power(10.,magdB/20.),ang*np.pi/180.))
#########################################################################################################################################################################################
# converts a complex number para (real and imaginary) to  a returned dB polar coordinates where the real part is the magnitude and the imaginary part is the angle in degrees
#
def convertRItodB(para):
	return complex(20.*np.log10(cm.polar(para)[0]),180.*cm.polar(para)[1]/np.pi)
############################################################################################################################################################################
# convert reflection coefficient to impedance and admittance
# gamma is in magnitude and angle (degrees) with the real part of gamma being the magnitude and the imaginary part the angle in degrees
def gammatoYZ(gamma=None,Z=True,Z0=50):
	gamma_ri=convertMAtoRI(gamma.real,gamma.imag)
	if Z:       # then calculate impedance from admittance and output as real and imaginary
		Z=Z0*(1+gamma_ri)/(1-gamma_ri)
		return Z
	else:
		Y=(1-gamma_ri)/(Z0*(1+gamma_ri))
		return Y
#########################################################################################################################################################################

#########################################################################################################################################################################################
# find maximum unilateral gain from complex S-parameters
#
def convertSRItoUMAX(s11,s21,s22):
	try:
		U=abs(s21)*abs(s21)/((1-abs(s11)*abs(s11))*(1-abs(s22)*abs(s22)))
	except ZeroDivisionError:
		print ("ERROR: cannot calculate maximum unilateral gain because S11 or S22 approach unity ")
		return 1.E40				# essentially return infinity
	if U<=0.: return 1.E-20			# if U is zero or negative it's nonphysical so return a very small nonzero number
	return U
#########################################################################################################################################################################################
# find maximum stable gain (MSG) or maximum available gain (MAG) from complex S-parameters
def convertSRItoGMAX(s11,s21,s12,s22):
	K =convertSRItoK(s11,s21,s12,s22)
	if K > 1.E20:
		if abs(s21)<=epsilon:
			return 0.
		if abs(s12)<=epsilon:									# then the device under test (DUT) is unilateral
			return convertSRItoUMAX(s11,s21,s22)				# for a unilateral device GMAX=UMAX
	elif K>=1.: return {'gain':(abs(s21)/abs(s12))*(K-np.sqrt(K*K-1)),'stability_factor':K}
	elif K<1.: return {'gain':abs(s21)/abs(s12),'stability_factor':K}
#########################################################################################################################################################################################
# find stability factor from complex S-parameters
#
def convertSRItoK(s11=None,s21=None,s12=None,s22=None):
	try:
		d = 1./(2.*abs(s21*s12))
	except ZeroDivisionError:
		#print "ERROR: cannot calculate stablity factor because S12 and/or S21 approaches zero "
		return 1.E40		# essentially return infinity
	D2= np.square(abs(s11*s22-s12*s21))
	return (1.-np.square(abs(s11))-np.square(abs(s22))+D2)*d		# this is K the stability factor
#########################################################################################################################################################################################
# find complex 2-port H parameters from complex S-parameters
# assumes that both port characteristic impedances are the same and equal to Z0
def convertSRItoH(s11=None,s21=None,s12=None,s22=None,Z0=50.):
	if s11==None or s21==None or s12==None or s22==None: raise ValueError("ERROR! missing S-parameter value")
	R0 = Z0.real
	D = (1-s11)*(np.conj(Z0)+s22*Z0)+s12*s21*Z0
	h11=((np.conj(Z0)+s11*Z0)*(np.conj(Z0)+s22*Z0)-s12*s21*Z0*Z0)/D
	h21 = -2.*s21*R0/D
	h12 = 2.*s12*R0/D
	h22 = ((1.-s11)*(1.-s22)-s12*s21)/D
	return h11,h21,h12,h22
#########################################################################################################################################################################################
# find complex 2-port Y parameters from complex S-parameters
# assumes that both port characteristic impedances are the same and equal to Z0
# assumes that Z0 is real and the same for both ports
def convertSRItoY(s11=None,s21=None,s12=None,s22=None,Z0=50.):
	if s11==None or s21==None or s12==None or s22==None: raise ValueError("ERROR! missing S-parameter value")
	R0 = Z0
	D = (Z0+s11*Z0)*(Z0+s22*Z0)-(s12*s21*Z0*Z0)
	y11=( (1.-s11)*(Z0+s22*Z0)+s12*s21*Z0 )/D
	y21 = -2.*s21*R0/D
	y12 = -2.*s12*R0/D
	y22 = ((Z0+s11*Z0)*(1.-s22)+s12*s21*Z0)/D
	#rfgm=-(y12-y21)
	return y11,y21,y12,y22
#########################################################################################################################################################################################
#########################################################################################################################################################################################
# find complex 2-port Y parameters from complex S-parameters
# assumes that both port characteristic impedances are the same and equal to z0
# assumes that z0 is real and the same for both ports
# similar to convertSRItoY() but uses 2x2 matrices
def convertStoY(S=None,z0=50.):
	#if S==None: raise ValueError("ERROR! missing S-parameter value(s)")
	r0=z0
	Y=np.empty((2,2),complex)
	r0 = z0
	D = (z0+S[0,0]*z0)*(z0+S[1,1]*z0)-(S[0,1]*S[1,0]*z0*z0)
	Y[0,0]=( (1.-S[0,0])*(z0+S[1,1]*z0)+S[0,1]*S[1,0]*z0 )/D
	Y[1,0] = -2.*S[1,0]*r0/D
	Y[0,1] = -2.*S[0,1]*r0/D
	Y[1,1] = ((z0+S[0,0]*z0)*(1.-S[1,1])+S[0,1]*S[1,0]*z0)/D
	return Y
#########################################################################################################################################################################################
# find complex 2-port T parameters from complex S-parameters S=np.array([S11,S12],[S21,S22]])
# assumes that the T and S parameters are given in 2x2 matrices of real,imaginary format (complex numbers)
# assumes that both port characteristic impedances are the same and equal to Z0
# assumes that Z0 is real and the same for both ports
def convertSRItoT(S=None):
	#if S==None: raise ValueError("ERROR! missing S-parameter value(s)")
	if abs(S[1,0])<1e-9:
		print("WARNING! |s21| too small, less than 1E-9 so setting s21=1E-9+j0.")
		S[1,0]=1E-9+0j
	T=np.empty((2,2),complex)
	# T[0,0]=1./S[1,0]
	# T[0,1]=-S[1,1]/S[1,0]
	# T[1,0]=S[0,0]/S[1,0]
	# T[1,1]=(S[0,1]*S[1,0]-S[0,0]*S[1,1])/S[1,0]

	# new as of April 22, 2020
	det=S[0,0]*S[1,1]-S[0,1]*S[1,0]     # det=S11*S22-S12*S21
	T[0,0]=-det/S[1,0]          # T11=-det/S21
	T[0,1]=S[0,0]/S[1,0]        # T12=S11/S21
	T[1,0]=-S[1,1]/S[1,0]       # T21=-S22/S21
	T[1,1]=1./S[1,0]            # T22=1/S21
	return T
#########################################################################################################################################################################################
# find complex 2-port S parameters from complex T-parameters where S=np.array([S11,S12],[S21,S22]])
# assumes that the T and S parameters are given in 2x2 matrices of real,imaginary format (complex numbers)
# assumes that both port characteristic impedances are the same and equal to Z0
# assumes that Z0 is real and the same for both ports
def convertTRItoS(T=None):
	#if T==None: raise ValueError("ERROR! missing T-parameter value(s)")
	if abs(T[0,0])<1e-9:
		print("WARNING! |t11| too small, less than 1E-9 so setting t11=1E-9+j0.")
		T[0,0]=1E-9+0j
	S=np.empty((2,2),complex)
	# S[0,0]=T[1,0]/T[0,0]
	# S[0,1]=(T[0,0]*T[1,1]-T[0,1]*T[1,0])/T[0,0]
	# S[1,0]=1./T[0,0]
	# S[1,1]=-T[0,1]/T[0,0]

	# new as of April 22, 2020
	det=T[0,0]*T[1,1]-T[0,1]*T[1,0]     # det=T11*T22-T12*T21
	S[0,0]=T[0,1]/T[1,1]                # S11=T12/T22
	S[0,1]=det/T[1,1]                   # S12=det/T22
	S[1,0]=1./T[1,1]                    # S21=1/T22
	S[1,1]=-T[1,0]/T[1,1]               # S22=-T21/T22
	return S
#########################################################################################################################################################################################
# find complex 2-port Z parameters from complex 2-port S parameters where S=np.array([S11,S12],[S21,S22]]) and Z=np.array([Z11,Z12],[Z21,Z22]])
def convertStoZ(S=None,z0=50.):
	#if S==None: raise ValueError("ERROR! missing S-parameter value(s)")
	r0=z0
	Z=np.empty((2,2),complex)
	D = (1-S[0,0])*(1-S[1,1])-S[0,1]*S[1,0]
	Z[0,0]=((z0+S[0,0]*z0)*(1-S[1,1])+S[0,1]*S[1,0]*z0)/D
	Z[0,1]=(2*S[0,1]*r0)/D
	Z[1,0]=(2*S[1,0]*r0)/D
	Z[1,1]=((1-S[0,0])*(z0+S[1,1]*z0)+S[0,1]*S[1,0]*z0)/D
	return Z
#########################################################################################################################################################################################

# get input reflection coefficient from complex S-parameters
# transducer power gain is Pouttoload/Pavailable where Pout is the power output from port 2 and Pavailabel is the maximum power available (if the generator were matched) from the generator
# S is the 2x2 matrix S-parameters of the two-port
# gammaout is the load reflection coefficient in real+jimaginary
def convertSRItoinputreflection(S=None,gammaout=None,MA=False):
	if gammaout==None: gammaout=complex(0.,0.)
	gin=S[0,0]+S[0,1]*S[1,0]*gammaout/(1-S[1,1]*gammaout)
	if MA: gin=convertRItoMA(gin)
	return gin
#########################################################################################################################################################################################
# get transducer power gain from complex S-parameters
# transducer power gain is Pouttoload/Pavailable where Pout is the power output from port 2 and Pavailabel is the maximum power available (if the generator were matched) from the generator
# S is the 2x2 matrix S-parameters of the two-port
# gammain is the generator reflection coefficient in real+jimaginary
# gammaout is the load reflection coefficient in real+jimaginary
def convertSRItoGt(S=None,gammain=None,gammaout=None,dBout=False):
	if gammain==None: gammain=complex(0.,0.)
	if gammaout==None: gammaout=complex(0.,0.)
	g1=convertSRItoinputreflection(S=S,gammaout=gammaout,MA=False)
	gain=(1-np.power(abs(gammain),2))*np.power(abs(S[1,0]),2)*(1-np.power(abs(gammaout),2))/(np.power(abs(1-gammain*g1),2)*np.power(abs(1-S[1,1]*gammaout),2))
	if dBout: gain=10*np.log10(gain)
	return gain
#########################################################################################################################################################################################
# cascade two 2-port S-parameters at a single frequency given S-parmeters as a 2x2 Numpy matrix of real+jimaginary pairs where S=np.array([S11,S12],[S21,S22]])
# assumes that the S parameters are given in real,imaginary format (complex numbers)
# output is the resultant cascaded set of S-parameters
# assumes that both port characteristic impedances are the same and equal to Z0
# assumes that Z0 is real and the same for both ports
def cascadeS(S1=None,S2=None):
	#if S1==None or S2==None: raise ValueError("ERROR! missing S-parameter value(s)")
	T1=convertSRItoT(S1)
	T2=convertSRItoT(S2)
	T=np.dot(T1,T2)
	return convertTRItoS(T)
#########################################################################################################################################################################################
#########################################################################################################################################################################################
# cascade two 2-port S-parameters at all their common frequencies given S-parmeters as a 2x2 Numpy matrix of real+jimaginary pairs where S=np.array([S11,S12],[S21,S22]])
# assumes that the S parameters are given in real,imaginary format (complex numbers)
# output is the resultant cascaded set of S-parameters at ONLY the frequencies which exactly match
# assumes that both port characteristic impedances are the same and equal to Z0
# assumes that Z0 is real and the same for both ports
def cascadeSf(S1=None,S2=None):
	f1=list(S1.keys())          # list of frequencies in MHz of S1
	f2=list(S2.keys())          # list of frequencies in MHz of S2
	fcommon=list(set(f1)&set(f2))     # list of frequencies common to both S1 and S2
	Sout={f:cascadeS(S1[f],S2[f]) for f in fcommon}
	return Sout
#########################################################################################################################################################################################

#########################################################################################################################################################################################
# find rf gm vs frequency from the S-parameter data
# assumes that both port characteristic impedances are the same and equal to Z0
# assumes that Z0 is real and the same for both ports
def convertSRItoRFGm(s11=None,s21=None,s12=None,s22=None,Z0=50.):
	if s11==None or s21==None or s12==None or s22==None: raise ValueError("ERROR! missing S-parameter value")
	R0 = Z0
	D = (Z0+s11*Z0)*(Z0+s22*Z0)-(s12*s21*Z0*Z0)
	y21 = -2.*s21*R0/D
	y12 = -2.*s12*R0/D
	rfgm=abs(y12-y21)
	return rfgm
#########################################################################################################################################################################################
#########################################################################################################################################################################################
# find rf go and Co vs time from S22 vs time data
# S22 is at a single frequency = frequency parameter
#  assumes that the port characteristic impedance is equal to Z0
# assumes that Z0 is real
# frequency is in Hz
# s22[time index]
# s22 is in real,imaginary complex number format
# go is in siemens and co in farads
def convertS22vstimeto_goco(s22=None,frequency=None,Z0=50.):
	if s22==None: raise ValueError("ERROR! missing S22 values")
	if frequency==None: raise ValueError("ERROR! missing frequency")
	R0 = Z0
	go=[((1.-s)/(Z0*(1.+s))).real  if abs(1.+s)>1.E-20 else 99E10 for s in s22]
	co=[((1.-s)/(Z0*(1.+s))).imag/(2.*np.pi*frequency)  if abs(1.+s)>1.E-20 else 99E10 for s in s22]
	return go,co
#########################################################################################################################################################################################
#########################################################################################################################################################################################
# find rf output conductance vs frequency from the S-parameter data. Not normalized
# assumes that both port characteristic impedances are the same and equal to Z0
# assumes that Z0 is real and the same for both ports
def convertSRItoRFGo(s22=None,Z0=50.):
	if s22==None: raise ValueError("ERROR! missing S-parameter value")
	G0 = 1/Z0
	rfgo=(G0*(1.-s22)/(1.+s22)).real
	return rfgo
#########################################################################################################################################################################################
# DC IV functions
#########################################################################################################################################################################################
# uses polynomial fit to determine Y function
# Y function determination of contact resistance, threshold voltage Vth, and smoothed gm curve. The Y-function is derived from the best linear fit
# find threshold voltage for a single-swept transfer curve
#Inputs:
# Vgs is the Vgs array, Id the Id array to form Id vs Vgs
# Vds is the fixed value of drain voltage used in the transfer curve sweep (Id vs Vgs sweep)
# norder is the order of a polynomial fit to the Id vs Vgs curve
# fractVgsfit is the fraction of the total Vgs sweep used to find the best linear fit of the Y function vs Vgs
# Returns:
# Idfit is the polynomial fit of the Id vs Vds curve
# Idlin is the line which best fits the polynomial Id curve fit
# Idleak is the Idfit where |Idfit| is a minimum
# VgsIdleak is the Vgsfit where |Idfit| is a minimum Vgsfit is the set of gate voltages used to evaluate Idfit polynomial fit to measured Id
# Idmax is the Id where |Idfit| is a maximum
# VgsIdmax is the Vgsfit (gate voltage) where |Idfit| is a maximum and Vgsfit is the set of gate voltages used to evaluate Idfit polynomial fit to measured Id
# Idonoffratio is |Idfitmax/Idleak| at Idfitmax which masximizes |Idfitmax| and Idleak which minimizes |Idleak| Note that Idleak is from the MEASURED DATA and Idfitmax is from the polynomial
# fit of Id
# gmfit is the transconductance curve derived from the first derivative of Idfit (polynomial fit of the measured Id)
# Yf is the Y-function based on a polynomial fit of order norder for Id (i.e. Idfit)
# Yflin is the best linear fit to the Y-function over the specifed fractVgsfit range of Vgs
# Vth is the threshold voltage derived from the Y-function linear fit, Yflin
# Rc is the contact resistance derived from the Y-function linear fit, Yflin

def find_Vth_Rc_gm(*args):
	Idlin = []
	Yflin = []
	Rc=-1
	VthY=-100

	VthId = -1.E99											# could not calculate threshold voltage so return  bogus number
	# first find number of points to fit line over
	if len(args)>4:
		Vds = args[0]
		Id = args[1]
		Vgs = args[2]
		norder = args[3]
		fractVgsfit = args[4]
		noptspolyfit = len(Vgs)
	if len(args)==6:
		noptspolyfit = args[5]					# this is the number of points in the polynomial fitting curves - Idfit, gmfit, and Vgsfit. If not specified, then noptspolyfit = the number of points in Id and Vgs
		if noptspolyfit<len(Vgs): noptspolyfit=len(Vgs)				# have at least len(Vgs) points in parameter arrays (e.g. Idfit, Vgsfit, gmfit, ...
	if len(args)<5 or len(args)>6: raise ValueError('ERROR! wrong number of parameters!')

	if fractVgsfit>0.75:
		print ("ERROR! from find_Vth_Rc_gm in device_parameter_request.py - linear fit over too large a fraction of Vgs in the transfer curve! No VthY nor  calculated!")
		return("no threshold voltage calculated")
	if len(Vgs) != len(Id):
		raise ValueError('ERROR! different number of points in the gate voltage array vs the drain current array')
	Vgsfit = np.linspace(Vgs[0],Vgs[-1],noptspolyfit)					# make array of gate voltages for use with the polynomial fit calculated gmfit, Idfit ...
	# fit a polynomial of order n to the measured Id curve and use the fit curve Idpolyr to find the leakage current
	Idpolyraw = np.polyfit(Vgs,Id,norder)	# find the polynomial coefficients of the raw Id(Vgs) transfer curve for a given polynomial order norder - This is a polynomal fit to the directly measured data.
	#Idleak = np.polyval(Idpolyraw,Vgs[ min( range(len(Vgs)), key=lambda i: abs(np.polyval(Idpolyraw,Vgs[i])) ) ])# find leakage current from the polynomial curve fit to the measured Id data
	iVgsIdleak = min( range(len(Vgsfit)), key=lambda i: abs(np.polyval(Idpolyraw,Vgsfit[i])) )	# gate voltage index of the leakage current minimum absolute value drain current from the polynomial fit
	iVgsIdmin = min( range(len(Id)), key=lambda  i: abs(Id[i]))	# gate voltage index of the current minimum Id from the measured drain current (Id) - note that the above iVgsIdleak is based on the polynomial fit of Id
	VgsIdleak = Vgsfit[iVgsIdleak]
	VgsIdmin = Vgs[iVgsIdmin]			# gate voltage where the minimum of the absolute value of the MEASURED drain current occurs (Id)
	Idmin = abs(Id[iVgsIdmin])			# absolute value of the MEASURED drain current having the minimum absolute value
	Idleak = np.polyval(Idpolyraw,VgsIdleak)# find leakage current from the polynomial curve fit to the measured Id data i.e. Idfit where |Idfit| is minimum from the polynomial fit of Id
	iVgsIdmax= max( range(noptspolyfit), key=lambda i: abs(np.polyval(Idpolyraw,Vgsfit[i])) )
	VgsIdmax=Vgsfit[iVgsIdmax]
	Idmax = abs(np.polyval(Idpolyraw,VgsIdmax))	# |Idfit| where |Idfit| is maximum from the polynomial fit of Id
	#Idmax = np.polyval(Idpolyraw,Vgsfit[ max( range(noptspolyfit), key=lambda i: abs(np.polyval(Idpolyraw,Vgsfit[i])) ) ])
	Idonoffratio=abs(Idmax/Idmin)			# on-off ratio using the polynomial fit of Id to get Idmax and the minimum absolute value of the measured Id to get Idmin
	# now subtract out the leakage current from the measured Id and fit a new polynomial to the result to get an estimate of the leakage-free Id i.e. Idfit[]
	#Idpoly = np.polyfit(Vgs,[I-Idleak for I in Id],norder) # find the polynomial coefficients of the transfer curve with the leakage current removed for a given polynomial order norder
	#gmpoly = np.polyder(Idpoly)							# find the gm polynomial coefficients from the transfer curve polynomial coefficients - i.e. the first derivative
	gmpoly = np.polyder(Idpolyraw)							# find the gm polynomial coefficients from the transfer curve polynomial coefficients - i.e. the first derivative
	Idfit = [np.polyval(Idpolyraw,Vgsfit[ii]) for ii in range(0,noptspolyfit)]
	gmfit = [np.polyval(gmpoly,Vgsfit[ii]) for ii in range(0,noptspolyfit)]
	Yf = [Idfit[ii]/np.sqrt(abs(gmfit[ii])) for ii in range(0,noptspolyfit)]

# find best least squares linear fit to Yf ###################################################################################################
#
# 	deltanpts = int(fractVgsfit*noptspolyfit)					# number of Vgs points for the linear fit
# 	iVgsYfbestfit = max(range(len(Vgsfit)-deltanpts), key=lambda iiVgs: st.linregress(Vgsfit[iiVgs:iiVgs+deltanpts],Yf[iiVgs:iiVgs+deltanpts])[2] )		# find Vgs index which yields the best fit of Yf[Vgs] to a line
# 	mbestfit,bbestfit,rvalbestfit,pval,stderr=st.linregress(Vgsfit[iVgsYfbestfit:iVgsYfbestfit+deltanpts],Yf[iVgsYfbestfit:iVgsYfbestfit+deltanpts])	# final call to least squares linear fit to get parameters of the fit
# 	Vgsbestfit = Vgsfit[iVgsYfbestfit+int(deltanpts/2)]
# 	Idbestfit = Idfit[iVgsYfbestfit+int(deltanpts/2)]
# 	statusdata = ""								# used to indicate status of calculations and trap bad data
# 	try: mbestfit
# 	except:
# 		statusdata = "no slope calculated "
# 		print("WARNING! find_Vth_Rc_gm() No Rc or threshold voltage data for this device because could not fit Y-function to positive slope - probably bad device")
# 	if "no" not in statusdata:
# 		try: Gmc = mbestfit*mbestfit/Vds
# 		except:
# 			statusdata +="Vds=0 "
# 			print("WARNING! find_Vth_Rc_gm() No Rc or threshold voltage data for this device because Vds=0 or too small")
# 		if "0" not in statusdata:
# 			try: VthY = -bbestfit/np.sqrt(Vds*Gmc)							# threshold voltage calculation
# 			except:
# 				statusdata +="Vds=0 and/or Gmc=0 "
# 				print("WARNING! find_Vth_Rc_gm() No Rc or threshold voltage data for this device because Vds=0 and/or Gmc=0 and/or either or both are too small- probably bad device")
# 			if "0" not in statusdata:
# 				try: Rc = (Vgsbestfit/Idbestfit)-1./(2.*Gmc*(Vgsbestfit-VthY))							# contact resistance calculation
# 				except:
# 					statusdata +="Vgsbestfit-VthY=0 and/or Gmc=0 "
# 					print("WARNING! find_Vth_Rc_gm() No Rc or threshold voltage data for this device because Vds=0 and/or Gmc=0 and/or either or both are too small- probably bad device")
# 				if "0" not in statusdata:
# 					Yflin = [mbestfit*V+bbestfit for V in Vgsfit]			# form line which is the best linear fit of the Y function over the specified fraction of Vgs
# 	if ("no slope calculated" in statusdata) or ("0" in statusdata):
# 		# indicate bad data
# 		Rc = -1.E99
# 		VthY = -1.E99
# 		Yflin = []
#
# 	iVgsIdbestfit = max(range(noptspolyfit-deltanpts), key=lambda iiVgs: st.linregress(Vgsfit[iiVgs:iiVgs+deltanpts],Idfit[iiVgs:iiVgs+deltanpts])[2] )		# find Vgs index which yields the best fit of Idfit[Vgs] to a line
# 	mIbestfit,bIbestfit,rvalbestfit,pval,stderr=st.linregress(Vgsfit[iVgsIdbestfit:iVgsIdbestfit+deltanpts],Idfit[iVgsIdbestfit:iVgsIdbestfit+deltanpts])	# final call to least squares linear fit to get parameters of the fit
# 	statusdata = ""								# used to indicate status of calculations and trap bad data
# 	try: mIbestfit
# 	except:
# 		statusdata =  "no slope calculated "
# 		print("WARNING! find_Vth_Rc_gm() No Id threshold or Idlin because could not get positive slope - probably bad device")
# 	if "no" not in statusdata:
# 		try: VthId = -bIbestfit/mIbestfit							# estimate of threshold voltage from Idfit
# 		except:
# 			statusdata =  "no threshold voltage Ic calculated "
# 			print("WARNING! find_Vth_Rc_gm() No Id threshold or Idlin because could not get positive slope - probably bad device")
# 	if "no" not in statusdata:
# 		Idlin = [mIbestfit*V+bIbestfit for V in Vgs]			# form line which is the best linear fit of the Id polynomial function over the specified fraction of Vgs
# 	else:
# 		# indicate bad data - could not calculate
# 		Idlin = []
# 		Yflin = []
# 		VthId = -1.E99											# could not calculate threshold voltage so return  bogus number
# 		#print len(Idfit),len(Vgsfit)
	return [Rc,VthY,VthId,Idfit,Idlin,Idleak,Idmin,VgsIdleak,VgsIdmin,Idmax,VgsIdmax,Idonoffratio,gmfit,Yf,Yflin,Vgsfit]
		#   0    1    2     3     4     5      6        7      8       9       10         11        12  13   14    15
#########################################################################################################################################################################################
#########################################################################################################################################################################################
# Alex adopted Phil's function below to use the smooth_spline_1d function
# uses spline fit to determine Y-function
# Y function determination of contact resistance, threshold voltage Vth, and smoothed gm curve. The Y-function is derived from the best linear fit
# find threshold voltage for a single-swept transfer curve
# Inputs:
# Vgs is the Vgs array, Id the Id array to form Id vs Vgs
# Vds is the fixed value of drain voltage used in the transfer curve sweep (Id vs Vgs sweep)
# norder is the order of a polynomial fit to the Id vs Vgs curve
# fractVgsfit is the fraction of the total Vgs sweep used to find the best linear fit of the Y function vs Vgs
# Returns:
# Idspline is the spline fit of the Id vs Vds curve
# Idleak is the Idsplne where |Idsplne| is a minimum
# VgsIdleak is the Vgsfit where |Idsplne| is a minimum Vgsfit is the set of gate voltages used to evaluate Idsplne polynomial fit to measured Id
# Idmax is the Id where |Idsplne| is a maximum
# VgsIdmax is the Vgsfit (gate voltage) where |Idsplne| is a maximum and Vgsfit is the set of gate voltages used to evaluate Idsplne polynomial fit to measured Id
# Idonoffratio is |Idsplnemax/Idleak| at Idsplnemax which masximizes |Idsplnemax| and Idleak which minimizes |Idleak| Note that Idleak is from the MEASURED DATA and Idsplnemax is from the polynomial spline
# fit of Id
# gmfit is the transconductance curve derived from the first derivative of Idsplne (polynomial fit of the measured Id)
# Yf is the Y-function based on a polynomial fit of order norder for Id (i.e. Idsplne)
# Yflin is the best linear fit to the Y-function over the specifed fractVgsfit range of Vgs
# Vth is the threshold voltage derived from the Y-function linear fit, Yflin
# Rc is the contact resistance derived from the Y-function linear fit, Yflin
# sf is the smoothing factor used to smooth the spline fit of Id which is used to calculate gm
def find_Vth_Rc_gm_spline(Vds=[], Id=None, Vgs=[], Ig=[], npolyorder=7, nsplineorder=3, fractVgsfit=None, noptspolyfit=None, Idleakfractmetal=0.0, sf=None,deltaVgsplusthres=None,performYf=False):
	Rc = -1
	VthY = -100
	Yflin = []
	#Id_atthesholdplusdelta=None
	#print("from line 462 in calculated_parameters.py, fractVgsfit=",fractVgsfit)

	# if len(Vgs) != len(Id): raise ValueError("ERROR! Id and Vgs have different array sizes")
	# if Vds==None: raise ValueError('ERROR! No Vds value given')
	# if Id==None or len(Id)<1: raise ValueError('ERROR! No Id array given')
	# if Vgs==None or len(Vgs)<1: raise ValueError('ERROR! No Vgs array given')
	if fractVgsfit == None:
		raise ValueError('ERROR! No fractVgsfit value given')
	elif fractVgsfit > 1.:
		print("WARNING: fractVgsfit>1 so resetting to 1")
		fractVgsfit = 1.
	Vgs = list(Vgs)
	Id = list(Id)

	### must first eliminate points which have the same values of Vgs to produce a curve with monotonically increasing or decreasing Vgs. This was necessary because non monotonic Vgs causes uncatchable crashes in  UnivariateSpline() and leads to undefined derivatives and undefined Gm
	if np.sum(np.diff(Vgs)) > 0:
		Vgsincreasing = True  # flag to detect overall increasing Vgs
		Vgs_spline, Id_reduced = list(zip(*[(Vgs[i], Id[i]) for i in range(len(Vgs)) if i == 0 or Vgs[i] > max(Vgs[:i])]))  # eliminate points that retrace the curve - so that Vgs is unique for all points
		if len(Ig) > 0:
			Vgs_splineIg, Ig_reduced = list(zip(*[(Vgs[i], Ig[i]) for i in range(len(Vgs)) if i == 0 or Vgs[i] > max(Vgs[:i])]))  # eliminate points that retrace the curve - so that Vgs is unique for all points
		else:
			Ig_reduced = None
	else:
		Vgsincreasing = False
		Vgs_spline, Id_reduced = list(zip(*[(Vgs[i], Id[i]) for i in range(len(Vgs)) if i == 0 or Vgs[i] < min(Vgs[:i])]))  # eliminate points that retrace the curve - so that Vgs is unique for all points
		if len(Ig) > 0:
			Vgs_splineIg, Ig_reduced = list(zip(*[(Vgs[i], Ig[i]) for i in range(len(Vgs)) if i == 0 or Vgs[i] < min(Vgs[:i])]))  # eliminate points that retrace the curve - so that Vgs is unique for all points
		else:
			Ig_reduced = None
	if len(Vgs_spline) != len(Id_reduced): raise ValueError('ERROR! different number of points in the measured gate voltage array vs the measured drain current array')
	if len(Ig) > 0 and len(Vgs_spline) != len(Ig_reduced): raise ValueError('ERROR! different number of points in the measured gate voltage array vs the measured gate current array')
	################

	if noptspolyfit == None or noptspolyfit < len(Vgs_spline): noptspolyfit = len(Vgs_spline)  # this is the number of points in the polynomial fitting curves - Idsplne, gmfit, and Vgs_spline. If not specified, then noptspolyfit = the number of points in Id and Vgs		# have at least len(Vgs) points in parameter arrays (e.g. Idfit, Vgsfit, gmfit, ...
	if fractVgsfit > 1.0: raise ValueError("ERROR! from find_Vth_Rc_gm in device_parameter_request.py - linear fit over too large a fraction of Vgs in the transfer curve! No VthY nor  calculated!")

	Vgsfit = np.linspace(Vgs[0], Vgs[-1], noptspolyfit)  # make array of gate voltages for use with the polynomial fit calculated gmfit, Idspline ...

	# fit a polynomial of order n to the measured Id curve and use the fit curve Idpolyr to find the residuals to be used in making the spline fit of Id = Idspline
	# Idpoly = np.polyfit(Vgs_spline,Id_reduced,npolyorder)	# find the polynomial coefficients of the raw Id(Vgs) transfer curve for a given polynomial order norder - This is a polynomal fit to the directly measured Id(Vgs) data.

	iVgsIdmin = min(range(len(Id_reduced)), key=lambda i: abs(Id_reduced[i]))  # gate voltage index of the current minimum Id from the measured drain current (Id) - note that the above iVgsIdleak is based on the polynomial fit of Id Note, Id is not the raw data here but rather the raw data with points possibly eliminated to remove non-monotonic Vgs
	VgsIdmin = Vgs_spline[iVgsIdmin]  # gate voltage where the minimum of the MEASURED drain current occurs (Id). Note, Id is not the raw data here but rather the raw data with points possibly eliminated to remove non-monotonic Vgs
	Idmin = Id_reduced[iVgsIdmin]  # MEASURED drain current having the minimum absolute value
	if len(Ig) > 0:
		IgatIdmin = abs(Ig_reduced[iVgsIdmin])
	else:
		IgatIdmin = None

	# now find Ig (gate current) having the maximum absolute value from the "Ig reduced" curve produced from removing non-monotoniclly increasing Vgs
	iVgsIgmax = max(range(len(Ig_reduced)), key=lambda i: abs(Ig_reduced[i]))  # gate voltage index of Ig at the maximum |Ig|
	Igmax = abs(Ig_reduced[iVgsIgmax])
	# now find the spline fit of Id = Idspline, based on the residuals of the polynomial fit of Id
	if not Vgsincreasing:  # Vgs swept from more positive to more negative
		try:
			Idsplinefunc = smooth_spline_1d(np.flipud(Vgs_spline), np.flipud(Id_reduced)) # spline fit function of the measured Id(Vgs) of order nsplineorder (nsplineorder usually = 3) flipup() reverses order of Vgs because we need ascending values of Vgs for the spline fit to work properly
		except:
			# print("from line 342 calculated_parameters.py Warning: could not produce spline fit")
			return None
	else:  # Vgs swept from more negative to more positive
		try:
			Idsplinefunc = smooth_spline_1d(np.array(Vgs_spline), np.array(Id_reduced))  # spline fit function of the measured Id(Vgs) of order nsplineorder (nsplineorder usually = 3) flipup() reverses order of Vgs because we need ascending values of Vgs for the spline fit to work properly
		except:
			# print("from line 347 calculated_parameters.py Warning: could not produce spline fit")
			return None

	usedpolyfit = False
	if not Vgsincreasing:
		Idspline = Idsplinefunc(np.flipud(Vgs_spline))  # spline fit estimate of the measured Id_reduced(Vgs_spline)
	else:
		Idspline = Idsplinefunc(Vgs_spline)  # spline fit estimate of the measured Id_reduced(Vgs_spline)
	if any(math.isnan(I) for I in Idspline):
		raise ValueError("ERROR invalid number")
		# usedpolyfit = True
		# Idpoly = np.polyfit(Vgs_spline, Id_reduced, npolyorder)
		# Idspline = np.polyval(Idpoly, Vgs_spline)  # spline fit not working for this Id data so use polynomial fit
	#print("from line 537 in calculated_parameters len(Idspline)",len(Idspline),len(Id_reduced))

	iVgsIdleak = min(range(len(Vgs_spline)), key=lambda i: abs(Idspline[i]))  # gate voltage index of the leakage current minimum absolute value drain current from the spline fit
	Idleak = Idspline[iVgsIdleak]  # find leakage current, i.e. the minimum of from the spline curve fit to the measured Id data i.e. Idfit where |Idfit| is minimum from the polynomial fit of Id
	VgsIdleak = Vgs_spline[iVgsIdleak]
	# print("calculated_parameters.py line 349") # debug
	Idspline_Y=np.subtract(Idsplinefunc(Vgs_spline),Idleakfractmetal*Idleak)	# spline fit estimate of Id(Vgs) minus the minimum current used to calculate the Y-function. Idleakfractmetal is the portion of current assumed to be caused by the metallic nanotubes
	try:
		gmfunc = Idsplinefunc.derivative()  # derivative function of spline Id function which is an approximation of gm
	except:
		print("from line 547 calculated_parameters.py Warning: could not produce gm")
		return None
	if not Vgsincreasing and not usedpolyfit:
		gmfit = -gmfunc(np.flipud(Vgs_spline))  # gm derived from spline fit which is an array of length Vgs[]
	else:
		gmfit = gmfunc(Vgs_spline)  # gm derived from spline fit which is an array of length Vgs[]


	#Yf=np.divide(np.subtract(Idspline_Y,Idleakfractmetal*Idleak),np.sqrt(abs(gmfit)))							# Y function array (one point for each point in Vgs[] array, calculated from the spline fit of Id(Vgs). The length of Yf[] is the same as Vgs[] and Id[] - the number of points in the spline-fit Id

	iVgsIdmax = max(range(noptspolyfit), key=lambda i: abs(Idsplinefunc(Vgs_spline[i])))  # Idmax is the Id where |Id| from the spline fit is maximum and iVgsIdmax is the spline fit gate voltage index where |Id| spline fit is a maximum
	VgsIdmax = Vgs_spline[iVgsIdmax]
	# maximum of the |spline fit of Id|
	Idmax = max(np.abs(Idspline))
	if math.isnan(Idmax):
		print("from line 563 calculated_parameters.py Warning: could not produce Idmax")
		return None  # if cannot calculate |Idmax| then data are bad so return None
	Idonoffratio = abs(Idmax / Idmin)  # on-off ratio using the spline fit of Id to get Idmax and the minimum absolute value of the measured Id to get Idmin
	# print("from calculated_parameters.py line 368 Idmin, Idmax, on-off ratio",Idmin,Idmax,Idonoffratio)
	# #################################################################################################
	############### Y function calculation if requested
	# # find best fit to Yf############################
	if performYf:
		Yf=np.divide(np.subtract(Idspline_Y,Idleakfractmetal*Idleak),np.sqrt(abs(gmfit)))							# Y function array (one point for each point in Vgs[] array, calculated from the spline fit of Id(Vgs). The length of Yf[] is the same as Vgs[] and Id[] - the number of points in the spline-fit Id
		deltanpts = int(fractVgsfit*len(Vgs_spline))					# number of Vgs points for the linear fit

		#print("from line 572 in calculated_parameters len(Vgs_spline),len(Yf),len(Idspline),len(Idspline_Y),deltaVgsplusthres",len(Vgs_spline),len(Yf),len(Idspline),len(Idspline_Y),deltaVgsplusthres)
		if len(Vgs_spline)!=len(Yf) or len(Vgs_spline)!= len(Idspline) or len(Vgs_spline)!=len(Idspline_Y): raise ValueError("ERROR!: Vgs length != Yf length!")		# sanity check on Vgs[] Yf[]

		iVgsYfbestfit = max(range(len(Vgs_spline)-deltanpts-1), key=lambda iiVgs: st.linregress(Vgs[iiVgs:iiVgs+deltanpts],Yf[iiVgs:iiVgs+deltanpts])[2] )		# find Vgs index which yields the best fit of Yf[Vgs] to a line
		mbestfit,bbestfit,rvalbestfit,pval,stderr=st.linregress(Vgsfit[iVgsYfbestfit:iVgsYfbestfit+deltanpts],Yf[iVgsYfbestfit:iVgsYfbestfit+deltanpts])	# final call to least squares linear fit to get parameters of the linear fit to Yf(Vgs)
		#Yfbestfit = Yf[iVgsYfbestfit+int(deltanpts/2)]				# Yf value at which the linear fit to Yf is optimum
		Vgsbestfit = Vgsfit[iVgsYfbestfit+int(deltanpts/2)]			# Vgs at best linear fit of Yf
		Idbestfit = Idspline_Y[iVgsYfbestfit+int(deltanpts/2)]		# Id value from spline fit

		statusdata = ""								# used to indicate status of calculations and trap bad data
		try: mbestfit
		except:
			statusdata = "no slope calculated "
			print("WARNING! find_Vth_Rc_gm() No Rc or threshold voltage data for this device because could not fit Y-function to positive slope - probably bad device")
		if "no" not in statusdata:
			try: Gmc = mbestfit*mbestfit/Vds
			except:
				statusdata +="Vds=0 "
				print("WARNING! find_Vth_Rc_gm() No Rc or threshold voltage data for this device because Vds=0 or too small")
			if "0" not in statusdata:
				#try: VthY = -bbestfit/np.sqrt(Vds*Gmc)							# threshold voltage calculation
				try: VthY = -bbestfit/np.sqrt(Vds*Gmc)							# threshold voltage calculation
				except:
					statusdata +="Vds=0 and/or Gmc=0 "
					print("WARNING! find_Vth_Rc_gm() No Rc or threshold voltage data for this device because Vds=0 and/or Gmc=0 and/or either or both are too small- probably bad device")
				if "0" not in statusdata:
					try: Rc = (Vds/Idbestfit)-1./(Gmc*(Vgsbestfit-VthY))							# contact resistance calculation
					#try: Rc = (0.5*Vds/Idbestfit)-1./(2.*Gmc*(Vgsbestfit-VthY))							# contact resistance calculation
					#try: Rc = (0.5*Vds/Idbestfit)-Vds/(2.*Gmc*(Vgsbestfit-VthY))							# contact resistance calculation
					except:
						statusdata +="Vgsbestfit-VthY=0 and/or Gmc=0 "
						print("WARNING! find_Vth_Rc_gm() No Rc or threshold voltage data for this device because Vds=0 and/or Gmc=0 and/or either or both are too small- probably bad device")
					#print("from calculated_parameters.py line400 Gmc, Vgsbestfit, VthY, Rc",Gmc,Vgsbestfit,VthY,Rc)
					if "0" not in statusdata:
						Yflin = [mbestfit*V+bbestfit for V in Vgsfit]			# form line which is the best linear fit of the Y function over the specified fraction of Vgs
		if ("no slope calculated" in statusdata) or ("0" in statusdata):
			# indicate bad data
			Rc = -1.E99
			VthY = -1.E99
			Yflin = []
	else:                   # do not perform Y-function calculation
		Yf=[]
		Yflin=[]
		VthY = -1.E99
	######
	# the following variables are obsolete but for legacy, include dummy versions
	Idlin = []
	VthId = -1.E99  # could not calculate threshold voltage so return  bogus number
	#####################
	# find Id at the threshold voltage + a user-defined offset
	if deltaVgsplusthres!=None: Id_atthesholdplusdelta=Idsplinefunc(VthY+deltaVgsplusthres)
	else: Id_atthesholdplusdelta=None
	# print len(Idfit),len(Vgsfit)
	return [Rc, VthY, VthId, Idspline, Idlin, Idleak, abs(Idmin), VgsIdleak, VgsIdmin, Idmax, VgsIdmax, Idonoffratio, gmfit, Yf, Yflin, Vgs_spline, IgatIdmin, Igmax, Id_atthesholdplusdelta]

		#   0    1    2     3        4     5      6            7         8       9       10         11      12  13   14    15			16		17
#########################################################################################################################################################################################
################################################################################################################################################################
# calculate TLM contact resistance Rc and sheet resistance Rsh
# input parameters:
# Rtlm is the list of resistances vs TLM S-D lengths
# Ltlm is the list of S-D metal spacing lengths in um
# Wtlm is the TLM width (default=1
# removes outliers until either only two points remain or the rval reaches that requested
def	calc_TLM(Ltlm=None,Rtlm=None,Wtlm=1.,minLtlm=0.,maxLtlm=None,linearfitquality_request=None):
	if Ltlm==None or Rtlm==None or len(Ltlm)<2 or len(Rtlm)<2: raise ValueError("ERROR! insufficient data to calculate TLM")
	if maxLtlm==None: maxLtlm=max(Ltlm)
	imin=min(range(len(Ltlm)), key=lambda i: abs(Ltlm[i]-minLtlm))
	imax=min(range(len(Ltlm)), key=lambda i: abs(Ltlm[i]-maxLtlm))+1
	#if (imax-imin)<2: raise ValueError("ERROR! interval too short")
	if (imax-imin)<2:
		#print("from calculated_parameters.py line 425 calc_TLM() imax-imin=",imax-imin)
		return None
	Ltlmr= Ltlm[imin:imax]
	Rtlmr=Rtlm[imin:imax]
	m, b, rval, pval, stderr = st.linregress(Ltlmr, Rtlmr)  # find least squares linear fit
	if linearfitquality_request!=None:
		if linearfitquality_request>1. or linearfitquality_request<0.: raise ValueError("ERROR! Illegal value for rvalrequest")
		# loop while removing the point with the worst fit until either the rval<=rvalrequested or we only have two points left -whichever occurs first
		while rval<linearfitquality_request and len(Ltlmr)>2:
			m, b, rval, pval, stderr = st.linregress(Ltlmr, Rtlmr)  # find least squares linear fit
			imaxres = max(range(len(Ltlmr)), key=lambda i: abs(m * Ltlmr[i] + b - Rtlmr[i]))			# find index of the measured value having the greatest deviation from the linear fit and delete this point
			del Ltlmr[imaxres]
			del Rtlmr[imaxres]
			if math.isnan(m) or math.isnan(b) or math.isnan(rval): return None
	if math.isnan(m) or math.isnan(b) or math.isnan(rval) or m<=0.: return None
	#or math.isfinite(m) or math.isfinite(b) or math.isfinite(rval): return None		# catch cases were the linear fit cannot be calculated
	return m*Wtlm,b*Wtlm/2.,rval,				# Rsh, Rc, "goodness" of linear fit
###################################################################################################################################################################
# used to calculate the hysteresis voltage when x=voltage and y=current of a pair of transfer curves
# find the maximum |x| between two curves for a value of y
def calc_xdiff(x1=None,x2=None,y1=None,y2=None):
	if len(x1)==None or len(x2)==None or len(y1)==None or len(y2)==None: raise ValueError("ERROR! missing values")
	if len(x1)!=len(y1):	raise ValueError("ERROR! length x1!=length y1")
	if len(x2)!=len(y2):	raise ValueError("ERROR! length x2!=length y2")
	if len(y1)<5:			raise ValueError("ERROR! less than 5 points in x1,y1 data")
	if len(y2)<5:			raise ValueError("ERROR! less than 5 points in x2,y2 data")

	if np.sum(np.diff(y1))<0:			# have decreasing y1 so flip array
		y1a=np.flipud(y1)
		x1a=np.flipud(x1)
	else:
		y1a=y1
		x1a=x1
	if np.sum(np.diff(y2))<0:			# have decreasing y2 so flip array
		y2a = np.flipud(y2)
		x2a = np.flipud(x2)
	else:
		y2a=y2
		x2a=x2
	#y1c=[(y1a for i in range(0,len(y1a)) if i == 0 or y1a[i] > max(y1a[:i])]
	try: y1b, x1b = zip(*[(y1a[i], x1a[i]) for i in range(0,len(y1a)) if i == 0 or y1a[i] > max(y1a[:i])]) # eliminate points that retrace the curve - so that Vgs is unique for all points
	except: return None
	try: y2b, x2b = zip(*[(y2a[i], x2a[i]) for i in range(0,len(y2a)) if i == 0 or y2a[i] > max(y2a[:i])])  # eliminate points that retrace the curve - so that Vgs is unique for all points
	except: return None

	if len(y1b)<6 or len(y2b)<6:
		return None
	# swap x with y and interpolate
	#f1 = InterpolatedUnivariateSpline(np.array(y1b),np.array(x1b))
	f1=interp1d(y1b,x1b)
	#f2 = InterpolatedUnivariateSpline(np.array(y2b),np.array(x2b))
	f2= interp1d(y2b, x2b)
	ymin=max(min(y1b),min(y2b))
	ymax=min(max(y1b),max(y2b))
	dely=min((max(y1b)-min(y1b))/len(y1b),(max(y2b)-min(y2b))/len(y2b))
	yarray=np.arange(ymin+dely,ymax,dely)
	try:	xarray1=f1(yarray)
	except: return None
	try: xarray2=f2(yarray)
	except: return None
	if len(xarray1)>5 and len(xarray2)>5 and len(xarray1)==len(xarray2):
		maxgap_x=max(np.abs(np.subtract(xarray1,xarray2)))
		#if maxgap_x>50: print("maxgap ",maxgap_x)
	else:
		maxgap_x=None
		return None

	# xmax1=max(abs(f1(y1b)))
	# xmax2= max(abs(f2(y2b)))
	# xmax1i=max(np.abs(xarray1))
	# xmax2i = max(np.abs(xarray2))
	# if xmax1>60: print("xmax1 ",xmax1)
	# if xmax2>60:  print("xmax2 ",xmax2)
	# #
	# if xmax1i > 40: print("xmax1i ", xmax1i,maxgap_x)
	# if xmax2i > 40:  print("xmax2i ", xmax2i)
	# # debug
	# for y in yarray:
	# 	if abs(f1(y))>50: print("f1 ",y,f1(y))
	# 	if abs(f2(y))>50: print("f2 " ,y,f2(y))
	# 	#print("from line 551 calculated_parameters.py ", f1(yarray),f2(yarray))
	return maxgap_x
############################################################################################################################################################################
###################################################################################################################################################################
# used to calculate the hysteresis current when x=voltage and y=current of a pair of transfer curves
# find the maximum |x| between two curves for a value of y
def calc_ydiff(x1=None,x2=None,y1=None,y2=None):
	if len(x1)==None or len(x2)==None or len(y1)==None or len(y2)==None: raise ValueError("ERROR! missing values")
	if len(x1)!=len(y1):	raise ValueError("ERROR! length x1!=length y1")
	if len(x2)!=len(y2):	raise ValueError("ERROR! length x2!=length y2")
	if len(y1)<5:			raise ValueError("ERROR! less than 5 points in x1,y1 data")
	if len(y2)<5:			raise ValueError("ERROR! less than 5 points in x2,y2 data")
	minonx=min(len(x1),len(x2))
	maxgap_y=np.max([abs(y2[i]-y1[min(range(len(x1)), key=lambda j: abs(x2[i]-x1[j]))]) for i in range(0,minonx) ])

	return maxgap_y
#########################################################################################################
# calculate approximate gate-source (Cgs) capacitance in femtofarads from S-parameters which are in complex format (real and imaginary)
# frequency is the RF frequency in Hz
def convertSRItoCgs(s11=None,s21=None,s12=None,s22=None,Z0=50.,frequency=None):
	y11,y21,y12,y22=convertSRItoY(s11=s11,s21=s21,s12=s12,s22=s22,Z0=Z0)
	y = y11+y12      # admittance of Cgs in S is the imaginary component
	Cgs = 1E15*y.imag/(2*np.pi*frequency)
	return Cgs
#########################################################################################################
# calculate approximate gate-drain (Cgd) capacitance in femtofarads from S-parameters which are in complex format (real and imaginary)
# frequency is the RF frequency in Hz
def convertSRItoCgd(s11=None,s21=None,s12=None,s22=None,Z0=50.,frequency=None):
	y11,y21,y12,y22=convertSRItoY(s11=s11,s21=s21,s12=s12,s22=s22,Z0=Z0)
	y = -y12         # admittance of Cgd in S is the imaginary component
	Cgd = 1E15*y.imag/(2*np.pi*frequency)
	return Cgd
#########################################################################################################
# calculate approximate drain (Cd) capacitance in femtofarads from S-parameters which are in complex format (real and imaginary)
# frequency is the RF frequency in Hz
def convertSRItoCds(s11=None,s21=None,s12=None,s22=None,Z0=50.,frequency=None):
	y11,y21,y12,y22=convertSRItoY(s11=s11,s21=s21,s12=s12,s22=s22,Z0=Z0)
	y = y22+y12         # admittance of Cd in S is the imaginary component
	Cds = 1E15*y.imag/(2*np.pi*frequency)
	return Cds


