#__author__ = 'PMarsh Carbonics'
import os
import sys
#import re
import numpy as np
from scipy import stats as st
from PyQt5 import QtCore, QtGui, QtWidgets, Qt
import multiprocessing as mp
import warnings
import collections as c
from scipy.interpolate import UnivariateSpline
from scipy.interpolate import CubicSpline
from loadpull_system_calibration import ENRtable, sacalfactor, volttocurrentcalibrationfactor         # interpolating ENR table, spectrum analyzer level calibration, and voltage to current calibration to measure instantaneous drain current
#from fileview import *								# file viewer tabulated data GUI
import decimal as dec
# utilities functions for wafer probe project
###############################################################################################################################################################################
# form the device name from device parameters such as lot number and wafer position etc....
def formdevicename(*args):
	devicename = args[0]
	for ii in range(1,len(args)):
		devicename += "_"+args[ii]
	return devicename
###############################################################################################################################################################################
# getlisting of all subdirectories from the directory pointed to by pathname and filter according to the rest of the argument list
# returns the name of the subdirectories
def getdirectorylisting(*args):
	if len(args)<1 or len(args)>2:
		raise ValueError('ERROR! incorrect number of parameters')
	pathname = str(args[0])
	rawdirectorylisting = [d for d in os.listdir(pathname) if os.path.isdir(os.path.join(pathname,d)) ]
	if len(args)==1:
		return [d for d in rawdirectorylisting]
	if len(args)==2:
		dcontains = str(args[1])
		return [d for d in rawdirectorylisting if  dcontains in d]
###############################################################################################################################################################################

# get file listings from the directory pointed to by pathname and filter according to the rest of the argument list
def getfilelisting(*args):
	if len(args)<1 or len(args)>3:
		raise ValueError('ERROR! incorrect number of parameters')
	pathname = str(args[0])
	try: rawfilelisting = [f for f in os.listdir(pathname) if os.path.isfile(os.path.join(pathname,f)) ]
	except:
		return None			# no files found!
	if len(args)==1:
		return [f for f in rawfilelisting]
	if len(args)==2:
		fex = args[1]
		return [f for f in rawfilelisting if f.endswith(fex)]
	if len(args)==3:
		fex = str(args[1])
		fcontains = str(args[2])
		return [f for f in rawfilelisting if f.endswith(fex) and fcontains in f]
###############################################################################################################################################################################
# extract unique devicenames from file listing
# this removes .xls, .s2p, transfer ...  and everything following as specified by the input
# returns a list of device names
# def file_to_devicename(*args):
# 	if len(args)<1:
# 		raise ValueError("ERROR! must provide at least one input: a file listing and (optionally) substring(s) to delete")
# 	nlist =0							# Number of filelistings in parameter list should be = 1 or this is an error
# 	delstring = []						# list of strings to delete from filenames to produce devicenames size must be at least 1
# 	for ii in range(0,len(args)):
# 		if args[ii]=="filelisting":
# 			if len(args)<=ii+1:
# 				raise ValueError("ERROR! actual file listing must follow \"filelisting\" designator")
# 			inputdevlisting = args[ii+1]
# 			nlist += 1
# 			if nlist >1:
# 				raise ValueError("ERROR! Too many filelistings given!")
# 		if args[ii]=="delstr":			# a string to delete from the filename listings
# 			if len(args)<=ii+1:
# 				raise ValueError("ERROR! actual string-to-delete must follow \"delstr\" designator")
# 			elif args[ii+1]=="filelisting" or args[ii+1]=="delendstr":
# 				raise ValueError("ERROR! \"filelisting\" or \"delstr\" follows \"delendstr\" but is a keyword and CANNOT be used as a string to be deleted")
# 			delstring.append(args[ii+1])		# this is the string to delete from the filename
#
# 			#print delstring[-1]
# 		if args[ii]=="delendstr":			# delete from this string onward to end of filename string
# 			if len(args)<=ii+1:
# 				raise ValueError("ERROR! actual string-to-delete must follow \"delendstr\" designator")
# 			elif args[ii+1]=="filelisting" or args[ii+1]=="delstr":
# 				raise ValueError("ERROR! \"filelisting\" or \"delendstr\" follows \"delstr\" but is a keyword and CANNOT be used as a string to be deleted")
# 			delendstr = args[ii+1]		# truncate the filename starting with this string
# 			inputdevlisting = [f[:f.find(delendstr)] for f in inputdevlisting]
# 	for idel in range(0,len(delstring)):
# 		inputdevlisting = [f.replace(delstring[idel],'').strip() for f in inputdevlisting ] # remove substrings to be deleted from device listing
# 	# now remove duplicate devicenames
# 	dst = ""
# 	for id in range(0,len(inputdevlisting)):
# 		if inputdevlisting[id] not in dst:
# 			dst += inputdevlisting[id]+" "
# 	return [f.strip() for f in dst.split()]
###############################################################################################################################################################################
# function to remove substrings from device measurement filenames to produce device names.
# only unique device names are produced and if several filenames map to a single devicename only one devicename will be  produced for all those filenames which map to one devicename
# inputdevlisting is a list of filenames to be converted to devicenames and is modified thoughtout the function
# deletestrings are the substrings to be removed from the filenames to produce the devicenames
# there must be specified a filelisting of at least one file (one member in the filelisting) and at least one deletestring. both inputs are lists of strings
def file_to_devicename(inputdevlisting=None,deletestrings=None,deleteendstrings=None):
	if inputdevlisting==None or len(inputdevlisting)<1:	return None
	if deleteendstrings!=None and len(deleteendstrings)>0:
		for idel in range(0,len(deleteendstrings)):			# remove this list of substrings (deleteendstrings) and all subsequent letters to the end of each filename
			inputdevlisting = [f.rsplit(deleteendstrings[idel],1)[0] for f in inputdevlisting]
	if deletestrings!=None and len(deletestrings)>0:
		for idel in range(0,len(deletestrings)):			# remove each of this list of substrings (deletestrings) from each of the filenames
			inputdevlisting = [f.replace(deletestrings[idel],'').strip() for f in inputdevlisting ] # remove substrings to be deleted from device listing
	# now remove duplicate devicenames
	dst = []
	for id in range(0,len(inputdevlisting)):
		if inputdevlisting[id] not in dst:
			dst.append(inputdevlisting[id])
	return dst

###############################################################################################################################################################################
# swap indices in a 2 dimensional array
# assumes that for all values of i in the range 0-len(din) that len(din[0])=len(din[i]) is constant
# def swapindex(din):
# 	dout = []
# 	for iin in range(0,len(din[0])):
# 		dout.append([])
# 		for iout in range(0,len(din)):
# 			dout[-1].append(din[iout][iin])
# 	return dout
def swapindex(din):
	return [list(x) for x in zip(*din)]
###############################################################################################################################################################################
# find linear extrapolation and slope for a line passing through the first point where y is a minimum to fit to a curve over the given fraction interval range
# assumes that for all values of i in the range 0-len(din) that len(din[0])=len(din[i]) is constant
# fit the line around the minimum abs(y) point if minmax=="min" otherwise, fit the line around
# the max abs(y) point
def linfitminmax(parentnotifier=None,x=None,y=None,fractrange=1.,minmax="min"):
	if np.any(x)==None: raise ValueError("ERROR! no x values supplied")
	if np.any(y)==None: raise ValueError("ERROR! no y values supplied")
	if (len(x)!=len(y)):
		raise ValueError("ERROR! number of points in the range is not equal to that of the domain")
	if len(x)<4:
		raise ValueError("ERROR! number of points must be > 3")
	deltanpts = int(fractrange*len(y))					# number of x points for the linear fit
	if deltanpts<3:
		#m=QtWidgets.QMessageBox()
		# m.setText("ERROR! fraction of range to perform linear fit is too small. Range fit Setting INVALID reset")
		# # if parenterrornotifier!=None:
		# # 	parenterrornotifier.emit("rangefittosmallerror")
		# m.exec_()
		#raise ValueError("ERROR! fraction of range to perform linear fit is too small!")
		print("WARNING from linfitminmax() number of points in linear fit was set <3 so increasing fitting range ")
		fractrange=3.1/len(y)
		#fractrange=1.
		deltanpts = int(fractrange*len(y))					# number of x points for the linear fit
		if fractrange>1: raise ValueError("ERROR! too few points in curve to perform linear fit!")
	if fractrange>1.0:
		print("WARNING!! fraction of range exceeds 1.0 -> resetting to 1.0")
		fractrange = 1.0
		deltanpts = int(fractrange*len(y))					# number of x points for the linear fit
	if minmax=="min":
		ii=min(range(len(y)), key=lambda i: np.abs(y[i]))
		#ii = y.index(min(np.abs(y)))
	elif minmax=="max":
		ii=max(range(len(y)), key=lambda i: np.abs(y[i]))
		#ii = y.index(max(np.abs(y)))
	else:
		raise ("ERROR: must specify min or max")
	linfit=[]
	if len(x)>(ii+deltanpts):			# then the minimum point is near the beginning of the series
		m,b,rval,pval,sterr = st.linregress(x[ii:ii+deltanpts],y[ii:ii+deltanpts])
	elif len(x)<=(ii+deltanpts):			# then the minimum point is near the end of the series
		m,b,rval,pval,sterr = st.linregress(x[ii-deltanpts:ii],y[ii-deltanpts:ii])
	for ii in range(0,len(x)):							# form linear extrapolation line
		linfit.append(m*x[ii]+b)
	#print linfit
	return linfit,m,b,rval

