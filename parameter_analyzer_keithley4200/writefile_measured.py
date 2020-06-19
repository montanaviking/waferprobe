# __author__ = 'test'
import os
import datetime as dt
import numpy as np
from utilities import formdevicename, sub, formatnum, lintodB
from calculated_parameters import convertRItodB, convertRItoMA


###################################
# measured data file data writing functions
# note that the subsitename is the name of the particular subsite - i.e. a descriptive name of the device at a subsite for all die
# the devicename is a unique name given to a device that is tested under a certain condition. One device can have many devicenames - one devicename per condition e.g. bias,
# temperature - etc.. which would cause the device to have different measured parameters.
######################################################################################################################################################
# write current IV family of curves results to a file
# Inputs:
# pathname
# The device name may be supplied or the parameters from Cascade Nucleus may be supplied to form the devicename
# For user-defined probe test plans, the devicename is obtained from the probe test file and must be supplied to this function as the devicename
def X_writefile_ivfoc(self,pathname=None, devicename=None, wafername=None,xloc=0,yloc=0,devicenamemodifier=""):
	if devicenamemodifier!="": devicenamemodifier= "".join(["_",devicenamemodifier])
	pathname_IV = pathname + sub("DC")
	try:
		self.Id_foc
	except:
		print("ERROR! NO family of curves exists! NO family of curves written!")
		return
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	filename="".join([pathname_IV,"/",wafername,devicenamemodifier,"__",devicename,"_foc.xls"])
	# now write the family of curves data for the current set of most recently measured or read data
	ffoc = open(filename, 'w')
	# parameters
	ffoc.write('# wafer name\t' + wafername + '\n')
	ffoc.write('# device name\t' + wafername+devicenamemodifier+"__"+devicename+'\n')
	ffoc.write('# x location um\t%d\n' % (int(xloc)))
	ffoc.write('# y location um\t%d\n' % (int(yloc)))
	# timestamp
	ffoc.write('# year\t' + str(dt.datetime.now().year) + '\n')
	ffoc.write('# month\t' + str(dt.datetime.now().month) + '\n')
	ffoc.write('# day\t' + str(dt.datetime.now().day) + '\n')
	ffoc.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	ffoc.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	ffoc.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	ffoc.write('# Vgs\tVds\tId\tIg\tdrainstatus\tgatestatus\n')

	for iVgs in range(0, len(self.Id_foc)):
		ffoc.write('# Vgs =\t %10.2f\n' % self.Vgs_foc[iVgs][0])
		for iVds in range(0, len(self.Id_foc[iVgs])):
			ffoc.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\n' % (
				self.Vgs_foc[iVgs][iVds], self.Vds_foc[iVgs][iVds], self.Id_foc[iVgs][iVds], self.Ig_foc[iVgs][iVds],
				self.drainstatus_foc[iVgs][iVds], self.gatestatus_foc[iVgs][iVds]))
	ffoc.close()
	return [filename, devicename]
######################################################################################################################################################
######################################################################################################################################################
# write current IV family of curves results to a file for backgated TLMS measured two at a time
# xloc_probe and yloc_probe are the locations of the probing position for these devices
# xloc and yloc are the actual locations of the device on the wafer. This can be different than xloc_probe and yloc_probe because the probe pads can be offset significantly from the devices
# The device name may be supplied or the parameters from Cascade Nucleus may be supplied to form the devicename
# For user-defined probe test plans, the devicename is obtained from the probe test file and must be supplied to this function as the devicename
def X_writefile_ivfoc_dual(self, backgated=True,pathname=None, wafername=None, devicenames=None, xloc_probe=None, yloc_probe=None,xloc0=None,xloc1=None,yloc0=None,yloc1=None,devicenamemodifier=""):
	if pathname == None:    raise ValueError("ERROR! No pathname provided")
	if wafername == None:    raise ValueError("ERROR! No wafername provided")
	if devicenames == None:    raise ValueError("ERROR! No device name provided")

	pathname_IV = "".join([pathname, sub("DC")])
	if not hasattr(self, 'Id0_foc') or not hasattr(self, 'Id1_foc'): raise ValueError(
		"ERROR! missing family of curves data")

	# write the family of curves data for the first TLM structure.
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	if devicenamemodifier!="": devicenamemodifier="_"+devicenamemodifier
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicenames[0],"_foc.xls"])
	# now write the family of curves data for the current set of most recently measured or read data
	ffoc = open(filename, 'w')
	# parameters
	ffoc.write("".join(['# wafer name\t', wafername, '\n']))
	ffoc.write("".join(['# device name\t',wafername,"__",devicenames[0],'\n']))
	if xloc0==None and yloc0==None:
		ffoc.write('# x location um\t%d\n' % (int(xloc_probe)))
		ffoc.write('# y location um\t%d\n' % (int(yloc_probe)))
	else:       # xloc0,yloc0 is the device 0 location xloc1,yloc1 is the device 1 location
		ffoc.write('# x location um\t%d\n' % (int(xloc0)))
		ffoc.write('# y location um\t%d\n' % (int(yloc0)))

	# timestamp
	ffoc.write('# year\t' + str(dt.datetime.now().year) + '\n')
	ffoc.write('# month\t' + str(dt.datetime.now().month) + '\n')
	ffoc.write('# day\t' + str(dt.datetime.now().day) + '\n')
	ffoc.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	ffoc.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	ffoc.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	ffoc.write('# Vgs\tVds\tId\tIg\tdrainstatus\tgatestatus\n')

	for iVgs in range(0, len(self.Id0_foc)):
		if backgated:
			ffoc.write('# Vgs =\t %10.2f\n' % self.Vgs_foc[iVgs][0])
			for iVds in range(0, len(self.Id0_foc[iVgs])):
				ffoc.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\n' % (
					self.Vgs_foc[iVgs][iVds], self.Vds0_foc[iVgs][iVds], self.Id0_foc[iVgs][iVds], self.Ig_foc[iVgs][iVds],self.drainstatus0_foc[iVgs][iVds], self.gatestatus_foc[iVgs][iVds]))
		else: # topgated
			ffoc.write('# Vgs =\t %10.2f\n' % self.Vgs0_foc[iVgs][0])
			for iVds in range(0, len(self.Id0_foc[iVgs])):
				ffoc.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\n' % (
					self.Vgs0_foc[iVgs][iVds], self.Vds0_foc[iVgs][iVds], self.Id0_foc[iVgs][iVds], self.Ig0_foc[iVgs][iVds],self.drainstatus0_foc[iVgs][iVds], self.gatestatus0_foc[iVgs][iVds]))
	ffoc.close()

	# write the family of curves data for the second TLM structure.
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)

	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicenames[1],"_foc.xls"])
	# now write the family of curves data for the current set of most recently measured or read data
	ffoc = open(filename, 'w')
	# parameters
	ffoc.write("".join(['# wafer name\t', wafername, '\n']))
	ffoc.write("".join(['# device name\t',wafername,"__",devicenames[1],'\n']))
	if xloc1==None and yloc1==None:
		ffoc.write('# x location um\t%d\n' % (int(xloc_probe)))
		ffoc.write('# y location um\t%d\n' % (int(yloc_probe)))
	else:       # xloc0,yloc0 is the device 0 location xloc1,yloc1 is the device 1 location
		ffoc.write('# x location um\t%d\n' % (int(xloc1)))
		ffoc.write('# y location um\t%d\n' % (int(yloc1)))
	# timestamp
	ffoc.write('# year\t' + str(dt.datetime.now().year) + '\n')
	ffoc.write('# month\t' + str(dt.datetime.now().month) + '\n')
	ffoc.write('# day\t' + str(dt.datetime.now().day) + '\n')
	ffoc.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	ffoc.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	ffoc.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	ffoc.write('# Vgs\tVds\tId\tIg\tdrainstatus\tgatestatus\n')
	if backgated:
		for iVgs in range(0, len(self.Id1_foc)):
			ffoc.write('# Vgs =\t %10.2f\n' % self.Vgs_foc[iVgs][0])
			for iVds in range(0, len(self.Id1_foc[iVgs])):
				ffoc.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\n' % (
					self.Vgs_foc[iVgs][iVds], self.Vds1_foc[iVgs][iVds], self.Id1_foc[iVgs][iVds], self.Ig_foc[iVgs][iVds],self.drainstatus1_foc[iVgs][iVds], self.gatestatus_foc[iVgs][iVds]))
	else: #topgated
		for iVgs in range(0, len(self.Id1_foc)):
			ffoc.write('# Vgs =\t %10.2f\n' % self.Vgs1_foc[iVgs][0])
			for iVds in range(0, len(self.Id1_foc[iVgs])):
				ffoc.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\n' % (
					self.Vgs1_foc[iVgs][iVds], self.Vds1_foc[iVgs][iVds], self.Id1_foc[iVgs][iVds], self.Ig1_foc[iVgs][iVds],self.drainstatus1_foc[iVgs][iVds], self.gatestatus1_foc[iVgs][iVds]))
	ffoc.close()
	return [filename, devicenames]
######################################################################################################################################################
# write current IV family of curves results to a file for topgated CFETs measured two at a time
# xloc_probe and yloc_probe are the locations of the probing position for these devices
# xloc and yloc are the actual locations of the device on the wafer. This can be different than xloc_probe and yloc_probe because the probe pads can be offset significantly from the devices
# The device name may be supplied or the parameters from Cascade Nucleus may be supplied to form the devicename
# For user-defined probe test plans, the devicename is obtained from the probe test file and must be supplied to this function as the devicename
# probe layout: gate1: CH2       drain1: CH4
#               gate0: CH1       drain0: CH3
def X_writefile_ivfoc_dual_topgate(self, pathname=None, wafername=None, devicenames=None, xloc_probe=None, yloc_probe=None,xloc0=0,xloc1=0,yloc0=0,yloc1=0,devicenamemodifier=""):
	if pathname == None:    raise ValueError("ERROR! No pathname provided")
	if wafername == None:    raise ValueError("ERROR! No wafername provided")
	if devicenames == None:    raise ValueError("ERROR! No device name provided")
	if devicenamemodifier!="": devicenamemodifier="_"+devicenamemodifier
	pathname_IV = "".join([pathname, sub("DC")])
	if not hasattr(self, 'Id0_foc') or not hasattr(self, 'Id1_foc'): raise ValueError(
		"ERROR! missing family of curves data")

	# write the family of curves data for the first TLM structure.
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicenames[0],"_foc.xls"])
	# now write the family of curves data for the current set of most recently measured or read data
	ffoc = open(filename, 'w')
	# parameters
	ffoc.write("".join(['# wafer name\t', wafername, '\n']))
	ffoc.write("".join(['# device name\t',wafername,"__",devicenames[0],'\n']))
	if xloc_probe!=None and yloc_probe!=None:
		ffoc.write('# x location um\t%d\n' % (int(xloc_probe)))
		ffoc.write('# y location um\t%d\n' % (int(yloc_probe)))
	else:       # xloc0,yloc0 is the device 0 location xloc1,yloc1 is the device 1 location
		ffoc.write('# x location um\t%d\n' % (int(xloc0)))
		ffoc.write('# y location um\t%d\n' % (int(yloc0)))

	# datetimestamp
	ffoc.write('# year\t' + str(dt.datetime.now().year) + '\n')
	ffoc.write('# month\t' + str(dt.datetime.now().month) + '\n')
	ffoc.write('# day\t' + str(dt.datetime.now().day) + '\n')
	ffoc.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	ffoc.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	ffoc.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	ffoc.write('# Vgs\tVds\tId\tIg\tdrainstatus\tgatestatus\n')
	for iVgs in range(0, len(self.Id0_foc)):
		ffoc.write('# Vgs =\t %10.2f\n' % self.Vgs0_foc[iVgs][0])
		for iVds in range(0, len(self.Id0_foc[iVgs])):
			ffoc.write('%10.2f\t %10.2f\t %10.2E\t%10.2E\t%s\t%s\n' % (
				self.Vgs0_foc[iVgs][iVds], self.Vds0_foc[iVgs][iVds], self.Id0_foc[iVgs][iVds], self.Ig0_foc[iVgs][iVds],
				self.drainstatus0_foc[iVgs][iVds], self.gatestatus0_foc[iVgs][iVds]))
	ffoc.close()

	# write the family of curves data for the second TLM structure.
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicenames[1],"_foc.xls"])
	# now write the family of curves data for the current set of most recently measured or read data
	ffoc = open(filename, 'w')
	# parameters
	ffoc.write("".join(['# wafer name\t', wafername, '\n']))
	ffoc.write("".join(['# device name\t',wafername,"__",devicenames[1],'\n']))
	if xloc_probe!=None and yloc_probe!=None:
		ffoc.write('# x location um\t%d\n' % (int(xloc_probe)))
		ffoc.write('# y location um\t%d\n' % (int(yloc_probe)))
	else:       # xloc0,yloc0 is the device 0 location xloc1,yloc1 is the device 1 location
		ffoc.write('# x location um\t%d\n' % (int(xloc1)))
		ffoc.write('# y location um\t%d\n' % (int(yloc1)))
	# datetimestamp
	ffoc.write('# year\t' + str(dt.datetime.now().year) + '\n')
	ffoc.write('# month\t' + str(dt.datetime.now().month) + '\n')
	ffoc.write('# day\t' + str(dt.datetime.now().day) + '\n')
	ffoc.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	ffoc.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	ffoc.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	ffoc.write('# Vgs\tVds\tId\tIg\tdrainstatus\tgatestatus\n')
	for iVgs in range(0, len(self.Id1_foc)):
		ffoc.write('# Vgs =\t %10.2f\n' % self.Vgs1_foc[iVgs][0])
		for iVds in range(0, len(self.Id1_foc[iVgs])):
			ffoc.write('%10.2f\t %10.2f\t %10.2E\t%10.2E\t%s\t%s\n' % (
				self.Vgs1_foc[iVgs][iVds], self.Vds1_foc[iVgs][iVds], self.Id1_foc[iVgs][iVds], self.Ig1_foc[iVgs][iVds],
				self.drainstatus1_foc[iVgs][iVds], self.gatestatus1_foc[iVgs][iVds]))
	ffoc.close()
	return [filename, devicenames]
######################################################################################################################################################
######################################################################################################################################################
# write current IV transfer curve results to a file
# Inputs:
# pathname
def X_writefile_ivtransfer(self,pathname=None,devicename=None,wafername=None,xloc=0,yloc=0,devicenamemodifier=""):
	pathname_IV ="".join([pathname, sub("DC")])
	if devicenamemodifier!="": devicenamemodifier= "".join(["_",devicenamemodifier])
	try:
		self.Id_t  # does the transfer curve exist?
	except:
		print("ERROR! NO transfer curve exists! NO transfer curve written!")
		return
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	filename="".join([pathname_IV,"/",wafername,devicenamemodifier,"__",devicename,"_transfer.xls"])
	ftransfer = open(filename, 'w')
	# parameters
	ftransfer.write('# wafer name\t' + wafername + '\n')
	ftransfer.write('# device name\t' + wafername+devicenamemodifier+"__"+devicename+'\n')
	ftransfer.write('# x location um\t%d\n' % (int(xloc)))
	ftransfer.write('# y location um\t%d\n' % (int(yloc)))
	ftransfer.write('# drain voltage, Vds (V)\t%10.2f\n' % (self.Vds_t[0]))
	if hasattr(self,"dithertime"):  # then this is a dither transfer curve
		ftransfer.write('# dithertime sec\t' + str(self.dithertime) + '\n')
		ftransfer.write('# dithertime step sec\t' + str(self.dithertimestep) + '\n')
		ftransfer.write('# Vgs soak time at end of Vgs dither sec\t' + str(self.soaktime) + '\n')
	# timestamp
	ftransfer.write('# year\t' + str(dt.datetime.now().year) + '\n')
	ftransfer.write('# month\t' + str(dt.datetime.now().month) + '\n')
	ftransfer.write('# day\t' + str(dt.datetime.now().day) + '\n')
	ftransfer.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	ftransfer.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	ftransfer.write('# second\t' + str(dt.datetime.now().second) + '\n')

	# data
	ftransfer.write('# Vgs\tId(A)\tIg\tdrainstatus\tgatestatus\n')

	for ii in range(0, len(self.Id_t)):
		ftransfer.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\n' % (
			self.Vgs_t[ii], self.Id_t[ii], self.Ig_t[ii], self.drainstatus_t[ii], self.gatestatus_t[ii]))
	ftransfer.close()
	return [filename, devicename]
######################################################################################################################################################
# write dual device current IV transfer single-swept curves results to files
# Inputs:
# pathname
def X_writefile_ivtransfer_dual(self, pathname=None, wafername=None, devicenames=None, devicenamemodifier="",xloc_probe=None, yloc_probe=None,xloc0=None,xloc1=None,yloc0=None,yloc1=None):
	if pathname == None:    raise ValueError("ERROR! No pathname provided")
	if wafername == None:    raise ValueError("ERROR! No wafername provided")
	if devicenames == None:    raise ValueError("ERROR! No device name provided")

	pathname_IV = "".join([pathname, sub("DC")])
	if not hasattr(self, 'Id0_t') or not hasattr(self, 'Id1_t'): raise ValueError(
		"ERROR! missing forward transfer curve data")

	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	# timestamp
	if devicenamemodifier!="": devicenamemodifier="_"+devicenamemodifier

	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicenames[0],"_transfer.xls"])
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	ftransfer = open(filename, 'w')
	# parameters
	ftransfer.write('# wafer name\t' + wafername + '\n')
	# write drain0 current
	ftransfer.write("".join(['# device name\t',wafername,"__",devicenames[0],'\n']))
	if xloc0==None and yloc0==None:
		ftransfer.write('# x location um\t%d\n' % (int(xloc_probe)))
		ftransfer.write('# y location um\t%d\n' % (int(yloc_probe)))
	else:       # xloc0,yloc0 is the device 0 location xloc1,yloc1 is the device 1 location
		ftransfer.write('# x location um\t%d\n' % (int(xloc0)))
		ftransfer.write('# y location um\t%d\n' % (int(yloc0)))

	ftransfer.write('# drain voltage, Vds (V)\t%10.7f\n' % (self.Vds0_t[0]))
	# timestamp
	ftransfer.write('# year\t' + str(dt.datetime.now().year) + '\n')
	ftransfer.write('# month\t' + str(dt.datetime.now().month) + '\n')
	ftransfer.write('# day\t' + str(dt.datetime.now().day) + '\n')
	ftransfer.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	ftransfer.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	ftransfer.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	ftransfer.write('# Vgs\tId(A)\tIg\tdrainstatus\tgatestatus\n')

	for ii in range(0, len(self.Id0_t)):
		ftransfer.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\n' % (
			self.Vgs_t[ii], self.Id0_t[ii], self.Ig_t[ii], self.drain0status_t[ii], self.gatestatus_t[ii]))
	ftransfer.close()

	# write drain1 current
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicenames[1],"_transfer.xls"])
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	ftransfer = open(filename, 'w')
	# parameters
	ftransfer.write('# wafer name\t' + wafername + '\n')
	ftransfer.write("".join(['# device name\t',wafername,"__",devicenames[1],'\n']))
	if xloc1==None and yloc1==None:
		ftransfer.write('# x location um\t%d\n' % (int(xloc_probe)))
		ftransfer.write('# y location um\t%d\n' % (int(yloc_probe)))
	else:       # xloc0,yloc0 is the device 0 location xloc1,yloc1 is the device 1 location
		ftransfer.write('# x location um\t%d\n' % (int(xloc1)))
		ftransfer.write('# y location um\t%d\n' % (int(yloc1)))

	# ftransfer.write('# x location um\t%d\n' % (int(xloc_probe)))
	# ftransfer.write('# y location um\t%d\n' % (int(yloc_probe)))
	ftransfer.write('# drain voltage, Vds (V)\t%10.2f\n' % (self.Vds1_t[0]))
	# timestamp
	ftransfer.write('# year\t' + str(dt.datetime.now().year) + '\n')
	ftransfer.write('# month\t' + str(dt.datetime.now().month) + '\n')
	ftransfer.write('# day\t' + str(dt.datetime.now().day) + '\n')
	ftransfer.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	ftransfer.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	ftransfer.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	ftransfer.write('# Vgs\tId(A)\tIg\tdrainstatus\tgatestatus\n')

	for ii in range(0, len(self.Id1_t)):
		ftransfer.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\n' % (
			self.Vgs_t[ii], self.Id1_t[ii], self.Ig_t[ii], self.drain1status_t[ii], self.gatestatus_t[ii]))
	ftransfer.close()
	return [filename, devicenames[0], devicenames[1]]


######################################################################################################################################################
######################################################################################################################################################
# topgated devices measured two at a time
# write dual device current IV transfer single-swept curves results to files
# Inputs:
# pathname
# probe layout: gate1: CH2       drain1: CH4
#               gate0: CH1       drain0: CH3
def X_writefile_ivtransfer_dual_topgate(self, pathname=None, wafername=None, devicenames=None, devicenamemodifier="",xloc0=0,xloc1=0,yloc0=0,yloc1=0):
	if pathname == None:    raise ValueError("ERROR! No pathname provided")
	if wafername == None:    raise ValueError("ERROR! No wafername provided")
	if devicenames == None:    raise ValueError("ERROR! No device name provided")
	if devicenamemodifier!="": devicenamemodifier="_"+devicenamemodifier

	pathname_IV = "".join([pathname, sub("DC")])
	if not hasattr(self, 'Id0_t') or not hasattr(self, 'Id1_t'): raise ValueError(
		"ERROR! missing forward transfer curve data")

	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)

	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicenames[0],"_transfer.xls"])

	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	ftransfer = open(filename, 'w')
	# parameters
	ftransfer.write('# wafer name\t' + wafername + '\n')
	# write gate0 and drain0 data
	ftransfer.write("".join(['# device name\t',wafername,devicenamemodifier,"__",devicenames[0],'\n']))
	# xloc0,yloc0 is the device 0 location xloc1,yloc1 is the device 1 location
	ftransfer.write('# x location um\t%d\n' % (int(xloc0)))
	ftransfer.write('# y location um\t%d\n' % (int(yloc0)))

	ftransfer.write('# drain voltage, Vds (V)\t%10.2f\n' % (self.Vds0_t[0]))
	# timestamp
	ftransfer.write('# year\t' + str(dt.datetime.now().year) + '\n')
	ftransfer.write('# month\t' + str(dt.datetime.now().month) + '\n')
	ftransfer.write('# day\t' + str(dt.datetime.now().day) + '\n')
	ftransfer.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	ftransfer.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	ftransfer.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	ftransfer.write('# Vgs\tId(A)\tIg\tdrainstatus\tgatestatus\n')

	for ii in range(0, len(self.Id0_t)):
		ftransfer.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\n' % (
			self.Vgs0_t[ii], self.Id0_t[ii], self.Ig0_t[ii], self.drain0status_t[ii], self.gate0status_t[ii]))
	ftransfer.close()

	# write gate1 and drain1 data
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicenames[1],"_transfer.xls"])
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	ftransfer = open(filename, 'w')
	# parameters
	ftransfer.write('# wafer name\t' + wafername + '\n')
	ftransfer.write("".join(['# device name\t',wafername,devicenamemodifier,"__",devicenames[1],'\n']))
	# if xloc_probe!=None and yloc_probe!=None:
	# 	ftransfer.write('# x location um\t%d\n' % (int(xloc_probe)))
	# 	ftransfer.write('# y location um\t%d\n' % (int(yloc_probe)))
	#else:       # xloc0,yloc0 is the device 0 location xloc1,yloc1 is the device 1 location
	ftransfer.write('# x location um\t%d\n' % (int(xloc1)))
	ftransfer.write('# y location um\t%d\n' % (int(yloc1)))

	# ftransfer.write('# x location um\t%d\n' % (int(xloc_probe)))
	# ftransfer.write('# y location um\t%d\n' % (int(yloc_probe)))
	ftransfer.write('# drain voltage, Vds (V)\t%10.2f\n' % (self.Vds1_t[0]))
	# timestamp
	ftransfer.write('# year\t' + str(dt.datetime.now().year) + '\n')
	ftransfer.write('# month\t' + str(dt.datetime.now().month) + '\n')
	ftransfer.write('# day\t' + str(dt.datetime.now().day) + '\n')
	ftransfer.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	ftransfer.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	ftransfer.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	ftransfer.write('# Vgs\tId(A)\tIg\tdrainstatus\tgatestatus\n')

	for ii in range(0, len(self.Id1_t)):
		ftransfer.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\n' % (
			self.Vgs1_t[ii], self.Id1_t[ii], self.Ig1_t[ii], self.drain1status_t[ii], self.gate1status_t[ii]))
	ftransfer.close()
	return [filename, devicenames[0], devicenames[1]]
######################################################################################################################################################
# write current IV transfer loop (bidirectional Vgs sweep) curve and gmloop results to a file
# Inputs:
# pathname
# now handles the case of application of a constant backgating voltage while sweeping the gate
def X_writefile_ivtransferloop(self,pathname=None,devicename=None,wafername=None,xloc_probe=0,yloc_probe=0,devicenamemodifier=""):
	pathname_IV ="".join([pathname, sub("DC")])
	if hasattr(self, 'Ibg_tf') and hasattr(self, 'Ibg_tr'):   # then this is a transfer loop with a constant backgate voltage applied
		backgated=True
	else: backgated=False
	if devicenamemodifier!="": devicenamemodifier="".join(["_",devicenamemodifier])
	try:
		self.Id_tf  # does the forward transfer curve exist?
	except:
		print("ERROR! NO forward loop transfer curve exists! NO transferloop curve written!")
		return
	try:
		self.Id_tr  # does the reverse transfer curve exist?
	except:
		print("ERROR! NO reverse loop transfer curve exists! NO transferloop curve written!")
		return

	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename, "_transferloop.xls"])
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	ftransferloop = open(filename, 'w')
	# parameters
	ftransferloop.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename]) + '\n')
	ftransferloop.write('# wafer name\t' + wafername + '\n')

	if backgated: ftransferloop.write('# backgate voltage (V)\t'+formatnum(self.Vbackgate,precision=2)+'\n')

	ftransferloop.write('# x location um\t%d\n' % (int(xloc_probe)))
	ftransferloop.write('# y location um\t%d\n' % (int(yloc_probe)))
	ftransferloop.write('# drain voltage, Vds (V)\t%10.2f\n' % (self.Vds_tf[0]))
	if hasattr(self,"elapsed_time") and hasattr(self,"Vgsslew") and self.elapsed_time!=None and self.Vgsslew!=None:
		ftransferloop.write('# Elapsed Time of measurment (sec)\t%10.2f\n' % (self.elapsed_time))
		ftransferloop.write('# Vgs rate of change (V/sec)\t%10.2f\n' % (self.Vgsslew))
	ftransferloop.write('# quiescent time prior to measurements (sec)\t%10.2f\n' % (self.quiescenttime))
	# datetimestamp
	ftransferloop.write('# year\t' + str(dt.datetime.now().year) + '\n')
	ftransferloop.write('# month\t' + str(dt.datetime.now().month) + '\n')
	ftransferloop.write('# day\t' + str(dt.datetime.now().day) + '\n')
	ftransferloop.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	ftransferloop.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	ftransferloop.write('# second\t' + str(dt.datetime.now().second) + '\n')
	if hasattr(self,'startstopzero') and self.startstopzero:       # did the Vgs start and stop at Vgs=0V?
		ftransferloop.write('# start and stop at Vgs=0V\n')
		ftransferloop.write('# minimum quiescent time at Vgs=0V and Vds=0V\t%10.2f\tsec\n' %(self.quiescenttime))

	############## write data #####################################################
	#### for case with backgate voltage applied
	if backgated:
		ftransferloop.write('# Vgs\tIdloop(A)\tIgloop\tdrainstatus\tgatestatus\tIbg\tbackgatestatus\ttimestamp sec\n')
		ftransferloop.write('# forward Vgs sweep\n')
		for ii in range(0, len(self.Id_tf)):
			ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.2E\t %s\t %10.2E\n' % (self.Vgs_tf[ii], self.Id_tf[ii], self.Ig_tf[ii], self.drainstatus_tf[ii], self.gatestatus_tf[ii],self.Ibg_tf[ii],self.backgatestatus_tf[ii], self.timestamp_tf[ii]))
		ftransferloop.write('# reverse Vgs sweep\n')
		for ii in range(0, len(self.Id_tr)):
			ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.2E\t %s\t %10.2E\n' % (self.Vgs_tr[ii], self.Id_tr[ii], self.Ig_tr[ii], self.drainstatus_tr[ii], self.gatestatus_tr[ii], self.Ibg_tr[ii], self.backgatestatus_tr[ii], self.timestamp_tr[ii]))
		ftransferloop.close()

	#### for case with no backgate voltage applied
	else:
		ftransferloop.write('# Vgs\tIdloop(A)\tIgloop\tdrainstatus\tgatestatus\ttimestamp sec\n')
		ftransferloop.write('# forward Vgs sweep\n')
		for ii in range(0, len(self.Id_tf)):
			ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.2E\n' % (self.Vgs_tf[ii], self.Id_tf[ii], self.Ig_tf[ii], self.drainstatus_tf[ii], self.gatestatus_tf[ii], self.timestamp_tf[ii]))
		ftransferloop.write('# reverse Vgs sweep\n')
		for ii in range(0, len(self.Id_tr)):
			ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.2E\n' % (self.Vgs_tr[ii], self.Id_tr[ii], self.Ig_tr[ii], self.drainstatus_tr[ii], self.gatestatus_tr[ii], self.timestamp_tr[ii]))
		ftransferloop.close()

	return [filename, devicename]
