# finds the noise figure and noise parameter of the composite noise meter using previously saved gain-bandwidth product and reflection data
#
from setup_noise_coldsource import *
from read_write_spar_noise_coldsource import *
from get_noisemeter_gainbandwidthproduct import get_noisemeter_gainbandwidthproduct
from calculate_noise_parameters_focus import solvefornoiseparameters, calculate_nffromnp
import numpy as np

rm=visa.ResourceManager()
noisesource=NoiseMeter(rm=rm,ENR=15,preset=True,turnonnoisesourceonly=True)               # ENR is bogus because the noise meter is being used only to drive the noise source
spectrumanalyzer=SpectrumAnalyzer(rm=rm)



################
# get noise parameters and noise figures of composite noise meter
# input parameters
# tunercalfile is the tuner calibration file
#
def get_noisemeter_noiseparameter_coldsource(tunercalfile=None, cascadefiles_port1=None, cascadefiles_port2=None, reflectioncoefficients=None, tunerIP=("192.168.1.31", 23), referencelevel=-50., inputfile_noisemeterdiodedata=None, resolutionbandwidthsetting=1E6, videobandwidthsetting=10, average=2, maxdeltaNF=0.1, Tamb=290):
	# turn off noise source diode since it should be a cold load
	noisesource.noise_sourceonoff(on=False)
	#cascade available 2port networks onto port1 of tuner
	cascaded2port1=None
	cascaded2port2=None
	if cascadefiles_port1!=None and len(cascadefiles_port1)>0:
		for c in cascadefiles_port1:
			if c[1]=='flip':
				cascaded2port1=spar_flip_ports(read_spar(c[0]))  # then flip ports 1 and 2 on this two-port
			else:
				cascaded2port1=read_spar(c[0])                              # don't flip ports
	#cascade available 2port networks onto port2 of tuner
	if cascadefiles_port2!=None and len(cascadefiles_port2)>0:
		for c in cascadefiles_port2:
			if c[1]=='flip':
				cascaded2port2=spar_flip_ports(read_spar(c[0]))  # then flip ports 1 and 2 on this two-port
			else:
				cascaded2port2=read_spar(c[0])                              # don't flip ports
	tuner=FocusTuner(IP=tunerIP,S1=cascaded2port1,S2=cascaded2port2,tunertype='source',tunercalfile=tunercalfile)           # set up the tuner with the tuner calibration file tunerfile S1 is the 2-port on the input side of the tuner and S2 then 2-port on the output (next to DUT) side of the tuner
	nmgb=read_Gnm_gamma(inputfile=inputfile_noisemeterdiodedata)        # read gain-bandwidth product and reflection coefficient data from file
	# normalize to tuner frequencies
	frequenciestuner=sorted([float(f) for f in list(tuner.tuner_data.keys())])      # get tuner frequencies measured in tuner data (MHz)
	frequencies=sorted(list(set(fx for fx in [round(fnm) for fnm in nmgb['frequenciesMHz']] if fx in [round(fd0) for fd0 in frequenciestuner] )))        # get all frequencies, rounded to nearest MHz, which are common to all measurements and the tuner
	# filter data and put in dictionary form
	GB={str(nmgb['frequenciesMHz'][i]):nmgb['GB'][i] for i in range(0,len(nmgb['frequenciesMHz'])) if nmgb['frequenciesMHz'][i] in frequencies}             # GB['frequencyMHz'] is the gain*bandwidth*K*T0 product of the composite noise meter, linear, not dB
	gammanm={str(nmgb['frequenciesMHz'][i]):nmgb['gammanm'][i] for i in range(0,len(nmgb['frequenciesMHz'])) if nmgb['frequenciesMHz'][i] in frequencies}   # gammanm['frequencyMHz'] is the reflection coefficient at the input of the composite noise meter real+jimaginary
	if len(frequencies)==0: raise ValueError("ERROR! no frequencies in common")
	spos=[[int(tuner.getPOS_reflection(frequency=frequencies[0],gamma=complex(rr[0],rr[1]),gamma_format='ma')['pos'].split(",")[0]), int(tuner.getPOS_reflection(frequency=frequencies[0],gamma=complex(rr[0],rr[1]),gamma_format='ma')['pos'].split(",")[1])] for rr in reflectioncoefficients]          # get positions for selected reflection coefficients format int p1,p2
	select_pos=sorted(spos, key=lambda x: (x[0],x[1]))       # sort all tuner positions from lowest to highest positions
	frequencies_str=[str(f) for f in frequencies]           # convert to strings
	Fnm={}              # noise figure of composite noise meter Fnm['frequencyMHz']['tuner position'], linear, not dB
	FnmdB={}              # noise figure of composite noise meter Fnm['frequencyMHz']['tuner position'] in dB
	gammatunerRI={}
	gammatunerMA={}
	noise_interp={}
	#centfreq=round(1E6*(min(frequencies)+max(frequencies))/2)
	#span=round(1E6*(max(frequencies)-min(frequencies)))
	for f in frequencies_str:
		Fnm[f]={}
		FnmdB[f]={}
		gammatunerRI[f]={}
		gammatunerMA[f]={}
		noise_interp[f]={}
	for p in select_pos:
		tuner.setPOS(pos1=p[0],pos2=p[1])   # set the tuner position to select the tuner gamma
		posstr=str(p[0])+','+str(p[1])
		for f in frequencies_str:               # loop through selected frequencies str representing the frequency in MHz
			# get noise (dBm) spectrum
			maxfreq,maxsig,frequencies_sa,noise=spectrumanalyzer.measure_spectrum(numberofaverages=average,centfreq=1E6*int(f),span=100E3,videobandwidth=videobandwidthsetting,resolutionbandwidth=resolutionbandwidthsetting,referencelevel=referencelevel,attenuation=0,preamp=True)
			#frequencies_sa=[int(1E-6*f) for f in frequencies_sa]        # convert spectrum analyzer frequencies from Hz to MHz
			# interpolate the noise spectrum returned by the spectrum analyzer
			#noise_interp={f:{posstr:dBtolin(np.interp(float(f),frequencies_sa,noise))} for f in frequencies_str}           # interpolate noise measurements (dBm) from spectrum analyzer at the selected frequencies (in MHz). Noise measurements are also converted to linear from dBm.
			tun=tuner.get_tuner_reflection_gain(frequency=f,position=",".join([str(p[0]),str(p[1])]))        # get tuner data at frequency f (MHz) and the tuner position defined by the selected reflection coefficient {"gamma_MA","gamma_RI","gain","Spar","frequency","pos"} gain is linear, not in dB
			pos=tun['pos']                       # get the tuner position x,y to use to index parameters such as GaDUT
			noise_interp[f][pos]=dBtolin(np.average(noise))          # get nolse averaged convert to linear
			gammatunerRI[f][pos]=tun['gamma_RI']           # real + jimaginary reflection coefficient presented by tuner to input of composite noise meter
			gammatunerMA[f][pos]=tun['gamma_MA']
			#Fnm[f][pos]=noise_interp[f][pos]*np.square(abs(1-gammatunerRI[f][pos]*gammanm[f]))/(GB[f]*(1-np.square(abs(gammatunerRI[f][pos]))))          # noise figure of composite noise meter, linear not dB
			Fnm[f][pos]=noise_interp[f][pos]*np.square(abs(1-gammatunerRI[f][pos]*gammanm[f]))/(GB[f]*(1-np.square(abs(gammatunerRI[f][pos])))) - Tamb/T0 +1        # noise figure of composite noise meter, linear not dB T0 is the reference temperature = 290K and Tamb is the lab ambient temperature K
	# now solve for the noise parameters of composite noise meter
	videobandwidthactual=spectrumanalyzer.get_videobandwidth()            # get actual video bandwidth of the spectrum analyzer
	resolutionbandwidthactual=spectrumanalyzer.get_resolutionbandwidth()        # get actual resolution bandwidth of the spectrum analyzer
	NPnm={}             # noise parameters of composite noise meter, NP['FmindB'['gammaopt']['Rn'] where FmindB is the minimum noise figure in dB, gammaopt the optimum reflection coefficient presented to the input of the composite noise meter in dB, Rn is the noise resistance in ohms
	NFcalcfromNPnm={}
	for f in frequencies_str:
		NPnm[f]={}
		Fgamma=[[Fnm[f][str(p[0])+','+str(p[1])],gammatunerRI[f][str(p[0])+','+str(p[1])]] for p in select_pos]
		npx=solvefornoiseparameters(Fgamma=Fgamma,type='weighted',maxdeltaNF=maxdeltaNF)
		NPnm[f]['FmindB']=npx[0]
		NPnm[f]['gopt']=npx[1]
		NPnm[f]['Rn']=npx[2]
		NFcalcfromNPnm[f]={str(p[0])+','+str(p[1]):calculate_nffromnp(reflectioncoef=gammatunerRI[f][str(p[0])+','+str(p[1])],noiseparameters=NPnm[f],typedBout=True) for p in select_pos}        # noise figure (dB) from noise parameters
	return {'NPnm':NPnm,'NFcalcfromNP':NFcalcfromNPnm,'NF':Fnm,'gammatunerRI':gammatunerRI,'gammatunerMA':gammatunerMA,'noise':noise_interp,'videobandwidth':videobandwidthactual,'resolutionbandwidth':resolutionbandwidthactual}

