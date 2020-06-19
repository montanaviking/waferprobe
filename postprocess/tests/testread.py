#__author__ = 'PMarsh Carbonics Inc'
#### test reading of S-parameter data
from device_parameter_request import *

print "starting testread"
pathname = 'C:/Users/test/python/waferprobe/data'
#devicename = 'Spar_lot_test1_waf#_1die_0_0_dev_cfet0.s2p'
devicename = 'lot_test1_waf#_1die_0_0_dev_cfet0'

sp = DeviceParameters(pathname,devicename)
sp.twoport("SRI")

print "device name",sp.device_name
print "Vds =", sp.Vds_spar
for ii in range (0,len(sp.freq)):
    print sp.freq[ii], sp.s11[ii], sp.s21[ii], sp.s12[ii], sp.s22[ii]
[freq_RI, s11_RI, s21_RI, s12_RI, s22_RI] = sp.twoport("SDB")
#for ii in range (0,len(freq_RI)):
#    print freq_RI[ii], s11_RI[ii], s21_RI[ii], s12_RI[ii], s22_RI[ii]
#[freq_DB, s11_DB, s21_DB, s12_DB, s22_DB] = sp.twoport("SDB")
#for ii in range (0,len(freq_DB)):
#     print freq_DB[ii], s11_DB[ii], s21_DB[ii], s12_DB[ii], s22_DB[ii]
[freq_U, Umax] = sp.twoport('UMAX')
for ii in range (0,len(freq_U)):
	 print freq_U[ii], Umax[ii]

print "sp.fth21()", sp.ft()
