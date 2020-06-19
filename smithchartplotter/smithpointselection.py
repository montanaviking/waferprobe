# class to allow selection of reflection points from smith chart
from plotter import *
import sys
import matplotlib
matplotlib.use('Qt5Agg')
from scipy.interpolate import griddata
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from plotter_smithchart import *
from IVplot import plot_smith_selectedpoints
from utilities import formatnum, image_to_clipboard
from calculated_parameters import convertRItoMA, convertMAtoRI
Z0=50.
degree_sign= u'\N{DEGREE SIGN}'
sys.path.append("..")
from smithplot import SmithAxes

class SmithPointSelector(Ui_SmithChartPlotter,QtWidgets.QDialog):
	def __init__(self,parent=None,fignum=11,plotlabel=""):
		super(SmithPointSelector,self).__init__()
		self.setupUi(self)
		# variables
		self._Zlist=[]                  # list of normalized impedance data
		self._fignum=fignum
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		#print ("self.findex is ",self.findex) #debug
		self._fig=plt.figure(self._fignum,figsize=(20,20),frameon=False)
		self._canvas=FigureCanvas(figure=self._fig)			# set up figure canvas to interface to wafermap GUI
		self._toolbar = NavigationToolbar(self._canvas,self)
		self._toolbar.hide()
		self.plotbox.addWidget(self._canvas)		# add plot to window
		self._fig.canvas.mpl_connect('button_press_event',self.reflectionpick)
		self._fig.canvas.mpl_connect('motion_notify_event',self.coord_display)
		self.setStyleSheet("""QToolTip {
                           background-color: white;
                           color: black;
                           border: black solid 1px
                           }""")
		self.plot_label.setText(plotlabel)
		# self.clipboard_text_button.setVisible(False)    # turn off text -> clipboard  button until implemented
		# self.clipboard_text_button.setEnabled(False)    # turn off text -> clipboard button until implemented
		#self.clear_data_button.clicked.connect(self.cleardata)
		self.clipboard_image_button.clicked.connect(self.__image_data_to_clipboard)
		self.clipboard_text_button.clicked.connect(self.__text_data_to_clipboard)
		self.clipboard_text_button_array.clicked.connect(self.__text_data_to_clipboard_arrayformat)
		self.clear_data_button.clicked.connect(self.__clear_data)
		self.plotZ_points(data=self._Zlist)

	def plotZ_points(self, data):
		plot_smith_selectedpoints(data=data,datatype="Z",canvas=self._canvas,figure=self._fig)

##########################################################################
# manually select a reflection from the smith chart
	def reflectionpick(self,e):
		mods=QtWidgets.QApplication.keyboardModifiers()
		if e.button==QtCore.Qt.LeftButton and e.xdata!=None and e.ydata!=None:      # left mouse button clicked within Smith chart
			Zselected=complex(e.xdata,e.ydata)                                      # mouse-selected normalized impedance point
			if mods!=QtCore.Qt.ControlModifier:         # add point
				self._Zlist.append(Zselected)            # append normalized impedance data point to user's selected points
				self.plotZ_points(data=self._Zlist)
			elif mods==QtCore.Qt.ControlModifier and len(self._Zlist)>0:                       # remove normalized impedance data from user's selected points
				iZremoved=min(range(len(self._Zlist)),key=lambda i:abs(self._Zlist[i]-Zselected))
				Zremoved=self._Zlist[iZremoved]
				gammaselected=(Zselected-1.)/(Zselected+1.)
				gammaremoved=(Zremoved-1.)/(Zremoved+1.)
				#print("gammselected gammaremoved abs(gammaselected-gammaremoved",gammaselected,gammaremoved,abs(gammaselected-gammaremoved))
				if abs(gammaselected-gammaremoved)<0.2:         # is the selected Z point close enough to the closest Z point?
					del self._Zlist[iZremoved]          # remove the selected Z point
					self.plotZ_points(data=self._Zlist)

	def coord_display(self,e):
		#print("x y data location",e.xdata,e.ydata)
		mods=QtWidgets.QApplication.keyboardModifiers()
		if e.xdata!=None and e.ydata!=None:
			if mods==QtCore.Qt.AltModifier:                           # then display impedance
				#print("x y data location",e.xdata,e.ydata)
				displ="Z= "+formatnum(Z0*e.xdata,precision=2,nonexponential=True)+" j"+formatnum(Z0*e.ydata,precision=2,nonexponential=True)
				self.setToolTip(displ)
			else:
				z=complex(e.xdata,e.ydata)
				gamma=(z-1.)/(z+1.)
				gamma=convertRItoMA(gamma)
				displ="gamma= "+formatnum(gamma.real,precision=2,nonexponential=True)+" "+formatnum(gamma.imag,precision=2,nonexponential=True)+degree_sign
				self.setToolTip(displ)
		else: self.setToolTip("")
###############################################################################
# send Smith chart image to clipboard
	def __image_data_to_clipboard(self):
		image_to_clipboard(canvas=self._canvas)
