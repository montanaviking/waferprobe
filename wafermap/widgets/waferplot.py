# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'waferplot.ui'
#
# Created: Wed Dec  6 19:06:47 2017
#      by: PyQt5 UI code generator 5.2.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.NonModal)
        Dialog.resize(884, 648)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.wafername = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(20)
        self.wafername.setFont(font)
        self.wafername.setObjectName("wafername")
        self.verticalLayout_4.addWidget(self.wafername)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.wafermapcontainer = QtWidgets.QHBoxLayout()
        self.wafermapcontainer.setObjectName("wafermapcontainer")
        self.horizontalLayout_4.addLayout(self.wafermapcontainer)
        self.colorscalecontainer = QtWidgets.QHBoxLayout()
        self.colorscalecontainer.setObjectName("colorscalecontainer")
        self.horizontalLayout_4.addLayout(self.colorscalecontainer)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem)
        self.verticalLayout_4.addLayout(self.horizontalLayout_4)
        self.frame = QtWidgets.QFrame(Dialog)
        self.frame.setMaximumSize(QtCore.QSize(16777215, 150))
        self.frame.setFrameShape(QtWidgets.QFrame.Box)
        self.frame.setObjectName("frame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout.setSpacing(1)
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.measurementtype_label = QtWidgets.QLabel(self.frame)
        self.measurementtype_label.setMinimumSize(QtCore.QSize(0, 20))
        self.measurementtype_label.setMaximumSize(QtCore.QSize(16777215, 20))
        self.measurementtype_label.setObjectName("measurementtype_label")
        self.horizontalLayout_2.addWidget(self.measurementtype_label)
        self.measurementtype = QtWidgets.QComboBox(self.frame)
        self.measurementtype.setMaximumSize(QtCore.QSize(16777215, 30))
        self.measurementtype.setEditable(False)
        self.measurementtype.setObjectName("measurementtype")
        self.horizontalLayout_2.addWidget(self.measurementtype)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.log_linear_scale_but = QtWidgets.QPushButton(self.frame)
        self.log_linear_scale_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.log_linear_scale_but.setStyleSheet("background-color: hsv(100, 200, 255);\n"
"color: rgb(0, 0,0);")
        self.log_linear_scale_but.setCheckable(True)
        self.log_linear_scale_but.setChecked(False)
        self.log_linear_scale_but.setAutoDefault(False)
        self.log_linear_scale_but.setObjectName("log_linear_scale_but")
        self.verticalLayout_2.addWidget(self.log_linear_scale_but)
        self.crossout_nodata_but = QtWidgets.QPushButton(self.frame)
        self.crossout_nodata_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.crossout_nodata_but.setStyleSheet("background-color: hsv(100, 200, 255);\n"
"color: rgb(0, 0,0);")
        self.crossout_nodata_but.setCheckable(True)
        self.crossout_nodata_but.setChecked(False)
        self.crossout_nodata_but.setAutoDefault(False)
        self.crossout_nodata_but.setObjectName("crossout_nodata_but")
        self.verticalLayout_2.addWidget(self.crossout_nodata_but)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.waferplan_label = QtWidgets.QLabel(self.frame)
        self.waferplan_label.setMinimumSize(QtCore.QSize(0, 20))
        self.waferplan_label.setMaximumSize(QtCore.QSize(16777215, 20))
        self.waferplan_label.setObjectName("waferplan_label")
        self.horizontalLayout_3.addWidget(self.waferplan_label)
        self.waferplanfile = QtWidgets.QComboBox(self.frame)
        self.waferplanfile.setMaximumSize(QtCore.QSize(16777215, 30))
        self.waferplanfile.setEditable(False)
        self.waferplanfile.setObjectName("waferplanfile")
        self.horizontalLayout_3.addWidget(self.waferplanfile)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.masklevels_label = QtWidgets.QLabel(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.masklevels_label.sizePolicy().hasHeightForWidth())
        self.masklevels_label.setSizePolicy(sizePolicy)
        self.masklevels_label.setMaximumSize(QtCore.QSize(16777215, 20))
        self.masklevels_label.setObjectName("masklevels_label")
        self.horizontalLayout.addWidget(self.masklevels_label)
        self.masklevels = QtWidgets.QListWidget(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.masklevels.sizePolicy().hasHeightForWidth())
        self.masklevels.setSizePolicy(sizePolicy)
        self.masklevels.setMaximumSize(QtCore.QSize(50, 130))
        self.masklevels.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        self.masklevels.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.masklevels.setProperty("showDropIndicator", False)
        self.masklevels.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.masklevels.setSelectionRectVisible(False)
        self.masklevels.setObjectName("masklevels")
        item = QtWidgets.QListWidgetItem()
        self.masklevels.addItem(item)
        item = QtWidgets.QListWidgetItem()
        self.masklevels.addItem(item)
        item = QtWidgets.QListWidgetItem()
        self.masklevels.addItem(item)
        item = QtWidgets.QListWidgetItem()
        self.masklevels.addItem(item)
        item = QtWidgets.QListWidgetItem()
        self.masklevels.addItem(item)
        item = QtWidgets.QListWidgetItem()
        self.masklevels.addItem(item)
        self.horizontalLayout.addWidget(self.masklevels)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.selectforanalysis_but = QtWidgets.QPushButton(self.frame)
        self.selectforanalysis_but.setObjectName("selectforanalysis_but")
        self.verticalLayout_3.addWidget(self.selectforanalysis_but)
        self.reset_selectforanalysis_but = QtWidgets.QPushButton(self.frame)
        self.reset_selectforanalysis_but.setObjectName("reset_selectforanalysis_but")
        self.verticalLayout_3.addWidget(self.reset_selectforanalysis_but)
        self.clearselections_but = QtWidgets.QPushButton(self.frame)
        self.clearselections_but.setObjectName("clearselections_but")
        self.verticalLayout_3.addWidget(self.clearselections_but)
        self.wafermap_to_clipboard_but = QtWidgets.QPushButton(self.frame)
        self.wafermap_to_clipboard_but.setObjectName("wafermap_to_clipboard_but")
        self.verticalLayout_3.addWidget(self.wafermap_to_clipboard_but)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout_4.addWidget(self.frame)
        self.Device_Listing_Table = DevTable(Dialog)
        self.Device_Listing_Table.setMaximumSize(QtCore.QSize(16777215, 200))
        self.Device_Listing_Table.setObjectName("Device_Listing_Table")
        self.Device_Listing_Table.setColumnCount(0)
        self.Device_Listing_Table.setRowCount(0)
        self.Device_Listing_Table.horizontalHeader().setCascadingSectionResizes(True)
        self.Device_Listing_Table.horizontalHeader().setStretchLastSection(True)
        self.Device_Listing_Table.verticalHeader().setCascadingSectionResizes(True)
        self.verticalLayout_4.addWidget(self.Device_Listing_Table)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.wafername.setText(_translate("Dialog", "Wafer Name"))
        self.measurementtype_label.setWhatsThis(_translate("Dialog", "<html><head/><body><p><span style=\" color:#000000;\">Select what parameter to display on wafer map. If there are no data for this parameter, the devices will all appear white with an X drawn through them.</span></p></body></html>"))
        self.measurementtype_label.setText(_translate("Dialog", "Measurement Type"))
        self.measurementtype.setToolTip(_translate("Dialog", "Data Format: Resistance (Ron) or Conductance (Gon)"))
        self.measurementtype.setWhatsThis(_translate("Dialog", "Ron @ Vds=0V is the slope of Ids/Vds at Vds=0V\n"
"Ron @ |Vds|=maximum is the maximum Vds/Id at maximum Vds\n"
"Gon s are similar to the above but are conductances = 1/Ron"))
        self.log_linear_scale_but.setWhatsThis(_translate("Dialog", "<html><head/><body><p><span style=\" color:#000000;\">Select linear or log color scale. When displaying wafer sections above the individual device level, the average of the devices/sections under the displayed section is shown via the color.</span></p><p><span style=\" color:#000000;\">If linear is selected - the average is shown. If log is selected, the geometric mean is shown and the color scale is logarithmic.</span></p></body></html>"))
        self.log_linear_scale_but.setText(_translate("Dialog", "Linear/Log scale"))
        self.crossout_nodata_but.setWhatsThis(_translate("Dialog", "<html><head/><body><p><span style=\" color:#000000;\">Select linear or log color scale. When displaying wafer sections above the individual device level, the average of the devices/sections under the displayed section is shown via the color.</span></p><p><span style=\" color:#000000;\">If linear is selected - the average is shown. If log is selected, the geometric mean is shown and the color scale is logarithmic.</span></p></body></html>"))
        self.crossout_nodata_but.setText(_translate("Dialog", "crossout"))
        self.waferplan_label.setWhatsThis(_translate("Dialog", "<html><head/><body><p><span style=\" color:#000000;\">Select wafer plan to use to display the wafer map. This controls which devices are shown and allows for unambiguous display of the same devices for different measurement conditions by selection of the wafer plan.</span></p></body></html>"))
        self.waferplan_label.setText(_translate("Dialog", "Wafer Plan"))
        self.waferplanfile.setToolTip(_translate("Dialog", "Data Format: Resistance (Ron) or Conductance (Gon)"))
        self.waferplanfile.setWhatsThis(_translate("Dialog", "Ron @ Vds=0V is the slope of Ids/Vds at Vds=0V\n"
"Ron @ |Vds|=maximum is the maximum Vds/Id at maximum Vds\n"
"Gon s are similar to the above but are conductances = 1/Ron"))
        self.masklevels_label.setWhatsThis(_translate("Dialog", "<html><head/><body><p><span style=\" color:#000000;\">Select mask level to display on the wafer map. A mask level 0 is the lowest, level and displays the individual devices. Higher levels have a parent-child relationship with levels underneath them.</span></p><p><span style=\" color:#000000;\">The color of devices having levels&gt;0 is determined by the average or geometric mean (depending on the state of the linear/log scale button) of the data values of the levels beneath them.</span></p></body></html>"))
        self.masklevels_label.setText(_translate("Dialog", "Masklevels"))
        __sortingEnabled = self.masklevels.isSortingEnabled()
        self.masklevels.setSortingEnabled(False)
        item = self.masklevels.item(0)
        item.setText(_translate("Dialog", "0"))
        item = self.masklevels.item(1)
        item.setText(_translate("Dialog", "1"))
        item = self.masklevels.item(2)
        item.setText(_translate("Dialog", "2"))
        item = self.masklevels.item(3)
        item.setText(_translate("Dialog", "3"))
        item = self.masklevels.item(4)
        item.setText(_translate("Dialog", "4"))
        item = self.masklevels.item(5)
        item.setText(_translate("Dialog", "5"))
        self.masklevels.setSortingEnabled(__sortingEnabled)
        self.selectforanalysis_but.setWhatsThis(_translate("Dialog", "<html><head/><body><p><span style=\" color:#000000;\">Clear all selections on the wafer made by the user.</p></body></html>"))
        self.selectforanalysis_but.setText(_translate("Dialog", "select devices for analysis"))
        self.reset_selectforanalysis_but.setWhatsThis(_translate("Dialog", "<html><head/><body><p><span style=\" color:#000000;\">Clear all selections on the wafer made by the user.</p></body></html>"))
        self.reset_selectforanalysis_but.setText(_translate("Dialog", "reset select devices for analysis"))
        self.clearselections_but.setWhatsThis(_translate("Dialog", "<html><head/><body><p><span style=\" color:#000000;\">Clear all selections on the wafer made by the user.</p></body></html>"))
        self.clearselections_but.setText(_translate("Dialog", "clear all selections"))
        self.wafermap_to_clipboard_but.setWhatsThis(_translate("Dialog", "<html><head/><body><p><span style=\" color:#000000;\">Clear all selections on the wafer made by the user.</p></body></html>"))
        self.wafermap_to_clipboard_but.setText(_translate("Dialog", "send wafermap to clipboard"))
        self.Device_Listing_Table.setWhatsThis(_translate("Dialog", "<html><head/><body><p><span style=\" color:#000000;\">Device listing from a selected device on the wafermap. If there is only one device in the selected item on the wafermap, then only one device will show up in the table. If the user selects an item at a level above the individual device level, then all devices under that level will show up in this table. </span></p><p><span style=\" color:#000000;\">Note that a ctrl-f opens a window which allows the user to place a Boolean expression to selectively display devices.</span></p><p><span style=\" color:#000000;\">Left mouse click on parameter (header) to sort. shift+left mouse click on parameter to select it for copy to clipboard - the selected columns will change color. After selecting all desired parameters, cntl-c to copy them to clipboard. Right mouse click deselects all. Shift right click to load individual cells to clipboard. Left mouse click on device name will allow plotting of selected device parameters.</span></p></body></html>"))

from devtable import DevTable
