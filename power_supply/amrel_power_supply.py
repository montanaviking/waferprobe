# Phil Marsh, Carbonics Inc
# Amrel PPS 18-4D power supply control
import time
timedelay=0.1
overvoltage=6.
maxcompliance=0.45
class amrelPowerSupply:
# set up of Amrel PPS-18-4D
	def __init__(self,rm=None,ptype=True):
		try:
			self.__pps=rm.open_resource("AmrelPPS18")
			self.__pps.query_delay=.5            # set up query delay to prevent errors
		except: raise ValueError("ERROR! power supply found")
		self.ptype=ptype            # indicates that DUT is p-type FET
		self.Voutsetting=0.
		self.compliance=0.01

	def __write(self,cmd=None):
		if cmd==None or len(cmd)==0: raise ValueError("ERROR! must supply write command")
		self.__pps.write(cmd)
		time.sleep(timedelay)
	def __query(self,cmd=None):
		if cmd==None or len(cmd)==0: raise ValueError("ERROR! must supply query command")
		ret=self.__pps.query(cmd)
		time.sleep(timedelay)
		return ret

	def setvoltage(self,channel=1,Vset=0.,compliance=0.2,overvoltage=overvoltage):
		if not (int(channel)==1 or int(channel)==2): raise ValueError("ERROR! invalid channel")
		if Vset<0:
			print("WARNING Vset set <0, setting to abs(Vset)")
			Vset=abs(Vset)
		if abs(Vset)>18:
			print("WARNING Vset set >18V which is outside the instrument capability")
		if compliance>maxcompliance: raise ValueError("compliance exceeds the maximum allowed")
		if abs(Vset)>overvoltage: raise ValueError("ERROR! set voltage>overvoltage setting")
		self.__write("OCP 1")           # enable overcurrent protection
		self.__write("ISET"+str(int(channel))+" "+str(compliance))
		self.__write("VSET"+str(int(channel))+" "+str(Vset))
		self.__write("OVSET"+str(int(channel))+" "+str(overvoltage))
		self.Voutsetting=Vset
		self.compliance=compliance

		# turn on supply
		self.__write("OUT"+str(int(channel))+" 1")                              # turn on selected channel output
		time.sleep(1.)
		Ioutactual,Voutactual,compliance_status=self.get_Iout(channel=channel)       # actual measured output voltage
		if self.ptype:                              # if measuring p-type devices then reverse sign of applied voltage and drain current
			Voutactual=-Voutactual
			Ioutactual=-Ioutactual

		err=int(self.__query("ERROR?").strip())                             # ERROR message 0=no errors, 1=command error, 2=numeric string out of range, 3=numeric string over length, 4=command sequence error
		if err!=0: print("WARNING! Amrel power supply has error number ",err)
		return err,compliance_status,Voutactual,Ioutactual             # reverse signs of voltage and current when we are measuring P-type devices

	def get_Iout(self,channel=1):
		if not (int(channel)==1 or int(channel)==2): raise ValueError("ERROR! invalid channel")
		Ioutactual=float(self.__query("IOUT"+str(int(channel))).strip())         # measured output current in A
		Voutactual=self.get_Vout(channel=channel)
		if self.ptype: Ioutactual=-Ioutactual                       # reverse sign of current if measuring a P-type FET
		#print("from line 60 in amrel_power_supply.py Ioutactual=None",Ioutactual)       # debug
		#print("from line 61 in amrel_power_supply.py Voutactual=None",Voutactual)       # debug
		#print("from line 62 in amrel_power_supply.py Voutsetting=None",Voutsetting)       # debug
		if abs(Ioutactual)>0.9*self.compliance or abs(Voutactual)<0.97*abs(self.Voutsetting):
			print("WARNING! Amrel power supply in compliance")
			comp="C"
		else: comp="N"
		return Ioutactual,Voutactual,comp

	def get_Vout(self,channel=1):
		if not (int(channel)==1 or int(channel)==2): raise ValueError("ERROR! invalid channel")
		Voutactual=float(self.__query("VOUT"+str(int(channel))).strip())         # measured output current in A
		if self.ptype: Voutactual=-Voutactual                           # reverse sign if measuring a P-type FET
		return Voutactual

	def output_on(self,channel=1):
		if not (int(channel)==1 or int(channel)==2): raise ValueError("ERROR! invalid channel")
		self.__write("OUT"+str(int(channel))+" 1")
		time.sleep(1.)

	def output_off(self,channel=1):
		if not (int(channel)==1 or int(channel)==2): raise ValueError("ERROR! invalid channel")
		self.__write("OUT"+str(int(channel))+" 0")
		time.sleep(1.)

	# def getstatusbyte(self,channel=1):
	# 	if not (int(channel)==1 or int(channel)==2): raise ValueError("ERROR! invalid channel")
	# 	self.output_off(channel=1)
	# 	self.output_off(channel=2)
	# 	#err=int(self.__query("ERROR?").strip())                             # ERROR message 0=no errors, 1=command error, 2=numeric string out of range, 3=numeric string over length, 4=command sequence error
	# 	statusfull=int(self.__query("STATUS?"))    # get channel1+channel2 status byte
	# 	statusb1=255&statusfull                  # get channel1 status byte
	# 	#statusb1=(65280&statusfull)>>8
	# 	statusb2=statusfull>>8
	# 	print(bin(statusb1),bin(statusb2))
	# 	quit()
	# 	stb={"LORNG":False,"CC":False,"OV":False,"OC":False,"OCP":False,"ON":False,"ON2":False,"ERR":False,"CH1":False,"CH2":False}
	# 	if 1&statusb1: stb["ERR"]=True
	# 	else: stb["ERR"]=False
	# 	if 64&statusb1: stb["LORNG"]=True
	# 	else: stb["LORNG"]=False
	# 	if channel==1:
	# 		if 2&statusb1: stb["ON"]=True
	# 		else: stb["ON"]=False
	# 		if 4&statusb1: stb["OCP"]=True
	# 		else: stb["OCP"]=False
	# 		if 8&statusb1: stb["OC"]=True
	# 		else: stb["OC"]=False
	# 		if 16&statusb1: stb["OV"]=True
	# 		else: stb["OV"]=False
	# 		if 32&statusb1: stb["CC"]=False
	# 		else: stb["CC"]=True
	# 	return stb
