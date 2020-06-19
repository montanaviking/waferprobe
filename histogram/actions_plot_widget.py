__author__ = 'viking'
import matplotlib
matplotlib.use('Qt5Agg')
# plots various parameters to widget pop-ups
# parent widget is plotter.ui
##import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
#from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

#from IVplot import plot_transfer, plot_family_of_curves, plot_Yf, plot_Umax
from IVplot import *
from plotter import *
from utilities import *
#from utilities import Yf_text_to_clipboard


class PlotGraphWidget(Ui_DataPlotter,QtWidgets.QDialog):
	def __init__(self,parent=None,dev=None,plottype=None,fignum=11):
		super(PlotGraphWidget,self).__init__(parent)
		if dev==None: raise ValueError("ERROR! no device data provided")

		self.setupUi(self)
		self.plottype=plottype
		self.dev=dev
		self.removeleakage=False

		self.figureplot =plt.figure(fignum,figsize=(12,12),frameon=False)
		#print ("self.findex is ",self.findex) #debug
		self.canvas=FigureCanvas(self.figureplot)			# set up figure canvas to interface to wafermap GUI
		self.toolbar = NavigationToolbar(self.canvas,self)
		self.toolbar.hide()
		self.plotbox.addWidget(self.canvas)		# add plot to window
		self.wafer_label.setText("Device: "+self.dev.get_devicename())
		self.clipboard_text_button.clicked.connect(self.__text_data_to_clipboard)
		self.clipboard_image_button.clicked.connect(self.__image_data_to_clipboard)
		self.linear_fit_lines_button.clicked.connect(self.__linearfitlinestoggle)						# toggle linear fit (family of curves) or spline fit (transfer curves) on plots
		self.legend_toggle_button.clicked.connect(self.__legendtoggle)									# toggle legend on plots
		self.add_Ig_button.clicked.connect(self.__igaddtoggle)                                          # allows user to add Ig vs Vgs to transfer curves
		self.remove_leakage_Id_button.clicked.connect(self.__removeIdleakage)                              # allows user to elect to remove or not remove leakage drain current i.e. the minimum Id - from the single-sweep transfer curve
		self.loglinear_yscale_button.clicked.connect(self.__loglinearset_y)                               # allows user to select linear or log y-scale

		self.loglinear_yscale_button.setVisible(False)
		self.loglinear_yscale_button.setEnabled(False)
		self.loglinear_yscale_button.setCheckable(True)
		self.loglinear_yscale_button.setChecked(False)
		self.loglinear_yscale_button.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(100,200,255)}')
		self.loglinear_yscale_button.setText("linear Y scale")

		self.remove_leakage_Id_button.setVisible(False)
		self.remove_leakage_Id_button.setEnabled(False)
		self.remove_leakage_Id_button.setCheckable(True)
		self.remove_leakage_Id_button.setChecked(False)
		self.remove_leakage_Id_button.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(100,200,255)}')
		self.remove_leakage_Id_button.setText("Id leakage not removed")

		self.VgsFOClabel.setVisible(False)
		self.VgsFOCselector.setVisible(False)
		self.VgsFOCselector.setEnabled(False)
		self.VgsFOCselector.blockSignals(True)

		if self.plottype=='4_swept_family_of_curves':
			self.VgsFOCselector.clear()
			# add Vgs values
			self.VgsFOCselector.addItem("All")          # indicates to show the entire family of curves data (FOC)
			for ii in range(0, len(self.dev.Vgs_4loopfoc1)):
				self.VgsFOCselector.addItem(formatnum(self.dev.Vgs_4loopfoc1[ii][0],precision=2))
		elif self.plottype=='double_swept_family_of_curves':
			self.VgsFOCselector.clear()
			# add Vgs values
			self.VgsFOCselector.addItem("All")          # indicates to show the entire family of curves data (FOC)
			for ii in range(0, len(self.dev.Vgs_loopfoc1)):
				self.VgsFOCselector.addItem(formatnum(self.dev.Vgs_loopfoc1[ii][0],precision=2))
		elif self.plottype=='family_of_curves':
			self.VgsFOCselector.clear()
			# add Vgs values
			self.VgsFOCselector.addItem("All")          # indicates to show the entire family of curves data (FOC)
			for ii in range(0, len(self.dev.Vgs_IVfoc)):
				self.VgsFOCselector.addItem(formatnum(self.dev.Vgs_IVfoc[ii][0],precision=2))

		self.add_Ig_button.setVisible(False)
		self.add_Ig_button.setEnabled(False)
		self.add_Ig_button.setCheckable(True)
		self.add_Ig_button.setChecked(False)

		self.legend_toggle_button.setEnabled(False)
		self.legend_toggle_button.setVisible(False)
		self.legend_toggle_button.setCheckable(True)
		self.legend_toggle_button.setChecked(True)

		self.VgsFOCselector.currentIndexChanged.connect(self.__selectVgs)

		self._xmin=None
		self._xmax=None
		self._ymin=None
		self._ymax=None

		#self.updateplot_button.clicked(self.__)

		self.set_lower_X.editingFinished.connect(self.__set_Xmin)
		self.set_upper_X.editingFinished.connect(self.__set_Xmax)
		self.set_lower_Y.editingFinished.connect(self.__set_Ymin)
		self.set_upper_Y.editingFinished.connect(self.__set_Ymax)

		parent.RefreshDeviceData.connect(self.__plot)
		#print("from line 78 in actions_plot_widget.py parent=",parent)

		self.linear_fit_lines_button.setEnabled(False)
		self.linear_fit_lines_button.setVisible(False)
		self.linear_fit_lines_button.setCheckable(True)
		self.linear_fit_lines_button.setChecked(False)											# default is to not plot least squares linear fit lines on the graphs
		if self.plottype=='Yf': self.linear_fit_lines_button.setChecked(True)					# however the default is to plot least squares linear fit lines for Y functions
		#print('from actions_plot_widget.py line 35',self.plottype)
		self.__plot()
		#
	def __plot(self):
		#print('from actions_plot_widget.py line 89',self.plottype)
		self.linear_fit_lines_button.setEnabled(False)
		self.linear_fit_lines_button.setVisible(False)
		self.clipboard_text_button.setVisible(True)
		self.clipboard_text_button.setEnabled(True)
		self.remove_leakage_Id_button.setVisible(False)
		self.remove_leakage_Id_button.setEnabled(False)
		self.add_Ig_button.setVisible(False)
		self.add_Ig_button.setEnabled(False)
		self.loglinear_yscale_button.setVisible(False)
		self.loglinear_yscale_button.setEnabled(False)

		if self.plottype=='gm_T':
			self.legend_toggle_button.setVisible(True)
			self.legend_toggle_button.setEnabled(True)
			plot_gm(self.dev,figure=self.figureplot,canvas=self.canvas,single_double='single',legendon=self.legend_toggle_button.isChecked(),xmin=self._xmin,xmax=self._xmax,ymin=self._ymin,ymax=self._ymax)
		if self.plottype=='gm_TFR':
			self.legend_toggle_button.setVisible(True)
			self.legend_toggle_button.setEnabled(True)
			plot_gm(self.dev,figure=self.figureplot,canvas=self.canvas,single_double='double',legendon=self.legend_toggle_button.isChecked())
		if self.plottype=='family_of_curves':
			self.clipboard_text_button.setVisible(False)                                        # turn off send data to clipboard since this doesn't work yet
			self.clipboard_text_button.setEnabled(False)
			self.linear_fit_lines_button.setVisible(True)
			self.linear_fit_lines_button.setEnabled(True)
			self.VgsFOClabel.setVisible(True)
			self.VgsFOCselector.setVisible(True)
			self.VgsFOCselector.setEnabled(True)
			self.VgsFOCselector.blockSignals(False)
			plot_family_of_curves(self.dev,figure=self.figureplot,canvas=self.canvas,plotlin=self.linear_fit_lines_button.isChecked(),xmin=self._xmin,xmax=self._xmax,ymin=self._ymin,ymax=self._ymax, Vgs=self.VgsFOCselector.currentText())
		if self.plottype=='double_swept_family_of_curves':
			self.clipboard_text_button.setVisible(False)                                        # turn off send data to clipboard since this doesn't work yet
			self.clipboard_text_button.setEnabled(False)
			self.linear_fit_lines_button.setVisible(False)
			self.linear_fit_lines_button.setEnabled(False)
			self.VgsFOClabel.setVisible(True)
			self.VgsFOCselector.setVisible(True)
			self.VgsFOCselector.setEnabled(True)
			self.VgsFOCselector.blockSignals(False)
			plot_family_of_curves_loop(self.dev,figure=self.figureplot,canvas=self.canvas,xmin=self._xmin,xmax=self._xmax,ymin=self._ymin,ymax=self._ymax, Vgs=self.VgsFOCselector.currentText())
		if self.plottype=='4_swept_family_of_curves':
			self.clipboard_text_button.setVisible(False)                                        # turn off send data to clipboard since this doesn't work yet
			self.clipboard_text_button.setEnabled(False)
			self.linear_fit_lines_button.setVisible(False)
			self.linear_fit_lines_button.setEnabled(False)
			self.VgsFOClabel.setVisible(True)
			self.VgsFOCselector.setVisible(True)
			self.VgsFOCselector.setEnabled(True)
			self.VgsFOCselector.blockSignals(False)
			plot_family_of_curves_4loop(self.dev,figure=self.figureplot,canvas=self.canvas,xmin=self._xmin,xmax=self._xmax,ymin=self._ymin,ymax=self._ymax,Vgs=self.VgsFOCselector.currentText())
		if self.plottype=='TLM':
			plotTLM(self.dev,figure=self.figureplot,canvas=self.canvas,xmin=self._xmin,xmax=self._xmax,ymin=self._ymin,ymax=self._ymax)
		if self.plottype=='Yf':		# plot the Y-function
			self.linear_fit_lines_button.setVisible(True)
			self.linear_fit_lines_button.setEnabled(True)
			self.wafer_label.setText("".join(["Device: ",self.dev.get_devicename()," Y factor Rc= ",formatnum(self.dev.Rc_T(),precision=2)," ohms"]))
			plot_Yf(self.dev,plotlin=self.linear_fit_lines_button.isChecked(),figure=self.figureplot,canvas=self.canvas,xmin=self._xmin,xmax=self._xmax,ymin=self._ymin,ymax=self._ymax)
		if self.plottype=='single transfer':
			self.linear_fit_lines_button.setVisible(True)
			self.linear_fit_lines_button.setEnabled(True)
			self.legend_toggle_button.setVisible(True)
			self.legend_toggle_button.setEnabled(True)
			self.remove_leakage_Id_button.setVisible(True)
			self.remove_leakage_Id_button.setEnabled(True)
			self.loglinear_yscale_button.setVisible(True)
			self.loglinear_yscale_button.setEnabled(True)
			if not self.removeleakage:                      # plot Ig ONLY if leakage (i.e. due to minimum Id) is removed
				self.add_Ig_button.setVisible(True)
				self.add_Ig_button.setEnabled(True)
			else:
				self.add_Ig_button.setVisible(False)
				self.add_Ig_button.setEnabled(False)
			plot_transfer(self.dev,figure=self.figureplot,canvas=self.canvas,removeleakage=self.removeleakage,single_double='single',plotsplinefit=self.linear_fit_lines_button.isChecked(),legendon=self.legend_toggle_button.isChecked(),plotIg=self.add_Ig_button.isChecked(),logplot=self.loglinear_yscale_button.isChecked(),xmin=self._xmin,xmax=self._xmax,ymin=self._ymin,ymax=self._ymax)
		if self.plottype=='double transfer':
			self.linear_fit_lines_button.setVisible(True)
			self.linear_fit_lines_button.setEnabled(True)
			self.legend_toggle_button.setVisible(True)
			self.legend_toggle_button.setEnabled(True)
			self.loglinear_yscale_button.setVisible(True)
			self.loglinear_yscale_button.setEnabled(True)
			if not self.removeleakage:                      # plot Ig ONLY if leakage (i.e. due to minimum Id) is removed
				self.add_Ig_button.setVisible(True)
				self.add_Ig_button.setEnabled(True)
			else:
				self.add_Ig_button.setVisible(False)
				self.add_Ig_button.setEnabled(False)
			plot_transfer(self.dev,figure=self.figureplot,canvas=self.canvas,removeleakage=self.removeleakage,single_double='double',plotsplinefit=self.linear_fit_lines_button.isChecked(),
			              legendon=self.legend_toggle_button.isChecked(),plotIg=self.add_Ig_button.isChecked(),logplot=self.loglinear_yscale_button.isChecked(),xmin=self._xmin,xmax=self._xmax,ymin=self._ymin,ymax=self._ymax)
		if 'db'.lower() in self.plottype.lower():
			plot_twoportparameters_dB(self.dev,figure=self.figureplot,canvas=self.canvas,type=self.plottype,xmin=self._xmin,xmax=self._xmax,ymin=self._ymin,ymax=self._ymax)				#plot selected S-parameter or UMAX or GMAX on a dB graph

		if 'time_domain_from_pulsedVgs'.lower() in self.plottype.lower():
			self.legend_toggle_button.setVisible(True)
			self.legend_toggle_button.setEnabled(True)
			self.loglinear_yscale_button.setVisible(True)
			self.loglinear_yscale_button.setEnabled(True)
			self.add_Ig_button.setVisible(True)
			self.add_Ig_button.setEnabled(True)
			plot_pulsedVgs_timedomain(self.dev,figure=self.figureplot,canvas=self.canvas,legendon=self.legend_toggle_button.isChecked(),logplot=self.loglinear_yscale_button.isChecked(),plotIg=self.add_Ig_button.isChecked(),xmin=self._xmin,xmax=self._xmax,ymin=self._ymin,ymax=self._ymax)

		if 'time_domain_from_pulsedVds'.lower() in self.plottype.lower():
			self.legend_toggle_button.setVisible(True)
			self.legend_toggle_button.setEnabled(True)
			self.loglinear_yscale_button.setVisible(True)
			self.loglinear_yscale_button.setEnabled(True)
			self.add_Ig_button.setVisible(True)
			self.add_Ig_button.setEnabled(True)
			plot_pulsedVds_timedomain(self.dev,figure=self.figureplot,canvas=self.canvas,legendon=self.legend_toggle_button.isChecked(),logplot=self.loglinear_yscale_button.isChecked(),plotIg=self.add_Ig_button.isChecked(),xmin=self._xmin,xmax=self._xmax,ymin=self._ymin,ymax=self._ymax)
		plt.close()				# necessary to prevent plot interactions between instances of this class
		#else: raise ValueError("ERROR! No plot type given")

	############################################
	# send text data to clipboard
	def __text_data_to_clipboard(self):
		if self.plottype=='Yf':	Yf_text_to_clipboard(cd=self.dev)				# send plotted text data to clipboard
		elif self.plottype=='single transfer': Id_text_single_swept_transfer_to_clipboard(cd=self.dev)
		elif self.plottype=='double transfer': Id_text_double_swept_transfer_to_clipboard(cd=self.dev)
		elif self.plottype=='gmaxdb': Gmax_text_to_clipboard(cd=self.dev)
		elif 's11db'.lower() in self.plottype.lower() or 's22db' in self.plottype.lower() or 's21db'.lower() in self.plottype.lower(): twopportparameters_dB_text_to_clipboard(cd=self.dev)
		#if self.plottype=='umaxdb':
		elif self.plottype=='h21db': H21_text_to_clipboard(cd=self.dev)
		elif self.plottype=='gm_T': gm_single_swept_transfer_text_to_clipboard(cd=self.dev)
		elif self.plottype=='gm_TFR': gm_dual_swept_transfer_text_to_clipboard(cd=self.dev)
		elif self.plottype=='TLM': TLM_text_to_clipboard(cd=self.dev)
		elif self.plottype=='umaxdb': Umax_text_to_clipboard(cd=self.dev)
	################################################################################
	# send graphics data to clipboard
	def __image_data_to_clipboard(self):
		#if self.plottype=='Yf':	Yf_text_to_clipboard(cd=self.dev)				# send plotted text data to clipboard
		if self.plottype!=None: image_to_clipboard(canvas=self.canvas)
	################################################################################
	# user toggled least squares linear fit lines or spline fit lines
	def __linearfitlinestoggle(self):
		self.__plot()
	################################################################################
	# user toggled the legend toggle
	def __legendtoggle(self):
		self.__plot()
	################################################################################
	# user toggled the add Ig button to add gate current vs Vgs to Id vs Vgs plot (at constant Vds, i.e. the transfer curve
	def __igaddtoggle(self):
		self.__plot()
	################################################################################
	# user toggled the button to remove the minimum Id i.e. the leakage current from the Id(Vgs) plot of the transfer curve
	def __removeIdleakage(self):
		if self.remove_leakage_Id_button.isChecked():       #User has selected to remove leakage current
			self.remove_leakage_Id_button.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(0,120,255)}')
			self.remove_leakage_Id_button.setText("Id leakage removed")
			self.removeleakage=True
			# remove option to plot Ig if leakage is removed
			#self.add_Ig_button.setChecked(False)
			self.add_Ig_button.setEnabled(False)
			self.add_Ig_button.setVisible(False)
		else:
			self.remove_leakage_Id_button.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(100,200,255)}')
			self.remove_leakage_Id_button.setText("Id leakage not removed")
			self.removeleakage=False
		self.__plot()
	################################################################################
	# user toggled the button to plot linear or log y-scale
	def __loglinearset_y(self):
		if self.loglinear_yscale_button.isChecked():        # User has selected the Y scale to be log
			self.loglinear_yscale_button.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(0,120,255)}')
			self.loglinear_yscale_button.setText("Log Y scale")
		else:                                               # User has selected the Y scale to be linear
			self.loglinear_yscale_button.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(100,200,255)}')
			self.loglinear_yscale_button.setText("Linear Y scale")
		self.__plot()
	################################################################################
	# # are the plot limits legal?
	# def __legalplotlimits(self):
	# 	if self.set_lower_X.text()!=
	################################################################################
	# user set lower X value
	def __set_Xmin(self):
		if self.set_lower_X.text()=="":
			self._xmin=None
			self.__plot()
		elif is_number(self.set_lower_X.text()) and (self.set_upper_X.text()=="" or (is_number(self.set_upper_X.text()) and (float(self.set_lower_X.text())<float(self.set_upper_X.text())) )):
			self._xmin=float(self.set_lower_X.text())
			self.__plot()
		else:
			self._xmin=None
			m=QtWidgets.QMessageBox()
			m.setText("Illegal Value for lower X value")
			m.exec()
			self.set_lower_X.clear()
			self._xmin=None
	################################################################################
	# user set lower X value
	def __set_Xmax(self):
		if self.set_upper_X.text() == "":
			self._xmax = None
			self.__plot()
		elif is_number(self.set_upper_X.text()) and (self.set_lower_X.text() == "" or (is_number(self.set_lower_X.text()) and (float(self.set_upper_X.text()) > float(self.set_lower_X.text())))):
			self._xmax = float(self.set_upper_X.text())
			self.__plot()
		else:
			self._xmin = None
			m = QtWidgets.QMessageBox()
			m.setText("Illegal Value for upper X value")
			m.exec()
			self.set_upper_X.clear()
			self._xmax = None
	################################################################################
	# user set lower X value
	def __set_Ymin(self):
		if self.set_lower_Y.text() == "":
			self._ymin = None
			self.__plot()
		elif is_number(self.set_lower_Y.text()) and (self.set_upper_Y.text() == "" or (is_number(self.set_upper_Y.text()) and (float(self.set_lower_Y.text()) < float(self.set_upper_Y.text())))):
			self._ymin = float(self.set_lower_Y.text())
			self.__plot()
		else:
			self._ymin = None
			m = QtWidgets.QMessageBox()
			m.setText("Illegal Value for lower Y value")
			m.exec()
			self.set_lower_Y.clear()
			self._ymin = None

	################################################################################
	# user set lower X value
	def __set_Ymax(self):
		if self.set_upper_Y.text() == "":
			self._ymax = None
			self.__plot()
		elif is_number(self.set_upper_Y.text()) and (self.set_lower_Y.text() == "" or (is_number(self.set_lower_Y.text()) and (float(self.set_upper_Y.text()) > float(self.set_lower_Y.text())))):
			self._ymax = float(self.set_upper_Y.text())
			self.__plot()
		else:
			self._ymin = None
			m = QtWidgets.QMessageBox()
			m.setText("Illegal Value for upper Y value")
			m.exec()
			self.set_upper_Y.clear()
			self._ymax = None
	###############################################################################
	# user selected Vgs value for FOC plots
	def __selectVgs(self):
		self.__plot()