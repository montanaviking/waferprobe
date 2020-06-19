__author__ = 'viking'
# wafer graph actions test
epsfloat=1E-12          # used to define smallest difference between floats. Used to compare floating-point numbers. If abs(f1-f2)<epsfloat then f1 is considered to be equal to f2 where f1, f2 are floating point values
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtGui import QPainterPath, QPainter, QPaintEvent, QBrush, QColor
from PyQt5.QtCore import QObject, pyqtSignal,Qt, QRectF
from waferplot import Ui_Dialog
import numpy as np
from utilities import formatnum, is_number
import scipy.stats as s
import collections as col

##########################################################################################################################
# view class for wafer map
class WaferView(QtWidgets.QGraphicsView):
	ResizeView=QtCore.pyqtSignal()
	#ResizeDataLabelFont=QtCore.pyqtSignal(float)
	def __init__(self,parent=None):
		super(WaferView,self).__init__()
		self.setMouseTracking(True)
		self.scalefactor=1.
	def wheelEvent(self, ew):
		eps=1E-3
		factor =1.+ew.angleDelta().y()/600
		#print("from line 26 wafergraph_scene_view_items.py factor,ew ",factor,ew.angleDelta().x(),ew.angleDelta().y())
		if factor<eps: factor=eps
		#factor =1.+ ew.delta()/1200
		#factor =1.+ ew.delta()/600         # delta is obsolete in Qt5
		self.scalefactor*=factor
		#print("total scalefactor is ",self.scalefactor)
		if self.scalefactor<0.01:
			self.scalefactor=self.scalefactor/factor
			factor=1.
		if self.scalefactor>500.:
			self.scalefactor=self.scalefactor/factor
			factor=1.
		mods = QtWidgets.QApplication.keyboardModifiers()
		if mods!=QtCore.Qt.ShiftModifier: self.scale(factor,factor)         # change zoom on wafermap scene

		else:       # shrink or grow datalabels
			self.scene().scaledatafont(factor)
		return ew.accept()

	def resizeEvent(self,er):                   # emit resize event to allow child scene to fill the frame
		#self.scalefactor=1.
		#self.ResizeView.emit()
		return er.accept()

	def mousePressEvent(self, e):
		QtWidgets.QGraphicsView.mousePressEvent(self,e)
#############################################################################################################################
# scene for wafer graph
# data is a dictionary data[devicenames][parameters] which gives the values of all measured parameters for each device - devicenames
# allparameters is a list of all the parameters measured - which relieves us from finding all these parameters from the dictionary data
class sw(QtWidgets.QGraphicsScene):
	DeviceClicked=QtCore.pyqtSignal(QtWidgets.QGraphicsRectItem,str,float)              # signal for selection of device to show in list on wafer map
	DeviceSelectedforAnalysis=QtCore.pyqtSignal(str)                                # signal for selection of device for analysis on wafer map
	VisibleLevelsChanged=QtCore.pyqtSignal()
	DataUpdate=QtCore.pyqtSignal()                 # signal to devices to update data due to change in data
	UpdateDevColors=QtCore.pyqtSignal()             # signal to devices to color due to change in data - this signal MUST always be emitted AFTER DataUpdate
	ResizeDataLabelFont=QtCore.pyqtSignal(float)        # signal to devices to change font size of data value
	UserSetMinMaxColorScale=QtCore.pyqtSignal(float,float)      # this signal, from the user, sets the wafermap color scale to that other than the default of the minimum and maximum visible data (mindata,maxdata)
	def __init__(self, parent=None):
		super(sw,self).__init__(parent)
		self.dragmodeon=False
		self.crossoutifnodata=True
		self.visible_levels=[0]            # wafer levels which will be visible - set default to the first level i.e. 0
		if parent!=None:                    # fit scene to view if parent view resizes
			self.view=parent
			self.view.ResizeView.connect(self.fitinview)
		# if data!=None: self.set_wafer_data(data=data)
		# else:
		self.data=None                      # must use method set_wafer_data() to set this scene's device data
		self.hierachial_device_names_lists=None # list of wafer devices' (level=0) names, which are broken into lists i.e. list of lists. Each wafer device name forms a list
												# which is derived from the device name as: self.hierachial_device_names_lists[i]=devicename.split('_') so self.hierachial_device_names_lists is a list of lists
												# self.hierachial_device_names_lists is set via method set_wafer_data()
		self.alldataparameters=None

	# set how devices which don't have data are treated - i.e. select either cross out device or don't show device at all
	# this is called from actions_wafergraph.py when the user changes the crossout status
	def set_nodata_mode(self,crossout=True):
		self.crossoutifnodata=crossout
		self.updatedevcolors()
	# set which levels are to be visible in the wafermap. Visible levels have their device data displayed (if it exists)
	def set_levels_visible(self,visible_levels=None):
		self.visible_levels=visible_levels
		self.updatedevcolors()         # notify wafermap items that the visible levels have changed

	# set data parameter type to be displayed on the wafermap
	def set_datatypedisplayed(self,parameter=None):     # parameter is the data type to be displayed
		if self.alldataparameters!=None and (parameter not in self.alldataparameters):   raise ValueError("ERROR! have data but selected parameter not measured")
		else:
			self.displayedparametertype=parameter
		self.DataUpdate.emit()                    # notify items in wafermap that the data type (parameter) displayed has changed and send along the new parameter
		self.updatedevcolors()               # update device colors to reflect data change - MUST ALWAYS follow self.DataUpdate.emit()

	# pass a data dictionary to the wafer and notify all items in the wafer scene
	# self.mindata is a dictionary of the form: {'parameter1':parameter1 minimum value, 'parameter2': parameter2 minimum value, .....}
	# self.maxdata is a dictionary of the form: {'parameter1':parameter1 maximum value, 'parameter2': parameter2 maximum value, .....}
