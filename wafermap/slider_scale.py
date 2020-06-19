### Phil Marsh Carbonics Inc
# slider scale for wafermap
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal,Qt, QRectF,QPoint
import numpy as np
from utilities import formatnum, is_number
import scipy.stats as s
import collections as col
from PyQt5.QtGui import QPainterPath, QPainter, QPaintEvent, QBrush, QColor, QPainterPath, QPainter, QPaintEvent
from PyQt5.QtWidgets import QGraphicsRectItem



##########################################################################################################################
# view class for wafer map
class SliderView(QtWidgets.QGraphicsView):
	ResizeView=QtCore.pyqtSignal()
	def __init__(self,parent=None):
		super(SliderView,self).__init__()
		self.setMouseTracking(True)

	def resizeEvent(self,er):                   # emit resize event to allow child scene to fill the frame
		#self.scalefactor=1.
		#self.ResizeView.emit()
		#self.fitInView(self.scene().itemsBoundingRect())
		#self.fitInView(0,0,20,50)
		self.fitInView(self.scene().sceneRect())
		return er.accept()

	def mousePressEvent(self, e):
		QtWidgets.QGraphicsView.mousePressEvent(self,e)
#############################################################################################################################

#############################################################################################################################
# scene for the slider
class SliderScene(QtWidgets.QGraphicsScene):
	#DeviceClicked=QtCore.pyqtSignal(QtWidgets.QGraphicsRectItem,str,float)
	DataUpdate=QtCore.pyqtSignal()                 # signal to devices to update data due to change in data
	UpdateDevColors=QtCore.pyqtSignal()             # signal to devices to color due to change in data - this signal MUST always be emitted AFTER DataUpdate
	def __init__(self, data=None,parent=None):
		super(SliderScene,self).__init__(parent)
		self.dragmodeon=True
		self.datamax=None
		self.datamin=None
		self.Yphysicalfullscale=100                 # fullscale physical Y
		self.Xphysicalfullscale=12                  # fullscale physical X
		self.logscale=False

		if parent!=None:                    # fit scene to view if parent view resizes
			self.view=parent
			#self.view.ResizeView.connect(self.fitinview)

	def set_data(self,data=None,logscale=False,minmaxset='min'):
		if minmaxset!='min' and minmaxset!='max': raise ValueError("ERROR! illegal value for minmaxset, must be min or max")
		if data!=None:
			if minmaxset=='min':
				self.datamin=data
			else:
				self.datamax=data

	def _setlogscale(self, logscale):
		self.logscale = logscale

	# sets the minimum and maximum data range
	def _setminmaxdata(self, datamin=None, datamax=None):
		self.datamin = datamin
		self.datamax = datamax

	def _translate_to_physical(self,data):
		if self.logscale == False:
			dataphysical=self.Yphysicalfullscale*(self.datamax-data)/(self.datamax-self.datamin)


##########################################################
# this is the high-side slider
class SliderHigh(QtWidgets.QGraphicsItem):
	def __init__(self,parent=None,scene=None):
		super(SliderHigh, self).__init__()
		self.setAcceptDrops(True)
		#self.setFlag(QGraphicsItem_GraphicsItemFlag=True)
		self.setFlag(self.ItemIsSelectable,True)
		self.setFlag(self.ItemIsMovable,True)
		self.setFlag(self.ItemSendsScenePositionChanges,True)
		self.setFlag(self.ItemSendsGeometryChanges,False)
		#self.setParentItem(parent)
		self.slidepolygon=QtGui.QPolygonF([QPoint(0,0),QPoint(10,0),QPoint(5,-6),QPoint(0,-6)])
		self.textbox=QRectF(1,-1,5,-3)
		self.parentscene=scene
		self.textvalue=GraphText(parent=self,posx=-3,posy=-7)
		self.textvalue.DoneEditing.connect(self.setValuefromText)
		self.parent=parent

	def paint(self, p, options, QWidget_widget=None):
		p.setPen(Qt.NoPen)
		p.setBrush(QBrush(Qt.blue,Qt.SolidPattern))
		p.drawPolygon(self.slidepolygon)
		p.setBrush(QBrush(Qt.white,Qt.SolidPattern))
		p.drawRect(self.textbox)

	def boundingRect(self):
		return QRectF(QPoint(-5,-5),QPoint(5,5))

	def shape(self):
		path=QPainterPath()
		path.addPolygon(self.slidepolygon)
		return path

	def mousePressEvent(self, e):
		QtWidgets.QGraphicsItem.mousePressEvent(self, e)

	def mouseMoveEvent(self, e):
		QtWidgets.QGraphicsItem.mouseMoveEvent(self, e)
		self.setPos(0, self.pos().y())
		if self.pos().y()<0: self.setPos(0,0)
		if self.pos().y()>20: self.setPos(0,20)
		#self.textvalue = formatnum(self.pos().y(), precision=2)
		self.textvalue.setValue(self.pos().y())
		self.scene().update()
		return e.ignore()

	def mouseReleaseEvent(self, em):
		QtWidgets.QGraphicsItem.mouseReleaseEvent(self, em)
		self.textvalue.setValue(self.pos().y())
		self.scene().update()
		return em.ignore()

	def setValuefromText(self,value):
		self.setPos(0.,value)

	##########################################################
	# this is the low-side slider
