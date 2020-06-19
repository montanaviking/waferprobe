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

#directory="/home/viking/Desktop/owncloudsync/X.Selected_Measurements/Wf169/Wf169meas11/RF_power/"
#directory="/home/viking/Desktop/owncloudsync/X.Selected_Measurements/USC_Aug29_2017/RF_power/"
#directory="/home/viking/Desktop/owncloudsync/X.Selected_Measurements/Wf167/Wf167meas2/RF_power/"
#directory="/home/viking/Desktop/owncloudsync/X.Selected_Measurements/GaN_Qorvo/at_carbonics/GaN_Sept26_2017/RF_power/"
#directory="/home/viking/Desktop/owncloudsync/X.Selected_Measurements/GaN_Qorvo/at_carbonics/GaN_Jan25_2018/RF_power/"
#directory="/carbonics/owncloudsync/X.Selected_Measurements/QW10/QW10meas1/RF_power/"
directory="/carbonics/owncloudsync/X.Selected_Measurements/QH27/QH27meas2/RF_power_sweepsearch/"
#directory="/carbonics/owncloudsync/X.Selected_Measurements/QH30/QH30meas2/RF_power_searchgamma/"
#directory="/home/viking/ownCloud/X.Selected_Measurements/USC_April18_2017/RF_power/"
#filename="aligned_nanotube_Feb13_2016__Vds-1.5_Vgs-1.00_R10_C14_TOI.xls"
#filename='Wf169meas9__Vds-2.0_Vgs-0.50__C6_R5_DV3_D31_TOI.xls'
#filename='QorvoGaNX5__Vds7.0_Vgs-2.30_D12_TOI.xls'
#filename='Qorvo_GaN_GaNNX5_TOI.xls'
#filename='QH5meas5__Vds-1.5_Vgs-1.25_C6_R8_T100_D11_TOI.xls'
#filename='QH5meas5__Vds-1.5_Vgs-1.25_C6_R7_T100_D32_TOI.xls'
#filename='QH5meas5__Vds-1.5_Vgs-1.25_C7_R8_B50_D31_TOI.xls'
#filename='QH5meas5__Vds-1.5_Vgs-1.25_C8_R8_T50_D31_TOI.xls'

#filename='QW10meas1_10mS_Pin_-14.00__C9_R4_T50_D22_TOIVgssweepsearch.xls'
#filename='QH27meas2_1mS_Pin_-14.00 Vds_-1.00___C3_R6_B50_D21_TOIVgssweepsearch.xls'
filename='QH27meas2_1mS_Pin_-14.00 Vds_-1.50___C3_R6_B50_D21_TOIVgssweepsearch.xls'
#filename='QH4meas7__Vds-1.0_Vgs-2.75_C6_R6_T50_D41_TOI.xls'

#filename='Wf167meas2__Vds-1.5_Vgs-3.00__C5_R5_V22_D33_TOI.xls'
#filename='Wf169meas11__Vds-2.5_Vgs-0.40__C6_R6_DV6_D22_TOI.xls'
#filename='R19_C14_Pgain_0dBm.xls'
#filename='0.0_R10_C14_Pgain.xls'
#filename='test.csv'

sys.path.append("..")
from smithplot import SmithAxes
from smith_contour_plot import *

app=QtWidgets.QApplication(sys.argv)

sm=SmithContourPlotter(datafilename=directory+filename)
app.setActiveWindow(sm)
sm.show()
sm.raise_()
sys.exit(app.exec_())
