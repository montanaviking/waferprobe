import os
from utilities import *
import collections as col
import re
# read S11
############################################################################################################################################################################
#	Outputs S parameters as complex numbers real and imaginary
# 	Frequency output is in Hz
# always reads the S-parameters when called
def convertS11tocap(pathname_spar=None):
	Z0=50.
	try: filelisting = os.listdir(pathname_spar)
	except:
		#print "ERROR directory", pathname_spar, "does not exist: returning from __readSpar() in device_parameter_request.py"
		return "NO DIRECTORY"
	nodevices=0

	for fileS in filelisting:
		try: fspar=open(os.path.join(pathname_spar,fileS),'r')
		except:
			print ("WARNING from readSpar in device_parameter_request.py: cannot open file: ")
			fullfilenameSRI="cannot open file"
			return "NO FILE"

		sfilelines = [a for a in fspar.read().splitlines()]             # sfilelines is a string array of the lines in the file
		for fileline in sfilelines:
			# get timestamp
			if "year" in fileline:
				spar_year=fileline.split('\t')[1].lstrip()
			elif "month" in fileline:
				spar_month=fileline.split('\t')[1].lstrip()
			elif "day" in fileline:
				spar_day=int(fileline.split('\t')[1].lstrip())
			elif "hour" in fileline:
				spar_hour=int(fileline.split('\t')[1].lstrip())
			elif "minute" in fileline:
				spar_minute=int(fileline.split('\t')[1].lstrip())
			elif "second" in fileline:
				spar_second=fileline.split('\t')[1].lstrip()
			# get devicename and location on wafer
			elif "wafer name" in fileline:
				wafer_name=fileline.split('\t')[1].lstrip()
			elif "device name" in fileline:
				devicename=fileline.split('\t')[1].lstrip()
			elif "x location" in fileline:
				x_location=int(fileline.split('\t')[1].lstrip())
			elif "y location" in fileline:
				y_location=int(fileline.split('\t')[1].lstrip())
			elif "Vds" in fileline:
				Vds_spar=float(fileline.split('\t')[1].lstrip())
			elif "Id" in fileline:
				Id_spar=float(fileline.split('\t')[1].lstrip())
			elif "drain status" in fileline:
				drainstatus_spar=fileline.split('\t')[1].lstrip()
			elif "Vgs" in fileline:
				Vgs_spar=float(fileline.split('\t')[1].lstrip())
			elif "Ig" in fileline:
				Ig_spar=float(fileline.split('\t')[1].lstrip())
			elif "gate status" in fileline:
				gatestatus_spar=fileline.split('\t')[1].lstrip()
		# now load in S-parameter data itself (complex)
		for fileline in sfilelines:                 # find type of file
			if (("#" in fileline) and (' S ' in fileline)):                         # this is the datatype specifier
				if (' RI ' in fileline):
					Sparameter_type = 'SRI'                      # these are complex 2-port S-parameter data
				elif (' DB ' in fileline):
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
				Z0 = float(fileline[re.search("R ",fileline).start()+2:])           # read characteristic impedance

	# now read data from file and output complex (RI) S-parameters ##############
		freq=col.deque()
		s11=col.deque()
		cap=col.deque()
		res=col.deque()
		fcap=open(os.path.join(pathname_spar,fileS.split('.')[0]+".cap"),'w')

		for fileline in sfilelines:                                                 # load lines from the data file
			if not(('!' in fileline) or ('#' in fileline)):                       # then this line are data
				freq.append(Sfrequency_multiplier*float(fileline.split()[0]))                    # frequency in Hz
				s11.append(complex(float(fileline.split()[1]),float(fileline.split()[2])))
				zin=Z0*(1.+s11[-1])/(1.-s11[-1])
				res.append(zin.real())
				cap.append(1./(2.*3.141*freq[-1]*zin.imag()))

				#convert to impedance



		fspar.close()
	try: parameters.append("SRI")											# we now have at complex S-parameters so set the indicator
	except:
		parameters = []
		parameters.append("SRI")
	return "success"
############################################################################################################################################################################