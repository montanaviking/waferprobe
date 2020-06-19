__author__ = 'viking'
# Custom device widget
# List devices in sorted format

from PyQt4 import QtCore, QtGui
import numpy as np
import collections as col
from devicefinder import Ui_BooleanFinder
from utilities import parse_rpn

#from datalisting import *
from utilities import formatnum, is_number
# note that the rows are in the format of data[ir][ic] where ir and ic are row and column indices respectively
# and headers[ic] are just a list of headers

class DevTable(QtGui.QTableWidget):
	VerticalHeaderClicked=QtCore.pyqtSignal(str,int)
	HorizontalHeaderClicked=QtCore.pyqtSignal(float,int)
	def __init__(self,parent=None,):
		super(DevTable,self).__init__(parent)

		self.setCursor(QtCore.Qt.WaitCursor)			# signal user that the program is working
		sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
		sizePolicy.setHorizontalStretch(9)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
		self.setSizePolicy(sizePolicy)
		self.setBaseSize(QtCore.QSize(0, 0))
		self.setMouseTracking(False)
		self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
		self.setProperty("showDropIndicator", False)
		self.setDragDropOverwriteMode(False)
		self.setDragDropMode(QtGui.QAbstractItemView.NoDragDrop)
		self.setAlternatingRowColors(True)

		self.horizontalHeader().setVisible(True)
		self.horizontalHeader().setCascadingSectionResizes(True)
		self.horizontalHeader().setDefaultSectionSize(140)
		self.horizontalHeader().setHighlightSections(False)
		self.horizontalHeader().setMinimumSectionSize(50)
		self.setSortingEnabled(False)
		#self.horizontalHeader().setSortIndicatorShown(True)
		self.horizontalHeader().setStretchLastSection(True)
		#self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
		self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
		self.horizontalHeader().setStretchLastSection(True)
		self.setColumnWidth(6,2000)

		self.verticalHeader().setVisible(False)
		self.verticalHeader().setCascadingSectionResizes(True)
		self.verticalHeader().setStretchLastSection(False)
		self.verticalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
		#self.setSortingEnabled(False)
		self.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
		self.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
		self.setSelectionBehavior(QtGui.QAbstractItemView.SelectColumns)
		#self.setFocusPolicy(QtCore.Qt.NoFocus)
		# top horizontal headers (column labels)
		self.hheaderview=QtGui.QHeaderView(QtCore.Qt.Horizontal)
		self.hheaderview.setClickable(True)
		self.hheaderview.sectionClicked.connect(self.sortitems)			# sort table or select columns to send to clipboard
		self.cellClicked.connect(self.vheadertext)						# get row header data if clicked column 0 or clear clipboard otherwise
		self.setHorizontalHeader(self.hheaderview)
		self.setAlternatingRowColors(True)
		# variable setups
		self.vheaders=None												# generally these are the device names
		self.hheaders=None												# usually the device parameters
		self.data=None													# device data data[d=device name][parameter (measured or calculated)] and data[d][p]=device data as specifed by the devicename=d and parameter name = parameter
		self.searchitems=""												# device name search)
		self.lastsortcolumn=1
		self.sortorder = 'ascending'
		self.lastsortorder='ascending'
	#self.setStyleSheet("QTableWidget::item:selected{background-color: palette(highlight); color: palette(highlightedText);};")
	##############################################################################################################################################################
	# set up this widget  necessary for promoted widgets
	# hheaders is the parameter type
	# vheaders is the device name
	# data is a dictionary of the format:
	# data[d=device name][parameter (measured or calculated)] and data[d][p]=device data as specifed by the devicename=d and parameter name = parameter
	# data does NOT include the device names as values (i.e.a parameter) because the device name is already the key for data.
	# However, the first value for hheaders MUST be a column label for the device names
	def setup(self,hheaders=None,vheaders=None,data=None):
		if hheaders==None: hheaders=self.hheaders						# use previous value for parameter headers if did not supply any values
		if vheaders==None: vheaders=self.vheaders						# use previous value for parameter headers if did not supply any values
		if data==None: data=self.data									# use previous value for parameter headers if did not supply any values

		if hheaders==None or data==None or vheaders==None: return
		self.clear()
		vheaders = [vh for vh in vheaders if vh in data.keys()]			# filter to ensure that no devicenames are called for that are not also in the data set data
		self.setColumnCount(len(hheaders))
		self.setRowCount(len(vheaders))
		# top horizontal headers (column labels)

		self.setHorizontalHeaderLabels(hheaders)
		# add data
		for ir in range(0,self.rowCount()):
			addeditem=sItem()
			addeditem.setText(vheaders[ir])
			self.setItem(ir,0,addeditem)						# the first column of data is the device name
			for ic in range(1,self.columnCount()):
				addeditem=sItem()
				if hheaders[ic] in data[vheaders[ir]] and is_number(formatnum(data[vheaders[ir]][hheaders[ic]],precision=2)): addeditem.setText(formatnum(data[vheaders[ir]][hheaders[ic]],precision=2))
				else:	addeditem.setText('no data')
				#print("from devtable.py line 89 ir,ic, add item",ir,ic,addeditem.text())
				self.setItem(ir,ic,addeditem)
		self.setCursor((QtCore.Qt.ArrowCursor))
		self.data=data
		self.vheaders=vheaders
		self.hheaders=hheaders
		self.selectedcolumns=col.deque()
		self.selectedcolumnheaders=col.deque()			# would contain the column labels of the selected columns
		self.coloredrow=[]					# indicates which rows are colored
		self.resizeColumnsToContents()
		self.resizeRowsToContents()
		# keep track of individual items highlighted for individual copy
		self.copyrowindex=None
		self.copycolumnindex=None
		#print("from line 119 in devtable.py sorting",self.lastsortcolumn)
		self.sortitemsfromrefresh()
