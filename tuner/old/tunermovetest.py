# test the tuner read
from old.MauryTunerMT986 import *
from old.read_write_spar_noise import *
rm = visa.ResourceManager()

tundir="C:/Users/test/maury_setups/noise/"
tunerfile="1-1.6GHz_longcable_Feb16_2017.tun"
probefile=tundir+"cascade_RFprobe_APC40-A-GSG_SNJC23G_1-1.6GHz_Feb14_2017_RI.s2p"
inputcircuitfile=tundir+"input_circuit_biasT+coupler+circulator_1-1.6GHz_Feb14_2017_SRI.s2p"
#preampnoiseparameters=tundir+"noise_parameters/preamp_noise_parameters.csv"

tunerfrequency=1.E9
fulltunerpath=os.path.join(tundir,tunerfile)

t=MauryTunerMT986(tunerfile=fulltunerpath,rm=rm)
Sinput=read_spar(inputcircuitfile)
Sprobe=spar_flip_ports(read_spar(probefile))
t.cascade_tuner(port=2,S=Sinput)
#t.cascade_tuner(port=1,S=Sprobe)

#ret=t.get_tuner_position_from_reflection(frequency=tunerfrequency,requested_reflection=[.9,270],reflection_type='MA')
#tunerposition=ret[0]
tunerposition="5996,302,5000"

t.set_tuner_position(tunerposition)
tunerreflection=t.get_tuner_reflection(tunerfrequency,tunerposition)
print(tunerposition,convertRItoMA(tunerreflection))