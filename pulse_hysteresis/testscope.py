# test of Rigol oscilloscope reading

############################################################################################################
# safely read data from scope
# re-read data if a read times out
def __readrawdata(self,channel=1):
	# if longdata==True then we need to read twice to capture the long-form, high-resolution data set
	#self.__oscilloscope.query_delay=6.         # necessary query delay to enable error free query statements
	#self.__oscilloscope.delay=6.
	self.__oscilloscope.chunck_size=10000000
	readerror=True
	maxreadtries=20
	readtries=0
	time.sleep(1.)
	print("entering read of raw data")
	timetoreadstart=time.time()
	while readerror and readtries<maxreadtries:
		self.__oscilloscope.write(":WAV:DATA? CHANNEL"+formatnum(channel,type=int))
		#waveformdataraw=self.__oscilloscope.query_binary_values(":WAV:DATA? CHANNEL"+formatnum(channel,type=int))
		#time.sleep(0.1)                 # allow this time for reading to minimize the need for re-reads of the data
		readtries+=1
		#self.__oscilloscope.clear()
		#time.sleep(10.)
		#waveformdataraw=self.__oscilloscope.read_raw()
		try: waveformdataraw=self.__oscilloscope.read_raw()
		except:
			print("have a read error, retrying")
			readerror=True
			continue
		readerror=False
		#time.sleep(0.2)
	timetoreadend=time.time()
	print("time to read raw data=",timetoreadend-timetoreadstart)
	self.__idel()
	self.__oscilloscope.query_delay=0.1         # necessary query delay to enable error free query statements
	self.__oscilloscope.delay=0.1
	if readerror: raise ValueError("ERROR! cannot read scope")
	else: return waveformdataraw
############################################################################################################