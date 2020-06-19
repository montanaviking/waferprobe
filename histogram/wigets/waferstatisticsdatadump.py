# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'waferstatisticsdatadump.ui'
#
# Created: Mon May 15 14:49:29 2017
#      by: PyQt5 UI code generator 5.2.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_WaferStatisticsDataDump(object):
    def setupUi(self, WaferStatisticsDataDump):
        WaferStatisticsDataDump.setObjectName("WaferStatisticsDataDump")
        WaferStatisticsDataDump.resize(1449, 475)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(WaferStatisticsDataDump)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.average_table_label = QtWidgets.QLabel(WaferStatisticsDataDump)
        self.average_table_label.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.average_table_label.setFont(font)
        self.average_table_label.setAlignment(QtCore.Qt.AlignCenter)
        self.average_table_label.setObjectName("average_table_label")
        self.verticalLayout.addWidget(self.average_table_label)
        self.wafer_label = QtWidgets.QLabel(WaferStatisticsDataDump)
        self.wafer_label.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.wafer_label.setFont(font)
        self.wafer_label.setAlignment(QtCore.Qt.AlignCenter)
        self.wafer_label.setObjectName("wafer_label")
        self.verticalLayout.addWidget(self.wafer_label)
        self.Device_Listing_Table = DevTable(WaferStatisticsDataDump)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Device_Listing_Table.setFont(font)
        self.Device_Listing_Table.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.Device_Listing_Table.setWhatsThis("")
        self.Device_Listing_Table.setAccessibleDescription("")
        self.Device_Listing_Table.setStyleSheet("")
        self.Device_Listing_Table.setObjectName("Device_Listing_Table")
        self.Device_Listing_Table.setColumnCount(0)
        self.Device_Listing_Table.setRowCount(0)
        self.Device_Listing_Table.horizontalHeader().setCascadingSectionResizes(True)
        self.Device_Listing_Table.horizontalHeader().setStretchLastSection(True)
        self.Device_Listing_Table.verticalHeader().setCascadingSectionResizes(True)
        self.verticalLayout.addWidget(self.Device_Listing_Table)
        self.verticalLayout_3.addLayout(self.verticalLayout)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.upper_lower_but = QtWidgets.QPushButton(WaferStatisticsDataDump)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.upper_lower_but.setFont(font)
        self.upper_lower_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.upper_lower_but.setCheckable(True)
        self.upper_lower_but.setAutoDefault(False)
        self.upper_lower_but.setObjectName("upper_lower_but")
        self.horizontalLayout.addWidget(self.upper_lower_but)
        self.set_fract_data_selected = QtWidgets.QLineEdit(WaferStatisticsDataDump)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.set_fract_data_selected.setFont(font)
        self.set_fract_data_selected.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.set_fract_data_selected.setAcceptDrops(True)
        self.set_fract_data_selected.setWhatsThis("")
        self.set_fract_data_selected.setReadOnly(False)
        self.set_fract_data_selected.setObjectName("set_fract_data_selected")
        self.horizontalLayout.addWidget(self.set_fract_data_selected)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.parameter_to_filter_label = QtWidgets.QLabel(WaferStatisticsDataDump)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.parameter_to_filter_label.setFont(font)
        self.parameter_to_filter_label.setObjectName("parameter_to_filter_label")
        self.horizontalLayout_4.addWidget(self.parameter_to_filter_label)
        self.parameter_to_filter = QtWidgets.QComboBox(WaferStatisticsDataDump)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.parameter_to_filter.setFont(font)
        self.parameter_to_filter.setEditable(False)
        self.parameter_to_filter.setObjectName("parameter_to_filter")
        self.parameter_to_filter.addItem("")
        self.parameter_to_filter.addItem("")
        self.parameter_to_filter.addItem("")
        self.parameter_to_filter.addItem("")
        self.horizontalLayout_4.addWidget(self.parameter_to_filter)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.parameter_essential_label = QtWidgets.QLabel(WaferStatisticsDataDump)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.parameter_essential_label.setFont(font)
        self.parameter_essential_label.setObjectName("parameter_essential_label")
        self.horizontalLayout_5.addWidget(self.parameter_essential_label)
        self.parameter_essential = QtWidgets.QComboBox(WaferStatisticsDataDump)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.parameter_essential.setFont(font)
        self.parameter_essential.setEditable(False)
        self.parameter_essential.setObjectName("parameter_essential")
        self.parameter_essential.addItem("")
        self.parameter_essential.addItem("")
        self.parameter_essential.addItem("")
        self.parameter_essential.addItem("")
        self.horizontalLayout_5.addWidget(self.parameter_essential)
        self.verticalLayout_2.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.populate_data_table_but = QtWidgets.QPushButton(WaferStatisticsDataDump)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.populate_data_table_but.setFont(font)
        self.populate_data_table_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.populate_data_table_but.setObjectName("populate_data_table_but")
        self.horizontalLayout_2.addWidget(self.populate_data_table_but)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3.addLayout(self.verticalLayout_2)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.verticalLayout_3.addLayout(self.horizontalLayout_3)

        self.retranslateUi(WaferStatisticsDataDump)
        QtCore.QMetaObject.connectSlotsByName(WaferStatisticsDataDump)

    def retranslateUi(self, WaferStatisticsDataDump):
        _translate = QtCore.QCoreApplication.translate
        WaferStatisticsDataDump.setWindowTitle(_translate("WaferStatisticsDataDump", "Wafer Statistics Tabulation"))
        self.average_table_label.setWhatsThis(_translate("WaferStatisticsDataDump", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Select devices to be analyzed by typing in key words</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">separated by commas and/or spaces</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Devices will be selected for analysis IF and ONLY IF</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">their name contains all the keywords.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Used to select devices based on their parameters</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">e.g. MO or Mo metal contacts or TLM0.4 for a</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">TLM device having gate or channel length of 0.4um</span></p></body></html>"))
        self.average_table_label.setText(_translate("WaferStatisticsDataDump", "Statistical Averaged Data"))
        self.wafer_label.setWhatsThis(_translate("WaferStatisticsDataDump", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Select devices to be analyzed by typing in key words</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">separated by commas and/or spaces</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Devices will be selected for analysis IF and ONLY IF</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">their name contains all the keywords.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Used to select devices based on their parameters</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">e.g. MO or Mo metal contacts or TLM0.4 for a</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">TLM device having gate or channel length of 0.4um</span></p></body></html>"))
        self.wafer_label.setText(_translate("WaferStatisticsDataDump", "Wafer"))
        self.Device_Listing_Table.setToolTip(_translate("WaferStatisticsDataDump", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\" bgcolor=\"#ffffff\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000; background-color:#ffffff;\">Device listing of statistical data of device types.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000; background-color:#ffffff;\">These data are the averages of data for each device type according to the parameters.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000; background-color:#ffffff;\">Note that a ctrl-f opens a window which allows the user to place a Boolean </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000; background-color:#ffffff;\">expression to selectively display devices. </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000; background-color:#ffffff;\">Can also select columns via shift+left click mouse click of parameter to copy to clipboard.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000; background-color:#ffffff;\">After selecting columns, ctrl-c copies the selected columns to the clipboard</span></p></body></html>"))
        self.upper_lower_but.setToolTip(_translate("WaferStatisticsDataDump", "<html><head/><body><p><span style=\" color:#000000; background-color:#ffffff;\">select upper/lower fraction of devices to cherry pick for this table</span></p></body></html>"))
        self.upper_lower_but.setWhatsThis(_translate("WaferStatisticsDataDump", "<html><head/><body><p><span style=\" color:#000000;\">Cherry-pick the upper or lower (user selectable) fraction of devices, of that parameter specified in the Sorting Parameter, to use to average for each device type (e.g. a device type can be a TLM length TLM_0.07). </span></p><p><br/></p></body></html>"))
        self.upper_lower_but.setText(_translate("WaferStatisticsDataDump", "Select Upper Fraction"))
        self.set_fract_data_selected.setToolTip(_translate("WaferStatisticsDataDump", "fraction (upper or lower) of devices selected for statistical analysis in the above table"))
        self.parameter_to_filter_label.setWhatsThis(_translate("WaferStatisticsDataDump", "<html><head/><body><p><span style=\" color:#000000;\">Parameter used to cherry-pick devices. Devices are chosen, based on the values of this parameter. For example, if the Select Upper Fraction = 0.1 then and the Sorting Parameter is |Idmax|, then the device will be chosen for the average if its parameter value is among the top 10% of |Idmax|.</span></p><p><br/></p></body></html>"))
        self.parameter_to_filter_label.setText(_translate("WaferStatisticsDataDump", "Sorting Parameter"))
        self.parameter_to_filter.setToolTip(_translate("WaferStatisticsDataDump", "Parameter to use to statistically cherry pick"))
        self.parameter_to_filter.setWhatsThis(_translate("WaferStatisticsDataDump", "Ron @ Vds=0V is the slope of Ids/Vds at Vds=0V\n"
"Ron @ |Vds|=maximum is the maximum Vds/Id at maximum Vds\n"
"Gon s are similar to the above but are conductances = 1/Ron"))
        self.parameter_to_filter.setItemText(0, _translate("WaferStatisticsDataDump", "|Idmax|"))
        self.parameter_to_filter.setItemText(1, _translate("WaferStatisticsDataDump", "On-Off Ratio"))
        self.parameter_to_filter.setItemText(2, _translate("WaferStatisticsDataDump", "Ron @ Vds=0V"))
        self.parameter_to_filter.setItemText(3, _translate("WaferStatisticsDataDump", "|Idmin|"))
        self.parameter_essential_label.setWhatsThis(_translate("WaferStatisticsDataDump", "<html><head/><body><p><span style=\" color:#000000;\">In order for a device to be selected, it must have the data for the parameter specified here. This is usually set to Ron if we\'re interested in obtaining Ron for a TLM characterization.<br/></p></body></html>"))
        self.parameter_essential_label.setText(_translate("WaferStatisticsDataDump", "Essential  Parameter"))
        self.parameter_essential.setToolTip(_translate("WaferStatisticsDataDump", "Data Format: Resistance (Ron) or Conductance (Gon)"))
        self.parameter_essential.setWhatsThis(_translate("WaferStatisticsDataDump", "Ron @ Vds=0V is the slope of Ids/Vds at Vds=0V\n"
"Ron @ |Vds|=maximum is the maximum Vds/Id at maximum Vds\n"
"Gon s are similar to the above but are conductances = 1/Ron"))
        self.parameter_essential.setItemText(0, _translate("WaferStatisticsDataDump", "|Idmax|"))
        self.parameter_essential.setItemText(1, _translate("WaferStatisticsDataDump", "On-Off Ratio"))
        self.parameter_essential.setItemText(2, _translate("WaferStatisticsDataDump", "Ron @ Vds=0V"))
        self.parameter_essential.setItemText(3, _translate("WaferStatisticsDataDump", "|Idmin|"))
        self.populate_data_table_but.setWhatsThis(_translate("WaferStatisticsDataDump", "<html><head/><body><p><span style=\" color:#000000;\">Send all data here to clipboard. WARNING: you might not always be able to paste due to a bug. You can work around this by selecting individual columns to send to the clipboard.</span></p></body></html>"))
        self.populate_data_table_but.setText(_translate("WaferStatisticsDataDump", "populate data table and clipboard"))

from devtable import DevTable
