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
			if ('GHZ' in fileline):
				Sfrequency_multiplier= 1E9
			elif ('MHZ' in fileline):
				Sfrequency_multiplier= 1E6
			elif ('KHZ' in fileline):
				Sfrequency_multiplier= 1E3
			else:
				Sfrequency_multiplier= 1.0
			#Z0 = float(fileline[re.search("R ",fileline).start()+2:])           # read characteristic impedance
	Spar={}
	Spar['name']=sparfilename
	Spar['frequency']=[]        # frequencies in Hz
	Spar['s']=[]                # 2x2 S-parameter matrix at
# now read data from file and output complex (RI) S-parameters ##############

	for fileline in sfilelines:                                                 # load lines from the data file
		if not(('!' in fileline) or ('#' in fileline)):                       # then this line are data at a single frequency
			Spar['frequency'].append(Sfrequency_multiplier*float(fileline.split()[0]))                    # read the frequency
			Spar['s'].append(np.empty((2,2),complex))           # S-parameters are in real+jimaginary
			if Sparameter_type is 'SRI':                 # these are complex S-parameter data
				#print "fileline =",fileline                                 # debug
				Spar['s'][-1][0,0]=complex(float(fileline.split()[1]),float(fileline.split()[2]))
				Spar['s'][-1][1,0]=complex(float(fileline.split()[3]),float(fileline.split()[4]))
				Spar['s'][-1][0,1]=complex(float(fileline.split()[5]),float(fileline.split()[6]))
				Spar['s'][-1][1,1]=complex(float(fileline.split()[7]),float(fileline.split()[8]))
			if Sparameter_type is 'SDB':                 					# these are dB/angle S-parameter data convert to complex
				sparm = float(fileline.split()[1])            					# read magnitude (dB)
				spara = float(fileline.split()[2])			                   # read angle (degrees)
				Spar['s'][-1][0,0]=convertdBtoRI(sparm,spara)                     # append real and imaginary to S-parameter array

				sparm = float(fileline.split()[3])					            # these are dB/angle S-parameter data convert to complex
				spara = float(fileline.split()[4])	                   			# read angle (degrees)
				Spar['s'][-1][1,0]=convertdBtoRI(sparm,spara)                    # append real and imaginary to S-parameter array

				sparm = float(fileline.split()[5])            					# these are dB/angle S-parameter data convert to complex
				spara = float(fileline.split()[6])                   			# read angle (degrees)
				Spar['s'][-1][0,1]=convertdBtoRI(sparm,spara)                     # append real and imaginary to S-parameter array

				sparm = float(fileline.split()[7])            					# these are dB/angle S-parameter data convert to complex
				spara = float(fileline.split()[8])                   			# read angle (degrees)
				Spar['s'][-1][1,1]=convertdBtoRI(sparm,spara)                     # append real and imaginary to S-parameter array

			if Sparameter_type is 'SMA':                 					# these are linear/angle (degrees) S-parameter data convert to complex
				sparm = float(fileline.split()[1])                              # read magnitude (linear)
				spara = float(fileline.split()[2])				                # read angle (degrees)
				Spar['s'][-1][0,0]=convertMAtoRI(sparm,spara)                     # append real and imaginary to S-parameter array

				sparm = float(fileline.split()[3])                              # read magnitude (linear)
				spara = float(fileline.split()[4])				                # read angle (degrees)
				Spar['s'][-1][1,0]=convertMAtoRI(sparm,spara)                    # append real and imaginary to S-parameter array

				sparm = float(fileline.split()[5])                              # read magnitude (linear)
				spara = float(fileline.split()[6])				                # read angle (degrees)
				Spar['s'][-1][0,1]=convertMAtoRI(sparm,spara)                     # append real and imaginary to S-parameter array

				sparm = float(fileline.split()[7])                              # read magnitude (linear)
				spara = float(fileline.split()[8])				                # read angle (degrees)
				Spar['s'][-1][1,1]=convertMAtoRI(sparm,spara)                     # append real and imaginary to S-parameter array
	fspar.close()
	return Spar
############################################################################################################################################################################
# flip two-port ports 1 and 2. Return transposed S-parameters
def spar_flip_ports(S):
	if len(S['frequency'])!=len(S['s']): raise ValueError("ERROR in S-parameters! Number of S-parameters not equal to number of frequency points")
	for ifreq in range(0,len(S['frequency'])):
		s11=S['s'][ifreq][0,0]
		s21=S['s'][ifreq][1,0]
		s12=S['s'][ifreq][0,1]
		s22=S['s'][ifreq][1,1]
		S['s'][ifreq][0,0]=s22
		S['s'][ifreq][1,0]=s12
		S['s'][ifreq][0,1]=s21
		S['s'][ifreq][1,1]=s11
	return S