############################################################################################
# set the wafer scene's data for devices
#
	def set_wafer_data(self,data=None,parameter=None,parameters=None,logscale=False):
		if data!=None and (type(data) is dict or len(data)>0):
			if hasattr(self,'data'): del self.data
			self.data=data
			self.logscale=logscale                   # if False, then data colors on device items in this scene are set according to a linear data scale and averages of child data are the simple, linear means. If True, then color is set to a logarithmic scale and the averages of child data are the geometric mean
			if parameter!=None: self.displayedparametertype=parameter
			self.alldataparameters = list(set([p[i] for p in [list(data[x].keys()) for x in data] for i in range(len(p))]))             # finds all the data parameters measured in this wafer
			if parameters!=None: self.alldataparameters=parameters          # set the list of parameters measured if provided
			self.hierarchical_device_names_lists=[devname.split('_') for devname in data]   # now set a list of lists formed from the list of device names																	# (at level=0) of all the devices whose data are to be displayed on the wafermap
		else:
			self.data=None
			self.alldataparameters=None
		self.DataUpdate.emit()                             # notify items in wafermap that we have fresh data
		self.updatedevcolors()                              # update device colors to reflect data change - MUST ALWAYS follow self.DataUpdate.emit()

	# deviceaction() method is called from devices within this scene when an item (which signifies a device) in this scene is clicked
	def deviceaction(self,deviceitem=None,devicename=None,devicedata=None): # emit signal for all children devices to report their data Children call this scene method when they are clicked
		deviceitem.deviceselect(True)                                              # highlight the clicked device
		if devicedata!=None: self.DeviceClicked.emit(deviceitem,devicename,devicedata)
		else: self.DeviceClicked.emit(deviceitem,devicename,-1E50)                            # signal captured by self.listdevicesclicked in actions_wafergraph.py

	# deviceaction() method is called from devices within this scene when an item (which signifies a device) in this scene is clicked for analysis
	def deviceaction_foranalysis(self, deviceitem=None, devicename=None, devicedata=None):  # emit signal for all children devices to report their data Children call this scene method when they are clicked
		deviceitem.devicetoanalyze(True)  # hghlight the clicked device
		self.DeviceSelectedforAnalysis.emit(devicename)                         # signal captured by self.addtodevicestoanalyze in actions_wafergraph.py

	def deselectalldevices(self):                           # deselects (unhighlights) all items selected for the wafermap device listing, i.e. devices in this scene
		for deviceitem in self.items():
			if deviceitem.is_deviceitem():
				deviceitem.deviceselect(False)

	def deselectdevicestoanalyze(self):                           # deselects (unhighlights) all items, i.e. devices in this scene and removes all devices from analysis list
		for deviceitem in self.items():
			if deviceitem.is_deviceitem():
				deviceitem.devicetoanalyze(False)

	def fitinview(self):
		#self.parent().fitInView(self.sceneRect(),Qt.IgnoreAspectRatio)
		self.parent().fitInView(self.sceneRect(),Qt.KeepAspectRatio)

	def mousePressEvent(self,e):
		QtWidgets.QGraphicsScene.mousePressEvent(self,e)
		if e.button()==QtCore.Qt.LeftButton: self.view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
		else: self.view.setDragMode(0)
		return e.ignore()

	def mouseReleaseEvent(self,em):
		QtWidgets.QGraphicsScene.mouseReleaseEvent(self,em)
		if em.button()==QtCore.Qt.LeftButton:
			self.view.setDragMode(0)
		return em.ignore()

##########################################################
# find min and max values for each device level
# This MUST follow a call to self.DataUpdate.emit() which will ensure that all the items in this scene will have fresh data
	def updatedevcolors(self):
		if self.visible_levels==None or len(self.visible_levels)<1: raise ValueError("ERROR! no visible layers specified")
		if self.logscale==False:                # using linear scale
			try: self.mindatalevel={level:min([devitem.devdata for devitem in self.items() if devitem.is_deviceitem() and devitem.level==level and is_number(devitem.devdata)])  for level in self.visible_levels}             # get minimums of data for each VISIBLE device level in the mask hierarchy
			except: self.mindatalevel={level:0.  for level in self.visible_levels}                                                                                                                  # insufficient data
			try: self.maxdatalevel={level:max([devitem.devdata for devitem in self.items() if devitem.is_deviceitem() and devitem.level==level and is_number(devitem.devdata)])  for level in self.visible_levels}             # get maximums of data for each VISIBLE device level in the mask hierarchy
			except: self.maxdatalevel={level:1.  for level in self.visible_levels}           # insufficient data
		else:                                   #using log scale
			try: self.mindatalevel={level:min(np.log10(np.abs([devitem.devdata for devitem in self.items() if devitem.is_deviceitem() and devitem.level==level and is_number(devitem.devdata)])))  for level in self.visible_levels}             # get minimums of data for each VISIBLE device level in the mask hierarchy
			except: self.mindatalevel={level:-1.  for level in self.visible_levels}                                                                                                                  # insufficient data
			try: self.maxdatalevel={level:max(np.log10(np.abs([devitem.devdata for devitem in self.items() if devitem.is_deviceitem() and devitem.level==level and is_number(devitem.devdata)])))  for level in self.visible_levels}             # get maximums of data for each VISIBLE device level in the mask hierarchy
			except: self.maxdatalevel={level:1.  for level in self.visible_levels}           # insufficient data
		#maxdataalllevels=max(self.maxdatalevel[])
		self.UpdateDevColors.emit()
################################################################
# change font size on data values in devices
	def scaledatafont(self,factor=1.):
		self.ResizeDataLabelFont.emit(factor)
#############
# change the color scale from the default to user-selected values
	def user_set_min_max_datascale(self,mindata=0,maxdata=1.):
		self.UserSetMinMaxColorScale.emit(mindata,maxdata)              # inform devices in scene that we are setting the color scale
##############################################################################################################################################################################################