###################################################################################################################################################################
######################################################################################################################################################
# write dual device IV transfer loop (bidirectional Vgs sweep) curve results to a file
# Inputs:
# pathname
#
def X_writefile_ivtransferloop_dual(self, pathname=None, wafername=None, devicenames=None, devicenamemodifier="",xloc0=None, yloc0=None,xloc1=None, yloc1=None):
	if pathname == None:    raise ValueError("ERROR! No pathname provided")
	if wafername == None:    raise ValueError("ERROR! No wafername provided")
	if devicenames == None:    raise ValueError("ERROR! No device name provided")

	pathname_IV = "".join([pathname, sub("DC")])
	if not hasattr(self, 'Id0_tf') or not hasattr(self, 'Id1_tf'): raise ValueError(
		"ERROR! missing forward transfer curve data")

	# drain0 current
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	devicename0=devicenames[0]
	devicename1=devicenames[1]
	if devicenamemodifier!="": devicenamemodifier="".join(["_",devicenamemodifier])

	### first device (left side)
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename0, "_transferloop.xls"])

	ftransferloop = open(filename, 'w')
	# parameters
	ftransferloop.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename0]) + '\n')
	ftransferloop.write('# wafer name\t' + wafername + '\n')
	ftransferloop.write('# x location um\t%d\n' % (int(xloc0)))
	ftransferloop.write('# y location um\t%d\n' % (int(yloc0)))
	ftransferloop.write('# drain voltage, Vds (V)\t%10.2f\n' % (self.Vds0_tf[0]))
	# if hasattr(self,"elapsed_time") and hasattr(self,"Vgsslew") and self.Vgsslew!=None:
	# 	ftransferloop.write('# Vgs rate of change (V/sec)\t%10.2f\n' % (self.Vgsslew))
	ftransferloop.write('# Elapsed Time of measurment (sec)\t%10.2f\n' % (self.elapsed_time))
	ftransferloop.write('# Vgs rate of change (V/sec)\t%10.2f\n' % (self.Vgsslew))
	# timestamp
	ftransferloop.write('# year\t' + str(dt.datetime.now().year) + '\n')
	ftransferloop.write('# month\t' + str(dt.datetime.now().month) + '\n')
	ftransferloop.write('# day\t' + str(dt.datetime.now().day) + '\n')
	ftransferloop.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	ftransferloop.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	ftransferloop.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	ftransferloop.write('# Vgs\tIdloop(A)\tIgloop\tdrainstatus\tgatestatus\ttimestamp sec\n')
	ftransferloop.write('# forward Vgs sweep\n')
	for ii in range(0, len(self.Id0_tf)):
		ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs_tf[ii], self.Id0_tf[ii], self.Ig_tf[ii], self.drain0status_tf[ii], self.gatestatus_tf[ii],self.timestamp_tf[ii]))
	ftransferloop.write('# reverse Vgs sweep\n')
	for ii in range(0, len(self.Id0_tr)):
		ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs_tr[ii], self.Id0_tr[ii], self.Ig_tr[ii], self.drain0status_tr[ii], self.gatestatus_tr[ii],self.timestamp_tr[ii]))
	ftransferloop.close()

	# drain1 current
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename1, "_transferloop.xls"])
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	ftransferloop = open(filename, 'w')

	# parameters
	ftransferloop.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename1]) + '\n')
	ftransferloop.write('# wafer name\t' + wafername + '\n')
	ftransferloop.write('# x location um\t%d\n' % (int(xloc1)))
	ftransferloop.write('# y location um\t%d\n' % (int(yloc1)))
	ftransferloop.write('# drain voltage, Vds (V)\t%10.2f\n' % (self.Vds1_tf[0]))
	# timestamp
	ftransferloop.write('# year\t' + str(dt.datetime.now().year) + '\n')
	ftransferloop.write('# month\t' + str(dt.datetime.now().month) + '\n')
	ftransferloop.write('# day\t' + str(dt.datetime.now().day) + '\n')
	ftransferloop.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	ftransferloop.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	ftransferloop.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	ftransferloop.write('# Vgs\tIdloop(A)\tIgloop\tdrainstatus\tgatestatus\ttimestamp sec\n')
	ftransferloop.write('# forward Vgs sweep\n')
	for ii in range(0, len(self.Id1_tf)):
		ftransferloop.write('%10.2f\t%10.2E\t%10.2E\t%s\t%s\t%10.4E\n' % (self.Vgs_tf[ii], self.Id1_tf[ii], self.Ig_tf[ii], self.drain1status_tf[ii], self.gatestatus_tf[ii],self.timestamp_tf[ii]))
	ftransferloop.write('# reverse Vgs sweep\n')
	for ii in range(0, len(self.Id1_tr)):
		ftransferloop.write('%10.2f\t%10.2E\t%10.2E\t%s\t%s\t%10.4E\n' % (self.Vgs_tr[ii], self.Id1_tr[ii], self.Ig_tr[ii], self.drain1status_tr[ii], self.gatestatus_tr[ii],self.timestamp_tr[ii]))
	ftransferloop.close()
	return [filename, devicenames[0], devicenames[1]]
######################################################################################################################################################
# write dual device IV transfer loop having 2x around loop - 4 sweeps  curve results to a file
# takes output from Parameteranalyzer::measure_ivtransferloop_4sweep_controlledslew_dual_backgated()
# Inputs:
# pathname
#
def X_writefile_ivtransferloop_4sweep_dual(self,backgated=True, pathname=None, wafername=None, devicenames=None, devicenamemodifier="",xloc0=None, yloc0=None,xloc1=None, yloc1=None):
	if pathname == None:    raise ValueError("ERROR! No pathname provided")
	if wafername == None:    raise ValueError("ERROR! No wafername provided")
	if devicenames == None:    raise ValueError("ERROR! No device name provided")

	pathname_IV = "".join([pathname, sub("DC")])
	if not hasattr(self, 'Id0_t1') or not hasattr(self, 'Id1_t1'): raise ValueError("ERROR! missing forward transfer curve data")

	# drain0 current
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	devicename0=devicenames[0]
	devicename1=devicenames[1]
	if devicenamemodifier!="": devicenamemodifier="".join(["_",devicenamemodifier])

	### first device (left side)
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename0, "_transferloop4.xls"])
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	ftransferloop = open(filename, 'w')
	# parameters
	ftransferloop.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename0, "_transferloop4.xls"]) + '\n')
	ftransferloop.write('# wafer name\t' + wafername + '\n')
	ftransferloop.write('# x location um\t%d\n' % (int(xloc0)))
	ftransferloop.write('# y location um\t%d\n' % (int(yloc0)))
	ftransferloop.write('# drain voltage, Vds (V)\t%10.2f\n' % (self.Vds0_t1[0]))
	ftransferloop.write('# Elapsed Time of measurment (sec)\t%10.2f\n' % (self.elapsed_time))
	ftransferloop.write('# Vgs rate of change (V/sec)\t%10.2f\n' % (self.Vgsslew))
	if hasattr(self,'startstopzero') and self.startstopzero:       # did the Vgs start and stop at Vgs=0V?
		ftransferloop.write('# start and stop at Vgs=0V\n')
		ftransferloop.write('# minimum quiescent time at Vgs=0V and Vds=0V\t%10.2f\tsec\n' %(self.quiescenttime))

	# timestamp
	ftransferloop.write('# year\t' + str(dt.datetime.now().year) + '\n')
	ftransferloop.write('# month\t' + str(dt.datetime.now().month) + '\n')
	ftransferloop.write('# day\t' + str(dt.datetime.now().day) + '\n')
	ftransferloop.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	ftransferloop.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	ftransferloop.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	if backgated:
		ftransferloop.write('# Vgs\tIdloop(A)\tIgloop\tdrainstatus\tgatestatus\ttimestamp sec\n')
		ftransferloop.write('# 1st Vgs sweep\n')
		for ii in range(0, len(self.Id0_t1)):ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs_t1[ii], self.Id0_t1[ii], self.Ig_t1[ii], self.drainstatus0_t1[ii], self.gatestatus_t1[ii],self.timestamp_t1[ii]))
		ftransferloop.write('# 2nd Vgs sweep\n')
		for ii in range(0, len(self.Id0_t2)): ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs_t2[ii], self.Id0_t2[ii], self.Ig_t2[ii], self.drainstatus0_t2[ii], self.gatestatus_t2[ii],self.timestamp_t2[ii]))
		ftransferloop.write('# 3rd Vgs sweep\n')
		for ii in range(0, len(self.Id0_t3)): ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs_t3[ii], self.Id0_t3[ii], self.Ig_t3[ii], self.drainstatus0_t3[ii], self.gatestatus_t3[ii],self.timestamp_t3[ii]))
		ftransferloop.write('# 4th Vgs sweep\n')
		for ii in range(0, len(self.Id0_t4)): ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs_t4[ii], self.Id0_t4[ii], self.Ig_t4[ii], self.drainstatus0_t4[ii], self.gatestatus_t4[ii],self.timestamp_t4[ii]))
	else: # topgated
		ftransferloop.write('# Vgs\tIdloop(A)\tIgloop\tdrainstatus\tgatestatus\ttimestamp sec\n')
		ftransferloop.write('# 1st Vgs sweep\n')
		for ii in range(0, len(self.Id0_t1)):ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs0_t1[ii], self.Id0_t1[ii], self.Ig0_t1[ii], self.drainstatus0_t1[ii], self.gatestatus0_t1[ii],self.timestamp_t1[ii]))
		ftransferloop.write('# 2nd Vgs sweep\n')
		for ii in range(0, len(self.Id0_t2)): ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs0_t2[ii], self.Id0_t2[ii], self.Ig0_t2[ii], self.drainstatus0_t2[ii], self.gatestatus0_t2[ii],self.timestamp_t2[ii]))
		ftransferloop.write('# 3rd Vgs sweep\n')
		for ii in range(0, len(self.Id0_t3)): ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs0_t3[ii], self.Id0_t3[ii], self.Ig0_t3[ii], self.drainstatus0_t3[ii], self.gatestatus0_t3[ii],self.timestamp_t3[ii]))
		ftransferloop.write('# 4th Vgs sweep\n')
		for ii in range(0, len(self.Id0_t4)): ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs0_t4[ii], self.Id0_t4[ii], self.Ig0_t4[ii], self.drainstatus0_t4[ii], self.gatestatus0_t4[ii],self.timestamp_t4[ii]))
	ftransferloop.close()

### 2nd device (left side)
	# drain1 current
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename1, "_transferloop4.xls"])
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	ftransferloop = open(filename, 'w')

	# parameters
	ftransferloop.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename1, "_transferloop4.xls"]) + '\n')
	ftransferloop.write('# wafer name\t' + wafername + '\n')
	ftransferloop.write('# x location um\t%d\n' % (int(xloc1)))
	ftransferloop.write('# y location um\t%d\n' % (int(yloc1)))
	ftransferloop.write('# drain voltage, Vds (V)\t%10.2f\n' % (self.Vds1_t1[0]))
	ftransferloop.write('# Elapsed Time of measurment (sec)\t%10.2f\n' % (self.elapsed_time))
	ftransferloop.write('# Vgs rate of change (V/sec)\t%10.2f\n' % (self.Vgsslew))
	if hasattr(self,'startstopzero') and self.startstopzero:       # did the Vgs start and stop at Vgs=0V?
		ftransferloop.write('# start and stop at Vgs=0V\n')
		ftransferloop.write('# minimum quiescent time at Vgs=0V and Vds=0V\t%10.2f\tsec\n' %(self.quiescenttime))
	# timestamp
	ftransferloop.write('# year\t' + str(dt.datetime.now().year) + '\n')
	ftransferloop.write('# month\t' + str(dt.datetime.now().month) + '\n')
	ftransferloop.write('# day\t' + str(dt.datetime.now().day) + '\n')
	ftransferloop.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	ftransferloop.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	ftransferloop.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	if backgated:
		ftransferloop.write('# Vgs\tIdloop(A)\tIgloop\tdrainstatus\tgatestatus\ttimestamp sec\n')
		ftransferloop.write('# 1st Vgs sweep\n')
		for ii in range(0, len(self.Id1_t1)):ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs_t1[ii], self.Id1_t1[ii], self.Ig_t1[ii], self.drainstatus1_t1[ii], self.gatestatus_t1[ii],self.timestamp_t1[ii]))
		ftransferloop.write('# 2nd Vgs sweep\n')
		for ii in range(0, len(self.Id1_t2)): ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs_t2[ii], self.Id1_t2[ii], self.Ig_t2[ii], self.drainstatus1_t2[ii], self.gatestatus_t2[ii],self.timestamp_t2[ii]))
		ftransferloop.write('# 3rd Vgs sweep\n')
		for ii in range(0, len(self.Id1_t3)): ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs_t3[ii], self.Id1_t3[ii], self.Ig_t3[ii], self.drainstatus1_t3[ii], self.gatestatus_t3[ii],self.timestamp_t3[ii]))
		ftransferloop.write('# 4th Vgs sweep\n')
		for ii in range(0, len(self.Id1_t4)): ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs_t4[ii], self.Id1_t4[ii], self.Ig_t4[ii], self.drainstatus1_t4[ii], self.gatestatus_t4[ii],self.timestamp_t4[ii]))
	else: # topgated
		ftransferloop.write('# Vgs\tIdloop(A)\tIgloop\tdrainstatus\tgatestatus\ttimestamp sec\n')
		ftransferloop.write('# 1st Vgs sweep\n')
		for ii in range(0, len(self.Id1_t1)):ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs1_t1[ii], self.Id1_t1[ii], self.Ig1_t1[ii], self.drainstatus1_t1[ii], self.gatestatus1_t1[ii],self.timestamp_t1[ii]))
		ftransferloop.write('# 2nd Vgs sweep\n')
		for ii in range(0, len(self.Id1_t2)): ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs1_t2[ii], self.Id1_t2[ii], self.Ig1_t2[ii], self.drainstatus1_t2[ii], self.gatestatus1_t2[ii],self.timestamp_t2[ii]))
		ftransferloop.write('# 3rd Vgs sweep\n')
		for ii in range(0, len(self.Id1_t3)): ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs1_t3[ii], self.Id1_t3[ii], self.Ig1_t3[ii], self.drainstatus1_t3[ii], self.gatestatus1_t3[ii],self.timestamp_t3[ii]))
		ftransferloop.write('# 4th Vgs sweep\n')
		for ii in range(0, len(self.Id1_t4)): ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs1_t4[ii], self.Id1_t4[ii], self.Ig1_t4[ii], self.drainstatus1_t4[ii], self.gatestatus1_t4[ii],self.timestamp_t4[ii]))

	ftransferloop.close()
	return [filename, devicenames]
###################################################################################################################################################################
######################################################################################################################################################
# write single device IV transfer loop having 2x around loop - 4 sweeps  curve results to a file
# Inputs:
# pathname
#
def X_writefile_ivtransferloop_4sweep(self, pathname=None, wafername=None, devicename=None, xloc=None, yloc=None, devicenamemodifier=""):
	if pathname == None:    raise ValueError("ERROR! No pathname provided")
	if wafername == None:    raise ValueError("ERROR! No wafername provided")
	if devicename == None:    raise ValueError("ERROR! No device name provided")
	#if devicenamemodifier!="": devicenamemodifier="".join(["_",devicenamemodifier])
	pathname_IV = "".join([pathname, sub("DC")])
	if not hasattr(self, 'Id_t1'): raise ValueError("ERROR! missing forward transfer curve data")

	# drain current
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	if devicenamemodifier!="": devicenamemodifier="_"+devicenamemodifier

	### first device (left side)

	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename, "_transferloop4.xls"])

	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	ftransferloop = open(filename, 'w')
	# parameters
	ftransferloop.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename]) + '\n')
	ftransferloop.write('# wafer name\t' + wafername + '\n')
	ftransferloop.write('# x location um\t%d\n' % (int(xloc)))
	ftransferloop.write('# y location um\t%d\n' % (int(yloc)))
	ftransferloop.write('# drain voltage, Vds (V)\t%10.2f\n' % (self.Vds_t1[0]))
	ftransferloop.write('# Elapsed Time of measurment (sec)\t%10.2f\n' % (self.elapsed_time))
	ftransferloop.write('# Vgs rate of change (V/sec)\t%10.2f\n' % (self.Vgsslew))
	if hasattr(self,'startstopzero') and self.startstopzero:       # did the Vgs start and stop at Vgs=0V?
		ftransferloop.write('# start and stop at Vds=0V\n')
	ftransferloop.write('# minimum quiescent time at Vgs=0V and Vds=0V\t%10.2f\tsec\n' %(self.quiescenttime))
	# timestamp
	ftransferloop.write('# year\t' + str(dt.datetime.now().year) + '\n')
	ftransferloop.write('# month\t' + str(dt.datetime.now().month) + '\n')
	ftransferloop.write('# day\t' + str(dt.datetime.now().day) + '\n')
	ftransferloop.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	ftransferloop.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	ftransferloop.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	ftransferloop.write('# Vgs\tIdloop(A)\tIgloop\tdrainstatus\tgatestatus\ttimestamp sec\n')
	ftransferloop.write('# 1st Vgs sweep\n')
	for ii in range(0, len(self.Id_t1)):ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs_t1[ii], self.Id_t1[ii], self.Ig_t1[ii], self.drainstatus_t1[ii], self.gatestatus_t1[ii],self.timestamp_t1[ii]))
	ftransferloop.write('# 2nd Vgs sweep\n')
	for ii in range(0, len(self.Id_t2)): ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs_t2[ii], self.Id_t2[ii], self.Ig_t2[ii], self.drainstatus_t2[ii], self.gatestatus_t2[ii],self.timestamp_t2[ii]))
	ftransferloop.write('# 3rd Vgs sweep\n')
	for ii in range(0, len(self.Id_t3)): ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs_t3[ii], self.Id_t3[ii], self.Ig_t3[ii], self.drainstatus_t3[ii], self.gatestatus_t3[ii],self.timestamp_t3[ii]))
	ftransferloop.write('# 4th Vgs sweep\n')
	for ii in range(0, len(self.Id_t4)): ftransferloop.write('%10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' % (self.Vgs_t4[ii], self.Id_t4[ii], self.Ig_t4[ii], self.drainstatus_t4[ii], self.gatestatus_t4[ii],self.timestamp_t4[ii]))
	ftransferloop.close()
	return [filename, devicename]
###################################################################################################################################################################
# write the current S-parameters to a file using the Touchstone format
# def X_writefile_spar(self, pathname, lotname, wafernumber, diecolumn, dierow, subsitename, xloc, yloc, Vds, Id, drainstatus, Vgs, Ig, gatestatus):
# The device name may be supplied or the parameters from Cascade Nucleus may be supplied to form the devicename
# For user-defined probe test plans, the devicename is obtained from the probe test file and must be supplied to this function as the devicename
def X_writefile_spar(self,measurement_type="all_RI",pathname=None,devicename=None,wafername=None,xloc=None,yloc=None,Vds=0.,Vgs=0.,Id=0.,Ig=0.,gatestatus=None,drainstatus=None,devicenamemodifier=""):
	pathname_RF=pathname+sub("SPAR")
	if devicenamemodifier!="": devicenamemodifier="__"+devicenamemodifier
	try:
		self.freq  # do S-parameter data exist?
	except:
		print("ERROR! NO frequency array so S-parameter data found! NO S-parameter data written")
		return
	if not (hasattr(self,"s11") or hasattr(self,"s11_oneport") or hasattr(self,"s22_oneport")):
		raise ValueError("ERROR from line 783 in pna.py: No S-parameters to write")

	if not os.path.exists(pathname_RF):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_RF)
	#if "ri" in measurement_type.lower(): filename = pathname_RF + "/" + devicename + "_SRI.s2p"
	if devicenamemodifier=="":
		if "ri" in measurement_type.lower(): filename = "".join([pathname_RF,"/",wafername,devicenamemodifier,"__", devicename,"_SRI.s2p"])
		elif "db" in measurement_type.lower(): filename = "".join([pathname_RF,"/",wafername,devicenamemodifier,"__", devicename,"_SDB.s2p"]) #filename = pathname_RF + "/" + devicename + "_SDB.s2p"
		elif "ma" in measurement_type.lower(): filename = "".join([pathname_RF,"/",wafername,devicenamemodifier,"__", devicename,"_MA.s2p"]) #filename = pathname_RF + "/" + devicename + "_MA.s2p"
		else: raise ValueError("ERROR! Illegal value for format of S-parameters")
	else:
		if "ri" in measurement_type.lower(): filename = "".join([pathname_RF,"/",wafername,devicenamemodifier,"_", devicename,"_SRI.s2p"])
		elif "db" in measurement_type.lower(): filename = "".join([pathname_RF,"/",wafername,devicenamemodifier,"_", devicename,"_SDB.s2p"]) #filename = pathname_RF + "/" + devicename + "_SDB.s2p"
		elif "ma" in measurement_type.lower(): filename = "".join([pathname_RF,"/",wafername,devicenamemodifier,"_", devicename,"_MA.s2p"]) #filename = pathname_RF + "/" + devicename + "_MA.s2p"
		else: raise ValueError("ERROR! Illegal value for format of S-parameters")
	fSpar = open(filename, 'w')
	# parameters
	if devicenamemodifier=="": fSpar.write('! device name\t' + "".join([wafername,devicenamemodifier,"__", devicename])+ '\n')
	else: fSpar.write('! device name\t' + "".join([wafername,devicenamemodifier,"_", devicename])+ '\n')
	fSpar.write('! wafer name\t' + wafername + '\n')

	fSpar.write('! x location um\t%d\n' % int(xloc))
	fSpar.write('! y location um\t%d\n' % int(yloc))
	fSpar.write('! Vds (V)\t%10.2f\n' % Vds)
	fSpar.write('! Id (A)\t%10.2E\n' % Id)
	fSpar.write('! drain status\t%s\n' % drainstatus)
	fSpar.write('! Vgs (V)\t%10.2f\n' % Vgs)
	fSpar.write('! Ig (A)\t%10.2E\n' % Ig)
	fSpar.write('! gate status\t%s\n' % gatestatus)
	# timestamp
	fSpar.write('! year\t' + str(dt.datetime.now().year) + '\n')
	fSpar.write('! month\t' + str(dt.datetime.now().month) + '\n')
	fSpar.write('! day\t' + str(dt.datetime.now().day) + '\n')
	fSpar.write('! hour\t' + str(dt.datetime.now().hour) + '\n')
	fSpar.write('! minute\t' + str(dt.datetime.now().minute) + '\n')
	fSpar.write('! second\t' + str(dt.datetime.now().second) + '\n')
	# datatype header
	fSpar.write("!\n!\n")

	# write data to file
	if "all" in measurement_type.lower():         # then we measured all four S-parameters
		if "db" in measurement_type.lower():         # write dB data
			fSpar.write("# GHZ S DB R 50\n")
			fSpar.write("!frequency_GHz S11_dB S11_ang S21_dB S21_ang S12_dB S12_ang S22_dB S22_ang\n")
			for ifr in range(0, len(self.freq)):
				s11dB=convertRItodB(self.s11[ifr])
				s21dB=convertRItodB(self.s21[ifr])
				s12dB=convertRItodB(self.s12[ifr])
				s22dB=convertRItodB(self.s22[ifr])
				fSpar.write("%7.3f" % (1E-9 * self.freq[ifr]))
				fSpar.write((" %7.3E" % (s11dB.real)) + (" %7.3E" % (s11dB.imag)))
				fSpar.write((" %7.3E" % (s21dB.real)) + (" %7.3E" % (s21dB.imag)))
				fSpar.write((" %7.3E" % (s12dB.real)) + (" %7.3E" % (s12dB.imag)))
				fSpar.write((" %7.3E" % (s22dB.real)) + (" %7.3E" % (s22dB.imag)) + "\n")
		elif "ri" in measurement_type.lower():      # real and imaginary
			fSpar.write("# GHZ S RI R 50\n")
			fSpar.write("!frequency_GHz S11_re S11_im S21_re S21_im S12_re S12_im S22_re S22_im\n")
			for ifr in range(0, len(self.freq)):
				fSpar.write("%7.3f" % (1E-9 * self.freq[ifr]))
				fSpar.write((" %7.3E" % (self.s11[ifr].real)) + (" %7.3E" % (self.s11[ifr].imag)))
				fSpar.write((" %7.3E" % (self.s21[ifr].real)) + (" %7.3E" % (self.s21[ifr].imag)))
				fSpar.write((" %7.3E" % (self.s12[ifr].real)) + (" %7.3E" % (self.s12[ifr].imag)))
				fSpar.write((" %7.3E" % (self.s22[ifr].real)) + (" %7.3E" % (self.s22[ifr].imag)) + "\n")
		elif "ma" in measurement_type.lower():      # real and imaginary
			fSpar.write("# GHZ S RI R 50\n")
			fSpar.write("!frequency_GHz S11_mag S11_ang S21_mag S21_ang S12_mag S12_ang S22_mag S22_ang\n")
			for ifr in range(0, len(self.freq)):
				s11ma=convertRItoMA(self.s11[ifr])
				s21ma=convertRItoMA(self.s21[ifr])
				s12ma=convertRItoMA(self.s12[ifr])
				s22ma=convertRItoMA(self.s22[ifr])
				fSpar.write("%7.3f" % (1E-9 * self.freq[ifr]))
				fSpar.write((" %7.3E" % (s11ma.real)) + (" %7.3E" % (s11ma.imag)))
				fSpar.write((" %7.3E" % (s21ma.real)) + (" %7.3E" % (s21ma.imag)))
				fSpar.write((" %7.3E" % (s12ma.real)) + (" %7.3E" % (s12ma.imag)))
				fSpar.write((" %7.3E" % (s22ma.real)) + (" %7.3E" % (s22ma.imag)) + "\n")
		else: raise ValueError("ERROR! must specify S-parameter data format!")
	elif "s11_only" in measurement_type.lower() or "s11" in measurement_type.lower():            # then we measured only s11
		if "db" in measurement_type.lower():         # write dB data
			fSpar.write("# GHZ S DB R 50\n")
			fSpar.write("!frequency_GHz S11_dB S11_ang\n")
			for ifr in range(0, len(self.freq)):
				s11dB=convertRItodB(self.s11_oneport[ifr])
				fSpar.write("%7.3f" % (1E-9 * self.freq[ifr]))
				fSpar.write((" %7.3E" % (s11dB.real)) + (" %7.3E" % (s11dB.imag))+ "\n")
		elif "ri" in measurement_type.lower():      # real and imaginary
			fSpar.write("# GHZ S RI R 50\n")
			fSpar.write("!frequency_GHz S11_re S11_im\n")
			for ifr in range(0, len(self.freq)):
				fSpar.write("%7.3f" % (1E-9 * self.freq[ifr]))
				fSpar.write((" %7.3E" % (self.s11_oneport[ifr].real)) + (" %7.3E" % (self.s11_oneport[ifr].imag))+ "\n")
		elif "ma" in measurement_type.lower():      # real and imaginary
			fSpar.write("# GHZ S RI R 50\n")
			fSpar.write("!frequency_GHz S11_mag S11_ang\n")
			for ifr in range(0, len(self.freq)):
				s11ma=convertRItoMA(self.s11_oneport[ifr])
				fSpar.write("%7.3f" % (1E-9 * self.freq[ifr]))
				fSpar.write((" %7.3E" % (s11ma.real)) + (" %7.3E" % (s11ma.imag))+ "\n")
	elif "s22_only" in measurement_type.lower() or "s22" in measurement_type.lower():            # then we measured only s11
		if "db" in measurement_type.lower():         # write dB data
			fSpar.write("# GHZ S DB R 50\n")
			fSpar.write("!frequency_GHz S22_dB S22_ang\n")
			for ifr in range(0, len(self.freq)):
				s11dB=convertRItodB(self.s22_oneport[ifr])
				fSpar.write("%7.3f" % (1E-9 * self.freq[ifr]))
				fSpar.write((" %7.3E" % (s11dB.real)) + (" %7.3E" % (s11dB.imag))+ "\n")
		elif "ri" in measurement_type.lower():      # real and imaginary
			fSpar.write("# GHZ S RI R 50\n")
			fSpar.write("!frequency_GHz S22_re S22_im\n")
			for ifr in range(0, len(self.freq)):
				fSpar.write("%7.3f" % (1E-9 * self.freq[ifr]))
				fSpar.write((" %7.3E" % (self.s22_oneport[ifr].real)) + (" %7.3E" % (self.s22_oneport[ifr].imag))+ "\n")
		elif "ma" in measurement_type.lower():      # real and imaginary
			fSpar.write("# GHZ S RI R 50\n")
			fSpar.write("!frequency_GHz S22_mag S22_ang\n")
			for ifr in range(0, len(self.freq)):
				s11ma=convertRItoMA(self.s22_oneport[ifr])
				fSpar.write("%7.3f" % (1E-9 * self.freq[ifr]))
				fSpar.write((" %7.3E" % (s11ma.real)) + (" %7.3E" % (s11ma.imag))+ "\n")
		else: raise ValueError("ERROR! must specify S-parameter data format!")
	else: raise ValueError("No valid measurement type specified")
	fSpar.close()
	return [filename, devicename]
##################################################################################################################
####################################################################################################################################################################
# write the current third order products for a given device
# def X_writefile_spar(self, pathname, lotname, wafernumber, diecolumn, dierow, subsitename, xloc, yloc, Vds, Id, drainstatus, Vgs, Ig, gatestatus):
# The device name may be supplied or the parameters from Cascade Nucleus may be supplied to form the devicename
# For user-defined probe test plans, the devicename is obtained from the probe test file and must be supplied to this function as the devicename
def X_writefile_TOI(self, pathname=None, wafername=None, xloc=None, yloc=None, Vds=None, Id=None, drainstatus=None,Vgs=None, Ig=None, gatestatus=None, devicename=None,devicenamemodifier=""):
	if pathname == None: raise ValueError("ERROR Must include pathname")
	if devicename == None: raise ValueError("ERROR Must give device name for this measurement")
	# Form devicename and devicename from function input parameters
	pathname_TOI = pathname + sub("RF_power")
	if devicenamemodifier!="": devicenamemodifier="".join(["_",devicenamemodifier])
	#devicename = formdevicename(wafername, devicename)

	if hasattr(self, 'TOIl') and hasattr(self,'TOIh') and self.TOIh != None and self.TOIl != None:  # do we have TOI (third order intercept data)?
		if len(self.TOIptt) != len(self.TOIpdl) or len(self.TOIptt) != len(self.TOIpdh): raise ValueError("ERROR! number of data points in two-tone power != upper distortion and/or != lower distortion")
		if not os.path.exists(pathname_TOI):    os.makedirs(pathname_TOI)  # if necessary, make the directory to contain the data
		#filename = pathname_TOI + "/" + devicename + "_TOI.xls"
		filename = "".join([pathname_TOI,"/",wafername,devicenamemodifier,"__", devicename, "_TOI.xls"])
		fTOI = open(filename, 'w')
		# parameters
		#fTOI.write('! device name\t' + devicename + '\n')
		fTOI.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename]) + '\n')
		fTOI.write('! wafer name\t' + wafername + '\n')

		fTOI.write('! x location um\t%d\n' % int(xloc))
		fTOI.write('! y location um\t%d\n' % int(yloc))
		fTOI.write('! Vds (V)\t%10.2f\n' % Vds)
		fTOI.write('! Id (A)\t%10.2E\n' % Id)
		fTOI.write('! drain status\t%s\n' % drainstatus)
		fTOI.write('! Vgs (V)\t%10.2f\n' % Vgs)
		fTOI.write('! Ig (A)\t%10.2E\n' % Ig)
		fTOI.write('! gate status\t%s\n' % gatestatus)
		# timestamp
		fTOI.write('! year\t' + str(dt.datetime.now().year)+'\n')
		fTOI.write('! month\t' + str(dt.datetime.now().month)+'\n')
		fTOI.write('! day\t' + str(dt.datetime.now().day)+'\n')
		fTOI.write('! hour\t' + str(dt.datetime.now().hour)+'\n')
		fTOI.write('! minute\t' + str(dt.datetime.now().minute)+'\n')
		fTOI.write('! second\t' + str(dt.datetime.now().second)+'\n')
		fTOI.write('!\n')
		fTOI.write('! Center frequency in Hz\t%f10.0\n' % (self._centfreq))
		fTOI.write('! Frequency spacing between two tones in Hz\t%10.0f\n' % (self._deltafreq))
		fTOI.write('! Resolution Bandwidth Hz for distortion products measurements\t%d\n' % (self._resbwdistortion))
		fTOI.write('! System TOI dBm\t %10.1f\n' % (self._sysTOI))
		# data vs tuner position and reflection coefficient and DUT input power
		fTOI.write("! Measured quantities\n")
		for pos in self.pinDUT.keys():              # print out data according to tuner position and reflection coefficient
			fTOI.write("! tuner motor position \t%s\treflection coefficient at DUT output mag angle\t%10.2f %10.2f\n" %(str(pos),self.actualrcoefMA[pos].real,self.actualrcoefMA[pos].imag))
			fTOI.write('! Noise Floor dBm at the DUT output for distortion products measurements\t%10.0f\n' % (self.noisefloor[pos]))
			fTOI.write('! DUT gain dB\t %10.1f\n' % (self.DUTgain[pos]))
			fTOI.write('! Average input TOI dBm\t%10.1f\n' % (self.TOIavg[pos]-self.DUTgain[pos]))
			fTOI.write('! Average output TOI dBm\t%10.1f\n' % (self.TOIavg[pos]))
		# datatype header
			fTOI.write("!\n")
			fTOI.write("! fundamental DUT input power dBm\tfundamental DUT output power dBm\tlower 3rd order product dBm\tupper third order product dBm\tlower OIPT\tupper OIPT\tsystem third order products dBm\n")
			for ii in range(0, len(self.TOIptt[pos])):
				fTOI.write("%7.1f\t%7.1f\t%7.1f\t%7.1f\t%7.1f\t%7.1f\t%7.1f\n" % (self.pinDUT[pos][ii], self.TOIptt[pos][ii], self.TOIpdl[pos][ii], self.TOIpdh[pos][ii],self.TOIl[pos][ii],self.TOIh[pos][ii], self.sys[pos][ii]))
			fTOI.write("!\n")
		# now write third order intercept points in the order of increasing magnitude
		sortedpos=sorted(self.TOIavg, key=lambda p :self.TOIavg[p])
		fTOI.write("!sorted averaged TOI\n")
		fTOI.write("! tuner motor position \treflection coefficient at DUT output mag angle\tAveraged output TOI dBm\tDUT gain dB\n" )
		for pos in sortedpos: # print out data sorted by minimum to maximum average of upper and lower output TOI according to tuner position and reflection coefficient
			fTOI.write("%s\t%10.2f %10.2f\t%10.1f\t%10.1f\n" %(str(pos),self.actualrcoefMA[pos].real,self.actualrcoefMA[pos].imag,self.TOIavg[pos],self.DUTgain[pos]))
		fTOI.close()
		return [filename, devicename]
	else:
		return [None, None]  # have no third order intercept data
