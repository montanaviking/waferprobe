__author__ = 'viking'
#### main file for wafer graph test

import sys

from test.actions_wafergraph_test_map import *

if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)
	ex = WaferGraph()
	#ex2=UIwafer()

	ex.show()
	ex.raise_()
	#ex2.show()
	##ex2.raise_()

	sys.exit(app.exec_())
