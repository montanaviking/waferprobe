#### device table data setup to display all device parameters via use of the devtable.py widget
# gathers data from device parameters and places it into a datatable with columnheaders for display by the devtable.py widget
# hheaders is the parameter type
# data is a dictionary of the format:
# data[d=device name][pparameter (measured or calculated)] and data[d][p]=device data as specifed by the devicename=d and parameter name = p
from utilities import *
import collections as col

def all_device_data_to_table(wd=None, selecteddevices=None, Vgs=None, fractVdsfit=None, minTLMlength=None, maxTLMlength=None,linearfitquality_request=None,Vds_foc=None,deltaVgsplusthres=None,fractVgsfit=None, performYf=False ):
	if is_number(Vds_foc): Vds_foc=float(Vds_foc)
	if is_number(deltaVgsplusthres): deltaVgsplusthres=float(deltaVgsplusthres)
	if is_number(fractVdsfit): fractVdsfit=float(fractVdsfit)
	if is_number(fractVgsfit): fractVgsfit=float(fractVgsfit)
	else: fractVdsfit=None
	if is_number(Vgs): Vgs=float(Vgs)
	else: Vgs=None
	if is_number(fractVdsfit): fractVdsfit=float(fractVdsfit)
	else: fractVdsfit=None
	if is_number(minTLMlength): minTLMlength=float(minTLMlength)
	else: minTLMlength=None
	if is_number(maxTLMlength): maxTLMlength=float(maxTLMlength)
	else: maxTLMlength=None

	if Vgs==None:
		if hasattr(wd,"Vgs") and wd.Vgs!=None: Vgs=wd.Vgs
		else:
			wd.Vgs=None
			Vgs=None
	if Vgs!=None:
		dfoc=wd.DCd[wd.focfirstdevindex].Ron_foc()
	else: dfoc=None
	if dfoc!=None: iVgs = min(range(len(dfoc['Vgs'])),key=lambda i: abs(dfoc['Vgs'][i]-Vgs))		# get the index of the requested gate voltage: assume that Vgs values are the same for all devices in the wafer wd.focfirstdevindex is the device index of the first "good" family of curves IV measurement e.g. no measurements in compliance etc..
	else: iVgs=None
	if not is_number(minTLMlength): minTLMlength=None
	else: minTLMlength=float(minTLMlength)
	if not is_number(maxTLMlength): maxTLMlength=None
	else: maxTLMlength=float(maxTLMlength)

	if fractVdsfit!=None: wd.fractVdsfit_Ronfoc=fractVdsfit								# then need to update the fraction of the Id(Vds) curves from the family of curves, the the least squares linear fit is performed on to get on resistance
	hheaders=col.deque()											# headers (device parameters which were measured)
	data={}			# data is a 2-D dictionary of format data[devicename][parameter]
	hheaders.append('Device Name')
	hheaders.append('X')
	hheaders.append('Y')
	hheaders.append('total gate width (um)')
	# put in columns which will always appear
	for devk in selecteddevices:
			if devk not in data: data[devk]={}									# add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['X']=wd.DCd[devk].x()
			data[devk]['Y']=wd.DCd[devk].y()
			if wd.DCd[devk].devwidth!=None:
				data[devk]['total gate width (um)']=wd.DCd[devk].devwidth					# device total gate width in um
			else: data[devk]['total gate width (um)']='Not scaled'
########### Get the TLM length in um (empirical measured value from geometry file) ####################################################################
	haveadevice=False															# flag to see if at least one valid device exists for this measurement
	for devk in selecteddevices:
		if hasattr(wd.DCd[devk],"tlmlength"):
			if devk not in data: data[devk]={}									# add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			print("from line 56 in all_device_data_to_table.py tlmlength=",devk,wd.DCd[devk].tlmlength)
			data[devk]['TLM length um']=wd.DCd[devk].tlmlength
			haveadevice=True
		if haveadevice:																# if we have one or more valid devices for this measurement then include the parameters for the data set
			if 'TLM length um' not in hheaders: hheaders.append('TLM length um')
#######################done getting the TLM length #####################################################
########### Get |Idmax| single and On-Off ratio single and |Idmin| single ####################################################################
	haveadevice=False															# flag to see if at least one valid device exists for this measurement
	for devk in selecteddevices:
		if len(wd.DCd[devk].Idonoffratio_T())>0:
			if devk not in data: data[devk]={}									# add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['On-Off ratio single']=wd.DCd[devk].Idonoffratio_T()['Ir']
			data[devk]['|Idmin| single']=wd.DCd[devk].Idmin_T()['I']
			data[devk]['|Idmax| single']=wd.DCd[devk].Idmax_T()['I']
			haveadevice=True
		if haveadevice:																# if we have one or more valid devices for this measurement then include the parameters for the data set
			if '|Idmax| single' not in hheaders: hheaders.append('|Idmax| single')
			if 'On-Off ratio single' not in hheaders: hheaders.append('On-Off ratio single')
			if '|Idmin| single' not in hheaders: hheaders.append('|Idmin| single')
