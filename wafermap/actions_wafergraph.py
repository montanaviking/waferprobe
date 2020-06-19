__author__ = 'viking'
# wafer graph actions test
from PyQt5 import QtCore, QtGui, QtWidgets
# from PyQt4.QtGui import QPainterPath, QPainter, QPaintEvent, QBrush, QColor, QGraphicsRectItem
#from PyQt4.QtCore import QObject, pyqtSignal,Qt, QRectF
from waferplot import Ui_Dialog
#import numpy as np
#from utilities import formatnum
#import collections as col
from wafergraph_scene_view_items import *
from select_device_to_plot_popup import *
from actions_devlisting import *
from read_testplan import *
#from actions_slider import *
from colorscale_scene_view_items import *

class WaferGraph(Ui_Dialog,QtWidgets.QGraphicsView):
	RefreshDeviceData = QtCore.pyqtSignal()
	#DevicesToAnalyzefromWaferGraph=QtCore.pyqtSignal(list)
	def __init__(self,parent=None,plandirectory=None):			# the plandirectory and planname is the full path and filename respectively of the wafer layout probe plan
		super(WaferGraph,self).__init__(parent)
		self.setupUi(self)
		# setup device listing table
		#wd=self.parent().parent().wd
		self.Device_Listing_Table.resizeRowsToContents()
		self.Device_Listing_Table.resizeColumnsToContents()

		self.devicesindisplaylist=[]
		self.devicestoanalyze=[]
		self._logscale=False
		self.visible_mask_levels=[]
		self.wafername.setText(self.parent().wafername)
		self.waferview=WaferView()                             # instantiate a wafermap view
		self.wafermapcontainer.addWidget(self.waferview)       # add this wafermap view to this widget's wafermap container
		self.wscene=sw(parent=self.waferview)					#instantiate the wafer map scene of class sw() from wafergraph_scene_view_items.py

		self.colorscaleview = ColorScaleView()
		self.colorscalecontainer.addWidget(self.colorscaleview)               # add a color scale to its container in this widget
		self.colorscalescene=ColorScaleScene(parent=self.colorscaleview) # instantiate the color scale scene of class ColorScaleScene() from colorscale_scene_view_items.py
		self.colorscaleview.setSceneRect(0,20,0,100)
		self.plandirectory = plandirectory
		self.mainanalysis=self.parent().parent()				# this is the main wafer analysis GUI from file actioins_histogram
		################ set up wafer plan selections
		try: filelisting = os.listdir("".join([plandirectory,sub('TESTPLAN')]))
		except: raise ValueError("ERROR wafer test plan file directory does not exist")
		if len(filelisting)<1: raise ValueError("ERROR wafer test plan file directory does not exist")
		for filetp in filelisting:
			if filetp.endswith("plan.csv"):
				self.waferplanfile.addItem(filetp)
		if plandirectory==None or self.waferplanfile.count()<1 or self.waferplanfile.currentText()==None: raise ValueError("ERROR! No wafer layout plan directory and/or name given")
		self.tp=TestPlan(plandirectory,self.waferplanfile.currentText())								# load in wafer geometry from test plan
		wafersizeX=self.tp.sectionsize_map_level()['X']
		wafersizeY=self.tp.sectionsize_map_level()['Y']
		self.waferview.setSceneRect(-wafersizeX, wafersizeY, 4 * wafersizeX, -4 * wafersizeY)            # set extents of wafer
		self.waferview.setScene(self.wscene)
		self.maxdevlevel=len(self.tp.leveldev)
		self.measurementtype.blockSignals(True)
		self.measurementtype.clear()
		for measurementtype in self.parent().measurementtypes:      # add all available data types to selector EXCEPT gate width
			if "total gate width" not in measurementtype:
				self.measurementtype.addItem(measurementtype)
		self.measurementtype.blockSignals(False)
		self.masklevels.blockSignals(True)
		self.masklevels.clear()
		self.masklevels.addItems([str(i) for i in range(0,len(self.tp.leveldev))])				# add all available levels to selector
		self.masklevels.blockSignals(False)
		self.addsites(level=len(self.tp.leveldev)-1)
		self.wscene.set_wafer_data(data=self.parent().tabledata,parameter=self.measurementtype.currentText())
		self.log_linear_scale_but.setChecked(False)
		self.log_linear_scale_but.setText("Linear color scale")		# then user has set to use linear plots and linear statistics (standard deviation and average)
		self.log_linear_scale_but.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(100,200,255)}')

		# set up button which determines how devices having no data are drawn
		self.crossout_nodata_but.setChecked(True)
		self.crossout_nodata_but.setText("no data then cross out")
		self.crossout_nodata_but.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(0,200,255)}')

		# connect the signals##################
		self.parent().RefreshDeviceData.connect(self.update)  # update wafermap data when data change
		self.measurementtype.currentIndexChanged.connect(self.changedmeasurementtype)		# enable user to change the data type displayed
		self.masklevels.itemClicked.connect(self.changedmaxmasklevelshown)			# enable user to change the maximum masklevel displayed
		self.Device_Listing_Table.VerticalHeaderClicked.connect(self.select_plot_menu)				# enable user to plot
		self.wscene.DeviceClicked.connect(self.listdevicesclicked)									# user right-clicked device (item) in scene to select and obtain data listing
		self.wscene.DeviceSelectedforAnalysis.connect(self.addtodevicestoanalyze)					# user cntrl-right-clicked  device in scene to add its devices to the validdevicelist for analysis
		self.selectforanalysis_but.clicked.connect(self.selectforanalysis)							# user requested that the devices selected for analysis be used to filter devices for analysis in the main histogram program
		self.clearselections_but.clicked.connect(self.cleardevicelist)								# user clicked clear selections button to deselect all devices (items) in scene self.wscene
		self.reset_selectforanalysis_but.clicked.connect(self.cleardevicestoanalyze)				# user clicked clear devices selected for analysis
		self.waferplanfile.currentIndexChanged.connect(self.setwaferplanfile)						# allow user to select from different wafer plan files to accomodate different measurement runs on the wafer
		self.log_linear_scale_but.clicked.connect(self.__loglinset)									# button to toggle color scale on wafermap from log to linear and back
		self.crossout_nodata_but.clicked.connect(self.__changedcrossoutstatus)						# button to allow user to toggle how devices having no data are shown - i.e. select them to be crossed-out or to be invisible
		self.wafermap_to_clipboard_but.clicked.connect(self.__send_to_clipboard)
		####################
		self.wscene.fitinview()
