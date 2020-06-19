# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'slider.ui'
#
# Created: Mon May 15 16:02:42 2017
#      by: PyQt5 UI code generator 5.2.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_slidertest(object):
    def setupUi(self, slidertest):
        slidertest.setObjectName("slidertest")
        slidertest.resize(519, 795)
        self.horizontalLayout = QtWidgets.QHBoxLayout(slidertest)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.slidercontainer = QtWidgets.QHBoxLayout()
        self.slidercontainer.setObjectName("slidercontainer")
        self.horizontalLayout.addLayout(self.slidercontainer)

        self.retranslateUi(slidertest)
        QtCore.QMetaObject.connectSlotsByName(slidertest)

    def retranslateUi(self, slidertest):
        _translate = QtCore.QCoreApplication.translate
        slidertest.setWindowTitle(_translate("slidertest", "slidertest"))