#######################done getting |Idmax| single, on-off ratio single, and |Idmin| single #####################################################
########### Get the minimum |Id| from a dual-swept (first sweep) transfer curve #####################################################################
	haveadevice = False
	for devk in selecteddevices:
		if len(wd.DCd[devk].Idmin_TF())>0:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['|Idmin| dual 1st'] = wd.DCd[devk].Idmin_tf
			haveadevice = True
		if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
			if '|Idmin| dual 1st' not in hheaders: hheaders.append('|Idmin| dual 1st')
#######################done getting |Idmin| dual 1st| #####################################################
########### Get the minimum |Id| from a dual-swept (2nd sweep) transfer curve  #####################################################################
	haveadevice = False
	for devk in selecteddevices:
		if len(wd.DCd[devk].Idmin_TR())>0:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['|Idmin| dual 2nd'] = wd.DCd[devk].Idmin_tr
			haveadevice = True
		if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
			if '|Idmin| dual 2nd' not in hheaders: hheaders.append('|Idmin| dual 2nd')
#######################done getting |Idmin| dual 2nd| #####################################################
########### Get the actual Vgs slew rate from a dual-swept (one loop) transfer curve  #####################################################################
	haveadevice = False
	for devk in selecteddevices:
		if hasattr(wd.DCd[devk],"Vgsslew_IVtfr") and wd.DCd[devk].Vgsslew_IVtfr!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['Vgsslew transfer 1loop'] = wd.DCd[devk].Vgsslew_IVtfr
			haveadevice = True
		if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
			if 'Vgsslew transfer 1loop' not in hheaders: hheaders.append('Vgsslew transfer 1loop')
#######################done getting dual-swept (one loop) Vgs| #####################################################
########### Get the minimum |Id| from a 4-swept (3rd sweep) transfer curve  #####################################################################
	haveadevice = False
	for devk in selecteddevices:
		if len(wd.DCd[devk].Idmin_T3())>0:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['|Idmin| four 3rd'] = wd.DCd[devk].Idmin_t3
			haveadevice = True
		if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
			if '|Idmin| four 3rd' not in hheaders: hheaders.append('|Idmin| four 3rd')
#######################done getting |Idmin| dual 2nd| #####################################################
########### Get the minimum |Id| from a 4-swept (4th sweep) transfer curve  #####################################################################
	haveadevice = False
	for devk in selecteddevices:
		if len(wd.DCd[devk].Idmin_T4())>0:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['|Idmin| four 4th'] = wd.DCd[devk].Idmin_t4
			haveadevice = True
		if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
			if '|Idmin| four 4th' not in hheaders: hheaders.append('|Idmin| four 4th')
#######################done getting |Idmin| dual 2nd| #####################################################
########### Get the actual Vgs slew rate from a 4-swept (two loop) transfer curve  #####################################################################
	haveadevice = False
	for devk in selecteddevices:
		if hasattr(wd.DCd[devk],"Vgsslew_IVt2loop") and wd.DCd[devk].Vgsslew_IVt2loop!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['Vgsslew transfer 2loop'] = wd.DCd[devk].Vgsslew_IVt2loop
			haveadevice = True
		if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
			if 'Vgsslew transfer 2loop' not in hheaders: hheaders.append('Vgsslew transfer 2loop')
#######################done getting dual-swept (two loop) Vgs slew rate #####################################################

########### Get Ron at Vds=0V (from family of curves)#########################################################
	haveadevice=False															# flag to see if at least one valid device exists for this measurement
	for devk in selecteddevices:
		r=wd.DCd[devk].Ron_foc(fractVdsfit=fractVdsfit)
		if len(r)>0:
			if devk not in data: data[devk]={}									# add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			if len(r['R'])==1: data[devk]['Ron']=r['R'][0]						# then this is likely a special structure like a probe resistance monitor
			else: data[devk]['Ron']=r['R'][iVgs]
			haveadevice=True
		if haveadevice:															# if we have one or more valid devices for this measurement then include the parameters for the data set
			if 'Ron' not in hheaders: hheaders.append('Ron')
########################## done getting Ron ###################################################################