############################################################################################################################################
# data setup and update
	def update(self):
		# set up measurement types available
		self.measurementtype.blockSignals(True)
		currentmeasurementtype=self.measurementtype.currentText()								# save current measurement type
		self.measurementtype.clear()
		self.measurementtype.addItems(self.parent().measurementtypes)							# add all available data types to selector
		if currentmeasurementtype in self.parent().measurementtypes:							# is the current measurement type setting included in the new measurement types?
			self.measurementtype.setCurrentIndex(self.measurementtype.findText(currentmeasurementtype))		# set selector to last measurement type if it exists
		# If possible, set the
		self.measurementtype.blockSignals(False)
		self.masklevels.blockSignals(True)
		self.masklevels.clear()
		self.masklevels.addItems([str(i) for i in range(0,len(self.tp.leveldev))])				# add all available levels to selector
		self.masklevels.blockSignals(False)
		self.wscene.set_wafer_data(data=self.parent().tabledata,parameter=self.measurementtype.currentText(),logscale=self._logscale)
		self.listdevicesclicked_refreshdata()													# refresh device list if it exists
		self.RefreshDeviceData.emit()  															# notify about device data updates e.g. notify the wafer map layout in actions_plot_widget.py
########################################################################################################################################
# set maximum masklevel displayed
	def changedmaxmasklevelshown(self):
		selitems=self.masklevels.selectedItems()
		self.wscene.set_levels_visible(visible_levels=[int(item.text()) for item in selitems])
		self.cleardevicelist()																	# clear wafermap device table
		self.cleardevicestoanalyze()  															# clear devices selected for analysis