####################################################################################################################################################################
####################################################################################################################################################################
# Third order intercept point obtained via sweeping the gate with a triangle-wave bias
# used with IP3_Vgssweep.measureTOI_gain()
def X_writefile_TOI_Vgssweep(self, pathname=None, wafername=None, xloc=None, yloc=None, devicename=None,devicenamemodifier="",overwrite=True):
	if pathname == None: raise ValueError("ERROR Must include pathname")
	if devicename == None: raise ValueError("ERROR Must give device name for this measurement")
	# Form devicename and devicename from function input parameters
	pathname_TOI = pathname + sub("RF_power")
	if devicenamemodifier!="": devicenamemodifier="".join(["_",devicenamemodifier])
	if self.haveTOI:  # do we have TOI with Vgssweep (third order intercept data)?
		if not os.path.exists(pathname_TOI):    os.makedirs(pathname_TOI)  # if necessary, make the directory to contain the data
		filename = "".join([pathname_TOI,"/",wafername,devicenamemodifier,"__", devicename, "_TOIVgssweepsearch.xls"])
		if overwrite:
			f=open(filename,'w')
		else:
			f = open(filename, 'a+')
		# parameters
		#f.write('! device name\t' + devicename + '\n')
		f.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename]) + '\n')
		f.write('! wafer name\t' + wafername + '\n')
		f.write('! x location um\t%d\n' % int(xloc))
		f.write('! y location um\t%d\n' % int(yloc))
		f.write('! Vds (V)\t%10.2f\n' % self.Vds)
		f.write('! Id (A)\t%10.2E\n' % self.Idaverage)
		f.write('! drain status\t%s\n' % self.drainstatus)
		f.write('! Pin\t%10.2f\n' % self.Pin)
		# timestamp
		f.write('! year\t' + str(dt.datetime.now().year)+'\n')
		f.write('! month\t' + str(dt.datetime.now().month)+'\n')
		f.write('! day\t' + str(dt.datetime.now().day)+'\n')
		f.write('! hour\t' + str(dt.datetime.now().hour)+'\n')
		f.write('! minute\t' + str(dt.datetime.now().minute)+'\n')
		f.write('! second\t' + str(dt.datetime.now().second)+'\n')
		f.write('!\n')
		f.write('! Center frequency in Hz\t%f10.0\n' % (self.centfreq))
		f.write('! Frequency spacing between two tones in Hz\t%10.0f\n' % (self.deltafreq))
		f.write('! Resolution Bandwidth Hz\t%d\n' % (self.actualresolutionbandwidth))
		f.write('! Video Bandwidth Hz\t%d\n' % (self.actualvideobandwidth))
		f.write('! Gate sweep period (S)\t%10.2E\n' % (self.Vgsperiod))
		f.write('! Input attenuation setting of spectrum analyzer (dB)\t%10.1f\n' % (self.spectrum_analyser_input_attenuation))
		# data vs tuner position and reflection coefficient and DUT input power
		f.write("! Measured quantities\n")
		f.write("! tuner motor position \t%s\treflection coefficient at DUT output mag angle\t%10.2f %10.2f\n" %(str(self.pos),self.actualrcoefMA.real,self.actualrcoefMA.imag))
		#f.write('! Noise Floor dBm at the DUT output for distortion products measurements\t%10.0f\n' % (self.noisefloor))
		f.write('! Max DUT gain dB\t %10.1f\n' % (max(self.gain_Vgsswept)))
		f.write('! Max output TOI dBm\t%10.1f\n' % max((self.TOI_Vgsswept)))
		f.write('! Associated DUT gain dB at max TOI\t %10.1f\n' % (self.gain_Vgsswept[self.TOI_Vgsswept.index(max(self.TOI_Vgsswept))]))
		f.write('! Max overall TOI-Pdc (dB)\t %10.2f\n' %(self.TOI_over_Pdc_Vgsswept_best))
		# datatype header
		f.write("!\n!\n!\n!\n!")
		f.write("! parameters vs output reflection coefficient (gamma) for the timestamp which produces highest peak TOI for the given gamma")
		f.write("\n! tuner motor position\treflection coefficient at DUT output mag angle\toutput TOI dBm\tassociated DUT gain dB")
		f.write("\n%s\t%10.2f %10.2f\t%10.1f\t%10.1f" % (self.pos, self.actualrcoefMA.real,self.actualrcoefMA.imag, max(self.TOI_Vgsswept),self.gain_Vgsswept[self.TOI_Vgsswept.index(max(self.TOI_Vgsswept))] ))
		f.write("\n!\n!\n!\n!")
		f.write("\n! parameters vs timestamps at the output reflection coefficient which produces the highest TOI")
		f.write("\n! timestamp (sec)\tVgs\tId(A)\tfundamental DUT output power dBm\tupper 3rd order product dBm\tlower 3rd order product dBm\tupper output TOI dBm\tlower output TOI dBm\toutput TOI dBm\tgain dB\tTOI-Pdc dB")
		for ii in range(0, len(self.timestamps)):
			f.write("\n%10.8E\t%10.8f\t%10.5E\t%7.2f\t%7.2f\t%7.2f\t%7.2f\t%7.2f\t%7.2f\t%7.2f\t%7.2f" % (self.timestamps[ii], self.Vgs[ii], self.Id[ii],self.pfund[ii],self.p3rdupper[ii],self.p3rdlower[ii], self.TOI_upper_Vgsswept[ii],self.TOI_lower_Vgsswept[ii],self.TOI_Vgsswept[ii], self.gain_Vgsswept[ii],self.TOI_over_Pdc_Vgsswept[ii]))
		#f.write("!\n!\n!\n!\n!")
		f.close()
		return [filename, devicename]
	else:
		return [None, None]  # have no third order intercept data
####################################################################################################################################################################
####################################################################################################################################################################
# Third order intercept point obtained via sweeping the gate with a triangle-wave bias
# used with IP3.measure_gainonly()
def X_writefile_gainonly_Vgssweep(self, pathname=None, wafername=None, xloc=None, yloc=None, devicename=None, devicenamemodifier="", overwrite=True):
	if pathname == None: raise ValueError("ERROR Must include pathname")
	if devicename == None: raise ValueError("ERROR Must give device name for this measurement")
	# Form devicename and devicename from function input parameters
	pathname_TOI = pathname + sub("RF_power")
	if not os.path.exists(pathname_TOI):    os.makedirs(pathname_TOI)  # if necessary, make the directory to contain the data
	filename = "".join([pathname_TOI,"/",wafername,devicenamemodifier,"__", devicename, "_gainVgssweep.xls"])
	if overwrite:
		f=open(filename,'w')
	else:
		f = open(filename, 'a+')
	# parameters
	f.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename]) + '\n')
	f.write('! wafer name\t' + wafername + '\n')
	f.write('! x location um\t%d\n' % int(xloc))
	f.write('! y location um\t%d\n' % int(yloc))
	f.write('! Vds (V)\t%10.2f\n' % self.Vds)
	f.write('! Id (A)\t%10.2E\n' % self.Idaverage)
	f.write('! drain status\t%s\n' % self.drainstatus)
	f.write('! Pin\t%10.2f\n' % self.Pin)
	# timestamp
	f.write('! year\t' + str(dt.datetime.now().year)+'\n')
	f.write('! month\t' + str(dt.datetime.now().month)+'\n')
	f.write('! day\t' + str(dt.datetime.now().day)+'\n')
	f.write('! hour\t' + str(dt.datetime.now().hour)+'\n')
	f.write('! minute\t' + str(dt.datetime.now().minute)+'\n')
	f.write('! second\t' + str(dt.datetime.now().second)+'\n')
	f.write('!\n')
	f.write('! Center frequency in Hz\t%f10.0\n' % (self.centfreq))
	f.write('! Resolution Bandwidth Hz\t%d\n' % (self.actualresolutionbandwidth))
	f.write('! Video Bandwidth Hz\t%d\n' % (self.actualvideobandwidth))
	f.write('! Gate sweep period (S)\t%10.2E\n' % (self.Vgsperiod))
	# data vs tuner position and reflection coefficient and DUT input power
	f.write("! Measured quantities\n")
	f.write("! tuner motor position \t%s\treflection coefficient at DUT output mag angle\t %10.2f %10.2f\n" %(str(self.pos),self.actualrcoefMA.real,self.actualrcoefMA.imag))
	f.write("! tuner impedance ohms\t%10.2f %10.2f\n" %(self.actual_Z.real,self.actual_Z.imag))
	f.write('! Max DUT gain dB\t %10.1f\n' % (max(self.gain_gainonly)))
	# datatype header
	f.write("!\n!\n!\n!\n!")
	f.write("\n! parameters vs timestamps at the output reflection coefficient which produces the highest TOI\n")
	f.write("! timestamp (sec)\tVgs\tId(A)\tfundamental DUT output power dBm\tgain dB")
	for ii in range(0, len(self.timestamps_gainonly)):
		f.write("\n%10.8E\t%10.8f\t%10.10f\t%7.2f\t%7.2f" % (self.timestamps_gainonly[ii], self.Vgs_gainonly[ii], self.Id_gainonly[ii],self.pfund_gainonly[ii],self.gain_gainonly[ii]))
	f.close()
	return [filename, devicename]
####################################################################################################################################################################
####################################################################################################################################################################
# Third order intercept point obtained via sweeping the gate with a triangle-wave bias
# these data are the best TOI vs reflection coefficient from IP3_Vgssweep.TOIsearch()
#
def X_writefile_Vgssweep_TOIsearch(self, pathname=None, wafername=None, xloc=None, yloc=None, devicename=None,devicenamemodifier="",overwrite=True):
	if pathname == None: raise ValueError("ERROR Must include pathname")
	if devicename == None: raise ValueError("ERROR Must give device name for this measurement")
	# Form devicename and devicename from function input parameters
	pathname_TOI = pathname + sub("RF_power")
	if devicenamemodifier!="": devicenamemodifier="".join(["_",devicenamemodifier])
	if self.haveTOIsearch:  # do we have TOI search data?
		if not os.path.exists(pathname_TOI):    os.makedirs(pathname_TOI)  # if necessary, make the directory to contain the data
		filename = "".join([pathname_TOI,"/",wafername,devicenamemodifier,"__", devicename, "_TOIVgssweepsearch.xls"])
		if overwrite:
			f=open(filename,'w')
		else:
			f = open(filename, 'a+')
		# parameters
		#f.write('! device name\t' + devicename + '\n')
		f.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename]) + '\n')
		f.write('! wafer name\t' + wafername + '\n')
		f.write('! x location um\t%d\n' % int(xloc))
		f.write('! y location um\t%d\n' % int(yloc))
		f.write('! Vds (V)\t%10.2f\n' % self.Vds)
		f.write('! Id (A)\t%10.2E\n' % self.Idaverage)
		f.write('! drain status\t%s\n' % self.drainstatus)
		f.write('! Pin\t%10.2f\n' % self.Pin)
		# timestamp
		f.write('! year\t' + str(dt.datetime.now().year)+'\n')
		f.write('! month\t' + str(dt.datetime.now().month)+'\n')
		f.write('! day\t' + str(dt.datetime.now().day)+'\n')
		f.write('! hour\t' + str(dt.datetime.now().hour)+'\n')
		f.write('! minute\t' + str(dt.datetime.now().minute)+'\n')
		f.write('! second\t' + str(dt.datetime.now().second)+'\n')
		f.write('!\n')
		f.write('! Center frequency in Hz\t%f10.0\n' % (self.centfreq))
		f.write('! Frequency spacing between two tones in Hz\t%10.0f\n' % (self.deltafreq))
		f.write('! Resolution Bandwidth Hz\t%d\n' % (self.actualresolutionbandwidth))
		f.write('! Video Bandwidth Hz\t%d\n' % (self.actualvideobandwidth))
		f.write('! Gate sweep period (S)\t%10.2E\n' % (self.Vgsperiod))
		#f.write('! System TOI dBm\t %10.1f\n' % (self._sysTOI))
		# data vs tuner position and reflection coefficient and DUT input power
		f.write("! Measured quantities\n")
		f.write("! tuner motor position \t%s\treflection coefficient at DUT output mag angle\t%10.2f %10.2f\n" %(str(self.pos_at_TOI_maxall),self.gamma_at_TOI_maxall.real,self.gamma_at_TOI_maxall.imag))
		#f.write('! Noise Floor dBm at the DUT output for distortion products measurements\t%10.0f\n' % (self.noisefloor))
		f.write('! Associated DUT gain dB at max TOI\t %10.1f\n' % (self.gain_at_TOI_maxall))
		f.write('! Max overall output TOI dBm\t%10.1f\n' % (self.TOI_maxall))
		f.write('! Max overall TOI-Pdc (dB)\t %10.2f\n' %(max(self.maxTOI_over_Pdc_sortedTOI)))
		# datatype header
		f.write("!\n!\n!\n!\n!")
		# write out time domain for each tuning position
		for ig in range(0, len(self.gamma_sortedTOI)):
			f.write("\nindividual sweep\treflection coefficient at DUT output mag angle\toutput TOI dBm\tassociated DUT gain dB\tmaximum TOI-Pdc (dBm)")
			f.write("\n%s\t%10.2f %10.2f\t%10.1f\t%10.1f\t%10.2f" % (self.pos_sortedTOI[ig], self.gamma_sortedTOI[ig].real,self.gamma_sortedTOI[ig].imag, self.TOImax_sortedTOI[ig], self.gainmaxTOI_sortedTOI[ig],self.maxTOI_over_Pdc_sortedTOI[ig]))
			f.write("\n!")
			f.write("\n!individual timestamp (sec)\tVgs\tId(A)\tfundamental DUT output power dBm\tupper 3rd order product dBm\tlower 3rd order product dBm\tupper output TOI dBm\tlower output TOI dBm\toutput TOI dBm\tgain dB\tTOI-Pdc dB")
			for it in range(0, len(self.timestamps_search)):
				f.write("\n%10.8E\t%10.8f\t%10.5E\t%7.2f\t%7.2f\t%7.2f\t%7.2f\t%7.2f\t%7.2f\t%7.2f\t%7.2f" % (self.timestamps_search[it], self.Vgs_measured_search[it],self.Id_sortedTOI[ig][it], self.pfund_sortedTOI[ig][it], self.p3rdupper_sortedTOI[ig][it],self.p3rdlower_sortedTOI[ig][it],
			                                                                               self.TOIupper_sortedTOI[ig][it], self.TOIlower_sortedTOI[ig][it], self.TOI_sortedTOI[ig][it], self.gain_sortedTOI[ig][it],self.TOI_over_Pdc_sortedTOI[ig][it]))
		f.write("\n!\n!\n!\n!\n!")
		f.write("! parameters vs output reflection coefficient (gamma) for the timestamp which produces highest peak TOI for the given gamma")
		f.write("\n! tuner motor position\treflection coefficient at DUT output mag angle\toutput TOI dBm\tassociated DUT gain dB")
		for ig in range(0, len(self.gamma_sortedTOI)):
			f.write("\n%s\t%10.2f %10.2f\t%10.2f\t%10.2f" % (self.pos_sortedTOI[ig], self.gamma_sortedTOI[ig].real,self.gamma_sortedTOI[ig].imag, self.TOImax_sortedTOI[ig], self.gainmaxTOI_sortedTOI[ig]))
		f.write("\n!\n!\n!\n!")
		f.write("\n! parameters vs timestamps at the output reflection coefficient which produces the highest TOI")
		f.write("\nindividual sweep\tbest reflection coefficient at DUT output mag angle\tmaximum output TOI dBm\tassociated DUT gain dB\tmaximum TOI-Pdc (dBm)")
		maxTOI= max(self.TOI_vstimestamp_at_best_gamma)
		indextimemaxTOI=self.TOI_vstimestamp_at_best_gamma.index(maxTOI)
		f.write("\n%s\t%10.2f %10.2f\t%10.2f\t%10.2f" % (self.TOI_gamma_at_best_gamma[0],self.TOI_gamma_at_best_gamma[1],maxTOI, self.gain_vstimestamp_at_best_gamma[indextimemaxTOI], max(self.TOI_over_Pdc_at_best_gamma)))
		f.write("\n!")
		f.write("\n! timestamp (sec)\tVgs\tId(A)\tfundamental DUT output power dBm\tupper 3rd order product dBm\tlower 3rd order product dBm\tupper output TOI dBm\tlower output TOI dBm\toutput TOI dBm\tgain dB\tTOI-Pdc dB")
		for it in range(0, len(self.timestamps_search)):
				f.write("\n%10.8E\t%10.8f\t%10.5E\t%7.2f\t%7.2f\t%7.2f\t%7.2f\t%7.2f\t%7.2f\t%7.2f\t%7.2f" % (self.timestamps_search[it], self.Vgs_measured_search[it],self.Id[it], self.pfund_vstimestamp_at_best_gamma[it], self.p3rdupper_vstimestamp_at_best_gamma[it],self.p3rdlower_vstimestamp_at_best_gamma[it],
			                                                                               self.TOI_upper_vstimestamp_at_best_gamma[it], self.TOI_lower_vstimestamp_at_best_gamma[it], self.TOI_vstimestamp_at_best_gamma[it], self.gain_vstimestamp_at_best_gamma[it],self.TOI_over_Pdc_at_best_gamma[it]))
		f.close()
		return [filename, devicename]
	else:
		return [None, None]  # have no third order intercept data
####################################################################################################################################################################
####################################################################################################################################################################
# write the current third order products for a given device
# def X_writefile_spar(self, pathname, lotname, wafernumber, diecolumn, dierow, subsitename, xloc, yloc, Vds, Id, drainstatus, Vgs, Ig, gatestatus):
# The device name may be supplied or the parameters from Cascade Nucleus may be supplied to form the devicename
# For user-defined probe test plans, the devicename is obtained from the probe test file and must be supplied to this function as the devicename
# def X_writefile_TOI_old(self, pathname=None, wafername=None, xloc=None, yloc=None, Vds=None, Id=None, drainstatus=None,Vgs=None, Ig=None, gatestatus=None, devicename=None, diecolumn=None, dierow=None, subsitename=None,devicenamemodifier=""):
# 	if pathname == None: raise ValueError("ERROR Must include pathname")
# 	# if xloc==None: raise ValueError("ERROR Must give x location of device")
# 	# if yloc==None: raise ValueError("ERROR Must give y location of device")
# 	# if Vds==None: raise ValueError("ERROR Must give drain voltage Vds for this measurement")
# 	# if Id==None: raise ValueError("ERROR Must give drain current Id for this measurement")
# 	# if drainstatus==None: raise ValueError("ERROR Must give drain status for this measurement")
# 	# if Vgs==None: raise ValueError("ERROR Must give gate voltage Vgs for this measurement")
# 	# if Ig==None: raise ValueError("ERROR Must give gate current Ig for this measurement")
# 	# if gatestatus==None: raise ValueError("ERROR Must give gate status for this measurement")
# 	if devicename == None: raise ValueError("ERROR Must give device name for this measurement")
# 	# Form devicename and devicename from function input parameters
# 	pathname_TOI = pathname + sub("RF_power")
# 	if devicenamemodifier!="": devicename = "".join([devicenamemodifier, "_", devicename])
# 	if diecolumn != None and dierow != None and subsitename != None:
# 		devicename = formdevicename(wafername, diecolumn, dierow, subsitename)
# 	else:
# 		devicename = formdevicename(wafername, devicename)
#
# 	if hasattr(self, 'TOIl') and hasattr(self,'TOIh') and self.TOIh != None and self.TOIl != None:  # do we have TOI (third order intercept data)?
# 		if len(self.TOIptt) != len(self.TOIpdl) or len(self.TOIptt) != len(self.TOIpdh): raise ValueError("ERROR! number of data points in two-tone power != upper distortion and/or != lower distortion")
# 		if not os.path.exists(pathname_TOI):    os.makedirs(pathname_TOI)  # if necessary, make the directory to contain the data
# 		filename = pathname_TOI + "/" + devicename + "_TOI.xls"
# 		fTOI = open(filename, 'w')
# 		# parameters
# 		fTOI.write('! device name\t' + devicename + '\n')
# 		fTOI.write('! wafer name\t' + wafername + '\n')
# 		if diecolumn != None and dierow != None and subsitename != None:
# 			fTOI.write('! die column\t' + diecolumn + '\n')
# 			fTOI.write('! die row\t' + dierow + '\n')
# 			fTOI.write('! subsite name\t' + subsitename + '\n')
# 			if diecolumn != None ^ dierow != None ^ subsitename != None: raise ValueError("ERROR need to provide all of die column, die row, subsite name if one is provided")
#
# 		fTOI.write('! x location um\t%d\n' % int(xloc))
# 		fTOI.write('! y location um\t%d\n' % int(yloc))
# 		fTOI.write('! Vds (V)\t%10.2f\n' % Vds)
# 		fTOI.write('! Id (A)\t%10.2E\n' % Id)
# 		fTOI.write('! drain status\t%s\n' % drainstatus)
# 		fTOI.write('! Vgs (V)\t%10.2f\n' % Vgs)
# 		fTOI.write('! Ig (A)\t%10.2E\n' % Ig)
# 		fTOI.write('! gate status\t%s\n' % gatestatus)
# 		# timestamp
# 		fTOI.write('! year\t' + str(dt.datetime.now().year)+'\n')
# 		fTOI.write('! month\t' + str(dt.datetime.now().month)+'\n')
# 		fTOI.write('! day\t' + str(dt.datetime.now().day)+'\n')
# 		fTOI.write('! hour\t' + str(dt.datetime.now().hour)+'\n')
# 		fTOI.write('! minute\t' + str(dt.datetime.now().minute)+'\n')
# 		fTOI.write('! second\t' + str(dt.datetime.now().second)+'\n')
# 		fTOI.write('!\n')
# 		fTOI.write('! Center frequency in Hz\t%f10.0\n' % (self._centfreq))
# 		fTOI.write('! Frequency spacing between two tones in Hz\t%10.0f\n' % (self._deltafreq))
# 		fTOI.write('! Resolution Bandwidth Hz for distortion products measurements\t%d\n' % (self._resbwdistortion))
# 		fTOI.write('! System TOI dBm\t %10.1f\n' % (self._sysTOI))
# 		# data vs tuner position and reflection coefficient and DUT input power
# 		fTOI.write("! Measured quantities\n")
# 		for pos in self.pinDUT.keys():              # print out data according to tuner position and reflection coefficient
# 			fTOI.write("! tuner motor position \t%s\treflection coefficient at DUT output mag angle\t%10.2f %10.2f\n" %(str(pos),self.actualrcoefMA[pos].real,self.actualrcoefMA[pos].imag))
# 			fTOI.write('! Noise Floor dBm at the DUT output for distortion products measurements\t%10.0f\n' % (self.noisefloor[pos]))
# 			fTOI.write('! DUT gain dB\t %10.1f\n' % (self.DUTgain[pos]))
# 			fTOI.write('! Lower frequency measured input TOI dBm\t%10.1f\n' % (self.TOIl[pos]-self.DUTgain[pos]))
# 			fTOI.write('! Upper frequency measured input TOI dBm\t%10.1f\n' % (self.TOIh[pos]-self.DUTgain[pos]))
# 			fTOI.write('! Lower frequency measured output TOI dBm\t%10.1f\n' % (self.TOIl[pos]))
# 			fTOI.write('! Upper frequency measured output TOI dBm\t%10.1f\n' % (self.TOIh[pos]))
# 			fTOI.write('! slope of linear fit of lower distortion tone\t#%10.1f\n' % (self.TOIml[pos]))
# 			fTOI.write('! intercept of linear fit of lower distortion tone\t#%10.1f\n' % (self.TOIbl[pos]))
# 			fTOI.write('! slope of linear fit of upper distortion tone\t#%10.1f\n' % (self.TOImh[pos]))
# 			fTOI.write('! intercept of linear fit of upper distortion tone\t#%10.1f\n' % (self.TOIbh[pos]))
# 		# datatype header
# 			fTOI.write("!\n")
# 			fTOI.write("! fundamental DUT input power dBm\tfundamental DUT output power dBm\tlower 3rd order product dBm\tupper third order product dBm\tsystem third order products dBm\n")
# 			for ii in range(0, len(self.TOIptt[pos])):
# 				fTOI.write("%7.1f\t%7.1f\t%7.1f\t%7.1f\t%7.1f\n" % (self.pinDUT[pos][ii], self.TOIptt[pos][ii], self.TOIpdl[pos][ii], self.TOIpdh[pos][ii], self.sys[pos][ii]))
# 			fTOI.write("!\n")
# 		# now write third order intercept points in the order of increasing magnitude
# 		sortedpos=sorted(self.TOIl, key=lambda p :(self.TOIl[p]+self.TOIh[p])/2.)
# 		fTOI.write("!sorted TOI\n")
# 		fTOI.write("! tuner motor position \treflection coefficient at DUT output mag angle\tLower frequency measured output TOI dBm\tUpper frequency measured output TOI dBm\tDUT gain dB\n" )
# 		for pos in sortedpos: # print out data sorted by minimum to maximum average of upper and lower output TOI according to tuner position and reflection coefficient
# 			fTOI.write("%s\t%10.2f %10.2f\t%10.1f\t%10.1f\t%10.1f\n" %(str(pos),self.actualrcoefMA[pos].real,self.actualrcoefMA[pos].imag,self.TOIl[pos],self.TOIh[pos],self.DUTgain[pos]))
# 		fTOI.close()
# 		return [filename, devicename]
# 	else:
# 		return [None, None]  # have no third order intercept data
####################################################################################################################################################################
# write output vs input power for compression tests for a given device
# def X_writefile_spar(self, pathname, lotname, wafernumber, diecolumn, dierow, subsitename, xloc, yloc, Vds, Id, drainstatus, Vgs, Ig, gatestatus):
# The device name may be supplied or the parameters from Cascade Nucleus may be supplied to form the devicename
# For user-defined probe test plans, the devicename is obtained from the probe test file and must be supplied to this function as the devicename
def X_writefile_Pcompression(self, pathname=None, wafername='', xloc='', yloc='', Vds=0., Id=0., drainstatus='', Vgs=0.,Ig=0, gatestatus='', devicename=None, diecolumn=None, dierow=None, subsitename=None,devicenamemodifier=""):
	if len(self.DUTcompression_pin) != len(self.DUTcompression_pout): raise ValueError(
		"ERROR: input and output power arrays are of different sizes ")
	if self._Vds != 0. and (len(self.DUTcompression_pin) != len(self.DUTcompression_Id) or len(self.DUTcompression_pin) != len(self.DUTcompression_Ig) or len(self.DUTcompression_pin) != len(self.DUTcompression_gatestatus) or len(self.DUTcompression_pin) != len(self.DUTcompression_drainstatus)): raise ValueError("ERROR: bias arrays of different sizes")
	if pathname == None: raise ValueError("ERROR Must include pathname")
	# if xloc==None: raise ValueError("ERROR Must give x location of device")
	# if yloc==None: raise ValueError("ERROR Must give y location of device")
	# if Vds==None: raise ValueError("ERROR Must give drain voltage Vds for this measurement")
	# if Id==None: raise ValueError("ERROR Must give drain current Id for this measurement")
	# if drainstatus==None: raise ValueError("ERROR Must give drain status for this measurement")
	# if Vgs==None: raise ValueError("ERROR Must give gate voltage Vgs for this measurement")
	# if Ig==None: raise ValueError("ERROR Must give gate current Ig for this measurement")
	# if gatestatus==None: raise ValueError("ERROR Must give gate status for this measurement")
	if devicename == None: raise ValueError("ERROR Must give device name for this measurement")
	# Form devicename and devicename from function input parameters
	pathname_compression = pathname + sub("RF_power")
	if devicenamemodifier!="": devicename = "".join([devicenamemodifier, "_", devicename])
	if diecolumn != None and dierow != None and subsitename != None:
		devicename = formdevicename(wafername, diecolumn, dierow, subsitename)
	else:
		devicename = formdevicename(wafername, devicename)

	if hasattr(self, 'DUTcompression_pin') and hasattr(self,
													   'DUTcompression_pout'):  # do we have power compression data?
		if len(self.DUTcompression_pin) != len(self.DUTcompression_pout): raise ValueError(
			"ERROR! number of data points in power in array != power out array!")
		if not os.path.exists(pathname_compression):    os.makedirs(
			pathname_compression)  # if necessary, make the directory to contain the data
		filename = pathname_compression + "/" + devicename + "_PCOMPRESS.xls"
		fPcomp = open(filename, 'w')
		# parameters
		fPcomp.write('! device name\t' + devicename + '\n')
		fPcomp.write('! wafer name\t' + wafername + '\n')

		fPcomp.write('! x location um\t%d\n' % int(xloc))
		fPcomp.write('! y location um\t%d\n' % int(yloc))
		if self._Vds != 0.:
			fPcomp.write('! Vds (V)\t%10.2f\n' % Vds)
			fPcomp.write('! Vgs (V)\t%10.2f\n' % Vgs)
		# timestamp
		fPcomp.write('! year\t' + str(dt.datetime.now().year) + '\n')
		fPcomp.write('! month\t' + str(dt.datetime.now().month) + '\n')
		fPcomp.write('! day\t' + str(dt.datetime.now().day) + '\n')
		fPcomp.write('! hour\t' + str(dt.datetime.now().hour) + '\n')
		fPcomp.write('! minute\t' + str(dt.datetime.now().minute) + '\n')
		fPcomp.write('! second\t' + str(dt.datetime.now().second) + '\n')
		fPcomp.write('!\n')
		fPcomp.write('! frequency in Hz\t%10.0f\n' % (self._frequency))
		fPcomp.write('! Selected Compression point target (dBm)\t%10.1f\n' % (self.compressiontarget))
		fPcomp.write('! Input Compression point (dBm)\t%10.1f\n' % (self.inputcompressionpoint))
		fPcomp.write('! Output Compression point (dBm)\t%10.1f\n' % (self.outputcompressionpoint))
		fPcomp.write('! Noise Floor dBm at the DUT output \t%10.0f\n' % (self.noisefloor))
		fPcomp.write('! DUT gain dB\t %10.1f\n' % (self.DUTgain))

		fPcomp.write('!')
		# datatype header
		fPcomp.write("!\n!\n")
		# data
		fPcomp.write("! Measured quantities\n")

		if self._Vds != 0:  # we have bias applied to the device under test
			fPcomp.write("! DUT input power dBm\tDUT output power dBm\tdrain current (A)\tgate current (A)\tdrain status\tgate status\n")
			for ii in range(0, len(self.DUTcompression_pin)):
				fPcomp.write("%7.1f\t%7.1f\t%7.2E\t%7.2E\t%s\t%s\n" % (
					self.DUTcompression_pin[ii], self.DUTcompression_pout[ii], self.DUTcompression_Id[ii],
					self.DUTcompression_Ig[ii], self.DUTcompression_drainstatus[ii],
					self.DUTcompression_gatestatus[ii]))
		else:
			fPcomp.write("! DUT input power dBm\tDUT output power dBm\n")
			for ii in range(0, len(self.DUTcompression_pin)):
				fPcomp.write("%7.1f\t%7.1f\n" % (self.DUTcompression_pin[ii], self.DUTcompression_pout[ii]))
		fPcomp.close()
		return [filename, devicename]
	else:
		return [None, None]  # have no power compression data