###############################################################################################################################################################################
# find linear extrapolation and slope for a least squares linear fit to a series of points, excluding the range above a given value of x
#
def linfitmin(x=None,y=None,minrange=-1.E30,maxrange=1.E30):
	if (len(x)!=len(y)):
		raise ValueError("ERROR! number of points in the range is not equal to that of the domain")
	if maxrange<min(x):
		print ("from linfitmin(): minrange, maxrange ",min(x),maxrange)
		raise ValueError("ERROR! maximum range less than minimum X")
	xx=[]
	yy=[]
	for ii in range(0,len(x)):
		if x[ii]<=maxrange and x[ii]>=minrange:
			xx.append(x[ii])
			yy.append(y[ii])
	if len(xx)<2:
		raise ValueError("ERROR! final number of points must be >=2")
	m,b,rval,pval,stderr = st.linregress(xx,yy)
	return m,b,rval
###############################################################################################################################################################################
# find linear extrapolation and slope for a line which is the best possible linear fit of the set of data points x,y as fit over the fraction of x range, fractrange
# The range of the fit is adjusted to produce the best linear fit
# the line fit xlin,ylin, slope, intercept, and r-value are returned
# Input parameters:
# x is the range array of the function to be fit with a line
# y is the domain array of the function to be fit with a line
# xfitmin is the minimum value of range of the linear fit line
# xfitmax is the maximum value of range of the linear fit line
def linfitbest(x,y,xfitmin,xfitmax,fractrange):
	if (len(x)!=len(y)):
		raise ValueError("ERROR! number of points of the range is not equal to that of the domain")
	if len(x)<4:
		raise ValueError("ERROR! number of points must be > 3")
	deltanpts = int(fractrange*len(y))					# number of x points for the linear fit
	if deltanpts<2:
		raise ValueError("ERROR! fraction of range to perform linear fit is too small!")
	if fractrange>1.0:
		print("WARNING!! fraction of range exceeds 1. -> resetting to 1.")
		fractrange = 1.
		deltanpts = int(fractrange*len(y))					# number of x points for the linear fit

	linfitx=[]
	linfity=[]

	rvalmax = 0.
	for ix in range(0,len(x)-deltanpts):				# find line which gives best linear fit
		m,b,rval,pval,stderr = st.linregress(x[ix:ix+deltanpts],y[ix:ix+deltanpts])
		if rval > rvalmax and m>0:						# find best fit with a positive slope
			rvalmax = rval
			mbestfit = m
			bbestfit = b
	if xfitmin==min(x) and xfitmax==max(x):             # return a line having the same number of points as the original function to be fit
		for ix in range(0,len(x)):							# form linear extrapolation line
			linfitx.append(x[ix])
			linfity.append(mbestfit*x[ix]+bbestfit)
	else:       # return a linear fit line having two points
		linfitx.append(xfitmin)
		linfitx.append(xfitmax)
		linfity.append(mbestfit*xfitmin+bbestfit)
		linfity.append(mbestfit*xfitmax+bbestfit)
	return linfitx,linfity,mbestfit,bbestfit,rval
###############################################################################################################################################################################
###############################################################################################################################################################################
# find linear extrapolation and slope for a line which over a portion of the points starting at npts*lowerfraction to npts*upperfraction inclusive
# where npts is the total number of points in the function to linear fit, lowerfraction is the lower fraction, upper fraction are the points to exclude from the fit at the
# low and high ends of the range respectively

# x is the range array of the function to be fit with a line
# y is the domain array of the function to be fit with a line
# xfitmin is the minimum value of range of the linear fit line
# xfitmax is the maximum value of range of the linear fit line
# returns just the slope and intercept points
def linfitendexclude(x=None,y=None,lowerfraction=None,upperfraction=None):
	if x==None or y==None or lowerfraction==None or upperfraction==None: raise ValueError("ERROR! missing manditory input parameters")
	if (len(x)!=len(y)):
		raise ValueError("ERROR! number of points of the range is not equal to that of the domain")
	if len(x)<2:
		raise ValueError("ERROR! number of points to fit must be > 1")
	lowerxpoint = int(lowerfraction*len(y))					# lower x point for the linear fit
	upperxpoint = int(upperfraction*len(y))					# upper x point for the linear fit
	npts=upperxpoint-lowerxpoint						# total number of points left in the function to be linear fit
	if npts<2:
		raise ValueError("ERROR! fraction of range to perform linear fit is too small!")
	m,b,rval,pval,stderr = st.linregress(x[lowerxpoint:upperxpoint],y[lowerxpoint:upperxpoint])
	return m,b,rval		# m,b, and rval are the least-squares linear fit slope, intercept, and quality of fit respectively
###############################################################################################################################################################################
# defines subdirectory structure here, in one place, for all other classes and functions
# also defines portions of devicenames to search in the device name
# This function enables one to modify the naming conventions as desired in but a single place
def sub(subdir):
	if subdir == "DC":				# subdirectory containing the measured CD IV data
		return "/IV"
	elif subdir == "SPAR" or subdir=="RF":			# subdirectory containing the S-parameter and other small-signal RF measured data
		return "/RF"
	elif subdir == "NOISE":			# subdirectory containing the noise data and other small-signal RF measured data
		return "/RF"
	elif subdir == "RF_power":			# subdirectory containing the S-parameter and other small-signal RF measured data
		return "/RF_power"
	elif subdir == "CALDC":			# subdirectory containing data calculated from DC IV measured data
		return "/IV/calculated"
	elif subdir == "CALS":			# subdirectory containing data calculated from the S-parameter and other small-signal RF measured data measured data
		return "/RF/calculated"
	elif subdir == "WAFER":			# subdirectory containing wafer-level data calculated from the DC IV, S-parameter, and other small-signal RF measured data measured data
		return "/waferlevel"
	elif subdir == "TESTPLAN":		# subdirectory containing wafer test plans
		return "/testplan"
	elif subdir == "GEOMETRY":		# then return the designator used for device geometries such as TLM length and total gate width
		return "/geometry"
	elif subdir == "save":		# then return the designator used for the TLM length indicator which is part of the TLM's device name
		return "/SAVESTATE"
	else:

		raise ValueError("ERROR Unknown subdirectory  or designator specified")
###############################################################################################################################################################################
# finds linear average of parameters given in dB
def dBaverage(dbno):
	dBavg = 10.*np.log10(np.average([pow(10.,l/10.) for l in dbno]))
	return dBavg