############################################################
# sort to properly sort numerical items by the values in column icol
# this method also adds one selected column to the selected columns
	def sortitems(self, icol=None):
		mods = QtGui.QApplication.keyboardModifiers()
		#print("from devtable.py line 99")
		### add to selected columns for clipboard################################################
		if (mods==QtCore.Qt.ShiftModifier or mods==QtCore.Qt.ControlModifier) and icol>0: 			# want to reserve shift mouseclick for to copy to select columns for clipboard
			self.blockSignals(True)
			self.hheaderview.blockSignals(True)
			duplicatecolumn=False
			self.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
			self.selectColumn(icol)
			self.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
			for ic in range(0,len(self.selectedcolumns)):
				if self.horizontalHeaderItem(icol).text()==self.selectedcolumnheaders[ic]:	duplicatecolumn=True				# is the newly-selected column already in the buffer?
			if not duplicatecolumn:
				self.setCursor(QtCore.Qt.WaitCursor)			# signal user that the sort is working
				self.selectedcolumns.append([self.item(ir,self.currentColumn()).text() for ir in range(0, self.rowCount())])		# append a newly-selected column selectedcolumns is two-dimensional [ic][ir]
				self.selectedcolumnheaders.append(self.horizontalHeaderItem(self.currentColumn()).text())					# append the header
				self.setCursor((QtCore.Qt.ArrowCursor))		# signal user that sort is complete
			#print("from devtable.py line 114",self.selectedcolumnheaders) #debug
			self.blockSignals(False)
			self.hheaderview.blockSignals(False)
			return
		##################### done with select columns for clipboard########################################

		################### or sort items in column #####################################
		# differs from self.sortitems() in that the sort order toggles
		#tempitem=QtGui.QTableWidgetItem()
		#print("from line 154 devtable.py",self.lastsortorder)
		self.setCursor(QtCore.Qt.WaitCursor)			# signal user that the sort is working
		self.lastsortcolumn = icol  # save last sort by column (parameter to sort by for use on list refresh
		self.lastsortorder = self.sortorder	# save last sorting order for use on list refresh
		if self.sortorder=='ascending':
			self.sortByColumn(icol,QtCore.Qt.AscendingOrder)
			self.sortorder='decending'
		else:
			self.sortByColumn(icol,QtCore.Qt.DescendingOrder)
			self.sortorder='ascending'
		self.setCursor((QtCore.Qt.ArrowCursor))		# signal user that sort is complete
		self.unselect()								# unselect because the selection is stale after resorting
		return