#############################################################################################################################################################################
# read the raw noise and the preamp noise parameters (if available). Returns preamppara and rawnoise
def read_raw_noise(noisefilename=None):
	preampnoiseparameters=[]
	rawnoisefiguredB=[]
	try: frawnoise=open(noisefilename,'r')
	except: raise ValueError("ERROR! cannot open "+noisefilename+" raw measured noise file")
	nlines = [a for a in frawnoise.read().splitlines()]             # nlines is a string array of the lines in the file
	for nl in nlines:
		if not '#' in nl and 'preamp' in nl:        # get preamplifier noise parameters if there is a preamp:
			if 'GHZ' in nl: frequency=1E9*float(nl.split('GHZ')[0].strip().split()[-1].strip())
			elif 'MHZ' in nl: frequency=1E6*float(nl.split('MHZ')[0].strip().split()[-1].strip())
			elif 'KHZ' in nl: frequency=1E3*float(nl.split('KHZ')[0].strip().split()[-1].strip())
			elif 'HZ' in nl: frequency=float(nl.split('HZ')[0].strip().split()[-1].strip())
			else: raise ValueError("ERROR! improper frequency format for preamp")
			if not ('FmindB' in nl and 'gopt' in nl and 'Rn' in nl): raise ValueError("ERROR! one of FmindB, gopt, and/or Rn missing and/or misnamed")
			preampnoiseparameters.append({})
			preampnoiseparameters[-1]['frequency']=frequency
			preampnoiseparameters[-1]['FmindB']=float(nl.split('FmindB')[1].strip().split()[0].strip())         # get the minimum noise figure (linear)
			preampnoiseparameters[-1]['gopt']=complex(float(nl.split('gopt')[1].split()[0].strip()),float(nl.split('gopt')[1].split('j')[0].split()[1].strip()))
			preampnoiseparameters[-1]['Rn']=float(nl.split('Rn')[1].split()[0].strip())

		elif not '#' in nl and 'rawnoise' in nl and not 'rawnoisefigure' in nl and not 'tuner_data position' in nl:        # get raw noise figure vs tuner_data position and frequency
			if 'GHZ' in nl: frequency=1E9*float(nl.split('GHZ')[0].split()[-1].strip())
			elif 'MHZ' in nl: frequency=1E6*float(nl.split('MHZ')[0].split()[-1].strip())
			elif 'KHZ' in nl: frequency=1E3*float(nl.split('KHZ')[0].split()[-1].strip())
			elif 'HZ' in nl: frequency=float(nl.split('HZ')[0].split()[-1].strip())
			else: raise ValueError("ERROR! improper frequency format for raw noise")
			rawnoisefiguredB.append({})
			rawnoisefiguredB[-1]['frequency']=frequency         # frequency in Hz for this raw noise data
		elif not '#' in nl and 'tuner position' in nl:        # get raw noise figure vs tuner_data position
			position=nl.split('tuner position')[1].split()[0].strip()       # tuner_data position xxxxx,yyyyyy,zzzzzz
			rawnoisefiguredB[-1][position]=float(nl.split('rawnoisefiguredB')[1].split()[0].strip())
	frawnoise.close()
	return rawnoisefiguredB,preampnoiseparameters
##############################################################################################################################################################################
# write noise figures vs frequency and tuner_data positions and tuner_data reflection coefficients
# noise figures are written in dB noise figure input data are in dB or linear and this is selected in the input parameter
# note that the tuner_data positions between the tuner_data and the noise measurements MUST match at the frequency point under consideration
def write_noisefigure_frequency_reflection(noisefilename=None,tuner=None,NF=None,dBinput=True):
	if tuner==None or len(tuner.tuner_data)==0: raise ValueError("ERROR! no tuner_data data")
	if NF==None or len(NF)==0: raise ValueError("ERROR! no noise figure data")
	try: fnf=open(noisefilename,'w')
	except: raise ValueError("ERROR! cannot write "+noisefilename+" noiseparameters file. Maybe directory does not exist")
	fnf.write('# frequency GHZ\ttuner_position\treflection_coefficient_MA\tnoise_figure_dB\n')
	for ifn in range(0,len(NF)):
		ift=min(range(len(tuner.tuner_data)), key=lambda i:abs(tuner.tuner_data[i]['frequency']-NF[ifn]['frequency']))
		if floatequal(tuner.tuner_data[ift]['frequency'],NF[ifn]['frequency'],1E-3):         # is there a close enough match between tuner_data and noisefigure frequency points?
			positions=[p for p in NF[ifn].keys() if p!='frequency']                      # get tuner_data positions from measured noise figure
			for p in positions:
				if dBinput: NFdB=NF[ifn][p]
				else: NFdB=10*np.log10(NF[ifn][p])
				tunerreflection=convertRItoMA(tuner.get_tuner_reflection(frequency=NF[ifn]['frequency'],position=p))
				fnf.write('%10.2f\t%s\t%10.2f %10.2f\t%10.2f\n' %(1E-9*NF[ifn]['frequency'],p,tunerreflection.real,tunerreflection.imag,NFdB))
	fnf.close()
