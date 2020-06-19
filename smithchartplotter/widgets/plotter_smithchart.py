# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'plotter_smithchart.ui'
#
# Created: Wed Aug  9 13:59:27 2017
#      by: PyQt5 UI code generator 5.2.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SmithChartPlotter(object):
    def setupUi(self, SmithChartPlotter):
        SmithChartPlotter.setObjectName("SmithChartPlotter")
        SmithChartPlotter.resize(960, 698)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(SmithChartPlotter)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.plot_label = QtWidgets.QLabel(SmithChartPlotter)
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.plot_label.setFont(font)
        self.plot_label.setObjectName("plot_label")
        self.verticalLayout.addWidget(self.plot_label)
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
        self.clear_data_button = QtWidgets.QPushButton(SmithChartPlotter)
        self.clear_data_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clear_data_button.setCheckable(True)
        self.clear_data_button.setObjectName("clear_data_button")
        self.horizontalLayout.addWidget(self.clear_data_button)
        self.clipboard_image_button = QtWidgets.QPushButton(SmithChartPlotter)
        self.clipboard_image_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clipboard_image_button.setObjectName("clipboard_image_button")
        self.horizontalLayout.addWidget(self.clipboard_image_button)
        self.clipboard_text_button = QtWidgets.QPushButton(SmithChartPlotter)
        self.clipboard_text_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clipboard_text_button.setObjectName("clipboard_text_button")
        self.horizontalLayout.addWidget(self.clipboard_text_button)
        self.clipboard_text_button_array = QtWidgets.QPushButton(SmithChartPlotter)
        self.clipboard_text_button_array.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clipboard_text_button_array.setObjectName("clipboard_text_button_array")
        self.horizontalLayout.addWidget(self.clipboard_text_button_array)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.retranslateUi(SmithChartPlotter)
        QtCore.QMetaObject.connectSlotsByName(SmithChartPlotter)

    def retranslateUi(self, SmithChartPlotter):
        _translate = QtCore.QCoreApplication.translate
        SmithChartPlotter.setWindowTitle(_translate("SmithChartPlotter", "Data Plot"))
        self.plot_label.setText(_translate("SmithChartPlotter", "Device"))
        self.clear_data_button.setWhatsThis(_translate("SmithChartPlotter", "<html><head/><body><p><span style=\" color:#000000;\">Send tabular data to the clipboard.</span></p></body></html>"))
        self.clear_data_button.setText(_translate("SmithChartPlotter", "&clear data"))
        self.clipboard_image_button.setWhatsThis(_translate("SmithChartPlotter", "<html><head/><body><p><span style=\" color:#000000;\">Send tabular data to the clipboard.</span></p></body></html>"))
        self.clipboard_image_button.setText(_translate("SmithChartPlotter", "send &image to clipboard"))
        self.clipboard_text_button.setWhatsThis(_translate("SmithChartPlotter", "<html><head/><body><p><span style=\" color:#000000;\">Send tabular data to the clipboard.</span></p></body></html>"))
        self.clipboard_text_button.setText(_translate("SmithChartPlotter", "send &text to clipboard"))
        self.clipboard_text_button_array.setWhatsThis(_translate("SmithChartPlotter", "<html><head/><body><p><span style=\" color:#000000;\">Send tabular data to the clipboard.</span></p></body></html>"))
        self.clipboard_text_button_array.setText(_translate("SmithChartPlotter", "send text to clipboard array format"))

