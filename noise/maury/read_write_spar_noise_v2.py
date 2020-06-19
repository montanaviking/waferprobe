# read S-parameters
# reads standard Touchstone format S-parameter files and outputs
#  2-port S parameters in real+jimaginary format and is of the form
# of a dictionary: S where S['name'] is the full filename of the S-parameter data file, S['frequency'][i]=ith frequency
# in GHz and S['s'][i]=2x2 matrix of S-parameters in real+jimaginary format
import numpy as np
from calculated_parameters import convertdBtoRI, convertMAtoRI, convertRItoMA
from utilities import floatequal

def read_spar(sparfilename=None):
	try: fspar=open(sparfilename,'r')
	except: raise ValueError("ERROR! cannot open S-parameter file")

	sfilelines = [a for a in fspar.read().splitlines()]             # sfilelines is a string array of the lines in the file
	# now load in S-parameter data itself (complex)
	for fileline in sfilelines:                 # find type of file
		if (("#" in fileline) and ('S' in fileline)):                         # this is the datatype specifier
			if ('RI' in fileline):
				Sparameter_type = 'SRI'                      # these are complex 2-port S-parameter data
			elif ('DB' in fileline):
				Sparameter_type= 'SDB'                      # these are S-parameter data dB magnitude and angle in degrees
			elif ('MA' in fileline):
				Sparameter_type = 'SMA'                      # these are S-parameter data magnitude and angle in degrees
			if ('ghz' in fileline.lower()):
				Sfrequency_multiplier= 1000
			elif ('mhz' in fileline.lower()):
				Sfrequency_multiplier= 1
			elif ('khz' in fileline.lower()):
				Sfrequency_multiplier=1E-3
			elif ('hz' in fileline.lower()):
				Sfrequency_multiplier=1E-6
			else: raise ValueError("ERROR! improper frequency designation. Must be one of GHz,MHz,KHz, or Hz")
			#Z0 = float(fileline[re.search("R ",fileline).start()+2:])           # read characteristic impedance
	Spar={}

# now read data from file and output complex (RI) S-parameters ##############
# frequency for the S-parameters is converted to MHz (str variable type as a dict key)
	for fileline in sfilelines:                                                 # load lines from the data file
		if not(('!' in fileline) or ('#' in fileline)):                       # then this line are data at a single frequency
			f=str(int(Sfrequency_multiplier*float(fileline.split()[0])))               # frequency of S-parameters in MHz
			Spar[f]=np.empty((2,2),complex)                   # read the frequency
			if Sparameter_type is 'SRI':                 # these are complex S-parameter data
				#print "fileline =",fileline                                 # debug
				Spar[f][0,0]=complex(float(fileline.split()[1]),float(fileline.split()[2]))     # S11
				Spar[f][1,0]=complex(float(fileline.split()[3]),float(fileline.split()[4]))     # S21
				Spar[f][0,1]=complex(float(fileline.split()[5]),float(fileline.split()[6]))     # S12
				Spar[f][1,1]=complex(float(fileline.split()[7]),float(fileline.split()[8]))     # S22
			if Sparameter_type is 'SDB':                 					# these are dB/angle S-parameter data convert to complex
				sparm = float(fileline.split()[1])            					# read magnitude (dB)
				spara = float(fileline.split()[2])			                   # read angle (degrees)
				Spar[f][0,0]=convertdBtoRI(sparm,spara)                     # append real and imaginary to S-parameter array

				sparm = float(fileline.split()[3])					            # these are dB/angle S-parameter data convert to complex
				spara = float(fileline.split()[4])	                   			# read angle (degrees)
				Spar[f][1,0]=convertdBtoRI(sparm,spara)                    # append real and imaginary to S-parameter array

				sparm = float(fileline.split()[5])            					# these are dB/angle S-parameter data convert to complex
				spara = float(fileline.split()[6])                   			# read angle (degrees)
				Spar[f][0,1]=convertdBtoRI(sparm,spara)                     # append real and imaginary to S-parameter array

				sparm = float(fileline.split()[7])            					# these are dB/angle S-parameter data convert to complex
				spara = float(fileline.split()[8])                   			# read angle (degrees)
				Spar[f][1,1]=convertdBtoRI(sparm,spara)                     # append real and imaginary to S-parameter array

			if Sparameter_type is 'SMA':                 					# these are linear/angle (degrees) S-parameter data convert to complex
				sparm = float(fileline.split()[1])                              # read magnitude (linear)
				spara = float(fileline.split()[2])				                # read angle (degrees)
				Spar[f][0,0]=convertMAtoRI(sparm,spara)                     # append real and imaginary to S-parameter array

				sparm = float(fileline.split()[3])                              # read magnitude (linear)
				spara = float(fileline.split()[4])				                # read angle (degrees)
				Spar[f][1,0]=convertMAtoRI(sparm,spara)                    # append real and imaginary to S-parameter array

				sparm = float(fileline.split()[5])                              # read magnitude (linear)
				spara = float(fileline.split()[6])				                # read angle (degrees)
				Spar[f][0,1]=convertMAtoRI(sparm,spara)                     # append real and imaginary to S-parameter array

				sparm = float(fileline.split()[7])                              # read magnitude (linear)
				spara = float(fileline.split()[8])				                # read angle (degrees)
				Spar[f][1,1]=convertMAtoRI(sparm,spara)                     # append real and imaginary to S-parameter array
	fspar.close()
	return Spar
