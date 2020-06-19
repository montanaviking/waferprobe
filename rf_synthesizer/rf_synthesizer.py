__author__ = 'PMarsh Carbonics'
# sets up synthesizers A or B
#
import visa
import time
settlingtime=0.1
class Synthesizer(object):
	def __init__(self,rm=None,syn='A',maximumpowersetting=17.):
		self.maximumpowersetting=maximumpowersetting                    # maximum allowed synthesizer power setting
		if syn.lower()=='a':
			try: self.__syn= rm.open_resource('GPIB0::6::INSTR')         # RF synthesizer A
			except:
				raise ValueError("Cannot open RF systhesizer A - check if instrument is on and/or connected to GPIB and/or instrument address (=6)")
		elif syn.lower()=='b':
			try: self.__syn= rm.open_resource('GPIB0::9::INSTR')         # RF synthesizer B
			except:
				raise ValueError("Cannot open RF systhesizer B - check if instrument is on and/or connected to GPIB and/or instrument address (=6)")
		else: raise ValueError("No valid RF synthesizer specified to connect")

		print (self.__syn.query("*IDN?"))
		self.__syn.write("*RST")                        # set instrument preset defaults
		#self.__syn.wait_for_srq()
		self.__syn.write("SOUR:POW:ALC:SOUR INT")       # set automatic level control on and to internal reference
		# set up for polling
		self.__syn.write("STAT:OPER:PTR 0")
		self.__syn.write("STAT:OPER:NTR 2")
		self.__syn.write("STAT:OPER:ENAB 2")
		self.__syn.write("*SRE 128")
		self.__poll()
		#self.__syn.wait_for_srq()
		#self.__syn.write("*CLS")
	def __del__(self):
		#self.__syn.write("*CLS")            # clear SRQ from bus
		self.__syn.close()
	#####################################################################ff###############################################
	# gets the error number for a system error
	def get_errornumber(self):
		err=self.__syn.query("SYST:ERR?")
		return err
	####################################################################################################################
	# sets the output frequency of the synthesizer
	def set_frequency(self,*args):
		#self.__syn.write("*CLS")          # clear SRQ
		if len(args)==2:            # assume default units is Hz
			if args[1].lower()=='ghz': freq=1.E9*args[0]
			elif args[1].lower()=='mhz': freq=1.E6*args[0]
			elif args[1].lower()=='khz': freq=1.E3*args[0]
			elif args[1].lower()=='hz': freq=args[0]
			else: raise ValueError("ERROR! illegal units!")
		elif len(args)==1:
			freq=args[0]                # assume that default units is Hz
		else: raise ValueError("ERROR! illegal number of parameters!")
		if freq<10.E6:
			raise ValueError("ERROR! frequency set below 10MHz is not allowed!")
		if freq>20.E9:
			raise ValueError("ERROR frequency set above 20GHz is not allowed!")
		self.__syn.write("SOUR:FREQ:CW "+str(freq))
		#self.__syn.write("*OPC")
		self.__poll()
		#self.__syn.write("*CLS")          # clear SRQ
		freq=self.__syn.query("SOUR:FREQ:CW?")            # return actual frequency set
		self.__poll()
		#
		return freq
	####################################################################################################################
	# gets the output frequency of the synthesizer (always in Hz)
	def get_frequency(self):
		#self.__syn.write("*CLS")          # clear SRQ
		freq= self.__syn.query("SOUR:FREQ:CW?")    # frequency in Hz
		self.__poll()
		#
		return freq
	####################################################################################################################
	# turns the RF output on
	def on(self):
		#self.__syn.write("*CLS")          # clear SRQ
		self.__syn.write("OUTP:STAT ON")
		#self.__syn.write("*OPC")
		self.__poll()
		#self.__syn.write("*CLS")          # clear SRQ
		outputstat= int(self.__syn.query("OUTP:STAT?"))
		self.__poll()
		if outputstat==1:
			return "on"
		else:
			return "off"
	####################################################################################################################
	# turns the RF output off
	def off(self):
		#self.__syn.write("*CLS")          # clear SRQ
		self.__syn.write("OUTP:STAT OFF")
		#self.__syn.write("*OPC")
		self.__poll()
		#self.__syn.write("*CLS")          # clear SRQ
		outputstat= int(self.__syn.query("OUTP:STAT?"))
		self.__poll()
		if outputstat==1:
			return "on"
		else:
			return "off"
	####################################################################################################################
		# set the RF output power level
		# turns RF on
	def set_power(self,leveldBm):
		if leveldBm>self.maximumpowersetting: raise ValueError("ERROR! attempted to set synthesizer at power level beyond that allowed")
		#self.__syn.write("*CLS")
		self.__syn.write("SOUR:POW:LEV "+str(leveldBm))
		self.on()
		#self.__syn.write("*OPC")
		#self.__poll()
		#print self.__syn.query("STAT:QUES:COND?") #debug
		#self.__syn.write("*CLS")
		lp=8&int(self.__syn.query("STAT:QUES:COND?"))
		self.__poll()
		if lp>0:       # then we have unleveled power
			return "unleveled"
		else:
			return "ok"
	####################################################################################################################
		# get the RF output power level setting
	def get_power(self):
		#self.__syn.write("*CLS")          # clear SRQ
		power=float(self.__syn.query("SOUR:POW:LEV?"))
		self.__poll()
		return power
	####################################################################################################################
	# clear
	def vclear(self):
		#self.__syn.write("*CLS")          # clear SRQ
		self.__syn.clear()
	####################################################################################################################
	# _poll status byte to make sure operation is complete before issuing another instruction
	def __poll(self):

		while True:

			st = 2&int(self.__syn.query("STAT:OPER:COND?"))
			sb=64&int(self.__syn.query('*STB?'))     # get bit 6 to see if the sweep is complete
			#print ("from line 113 rf_synthesizer _poll st, sb", st,sb)
			if st==0 and sb>0: break


		# # set up for polling
		# print("polling synthesizer")
		# self.__syn.wait_for_srq()
		# self.__syn.write("STAT:OPER:PTR 0")
		# self.__syn.write("STAT:OPER:NTR 2")
		# self.__syn.write("STAT:OPER:ENAB 2")
		# self.__syn.write("*SRE 128")
		return