#############################################################################################################################################################################
# write out noise parameters
def write_noise_parameters(noisefilename=None,npar=None,preampresults=False,):
	if npar==None or len(npar)==0: raise ValueError("ERROR! no noise parameter data")
	try: fnp=open(noisefilename,'w')
	except: raise ValueError("ERROR! cannot write "+noisefilename+" noiseparameters file. Maybe directory does not exist")
	if not preampresults: fnp.write('# frequency GHZ\tFmindB\tgammaopt_Mag_Angle\tRn(ohms)\n')
	for ifp in range(0,len(npar)):
		if not preampresults: fnp.write('%10.2f\t%10.2f\t %10.3f %10.2f\t%10.2f\n' %(1E-9*npar[ifp]['frequency'],npar[ifp]['FmindB'],convertRItoMA(npar[ifp]['gopt']).real,convertRItoMA(npar[ifp]['gopt']).imag,npar[ifp]['Rn']))
		else: fnp.write('preamp\t%10.2fGHZ\tFmindB %10.2f\tgopt %10.3f %10.3fj\tRn %10.2f\n' %(1E-9*npar[ifp]['frequency'],npar[ifp]['FmindB'],npar[ifp]['gopt'].real,npar[ifp]['gopt'].imag,npar[ifp]['Rn']))
	fnp.close()
#############################################################################################################################################################################
# typically used to read system noise parameters
# the data output (noiseparameters) has the format:

#e.g.
#npar[i]['frequency'] = frequency in Hz at the i'th frequency point.
# npar[i]['gopt']= the reflection coefficient presented to port 1 of the 2-port having these noise parameters which gives the minimum noise figure, formatted as real+jimaginary, at the i'th frequency point.
# npar[i]['FmindB']= the 2-port's minimum noise figure given in dB, at the i'th frequency point.
# npar[i]['Rn']= the 2-port's noise resistance in ohms, at the i'th frequency point.
# npar[i]['GassocdB']=the 2-port's associated gain in dB
#Z0 = 50ohms
def read_noise_parameters(noisefilename=None):
	try: fnpar=open(noisefilename,'r')
	except: raise ValueError("ERROR! cannot read "+noisefilename+" noiseparameters file.")
	npar=[]                       # noise parameters list of dictionaries
	for pl in fnpar:
		if '#' in pl and "frequency" in pl:         # this line determines the units of frequency
			if pl.split('frequency_')[1].strip().split()[0].strip().lower()=='khz': frequencymulitplier=1E3
			elif pl.split('frequency_')[1].strip().split()[0].strip().lower()=='mhz': frequencymulitplier=1E6
			elif pl.split('frequency_')[1].strip().split()[0].strip().lower()=='ghz': frequencymulitplier=1E9
			elif pl.split('frequency_')[1].strip().split()[0].strip().lower()=='hz': frequencymulitplier=1.
			else: raise ValueError("ERROR! illegal frequency units")
		elif not '#' in pl:
			npar.append({})
			npar[-1]['frequency']=frequencymulitplier*float(pl.split()[0].strip())
			npar[-1]['FmindB']=float(pl.split()[1].strip())
			npar[-1]['gopt']=convertMAtoRI(float(pl.split()[2].strip()), float(pl.split()[3].strip()))
			npar[-1]['Rn']=float(pl.split()[4].strip())
	fnpar.close()
	return npar
