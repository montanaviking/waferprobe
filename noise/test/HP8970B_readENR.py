
import visa
from ctypes import c_ulong, create_string_buffer, byref
import binascii
import time
from HP8970B_noisemeter import *
rm = visa.ResourceManager()
outfiledirectory="c:/Users/test/python/data/Wf169meas5/testplan"
nm=NoiseMeter(losstable="c:/Users/test/python/data/Wf169meas5/testplan/losscomp.csv",rm=rm)