#######################################################################################################
# sort items when the device list is set up or refreshed - here sort order does NOT toggle
	def sortitemsfromrefresh(self):
		#print("from line 170 devtable.py", self.lastsortorder)
		self.setCursor(QtCore.Qt.WaitCursor)  # signal user that the sort is working
		if self.lastsortorder == 'ascending':
			self.sortByColumn(self.lastsortcolumn, QtCore.Qt.AscendingOrder)
		else:
			self.sortByColumn(self.lastsortcolumn, QtCore.Qt.DescendingOrder)
		self.setCursor((QtCore.Qt.ArrowCursor))  # signal user that sort is complete
		self.unselect()  # unselect because the selection is stale after resorting
		return
#######################################################################################
# copy the selected data to the clipboard
	def keyPressEvent(self,ke):
		mods=QtGui.QApplication.keyboardModifiers()
		if ke.key()== QtCore.Qt.Key_C and mods==QtCore.Qt.ControlModifier:			# cntl-c to send selected column data to clipboard
			clipb=QtGui.QApplication.clipboard()							# set up clipboard
			dataclip="\t"
			#print("from devtable.py line 161 ctrl-c") #debug
			QtCore.QEvent.ignore(ke)
			# send to clipboard
			self.setCursor(QtCore.Qt.WaitCursor)									# signal user that the clipboard is appending
			for ic in range(0,len(self.selectedcolumnheaders)):						# append column labels
				dataclip+=self.selectedcolumnheaders[ic]+"\t"
			dataclip+="\n"
			for ir in range(0,self.rowCount()):
				dataclip+=self.item(ir,0).text()+"\t"		# append row label
				for ic in range(0,len(self.selectedcolumns)):
					if is_number(self.selectedcolumns[ic][ir]):
						dataclip="".join([dataclip,formatnum(float(self.selectedcolumns[ic][ir]),precision=2),"\t"])
					else:		# treat as ASCII text
						dataclip="".join([dataclip,str(self.selectedcolumns[ic][ir]),"\t"])	# append data of selected columns
				dataclip+="\n"
			clipb.setText(dataclip)
			self.setCursor((QtCore.Qt.ArrowCursor))									# signal to user that appending to clipboard is done

		elif ke.key()==QtCore.Qt.Key_X and mods==QtCore.Qt.ControlModifier:			# cntl-x to clear clipboard and column selections
			QtCore.QEvent.ignore(ke)
			self.unselect()
		#### find selected devices using ctrl-f
		elif ke.key()==QtCore.Qt.Key_F and mods==QtCore.Qt.ControlModifier:			# cntl-f to find devices
			findpop=Boolean_find(self)
			findpop.show()
		ke.accept()
############################################################
# emit signal with the string contents of selected row and the row number Looks like it does in fact work
	def vheadertext(self,irow,icol):
		mods = QtGui.QApplication.keyboardModifiers()
		if mods==QtCore.Qt.ShiftModifier:
			if self.copycolumnindex!=None:
				if (self.copycolumnindex==0 and self.copycolumnindex not in self.coloredrow) or icol!=0: self.item(self.copyrowindex,0).setBackground(QtCore.Qt.white)
				if self.copycolumnindex!=0: self.item(self.copyrowindex,self.copycolumnindex).setBackground(QtCore.Qt.white)
			self.copyrowindex=irow
			self.copycolumnindex=icol
			self.item(irow,icol).setBackground(QtCore.Qt.yellow)
			#if icol==0 and irow not in self.coloredrow: self.coloredrow.append(irow)
			clipb=QtGui.QApplication.clipboard()
			clipb.setText(self.item(irow,icol).text())
		else:
			if icol==0:					# then read the text for the selected row
				self.item(irow,0).setBackground(QtCore.Qt.yellow) #self.item(ir,icol).setBackground(QtCore.Qt.red)
				self.coloredrow.append(irow)
				self.VerticalHeaderClicked.emit(self.item(irow,0).text(),irow)		# this signal is captured by select_plot_menu() method of DeviceListing() in actions_devlisting.py
			else:
				self.unselect()			# unselect clipboard selections for columns -> clipboard via mouseclick off column 0
