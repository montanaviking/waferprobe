__author__ = 'viking'
#### main file for slider test

import sys

from actions_slider import *

if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	ex = Slider()

	ex.show()
	ex.raise_()

	sys.exit(app.exec_())