########################################################################################################################
# this is a device rectangle. Can be a device or a reticle or possibly (in the future) a group of die
# mouseclick signals from the device rectangle item are sent outward via the parent scene
# origin is one of 'lowerright', upperright lowerleft and upperleft
# a specific call can prevent the above for a clear, see-through item
# data are set by the setdevdata() method
# When no value is specified, in the call to setdata() the item takes its data as the average of all its children's data.
# A call to setdevdata('clear') forces the item to have data=None and be clear
# the level parameter specifies the wafer level of the device e.g. level=0 is specifies the individual measured devices while level>0 are divisions
# of the wafer
# Devices which are childless get their data from the data dictionary provided by the scene
class DeviceRect(QtWidgets.QGraphicsRectItem):
	def __init__(self, brushstyle=None,loc_wafer=None, posX=0., posY=0.,level=None,width=None, height=None, devicename=None, origin='lowerleft',parent=None,setscene=None):
		super(DeviceRect,self).__init__(parent)
		self.setParentItem(parent)              # pass along parent setting to parent
		self.setscene=setscene                  # this allows us to set the parent scene a-priori before adding item to the scene
		self.devdata=None
		self.is_visible=True                    # is the device set to be visible on the wafer map?
		self.is_measured=True                   # was the device measured i.e. not specifically excluded from measurement?
		self.is_bad=False                       # are data missing because the device failed either initial test or during test?
		self.level=level                        # wafer level - specified only for the highest level considered and overridden if have parent
		# DeviceRect control signals from parent scene
		self.setscene.VisibleLevelsChanged.connect(self.showcolors)               # scene has gotten a signal to change its visible level configuration
		self.setscene.DataUpdate.connect(self.setdevdata)                              # scene has refreshed data
		self.setscene.UpdateDevColors.connect(self.showcolors)                   # update colors signal connection
		self.setscene.ResizeDataLabelFont.connect(self.changedatalabelfontsize)
		self.setscene.UserSetMinMaxColorScale.connect(self.usersetminmaxcolorscale)
		##########
		self.fillbrush=QBrush()
		self.pen=QtGui.QPen()                   # setup pen for item
		self.pen.setCosmetic(True)              # adjust pen width (for width != 0) to be same on screen regardless of zoom scaling
		self.isselected=False                  # controls selection of item
		self.isselectedforanalysis=False        # controls selection of item for analysis
		if loc_wafer==None: raise ValueError("ERROR! device does not have valid wafer location")
		self.loc_wafer=loc_wafer                # these are the device's wafer coordinates where self.loc_wafer['X'] is the probed X-location, self.loc_wafer['actualX'] the X location of the actual device and similarly for
												# self.loc_wafer['Y'] and self.loc_wafer['actualY']
		#self.logscale=False                     # if False, then data color is set according to a linear data scale and averages of child data are the simple, linear means. If True, then color is set to a logarithmic scale and the averages of child data are the geometric mean
		# transform coordinates
		if self.parentItem()!=None:        # have parent and this item is a sub item of a parent item
			#rect=parent.boundingRect()
			if origin=='lowerleft':
				posY=self.parentItem().rect().height()-posY-height
			if origin=='upperright':
				posX=self.parentItem().rect().width()-posX-width
			if origin=='lowerright':
				posX=self.parentItem().rect().width()-posX-width
				posY=self.parentItem().rect().height()-posY-height
			self.setRect(self.parentItem().rect().left(),self.parentItem().rect().top(),width,height)
			self.setPos(posX,posY)                          # set X and Y position relative to the parent's origin
			if self.parentItem().level!=None: self.level=self.parentItem().level-1            # override wafer level to set to parent's - 1 if parent exists
		else:               # no parent but has parent scene this is a base item
			if origin=='lowerleft':
				posY=-posY-height
			if origin=='upperright':
				posX=-posX-width
			if origin=='lowerright':
				posX=-posX-width
				posY=-posY-height
			self.setRect(posX,posY,width,height)
		if self.level==None or self.level<0: raise ValueError("ERROR! specified wafer level is invalid")

		self.devicename=devicename
		# now find location of the device (or device group) on the wafer
		self.scenebr=self.mapToScene(self.rect())
		self.setAcceptHoverEvents(True)
		self.color=QColor(0,0,0,0)      # set transparent since no color was specified
		self.fillbrush.setColor(self.color)

		if brushstyle!=None:
			self.brush().setStyle(brushstyle)
		else:
			self.brush().setStyle(Qt.SolidPattern)            # the default is a solid color
			self.setBrush(self.fillbrush)
		self.minsetdatalevel=None                       # minimum value of the user-set data
		self.maxsetdatalevel=None                       # maximum value of the user-set data
#######################################################################
# method to set the device item's data and consequently its color
# Calling this method with no arguments sets the items data value to be that of the average of its children
# color is set to clear if the device is set to not visible
# datatype is the data parameter to be displayed
# finds data average or geometric means of the selected device by averaging over children
	def setdevdatatreeaverage(self):
		if self==None: return
		if hasattr(self.setscene,'data') and self.setscene.data!=None and (self.devicename in self.setscene.data):                                           # if the devicename is of a measured device, then display this data
			if self.setscene.displayedparametertype in self.setscene.data[self.devicename]:                       # has this parameter been measured or calculated for this device?
				self.devdata=self.setscene.data[self.devicename][self.setscene.displayedparametertype]            # set data to the that of the device (self.device) and the parameter (datatype) to be displayed if the parameter has been measured for this device
			else: self.devdata=None                                                                                 # This parameter has not been measured for this device
		elif (self.childItems()!=None and self.level>0 and len(self.childItems())>0):   # No measured data so are there children? If so, set data value according to average of all children's values because this device is not an actual measured device, but rather represents a grouping of devices such as a
			for child in self.childItems(): # first recursively set values for all children based on their childrens' value settings and so on
				if hasattr(child,'setdevdata') and child.level==self.level-1: child.setdevdata()                    # update all children's data
			childdatalist=[child.devdata for child in self.childItems() if child.is_deviceitem() and child.level==self.level-1 and child.devdata!=None and is_number(child.devdata)]
			if len(childdatalist)>0 and self.setscene.logscale==True:
				self.devdata=s.mstats.gmean(np.abs(childdatalist))              # set this item's value to the geometric mean of the absolute value of all children's values
			elif len(childdatalist)>0 and self.setscene.logscale==False:
				self.devdata=np.average(childdatalist)                          # set this item's value to the arithmetic mean of all children's values
			else: self.devdata=None
		else: self.devdata=None