########################################################################################################################################
# set maximum masklevel displayed
	def changedmeasurementtype(self):
		self.wscene.set_datatypedisplayed(self.measurementtype.currentText())
########################################################################################################################################
########################################################################################################################################
# user set the wafer plan file
	def setwaferplanfile(self):
		#while len(self.wscene.items())>0: self.wscene.removeItem(self.wscene.items()[0])					# clear all items (devices and wafermap) from wafermap scene (obsolete method)
		self.wscene.clear()																					# clear all items (devices and wafermap) from wafermap scene
		self.tp=TestPlan(self.plandirectory,self.waferplanfile.currentText())								# load in wafer geometry from test plan
		self.maxdevlevel=len(self.tp.leveldev)
		self.addsites(level=len(self.tp.leveldev)-1)
		self.wscene.set_wafer_data(data=self.parent().tabledata,parameter=self.measurementtype.currentText())
		self.listdevicesclicked_refreshdata()
		self.cleardevicelist()																				# clear wafermap device table
		self.cleardevicestoanalyze()																		# clear devices selected for analysis
########################################################################################################################################
########################################################################################################################################
# remove all signal connections prior to closing this dialog
	def closeEvent(self,e):
		#print("from actions_wafergraph.py line 79 close")
		try: self.parent().RefreshDeviceListing.disconnect()
		except: pass
		try: self.masklevels.itemClicked.disconnect()
		except: pass
		try: self.measurementtype.currentIndexChanged.disconnect()
		except: pass
		try: self.Device_Listing_Table.VerticalHeaderClicked.disconnect()
		except: pass
		try: self.wscene.DeviceClicked.disconnect()
		except: pass
		try: self.clearselections_but.clicked.disconnect()
		except: pass
		try: self.waferplanfile.currentIndexChanged.disconnect()
		except: pass
		self.close()
# #################################################################################################################################
# user clicked on device so set up list of device or it's children at level = 0 to show all data in list
# devicedata is the device item clicked of type QtWidgets.QGraphicsRectItem - a dummy that's not used here
# devicedata is the single data point of the device - a dummy that's not used here
# devicename is the name of the clicked device and is used to retrieve data to populate the list of the device's decendents at mask level=0
# self.wscene.alldataparameters is a list of the data parameters measured in this wafer
# self.wscene.data is a 2D dictionary data type having the device wafer data with format {devicename1:{parameter1:data1, parameter2:data2,....}, devicename2:{parameter1:data1, parameter2:data2,....},....}
	def listdevicesclicked(self, deviceitem, devicename, devicedata):
		self.devicesindisplaylist+=[dn for dn in list(self.wscene.data.keys()) if devicename.split('_')==dn.split('_')[:len(devicename.split('_'))]]
		self.devicesindisplaylist=list(set(self.devicesindisplaylist))											# eliminate duplicate devices from list
		devparameters=self.parent().devparametersmeasured
		selecteddevicedata={devname:self.wscene.data[devname] for devname in self.devicesindisplaylist if devname in self.wscene.data}
		self.Device_Listing_Table.setup(hheaders=devparameters,vheaders=self.devicesindisplaylist,data=selecteddevicedata)
		self.Device_Listing_Table.setFixedHeight(50+25*self.Device_Listing_Table.rowCount())
		self.Device_Listing_Table.resizeColumnsToContents()

	def listdevicesclicked_refreshdata(self):								# same as above but keep same device selections and refresh data
		if len(self.devicesindisplaylist)>0:
			self.devicesindisplaylist=[dn for dn in list(self.wscene.data.keys()) if dn in self.devicesindisplaylist]			# added to properly update list should members of the list disappear due to filtering
			#self.devicesindisplaylist=list(set(self.devicesindisplaylist))											# eliminate duplicate devices from list
			devparameters=self.parent().devparametersmeasured
			selecteddevicedata={devname:self.wscene.data[devname] for devname in self.devicesindisplaylist if devname in self.wscene.data}
			self.Device_Listing_Table.setup(hheaders=devparameters,vheaders=self.devicesindisplaylist,data=selecteddevicedata)
			self.Device_Listing_Table.setFixedHeight(50+25*self.Device_Listing_Table.rowCount())
			self.Device_Listing_Table.resizeColumnsToContents()
