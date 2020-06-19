# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fileview.ui'
#
# Created: Thu Dec 10 10:45:33 2015
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_FileView(object):
    def setupUi(self, FileView):
        FileView.setObjectName(_fromUtf8("FileView"))
        FileView.resize(400, 300)
        self.verticalLayout = QtGui.QVBoxLayout(FileView)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.device_label = QtGui.QLabel(FileView)
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.device_label.setFont(font)
        self.device_label.setFocusPolicy(QtCore.Qt.NoFocus)
        self.device_label.setObjectName(_fromUtf8("device_label"))
        self.verticalLayout.addWidget(self.device_label)
        self.datatype_label = QtGui.QLabel(FileView)
        self.datatype_label.setObjectName(_fromUtf8("datatype_label"))
        self.verticalLayout.addWidget(self.datatype_label)
        self.file_table = QtGui.QTableWidget(FileView)
        self.file_table.setObjectName(_fromUtf8("file_table"))
        self.file_table.setColumnCount(0)
        self.file_table.setRowCount(0)
        self.file_table.horizontalHeader().setCascadingSectionResizes(True)
        self.file_table.horizontalHeader().setSortIndicatorShown(True)
        self.file_table.horizontalHeader().setStretchLastSection(True)
        self.file_table.verticalHeader().setVisible(False)
        self.file_table.verticalHeader().setHighlightSections(False)
        self.verticalLayout.addWidget(self.file_table)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.clipboard_but = QtGui.QPushButton(FileView)
        self.clipboard_but.setObjectName(_fromUtf8("clipboard_but"))
        self.horizontalLayout.addWidget(self.clipboard_but)
        spacerItem = QtGui.QSpacerItem(178, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(FileView)
        QtCore.QMetaObject.connectSlotsByName(FileView)

    def retranslateUi(self, FileView):
        FileView.setWindowTitle(_translate("FileView", "Dialog", None))
        self.device_label.setText(_translate("FileView", "Device", None))
        self.datatype_label.setText(_translate("FileView", "data type", None))
        self.clipboard_but.setText(_translate("FileView", "send to clipboard", None))