########### Get |Idmax|FOC from family of curves#########################################################
	haveadevice=False															# flag to see if at least one valid device exists for this measurement
	for devk in selecteddevices:
		r=wd.DCd[devk].Idmax_foc(Vds=Vds_foc)
		if r!=None:
			if devk not in data: data[devk]={}							# add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			#if len(r)==1: data[devk]['|Idmax|FOC']=max(np.abs(r[0]))		# then this is likely a special structure like a probe resistance monitor OR a regular FET device with FOC at just one Vgs
			data[devk]['|Idmax(Vds)|FOC']=r
			haveadevice=True
		if haveadevice:													# if we have one or more valid devices for this measurement then include the parameters for the data set
			if '|Idmax(Vds)|FOC' not in hheaders: hheaders.append('|Idmax(Vds)|FOC')
########################## done getting |Idmax|FOC ###################################################################

########### Get the maximum |Ig| i,e, |Igmax| from the single-swept transfer curve #####################################################################
	haveadevice=False
	for devk in selecteddevices:
		if len(wd.DCd[devk].Ig_T())>0:
			if devk not in data: data[devk]={}									# add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['|Igmax| single']=max(np.abs(wd.DCd[devk].Ig_IVt))
			haveadevice=True
		if haveadevice:														# if we have one or more valid devices for this measurement then include the parameters for the data set
			if '|Igmax| single' not in hheaders: hheaders.append('|Igmax| single')
#######################done getting |Igmax| #####################################################

########### Get ft from the S-parameter data #####################################################################
	haveadevice=False															# flag to see if at least one valid device exists for this measurement
	for devk in selecteddevices:
		if wd.DCd[devk].ft()!=None:
			if devk not in data: data[devk]={}									# add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['ft']=wd.DCd[devk].ft()
			#data[devk]['fmax']=wd.DCd[devk].fmax()
			haveadevice=True
		if haveadevice:														# if we have one or more valid devices for this measurement then include the parameters for the data set
			if 'ft' not in hheaders: hheaders.append('ft')
			#if 'fmax' not in hheaders: hheaders.append('fmax')
#######################done getting ft #####################################################
########### Get fmax from the S-parameter data #####################################################################
	haveadevice=False															# flag to see if at least one valid device exists for this measurement
	for devk in selecteddevices:
		if wd.DCd[devk].fmax()!=None:
			if devk not in data: data[devk]={}									# add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			#data[devk]['ft']=wd.DCd[devk].ft()
			data[devk]['fmax']=wd.DCd[devk].fmax()
			haveadevice=True
		if haveadevice:														# if we have one or more valid devices for this measurement then include the parameters for the data set
			#if 'ft' not in hheaders: hheaders.append('ft')
			if 'fmax' not in hheaders: hheaders.append('fmax')
#######################done getting fmax #####################################################

########### Get RF Gm and RF Go at the specified frequency, from the S-parameter data #####################################################################
# RF Go is the output (drain) conductance at the selected frequency = selectedfrequency
# TODO: develop ability to select the frequency of RF Gm from the menu. For now, use the frequency closest to 1.5GHz
	selectedfrequency=1.5E9
	haveadevice = False  # flag to see if at least one valid device exists for this measurement
	# for devk in selecteddevices:			# get a device which has S-parameter data and find the frequency index of the selected frequency. Assumes all devices which have S-parameters were measured at the same frequencies
	# 	if wd.DCd[devk].sfrequencies()!=None:
	# 		ifreq = min(range(len(wd.DCd[selecteddevices[0]].sfrequencies())), key=lambda i: abs(wd.DCd[selecteddevices[0]].sfrequencies()[i] - selectedfrequency))
	# 		break
	for devk in selecteddevices:
		if len(wd.DCd[devk].RFGm())>0:
			ifreq = min(range(len(wd.DCd[devk].sfrequencies())), key=lambda i: abs(wd.DCd[devk].sfrequencies()[i] - selectedfrequency))     # find RF Gm at the selected frequency
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['RFGm'] = wd.DCd[devk].rfgm[ifreq]
			data[devk]['Vgs_spar'] = wd.DCd[devk].Vgs_spar
			data[devk]['Id_spar']=wd.DCd[devk].Id_spar
			if 'RFGm' not in hheaders: hheaders.append('RFGm')
			haveadevice = True
		if len(wd.DCd[devk].RFGo())>0:
			ifreq = min(range(len(wd.DCd[devk].sfrequencies())), key=lambda i: abs(wd.DCd[devk].sfrequencies()[i] - selectedfrequency))     # find RF Gm at the selected frequency
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['RFGo']  = wd.DCd[devk].rfgo[ifreq]
			data[devk]['Vgs_spar'] = wd.DCd[devk].Vgs_spar
			data[devk]['Id_spar']=wd.DCd[devk].Id_spar
			if 'RFGo' not in hheaders: hheaders.append('RFGo')
			haveadevice = True
		if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
			if 'Vgs_spar' not in hheaders: hheaders.append('Vgs_spar')
			if 'Id_spar' not in hheaders: hheaders.append('Id_spar')
