from calculated_parameters import convertMAtoRI, convertRItoMA
import numpy as np
# read mag ang reflection coefficients from a file
# filename is the complete path of the file containing the reflection coefficients to be read
def read_reflection_coefficients(filename=None):
	try: fref=open(filename,'r')
	except: raise ValueError("ERROR! cannot open reflection coefficient file")
	filelines = [a for a in fref.read().splitlines()]             # sfilelines is a string array of the lines in the file
	ref=[]
	for fileline in filelines:                                                 # load lines from the data file
		if not(('!' in fileline) or ('#' in fileline)):                       # skip comment lines
			ref.append([float(fileline.split()[0]),float(fileline.split()[1])])             # read reflection coefficient magnitude (linear)
	fref.close()
	return ref
#########
# read 3rd order output intercept points vs reflection coefficients
# the parameter is a real and can be power, third order intercept pointnoise figure,
def read_OIP3_vs_reflection_coefficients(filename=None):
	try: fref=open(filename,'r')
	except: raise ValueError("ERROR! cannot open reflection coefficient file")
	filelines = [a for a in fref.read().splitlines()]             # sfilelines is a string array of the lines in the file
	Pgain=[]
	Pout=[]
	gain=[]
	TOI=[]
	ref=[]
	haveTOI=False
	PGAIN=False
	if '_TOI.' in filename:
		for l in filelines:                                                 # load lines from the data file
			if "sorted averaged TOI" in l:
				haveTOI=True                   # read data that follows
				PGAIN=False
			elif "DUT power output" in l:
				haveTOI=False
				PGAIN=True
			if haveTOI and not(('!' in l) or ('#' in l)):                       # skip comment lines
				ref.append(convertMAtoRI(mag=float(l.split()[1].strip()),ang=float(l.split()[2].strip())))             # read reflection coefficient magnitude (linear) and angle and convert them to complex real+jimaginary
				TOI.append(float(l.split()[3].strip()))
				gain.append(float(l.split()[4].strip()))
				print(ref[-1])
			if PGAIN and not(('!' in l) or ('#' in l)):                       # skip comment lines
				ref.append(convertMAtoRI(mag=float(l.split()[1].strip()),ang=float(l.split()[2].strip())))             # read reflection coefficient magnitude (linear) and angle and convert them to complex real+jimaginary
				Pout.append(float(l.split()[3].strip()))
				Pgain.append(float(l.split()[4].strip()))
	elif '_TOIVgssweep' in filename:
		valid_data=False
		for l in filelines:                                                 # load lines from the data file
			if "parameters vs output reflection coefficient (gamma) for the timestamp which produces highest peak TOI for the given gamma" in l: valid_data=True     # turn on data read
			if "parameters vs timestamps" in l: valid_data=False                   # turn off data read
			if valid_data and not(('!' in l) or ('#' in l)):                       # skip comment lines
				ref.append(convertMAtoRI(mag=float(l.split()[1].strip()),ang=float(l.split()[2].strip())))             # read reflection coefficient magnitude (linear) and angle and convert them to complex real+jimaginary
				TOI.append(float(l.split()[3].strip()))
				gain.append(float(l.split()[4].strip()))
				print(ref[-1])
	fref.close()
	print(len(ref),ref)
	if '_TOIVgssweep' in filename: return "TOI",ref,TOI,gain
	if TOI: return "TOI",ref,TOI,gain
	elif PGAIN: return "pgain",ref,Pgain,Pout