######################################################################
#######################################################################
# method to set the device item's data and consequently its color
# Calling this method with no arguments sets the items data value to be that of the average of its children
# color is set to clear if the device is set to not visible
# datatype is the data parameter to be displayed
# finds selected data averages or geometric means of all single individual devices under the item under consideration
	def setdevdata(self):
		if self==None: return
		if hasattr(self.setscene,'data') and self.setscene.data!=None and (self.devicename in self.setscene.data):                                           # if the devicename is of a measured device, then display this data
			if self.setscene.displayedparametertype in self.setscene.data[self.devicename]:                       # has this parameter been measured or calculated for this device?
				self.devdata=self.setscene.data[self.devicename][self.setscene.displayedparametertype]            # set data to the that of the device (self.device) and the parameter (datatype) to be displayed if the parameter has been measured for this device
			else: self.devdata=None                                                                                 # This parameter has not been measured for this device
		elif (self.childItems()!=None and self.level>0 and len(self.childItems())>0):   # No measured data so are there children? If so, set data value according to average of all children's values because this device is not an actual measured device, but rather represents a grouping of devices such as a
			for child in self.childItems():         # first recursively set values for all children based on their childrens' value settings and so on
				if hasattr(child,'setdevdata') and child.level==self.level-1: child.setdevdata()                    # update all children's data
			# self.devicename is the name of the current device under consideration. Need to find all individual devices at level=0 which are under the current device under consideration. If a level=0 device is under the
			# current device, self.devicename will be a subset of the level=0 device's name
			decendantdatalistlevel0=[self.setscene.data[d][self.setscene.displayedparametertype] for d in self.setscene.data.keys() if self.devicename.split('_')==d.split('_')[:len(self.devicename.split('_'))] and self.setscene.displayedparametertype in self.setscene.data[d]]       # get list of the data of the selected parameter for all level0 i.e. individual devices, which are under the device under consideration
			if self.setscene.logscale==True and len(decendantdatalistlevel0)>0:
				self.devdata=s.mstats.gmean(np.abs(decendantdatalistlevel0))              # set this item's value to the geometric mean of the absolute value of all children's values
			elif self.setscene.logscale==False and len(decendantdatalistlevel0)>0:
				self.devdata=np.average(decendantdatalistlevel0)                          # set this item's value to the arithmetic mean of all children's values
			else: self.devdata=None
		else: self.devdata=None
######################################################################