#######################done getting RFGm #####################################################
########### Get 50ohm noisefigure parameters, from the S-parameter data and raw noisefigure at 50ohms data #####################################################################
	haveadevice = False  # flag to see if at least one valid device exists for this measurement
	for devk in selecteddevices:
		if len(wd.DCd[devk].get_NF50())>0:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['Fmin50average'] = wd.DCd[devk].Fmin50average
			data[devk]['Fmin50lowest'] = wd.DCd[devk].Fmin50lowest
			data[devk]['freqFmin50lowest'] = wd.DCd[devk].freqFmin50lowest
			data[devk]['gainFmin50average']=wd.DCd[devk].gainFmin50average
			data[devk]['gainFmin50lowest']=wd.DCd[devk].gainFmin50lowest
			haveadevice = True
		if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
			if 'Fmin50average' not in hheaders: hheaders.append('Fmin50average')
			if 'Fmin50lowest' not in hheaders: hheaders.append('Fmin50lowest')
			if 'freqFmin50lowest' not in hheaders: hheaders.append('freqFmin50lowest')
			if 'gainFmin50average' not in hheaders: hheaders.append('gainFmin50average')
			if 'gainFmin50lowest' not in hheaders: hheaders.append('gainFmin50lowest')
#######################done getting noisefigure at 50ohms #####################################################
########### Get tuned noise parameters #####################################################################
	haveadevice = False  # flag to see if at least one valid device exists for this measurement
	for devk in selecteddevices:
		if len(wd.DCd[devk].get_noise_parameters())>0:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['FmindB_lowest'] = wd.DCd[devk].NPmin['FmindB']                 # minimum value of Fmin in dB from across the measured frequency range of tuned noise parameters
			data[devk]['freq_Fmin_lowest'] = wd.DCd[devk].NPmin['frequency']            # frequency having the minimum value of Fmin in dB from across the measured frequency range of tuned noise parameters
			data[devk]['Assoc_gain_Fmin_lowest']=wd.DCd[devk].NPmin['GassocdB']         # Associated gain at the frequency having the minimum value of Fmin in dB from across the measured frequency range of tuned noise parameters
			data[devk]['Rn_Fmin_lowest']=wd.DCd[devk].NPmin['Rn']                       # noise resistance at the frequency having the minimum value of Fmin in dB from across the measured frequency range of tuned noise parameters
			data[devk]['Vgs_noiseparameters']=wd.DCd[devk].Vgs_noise_parameters         # Vgs of tuned noise parameters
			data[devk]['Id_noiseparameters']=wd.DCd[devk].Id_noise_parameters         # Vgs of tuned noise parameters
			#data[devk]['Goptmag_Fmin_lowest'] = wd.DCd[devk].NPmin['gopt'].real                 # minimum value of Fmin in dB from across the measured frequency range of tuned noise parameters
			haveadevice = True
		if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
			if 'FmindB_lowest' not in hheaders: hheaders.append('FmindB_lowest')
			if 'freq_Fmin_lowest' not in hheaders: hheaders.append('freq_Fmin_lowest')
			if 'Assoc_gain_Fmin_lowest' not in hheaders: hheaders.append('Assoc_gain_Fmin_lowest')
			if 'Rn_Fmin_lowest' not in hheaders: hheaders.append('Rn_Fmin_lowest')
			if 'Vgs_noiseparameters' not in hheaders: hheaders.append('Vgs_noiseparameters')
			if 'Id_noiseparameters' not in hheaders: hheaders.append('Id_noiseparameters')
#######################done getting noisefigure at 50ohms #####################################################



##################### Get Vgs and Ids for the given S-parameter measurement

########### Get the maximum gm from the single-swept transfer curves #####################################################################
	haveadevice=False															# flag to see if at least one valid device exists for this measurement
	if len(selecteddevices)>0:												# did any devices pass the filter?
		for devk in selecteddevices:										# devk is the device key and also the device name
			gmmax=wd.DCd[devk].gmmax_T()									# see if data exists for this device
			if len(gmmax)>0:														# add data only if it exists
				if devk not in data: data[devk]={}									# add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
				data[devk]['gmmax single']=gmmax['G']				# get the maximum Gm
				haveadevice=True
		if haveadevice:														# if we have one or more valid devices for this measurement then include the parameters for the data set
			if 'gmmax single' not in hheaders: hheaders.append('gmmax single')
