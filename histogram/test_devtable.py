__author__ = 'viking'
import sys

from devtable import *

if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)
	hheader=["|Idmax|","onoffratio"]
	vheader=["dev1","dev2","dev3","dev5"]
	dat = [[1.2, 4.],['xx',1E9],[1E-5,1.1E3],['a',1.1E-3]]
	ex = DevTable()
	ex.setup(hheaders=hheader,vheaders=vheader,data=dat)


	ex.show()
	ex.raise_()
	#ex2.show()
	##ex2.raise_()

	sys.exit(app.exec_())