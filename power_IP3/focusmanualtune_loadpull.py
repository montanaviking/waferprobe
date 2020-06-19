# manually tune focus tuner in loadpull mode
from calculated_parameters import *
#from measure_noiseparameters_focus import *
from read_write_spar_noise import *
from pna import *
from calculated_parameters import *
#from loadpull_system_calibration import *
import visa

from focustuner_pos import *

sysdir="C:/Users/test/focus_setups/noise/"          # base directory of noise calibrations
#probefile=sysdir+"KP2GC_May4_2018_SRI.s2p"                                                 # right side probe

tunerinputcable=sysdir+"noise__coupler_biastee_isolator_April23_2020_SRI.s2p"                           # noise figure
#inputprobe=sysdir+"ACP150_JC2G6-1_May4_2020_SRI.s2p"
frequency=1000
tunertype='source'
gamma=[0.58,-16.85]


if tunertype=='source':
	from focustuner_pos import *
	tunercalfile="c:/Users/test/focus_setups/tunercals_sourcepull/tunercal_1389source_April16_2020_1GHz_1.6GHz_13pts.txt"
elif tunertype=='load':from focustuner import *


rm=visa.ResourceManager()
# Sparameter files to cascade
#cascade available 2port networks onto port1 of tuner

cascadefiles_port2=None
#cascadefiles_port1=None
cascadefiles_port1=[tunerinputcable,'noflip']
#cascadefiles_port2=[inputprobe,'noflip']


cascaded2port1=None
cascaded2port2=None
#
if cascadefiles_port1!=None and len(cascadefiles_port1)>0:
	if cascadefiles_port1[1]=='flip': casaded2port1=spar_flip_ports(read_spar(cascadefiles_port1[0]))  # then flip ports 1 and 2 on this two-port
	else: casaded2port1=read_spar(cascadefiles_port1[0])                              # don't flip ports
# if cascadefiles_inputprobe!=None and len(cascadefiles_inputprobe)>0:
# 	if cascadefiles_inputprobe[1]=='flip':
# 		casadedinputport=spar_flip_ports(read_spar(cascadefiles_inputprobe[0]))  # then flip ports 1 and 2 on this two-port
# 	else:
# 		cascadedinputprobe=read_spar(cascadefiles_inputprobe[0])
#

#cascade available 2port networks onto port2 of tuner
if cascadefiles_port2!=None and len(cascadefiles_port2)>0:
	if cascadefiles_port2[1]=='flip':
		cascaded2port2=spar_flip_ports(read_spar(cascadefiles_port2[0]))  # then flip ports 1 and 2 on this two-port
	else:
		cascaded2port2=read_spar(cascadefiles_port2[0])                              # don't flip ports


if tunertype=='source':
	tuner=FocusTuner(IP=("192.168.1.31",23),S1=casaded2port1,S2=cascaded2port2,tunertype=tunertype,tunercalfile=tunercalfile)  # set up tuner
else:
	tuner=FocusTuner(IP=("192.168.1.30",23),S1=casaded2port1,S2=cascaded2port2,tunertype=tunertype)  # set up tuner

t=tuner.set_tuner_reflection(frequency=frequency,gamma=complex(gamma[0],gamma[1]),gamma_format='ma')


pna=Pna(rm=rm,navg=4)
if tunertype=='source': # source tuner
	pna.pna_get_S_oneport(navg=4,instrumentstate="S22.sta",calset="CalSet_2",type="s22")
	#pna.pna_getS_2port(instrumentstate="2port_LF.sta",calset="CalSet_1",navg=4)
	ifreq=min(range(len(pna.freq)), key=lambda i: np.abs(frequency-pna.freq[i]/1E6))
	gammameasured=convertRItoMA(pna.s22_oneport[ifreq])
	#gammameasured=convertRItoMA(pna.s22[ifreq])
else:   # load tuner
	pna.pna_get_S_oneport(navg=4,type="s22")
	ifreq=min(range(len(pna.freq)), key=lambda i: np.abs(frequency-pna.freq[i]/1E6))
	gammameasured=convertRItoMA(pna.s22_oneport[ifreq])
pos1,pos2=tuner.getPOS()
# #tuner.resettuner()
#
print('tuner position = %d,%d' %(pos1,pos2))
print('set gamma = %5.3f %5.2f deg' %(t['gamma_MA'].real,t['gamma_MA'].imag) )
print('measured gamma = %5.3f %5.2f deg' %(gammameasured.real,gammameasured.imag) )
print("Tuner gain from tuner = %5.3f" %(t['gain']))
print("Tuner gain from tunerdB = %5.3f" %(lintodB(t['gain'])))
ifreq=min(range(len(pna.freq)), key=lambda i: np.abs(frequency-pna.freq[i]/1E6))
#gainfromspar=lintodB(  pow(abs(pna.s21[ifreq]),2)/(1-pow(abs(pna.s22[ifreq]),2)) )
#print("Tuner gain from measured S-parameters = %5.3f dB" %(gainfromspar))


#print('measured mag S21 %5.2f angle %5.2f '%(abs(pna.s21[ifreq]), convertRItoMA(pna.s21[ifreq]).imag))
print('tuner mag S21 %5.2f angle %5.2f '%(convertRItoMA(t['Spar'][1][0]).real, convertRItoMA(t['Spar'][1][0]).imag))
#print('measured mag S22 %5.2f angle %5.2f '%(abs(pna.s22[ifreq]), convertRItoMA(pna.s22[ifreq]).imag))
print('tuner mag S22 %5.2f angle %5.2f '%(convertRItoMA(t['Spar'][1][1]).real, convertRItoMA(t['Spar'][1][1]).imag))

print('measured gamma corrected for thru line = %5.3f %5.2f deg' %(gammameasured.real,gammameasured.imag+1E6*frequency*2E-12*360) )
Z=gammatoYZ(gamma=gammameasured,Z=True)
print('measured Z = %5.3f + j%5.2f' %(Z.real,Z.imag) )
Y=gammatoYZ(gamma=gammameasured,Z=False)
print('measured Y = %5.3f + j%5.2f' %(Y.real,Y.imag) )