######################################################################
# this method sets color if level is visible otherwise it sets the color to clear
# colors are scaled according to the instantiation of the SpectralColorMap() min and max data values in the definition of class clmap
	def showcolors(self):
		if self==None:
			#print("from line 261 in wafergraph_scene_view_items.py self=None")
			return
		if not hasattr(self.setscene,'displayedparametertype') or self.setscene.displayedparametertype==None: raise ValueError("ERROR! No parameter has been set to display")
		# is this scene visible?
		if self.setscene.alldataparameters!=None and (self.setscene is None or self.setscene.visible_levels is None or self.level in self.setscene.visible_levels):
			 self.is_visible=True
		else: self.is_visible=False
		if self.is_visible==True: self.setAcceptHoverEvents(True)
		else:
			self.setAcceptHoverEvents(False)
			if hasattr(self,'cross0'):
				self.setscene.removeItem(self.cross0)
				del self.cross0
			if hasattr(self,'datavaluelable'):
				self.setscene.removeItem(self.datavaluelabel)
				del self.datavaluelabel
			if hasattr(self,'cross1'):
				self.setscene.removeItem(self.cross1)
				del self.cross1
			if hasattr(self,'datavaluelabel'):
				self.setscene.removeItem(self.datavaluelabel)
				del self.datavaluelabel
		if self.is_visible and hasattr(self,'devdata') and is_number(self.devdata):                                       # then we have real data so set color accordingly
			#clmap=MonoColorMap(min=self.setscene.mindata[self.setscene.displayedparametertype],max=self.setscene.maxdata[self.setscene.displayedparametertype])     # set up colormap giving minimum and maximum data on the wafer. self.setscene.displayedparametertype is the parameter type to be displayed
			# mindatasib=min([devitem.devdata for devitem in self.setscene.items() if devitem.level==self.level and is_number(devitem.devdata)])                # get minimum of data for all sibling devices (all devices at this device's level)
			# maxdatasib=max([devitem.devdata for devitem in self.setscene.items() if devitem.level==self.level and is_number(devitem.devdata)])                # get minimum of data for all sibling devices (all devices at this device's level)
			#clmap=MonoColorMap(min=mindatasib,max=maxdatasib)     # set up colormap giving minimum and maximum data on the wafer. self.setscene.displayedparametertype is the parameter type to be displayed
			#clmap=MonoColorMap(minv=self.setscene.mindatalevel[self.level],maxv=self.setscene.maxdatalevel[self.level],logscale=self.setscene.logscale)     # set up colormap giving minimum and maximum data on the wafer at this level. self.setscene.displayedparametertype is the parameter type to be displayed. For log plots,

			#clmap=SpectralColorMap(min=self.setscene.mindatalevel[self.level],max=self.setscene.maxdatalevel[self.level],logplot=self.setscene.logscale)
			if self.minsetdatalevel==None or self.maxsetdatalevel==None:
				clmap=InvertSpectralColorMap(min=self.setscene.mindatalevel[self.level],max=self.setscene.maxdatalevel[self.level],logplot=self.setscene.logscale)
			else:
				self.minsetdatalevel=min(self.setscene.mindatalevel[self.level],self.minsetdatalevel)
				self.maxsetdatalevel=max(self.setscene.maxdatalevel[self.level],self.maxsetdatalevel)
				#print("from line 313 in wafergraph_scene_view_items.py ",self.minsetdatalevel)
				clmap=InvertSpectralColorMap(min=self.minsetdatalevel,max=self.maxsetdatalevel,logplot=self.setscene.logscale)
			#print("from wafergraph_scene_view_items.py line 300 self.devdata=",self.devdata)
			self.color=clmap.setvalue(value=self.devdata)

			if hasattr(self,'cross0'):      # remove cross-out, if any, which indicates no data for this item
				self.setscene.removeItem(self.cross0)
				del self.cross0
			if hasattr(self,'cross1'):      # remove cross-out, if any, which indicates no data for this item
				self.setscene.removeItem(self.cross1)
				del self.cross1
			self.setBrush(QColor(self.color))
			if hasattr(self,'datavaluelabel'):      # clear data label prior to setting with possibly new values
				self.setscene.removeItem(self.datavaluelabel)        # remove data value from item
				del self.datavaluelabel

			textcolor=Qt.black
			if self.color.value()<220: textcolor=Qt.white           # adjust text colors so as to maximize text contrast with background color
			elif self.color.hue()>210 and self.color.hue()<270: textcolor=Qt.white

			self.datavaluelabel=DataValueText(parent=self,data=self.devdata,textcolor=textcolor)        # now add data value text to this graphics item

		else:           # have no data
			#crossline1=line(self.pos)
			#self.color=QColor(0,0,0,0)                              # no numerical data available so set clear
			#self.setBrush(Qt.gray)
			#self.setBrush(QColor(Qt.lightGray))
			#if self.is_visible: self.setBrush(QColor(Qt.lightGray))
			if self.setscene.crossoutifnodata==True:                # if crossout option is selected to signify no data for the device then draw a cross through the device
				if self.is_visible and not hasattr(self,'cross0'):
					self.cross0=CrossOut(parent=self,cross=0)
					self.setBrush(QColor(Qt.white))
				if self.is_visible and not hasattr(self,'cross1'):
					self.cross1=CrossOut(parent=self,cross=1)
					self.setBrush(QColor(Qt.white))
			else:                                                   # just blank the device if we have no data
				#self.deviceselect(False)  # deselect device (item) if it's not visible
				#self.pen.setStyle(Qt.NoPen)
				self.is_visible=False
				self.is_selected=False
				self.setBrush(QBrush(Qt.BrushStyle(Qt.NoBrush)))
				if hasattr(self, 'cross0'):
					self.setscene.removeItem(self.cross0)
					del self.cross0
				if hasattr(self, 'cross1'):
					self.setscene.removeItem(self.cross1)
					del self.cross1
			#self.setBrush(QBrush(Qt.BrushStyle(Qt.DiagCrossPattern)))
			#self.setBrush(QBrush(Qt.BrushStyle(Qt.Dense7Pattern)))
			if hasattr(self,'datavaluelabel'):
				self.setscene.removeItem(self.datavaluelabel)        # remove data value from item
				del self.datavaluelabel
			self.deviceselect(False)                                # deselect device if there are no data
		if not self.is_visible:
			self.pen.setStyle(Qt.NoPen)
			self.setPen(self.pen)
			self.deviceselect(False)                                # deselect device (item) if it's not visible
			self.setBrush(QBrush(Qt.BrushStyle(Qt.NoBrush)))
			if hasattr(self,'datavaluelabel'):
				self.setscene.removeItem(self.datavaluelabel)        # remove data value from item
				del self.datavaluelabel
		else:
			self.deviceselect(self.isselected)                      # color device outline to reflect selection status
			self.pen.setStyle(Qt.SolidLine)
#####################################################################
# Highlight device for printout of device  parameters in wafer plot window
	def deviceselect(self,deviceselected):
		if deviceselected:                      # device selected to display parameters in table
			self.pen.setStyle(Qt.SolidLine)
			self.pen.setWidth(5)
			self.pen.setColor(QColor(Qt.red))
			self.setPen(self.pen)
			self.isselected=True
			if self.isselectedforanalysis:      # device is also selected for analysis
				self.pen.setStyle(Qt.SolidLine)
				self.pen.setWidth(5)
				self.pen.setColor(QColor(Qt.magenta))
				self.setPen(self.pen)
		elif self.isselectedforanalysis:                               # device not selected for list but is selected for analysis
			self.pen.setStyle(Qt.SolidLine)
			self.pen.setWidth(5)
			self.pen.setColor(QColor(Qt.blue))
			self.setPen(self.pen)
			self.isselected=False
		else:                                                          # device selected for neither display parameters nor for analysis
			if self.is_visible: self.pen.setStyle(Qt.SolidLine)
			else: self.pen.setStyle(Qt.NoPen)
			self.pen.setWidth(0)
			self.pen.setColor(QColor(Qt.black))
			self.setPen(self.pen)
			self.isselected=False