#######################done getting maximum gm from single-swept transfer curve  #####################################################
########### Get TLM parameters from the family of curves #####################################################################
	if wd.get_parametersTLM(fractVdsfit=fractVdsfit,Vgs_selected=Vgs,minTLMlength=minTLMlength,maxTLMlength=maxTLMlength,linearfitquality_request=linearfitquality_request):
		haveadevice=False
		for devk in selecteddevices:
			if wd.DCd[devk].Rc_TLM!=None:								# does this device have TLM data? i.e. is it a part of a valid TLM structure?
				if devk not in data: data[devk]={}									# add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
				data[devk]['Rc TLM']=wd.DCd[devk].Rc_TLM
				data[devk]['Rsh TLM']=wd.DCd[devk].Rsh_TLM
				haveadevice=True
		if haveadevice:														# if we have one or more valid devices for this measurement then include the parameters for the data set
			if 'Rc TLM' not in hheaders: hheaders.append('Rc TLM')
			if 'Rsh TLM' not in hheaders: hheaders.append('Rsh TLM')
#######################done getting maximum gm from single-swept transfer curve  #####################################################

##########################################################################################################################################################################################################################
########### Get ORTH parameters - i.e. ratios |Idmax|, in aligned and orthogonal to cnt structures from the family of curves and/or single-swept transfer curves respectively ######################
	if wd.get_parametersORTHO(fractVdsfit=fractVdsfit, Vgs_selected=Vgs):
		haveadevice=False
		for devk in selecteddevices:
			if wd.DCd[devk].ratioIdmax!=None:
				if devk not in data: data[devk]={}									# add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
				data[devk]['ORTHRatio |Idmax| single']=wd.DCd[devk].ratioIdmax
				haveadevice=True
		if haveadevice:														# if we have one or more valid devices for this measurement then include the parameters for the data set
			if 'ORTHRatio |Idmax| single' not in hheaders: hheaders.append('ORTHRatio |Idmax| single')
##########################################################################################################################################################################################################################
########### Get ORTH parameter - i.e. ratios |Idmax| first sweep, in aligned and orthogonal to cnt structures from the dual-swept transfer curves respectively ######################
	if wd.get_parametersORTHO(fractVdsfit=fractVdsfit, Vgs_selected=Vgs):
		haveadevice = False
		for devk in selecteddevices:
			if wd.DCd[devk].ratioIdmaxF!=None:
				if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
				data[devk]['ORTHRatio |Idmax| dual 1st'] = wd.DCd[devk].ratioIdmaxF
				haveadevice = True
		if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
			if 'ORTHRatio |Idmax| dual 1st' not in hheaders: hheaders.append('ORTHRatio |Idmax| dual 1st')
##########################################################################################################################################################################################################################
########### Get ORTH parameter - i.e. ratios |Idmax| 2nd sweep, in aligned and orthogonal to cnt structures from the dual-swept transfer curves respectively ######################
	if wd.get_parametersORTHO(fractVdsfit=fractVdsfit, Vgs_selected=Vgs):
		haveadevice = False
		for devk in selecteddevices:
			if wd.DCd[devk].ratioIdmaxR!=None:
				if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
				data[devk]['ORTHRatio |Idmax| dual 2nd'] = wd.DCd[devk].ratioIdmaxR
				haveadevice = True
		if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
			if 'ORTHRatio |Idmax| dual 2nd' not in hheaders: hheaders.append('ORTHRatio |Idmax| dual 2nd')
##########################################################################################################################################################################################################################
########### Get ORTH parameters - i.e. ratios of on resistances in aligned and orthogonal to cnt structures from the family of curves and/or single-swept transfer curves respectively ######################
	if wd.get_parametersORTHO(fractVdsfit=fractVdsfit, Vgs_selected=Vgs):
		haveadevice=False
		for devk in selecteddevices:
			if wd.DCd[devk].ratioRon!=None:
				if devk not in data: data[devk]={}									# add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
				data[devk]['ORTHRatio Ron']=wd.DCd[devk].ratioRon
				haveadevice=True
		if haveadevice:														# if we have one or more valid devices for this measurement then include the parameters for the data set
			if 'ORTHRatio Ron' not in hheaders: hheaders.append('ORTHRatio Ron')
############################################################################
##########################################################################################################################################################################################################################
########### Get |Idmax| for the first (forward) sweep of the dual transfer curve
	haveadevice=False
	for devk in selecteddevices:
		if len(wd.DCd[devk].Idmax_TF())>0:
			if devk not in data: data[devk]={}									# add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['|Idmax| dual 1st']=wd.DCd[devk].Idmax_tf
			haveadevice=True
	if haveadevice:														# if we have one or more valid devices for this measurement then include the parameters for the data set
		if '|Idmax| dual 1st' not in hheaders: hheaders.append('|Idmax| dual 1st')
############################################################################
##########################################################################################################################################################################################################################
########### Get |Idmax| for the second (reverse) sweep of the dual transfer curve
	haveadevice=False
	for devk in selecteddevices:
		if len(wd.DCd[devk].Idmax_TR())>0:
			if devk not in data: data[devk]={}									# add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['|Idmax| dual 2nd']=wd.DCd[devk].Idmax_tr
			haveadevice=True
	if haveadevice:														# if we have one or more valid devices for this measurement then include the parameters for the data set
		if '|Idmax| dual 2nd' not in hheaders: hheaders.append('|Idmax| dual 2nd')
