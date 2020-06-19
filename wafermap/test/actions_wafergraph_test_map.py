__author__ = 'viking'
# wafer graph actions test
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QPainterPath, QPainter, QPaintEvent, QBrush, QColor, QGraphicsRectItem
from PyQt4.QtCore import QObject, pyqtSignal,Qt, QRectF
from waferplot import Ui_Dialog
import numpy as np
from utilities import formatnum
import collections as col
from read_testplan import *                             # this gives the wafer map structure
from wafergraph_scene_view_items import *


class WaferGraph(Ui_Dialog,QtGui.QGraphicsView):
	def __init__(self,parent=None):
		super(WaferGraph,self).__init__()
		self.setupUi(self)



		plandir = "/home/viking/test/T56/T56meas4"
		planname = "T56meas4_plan.csv"
		# plandir = "/home/viking/phil@carbonicsinc.com/07. Measurements/H43/H43MQ2SQ4meas5"
		# planname = "H43MQ2SQ4meas5_plan.csv"

		self.tp=TestPlan(plandir,planname)

		self.masklevels.itemClicked.connect(self.changedmaxmasklevelshown)			# enble user to change the maximum masklevel displayed
		self.masklevels.blockSignals(True)
		self.masklevels.clear()
		self.masklevels.addItems([str(i) for i in range(0,len(self.tp.leveldev))])				# add all available levels to selector
		self.masklevels.blockSignals(False)

		self.measurementtype.currentIndexChanged.connect(self.changedmeasurementtype)		# enable user to change the data type displayed
		self.measurementtype.blockSignals(True)
		self.measurementtype.clear()
		self.measurementtype.addItems(['|Idmax|','On-Off Ratio'])							# add all available data types to selector
		self.measurementtype.blockSignals(False)


											 # reticle level
		wafersizeX=self.tp.sectionsize_map_level()['X']
		wafersizeY=self.tp.sectionsize_map_level()['Y']
		self.wafergraph=WaferView()
		self.wafermapcontainer.addWidget(self.wafergraph)
		self.wscene=sw(parent=self.wafergraph)
		self.wafergraph.setSceneRect(-wafersizeX,wafersizeY,3*wafersizeX,-3*wafersizeY)            # set extents of wafer
		self.wafergraph.setScene(self.wscene)
		self.wscene.set_wafer_data()
		#testdata={'child device1':{'|Idmax|':0.5,'On-Off Ratio':20},'child device2':{'|Idmax|':2.0,'On-Off Ratio':40}}
		# set up wafer and its base scene
		self.maxdevlevel=len(self.tp.leveldev)



		self.wscene.set_levels_visible(visible_levels=[0,1])
		self.wscene.set_datatypedisplayed("|Idmax|")


		testdata={self.tp.wafername+'_R1_C1_Q3_DV1_TLM0.5':{'|Idmax|':0.5,'On-Off Ratio':20},self.tp.wafername+'_R1_C1_Q3_DV1_TLM0.4':{'|Idmax|':2.0,'On-Off Ratio':40},self.tp.wafername+'_R1_C1_Q3_DV1_TLM0.6':{'|Idmax|':3.0},self.tp.wafername+'_R1_C1_Q3_DV1_TLM1.2':{'|Idmax|':5.0}}


		self.wscene.set_wafer_data(data=testdata)
		self.addsites(level=len(self.tp.leveldev)-1)


########################################################################################################################################
# populate wafer map with all devices
# self.tp is the test plan of the wafer which is a class containing information on current position, devicename, and level under consideration in the wafer map
# self.maxdevlevel is the maximum level which is populated with devices - usually the reticle level
# output is self.dev[ilevel][devicename] which is a dictionary of devices
	def addsites(self,level=0,parent=None):
		#dev=[]
		donelevel=False
		while not donelevel:
			if level<self.maxdevlevel:                              # create a device only at the highest device level (usually the reticle level) and below
				xsize=self.tp.devicesize_map_level(level=level)['X']
				ysize=self.tp.devicesize_map_level(level=level)['Y']
				xloc=self.tp.tpx[level][self.tp.leveldev[level]]
				yloc=self.tp.tpy[level][self.tp.leveldev[level]]
				dev=DeviceRect(posX=xloc,posY=yloc,width=xsize,height=ysize,devicename="".join([self.tp.wafername,self.tp.devicename_map_level(level=level)]),level=level,parent=parent,setscene=self.wscene)     # make device
				#dev.append(DeviceRect(posX=xloc,posY=yloc,width=xsize,height=ysize,devicename=self.tp.devicename_map_level(level=level),parent=parent,setscene=setscene))     # make device
				if level>0:
					chs=self.addsites(level=level-1,parent=dev)['status']                                  # add children devices recursively
					if chs['donelevel']: s=self.tp.movenextsite_within_map_level(level=level)											# if the child level is done, then attempt to move to the next device
				else: s=self.tp.movenextsite_within_map_level(level=0)                                                                                 # we are at the lowest level
			donelevel=s['donelevel']
			if parent==None: self.wscene.addItem(dev)
		return {'device':dev,'status':s}
	# emitted signal to widgets that the type of data displayed on the wafer map has been changed

	########################################################################################################################################
# set maximum masklevel displayed
	def changedmaxmasklevelshown(self):
		selitems=self.masklevels.selectedItems()
		self.wscene.set_levels_visible(visible_levels=[int(item.text()) for item in selitems])
########################################################################################################################################
########################################################################################################################################
# set maximum masklevel displayed
	def changedmeasurementtype(self):
		print(self.measurementtype.currentText())
		self.wscene.set_datatypedisplayed(self.measurementtype.currentText())
########################################################################################################################################