#####################################################################
#####################################################################
# Highlight device for printout of device  parameters in wafer plot window
	def devicetoanalyze(self, deviceselected):
		if deviceselected == True:                  # device is selected for analysis
			self.pen.setStyle(Qt.SolidLine)
			self.pen.setWidth(5)
			self.pen.setColor(QColor(Qt.blue))
			self.setPen(self.pen)
			self.isselectedforanalysis = True
			if self.isselected:                     # device is also selected for display of parameters in table
				self.pen.setStyle(Qt.SolidLine)
				self.pen.setWidth(5)
				self.pen.setColor(QColor(Qt.magenta))
				self.setPen(self.pen)
				#print("from line 363 in wafergraph_scene_view_items.py magenta",self.devicename)
		elif self.isselected:                       # device only selected for display of parameters in table
			self.pen.setStyle(Qt.SolidLine)
			self.pen.setWidth(5)
			self.pen.setColor(QColor(Qt.red))
			self.setPen(self.pen)
			self.isselectedforanalysis=False
		else:                                       # device selected for neither display parameters nor for analysis
			if self.is_visible: self.pen.setStyle(Qt.SolidLine)
			else: self.pen.setStyle(Qt.NoPen)
			self.pen.setWidth(0)
			self.pen.setColor(QColor(Qt.black))
			self.setPen(self.pen)
			self.isselectedforanalysis = False
		#####################################################################
# type of this graphics item
	def is_deviceitem(self):
		 return True
#####################################################################
	### handle mouse click events to the device item.
	### signals are sent to the parent scene to be then broadcast with the item's name and data value - if data exist
	def mousePressEvent(self, e):
		QtWidgets.QGraphicsItem.mousePressEvent(self,e)
		kmod = QtWidgets.QApplication.keyboardModifiers()
		scene = self.scene()
		if self.is_visible and scene is not None and e.button()==QtCore.Qt.RightButton:
			if  kmod!=QtCore.Qt.ControlModifier:
				scene.deviceaction(deviceitem=self,devicename=self.devicename,devicedata=self.devdata)   # make the parent scene emit the devicename and data to allow one to, for instance, open a menu of actions (e.g. plotting) on the selected device
				return e.accept()
			else:
				scene.deviceaction_foranalysis(deviceitem=self,devicename=self.devicename)      # make the parent scene emit the devicename and device to allow adding selecting which device get analyzed
				return e.accept()
		return e.ignore()
######################################################################
# provide readout of data when we hover over a device item
	def hoverEnterEvent(self,e):
		kmod = QtWidgets.QApplication.keyboardModifiers()
		QtWidgets.QGraphicsItem.hoverEnterEvent(self,e)
		scene=self.scene()

		self.setToolTip('')
		if scene is not None:
			if self.is_visible==False: return e.accept()
			if is_number(self.devdata) and kmod!=QtCore.Qt.ShiftModifier:           # then show value
				self.setToolTip(self.devicename+" Datatype "+scene.displayedparametertype+" Value="+formatnum(self.devdata,precision=2))
			elif kmod!=QtCore.Qt.ShiftModifier: self.setToolTip(self.devicename+" Datatype "+scene.displayedparametertype+" No Data")

			if kmod==QtCore.Qt.ShiftModifier:                                       # then show device location
				if self.devicename in scene.data:                                   # are we at the individual device level?
					x=scene.data[self.devicename]['X']
					y=scene.data[self.devicename]['Y']
				else:
					x=self.loc_wafer['actualX']                                     # actual X location of device group in wafer coordinates
					y=self.loc_wafer['actualY']                                     # actual Y location of device group in wafer coordinates
				self.setToolTip("Location (" + formatnum(x, type='int') + "," + formatnum(y, type='int') + ")")
			return e.accept()
		else: return e.accept()
#######################################################################################################################################################
	def changedatalabelfontsize(self,fontscale):
		if hasattr(self,'datavaluelabel'):
			newpointsize=fontscale*self.datavaluelabel.font().pointSize()
			valuefont=QtGui.QFont()
			valuefont.setPointSize(newpointsize)
			self.datavaluelabel.setFont(valuefont)
		else: return
###############################################################
# allow user to change data values associated with minimum and maximum data colorscale for visible items
	def usersetminmaxcolorscale(self,mindata=None,maxdata=None):
		self.minsetdatalevel=mindata
		self.maxsetdatalevel=maxdata
		self.showcolors()               # must call this to update item color
#######################################################################################################################################################
# draw an X through a device to indicate either a lack of data (perhaps bad device) or that the device was excluded from the measurement
#
class CrossOut(QtWidgets.QGraphicsLineItem):
	def __init__(self, parent=None,cross=0):
		super(CrossOut,self).__init__(parent)
		self.setParentItem(parent)
		self.pen=QtGui.QPen()                   # setup pen for item
		self.pen.setCosmetic(True)              # adjust pen width (for width != 0) to be same on screen regardless of zoom scaling
		if cross==0:
			x0=self.parentItem().rect().left()
			y0=self.parentItem().rect().top()
			x1=self.parentItem().rect().right()
			y1=self.parentItem().rect().bottom()
		else:
			x0=self.parentItem().rect().left()
			y0=self.parentItem().rect().bottom()
			x1=self.parentItem().rect().right()
			y1=self.parentItem().rect().top()
		self.pen.setStyle(Qt.DotLine)
		self.pen.setWidth(1)
		self.pen.setColor(QColor(Qt.red))
		self.setPen(self.pen)
		self.setLine(x0,y0,x1,y1)
# type of this graphics item. This is NOT a device in the wafermap, so do not highlight or unhighlight
	def is_deviceitem(self):
		 return False
#######################################################################################################################################################
# label devices with numeric values of their data
#
class DataValueText(QtWidgets.QGraphicsTextItem):
	def __init__(self, parent=None,data=None,textcolor=Qt.black):
		super(DataValueText,self).__init__(parent)
		width=self.parentItem().rect().width()          # width of parent device item this text is being printed in
		height=self.parentItem().rect().height()        # height of parent device item this text is being printed in
		left=self.parentItem().rect().left()            # left side of parent device item this text is being printed in
		bottom=self.parentItem().rect().bottom()        # bottom side of parent device item this text is being printed in
		top=self.parentItem().rect().top()              # top side of parent device item this text is being printed in


		self.setParentItem(parent)
		self.setPlainText(formatnum(data,precision=2))
		self.setDefaultTextColor(QColor(textcolor))
		valuefont=QtGui.QFont()
		#print("from wafergraph_scene_view_items.py width,height = ",width,height)       #debug
		if width>=0.8*height:
			self.setTextWidth(width)
			self.setPos(left,top+0.2*height)
			pointsizel=0.15*width
			pointsizeh=0.6*height
			pointsize=min(pointsizel,pointsizeh)
			valuefont.setPointSize(pointsize)
			self.setRotation(0.)
		else:
			self.setTextWidth(height)
			self.setPos(left,bottom)
			pointsizel=0.15*height
			pointsizeh=0.6*width
			pointsize=min(pointsizel,pointsizeh)
			valuefont.setPointSize(pointsize)
			self.setRotation(-90.)
		self.setFont(valuefont)
