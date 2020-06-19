# sets up the color scale for the wafermap
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtGui import QPainterPath, QPainter, QPaintEvent, QBrush, QColor
from PyQt5.QtCore import QObject, pyqtSignal,Qt, QRectF
from waferplot import Ui_Dialog
import numpy as np
from utilities import formatnum, is_number
import scipy.stats as s
import collections as col
from wafergraph_scene_view_items import DataValueText, InvertSpectralColorMap

from wafergraph_scene_view_items import SpectralColorMap, DataValueText
# view for wafer color scale map
class ColorScaleView(QtWidgets.QGraphicsView):
	ColorRectSelected=QtCore.pyqtSignal(QtWidgets.QGraphicsRectItem)
	ResizeView=QtCore.pyqtSignal()
	def __init__(self,parent=None):
		super(ColorScaleView,self).__init__()
		self.setMouseTracking(True)
		self.colorscalescene=ColorScaleScene()
		self.setScene(self.colorscalescene)

	def resizeEvent(self,er):                   # emit resize event to allow child scene to fill the frame
		return er.accept()
	def mousePressEvent(self, e):
		QtWidgets.QGraphicsView.mousePressEvent(self,e)

# scene for wafer color map

class ColorScaleScene(QtWidgets.QGraphicsScene):
	ColorScaleValueSelected=QtCore.pyqtSignal(float)                # signal to
	def __init__(self,parent=None):
		super(ColorScaleScene,self).__init__(parent)
		if parent!=None:                    # fit scene to view if parent view resizes
			self.view=parent
			self.view.ResizeView.connect(self.fitinview)

	def fitinview(self):
		self.parent().fitInView(self.sceneRect(),Qt.IgnoreAspectRatio)
# defines action when clicking a color rectangle
	def colorrectclicked(self,colorrectselected=None):
		self.ColorRectSelected.emit(colorrectselected)



class ColorScaleRect(QtWidgets.QGraphicsRectItem):
	def __init__(self, loc_wafer=None, devdata=None, posX=0., posY=0.,width=None, height=None, origin='lowerleft',parent=None,setscene=None):
		super(ColorScaleRect,self).__init__(parent)
		self.devdata=devdata
		self.setParentItem(parent)  # pass along parent setting to parent
		self.setscene = setscene  # this allows us to set the parent scene a-priori before adding item to the scene
		self.setscene.DataUpdate.connect(self.setdevdata)  # scene has refreshed data
		self.setscene.UserSetMinMaxColorScale.connect(self.usersetminmaxcolorscale)
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
		self.brush().setStyle(Qt.SolidPattern)  # the default is a solid color
		self.updatedata()
	def updatedata(self):
		clmap = InvertSpectralColorMap(min=self.setscene.mindatalevel[self.level], max=self.setscene.maxdatalevel[self.level], logplot=self.setscene.logscale)
		self.color = clmap.setvalue(value=self.devdata)