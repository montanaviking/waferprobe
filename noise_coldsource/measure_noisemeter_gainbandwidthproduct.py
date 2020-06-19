# measure the gain-bandwidth product of the noise meter
# writes to file the gain-bandwidth product, reflection coefficient of composite noise meter and reflection coefficient of diode noise source
#from setup_noise_coldsource import *
from obsolete.get_noisemeter_noiseparameter_coldsource_June12_2020 import *

tundir="C:/Users/test/focus_setups/noise/"          # base directory of noise calibrations
#inputcircuitfile=tundir+"noise__coupler_biastee_isolator_April23_2020_SRI.s2p"
#tunercal="c:/Users/test/focus_setups/tunercals_sourcepull/tunercal_1389source_April16_2020_1GHz_1.6GHz_13pts.txt"
inputfile_noisemetergamma=tundir+"1_1.6GHz_noisemetergamma_May21_2020_SRI.s2p"
inputfile_noisesourcegammacold=tundir+"1_1.6GHz_noisediodegammacold_May21_2020_SRI.s2p"
inputfile_noisesourcegammahot=tundir+"1_1.6GHz_noisediodegammahot_May21_2020_SRI.s2p"
outputfilegb=tundir+"1_1.6GHz_gainbandwidth_gamma_June12_2020.xls"
# rm=visa.ResourceManager()
# noisesource=NoiseMeter(rm=rm,ENR=15,preset=True,turnonnoisesourceonly=True)               # ENR is bogus because the noise meter is being used only to drive the noise source
# spectrumanalyzer=SpectrumAnalyzer(rm=rm)

frequencies=[1000,1050,1200,1250,1300,1350,1400,1450,1500,1550,1600]
#frequencies=[1000]

GBnm=get_noisemeter_gainbandwidthproduct(noisesource=noisesource, spectrumanalyzer=spectrumanalyzer, inputfile_noisesourcegammacold=inputfile_noisesourcegammacold, inputfile_noisesourcegammahot=inputfile_noisesourcegammahot, inputfile_noisemetergamma=inputfile_noisemetergamma,
                                        frequenciesMHz=frequencies, average=1, videobandwidthsetting=10)
write_Gnm_gamma(outputfile=outputfilegb,frequencies=GBnm['frequencies'],GB=GBnm['GB'],resolutionbandwidthHz=GBnm['resolutionbandwidthHz'],videobandwidthHz=GBnm['videobandwidthHz'],gammanm=GBnm['gammanm'],gammadcold=GBnm['gammadcold'],gammadhot=GBnm['gammadhot'])