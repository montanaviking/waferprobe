# test clipboard
from PyQt4 import QtCore, QtGui
#from fileview import *
import sys
a=QtGui.QApplication(sys.argv)
clipb=a.clipboard()							# set up clipboard
clipb.setText("test clipboard")
del a