####################################################################################################################################################################
# write output vs input power for compression tests for a given device with use of load pull tuner
# def X_writefile_spar(self, pathname, lotname, wafernumber, diecolumn, dierow, subsitename, xloc, yloc, Vds, Id, drainstatus, Vgs, Ig, gatestatus):
# The device name may be supplied or the parameters from Cascade Nucleus may be supplied to form the devicename
# For user-defined probe test plans, the devicename is obtained from the probe test file and must be supplied to this function as the devicename
def X_writefile_Pcompression_tuned(self, pathname=None, wafername='', xloc='', yloc='', devicename=None,devicenamemodifier=""):
	# if self._Vds != 0. and (len(self.DUTcompression_pin) != len(self.DUTcompression_Id) or len(self.DUTcompression_pin) != len(self.DUTcompression_Ig) or len(self.DUTcompression_pin) != len(self.DUTcompression_gatestatus) or len(self.DUTcompression_pin) != len(self.DUTcompression_drainstatus)): raise ValueError("ERROR: bias arrays of different sizes")
	if pathname == None: raise ValueError("ERROR Must include pathname")
	if devicename == None: raise ValueError("ERROR Must give device name for this measurement")
	# Form devicename and devicename from function input parameters
	pathname_compression = pathname + sub("RF_power")
	if devicenamemodifier!="": devicename = "".join([devicenamemodifier, "_", devicename])
	devicename = formdevicename(wafername, devicename)

	if hasattr(self, 'outputcompressionpoint'):  # do we have power compression data?
		if not os.path.exists(pathname_compression):    os.makedirs(
			pathname_compression)  # if necessary, make the directory to contain the data
		filename = pathname_compression + "/" + devicename + "_PCOMPRESS.xls"
		fPcomp = open(filename, 'w')
		# parameters
		fPcomp.write('! device name\t' + devicename + '\n')
		fPcomp.write('! wafer name\t' + wafername + '\n')

		fPcomp.write('! x location um\t%d\n' % int(xloc))
		fPcomp.write('! y location um\t%d\n' % int(yloc))
		fPcomp.write('! Vds (V)\t%10.2f\n' % self.Vds)
		fPcomp.write('! Vgs (V)\t%10.2f\n' % self.Vgs)
		# timestamp
		fPcomp.write('! year\t' + str(dt.datetime.now().year) + '\n')
		fPcomp.write('! month\t' + str(dt.datetime.now().month) + '\n')
		fPcomp.write('! day\t' + str(dt.datetime.now().day) + '\n')
		fPcomp.write('! hour\t' + str(dt.datetime.now().hour) + '\n')
		fPcomp.write('! minute\t' + str(dt.datetime.now().minute) + '\n')
		fPcomp.write('! second\t' + str(dt.datetime.now().second) + '\n')
		fPcomp.write('!\n')
		fPcomp.write('! frequency in MHz\t%d\n' % (int(self.frequency)))
		print("from line 1159 in writefile_measured.py self.frequency = ",self.frequency)
		fPcomp.write('! Selected Compression point target (dBm)\t%10.1f\n' % (self.compressiontarget))
		for pos in self.pDUTout.keys(): # loop through all tuner positions (reflection coefficients
			fPcomp.write("! tuner motor position \t%s\treflection coefficient at DUT output mag angle\t%10.2f %10.2f\n" %(str(pos),self.actualrcoefMA[pos].real,self.actualrcoefMA[pos].imag))
			fPcomp.write('! Input Compression point (dBm)\t%10.1f\n' % (self.inputcompressionpoint[pos]))
			fPcomp.write('! Output Compression point (dBm)\t%10.1f\n' % (self.outputcompressionpoint[pos]))
			#fPcomp.write('! Noise Floor dBm at the DUT output \t%10.0f\n' % (self.noisefloor[pos]))
			fPcomp.write('! DUT gain dB\t %10.1f\n' % (self.DUTgain[pos]))
			fPcomp.write('!')
			# datatype header
			fPcomp.write("!\n!\n")
			# data
			fPcomp.write("! Measured quantities\n")
			pinDUTsortedasc=[p for p in self.pDUTout[pos].keys()]
			pinDUTsortedasc.sort(key=float)
			pinDUT=[float(p) for p in pinDUTsortedasc]
			poutDUT=[self.pDUTout[pos][p] for p in pinDUTsortedasc]
			gainvspin=[poutDUT[i]-pinDUT[i] for i in range(0,len(pinDUT))]
			if self.Vds!=0:  # we have bias applied to the device under test
				fPcomp.write("! DUT input power dBm\tDUT output power dBm\tgain dB\tdrain current (A)\tgate current (A)\tdrain status\tgate status\n")
				for i in range(0,len(pinDUT)):
					fPcomp.write("%s\t%7.3f\t%7.3E\t%7.3E\t%7.3E\t%s\t%s\n" % (pinDUT[i], poutDUT[i],gainvspin[i], self.IdDUT[pos][pinDUTsortedasc[i]], self.IgDUT[pos][pinDUTsortedasc[i]], self.drainstatusDUT[pos][pinDUTsortedasc[i]], self.gatestatusDUT[pos][pinDUTsortedasc[i]]))
			else:
				fPcomp.write("! DUT input power dBm\tDUT output power dBm\n")
				for i in range(0,len(pinDUT)):
					fPcomp.write("%7.3f\t%7.3f\t%7.3f\n" % (pinDUT[i], poutDUT[i],gainvspin[i]))
			fPcomp.write("! Spline fit \n")
			fPcomp.write("! DUT input power dBm\tDUT output power dBm\tgain dB\n")
			for i in range(0,len(self.pin_spline[pos])):
				fPcomp.write("%7.3f\t%7.3f\t%7.3f\n" % (self.pin_spline[pos][i], self.pout_spline[pos][i],self.gainvspinspline[pos][i]))
		fPcomp.close()
######################################################################################################################################################
####################################################################################################################################################################
# write output vs input power for compression tests for a given device with use of load pull tuner and Vgs swept
# The device name may be supplied or the parameters from Cascade Nucleus may be supplied to form the devicename
# For user-defined probe test plans, the devicename is obtained from the probe test file and must be supplied to this function as the devicename
def X_writefile_Pcompression_tuned_Vgssweep(self, pathname=None, wafername='', xloc='', yloc='', devicename=None,devicenamemodifier=""):
	# if self._Vds != 0. and (len(self.DUTcompression_pin) != len(self.DUTcompression_Id) or len(self.DUTcompression_pin) != len(self.DUTcompression_Ig) or len(self.DUTcompression_pin) != len(self.DUTcompression_gatestatus) or len(self.DUTcompression_pin) != len(self.DUTcompression_drainstatus)): raise ValueError("ERROR: bias arrays of different sizes")
	if pathname == None: raise ValueError("ERROR Must include pathname")
	if devicename == None: raise ValueError("ERROR Must give device name for this measurement")
	# Form devicename and devicename from function input parameters
	pathname_compression = pathname + sub("RF_power")
	if devicenamemodifier!="": devicename = "".join([devicenamemodifier, "_", devicename])
	devicename = formdevicename(wafername, devicename)

	if hasattr(self, 'outputcompressionpoints'):  # do we have power compression data?
		if not os.path.exists(pathname_compression):    os.makedirs(
			pathname_compression)  # if necessary, make the directory to contain the data
		filename = pathname_compression + "/" + devicename + "_PCOMPRESS_Vgssweep.xls"
		fPcomp = open(filename, 'w')
		# parameters
		fPcomp.write('! device name\t' + devicename + '\n')
		fPcomp.write('! wafer name\t' + wafername + '\n')

		fPcomp.write('! x location um\t%d\n' % int(xloc))
		fPcomp.write('! y location um\t%d\n' % int(yloc))
		fPcomp.write('! Vds (V)\t%10.2f\n' % self.Vds)
		# timestamp
		fPcomp.write('! year\t' + str(dt.datetime.now().year) + '\n')
		fPcomp.write('! month\t' + str(dt.datetime.now().month) + '\n')
		fPcomp.write('! day\t' + str(dt.datetime.now().day) + '\n')
		fPcomp.write('! hour\t' + str(dt.datetime.now().hour) + '\n')
		fPcomp.write('! minute\t' + str(dt.datetime.now().minute) + '\n')
		fPcomp.write('! second\t' + str(dt.datetime.now().second) + '\n')
		fPcomp.write('!\n')
		fPcomp.write('! frequency in Hz\t%d\n' % (int(self.frequency)))
		fPcomp.write('! Selected Compression point target (dBm)\t%10.1f\n' % (self.compressiontarget))
		fPcomp.write("! reflection coefficient at DUT output mag angle\t%10.2f %10.2f\n" %(self.output_reflection[0],self.output_reflection[1]))
		fPcomp.write("! highest overall output compression point (dBm)\t%10.2f" % (self.maxoutputcompression))
		fPcomp.write('\n!\n!\n!')
		# output compression points vs timestamp
		fPcomp.write('\n!timestamp (sec)\tVgs\toutput compression point (dBm)\tsmall_signal_gain (dB)')
		for it in range(0,len(self.timestamps_gainonly)):
			fPcomp.write('\n%10.2E\t%10.5f\t%10.2f\t%10.2f' %(self.timestamps_gainonly[it],self.Vgs_gainonly[it],self.outputcompressionpoints[it],self.pcomp_lineargain[it]))
		fPcomp.write('\n!\n!\n!')
		fPcomp.write('\n!compression vs Pout at each timestamp')
		for it in range(0,len(self.timestamps_gainonly)): #[timestamps loop]         output gain vs Pin, Pout for each timestamp
			fPcomp.write('\n!\n!\n!')
			fPcomp.write('\n!timestamp (sec)\tVgs\toutput compression point (dBm)\tsmall_signal_gain (dB)')
			fPcomp.write('\n%10.2E\t%10.5f\t%10.2f\t%10.2f' %(self.timestamps_gainonly[it],self.Vgs_gainonly[it],self.outputcompressionpoints[it],self.pcomp_lineargain[it]))
			fPcomp.write('\n!')
			# now write out compression parameters at the selected timestamp vs output power
			fPcomp.write('\nPout (dBm)\tgain (dB)\tcompression (dB)')
			for ip in range(0,len(self.pcomp_gain[it])):
				fPcomp.write('\n%10.2f\t%10.2f\t%10.2f' % (self.pcomp_pfund[it][ip],self.pcomp_gain[it][ip],self.pcomp_compression[it][ip]))
		fPcomp.close()
######################################################################################################################################################
# write pulsed transfer to disk
# these data are measured by the oscilloscope instead of the 4200
# Inputs:
# pathname
#
def X_writefile_pulsedtransfer(self, pathname=None, wafername='', xloc='0', yloc='0', Vds=0.,devicename=None,writetimedomain=True):
	pathname_IV = "".join([pathname, sub("DC")])
	if not hasattr(self,"Idp"): raise ValueError("ERROR! No pulsed transfer curve data exists")
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	filename = pathname_IV + "/" + devicename + "_pulsedtrans.xls"
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	fpt = open(filename, 'w')
	# parameters
	fpt.write('# device name\t' + devicename + '\n')
	fpt.write('# wafer name\t' + wafername + '\n')

	fpt.write('# x location um\t%d\n' % (int(xloc)))
	fpt.write('# y location um\t%d\n' % (int(yloc)))
	fpt.write('# drain voltage, Vds (V)\t%10.2f\n' % (Vds))

	# timestamp
	fpt.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fpt.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fpt.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fpt.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fpt.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fpt.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	if len(self.Idp)!=len(self.pulseVgs):   raise ValueError("ERROR! pulsed Vgs array not same size as pulsed Ids array")
	fpt.write('# Vgs pulsed (V)\tId pulsed(A\tId pulsed fraction std dev\n')
	for iVgs in range(0, len(self.pulseVgs)):
		fpt.write('%10.2f\t%10.2E\t%10.2E\n' % (self.pulseVgs[iVgs], self.Idp[iVgs], self.Idp_stddev[iVgs]))
	if writetimedomain:         # then write out the time-domain Id for each Vgs pulsed voltage
		fpt.write('#\n#\n# Time Domain drain current vs pulsed gate voltage\n#\n')
		for iVgs in range(0, len(self.pulseVgs)):
			fpt.write('pulsed Vgs\t%10.2f\n' %(self.pulseVgs[iVgs]))
			for it in range(0, len(self.Idt[iVgs])):          # write out timestamps and data
				fpt.write('%10.2E\t  %10.2f\t %10.2E\n' % (self.ts[iVgs][it],self.Vgst[iVgs][it], self.Idt[iVgs][it]))
	fpt.close()
	return [filename, devicename]
###################################################################################################################################################################

###################################################################################################################################################################
######################################################################################################################################################
# write burn sweep to disk. This is for multiple sweeps of increasing Vds
# Inputs:
# pathname
def X_writefile_burnsweepVds(self, pathname=None, wafername='', xloc='', yloc='',devicename=None):
	pathname_IV = "".join([pathname, sub("DC")])

	if not hasattr(self,"Id_burnfinal"): raise ValueError("ERROR! No burnsweep curve data exist")

	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	filename = pathname_IV + "/" + devicename + "_burnsweepVds.xls"
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	fburn = open(filename, 'w')
	# parameters
	fburn.write('# device name\t' + devicename + '\n')
	fburn.write('# wafer name\t' + wafername + '\n')

	fburn.write('# x location um\t%d\n' % (int(xloc)))
	fburn.write('# y location um\t%d\n' % (int(yloc)))
	fburn.write('# gate voltage setting, Vgs (V)\t%10.2f\n' % (self.Vgs_burn_set))
	#fburn.write('# Elapsed Time of measurment (sec)\t%10.2f\n' % (self.elapsed_time))
	#fburn.write('# Vgs rate of change (V/sec)\t%10.2f\n' % (self.Vdsslewrate_burn))

	# timestamp
	fburn.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fburn.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fburn.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fburn.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fburn.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fburn.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	if len(self.Idp)!=len(self.pulseVgs):   raise ValueError("ERROR! pulsed Vgs array not same size as pulsed Ids array")
	fburn.write('# Vds last (V)\tId last (A\tVgs last (V)\tIg last (A)\tdrainstatus last\tgatestatus last\tVds slew rate (V/sec)\n')
	for ii in range(0, len(self.Id_burnfinal)):
		fburn.write('%10.1f\t%10.2E\t%10.1f\t%s\t%s\t%10.2E\n' % (self.Vds_burnfinal[ii], self.Id_burnfinal[ii], self.Vgs_burnfinal[ii],self.drainstatus_burn[ii],self.gatestatus_burn[ii],self.Vdsslewrate_burn[ii]))
	fburn.close()
	return [filename, devicename]
###################################################################################################################################################################
# write burn sweep to disk. This is for a single sweep of Vds with Vgs held constant (generally in pinchoff)
# Inputs:
# pathname
def X_writefile_burnonesweepVds(self, pathname=None, wafername='', xloc='', yloc='',devicename=None,devicenamemodifier=""):
	pathname_IV = "".join([pathname, sub("DC")])

	if not hasattr(self,"Id_burnfinal"): raise ValueError("ERROR! No burnsweep curve data exist")

	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)

	if devicenamemodifier!="": devicename= "".join([devicenamemodifier, "_", devicename])

	filename = pathname_IV + "/" + devicename + "_burnsweepVds.xls"
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	fburn = open(filename, 'w')
	# parameters
	fburn.write('# device name\t' + devicename + '\n')
	fburn.write('# wafer name\t' + wafername + '\n')

	fburn.write('# x location um\t%d\n' % (int(xloc)))
	fburn.write('# y location um\t%d\n' % (int(yloc)))
	fburn.write('# gate voltage setting, Vgs (V)\t%10.2f\n' % (self.Vgs_burn_set))
	fburn.write('# Elapsed Time of measurment (sec)\t%10.2f\n' % (self.elapsed_time_burn))
	fburn.write('# Vgs rate of change (V/sec)\t%10.2f\n' % (self.Vdsslew_burn))

	# timestamp
	fburn.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fburn.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fburn.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fburn.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fburn.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fburn.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	if len(self.Idp)!=len(self.pulseVgs):   raise ValueError("ERROR! pulsed Vgs array not same size as pulsed Ids array")
	fburn.write('# Vds last (V)\tId last (A\tVgs last (V)\tIg last (A)\tdrainstatus last\tgatestatus last\tVds slew rate (V/sec)\n')
	for ii in range(0, len(self.Id_burnfinal)):
		fburn.write('%10.1f\t%10.2E\t%10.1f\t%s\t%s\t%10.2E\n' % (self.Vds_burn[ii], self.Id_burn[ii], self.Vgs_burn[ii],self.drainstatus_burn[ii],self.gatestatus_burn[ii],self.Vdsslewrate_burn[ii]))
	fburn.close()
	return [filename, devicename]
###################################################################################################################################################################
###################################################################################################################################################################
# write burn sweep final values (at max |Vds| to disk. This is for a single sweep of Vds with Vgs held constant (generally in pinchoff)
# Inputs:
# pathname
def X_writefile_burnonefinalvaluessweepVds(self, pathname=None, wafername='', xloc='', yloc='',devicename=None,writeheader=False,newfile=False):
	pathname_IV = "".join([pathname, sub("DC")])
	devicename = formdevicename(wafername, devicename)
	if not hasattr(self,"Id_burn"): raise ValueError("ERROR! No burnsweep curve data exist")
	if not hasattr(self,"Id_t"): raise ValueError("ERROR! No transfer curve data exist")

	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	filename = pathname_IV + "/" + devicename + "_burnsweepVds.xls"
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	if newfile:
		fburn=open(filename,'w')
	else: fburn = open(filename, 'a')

	# parameters
	if writeheader:
		fburn.write('# device name\t' + devicename + '\n')
		fburn.write('# wafer name\t' + wafername + '\n')

		fburn.write('# x location um\t%d\n' % (int(xloc)))
		fburn.write('# y location um\t%d\n' % (int(yloc)))
		fburn.write('# gate voltage setting, Vgs (V)\t%10.2f\n' % (self.Vgs_burn_set))
		#fburn.write('# Elapsed Time of measurment (sec)\t%10.2f\n' % (self.elapsed_time_burn))
		#fburn.write('# Vgs rate of change (V/sec)\t%10.2f\n' % (self.Vdsslew_burn))

		# timestamp
		fburn.write('# year\t' + str(dt.datetime.now().year) + '\n')
		fburn.write('# month\t' + str(dt.datetime.now().month) + '\n')
		fburn.write('# day\t' + str(dt.datetime.now().day) + '\n')
		fburn.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
		fburn.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
		fburn.write('# second\t' + str(dt.datetime.now().second) + '\n')
		# data
		if len(self.Vds_burn)!=len(self.Id_burn):   raise ValueError("ERROR! pulsed Vgs array not same size as pulsed Ids array")
		#if onoffratio!=None: fburn.write('# Vds last (V)\tId last (A\tVgs last (V)\tIg last (A)\tdrainstatus last\tgatestatus last\tOn-Off ratio post burn\tVds slew rate (V/sec)\n')
		#else: fburn.write('# Vds last (V)\tId last (A\tVgs last (V)\tIg last (A)\tdrainstatus last\tgatestatus last\tVds slew rate (V/sec)\n')
		fburn.write('# Vds last (V)\tId last (A\tIdmax post burn\tIdmin post burn\tVgs last (V)\tIg last (A)\tdrainstatus last\tgatestatus last\tOn-Off ratio post burn\tVds slew rate (V/sec)\n')
	# write just last point of burn curve
	#if onoffratio!=None: fburn.write('%10.1f\t%10.2E\t%10.1f\t%10.2E\t%s\t%s\t%10.1f\t%10.2f\n' % (self.Vds_burn[-1], self.Id_burn[-1], self.Vgs_burn[-1],self.Ig_burn[-1],self.drainstatus_burn[-1],self.gatestatus_burn[-1],onoffratio,self.Vdsslew_burn))
	#else: fburn.write('%10.1f\t%10.2E\t%10.1f\t%10.2E\t%s\t%s\t%10.2f\n' % (self.Vds_burn[-1], self.Id_burn[-1], self.Vgs_burn[-1],self.Ig_burn[-1],self.drainstatus_burn[-1],self.gatestatus_burn[-1],self.Vdsslew_burn))
	Idmax=max(np.abs(self.Id_t))
	Idmin=min(np.abs(self.Id_t))
	onoffratio=Idmax/Idmin
	fburn.write('%10.3f\t%10.3E\t%10.3E\t%10.3E\t%10.3f\t%10.3E\t%s\t%s\t%10.1f\t%10.2f\n' % (self.Vds_burn[-1], self.Id_burn[-1],Idmax,Idmin, self.Vgs_burn[-1],self.Ig_burn[-1],self.drainstatus_burn[-1],self.gatestatus_burn[-1],onoffratio,self.Vdsslew_burn))
	fburn.close()
	return [filename, devicename]
###################################################################################################################################################################
###################################################################################################################################################################
# write write time domain having pulsed Vgs
# uses output of measure_hysteresistimedomain() in parameter_analyzer.py
# timepointsperdecade throws out all but a few selected timepoints which are logarithmically evenly-spaced for each time decade
# writes time-domain data
def X_writefile_pulsedtimedomain4200(self,pathname=None,wafername='',xloc='0',yloc='0',timepointsperdecade=None,devicename=None,devicenamemodifier=""):
	if timepointsperdecade!=None: mulfactor=pow(10.,1./float(timepointsperdecade))                    # find factor to multiply by to get next timepoint
	if timepointsperdecade!=None and timepointsperdecade<=1.: raise ValueError("ERROR! must have at least one timepoint/decade")
	pathname_IV = "".join([pathname, sub("DC")])

	if devicenamemodifier!="": devicenamemodifier="".join(["_",devicenamemodifier])         # modify device name to indicate, for example different bias or other test conditions of the same device
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename, "_pulsedtimedomain.xls"])
	if not hasattr(self,"Id_td"): raise ValueError("ERROR! No pulsed transfer curve data exists")

	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)

	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	fpt = open(filename, 'w')
	# parameters
	fpt.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename, "_pulsedtimedomain.xls"]) + '\n')
	fpt.write('# wafer name\t' + wafername + '\n')

	fpt.write('# x location um\t%d\n' % (int(xloc)))
	fpt.write('# y location um\t%d\n' % (int(yloc)))
	fpt.write('# drain voltage, Vds (V)\t%10.2f\n' % (self.Vdsset))
	fpt.write('# quiescent time, (Sec)\t%10.2E\n' % (self.timequiescent))
	fpt.write('# gate quiescent voltage setting, (V)\t%10.2f\n' % (self.Vgsquiescent))
	# datetimestamp
	fpt.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fpt.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fpt.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fpt.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fpt.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fpt.write('# second\t' + str(dt.datetime.now().second) + '\n')

	# data
	# write out time-domain curves for each gate bias
	for iVgs in range(0, len(self.Vgssweeparray)):
		fpt.write("# Vgs\t%10.2f\n"%self.Vgssweeparray[iVgs])           # pulsed gate voltage setting
		fpt.write("# time (S)\tdrain current (A)\tgate current (A)\tdrain status\tgate status\n")           # labels
		# now write out the time-domain values for each timestep at Vgs pulsed voltage
		# note that the time steps start at the 2nd time point because the first point is the gate voltage quiescent bias
		if timepointsperdecade==None:
			for it in range(0, self.ntimepts):
				fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVgs][it+1], self.Id_td[iVgs][it+1], self.Ig_td[iVgs][it+1], self.drainstatus_td[iVgs][it+1], self.gatestatus_td[iVgs][it+1]))
		else:
			# reduce timepoints to obtain subset of time points
			selectedtimeindices = sorted(list(set([int(pow(mulfactor, i) + 0.5) for i in range(0, int(np.log(self.ntimepts) / np.log(mulfactor)) + 1) if pow(mulfactor, i) <= self.ntimepts])))
			for it in selectedtimeindices:
				fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVgs][it], self.Id_td[iVgs][it], self.Ig_td[iVgs][it], self.drainstatus_td[iVgs][it], self.gatestatus_td[iVgs][it]))
	fpt.close()
	return [filename, devicename]
###################################################################################################################################################################
###################################################################################################################################################################
# write time domain having pulsed Vgs for two devices which were simultaneously probed
# uses output of measure_hysteresistimedomain_dual_backgated() in parameter_analyzer.py
# timepointsperdecade throws out all but a few selected timepoints which are logarithmically evenly-spaced for each time decade
# writes time-domain data
# verified June 24, 2018
def X_writefile_pulsedtimedomain4200_dual(self,backgated=True,pathname=None,wafername='',xloc_probe='0',yloc_probe='0',xloc0='0',yloc0='0',xloc1='0',yloc1='0',timepointsperdecade=None,devicenames=None,devicenamemodifier=""):
	if timepointsperdecade!=None: mulfactor=pow(10.,1./float(timepointsperdecade))                    # find factor to multiply by to get next timepoint
	if timepointsperdecade!=None and timepointsperdecade<=1.: raise ValueError("ERROR! must have at least one timepoint/decade")
	pathname_IV = "".join([pathname, sub("DC")])
	if not hasattr(self,"Id0_td"): raise ValueError("ERROR! No pulsed transfer curve data exists")
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	devicename0=devicenames[0]
	devicename1=devicenames[1]
	if devicenamemodifier!="": devicenamemodifier="".join(["_",devicenamemodifier])
	# write left device (SMU1 on drain) data
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename0, "_pulsedtimedomain.xls"])
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	fpt = open(filename, 'w')
	# parameters
	fpt.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename0]) + '\n')
	fpt.write('# wafer name\t' + wafername + '\n')

	fpt.write('# probe x location um\t%d\n' % (int(xloc_probe)))
	fpt.write('# probe y location um\t%d\n' % (int(yloc_probe)))
	fpt.write('# x location um\t%d\n' % (int(xloc0)))
	fpt.write('# y location um\t%d\n' % (int(yloc0)))
	fpt.write('# drain voltage, Vds (V)\t%10.2f\n' % (self.Vdsset))
	fpt.write('# quiescent time, (Sec)\t%10.2E\n' % (self.timequiescent))
	fpt.write('# gate quiescent voltage setting, (V)\t%10.2f\n' % (self.Vgsquiescent))
	# datetimestamp
	fpt.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fpt.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fpt.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fpt.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fpt.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fpt.write('# second\t' + str(dt.datetime.now().second) + '\n')

	# data
	# left side device (SMU1 on drain)
	# write out time-domain curves for each gate bias
	for iVgs in range(0, len(self.Vgssweeparray)):
		fpt.write("# Vgs\t%10.2f\n"%self.Vgssweeparray[iVgs])           # pulsed gate voltage setting
		fpt.write("# time (S)\tdrain current (A)\tgate current (A)\tdrain status\tgate status\n")           # labels
		# now write out the time-domain values for each timestep at Vgs pulsed voltage
		# note that the time steps start at the 2nd time point because the first point is the gate voltage quiescent bias
		if timepointsperdecade==None:
			for it in range(0, self.ntimepts):
				if backgated:
					fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVgs][it+1], self.Id0_td[iVgs][it+1], self.Ig_td[iVgs][it+1], self.drainstatus0_td[iVgs][it+1], self.gatestatus_td[iVgs][it+1]))
				else:
					fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVgs][it+1], self.Id0_td[iVgs][it+1], self.Ig0_td[iVgs][it+1], self.drainstatus0_td[iVgs][it+1], self.gatestatus0_td[iVgs][it+1]))
		else:
			# reduce timepoints to obtain subset of time points
			selectedtimeindices = sorted(list(set([int(pow(mulfactor, i) + 0.5) for i in range(0, int(np.log(self.ntimepts) / np.log(mulfactor)) + 1) if pow(mulfactor, i) <= self.ntimepts])))
			for it in selectedtimeindices:
				if backgated:
					fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVgs][it], self.Id0_td[iVgs][it], self.Ig_td[iVgs][it], self.drainstatus0_td[iVgs][it], self.gatestatus_td[iVgs][it]))
				else:
					fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVgs][it], self.Id0_td[iVgs][it], self.Ig0_td[iVgs][it], self.drainstatus0_td[iVgs][it], self.gatestatus0_td[iVgs][it]))
	fpt.close()

	# write right device (SMU2 on drain) data
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename1, "_pulsedtimedomain.xls"])
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	fpt = open(filename, 'w')
	# parameters
	fpt.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename1]) + '\n')
	fpt.write('# wafer name\t' + wafername + '\n')

	fpt.write('# probe x location um\t%d\n' % (int(xloc_probe)))
	fpt.write('# probe y location um\t%d\n' % (int(yloc_probe)))
	fpt.write('# x location um\t%d\n' % (int(xloc1)))
	fpt.write('# y location um\t%d\n' % (int(yloc1)))
	fpt.write('# drain voltage, Vds (V)\t%10.2f\n' % (self.Vdsset))
	fpt.write('# quiescent time, (Sec)\t%10.2E\n' % (self.timequiescent))
	fpt.write('# gate quiescent voltage setting, (V)\t%10.2f\n' % (self.Vgsquiescent))
	# datetimestamp
	fpt.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fpt.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fpt.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fpt.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fpt.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fpt.write('# second\t' + str(dt.datetime.now().second) + '\n')

	# data
	# right side device (SMU2 on drain)
	# write out time-domain curves for each gate bias
	for iVgs in range(0, len(self.Vgssweeparray)):
		fpt.write("# Vgs\t%10.2f\n"%self.Vgssweeparray[iVgs])           # pulsed gate voltage setting
		fpt.write("# time (S)\tdrain current (A)\tgate current (A)\tdrain status\tgate status\n")           # labels
		# now write out the time-domain values for each timestep at Vgs pulsed voltage
		# note that the time steps start at the 2nd time point because the first point is the gate voltage quiescent bias
		if timepointsperdecade==None:
			for it in range(0, self.ntimepts):
				if backgated:
					fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVgs][it+1], self.Id1_td[iVgs][it+1], self.Ig_td[iVgs][it+1], self.drainstatus1_td[iVgs][it+1], self.gatestatus_td[iVgs][it+1]))
				else:
					fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVgs][it+1], self.Id1_td[iVgs][it+1], self.Ig1_td[iVgs][it+1], self.drainstatus1_td[iVgs][it+1], self.gatestatus1_td[iVgs][it+1]))
		else:
			# reduce timepoints to obtain subset of time points
			selectedtimeindices = sorted(list(set([int(pow(mulfactor, i) + 0.5) for i in range(0, int(np.log(self.ntimepts) / np.log(mulfactor)) + 1) if pow(mulfactor, i) <= self.ntimepts])))
			for it in selectedtimeindices:
				if backgated:
					fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVgs][it], self.Id1_td[iVgs][it], self.Ig_td[iVgs][it], self.drainstatus1_td[iVgs][it], self.gatestatus_td[iVgs][it]))
				else:
					fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVgs][it], self.Id1_td[iVgs][it], self.Ig1_td[iVgs][it], self.drainstatus1_td[iVgs][it], self.gatestatus1_td[iVgs][it]))
	fpt.close()
	return [filename, devicenames]
