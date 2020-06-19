# test of Focus tuner functions
from focustuner import *
from read_write_spar_noise_v2 import *
from calculated_parameters import cascadeSf
S1=read_spar("/carbonics/owncloudsync/X.Selected_Measurements/TOIsys_test_2017/S1_longcable_1-1.6GHz_April14_2017_SRI.s2p")
S2=read_spar("/carbonics/owncloudsync/X.Selected_Measurements/TOIsys_test_2017/S2_IP3cablebiastee_1-1.6GHz_April14_2017_SRI.s2p")
probe=spar_flip_ports(read_spar("/carbonics/owncloudsync/X.Selected_Measurements/TOIsys_test_2017/cascade_RFprobe_APC40-A-GSG_SNJC23F_1-1.6GHz_Jan25_2017_RI.s2p"))
S1=cascadeSf(probe,S1)
tuner=FocusTuner(tunertype='load',S1=S1,S2=S2)
gammaset=(.8,90)
ret=tuner.set_tuner_reflection(frequency=1500,gamma=gammaset)
print("gamma= ",ret['gamma_MA'])
print("gain dB= ",10*np.log10(ret['gain']))
tunerpos=tuner.getPOS()
print("current tuner initial position = ",tunerpos)
#tuner.initializetuner(nocascade=True)
# tuner.setPOS(pos1=2000,pos2=2000)
# tunerpos=tuner.getPOS()
# print("tuner position = ",tunerpos)
# tuner.initializetuner()
# tunerpos=tuner.getPOS()
# print("tuner position after initialize = ",tunerpos)
# tuner.setPOS(pos1=1000,pos2=4000)
# tunerpos=tuner.getPOS()
# print("current tuner final position = ",tunerpos)

#del tunerpos