class SliderLow(QtWidgets.QGraphicsItem):
	def __init__(self,parent=None, scene=None):
		super(SliderLow, self).__init__()
		self.setAcceptDrops(True)
		# self.setFlag(QGraphicsItem_GraphicsItemFlag=True)
		self.setFlag(self.ItemIsSelectable, True)
		self.setFlag(self.ItemIsMovable, True)
		self.setFlag(self.ItemSendsScenePositionChanges, True)
		self.setFlag(self.ItemSendsGeometryChanges, False)
		# self.setParentItem(parent)
		self.slidepolygon = QtGui.QPolygonF([QPoint(0, 0), QPoint(10, 0), QPoint(5, 6), QPoint(0, 6)])
		self.textbox = QRectF(1, 1, 5, 3)
		self.parentscene = scene
		self.textvalue = GraphText(parent=self,posx=-3,posy=-2)
		self.textvalue.DoneEditing.connect(self.setValuefromText)
		self.parent = parent                      # this is the parent widget



	def paint(self, p, options, QWidget_widget=None):
		p.setPen(Qt.NoPen)
		p.setBrush(QBrush(Qt.red, Qt.SolidPattern))
		p.drawPolygon(self.slidepolygon)
		p.setBrush(QBrush(Qt.white, Qt.SolidPattern))
		p.drawRect(self.textbox)

	def boundingRect(self):
		return QRectF(QPoint(-10, -10), QPoint(10,10))

	def shape(self):
		path = QPainterPath()
		path.addPolygon(self.slidepolygon)
		return path

	def mousePressEvent(self, e):
		QtWidgets.QGraphicsItem.mousePressEvent(self, e)

	def mouseMoveEvent(self, e):
		QtWidgets.QGraphicsItem.mouseMoveEvent(self, e)
		otherslider = self.parent.sliderhigh  # other slider
		self.setPos(0, self.pos().y())                          # force mouse to move only in Y direction
		if self.pos().y() < 0: self.setPos(0, 0)
		if self.pos().y() > self.scene().Yphysicalfullscale: self.setPos(0, self.scene().Yphysicalfullscale)
		# self.textvalue = formatnum(self.pos().y(), precision=2)
		self.textvalue.setValue(self.pos().y())
		self.scene().update()
		return e.ignore()

	def mouseReleaseEvent(self, em):
		QtWidgets.QGraphicsItem.mouseReleaseEvent(self, em)
		self.textvalue.setValue(self.pos().y())
		self.scene().update()
		return em.ignore()

	def setValuefromText(self, value):
		self.setPos(0., value)




#################################################################################################################################################################
class GraphText(QtWidgets.QGraphicsTextItem):
	DoneEditing=QtCore.pyqtSignal(float)
	def __init__(self,parent=None,posx=0,posy=0):
		super(GraphText,self).__init__()
		self.setPlainText('13.1')
		self.value=None
		#self.textbox=textbox
		#print("textbox pos ",parent.pos().y(),self.textbox.y())
		self.setParentItem(parent)
		#self.setPos(parent.pos().x()-3,parent.pos().y()-2)
		self.setPos(parent.pos().x()+posx,parent.pos().y()+posy)
		self.setFlags(QtWidgets.QGraphicsItem.ItemIsSelectable | QtWidgets.QGraphicsItem.ItemIsFocusable)
		self.setTextInteractionFlags(Qt.TextEditable | Qt.TextEditorInteraction | Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
		f=QtGui.QFont()
		f.setPointSize(1)
		self.setFont(f)
		# cursor=QtGui.QTextCursor()
		#
		# self.setTextCursor(cursor)
		# cursor.movePosition(QtGui.QTextCursor.End)

	def mousePressEvent(self, e):
		return e.ignore()

	def keyReleaseEvent(self, e):
		if e.key()==Qt.Key_Return:
			text=self.toPlainText()
			self.setPlainText(text.replace('\n',''))
			if is_number(self.toPlainText()):		# set new value
				self.value=float(self.toPlainText())
				self.DoneEditing.emit(self.value)
				print("emit textchanged")
			else:			# restore former value
				self.setPlainText(formatnum(self.value,precision=2))

	def setValue(self,value):
		self.value=value
		self.setPlainText(formatnum(self.value, precision=2))