############################################################################
##########################################################################################################################################################################################################################
########### Get |Idmax| for the 3rd sweep of the four swept transfer curve
	haveadevice = False
	for devk in selecteddevices:
		if len(wd.DCd[devk].Idmax_T3())>0:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['|Idmax| four 3rd'] = wd.DCd[devk].Idmax_t3
			haveadevice = True
	if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
		if '|Idmax| four 3rd' not in hheaders: hheaders.append('|Idmax| four 3rd')
############################################################################
##########################################################################################################################################################################################################################
########### Get |Idmax| for the 4th sweep of the four swept transfer curve
	haveadevice = False
	for devk in selecteddevices:
		if len(wd.DCd[devk].Idmax_T4())>0:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['|Idmax| four 4th'] = wd.DCd[devk].Idmax_t4
			haveadevice = True
	if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
		if '|Idmax| four 4th' not in hheaders: hheaders.append('|Idmax| four 4th')
############################################################################
##########################################################################################################################################################################################################################
########### Get |Ig| at Vgs of minimum |Id| for the single transfer curve
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].Ig_atIdmin_T()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['|Ig|@|Idmin| single'] = wd.DCd[devk].IgatIdmin_t
			haveadevice = True
	if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
		if '|Ig|@|Idmin| single' not in hheaders: hheaders.append('|Ig|@|Idmin| single')
##########################################################################################################################################################################################################################
##########################################################################################################################################################################################################################
########### Get |Ig| at Vgs of minimum |Id| for the first (forward) sweep of the dual transfer curve
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].Ig_atIdmin_TF()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['|Ig|@|Idmin| dual 1st'] = wd.DCd[devk].IgatIdmin_tf
			haveadevice = True
	if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
		if '|Ig|@|Idmin| dual 1st' not in hheaders: hheaders.append('|Ig|@|Idmin| dual 1st')
############################################################################
##########################################################################################################################################################################################################################
########### Get |Ig| at Vgs of minimum |Id| for the second (reverse) sweep of the dual transfer curve
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].Ig_atIdmin_TR()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['|Ig|@|Idmin| dual 2nd'] = wd.DCd[devk].IgatIdmin_tr
			haveadevice = True
	if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
		if '|Ig|@|Idmin| dual 2nd' not in hheaders: hheaders.append('|Ig|@|Idmin| dual 2nd')
##########################################################################################################################################################################################################################
##########################################################################################################################################################################################################################
########### Get |Igmax| for the single transfer curve
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].Igmax_T()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]["|Igmax| single"] = abs(wd.DCd[devk].Igmax_t)
			haveadevice = True
	if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
		if "|Igmax| single" not in hheaders: hheaders.append("|Igmax| single")
##########################################################################################################################################################################################################################
##########################################################################################################################################################################################################################
########### Get |Igmax| for the first (forward) sweep of the dual transfer curve
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].Ig_atIdmin_TF()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]["|Igmax| dual 1st"] = abs(wd.DCd[devk].Igmax_tf)
			haveadevice = True
	if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
		if "|Igmax| dual 1st" not in hheaders: hheaders.append("|Igmax| dual 1st")
############################################################################
##########################################################################################################################################################################################################################
########### Get |Igmax| for the second (reverse) sweep of the dual transfer curve
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].Ig_atIdmin_TR()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]["|Igmax| dual 2nd"] = abs(wd.DCd[devk].Igmax_tr)
			haveadevice = True
	if haveadevice:  # if we have one or more valid devices for this measurement then include the parameters for the data set
		if '|Igmax| dual 2nd' not in hheaders: hheaders.append('|Igmax| dual 2nd')
##########################################################################################################################################################################################################################
########### Get On-Off ratios for the first (forward) and second (reverse) sweep of the dual transfer curve
	haveadevice=False
	for devk in selecteddevices:
		if len(wd.DCd[devk].Idonoffratio_TF())>0 and len(wd.DCd[devk].Idonoffratio_TR())>0:
			if devk not in data: data[devk]={}									# add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['On-Off ratio dual 1st']=wd.DCd[devk].Idonoffratio_tf
			data[devk]['On-Off ratio dual 2nd']=wd.DCd[devk].Idonoffratio_tr
			haveadevice=True
	if haveadevice:														# if we have one or more valid devices for this measurement then include the parameters for the data set
		if 'On-Off ratio dual 1st' not in hheaders: hheaders.append('On-Off ratio dual 1st')
		if 'On-Off ratio dual 2nd' not in hheaders: hheaders.append('On-Off ratio dual 2nd')

