# measure the gain-bandwidth product of the composite noise meter
# measure the preamp noise parameters
# input parameters:
# inputfile_noisemetergamma is the EESOF-formatted .s1p file full pathname for the reflection coefficient of the noise meter
# inputfile_noisesourcegammacold is the EESOF-formatted .s1p file full pathname for the reflection coefficient of the noise diode when off (cold)


from setup_noise_coldsource import *
from read_write_spar_noise_coldsource import *

# measure the gain-bandwidth product of the noisemeter (this is the composite noise meter) hereafter called the NM.
def get_noisemeter_gainbandwidthproduct(noisesource=None, spectrumanalyzer=None, inputfile_noisemetergamma=None, inputfile_noisesourcegammacold=None, inputfile_noisesourcegammahot=None, frequenciesMHz=None, resolutionbandwidthsetting=1E6, videobandwidthsetting=10, average=1, referencelevel=-50):
	# read reflection coefficient file of noisemeter input
	gammanoisemeter=read_spar_1port(sparfilename=inputfile_noisemetergamma)
	# read reflection coefficient file of the noise diode in the off-state
	gammadiodeoff=read_spar_1port(sparfilename=inputfile_noisesourcegammacold)
	# read reflection coefficient file of the noise diode in the on-state
	gammadiodeon=read_spar_1port(sparfilename=inputfile_noisesourcegammahot)
	#frequencies=sorted(list(set(fx for fx in [round(fnm) for fnm in gammanoisemeter['frequency']] if fx in [round(fd0) for fd0 in gammadiodeoff['frequency']] and fx in [round(fd1) for fd1 in gammadiodeon['frequency']] )))        # get all frequencies, rounded to nearest MHz, which are common to all measurements
	# now interpolate all S-parameters to have the same frequency basis
	if min(gammanoisemeter['frequency'])>min(frequenciesMHz) or max(gammanoisemeter['frequency'])<max(frequenciesMHz): raise ValueError("ERROR! frequenciesMHz outside of gamma measurement frequency range of noisemeter input gamma")
	if min(gammadiodeoff['frequency'])>min(frequenciesMHz) or max(gammadiodeoff['frequency'])<max(frequenciesMHz): raise ValueError("ERROR! frequenciesMHz outside of off-state noise source gamma measurement frequency range")
	if min(gammadiodeon['frequency'])>min(frequenciesMHz) or max(gammadiodeon['frequency'])<max(frequenciesMHz): raise ValueError("ERROR! frequenciesMHz outside of on-state noise source gamma measurement frequency range")
	gammanm = {str(f):np.interp(f,gammanoisemeter['frequency'],gammanoisemeter['gamma']) for f in frequenciesMHz}     # interpolate noise meter reflection to frequencies (int MHz) which are common to all gamma measurements
	gammadcold = {str(f):np.interp(f,gammadiodeoff['frequency'],gammadiodeoff['gamma']) for f in frequenciesMHz}     # interpolate off-state diode reflection to frequencies (int MHz) which are common to all gamma measurements
	gammadhot = {str(f):np.interp(f,gammadiodeon['frequency'],gammadiodeon['gamma']) for f in frequenciesMHz}     # interpolate on-state diode reflection to frequencies (int MHz) which are common to all gamma measurements
	# get noise power with the noise source off and on
	noise=get_cold_hot_spectrumanalyzer(spectrumanalyzer=spectrumanalyzer,noisesource=noisesource,average=average,frequenciesMHz=frequenciesMHz,resolutionbandwidthsetting=resolutionbandwidthsetting,videobandwidthsetting=videobandwidthsetting,referencelevelguess=referencelevel)
	# interpolate noise powers from spectrum analyzer to frequencies
	# noise_cold = [np.interp(f,noise['frequenciesMHz'],noise['noisecold']) for f in frequencies]         # noise power with noise diode off
	# noise_hot = [np.interp(f,noise['frequenciesMHz'],noise['noisehot']) for f in frequencies]         # noise power with noise diode on

	noise_cold_mW ={str(f):dBtolin(noise['noisecold'][str(f)]) for f in frequenciesMHz}                # cold diode noise measured at spectrum analyzer in mW
	noise_hot_mW ={str(f):dBtolin(noise['noisehot'][str(f)]) for f in frequenciesMHz}                # cold diode noise measured at spectrum analyzer in mW
	GBnmlin={}
	for f in frequenciesMHz:
		str_f=str(f)
		ENRratio=dBtolin(ENRtablecubicspline(f))         # ENRratio is the diode on-state excess noise ratio (linear not dB) with frequencies (MHz)
		GBnmlin[str_f]=(noise_hot_mW[str_f]-noise_cold_mW[str_f])/(    ( (ENRratio+1)/np.square(abs(1-gammadhot[str_f]*gammanm[str_f])) )-( 1/np.square(abs(1-gammadcold[str_f]*gammanm[str_f])) )   )              # gain-bandwidth product of the noise meter* thermal noise referenced to input of noise meter
	return {'resolutionbandwidthHz':noise['resolutionbandwidth'],'videobandwidthHz':noise['videobandwidth'],'frequencies':frequenciesMHz,'GB':GBnmlin,'gammanm':gammanm,'gammadcold':gammadcold,'gammadhot':gammadhot,'noise_hot_mW':noise_hot_mW,'noise_cold_mW':noise_cold_mW}
