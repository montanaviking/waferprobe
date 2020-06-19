# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'devicefinder.ui'
#
# Created: Tue Jun 27 17:09:30 2017
#      by: PyQt5 UI code generator 5.2.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_BooleanFinder(object):
    def setupUi(self, BooleanFinder):
        BooleanFinder.setObjectName("BooleanFinder")
        BooleanFinder.resize(783, 83)
        self.verticalLayout = QtWidgets.QVBoxLayout(BooleanFinder)
        self.verticalLayout.setObjectName("verticalLayout")
        self.boolean_finder_label = QtWidgets.QLabel(BooleanFinder)
        self.boolean_finder_label.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(20)
        self.boolean_finder_label.setFont(font)
        self.boolean_finder_label.setObjectName("boolean_finder_label")
        self.verticalLayout.addWidget(self.boolean_finder_label)
        self.boolean_device_finder = QtWidgets.QLineEdit(BooleanFinder)
        self.boolean_device_finder.setAcceptDrops(False)
        self.boolean_device_finder.setWhatsThis("")
        self.boolean_device_finder.setText("")
        self.boolean_device_finder.setReadOnly(False)
        self.boolean_device_finder.setObjectName("boolean_device_finder")
        self.verticalLayout.addWidget(self.boolean_device_finder)

        self.retranslateUi(BooleanFinder)
        QtCore.QMetaObject.connectSlotsByName(BooleanFinder)

    def retranslateUi(self, BooleanFinder):
        _translate = QtCore.QCoreApplication.translate
        BooleanFinder.setWindowTitle(_translate("BooleanFinder", "Dialog"))
        self.boolean_finder_label.setWhatsThis(_translate("BooleanFinder", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\"><span style=\" color:#000000;\">Boolean selector:</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Selects devices for analysis based on their names</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Default is to analyze all devices.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">This is a reverse Polish Boolean evaluator</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Operators (binary-two arguments): and, or, xor - call them bx</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Operators (unary-one argument): not - call it ux</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Format for search terms (strings) with operators bx, ux is:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">A B ba C ua bb D bc .......</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">where ba operates on A and B, ua operates on C, bb operates on the two results of</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">of ba and ua and bc this result and D. Example:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Aa Bla and Cz not and D or is equivalent to:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">((Aa and Bla) and not Cz) and D</span></p></body></html>"))
        self.boolean_finder_label.setText(_translate("BooleanFinder", "device finder"))
        self.boolean_device_finder.setToolTip(_translate("BooleanFinder", "Enter parts of device names to search separated by a space "))