###############################################################################################################################################################################
# format numbers cleanly and return a string
# nonexponential flag formats numbers as pure decimal digits + sign + decimal point - NO exponential notation
def formatnum(number,precision=None,type=None,removeplussigns=False,nonexponential=False):
	warnings.resetwarnings()
	warnings.filterwarnings('error')        # set warning behavior to throw errors so non-floats can be trapped
	try: number=float(number)
	except:
		print("from line 293 in utilities.py number not a float",number)
		return number			# just return original string if it's not a number
	warnings.resetwarnings()
	warnings.filterwarnings('default')      # set warning behavior to NOT throw errors
	# try: warnings.warn(Warning())
	# except Warning:
	#	print("Warning from line 297 in untilities.py number could be complex")
	#if nonexponential and not (type=='int' or float(number).is_integer()):
	if nonexponential and not type=='int':
		if precision==None: precision=8
		formatter="{:5."+str(precision)+"f}"
		numstr=str(formatter.format(number))
		return numstr.lstrip()                          # strip off leading whitespaces
	#if type=='int' or float(number).is_integer(): # and abs(number)<=10000):
	if type=='int':
		numstr=str(int(number))
		return numstr
	elif abs(number)<1.E-40:		# this is zero!
		numstr=str('{:5.1f}'.format(number))
	elif abs(number)>10000. or abs(number) < 0.1:
		if precision!=None:
			formatter = "{:5."+str(precision)+"E}"
			numstr=str(formatter.format(number))
			#except: print("fron utilities.py line 263 number= ",number)
			if removeplussigns: numstr=numstr.replace("+","")
		else:
			numstr=str('{:5.1E}'.format(number))	# default precision
			if removeplussigns: numstr=numstr.replace("+","")
	else:
		if precision!=None:
			formatter = "{:5."+str(precision)+"f}"
			numstr=str(formatter.format(number))
		else:
			numstr=str('{:5.1f}'.format(number))	# default precision
	return numstr.lstrip()                          # strip off leading whitespaces
###############################################################################################################################################################################
# find device name indices for a given device name from a list of devices on a wafer
# dl is the list of devices
# namecontains is a string which occurs in the name(s) of all the devices you want the indices for.
def find_devname(dl,namecontains):
	return [i for i in range(len (dl)) if namecontains in dl[i].get_devicename()]	# find all indices to devices having names which contain the substring namecontains
###############################################################################################################################################################################
# Reverse Polish Boolean Algebraic evaluator
# This function determines target devices using a reverse-polish evaluator to select devices on a wafer based on substrings of the target data's filenames
# expression is a string containing the substrings and logical operators separated by commas or spaces
# targefilename is the filename we want to determine if it meets the criteria imposed by the substrings and logic operators
# the returned value is a boolean data True or False which indicates whether the string in targetfilename meets the criteria
def parse_rpn(expression=None,targetfilename=None,parentwidget=None):
	#if parentwidget==None:
	#app=QtWidgets.QApplication(sys.argv)
	#m = QtWidgets.QMessageBox()
	if expression==None or expression=="":
		return True														# because no criteria was given - allow anything to pass
	expression = expression.replace(" ", ",")  # replace all blanks with commas
	while ",," in expression: expression=expression.replace(",,",",")	# make sure only single commas are separating operators and strings
	if targetfilename==None: raise ValueError("ERROR! Must specify both expression and target data file name")
	# first convert expression into logical values and True False
	logicexpression = []		# the logical expression formed from the substrings and logic operators
	for val in expression.split(','):
		if val not in ['or', 'and', 'xor', 'not']:							# then this is NOT a logical operator but rather a substring in the target data filename
			logicexpression.append(val in targetfilename)					# append the logical result of the substring in target filename test
		else: logicexpression.append(val)									# else just append the logic operator

	stack = []
	#print("from 336 in utilities.py expression=", expression)
	for val in logicexpression:
		if val in ['or', 'and', 'xor']:			# binary operations
			#print("from 339 in utilities.py expression=", expression)
			try: op1 = stack.pop()
			except:
				#print("from 342 in utilities.py expression=", expression)
				#m.setText("Warning! Incorrect Boolean Expression. Missing argument!")
				#m.exec()
				#print("from 346 in utilities.py expression=", expression)
				if parentwidget!=None:			# then clear the parent widget
					parentwidget.setText("")
				return 'illegal'
			try: op2 = stack.pop()
			except:
				#print("from 353 in utilities.py expression=", expression)
				#m.setText("Warning! Incorrect Boolean Expression Missing argument!")
				#m.exec()
				if parentwidget != None:  # then clear the parent widget
					parentwidget.setText("")
				return 'illegal'
			if val=='and': result = (op2 and op1)
			elif val=='or': result = (op2 or op1)
			elif val=='xor': result = (op2 != op1)
			stack.append(result)
		elif val=='not':						# unary operation
			op1 = stack.pop()
			result= not op1
			stack.append(result)
		else: stack.append(val)
	return stack.pop()
############################################################################################################################################################################
# database query Boolean filter
############################################################
# execute the query according to the filter
# def filterquery(self,bool_=None):
# 	ops=[]
#
# 	## now have RPN input operands (SQLALCHEMY logic units) and Boolean operators on the RPN input stack - unitops[]. For unitops[], the last item is the top of the stack
# 	### Build Boolean SQLALCHEMY search from unitops[] RPN input stack
# 	RPNstack=[]     # working RPN stack
#
# 	while len(unitops)>0:
# 		while len(unitops)>0 and (type(unitops[-1]) is not str): # push only operands on stack
# 			RPNstack.append(unitops.pop())      # push operand onto stack
# 		if len(unitops)>0:
# 			if unitops[-1]=='not':
# 				if len(RPNstack)<1:         # is Boolean expression valid?
# 					mssg.setText("ERROR! nothing left to apply not_ operator on! Erroneous Boolean expression")
# 					mssg.exec_()
# 					del mssg
# 					return         # return user so they can fix Boolean expression
# 				unitops.pop()
# 				RPNstack.append(not_(RPNstack.pop()))   # negate operand then push it back onto RPNstack[]
# 			elif unitops[-1]=='and':
# 				if len(RPNstack)<2:
# 					mssg.setText("ERROR! less than two operands. ERROR on performing and_ operation: Erroneous Boolean expression")
# 					mssg.exec_()
# 					del mssg
# 					return          # return user so they can fix Boolean expression
# 				op1=RPNstack.pop()
# 				op2=RPNstack.pop()
# 				unitops.pop()
# 				RPNstack.append(and_(op1,op2))
# 			elif unitops[-1]=='or':
# 				if len(RPNstack)<2:
# 					mssg.setText("ERROR! less than two operands. ERROR on performing or_ operation: Erroneous Boolean expression")
# 					mssg.exec_()
# 					del mssg
# 					return          # return user so they can fix Boolean expression
# 				op1=RPNstack.pop()
# 				op2=RPNstack.pop()
# 				unitops.pop()
# 				RPNstack.append(or_(op1,op2))
# 	if len(RPNstack)>1:    # RPNstack should contain at most one Boolean search term at the end of the evaluation of a valid Boolean expression
# 		mssg.setText("ERROR! too many operations for number of operands. Erroneous Boolean expression")
# 		mssg.exec_()
# 		del mssg
# 		return          # return user so they can fix Boolean expression
# 	#### send Boolean expression, now in SQLACHEMY-compatible form, to be executed via the database
# 	if len(RPNstack)==1:
# 		query=select([self.table]).where(RPNstack[0])           # prepare database query via SQLACHEMY
# 		#self.dBQuerySignal.emit(query)                          # execute database query and send results to query table
# 		self.parent().setQuery(query)
# 	del mssg
# 	return
# 	###############################################################################################################
############################################################################################################################################################################
# test to check if a string is a valid number
def is_number(number=None):
	isnumber=True
	if number==None or number=="": return False
	try: float(number)
	except: isnumber=False
	return isnumber
############################################################################################################################################################
########################################################################################################################
# population statistics
# this method obtains the top n% (user-specified) of the data and returns the mean or geometric mean and std deviations
# top_fraction is the top fraction of devices to pick
# bottom_fraction is the bottom fraction of devices to pick
# absolutevalue=True - statistics and sorting based on absolute value
# top_fraction and bottom_fraction cannot be simultaneously specified as this will throw an error

