__author__ = 'PMarsh Carbonics'
import visa

from Maury.compression_maury_tuned_with_powermeter import PowerCompressionTunedMaury

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())
#ps=ParameterAnalyzer(rm)
sysdir="C:/Users/test/maury_setups/power/"
tunerfile=sysdir+"1-1.6GHz_longcable_Mar1_2017.tun"
probefile=sysdir+"cascade_RFprobe_APC40-A-GSG_SNJC23F_1-1.6GHz_Jan25_2017_RI_Jan25_2016.s2p"
outputcablefile=sysdir+"output_circuit_biasT_amp_1-1.6GHz_Mar28_2017_SRI.s2p"
cas1=[[probefile,'flip']]
cas2=[[outputcablefile,'noflip']]

Vgsbias = -2.
Vdsbias = -2.5
gcomp = 1e-5
dcomp = 50e-3

navg=10                         # number of averages to form measured spectra
fcent = 1.5E9
fdelta = 100E6
#fspanf = 100E3                 # measurement span for each frequency component of the fundamentals

ffa = fcent-fdelta/2
ffb= fcent+fdelta/2
fda = ffa-fdelta
fdb = ffb+fdelta
atten = 30.
#pwrstart = -25.
#pwrstop = -8.
pwrstart = -20.
pwrstop = -10.
delpwr=2.
#sourcecalfactor=-8.25   # sourcecalfactor is the dB difference between the power meter measured power and that set on the rf synthesizer (A) = dB power meter - dB synthesizer setting (usually negative dB)
sourcecalfactor=-2.14   # sourcecalfactor is the dB difference between the power meter measured power and that set on the rf synthesizer (A) = dB power meter - dB synthesizer setting (usually negative dB)
#sacalfactor = 0.65       # sacalfactor is dB power meter - dB spectrum analyzer display - loss, according to the spectrum analyzer display from the DUT output to the spectrum analyzer - a positive number


pathname = "C:/Users/test/python/data/TOIsys_Mar7_2017"
#SDUT=pathname+"/mismatch_Mar13_2017_SRI.s2p"
SDUT=pathname+"/coaxthru_Mar22_2017_SRI.s2p"
Cp=PowerCompressionTunedMaury(rm=rm, tunerfile=tunerfile, cascadefiles_port1=cas1, cascadefiles_port2=cas2, powerlevellinear_min=pwrstart, powerlevellinear_max=pwrstop, powerlevel_step=delpwr, source_calibration_factor=sourcecalfactor, maxpower=10, comp_fillin_step=1)
#reflections=[[0,0],[.4,0.],[.4,90.],[.5,0.],[.5,90.],[.6,0.],[.6,90.],[.6,180.],[.7,0.],[.7,90.],[.8,0],[.8,180]]
reflections=[[0,0]]
#Cp.gain_vs_outputreflection(output_reflection=reflections,RFinputpower=0,frequency=fcent,DUTSparfile=SDUT)
#Cp.writefile_Pgain(pathname=pathname,wafername="",xloc=0,yloc=0,Id=0,Vds=0,Vgs=0,Ig=0,devicename="system")
#Cp.measurePcomp(output_reflection=reflections,frequency=fcent,Vgs=0,Vds=0,draincomp=0.04,gatecomp=0.01,maxiterations=20)
Cp.measurePcomp(output_reflection=reflections,frequency=fcent,maxiterations=20)
Cp.writefile_Pcompression_tuned(pathname=pathname,wafername="",xloc=0,yloc=0,devicename="systemfull")

