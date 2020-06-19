# test oscilloscope for read issues
import visa
import time
############################################################################################################
# set time delay to allow for processing of commands
def idel():
	time.sleep(0.1)
############################################################################################################
############################################################################################################
# safely read data from scope
# re-read data if a read times out
def readrawdata(scope,channel=1):

	scope.chunk_size=10000000
	readerror=True
	maxreadtries=20
	readtries=0
	time.sleep(1.)
	print("entering read of raw data")
	timetoreadstart=time.time()
	while readerror and readtries<maxreadtries:
		scope.write(":WAV:DATA? CHANNEL1")
		#waveformdataraw=scope.query_binary_values(":WAV:DATA? CHANNEL"+formatnum(channel,type=int))
		#time.sleep(0.1)                 # allow this time for reading to minimize the need for re-reads of the data
		readtries+=1
		#scope.clear()
		#time.sleep(10.)
		#waveformdataraw=scope.read_raw()
		try: waveformdataraw=scope.read_raw()
		except:
			print("have a read error, retrying")
			readerror=True
			continue
		readerror=False
		#time.sleep(0.2)
	timetoreadend=time.time()
	print("time to read raw data=",timetoreadend-timetoreadstart)
	idel()
	scope.query_delay=0.1         # necessary query delay to enable error free query statements
	scope.delay=0.1
	if readerror: raise ValueError("ERROR! cannot read scope")
	else: return waveformdataraw
############################################################################################################
rm=visa.ResourceManager()
print(rm.list_resources())
scope = rm.open_resource('USB0::0x1AB1::0x0588::DS1ED121603918::INSTR')

idel()
scope.write(":ACQ:TYPE NORMAL")
idel()
scope.write(":ACQ:MEMDepth LONG")
idel()
scope.write(":ACQ:MEMDepth LONG")
idel()
scope.query_delay=0.1         # necessary query delay to enable error free query statements
scope.timeout=4000.

print(scope.query("*IDN?"))
scope.write("*RST")
idel()
scope.write(":ACQUIRE:MODE RTIME")          # set to real time acquisition
idel()
scope.write(":ACQUIRE:TYPE NORMAL")
idel()
scope.write(":ACQUIRE:MEMD LONG")           # set for largest memory depth
idel()
scope.write(":TIMEBASE:MODE MAIN")
idel()
scope.write(":WAV:POIN:MODE RAW")
idel()