# def read_noise_parameters(noisefilename=None):
# 	try: fnpar=open(noisefilename,'r')
# 	except: raise ValueError("ERROR! cannot read "+noisefilename+" noiseparameters file.")
# 	npar=[]                       # noise parameters list of dictionaries
# 	for pl in fnpar:
# 		if not '#' in pl:
# 			npar.append({})
# 			if 'preamp' in pl:
# 				npar[-1]['frequency']=1E9*float(pl.split('GHZ')[0].strip().split()[-1].strip())
# 				npar[-1]['FmindB']=float(pl.split('FmindB')[1].strip().split()[0].strip())
# 				npar[-1]['gopt']=complex(float(pl.split('gopt')[1].strip().split()[0].strip()), float(pl.split('gopt')[1].strip().split()[1].split('j')[0].strip()))
# 				npar[-1]['Rn']=float(pl.split('Rn')[1].strip())
# 			else:
# 				npar[-1]['frequency']=1E9*float(pl.split()[0].strip())
# 				npar[-1]['FmindB']=float(pl.split()[1].strip())
# 				npar[-1]['gopt']=convertMAtoRI(float(pl.split()[2].strip()),float(pl.split()[3].strip()))
# 				npar[-1]['Rn']=float(pl.split()[4].strip())
# 	fnpar.close()
# 	return npar
#############################################################################################################################################################################
# write the noisefigure as a function of frequency (GHz) and position
# noisefile name is the full pathname of the noise figure output file
# if NF is in dB then set dBinput=True. If NF is linear then set dBinput=False
# NF is the noise figure formatted:
def write_noisefigure_frequency_position_reflection(noisefilename=None, NF=None, tuner=None, dBinput=True):
	try: fn=open(noisefilename,'w')
	except: raise ValueError("ERROR! cannot write "+noisefilename+" noisefigure file. Maybe directory does not exist")
	for ifr in range(0,len(NF)):
		fn.write('# frequency\t%10.2fGHZ\n'%(1E-9*NF[ifr]['frequency']))
		fn.write('! tuner position\treflection coefficient mag angle\tnoisefigure dB\n')
		for pos in NF[ifr].keys():
			if str(pos)!="frequency":           # exclude frequencies - looking at tuner positions only
				reflectioncoef=convertRItoMA(tuner.get_tuner_reflection(position=pos,frequency=NF[ifr]['frequency']))
				if not dBinput: noisefiguredB=10.*np.log10(NF[ifr][pos])            # convert noisefigure to dB if it's not already in dB
				else: noisefiguredB=NF[ifr][pos]
				fn.write('%s\t%10.2f %10.1f\t%10.2f\n'%(str(pos),reflectioncoef.real,reflectioncoef.imag,noisefiguredB))
	fn.close()
############################################################################################################################################################################
# # read the raw noise and the preamp noise parameters (if available). Returns preamppara and rawnoise:
# def read_noisefigure(noisefilename=None):
# 	preampnoiseparameters=[]
# 	noisefiguredB=[]
# 	try: fnoise=open(noisefilename,'r')
# 	except: raise ValueError("ERROR! cannot open "+noisefilename+" noise file")
# 	nlines = [a for a in fnoise.read().splitlines()]             # nlines is a string array of the lines in the file
# 	for nl in nlines:
# 		if not '!' in nl and 'frequency' in nl:        # get raw noise figure vs tuner_data position and frequency
# 			if 'GHZ' in nl: frequency=1E9*float(nl.split('GHZ')[0].split()[-1].strip())
# 			elif 'MHZ' in nl: frequency=1E6*float(nl.split('MHZ')[0].split()[-1].strip())
# 			elif 'KHZ' in nl: frequency=1E3*float(nl.split('KHZ')[0].split()[-1].strip())
# 			elif 'HZ' in nl: frequency=float(nl.split('HZ')[0].split()[-1].strip())
# 			else: raise ValueError("ERROR! improper frequency format for noise")
# 			noisefiguredB.append({})
# 			noisefiguredB[-1]['frequency']=frequency         # frequency in Hz for this raw noise data
# 		elif not '#' in nl and not '!' in nl and not 'frequency' in nl:        # get raw noise figure vs tuner_data position
# 			position=nl.split()[0].split()[0].strip()       # tuner_data position xxxxx,yyyyyy,zzzzzz
# 			noisefiguredB[-1][position]=float(nl.split()[-1].strip())   # last value is the dB noise figure
# 	fnoise.close()
# 	return noisefiguredB
##############################################################################################################################################################################
# read the raw noise and the preamp noise parameters (if available). Returns preamppara and rawnoise:
def read_noisefigure(noisefilename=None):
	preampnoiseparameters=[]
	noisefiguredB=[]
	try: fnoise=open(noisefilename,'r')
	except: raise ValueError("ERROR! cannot open "+noisefilename+" noise file")
	nlines = [a for a in fnoise.read().splitlines()]             # nlines is a string array of the lines in the file
	for nl in nlines:
		if '#' in nl and 'frequency' in nl:
			noisefiguredB.append({})
			noisefiguredB[-1]['frequency']=1E9*float(nl.split('frequency')[1].strip().split('GHZ')[0].strip())         # frequency in Hz for this raw noise data
		elif not '#' in nl and not '!' in nl:        # get raw noise figure vs tuner_data position
			position=nl.split()[0].strip()       # tuner_data position xxxxx,yyyyyy,zzzzzz
			reflectioncoefficientmag=float(nl.split()[1].strip())
			reflectioncoefficientang=float(nl.split()[2].strip())
			noisefiguredB[3][position]=float(nl.split()[3].strip())   # last value is the dB noise figure
	fnoise.close()
	return noisefiguredB
#################################################################################################################################################################################