def devstat(logstat=False,data=None,top_fraction=None,bottom_fraction=None,absolutevalue=True):
	if data==None or len(data)<1: raise ValueError("ERROR! Must specify at least one data point")
	if (top_fraction==None and bottom_fraction==None) or (top_fraction!=None and bottom_fraction!=None): raise ValueError("ERROR! must specify either toppercent or bottomepercent but not both")
	if top_fraction!=None:
		if top_fraction>=1.or top_fraction<=0.: raise ValueError("ERROR! top_fraction value not valid")
		topN=round(top_fraction*len(data))
		if absolutevalue==True: sdata=sorted(np.abs(data))[topN:]		# first sort data
		else: sdata=sorted(data)[topN:]		# first sort data
		limitvalue=[topN]
	else:
		if bottom_fraction>=1.or bottom_fraction<=0.: raise ValueError("ERROR! bottom_fraction value not valid")
		botN=round(bottom_fraction*len(data))
		if absolutevalue==True: sdata=sorted(np.abs(data))[:botN]		# first sort data
		else: sdata=sorted(data)[:botN]		# first sort data
		limitvalue=sdata[botN]				# get the upper limit of the data values
	# now get statistics
	if logstat:
		avg=st.mstats.gmean(sdata)
		std_dev=avg*np.std(sdata)
	else:
		avg=np.average(sdata)
		std_dev=np.std(sdata)
	return{'N':len(sdata),'std_dev':std_dev,'avg':avg,'limitvalue':limitvalue}

		# first sort data

###########################################################################################################################################################
# This series of functions write data to clipboard
#
# ###########################################################################################################################################################
# # class to view data (Future expansion)
# class FileView(Ui_FileView,QtWidgets.QDialog):
# 	def __int__(self,devicename=None,measurementtype=None,headerlabels=None,parent=None):
# 		super(FileView,self).__init__(parent)
# 		self.setupUi(self)
# 		self.
# ###############################################################################
# # subclass of item to enable custom sorting i.e. numeric
# # http://stackoverflow.com/questions/2304199/how-to-sort-a-qtablewidget-with-my-own-code
# class sItem(QtWidgets.QTableWidgetItem):
# 	#def __init__(self,data=None):
# 	#	QtWidgets.QTableWidgetItem.__init__(self,data)
# 	#	self.data=data
# 	def __lt__(self, other):
# 		#print(float(self.text()))
# 		#print(float(other.text()))
# 		#return float(str(self.data)) < float(str(other.text()))
# 		if is_number(self.text()) and not is_number(other.text()): return False
# 		if is_number(other.text()) and not is_number(self.text()): return True
# 		if is_number(self.text()) and is_number(other.text()):
# 			#print(float(self.text()),float(other.text()))
# 			return float(self.text())<float(other.text())
# 		return False
##########################################################################################################################################
################################################################################################################################################################
# Write a single device's data image to the clipboard. Works for all graphs
# pathname is the path to the wafer-level data
# called from actions_plot_widget.py
def image_to_clipboard(canvas=None):
	clipb=QtWidgets.QApplication.clipboard()
	if canvas!=None:						# do we have this data?
		#imagemap=QtGui.QPixmap.grabWidget(canvas)
		imagemap=Qt.QWidget.grab(canvas)
		clipb.setPixmap(imagemap)
		#print(" from line 450 utilities.py image_to_clipboard", len(imagemap))
		# imagesize=canvas.size()
		# w,h=imagesize.width(),imagesize.height()
		# im=QtWidgets.QImage(canvas.buffer_rgba(),w,h,QtWidgets.QImage.Format_ARGB32)
		# clipb.setImage(im)
	else:
		m=QtWidgets.QMessageBox()
		m.setText("No single-swept transfer curve (or Id(Vgs) data exist with the selected parameters.")
		m.exec_()
	#del clipb
	return
################################################################################################################################################################
###########################################################################################################################################################
# Write a single device's Yf to the clipboard
# pathname is the path to the wafer-level data
# called from actions_plot_widget.py
def Yf_text_to_clipboard(cd=None):
	clipb=QtWidgets.QApplication.clipboard()							# set up clipboard
	clipb.setText("")												# first clear clipboard
	clipbdata=""
	# dirname="".join([dirname,"/exported"])
	# if not os.path.exists(dirname):
	# 	os.makedirs(dirname)
	# filename = "".join([dirname+"/",cd.get_wafername(),"_",cd.get_devicename,"_Yf_T.xls"])			# form full file name
	# fwdat=open(filename,'w')

	if hasattr(cd,'Yf_t') and not (cd.Yf_T()=='None' or cd.Yf_T()==None) and len(cd.Yf_T()['Y'])>0:						# do we have this data?
		# set up file headers
		clipbdata="".join([clipbdata,'# Data from Id(Vgs) single-swept transfer curve\n'])
		clipbdata="".join([clipbdata,'# Y-function and Y-function linear fit\n'])
		clipbdata="".join([clipbdata,'# Vds=\t',formatnum(cd.Yf_T()['Vds'],precision=2),'\n'])
		clipbdata="".join([clipbdata,'# device name\t',cd.get_devicename(),'\t','X(um)=\t',formatnum(cd.x()),'\tY(um)=\t',formatnum(cd.y()),'\n#\n'])
		#clipbdata="".join([clipbdata,'# Vgs(V)\tYf_T\tYf linear fit\tgate status\tdrain status\n'])
		clipbdata="".join([clipbdata,'# Vgs(V)\tYf_T\tgate status\tdrain status\n'])
		# data
		for iVgs in range(len(cd.Yf_T()['Vgs'])):
			#clipbdata="".join([clipbdata,formatnum(cd.Yf_T()['Vgs'][iVgs],precision=2),'\t',formatnum(cd.Yf_T()['Y'][iVgs],precision=2),'\t',formatnum(cd.Yflin_T()['Y'][iVgs],precision=2),'\t',cd.Yf_T()['gatestatus'][iVgs],'\t',cd.Yf_T()['drainstatus'][iVgs],'\n'])
			clipbdata="".join([clipbdata,formatnum(cd.Yf_T()['Vgs'][iVgs],precision=2),'\t',formatnum(cd.Yf_T()['Y'][iVgs],precision=2),'\t',cd.Yf_T()['gatestatus'][iVgs],'\t',cd.Yf_T()['drainstatus'][iVgs],'\n'])
		#print("from utilities.py line 414  ",clipbdata)		#debug
		clipb.setText(clipbdata)			# send text data to clipboard
	else:
		m=QtWidgets.QMessageBox()
		m.setText("No Y function data exist with the selected parameters.")
		m.exec_()
	del clipb
	return
################################################################################################################################################################
###########################################################################################################################################################
# Write a single device's Id(Vgs) single-swept transfer curve text to the clipboard
# pathname is the path to the wafer-level data
# called from actions_plot_widget.py
def Id_text_single_swept_transfer_to_clipboard(cd=None):
	clipb=QtWidgets.QApplication.clipboard()
	# clipb=a.clipboard()							# set up clipboard
	clipb.setText("")												# first clear clipboard
	clipbdata=""
	#if hasattr(cd,'Id_IVt') and not (cd.Id_T()=='None' or cd.Id_T()==None) and len(cd.Id_IVt)>0:						# do we have this data?
	if hasattr(cd,'Id_IVt') and len(cd.Id_T())>0 and len(cd.Id_IVt)>0:						# do we have this data?
		# set up file headers
		clipbdata="".join([clipbdata,'# Data from Id(Vgs) single-swept transfer curve\n'])
		clipbdata="".join([clipbdata,'# Id(Vgs)\n'])
		clipbdata="".join([clipbdata,'# Vds=\t',formatnum(cd.Vds_IVt,precision=2),'\n'])
		clipbdata="".join([clipbdata,'# device name\t',cd.get_devicename(),'\t','X(um)=\t',formatnum(cd.x()),'\tY(um)=\t',formatnum(cd.y()),'\n#\n'])
		clipbdata="".join([clipbdata,'# Vgs(V)\tmeasured Id(Vgs) (A)\tgate status\tdrain status\n'])
		# data
		for iVgs in range(len(cd.Id_T())):
			clipbdata="".join([clipbdata,formatnum(cd.Vgs_IVt[iVgs],precision=2),'\t',formatnum(cd.Id_IVt[iVgs],precision=2),'\t',cd.gatestatus_IVt[iVgs],'\t',cd.drainstatus_IVt[iVgs],'\n'])
		clipb.setText(clipbdata)			# send text data to clipboard
		# now add spline fit Id(Vgs) data
		clipbdata="".join([clipbdata,'#\n#\n# Vgs(V)\tspline fit Id(Vgs) (A)\n'])
		for iVgs in range(len(cd.Id_T())):
			clipbdata="".join([clipbdata,formatnum(cd.Idfit_T()['Vgs'][iVgs],precision=2),'\t',formatnum(cd.Idfit_T()['I'][iVgs],precision=2),'\t',cd.gatestatus_IVt[iVgs],'\t',cd.drainstatus_IVt[iVgs],'\n'])
		clipb.setText(clipbdata)			# send text data to clipboard
	else:
		m=QtWidgets.QMessageBox()
		m.setText("No single-swept transfer curve (or Id(Vgs) data exist with the selected parameters.")
		m.exec_()
	del clipb
	return