# clear list of selected devices
	def cleardevicelist(self):
		self.devicesindisplaylist = []
		self.Device_Listing_Table.clear()
		self.Device_Listing_Table.setRowCount(0)
		self.Device_Listing_Table.setColumnCount(0)
		self.Device_Listing_Table.setFixedHeight(0)
		self.wscene.deselectalldevices()
# #################################################################################################################################
# user clicked on device to analyze so set up list of device or it's children at level = 0 to analyze
	def addtodevicestoanalyze(self, devicename):
		self.devicestoanalyze.extend([dn for dn in list(self.wscene.data.keys()) if devicename.split('_')==dn.split('_')[:len(devicename.split('_'))]])
		self.devicestoanalyze = list(set(self.devicestoanalyze))  # eliminate duplicate devices from list

# user requested that the devices selected for analysis be used to filter devices for analysis in the main histogram program
	def selectforanalysis(self):
		if len(self.devicestoanalyze)>1:
			self.selectforanalysis_but.setText('only selected devices analyzed')
			self.selectforanalysis_but.setStyleSheet('QPushButton {color:rgb(255,0,0);background-color:rgb(255,255,255)}')
			#self.DevicesToAnalyzefromWaferGraph.emit(self.devicestoanalyze) # send list of devices to analyze to actions_histogram.py
			self.mainanalysis.set_selected_devices(self.devicestoanalyze)  # send list of devices to analyze to actions_histogram.py
			#print("from line 196 in actions_wafergraph.py list of devices to analyze", self.devicestoanalyze)
			self.update()
		else:
			m = QtWidgets.QMessageBox()
			m.setText("You must select more than 1 device for statistical analysis")
			m.exec_()
# clear list of selected devices to analyze
	def cleardevicestoanalyze(self):
		self.selectforanalysis_but.setText('select devices for analysis')
		self.selectforanalysis_but.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:rgb(255,255,255)}')
		self.devicestoanalyze=[]										# clear list of devices to apply to filter for analysis
		self.cleardevicelist()
		self.wscene.deselectdevicestoanalyze()
		self.mainanalysis.set_selected_devices(self.devicestoanalyze)  # send list of devices to analyze to actions_histogram.py
		self.update()
# #################################################################################################################################
# 	# user clicked on row header i.e. device name so plot device IV and/or other parameters
	def select_plot_menu(self,devicename):
		print("from line 216 in wafer_analysis.py device=",self.mainanalysis.wd.DCd[devicename].devicename)
		select_device_to_plot_menu(parent=self, cd=self.mainanalysis.wd.DCd[devicename])
