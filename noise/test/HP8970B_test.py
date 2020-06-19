
import visa
from ctypes import c_ulong, create_string_buffer, byref
import binascii
import time
def readpoll(noisemeter=None):
	loop=True
	while(loop):
		loop=False
		try: x=noisemeter.read_raw()
		except : loop=True
	return



rm = visa.ResourceManager()
#noisemeter = rm.open_resource('GPIB0::8::INSTR')
noisemeter = rm.open_resource('GPIB0::18::INSTR')
noisemeter.query_delay=1.
noisemeter.write("*SPE EN")
noisemeter.write("RM EN")
noisemeter.write("RE EN")
noisemeter.write("RE EN")
noisemeter.write("OS EN")

#noisemeter.values_format.use_ascii('f',';')
#noisemeter.values_format.datatype='x'
#sb=noisemeter.read_stb()
#print("status byte =",sb)
noisemeter.write("H1 EN")
noisemeter.write("M2 EN")
#p,x=noisemeter.query("M1")
#x=noisemeter.query_binary_values("M2")
#x=noisemeter.read_raw()
#noisemeter.read_termination=''
#x=noisemeter.read_bytes()
#noisemeter.write("T2")
#time.sleep(5)
#x=noisemeter.read_raw()
#sb=noisemeter.read_stb()
#count = noisemeter.chunk_size
#buffer = create_string_buffer(count)
#buffer=hex(1)
#return_count = c_ulong()
#noisemeter.visalib.lib.viRead(noisemeter.session,buffer, count, byref(return_count))

#p=noisemeter.query("T2")
#time.sleep(10)
#enrcurrent=noisemeter.read_raw()
#print(x)
noisemeter.write("FR 1300 EN")
tr=noisemeter.read_raw()
tr2=noisemeter.read_raw()
t1=noisemeter.read()
t2=noisemeter.read()
readpoll(noisemeter=noisemeter)
print(noisemeter.read())

# noisemeter.write("FR 1400 EN")
# readpoll(noisemeter=noisemeter)
# print(noisemeter.read())
#
# noisemeter.write("FR900MZ")
# readpoll(noisemeter=noisemeter)
# print(noisemeter.read())
#
# noisemeter.write("UP")
# readpoll(noisemeter=noisemeter)
# print(noisemeter.read())
# print(noisemeter.read())
# print(noisemeter.read())

noisemeter.write("F0")

noisemeter.write("SE")
readpoll(noisemeter=noisemeter)
print(noisemeter.read())

noisemeter.write("FR 1400 EN")
readpoll(noisemeter=noisemeter)
print(noisemeter.read())

#print("status byte after read=",sb)
# print(binascii.hexlify(x))
#print(binascii.hexlify(buffer[:return_count.value]))
#print(" ".join("{:02x}".format(c) for c in x))
#print("{0:x}".format(x))
