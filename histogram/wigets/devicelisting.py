# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'devicelisting.ui'
#
# Created: Mon May 15 14:45:10 2017
#      by: PyQt5 UI code generator 5.2.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DeviceListing(object):
    def setupUi(self, DeviceListing):
        DeviceListing.setObjectName("DeviceListing")
        DeviceListing.resize(1238, 310)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(DeviceListing)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.wafer_label = QtWidgets.QLabel(DeviceListing)
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.wafer_label.setFont(font)
        self.wafer_label.setFocusPolicy(QtCore.Qt.NoFocus)
        self.wafer_label.setObjectName("wafer_label")
        self.verticalLayout_3.addWidget(self.wafer_label)
        self.Device_Listing_Table = DevTable(DeviceListing)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Device_Listing_Table.setFont(font)
        self.Device_Listing_Table.setStatusTip("")
        self.Device_Listing_Table.setWhatsThis("")
        self.Device_Listing_Table.setObjectName("Device_Listing_Table")
        self.Device_Listing_Table.setColumnCount(0)
        self.Device_Listing_Table.setRowCount(0)
        self.Device_Listing_Table.horizontalHeader().setCascadingSectionResizes(True)
        self.Device_Listing_Table.horizontalHeader().setStretchLastSection(True)
        self.Device_Listing_Table.verticalHeader().setCascadingSectionResizes(True)
        self.verticalLayout_3.addWidget(self.Device_Listing_Table)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.transfer_curve_type_label = QtWidgets.QLabel(DeviceListing)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.transfer_curve_type_label.setFont(font)
        self.transfer_curve_type_label.setObjectName("transfer_curve_type_label")
        self.horizontalLayout_2.addWidget(self.transfer_curve_type_label)
        self.selector_transfer_curve_type = QtWidgets.QComboBox(DeviceListing)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.selector_transfer_curve_type.setFont(font)
        self.selector_transfer_curve_type.setEditable(False)
        self.selector_transfer_curve_type.setObjectName("selector_transfer_curve_type")
        self.selector_transfer_curve_type.addItem("")
        self.horizontalLayout_2.addWidget(self.selector_transfer_curve_type)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.comparator_but = QtWidgets.QPushButton(DeviceListing)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.comparator_but.setFont(font)
        self.comparator_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.comparator_but.setObjectName("comparator_but")
        self.verticalLayout_2.addWidget(self.comparator_but)
        self.wafermap_but = QtWidgets.QPushButton(DeviceListing)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.wafermap_but.setFont(font)
        self.wafermap_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.wafermap_but.setObjectName("wafermap_but")
        self.verticalLayout_2.addWidget(self.wafermap_but)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_3 = QtWidgets.QLabel(DeviceListing)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.verticalLayout.addWidget(self.label_3)
        self.label = QtWidgets.QLabel(DeviceListing)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.label_4 = QtWidgets.QLabel(DeviceListing)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.verticalLayout.addWidget(self.label_4)
        self.label_2 = QtWidgets.QLabel(DeviceListing)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.retranslateUi(DeviceListing)
        QtCore.QMetaObject.connectSlotsByName(DeviceListing)

    def retranslateUi(self, DeviceListing):
        _translate = QtCore.QCoreApplication.translate
        DeviceListing.setWindowTitle(_translate("DeviceListing", "Device Listing"))
        self.wafer_label.setText(_translate("DeviceListing", "Wafer"))
        self.Device_Listing_Table.setToolTip(_translate("DeviceListing", "<html><head/><body><p><span style=\" color:#000000; background-color:#ffffff;\">Device listing of all devices which are not filtered out of the analysis. Note that a ctrl-f opens a window which allows the user to place a Boolean expression to selectively display devices.</span></p><p><span style=\" color:#000000; background-color:#ffffff;\">Left mouse click on parameter (header) to sort. </span></p><p><span style=\" color:#000000; background-color:#ffffff;\">Shift+left mouse click on parameter (column header) to select it for copy to clipboard - the selected columns will change color. </span></p><p><span style=\" color:#000000; background-color:#ffffff;\">After selecting all desired parameters, cntl-c to copy them to clipboard. </span></p><p><span style=\" color:#000000; background-color:#ffffff;\">Right mouse click deselects all. Shift right click to load individual cells to clipboard. </span></p><p><span style=\" color:#000000; background-color:#ffffff;\">Left mouse click on device name will allow plotting of selected device parameters.</span></p></body></html>"))
        self.transfer_curve_type_label.setToolTip(_translate("DeviceListing", "Selects type of transfer curve to display data on"))
        self.transfer_curve_type_label.setWhatsThis(_translate("DeviceListing", "<html><head/><body><p><span style=\" color:#000000;\">Parameter used to cherry-pick devices. Devices are chosen, based on the values of this parameter. For example, if the Select Upper Fraction = 0.1 then and the Sorting Parameter is |Idmax|, then the device will be chosen for the average if its parameter value is among the top 10% of |Idmax|.</span></p><p><br/></p></body></html>"))
        self.transfer_curve_type_label.setText(_translate("DeviceListing", "Transfer Curve Type"))
        self.selector_transfer_curve_type.setToolTip(_translate("DeviceListing", "Selects type of transfer curve"))
        self.selector_transfer_curve_type.setWhatsThis(_translate("DeviceListing", "Ron @ Vds=0V is the slope of Ids/Vds at Vds=0V\n"
"Ron @ |Vds|=maximum is the maximum Vds/Id at maximum Vds\n"
"Gon s are similar to the above but are conductances = 1/Ron"))
        self.selector_transfer_curve_type.setItemText(0, _translate("DeviceListing", "type of transfer curve"))
        self.comparator_but.setWhatsThis(_translate("DeviceListing", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">User to select wafer directory to open and analyze.</span></p></body></html>"))
        self.comparator_but.setText(_translate("DeviceListing", "&comparator"))
        self.wafermap_but.setWhatsThis(_translate("DeviceListing", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">User to select wafer directory to open and analyze.</span></p></body></html>"))
        self.wafermap_but.setText(_translate("DeviceListing", "&wafer map"))
        self.label_3.setText(_translate("DeviceListing", "Left mouse click on column header to sort"))
        self.label.setText(_translate("DeviceListing", "shift + left mouse click on column header to select column"))
        self.label_4.setText(_translate("DeviceListing", "ctrl-c on header to copy selection to clipboard"))
        self.label_2.setText(_translate("DeviceListing", "right mouse click to deselect all"))

from devtable import DevTable
