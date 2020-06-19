
import visa
from ctypes import c_ulong, create_string_buffer, byref
import binascii
import time
from HP8970B_noisemeter import *
rm = visa.ResourceManager()
#outfiledirectory="c:/Users/test/python/data/noisetest"
outfiledirectory="c:/Users/test/python/data/noisefiguretests"
#noiseoutfilename="amp_baresystem"
#nm=NoiseMeter(ENR=13.0,rm=rm)
#nm=NoiseMeter(losstable="c:/Users/test/python/data/Wf169meas5/testplan/losscomp.csv",rm=rm)
#nm=NoiseMeter(rm=rm,losstable="c:/Users/test/python/data/noisefiguretests/testplan/losscompfromSpara.csv")
nm=NoiseMeter(ENR=13.,rm=rm)
#f,gain,NF=nm.sweep(smoothing=32)
gain,NF=nm.get_NF_singlefrequency(frequency=1100,smoothing=16)
#nm.writefile_noise(pathname=outfiledirectory,devicename="10dBpad")

# print("average noise figure = ",np.mean(NF))
# print("average gain = ",np.mean(gain))
#print("frequencies ",list(np.divide(f,1E6)))
print("gain ",gain)
print("noise figure ",NF)