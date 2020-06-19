# test for power meter functions
import visa
from HP438A import *

rm = visa.ResourceManager()
pm=HP438A(rm=rm)
print(pm.readpower(sensor='A'))
print(pm.readpower(sensor='B'))