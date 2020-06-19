# class to allow plotting of parameter contours of a parameter vs reflection coefficient, on the smith chart
from plotter import *

import sys
import math
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib import cm
from scipy.interpolate import griddata
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from plotter_smithchart import *
from IVplot import plot_smith_selectedpoints
from utilities import formatnum, image_to_clipboard
from calculated_parameters import convertRItoMA, convertMAtoRI
from read_reflection_parametervsreflection import read_OIP3_vs_reflection_coefficients
matplotlib.use('Qt5Agg')
Z0=50.
degree_sign= u'\N{DEGREE SIGN}'
sys.path.append("..")
from smithplot import SmithAxes

class SmithContourPlotter(Ui_SmithChartPlotter,QtWidgets.QDialog):
	def __init__(self,parent=None,fignum=11,plotlabel="contour plot",datafilename=""):
		super(SmithContourPlotter,self).__init__()
		self.setupUi(self)
		# variables
		if datafilename==None or datafilename=="": raise ValueError("ERROR! Must give data filename")
		self._filename=datafilename


		self._Zlist=[]                  # list of normalized impedance data
		self._fignum=fignum
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		#print ("self.findex is ",self.findex) #debug
		self._fig=plt.figure(self._fignum,figsize=(20,20),frameon=False)
		self._canvas=FigureCanvas(figure=self._fig)			# set up figure canvas to interface to wafermap GUI
		self._toolbar = NavigationToolbar(self._canvas,self)
		self._toolbar.hide()
		self.plotbox.addWidget(self._canvas)		# add plot to window
		#self._fig.canvas.mpl_connect('button_press_event',self.reflectionpick)
		self._fig.canvas.mpl_connect('motion_notify_event',self.coord_parameter_display)
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
		self.clear_data_button.clicked.connect(self.__clear_data)
		self.plot()

	# def plot(self, data):
	# 	plot_smith_selectedpoints(data=data,datatype="S",canvas=self._canvas,figure=self._fig)