# type of this graphics item. This is NOT a device in the wafermap, so do not highlight or unhighlight
	def is_deviceitem(self):
		 return False
#####################################################################

	# dummy functions to prevent errors when items are called under scene
	# def deviceselect(self,deviceselected): return False             #dummy function
	# def deselectalldevices(self): return
#######################################################################################################################################################
# map a value to a color to generate a colormap
# values are normalized to a 0 - 1 scale
#
class SpectralColorMap(QColor):
	def __init__(self,min=0.,max=1.,logplot=False):
		super(SpectralColorMap,self).__init__()
		self.__minhue=0.
		self.__maxhue=270
		self.__minlum=0
		self.__maxlum=255
		self.__minsat=0
		self.__maxsat=255

		self.__lowerramp=0.1      # luminance setting for color is ramped from zero to maximum for the hue setting from zero to 0.2 the (self.__maxhue-self.__minhue) i.e. the hue range
		self.__upperramp=0.7      # saturation setting for color is ramped from zero to maximum for the hue setting from self_upperramp to 1. the (self.__maxhue-self.__minhue) i.e. the hue range
		self.__logplot=logplot
			# find the color mapping
		if min>max: raise ValueError("ERROR! maximum value must be > minimum value!")
		self.__min=min
		self.__max=max

	def setvalue(self,value=None):
	# def setcolor(self,colorindex,minrange,maxrange):
	#     # first scale to
		if value==None: raise ValueError("ERROR! Must specify a value!")
		if abs(self.__max-self.__min)>epsfloat:                     # prevent divide by zero
			if not self.__logplot: # then this is a linear plot
				self.__valuenorm=(value-self.__min)/(self.__max-self.__min)         # normalize values to all fall between 0. and 1.
			else:
				if value<=0.: raise ValueError("ERROR! Log value input must be >0.!")
				self.__valuenorm=(np.log10(value)-self.__min)/(self.__max-self.__min)       # For log scales the self.__min and self.__max are the exponents to power of 10 for the minimum and maximum limits respectively
		else:
			self.__valuenorm=0.5                                # if the minimum and maximum value of data are equal, then set the color to midway between the extremes - prevents divide by zero

		if self.__valuenorm>1.: self.__valuenorm=1.
		if self.__valuenorm<0.: self.__valuenorm=0.

		# set lower part of scale
		if self.__valuenorm<self.__lowerramp:   # then we are ramping
			self.__value_hue=self.__minhue
			self.__value_lum=self.__maxlum*self.__valuenorm/self.__lowerramp
			self.__value_sat=self.__maxsat
		elif self.__valuenorm>=self.__lowerramp and self.__valuenorm<=self.__upperramp:
			self.__value_hue=self.__minhue+(self.__maxhue-self.__minhue)*(self.__valuenorm-self.__lowerramp)/(self.__upperramp-self.__lowerramp)   # set hue
			self.__value_lum=self.__maxlum
			self.__value_sat=self.__maxsat
		elif self.__valuenorm>self.__upperramp:
			self.__value_hue=self.__maxhue
			self.__value_lum=self.__maxlum
			self.__value_sat=self.__maxsat*(1-(self.__valuenorm-self.__upperramp)/(1.-self.__upperramp))
		#print(self.__value_hue,self.__value_sat,self.__value_lum)
		colorm=QColor()
		colorm.setHsv(self.__value_hue,self.__value_sat,self.__value_lum)
		#print("color =",colorm)
		return colorm
