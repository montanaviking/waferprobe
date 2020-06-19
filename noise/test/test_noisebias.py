# test noise bias source
import visa, time
from parameter_analyzer import *
from HP8970B_noisemeter import *
rm=visa.ResourceManager()
#iv = ParameterAnalyzer(rm)                # setup IV and bias
nm = NoiseMeter(rm=rm,ENR=15,preset=True,turnonnoisesourceonly=True)               # ENR is bogus because the noise meter is being used only to drive the noise source

nm.noise_sourceonoff(True)                  # turn on noise source - DC not pulsed
time.sleep(20)
nm.noise_sourceonoff(False)                 # turn off noise source