###########################################################################################################################################################
# Write a single device's Id(Vgs) double-swept transfer curve to the clipboard
# pathname is the path to the wafer-level data
# called from actions_plot_widget.py
def Id_text_double_swept_transfer_to_clipboard(cd=None):
	clipb=QtWidgets.QApplication.clipboard()
	# clipb=a.clipboard()							# set up clipboard
	clipb.setText("")												# first clear clipboard
	#clipb.clear()
	clipbdata=""
	if len(cd.Id_TF())>0 and len(cd.Id_TR())>0:						# do we have this data?
		# set up file headers
		clipbdata="".join([clipbdata,'# Data from Id(Vgs) double-swept transfer curve\n'])
		clipbdata="".join([clipbdata,'# Id(Vgs)\n'])
		clipbdata="".join([clipbdata,'# Vds=\t',formatnum(cd.Vds_IVtfr,precision=2),'\n'])
		clipbdata="".join([clipbdata,'# device name\t',cd.get_devicename(),'\t','X(um)=\t',formatnum(cd.x()),'\tY(um)=\t',formatnum(cd.y()),'\n#\n'])

		# 1st-swept raw measured Id
		clipbdata="".join([clipbdata,'# 1st-swept transfer curve\n'])
		clipbdata="".join([clipbdata,'# Vgs(V)\tId(Vgs)\tgate status\tdrain status\n'])
		for iVgs in range(len(cd.Id_IVtf)): clipbdata="".join([clipbdata,formatnum(cd.Vgs_IVtf[iVgs],precision=2),'\t',formatnum(cd.Id_IVtf[iVgs],precision=2),'\t',cd.gatestatus_IVtf[iVgs],'\t',cd.drainstatus_IVtf[iVgs],'\n'])
		# 1st-swept spline fit Id - Note that the spline fit Id - Idspline, can have a different number of points than the raw data due to the necessity of removing Vgs points which are non-monotonic and which would not lend well to a spline fit
		clipbdata = "".join([clipbdata, '# Vgs(V)\tspline fit Id(Vgs)\n'])
		for iVgs in range(len(cd.Idfit_TF()['I'])): clipbdata="".join([clipbdata,formatnum(cd.Idfit_TF()['Vgs'][iVgs],precision=2),'\t',formatnum(cd.Idfit_TF()['I'][iVgs],precision=2),'\n'])

		# 2nd-swept raw measured Id
		clipbdata="".join([clipbdata,'# 2nd-swept transfer curve\n'])
		clipbdata="".join([clipbdata,'# Vgs(V)\tId(Vgs)\tspline fit Id(Vgs)\tgate status\tdrain status\n'])
		for iVgs in range(len(cd.Id_IVtr)): clipbdata="".join([clipbdata,formatnum(cd.Vgs_IVtr[iVgs],precision=2),'\t',formatnum(cd.Id_IVtr[iVgs],precision=2),'\t',cd.gatestatus_IVtr[iVgs],'\t',cd.drainstatus_IVtr[iVgs],'\n'])
		# 2nd-swept spline fit Id - Note that the spline fit Id - Idspline, can have a different number of points than the raw data due to the necessity of removing Vgs points which are non-monotonic and which would not lend well to a spline fit
		clipbdata = "".join([clipbdata, '# Vgs(V)\tspline fit Id(Vgs)\n'])
		for iVgs in range(len(cd.Idfit_TR()['I'])): clipbdata = "".join([clipbdata, formatnum(cd.Idfit_TR()['Vgs'][iVgs], precision=2), '\t',formatnum(cd.Idfit_TR()['I'][iVgs], precision=2), '\n'])

	# 3rd-swept raw measured Id
	if len(cd.Id_T3())>0 and len(cd.Id_T4())>0:
		clipbdata = "".join([clipbdata, '# 3rd-swept transfer curve\n'])
		clipbdata = "".join([clipbdata, '# Vgs(V)\tId(Vgs)\tspline fit Id(Vgs)\tgate status\tdrain status\n'])
		for iVgs in range(len(cd.Id_IVt3)): clipbdata = "".join([clipbdata, formatnum(cd.Vgs_IVt3[iVgs], precision=2), '\t', formatnum(cd.Id_IVt3[iVgs], precision=2), '\t', cd.gatestatus_IVt3[iVgs], '\t', cd.drainstatus_IVt3[iVgs], '\n'])
		# 3rd-swept spline fit Id - Note that the spline fit Id - Idspline, can have a different number of points than the raw data due to the necessity of removing Vgs points which are non-monotonic and which would not lend well to a spline fit
		clipbdata = "".join([clipbdata, '# Vgs(V)\tspline fit Id(Vgs)\n'])
		for iVgs in range(len(cd.Idfit_T3()['I'])): clipbdata = "".join([clipbdata, formatnum(cd.Idfit_T3()['Vgs'][iVgs], precision=2), '\t', formatnum(cd.Idfit_T3()['I'][iVgs], precision=2), '\n'])

		# 4th-swept raw measured Id
		clipbdata = "".join([clipbdata, '# 4th-swept transfer curve\n'])
		clipbdata = "".join([clipbdata, '# Vgs(V)\tId(Vgs)\tspline fit Id(Vgs)\tgate status\tdrain status\n'])
		for iVgs in range(len(cd.Id_IVt4)): clipbdata = "".join([clipbdata, formatnum(cd.Vgs_IVt4[iVgs], precision=2), '\t', formatnum(cd.Id_IVt4[iVgs], precision=2), '\t', cd.gatestatus_IVt4[iVgs], '\t', cd.drainstatus_IVt4[iVgs], '\n'])
		# 4th-swept spline fit Id - Note that the spline fit Id - Idspline, can have a different number of points than the raw data due to the necessity of removing Vgs points which are non-monotonic and which would not lend well to a spline fit
		clipbdata = "".join([clipbdata, '# Vgs(V)\tspline fit Id(Vgs)\n'])
		for iVgs in range(len(cd.Idfit_T4()['I'])): clipbdata = "".join([clipbdata, formatnum(cd.Idfit_T4()['Vgs'][iVgs], precision=2), '\t', formatnum(cd.Idfit_T4()['I'][iVgs], precision=2), '\n'])


	if len(cd.Id_TF())==0 and len(cd.Id_TR())==0 and len(cd.Id_T3())==0 and len(cd.Id_T4())==0:
			m=QtWidgets.QMessageBox()
			m.setText("No double-swept transfer curve (or Id(Vgs) data exist with the selected parameters.")
			m.exec_()
	else: clipb.setText(clipbdata)			# send text data to clipboard
	#print("from line 586 utilities.py clipboard = ",clipb.text())
	del clipb
	return
################################################################################################################################################################
###########################################################################################################################################################
# Write a single device's gm(Vgs) single-swept transfer curve to the clipboard
# pathname is the path to the wafer-level data
# called from actions_plot_widget.py
def gm_single_swept_transfer_text_to_clipboard(cd=None):
	clipb=QtWidgets.QApplication.clipboard()
	# clipb=a.clipboard()							# set up clipboard
	clipb.setText("")												# first clear clipboard
	clipbdata=""
	if hasattr(cd,'gm_t') and not (cd.gm_T()=='None' or cd.gm_T()==None) and len(cd.gm_t)>0:						# do we have this data?
		# set up file headers
		clipbdata="".join([clipbdata,'# Data from curve fit of Id(Vgs) single-swept transfer curve\n'])
		clipbdata="".join([clipbdata,'# transconductance vs Vgs\n'])
		clipbdata="".join([clipbdata,'# Vds=\t',formatnum(cd.Vds_IVt,precision=2),'\n'])
		clipbdata="".join([clipbdata,'# device name\t',cd.get_devicename(),'\t','X(um)=\t',formatnum(cd.x()),'\tY(um)=\t',formatnum(cd.y()),'\n#\n'])
		clipbdata="".join([clipbdata,'# Vgs(V)\tgm(Vgs)\tgate status\tdrain status\n'])
		# data
		for iVgs in range(len(cd.gm_T()['Vgs'])):
			clipbdata="".join([clipbdata,formatnum(cd.gm_T()['Vgs'][iVgs],precision=2),'\t',formatnum(cd.gm_T()['G'][iVgs],precision=2),'\t',cd.gatestatus_IVt[iVgs],'\t',cd.drainstatus_IVt[iVgs],'\n'])
		clipb.setText(clipbdata)			# send text data to clipboard
	else:
		m=QtWidgets.QMessageBox()
		m.setText("No single-swept transfer curve (or Id(Vgs) data exist with the selected parameters.")
		m.exec_()
	del clipb
	return
