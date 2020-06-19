__author__ = 'viking'
# wafer graph actions test
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QPainterPath, QPainter, QPaintEvent, QBrush, QColor, QGraphicsRectItem
from PyQt4.QtCore import QObject, pyqtSignal,Qt, QRectF
from waferplot import Ui_Dialog
import numpy as np
from utilities import formatnum
import collections as col

class WaferGraph(Ui_Dialog,QtGui.QGraphicsView):
    def __init__(self,parent=None):
        super(WaferGraph,self).__init__()
        self.setupUi(self)

        self.wafergraph=WaferView()
        self.horizontalLayout.addWidget(self.wafergraph)
        self.wscene=sw(parent=self.wafergraph)

        #clmap = SpectralColorMap()
        clmap = MonoColorMap()
        #colorchild = QColor()
        #colorchild.setHsv(49.99999999999998, 255, 255)
        # colorrect= QColor().setHsv(50,100,200)
        # colorrect.setHsv(50,100,200)

        # colorchild=clmap.setvalue(value=0.1)
        # print("colorchild",colorchild)
        colorrect=clmap.setvalue(value=0.95)


        # self.itemrect2= DeviceRect(posX=200,posY=200,width=90,height=90,color=colorrect,dev="device2")
        #
        #
        # self.it1 = DeviceRect(posX=20.,posY=10,width=50,height=50,color=colorchild,dev="devchild",parent=self.itemrect2)
        # self.it2 = DeviceRect(posX=5.,posY=5,width=20,height=20,color=clmap.setvalue(value=0.95),dev="devchild2",parent=self.it1)
        #self.wscene.addItem(self.itemrect2)
        #self.wafergraph.passscene(self.wscene)
        colorchild=QColor()
        colorchild.setHsv(100,100,100)

        self.wafergraph.setSceneRect(0,0,30000,-30000)
        self.wafergraph.setScene(self.wscene)
        #print("actions_wafergraph.py",self.wscene.bottom(),self.wscene.top())
        #quit()
        imax=50
        for ii in range(0,imax):
            # devr=DeviceRect(posX=100*ii, posY=100*ii, width=50, height=50, color=clmap.setvalue(value=ii/imax),
            #                 devicename="device " + formatnum(ii, type='int'))
            # cr=DeviceRect(posX=2, posY=10, width=5, height=10, color=colorchild, devicename=" child device ", parent=devr)
            devr=DeviceRect(posX=100*ii, posY=100*ii, width=50, height=50, devicename="device " + formatnum(ii, type='int'))
            cr=DeviceRect(posX=2, posY=10, width=5, height=10, devicename=" child device ", parent=devr)
            cr.setdevdata(ii/(imax))
            cr=DeviceRect(posX=10, posY=10, width=5, height=10, devicename=" child device2 ", parent=devr)
            cr.setdevdata(ii/(imax))
            #devr.setdevdata(ii/imax)
            devr.setdevdata('clear')

            self.wscene.addItem(devr)
        self.wscene.DeviceClicked.connect(self.deviceclicked)
    def deviceclicked(self,dev):
        print("device clicked gives ",dev)

class WaferView(QtGui.QGraphicsView):
    ResizeView=QtCore.pyqtSignal()
    def __init__(self,parent=None):
        super(WaferView,self).__init__()
        self.setMouseTracking(True)

    def wheelEvent(self, ew):
        factor =1.+ ew.delta()/12000

        # if factor<0.1:self.factor=0.1
        # if factor>5. :self.factor=5.
        self.scale(factor,factor)
        #print(factor,self.transform().m11())
        return ew.accept()

    def resizeEvent(self,er):                   # emit resize event to allow child scene to fill the frame
        self.ResizeView.emit()
        return er.accept()

    def mousePressEvent(self, e):
        QtGui.QGraphicsView.mousePressEvent(self,e)

