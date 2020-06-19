__author__ = 'PMarsh Carbonics'
import os
import re
import numpy as np
from scipy import stats as st
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
def file_to_devicename(*args):
	if len(args)<1:
		raise ValueError("ERROR! must provide at least one input: a file listing and (optionally) substring(s) to delete")
	nlist =0							# Number of filelistings in parameter list should be = 1 or this is an error
	delstring = []						# list of strings to delete from filenames to produce devicenames size must be at least 1
	for ii in range(0,len(args)):
		if args[ii]=="filelisting":
			if len(args)<=ii+1:
				raise ValueError("ERROR! actual file listing must follow \"filelisting\" designator")
			inputdevlisting = args[ii+1]
			nlist += 1
			if nlist >1:
				raise ValueError("ERROR! Too many filelistings given!")
		if args[ii]=="delstr":			# a string to delete from the filename listings
			if len(args)<=ii+1:
				raise ValueError("ERROR! actual string-to-delete must follow \"delstr\" designator")
			elif args[ii+1]=="filelisting" or args[ii+1]=="delendstr":
				raise ValueError("ERROR! \"filelisting\" or \"delstr\" follows \"delendstr\" but is a keyword and CANNOT be used as a string to be deleted")
			delstring.append(args[ii+1])		# this is the string to delete from the filename

			#print delstring[-1]
		if args[ii]=="delendstr":			# delete from this string onward to end of filename string
			if len(args)<=ii+1:
				raise ValueError("ERROR! actual string-to-delete must follow \"delendstr\" designator")
			elif args[ii+1]=="filelisting" or args[ii+1]=="delstr":
				raise ValueError("ERROR! \"filelisting\" or \"delendstr\" follows \"delstr\" but is a keyword and CANNOT be used as a string to be deleted")
			delendstr = args[ii+1]		# truncate the filename starting with this string
			inputdevlisting = [f[:f.find(delendstr)] for f in inputdevlisting]
	for idel in range(0,len(delstring)):
		inputdevlisting = [f.replace(delstring[idel],'').strip() for f in inputdevlisting ] # remove substrings to be deleted from device listing
	# now remove duplicate devicenames
	dst = ""
	for id in range(0,len(inputdevlisting)):
		if inputdevlisting[id] not in dst:
			dst += inputdevlisting[id]+" "
	return [f.strip() for f in dst.split()]
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
def linfitminmax(x,y,fractrange,minmax):
	if (len(x)!=len(y)):
		raise ValueError("ERROR! number of points in the range is not equal to that of the domain")
	if len(x)<4:
		raise ValueError("ERROR! number of points must be > 3")
	deltanpts = int(fractrange*len(y))					# number of x points for the linear fit
	if deltanpts<2:
		raise ValueError("ERROR! fraction of range to perform linear fit is too small!")
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
		m,b,rval,pval,stderr = st.linregress(x[ii:ii+deltanpts],y[ii:ii+deltanpts])
	elif len(x)<=(ii+deltanpts):			# then the minimum point is near the end of the series
		m,b,rval,pval,stderr = st.linregress(x[ii-deltanpts:ii],y[ii-deltanpts:ii])
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
# defines subdirectory structure here, in one place, for all other classes and functions
# also defines portions of devicenames to search in the device name
# This function enables one to modify the naming conventions as desired in but a single place
def sub(subdir):
	if subdir == "DC":				# subdirectory containing the measured CD IV data
		return "/IV"
	elif subdir == "SPAR":			# subdirectory containing the S-parameter and other small-signal RF measured data
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
	elif subdir == "TLMlength":		# then return the designator used for the TLM length indicator which is part of the TLM's device name
		return "len_"
	elif subdir == "save":		# then return the designator used for the TLM length indicator which is part of the TLM's device name
		return "/SAVESTATE"
	else:

		raise ValueError("ERROR Unknown subdirectory  or designator specified")
###############################################################################################################################################################################
# finds linear average of parameters given in dB
def dBaverage(*args):
	dBavg = 10.*np.log10(np.average([pow(10.,l/10.) for l in args]))
	return dBavg
###############################################################################################################################################################################
# format numbers cleanly and return a string
def formatnum(number,precision=None,type=None):
	if type=='int':
		numstr=str(int(number))
	elif abs(number)<1.E-40:		# this is zero!
		numstr=str('{:5.1f}'.format(number))
	elif abs(number)>10000. or abs(number) < 0.1:
		if precision!=None:
			formatter = "{:5."+str(precision)+"E}"
			numstr=str(formatter.format(number))
		else:
			numstr=str('{:5.1E}'.format(number))	# default precision
	else:
		if precision!=None:
			formatter = "{:5."+str(precision)+"f}"
			numstr=str(formatter.format(number))
		else:
			numstr=str('{:5.1f}'.format(number))	# default precision
	return numstr
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
def parse_rpn(expression=None,targetfilename=None):
	expression=expression.replace(" ",",")								# replace all blanks with commas
	if expression==None:
		return True														# because no criteria was given - allow anything to pass
	while ",," in expression: expresion=expression.replace(",,",",")	# make sure only single commas are separating operators and strings
	if targetfilename==None: raise ValueError("ERROR! Must specify both expression and target data file name")
	# first convert expression into logical values and True False
	logicexpression = []		# the logical expression formed from the substrings and logic operators
	for val in expression.split(','):
		if val not in ['or', 'and', 'xor', 'not']:							# then this is NOT a logical operator but rather a substring in the target data filename
			logicexpression.append(val in targetfilename)					# append the logical result of the substring in target filename test
		else: logicexpression.append(val)									# else just append the logic operator

	stack = []
	for val in logicexpression:
		if val in ['or', 'and', 'xor']:			# binary operations
			op1 = stack.pop()
			op2 = stack.pop()
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