################################################################################################################################################################
###########################################################################################################################################################
# Write a single device's gm(Vgs) 1st and 2nd sweeps of multi-swept transfer curve to the clipboard
# pathname is the path to the wafer-level data
# called from actions_plot_widget.py
def gm_dual_swept_transfer_text_to_clipboard(cd=None):
	clipb=QtWidgets.QApplication.clipboard()
	# clipb=a.clipboard()							# set up clipboard
	clipb.setText("")												# first clear clipboard
	clipbdata=""
	if hasattr(cd,'gm_tf') and not (cd.gm_TF()=='None' or cd.gm_TF()==None) and len(cd.gm_tf)>0:						# do we have this data?
		# set up file headers
		clipbdata="".join([clipbdata,'# Data from curve fit of Id(Vgs) 1st and 2nd sweeps of the transfer curve\n'])
		clipbdata="".join([clipbdata,'# transconductance vs Vgs\n'])
		clipbdata="".join([clipbdata,'# Vds=\t',formatnum(cd.Vds_IVtfr,precision=2),'\n'])
		clipbdata="".join([clipbdata,'# device name\t',cd.get_devicename(),'\t','X(um)=\t',formatnum(cd.x()),'\tY(um)=\t',formatnum(cd.y()),'\n#\n'])

		clipbdata="".join([clipbdata,'# 1st-swept transfer curve\n'])
		clipbdata="".join([clipbdata,'# Vgs(V)\tgm(Vgs)\tgate status\tdrain status\n'])
		# data
		# from first-swept Id transfer curve
		for iVgs in range(len(cd.gm_TF()['Vgs'])):
			clipbdata="".join([clipbdata,formatnum(cd.gm_TF()['Vgs'][iVgs],precision=2),'\t',formatnum(cd.gm_TF()['G'][iVgs],precision=2),'\t',cd.gatestatus_IVtf[iVgs],'\t',cd.drainstatus_IVtf[iVgs],'\n'])

		# from 2nd-swept Id transfer curve
		clipbdata="".join([clipbdata,'# 2nd-swept transfer curve\n'])
		clipbdata="".join([clipbdata,'# Vgs(V)\tgm(Vgs)\tgate status\tdrain status\n'])
		for iVgs in range(len(cd.gm_TR()['Vgs'])):
			clipbdata="".join([clipbdata,formatnum(cd.gm_TR()['Vgs'][iVgs],precision=2),'\t',formatnum(cd.gm_TR()['G'][iVgs],precision=2),'\t',cd.gatestatus_IVtr[iVgs],'\t',cd.drainstatus_IVtr[iVgs],'\n'])

		clipb.setText(clipbdata)			# send text data to clipboard
	else:
		m=QtWidgets.QMessageBox()
		m.setText("No single-swept transfer curve (or Id(Vgs) data exist with the selected parameters.")
		m.exec_()
	del clipb
	return
################################################################################################################################################################
###########################################################################################################################################################
# Write a single device's H21 dB curve (from S-parameter data) to the clipboard
# pathname is the path to the wafer-level data
# called from actions_plot_widget.py
def H21_text_to_clipboard(cd=None):
	clipb=QtWidgets.QApplication.clipboard()
	# clipb=a.clipboard()							# set up clipboard
	clipb.setText("")												# first clear clipboard
	clipbdata=""
	if hasattr(cd,'h21_DB') and len(cd.h21_DB)>0:						# do we have this data?
		# set up file headers
		clipbdata="".join([clipbdata,'# Data from S-parameters\n'])
		clipbdata="".join([clipbdata,'# Vds=\t',formatnum(cd.Vds_Spar(),precision=2),'\tId(A)=\t',formatnum(cd.Id_Spar(),precision=2),'\tVgs=\t',formatnum(cd.Vgs_Spar(),precision=2),'\tIg(A)=\t',formatnum(cd.Ig_Spar(),precision=2),'\n'])
		clipbdata="".join([clipbdata,'# gate status\t',cd.gatestatus_Spar(),'\tdrain status\t',cd.drainstatus_Spar(),'\n'])
		clipbdata="".join([clipbdata,'# ft=\t',formatnum(1.E-9*cd.ft(),precision=2),'\tGHz\n'])
		clipbdata="".join([clipbdata,'# device name\t',cd.get_devicename(),'\t','X(um)=\t',formatnum(cd.x()),'\tY(um)=\t',formatnum(cd.y()),'\n#\n'])
		clipbdata="".join([clipbdata,'# Frequency GHz\tH21(dB)\n'])
		# data
		for ii in range(len(cd.h21_DB)):
			clipbdata="".join([clipbdata,formatnum(1.E-9*cd.sfrequencies()[ii],precision=2),'\t',formatnum(cd.h21_DB[ii].real,precision=2),'\n'])
		clipb.setText(clipbdata)			# send text data to clipboard
	else:
		m=QtWidgets.QMessageBox()
		m.setText("No H-parameter data exist with the selected parameters.")
		m.exec_()
	del clipb
	return
################################################################################################################################################################
###########################################################################################################################################################
# Write a single device's Sparameter dB data (from S-parameter data) to the clipboard
# pathname is the path to the wafer-level data
# called from actions_plot_widget.py
def twopportparameters_dB_text_to_clipboard(cd=None):
	clipb=QtWidgets.QApplication.clipboard()
	# clipb=a.clipboard()							# set up clipboard
	clipb.setText("")												# first clear clipboard
	clipbdata=""
	if not hasattr(cd, 's11_DB') or not len(cd.s11_DB) > 0:  					# do we have this data? If not then try to read and/or calculate
		cd.Spar(type="s11db")
	if hasattr(cd,'s11_DB') and len(cd.s11_DB)>0:						# do we have this data?
		# set up file headers
		clipbdata="".join([clipbdata,'# Data from S-parameters\n'])
		clipbdata="".join([clipbdata,'# Vds=\t',formatnum(cd.Vds_Spar(),precision=2),'\tId(A)=\t',formatnum(cd.Id_Spar(),precision=2),'\tVgs=\t',formatnum(cd.Vgs_Spar(),precision=2),'\tIg(A)=\t',formatnum(cd.Ig_Spar(),precision=2),'\n'])
		clipbdata="".join([clipbdata,'# gate status\t',cd.gatestatus_Spar(),'\tdrain status\t',cd.drainstatus_Spar(),'\n'])
		clipbdata="".join([clipbdata,'# ft=\t',formatnum(1.E-9*cd.ft(),precision=2),'\tGHz\n'])
		clipbdata="".join([clipbdata,'# device name\t',cd.get_devicename(),'\t','X(um)=\t',formatnum(cd.x()),'\tY(um)=\t',formatnum(cd.y()),'\n#\n'])
		clipbdata="".join([clipbdata,'# Frequency GHz\tS11(dB)\tS11 angle deg\tS21(dB)\tS21 angle deg\tS12(dB)\tS12 angle deg\tS22(dB)\tS22 angle deg\tgate status\tdrain status\n'])
		# data
		for ii in range(len(cd.s11_DB)):
			clipbdata="".join([clipbdata,formatnum(1.E-9*cd.sfrequencies()[ii],precision=2),'\t',
							   formatnum(np.real(cd.Spar('s11db')[ii]),precision=2),'\t',formatnum(np.imag(cd.Spar('s11db')[ii]),precision=2),'\t',
							   formatnum(np.real(cd.Spar('s21db')[ii]),precision=2),'\t',formatnum(np.imag(cd.Spar('s21db')[ii]), precision=2), '\t',
							   formatnum(np.real(cd.Spar('s12db')[ii]),precision=2),'\t',formatnum(np.imag(cd.Spar('s12db')[ii]), precision=2), '\t',
							   formatnum(np.real(cd.Spar('s22db')[ii]),precision=2),'\t',formatnum(np.imag(cd.Spar('s22db')[ii]), precision=2), '\n'])
		clipb.setText(clipbdata)			# send text data to clipboard
	else:
		m=QtWidgets.QMessageBox()
		m.setText("No S-parameter data exist with the selected parameters.")
		m.exec_()
	del clipb
	return