class sw(QtGui.QGraphicsScene):
    DeviceClicked=QtCore.pyqtSignal(str,float)
    def __init__(self, parent=None):
        super(sw,self).__init__(parent)
        self.dragmodeon=False
        if parent!=None:                    # fit scene to view if parent view resizes
            self.view=parent
            self.view.ResizeView.connect(self.fitinview)
            #self.view.passscene(self)       # pass scene parameters to view to allow resizing
        #print("view is", self.view)
    def deviceaction(self,devicename=None,devicedata=None):
        #self.devicename=devicename           # device name from device rectangle
        self.DeviceClicked.emit(devicename,devicedata)
    def fitinview(self):
        self.parent().fitInView(self.sceneRect(),Qt.IgnoreAspectRatio)

    def mousePressEvent(self,e):
        QtGui.QGraphicsScene.mousePressEvent(self,e)
        if e.button()==QtCore.Qt.LeftButton: self.view.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        else: self.view.setDragMode(0)
            #return e.accept()
        return e.ignore()

    def mouseReleaseEvent(self,em):
        QtGui.QGraphicsScene.mouseReleaseEvent(self,em)
        if em.button()==QtCore.Qt.LeftButton:
            self.view.setDragMode(0)
        return em.ignore()
########################################################################################################################
# this is a device rectangle. Can be a device or a reticle
# class DeviceRect(QtGui.QGraphicsObject):
#     DeviceRightClicked=QtCore.pyqtSignal()
#     def __init__(self,color=None,brushstyle=None,posX=0.,posY=0.,width=None,height=None,dev=None,origin='lowerleft',parent=None):
#         # transform coordinates
#         if parent!=None:        # have parent and this item is a sub item of a parent item
#             #rect=parent.boundingRect()
#             # if origin=='lowerleft':
#             #     posY=parent.rect.height()-posY-height
#             # if origin=='upperright':
#             #     posX=parent.rect.width()-posX-width
#             # if origin=='lowerright':
#             #     posX=parent.rect.width()-posX-width
#             #     posY=parent.rect.height()-posY-height
#             # print("actions_wafergraph.py line 113",parent.rect.rect())
#             # self.setRect(parent.rect().left(),parent.rect().top())
#             # #self.rect=QGraphicsRectItem(parent.rect.rect().left(),parent.rect.rect().top(),width,height)
#             super(DeviceRect,self).__init__()
#             self.setPos(posX,posY)                          # set X and Y position relative to the parent's origin
#             #print('from actions_wafergraph.py line 117 ',parent.rect.rect().right())
#         else:       # no parent, this is a base item
#             # if origin=='lowerleft':
#             #     posY=-posY-height
#             # if origin=='upperright':
#             #     posX=-posX-width
#             # if origin=='lowerright':
#             #     posX=-posX-width
#             #     posY=-posY-height
#             super(DeviceRect,self).__init__()
#             self.setPos(posX,posY)
#
#         self.dev=dev
#         #self.rect=rect
#         #penst=Qt.PenStyle = 5
#         # pen = QtGui.QPen()
#         # pen.setWidth(0)
#
#         # self.setPen(pen)
#         # self.setBrush(QBrush(color))
#         self.setAcceptHoverEvents(True)
#
#         #self.setToolTip(self.dev)
#
#         # if brushstyle!=None:
#         #     self.brush().setStyle(brushstyle)
#         # else: self.brush().setStyle(Qt.SolidPattern)            # the default is a solid color
#         #self.setPen(Qt.NoPen)
#
#         #self.mclick=QtCore.pyqtSignal()
#     def mousePressEvent(self, e):
#         QtGui.QGraphicsItem.mousePressEvent(self,e)
#         if e.button()==QtCore.Qt.RightButton:
#             print("mouse pressed", e.scenePos().x(),e.scenePos().y(),self.dev)
#             self.DeviceRightClicked.emit(self.dev)
#             return e.accept()
#         if e.button()!=QtCore.Qt.RightButton: return e.ignore()
#
#     def hoverEnterEvent(self,e):
#         self.setToolTip(self.dev)
#         return e.accept()
#     def paint(self, painter, option, widget=None):
#         pen=QtGui.QPen()
#         pen.setWidth(0)
#         painter.setPen(pen)
#######################################################################################################################################################
# ########################################################################################################################
# # this is a device rectangle. Can be a device or a reticle
# class DeviceRect(QtGui.QGraphicsRectItem,QtGui.QGraphicsObject):
#     DeviceRightClicked=QtCore.pyqtSignal()
#     def __init__(self,color=None,brushstyle=None,posX=0.,posY=0.,width=None,height=None,dev=None,origin='lowerleft',parent=None):
#         # transform coordinates
#         if parent!=None:        # have parent and this item is a sub item of a parent item
#             #rect=parent.boundingRect()
#             if origin=='lowerleft':
#                 posY=parent.rect.height()-posY-height
#             if origin=='upperright':
#                 posX=parent.rect.width()-posX-width
#             if origin=='lowerright':
#                 posX=parent.rect.width()-posX-width
#                 posY=parent.rect.height()-posY-height
#
#             self.rect=QRectF(parent.rect.left(),parent.rect.top(),width,height)
#             super(DeviceRect,self).__init__(self.rect,parent)
#             self.setPos(posX,posY)                          # set X and Y position relative to the parent's origin
#             print('from actions_wafergraph.py line 118 ',parent.rect.right(),self.sceneBoundingRect().height())
#         else:       # no parent, this is a base item
#             if origin=='lowerleft':
#                 posY=-posY-height
#             if origin=='upperright':
#                 posX=-posX-width
#             if origin=='lowerright':
#                 posX=-posX-width
#                 posY=-posY-height
#             self.rect=QRectF(posX,posY,width,height)
#             super(DeviceRect,self).__init__(self.rect)
#         self.dev=dev
#         #self.rect=rect
#         #penst=Qt.PenStyle = 5
#         pen = QtGui.QPen()
#         pen.setWidth(0)
#
#         self.setPen(pen)
#         #self.setPen(pen)
#         self.setBrush(QBrush(color))
#         self.setAcceptHoverEvents(True)
#         #self.setToolTip(self.dev)
#
#         if brushstyle!=None:
#             self.brush().setStyle(brushstyle)
#         else: self.brush().setStyle(Qt.SolidPattern)            # the default is a solid color
#         #self.setPen(Qt.NoPen)
#
#         #self.mclick=QtCore.pyqtSignal()
#     def mousePressEvent(self, e):
#         QtGui.QGraphicsItem.mousePressEvent(self,e)
#         if e.button()==QtCore.Qt.RightButton:
#             print("mouse pressed", e.scenePos().x(),e.scenePos().y(),self.dev)
#             self.DeviceRightClicked.emit(self.dev)
#             return e.accept()
#         if e.button()!=QtCore.Qt.RightButton: return e.ignore()
#
#     def hoverEnterEvent(self,e):
#         self.setToolTip(self.dev)
#         return e.accept()
#######################################################################################################################################################
########################################################################################################################
# this is a device rectangle. Can be a device or a reticle
# mouseclick signals are sent via the calling scene
# origin is one of 'lowerright', upperright lowerleft and upperleft
# instantiations of this class maintain a list of children
# data
class DeviceRect(QtGui.QGraphicsRectItem):
    def __init__(self, brushstyle=None, posX=0., posY=0., width=None, height=None, devicename=None, origin='lowerleft',parent=None):
        super(DeviceRect,self).__init__(parent)
        self.setParentItem(parent)              # pass along parent setting to parent
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
            #if self not in parent.child: parent.child.append(self)                       # append this child to parent's children list but only if it's not already in the parent
            #print('from actions_wafergraph.py line 118 ',parent.rect().right(),self.sceneBoundingRect().height())
        else:               # no parent but has parent scene this is a base item
            if origin=='lowerleft':
                posY=-posY-height
            if origin=='upperright':
                posX=-posX-width
            if origin=='lowerright':
                posX=-posX-width
                posY=-posY-height
            self.setRect(posX,posY,width,height)
        #self.devicename="".join([parent.devicename,'_',devicename])
        pen = QtGui.QPen()
        pen.setWidth(0)
        self.setPen(pen)

        self.devicename=devicename
        self.setAcceptHoverEvents(True)
        self.color=QColor(0,0,0,0)      # set transparent since no color was specified
        self.setBrush(QBrush(self.color))
        if brushstyle!=None:
            self.brush().setStyle(brushstyle)
        else: self.brush().setStyle(Qt.SolidPattern)            # the default is a solid color

    def setdevdata(self,devdata=None):
        if devdata!=None: self.devdata=devdata                                  # we should use the given devdata value if it's given
        elif devdata=='clear': self.devdata='clear'
        elif devdata==None and self.childItems()!=None and len(self.childItems())>0:                           # if no devdata are given AND there are children, set value according to average of all children's values
            {child.setdevdata() for child in self.childItems() if hasattr(child,'setdevdata') }                   # first recursively set values for all children based on their childrens' value settings
            self.devdata=np.average([child.devdata for child in self.childItems() if hasattr(child,'devdata') and child.devdata!=None])         # set this item's value to the average of all children's values
        if hasattr(self,'devdata') and self.devdata!='clear':                   # then we have real data so set color accordingly
            clmap=MonoColorMap()
            self.color=clmap.setvalue(value=self.devdata)
        else:   self.color=QColor(0,0,0,0)                              # no data available so set clear
        self.setBrush(QBrush(self.color))

    ### handle mouse click events
    def mousePressEvent(self, e):
        QtGui.QGraphicsItem.mousePressEvent(self,e)
        if e.button()==QtCore.Qt.RightButton:
            print("mouse pressed", e.scenePos().x(),e.scenePos().y(),self.devicename)
            #self.DeviceRightClicked.emit(self.dev)
            scene=self.scene()
            if scene is not None:
                scene.deviceaction(devicename=self.devicename,devicedata=self.devdata)
            return e.accept()
        if e.button()!=QtCore.Qt.RightButton: return e.ignore()

    def hoverEnterEvent(self,e):
        self.setToolTip(self.devicename)
        return e.accept()
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

        #self.__value_lum=self.__maxlum
        #self.__value_sat=self.__maxsat

        self.__lowerramp=0.1      # luminance setting for color is ramped from zero to maximum for the hue setting from zero to 0.2 the (self.__maxhue-self.__minhue) i.e. the hue range
        self.__upperramp=0.7      # saturation setting for color is ramped from zero to maximum for the hue setting from self_upperramp to 1. the (self.__maxhue-self.__minhue) i.e. the hue range
        self.__logplot=logplot
            # find the color mapping
        if min>=max: raise ValueError("ERROR! maximum value must be > minimum value!")
        self.__min=min
        self.__max=max

    def setvalue(self,value=None):
    # def setcolor(self,colorindex,minrange,maxrange):
    #     # first scale to
        if value==None: raise ValueError("ERROR! Must specify a value!")
        if not self.__logplot: # then this is a linear plot
            self.__valuenorm=(value-self.__min)/(self.__max-self.__min)         # normalize values to all fall between 0. and 1.
        else:
            if value<=0.: raise ValueError("ERROR! Log value input must be >0.!")
            self.__valuenorm=(np.log10(value)-self.__min)/(self.__max-self.__min)       # For log scales the self.__min and self.__max are the exponents to power of 10 for the minimum and maximum limits respectively
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
        print(self.__value_hue,self.__value_sat,self.__value_lum)
        colorm=QColor()
        colorm.setHsv(self.__value_hue,self.__value_sat,self.__value_lum)
        print("color =",colorm)
        return colorm
#######################################################################################################################################################
# map a value to a color to generate a colormap
# values are normalized to a 0 - 1 scale
#
class MonoColorMap(QColor):
    def __init__(self,min=0.,max=1.,logplot=False):
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
        self.__logplot=logplot
            # find the color mapping
        if min>=max: raise ValueError("ERROR! maximum value must be > minimum value!")
        self.__min=min
        self.__max=max

    def setvalue(self,value=None):
    # def setcolor(self,colorindex,minrange,maxrange):
    #     # first scale to
        if value==None: raise ValueError("ERROR! Must specify a value!")
        if not self.__logplot: # then this is a linear plot
            self.__valuenorm=(value-self.__min)/(self.__max-self.__min)         # normalize values to all fall between 0. and 1.
        else:
            if value<=0.: raise ValueError("ERROR! Log value input must be >0.!")
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
        print(self.__value_hue,self.__value_sat,self.__value_lum)
        colorm=QColor()
        colorm.setHsv(self.__value_hue,self.__value_sat,self.__value_lum)
        #print("color =",colorm)
        return colorm