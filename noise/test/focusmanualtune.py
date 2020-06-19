# manually tune focus tuner
from focustuner_pos import *
#from measure_noiseparameters_focus import *
from read_write_spar_noise import *
from pna import *
from calculated_parameters import *
import visa

frequency=1500
tunertype='source'
gamma=[0.8,150]

tunercal="c:/Users/test/focus_setups/noise/tunercals_sourcepull"

rm=visa.ResourceManager()
# Sparameter files to cascade
#cascade available 2port networks onto port1 of tuner
tundir="C:/Users/test/python/data/RFamptest1/RF/"
#inputcircuitfile=tundir+"/S1_1-1.6GHz_July20_2017_SRI.s2p"
inputcircuitfile=tundir+"RFamptests1__input_isolator+cable_SRI.s2p"
#fixturecircuitfile=tundir+"/cascade_JC23F_1-1.6GHz_Aug14_2017_RI.s2p"
#cascadefiles_port1=
cascadefiles_port2=None
cascadefiles_port1=[inputcircuitfile,'noflip']
#cascadefiles_port2=[fixturecircuitfile,'noflip']
casaded2port1=None
casaded2port2=None

if cascadefiles_port1!=None and len(cascadefiles_port1)>0:
	if cascadefiles_port1[1]=='flip': casaded2port1=spar_flip_ports(read_spar(cascadefiles_port1[0]))  # then flip ports 1 and 2 on this two-port
	else: casaded2port1=read_spar(cascadefiles_port1[0])                              # don't flip ports

#cascade available 2port networks onto port2 of tuner
if cascadefiles_port2!=None and len(cascadefiles_port2)>0:
	if cascadefiles_port2[1]=='flip': casaded2port1=spar_flip_ports(read_spar(cascadefiles_port2[0]))  # then flip ports 1 and 2 on this two-port
	else: casaded2port2=read_spar(cascadefiles_port2[0])                              # don't flip ports


tuner=FocusTuner(S1=casaded2port1,S2=casaded2port2,tunertype=tunertype,tunercalfile=tunercal)  # set up tuner
t=tuner.set_tuner_reflection(frequency=frequency,gamma=complex(gamma[0],gamma[1]),gamma_format='ma')


pna=Pna(rm=rm,navg=16)
if tunertype=='source':
	pna.pna_getS22()
	ifreq=min(range(len(pna.freq)), key=lambda i: np.abs(frequency-pna.freq[i]/1E6))
	gammameasured=convertRItoMA(pna.s22[ifreq])
else:
	pna.pna_getS11()
	ifreq=min(range(len(pna.freq)), key=lambda i: np.abs(frequency-pna.freq[i]/1E6))
	gammameasured=convertRItoMA(pna.s11[ifreq])
pos1,pos2=tuner.getPOS()
tuner.resettuner()
print('tuner position = %d,%d' %(pos1,pos2))
print('set gamma = %5.3f %5.2f deg' %(t['gamma_MA'].real,t['gamma_MA'].imag) )
print("Tuner gain from tuner = %5.3f" %(t['gain']))
print('measured gamma = %5.3f %5.2f deg' %(gammameasured.real,gammameasured.imag) )