##########################################################################################################################################################################################################################
########### Get maximum hysteresis voltage for the first (forward) and second (reverse) sweep of the dual transfer curve
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].Vhyst12()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['hysteresis voltage 12'] = wd.DCd[devk]._Vhyst12
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if 'hysteresis voltage 12' not in hheaders: hheaders.append('hysteresis voltage 12')
##########################################################################################################################################################################################################################
########### Get maximum hysteresis current for the first (forward) and second (reverse) sweep of the double-swept family of curves
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].get_Idhystfocmax()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['hysteresis foc current'] = wd.DCd[devk].Idhystfocmax
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if 'hysteresis foc current' not in hheaders: hheaders.append('hysteresis foc current')
############################################################################


##########################################################################################################################################################################################################################
# TOI measurements with constant Vgs and Vds
##########################################################################################################################################################################################################################
########### Get output reflection coefficient which gives the maximum output TOI
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].get_reflect_maxTOI()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['reflect max TOI mag'] = wd.DCd[devk].TOI['reflect_mag_maxTOI']
			data[devk]['reflect max TOI ang'] = wd.DCd[devk].TOI['reflect_ang_maxTOI']
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if 'reflect max TOI mag' not in hheaders: hheaders.append('reflect max TOI mag')
		if 'reflect max TOI ang' not in hheaders: hheaders.append('reflect max TOI ang')
############################################################################
##########################################################################################################################################################################################################################
########### Get maximum output TOI
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].get_TOIoutmax()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['TOI maximum'] = wd.DCd[devk].TOI['TOIoutmax']
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if 'TOI maximum' not in hheaders: hheaders.append('TOI maximum')
###########################################################################
##########################################################################################################################################################################################################################
########### Get the maximum gain for the TOI measurement
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].get_TOIoutmax()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['max gain TOI'] = wd.DCd[devk].TOI['DUTmaxgainTOI']
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if 'max gain TOI' not in hheaders: hheaders.append('max gain TOI')
############################################################################
##########################################################################################################################################################################################################################
########### Get output reflection coefficient which gives the maximum gain during the TOI measurement
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].get_reflect_maxgainTOI()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['reflect TOImaxgain mag'] = wd.DCd[devk].TOI['reflect_mag_maxgainTOI']
			data[devk]['reflect TOImaxgain ang'] = wd.DCd[devk].TOI['reflect_ang_maxgainTOI']
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if 'reflect TOImaxgain mag' not in hheaders: hheaders.append('reflect TOImaxgain mag')
		if 'reflect TOImaxgain ang' not in hheaders: hheaders.append('reflect TOImaxgain ang')
############################################################################
##########################################################################################################################################################################################################################
########### Get output TOI at the maximum gain
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].get_TOIoutmax()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['TOI at maximum gain'] = wd.DCd[devk].TOI['TOImaxgain']
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if 'TOI at maximum gain' not in hheaders: hheaders.append('TOI at maximum gain')
############################################################################
##########################################################################################################################################################################################################################
########### Get Vds for TOI measurement
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].get_VdsTOI()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['Vds TOI'] = wd.DCd[devk].TOI['Vds']
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if 'Vds TOI' not in hheaders: hheaders.append('Vds TOI')
############################################################################
##########################################################################################################################################################################################################################
########### Get Vgs for TOI measurement
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].get_VgsTOI()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['Vgs TOI'] = wd.DCd[devk].TOI['Vgs']
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if 'Vgs TOI' not in hheaders: hheaders.append('Vgs TOI')
############################################################################
##########################################################################################################################################################################################################################
########### Get Id for TOI measurement
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].get_IdTOI()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['Id TOI'] = wd.DCd[devk].TOI['Id']
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if 'Id TOI' not in hheaders: hheaders.append('Id TOI')
############################################################################
	##########################################################################################################################################################################################################################
########### Get Ig for TOI measurement
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].get_IgTOI()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['Ig TOI'] = wd.DCd[devk].TOI['Ig']
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if 'Ig TOI' not in hheaders: hheaders.append('Ig TOI')
############################################################################
##########################################################################################################################################################################################################################
########### Get maximum TOI from TOI vs Vgs calculated from 3rd harmonic measurements at low RF frequency
	haveadevice = False
	for devk in selecteddevices:
		if wd.DCd[devk].get_TOIHARM()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk]['TOI HARM'] = wd.DCd[devk].HARM['TOImax']
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if 'TOI HARM' not in hheaders: hheaders.append('TOI HARM')
###################################################################################################################################################################################################################################
###################################################################################################################################################################################################################################

