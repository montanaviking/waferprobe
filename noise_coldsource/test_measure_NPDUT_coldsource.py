# measure the noise parameters of the composite noise meter using the cold-source method
from writefile_measured import writefile_noiseparameters_coldsource, writefile_noisefigure_coldsource
from get_DUTnoiseparameters_coldsource import *

tundir="C:/Users/test/focus_setups/noise/"          # base directory of noise calibrations
inputcircuitfile=tundir+"noise__coupler_biastee_isolator_April23_2020_SRI.s2p"
tunercal="c:/Users/test/focus_setups/tunercals_sourcepull/tunercal_1389source_April16_2020_1GHz_1.6GHz_13pts.txt"
# inputfile_noisemetergamma=tundir+"noisemetergamma.s1p"
# inputfile_noisesourcegammacold=tundir+"noisesourcegammacold.s1p"
# inputfile_noisesourcegammahot=tundir+"noisesourcegammaholt.s1p"
inputfile_noisemeterdiodedata=tundir+"1_1.6GHz_gainbandwidth_gamma_June12_2020.xls"
inputfile_noisemeternoiseparameters=tundir+"nmcold_npJune12_2020_noiseparameter.xls"


cascadeport1=[[inputcircuitfile,'noflip']]
#frequencies=[1050,1150,1250,1350,1450,1550]
frequencies=[1250]


requested_reflections=[ [0.015,-50.368], [0.225,91.200], [0.239,-86.499], [0.275,-177.543], [0.252,-2.691], [0.793,48.837], [0.787,139.588], [0.761,-141.322], [0.849,-46.019] ]
#requested_reflections=[ [0.565,-15.076], [0.548,-5.280], [0.650,-13.081], [0.497,-17.785], [0.579,-20.751], [0.550,-10.343], [0.616,-15.209], [0.532,-15.521], [0.615,-29.355], [0.508,-31.165], [0.396,-8.732], [0.515,5.685], [0.706,-1.744], [0.740,-17.644], [0.373,-29.838], [0.733,-43.510], [0.552,31.969], [0.705,6.512], [0.764,2.375], [0.781,-5.126], [0.643,2.821], [0.712,-7.970] ]

NDUT=get_DUTnoiseparameters_coldsource(cascadefiles_port1=cascadeport1,system_noiseparametersfile=inputfile_noisemeternoiseparameters,reflectioncoefficients=requested_reflections,tunercalfile=tunercal,frequenciesMHz=frequencies,
                                       pna_calset1port="CalSet_2",pna_calset2port="CalSet_1",pna_instrumentstate1port="S22.sta",spectrumanalyzervideobandwidth=10,pna_instrumentstate2port="2port_LF.sta",
                                       inputfile_noisemeterdiodedata=inputfile_noisemeterdiodedata,maxdeltaNF=500,Tamb=290)
writefile_noiseparameters_coldsource(pathname=tundir,devicename="reflectattencoupler_npJune12_2020",NP=NDUT['NP'],videobandwidth=NDUT['videobandwidth'],resolutionbandwidth=NDUT['resolutionbandwidth'])
writefile_noisefigure_coldsource(pathname=tundir,devicename="reflectattencoupler_nfJune12_2020",NF=NDUT['NF'],NFcalcfromNP=NDUT['NFcalcfromNP'],gammatunerMA=NDUT['gammatunerMA'],noise=NDUT['noise'],videobandwidth=NDUT['videobandwidth'],resolutionbandwidth=NDUT['resolutionbandwidth'])