# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'plotter.ui'
#
# Created: Tue Oct 17 11:13:02 2017
#      by: PyQt5 UI code generator 5.2.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DataPlotter(object):
    def setupUi(self, DataPlotter):
        DataPlotter.setObjectName("DataPlotter")
        DataPlotter.resize(1098, 728)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(DataPlotter)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.wafer_label = QtWidgets.QLabel(DataPlotter)
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.wafer_label.setFont(font)
        self.wafer_label.setObjectName("wafer_label")
        self.verticalLayout.addWidget(self.wafer_label)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.plotbox = QtWidgets.QHBoxLayout()
        self.plotbox.setObjectName("plotbox")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.plotbox.addItem(spacerItem)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.plotbox.addItem(spacerItem1)
        self.verticalLayout_2.addLayout(self.plotbox)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.remove_leakage_Id_button = QtWidgets.QPushButton(DataPlotter)
        self.remove_leakage_Id_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.remove_leakage_Id_button.setCheckable(True)
        self.remove_leakage_Id_button.setObjectName("remove_leakage_Id_button")
        self.horizontalLayout.addWidget(self.remove_leakage_Id_button)
        self.add_Ig_button = QtWidgets.QPushButton(DataPlotter)
        self.add_Ig_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.add_Ig_button.setObjectName("add_Ig_button")
        self.horizontalLayout.addWidget(self.add_Ig_button)
        self.clipboard_text_button = QtWidgets.QPushButton(DataPlotter)
        self.clipboard_text_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clipboard_text_button.setObjectName("clipboard_text_button")
        self.horizontalLayout.addWidget(self.clipboard_text_button)
        self.clipboard_image_button = QtWidgets.QPushButton(DataPlotter)
        self.clipboard_image_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clipboard_image_button.setObjectName("clipboard_image_button")
        self.horizontalLayout.addWidget(self.clipboard_image_button)
        self.linear_fit_lines_button = QtWidgets.QPushButton(DataPlotter)
        self.linear_fit_lines_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.linear_fit_lines_button.setObjectName("linear_fit_lines_button")
        self.horizontalLayout.addWidget(self.linear_fit_lines_button)
        self.legend_toggle_button = QtWidgets.QPushButton(DataPlotter)
        self.legend_toggle_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.legend_toggle_button.setObjectName("legend_toggle_button")
        self.horizontalLayout.addWidget(self.legend_toggle_button)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.VgsFOClabel = QtWidgets.QLabel(DataPlotter)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.VgsFOClabel.setFont(font)
        self.VgsFOClabel.setObjectName("VgsFOClabel")
        self.horizontalLayout_3.addWidget(self.VgsFOClabel)
        self.VgsFOCselector = QtWidgets.QComboBox(DataPlotter)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.VgsFOCselector.setFont(font)
        self.VgsFOCselector.setEditable(False)
        self.VgsFOCselector.setObjectName("VgsFOCselector")
        self.horizontalLayout_3.addWidget(self.VgsFOCselector)
        self.horizontalLayout.addLayout(self.horizontalLayout_3)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.set_xlower_label = QtWidgets.QLabel(DataPlotter)
        self.set_xlower_label.setEnabled(True)
        self.set_xlower_label.setObjectName("set_xlower_label")
        self.horizontalLayout_2.addWidget(self.set_xlower_label)
        self.set_lower_X = QtWidgets.QLineEdit(DataPlotter)
        self.set_lower_X.setEnabled(True)
        self.set_lower_X.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.set_lower_X.setAcceptDrops(True)
        self.set_lower_X.setWhatsThis("")
        self.set_lower_X.setReadOnly(False)
        self.set_lower_X.setObjectName("set_lower_X")
        self.horizontalLayout_2.addWidget(self.set_lower_X)
        self.set_xupper_label = QtWidgets.QLabel(DataPlotter)
        self.set_xupper_label.setEnabled(True)
        self.set_xupper_label.setObjectName("set_xupper_label")
        self.horizontalLayout_2.addWidget(self.set_xupper_label)
        self.set_upper_X = QtWidgets.QLineEdit(DataPlotter)
        self.set_upper_X.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.set_upper_X.setAcceptDrops(True)
        self.set_upper_X.setWhatsThis("")
        self.set_upper_X.setReadOnly(False)
        self.set_upper_X.setObjectName("set_upper_X")
        self.horizontalLayout_2.addWidget(self.set_upper_X)
        self.loglinear_yscale_button = QtWidgets.QPushButton(DataPlotter)
        self.loglinear_yscale_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.loglinear_yscale_button.setCheckable(True)
        self.loglinear_yscale_button.setObjectName("loglinear_yscale_button")
        self.horizontalLayout_2.addWidget(self.loglinear_yscale_button)
        self.set_ylower_label = QtWidgets.QLabel(DataPlotter)
        self.set_ylower_label.setEnabled(True)
        self.set_ylower_label.setObjectName("set_ylower_label")
        self.horizontalLayout_2.addWidget(self.set_ylower_label)
        self.set_lower_Y = QtWidgets.QLineEdit(DataPlotter)
        self.set_lower_Y.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.set_lower_Y.setAcceptDrops(True)
        self.set_lower_Y.setWhatsThis("")
        self.set_lower_Y.setReadOnly(False)
        self.set_lower_Y.setObjectName("set_lower_Y")
        self.horizontalLayout_2.addWidget(self.set_lower_Y)
        self.set_yupper_label = QtWidgets.QLabel(DataPlotter)
        self.set_yupper_label.setEnabled(True)
        self.set_yupper_label.setObjectName("set_yupper_label")
        self.horizontalLayout_2.addWidget(self.set_yupper_label)
        self.set_upper_Y = QtWidgets.QLineEdit(DataPlotter)
        self.set_upper_Y.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.set_upper_Y.setAcceptDrops(True)
        self.set_upper_Y.setWhatsThis("")
        self.set_upper_Y.setReadOnly(False)
        self.set_upper_Y.setObjectName("set_upper_Y")
        self.horizontalLayout_2.addWidget(self.set_upper_Y)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.retranslateUi(DataPlotter)
        QtCore.QMetaObject.connectSlotsByName(DataPlotter)

    def retranslateUi(self, DataPlotter):
        _translate = QtCore.QCoreApplication.translate
        DataPlotter.setWindowTitle(_translate("DataPlotter", "Data Plot"))
        self.wafer_label.setText(_translate("DataPlotter", "Device"))
        self.remove_leakage_Id_button.setWhatsThis(_translate("DataPlotter", "<html><head/><body><p><span style=\" color:#000000;\">Send tabular data to the clipboard.</span></p></body></html>"))
        self.remove_leakage_Id_button.setText(_translate("DataPlotter", "Id leakage not removed"))
        self.add_Ig_button.setWhatsThis(_translate("DataPlotter", "<html><head/><body><p><span style=\" color:#000000;\">Send tabular data to the clipboard.</span></p></body></html>"))
        self.add_Ig_button.setText(_translate("DataPlotter", "add Ig to plot"))
        self.clipboard_text_button.setWhatsThis(_translate("DataPlotter", "<html><head/><body><p><span style=\" color:#000000;\">Send tabular data to the clipboard.</span></p></body></html>"))
        self.clipboard_text_button.setText(_translate("DataPlotter", "send &text to clipboard"))
        self.clipboard_image_button.setWhatsThis(_translate("DataPlotter", "<html><head/><body><p><span style=\" color:#000000;\">Send tabular data to the clipboard.</span></p></body></html>"))
        self.clipboard_image_button.setText(_translate("DataPlotter", "send &image to clipboard"))
        self.linear_fit_lines_button.setWhatsThis(_translate("DataPlotter", "<html><head/><body><p><span style=\" color:#000000;\">When clicked this button toggles between showing the lines used to find Ron on the family of curves OR whether or not to show the spline fit overlaying the measured data.</span></p></body></html>"))
        self.linear_fit_lines_button.setText(_translate("DataPlotter", "&fit lines spline/linear"))
        self.legend_toggle_button.setWhatsThis(_translate("DataPlotter", "<html><head/><body><p><span style=\" color:#000000;\">When clicked this button toggles between showing the lines used to find Ron on the family of curves OR whether or not to show the spline fit overlaying the measured data.</span></p></body></html>"))
        self.legend_toggle_button.setText(_translate("DataPlotter", "&Legend On/Off"))
        self.VgsFOClabel.setWhatsThis(_translate("DataPlotter", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Parameter selector:</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Selects parameter to be displayed on histogram.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">If you get the warning message &quot;no devices&quot;</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">then try to adjust the parameter selector to find a </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">parameter for which there are data. The parameter </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">selector MUST be set to data that exists for any analysis</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">to proceed.</p></body></html>"))
        self.VgsFOClabel.setText(_translate("DataPlotter", "FOC Vgs"))
        self.VgsFOCselector.setToolTip(_translate("DataPlotter", "Data Format: Resistance (Ron) or Conductance (Gon)"))
        self.VgsFOCselector.setWhatsThis(_translate("DataPlotter", "Ron @ Vds=0V is the slope of Ids/Vds at Vds=0V\n"
"Ron @ |Vds|=maximum is the maximum Vds/Id at maximum Vds\n"
"Gon s are similar to the above but are conductances = 1/Ron"))
        self.set_xlower_label.setWhatsThis(_translate("DataPlotter", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
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
        self.set_xlower_label.setText(_translate("DataPlotter", "lower X"))
        self.set_lower_X.setToolTip(_translate("DataPlotter", "Set which devices are included in analysis"))
        self.set_xupper_label.setWhatsThis(_translate("DataPlotter", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
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
        self.set_xupper_label.setText(_translate("DataPlotter", "Upper X"))
        self.set_upper_X.setToolTip(_translate("DataPlotter", "Set which devices are included in analysis"))
        self.loglinear_yscale_button.setWhatsThis(_translate("DataPlotter", "<html><head/><body><p><span style=\" color:#000000;\">Send tabular data to the clipboard.</span></p></body></html>"))
        self.loglinear_yscale_button.setText(_translate("DataPlotter", "Linear Y"))
        self.set_ylower_label.setWhatsThis(_translate("DataPlotter", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
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
        self.set_ylower_label.setText(_translate("DataPlotter", "lower Y"))
        self.set_lower_Y.setToolTip(_translate("DataPlotter", "Set which devices are included in analysis"))
        self.set_yupper_label.setWhatsThis(_translate("DataPlotter", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
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
        self.set_yupper_label.setText(_translate("DataPlotter", "Upper Y"))
        self.set_upper_Y.setToolTip(_translate("DataPlotter", "Set which devices are included in analysis"))