###################################################################################################################################################################
###################################################################################################################################################################
# write time domain having pulsed Vds
# uses output of measure_hysteresistimedomain_pulseddrain() in parameter_analyzer.py
# timepointsperdecade throws out all but a few selected timepoints which are logarithmically evenly-spaced for each time decade
# writes time-domain data
# tested Nov 8, 2018
def X_writefile_pulsedtimedomain4200_pulseddrain(self,pathname=None,wafername='',xloc='0',yloc='0',timepointsperdecade=None,devicename=None,devicenamemodifier=""):
	if timepointsperdecade!=None: mulfactor=pow(10.,1./float(timepointsperdecade))                    # find factor to multiply by to get next timepoint
	if timepointsperdecade!=None and timepointsperdecade<=1.: raise ValueError("ERROR! must have at least one timepoint/decade")
	pathname_IV = "".join([pathname, sub("DC")])
	if devicenamemodifier!="": devicenamemodifier="".join(["_",devicenamemodifier])         # modify device name to indicate, for example different bias or other test conditions of the same device
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename, "_pulsedtimedomaindrain.xls"])
	if not hasattr(self,"Id_td"): raise ValueError("ERROR! No pulsed transfer curve data exists")

	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)

	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	fpt = open(filename, 'w')
	# parameters
	fpt.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename, "_pulsedtimedomaindrain.xls"]) + '\n')
	fpt.write('# wafer name\t' + wafername + '\n')

	fpt.write('# x location um\t%d\n' % (int(xloc)))
	fpt.write('# y location um\t%d\n' % (int(yloc)))
	fpt.write('# gate voltage, Vgs (V)\t%10.2f\n' % (self.Vgsset))
	fpt.write('# quiescent time, (Sec)\t%10.2E\n' % (self.timequiescent))
	fpt.write('# drain quiescent voltage setting, (V)\t%10.2f\n' % (self.Vdsquiescent))
	# datetimestamp
	fpt.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fpt.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fpt.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fpt.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fpt.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fpt.write('# second\t' + str(dt.datetime.now().second) + '\n')

	# data
	# write out time-domain curves for each gate bias
	for iVds in range(0, len(self.Vdssweeparray)):
		fpt.write("# Vds\t%10.2f\n"%self.Vdssweeparray[iVds])           # pulsed drain voltage setting
		fpt.write("# time (S)\tdrain current (A)\tgate current (A)\tdrain status\tgate status\n")           # labels
		# now write out the time-domain values for each timestep at Vgs pulsed voltage
		# note that the time steps start at the 2nd time point because the first point is the gate voltage quiescent bias
		if timepointsperdecade==None:
			for it in range(0, self.ntimepts):
				#fpt.write('%10.2E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestep*(it+1), self.Id_td[iVgs][it+1], self.Ig_td[iVgs][it+1], self.drainstatus_td[iVgs][it+1], self.gatestatus_td[iVgs][it+1]))
				fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVds][it+1], self.Id_td[iVds][it+1], self.Ig_td[iVds][it+1], self.drainstatus_td[iVds][it+1], self.gatestatus_td[iVds][it+1]))
		else:
			# reduce timepoints to obtain subset of time points
			selectedtimeindices = sorted(list(set([int(pow(mulfactor, i) + 0.5) for i in range(0, int(np.log(self.ntimepts) / np.log(mulfactor)) + 1) if pow(mulfactor, i) <= self.ntimepts])))
			for it in selectedtimeindices:
				#fpt.write('%10.2E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestep*(it), self.Id_td[iVgs][it], self.Ig_td[iVgs][it], self.drainstatus_td[iVgs][it], self.gatestatus_td[iVgs][it]))
				fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVds][it], self.Id_td[iVds][it], self.Ig_td[iVds][it], self.drainstatus_td[iVds][it], self.gatestatus_td[iVds][it]))
	fpt.close()
	return [filename, devicename]
###################################################################################################################################################################
###################################################################################################################################################################
# write time domain having pulsed Vds for two devices which were simultaneously probed
# uses output of measure_hysteresistimedomain_pulseddrain_dual_backgated() in parameter_analyzer.py
# timepointsperdecade throws out all but a few selected timepoints which are logarithmically evenly-spaced for each time decade
# writes time-domain data
# handles both dual top and dual backgated cases
# verified topgated June 24, 2018
def X_writefile_pulsedtimedomain4200_pulseddrain_dual(self,backgated=True,pathname=None,wafername='',xloc0='0',yloc0='0',xloc1='0',yloc1='0',timepointsperdecade=None,devicenames=None,devicenamemodifier=""):
	if timepointsperdecade!=None: mulfactor=pow(10.,1./float(timepointsperdecade))                    # find factor to multiply by to get next timepoint
	if timepointsperdecade!=None and timepointsperdecade<=1.: raise ValueError("ERROR! must have at least one timepoint/decade")
	pathname_IV = "".join([pathname, sub("DC")])

	if not hasattr(self,"Id0_td") or not hasattr(self,"Id1_td"): raise ValueError("ERROR! No pulsed transfer curve data exists")

	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	devicename0=devicenames[0]
	devicename1=devicenames[1]
	if devicenamemodifier!="": devicenamemodifier="".join(["_",devicenamemodifier])
	# left side device #################################
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename0, "_pulsedtimedomaindrain.xls"])
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	fpt = open(filename, 'w')
	# parameters
	fpt.write('# device name\t' + "".join([wafername,devicenamemodifier,"__", devicename0]) + '\n')
	fpt.write('# wafer name\t' + wafername + '\n')

	fpt.write('# x location um\t%d\n' % (int(xloc0)))
	fpt.write('# y location um\t%d\n' % (int(yloc0)))
	fpt.write('# gate voltage, Vgs (V)\t%10.2f\n' % (self.Vgsset))
	fpt.write('# quiescent time, (Sec)\t%10.2E\n' % (self.timequiescent))
	fpt.write('# drain quiescent voltage setting, (V)\t%10.2f\n' % (self.Vdsquiescent))
	# datetimestamp
	fpt.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fpt.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fpt.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fpt.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fpt.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fpt.write('# second\t' + str(dt.datetime.now().second) + '\n')

	# data
	# write out time-domain curves for each gate bias
	for iVds in range(0, len(self.Vdssweeparray)):
		fpt.write("# Vds\t%10.2f\n"%self.Vdssweeparray[iVds])           # pulsed drain voltage setting
		fpt.write("# time (S)\tdrain current (A)\tgate current (A)\tdrain status\tgate status\n")           # labels
		# now write out the time-domain values for each timestep at Vgs pulsed voltage
		# note that the time steps start at the 2nd time point because the first point is the gate voltage quiescent bias
		if timepointsperdecade==None:
			for it in range(0, self.ntimepts):
				if backgated:
					fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVds][it+1], self.Id0_td[iVds][it+1], self.Ig_td[iVds][it+1], self.drainstatus0_td[iVds][it+1], self.gatestatus_td[iVds][it+1]))
				else:
					fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVds][it+1], self.Id0_td[iVds][it+1], self.Ig0_td[iVds][it+1], self.drainstatus0_td[iVds][it+1], self.gatestatus0_td[iVds][it+1]))
		else:
			# reduce timepoints to obtain subset of time points
			selectedtimeindices = sorted(list(set([int(pow(mulfactor, i) + 0.5) for i in range(0, int(np.log(self.ntimepts) / np.log(mulfactor)) + 1) if pow(mulfactor, i) <= self.ntimepts])))
			for it in selectedtimeindices:
				if backgated:
					fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVds][it], self.Id0_td[iVds][it], self.Ig_td[iVds][it], self.drainstatus0_td[iVds][it], self.gatestatus_td[iVds][it]))
				else:
					fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVds][it], self.Id0_td[iVds][it], self.Ig0_td[iVds][it], self.drainstatus0_td[iVds][it], self.gatestatus0_td[iVds][it]))
	fpt.close()

	# right side device ###############################
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename1, "_pulsedtimedomaindrain.xls"])
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	fpt = open(filename, 'w')
	# parameters
	fpt.write('# device name\t' + "".join([wafername,devicenamemodifier,"__", devicename1]) + '\n')
	fpt.write('# wafer name\t' + wafername + '\n')

	fpt.write('# x location um\t%d\n' % (int(xloc1)))
	fpt.write('# y location um\t%d\n' % (int(yloc1)))
	fpt.write('# gate voltage, Vgs (V)\t%10.2f\n' % (self.Vgsset))
	fpt.write('# quiescent time, (Sec)\t%10.2E\n' % (self.timequiescent))
	fpt.write('# drain quiescent voltage setting, (V)\t%10.2f\n' % (self.Vdsquiescent))
	# datetimestamp
	fpt.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fpt.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fpt.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fpt.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fpt.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fpt.write('# second\t' + str(dt.datetime.now().second) + '\n')

	# data
	# write out time-domain curves for each gate bias
	for iVds in range(0, len(self.Vdssweeparray)):
		fpt.write("# Vds\t%10.2f\n"%self.Vdssweeparray[iVds])           # pulsed drain voltage setting
		fpt.write("# time (S)\tdrain current (A)\tgate current (A)\tdrain status\tgate status\n")           # labels
		# now write out the time-domain values for each timestep at Vgs pulsed voltage
		# note that the time steps start at the 2nd time point because the first point is the gate voltage quiescent bias
		if timepointsperdecade==None:
			for it in range(0, self.ntimepts):
				if backgated:
					fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVds][it+1], self.Id1_td[iVds][it+1], self.Ig_td[iVds][it+1], self.drainstatus1_td[iVds][it+1], self.gatestatus_td[iVds][it+1]))
				else:
					fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVds][it+1], self.Id1_td[iVds][it+1], self.Ig1_td[iVds][it+1], self.drainstatus1_td[iVds][it+1], self.gatestatus1_td[iVds][it+1]))
		else:
			# reduce timepoints to obtain subset of time points
			selectedtimeindices = sorted(list(set([int(pow(mulfactor, i) + 0.5) for i in range(0, int(np.log(self.ntimepts) / np.log(mulfactor)) + 1) if pow(mulfactor, i) <= self.ntimepts])))
			for it in selectedtimeindices:
				if backgated:
					fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVds][it], self.Id1_td[iVds][it], self.Ig_td[iVds][it], self.drainstatus1_td[iVds][it], self.gatestatus_td[iVds][it]))
				else:
					fpt.write('%10.4E\t%10.2E\t%10.2E\t%s\t%s\n' % (self.timestamp_td[iVds][it], self.Id1_td[iVds][it], self.Ig1_td[iVds][it], self.drainstatus1_td[iVds][it], self.gatestatus1_td[iVds][it]))
	fpt.close()
	return [filename, devicenames]
###################################################################################################################################################################
###################################################################################################################################################################
# write transfer curve having pulsed Vgs
# uses output of measure_hysteresistimedomain_backgate() in parameter_analyzer.py
# Inputs:
# pathname
# this writes the the time domain data as a transfer curve at each timestep
def X_writefile_pulsedtransfertimedomain4200(self,pathname=None,wafername='',xloc='0',yloc='0',timepointsperdecade=None,devicename=None,devicenamemodifier=""):
	if timepointsperdecade != None and timepointsperdecade <= 1.: raise ValueError("ERROR! must have at least one timepoint/decade")
	pathname_IV = "".join([pathname, sub("DC")])
	if devicenamemodifier!="": devicename = "".join([devicenamemodifier, "_", devicename])                 # modify device name to indicate, for example different bias or other test conditions of the same device
	devicename = formdevicename(wafername, devicename)
	if not hasattr(self,"Id_td"): raise ValueError("ERROR! No pulsed transfer curve data exists")

	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	filename = pathname_IV + "/" + devicename + "_pulsedtransfertimedomain.xls"
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	fpt = open(filename, 'w')
	# parameters
	fpt.write('# device name\t' + devicename + '\n')
	fpt.write('# wafer name\t' + wafername + '\n')

	fpt.write('# x location um\t%d\n' % (int(xloc)))
	fpt.write('# y location um\t%d\n' % (int(yloc)))
	fpt.write('# drain voltage, Vds (V)\t%10.2f\n' % (self.Vdsset))
	fpt.write('# quiescent time, (Sec)\t%10.2E\n' % (self.timequiescent))
	fpt.write('# gate quiescent voltage setting, (V)\t%10.2f\n' % (self.Vgsquiescent))
	# timestamp
	fpt.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fpt.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fpt.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fpt.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fpt.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fpt.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# data
	# write out time-domain curves for each gate bias
	if timepointsperdecade == None:
		for it in range(0, self.ntimepts):
			#fpt.write("# time (S)\t%10.2E\n"%(self.timestep*(it+1)))         # pulsed gate voltage setting
			fpt.write("# time (S)\t%10.2E\n"%(self.timestamp_td[0][it]))         # write timestamps assuming that they're the same for all gate voltages
			fpt.write("# Vgs (V)\tdrain current (A)\tgate current (A)\tdrain status\tgate status\n")           # labels
			#print("from writefile_measured.py line 1077 timestamp",self.timestep*(it+1))
			# now write out the time-domain values for each timestep at Vgs pulsed voltage
			# note that the time steps start at the 2nd time point because the first point is the gate voltage quiescent bias
			for iVgs in range(0, len(self.Vgssweeparray)):
				fpt.write('%10.2f\t%10.2E\t%10.2E\t%s\t%s\n' % (self.Vgssweeparray[iVgs], self.Id_td[iVgs][it+1], self.Ig_td[iVgs][it+1], self.drainstatus_td[iVgs][it+1], self.gatestatus_td[iVgs][it+1]))
	else:
		# reduce timepoints to obtain subset of time points
		mulfactor = pow(10., 1. / float(timepointsperdecade))  # find factor to multiply by to get next timepoint
		selectedtimeindices = sorted(list(set([int(pow(mulfactor, i) + 0.5) for i in range(0, int(np.log(self.ntimepts) / np.log(mulfactor)) + 1) if pow(mulfactor, i) <= self.ntimepts])))
		for it in selectedtimeindices:
			#fpt.write("# time (S)\t%10.2E\n" % (self.timestep *it))  # pulsed gate voltage setting
			fpt.write("# time (S)\t%10.2E\n"%(self.timestamp_td[0][it]))         # write timestamps assuming that they're the same for all gate voltages
			fpt.write("# Vgs (V)\tdrain current (A)\tgate current (A)\tdrain status\tgate status\n")  # labels
			# print("from writefile_measured.py line 1077 timestamp",self.timestep*(it+1))
			# now write out the time-domain values for each timestep at Vgs pulsed voltage
			# note that the time steps start at the 2nd time point because the first point is the gate voltage quiescent bias
			for iVgs in range(0, len(self.Vgssweeparray)):
				# print("from writefile_measured.py line 1081 timestamp, Vgs",self.timestep*(it+1),self.Vgssweeparray[iVgs])
				fpt.write('%10.2f\t%10.2E\t%10.2E\t%s\t%s\n' % (self.Vgssweeparray[iVgs], self.Id_td[iVgs][it], self.Ig_td[iVgs][it], self.drainstatus_td[iVgs][it], self.gatestatus_td[iVgs][it]))
	fpt.close()
	return [filename, devicename]
###################################################################################################################################################################
###################################################################################################################################################################
# write the noise measurements to a file using the Touchstone format
# def X_writefile_spar(self, pathname, lotname, wafernumber, diecolumn, dierow, subsitename, xloc, yloc, Vds, Id, drainstatus, Vgs, Ig, gatestatus):
# The device name may be supplied or the parameters from Cascade Nucleus may be supplied to form the devicename
# For user-defined probe test plans, the devicename is obtained from the probe test file and must be supplied to this function as the devicename
def X_writefile_noise(self,pathname=None,devicename=None,wafername="",xloc=0,yloc=0,Vds=0.,Vgs=0.,Id=0.,Ig=0.,gatestatus="",drainstatus="",devicenamemodifier=""):
	pathname_RF=pathname+sub("SPAR")
	if devicenamemodifier!="": devicename = "".join([devicenamemodifier, "_", devicename])                 # modify device name to indicate, for example different bias or other test conditions of the same device
	devicename = formdevicename(wafername,devicename)
	try:
		self.NF  # do noise figure data exist?
	except:
		print("ERROR! NO frequency array so found! NO noise data written")
		return
	if not os.path.exists(pathname_RF):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_RF)
	filename = pathname_RF + "/" + devicename + "_noise.xls"
	fn = open(filename, 'w')
	# device parameters file header
	fn.write('# device name\t' + devicename + '\n')
	fn.write('# wafer name\t' + wafername + '\n')

	fn.write('# x location um\t%d\n' % int(xloc))
	fn.write('# y location um\t%d\n' % int(yloc))
	fn.write('# Vds (V)\t%10.2f\n' % Vds)
	fn.write('# Id (A)\t%10.2E\n' % Id)
	fn.write('# drain status\t%s\n' % drainstatus)
	fn.write('# Vgs (V)\t%10.2f\n' % Vgs)
	fn.write('# Ig (A)\t%10.2E\n' % Ig)
	fn.write('# gate status\t%s\n' % gatestatus)
	# timestamp
	fn.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fn.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fn.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fn.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fn.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fn.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# datatype header
	fn.write("#\n#\n# system Z=50ohms\n")
	# write data to file
	if self.gaDUT!=None:
		fn.write("# frequency_MHz\tDUT gaindB\tDUT MAG dB\tDUT noisefigure dB\tDUT+noisemeter gain dB\tDUT+noisemeter NoisefiguredB\n")
		for freq in list(self.NF.keys()):
			fn.write("%s\t" % (freq))
			fn.write(" %7.2f\t" % (self.gainDUT[freq]))
			fn.write(" %7.2f\t" % (self.gaDUT[freq]))
			fn.write(" %7.2f\t" % (self.NFDUT[freq]))
			fn.write(" %7.2f\t" % (self.gain[freq]))
			fn.write(" %7.2f\t\n" % (self.NF[freq]))
	else:
		fn.write("# frequency_MHz\tDUT gaindB\tDUT noisefigure dB\n")
		for freq in list(self.NF.keys()):
			fn.write("%s\t" % (freq))
			fn.write(" %7.2f\t" % (self.gainDUT[freq]))
			fn.write(" %7.2f\n" % (self.NFDUT[freq]))
	fn.close()
	return [filename, devicename]
##################################################################################################################
# writes noise parameters to a file at a single bias point and multiple frequencies
# inputs: (besides those in the parameter list)
# self.NP[ifreq][para] where ifreq is the frequency index and para is the dictionary key = 'frequency' (for frequency in Hz), 'gopt' for the optimum noise source reflection coefficient
# real+jimaginary, 'FmindB' for the minimum noise figure in dB, 'Rn' for the noise resistance in ohms
def X_writefile_noiseparameters(self,pathname=None,devicename="",wafername="",xloc=0,yloc=0,Vds=0.,Vgs=0.,Id=0.,Ig=0.,gatestatus="",drainstatus="",devicenamemodifier=""):
	pathname_RF=pathname+sub("SPAR")
	if devicenamemodifier!="": devicename = "".join([devicenamemodifier, "_", devicename])                 # modify device name to indicate, for example different bias or other test conditions of the same device
	devicename = formdevicename(wafername,devicename)
	try:
		self.NP  # do noise parameter data exist?
	except:
		print("ERROR! NO frequency array so found! NO noise data written")
		return
	if not os.path.exists(pathname_RF):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_RF)
	filename = pathname_RF + "/" + devicename + "_noiseparameter.xls"
	fn = open(filename, 'w')
	# device parameters file header
	fn.write('# device name\t' + devicename + '\n')
	fn.write('# wafer name\t' + wafername + '\n')

	fn.write('# x location um\t%d\n' % int(xloc))
	fn.write('# y location um\t%d\n' % int(yloc))
	fn.write('# Vds (V)\t%10.2f\n' % Vds)
	fn.write('# Id (A)\t%10.2E\n' % Id)
	fn.write('# drain status\t%s\n' % drainstatus)
	fn.write('# Vgs (V)\t%10.2f\n' % Vgs)
	fn.write('# Ig (A)\t%10.2E\n' % Ig)
	fn.write('# gate status\t%s\n' % gatestatus)
	# timestamp
	fn.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fn.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fn.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fn.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fn.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fn.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# datatype header
	fn.write("#\n#\n# system Z=50ohms\n")
	# write data to file
	if 'GassocdB' in self.NP[0].keys(): fn.write("# frequency_GHz\tFmindB\tgammaopt_mag\t gammaopt_angle\tRn_(ohms)\tassociated_gain_dB\tgain_type\n")
	else: fn.write("# frequency_GHz\tFmindB\tgammaopt_mag\t gammaopt_angle\tRn_(ohms)\n")
	for p in self.NP:
		if 'GassocdB' in p.keys(): fn.write("%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%s\n" %(1E-9*p['frequency'],p['FmindB'],convertRItoMA(p['gopt']).real,convertRItoMA(p['gopt']).imag,p['Rn'],p['GassocdB'],p['gain_type']))
		else: fn.write("%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\n" %(1E-9*p['frequency'],p['FmindB'],convertRItoMA(p['gopt']).real,convertRItoMA(p['gopt']).imag,p['Rn']))
	fn.close()
	return [filename, devicename]
##################################################################################################################
# writes DUT deembedded noise figure (dB) to a file at a single bias point and multiple frequencies as a function of tuner position and source reflection coefficient presented to the DUT
# inputs: (besides those in the parameter list)
# self.NP[ifreq][para] where ifreq is the frequency index and para is the dictionary key = 'frequency' (for frequency in Hz), 'gopt' for the optimum noise source reflection coefficient
# real+jimaginary, 'FmindB' for the minimum noise figure in dB, 'Rn' for the noise resistance in ohms
def X_writefile_noisefigure(self,pathname=None,devicename=None,wafername="",xloc=0,yloc=0,Vds=0.,Vgs=0.,Id=0.,Ig=0.,gatestatus="",drainstatus="",devicenamemodifier=""):
	pathname_RF=pathname+sub("SPAR")
	if devicenamemodifier!="": devicename = "".join([devicenamemodifier, "_", devicename])                 # modify device name to indicate, for example different bias or other test conditions of the same device
	devicename = formdevicename(wafername,devicename)
	try:
		self.NF  # do noise data exist?
	except:
		print("ERROR! NO frequency array so found! NO noise data written")
		return
	if not os.path.exists(pathname_RF):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_RF)
	filename = pathname_RF + "/" + devicename + "_noisefigure.xls"
	fn = open(filename, 'w')
	# device parameters file header
	fn.write('# device name\t' + devicename + '\n')
	fn.write('# wafer name\t' + wafername + '\n')

	fn.write('# x location um\t%d\n' % int(xloc))
	fn.write('# y location um\t%d\n' % int(yloc))
	fn.write('# Vds (V)\t%10.2f\n' % Vds)
	fn.write('# Id (A)\t%10.2E\n' % Id)
	fn.write('# drain status\t%s\n' % drainstatus)
	fn.write('# Vgs (V)\t%10.2f\n' % Vgs)
	fn.write('# Ig (A)\t%10.2E\n' % Ig)
	fn.write('# gate status\t%s\n' % gatestatus)
	# timestamp
	fn.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fn.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fn.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fn.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fn.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fn.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# datatype header
	fn.write("#\n#\n# system Z=50ohms\n")
	# write data to file
	for ifr in range(0,len(self.NF)):
		fn.write('# frequency\t%10.2fGHZ\n'%(1E-9*self.NF[ifr]['frequency']))
		fn.write('! tuner position\treflection coefficient mag angle\tnoisefigure dB\tnoisefigure dB calculated from noise parameters\n')
		for pos in self.NF[ifr].keys():
			if str(pos)!="frequency":           # exclude frequencies - looking at tuner positions only
				reflectioncoef=convertRItoMA(self.get_tuner_reflection(position=pos,frequency=self.NF[ifr]['frequency']))
				noisefiguredB=10.*np.log10(self.NF[ifr][pos])            # convert noisefigure to dB
				ifcn=min(range(len(self.NFcalcfromNP)), key=lambda i:abs(self.NFcalcfromNP[i]['frequency']-self.NF[ifr]['frequency']))
				fn.write('%s\t%10.2f %10.1f\t%10.2f\t%10.2f\n'%(str(pos),reflectioncoef.real,reflectioncoef.imag,noisefiguredB,self.NFcalcfromNP[ifcn][pos]))
	fn.close()
	return [filename, devicename]
#############################################################################################################################################################
#############################################################################################################################################################
# New versions of the above using new data format
##################################################################################################################
# writes noise parameters to a file at a single bias point and multiple frequencies
# inputs: (besides those in the parameter list)
# self.NP[frequency][para] where frequency is in MHz and para is the dictionary key =  'gopt' for the optimum noise source reflection coefficient
# real+jimaginary, 'FmindB' for the minimum noise figure in dB, 'Rn' for the noise resistance in ohms
def X_writefile_noiseparameters_v2(self,pathname=None,devicename="",wafername="",xloc=0,yloc=0,Vds=0.,Vgs=0.,Id=0.,Ig=0.,gatestatus="",drainstatus="",devicenamemodifier=""):
	pathname_RF=pathname+sub("SPAR")
	#if devicenamemodifier!="": devicename = "".join([devicenamemodifier, "_", devicename])                 # modify device name to indicate, for example different bias or other test conditions of the same device
	try:
		self.NP  # do noise parameter data exist?
	except:
		print("ERROR! NO frequency array so found! NO noise data written")
		return
	if not os.path.exists(pathname_RF):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_RF)
	filename = "".join([pathname_RF,"/",wafername,devicenamemodifier,"__", devicename, "_noiseparameter.xls"])
	fn = open(filename, 'w')
	# device parameters file header
	#fn.write('# device name\t' + devicename + '\n')
	if devicenamemodifier=="": fn.write('! device name\t' + "".join([wafername,devicenamemodifier,"__", devicename])+ '\n')
	else: fn.write('! device name\t' + "".join([wafername,devicenamemodifier,"_", devicename])+ '\n')
	fn.write('# wafer name\t' + wafername + '\n')

	fn.write('# x location um\t%d\n' % int(xloc))
	fn.write('# y location um\t%d\n' % int(yloc))
	fn.write('# Vds (V)\t%10.2f\n' % Vds)
	fn.write('# Id (A)\t%10.2E\n' % Id)
	fn.write('# drain status\t%s\n' % drainstatus)
	fn.write('# Vgs (V)\t%10.2f\n' % Vgs)
	fn.write('# Ig (A)\t%10.2E\n' % Ig)
	fn.write('# gate status\t%s\n' % gatestatus)
	# timestamp
	fn.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fn.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fn.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fn.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fn.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fn.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# datatype header
	fn.write("#\n#\n# system Z=50ohms\n")
	# write data to file
	f0=list(self.NP.keys())[0]              # get noise parameter data from one of the frequency points to check to see if associated gain GassocdB is included
	if 'GassocdB' in self.NP[f0].keys(): fn.write("# frequency_GHz\tFmindB\tgammaopt_mag\t gammaopt_angle\tRn_(ohms)\tassociated_gain_dB\tavailable_gain_dB\n")
	else: fn.write("# frequency_GHz\tFmindB\tgammaopt_mag\t gammaopt_angle\tRn_(ohms)\n")
	frequencies=list(map(str,sorted([int(f) for f in list(self.NP.keys())])))                       # sort frequencies in ascending value. Needed to use map() to sort frequencies since they are of type str
	for f in frequencies:
		if 'GassocdB' in self.NP[f].keys(): fn.write("%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%s\n" %(1E-3*int(f),self.NP[f]['FmindB'],convertRItoMA(self.NP[f]['gopt']).real,convertRItoMA(self.NP[f]['gopt']).imag,self.NP[f]['Rn'],self.NP[f]['GassocdB'],self.NP[f]['gavaildB']))    # write out frequency in GHz
		else: fn.write("%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\n" %(1E-3*int(f),self.NP[f]['FmindB'],convertRItoMA(self.NP[f]['gopt']).real,convertRItoMA(self.NP[f]['gopt']).imag,self.NP[f]['Rn']))
	fn.close()
	return [filename, devicename]