#######################################################################################################################################################
#######################################################################################################################################################
# map a value to a color to generate a colormap with black blue as lowest scale and red violet, white as highest scale
# values are normalized to a 0 - 1 scale
#
class InvertSpectralColorMap(QColor):
	def __init__(self,min=0.,max=1.,logplot=False):
		super(InvertSpectralColorMap,self).__init__()
		self.__minhue=40.
		self.__maxhue=240
		#self.__maxhue=280
		self.__minlum=30
		self.__maxlum=255
		self.__minsat=100
		self.__maxsat=220

		self.__lowerramp=0.1      # luminance setting for color is ramped from zero to maximum for the hue setting from zero to 0.2 the (self.__maxhue-self.__minhue) i.e. the hue range
		self.__upperramp=0.7      # saturation setting for color is ramped from zero to maximum for the hue setting from self_upperramp to 1. the (self.__maxhue-self.__minhue) i.e. the hue range
		self.__logplot=logplot
			# find the color mapping
		if min>max: raise ValueError("ERROR! maximum value must be > minimum value!")
		self.__min=min
		self.__max=max

	def setvalue(self,value=None):
	# def setcolor(self,colorindex,minrange,maxrange):
	#     # first scale to
		if value==None: raise ValueError("ERROR! Must specify a value!")
		if abs(self.__max-self.__min)>epsfloat:                     # prevent divide by zero
			if not self.__logplot: # then this is a linear plot
				self.__valuenorm=(value-self.__min)/(self.__max-self.__min)         # normalize values to all fall between 0. and 1.
			else:
				if value<=0.: raise ValueError("ERROR! Log value input must be >0.!")
				self.__valuenorm=(np.log10(value)-self.__min)/(self.__max-self.__min)       # For log scales the self.__min and self.__max are the exponents to power of 10 for the minimum and maximum limits respectively
		else:
			self.__valuenorm=0.5                                # if the minimum and maximum value of data are equal, then set the color to midway between the extremes - prevents divide by zero

		if self.__valuenorm>1.: self.__valuenorm=1.
		if self.__valuenorm<0.: self.__valuenorm=0.

		# set lower part of scale
		# if self.__valuenorm<self.__lowerramp:   # then we are ramping
		# 	self.__value_hue=self.__maxhue
		# 	self.__value_lum=self.__maxlum*self.__valuenorm/self.__lowerramp
		# 	self.__value_sat=self.__maxsat
		# elif self.__valuenorm>=self.__lowerramp and self.__valuenorm<=self.__upperramp:
		# 	self.__value_hue=self.__maxhue-(self.__maxhue-self.__minhue)*(self.__valuenorm-self.__lowerramp)/(self.__upperramp-self.__lowerramp)   # set hue
		# 	self.__value_lum=self.__maxlum
		# 	self.__value_sat=self.__maxsat
		# elif self.__valuenorm>self.__upperramp:
		# 	self.__value_hue=self.__minhue
		# 	self.__value_lum=self.__maxlum
		# 	self.__value_sat=self.__maxsat*(1-(self.__valuenorm-self.__upperramp)/(1.-self.__upperramp))

		self.__value_lum=(self.__maxlum-self.__minlum)*self.__valuenorm+self.__minlum
		self.__value_hue=self.__maxhue-(self.__maxhue-self.__minhue)*self.__valuenorm
		#self.__value_hue=(self.__maxhue-self.__minhue)*self.__valuenorm+self.__minhue
		self.__value_sat=self.__maxsat-(self.__maxsat-self.__minsat)*self.__valuenorm
		#print(self.__value_hue,self.__value_sat,self.__value_lum)
		colorm=QColor()
		colorm.setHsv(self.__value_hue,self.__value_sat,self.__value_lum)
		print("from line 789 in wafergraph_scene_view_items.py color, valuenorm =",self.__value_hue,self.__value_sat,self.__value_lum,self.__valuenorm) #
		return colorm
#######################################################################################################################################################
# map a value to a color to generate a colormap
# values are normalized to a 0 - 1 scale
#
class MonoColorMap(QColor):
	def __init__(self,minv=0.,maxv=1.,logscale=False):
		super(MonoColorMap,self).__init__()
		self.__minhue=0.
		self.__maxhue=20.
		self.__minlum=20
		self.__maxlum=255
		self.__midlum=150
		self.__minsat=20
		self.__maxsat=255
		self.__midsat=100

		#self.__value_lum=self.__maxlum
		#self.__value_sat=self.__maxsat
		self.__lowerramp=0.2      # luminance setting for color is ramped from zero to maximum for the hue setting from zero to 0.2 the (self.__maxhue-self.__minhue) i.e. the hue range
		self.__upperramp=0.8      # saturation setting for color is ramped from zero to maximum for the hue setting from self_upperramp to 1. the (self.__maxhue-self.__minhue) i.e. the hue range
		self.__logscale=logscale
			# find the color mapping
		if minv>maxv: raise ValueError("ERROR! maximum value must be > minimum value!")
		if abs(maxv-minv)/(abs(maxv)+abs(minv))<1E-20:
			maxv=minv+1E-10*abs(maxv+minv)
		self.__min=minv
		self.__max=maxv

	def setvalue(self,value=None):
	# def setcolor(self,colorindex,minrange,maxrange):
	#     # first scale to
		if value==None: raise ValueError("ERROR! Must specify a value!")
		if not self.__logscale: # then this is a linear plot
			self.__valuenorm=(value-self.__min)/(self.__max-self.__min)                 # normalize values to all fall between 0. and 1.
		else:
			self.__valuenorm=(np.log10(value)-self.__min)/(self.__max-self.__min)       # For log scales the self.__min and self.__max are the exponents to power of 10 for the minimum and maximum limits respectively
		if self.__valuenorm>1.: self.__valuenorm=1.
		if self.__valuenorm<0.: self.__valuenorm=0.

		# calculate color
		# set lower part of scale
		if self.__valuenorm<self.__lowerramp:   # then we are ramping
			self.__value_lum=self.__minlum+(self.__midlum-self.__minlum)*self.__valuenorm/self.__lowerramp
			self.__value_sat=self.__maxsat-(self.__maxsat-self.__midsat)*self.__valuenorm/self.__lowerramp
		elif self.__valuenorm>=self.__lowerramp and self.__valuenorm<=self.__upperramp:
			self.__value_lum=self.__midlum
			self.__value_sat=self.__midsat
		elif self.__valuenorm>self.__upperramp:
			self.__value_lum=self.__midlum+(self.__maxlum-self.__midlum)*(self.__valuenorm-self.__upperramp)/(1.-self.__upperramp)
			self.__value_sat=self.__midsat-(self.__midsat-self.__minsat)*(self.__valuenorm-self.__upperramp)/(1.-self.__upperramp)

		self.__value_hue=(self.__valuenorm*(self.__maxhue-self.__minhue) )+self.__minhue
		#self.__value_lum=(self.__valuenorm*(self.__maxlum-self.__minlum) )+self.__minlum
		self.__value_sat=self.__maxsat-(self.__valuenorm*(self.__maxsat-self.__minsat) )
		#print("from wafergraph_scene_view_items.py line 356",self.__value_hue,self.__value_sat,self.__value_lum)
		colorm=QColor()
		try: self.__value_lum       #debug
		except:
			print("min,max",self.__min,self.__max)
			print("valuenorm", self.__lowerramp,self.__valuenorm)
		colorm.setHsv(self.__value_hue,self.__value_sat,self.__value_lum)
		#print("color =",colorm)
		return colorm