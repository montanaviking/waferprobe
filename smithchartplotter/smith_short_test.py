#!/usr/bin/env python3

import sys
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
#from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
#from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

import numpy as np
from matplotlib import pyplot as plt

sys.path.append("..")
from smithplot import SmithAxes
from smithpointselection import *
#pp.figure=plt.figure(1,figsize=(12,12),frameon=False)
# figcanvas=FigureCanvas(figure=plt.figure(1,figsize=(12,12),frameon=False))
#
# # sample data
# data = np.loadtxt("data/s11.csv", delimiter=",", skiprows=1)[::100]
# val1 = data[:, 1] + data[:, 2] * 1j
#
# data = np.loadtxt("data/s22.csv", delimiter=",", skiprows=1)[::100]
#val2 = data[:, 1] + data[:, 2] * 1j

#ax = plt.subplot(1, 1, 1, projection='smith')

#ax.plot(50 * val1, label="default", interpolate=2,datatype=SmithAxes.Z_PARAMETER)
#
# ax.legend(loc="lower right", fontsize=12)
# ax.set_title("Matplotlib Smith Chart Projection")
# plt.savefig("export.pdf", format="pdf", bbox_inches="tight")
app=QtWidgets.QApplication(sys.argv)

sm=SmithPointSelector()
app.setActiveWindow(sm)
sm.show()
sm.raise_()
sys.exit(app.exec_())
