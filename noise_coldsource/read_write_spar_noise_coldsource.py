# read S-parameters
# reads standard Touchstone format S-parameter files and outputs
#  2-port S parameters in real+jimaginary format and is of the form
# of a dictionary: S where S['name'] is the full filename of the S-parameter data file, S['frequency'][i]=ith frequency
# in GHz and S['s'][i]=2x2 matrix of S-parameters in real+jimaginary format
import numpy as np
import datetime as dt
from calculated_parameters import convertdBtoRI, convertMAtoRI, convertRItoMA
from utilities import floatequal

def read_spar_2port(sparfilename=None):
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
############################################################################################################################################################################
# Read .s1p, i.e. one-port reflection coefficient data
def read_spar_1port(sparfilename=None):
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
	gamma={}

# now read data from file and output complex (RI) S-parameters ##############
#
	f=[]
	gamma=[]
	for fileline in sfilelines:                                                 # load lines from the data file
		if not(('!' in fileline) or ('#' in fileline)):                       # then this line are data at a single frequency
			f.append(Sfrequency_multiplier*float(fileline.split()[0]))               # frequency of S-parameters in MHz

			if Sparameter_type is 'SRI':                 # these are complex S-parameter data
				gamma.append(complex(float(fileline.split()[1]),float(fileline.split()[2])))     # gamma, real and j*imaginary
			if Sparameter_type is 'SDB':                 					# these are dB/angle S-parameter data convert to complex real and j*imaginary
				gammam = float(fileline.split()[1])            					# read magnitude (dB)
				gammaa = float(fileline.split()[2])			                   # read angle (degrees)
				gamma.append(convertdBtoRI(gammam,gammaa))                     # append real and imaginary to gamma array

			if Sparameter_type is 'SMA':                 					# these are linear/angle (degrees) gamma data convert to complex
				gammam = float(fileline.split()[1])            					# read magnitude (dB)
				gammaa = float(fileline.split()[2])			                   # read angle (degrees)
				gamma.append(convertMAtoRI(gammam,gammaa))                     # append real and imaginary to gamma array
	fspar.close()
	return {'frequency':f,'gamma':gamma}                                # frequencies are in MHz and gammas are in real+jimaginary
############################################################################################################################################################################




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
############################################################################################################
# write gain-bandwidth product of composite noise meter, reflection coefficient of composite noise meter and noise source diode to file
# writes data from get_noisemeter_gainbandwidthproduct() in get_noisemeter_gainbandwidthproduct.py
# parameter inputs:
#
# outputfile -> the full pathname of the date to be written
# resolutionbandwidthHz -> the spectrum analyzer's resolution bandwidth in Hz, used to obtain the gain-bandwidth product
# videobandwidthHz -> the spectrum analyzer's video bandwidth in Hz, used to obtain the gain-bandwidth product
# frequencies -> the set of frequencies of the gain bandwidth products in MHz frequencies[frequencyindex]
# GB -> the gain-bandwidth product GB[frequencyindex]
# gammanm -> gammanm[frequencyindex] is the reflection coefficient of the composite noise meter real+jimaginary
# gammadcold -> gammacold[frequencyindex] is the reflection coefficient of the noise diode in the off state real+jimaginary
# gammadhot -> gammahot[frequencyindex] is the reflection coefficient of the noise diode in the on state real+jimaginary

#
##############################################################
def write_Gnm_gamma(outputfile=None,resolutionbandwidthHz=None,videobandwidthHz=None,frequencies=None,GB=None,gammanm=None,gammadcold=None,gammadhot=None):
	fn = open(outputfile, 'w')
	fn.write('# gain-bandwidth product and reflection coefficients for composite noise meter and noise source\n')
	fn.write('# filename\t' + outputfile + '\n')
	fn.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fn.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fn.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fn.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fn.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fn.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# datatype header
	fn.write("#\n#\n# system Z=50ohms\n#\n")
	fn.write("# resolution bandwidth Hz\t%10.0f\n" %(resolutionbandwidthHz))
	fn.write("# video bandwidth Hz\t %10.0f\n" %(videobandwidthHz))
	fn.write("# frequency MHz\tgain-bandwidth product\tnoise meter reflection coefficient (real)\tnoise meter reflection coefficient (imaginary)\tdiode off reflection coefficient (real)\tdiode off reflection coefficient (imaginary)\tdiode on reflection coefficient (real)\tdiode on reflection coefficient (imaginary)")
	for f in frequencies:
		fn.write("\n%10.0f\t%10.5E\t%10.5E\t%10.5E\t%10.5E\t%10.5E\t%10.5E\t%10.5E" %(f,GB[str(f)],gammanm[str(f)].real,gammanm[str(f)].imag,gammadcold[str(f)].real,gammadcold[str(f)].imag,gammadhot[str(f)].real,gammadhot[str(f)].imag))
	fn.close()
########################################################################################################
# read gain-bandwidth product of composite noise meter, reflection coefficient of composite noise meter and noise source diode from file
#
########################################################################################################################
def read_Gnm_gamma(inputfile=None):
	try: fin=open(inputfile,'r')
	except: raise ValueError("ERROR! cannot open gain-bandwidth-gamma file")
	filelines = [a for a in fin.read().splitlines()]             # sfilelines is a string array of the lines in the file
	nmgb={}
	nmgb['frequenciesMHz']=[]
	nmgb['GB']=[]
	nmgb['gammanm']=[]
	nmgb['gammadcold']=[]
	for fileline in filelines:                 # find type of file
		if (not "#" in fileline) and (not "!" in fileline):                         # skip over comments
			nmgb['frequenciesMHz'].append(round(float(fileline.split('\t')[0])))       # frequencies in MHz
			nmgb['GB'].append(float(fileline.split('\t')[1]))                       # linear, not dB
			nmgb['gammanm'].append(complex(float(fileline.split('\t')[2]),float(fileline.split('\t')[3])))      # real+jimaginary
			nmgb['gammadcold'].append(complex(float(fileline.split('\t')[4]),float(fileline.split('\t')[5])))   # real+jimaginary
	fin.close()
	return nmgb
###########################################################################################################################