##################################################################################################################
##################################################################################################################
# writes noise parameters to a file at a single bias point and multiple frequencies
# inputs:
# pathname+wafername+devicename+devicenamemodifier = full output filename
# xloc, yloc, are the integer locations (um) of the device, on the wafer
# Vds -> drain voltage, Id -> drain currrent in A, Vgs-> gate voltage, Ig -> gate current in A, gatestatus, drainstatus both tell if the gate and/or drain are current-limited respectively
# NP are the noise parameters, NP[f][type] where f is the frequency in MHz and type is one of 'FmindB', 'gopt', or 'Rn' to designate the noise parameters, 'gopt' is the optimum for noise reflection coefficient in real+jimaginary
def writefile_noiseparameters_coldsource(pathname=None,devicename="",wafername="",xloc=0,yloc=0,Vds=0.,Vgs=0.,Id=0.,Ig=0.,gatestatus="",drainstatus="",NP=None,videobandwidth=None, resolutionbandwidth=None,devicenamemodifier=""):
	pathname_RF=pathname+sub("SPAR")
	if NP==None: raise ValueError("ERROR! no noise parameters given")
	if not os.path.exists(pathname_RF):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_RF)
	filename = "".join([pathname_RF,"/",wafername,devicenamemodifier,"__", devicename, "_noiseparameter.xls"])
	fn = open(filename, 'w')
	# device parameters file header
	#fn.write('# device name\t' + devicename + '\n')
	if devicenamemodifier=="": fn.write('! device name\t' + "".join([wafername,devicenamemodifier,"__", devicename])+ '\n')
	else: fn.write('! device name\t' + "".join([wafername,devicenamemodifier,"_", devicename])+ '\n')
	fn.write('# wafer name\t' + wafername + '\n')
	fn.write('# x location um\t%d\n' % int(xloc))
	fn.write('# y location um\t%d\n' % int(yloc))
	fn.write('# Vds (V)\t%10.2f\n' % Vds)
	fn.write('# Id (A)\t%10.2E\n' % Id)
	fn.write('# drain status\t%s\n' % drainstatus)
	fn.write('# Vgs (V)\t%10.2f\n' % Vgs)
	fn.write('# Ig (A)\t%10.2E\n' % Ig)
	fn.write('# gate status\t%s\n' % gatestatus)
	fn.write('# video bandwidth Hz\t%d\n' % videobandwidth)
	fn.write('# resolution bandwidth Hz\t%d\n' % resolutionbandwidth)
	# timestamp
	fn.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fn.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fn.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fn.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fn.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fn.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# datatype header
	fn.write("#\n#\n# system Z=50ohms\n")
	# write data to file
	f0=list(NP.keys())[0]              # get noise parameter data from one of the frequency points to check to see if associated gain GassocdB is included
	frequencies_str=[str(f) for f in list(map(str,sorted([int(f) for f in list(NP.keys())])))  ]                     # sort frequencies in ascending value. convert to type str
	# write the headers
	if 'gassoc' in NP[f0].keys():       # then this is a DUT measurement
		if NP[frequencies_str[0]]['K']<1: fn.write("#_frequency_MHz\tFmindB\tgammaopt_mag\tgammaopt_angle\tRn_(ohms)\tassociated gain dB\tmaximum_stable_gain_dB\n")        # the DUT is conditionally stable
		else: fn.write("#_frequency_GHz\tFmindB\tgammaopt_mag\t gammaopt_angle\tRn_(ohms)\tassociated_gain_dB\tmaximum_available_gain_dB\tconjugate_input_match_mag\tconjugate_input_match_ang_(deg)\tconjugate_output_match_mag\tconjugate_output_match_ang_(deg)\n")         # the DUT is unconditionally stable
	else: fn.write("#_frequency_GHz\tFmindB\tgammaopt_mag\tgammaopt_angle\tRn_(ohms)\n")       # No associated gain exists because we measured the noise parameters of the noise system itself
	# write the data
	for f in frequencies_str:
		if 'gassoc' in NP[f].keys():    # then this is a DUT measurement
			if NP[f]['K']<1: fn.write("%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\n" %(int(f),NP[f]['FmindB'],convertRItoMA(NP[f]['gopt']).real,convertRItoMA(NP[f]['gopt']).imag,NP[f]['Rn'],lintodB(NP[f]['gassoc']),lintodB(NP[f]['MAG'])))    # the DUT is conditionally stable
			else:
				fn.write("%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\n" %(1E-3*int(f),NP[f]['FmindB'],convertRItoMA(NP[f]['gopt']).real,convertRItoMA(NP[f]['gopt']).imag,NP[f]['Rn'],lintodB(NP[f]['gassoc']),lintodB(NP[f]['MAG']),
				                                                                                        convertRItoMA(NP[f]['gammainopt']).real,convertRItoMA(NP[f]['gammainopt']).imag,convertRItoMA(NP[f]['gammaoutopt']).real,convertRItoMA(NP[f]['gammaoutopt']).imag))    # the DUT is unconditionally stable
		else:
			fn.write("%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\n" %(1E-3*int(f),NP[f]['FmindB'],convertRItoMA(NP[f]['gopt']).real,convertRItoMA(NP[f]['gopt']).imag,NP[f]['Rn']))
	fn.close()
	return [filename, devicename]
##################################################################################################################
##################################################################################################################
# writes DUT deembedded noise figure (dB) to a file at a single bias point and multiple frequencies as a function of tuner position and source reflection coefficient presented to the DUT
# inputs: (besides those in the parameter list)
# NF[frequency][para] where frequency is the dict key in MHz and para is the dictionary key = 'gopt' for the optimum noise source reflection coefficient
# real+jimaginary, 'FmindB' for the minimum noise figure in dB, 'Rn' for the noise resistance in ohms
def writefile_noisefigure_coldsource(pathname=None,devicename=None,wafername="",xloc=0,yloc=0,Vds=0.,Vgs=0.,Id=0.,Ig=0.,gatestatus="",drainstatus="",NF=None, NFcalcfromNP=None,noise=None,gammatunerMA=None,videobandwidth=None, resolutionbandwidth=None,devicenamemodifier=""):
	pathname_RF=pathname+sub("SPAR")
	#if devicenamemodifier!="": devicename = "".join([devicenamemodifier, "_", devicename])                 # modify device name to indicate, for example different bias or other test conditions of the same device
	if not os.path.exists(pathname_RF):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_RF)
	filename = "".join([pathname_RF,"/",wafername,devicenamemodifier,"__", devicename, "_noisefigure.xls"])
	#filename = pathname_RF + "/" + devicename + "_noisefigure.xls"
	fn = open(filename, 'w')
	# device parameters file header
	#fn.write('# device name\t' + devicename + '\n')
	if devicenamemodifier=="": fn.write('! device name\t' + "".join([wafername,devicenamemodifier,"__", devicename])+ '\n')
	else: fn.write('! device name\t' + "".join([wafername,devicenamemodifier,"_", devicename])+ '\n')
	fn.write('# wafer name\t' + wafername + '\n')
	fn.write('# x location um\t%d\n' % int(xloc))
	fn.write('# y location um\t%d\n' % int(yloc))
	fn.write('# Vds (V)\t%10.2f\n' % Vds)
	fn.write('# Id (A)\t%10.2E\n' % Id)
	fn.write('# drain status\t%s\n' % drainstatus)
	fn.write('# Vgs (V)\t%10.2f\n' % Vgs)
	fn.write('# Ig (A)\t%10.2E\n' % Ig)
	fn.write('# gate status\t%s\n' % gatestatus)
	fn.write('# video bandwidth Hz\t%d\n' % videobandwidth)
	fn.write('# resolution bandwidth Hz\t%d\n' % resolutionbandwidth)
	# timestamp
	fn.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fn.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fn.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fn.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fn.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fn.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# datatype header
	fn.write("#\n#\n# system Z=50ohms\n")
	# write data to file
	frequencies_str=[str(f) for f in list(map(str,sorted([int(f) for f in list(NF.keys())])))  ]                     # sort frequencies in ascending value. convert to type str
	for f in frequencies_str:
		fn.write('# frequency\t%10.2fGHZ\n'%(1E-3*int(f)))
		fn.write('# tuner position\treflection coefficient mag\t reflection coefficient angle (deg)\tnoisefigure dB measured\tnoisefigure dB calculated from noise parameters\tspectrum analyzer noise mW\n')
		for pos in NF[f].keys():               # tuner motor positions used to produce the noise figure
			fn.write('%s\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.3E\n'%(str(pos),gammatunerMA[f][pos].real,gammatunerMA[f][pos].imag,lintodB(NF[f][pos]),NFcalcfromNP[f][pos],noise[f][pos]))
	fn.close()
	return [filename, devicename]
####################################################################################################################################################################
##################################################################################################################
# writes noise parameters to a file at a swept gate bias and single drain bias and multiple frequencies
# inputs: (besides those in the parameter list)
# NP are the DUT noise parameters. NP[frequency MHz]['parametertype'][timestampindex] where 'parametertype' is FmindB, gopt, Rn, GassocdB, gain_type, gavaildB, gammainopt, and gammaoutopt
# real+jimaginary, 'FmindB' for the minimum noise figure in dB, 'Rn' for the noise resistance in ohms
# drain current in A interpolated in timestampindex Id[frequencyMHz][tuner position]['I' or 'time'][timestampindex] captured at the given tuner position and frequency measurement where 'I' gives the current in amps and 'time' the time in seconds
# Id is the drain current vs time in A, Id[timestampindex],
# Vgs[timestampindex] is the gate voltage vs time
# NP is are the DUT noise parameters vs frequency and time, NP[frequencyMHz]['parametertype'][timestampindex] where 'parametertype' is FmindB, gopt=real+jimaginary, Rn, GassocdB, gain_type, gavaildB, gammainopt, and gammaoutopt. If the DUT is unconditionally stable, then gammainopt, and gammaoutopt are the reflection coefficient (real+jimaginary) which simultaneously produce an imput and output match respectively. If the DUT is conditionally stable, the both gammainopt, and gammaoutopt are set to None.
# NFcalcfromNP is the DUT noise figure in dB calculated from the DUT noise parameters, noise figures of the DUT calculated from DUT noise parameters at each tuner position (tuner reflection coefficient). NFcalcfromNPtimedomain[frequencyMHz][tuner position][timestampindex].
# NF is the measured DUT noise figure, linear NOT dB, [frequencyMHz][tuner_position][timestampindex]
# timestamps are the timestamps in Sec
#
def writefile_noiseparameters_Vgssweep(pathname=None,devicename="",wafername="",xloc=0,yloc=0,Vds=0.,Id=None,NP=None,Vgs=None,videobandwidth=None, resolutionbandwidth=None,timestamps=None,devicenamemodifier=""):
	if pathname == None: raise ValueError("ERROR Must include pathname")
	if devicename == None: raise ValueError("ERROR Must give device name for this measurement")
	pathname_RF=pathname+sub("SPAR")
	if NP==None: raise ValueError("ERROR! no DUT noiseparameters given")
	if Vgs==None: raise ValueError("ERROR! no gate voltage given")
	if Id==None: raise ValueError("ERROR! no drain current given")
	if timestamps==None: raise ValueError("ERROR! no timestamps given")
	#if len(timestamps)!=len(Vgs): raise ValueError("number of timestamps not equal to number of Vgs")
	#if len(timestamps)!=len(Id): raise ValueError("number of timestamps not equal to number of Id")
	#if len(NP)!=len(Id): raise ValueError("number of timestamps not equal to number of Id")

	if not os.path.exists(pathname_RF):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_RF)
	filename = "".join([pathname_RF,"/",wafername,devicenamemodifier,"__", devicename, "_noiseparameter.xls"])
	f = open(filename, 'w')
	# device parameters file header
	if devicenamemodifier=="": f.write('! device name\t' + "".join([wafername,devicenamemodifier,"__", devicename])+ '\n')
	else: f.write('! device name\t' + "".join([wafername,devicenamemodifier,"_", devicename])+ '\n')
	############
	f.write('# wafer name\t' + wafername + '\n')
	f.write('# x location um\t%d\n' % int(xloc))
	f.write('# y location um\t%d\n' % int(yloc))
	f.write('# Vds (V)\t%10.2f\n' % Vds)
	#f.write('# gate status\t%s\n' % gatestatus)
	f.write('# video bandwidth Hz\t%d\n' % videobandwidth)
	f.write('# resolution bandwidth Hz\t%d\n' % resolutionbandwidth)
	# timestamp
	f.write('# year\t' + str(dt.datetime.now().year) + '\n')
	f.write('# month\t' + str(dt.datetime.now().month) + '\n')
	f.write('# day\t' + str(dt.datetime.now().day) + '\n')
	f.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	f.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	f.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# datatype header
	f.write("#\n#\n# system Z=50ohms\n")
	# write data to file
	# sort frequencies in ascending value. Needed to use map() to sort frequencies since they are of type str
	frequencies_str=[str(fr) for fr in list(map(str,sorted([int(fx) for fx in list(NP.keys())])))  ]                     # sort frequencies in ascending value. convert to type str

	for fs in frequencies_str:
		f.write('\n# frequency_GHz\t%s' %(fs))
		f.write("\n# time (S)\tFmin (dB)\tgammaopt magnitude\tgammaopt angle deg\tRn (ohms)\tassociated gain dB\tVgs (V)\tId (A)\tmaximum_available_gain_dB\tconjugate_input_match_mag\tconjugate_input_match_ang_(deg)\tconjugate_output_match_mag\tconjugate_output_match_ang_(deg)")
		for  it in range(0,len(timestamps)):
			if NP[fs]['K'][it]>=1:       # 2-port is unconditionally stable
				f.write("\n%10.7f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.9f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f" %(timestamps[it],NP[fs]['FmindB'][it],convertRItoMA(NP[fs]['gopt'][it]).real,convertRItoMA(NP[fs]['gopt'][it]).imag,NP[fs]['Rn'][it],lintodB(NP[fs]['gassoc'][it]),Vgs[it],Id[it],lintodB(NP[fs]['MAG'][it]),convertRItoMA(NP[fs]['gammainopt'][it]).real,convertRItoMA(NP[fs]['gammainopt'][it]).imag,convertRItoMA(NP[fs]['gammaoutopt'][it]).real,convertRItoMA(NP[fs]['gammaoutopt'][it]).imag))    # write out frequency in MHz
			else:
				#f.write("# time (S)\tFmin (dB)\tgammaopt magnitude\tgammaopt angle deg\tRn (ohms)\tassociated gain dB\tVgs (V)\tId (A)\n")
				#for  it in range(0,len(timestamps)):
				f.write("\n%10.7f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.9f" %(timestamps[it],NP[fs]['FmindB'][it],convertRItoMA(NP[fs]['gopt'][it]).real,convertRItoMA(NP[fs]['gopt'][it]).imag,NP[fs]['Rn'][it],lintodB(NP[fs]['gassoc'][it]),Vgs[it],Id[it]))    # write out frequency in MHz
	##########
	f.close()
	return [filename, devicename]
##################################################################################################################
##################################################################################################################
# writes noise figure to a file at a swept gate bias and single drain bias and multiple frequencies
# inputs: (besides those in the parameter list)
# tunerdata are the composite tuner gamma, gain, S-parameters: tunerdata[frequencyMHz][tunerposition][parametertype] where: parametertype is one of:
# gamma_MA is complex gamma_mag.real+jgamma_angle.imag where gamma_angle is in degrees;  gamma_RI is complex gamma.real+jgamma.imag; gain is linear, not dB and always < 1. since
# the tuner is a passive device, Spar is a 2x2 matrix of S-parameters in real+jimaginary format
# Id is the drain current in A interpolated in timestampindex Id[timestampindex]
# Vgs[timestampindex] is the gate voltage vs time
# NFcalcfromNP is the DUT noise figure in dB calculated from the DUT noise parameters, noise figures of the DUT calculated from DUT noise parameters at each tuner position (tuner reflection coefficient). NFcalcfromNPtimedomain[frequencyMHz][tuner position][timestampindex].
# NF is the measured DUT noise figure, linear NOT dB, [frequencyMHz][tuner_position][timestampindex]
#
def writefile_noisefigure_Vgssweep(pathname=None,devicename="",wafername="",xloc=0,yloc=0,Vds=0.,Vgs=None,Id=None,timestamps=None,NFmeas=None,NFcalcfromNP=None,gammatuner=None,videobandwidth=None, resolutionbandwidth=None,devicenamemodifier=""):
	if pathname == None: raise ValueError("ERROR Must include pathname")
	if devicename == None: raise ValueError("ERROR Must give device name for this measurement")
	if Id==None: raise ValueError("ERROR! no drain current given")
	if Vgs==None: raise ValueError("ERROR! no gate voltage given")
	pathname_RF=pathname+sub("SPAR")
	if NFmeas==None: raise ValueError("ERROR! no  measured DUT noisefigures given")
	if NFcalcfromNP==None: raise ValueError("ERROR! no  calculated DUT noisefigures given")
	if timestamps==None: raise ValueError("ERROR! no timestamps given")
	if not os.path.exists(pathname_RF):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_RF)
	filename = "".join([pathname_RF,"/",wafername,devicenamemodifier,"__", devicename, "_noisefigure.xls"])
	f = open(filename, 'w')
	# device parameters file header
	if devicenamemodifier=="": f.write('! device name\t' + "".join([wafername,devicenamemodifier,"__", devicename])+ '\n')
	else: f.write('! device name\t' + "".join([wafername,devicenamemodifier,"_", devicename])+ '\n')
	############
	f.write('# wafer name\t' + wafername + '\n')
	f.write('# x location um\t%d\n' % int(xloc))
	f.write('# y location um\t%d\n' % int(yloc))
	f.write('# Vds (V)\t%10.2f\n' % Vds)
	#f.write('# gate status\t%s\n' % gatestatus)
	f.write('# video bandwidth Hz\t%d\n' % videobandwidth)
	f.write('# resolution bandwidth Hz\t%d\n' % resolutionbandwidth)
	# timestamp
	f.write('# year\t' + str(dt.datetime.now().year) + '\n')
	f.write('# month\t' + str(dt.datetime.now().month) + '\n')
	f.write('# day\t' + str(dt.datetime.now().day) + '\n')
	f.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	f.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	f.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# datatype header
	f.write("#\n#\n# system Z=50ohms\n")
	# write data to file
	# sort frequencies in ascending value. Needed to use map() to sort frequencies since they are of type str
	frequencies=sorted([int(f) for f in NFcalcfromNP.keys()])
	for freq in frequencies:
		fs=str(freq)           # format frequencies to string to access dictionary keys
		f.write("\n#\n# frequency MHz\t%d\n" %(freq))
		for pos in NFmeas[fs].keys():
			f.write("\n#\n# frequency MHz\t%d\n" %(freq))
			f.write("\n# tuner position\ttuner gamma magnitude\ttuner gamma angle deg")
			f.write("\n# %s\t%10.2f\t%10.2f" %(pos,gammatuner[fs][pos].real,gammatuner[fs][pos].imag))
			f.write("\n# time (S)\tmeasured DUT noise figure (dB)\tDUT noise figure calculated from noise parameters (dB)\tVgs (V)\tId (A)")
			for it in range(0,len(timestamps)):
				f.write("\n%10.7f\t%10.2f\t%10.2f\t%10.2f\t%10.9f" %(timestamps[it], lintodB(NFmeas[fs][pos][it]), lintodB(NFcalcfromNP[fs][pos][it]), Vgs[it], Id[it]))
	f.close()
	return [filename, devicename]
##################################################################################################################
# writes DUT deembedded noise figure (dB) to a file at a single bias point and multiple frequencies as a function of tuner position and source reflection coefficient presented to the DUT
# inputs: (besides those in the parameter list)
# self.NF[frequency][para] where frequency is the dict key in MHz and para is the dictionary key = 'gopt' for the optimum noise source reflection coefficient
# real+jimaginary, 'FmindB' for the minimum noise figure in dB, 'Rn' for the noise resistance in ohms
def X_writefile_noisefigure_v2(self,pathname=None,devicename=None,wafername="",xloc=0,yloc=0,Vds=0.,Vgs=0.,Id=0.,Ig=0.,gatestatus="",drainstatus="",devicenamemodifier=""):
	pathname_RF=pathname+sub("SPAR")
	#if devicenamemodifier!="": devicename = "".join([devicenamemodifier, "_", devicename])                 # modify device name to indicate, for example different bias or other test conditions of the same device
	try:
		self.NF  # do noise data exist?
	except:
		print("ERROR! NO frequency array so found! NO noise data written")
		return
	if not os.path.exists(pathname_RF):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_RF)
	filename = "".join([pathname_RF,"/",wafername,devicenamemodifier,"__", devicename, "_noisefigure.xls"])
	#filename = pathname_RF + "/" + devicename + "_noisefigure.xls"
	fn = open(filename, 'w')
	# device parameters file header
	#fn.write('# device name\t' + devicename + '\n')
	if devicenamemodifier=="": fn.write('! device name\t' + "".join([wafername,devicenamemodifier,"__", devicename])+ '\n')
	else: fn.write('! device name\t' + "".join([wafername,devicenamemodifier,"_", devicename])+ '\n')
	fn.write('# wafer name\t' + wafername + '\n')
	fn.write('# x location um\t%d\n' % int(xloc))
	fn.write('# y location um\t%d\n' % int(yloc))
	fn.write('# Vds (V)\t%10.2f\n' % Vds)
	fn.write('# Id (A)\t%10.2E\n' % Id)
	fn.write('# drain status\t%s\n' % drainstatus)
	fn.write('# Vgs (V)\t%10.2f\n' % Vgs)
	fn.write('# Ig (A)\t%10.2E\n' % Ig)
	fn.write('# gate status\t%s\n' % gatestatus)
	# timestamp
	fn.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fn.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fn.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fn.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fn.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fn.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# datatype header
	fn.write("#\n#\n# system Z=50ohms\n")
	# write data to file
	frequencies=list(map(str,sorted([int(f) for f in list(self.NF.keys())])))                       # sort frequencies in ascending value. Needed to use map() to sort frequencies since they are of type str
	for f in frequencies:
		fn.write('# frequency\t%10.2fGHZ\n'%(1E-3*int(f)))
		if self.GaDUT!=None and len(self.GaDUT[str(f)])>0:
			fn.write('! tuner position\treflection coefficient mag angle\tnoisefigure dB\tnoisefigure linear\tnoisefigure dB calculated from noise parameters\tDUT available gain\tDUT available gain dB\ttuner available gain\ttuner available gain dB\tComposite Noise figure (dB) DUT+noisemeter\tnoise cold diode dBm\tnoise hot diode dBm\n')
		else:
			fn.write('! tuner position\treflection coefficient mag angle\tnoisefigure dB\tnoisefigure linear\tnoisefigure dB calculated from noise parameters\ttuner available gain\ttuner available gain dB\n')
		for pos in self.NF[f].keys():               # tuner motor positions used to produce the noise figure
			#reflectioncoef=convertRItoMA(self.get_tuner_reflection(position=pos,frequency=int(f)))
			#reflectioncoef=self.get_tuner_reflection_gain(frequency=int(f),position=pos)["gamma_MA"]
			reflectioncoef=self.tunerdata[f][pos]['gamma_MA']
			GatunerdB=lintodB(self.tunerdata[f][pos]['gain'])
			Gatuner=self.tunerdata[f][pos]['gain']
			noisefiguredB=lintodB(self.NF[f][pos])            # convert noisefigure to dB
			#GatunerdB=lintodB(self.Gatuner[f][pos])             # convert tuner available gain to dB
			#GatunerdB=10.*np.log10(self.get_tuner_reflection_gain(frequency=int(f),position=pos)["gain"])             # convert tuner available gain to dB
			if self.GaDUT!=None and len(self.GaDUT[str(f)])>0:
				GaDUTdB=10.*np.log10(self.GaDUT[f][pos])            # convert DUT available gain to dB if DUT was tested
				fn.write('%s\t%10.2f %10.1f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\n'%(str(pos),reflectioncoef.real,reflectioncoef.imag,noisefiguredB,self.NF[f][pos],self.NFcalcfromNP[f][pos],self.GaDUT[f][pos],GaDUTdB,Gatuner,GatunerdB,self.NFraw[f][pos],self.noisecold[f][pos],self.noisehot[f][pos]))
			else:
				fn.write('%s\t%10.2f %10.1f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\n'%(str(pos),reflectioncoef.real,reflectioncoef.imag,noisefiguredB,self.NF[f][pos],self.NFcalcfromNP[f][pos],Gatuner,GatunerdB))
	fn.close()
	return [filename, devicename]
####################################################################################################################################################################
# write the power gain for a DUT measured as a function of the reflection coefficient presented to the DUT by the load tuner
def X_writefile_Pgain(self, pathname=None, wafername=None, xloc=None, yloc=None, Vds=None, Id=None, drainstatus=None,Vgs=None, Ig=None, gatestatus=None, devicename=None, diecolumn=None, dierow=None, subsitename=None,devicenamemodifier=""):
	if pathname == None: raise ValueError("ERROR Must include pathname")
	if devicename == None: raise ValueError("ERROR Must give device name for this measurement")
	# Form devicename and devicename from function input parameters
	pathname_Pgain = pathname + sub("RF_power")
	if devicenamemodifier!="": devicename = "".join([devicenamemodifier, "_", devicename])
	if diecolumn != None and dierow != None and subsitename != None:
		devicename = formdevicename(wafername, diecolumn, dierow, subsitename)
	else:
		devicename = formdevicename(wafername, devicename)
	if not os.path.exists(pathname_Pgain):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_Pgain)
	if hasattr(self, 'DUTgain') and len(self.DUTgain)>0:  # do we have gain data?
		filename = pathname_Pgain + "/" + devicename + "_Pgain.xls"
		fPg = open(filename, 'w')
		# parameters
		if devicename!=None: fPg.write('! device name\t'+devicename+'\n')
		if wafername!=None: fPg.write('! wafer name\t'+wafername+'\n')
		if xloc!=None: fPg.write('! x location um\t%d\n' % int(xloc))
		if yloc!=None: fPg.write('! y location um\t%d\n' % int(yloc))
		if Vds!=None: fPg.write('! Vds (V)\t%10.2f\n' % Vds)
		if Id !=None: fPg.write('! Id (A)\t%10.2E\n' % Id)
		if drainstatus!=None: fPg.write('! drain status\t%s\n' % drainstatus)
		if Vgs!=None: fPg.write('! Vgs (V)\t%10.2f\n' % Vgs)
		if Ig!=None: fPg.write('! Ig (A)\t%10.2E\n' % Ig)
		if gatestatus!=None: fPg.write('! gate status\t%s\n' % gatestatus)
		# timestamp
		fPg.write('! year\t' + str(dt.datetime.now().year) + '\n')
		fPg.write('! month\t' + str(dt.datetime.now().month) + '\n')
		fPg.write('! day\t' + str(dt.datetime.now().day) + '\n')
		fPg.write('! hour\t' + str(dt.datetime.now().hour) + '\n')
		fPg.write('! minute\t' + str(dt.datetime.now().minute) + '\n')
		fPg.write('! second\t' + str(dt.datetime.now().second) + '\n')
		fPg.write('!\n')
		fPg.write('! Frequency in MHz\t%d\n' % (int(1E-6*self.frequency)))
		fPg.write('! DUT power input dBm\t%10.2f\n' % (self.RFinputpower))
		# data vs tuner position and reflection coefficient and DUT input power
		fPg.write("! Measured quantities\n")
		# sort gains by magnitude
		sortedtunerpositions=sorted(self.rfoutputlevel,key=self.rfoutputlevel.get)
		if len(self.calcDUTgain)>0:
			fPg.write("! tuner motor position\treflection coefficient at DUT output mag angle\tDUT power output dBm\tDUT power gain dB\ttuner gain in 50ohm system dB (check)\ttuner max available gain dB\tcalc DUT gain (dB) from cascaded\tcalc DUT gain (dB)\n")
			for pos in sortedtunerpositions:              # print out data according to tuner position and reflection coefficient
				fPg.write("%s\t%10.2f %10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\n" %(str(pos), self.actualrcoefMA[pos].real, self.actualrcoefMA[pos].imag, self.rfoutputlevel[pos], self.DUTgain[pos],self.tunergain50ohms[pos],-self.tuner_loss[pos],self.calcDUTgain_from_cascade[pos],self.calcDUTgain[pos]))
		else:
			fPg.write("! tuner motor position\treflection coefficient at DUT output mag angle\tDUT power output dBm\tDUT power gain dB\ttuner gain in 50ohm system dB (check)\ttuner max available gain dB\n")
			for pos in sortedtunerpositions:              # print out data according to tuner position and reflection coefficient
				fPg.write("%s\t%10.2f %10.2f\t%10.2f\t%10.2f\t%10.2f\t%10.2f\n" %(str(pos), self.actualrcoefMA[pos].real, self.actualrcoefMA[pos].imag, self.rfoutputlevel[pos], self.DUTgain[pos],self.tunergain50ohms[pos],-self.tuner_loss[pos]))
			fPg.close()
	return
