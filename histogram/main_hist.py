#!/usr/bin/python3.4
#!/usr/env python3
__author__ = 'PMarsh Carbonics Inc'

###################
# main program
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from actions_histogram import *

def figsindex(inc=[0]):
	inc[0]+=1
	return inc[0]


if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	ex = WaferHist()
	app.setActiveWindow(ex)
	ex.show()
	ex.raise_()
	#app.exec_()
	sys.exit(app.exec_())