##########################################################################
# # manually select a reflection from the smith chart
# and show the interpolated parameter value at the cursor point
# self.plot() MUST be called before this
	def coord_parameter_display(self,e):
		#print("x y data location",e.xdata,e.ydata)
		mods=QtWidgets.QApplication.keyboardModifiers()
		if e.xdata!=None and e.ydata!=None:
			# find value of parameter to display
			z=complex(e.xdata,e.ydata)
			gamma_ri=(z-1.)/(z+1.)
			gamma=convertRItoMA(gamma_ri)                   # convert reflection coefficient to magnitude + jangle (degrees)
			# 2D index of best fit to reflection coefficient under pointer
			ir=min(range(len(self._ref_real_int)), key=lambda i: abs(self._ref_real_int[i]-gamma_ri.real))
			ii=min(range(len(self._ref_imag_int)), key=lambda i: abs(self._ref_imag_int[i]-gamma_ri.imag))
			parametervalue=self._paraplotint[ii,ir]                     # get parameter at closest reflection coefficient pointed to plot. note that the order of the indices is y,x i.e. [index of imaginary, index of real]
			if mods==QtCore.Qt.AltModifier:                           # then display impedance
				#print("x y data location",e.xdata,e.ydata,ii,ir)
				if not math.isnan(parametervalue):
					displ="".join(["Z= ",formatnum(Z0*e.xdata,precision=2,nonexponential=True)," j",formatnum(Z0*e.ydata,precision=2,nonexponential=True)," data= ",formatnum(parametervalue,precision=2,nonexponential=True)])
				else:
					displ="".join(["Z= ",formatnum(Z0*e.xdata,precision=2,nonexponential=True)," j",formatnum(Z0*e.ydata,precision=2,nonexponential=True)])
				self.setToolTip(displ)
			else:
				if not math.isnan(parametervalue):
					displ="".join(["gamma= ",formatnum(gamma.real,precision=2,nonexponential=True)," ",formatnum(gamma.imag,precision=2,nonexponential=True),degree_sign," data= ",formatnum(parametervalue,precision=2,nonexponential=True)])
					             # " gammaint= ",formatnum(self._ref_real_int[ir],precision=2,nonexponential=True)," j",formatnum(self._ref_imag_int[ii],precision=2,nonexponential=True)])
				else:
					displ="".join(["gamma= ",formatnum(gamma.real,precision=2,nonexponential=True)," ",formatnum(gamma.imag,precision=2,nonexponential=True),degree_sign])
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
		clipbtext="gamma magnitude\tgamma angle degrees"
		if len(gamma)>0:
			for g in gamma:
				clipbtext="".join([clipbtext,"\n",formatnum(g[0],precision=3,nonexponential=True),"\t",formatnum(g[1],precision=3,nonexponential=True)])
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
# plot contours of a parameter vs tuning using 2-dimensional cubic spline fit of a parameter vs reflection coefficient on the Smith chart
# returns the minimum and/or maximum fit value of the parameter and the corresponding reflection coefficient
	def plot(self):
		nopts=100
		ret=read_OIP3_vs_reflection_coefficients(self._filename)
		if ret[0].lower()=="toi": type,Rho,outputTOI_average,gain=ret
		elif len(ret)==3: Rho,outputTOI_average,Pout=ret
		minreflectionreal=np.min(np.real(Rho))
		maxreflectionreal=np.max(np.real(Rho))
		minreflectionimag=np.min(np.imag(Rho))
		maxreflectionimag=np.max(np.imag(Rho))

		# minreflectionreal=-1.
		# maxreflectionreal=1.
		# minreflectionimag=-1.
		# maxreflectionimag=1.
		self._ref_real_int=np.linspace(minreflectionreal,maxreflectionreal,nopts)         # real reflection coefficient on the interpolated grid
		self._ref_imag_int=np.linspace(minreflectionimag,maxreflectionimag,nopts)         # imaginary reflection coefficient on the interpolated grid
		# print(len(outputTOI_average))
		# print(len(np.real(Rho)))

		self._paraplotint=griddata((np.real(Rho),np.imag(Rho)),outputTOI_average,(self._ref_real_int[None,:] ,self._ref_imag_int[:,None]),method='linear',fill_value=-9999999) # 2D cubic spline interpolation (x,y,z)

		Preint,Pimint=np.meshgrid(self._ref_real_int,self._ref_imag_int)

		levels=np.linspace(min(outputTOI_average),max(outputTOI_average),20)
		Rhoint=[[complex(Preint[i][j],Pimint[i][j]) for j in range(0,np.shape(Preint)[1]) ] for i in range(0,np.shape(Preint)[0])]

		irmax,iimax=np.unravel_index(self._paraplotint.argmax(),self._paraplotint.shape)
		print(irmax,iimax,self._paraplotint[irmax][iimax],convertRItoMA(Rhoint[irmax][iimax]))
		self._paraplotint=griddata((np.real(Rho),np.imag(Rho)),outputTOI_average,(self._ref_real_int[None,:] ,self._ref_imag_int[:,None]),method='linear') # 2D linear spline interpolation (x,y,z)
		Zreint=[[((1+Rhoint[i][j])/(1-Rhoint[i][j])).real for j in range(0,np.shape(Rhoint)[1])] for i in range(0,np.shape(Rhoint)[0])]
		Zimint=[[((1+Rhoint[i][j])/(1-Rhoint[i][j])).imag for j in range(0,np.shape(Rhoint)[1])] for i in range(0,np.shape(Rhoint)[0])]

		znorm=[(1+Rho[i])/(1-Rho[i]) for i in range(0,len(Rho))]

		ax=self._fig.add_subplot(1,1,1,projection='smith')
		#ax=self._fig.add_subplot(1,1,1)
		#print(self._paraplotint)
		#print(Rhoint)
		ax.contourf(Zreint,Zimint,self._paraplotint,levels=levels,zorder=10,datatype='SmithAxes.S_PARAMETER')
		#print(Zreint)
		#ax.contourf(np.real(Rhoint),np.imag(Rhoint),self._paraplotint,levels=levels,zorder=10)
		ax.scatter(np.real(znorm),np.imag(znorm),zorder=11,color='black')
		#ax.plot_surface(X=Zreint,Y=Zimint,Z=self._paraplotint,cmap=cm.coolwarm,linewidth=0, antialiased=False)
		#ax.plot_surface(X=np.real(Rhoint),Y=np.imag(Rhoint),Z=self._paraplotint,cmap=cm.coolwarm,linewidth=0, antialiased=False)
		#ax.scatter(np.real(Rho),np.imag(Rho),zorder=11,color='black')
		#ax.clabel(CS,inline=1,fontsize=5,datatype='SmithAxes.S_PARAMETER')
		ax.grid(True)
		#plt.show()
		#self._canvas.draw()