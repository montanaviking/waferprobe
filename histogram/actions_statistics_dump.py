__author__ = 'viking'
# actions for wafer statistics dump for selected parameters e.g. TLM
import platform

from wafer_analysis import *
from waferstatisticsdatadump import *
from select_device_to_plot_popup import *
from utilities import parse_rpn
from all_device_data_to_table import *
from operator import itemgetter, attrgetter
import collections as c
from itertools import chain

class StatisticsDump(Ui_WaferStatisticsDataDump,QtWidgets.QDialog):
	CloseStaticsDump=QtCore.pyqtSignal()
	def __init__(self,parent=None):
		super(StatisticsDump,self).__init__(parent)
		self.setupUi(self)
		if "Windows" in platform.system():
			#self.app_set_dir="C:/Documents and Settings/All Users/Application Data/"			# this will be the directory for the program settings in Windows
			self.app_set_dir="C:/ProgramData/Python"
		elif "Linux" in platform.system():
			self.app_set_dir=os.path.expanduser("~/bin/Python")

		if not hasattr(self.parent(),"lastdirectory") or not os.path.exists(self.parent().lastdirectory):
			if "Windows" in platform.system(): self.parent().lastdirectory="C:\\"
			elif "Linux" in platform.system(): self.lastdirectory=str(os.path.expanduser("~"))
			else: raise ValueError("ERROR! Not a known OS")

		self.wafername=self.parent().wafername.text()
		self.wafer_label.setText("Wafer: "+self.parent().wafername.text())

		# set up widgets
		#self.Device_Listing_Table.VerticalHeaderClicked.connect(self.select_plot_menu)
		self.populate_data_table_but.clicked.connect(self.__save_to_clipboard)
		self.upper_lower_but.clicked.connect(self.__toggleupperlowerfract)
		self.set_fract_data_selected.returnPressed.connect(self.__TLM_table_new_cherrypick)
		self.set_fract_data_selected.blockSignals(True)
		self.set_fract_data_selected.setText('1.')
		self.set_fract_data_selected.blockSignals(False)
		self.parameter_to_filter.currentIndexChanged.connect(self.__TLM_table_new_cherrypick)
		self.parameter_to_filter.blockSignals(True)
		self.parameter_to_filter.clear()

		self.parameter_essential.currentIndexChanged.connect(self.__TLM_table_new_cherrypick)
		self.parameter_essential.blockSignals(True)
		self.parameter_essential.clear()

		self.Device_Listing_Table.resizeRowsToContents()
		self.Device_Listing_Table.resizeColumnsToContents()
		#self.Device_Listing_Table.VerticalHeaderClicked.connect(self.select_plot_menu)
		self.columnscaptured=c.deque([])				# columns to be delivered to clipboard
		self.TLM_table_refresh()
		self.__toggleupperlowerfract()
################################################################################################################
# called to import data from devices and refresh data in TLM table when it changes - not due to changes in user cherrypick on this GUI
# get all device data
# data is a dictionary of the format:
# self.data[d=device name][pparameter (measured or calculated)] and data[d][p]=device data as specifed by the devicename=d and parameter name =
# and devparameters contains all the available device parameters
	def TLM_table_refresh(self):
		candidatestodisplay=['Ron','|Idmax(Vds)|FOC','|Idmax| single','|Idmax| dual 1st','|Idmax| dual 2nd',"ORTHRatio |Idmax| single","On-Off ratio single","On-Off ratio dual 1st","On-Off ratio dual 2nd",'|Idmin| single',
		                     "|Igmax| single","|Ig|@|Idmin| single",'|Idmin| dual 1st',"|Idmin| dual 2nd","hysteresis voltage 12","ft","fmax","Fmin50average","gainFmin50average","Vth","Idatthres+dVgs"]								# candidate parameters to display
		self.data,self.devparameters=all_device_data_to_table(wd=self.parent().wd,selecteddevices=self.parent().wd.validdevices,Vgs=self.parent().Vgs_comboBox.currentText(),fractVdsfit=self.parent().range_linearfit.text(),
		                                                      minTLMlength=self.parent().TLMlengthminimum.currentText(),maxTLMlength=self.parent().TLMlengthmaximum.currentText(),linearfitquality_request=self.parent().TLMlinearfitquality_request,Vds_foc=float(self.parent().Vds_FOC.text()),deltaVgsplusthres=float(self.parent().delta_Vgs_thres.text()))
		self.parameterlisttodisplay=[c for c in candidatestodisplay if c in self.devparameters]
		self.parameter_to_filter.blockSignals(True)
		self.parameter_to_filter.clear()
		self.parameter_to_filter.addItems(self.parameterlisttodisplay)
		self.parameter_to_filter.blockSignals(False)
		self.parameter_essential.blockSignals(True)
		self.parameter_essential.clear()
		self.parameter_essential.addItems(self.parameterlisttodisplay)
		for candd in candidatestodisplay:
			if candd in self.parameterlisttodisplay:
				self.parameter_essential.setCurrentIndex(self.parameter_essential.findText(candd))
				break
		self.parameter_essential.blockSignals(False)
		self.__TLM_table_new_cherrypick()
