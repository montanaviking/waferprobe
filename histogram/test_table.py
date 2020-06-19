# table tester
__author__ = 'viking'
import sys
from actions_statistics_dump import *
if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)

	ex = StatisticsDump()

	#ex2=UIwafer()

	ex.show()
	ex.raise_()


	sys.exit(app.exec_())