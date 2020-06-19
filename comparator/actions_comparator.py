# device comparator table
#from actions_wafergraph import *
from comparator_widget import *
from actions_wafergraph import *
from collections import deque
from utilities import parse_rpn
from actions_plot_widget import *
#from all_device_data_to_table import *
from select_device_to_plot_popup import *
from collections import ChainMap


class Comparator(Ui_Comparator,QtWidgets.QDialog):
	CloseComparator=QtCore.pyqtSignal()
	RefreshComparatorData=QtCore.pyqtSignal()
	def __init__(self,parent=None):
		super(Comparator,self).__init__(parent)
		self.setupUi(self)
		self.colAfilled=False
		self.colBfilled=False
		#self.cliprows=deque()
		self.datatypes=[]
		self.pasteddata=[]
		self.prefixes=[]
		self.PrefixA.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
		self.PrefixB.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
		self.wafername=None

		self.Device_Listing_Table.setColumnCount(3)
		self.Device_Listing_Table.resizeRowsToContents()
		self.Device_Listing_Table.resizeColumnsToContents()
		#self.Device_Listing_Table.PasteColumn.connect(self.__pastecolumn)
		self.paste_data_but.clicked.connect(self.__pastecolumn)
		self.paste_data_but.setText("Click to Paste New Data or Data Ready")
		self.paste_data_but.setStyleSheet("QPushButton { background-color : green; color : black; }")

		self.Device_Listing_Table.VerticalHeaderClicked.connect(self.select_plot_menu)

		self.__controlsonoff(blocksignals=True)
		self.comparison_type_selector.clear()
		self.comparison_type_selector.currentIndexChanged.connect(self.table_update)
		self.comparison_type_selector.addItem("A/B")
		self.comparison_type_selector.addItem("abs(A/B)")
		self.comparison_type_selector.addItem("A-B")

		self.data_type_selectorA.currentIndexChanged.connect(self.table_update)
		self.data_type_selectorB.currentIndexChanged.connect(self.table_update)
		self.PrefixA.currentIndexChanged.connect(self.table_update)
		self.PrefixB.currentIndexChanged.connect(self.table_update)
#####################################################################################################
# initializes and updates data in table
# uses dictionaries for data
#
# outputs data is a 2-D dictionary with the structure: data[device name suffix][data type]=value
# where devicename and parametername are dictionary keys and the value is the value indicated by the devicename (device) and parametername (parameter)
# hheaders[] is a list containing all the parameternames for which valid data exist on this wafer
# vheaders[] is a list of all the device names for which there are valid data
# pastedict is a dictionary of data with: pastedict[data type][device name prefix][device name extension after prefix (suffix)]=value i.e. the device name suffix
# note that __ is the separator to split the device name prefix from the device name suffix The suffix is the portion of the device name that identifies a device on the wafer
# the prefix may contain the wafer name and also some information about measurement conditions
# self.pastedict is a nested list self.pastedict[data type index][index of device][index 0=full device name,1=value]
# results[device name suffix]=data      where device name suffix is the device name excluding the wafer and measurement information - i.e. the portion of the device name which identifies the device type on the maskset

	def table_update(self):
		self.__controlsonoff(blocksignals=False)
		# build table
		dtA=self.data_type_selectorA.currentText()           #user-selected data type to compare in first column data
		prA=self.PrefixA.currentText()                       #user-selected device type (wafer+test parameters) to compare in first column data. Excludes the portion of the device name which identifies it on the wafer mask
		dtB=self.data_type_selectorB.currentText()           #user-selected data type to compare in 2nd column data
		prB=self.PrefixB.currentText()                       #user-selected device type (wafer+test parameters) to compare in 2nd column data Excludes the portion of the device name which identifies it on the wafer mask
		#print("from line 79 in actions_comparator.py prA,prB",prA,prB)
		if self.comparison_type_selector.currentText()=="A-B": results={k:formatnum(self.pastedict[dtA][prA][k] - self.pastedict[dtB][prB][k], precision=2) for k in self.pastedict[dtA][prA].keys()
		                                                                  if  dtA in self.pastedict.keys() and dtB in self.pastedict.keys() and prA in self.pastedict[dtA].keys() and prB in self.pastedict[dtB].keys() and k in self.pastedict[dtB][prB].keys()
		                                                                  and is_number(self.pastedict[dtA][prA][k]-self.pastedict[dtB][prB][k])}
		elif self.comparison_type_selector.currentText()=="A/B": results={k:formatnum(self.pastedict[dtA][prA][k]/self.pastedict[dtB][prB][k], precision=2) for k in self.pastedict[dtA][prA].keys()
		                                                                  if  dtA in self.pastedict.keys() and dtB in self.pastedict.keys() and prA in self.pastedict[dtA].keys() and prB in self.pastedict[dtB].keys() and k in self.pastedict[dtB][prB].keys()
		                                                                  and is_number(self.pastedict[dtA][prA][k]/self.pastedict[dtB][prB][k])}
		elif self.comparison_type_selector.currentText()=="abs(A/B)": results={k:formatnum(abs(self.pastedict[dtA][prA][k]/self.pastedict[dtB][prB][k]), precision=2) for k in self.pastedict[dtA][prA].keys()
		                                                                  if  dtA in self.pastedict.keys() and dtB in self.pastedict.keys() and prA in self.pastedict[dtA].keys() and prB in self.pastedict[dtB].keys() and k in self.pastedict[dtB][prB].keys()
		                                                                  and is_number(self.pastedict[dtA][prA][k]/self.pastedict[dtB][prB][k])}
		else:
			m=QtWidgets.QMessageBox()
			m.setText("ERROR! comparison type selection not available")
			m.exec_()
			return

		hheaders=["Device Mask Name","A","B","Results"]
		suffixes=list(self.pastedict[dtA][prA].keys())

		data={vh:dict(ChainMap({hheaders[0]:vh},{hheaders[1]:self.pastedict[dtA][prA][vh]},{hheaders[2]:self.pastedict[dtB][prB][vh]},{hheaders[3]:results[vh]})) for vh in suffixes if vh in results}           # data without results column - contains just the two input columns to be compared
		self.Device_Listing_Table.setup(hheaders=hheaders, vheaders=suffixes, data=data)
		#self.RefreshDeviceData.emit()																# notify about device data table updates e.g. notify the wafer map layout in actions_wafergraph.py
