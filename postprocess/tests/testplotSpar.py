__author__ = 'PMarsh Carbonics Inc'
# test of plotting
from plot import *
import matplotlib.pyplot as plt
from utilities import sub

from device_parameter_request import DeviceParameters
import time
pathname = "C:/Users/test/python/waferprobe/data"
filename = "lot_test1_waf#_1die_0_0_dev_cfet0SRI.s2p"
devname = 'lot_test1_waf#_1die_0_0_dev_cfet0'
para = DeviceParameters(pathname,devname)
try: [freqSDB,s11dB,s21dB,s12dB,s22dB]=para.twoport('SDB')
except:
    print para.twoport('SDB')
    quit()


splt = dataPlotter()

splt.smithplotSpar(pathname+sub("SPAR")+"/"+filename,0,0)
splt.smithplotSpar(pathname+sub("SPAR")+"/"+filename,1,1)
#time.sleep(10)
#pl.clf()
splt.spardBplot(freqSDB,s21dB,'S21 (dB)')
time.sleep(10)
splt.close()
#splt.spardBplot(freqSDB,s11dB,'S11 (dB)')

quit()
sp = [s.real for s in s21dB]
del para
plt.ion()
plt.figure(1)
plt.plot(freqSDB,sp)
#plt.draw()
#time.sleep(10)

plt.figure(2)
sp = [s.real for s in s11dB]
plt.plot(freqSDB,sp)
plt.draw()
#time.sleep(10)