####################################################################################################################################################################
# Bad devices list
# listing of devices which failed
# this is for
def X_writefile_baddeviceslist(self, backside=True, pathname=None, wafername=None, devicenames=None, devicenamemodifier="",xloc_probe=None, yloc_probe=None,xloc0=0,xloc1=0,yloc0=0,yloc1=0):
	if pathname == None:    raise ValueError("ERROR! No pathname provided")
	if wafername == None:    raise ValueError("ERROR! No wafername provided")
	if devicenames == None:    raise ValueError("ERROR! No device name provided")

	pathname_IV = "".join([pathname, sub("DC")])

	# files
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)

	if type(devicenames) is str:        # devicenames would be a list if there is more than one device
		numberofdevices=1
		dv=devicenames
	else:
		numberofdevices=len(devicenames)    # devicenames could be a list of size 1 if there is only one device
		if numberofdevices==1: dv=devicenames[0]

	if numberofdevices==2:
		if devicenamemodifier!="": devicename0 = "".join([devicenamemodifier, "_", devicenames[0]])
		else: devicename0=devicenames[0]
		if devicenamemodifier!="": devicename1 = "".join([devicenamemodifier, "_", devicenames[1]])
		else: devicename1=devicenames[1]
		if not hasattr(self, 'Id0_bias') or not hasattr(self, 'Id1_bias'): raise ValueError("ERROR! missing forward transfer curve data")
	else:
		if devicenamemodifier!="": devicename0 = "".join([devicenamemodifier, "_", dv])
		else: devicename0=dv

	filename = pathname_IV + "/" + formdevicename(wafername,"") + "_baddeviceslist.xls"

	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	if not os.path.isfile(filename):
		fout = open(filename, 'w')
		fout.write('# year\tmonth\tday\thour\tminute\tsecond\tdevice name\tx location um\ty location um\tVds\tVgs\tId(A)\tIg(A)\tdrainstatus\tgatestatus\n')
	else:
		fout=open(filename, 'a')

	# parameters device 0
	fout.write(str(dt.datetime.now().year) + '\t')
	fout.write( str(dt.datetime.now().month) + '\t')
	fout.write(str(dt.datetime.now().day) + '\t')
	fout.write(str(dt.datetime.now().hour) + '\t')
	fout.write(str(dt.datetime.now().minute) + '\t')
	fout.write(str(dt.datetime.now().second) + '\t')
	fout.write(formdevicename(wafername, devicename0))
	if numberofdevices==2:
		# parameters device 0
		if xloc_probe!=None and yloc_probe!=None:
			fout.write('\t%d' % (int(xloc_probe)))
			fout.write('\t%d' % (int(yloc_probe)))
		# else:       # xloc0,yloc0 is the device 0 location xloc1,yloc1 is the device 1 location
		# 	fout.write('\t%d' % (int(xloc1)))
		# 	fout.write('\t%d' % (int(yloc1)))
		fout.write('\t%10.2f' % (self.Vds0_set))
		if not backside: fout.write('\t%10.2f' % (self.Vgs0_set))
		else: fout.write('\t%10.2f' % (self.Vgs_set))
		fout.write('\t%10.2E' % (self.Id0_bias))
		if not backside: fout.write('\t%10.2E' % (self.Ig0_bias))
		else: fout.write('\t%10.2E' % (self.Ig_bias))
		fout.write('\t'+(self.drainstatus0_bias))
		if not backside: fout.write('\t'+(self.gatestatus0_bias)+'\n')
		else: fout.write('\t'+(self.gatestatus_bias)+'\n')
	# parameters device 1
		fout.write(str(dt.datetime.now().year) + '\t')
		fout.write( str(dt.datetime.now().month) + '\t')
		fout.write(str(dt.datetime.now().day) + '\t')
		fout.write(str(dt.datetime.now().hour) + '\t')
		fout.write(str(dt.datetime.now().minute) + '\t')
		fout.write(str(dt.datetime.now().second) + '\t')
		fout.write(formdevicename(wafername, devicename1))

		if xloc1!=None and yloc1!=None:
			fout.write('\t%d' % (int(xloc1)))
			fout.write('\t%d' % (int(yloc1)))
		# else:       # xloc0,yloc0 is the device 0 location xloc1,yloc1 is the device 1 location
		# 	fout.write('\t%d' % (int(xloc1)))
		# 	fout.write('\t%d' % (int(yloc1)))
		fout.write('\t%10.2f' % (self.Vds1_set))
		if not backside: fout.write('\t%10.2f' % (self.Vgs1_set))
		else: fout.write('\t%10.2f' % (self.Vgs_set))
		fout.write('\t%10.2E' % (self.Id1_bias))
		if not backside: fout.write('\t%10.2E' % (self.Ig1_bias))
		else: fout.write('\t%10.2E' % (self.Ig_bias))
		fout.write('\t'+(self.drainstatus1_bias))
		if not backside: fout.write('\t'+(self.gatestatus1_bias)+'\n')
		else: fout.write('\t'+(self.gatestatus_bias)+'\n')
	else:       # just one device probed
		if xloc_probe!=None and yloc_probe!=None:
			fout.write('\t%d' % (int(xloc_probe)))
			fout.write('\t%d' % (int(yloc_probe)))
		fout.write('\t%10.2f' % (self.Vds_bias))
		fout.write('\t%10.2f' % (self.Vgs_bias))
		fout.write('\t%10.2E' % (self.Id_bias))
		fout.write('\t%10.2E' % (self.Ig_bias))
		fout.write('\t'+(self.drainstatus_bias))
		fout.write('\t'+(self.gatestatus_bias)+'\n')
	fout.close()
######################################################################################################################################################
# write current IV family of curves Vds loop (bidirectional Vds sweep) curve results to a file
#
# Inputs:
# pathname
# now handles the case of application of a constant backgating voltage while sweeping the gate
def X_writefile_ivfoc_Vdsloop(self,pathname=None,devicename=None,wafername=None,xloc=0,yloc=0,devicenamemodifier=""):
	pathname_IV ="".join([pathname, sub("DC")])
	if hasattr(self, 'Ibg_tf') and hasattr(self, 'Ibg_tr'):   # then this is a transfer loop with a constant backgate voltage applied
		backgated=True
	else: backgated=False
	if devicenamemodifier!="": devicenamemodifier= "".join(["_",devicenamemodifier])
	if not hasattr(self,'Id_loopfoc1'):   # do the forward Vds sweep foc curve exist?
		print("WARNING! NO loop Vds swept foc exist! NO loop foc curves written!")
		return
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	filename="".join([pathname_IV,"/",wafername,devicenamemodifier,"__",devicename,"_loopfoc.xls"])
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	focloop = open(filename, 'w')
	# parameters
	focloop.write('# device name\t' + wafername+devicenamemodifier+"__"+devicename+'\n')
	focloop.write('# wafer name\t' + wafername + '\n')

	if backgated: focloop.write('# backgate voltage (V)\t'+formatnum(self.Vbackgate,precision=2)+'\n')

	focloop.write('# x location um\t%d\n' % (int(xloc)))
	focloop.write('# y location um\t%d\n' % (int(yloc)))
	focloop.write('# Elapsed Time of measurment per Vds sweep (sec)\t%10.2f\n' % (self.elapsed_time))
	focloop.write('# Vds rate of change (V/sec)\t%10.2f\n' % (self.Vdsslew))
	if hasattr(self,'startstopzero') and self.startstopzero:       # did the Vgs start and stop at Vgs=0V?
		focloop.write('# start and stop at Vds=0V\n')
	focloop.write('# minimum quiescent time at Vgs=0V and Vds=0V\t%10.2f\tsec\n' %(self.quiescenttime))
	# timestamp
	focloop.write('# quiescent time prior to measurements (sec)\t%10.2f\n' % (self.quiescenttime))
	focloop.write('# year\t' + str(dt.datetime.now().year) + '\n')
	focloop.write('# month\t' + str(dt.datetime.now().month) + '\n')
	focloop.write('# day\t' + str(dt.datetime.now().day) + '\n')
	focloop.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	focloop.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	focloop.write('# second\t' + str(dt.datetime.now().second) + '\n')
	############## write data #####################################################
	focloop.write('# Vgs\tVds\tId\tIg\tdrainstatus\tgatestatus\ttimestamp sec\n')
	for iVgs in range(0, len(self.Id_loopfoc1)):
		focloop.write('# Vgs =\t %10.2f\tVds sweep 1\n' % self.Vgs_loopfoc1[iVgs][0])
		for iVds in range(0, len(self.Id_loopfoc1[iVgs])):
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (self.Vgs_loopfoc1[iVgs][iVds], self.Vds_loopfoc1[iVgs][iVds], self.Id_loopfoc1[iVgs][iVds], self.Ig_loopfoc1[iVgs][iVds],
				self.drainstatus_loopfoc1[iVgs][iVds], self.gatestatus_loopfoc1[iVgs][iVds], self.timestamp_loopfoc1[iVgs][iVds]))
		focloop.write('# Vgs =\t %10.2f\tVds sweep 2\n' % self.Vgs_loopfoc2[iVgs][0])
		for iVds in range(0, len(self.Id_loopfoc2[iVgs])):
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (self.Vgs_loopfoc2[iVgs][iVds], self.Vds_loopfoc2[iVgs][iVds], self.Id_loopfoc2[iVgs][iVds], self.Ig_loopfoc2[iVgs][iVds],
				self.drainstatus_loopfoc2[iVgs][iVds], self.gatestatus_loopfoc2[iVgs][iVds], self.timestamp_loopfoc2[iVgs][iVds]))
	focloop.close()
	return [filename, devicename]
###################################################################################################################################################################
######################################################################################################################################################
# write current IV family of curves Vds loop (bidirectional Vds sweep) curve results to a file
# for dual devices
# Inputs:
# pathname
# now handles the case of application of a constant backgating voltage while sweeping the gate

def X_writefile_ivfoc_Vdsloop_dual(self,pathname=None,devicenames=None,wafername=None,xloc0=0,yloc0=0,xloc1=0,yloc1=0,devicenamemodifier=""):
	if pathname == None:    raise ValueError("ERROR! No pathname provided")
	if wafername == None:    raise ValueError("ERROR! No wafername provided")
	if devicenames == None:    raise ValueError("ERROR! No device name provided")
	pathname_IV ="".join([pathname, sub("DC")])
	# write the family of curves data for device0 (left device).
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	devicename0=devicenames[0]
	devicename1=devicenames[1]
	if devicenamemodifier!="": devicenamemodifier="".join(["_",devicenamemodifier])

	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename0, "_loopfoc.xls"])
	if not hasattr(self,'Id0_loopfoc1'):   # do the forward Vds sweep foc curve exist?
		print("WARNING! NO loop Vds swept foc exist for device0! NO loop device0 foc curves written!")
		return

	# write transfer curve to file for device0 (left side device)  i.e. Id vs Vgs the current set of most recently measured or read data
	focloop = open(filename, 'w')
	# parameters
	focloop.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename0, "_loopfoc.xls"]) + '\n')
	focloop.write('# wafer name\t' + wafername + '\n')

	focloop.write('# x location um\t%d\n' % (int(xloc0)))
	focloop.write('# y location um\t%d\n' % (int(yloc0)))
	focloop.write('# Elapsed Time of measurment per Vds sweep (sec)\t%10.2f\n' % (self.elapsed_time))
	focloop.write('# Vds rate of change (V/sec)\t%10.2f\n' % (self.Vdsslew))
	if hasattr(self,'startstopzero') and self.startstopzero:       # did the Vgs start and stop at Vgs=0V?
		focloop.write('# start and stop at Vds=0V\n')
	focloop.write('# minimum quiescent time at Vgs=0V and Vds=0V\t%10.2f\tsec\n' %(self.quiescenttime))
	# timestamp
	focloop.write('# quiescent time prior to measurements (sec)\t%10.2f\n' % (self.quiescenttime))
	focloop.write('# year\t' + str(dt.datetime.now().year) + '\n')
	focloop.write('# month\t' + str(dt.datetime.now().month) + '\n')
	focloop.write('# day\t' + str(dt.datetime.now().day) + '\n')
	focloop.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	focloop.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	focloop.write('# second\t' + str(dt.datetime.now().second) + '\n')

	############## write data from device 0 (left device) #####################################################
	focloop.write('# Vgs\tVds\tId\tIg\tdrainstatus\tgatestatus\ttimestamp sec\n')
	for iVgs in range(0, len(self.Id0_loopfoc1)):
		focloop.write('# Vgs =\t %10.2f\tVds sweep 1\n' % self.Vgs_loopfoc1[iVgs][0])
		for iVds in range(0, len(self.Id0_loopfoc1[iVgs])):
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (self.Vgs_loopfoc1[iVgs][iVds], self.Vds0_loopfoc1[iVgs][iVds], self.Id0_loopfoc1[iVgs][iVds], self.Ig_loopfoc1[iVgs][iVds],
				self.drainstatus0_loopfoc1[iVgs][iVds], self.gatestatus_loopfoc1[iVgs][iVds], self.timestamp_loopfoc1[iVgs][iVds]))
		focloop.write('# Vgs =\t %10.2f\tVds sweep 2\n' % self.Vgs_loopfoc2[iVgs][0])
		for iVds in range(0, len(self.Id0_loopfoc2[iVgs])):
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (self.Vgs_loopfoc2[iVgs][iVds], self.Vds0_loopfoc2[iVgs][iVds], self.Id0_loopfoc2[iVgs][iVds], self.Ig_loopfoc2[iVgs][iVds],
				self.drainstatus0_loopfoc2[iVgs][iVds], self.gatestatus_loopfoc2[iVgs][iVds], self.timestamp_loopfoc2[iVgs][iVds]))
	focloop.close()


	# write transfer curve to file for device1 (right side device)  i.e. Id vs Vgs the current set of most recently measured or read data
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename1, "_loopfoc.xls"])
	if not hasattr(self,'Id1_loopfoc1'):   # do the forward Vds sweep foc curve exist?
		print("WARNING! NO loop Vds swept foc exist for device1! NO loop device1 foc curves written!")
		return
	focloop = open(filename, 'w')
	# parameters
	focloop.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename1, "_loopfoc.xls"]) + '\n')
	focloop.write('# wafer name\t' + wafername + '\n')

	focloop.write('# x location um\t%d\n' % (int(xloc1)))
	focloop.write('# y location um\t%d\n' % (int(yloc1)))
	focloop.write('# Elapsed Time of measurment per Vds sweep (sec)\t%10.2f\n' % (self.elapsed_time))
	focloop.write('# Vds rate of change (V/sec)\t%10.2f\n' % (self.Vdsslew))
	if hasattr(self,'startstopzero') and self.startstopzero:       # did the Vgs start and stop at Vgs=0V?
		focloop.write('# start and stop at Vds=0V\n')
	focloop.write('# minimum quiescent time at Vgs=0V and Vds=0V\t%10.2f\tsec\n' %(self.quiescenttime))
	# timestamp
	focloop.write('# quiescent time prior to measurements (sec)\t%10.2f\n' % (self.quiescenttime))
	focloop.write('# year\t' + str(dt.datetime.now().year) + '\n')
	focloop.write('# month\t' + str(dt.datetime.now().month) + '\n')
	focloop.write('# day\t' + str(dt.datetime.now().day) + '\n')
	focloop.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	focloop.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	focloop.write('# second\t' + str(dt.datetime.now().second) + '\n')

	############## write data from device 1 (right device) #####################################################
	focloop.write('# Vgs\tVds\tId\tIg\tdrainstatus\tgatestatus\ttimestamp sec\n')
	for iVgs in range(0, len(self.Id1_loopfoc1)):
		focloop.write('# Vgs =\t %10.2f\tVds sweep 1\n' % self.Vgs_loopfoc1[iVgs][0])
		for iVds in range(0, len(self.Id1_loopfoc1[iVgs])):
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (self.Vgs_loopfoc1[iVgs][iVds], self.Vds1_loopfoc1[iVgs][iVds], self.Id1_loopfoc1[iVgs][iVds], self.Ig_loopfoc1[iVgs][iVds],
				self.drainstatus0_loopfoc1[iVgs][iVds], self.gatestatus_loopfoc1[iVgs][iVds], self.timestamp_loopfoc1[iVgs][iVds]))
		focloop.write('# Vgs =\t %10.2f\tVds sweep 2\n' % self.Vgs_loopfoc2[iVgs][0])
		for iVds in range(0, len(self.Id1_loopfoc2[iVgs])):
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (self.Vgs_loopfoc2[iVgs][iVds], self.Vds1_loopfoc2[iVgs][iVds], self.Id1_loopfoc2[iVgs][iVds], self.Ig_loopfoc2[iVgs][iVds],
				self.drainstatus1_loopfoc2[iVgs][iVds], self.gatestatus_loopfoc2[iVgs][iVds], self.timestamp_loopfoc2[iVgs][iVds]))
	focloop.close()
	return [filename, devicenames]
###################################################################################################################################################################
######################################################################################################################################################
# write current IV family of curves 2 loops Vds sweep) curve results to a file
# uses output of measure_ivfoc_Vdsloop_4sweep_controlledslew()
# Inputs:
# pathname
def X_writefile_ivfoc_Vds4sweep(self,pathname=None,devicename=None,wafername=None,xloc=0,yloc=0,devicenamemodifier=""):
	pathname_IV ="".join([pathname, sub("DC")])
	if hasattr(self, 'Ibg_tf') and hasattr(self, 'Ibg_tr'):   # then this is a transfer loop with a constant backgate voltage applied
		backgated_constant=True
	else: backgated_constant=False
	if devicenamemodifier!="": devicenamemodifier="".join(["_",devicenamemodifier])
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename, "_loop4foc.xls"])
	if not hasattr(self,"Id_loopfoc3"):  # does the third drain sweep curve exist?
		print("Warning! NO no valid data for Vds 4 sweep loops exists! NO  foc4loop curves written!")
		return

	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	focloop = open(filename, 'w')
	# parameters
	#focloop.write('# device name\t' + formdevicename(wafername, devicename) + '\n')
	focloop.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename, "_loopfoc.xls"]) + '\n')
	focloop.write('# wafer name\t' + wafername + '\n')

	if backgated_constant: focloop.write('# backgate voltage (V)\t'+formatnum(self.Vbackgate,precision=2)+'\n')

	focloop.write('# x location um\t%d\n' % (int(xloc)))
	focloop.write('# y location um\t%d\n' % (int(yloc)))
	#focloop.write('# drain voltage, Vds (V)\t%10.2f\n' % (self.Vds_tf[0]))
	if hasattr(self,"elapsed_time") and hasattr(self,"Vdsslew") and self.elapsed_time!=None and self.Vdsslew!=None:
		focloop.write('# Elapsed Time of measurment per Vds sweep (sec)\t%10.2f\n' % (self.elapsed_time))
		focloop.write('# Vds rate of change (V/sec)\t%10.2f\n' % (self.Vdsslew))
	if hasattr(self,'startstopzero') and self.startstopzero:       # did the Vgs start and stop at Vgs=0V?
		focloop.write('# start and stop at Vds=0V\n')
	focloop.write('# minimum quiescent time at Vgs=0V and Vds=0V\t%10.2f\tsec\n' %(self.quiescenttime))
	# timestamp
	focloop.write('# year\t' + str(dt.datetime.now().year) + '\n')
	focloop.write('# month\t' + str(dt.datetime.now().month) + '\n')
	focloop.write('# day\t' + str(dt.datetime.now().day) + '\n')
	focloop.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	focloop.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	focloop.write('# second\t' + str(dt.datetime.now().second) + '\n')

	############## write data #####################################################
	focloop.write('# Vgs\tVds\tId\tIg\tdrainstatus\tgatestatus\ttimestamp sec\n')
	for iVgs in range(0, len(self.Id_loopfoc1)):
		focloop.write('# Vgs =\t %10.2f\tVds sweep 1\n' % self.Vgs_loopfoc1[iVgs][0])
		for iVds in range(0, len(self.Id_loopfoc1[iVgs])):
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (self.Vgs_loopfoc1[iVgs][iVds], self.Vds_loopfoc1[iVgs][iVds], self.Id_loopfoc1[iVgs][iVds], self.Ig_loopfoc1[iVgs][iVds],
				self.drainstatus_loopfoc1[iVgs][iVds], self.gatestatus_loopfoc1[iVgs][iVds], self.timestamp_loopfoc1[iVgs][iVds]))
		focloop.write('# Vgs =\t %10.2f\tVds sweep 2\n' % self.Vgs_loopfoc2[iVgs][0])
		for iVds in range(0, len(self.Id_loopfoc2[iVgs])):
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (self.Vgs_loopfoc2[iVgs][iVds], self.Vds_loopfoc2[iVgs][iVds], self.Id_loopfoc2[iVgs][iVds], self.Ig_loopfoc2[iVgs][iVds],
				self.drainstatus_loopfoc2[iVgs][iVds], self.gatestatus_loopfoc2[iVgs][iVds], self.timestamp_loopfoc2[iVgs][iVds]))
		focloop.write('# Vgs =\t %10.2f\tVds sweep 3\n' % self.Vgs_loopfoc3[iVgs][0])
		for iVds in range(0, len(self.Id_loopfoc3[iVgs])):
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (self.Vgs_loopfoc3[iVgs][iVds], self.Vds_loopfoc3[iVgs][iVds], self.Id_loopfoc3[iVgs][iVds], self.Ig_loopfoc3[iVgs][iVds],
				self.drainstatus_loopfoc3[iVgs][iVds], self.gatestatus_loopfoc3[iVgs][iVds], self.timestamp_loopfoc3[iVgs][iVds]))
		focloop.write('# Vgs =\t %10.2f\tVds sweep 4\n' % self.Vgs_loopfoc4[iVgs][0])
		for iVds in range(0, len(self.Id_loopfoc4[iVgs])):
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (self.Vgs_loopfoc4[iVgs][iVds], self.Vds_loopfoc4[iVgs][iVds], self.Id_loopfoc4[iVgs][iVds], self.Ig_loopfoc4[iVgs][iVds],
				self.drainstatus_loopfoc4[iVgs][iVds], self.gatestatus_loopfoc4[iVgs][iVds], self.timestamp_loopfoc4[iVgs][iVds]))
	focloop.close()
	return [filename, devicename]
###################################################################################################################################################################
######################################################################################################################################################
# write Id IV family of curves for 2 backgated devices 2 loops Vds sweeps curve results to two files
# uses output of measure_ivfoc_Vdsloop_4sweep_controlledslew_dual_backgated() and ivfoc_Vdsloop_4sweep_controlledslew_dual_topgated()
# pathname
# verified July 3, 2018
def X_writefile_ivfoc_Vds4sweep_dual(self,backgated=True,pathname=None,devicenames=None,wafername=None,xloc0=0,yloc0=0,xloc1=0,yloc1=0,devicenamemodifier=""):
	pathname_IV ="".join([pathname, sub("DC")])
	# write the family of curves data for device0 (left device).
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	devicename0=devicenames[0]
	devicename1=devicenames[1]
	if devicenamemodifier!="": devicenamemodifier="".join(["_",devicenamemodifier])

	# write left device data file##################################################
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename0, "_loop4foc.xls"])
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	focloop = open(filename, 'w')
	# parameters
	focloop.write('# wafer name\t' + wafername + '\n')
	focloop.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename0,"\n"]) )
	focloop.write('# x location um\t%d\n' % (int(xloc0)))
	focloop.write('# y location um\t%d\n' % (int(yloc0)))
	if hasattr(self,"elapsed_time") and hasattr(self,"Vdsslew") and self.elapsed_time!=None and self.Vdsslew!=None:
		focloop.write('# Elapsed Time of measurment per Vds sweep (sec)\t%10.2f\n' % (self.elapsed_time))
		focloop.write('# Vds rate of change (V/sec)\t%10.2f\n' % (self.Vdsslew))
	if hasattr(self,'startstopzero') and self.startstopzero:       # did the Vgs start and stop at Vgs=0V?
		focloop.write('# start and stop at Vds=0V\n')
	#focloop.write('# minimum quiescent time at Vgs=0V and Vds=0V\t%10.2f\tsec\n' %(self.quiescenttime))
	# timestamp
	focloop.write('# year\t' + str(dt.datetime.now().year) + '\n')
	focloop.write('# month\t' + str(dt.datetime.now().month) + '\n')
	focloop.write('# day\t' + str(dt.datetime.now().day) + '\n')
	focloop.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	focloop.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	focloop.write('# second\t' + str(dt.datetime.now().second) + '\n')

	############## write bottom device data #####################################################
	# if backgated (both devices' gates are common
	focloop.write('# Vgs\tVds\tId\tIg\tdrainstatus\tgatestatus\ttimestamp sec\n')
	for iVgs in range(0, len(self.Id0_loopfoc1)):
		if backgated: focloop.write('# Vgs =\t %10.2f\tVds sweep 1\n' % self.Vgs_loopfoc1[iVgs][0])
		else: focloop.write('# Vgs =\t %10.2f\tVds sweep 1\n' % self.Vgs0_loopfoc1[iVgs][0])
		for iVds in range(0, len(self.Id0_loopfoc1[iVgs])):
			if backgated:
				Vgs=self.Vgs_loopfoc1[iVgs][iVds]
				Ig=self.Ig_loopfoc1[iVgs][iVds]
				gatestatus=self.gatestatus_loopfoc1[iVgs][iVds]
			else:
				Vgs=self.Vgs0_loopfoc1[iVgs][iVds]
				Ig=self.Ig0_loopfoc1[iVgs][iVds]
				gatestatus=self.gatestatus0_loopfoc1[iVgs][iVds]
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (Vgs, self.Vds0_loopfoc1[iVgs][iVds], self.Id0_loopfoc1[iVgs][iVds], Ig,
				self.drainstatus0_loopfoc1[iVgs][iVds], gatestatus, self.timestamp_loopfoc1[iVgs][iVds]))
		if backgated: focloop.write('# Vgs =\t %10.2f\tVds sweep 2\n' % self.Vgs_loopfoc2[iVgs][0])
		else: focloop.write('# Vgs =\t %10.2f\tVds sweep 2\n' % self.Vgs0_loopfoc2[iVgs][0])
		for iVds in range(0, len(self.Id0_loopfoc2[iVgs])):
			if backgated:
				Vgs=self.Vgs_loopfoc2[iVgs][iVds]
				Ig=self.Ig_loopfoc2[iVgs][iVds]
				gatestatus=self.gatestatus_loopfoc2[iVgs][iVds]
			else:
				Vgs=self.Vgs0_loopfoc2[iVgs][iVds]
				Ig=self.Ig0_loopfoc2[iVgs][iVds]
				gatestatus=self.gatestatus0_loopfoc2[iVgs][iVds]
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (Vgs, self.Vds0_loopfoc2[iVgs][iVds], self.Id0_loopfoc2[iVgs][iVds], Ig,
				self.drainstatus0_loopfoc2[iVgs][iVds], gatestatus, self.timestamp_loopfoc2[iVgs][iVds]))
		if backgated: focloop.write('# Vgs =\t %10.2f\tVds sweep 3\n' % self.Vgs_loopfoc3[iVgs][0])
		else: focloop.write('# Vgs =\t %10.2f\tVds sweep 3\n' % self.Vgs0_loopfoc3[iVgs][0])
		for iVds in range(0, len(self.Id0_loopfoc3[iVgs])):
			if backgated:
				Vgs=self.Vgs_loopfoc3[iVgs][iVds]
				Ig=self.Ig_loopfoc3[iVgs][iVds]
				gatestatus=self.gatestatus_loopfoc3[iVgs][iVds]
			else:
				Vgs=self.Vgs0_loopfoc3[iVgs][iVds]
				Ig=self.Ig0_loopfoc3[iVgs][iVds]
				gatestatus=self.gatestatus0_loopfoc3[iVgs][iVds]
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (Vgs, self.Vds0_loopfoc3[iVgs][iVds], self.Id0_loopfoc3[iVgs][iVds], Ig,
				self.drainstatus0_loopfoc3[iVgs][iVds], gatestatus, self.timestamp_loopfoc3[iVgs][iVds]))
		if backgated: focloop.write('# Vgs =\t %10.2f\tVds sweep 4\n' % self.Vgs_loopfoc4[iVgs][0])
		else: focloop.write('# Vgs =\t %10.2f\tVds sweep 4\n' % self.Vgs0_loopfoc4[iVgs][0])
		for iVds in range(0, len(self.Id0_loopfoc4[iVgs])):
			if backgated:
				Vgs=self.Vgs_loopfoc4[iVgs][iVds]
				Ig=self.Ig_loopfoc4[iVgs][iVds]
				gatestatus=self.gatestatus_loopfoc4[iVgs][iVds]
			else:
				Vgs=self.Vgs0_loopfoc4[iVgs][iVds]
				Ig=self.Ig0_loopfoc4[iVgs][iVds]
				gatestatus=self.gatestatus0_loopfoc4[iVgs][iVds]
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (Vgs, self.Vds0_loopfoc4[iVgs][iVds], self.Id0_loopfoc4[iVgs][iVds], Ig,
				self.drainstatus0_loopfoc4[iVgs][iVds], gatestatus, self.timestamp_loopfoc4[iVgs][iVds]))
	focloop.close()
	# write top device data file##################################################
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename1, "_loop4foc.xls"])
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	focloop = open(filename, 'w')
	# parameters
	focloop.write('# wafer name\t' + wafername + '\n')
	focloop.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename1,"\n"]) )

	focloop.write('# x location um\t%d\n' % (int(xloc1)))
	focloop.write('# y location um\t%d\n' % (int(yloc1)))
	if hasattr(self,"elapsed_time") and hasattr(self,"Vdsslew") and self.elapsed_time!=None and self.Vdsslew!=None:
		focloop.write('# Elapsed Time of measurment per Vds sweep (sec)\t%10.2f\n' % (self.elapsed_time))
		focloop.write('# Vds rate of change (V/sec)\t%10.2f\n' % (self.Vdsslew))
	if hasattr(self,'startstopzero') and self.startstopzero:       # did the Vgs start and stop at Vgs=0V?
		focloop.write('# start and stop at Vds=0V\n')
	#focloop.write('# minimum quiescent time at Vgs=0V and Vds=0V\t%10.2f\tsec\n' %(self.quiescenttime))
	# timestamp
	focloop.write('# year\t' + str(dt.datetime.now().year) + '\n')
	focloop.write('# month\t' + str(dt.datetime.now().month) + '\n')
	focloop.write('# day\t' + str(dt.datetime.now().day) + '\n')
	focloop.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	focloop.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	focloop.write('# second\t' + str(dt.datetime.now().second) + '\n')

	############## write data #####################################################
	focloop.write('# Vgs\tVds\tId\tIg\tdrainstatus\tgatestatus\ttimestamp sec\n')
	for iVgs in range(0, len(self.Id1_loopfoc1)):
		if backgated: focloop.write('# Vgs =\t %10.2f\tVds sweep 1\n' % self.Vgs_loopfoc1[iVgs][0])
		else: focloop.write('# Vgs =\t %10.2f\tVds sweep 1\n' % self.Vgs1_loopfoc1[iVgs][0])
		for iVds in range(0, len(self.Id1_loopfoc1[iVgs])):
			if backgated:
				Vgs=self.Vgs_loopfoc1[iVgs][iVds]
				Ig=self.Ig_loopfoc1[iVgs][iVds]
				gatestatus=self.gatestatus_loopfoc1[iVgs][iVds]
			else:
				Vgs=self.Vgs1_loopfoc1[iVgs][iVds]
				Ig=self.Ig1_loopfoc1[iVgs][iVds]
				gatestatus=self.gatestatus1_loopfoc1[iVgs][iVds]
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (Vgs, self.Vds1_loopfoc1[iVgs][iVds], self.Id1_loopfoc1[iVgs][iVds], Ig,
				self.drainstatus1_loopfoc1[iVgs][iVds], gatestatus, self.timestamp_loopfoc1[iVgs][iVds]))
		if backgated: focloop.write('# Vgs =\t %10.2f\tVds sweep 2\n' % self.Vgs_loopfoc2[iVgs][0])
		else: focloop.write('# Vgs =\t %10.2f\tVds sweep 2\n' % self.Vgs1_loopfoc2[iVgs][0])
		for iVds in range(0, len(self.Id1_loopfoc2[iVgs])):
			if backgated:
				Vgs=self.Vgs_loopfoc2[iVgs][iVds]
				Ig=self.Ig_loopfoc2[iVgs][iVds]
				gatestatus=self.gatestatus_loopfoc2[iVgs][iVds]
			else:
				Vgs=self.Vgs1_loopfoc2[iVgs][iVds]
				Ig=self.Ig1_loopfoc2[iVgs][iVds]
				gatestatus=self.gatestatus1_loopfoc2[iVgs][iVds]
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (Vgs, self.Vds1_loopfoc2[iVgs][iVds], self.Id1_loopfoc2[iVgs][iVds], Ig,
				self.drainstatus1_loopfoc2[iVgs][iVds], gatestatus, self.timestamp_loopfoc2[iVgs][iVds]))
		if backgated: focloop.write('# Vgs =\t %10.2f\tVds sweep 3\n' % self.Vgs_loopfoc3[iVgs][0])
		else: focloop.write('# Vgs =\t %10.2f\tVds sweep 3\n' % self.Vgs1_loopfoc3[iVgs][0])
		for iVds in range(0, len(self.Id1_loopfoc3[iVgs])):
			if backgated:
				Vgs=self.Vgs_loopfoc3[iVgs][iVds]
				Ig=self.Ig_loopfoc3[iVgs][iVds]
				gatestatus=self.gatestatus_loopfoc3[iVgs][iVds]
			else:
				Vgs=self.Vgs1_loopfoc3[iVgs][iVds]
				Ig=self.Ig1_loopfoc3[iVgs][iVds]
				gatestatus=self.gatestatus1_loopfoc3[iVgs][iVds]
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (Vgs, self.Vds1_loopfoc3[iVgs][iVds], self.Id1_loopfoc3[iVgs][iVds], Ig,
				self.drainstatus1_loopfoc3[iVgs][iVds], gatestatus, self.timestamp_loopfoc3[iVgs][iVds]))
		if backgated: focloop.write('# Vgs =\t %10.2f\tVds sweep 4\n' % self.Vgs_loopfoc4[iVgs][0])
		else: focloop.write('# Vgs =\t %10.2f\tVds sweep 4\n' % self.Vgs1_loopfoc4[iVgs][0])
		for iVds in range(0, len(self.Id1_loopfoc4[iVgs])):
			if backgated:
				Vgs=self.Vgs_loopfoc4[iVgs][iVds]
				Ig=self.Ig_loopfoc4[iVgs][iVds]
				gatestatus=self.gatestatus_loopfoc4[iVgs][iVds]
			else:
				Vgs=self.Vgs1_loopfoc4[iVgs][iVds]
				Ig=self.Ig1_loopfoc4[iVgs][iVds]
				gatestatus=self.gatestatus1_loopfoc4[iVgs][iVds]
			focloop.write('%10.2f\t %10.2f\t %10.2E\t %10.2E\t %s\t %s\t %10.4E\n' %
			    (Vgs, self.Vds1_loopfoc4[iVgs][iVds], self.Id1_loopfoc4[iVgs][iVds], Ig,
				self.drainstatus1_loopfoc4[iVgs][iVds], gatestatus, self.timestamp_loopfoc4[iVgs][iVds]))
	focloop.close()
	return [filename, devicenames]