################################################################################################################
	# set up of device selector - internally set at first then later editions allow user to set devices
	# self.parent(().wd.tlmlength is a dictionary with keys of the TLM structures e.g. TLM0.3, TLM0.4 etc... and having as values the TLM lengths e.g. 0.3, 0.4, etc....
	# self.parent(().wd.tlmlength is formed in actions_histogram.py -> wafer_analysis.py -> utilities.py (geometry function)
	def __TLM_table_new_cherrypick(self):
		self.TLMlist=[d[0] for d in sorted(self.parent().wd.tlmlength.items(), key=lambda x:x[1])]					# self.TLMlist is a list containing the keys e.g. TLM0.3, TLM0.4 etc... of self.parent.parent(().wd.tlmlength sorted according to TLM length
		# enable  TLM length setter
		if hasattr(self.parent(),'TLMlengthminimum') and hasattr(self.parent(),'TLMlengthmaximum'):
			self.parent().TLMlengthminimum.setEnabled(True)
			self.parent().TLMlengthminimum.blockSignals(False)
			self.parent().TLMlengthmaximum.setEnabled(True)
			self.parent().TLMlengthmaximum.blockSignals(False)
		self.data_table=self.__get_datatable()
		if self.data_table!=None: self.Device_Listing_Table.setup(hheaders=self.data_table['parameter_headers'],vheaders=self.data_table['device_headers'],data=self.data_table['statdata'])
		else: self.Device_Listing_Table.setup(forcecleartable=True)		# just clear the table if have no data
#############################################################################################################################
	# user pressed button to save everything to clipboard
	def __save_to_clipboard(self):
		clipb=QtWidgets.QApplication.clipboard()
		dataclip=""
		#dataclip="Device Name\t"
		for parameterlabel in self.data_table['parameter_headers']:
			dataclip="".join([dataclip,parameterlabel,"\t"])				# column headers which are parameter names e.g. average |Idmax|, std dev |Idmax|, average Ron, etc....
		dataclip="".join([dataclip,"\n"])
		for devicetypelabel in self.data_table['device_headers']:			# row header which is the device type e.g. TLM0.3, TLM0.4, etc....
			for parameterlabel in self.data_table['parameter_headers']:
				if parameterlabel=='Device Name': dataclip="".join([dataclip,devicetypelabel,"\t"])
				# apply formatting specific to data type as determined by parameterlabel
				elif parameterlabel=="sample size":	dataclip="".join([dataclip,formatnum(self.data_table['statdata'][devicetypelabel][parameterlabel],type='int'),"\t"])		# use integer formatting
				else:	dataclip="".join([dataclip,formatnum(self.data_table['statdata'][devicetypelabel][parameterlabel],precision=2,removeplussigns=True),"\t"])				# use floating point formatting
			dataclip="".join([dataclip,"\n"])
		clipb.clear()
		clipb.setText("")
		clipb.setText(dataclip)
		#print("from line 99 of actions_statistics_dump.py clipdata",dataclip)
		#print("from line 101 of actions_statistics_dump.py clip board itself", clipb.text())
		# del clipb
		# clipb = QtWidgets.QApplication.clipboard()
		# clipb.setText("testing2")
