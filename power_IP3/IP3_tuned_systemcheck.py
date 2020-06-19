__author__ = 'PMarsh Carbonics'
import visa

from Maury.IP3_tuned import IP3_Tuned

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())
#ps=ParameterAnalyzer(rm)
sysdir="C:/Users/test/maury_setups/power/"
tunerfile=sysdir+"1-1.6GHz_longcable_Mar1_2017.tun"
probefile=sysdir+"cascade_RFprobe_APC40-A-GSG_SNJC23F_1-1.6GHz_Jan25_2017_RI_Jan25_2016.s2p"
outputcablefile=sysdir+"IOPoutputcable_Mar6_2017_SRI.s2p"
cas1=[[probefile,'flip']]
cas2=[[outputcablefile,'noflip']]

Vgsbias = -2.
Vdsbias = -2.5
gcomp = 1e-5
dcomp = 50e-3

navg=10                         # number of averages to form measured spectra
fcent = 1.5E9
fdelta = 4E6
#fspanf = 100E3                 # measurement span for each frequency component of the fundamentals

ffa = fcent-fdelta/2
ffb= fcent+fdelta/2
fda = ffa-fdelta
fdb = ffb+fdelta
atten = 10.
#pwrstart = -25.
#pwrstop = -8.
pwrstart = -30.
pwrstop = -20.
delpwr=5.
#sourcecalfactor=-8.54   #input probe loss=-0.08dB @ 1.5GHz sourcecalfactor is the dB difference between the power meter measured power and that set on the rf synthesizer (A) = dB power meter - dB synthesizer setting (usually negative dB)
#sacalfactor = 0.65       # sacalfactor is dB power meter - dB spectrum analyzer display - loss, according to the spectrum analyzer display from the DUT output to the spectrum analyzer - a positive number
#sourcecalfactor=-8.27   # sourcecalfactor is the dB difference between the power meter measured power and that set on the rf synthesizers (A) = dB power meter - dB synthesizer setting (usually negative dB)
#sacalfactor = 3.3       # sacalfactor is dB power meter - dB spectrum analyzer display
sysTOI=85.

pathname = "C:/Users/test/python/data/TOIsys_Mar7_2017"
IP3tuned = IP3_Tuned(rm=rm, tunerfile=tunerfile, cascadefiles_port1=cas1, cascadefiles_port2=cas2, spectrum_analyser_input_attenuation=atten, number_of_averages=navg, powerlevel_start=pwrstart ,powerlevel_stop=pwrstop ,powerlevel_step=delpwr, center_frequency=fcent, frequency_spread=fdelta,spectrum_analyzer_cal_factor=sacalfactor, source_calibration_factor=sourcecalfactor,system_TOI=sysTOI)
reflections=[[.6,0.]]
IP3tuned.measureTOI(output_reflection=reflections, fractlinfitlower=0., fractlinearfitupper=1., plotgraphs=True)
IP3tuned.writefile_TOI(pathname=pathname,wafername="",xloc=0,yloc=0,Id=0,Vds=0,Vgs=0,Ig=0,devicename="system")
##IP3m.writefile_TOI(pathname="C:/Users/test/python/waferprobe/data/Wf166meas3",wafername="system",xloc=27300,yloc=21650,Id=0,Vds=0,Vgs=0,Ig=0,devicename="system",)


