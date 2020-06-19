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

        self.wafergraph=WaferView()
        self.horizontalLayout.addWidget(self.wafergraph)
        self.wscene=sw(parent=self.wafergraph)

       # clmap = MonoColorMap()

        #colorrect=clmap.setvalue(value=0.95)

        testdata={'child device1':{'|Idmax|':0.5,'On-Off Ratio':20},'child device2':{'|Idmax|':2.0,'On-Off Ratio':40}}
        #testdata=None

        colorchild=QColor()
        colorchild.setHsv(100,100,100)

        self.wafergraph.setSceneRect(0,0,30000,-30000)
        self.wafergraph.setScene(self.wscene)
        self.wscene.set_wafer_data()
        #self.wscene.set_wafer_data(data=testdata)
        self.wscene.set_datatypedisplayed("|Idmax|")
        #self.wscene.set_levels_visible(visible_levels=[0])
        #print("actions_wafergraph.py",self.wscene.bottom(),self.wscene.top())
        #quit()
        imax=50
        for ii in range(0,imax):
            # devr=DeviceRect(posX=100*ii, posY=100*ii, width=50, height=50, color=clmap.setvalue(value=ii/imax),
            #                 devicename="device " + formatnum(ii, type='int'))
            # cr=DeviceRect(posX=2, posY=10, width=5, height=10, color=colorchild, devicename=" child device ", parent=devr)
            devr=DeviceRect(posX=100*ii, posY=100*ii, width=50, height=50, level=2,devicename="device " + formatnum(ii, type='int'),setscene=self.wscene)
            cr=DeviceRect(posX=2, posY=10, width=5, height=10, devicename="child device1", parent=devr,setscene=self.wscene)
            #cr.setdevdata()
            cr=DeviceRect(posX=10, posY=10, width=5, height=10, devicename="child device2", parent=devr,setscene=self.wscene)
            #cr.setdevdata()
            cr=DeviceRect(posX=3, posY=3, width=2, height=5, devicename="child device3", parent=cr,setscene=self.wscene)
            #cr.setdevdata()
            #devr.setdevdata(ii/imax)
            self.wscene.addItem(devr)
            devr.setdevdata()

        self.wscene.DeviceClicked.connect(self.deviceclicked)
        self.wscene.set_levels_visible(visible_levels=[0,1,2])
    def deviceclicked(self,dev):
        print("device clicked gives ",dev)


########################################################################################################################################
