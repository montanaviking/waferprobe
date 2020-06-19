# actions for slider
__author__='viking'
# from PyQt4 import QtCore, QtGui
# from PyQt4.QtGui import QPainterPath, QPainter, QPaintEvent, QBrush, QColor, QGraphicsRectItem
# from PyQt4.QtCore import QObject, pyqtSignal,Qt, QRectF
from slider import Ui_slidertest
from slider_scale import *
#import numpy as np
from utilities import *
#import collections as col

class Slider(Ui_slidertest,QtWidgets.QGraphicsView):
	def __init__(self,parent=None):
		super(Slider,self).__init__(parent)
		self.setupUi(self)
		self.sliderview=SliderView()
		self.sliderview.setAcceptDrops(True)

		#self.sliderview.setFixedSize(100,100)

		#self.sliderview.setFixedSize(20,50)
		#self.sliderview.setSceneRect(0,0,20,50)

		# self.sliderview.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		# self.sliderview.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

		#self.viewport(100,100)
		#self.setMinimumSize(100,100)
		self.sliderview.setAcceptDrops(True)
		self.slidercontainer.addWidget(self.sliderview)

		self.sliderscene=SliderScene(parent=self.sliderview)


		self.sliderview.setScene(self.sliderscene)
		self.sliderlow=SliderLow(parent=self,scene=self.sliderscene)
		self.sliderscene.addItem(self.sliderlow)
		self.sliderhigh=SliderHigh(parent=self,scene=self.sliderscene)
		self.sliderscene.addItem(self.sliderhigh)
		print("scene items", self.sliderscene.items())
		#self.sliderscene.setSceneRect(self.sliderscene.itemsBoundingRect())
		self.sliderscene.setSceneRect(0,-10,self.sliderscene.Xphysicalfullscale,self.sliderscene.Yphysicalfullscale+20)
		#print(self.sliderscene.itemsBoundingRect())

		#self.sliderview.fitInView(0,0,20,50)
		#self.sliderview.scale(0.1,0.1)
		#self.sliderview.fitInView(self.sliderscene.itemsBoundingRect())