###########################################################################################################################
# toggle to select upper fraction or lower fraction of the distribution to perform statistics
	def __toggleupperlowerfract(self):
		if self.upper_lower_but.isChecked():
			self.upper_lower_but.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(100,200,255)}')
			self.upper_lower_but.setText("Selected Upper Fraction")
			self.__TLM_table_new_cherrypick()												# refresh data on sheet
		else:
			self.upper_lower_but.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(0,120,255)}')
			self.upper_lower_but.setText("Selected Lower Fraction")
			self.__TLM_table_new_cherrypick()											# refresh data on sheet
#################################################################################################################################################################
# form table of statistical data and sort and filter it according to the column to be sorted and filtered (e.g. get lowest 10% Ron data)
# return row of measured parameter data e.g. |Idmax| etc... for a give device type e.g. TLM0.4 etc...
# topfilter=True means get devices which have columnkey data in the upper fractionfiltered range of data
# self.data is a dictionary of the format:
# self.data[d=device name][parameter (measured or calculated)] and data[d][p]=device data as specifed by the devicename=d and parameter name = p
	def __get_datatable(self):
		filteredparameter=self.parameter_to_filter.currentText()						# device parameter to use in "cherry picking" filter
		topfilter=self.upper_lower_but.isChecked()										# if topfilter==True then cherry pick the devices having data in the top fraction else cherry pick data  from the bottom fraction = fractionfiltered
		fractionfiltered=float(self.set_fract_data_selected.text())
		#essentialparameter='Ron'														# data to be considered here MUST have an Ron to be included - since these data are related to TLM parameters
		essentialparameter=self.parameter_essential.currentText()						# data to be considered here MUST have the essential parameter to be included e.g. Ron for TLM parameters
		# now sort data according to selected parameter
		# find column number according to column label key
		# data[device name][parameter name] parameters are things such as |Idmax|, On-Off ratio, etc.....

		# produce a dictionary data structure filterdata_keys_sorted[devicetype] which is an ordered list of devicenames (device keys) of all device keys containing the devicetype where devicetype can be things like TLM0.3, TLM0.6 etc...
		#filterdata_keys_sorted = {}
		device_statistical_data={}				# dictionary containing filtered (cherry-picked) data
		# define parts of parameter keys here to ensure consistency
		avg='average '
		stddev='std dev '
		geomean='geometric mean '
		logstddev='log std dev '
		#if not hasattr(self,'data'): print("from line 128 actions_statistics_dump.py no attribute data")
		for tlm in self.TLMlist:			#self.TLMlist is a sorted list of TLM device specifiers from self.__data_table_setup() e.g. ['TLM0.3','TLM0.4',....]
			# filterdata_keys_sorted is a list of device keys sorted according to the parameter: filteredparameter including only devices which have the parameter filterparameter.
			# note that the statement: if not is_number(k.split(tlm)[-1]) : was added to the following line due to conflation of things like 0.5 with 0.55
			# TODO do we really want to filter using: not is_number(k.split(tlm)[-1]) : or should we filter using just: k.split(tlm)[-1]=='' ?
			##filterdata_keys_sorted=[a[0] for a in sorted({k:self.data[k] for k in self.data if filteredparameter in self.data[k] and essentialparameter in self.data[k]  and tlm in k if not is_number(k.split(tlm)[-1])}.items(),key=lambda k_v: k_v[1][filteredparameter])]		# get data keys, i.e. device names representing the devices which have the filterparameter parameter so we can sort and filter
			#(last working) filterdata_keys_sorted=[a[0] for a in sorted({k:self.data[k] for k in self.data if filteredparameter in self.data[k] and essentialparameter in self.data[k]  and tlm in k}.items(),key=lambda k_v: k_v[1][filteredparameter])]		# get data keys, i.e. device names representing the devices which have the filterparameter parameter so we can sort and filter

			#filterdata_keys_sorted=[a[0] for a in sorted({k:self.data[k] for k in self.data if filteredparameter in self.data[k] and essentialparameter in self.data[k] and parse_rpn(expression=tlm,targetfilename=k)}.items(),key=lambda k_v: k_v[1][filteredparameter])]		# get data keys, i.e. device names representing the devices which have the filterparameter parameter so we can sort and filter
			filterdata_keys_sorted=[a[0] for a in sorted({k:self.data[k] for k in self.data if filteredparameter in self.data[k] and essentialparameter in self.data[k] and tlm in k.split('_')}.items(),key=lambda k_v: k_v[1][filteredparameter])]		# get data keys, i.e. device names representing the devices which have the filterparameter parameter so we can sort and filter

			N=round(fractionfiltered*len(filterdata_keys_sorted))							# find number of rows in the selected (upper or lower) fraction of data
			if N>0:																							# add data from tlm structure to table ONLY if it has the parameter that's being filtered
				# now get statistics of all reamaining data in the table tabledata is the top or bottom fraction of data in tablesorted
				if topfilter==True: tabledata_keys=filterdata_keys_sorted[len(filterdata_keys_sorted)-N:]					# get upper portion (fraction) of table data according to key column's data values
				else: tabledata_keys=filterdata_keys_sorted[:N]																# get lower portion (fraction) of table data according to key column's data values

				device_statistical_data[tlm]={}															# dictionary containing filtered (cherry-picked) data

				device_statistical_data[tlm]['TLM length um']=self.parent().wd.tlmlength[tlm]			# first column is the TLM length
				existingparameters=c.deque()
				#existingparameters_avg=c.deque()
				#existingparameters_std = c.deque()
				for kp in self.parameterlisttodisplay:																# populate table data structure for all parameters we want to show (actually the averages and std dev of those parameters)
					datatogetstatistics=[self.data[devk][kp] for devk in tabledata_keys if kp in self.data[devk]]				# tabledata_keys are the filtered device keys of cherry-picked data
					if not self.parent()._logplot:
						if len(datatogetstatistics)==1:
							device_statistical_data[tlm]["".join([avg,kp])]=datatogetstatistics[0]
							device_statistical_data[tlm]["".join([stddev,kp])]=0.
							if kp not in existingparameters: existingparameters.append(kp)
							# if "".join([avg, kp]) not in existingparameters_avg: existingparameters_avg.append("".join([avg, kp]))
							# if "".join([stddev,kp]) not in existingparameters_std: existingparameters_std.append("".join([stddev,kp]))
						elif len(datatogetstatistics)>1:
							device_statistical_data[tlm]["".join([avg,kp])]=np.average(datatogetstatistics)
							device_statistical_data[tlm]["".join([stddev,kp])]=np.std(datatogetstatistics)
							if kp not in existingparameters: existingparameters.append(kp)
							# if "".join([avg, kp]) not in existingparameters_avg: existingparameters_avg.append("".join([avg, kp]))
							# if "".join([stddev, kp]) not in existingparameters_std: existingparameters_std.append("".join([stddev, kp]))
						# else:
						# 	device_statistical_data[tlm]["".join([avg,kp])]='no data'
						# 	device_statistical_data[tlm]["".join([stddev,kp])]='no data'
					else:				# must use geometric mean np.power(10.,np.std(np.log10(
						if len(datatogetstatistics)==1:
							device_statistical_data[tlm]["".join([geomean,kp])]=datatogetstatistics[0]
							device_statistical_data[tlm]["".join([logstddev,kp])]=0.
							if kp not in existingparameters: existingparameters.append(kp)
							# if "".join([geomean,kp]) not in existingparameters_avg: existingparameters_avg.append("".join([geomean,kp]))
							# if "".join([logstddev,kp]) not in existingparameters_std: existingparameters_std.append("".join([logstddev,kp]))

						elif len(datatogetstatistics)>1:
							device_statistical_data[tlm]["".join([geomean,kp])]=st.mstats.gmean(datatogetstatistics)
							device_statistical_data[tlm]["".join([logstddev,kp])]=np.power(10.,np.std(np.log10(datatogetstatistics)))
							if kp not in existingparameters: existingparameters.append(kp)
							# if "".join([geomean,kp]) not in existingparameters_avg: existingparameters_avg.append("".join([geomean,kp]))
							# if "".join([logstddev,kp]) not in existingparameters_std: existingparameters_std.append("".join([logstddev,kp]))
						# else:
						# 	device_statistical_data[tlm]["".join([geomean,kp])]='no data'
						# 	device_statistical_data[tlm]["".join([logstddev,kp])]='no data'
				device_statistical_data[tlm]["sample size"]=N													# number of devices to form average for this TLM device type

		if len(device_statistical_data)>0:		# do we have any data?
			if not self.parent()._logplot:
				mean=lambda kp: "".join([avg,kp])
				stdd=lambda kp: "".join([stddev,kp])
			else:
				mean=lambda kp: "".join([geomean,kp])
				stdd=lambda kp: "".join([logstddev,kp])

			#parameter_headers=list(chain.from_iterable((mean(kp),stdd(kp)) for kp in self.parameterlisttodisplay))
			parameter_headers = list(chain.from_iterable((mean(kp),stdd(kp)) for kp in existingparameters))
			parameter_headers.insert(0,'Device Name')
			parameter_headers.insert(1,'TLM length um')
			parameter_headers.append("sample size")
			device_headers = [d for d in self.TLMlist if d in device_statistical_data]
			return {'statdata':device_statistical_data,'device_headers':device_headers, 'parameter_headers':parameter_headers}
		else: return None