############################################################################################################################################################################
# flip two-port ports 1 and 2. Return transposed S-parameters
def spar_flip_ports(S):
	for f in S.keys():
		s11=S[f][0,0]
		s21=S[f][1,0]
		s12=S[f][0,1]
		s22=S[f][1,1]
		S[f][0,0]=s22
		S[f][1,0]=s12
		S[f][0,1]=s21
		S[f][1,1]=s11
	return S
#############################################################################################################################################################################
# write noise figures vs frequency and tuner_data positions and tuner_data reflection coefficients
# noise figures are written in dB noise figure input data are in dB or linear and this is selected in the input parameter
# note that the tuner_data positions between the tuner_data and the noise measurements MUST match at the frequency point under consideration. Frequencies in MHz.
# writes ONLY the data where the tuner data and NF data have frequency points in common
def write_noisefigure_frequency_reflection(noisefilename=None,tuner=None,NF=None,dBinput=True):
	if tuner==None or len(tuner.tuner_data)==0: raise ValueError("ERROR! no tuner_data data")
	if NF==None or len(NF)==0: raise ValueError("ERROR! no noise figure data")
	try: fnf=open(noisefilename,'w')
	except: raise ValueError("ERROR! cannot write "+noisefilename+" noiseparameters file. Maybe directory does not exist")
	fnf.write('# frequency GHZ\ttuner_position\treflection_coefficient_MA\tnoise_figure_dB\n')
	frequencies=list(set(tuner.keys())&set(NF.keys()))                                      # get list of frequencies (MHz) common to both NF and tuner data
	for f in frequencies:
		for pos in tuner.tuner_data.keys():                                 # tuner motor positions for both tuner and NF data
			if dBinput: NFdB=NF[f][pos]
			else: NFdB=10*np.log10(NF[f][pos])
			tunerreflection=convertRItoMA(tuner.get_tuner_reflection(frequency=int(f),position=pos))
			fnf.write('%10.2f\t%s\t%10.2f %10.2f\t%10.2f\n' %(1E-9*NF[f],str(pos),tunerreflection.real,tunerreflection.imag,NFdB))
	fnf.close()
#############################################################################################################################################################################
# typically used to read system noise parameters
# the data output (noiseparameters) has the format:
#e.g.
# frequency is in MHz (dictionary key)
# npar[requency]['gopt']= the reflection coefficient presented to port 1 of the 2-port having these noise parameters which gives the minimum noise figure, formatted as real+jimaginary, at the i'th frequency point.
# npar[requency]['FmindB']= the 2-port's minimum noise figure given in dB, at the i'th frequency point.
# npar[requency]['Rn']= the 2-port's noise resistance in ohms, at the i'th frequency point.
# npar[requency]['GassocdB']=the 2-port's associated gain in dB
#Z0 = 50ohms
def read_noise_parameters(noisefilename=None):
	try: fnpar=open(noisefilename,'r')
	except: raise ValueError("ERROR! cannot read "+noisefilename+" noiseparameters file.")
	npar={}                       # noise parameters list of dictionaries
	for pl in fnpar:
		if '#' in pl and "frequency" in pl:         # this line determines the units of frequency
			if pl.split('frequency_')[1].strip().split()[0].strip().lower()=='mhz': frequency_multiplier=1
			elif pl.split('frequency_')[1].strip().split()[0].strip().lower()=='ghz': frequency_multiplier=1000
			else: raise ValueError("ERROR! illegal frequency units, must be MHz or GHz")
		elif not '#' in pl:
			frequency=str(int(frequency_multiplier*float(pl.split()[0])))               # frequency of S-parameters in MHz
			npar[frequency]={}
			npar[frequency]['FmindB']=float(pl.split()[1].strip())
			npar[frequency]['gopt']=convertMAtoRI(float(pl.split()[2].strip()), float(pl.split()[3].strip()))
			npar[frequency]['Rn']=float(pl.split()[4].strip())
	fnpar.close()
	return npar
#############################################################################################################################################################################
# write the noisefigure as a function of frequency (GHz) and position
# noisefile name is the full pathname of the noise figure output file
# if NF is in dB then set dBinput=True. If NF is linear then set dBinput=False
# NF is the noise figure formatted: NF[frequency][pos]
# where frequency is the dict key of frequency in MHz and pos the dict key of tuner motor position to produce this noise figure, in xxxx,yyyyy,zzzz
def write_noisefigure_frequency_position_reflection(noisefilename=None, NF=None, tuner=None, dBinput=True):
	try: fn=open(noisefilename,'w')
	except: raise ValueError("ERROR! cannot write "+noisefilename+" noisefigure file. Maybe directory does not exist")
	for f in NF.keys():
		fn.write('# frequency\t%sGHZ\n'%(str(f)))
		fn.write('! tuner position\treflection coefficient mag angle\tnoisefigure dB\n')
		for pos in NF[f].keys():
			if str(pos)!="frequency":           # exclude frequencies - looking at tuner positions only
				reflectioncoef=convertRItoMA(tuner.get_tuner_reflection(position=pos,frequency=str(f)))
				if not dBinput: noisefiguredB=10.*np.log10(NF[f][pos])            # convert noisefigure to dB if it's not already in dB
				else: noisefiguredB=NF[f][pos]
				fn.write('%s\t%10.2f %10.1f\t%10.2f\n'%(str(pos),reflectioncoef.real,reflectioncoef.imag,noisefiguredB))
	fn.close()
############################################################################################################################################################################