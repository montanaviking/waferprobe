# measure the noise parameters of the composite noise meter using the cold-source method
from writefile_measured import writefile_noiseparameters_coldsource, writefile_noisefigure_coldsource
from get_noisemeter_noiseparameter_coldsource import *

tundir="C:/Users/test/focus_setups/noise/"          # base directory of noise calibrations
inputcircuitfile=tundir+"noise__coupler_biastee_isolator_April23_2020_SRI.s2p"
tunercal="c:/Users/test/focus_setups/tunercals_sourcepull/tunercal_1389source_April16_2020_1GHz_1.6GHz_13pts.txt"
# inputfile_noisemetergamma=tundir+"noisemetergamma.s1p"
# inputfile_noisesourcegammacold=tundir+"noisesourcegammacold.s1p"
# inputfile_noisesourcegammahot=tundir+"noisesourcegammaholt.s1p"
inputfile_noisemeterdiodedata=tundir+"1_1.6GHz_gainbandwidth_gamma_June12_2020.xls"




cascadeport1=[[inputcircuitfile,'noflip']]

#requested_reflections=[[.24,140],[.86,90.5],[.86,49.3],[.2,41.4],[0.81,-.7],[.42,-0.6],[.86,-46.7],[.22,-48.1],[.8,-88.7],[.45,-87.4],[.85,-133.4],[.26,-122.9],[.85,-179.2],[.4,-177.2],[.81,139.9],[.36,89.9],[0.3,180],[0.3,-90],[0,0]]
requested_reflections=[[0,0],[.2,180],[.2,90],[.2,-90],[.2,0],[.5,180],[.5,90],[.5,-90],[.8,180],[.8,90],[.8,-90],[.8,0]]

NPNFnm=get_noisemeter_noiseparameter_coldsource(tunercalfile=tunercal, cascadefiles_port1=cascadeport1, reflectioncoefficients=requested_reflections, inputfile_noisemeterdiodedata=inputfile_noisemeterdiodedata, average=1, maxdeltaNF=500, videobandwidthsetting=10, Tamb=290)
writefile_noiseparameters_coldsource(pathname=tundir,devicename="nmcold_npJune12_2020",NP=NPNFnm['NPnm'],videobandwidth=NPNFnm['videobandwidth'],resolutionbandwidth=NPNFnm['resolutionbandwidth'])
writefile_noisefigure_coldsource(pathname=tundir,devicename="nmcold_nfJune12_2020",NF=NPNFnm['NF'],NFcalcfromNP=NPNFnm['NFcalcfromNP'],gammatunerMA=NPNFnm['gammatunerMA'],noise=NPNFnm['noise'],videobandwidth=NPNFnm['videobandwidth'],resolutionbandwidth=NPNFnm['resolutionbandwidth'])