###############################################################################
###############################################################################
# send Smith chart selected reflections magnitude, angle to clipboard
	def __text_data_to_clipboard(self):
		clipb=QtWidgets.QApplication.clipboard()
		clipb.setText("")       # clear clipboard
		gamma=[[convertRItoMA((z-1)/(z+1)).real,convertRItoMA((z-1)/(z+1)).imag] for z in self._Zlist]        # convert normalized selected impedances to reflection coefficients (magnitude and angle) [[mag1,ang1],[mag2,ang2],...]
		clipbtext="# gamma magnitude\tgamma angle degrees"
		if len(gamma)>0:
			for g in gamma:
				clipbtext="".join([clipbtext,"\n",formatnum(g[0],precision=3,nonexponential=True),"\t",formatnum(g[1],precision=3,nonexponential=True)])
			clipb.setText(clipbtext)
		else:
			message=QtWidgets.QMessageBox()
			message.setText("WARNING! No reflection data")
			message.exec_()
###############################################################################
# send Smith chart selected reflections magnitude, angle to clipboard
# same as above but formatted as 2-d array [[mag,angle],[mag,angle],...]
	def __text_data_to_clipboard_arrayformat(self):
		clipb=QtWidgets.QApplication.clipboard()
		clipb.setText("")       # clear clipboard
		clipbtext="[ "
		gamma=[[convertRItoMA((z-1)/(z+1)).real,convertRItoMA((z-1)/(z+1)).imag] for z in self._Zlist]        # convert normalized selected impedances to reflection coefficients (magnitude and angle) [[mag1,ang1],[mag2,ang2],...]
		clipbtext="".join(["[ [",formatnum(gamma[0][0],precision=3,nonexponential=True),",",formatnum(gamma[0][1],precision=3,nonexponential=True),"]"])
		if len(gamma)>0:
			for i in range(1,len(gamma)):
				clipbtext="".join([clipbtext,", [",formatnum(gamma[i][0],precision=3,nonexponential=True),",",formatnum(gamma[i][1],precision=3,nonexponential=True),"]"])
			clipbtext="".join([clipbtext," ]"])
			clipb.setText(clipbtext)
		else:
			message=QtWidgets.QMessageBox()
			message.setText("WARNING! No reflection data")
			message.exec_()
###############################################################################
# clear all selected data points from Smith Chart
	def __clear_data(self):
		self._Zlist=[]
		self.plotZ_points(data=self._Zlist)
#########################################################################################################################
# return Smith chart selected reflections
# return type is 'ri' real+jimaginary and 'ma' -> magnitude+jangle (degrees)
# return reflection coefficients (gamma) are those to be actually set by the Focus tuner
# NOT IMPLEMENTED YET
#
	def get_selected_reflection_coefficients_focus(self,tuner=None):
		gamma_ri=[(z-1)/(z+1) for z in self._Zlist]        # convert normalized selected impedances to reflection coefficients (real+jimaginary) array of complex numbers
		gamma_ma=[convertRItoMA((z-1)/(z+1)) for z in self._Zlist]        # convert normalized selected impedances to reflection coefficients (magnitude and angle) [[mag1,ang1],[mag2,ang2],...]
#########################################################################################################################
# perform and return a 2-dimensional cubic spline fit of a parameter vs reflection coefficient on the Smith chart
# reflections are in the format [[mag1,angle1],[mag2,angle2],[mag3,angle3],...]
# parameter is a list of values to plot - one value for each mag,ang pair in reflections
# returns the minimum and/or maximum fit value of the parameter and the corresponding reflection coefficient
# NOT IMPLEMENTED YET
	def smithfitspline(self,reflections=None,parameters=None):
		if len(reflections)!=len(parameters): raise ValueError("ERROR! number of x,y pairs is not equal to the number of Z values")
		npoints=100
		# convert reflections to [real,imaginary] which are both floating numbers
		# gammas is an array of arrays of form [[real1,imaginary1],[real,imaginary2],......]
		#gammas=np.array([[convertMAtoRI(mag=r[0],ang=r[1]).real,convertMAtoRI(mag=r[0],ang=r[1]).imag] for r in reflections])
		gammas=np.array([convertMAtoRI(mag=r[0],ang=r[1]) for r in reflections])
		zsri=np.divide(np.add(1,gammas),np.subtract(1,gammas))            # convert reflections to normalized impedance
		zs=np.array([z.real,z.imag] for z in zsri)                        # convert real+jimaginary normalized impedance to [real,imaginary] (both floats)

		# find min and max of real and imaginary parts
		zmin_real=np.min(zs[:][0])
		zmax_real=np.max(zs[:][0])
		zmin_imag=np.min(zs[:][1])
		zmax_imag=np.min(zs[:][1])
		rr,ri=np.meshgrid(np.linspace(zmin_real,zmax_real,npoints),np.linspace(zmin_imag,zmax_imag,npoints))            # set up grid to hold calculated interpolated results
		paragrid=griddata(zs,parameters,(rr,ri),method='cubic')
		return paragrid



