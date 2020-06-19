# control of HP438A power meter
# Phil Marsh Carbonics Inc 2017
import visa
from utilities import formatnum
minreadablepower=-25.0          # minimum RF power that is readable by the power meter
maxreadablepower=19.5          # maximum RF power that is readable by the power meter

class HP438A(object):
	def __init__(self,rm=None,calfactorA=97.5,calfactorB=97.6,loglin='LG'):
		if rm==None: raise ValueError("ERROR! No VISA resource handle for HP438A power meter.")
		try:
			self.__powermeter=rm.open_resource('GPIB0::8::INSTR')
		except: raise ValueError("ERROR on HP438A power meter: Could not find on GPIB\n")
		self.__powermeter.timeout=30000
		self.__powermeter.query_delay=0.5            # set up query delay to prevent errors
		self.__powermeter.write('SRQ')
		self.__powermeter.write('PR')                          # preset power meter

		self.__powermeter.write('AEEN')             # set up channel A
		calfactorA=formatnum(calfactorA,precision=1,nonexponential=True)      # convert calfactor to a string
		self.__powermeter.write(loglin+'EN')          # set to log (dBm) output data mode
		self.__powermeter.write('KB'+calfactorA+'EN')
		self.__powermeter.write('RAEN')        # set power meter to autorange
		self._status=self.__powermeter.query('SM')          # get powermeter status
		self.__powermeter.write('FAEN')                    # set auto filtering

		self.__powermeter.write('BEEN')             # set up channel B
		calfactorB=formatnum(calfactorB,precision=1,nonexponential=True)      # convert calfactor to a string
		self.__powermeter.write(loglin+'EN')          # set to log (dBm) output data mode
		self.__powermeter.write('KB'+calfactorB+'EN')
		self.__powermeter.write('RAEN')        # set power meter to autorange
		self._status=self.__powermeter.query('SM')          # get powermeter status
		self.__powermeter.write('FAEN')                    # set auto filtering
		self.__loglin=loglin
		if loglin.lower()=='lg':
			self.__minreadablepower=minreadablepower
			self.__maxreadablepower=maxreadablepower
		elif loglin.lower()=='lin':
			self.__minreadablepower=pow(10.,minreadablepower/10.)   # convert minimum readable power to linear
			self.__maxreadablepower=pow(10.,maxreadablepower/10.)   # convert maximum readable power to linear
	# trigger and read power meter
	def readpower(self,filter=None,sensor=None):
		if sensor==None: raise ValueError("ERROR! No sensor designator given. Must be 'A' or 'B'")
		if filter!=None:
			filter=str(int(filter))
			if int(filter)<0 or int(filter)>9: raise ValueError("ERROR! from HP438A Illegal value of filter")
			self.__powermeter.write('FM'+filter+'EN')      # set filter for averaging of data
		else: self.__powermeter.write('FAEN')           # set filter to auto
		if sensor.lower()=='a':
			self.__powermeter.write('AEEN')     # control sensor A
			self.__powermeter.write('APEN')     # read sensor A
		elif sensor.lower()=='b':
			self.__powermeter.write('BEEN')   # control sensor B
			self.__powermeter.write('BPEN')   # read sensor B
		self.__powermeter.write('CS')           # clear status byte first prior to polling for data
		self.__powermeter.write('TR2EN')        # trigger for reading data
		self.__pollpowermeter()                           # poll loop until data ready
		power=float(self.__powermeter.read())        # read raw data
		if power<self.__minreadablepower: return -999
		elif power>self.__maxreadablepower: return 999
		return power
	# polling
	def __pollpowermeter(self):
		#print("polling HP438A start")
		#self.__powermeter.wait_for_srq()
		while True:
			sb=self.__powermeter.read_stb()
			#print("status byte = ",sb)
			if sb&1==1:
				self.__powermeter.write('CS')       # clear status byte
				break