# #################################################################################################################################
# 	# user clicked on row header i.e. device name so plot device IV and/or other parameters
	def select_plot_menu(self,devicename):
		select_device_to_plot_menu(parent=self,cd=self.parent().wd.DCd[devicename])
# #################################################################################################################################
# #################################################################################################################################
# 	# user clicked to show wafer map
	def showwafermap(self):
		#plandirectory=self.parent().wd.pathname
		self.wafershow=WaferGraph(parent=self,plandirectory=self.parent().wd.pathname)				# WaferGraph() class is in actions_wafergraph.py
		self.wafershow.setWindowFlags(QtCore.Qt.Dialog)
		self.wafershow.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.wafershow.show()
####################################################################################################################################
# User has pasted set of data
	def __pastecolumn(self):
		clipb=QtWidgets.QApplication.clipboard()
		if clipb.text()!="":
			clipdatastr=clipb.text()                              # need to pass this way to avoid deletion of clipboard
		else:
			m=QtWidgets.QMessageBox()
			m.setText("No data to paste")
			m.exec_()
			return
		self.paste_data_but.setText("Data NOT Ready Loading ...")
		self.paste_data_but.setStyleSheet("QPushButton { background-color : red; color : black; }")
		#self.paste_data_but.repaint()
		self.repaint()
		self.__controlsonoff(blocksignals=True)                             # block signals to selectors to allow programmatic changes
		newpasteddata=[r.strip() for r in clipdatastr.split("\n")]          # get rows of clipboard data
		currentdatatypes=[s for s in newpasteddata[0].split("\t") if s!='' and s!='\t' and s!='\n']            # get list of current datatypes (parameter types) selected. Eliminate white space too

		if len(currentdatatypes)>2:                  # Number of columns to be copied. Can only be one as we are only allowed to paste in one column of data at a time
			m=QtWidgets.QMessageBox()
			m.setText("Can paste only a maximum of two columns at a time!")
			m.exec_()
			self.loading_indicator.setText("Data Ready")
			self.loading_indicator.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(100,200,255)}')
			return
		else:       # add data types to selectors

			del newpasteddata[0]                                  # remove first row because it contains only header information i.e. parameter labels
			self.datatypes.extend(currentdatatypes)                 # add in newly-selected column(s) datatypes
			self.prefixes.append(list(set([s.split("\t")[0].split("__")[0] for s in newpasteddata if s.split("\t")[0].split("__")[0]!='' ])))                        # get all unique prefixes from devicenames on the currently-selected data columns
			self.pasteddata.append([[p.split("\t")[0],p.split("\t")[1]] for p in newpasteddata if p!=''])
			if len(currentdatatypes)==2:
				self.prefixes.append(list(set([s.split("\t")[0].split("__")[0] for s in newpasteddata if s.split("\t")[0].split("__")[0]!=''])))    # make sure that each column of data has a corresponding set of prefixes
				self.pasteddata.append([[p.split("\t")[0],p.split("\t")[2]] for p in newpasteddata if p!=''] )                    # if we added two columns of data, then add in the second column
			while len(self.datatypes)>2:
				del self.datatypes[0]        # remove previous data types (oldest one selected) if necessary to keep total number at 2 or below
				del self.prefixes[0]         # remove previous prefixes associated with the previous column (oldest one selected)
				del self.pasteddata[0]

			if len(self.prefixes)>2: print("from line 124 in actions_comparator.py ERROR! number of prefix source columns >2")
			self.data_type_selectorA.clear()
			self.data_type_selectorB.clear()
			contentsmaxlength=max([len(p) for p in self.datatypes])
			self.data_type_selectorA.addItems(self.datatypes)
			self.data_type_selectorB.addItems(self.datatypes)
			self.data_type_selectorA.setMinimumContentsLength(contentsmaxlength)
			self.data_type_selectorB.setMinimumContentsLength(contentsmaxlength)

			#print("from line 125 in actions_comparator.py self.datatypes",self.datatypes)

			# now populate the prefix selectors
			combined_prefixes=[]
			for cp in self.prefixes: combined_prefixes.extend(cp)              # combine prefixes from all the columns
			combined_prefixes=list(set(combined_prefixes))                            # eliminate prefixes which are the same
			self.PrefixA.clear()
			self.PrefixB.clear()
			self.PrefixA.addItems(combined_prefixes)
			self.PrefixB.addItems(combined_prefixes)
			contentsmaxlength=max([len(p) for p in combined_prefixes])
			self.PrefixA.setMinimumContentsLength(contentsmaxlength)
			self.PrefixB.setMinimumContentsLength(contentsmaxlength)
			self.pastedict={self.datatypes[0]:{d[0].split("__")[0]:{dv[0].split("__")[1]:float(dv[1]) for dv in self.pasteddata[0] if is_number(dv[1]) and d[0].split("__")[0]==dv[0].split("__")[0] }  for d in self.pasteddata[0]}}
			if len(self.datatypes)>1:
				if self.datatypes[0]==self.datatypes[1]:
					self.pastedict[self.datatypes[1]]=ChainMap(self.pastedict[self.datatypes[1]],{d[0].split("__")[0]:{dv[0].split("__")[1]:float(dv[1]) for dv in self.pasteddata[1] if is_number(dv[1]) and d[0].split("__")[0]==dv[0].split("__")[0] }  for d in self.pasteddata[1]})
				else:
					self.pastedict=ChainMap(self.pastedict,{self.datatypes[1]:{d[0].split("__")[0]:{dv[0].split("__")[1]:float(dv[1]) for dv in self.pasteddata[1] if is_number(dv[1]) and d[0].split("__")[0]==dv[0].split("__")[0] }  for d in self.pasteddata[1]}})
			self.table_update()
		self.paste_data_but.setText("Click to Paste New Data or Data Ready")
		self.paste_data_but.setStyleSheet("QPushButton { background-color : green; color : black; }")
		self.repaint()
		self.__controlsonoff(blocksignals=False)
		return                # need to add more data before you can compare

		#### have datatypes updated now load in
###################################################################################################################################################################################################################
# user selected a device name prefix
# 	def __selected_prefix(self):

#########################################
	def __controlsonoff(self,blocksignals=False):
		self.comparison_type_selector.blockSignals(blocksignals)
		self.data_type_selectorA.blockSignals(blocksignals)
		self.data_type_selectorB.blockSignals(blocksignals)
		self.PrefixA.blockSignals(blocksignals)
		self.PrefixB.blockSignals(blocksignals)
###############################################