# #################################################################################################################################
########################################################################################################################################
# user has changed the wafer plan file
########################################################################################################################################
# populate wafer map with all devices
# self.tp is the test plan of the wafer which is a class containing information on current position, devicename, and level under consideration in the wafer map
# self.maxdevlevel is the maximum level which is populated with devices - usually the reticle level
# output is self.dev[ilevel][devicename] which is a dictionary of devices
# level is the maximum mask level data are shown
	def addsites(self,level=0,parent=None):
		donelevel=False
		while not donelevel:
			if level<self.maxdevlevel:                              # create a device only at the highest device level (usually the reticle level) and below
				xsize=self.tp.devicesize_map_level(level=level)['X']
				ysize=self.tp.devicesize_map_level(level=level)['Y']
				xloc=self.tp.devactualX[level][self.tp.leveldev[level]]				# x location relative to parent coordinates
				yloc=self.tp.devactualY[level][self.tp.leveldev[level]]				# y location relative to parent coordinates
				loc_wafer=self.tp.get_posplan_map_level(level=level)					# get location of device in wafer coordinates
				# find if this device is excluded from the measurements
				devicename="".join([self.tp.wafername,'_',self.tp.devicename_map_level(level=level)])
				for ex in self.tp.get_exclusions(): # ex is an array of level designators to exclude from measurements
					devmeasured=False
					for tex in ex:		# look at each element of the exclusion all must match to exclude device
						if tex not in devicename: devmeasured=True # test to see if the devicename is among those excluded from probing
				dev=DeviceRect(loc_wafer=loc_wafer,posX=xloc,posY=yloc,width=xsize,height=ysize,devicename=devicename,level=level,parent=parent,setscene=self.wscene)     # make device
				if level>0:
					chs=self.addsites(level=level-1,parent=dev)['status']                                  # add children devices recursively
					if chs['donelevel']: s=self.tp.movenextsite_within_map_level(level=level)											# if the child level is done, then attempt to move to the next device
				else: s=self.tp.movenextsite_within_map_level(level=0)                                                                                 # we are at the lowest level
			donelevel=s['donelevel']
			if parent==None: self.wscene.addItem(dev)
		return {'device':dev,'status':s}
########################################################################################################################
# toggle between linear and log wafer map data display - note this also affects how average and standard deviations are presented!
# a checked button means that the scale is linear
	def __loglinset(self):
		#print("from actions_wafergraph.py __loglinset() line 209 is checked before?",self.log_linear_scale_but.isChecked()) #debug
		#print("from actions_histogram.py __loglinset() line 971 is checkable?",self.log_linear_histogram_but.isCheckable()) #debug
		if self.log_linear_scale_but.isChecked():			# Toggle from linear plots to log plots and log normal statistics (standard deviation and average)
			self.log_linear_scale_but.setText("Log color scale")
			self.log_linear_scale_but.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(0,120,255)}')
			self._logscale=True
			self.wscene.set_wafer_data(data=self.parent().tabledata,parameter=self.measurementtype.currentText(),logscale=self._logscale)
		else:
			#print("from actions_wafergraph.py __loglinset() line 217 set linear") #debug
			self.log_linear_scale_but.setText("Linear color scale")		# then user has set to use linear plots and linear statistics (standard deviation and average)
			self.log_linear_scale_but.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(100,200,255)}')
			self._logscale=False
			self.wscene.set_wafer_data(data=self.parent().tabledata,parameter=self.measurementtype.currentText(),logscale=self._logscale)
########################################################################################################################################
# user clicked button to toggle crossout status of devices which have no data
# allows user to select view of devices with no data either with a cross through them or invisible
	def __changedcrossoutstatus(self):
		if self.crossout_nodata_but.isChecked():			# Toggle from linear plots to log plots and log normal statistics (standard deviation and average)
			self.crossout_nodata_but.setText("no data then cross out")
			self.crossout_nodata_but.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(100,200,255)}')
			self.wscene.set_nodata_mode(crossout=True)
			#self.wscene.updatedevcolors()
		else:
			self.crossout_nodata_but.setText("no data then blank out")
			self.crossout_nodata_but.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(0,120,255)}')
			self.wscene.set_nodata_mode(crossout=False)
			#self.wscene.updatedevcolors()
########################################################################################################################
# user clicked to have waferview sent to clipboard
	def __send_to_clipboard(self):
		clipb=QtWidgets.QApplication.clipboard()
		#imagemap=QtGui.QPixmap.grabWidget(self.waferview) # Qt4
		imagemap=QtWidgets.QWidget.grab(self.waferview)    # Qt5
		clipb.setPixmap(imagemap)