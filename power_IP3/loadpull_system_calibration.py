from scipy.interpolate import CubicSpline
# parameters for loadpull system calibration
#sysdir="C:/Users/test/focus_setups/power/July17_2018/RF/"          # base directory of loadpull calibrations
#probefile=sysdir+"KP2GC_May4_2018_SRI.s2p"
sysdir="C:/Users/test/python/data/RFamptests1/RF/"          # base directory of noise calibrations
#probefile=sysdir+"KP2GC_May4_2018_SRI.s2p"                                                 # right side probe

tunerinputcable=sysdir+"RFamptests1__input_isolator+cable_SRI.s2p"                           # noise figure
#tuneroutputcable=sysdir+"TOI_outputcablebiastee_oct23_2019_SRI.s2p"        # for TOI tests
#tuneroutputcable=sysdir+"outputbiastee_TOI50ohms_Aug7_2019_SRI.s2p"        # for TOI tests
#tunerinputcable=sysdir+"noise_biasteeinputcouplerisolator_oct11_2019_SRI.s2p"
#tuneroutputcable=sysdir+"JC2G4_Oct9_2019_SRI.s2p"           # this is the probe on the left side
#tuneroutputcable=sysdir+"JC2G4_May4_2018_SRI.s2p"           # this is the probe on the left side
#tuneroutputcable=sysdir+"noise_outputcableport2_oct11_2019_SRI.s2p"           # this is coupler on the right side of the tuner
#tuneroutputcable=sysdir+"mismatch_Oct10_2019_SRI.s2p"           # this is a cable on the right side of the tuner
#tuneroutputcable=sysdir+"outputbiastee_P1dB_Oct14_2018__biastee_SRI.s2p"        # for compression tests

# 1.5GHz TOI measurements
powermeterAcalfactor=97.6               # power meter A calibration factor at 1.5GHz

#sourcecalfactor=-21.6                    # used only in Focus/IP3_focus_tuned.py = PinDUT-Ppowermeter in dB, PinDUT coaxial
sourcecalfactor=-11.83-0.07                    # units dB, used for TOI measurements PinDUT-Ppowermeter in dB, PinDUT coaxial
sacalfactor = 0.85       # TOI sacalfactor is dB power meter - dB spectrum analyzer display - i.e. the difference between what the power meter reads and the spectrum analyzer reading
Tcold=290               # ambient equivalent noise temperature of noise source in off state in degrees K
#sacalfactor = 0.98
#outputcalfactoruntunedTOI=1.76              # dB loss from DUT to spectrum analyzer at 1500MHz - used only in untuned TOI measurements = positive number for loss
# analyzer reads - usually a positive number


# harmonic low-frequency RF measurements
# PowersensorA calfactor 170MHz =98.68%, 340MHz calfactor 98.2%, 510MHz calfactor=97.8
sacalfactor1st= 0.75            # sacalfactor1st is dB power meter - dB spectrum analyzer display at the fundamental - i.e. the difference between what the power meter reads and the spectrum
# analyzer reads - usually a positive number
sacalfactor2nd= 0.74            # sacalfactor2nd is dB power meter - dB spectrum analyzer display at the 2nd harmonic - i.e. the difference between what the power meter reads and the spectrum
# analyzer reads - usually a positive number
sacalfactor3rd= 0.73             # sacalfactor3rd is dB power meter - dB spectrum analyzer display at the 3rd harmonic - i.e. the difference between what the power meter reads and the spectrum
# analyzer reads - usually a positive numbe
outputloss1st= -0.5-0.02             # gain of the output bias Tee+cables + probe connecting the DUT output to the spectrum analyzer, at the fundamental frequency
outputloss2nd= -0.63-0.02             # gain of the output bias Tee+cables + probe connecting the DUT output to the spectrum analyzer, at the 2nd harmonic frequency
outputloss3rd= -0.753-0.02             # gain of the output bias Tee+cables + probe connecting the DUT output to the spectrum analyzer, at the 3rd harmonic frequency

sourcecalfactorharmonic = -11.64              # = fundamental frequency DUT input power dBm - RF source power setting used for harmonic measurements

outputcalfactorharmonic_1st=sacalfactor1st-outputloss1st       # calibration factor = DUT output - spectrum analyser reading for fundamental frequency. Used for harmonic generation measurements
outputcalfactorharmonic_2nd=sacalfactor2nd-outputloss2nd       # calibration factor = DUT output - spectrum analyser reading for 2nd harmonic frequency. Used for harmonic generation measurements
outputcalfactorharmonic_3rd=sacalfactor3rd-outputloss3rd        # calibration factor = DUT output - spectrum analyser reading for 3rd harmonic frequency. Used for harmonic generation measurements
##################
#
# source_calibration_factor=-2.79    # PinDUT- input synthesizer (A) power setting (accounting for 0.07dB probe loss)
# input_sensor_calfactor=0.26      # sensor A - PinDUT (accounting for 0.07dB probe loss)


# volttocurrentcalibrationfactor is the factor used to convert the channel2 oscilloscope voltage to drain current. Units are amps/volt where volt is the displayed voltage on the oscilloscope and
#  amps is the drain current. The default value, 6.6225E-3, is valid for Rdrain (drain resistor in test setup) = 1.8ohm and the differential probe amp gain set to 100.
#volttocurrentcalibrationfactor=6.5763E-3   # for 100X differential amp gain setting
#volttocurrentcalibrationfactor=5.571338E-3   # for 100X differential amp gain setting
volttocurrentcalibrationfactor=5.555E-3   # for 100X differential amp gain setting units A/V amps per volt on the oscilloscope scale
#volttocurrentcalibrationfactor=66.336E-3   # for 10X differential amp gain setting


################3
# ENR table for HP346B, SN 2330A03414 calibrated Dec 4, 2019 by Tektronix
ENRtablefreqMHz = {"10":15.63,"100":15.60,"1000":15.43,"2000":15.34,"3000":15.13,"4000":15.11,"5000":15.15,"6000":15.10,"7000":15.44,"8000":15.43,"9000":15.55,"10000":15.40,"11000":15.42,"12000":15.38,"13000":15.22,"14000":15.07,"15000":15.10,"16000":15.24,"17000":15.39,"18000":15.47}
ENRtablefreqMHz_int=sorted([int(f) for f in ENRtablefreqMHz.keys()])          # convert ENRtable frequencies to integers and sort from lowest to highest frequency
ENRtable_values = [ENRtablefreqMHz[str(f)] for f in ENRtablefreqMHz_int]               # ENR table sorted by frequency and converted to values with frequency index
ENRtable = CubicSpline(ENRtablefreqMHz_int,ENRtable_values)                  # get cubic spline of ENR table