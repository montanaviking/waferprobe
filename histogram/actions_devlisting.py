# device listing actions to produce a sortable list of devices on a wafer and their parameters
# device data dicfionary
#from devicelisting import *
from actions_wafergraph import *
#import collections as c
#from utilities import parse_rpn
from actions_plot_widget import *
from all_device_data_to_table import *
from select_device_to_plot_popup import *
from actions_comparator import *
import filter_defaults

class DeviceListing(Ui_DeviceListing,QtWidgets.QDialog):
	CloseDeviceListing=QtCore.pyqtSignal()
	RefreshDeviceData=QtCore.pyqtSignal()
	def __init__(self,parent=None,Vgs=None,minTLMlength=None,maxTLMlength=None,linearfitquality_request=None,fractVdsfit=None):
		super(DeviceListing,self).__init__(parent)
		# minimum and maximum TLM lengths are required during instantiation so as to also serve as indicators whether the TLM data have ever been calculated
		# if not is_number(minTLMlength) or not is_number(maxTLMlength): raise ValueError("ERROR! no minimum or maximum TLM length specified for DeviceListing setup")
		# else:
		# 	minTLMlength=float(minTLMlength)
		# 	maxTLMlength=float(maxTLMlength)
		if is_number(minTLMlength) and is_number(maxTLMlength):
			minTLMlength = float(minTLMlength)
			maxTLMlength=float(maxTLMlength)
		else:
			minTLMlength = None
			maxTLMlength = None

		if not is_number(fractVdsfit): raise ValueError("ERROR! need to specify fractVds for instantiation")
		else: fractVdsfit=float(fractVdsfit)
		#if wd!=None: self.parent().wd=wd												# wafer data
		#else: raise ValueError("ERROR! No wafer data supplied")
		if Vgs!=None: self.Vgs=float(Vgs)
		else: self.Vgs=None

		# selected gate voltage
		#else: raise ValueError("ERROR! No Vgs given")
		self.wafername=None
		self.setupUi(self)
		self.Device_Listing_Table.resizeRowsToContents()
		self.Device_Listing_Table.resizeColumnsToContents()

		self.comparator_but.clicked.connect(self.opencomparatorwidget)

		self.transfercurve_types=["single","dual 1st","dual 2nd","four 3rd","four 4th"]																	# default is to select all transfer curve types
		self.transfercurves_available=None
		self.transfercurve_standins=None

		if parent!=None: parent.RefreshDeviceData.connect(self._signaldatachanged)
		self.Device_Listing_Table.VerticalHeaderClicked.connect(self.select_plot_menu)
		self.selector_transfer_curve_type.clear()
		self.selector_transfer_curve_type.currentIndexChanged.connect(self.select_transfer_curve_type)
		self.selector_transfer_curve_type.blockSignals(True)
		self.selector_transfer_curve_type.setVisible(False)
		self.transfer_curve_type_label.setVisible(False)
		self.columnscaptured=c.deque([])				# columns to be delivered to clipboard
		self.wafermap_but.clicked.connect(self.showwafermap)
		self.transfercurve_possibilities= {"|Idmax| single":"|Idmax|","|Idmax| dual 1st":"|Idmax|","|Idmax| dual 2nd":"|Idmax|","|Idmax| four 3rd":"|Igmax|","|Idmax| four 4th":"|Igmax|",
								"On-Off ratio single":"On-Off ratio","On-Off ratio dual 1st":"On-Off ratio","On-Off ratio dual 2nd":"On-Off ratio",
								"|Igmax| single":"|Igmax|","|Igmax| dual 1st":"|Igmax|","|Igmax| dual 2nd":"|Igmax|",
								"gmmax single":"gmmax","gmmax dual 1st":"gmmax","gmmax dual 2nd":"gmmax",
								"|Idmin| single":"|Idmin|","|Idmin| dual 1st":"|Idmin|","|Idmin| dual 2nd":"|Idmin|","|Idmin| four 3rd":"|Idmin|","|Idmin| four 4th":"|Idmin|",
								"ORTHRatio |Idmax| single":"ORTHRatio |Idmax|","ORTHRatio |Idmax| dual 1st":"ORTHRatio |Idmax|","ORTHRatio |Idmax| dual 2nd":"ORTHRatio |Idmax|",
								"|Ig|@|Idmin| single":"|Ig|@|Idmin|","|Ig|@|Idmin| dual 1st":"|Ig|@|Idmin|","|Ig|@|Idmin| dual 2nd":"|Ig|@|Idmin|"}
		#self.select_transfer_curve_type()
		self.table_update(Vgs=Vgs,fractVdsfit=fractVdsfit,minTLMlength=minTLMlength,maxTLMlength=maxTLMlength,linearfitquality_request=linearfitquality_request,Vds_foc=parent.Vds_FOC.text(),deltaVgsplusthres=parent.delta_Vgs_thres.text(),fractVgsfit=parent.Yf_Vgsfitrange_frac.text(),performYf=parent.Yf_checkBox.isChecked())								# initialize table data