###################################################################################################################################################################
######################################################################################################################################################
# write harmonic distortion data
# Inputs:
# pathname
def X_writefile_harmonicdistortion(self,pathname=None,devicename=None,wafername=None,xloc=0,yloc=0,devicenamemodifier=""):
	pathname_harmdistortion ="".join([pathname, sub("RF_power")])
	if devicenamemodifier!="": devicename= "".join([devicenamemodifier, "_", devicename])
	if not  ((hasattr(self,"pharm2") and len(self.pharm2)>0) or (hasattr(self,"pharm3") and len(self.pharm3)>0)) :  # do the harmonic distortion data exist?
		print("Warning! NO no valid data for harmonic distortion exists! NO harmonic distortion data written!")
		return
	if not os.path.exists(pathname_harmdistortion):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_harmdistortion)
	#filename = pathname_harmdistortion + "/" + formdevicename(wafername, devicename) + "_harmdistortion.xls"
	filename = "".join([pathname_harmdistortion,"/",wafername,devicenamemodifier,"__", devicename, "_harmdistortion.xls"])
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	outf = open(filename, 'w')
	# parameters
	#outf.write('# device name\t' + formdevicename(wafername, devicename) + '\n')
	outf.write('# device name\t' + "".join([wafername,devicenamemodifier,"__", devicename]) + '\n')
	outf.write('# wafer name\t' + wafername + '\n')

	outf.write('# x location um\t%d\n' % (int(xloc)))
	outf.write('# y location um\t%d\n' % (int(yloc)))
	if self.Vds!=None:outf.write('! Vds (V)\t%10.2f\n' % self.Vds)

	# timestamp
	outf.write('# year\t' + str(dt.datetime.now().year) + '\n')
	outf.write('# month\t' + str(dt.datetime.now().month) + '\n')
	outf.write('# day\t' + str(dt.datetime.now().day) + '\n')
	outf.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	outf.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	outf.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# RF measurement parameters
	outf.write('! Fundamental frequency in MHz\t%d\n' % (int(1E-6*self.fundamental_frequency)))
	outf.write('! Fundamental DUT power input dBm\t%10.2f\n' % (self.input_powerlevel_fundamental))
	if hasattr(self,"harmonic_frequency2"): outf.write('! 2nd Harmonic frequency in MHz\t%d\n' % (int(1E-6*self.harmonic_frequency2)))
	if hasattr(self,"harmonic_frequency3"): outf.write('! 2nd Harmonic frequency in MHz\t%d\n' % (int(1E-6*self.harmonic_frequency2)))
	############## write data #####################################################
	if (hasattr(self,"pharm2") and len(self.pharm2)>0) and (hasattr(self,"pharm3") and len(self.pharm3)>0):      # have both 2nd and 3rd harmonic data
		outf.write('# Vgs\tGain (dB)\tPout fundamental (dBm)\tPout 2nd harmonic (dBm)\tPout 3rd harmonic (dBm)\tRatio Pharm2/Pfund (dB)\tRatio Pharm3/Pfund\toutput TOI\tfundamental noise floor dBm\t2nd harmonic noise floor dBm\t3rd harmonic noise floor dBm\tId\tIg\tdrainstatus\tgatestatus\n')
		for iVgs in range(0, len(self.Vgs)):
			outf.write('%10.2f\t%10.1f\t%10.1f\t%10.1f\t%10.1f\t%10.1f\t%10.1f\t%10.1f\t%10.1f\t%10.1f\t%10.1f\t%10.2E\t%10.2E\t%s\t%s\n' %(self.Vgs[iVgs],self.pfund[iVgs]-self.input_powerlevel_fundamental, self.pfund[iVgs], self.pharm2[iVgs], self.pharm3[iVgs], self.pharm2[iVgs]-self.pfund[iVgs], self.pharm3[iVgs]-self.pfund[iVgs], self.pharm3TOI[iVgs],self.noisefloor_fund[iVgs],self.noisefloor_2nd[iVgs],self.noisefloor_3rd[iVgs],self.Id[iVgs], self.Ig[iVgs], self.drainstatus[iVgs],self.gatestatus[iVgs]) )
	elif (hasattr(self,"pharm2") and len(self.pharm2)>0) and not (hasattr(self,"pharm3") and len(self.pharm3)>0):      # have only 2nd harmonic data
		outf.write('# Vgs\tGain (dB)\tPout fundamental (dBm)\tPout 2nd harmonic (dBm)\tRatio Pharm2/Pfund (dB)\tfundamental noise floor dBm\t2nd harmonic noise floor dBm\tId\tIg\tdrainstatus\tgatestatus\n')
		for iVgs in range(0, len(self.Vgs)):
			outf.write('%10.2f\t%10.1f\t%10.1f\t%10.1f\t%10.1f\t%10.1f\t%10.1f\t%10.2E\t%10.2E\t%s\t%s\n' %(self.Vgs[iVgs],self.pfund[iVgs]-self.input_powerlevel_fundamental, self.pfund[iVgs], self.pharm2[iVgs], self.pharm2[iVgs]-self.pfund[iVgs],
			                                                                        self.noisefloor_fund[iVgs],self.noisefloor_2nd[iVgs],self.Id[iVgs], self.Ig[iVgs], self.drainstatus[iVgs],self.gatestatus[iVgs]) )
	elif not (hasattr(self,"pharm2") and len(self.pharm2)>0) and (hasattr(self,"pharm3") and len(self.pharm3)>0):      # have only 3rd harmonic data
		outf.write('# Vgs\tGain (dB)\tPout fundamental (dBm)\tPout 3rd harmonic (dBm)\tRatio Pharm3/Pfund (dB)\toutput TOI\tfundamental noise floor dBm\t3rd harmonic noise floor dBm\tId\tIg\tdrainstatus\tgatestatus\n')
		for iVgs in range(0, len(self.Vgs)):
			outf.write('%10.2f\t%10.1f\t%10.1f\t%10.1f\t%10.1f\t%10.1f\t%10.1f\t%10.1f\t%10.2E\t%10.2E\t%s\t%s\n' %(self.Vgs[iVgs],self.pfund[iVgs]-self.input_powerlevel_fundamental, self.pfund[iVgs], self.pharm3[iVgs], self.pharm3[iVgs]-self.pfund[iVgs],
			                                                                                        self.pharm3TOI[iVgs],self.noisefloor_fund[iVgs],self.noisefloor_2nd[iVgs], self.Id[iVgs], self.Ig[iVgs], self.drainstatus[iVgs],self.gatestatus[iVgs]) )
	outf.close()
	return [filename, devicename]
###################################################################################################################################################################
def X_writefile_probecleanlog(self,pathname=None, wafername=None, devicenames=None, devicenamemodifier="", probe0resistance_beforeclean=None, probe0resistance_afterclean=None ,probe1resistance_beforeclean=None, probe1resistance_afterclean=None,cleaniter=1):
	if pathname == None:    raise ValueError("ERROR! No pathname provided")
	if wafername == None:    raise ValueError("ERROR! No wafername provided")
	if devicenames == None:    raise ValueError("ERROR! No device name provided")

	pathname_IV = "".join([pathname, sub("DC")])

	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	# device names

	if devicenamemodifier!="": devicename0 = "".join([devicenamemodifier, "_", devicenames[0]])
	else: devicename0=devicenames[0]
	if len(devicenames)>1:
		if devicenamemodifier!="": devicename1 = "".join([devicenamemodifier, "_", devicenames[1]])
		else: devicename1=devicenames[1]
	filename = pathname_IV + "/" + formdevicename(wafername, devicename0) + "_cleanlog.xls"
	# write cleaning log to file i.e. Id vs Vgs the current set of most recently measured or read data
	fout=open(filename,'a+')
	# parameters
	#fout.write('# wafer name\t' + wafername + '\n')

	fout.write("\t".join(['# device0 name',formdevicename(wafername,devicename0),'resistance before clean',formatnum(probe0resistance_beforeclean,precision=2),'resistance after clean',formatnum(probe0resistance_afterclean,precision=2)]))
	if len(devicenames)>1:
		fout.write('\t')
		fout.write("\t".join(['# device1 name',formdevicename(wafername,devicename1),'resistance before clean',formatnum(probe1resistance_beforeclean,precision=2),'resistance after clean',formatnum(probe1resistance_afterclean,precision=2)]))
	fout.write('clean iteration '+formatnum(cleaniter,type='int')+'\n')
	fout.close()
###################################################################################################################################################################
def X_writefile_probecleanlog_dual_topgate(self,pathname=None, wafername=None, devicenames=None, devicenamemodifier="",gate0_beforeclean=None,gate0_afterclean=None,gate1_beforeclean=None,gate1_afterclean=None,
                              drain0_beforeclean=None, drain0_afterclean=None ,drain1_beforeclean=None, drain1_afterclean=None,cleaniter=1):
	if pathname == None:    raise ValueError("ERROR! No pathname provided")
	if wafername == None:    raise ValueError("ERROR! No wafername provided")
	if devicenames == None:    raise ValueError("ERROR! No device name provided")

	pathname_IV = "".join([pathname, sub("DC")])

	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	# device names

	if devicenamemodifier!="": devicename0 = "".join([devicenamemodifier, "_", devicenames[0]])
	else: devicename0=devicenames[0]
	if len(devicenames)>1:
		if devicenamemodifier!="": devicename1 = "".join([devicenamemodifier, "_", devicenames[1]])
		else: devicename1=devicenames[1]
	filename = pathname_IV + "/" + formdevicename(wafername, devicename0) + "_cleanlog.xls"
	# write cleaning log to file i.e. Id vs Vgs the current set of most recently measured or read data
	fout=open(filename,'a+')
	# parameters
	#fout.write('# wafer name\t' + wafername + '\n')

	fout.write("\t".join(['# device0 name',formdevicename(wafername,"_"+devicename0),'gate resistance before clean',formatnum(gate0_beforeclean,precision=2),'gate resistance after clean',formatnum(gate0_afterclean),
	        'drain resistance before clean',formatnum(drain0_beforeclean,precision=2),'drain resistance after clean',formatnum(drain0_afterclean,precision=2)]))
	if len(devicenames)>1:
		fout.write('\t')
		fout.write("\t".join(['# device1 name',formdevicename(wafername,"_"+devicename1),'gate resistance before clean',formatnum(gate1_beforeclean,precision=2),'gate resistance after clean',formatnum(gate1_afterclean),
	        'drain resistance before clean',formatnum(drain1_beforeclean,precision=2),'drain resistance after clean',formatnum(drain1_afterclean,precision=2)]))
	fout.write('clean iteration '+formatnum(cleaniter,type='int')+'\n')
	fout.close()
###################################################################################################################################################################
def X_writefile_probecleanlog_topgate(self,pathname=None, wafername=None, devicename=None, devicenamemodifier="",gate_beforeclean=None,gate_afterclean=None,
                              drain_beforeclean=None, drain_afterclean=None, cleaniter=1):
	if pathname == None:    raise ValueError("ERROR! No pathname provided")
	if wafername == None:    raise ValueError("ERROR! No wafername provided")
	if devicename == None:    raise ValueError("ERROR! No device name provided")

	pathname_IV = "".join([pathname, sub("DC")])

	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	# device names

	if devicenamemodifier!="": devicenamemodifier="_"+devicenamemodifier
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename,"_cleanlog.xls"])
	# write cleaning log to file i.e. Id vs Vgs the current set of most recently measured or read data
	fout=open(filename,'a+')
	# parameters
	#fout.write('# wafer name\t' + wafername + '\n')

	fout.write("\t".join(['# device name',wafername,"__",devicename,'gate resistance before clean',formatnum(gate_beforeclean,precision=2),'gate resistance after clean',formatnum(gate_afterclean),
	        'drain resistance before clean',formatnum(drain_beforeclean,precision=2),'drain resistance after clean',formatnum(drain_afterclean,precision=2)]))
	fout.write('clean iteration '+formatnum(cleaniter,type='int')+'\n')
	fout.close()

###################################################################################################################################################################################
######################################################################################################################################################
# write current IV family of curves Vds loop using the signal generator drive to the drain
#
# Inputs:
# pathname
# now handles the case of application of a constant gate voltage while sweeping the gate
def writefile_ivfoc_Vdsswept(pathname=None,devicename=None,wafername=None,xloc=0,yloc=0,devicenamemodifier="",data=None):
	pathname_IV ="".join([pathname, sub("DC")])

	if devicenamemodifier!="": devicenamemodifier= "".join(["_",devicenamemodifier])

	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	filename="".join([pathname_IV,"/",wafername,devicenamemodifier,"__",devicename,"_Vdssweepfoc.xls"])
	# write transfer curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	focloop = open(filename, 'w')
	# parameters
	focloop.write('# device name\t' + wafername+devicenamemodifier+"__"+devicename+'\n')
	focloop.write('# wafer name\t' + wafername + '\n')
	focloop.write('# x location um\t%d\n' % (int(xloc)))
	focloop.write('# y location um\t%d\n' % (int(yloc)))
	focloop.write('# drain sweep period (sec)\t%10.2E\n' % (data['period']))
	focloop.write('# RF frequency GHz\t%10.2f\n' % (data['frequency']))

	# measurement time
	focloop.write('# year\t' + str(dt.datetime.now().year) + '\n')
	focloop.write('# month\t' + str(dt.datetime.now().month) + '\n')
	focloop.write('# day\t' + str(dt.datetime.now().day) + '\n')
	focloop.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	focloop.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	focloop.write('# second\t' + str(dt.datetime.now().second) + '\n')
	# calculate output conductance and capacitance
	############## write data #####################################################
	for iVgs in range(0, len(data['Vgs'])):
		focloop.write('# Vgs =\t %10.2f\n' % data['Vgs'][iVgs])
		focloop.write('# timestamp\tVgs\tVds\tId\tGo\tCo\tS22_real\tS22_imag\tS22_mag\tS22_ang\tZout_real\tZout_imag\tYout_real\tYout_imag\tgatestatus\n')
		for it in range(0, len(data['timestamps'])):
			focloop.write('%10.2E\t %10.2f\t %10.2f\t %10.2E\t %10.2E\t %10.2E\t %10.2E\t %10.2E\t %10.2E\t %10.2E\t %10.2E\t %10.2E\t %10.2E\t %10.2E\t%s\n' % (data['timestamps'][it], data['Vgs'][iVgs], data['Vds'][iVgs][it], data['Id'][iVgs][it], data['Go'][iVgs][it], data['Co'][iVgs][it],data['S22'][iVgs][it].real, data['S22'][iVgs][it].imag, convertRItoMA(data['S22'][iVgs][it]).real, convertRItoMA(data['S22'][iVgs][it]).imag,
			                                                                                                                 data['Zout'][iVgs][it].real, data['Zout'][iVgs][it].imag, data['Yout'][iVgs][it].real, data['Yout'][iVgs][it].imag, data['gatestatus'][iVgs] ))
	focloop.close()
	return [filename, devicename]
###################################################################################################################################################################
####################################################################################################################################################################
# write S-parameters, Id, and swept Vgs or Vds vs frequency and time

def writefile_swept_Spar(pathname=None, wafername='', xloc='', yloc='', devicename=None,devicenamemodifier="",timestamps=None,spar=None,Id=None,Vswept=None,gm_ex=None,go_ex=None,Cgs=None,Cgd=None,Cds=None,gatesweep=True,fileformat="freqtime",Vconstbias=None):
	if spar==None or Id==None or Vswept==None: raise ValueError("ERROR! missing data")
	if pathname == None: raise ValueError("ERROR Must include pathname")
	if devicename == None: raise ValueError("ERROR Must give device name for this measurement")
	if Vconstbias==None: raise ValueError("ERROR Must give the constant bias voltage (Vds or Vgs, whichever is not swept")
	if timestamps==None: raise ValueError("ERROR Must give timestamps array")
	# find lowest and highest RF frequencies measured
	minfreqRF=min([int(k)*1E6 for k in Vswept.keys()])
	maxfreqRF=max([int(k)*1E6 for k in Vswept.keys()])

	# Form devicename and devicename from function input parameters
	pathname_out = pathname + sub("RF")

	if devicenamemodifier!="": devicenamemodifier="".join(["_",devicenamemodifier])
	if gatesweep: filename = "".join([pathname_out,"/",wafername,devicenamemodifier,"__", devicename, "_sweptVgsspar.xls"])     # the gate is swept and drain is DC
	else: filename = "".join([pathname_out,"/",wafername,devicenamemodifier,"__", devicename, "_sweptVdsspar.xls"])             # the drain is swept and gate is DC

	if not os.path.exists(pathname_out):    os.makedirs(pathname_out)  # if necessary, make the directory to contain the data

	fout = open(filename, 'w')
	# parameters
	fout.write('! device name\t' + devicename + '\n')
	fout.write('! wafer name\t' + wafername + '\n')

	fout.write('! x location um\t%d\n' % int(xloc))
	fout.write('! y location um\t%d\n' % int(yloc))
	if gatesweep:
		fout.write('! sweep type\tVgs\n')     # gate voltage is swept and drain is DC biased
		fout.write('! Vds (V)\t%10.2f\n' % (Vconstbias))
	else:           # drain voltage is swept and gate is DC biased
		fout.write('! sweep type\tVds\n')                                 # drain voltage is swept and gate is DC biased
		fout.write('! Vgs (V)\t%10.2f\n' % (Vconstbias))
	# timestamp
	fout.write('! year\t' + str(dt.datetime.now().year) + '\n')
	fout.write('! month\t' + str(dt.datetime.now().month) + '\n')
	fout.write('! day\t' + str(dt.datetime.now().day) + '\n')
	fout.write('! hour\t' + str(dt.datetime.now().hour) + '\n')
	fout.write('! minute\t' + str(dt.datetime.now().minute) + '\n')
	fout.write('! second\t' + str(dt.datetime.now().second) + '\n')
	fout.write('!\n')
	fout.write('! lowest RF frequency in Hz\t%d\n' % (minfreqRF))
	fout.write('! highest RF frequency in Hz\t%d\n' % (maxfreqRF))
	fout.write('\n!\n!\n!')
	###########
	frequencies=[int(f) for f in list(Vswept.keys())]     # frequencies in MHz
	frequencies.sort()
	fout.write('\n!frequency_MHz\ttimestamp (sec)\tVgs\tId(A)\tS11_re\tS11_im\tS21_re\tS21_im\tS12_re\tS12_im\tS22_re\tS22_im\tgm_ex\tgo_ex\tCgs fF\tCgd fF\tCds fF')      # gate voltage is swept and drain is DC biased
	if fileformat=="freqtime":      # then frequency is the slower-changing parameter.
		for freq in frequencies:
			for it in range(0,len(timestamps)):
				fout.write('\n%d\t%10.6E\t%10.6f \t%10.6E\t%10.6E \t%10.6E\t%10.6E \t%10.6E\t%10.6E \t%10.6E \t%10.6E\t%10.6E\t%10.6E\t%10.6E\t%10.6E\t%10.6E\t%10.6E' %(freq,timestamps[it],Vswept[str(freq)][it], Id[str(freq)][it], spar['s11'][str(freq)][it].real, spar['s11'][str(freq)][it].imag, spar['s21'][str(freq)][it].real, spar['s21'][str(freq)][it].imag,
			                                                  spar['s12'][str(freq)][it].real, spar['s12'][str(freq)][it].imag, spar['s22'][str(freq)][it].real, spar['s22'][str(freq)][it].imag, gm_ex[str(freq)][it], go_ex[str(freq)][it], Cgs[str(freq)][it], Cgd[str(freq)][it], Cds[str(freq)][it]))
			fout.write('\n!')
	else:                           # then time is the slower-changing index
		for it in range(0,len(timestamps)):
			for freq in frequencies:
				fout.write('\n%d\t%10.6E\t%10.6f \t%10.6E\t%10.6E \t%10.6E\t%10.6E \t%10.6E\t%10.6E \t%10.6E \t%10.6E\t%10.6E\t%10.6E\t%10.6E\t%10.6E\t%10.6E\t%10.6E' %(freq,timestamps[it],Vswept[str(freq)][it], Id[str(freq)][it], spar['s11'][str(freq)][it].real, spar['s11'][str(freq)][it].imag, spar['s21'][str(freq)][it].real, spar['s21'][str(freq)][it].imag,
			                                                  spar['s12'][str(freq)][it].real, spar['s12'][str(freq)][it].imag, spar['s22'][str(freq)][it].real, spar['s22'][str(freq)][it].imag, gm_ex[str(freq)][it], go_ex[str(freq)][it], Cgs[str(freq)][it], Cgd[str(freq)][it], Cds[str(freq)][it]))
			fout.write('\n!')
	fout.write('\n!\n!\n!')
	fout.close()
######################################################################################################################################################




###################################################################################################################################################################
# write the switching factors to a file using the Touchstone format
#
def X_writefile_swfactors(self,pathname=None,filenamemod=None):
	pathname_RF=pathname+sub("SPAR")
	try:
		self.freq  # do S-parameter data exist?
	except:
		print("ERROR! NO frequency array so S-parameter data found! NO S-parameter data written")
		return
	if not (hasattr(self,"swt_a1overb1") and hasattr(self,"swt_a2overb2")):
		raise ValueError("ERROR from line 3129 in writefile_measured.py: No switching factors to write")

	if not os.path.exists(pathname_RF):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_RF)
	filename_swt1 = "".join([pathname_RF,"/",filenamemod,"swt_a1overb1_SRI.s1p"])
	filename_swt2 = "".join([pathname_RF,"/",filenamemod,"swt_a2overb2_SRI.s1p"])
	fout = open(filename_swt1, 'w')

	# write first switch factor ##############
	fout.write('! year\t' + str(dt.datetime.now().year) + '\n')
	fout.write('! month\t' + str(dt.datetime.now().month) + '\n')
	fout.write('! day\t' + str(dt.datetime.now().day) + '\n')
	fout.write('! hour\t' + str(dt.datetime.now().hour) + '\n')
	fout.write('! minute\t' + str(dt.datetime.now().minute) + '\n')
	fout.write('! second\t' + str(dt.datetime.now().second) + '\n')
	# datatype header
	fout.write("!\n!\n")
	# write data to file
	# real and imaginary
	fout.write("# GHZ S RI R 50\n")
	fout.write("!frequency_GHz\treal\timaginary\n")
	for ifr in range(0, len(self.freq)):
		fout.write("%7.3f" % (1E-9 * self.freq[ifr]))
		fout.write((" %7.3E" % (self.swt_a1overb1[ifr].real)) + (" %7.3E" % (self.swt_a1overb1[ifr].imag))+ "\n")
	fout.close()
	######################
	fout = open(filename_swt2, 'w')
	# write second switch factor ##############
	fout.write('! year\t' + str(dt.datetime.now().year) + '\n')
	fout.write('! month\t' + str(dt.datetime.now().month) + '\n')
	fout.write('! day\t' + str(dt.datetime.now().day) + '\n')
	fout.write('! hour\t' + str(dt.datetime.now().hour) + '\n')
	fout.write('! minute\t' + str(dt.datetime.now().minute) + '\n')
	fout.write('! second\t' + str(dt.datetime.now().second) + '\n')
	# datatype header
	fout.write("!\n!\n")
	# write data to file
	# real and imaginary
	fout.write("# GHZ S RI R 50\n")
	fout.write("!frequency_GHz\treal\timaginary\n")
	for ifr in range(0, len(self.freq)):
		fout.write("%7.3f" % (1E-9 * self.freq[ifr]))
		fout.write((" %7.3E" % (self.swt_a2overb2[ifr].real)) + (" %7.3E" % (self.swt_a2overb2[ifr].imag))+ "\n")
	fout.close()
	return [filename_swt1,filename_swt2]
##################################################################################################################


######################################################################################################################################################
# write leakage current data from output of measure_leakage_controlledslew

def X_writefile_measure_leakage_controlledslew(self,pathname=None,devicename=None,wafername=None,xloc=0,yloc=0,devicenamemodifier=""):
	pathname_IV ="".join([pathname, sub("DC")])
	try:
		self.Ibias  # does the bias sweep current exist?
	except:
		raise ValueError("ERROR! NO bias current data exist!")
	if not os.path.exists(pathname_IV):  # if necessary, make the directory to contain the data
		os.makedirs(pathname_IV)
	filename = "".join([pathname_IV,"/",wafername,devicenamemodifier,"__", devicename, "_biascurrent.xls"])
	# write bias current curve to file i.e. Id vs Vgs the current set of most recently measured or read data
	fout = open(filename, 'w')
	# parameters
	fout.write('# device name\t' +"".join([wafername,devicenamemodifier,"__", devicename]) + '\n')
	fout.write('# wafer name\t' + wafername + '\n')

	fout.write('# x location um\t%d\n' % (int(xloc)))
	fout.write('# y location um\t%d\n' % (int(yloc)))

	if hasattr(self,"elapsed_time"):
		fout.write('# Elapsed Time of measurment (sec)\t%10.2f\n' % (self.elapsed_time))
		fout.write('# Vgs rate of change (V/sec)\t%10.2f\n' % (self.Vbiasslewrate))
	# datetimestamp
	fout.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fout.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fout.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fout.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fout.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fout.write('# second\t' + str(dt.datetime.now().second) + '\n')
	############## write data #####################################################

	fout.write('# timestamp sec\tVbias(V)\tIbias(A)\tstatus\n')
	for ii in range(0, len(self.Ibias)):
		fout.write('%10.2f\t %10.3E\t %10.3E\t%s\n' %  (self.ts[ii], self.Vbias[ii], self.Ibias[ii], self.status[ii]))
	fout.close()



	return [filename, devicename]
###################################################################################################################################################################

###################################################################################################################################################################
# write system noise figure vs frequency This is a debug tool
def X_writefile_systemnoisefigure_vs_time(self,pathname=None,filename=None):
	filename = "".join([pathname,"/",filename, "_sysnoisetime.xls"])
	if not os.path.exists(pathname):  # if necessary, make the directory to contain the data
		os.makedirs(pathname)
	fout = open(filename, 'w')
	# datetimestamp
	fout.write('# filename is\t'+filename+'\n')
	fout.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fout.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fout.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fout.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fout.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fout.write('# second\t' + str(dt.datetime.now().second) + '\n')
	fout.write('# RF Frequency (MHz)\t'+formatnum(1E-6*self.frequency_sa,precision=2,nonexponential=True)+'\n')
	fout.write('# Resolution Bandwidth (Hz)\t'+formatnum(self.actualresolutionbandwidth,precision=2,nonexponential=True)+'\n')
	fout.write('# Video Bandwidth (Hz)\t'+formatnum(self.actualvideobandwidth,precision=2,nonexponential=True)+'\n')
	fout.write('# ENR (dB)\t'+formatnum(self.ENR,precision=2,nonexponential=True)+'\n')
	fout.write('# average system noisefigure (dB)\t'+formatnum(self.NFdBaverageacrosstime,precision=3,nonexponential=True)+'\n')
	fout.write('# average Y factor dB\t'+formatnum(self.YfactdBaverageacrosstime,precision=3,nonexponential=True)+'\n')
	fout.write('# timestamp sec\tsystem noisefigure dB\tYfactor dB\tnoisecold_dBm/Hz\tnoisehot_dBm/Hz\n')
	for ii in range(0, len(self.timestamps)):
		fout.write('%10.6f\t %10.3f\t %10.3f\t %10.3f\t %10.3f\n' %  (self.timestamps[ii], self.NFdB[ii], self.YfactdB[ii],self.noisecold_sa[ii],self.noisehot_sa[ii]))
	fout.close()
###################################################################################################################################################################
# write system noise figure vs frequency This is a debug tool
def X_writefile_systemnoisefigure_vs_frequency(self,pathname=None,filename=None):
	filename = "".join([pathname,"/",filename, "_sysnoisefreq.xls"])
	if not os.path.exists(pathname):  # if necessary, make the directory to contain the data
		os.makedirs(pathname)
	fout = open(filename, 'w')
	# datetimestamp
	fout.write('# filename is\t'+filename+'\n')
	fout.write('# year\t' + str(dt.datetime.now().year) + '\n')
	fout.write('# month\t' + str(dt.datetime.now().month) + '\n')
	fout.write('# day\t' + str(dt.datetime.now().day) + '\n')
	fout.write('# hour\t' + str(dt.datetime.now().hour) + '\n')
	fout.write('# minute\t' + str(dt.datetime.now().minute) + '\n')
	fout.write('# second\t' + str(dt.datetime.now().second) + '\n')
	fout.write('# Resolution Bandwidth (Hz)\t'+formatnum(self.actualresolutionbandwidth,precision=1,nonexponential=True)+'\n')
	fout.write('# frequency MHz\tsystem noisefigure dB\tYfactor dB\tENR dB\tnoisecold_dBm/Hz\tnoisehot_dBm/Hz\n')
	for ii in range(0, len(self.frequenciescold)):
		fout.write('%10.6f\t %10.3f\t %10.3f\t %10.3f\t %10.3f\t %10.3f\n' %  (self.frequenciescold[ii], self.NFdB[ii], self.YfactdB[ii],self.ENR[ii],self.noisecold_sa[ii],self.noisehot_sa[ii]))
	fout.close()