################################################################################################################################################################
###########################################################################################################################################################
# Write a single device's Gmax dB curve (from S-parameter data) to the clipboard
# pathname is the path to the wafer-level data
# called from actions_plot_widget.py
def Gmax_text_to_clipboard(cd=None):
	clipb=QtWidgets.QApplication.clipboard()
	# clipb=a.clipboard()							# set up clipboard
	clipb.setText("")												# first clear clipboard
	clipbdata=""
	if hasattr(cd,'GMAX_DB') and len(cd.GMAX_DB)>0:						# do we have this data?
		# set up file headers
		clipbdata="".join([clipbdata,'# Data from S-parameters\n'])
		clipbdata="".join([clipbdata,'# Vds=\t',formatnum(cd.Vds_Spar(),precision=2),'\tId(A)=\t',formatnum(cd.Id_Spar(),precision=2),'\tVgs=\t',formatnum(cd.Vgs_Spar(),precision=2),'\tIg(A)=\t',formatnum(cd.Ig_Spar(),precision=2),'\n'])
		clipbdata="".join([clipbdata,'# gate status\t',cd.gatestatus_Spar(),'\tdrain status\t',cd.drainstatus_Spar(),'\n'])
		if is_number(cd.ft()): clipbdata="".join([clipbdata,'# ft=\t',formatnum(1.E-9*cd.ft(),precision=2),'\tGHz\t'])
		if is_number(cd.fmax()): clipbdata="".join([clipbdata,'fmax=\t',formatnum(1.E-9*cd.fmax(),precision=2),'\tGHz'])
		clipbdata="".join([clipbdata,'\n'])
		clipbdata="".join([clipbdata,'# device name\t',cd.get_devicename(),'\t','X(um)=\t',formatnum(cd.x()),'\tY(um)=\t',formatnum(cd.y()),'\n#\n'])
		clipbdata="".join([clipbdata,'# Frequency GHz\tGMAX(dB)\tstability factor\n'])
		# data
		for ii in range(len(cd.h21_DB)):
			clipbdata="".join([clipbdata,formatnum(1.E-9*cd.sfrequencies()[ii],precision=2),'\t',formatnum(cd.GMAX_DB[ii],precision=2),'\t',formatnum(cd.Kfactor[ii],precision=2),'\n'])
		clipb.setText(clipbdata)			# send text data to clipboard
	else:
		m=QtWidgets.QMessageBox()
		m.setText("No Gmax data exist with the selected parameters.")
		m.exec_()
	del clipb
	return
###########################################################################################################################################################
# Write a single device's Gmax dB curve (from S-parameter data) to the clipboard
# pathname is the path to the wafer-level data
# called from actions_plot_widget.py
def Umax_text_to_clipboard(cd=None):
	clipb=QtWidgets.QApplication.clipboard()
	# clipb=a.clipboard()							# set up clipboard
	clipb.setText("")												# first clear clipboard
	clipbdata=""
	if hasattr(cd,'UMAX_DB') and len(cd.UMAX_DB)>0:						# do we have this data?
		# set up file headers
		clipbdata="".join([clipbdata,'# Data from S-parameters\n'])
		clipbdata="".join([clipbdata,'# Vds=\t',formatnum(cd.Vds_Spar(),precision=2),'\tId(A)=\t',formatnum(cd.Id_Spar(),precision=2),'\tVgs=\t',formatnum(cd.Vgs_Spar(),precision=2),'\tIg(A)=\t',formatnum(cd.Ig_Spar(),precision=2),'\n'])
		clipbdata="".join([clipbdata,'# gate status\t',cd.gatestatus_Spar(),'\tdrain status\t',cd.drainstatus_Spar(),'\n'])
		if cd.ft()!=None and cd.fmax()!=None:			# sometimes bad data causes errors, Skip recording bad data
			clipbdata="".join([clipbdata,'# ft=\t',formatnum(1.E-9*cd.ft(),precision=2),'\tGHz\tfmax=\t',formatnum(1.E-9*cd.fmax(),precision=2),'\tGHz\n'])
		else:
			clipbdata = "".join([clipbdata, '# ft=\t', "NO valid ft DATA", '\tGHz\tfmax=\t', "NO valid fmax DATA\n"])
		clipbdata="".join([clipbdata,'# device name\t',cd.get_devicename(),'\t','X(um)=\t',formatnum(cd.x()),'\tY(um)=\t',formatnum(cd.y()),'\n#\n'])
		clipbdata="".join([clipbdata,'# Frequency GHz\tUMAX(dB)\n'])
		# data
		for ii in range(len(cd.h21_DB)):
			clipbdata="".join([clipbdata,formatnum(1.E-9*cd.sfrequencies()[ii],precision=2),'\t',formatnum(cd.UMAX_DB[ii],precision=2),'\n'])
		clipb.setText(clipbdata)			# send text data to clipboard
	else:
		m=QtWidgets.QMessageBox()
		m.setText("No UMAX data exist with the selected parameters.")
		m.exec_()
	del clipb
	return
################################################################################################################################################################
###########################################################################################################################################################
# Write a single device's TLM Ron vs TLM length to the clipboard
# called from actions_plot_widget.py
def TLM_text_to_clipboard(cd=None):
	clipb=QtWidgets.QApplication.clipboard()
	clipb.setText("")												# first clear clipboard
	clipbdata=""
	if cd.Rc_TLM!=None:						# do we have this data?
		# find linear fit line to TLM data
		m=cd.Rsh_TLM
		b=2.*cd.Rc_TLM
		TLMfitlen=np.linspace(0.,1.1*max(cd.TLMlengths),5)
		TLMfitRon=[m*x+b for x in TLMfitlen]
		# set up file headers
		clipbdata="".join([clipbdata,'# Data from TLM curves derived from the family of curves\n'])
		clipbdata="".join([clipbdata,'# Vgs=\t',formatnum(cd.TLM_Vgs,precision=2),'\tfraction Vds fit for Ron\t',formatnum(cd.fractVdsfit_Ronfoc,precision=2),'\n'])
		clipbdata="".join([clipbdata,'# Number of not-normal measurement points (compliance or otherwise) for entire TLM measurement\t',formatnum(cd.noptsincompliance_TLM,type='int'),'\n'])
		clipbdata="".join([clipbdata,'# Contact Resistance (ohms)\t',formatnum(cd.Rc_TLM,precision=2),'\tSheet resistance (ohms)\t',formatnum(cd.Rsh_TLM,precision=2),'\n'])
		clipbdata="".join([clipbdata,'# Linear fit figure of merit\t',formatnum(cd.fit_TLM,precision=2),'\n'])
		clipbdata="".join([clipbdata,'# Minimum TLM length for linear fit\t',formatnum(cd.TLM_min_fitlength,precision=1),'\tMaximum TLM length for linear fit\t',formatnum(cd.TLM_max_fitlength,precision=1),'\n'])
		clipbdata="".join([clipbdata,'# device name\t',cd.get_devicename(),'\t','X(um)=\t',formatnum(cd.x()),'\tY(um)=\t',formatnum(cd.y()),'\n#\n'])
		clipbdata="".join([clipbdata,'# TLM length um\tMeasured TLM Ron\n'])
		# measured data
		for ii in range(len(cd.TLM_Ron)): clipbdata="".join([clipbdata,formatnum(cd.TLMlengths[ii],precision=3),'\t',formatnum(cd.TLM_Ron[ii],precision=2),'\n'])
		# least squares linear fit data calculation
		clipbdata="".join([clipbdata,'\n# TLM length um\tLinear Fit TLM Ron\n'])
		for ii in range(len(TLMfitlen)): clipbdata="".join([clipbdata,formatnum(TLMfitlen[ii],precision=3),'\t',formatnum(TLMfitRon[ii],precision=2),'\n'])

		clipb.setText(clipbdata)			# send text data to clipboard
	else:
		m=QtWidgets.QMessageBox()
		m.setText("No TLM data exist with the selected parameters.")
		m.exec_()
	del clipb
	return