#####################################################################################################
# initializes and updates data in table
# uses dictionaries for data
# data are taken from parent's wafer data
	def table_update(self,Vgs=None,fractVdsfit=None,minTLMlength=None,maxTLMlength=None,linearfitquality_request=None,Vds_foc=None,deltaVgsplusthres=None,fractVgsfit=None,performYf=False):
		if Vgs==None: Vgs=self.Vgs
		if Vds_foc!=None: self.Vds_foc=float(Vds_foc)
		if deltaVgsplusthres!=None: self.deltaVgsplusthres=float(deltaVgsplusthres)
		if fractVgsfit!=None: self.fractVgsfit=float(fractVgsfit)
		if hasattr(self,'wafershow') and self.wafername!=self.parent().wd.wafername:	resetwafermap=True		# have we loaded a new wafer with the wafermap open?
		else: resetwafermap=False
		self.wafername=self.parent().wd.wafername
		self.wafer_label.setText("Wafer: "+self.parent().wd.wafername)									# set the wafer label
		self.data,self.hheaders=all_device_data_to_table(wd=self.parent().wd, selecteddevices=self.parent().wd.validdevices, Vgs=Vgs, fractVdsfit=fractVdsfit, minTLMlength=minTLMlength, maxTLMlength=maxTLMlength,linearfitquality_request=linearfitquality_request,Vds_foc=self.Vds_foc,deltaVgsplusthres=self.deltaVgsplusthres,fractVgsfit=self.fractVgsfit,performYf=performYf)
		if hasattr(self.parent(),'TLMlengthminimum') and hasattr(self.parent(),'TLMlengthmaximum') and "Rc TLM" in self.hheaders and "Rsh TLM" in self.hheaders:
			self.parent().TLMlengthminimum.blockSignals(False)
			self.parent().TLMlengthminimum.setEnabled(True)
			self.parent().TLMlengthmaximum.blockSignals(False)
			self.parent().TLMlengthmaximum.setEnabled(True)
		# populate transfer curve type selector only with those types availabel in the data set
		actual_tranfer_curve_types_for_selector=None
		self.transfercurves_available={hh:self.transfercurve_possibilities[hh] for hh in self.hheaders if hh in self.transfercurve_possibilities.keys()}		# the keys of self.transfercurvetypes are the transfer curve type data parameters available from the dataset
		if self.transfercurves_available!=None and len(self.transfercurves_available)>0:															# we have transfer curve data
			self.selector_transfer_curve_type.blockSignals(True)
			actual_tranfer_curve_types_for_selector=list(set([t for t in self.transfercurve_types for ta in self.transfercurves_available if t in ta]))		# transfer curve types which are available in the dataset and used to populate the transfer curve type selector, self.selector_transfer_curve_type
			actual_tranfer_curve_types_for_selector.insert(0,"All")
			self.selector_transfer_curve_type.clear()
			self.selector_transfer_curve_type.addItems(actual_tranfer_curve_types_for_selector)
			self.selector_transfer_curve_type.blockSignals(False)
			self.selector_transfer_curve_type.setVisible(True)
			self.transfer_curve_type_label.setVisible(True)
############################Done getting data################################################################
# data is a 2-D dictionary with the structure: data[devicename][parametername]
# where devicename and parametername are dictionary keys and the value is the value indicated by the devicename (device) and parametername (parameter)
# hheaders[] is a list containing all the parameternames for which valid data exist on this wafer
# vheaders[] is a list of all the device names for which there are valid data
# all data are post filtering (both for devicename and parameter value ranges allowed)
		self.Device_Listing_Table.setup(hheaders=self.hheaders,vheaders=list(self.data.keys()),data=self.data,parameter_standins=self.transfercurve_standins)				# calls setup in file devtable.py
		self.measurementtypes=[self.hheaders[i] for i in range(3,len(self.hheaders))]									# pass on available measurement types, excluding "devicename', 'X', and 'Y'from hheaders
		self.tabledata=self.data																		# data to wafermap in actions_wafergraph.py
		self.devparametersmeasured=self.hheaders																	# roll up measured device parameters list to allow other widgets/dialogs to access
		if resetwafermap:
			for child in self.findChildren(WaferGraph): child.close()									# close all open old wafermaps because they're stale
			self.showwafermap()																			# open fresh wafer map
		self.RefreshDeviceData.emit()																# notify about device data table updates e.g. notify the wafer map layout in actions_wafergraph.py
#########################################################################################################################################################################################################
# user or setup has selected the type of dual transfer curve
	def select_transfer_curve_type(self):
		if self.selector_transfer_curve_type.currentText()=="All": 			# don't modify table headers and present all available data in table
			self.transfercurve_standins = None
			hheaderseffective=self.hheaders
		else: 																							# user has selected data derived from single-swept transfer curve and only that data will be presented in the table for transfer curve data with generic headers
			self.transfercurve_standins={k:self.transfercurves_available[k] for k in self.transfercurves_available if self.selector_transfer_curve_type.currentText() in k}
			hheaderseffective=[h for h in self.hheaders if h not in self.transfercurve_possibilities or h in self.transfercurve_standins]
		self.Device_Listing_Table.setup(hheaders=hheaderseffective,vheaders=list(self.data.keys()),data=self.data,parameter_standins=self.transfercurve_standins)				# calls setup in file devtable.py
#########################################################################################################################################################################################################
	def closeEvent(self,ce):
		print("close")
		self.CloseDeviceListing.emit()
		# disable  TLM length setter
		if hasattr(self.parent(),'TLMlengthminimum') and hasattr(self.parent(),'TLMlengthmaximum'):
			self.parent().TLMlengthminimum.blockSignals(True)
			self.parent().TLMlengthminimum.setEnabled(False)
			self.parent().TLMlengthmaximum.blockSignals(True)
			self.parent().TLMlengthmaximum.setEnabled(False)
		ce.accept()
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
###################################################################################################################################
# user clicked to open comparator table
	def opencomparatorwidget(self):
		self.comparator=Comparator(parent=self)
		self.comparator.setWindowFlags(QtCore.Qt.Dialog)
		self.comparator.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.comparator.show()
####################################################################################################################################
# # change in parent data - pass signal to children e.g. plots
	def _signaldatachanged(self):
		self.RefreshDeviceData.emit()
		#print("from 159 in actions_devlistin.py signal")