##############################################################################################################################################
# TOI tests measured using swept Vgs
##############################################################################################################################################
# get output TOI which is maximum for all measured TOI for this device (over all measured output reflections and all measured Vgs values of the Vgs sweep)
	haveadevice=False
	datakey='TOImax_Vgswept'
	for devk in selecteddevices:
		if wd.DCd[devk].get_TOImaxVgsswept()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk][datakey] = wd.DCd[devk].TOIVgsswept['TOImax']
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if datakey not in hheaders: hheaders.append(datakey)
############################################################################
##############################################################################################################################################
# get associated output reflection coefficient for the output TOI which is maximum for all measured TOI for this device (over all measured output reflections and all measured Vgs values of the Vgs sweep)
	haveadevice=False
	datakeymag='reflect_mag_maxTOI_Vgsswept'
	datakeyang='reflect_ang_maxTOI_Vgsswept'
	for devk in selecteddevices:
		if wd.DCd[devk].get_TOImaxVgsswept()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk][datakeymag] = wd.DCd[devk].TOIVgsswept['reflect_mag_maxTOI']
			data[devk][datakeyang] = wd.DCd[devk].TOIVgsswept['reflect_ang_maxTOI']
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if datakeymag not in hheaders: hheaders.append(datakeymag)
		if datakeyang not in hheaders: hheaders.append(datakeyang)
############################################################################
##########################################################################################################################################################################################################################
# get associated gain (dB) for the output TOI which is maximum for all measured TOI for this device (over all measured output reflections and all measured Vgs values of the Vgs sweep)
	haveadevice=False
	datakey='gainatmaxTOI_Vgsswept'
	for devk in selecteddevices:
		if wd.DCd[devk].get_TOImaxVgsswept()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk][datakey] = wd.DCd[devk].TOIVgsswept['gainatmaxTOI']
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if datakey not in hheaders: hheaders.append(datakey)
############################################################################
##########################################################################################################################################################################################################################
# get associated gain (dB) for the output TOI which is maximum for all measured TOI for this device (over all measured output reflections and all measured Vgs values of the Vgs sweep)
	haveadevice=False
	datakey='Max_TOI-Pdc_Vgsswept'
	for devk in selecteddevices:
		if wd.DCd[devk].get_TOImaxVgsswept()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk][datakey] = wd.DCd[devk].TOIVgsswept['Max_TOI-Pdc']
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if datakey not in hheaders: hheaders.append(datakey)
############################################################################
##########################################################################################################################################################################################################################
# get associated gain (dB) for the output TOI which is maximum for all measured TOI for this device (over all measured output reflections and all measured Vgs values of the Vgs sweep)
	haveadevice=False
	datakey='Max_TOI-Pdc_Vgsswept'
	for devk in selecteddevices:
		if wd.DCd[devk].get_TOImaxVgsswept()!=None:
			if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
			data[devk][datakey] = wd.DCd[devk].TOIVgsswept['Max_TOI-Pdc']
			haveadevice = True
	if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
		if datakey not in hheaders: hheaders.append(datakey)
############################################################################
###################################################################################################################################################################################################################################
# perform Y-function analysis only if requested by user
	if performYf:
	# get Vgs threshold
		haveadevice=False
		datakey='Vth'
		for devk in selecteddevices:
			if wd.DCd[devk].Vth_YT()!=None:
				if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
				data[devk][datakey] = wd.DCd[devk].Vth_YT()
				haveadevice = True
		if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
			if datakey not in hheaders: hheaders.append(datakey)

	###############
	# get drain current at Vgs = Vgs threshold + user specified Vgs offset (deltaVgs)
		haveadevice=False
		datakey_Id='Idatthres+dVgs'
		datakey_Ron='Ronatthres+dVgs'
		for devk in selecteddevices:
			if wd.DCd[devk].Id_atthesholdplusdelta_T_Ronatthesholdplusdelta_T(deltaVgsplusthres=deltaVgsplusthres, fractVgsfit=fractVgsfit)!=None:
				if devk not in data: data[devk] = {}  # add a new subdictionary if and only if this device isn't already in the data dictionary of dictionaries: data[][]
				ret= wd.DCd[devk].Id_atthesholdplusdelta_T_Ronatthesholdplusdelta_T(deltaVgsplusthres=deltaVgsplusthres, fractVgsfit=fractVgsfit)
				data[devk][datakey_Id] = ret['Id']
				data[devk][datakey_Ron] = ret['Ron']
				haveadevice = True
		if haveadevice:  								# if we have one or more valid devices for this measurement then include the parameters for the data set
			if datakey_Id not in hheaders:
				hheaders.append(datakey_Id)
			if datakey_Ron not in hheaders:
				hheaders.append(datakey_Ron)
###################################################################################################################################################################################################################################
###################################################################################################################################################################################################################################
	if len(data)>0:
		return data,hheaders			# return data and column headers
	else: return None