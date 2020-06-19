__author__ = 'viking'
#### main file for wafer graph test

import sys
from PyQt4 import QtCore, QtGui
from actions_wafergraph import *

if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)
	ex = WaferGraph()
	#ex2=UIwafer()

	ex.show()
	ex.raise_()
	#ex2.show()
	##ex2.raise_()

	sys.exit(app.exec_())
