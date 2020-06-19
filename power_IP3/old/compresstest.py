__author__ = 'PMarsh Carbonics'
import visa
import time
#import skrf as rf
from parameter_analyzer import *
#from PyQt4 import QtCore
#from utilities import *

from spectrum_analyzer import *
from rf_sythesizer import *
from IVplot import plotCompression
from compression import PowerCompression
from cascade import CascadeProbeStation                                                    # Cascade wafer prober

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

print("from line 16 compresstest.py",is_number("5"))    #debug

ps=ParameterAnalyzer(rm)
sa=SpectrumAnalyzer(rm)
rf=Synthesizer(rm=rm,syn='A')
Vgsbias = -2.
Vdsbias = -2.
gcomp = 1e-5
dcomp = 50e-3


navg=10                         # number of averages to form measured spectra
fcent = 1.45E9
#fdelta = 100E6
#
# ffa = fcent-fdelta/2
# ffb= fcent+fdelta/2
# fda = ffa-fdelta
# fdb = ffb+fdelta
atten = 20.
#pwrstart = -25.
#pwrstop = -8.
pwrstart = -16.                 # power calibrated to be at input of DUT
pwrstop = -10.
delpwr=2.
#sourcecalfactor=-8.23   # sourcecalfactor is the dB difference between the power meter measured power and that set on the rf synthesizers (A) = dB power meter - dB synthesizer setting (usually negative dB)
#sacalfactor = 3.41       # sacalfactor is dB power meter - dB spectrum analyzer display
#sysTOI=20.

sourcecalfactor=-8.4   # sourcecalfactor is the dB difference between the power meter measured power and that set on the rf synthesizers (A) = dB power meter - dB synthesizer setting (usually negative dB)
sacalfactor = 2.65       # sacalfactor is dB power meter - dB spectrum analyzer display - loss, according to the spectrum analyzer display from the DUT input to the spectrum analyzer - a positive number
maxpower=5

Vgsarray=np.arange(-0.5,-3.25,-0.5)

pathname = "C:/Users/test/python/data/Wf169meas1"

pr = CascadeProbeStation(rm=rm,pathname=pathname,planname="Wf169meas1_plan",opticalcorrectionon="correction off")                                                               # setup Cascade
pr.move_plan_index()					# move to first site

while pr.get_probingstatus()=="probing wafer":
	for Vgsbias in Vgsarray:
		#PC = PowerCompression(synthesizer=rf,spectrumanalyzer=sa,parameteranalyzer=ps,spectrum_analyser_input_attenuation=atten,number_of_averages=navg,powergain_min=pwrstart,powergain_max=pwrstop,powergain_step=delpwr, maxpower=maxpower,comp_step=0.5,frequency=fcent,spectrum_analyzer_cal_factor=sacalfactor,source_calibration_factor=sourcecalfactor,Vgs=Vgsbias,Vds=Vdsbias,Igcomp=gcomp,Idcomp=dcomp)
		PC = PowerCompression(synthesizer=rf,spectrumanalyzer=sa,spectrum_analyser_input_attenuation=atten,number_of_averages=navg,powergain_min=pwrstart,powergain_max=pwrstop,powergain_step=delpwr, maxpower=maxpower,comp_step=0.5,frequency=fcent,spectrum_analyzer_cal_factor=sacalfactor,source_calibration_factor=sourcecalfactor)

		Id,Ig,drainstatus,gatestatus=ps.fetbiason_topgate(Vgsbias, Vdsbias, gcomp, dcomp,timeon=5.)				# bias device again to update currents etc..
		print("Vds, Vgs, Id, Ig, drain status gate status", Vdsbias, Vgsbias, Id, Ig,drainstatus,gatestatus)
		PC.measurePcomp()
		ps.fetbiasoff()
		#PC.writefile_Pcompression(pathname="C:/Users/test/python/waferprobe/data/GaN_April4_2016",wafername="GaN_April4_2016",xloc=0,yloc=0,Id=ps.Id_bias,Vds=ps.Vds_bias,Vgs=ps.Vgs_bias,Ig=ps.Ig_bias,devicename="GaNHEMT1Vgs_-2V",)
		#PC.writefile_Pcompression(pathname="C:/Users/test/python/waferprobe/data/GaN_April4_2016",wafername="GaN_April4_2016",xloc=0,yloc=0,devicename="GaNHEMT2Vgs_-1.5V",)
		PC.writefile_Pcompression(pathname=pathname,wafername=pr.wafername(),xloc=pr.x(),yloc=pr.y(),Id=Id,Vds=Vdsbias,Vgs=Vgsbias,Ig=Ig,devicename=pr.devicename(),devicenamemodifier="_Vds"+formatnum(Vdsbias,precision=1)+"_Vgs"+formatnum(Vgsbias,precision=1))
		#IP3m.writefile_TOI(pathname="C:/Users/test/python/waferprobe/data/Wf166meas3",wafername="system",xloc=27300,yloc=21650,Id=0,Vds=0,Vgs=0,Ig=0,devicename="system",)
		print ("input compression =",PC.inputcompressionpoint)
		print ("output compression =",PC.outputcompressionpoint)
		print ("DUT gain =",PC.DUTgain)
		plotCompression(pin=PC.DUTcompression_pin,pout=PC.DUTcompression_pout, gain=PC.DUTgain, gainm=PC.gainm,inputcompression=PC.inputcompressionpoint,outputcompression=PC.outputcompressionpoint)