################################################################################################################################################################
################################################################################################################################################################
# this returns True if the floating point arguments differ by <= reltol
# to compare floating point numbers
# good to 1E-20
def floatequal(fl1,fl2,reltol):
	if fl1==None or fl2==None: return False
	if abs(fl1+fl2)<=1E-20: return True
	if abs((fl1-fl2)/(fl1+fl2))<reltol: return True
	else: return False
################################################################################################################################################################
################################################################################################################################################################
# this reads and returns the device geometries
# gatewidth and tlmlength are dictionaries which have keys which are the level 0 device name subtype and values of the total gatewidth and TLM length in um respectively
def geometry(waferdirectory=None):
	if waferdirectory==None: raise ValueError("ERROR! did not give a wafer directory name")
	#print("from utilities.py line 616 waferdirectory", waferdirectory)
	geometryfile = "".join([waferdirectory,sub('GEOMETRY'),'/geometry.csv'])
	try: fgeo=open(geometryfile,'r')
	except: return None
	tlmlength={}
	gatewidth={}
	orthmate={}
	leadreasistance={}					# device lead (access) resistance in ohms due to traces leading to the device
	geofilelines=[l for l in fgeo.read().splitlines()]
	for geoline in geofilelines:
		if not '#' in geoline:				# eliminate comments
			if 'TLMlength' in geoline:			# then expect a name and TLM length dimension in this line
				if is_number(geoline.split()[geoline.split().index('TLMlength')+1].strip()) and float(geoline.split()[geoline.split().index('TLMlength')+1].strip())>0:				# add only positive TLM lengths
					#tlmlength[geoline.split()[0].strip()]=float(geoline.split()[geoline.split().index('TLMlength')+1].strip())
					tlmlength[geoline.split('\t')[0].strip()]=float(geoline.split()[geoline.split().index('TLMlength')+1].strip())
			if 'width' in geoline:
				gatewidth[geoline.split()[0].strip()]=float(geoline.split()[geoline.split().index('width')+1].strip())
			if 'orthdevice' in geoline:			# specify mates of orthogonal devices
				orthmate[geoline.split()[geoline.split().index('orthdevice')+1].strip()]=geoline.split()[geoline.split().index('ORTHmate')+1].strip()			# get mate of orthogonal device
			if 'leadresistance' in geoline:
				try: leadreasistance[geoline.split()[0].strip()]=float(geoline.split()[geoline.split().index('leadresistance')+1].strip())
				except: pass							# device lead (access) resistance in ohms due to traces leading to the device
	fgeo.close()
	return {'gatewidth':gatewidth,'TLMlength':tlmlength,'ORTHmate':orthmate,'leadresistance':leadreasistance}
################################################################################################################################################################
# split up devices for multiprocessing
# returns several device lists depending on number of cores in machine = splitlists[CPUcoreindex][devicenamesindex]
def split_device_list(devicelist):
	devicelist=list(devicelist)
	nd=len(devicelist)
	nc=mp.cpu_count()					# find number of CPU cores = nc
	threadspercpu=float(len(devicelist))/float(nc)		# number of threads/cpu
	splitlists=[]				# array of device lists
	if nc==1:							# single CPU core so don't split list
		splitlists.append(devicelist)
		return splitlists
	if nc>nd: nc=nd								# reduce number of cores used, as necessary to ensure a minimum of one process per remaining core
	deltalist=int(nd/nc)
	splitlists=[devicelist[i:i+deltalist] for i in range(0,nd,deltalist)]	# split up list
	return splitlists
###############################################################################################################################################################
# convert dB power quantity to linear
def dBtolin(dB):
	return(np.power(10.,np.divide(dB,10.)))
# convert linear (power) to dB
def lintodB(lin):
	return(np.multiply(10.,np.log10(lin)))
# def testu(test=None):
# 	print("utilityimporttest working")

################################################################################
# sort list a with values from list b
def sortlist(tosort=None,sortfrom=None):
	sortout=[x for _, x in sorted(zip(sortfrom,tosort))]
	return sortout
################################################################################
# find index of number nearest to numbertofindindex within the list
def findnearest(list=None,numbertofindindex=None):
	indexofnearest=np.fabs(np.array(list)-numbertofindindex).argmin(axis=0)
	return indexofnearest

#####################################################################################################
#######################################################################################################################################################
#General utility functions

def smooth_spline_1d(x_data=None,y_data=None, pdeg=-1,s_factor = 1.0):            #takes 1D y array data sampled at x_data and smooths it using a smoothing spline.  #returns a UnivariateSpline object
	if x_data.any()==None: raise ValueError("ERROR! no value for x_data")
	if y_data.any()==None: raise ValueError("ERROR! no value for y_data")
	if pdeg==None: raise ValueError("ERROR! no value for pdeg")
	if s_factor==None: raise ValueError("ERROR! no value for s_factor")
   # """Inspired by Igor and by Phil Marsh's YFM programs,
   # y_data is a 1D array, such as I_D, x_data is the corresponding array of x_data points,
   # s_factor is the smoothing factor, normalized to the number of points in the data, should vary from about 0 to 1"""
#   This function doesn't currently have any error handling and expects well-formatted data
	if pdeg == -1:
#   Determine reasonable order of polynomial to fit, if the pdeg isn't specified:
		poly_a = np.linspace(7,20, num=14)
		for ind, degree in enumerate(poly_a):
			poly_a[ind] = np.polynomial.polynomial.Polynomial.fit(x_data, y_data, int(degree), full=True)[1][0][0]
		pdeg = (poly_a < 1.2*poly_a.min()).argmax()+7  #finds the ceiling index at which poly_a becomes less than 20% above its minimum value
#    print("the polynomical degree is ", pdeg)
#   least squares fit of a polynomial of degree norder to the data, in order to approximate the noise standard deviation
	chi_sq = np.polynomial.polynomial.Polynomial.fit(x_data, y_data, pdeg, full=True)[1][0][0] #This returns the sum of the residuals squared, aka chi squared
#  resid_sq will be on order of 10^-11, so 0.1*resid_Sq will be on order of 10^-12
	s_value = s_factor*chi_sq
#  3rd order smoothing spline interpolation to the data.
	spl_fit = UnivariateSpline(x_data,y_data,s=s_value)

#--------------old algorithm works well, but will create an extra array every time------------
#    numpnts = len(x_data)
#    noise_std = (chi_sq/(numpnts-1))**0.5 #gives a comparable number to the variance of the residuals wave used in Igor
#    weights = np.full_like(x_array, 1 / noise_std) #convert the noise STD to weights for the numpy class
#  s_value is normalized to the number of points. Note that this essentially cancels out the same factor in the weights.  I am not sure if this is good numerically or not.
#  Doing it like this, s_factor will be on order of 70, weights will be on order of 10^6, data is on order of 10^-9 to 10^-2
#  Otherwise s_factor is on order 10^-11, machine resolution is 10^-15
#    s_value = s_factor*numpnts
#  3rd order smoothing spline interpolation to the data.
#  spl_fit = UnivariateSpline(x_data,y_data,w=weights,s=s_value)
#------------------------------------------------------------------------------------------------
	return spl_fit
#######################################################################################################################################################
# ENR table cubic spline fit
# uses ENRtablefreqMHz ENR table dictionary from loadpull_system_calibration.py
# frequencyMHz is int or str and is the frequency in MHz
def ENRtablecubicspline(frequencyMHz=None):
	frequencyMHz=int(float(frequencyMHz))       # convert str to float then truncate to get integer frequency in MHz
	if frequencyMHz==None: raise ValueError("ERROR! no frequency in MHz given for ENR table interpolation")
	if frequencyMHz<10 or frequencyMHz>18000: raise ValueError("ERROR! frequency in MHz is out of range for ENR table interpolation")
	return ENRtable(frequencyMHz)                                               # cubic spline interpolated ENR in dB