#########################################################################################################################################################################################################

	def closeEvent(self,ce):
		print("close")
		self.CloseStaticsDump.emit()
		# disable  TLM length setter
		if hasattr(self.parent(),'TLMlengthminimum') and hasattr(self.parent(),'TLMlengthmaximum'):
			self.parent().TLMlengthminimum.setEnabled(False)
			self.parent().TLMlengthminimum.blockSignals(True)
			self.parent().TLMlengthmaximum.setEnabled(False)
			self.parent().TLMlengthmaximum.blockSignals(True)
		ce.accept()
# #################################################################################################################################












#########################################################################################################################
# Future expansions
##########################################################################################################################
# user has requested to add a manually histogram-filtered single datapoint to a single pair of cells (average and std deviation) in the data table for possible future export to a file
# NOT USED YET FUTURE POSSIBLE EXPANSION

	def __addhistogramtotable(self):
		dataaverage=self.parent().wd.Ron_Gon_histogram()['average']                # average
		datastddev=self.parent().wd.Ron_Gon_histogram()['stddev']                # standard deviation
		if dataaverage!='No data' and datastddev!='No data':                        # do we have data?
			itemmatch=self.parameter_averages_table.findItems(self.__devicetype,0)[0]       # search to see if there already exists a row containing this device
			if itemmatch!=None:                                                     # does the device already have an entry? If so, find it
				row=self.parameter_averages_table.row(self.parameter_averages_table.findItems(self.__devicetype,0)[0])      # find row   index of the device
				# now find where to insert the new data from the histogram
				# first we need to know the type of data returned from the histogram to know where to insert it

			else:           # add the device to a row
				self.parameter_averages_table.setRowCount(self.parameter_averages_table.rowCount()+1)   # Add a new row to the table

   # user requested a device change for manual data ###################################################################
   #  def __changed_device(self,index):
   #      self.__devicetype=self.devtype_selector.itemText(index)
   #      self.parent().includes += " "+self.__devicetype+" and"     # use this to filter data for the histogram too
   #      self.parent().set_includes.setText(self.parent().includes)      # update main histogram widget (this widget's parent) to reflect change
   #      self.parent()._update()                             # update histogram plots etc... using the selected parameters - in this case the S-D length
   #      return

#######################################################################################################################
# # subclass QTableWidget to add functionality
# class dataTable(QtWidgets.QTableWidget):
#     def __init__(self,parent=None):
#         super(dataTable,self).__init__(parent)