###########################################################################
# unselect all and empty selection buffer
	def unselect(self):
		del self.selectedcolumns
		del self.selectedcolumnheaders
		self.selectedcolumnheaders =col.deque()						# clear selected columns
		self.selectedcolumns = col.deque()
		# reset cell background colors to all white
		clipb=QtGui.QApplication.clipboard()						# set up clipboard
		clipb.setText("")											# clear clipboard
		del clipb
		self.clearSelection()										# clear selection
		for ii in range(0,len(self.coloredrow)):					# clear highlighting in device names column
			self.item(self.coloredrow[ii],0).setBackground(QtCore.Qt.white)
		if self.copyrowindex!=None: self.item(self.copyrowindex,self.copycolumnindex).setBackground(QtCore.Qt.white)
		#self.QA(QtGui.QAbstractItemView.clearSelection)
		# for ir in range(0,self.rowCount()):
		# 	for ic in range(0, self.columnCount()):
		# 		#print("from devtable.py line 218 row,col = ",ir,ic)
		# 		self.item(ir,ic).setBackground(QtCore.Qt.white)
###################################################################################
###############################################################################
# subclass of item to enable custom sorting i.e. numeric
# http://stackoverflow.com/questions/2304199/how-to-sort-a-qtablewidget-with-my-own-code
class sItem(QtGui.QTableWidgetItem):
	#def __init__(self,data=None):
	#	QtGui.QTableWidgetItem.__init__(self,data)
	#	self.data=data
	def __lt__(self, other):
		if is_number(self.text()) and not is_number(other.text()): return False
		if is_number(other.text()) and not is_number(self.text()): return True
		if is_number(self.text()) and is_number(other.text()):
			return float(self.text())<float(other.text())
		return False
##########################################################################################################################################

######################## pop-up to get Boolean search terms
class Boolean_find(Ui_BooleanFinder,QtGui.QDialog):
	#SetBooleanFind=QtCore.pyqtSignal(list)
	def __init__(self,parent=None):
		super(Boolean_find,self).__init__(parent)
		self.setupUi(self)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.boolean_device_finder.setText(self.parent().searchitems)				# start with previous search items as default
		self.boolean_device_finder.editingFinished.connect(self.newsearch)
		self.alldevices_vheaders=list(self.parent().vheaders)		# keep original list of devices to restore after find
		#print(self.parent().mapToGlobal(QtCore.QPoint(0,0)).x(),self.parent().mapToGlobal(QtCore.QPoint(0,0)).y())
		#pos=self.mapFromParent(QtCore.QPoint(0,0))
		posparent=QtCore.QPoint(self.parent().mapToGlobal(QtCore.QPoint(0,0)))
		pos=QtCore.QPoint(posparent.x()+1000,posparent.y())
		self.move(pos)
		#self.move(self.mapFromParent(QtCore.QPoint(self.parent().rect().right(),self.parent().rect().bottom())))
		if self.boolean_device_finder.text()!="": self.newsearch()

	def newsearch(self):
		if self.boolean_device_finder.text()=="": vheaders=self.alldevices_vheaders
		else: vheaders=[dev for dev in self.alldevices_vheaders if parse_rpn(expression=self.boolean_device_finder.text(),targetfilename=dev )]
		self.parent().setup(vheaders=vheaders)
		if len(vheaders)>0: self.parent().searchitems=self.boolean_device_finder.text()				# save last search only if it produced at least one match
	def closeEvent(self,e):
		self.boolean_device_finder.blockSignals(True)				# MUST block signals before disable if disable before blocksignals this won't work blocksignals is necessary because the act of closing the widget results in firing a self.boolean_device_finder.editingFinished signal
		self.parent().setup(vheaders=self.alldevices_vheaders)  # restore all former devices after find to listing
		e.accept()
