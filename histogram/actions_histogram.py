__author__ = 'viking'
import collections as col
import matplotlib
matplotlib.use('Qt5Agg')
import pickle as pick

from waferdata_histogram import *
##from IVplot_popup import *
from IVplot import plot_family_of_curves, plothistRon
from actions_statistics_dump import *
from actions_filterdata import *
import platform
import getpass				# to allow code to get the user's ID to uniquely label saved files
##from Vgs_setter import *
from main_hist import figsindex
from utilities import *
#from actions_plot_widget import *
from actions_devlisting import *
#import collections as col
from all_device_data_to_table import *
from wafer_analysis import *
#from PyQt4 import *
from PyQt5 import QtWidgets, QtCore, QtGui
import functools as ftool


import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

fractftfit=0.8
fractfmaxfit=0.8

#from databasepacker_core import *



try:
	_fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
	def _fromUtf8(s):
		return s

class WaferHist(Ui_Histogram,QtWidgets.QDialog):
	SetWaferPlanFile=QtCore.pyqtSignal()
	RefreshDeviceData = QtCore.pyqtSignal()
	def __init__(self,parent=None):
		super(WaferHist,self).__init__()
		self.setupUi(self)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		# set up initial directories for saving program settings between runs
		if "Windows" in platform.system():
			#self.app_set_dir="C:/Documents and Settings/All Users/Application Data/"			# this will be the directory for the program settings in Windows
			self.app_set_dir="C:/ProgramData/Python"
		elif "Linux" in platform.system():
			self.app_set_dir=os.path.expanduser("~/bin/Python")
		#print(platform.system(),self.app_set_dir)				# debug
		if not os.path.exists(self.app_set_dir):				# go to the settings directory
			os.makedirs(self.app_set_dir)						# create settings directory if none exists
		settingsfilename=os.path.join(self.app_set_dir,"pyhistogramsettings")
		if os.path.isfile(settingsfilename):
			filesettings = open(settingsfilename,'r')		# load the settings file if it exists
			settingslines = [l for l in filesettings.read().splitlines()]
			for sline in settingslines:
				if "last_directory" in sline or "last directory" in sline:
					self.lastdirectory = sline.split('\t')[1].lstrip()
			filesettings.close()
		self.userID = getpass.getuser()
		self.__epsilon=1.E-20		# a very small value used to compare floating point numbers
		self.opendirbut.clicked.connect(self.selectdirectory)
		self.disableall()
		#self.opendirbut.setAutoDefault(False)
		#self.setup_waferplot()
		# set initial defaults so we don't blow up in the beginning
		self.__maxstacksize=20		# maximum size of backup stack
		#self._Vgs=-9999			# Vgs is set to the minimum
		self._histogram_data_type= 'Ron'				# default histogram is the on resistance at Vds=0V
		self.__minRon=col.deque([])			# minimum Ron or Gon plotted/analyzed
		self.__minRon.append(0.)
		self.__maxRon=col.deque([])			# maximum Ron or Gon to be plotted/analyzed
		self.__maxRon.append(1.E99)
		self.__binsizeRondev=0.1			# bin size in standard deviation
		#self.__minRonstddev=0.		# lower cutoff point for Ron or Gon data to be plotted/analyzed related to standard deviation
		#self.__maxRonstddev=5.		# upper cutoff point for Ron or Gon data to be plotted/analyzed related to standard deviation
		#self.includes=""			# device filenames must have these strings to be included
		self._fractVdsfit=0.25		# fraction of Vds range to be used to perform linear fits of Ron or Gon about Vds=0V
		self.__binsizepolicy='Directly Set'	# bin size policy used to set bin sizes for histogram - default is direct user set
		self.__previousmeasurementtype="Ron @ Vds=0V"
		self.__ipickbin=None		# index of the histogram bin that's been picked
		self.__linfit_linesdisplay=False	# whether or not to display least square linear fits in plots
		self._logplot=False			# True - perform statistics log10(abs(data)) and plot histograms on log X plot False - perform statistics on linear data
		self.devicesselected=None	# devices to be applied to filter - when self.devicesselected length >1 and self.devicesselected != None then we analyze only these devices
		self.transfer_curve_smoothing_factor_number=1            # user-selected transfer curve smoothing factor
		self._Vdsfocsetting=0.      # user-set Vds to find |Id(Vds)| with Vgs set to provide maximum turn-on for the FET
		self._deltaVgssetting=-0.5
		self._Yf_fractVgssetting=0.1
		self.__allownohistogramdatamessageflag=True       # used to toggle no data message for histogram

		#self.__rootdir="/home/viking/documents_2/MicrocraftX_LLC/customers/Carbonics/projects/documents/wafer_tests"
		#self.__rootdir="/home/viking/phil@carbonicsinc.com"
		#### set up the plotting
		self.__setup_histplot()
		####################################################################################################
		############### make all widget connections #############
		self.set_includes.editingFinished.connect(self._update,QtCore.Qt.UniqueConnection)
		self.measurementtype.currentIndexChanged.connect(self.__get_type,QtCore.Qt.UniqueConnection)
		self.selectmintype.currentIndexChanged.connect(self.__changetypeminsetting,QtCore.Qt.UniqueConnection)
		self.selectmaxtype.currentIndexChanged.connect(self.__changetypemaxsetting,QtCore.Qt.UniqueConnection)
		self.minimum.editingFinished.connect(self.__minsetting,QtCore.Qt.UniqueConnection)
		self.maximum.editingFinished.connect(self.__maxsetting,QtCore.Qt.UniqueConnection)
		self.range_linearfit.editingFinished.connect(self.__set_range_linfit)
		self.binsizepolicy.currentIndexChanged.connect(self.__binsizepolicy_changed,QtCore.Qt.UniqueConnection)
		self.binsize_stddev.editingFinished.connect(self.__update_binsizechanged,QtCore.Qt.UniqueConnection)
		self.Device_Listing_Table.VerticalHeaderClicked.connect(self.select_plot_menu)				# enable user to plot
		# self.tableWidget.cellPressed.connect(self.plotiv,QtCore.Qt.UniqueConnection)
		# self.tableWidget.cellPressed.connect(self.plottrans,QtCore.Qt.UniqueConnection)
		# self.tableWidget.cellPressed.connect(self.plottransdual,QtCore.Qt.UniqueConnection)
		self.Vgs_comboBox.currentIndexChanged.connect(self.__get_Vgs,QtCore.Qt.UniqueConnection)	# Vgs selector connection
		#self.recall_state_but.clicked.connect(self.__recall_state)						# recall previous state from file using Pickle
		self.save_state_but.clicked.connect(self.__save_state)							# save state to file using Pickle
		self.backview_but.clicked.connect(self.__backview)								# set histogram limits to earlier value
		self.forwardview_but.clicked.connect(self.__forwardview)							# set histogram limits to forward view
		self.fullview_but.clicked.connect(self.__fullview)								# set histogram to see all available data
		#self.linearfitlines_but.clicked.connect(self.__set_linfit_linesdisplay)
		self.open_filter_but.clicked.connect(self.__open_filter_widget)					# filter data
		self.log_linear_histogram_but.clicked.connect(self.__loglinset)					# set histogram to log or linear data
		self.export_but.clicked.connect(self.__open_datadump_widget)					# open data dump widget
		self.device_list_but.clicked.connect(self.__open_device_listing)				# open device listing
		self.TLMlengthminimum.currentIndexChanged.connect(self.__changedminTLMlength)	# set minimum TLM length to perform linear fit
		self.TLMlengthmaximum.currentIndexChanged.connect(self.__changedmaxTLMlength)	# set maximum TLM length to perform linear fit
		self.pack_database_but.clicked.connect(self.__pack_database)                    # enable packing of database
		self.pack_database_but.blockSignals(True)
		self.pack_database_but.setEnabled(False)

		self.selected_bin_only_but.clicked.connect(self.__selectdevice_selectedbin)      # to allow the user to select only the devices in the selected bin from the histogram for analysis
		self.selected_bin_only_but.setVisible(False)
		self.selected_bin_only_but.blockSignals(True)

		self.TLM_fit_quality.editingFinished.connect(self.__changedTLMfitquality)  # set TLM fit quality requested
		self.TLM_fit_quality.setEnabled(False)
		self.TLM_fit_quality.blockSignals(True)
		self.TLM_fit_quality.setText("0.")
		self.TLMlinearfitquality_request=0.
		self.transfer_curve_smoothing_factor.setText("1")
		self.transfer_curve_smoothing_factor.setEnabled(True)
		self.transfer_curve_smoothing_factor.editingFinished.connect(self.__changed_transfercurve_smoothing_factor)

		# setting for Vds to find |Idmax| from the family of curves (FOC) data at the maximum turn-on gate voltage
		self.Vds_FOC.editingFinished.connect(self.__changedVdsfoc)  # user set Vds to find |Idmax| from FOC
		self.Vds_FOC.setEnabled(False)
		self.Vds_FOC.blockSignals(True)
		self.Vds_FOC.setText("0.")

		# setting for Vgs delta for Y-function analysis to find Id at Vgs=Vth + Vgs offset specified by user
		# this entry is added to each device's calculated threshold voltage, from its single swept transfer curve, to give self.Vgsdeltathres which is used to find self.Idatthresplusdelta_T (from device_parameter.py)= Id @ self.Vgsdeltathres
		self.delta_Vgs_thres.editingFinished.connect(self.__changeddeltaVgs)  # user set deltaVgs to find |Id| from single swept transfer curve
		self.delta_Vgs_thres.setEnabled(False)
		self.delta_Vgs_thres.blockSignals(True)
		self.delta_Vgs_thres.setText("-0.5")

		self.Yf_Vgsfitrange_frac.editingFinished.connect(self.__changed_Vgsfract_Yf)
		self.Yf_Vgsfitrange_frac.setEnabled(False)
		self.Yf_Vgsfitrange_frac.blockSignals(True)
		self.Yf_Vgsfitrange_frac.setText("0.1")

		# user checkbox to turn Y-function analysis on or off because Y-function analysis is time-consuming
		self.Yf_checkBox.setChecked(False)
		self.Yf_checkBox.stateChanged.connect(self.__Yf_clickedcheckbox)
		self.Yf_checkBox.setEnabled(False)
		self.Yf_checkBox.blockSignals(True)
		#########################

		self.quit_but.clicked.connect(self.quitbut)										# quit button
		self.histograph_image_to_clipboard_but.clicked.connect(self.__histograph_plot_image_to_clipboard)
		#self.waferplanfile.currentIndexChanged.connect(self.setwaferplanfile)			# allow user to select from different wafer plan files to accomodate different measurement runs on the wafer
###################### set up widget elements################################################
		self.disableall()
		#self.set_includes.setText(self.includes)
		self.set_includes.clear()

		# set up select minimum type (Qcombobox) (is it # standard deviations below mean or just a value)? Note that the actual setting is effective only for values >0
		self.selectmintype.blockSignals(True)
		self.selectmintype.clear()
		self.selectmintype.addItem("Std Dev Below Mean")
		self.selectmintype.addItem("Straight Value")
		self.selectmintype.setCurrentIndex(1)

		# set up select maximum type (Qcombobox) (is it # standard deviations above mean or just a value)? Note that the actual setting is effective only for values >0
		self.selectmaxtype.blockSignals(True)
		self.selectmaxtype.clear()
		self.selectmaxtype.addItem("Std Dev Above Mean")
		self.selectmaxtype.addItem("Straight Value")
		self.selectmaxtype.setCurrentIndex(1)

		# set up lower limit setting self.minimum (QLineEdit)
		if self.selectmintype.currentText()=="Straight Value": self.minimum.setText(formatnum(self.__minRon[-1]))

		# set up upper limit setting self.minimum (QLineEdit)
		if self.selectmaxtype.currentText()=="Straight Value": self.maximum.setText(formatnum(self.__maxRon[-1]))

		# set up bin sizing policy (Qcombobox)
		self.binsizepolicy.addItems(['Directly Set','Sturges','Scott'])

		# set up bin size (QLineEdit)
		self.binsize_stddev.setText(formatnum(self.__binsizeRondev))

########### done setting up widget elements##########################

#######################################################################


#########################################################################################################

	# opens a directory and sets up GUI paramters here because we need to know something about the wafer data to set
	# up the GUI selections
	def selectdirectory(self):
		self.disableall()
		self.opendirbut.setDisabled(True)
		self.opendirbut.setVisible(False)
		#self.includes=""								# clear the includes widget
		self.set_includes.clear()		# clear the includes widget
		if hasattr(self,'wd.DCd'): del self.wd.DCd
		if hasattr(self,"wd"): del self.wd
		#self.__delete_histplot()
		#### set up the plotting
		#self.__setup_histplot()
		dirDialog = QtWidgets.QFileDialog()					# file open dialog
		dirDialog.ShowDirsOnly
		if not hasattr(self,"lastdirectory") or not os.path.exists(self.lastdirectory):
			if "Windows" in platform.system(): self.lastdirectory="C:\\"
			elif "Linux" in platform.system(): self.lastdirectory=str(os.path.expanduser("~"))
			else: raise ValueError("ERROR! Not a known OS")
		os.chdir(self.lastdirectory)
		dirDialog.setDirectory(self.lastdirectory)
		dirDialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
		dirnametemp= dirDialog.getExistingDirectory(self,self.lastdirectory)     # get selected directory name
		self.dirname=dirnametemp.replace("\\","/")
		print(dirnametemp,self.dirname) # debug
		self.wafername.setText(self.dirname.split("/")[-1])
		if len(self.dirname)==0 or self.dirname=='':		# did not select a directory and/or hit cancel button
			return
		self.lastdirectory=os.path.split(self.dirname)[0]					# set the default last directory visited to the currently selected directory
		self.wd = WaferData(parent=self,pathname=self.dirname,wafername=self.wafername.text(),Y_Ids_fitorder=8, fractVdsfit_Ronfoc=self._fractVdsfit, fractftfit=0.8, fractfmaxfit=0.4)


		########## Look for saved, (i.e. pickled) preprocessed data and if they exists, ask user if they want to load it instead ########################################
		dir_save=self.dirname+sub('save')
		# do preprocessed data exist?
		if os.path.isdir(dir_save) and os.path.isfile(dir_save+'/'+self.wd.get_wafername()+'_savedwaferdata.sav') and os.path.isfile(dir_save+'/'+self.wd.get_wafername()+'_savedsettings.sav'):
			mi=QtWidgets.QMessageBox()
			mi.setText("Found existing preprocessed data Load?")
			mi.setStandardButtons(QtWidgets.QMessageBox.Yes)
			mi.addButton(QtWidgets.QMessageBox.No)
			mi.setDefaultButton(QtWidgets.QMessageBox.No)
			if mi.exec()==QtWidgets.QMessageBox.Yes:    # user has chosen to load pre-processed data
				self.__recall_state()

		if self.wd.Ron_Gon_histogram(minRon=self.__minRon[-1], binsizeRondev=self.__binsizeRondev, binsizepolicy=self.__binsizepolicy, maxRon=self.__maxRon[-1], includes=self.set_includes.text(), fractVdsfit_Ronfoc=self._fractVdsfit, recalc='yes', RG=self._histogram_data_type, Vgs_selected=-9999., logplot=self._logplot)== "No Files Found":
			m=QtWidgets.QMessageBox()
			m.setText("No Files Found or Not a valid wafer directory. Select a valid wafer directory")
			m.exec_()
			return

		#print("from line 172 in actions_histogram.py self.wd.focfirstdevindex",self.wd.focfirstdevindex)
		if self.wd.focfirstdevindex!=None and len(self.wd.DCd[self.wd.focfirstdevindex].Ron_foc())>0:
			self._Vgsarray= self.wd.DCd[self.wd.focfirstdevindex].Ron_foc()['Vgs'] 				# this is the device which has the first "good" array of gate voltages (gate not in compliance etc...)
			# have family of curves data
			self.Vds_FOC.blockSignals(False)
			self.Vds_FOC.setEnabled(True)
		else: self._Vgsarray=None			# no family of curves data
		if self.wd.focfirstdevindex!=None and self.wd.DCd[self.wd.focfirstdevindex].devwidth!=None and self.wd.DCd[self.wd.focfirstdevindex].devwidth>0.: self.devicewidthspecified=True		# use the settings on the above device to be representative of all devices on this wafer. i.e. if this device has a gate width set, then assume all devices on the wafer																												# also have their total gate widths specified
		else: self.devicewidthspecified=False				# devices DO NOT have their gate widths specified so just default to no scaling
		self.__setup_type()                                 # set up TODO(check Oct 9, 2017)

		# turn on user entry for delta voltage + V threshold to enable calculation of Id at a gate voltage Vgs = V threshold + user-defined deltaVgs = V threshold + float(self.delta_Vgs_thres.text())
		if self.wd.havetransfer==True:
			self.delta_Vgs_thres.blockSignals(False)
			self.delta_Vgs_thres.setEnabled(True)
			self.deltaVgs_thres_label.setEnabled(True)

			self.Yf_Vgsfitrange_frac.blockSignals(False)
			self.Yf_Vgsfitrange_frac.setEnabled(True)
			self.Yf_Vgsfitrange_label.setEnabled(True)

			self.Yf_checkBox.blockSignals(False)
			self.Yf_checkBox.setEnabled(True)



		#print("from actions_histogram.py selectdirectory() line 210 self._Vgsarray", self._Vgsarray)

		# set up widgets which depend on data here
		# set up Vgs selector and populate it with the available gate voltages which we measured
		if self.wd.focfirstdevindex!=None:
			self.__Vgs_selector_setup()
			self.__TLMlength_selector_setup()			# populate TLM minimum and maximum length selector
			self.clearhistogrambindevicelist()						# remove all now-stale histogram bin device selections
			self.range_linearfit.setText(formatnum(self.wd.DCd[self.wd.focfirstdevindex].get_fractVdsfit_Ronfoc(),precision=2))
			self.enableall()

		if self.binsizepolicy.currentText()!='Directly Set':
			self.binsize_stddev.setEnabled(False)	# disable binsize setting unless we are setting it directly
		else: self.binsize_stddev.setEnabled(True)
		if hasattr(self,'filter'):	# remove stale filter specifier
			self.filter.close()
			del self.filter
		self._update()
		self.pack_database_but.setEnabled(False)                        # disabled for now
		self.pack_database_but.blockSignals(False)                      # allow user to pack the database if they choose
		#database_packer(cd=self.wd.DCd,wafername=self.wd.wafername)


	# plot histogram
	def __setup_histplot(self):
		self.findex=figsindex()      # increment number of figures counter - this ensures that we will get a unique figure to plot onto
		self._figure_hist =plt.figure(self.findex, figsize=(12, 12), frameon=False)
		self._canvas_hist=FigureCanvas(self._figure_hist)			# set up figure canvas to interface to wafermap GUI imported in actions_plot_widget.py
		self.toolbar = NavigationToolbar(self._canvas_hist, self)	# imported in actions_plot_widget.py
		self.toolbar.hide()
		self.plotframebox.addWidget(self._canvas_hist)		# add plot to window
		self._figure_hist.canvas.mpl_connect('button_press_event', ftool.partial(self.devicepickhist))
		self._figure_hist.canvas.mpl_connect('button_press_event', self.minmaxpickhist)					# connection to pick range to analyze
		return
	# delete histogram plot for fresh data
	def __delete_histplot(self):
		if hasattr(self,'_findex'): del self._findex
		if hasattr(self,"_figure_hist"): del self._figure_hist
		if hasattr(self,"_canvas_hist"): del self._canvas_hist
		if hasattr(self,"toolbar"): del self.toolbar
		child=self.plotframebox.takeAt(0)
		while child!=None:
			del child
			child = self.plotframebox.takeAt(0)
	# send histograph plot image to clipboard
	def __histograph_plot_image_to_clipboard(self):
		if hasattr(self,"_canvas_hist") and self._canvas_hist!=None:
			#print("from line 257 in actions_histogram.py clipboard")
			image_to_clipboard(canvas=self._canvas_hist)
############################################################################################
# set up parameter type selector for histograms
	def __setup_type(self):
		self.measurementtype.blockSignals(True)
		self.lastmeasurementtype=self.measurementtype.currentText()             # save last setting
		self.measurementtype.clear()                        # clear out old menu
		if [hasattr(self.wd.DCd[k],'Id_IVfoc') and self.wd.DCd[k].Id_IVfoc is not None and len(self.wd.DCd[k].Id_IVfoc)>0 for k in self.wd.validdevices].count(True)>1:
			self.measurementtype.addItem("Gon @ Vds=0V")
			self.measurementtype.addItem("Ron @ Vds=0V")
			self.measurementtype.addItem("Gon @ |Vds|=maximum")
			self.measurementtype.addItem("Ron @ |Vds|=maximum")
		if [hasattr(self.wd.DCd[k],'Idmax_t') and self.wd.DCd[k].Idmax_t is not None and not np.isnan(self.wd.DCd[k].Idmax_t) for k in self.wd.validdevices].count(True)>1:
			self.measurementtype.addItem("On-Off ratio single")
			self.measurementtype.addItem("|Idmax| single")
		if [hasattr(self.wd.DCd[k],'Idmax_tf') and self.wd.DCd[k].Idmax_tf is not None and not np.isnan(self.wd.DCd[k].Idmax_tf) for k in self.wd.validdevices].count(True)>1:
			self.measurementtype.addItem("On-Off ratio dual 1st")
			self.measurementtype.addItem("On-Off ratio dual 2nd")
			self.measurementtype.addItem("hysteresis voltage 12")
			self.measurementtype.addItem("|Idmax| dual 1st")
			self.measurementtype.addItem("|Idmax| dual 2nd")
		if [hasattr(self.wd.DCd[k],'Rc_TLM') and self.wd.DCd[k].Rc_TLM is not None and not np.isnan(self.wd.DCd[k].Rc_TLM) for k in self.wd.validdevices].count(True)>1:
			self.measurementtype.addItem("Rc TLM")
			self.measurementtype.addItem("Rsh TLM")
		if [hasattr(self.wd.DCd[k],'ratioIdmax') and self.wd.DCd[k].ratioIdmax is not None and not np.isnan(self.wd.DCd[k].ratioIdmax) for k in self.wd.validdevices].count(True)>1:
			self.measurementtype.addItem("ORTHRatio |Idmax| single")
		if [hasattr(self.wd.DCd[k],'ratioIdmaxF') and self.wd.DCd[k].ratioIdmaxF is not None and not np.isnan(self.wd.DCd[k].ratioIdmaxF) for k in self.wd.validdevices].count(True)>1:
			self.measurementtype.addItem("ORTHRatio |Idmax| dual 1st")
			self.measurementtype.addItem("ORTHRatio |Idmax| dual 2nd")
		if [hasattr(self.wd.DCd[k],'ratioRon') and self.wd.DCd[k].ratioRon is not None and not np.isnan(self.wd.DCd[k].ratioRon) for k in self.wd.validdevices].count(True)>1:
			self.measurementtype.addItem("ORTHRatio Ron")
		if [hasattr(self.wd.DCd[k],'Idmaxfoc_Vds') and self.wd.DCd[k].Idmaxfoc_Vds is not None and not np.isnan(self.wd.DCd[k].Idmaxfoc_Vds) for k in self.wd.validdevices].count(True)>1:
			self.measurementtype.addItem("|Idmax(Vds)|FOC")
		if [hasattr(self.wd.DCd[k],'Idhystfocmax') and self.wd.DCd[k].Idhystfocmax is not None and not np.isnan(self.wd.DCd[k].Idhystfocmax) for k in self.wd.validdevices].count(True)>1:
			self.measurementtype.addItem("FOC hysteresis current")

		#self.measurementtype.setCurrentIndex(1)
		# set initial parameter
		available_parameters=[self.measurementtype.itemText(i) for i in range(self.measurementtype.count())]
		if self.lastmeasurementtype!=None and self.lastmeasurementtype in available_parameters:
			self.measurementtype.setCurrentText(self.lastmeasurementtype)
		elif "|Idmax| single" in available_parameters:
			self.measurementtype.setCurrentText("|Idmax| single")
		elif "|Idmax(Vds)|FOC" in available_parameters:
			self.measurementtype.setCurrentText("|Idmax(Vds)|FOC")
		elif "Ron @ Vds=0V" in available_parameters:
			self.measurementtype.setCurrentText("Ron @ Vds=0V")


		if self.measurementtype.currentText()=="Gon @ Vds=0V":
			self._histogram_data_type= 'Gon'
			if self.devicewidthspecified==True: self.__xlabel="On Conductance mS/mm"
			else: self.__xlabel="On Conductance S"
		elif self.measurementtype.currentText()=="Ron @ Vds=0V":
			self._histogram_data_type= 'Ron'
			if self.devicewidthspecified==True: self.__xlabel="On Resistance ohm*mm"
			else: self.__xlabel="On Resistance Ohms"
		elif self.measurementtype.currentText()=="Gon @ |Vds|=maximum":
			self._histogram_data_type= 'Gmax'
			if self.devicewidthspecified==True: self.__xlabel="Conductance mS/mm"
			else: self.__xlabel="Conductance S"
		elif self.measurementtype.currentText()=="Ron @ |Vds|=maximum":
			self._histogram_data_type= 'Rmax'
			if self.devicewidthspecified==True: self.__xlabel="Resistance ohm*mm"
			else: self.__xlabel="Resistance Ohms"
		elif self.measurementtype.currentText()=="On-Off ratio single":
			self.__xlabel="On-Off Ratio"
			self._histogram_data_type= "On-Off ratio single"
		elif self.measurementtype.currentText()=="On-Off ratio dual 1st":
			self.__xlabel="On-Off Ratio"
			self._histogram_data_type= "On-Off ratio dual 1st"
		elif self.measurementtype.currentText()=="On-Off ratio dual 2nd":
			self.__xlabel="On-Off Ratio"
			self._histogram_data_type= "On-Off ratio dual 2nd"
		elif self.measurementtype.currentText()=="|Idmax| single":
			if self.devicewidthspecified==True: self.__xlabel="Maximum |Drain Current| (mA/mm)"			# label on histogram plot
			else: self.__xlabel="Maximum |Drain Current| (A)"			# label on histogram plot
			self._histogram_data_type= "|Idmax| single"
		elif self.measurementtype.currentText()=="|Idmax| dual 1st":
			if self.devicewidthspecified==True: self.__xlabel="Maximum |Drain Current| (mA/mm)"			# label on histogram plot
			else: self.__xlabel="Maximum |Drain Current| (A)"			# label on histogram plot
			self._histogram_data_type= '|Idmax| dual 1st'
		elif self.measurementtype.currentText()=="|Idmax| dual 2nd":
			if self.devicewidthspecified==True: self.__xlabel="Maximum |Drain Current| (mA/mm)"			# label on histogram plot
			else: self.__xlabel="Maximum |Drain Current| (A)"			# label on histogram plot
			self._histogram_data_type= '|Idmax| dual 2nd'
		elif self.measurementtype.currentText()=="Rc TLM":
			self._histogram_data_type= 'Rc TLM'
			if self.devicewidthspecified==True: self.__xlabel="TLM contact resistance ohm*mm"
			else: self.__xlabel="TLM contact resistance ohms"
		elif self.measurementtype.currentText()=="Rsh TLM":
			self._histogram_data_type= 'Rsh TLM'
			if self.devicewidthspecified==True: self.__xlabel="TLM channel resistance ohm/square"			# label on histogram plot
			else: self.__xlabel="TLM channel resistance ohms/um length"			# label on histogram plot
		elif self.measurementtype.currentText()=="ORTHRatio |Idmax| single":
			self._histogram_data_type= "ORTHRatio |Idmax| single"
			self.__xlabel="ratio of |Idmax|0deg/|Idmax|90deg"			# label on histogram plot
		elif self.measurementtype.currentText()=="ORTHRatio Ron":
			self._histogram_data_type= 'ORTHRatio Ron'
			self.__xlabel="ratio of Ron 90deg/Ron 0deg"			# label on histogram plot
		elif self.measurementtype.currentText()=="hysteresis voltage 12":
			self._histogram_data_type = 'hysteresis voltage 12'
			self.__xlabel = "hysteresis voltage between 1st and 2nd sweeps (V)"  # label on histogram plot
		elif self.measurementtype.currentText()=="|Idmax(Vds)|FOC":
			self._histogram_data_type= "|Idmax(Vds)|FOC"
			if self.devicewidthspecified: self.__xlabel="|Idmax(Vds)|FOC mA/mm"
			else: self.__xlabel="|Idmax(Vds)|FOC A"
		elif self.measurementtype.currentText()=="FOC hysteresis current":
			self._histogram_data_type= "FOC hysteresis current"
			if self.devicewidthspecified: self.__xlabel="maximum FOC hysteresis current mA/mm"
			else: self.__xlabel="maximum FOC hysteresis current A"
		#else: raise ValueError("ERROR! No types match")
		else: print("WARNING! no types match")
		self.measurementtype.blockSignals(False)
#############################################################################################################

# The measurement type was changed - label is "parameter"
	def __get_type(self):
		#user controls for TLM structures
		self.TLMlengthminimum.blockSignals(True)
		self.TLMlengthminimum.setEnabled(False)
		self.TLMlengthmaximum.blockSignals(True)
		self.TLMlengthmaximum.setEnabled(False)
		self.TLM_fit_quality.blockSignals(True)
		self.TLM_fit_quality.setEnabled(False)
		# user controls relevant to family of curves data such as
		# Ron, Gon, Gmax
		self.selectmintype.blockSignals(True)
		self.selectmaxtype.blockSignals(True)
		self.Vgs_comboBox.setEnabled(False)
		self.range_linearfit.setEnabled(False)
		if self.measurementtype.currentText()=="Gon @ Vds=0V":
			self._histogram_data_type= 'Gon'
			if self.devicewidthspecified==True: self.__xlabel="On Conductance mS/mm"
			else: self.__xlabel="On Conductance S"
			self.Vgs_comboBox.setEnabled(True)
			self.range_linearfit.setEnabled(True)

		elif self.measurementtype.currentText()=="Ron @ Vds=0V":
			self._histogram_data_type= 'Ron'
			self.Vgs_comboBox.setEnabled(True)
			self.range_linearfit.setEnabled(True)
			if self.devicewidthspecified==True: self.__xlabel="On Resistance ohm*mm"
			else: self.__xlabel="On Resistance Ohms"
			# disable TLM length setter because it's not relevant here

		elif self.measurementtype.currentText()=="Gon @ |Vds|=maximum":
			self._histogram_data_type= 'Gmax'
			if self.devicewidthspecified==True: self.__xlabel="Conductance mS/mm"
			else: self.__xlabel="Conductance S"
			self.Vgs_comboBox.setEnabled(True)
			self.range_linearfit.setEnabled(False)
			# disable TLM length setter because it's not relevant here

		elif self.measurementtype.currentText()=="Ron @ |Vds|=maximum":
			self._histogram_data_type= 'Rmax'
			if self.devicewidthspecified==True: self.__xlabel="Resistance Ohm*mm"
			else: self.__xlabel="Resistance Ohms"
			self.Vgs_comboBox.setEnabled(True)
			self.range_linearfit.setEnabled(False)
			# disable TLM length setter because it's not relevant here
			self.selectmintype.blockSignals(False)
			self.selectmaxtype.blockSignals(False)
			self.Vgs_comboBox.setEnabled(True)
			self.range_linearfit.setEnabled(True)

		elif "On-Off ratio" in self.measurementtype.currentText():
			if self.measurementtype.currentText()=="On-Off ratio single": self._histogram_data_type= "On-Off ratio single"
			elif self.measurementtype.currentText()=="On-Off ratio dual 1st": self._histogram_data_type= "On-Off ratio dual 1st"
			elif self.measurementtype.currentText()=="On-Off ratio dual 2nd": self._histogram_data_type= 'On-Off ratio dual 2nd'
			self.__xlabel="On-Off Ratio"
			self.selectmintype.blockSignals(True)
			self.selectmintype.setCurrentIndex(self.selectmintype.findText("Straight Value"))
			self.selectmaxtype.blockSignals(True)
			self.selectmaxtype.setCurrentIndex(self.selectmaxtype.findText("Straight Value"))
			self.minimum.setText("0.")
			self.__minRon[-1]=0.
			self.maximum.setText("1.E99")
			self.__maxRon[-1]=1.E99

		elif "|Idmax|" in self.measurementtype.currentText() and "ORTH" not in self.measurementtype.currentText():
			if self.measurementtype.currentText()=="|Idmax| single": self._histogram_data_type= "|Idmax| single"
			elif self.measurementtype.currentText()=="|Idmax| dual 1st": self._histogram_data_type= "|Idmax| dual 1st"
			elif self.measurementtype.currentText()=="|Idmax| dual 2nd": self._histogram_data_type= '|Idmax| dual 2nd'
			if self.devicewidthspecified==True: self.__xlabel="Maximum |Drain Current| (mA/mm)"			# label on histogram plot
			else: self.__xlabel="Maximum |Drain Current| (A)"			# label on histogram plot
			self.selectmintype.blockSignals(True)
			self.selectmintype.setCurrentIndex(self.selectmintype.findText("Straight Value"))
			self.selectmaxtype.blockSignals(True)
			self.selectmaxtype.setCurrentIndex(self.selectmaxtype.findText("Straight Value"))
			self.minimum.setText("0.")
			self.__minRon[-1]=0.
			self.maximum.setText("1.E99")
			self.__maxRon[-1]=1.E99
			self.selectmintype.blockSignals(False)
			self.selectmaxtype.blockSignals(False)
			self.Vgs_comboBox.setEnabled(False)
			self.range_linearfit.setEnabled(False)

		elif "|Idmax(Vds)|FOC" in self.measurementtype.currentText():
			self._histogram_data_type= "|Idmax(Vds)|FOC"
			# labels on X-axis of histogram plot
			if self.devicewidthspecified: self.__xlabel="|Idmax(Vds)|FOC mA/mm"
			else: self.__xlabel="|Idmax(Vds)|FOC A"
			self.selectmintype.blockSignals(True)
			self.selectmintype.setCurrentIndex(self.selectmintype.findText("Straight Value"))
			self.selectmaxtype.blockSignals(True)
			self.selectmaxtype.setCurrentIndex(self.selectmaxtype.findText("Straight Value"))
			self.minimum.setText("0.")
			self.__minRon[-1]=0.
			self.maximum.setText("1.E99")
			self.__maxRon[-1]=1.E99
			self.selectmintype.blockSignals(False)
			self.selectmaxtype.blockSignals(False)
			self.Vgs_comboBox.setEnabled(False)
			self.range_linearfit.setEnabled(False)

		elif "FOC hysteresis current" in self.measurementtype.currentText():
			self._histogram_data_type= "FOC hysteresis current"
			# labels on X-axis of histogram plot
			if self.devicewidthspecified: self.__xlabel="maximum FOC hysteresis current mA/mm"
			else: self.__xlabel="maximum FOC hysteresis current A"
			self.selectmintype.blockSignals(True)
			self.selectmintype.setCurrentIndex(self.selectmintype.findText("Straight Value"))
			self.selectmaxtype.blockSignals(True)
			self.selectmaxtype.setCurrentIndex(self.selectmaxtype.findText("Straight Value"))
			self.minimum.setText("0.")
			self.__minRon[-1]=0.
			self.maximum.setText("1.E99")
			self.__maxRon[-1]=1.E99
			self.selectmintype.blockSignals(False)
			self.selectmaxtype.blockSignals(False)
			self.Vgs_comboBox.setEnabled(False)
			self.range_linearfit.setEnabled(False)

		elif self.measurementtype.currentText()=="Rc TLM":
			self._histogram_data_type= 'Rc TLM'
			if self.devicewidthspecified==True: self.__xlabel="TLM contact resistance ohm*mm"			# label on histogram plot
			else: self.__xlabel="TLM contact resistance ohms"			# label on histogram plot
			self.selectmintype.blockSignals(True)
			self.selectmintype.setCurrentIndex(self.selectmintype.findText("Straight Value"))
			self.selectmaxtype.blockSignals(True)
			self.selectmaxtype.setCurrentIndex(self.selectmaxtype.findText("Straight Value"))
			self.minimum.setText("0.")
			self.__minRon[-1]=0.
			self.maximum.setText("1.E99")
			self.__maxRon[-1]=1.E99
			self.selectmintype.blockSignals(False)
			self.selectmaxtype.blockSignals(False)
			self.range_linearfit.setEnabled(True)
			# enable  TLM length setter
			self.TLMlengthminimum.setEnabled(True)
			self.TLMlengthminimum.blockSignals(False)
			self.TLMlengthmaximum.setEnabled(True)
			self.TLMlengthmaximum.blockSignals(False)
			self.TLM_fit_quality.setEnabled(True)
			self.TLM_fit_quality.blockSignals(False)
		elif self.measurementtype.currentText()=="Rsh TLM":
			self._histogram_data_type= 'Rsh TLM'
			if self.devicewidthspecified==True: self.__xlabel="TLM channel resistance ohm/square"			# label on histogram plot
			else: self.__xlabel="TLM channel resistance ohms/um length"			# label on histogram plot
			self.selectmintype.blockSignals(True)
			self.selectmintype.setCurrentIndex(self.selectmintype.findText("Straight Value"))
			self.selectmaxtype.blockSignals(True)
			self.selectmaxtype.setCurrentIndex(self.selectmaxtype.findText("Straight Value"))
			self.minimum.setText("0.")
			self.__minRon[-1]=0.
			self.maximum.setText("1.E99")
			self.__maxRon[-1]=1.E99
			self.selectmintype.blockSignals(False)
			self.selectmaxtype.blockSignals(False)
			self.range_linearfit.setEnabled(True)
			# enable  TLM length setter
			self.TLMlengthminimum.setEnabled(True)
			self.TLMlengthminimum.blockSignals(False)
			self.TLMlengthmaximum.setEnabled(True)
			self.TLMlengthmaximum.blockSignals(False)
			self.TLM_fit_quality.setEnabled(True)
			self.TLM_fit_quality.blockSignals(False)
		elif self.measurementtype.currentText()=="ORTHRatio |Idmax| single":
			self._histogram_data_type= "ORTHRatio |Idmax| single"
			self.__xlabel="ratio of |Idmax|0deg/|Idmax|90deg"			# label on histogram plot
			self.selectmintype.blockSignals(True)
			self.selectmintype.setCurrentIndex(self.selectmintype.findText("Straight Value"))
			self.selectmaxtype.blockSignals(True)
			self.selectmaxtype.setCurrentIndex(self.selectmaxtype.findText("Straight Value"))
			self.minimum.setText("0.")
			self.__minRon[-1]=0.
			self.maximum.setText("1.E99")
			self.__maxRon[-1]=1.E99
			self.selectmintype.blockSignals(False)
			self.selectmaxtype.blockSignals(False)
			self.range_linearfit.setEnabled(False)
		elif self.measurementtype.currentText() == "ORTHRatio |Idmax| dual 1st":
			self._histogram_data_type = "ORTHRatio |Idmax| dual 1st"
			self.__xlabel = "ratio of |Idmax|0deg/|Idmax|90deg 1st sweep"  # label on histogram plot
			self.selectmintype.blockSignals(True)
			self.selectmintype.setCurrentIndex(self.selectmintype.findText("Straight Value"))
			self.selectmaxtype.blockSignals(True)
			self.selectmaxtype.setCurrentIndex(self.selectmaxtype.findText("Straight Value"))
			self.minimum.setText("0.")
			self.__minRon[-1] = 0.
			self.maximum.setText("1.E99")
			self.__maxRon[-1] = 1.E99
			self.selectmintype.blockSignals(False)
			self.selectmaxtype.blockSignals(False)
			self.range_linearfit.setEnabled(False)
		elif self.measurementtype.currentText() == "ORTHRatio |Idmax| dual 2nd":
			self._histogram_data_type = "ORTHRatio |Idmax| dual 2nd"
			self.__xlabel = "ratio of |Idmax|0deg/|Idmax|90deg 2nd sweep"  # label on histogram plot
			self.selectmintype.blockSignals(True)
			self.selectmintype.setCurrentIndex(self.selectmintype.findText("Straight Value"))
			self.selectmaxtype.blockSignals(True)
			self.selectmaxtype.setCurrentIndex(self.selectmaxtype.findText("Straight Value"))
			self.minimum.setText("0.")
			self.__minRon[-1] = 0.
			self.maximum.setText("1.E99")
			self.__maxRon[-1] = 1.E99
			self.selectmintype.blockSignals(False)

			self.selectmaxtype.blockSignals(False)
			self.range_linearfit.setEnabled(False)
		elif self.measurementtype.currentText()=="ORTHRatio Ron":
			self._histogram_data_type= 'ORTHRatio Ron'
			self.__xlabel="ratio of Ron 90deg/Ron 0deg"			# label on histogram plot
			self.selectmintype.blockSignals(True)
			self.selectmintype.setCurrentIndex(self.selectmintype.findText("Straight Value"))
			self.selectmaxtype.blockSignals(True)
			self.selectmaxtype.setCurrentIndex(self.selectmaxtype.findText("Straight Value"))
			self.minimum.setText("0.")
			self.__minRon[-1]=0.
			self.maximum.setText("1.E99")
			self.__maxRon[-1]=1.E99
			self.selectmintype.blockSignals(False)
			self.selectmaxtype.blockSignals(False)
			self.range_linearfit.setEnabled(False)
		elif self.measurementtype.currentText() == "hysteresis voltage 12":
			self._histogram_data_type = 'hysteresis voltage 12'
			self.__xlabel = "hysteresis voltage between 1st and 2nd sweeps (V)"  # label on histogram plot
			self.selectmintype.blockSignals(True)
			self.selectmintype.setCurrentIndex(self.selectmintype.findText("Straight Value"))
			self.selectmaxtype.blockSignals(True)
			self.selectmaxtype.setCurrentIndex(self.selectmaxtype.findText("Straight Value"))
			self.minimum.setText("0.")
			self.__minRon[-1] = 0.
			self.maximum.setText("1.E99")
			self.__maxRon[-1] = 1.E99
			self.selectmintype.blockSignals(False)
			self.selectmaxtype.blockSignals(False)
			self.range_linearfit.setEnabled(False)

		else: raise ValueError("ERROR! No types match")
		mx=self.__maxRon[-1]
		mn=self.__minRon[-1]
		if ("Ron" in self.__previousmeasurementtype and "Gon" in self.measurementtype.currentText()) or ("Gon" in self.__previousmeasurementtype and "Ron" in self.measurementtype.currentText()) :	# Changing from resistance to conductance or vice versa
			self.__minRon[-1] = 1./mx
			if mn==0.: self.__maxRon[-1]=1.E99
			else: self.__maxRon[-1]=1./mn
			if self.selectmintype.currentText()=="Straight Value":
				self.minimum.setText(formatnum(self.__minRon[-1],precision=2))
			if self.selectmaxtype.currentText()=="Straight Value":
				self.maximum.setText(formatnum(self.__maxRon[-1],precision=2))
			if self.selectmintype.currentText()=="Std Dev Below Mean":
				self.minimum.setText(formatnum((float(self.average.text())-self.__minRon[-1])/float(self.standard_deviation.text()),precision=2))
			if self.selectmaxtype.currentText()=="Std Dev Above Mean":
				maxlim=(self.__maxRon[-1]-float(self.average.text()))/float(self.standard_deviation.text())
				if maxlim>1000.: maxlim=1000.
				self.maximum.setText(formatnum(maxlim,precision=2))
		elif not ("Ron" in self.__previousmeasurementtype) and not ("Gon" in self.__previousmeasurementtype) and ("Ron" in self.measurementtype.currentText() or "Gon" in self.measurementtype.currentText()):
			# then we are going from a Ron or Gon type measurement so reset minimum and maximums
			self.selectmintype.blockSignals(True)
			self.selectmintype.setCurrentIndex(self.selectmintype.findText("Straight Value"))
			self.selectmaxtype.blockSignals(True)
			self.selectmaxtype.setCurrentIndex(self.selectmaxtype.findText("Straight Value"))
			self.minimum.setText("0.")
			self.__minRon[-1]=0.
			self.maximum.setText("1.E99")
			self.__maxRon[-1]=1.E99
			self.selectmintype.blockSignals(False)
			self.selectmaxtype.blockSignals(False)
		self.__previousmeasurementtype=self.measurementtype.currentText()
		# Update the works
		self._update()
################################################################################################################################################

# The user changed the Vgs selection
	def __get_Vgs(self):
		#self._Vgs=float(self.Vgs_comboBox.currentText())
		self._update()
# the user changed the type of the data minimum cutoff
	def __changetypeminsetting(self): # convert from staight value to std dev
		if self.selectmintype.currentText()=="Std Dev Below Mean":	# converting from straight value to Std deviation
			if self.__minRon[-1]<0.: self.__minRon[-1]=0.
			self.minimum.setText(formatnum((float(self.average.text())-self.__minRon[-1])/float(self.standard_deviation.text()),precision=2))
		elif self.selectmintype.currentText()=="Straight Value":	# converting from Std dev to straight value
			self.minimum.setText(formatnum(float(self.average.text())-float(self.minimum.text())*float(self.standard_deviation.text()),precision=2))
			if self.__minRon[-1]<0.: self.__minRon[-1]=0.
		else: raise ValueError("ERROR! no legal value found")
	# the user changed the type of the data maximum cutoff
	def __changetypemaxsetting(self): # convert from staight value to std dev
		if self.selectmaxtype.currentText()=="Std Dev Above Mean":	# converting from straight value to Std deviation
			maxlim=(self.__maxRon[-1]-float(self.average.text()))/float(self.standard_deviation.text())
			if maxlim>1000.: maxlim=1000.
			#self.maximum.setText(str('{:5.2f}'.format(maxlim)))
			self.maximum.setText(formatnum(maxlim,precision=2))
		elif self.selectmaxtype.currentText()=="Straight Value":	# converting from Std dev to straight value
			print(self.maximum.text(),self.average.text(),self.standard_deviation.text()) #debug
			#self.maximum.setText(str('{:5.2E}'.format(float(self.average.text())+float(self.maximum.text())*float(self.standard_deviation.text()))))
			self.maximum.setText(formatnum(float(self.average.text())+float(self.maximum.text())*float(self.standard_deviation.text()),precision=2))
		else: raise ValueError("ERROR! no legal value found")

	# user typed in the lower limit of the sample population
	def __minsetting(self):
		if len(self.__minRon)!=len(self.__maxRon): raise ValueError("ERROR! histerogram limit stacks not equal")
		if self.selectmintype.currentText()=="Std Dev Below Mean":
			if abs(self.__minRon[-1]-float(self.average.text())-float(self.minimum.text())*float(self.standard_deviation.text()))>self.__epsilon: # did the value change?
				if len(self.__minRon)<self.__maxstacksize:			# push new value onto stack if not at max stack size
					self.__maxRon.append(self.__maxRon[-1])
					self.__minRon.append(float(self.average.text())-float(self.minimum.text())*float(self.standard_deviation.text()))
				else:		# push rotate and append
					maxRontemp=self.__maxRon[-1]
					self.__maxRon.rotate(-1)
					self.__maxRon[-1]=maxRontemp
					self.__minRon.rotate(-1)
					self.__minRon[-1] = float(self.average.text())-float(self.minimum.text())*float(self.standard_deviation.text())
				self._update()	# recalculate and replot
			if self.__minRon[-1]<self.__epsilon:
				self.__minRon[-1]=0.
				self.minimum.setText(formatnum(float(self.average.text())/float(self.standard_deviation.text()),precision=2))
				self._update()	# recalculate and replot
		elif self.selectmintype.currentText()=="Straight Value":
			if abs(self.__minRon[-1]-float(self.minimum.text()))>self.__epsilon: # did the value change?
				if len(self.__minRon)<self.__maxstacksize:			# push new value onto stack if not at max stack size
					self.__maxRon.append(self.__maxRon[-1])
					self.__minRon.append(float(self.minimum.text()))
				else: # push rotate setting onto stack
					maxRontemp=self.__maxRon[-1]
					self.__maxRon.rotate(-1)
					self.__maxRon[-1]=maxRontemp
					self.__minRon.rotate(-1)
					self.__minRon[-1]=float(self.minimum.text())
				self._update()	# recalculate and replot
				if self.__minRon[-1]<self.__epsilon:
					self.__minRon[-1]=0.
					self.minimum.setText("0.")
					self._update()	# recalculate and replot
		else: raise ValueError("ERROR! no legal value found")

	# user typed in the upper limit of the sample population
	def __maxsetting(self):
		if len(self.__minRon)!=len(self.__maxRon): raise ValueError("ERROR! histerogram limit stacks not equal")
		if self.selectmaxtype.currentText()=="Std Dev Above Mean":
			if abs(self.__maxRon[-1]-(float(self.average.text())+float(self.maximum.text())*float(self.standard_deviation.text())))>self.__epsilon: # did the value change?
				if len(self.__maxRon)<self.__maxstacksize:			# push new value onto stack if not at max stack size
					self.__minRon.append(self.__minRon[-1])
					self.__maxRon.append(float(self.average.text())+float(self.maximum.text())*float(self.standard_deviation.text()))
				else: 		# push rotate setting onto stack
					minRontemp=self.__minRon[-1]
					self.__minRon.rotate(-1)
					self.__minRon[-1]=minRontemp
					self.__maxRon.rotate(-1)
					self.maxRon[-1]=float(self.average.text())+float(self.maximum.text())*float(self.standard_deviation.text())
				self._update()	# recalculate and replot
		elif self.selectmaxtype.currentText()=="Straight Value":
			if abs(self.__maxRon[-1]-float(self.maximum.text()))>self.__epsilon: # did the value change?
				if len(self.__maxRon)<self.__maxstacksize:			# push new value onto stack if not at max stack size
					self.__minRon.append(self.__minRon[-1])
					self.__maxRon.append(float(self.maximum.text()))
				else: 		# push rotate setting onto stack
					minRontemp=self.__minRon[-1]
					self.__minRon.rotate(-1)
					self.__minRon[-1]=minRontemp
					self.__maxRon.rotate(-1)
					self.__maxRon[-1]=float(self.maximum.text())
				self._update()	# recalculate and replot
		else: raise ValueError("ERROR! no legal value found")

	# refresh and update the upper limit display to its current internal value DO NOT recalculate
	def __refresh_maxsetting_display(self):
		if self.selectmaxtype.currentText()=="Std Dev Above Mean":
			maxlim = (self.__maxRon[-1]-float(self.average.text()))/float(self.standard_deviation.text())
			if maxlim>1000.: maxlim=1000.
			self.maximum.setText(formatnum(maxlim,precision=2))
		elif self.selectmaxtype.currentText()=="Straight Value":
			self.maximum.setText(formatnum(self.__maxRon[-1],precision=2))
		else: raise ValueError("ERROR! selectmaxtype does not specify an existing type")
	# refresh and update the lower limit display to its current internal value DO NOT recalculate
	def __refresh_minsetting_display(self):
		if self.selectmintype.currentText()=="Std Dev Below Mean":
			self.minimum.setText(formatnum((float(self.average.text())-self.__minRon[-1])/float(self.standard_deviation.text()),precision=2))
		elif self.selectmintype.currentText()=="Straight Value":
			self.minimum.setText(formatnum(self.__minRon[-1],precision=2))
		else: raise ValueError("ERROR! selectmintype does not specify an existing type")


## user changed bin size policy
	def __binsizepolicy_changed(self):
		if self.binsizepolicy.currentText()!='Directly Set':
			self.binsize_stddev.setEnabled(False)	# disable binsize setting unless we are setting it directly
		else: self.binsize_stddev.setEnabled(True)
		if self.__binsizepolicy!=self.binsizepolicy.currentText():		# has the bin size policy changed?
			self.__binsizepolicy=self.binsizepolicy.currentText()
			self._update()
		else: return

# user updated bin size
	def __update_binsizechanged(self):
		if self.__binsizeRondev!=float(self.binsize_stddev.text()):
			self.__binsizeRondev = float(self.binsize_stddev.text())
			self._update()
		else: return
##
# user updated includes to allow device filtering by type
	def __update_includes(self):
		if self.includes!=self.set_includes.text():
			self.includes=self.set_includes.text()
			self._update()
		else: return

# user set histogram to full view
	def __fullview(self):
		self.__minRon[-1]=0.
		self.__maxRon[-1]=1.E99
		self._update()
# user set histogram back one view
	def __backview(self):
		if len(self.__minRon)!=len(self.__maxRon): raise ValueError("ERROR! histerogram limit stacks not equal")
		# rotate stack one step backward
		if len(self.__minRon)>1:
			minRontemp=self.__minRon[-1]
			maxRontemp=self.__maxRon[-1]
			self.__minRon.rotate(1)
			self.__maxRon.rotate(1)
			if abs(self.__minRon[-1]-minRontemp)>self.__epsilon or abs(self.__maxRon[-1]-maxRontemp)>self.__epsilon:		# did either or both values change with rotation?
				self._update()
# user set histogram forward one view
	def __forwardview(self):
		if len(self.__minRon)!=len(self.__maxRon): raise ValueError("ERROR! histerogram limit stacks not equal")
		# rotate stack one step backward
		if len(self.__minRon)>1:
			minRontemp=self.__minRon[-1]
			maxRontemp=self.__maxRon[-1]
			self.__minRon.rotate(-1)
			self.__maxRon.rotate(-1)
			if abs(self.__minRon[-1]-minRontemp)>self.__epsilon or abs(self.__maxRon[-1]-maxRontemp)>self.__epsilon:		# did either or both values change with rotation?
				self._update()

# update GUI and plot#########################################################################################################################################################################
	def _update(self,suppressmessage=False):	# update plot and GUI suppressmessage suppresses "no data" message to allow programmatic capture of the no data condition
		# m=QtWidgets.QMessageBox()
		# m.setText("Waiting for data update")
		# m.setWindowModality(Qt.NonModal)
		# m.show()
		# time.sleep(5)
		self.wd.devfilter(selected_devices=self.devicesselected,booleanfilter=self.set_includes.text(),fractVdsfit=self.range_linearfit.text(),Vgs_selected=self.Vgs_comboBox.currentText(),minTLMlength=self.TLMlengthminimum.currentText(),maxTLMlength=self.TLMlengthmaximum.currentText())
		self.wd.get_parametersTLM(fractVdsfit=self.range_linearfit.text(), Vgs_selected=self.Vgs_comboBox.currentText(), minTLMlength=self.TLMlengthminimum.currentText(), maxTLMlength=self.TLMlengthmaximum.currentText(),linearfitquality_request=self.TLMlinearfitquality_request)
		self.wd.get_parametersORTHO(self.range_linearfit.text(), Vgs_selected=self.Vgs_comboBox.currentText())
		self.wd.devfilter(selected_devices=self.devicesselected,booleanfilter=self.set_includes.text(),fractVdsfit=self.range_linearfit.text(),Vgs_selected=self.Vgs_comboBox.currentText(),minTLMlength=self.TLMlengthminimum.currentText(),maxTLMlength=self.TLMlengthmaximum.currentText())

		#self.wd.get_parametersTLM(fractVdsfit=self.range_linearfit.text(), Vgs_selected=self.Vgs_comboBox.currentText(), minTLMlength=self.TLMlengthminimum.currentText(), maxTLMlength=self.TLMlengthmaximum.currentText(), linearfitquality_request=self.TLMlinearfitquality_request)			# eliminate devices and TLM structures that were filtered out
		self.__refresh_minsetting_display()		# update lower limit display to internal lower limit
		self.__refresh_maxsetting_display()		# update lower limit display to internal upper limit
		if is_number(self.TLMlengthminimum.currentText()): minTLMlength=float(self.TLMlengthminimum.currentText())
		else: minTLMlength=None
		if is_number(self.TLMlengthmaximum.currentText()): maxTLMlength=float(self.TLMlengthmaximum.currentText())
		else: maxTLMlength=None

		message=self.wd.Ron_Gon_histogram(minRon=self.__minRon[-1], binsizeRondev=self.__binsizeRondev, binsizepolicy=self.__binsizepolicy, maxRon=self.__maxRon[-1], includes=self.set_includes.text(),
		                                  fractVdsfit_Ronfoc=self._fractVdsfit, recalc='yes', RG=self._histogram_data_type, Vgs_selected=self.Vgs_comboBox.currentText(),
		                                  logplot=self._logplot, minTLMlength=minTLMlength, maxTLMlength=maxTLMlength,linearfitquality_request=self.TLMlinearfitquality_request,
		                                  transfercurve_smoothing_factor=self.transfer_curve_smoothing_factor_number)
		if message != "No data": self.__allownohistogramdatamessageflag=True            # allow warning message for no histogram data when we finally get histogram data again - prevents no data message from blocking up GUI
		self.__setup_type()         # update parameter selector for histogram
		if message=='No data' and self.__allownohistogramdatamessageflag:
			self.__allownohistogramdatamessageflag=False       # do not allow no data histogram message until we get data in histogram again
			if suppressmessage==True: return "No data"			# return "no data" to calling routine but do not pop up warning and do not stop program
			print("No data in histogram")
			m=QtWidgets.QMessageBox()
			m.setText("No data exist with the selected parameters!")
			m.exec_()
			plothistRon(figurecanvas=self._figure_hist, canvas=self._canvas_hist, clearplot=True, logplot=self._logplot)
			return
		elif message==None:
			m=QtWidgets.QMessageBox()
			m.setText("No data exist with the selected parameters! or a program bug!")
			m.exec_()
			return

		#self.__iVgs = min(range(len(self._Vgsarray)), key=lambda i: abs(self._Vgsarray[i] - float(self.Vgs_comboBox.currentText()))) # find index of Vgs

		self.bins=plothistRon(binmin=self.wd.Ron_Gon_histogram()['binmin'], binmax=self.wd.Ron_Gon_histogram()['binmax'], datahist=self.wd.Ron_Gon_histogram()['R'], figurecanvas=self._figure_hist, canvas=self._canvas_hist, xlabel=self.__xlabel, logplot=self._logplot)
		self.standard_deviation.setText(formatnum(self.wd.Ron_Gon_histogram()['stddev'],precision=2))		# update standard deviation
		self.average.setText(formatnum(self.wd.Ron_Gon_histogram()['average'],precision=2))		# update average
		self.numberofdevices.setText(str(self.wd.Ron_Gon_histogram()['N']))		# update number of devices
		#self.__refresh_minsetting_display()		# update lower limit display since std dev and average changed with calculation
		#self.__refresh_maxsetting_display()		# update lower limit display since std dev and average changed with calculation
		# get device names in bins
		self.devices_bin=self.wd.Ron_Gon_histogram()['D']	# array of devices' names in bins indexed by [ib][idev] at the selected gate voltage where ib
		# and idev are the bin and device indices respectively
		self.X = self.wd.Ron_Gon_histogram()['X']	# array of devices' X-location in bins indexed by [ib][idev] at the selected gate voltage where ib
		# and idev are the bin and device indices respectively
		self.Y = self.wd.Ron_Gon_histogram()['Y']	# array of devices' Y-location in bins indexed by [ib][idev] at the selected gate voltage where ib
		# and idev are the bin and device indices respectively
		self.RGon = self.wd.Ron_Gon_histogram()['R']	# array of devices' Ron or Gon in bins indexed by [ib][idev] at the selected gate voltage where ib

		devicelistingopen=True
		try: self.devicelisting.isVisible()
		except: devicelistingopen=False
		if devicelistingopen and hasattr(self,"devicelisting") and self.devicelisting.isVisible():
			#self.__open_device_listing()	# clear device listing on data update
			if self.Vgs_comboBox.currentText()!='': Vgs=float(self.Vgs_comboBox.currentText())
			else: Vgs=None
			self.devicelisting.table_update(Vgs=Vgs,minTLMlength=self.TLMlengthminimum.currentText(),maxTLMlength=self.TLMlengthmaximum.currentText(),Vds_foc=self.Vds_FOC.text(),deltaVgsplusthres=self.delta_Vgs_thres.text(),fractVgsfit=self.Yf_Vgsfitrange_frac.text(),performYf=self.Yf_checkBox.isChecked())
# When no value is specified, the item takes its data as the average of all its children's data
		try: isvis=self.ddump.isVisible()
		except: return
		if hasattr(self,'ddump') and self.ddump.isVisible():
			self.ddump.TLM_table_refresh()
			message=self.wd.Ron_Gon_histogram(minRon=self.__minRon[-1], binsizeRondev=self.__binsizeRondev, binsizepolicy=self.__binsizepolicy, maxRon=self.__maxRon[-1], includes=self.set_includes.text(),
			                                  fractVdsfit_Ronfoc=self._fractVdsfit, recalc='yes', RG=self._histogram_data_type, Vgs_selected=float(self.Vgs_comboBox.currentText()),
			                                  logplot=self._logplot,transfercurve_smoothing_factor=self.transfer_curve_smoothing_factor_number)
			self.bins=plothistRon(binmin=self.wd.Ron_Gon_histogram()['binmin'], binmax=self.wd.Ron_Gon_histogram()['binmax'], datahist=self.wd.Ron_Gon_histogram()['R'], figurecanvas=self._figure_hist, canvas=self._canvas_hist, xlabel=self.__xlabel, logplot=self._logplot)
		self.RefreshDeviceData.emit()  # notify about device data updates e.g. notify the wafer map layout in actions_plot_widget.py
		return
###################################################################################################################################################################################################
# set up the Vgs selector
	def __Vgs_selector_setup(self):
		if self._Vgsarray!=None:
			self.Vgs_comboBox.clear()			# first clear the Vgs setup
			self.Vgs_comboBox.blockSignals(True)
			for iVgs in range(0,len(self._Vgsarray)):
				self.Vgs_comboBox.addItem(formatnum(self._Vgsarray[iVgs]))
			setindex=self.Vgs_comboBox.findText(formatnum(self._Vgsarray[min(range(len(self._Vgsarray)), key=lambda i: self._Vgsarray[i])]))			# set Vgs to minimum value possible to initialize
			self.Vgs_comboBox.setCurrentIndex(setindex)
			self.Vgs_comboBox.setEnabled(True)
			self.Vgs_comboBox.blockSignals(False)
		else:			# have no family of curves so cannot set gate voltage
			self.Vgs_comboBox.blockSignals(True)
			self.Vgs_comboBox.setEnabled(False)
####################################################################################################################################################################################################
# set up the minimum and maximum TLM lengths selector for the TLM linear fit
	def __TLMlength_selector_setup(self):
		self.TLMlengthminimum.clear()
		self.TLMlengthmaximum.clear()
		self.TLMlengthminimum.setDuplicatesEnabled(False)
		self.TLMlengthmaximum.setDuplicatesEnabled(False)
		if self.wd.tlmlength==None:						# are the geometries of the TLMs in the geometry.csv file? If not, we cannot calculate TLM parameters
			self.TLMlengthminimum.blockSignals(True)
			self.TLMlengthminimum.setEnabled(False)
			self.TLMlengthmaximum.blockSignals(True)
			self.TLMlengthmaximum.setEnabled(False)
			return										# cannot calculate TLM data because there is either no geometry.csv file or no TLM length/width data in the existing geometry.csv file

		if self.measurementtype.currentText()=="TLM contact resistance" or self.measurementtype.currentText()=="TLM channel resistance":				# allow selection of TLM lengths only if we have selected TLM parameters
			self.TLMlengthminimum.setEnabled(True)
			self.TLMlengthminimum.blockSignals(False)
			self.TLMlengthmaximum.setEnabled(True)
			self.TLMlengthmaximum.blockSignals(False)
		else:
			self.TLMlengthminimum.blockSignals(True)
			self.TLMlengthminimum.setEnabled(False)
			self.TLMlengthmaximum.blockSignals(True)
			self.TLMlengthmaximum.setEnabled(False)
		if len([self.wd.tlmlength[k] for k in self.wd.tlmlength.keys()])>1:
			self.TLMlengthminimum.addItems([str(l) for l in sorted([self.wd.tlmlength[k] for k in self.wd.tlmlength.keys()]) ][:-1])						# add all but the highest value of TLM lengths to the minimum selector
			self.TLMlengthmaximum.addItems([str(l) for l in sorted([self.wd.tlmlength[k] for k in self.wd.tlmlength.keys()]) ][1:])						# add all but the lowest value of TLM lengths to the maximum selector
			self.TLMlengthminimum.setCurrentIndex(0)
			self.TLMlengthmaximum.setCurrentIndex(self.TLMlengthmaximum.count()-1)

####################################################################################################################################################################################################
####################################################################################################################################################################################################
# the user set the minimum TLM length for the TLM linear fit. Assumes that the selectors have already been set up
	def __changedmaxTLMlength(self):
		self.TLMlengthminimum.blockSignals(True)
		self.TLMlengthminimum.setEnabled(False)
		currentlength=self.TLMlengthminimum.currentText()			# save the present TLM length setting
		self.TLMlengthminimum.clear()								# clear all minimum TLM settings before adding
		self.TLMlengthminimum.addItems([str(l) for l in sorted([self.wd.tlmlength[k] for k in self.wd.tlmlength.keys()]) if l<float(self.TLMlengthmaximum.currentText())])
		self.TLMlengthminimum.setCurrentIndex(self.TLMlengthminimum.findText(currentlength))		# set minimum TLM setting to former setting
		self.TLMlengthminimum.blockSignals(False)
		self.TLMlengthminimum.setEnabled(True)
		self._update()
####################################################################################################################################################################################################
###################################################################################################################################################################################################
# the user set the minimum TLM length for the TLM linear fit. Assumes that the selectors have already been set up
	def __changedminTLMlength(self):
		self.TLMlengthmaximum.blockSignals(True)
		self.TLMlengthmaximum.setEnabled(False)
		currentlength=self.TLMlengthmaximum.currentText()			# save the present TLM length setting
		self.TLMlengthmaximum.clear()								# clear all minimum TLM settings before adding
		self.TLMlengthmaximum.addItems([str(l) for l in sorted([self.wd.tlmlength[k] for k in self.wd.tlmlength.keys()]) if l>float(self.TLMlengthminimum.currentText())])
		self.TLMlengthmaximum.setCurrentIndex(self.TLMlengthmaximum.findText(currentlength))		# set maximum TLM setting to former setting
		self.TLMlengthmaximum.blockSignals(False)
		self.TLMlengthmaximum.setEnabled(True)
		self._update()

###################################################################################################################################################################################################
# the user changed the requested TLM linear fit quality
	def __changedTLMfitquality(self):
		self.TLM_fit_quality.blockSignals(True)
		if self.TLM_fit_quality.text()=="":
			self.TLMlinearfitquality_request=0.
			#self.TLM_fit_quality.setText("0.")
		try: self.TLMlinearfitquality_request=float(self.TLM_fit_quality.text())
		except:
			m=QtWidgets.QMessageBox()
			m.setText("ERROR Illegal value for linear fit quality, must be a number between 0 and 1")
			m.exec_()
			self.TLM_fit_quality.setText("0.")
			self.TLMlinearfitquality_request=0.
		self.TLM_fit_quality.blockSignals(False)
		self._update()
####################################################################################################################################################################################################
# # user has changed the Vds range for the linear fit
	def __set_range_linfit(self):
		if float(self.range_linearfit.text())<0.1:
			self._fractVdsfit=0.1
			#self.range_linearfit.setText(str('{:5.2f}'.format(self.__fractVdsfit)))
			self.range_linearfit.setText(formatnum(self._fractVdsfit,precision=2))
			return
		elif float(self.range_linearfit.text())>1.:
			self._fractVdsfit=1.
			#self.range_linearfit.setText(str('{:5.2f}'.format(self.__fractVdsfit)))
			self.range_linearfit.setText(formatnum(self._fractVdsfit,precision=2))
			return
		if abs(float(self.range_linearfit.text())-self._fractVdsfit)>self.__epsilon: # has this changed?
			self._fractVdsfit=float(self.range_linearfit.text())
			self._update()
####################################################################################################################################################################################################
# # user has changed the Vds value to find the |Id| at the selected Vds and at the Vgs which maximally turns on the FET i.e. the Vgs which should yield the highest |Id| at the selected Vds
# set self._Vdsfocsetting
	def __changedVdsfoc(self):
		if is_number(self.Vds_FOC.text()):
			self._Vdsfocsetting=float(self.Vds_FOC.text())
		else:       # restore earlier setting if new setting isn't a valid number
			self.Vds_FOC.setText(formatnum(self._Vdsfocsetting,precision=2))
		self._update()
####################################################################################################################################################################################################
# # user has changed the deltaVgs value to find the |Id| at the selected deltaVgs+Vthreshold
#
	def __changeddeltaVgs(self):
		if is_number(self.delta_Vgs_thres.text()):
			self._deltaVgssetting=float(self.delta_Vgs_thres.text())
			self._update()
		else:       # restore earlier setting if new setting isn't a valid number
			self.delta_Vgs_thres.setText(formatnum(self._deltaVgssetting,precision=2))
####################################################################################################################################################################################################
# # user has changed the Vgs fit range for the linear fit of Yf
#
	def __changed_Vgsfract_Yf(self):
		if is_number(self.Yf_Vgsfitrange_frac.text()):
			self._Yf_fractVgssetting=float(self.Yf_Vgsfitrange_frac.text())
			self._update()
		else:       # restore earlier setting if new setting isn't a valid number
			self.Yf_Vgsfitrange_frac.setText(formatnum(self._Yf_fractVgssetting,precision=2))
####################################################################################################################################################################################################
# # user has clicked the checkbox to turn on or off Y-function analysis
#
	def __Yf_clickedcheckbox(self):
		if self.Yf_checkBox.isChecked():
			self.delta_Vgs_thres.setEnabled(True)
			self.delta_Vgs_thres.blockSignals(False)
			self.Yf_Vgsfitrange_frac.setEnabled(True)
			self.Yf_Vgsfitrange_frac.blockSignals(False)
		else:
			self.delta_Vgs_thres.setEnabled(False)
			self.delta_Vgs_thres.blockSignals(True)
			self.Yf_Vgsfitrange_frac.setEnabled(False)
			self.Yf_Vgsfitrange_frac.blockSignals(True)
		self._update()
####################################################################################################################################################################################################
########## Plot IV for selected device ************************
	def plotiv(self,row,column):
		if column!=0: return		# interested only in the device names which are in the first column
		if row<0 or column<0: return 	# have not selected a row and/or column
		#self.linearfitlines_but.blockSignals(False)
		#self.linearfitlines_but.setEnabled(True)			# enable the button which toggles whether least squares linear fit lines are on or off
		plot_family_of_curves(self.wd.DCd[self.tableWidget.item(row,0).text()],self.__figure_IV,self.__canvas_IV,plotlin=self.__linfit_linesdisplay)

######### Plot single-swept transfer curves for selected device ****************
	def plottrans(self,row,column):
		if column !=0: return 		# interested only in the device names which are in the first column
		if row<0 or column<0: return 	# have not selected a row and/or column
		for cd in self.wd.DCd:
			if cd.get_devicename()==self.tableWidget.item(row,0).text():
				plot_transfer(cd,self.__figure_trans,self.__canvas_trans,removeleakage=True,single_double='single')
				#print("plot transfer") # debug
				del cd
######### Plot dual-swept transfer curves for selected device ****************
	def plottransdual(self,row,column):
		#print("from actions_histogram.py plottransdual() line 643: row,col",row,column)	#debug
		if hasattr(self.wd.DCd[self.wd.focfirstdevindex],'Id_TF') and self.wd.DCd[self.wd.focfirstdevindex].Idmax_TF()!="None":
			if column !=0: return 		# interested only in the device names which are in the first column
			if row<0 or column<0: return 	# have not selected a row and/or column
			for cd in self.wd.DCd:
				if cd.get_devicename()==self.tableWidget.item(row,0).text():
					#print("from actions_histogram.py plottransdual() line 647: device name",cd.get_devicename())	#debug
					#if not hasattr(self,"dualtrans" or not self.dualtrans.isVisible() ):
					try: self.dataplot.close()
					except: pass
					try: del(self.dataplot)
					except: pass
					self.transdual=PlotGraphWidget(self,dev=cd, plottype='double transfer')
					self.transdual.setAttribute(QtCore.Qt.WA_DeleteOnClose)
					self.transdual.move(self.x()+self.width(),self.y()+self.height())
					self.transdual.lower()
					self.transdual.show()
					del cd
# ######### Plot TLM linear fit for selected TLM site ************
	def plotTLMsite(self,row,column):
		if column !=0: return 		# interested only in the device names which are in the first column
		if row<0 or column<0: return 	# have not selected a row and/or column
		for cd in self.wd.DCd:
			if cd.get_devicename()==self.tableWidget.item(row,0).text():
				plot_transfer(cd,self.__figure_trans,self.__canvas_trans,removeleakage=True,single_double='single')
				#print("plot transfer") # debug
				del cd
##########disable all widgets
	def disableall(self):
		self.set_includes.blockSignals(True)
		self.set_includes.setEnabled(False)
		self.measurementtype.blockSignals(True)
		self.measurementtype.setEnabled(False)
		self.selectmintype.blockSignals(True)
		self.selectmintype.setEnabled(False)
		self.selectmaxtype.blockSignals(True)
		self.selectmaxtype.setEnabled(False)
		self.minimum.blockSignals(True)
		self.minimum.setEnabled(False)
		self.maximum.blockSignals(True)
		self.maximum.setEnabled(False)
		self.range_linearfit.blockSignals(True)
		self.range_linearfit.setEnabled(False)
		self.binsizepolicy.blockSignals(True)
		self.binsizepolicy.setEnabled(False)
		self.binsize_stddev.blockSignals(True)
		self.binsize_stddev.setEnabled(False)
		self.Vgs_comboBox.blockSignals(True)
		self.Vgs_comboBox.setEnabled(False)
		#self.linearfitlines_but.setEnabled(False)
		#self.linearfitlines_but.blockSignals(True)
		self.open_filter_but.setEnabled(False)
		self.open_filter_but.blockSignals(True)
		self.export_but.setEnabled(False)
		self.export_but.blockSignals(True)
		self.device_list_but.setEnabled(False)
		self.device_list_but.blockSignals(True)
		self.log_linear_histogram_but.setEnabled(False)
		self.log_linear_histogram_but.blockSignals(True)
		self.TLMlengthminimum.setEnabled(False)
		self.TLMlengthminimum.blockSignals(True)
		self.TLMlengthmaximum.setEnabled(False)
		self.TLMlengthmaximum.blockSignals(True)
		self.TLM_fit_quality.setEnabled(False)
		self.TLM_fit_quality.blockSignals(True)
		# self.waferplanfile.blockSignals(True)
		# self.waferplanfile.setEnabled(False)
##########enable all widgets
	def enableall(self):
		self.set_includes.blockSignals(False)
		self.set_includes.setEnabled(True)
		self.measurementtype.blockSignals(False)
		self.measurementtype.setEnabled(True)
		self.selectmintype.blockSignals(False)
		self.selectmintype.setEnabled(True)
		self.selectmaxtype.blockSignals(False)
		self.selectmaxtype.setEnabled(True)
		self.minimum.blockSignals(False)
		self.minimum.setEnabled(True)
		self.maximum.blockSignals(False)
		self.maximum.setEnabled(True)
		self.range_linearfit.blockSignals(False)
		self.range_linearfit.setEnabled(True)
		self.binsizepolicy.blockSignals(False)
		self.binsizepolicy.setEnabled(True)
		self.binsize_stddev.blockSignals(False)
		self.binsize_stddev.setEnabled(True)
		self.Vgs_comboBox.blockSignals(False)
		self.Vgs_comboBox.setEnabled(True)
		self.open_filter_but.blockSignals(False)
		self.open_filter_but.setEnabled(True)
		self.export_but.setEnabled(True)
		self.export_but.blockSignals(False)
		self.device_list_but.setEnabled(True)
		self.device_list_but.blockSignals(False)
		self.log_linear_histogram_but.setEnabled(True)
		self.log_linear_histogram_but.blockSignals(False)
################################################
# pick devices from histogram
	def devicepickhist(self,event):
		if event.button==3 and len(self.wafername.text())>0: # right button clicked and we have a wafer selected
			number_of_selected_devices=0					# number of devices in selected bin (if no bin is selected then this remains at 0)
			for ipickbin in range(0,len(self.wd.Ron_Gon_histogram()['R'])):		# find out which measured device(s) are selected by the mouse on the histogram plot
				if event.xdata<=self.wd.Ron_Gon_histogram()['binmax'][ipickbin] and event.xdata>self.wd.Ron_Gon_histogram()['binmin'][ipickbin] and len(self.wd.Ron_Gon_histogram()['R'][ipickbin])>0:	# which bin is selected on histogram?
					self.__ipickbin=ipickbin
					number_of_selected_devices=len(self.devices_bin[ipickbin])
					try: Vgs=float(self.Vgs_comboBox.currentText())
					except: Vgs=None
					bindat,colheaders=all_device_data_to_table(wd=self.wd, selecteddevices=self.devices_bin[ipickbin], Vgs=Vgs, fractVdsfit=self._fractVdsfit, minTLMlength=self.TLMlengthminimum.currentText(),
					                                           maxTLMlength=self.TLMlengthmaximum.currentText(),linearfitquality_request=self.TLMlinearfitquality_request,Vds_foc=float(self.Vds_FOC.text()), deltaVgsplusthres=float(self.delta_Vgs_thres.text()))
					self.Device_Listing_Table.setup(hheaders=colheaders,vheaders=list(bindat.keys()),data=bindat)				# display data table of selected bin
					if self.Device_Listing_Table.rowCount()<11: numberofrowsdisplayed=self.Device_Listing_Table.rowCount()			# limit the number of rows to be displayed here to 20
					else: numberofrowsdisplayed=10
					self.Device_Listing_Table.setFixedHeight(50+25*numberofrowsdisplayed)
					self.Device_Listing_Table.resizeColumnsToContents()
					# now plot histogram again to highlight the selected bin
					#self._update() # TODO: added to try to eliminate update bug
					message=self.wd.Ron_Gon_histogram(minRon=self.__minRon[-1], binsizeRondev=self.__binsizeRondev, binsizepolicy=self.__binsizepolicy, maxRon=self.__maxRon[-1], includes=self.set_includes.text(), fractVdsfit_Ronfoc=self._fractVdsfit, recalc='yes', RG=self._histogram_data_type, Vgs_selected=Vgs, logplot=self._logplot,transfercurve_smoothing_factor=self.transfer_curve_smoothing_factor_number)
					self.bins=plothistRon(binmin=self.wd.Ron_Gon_histogram()['binmin'], binmax=self.wd.Ron_Gon_histogram()['binmax'], datahist=self.wd.Ron_Gon_histogram()['R'], figurecanvas=self._figure_hist, canvas=self._canvas_hist, xlabel=self.__xlabel, highlightbarindex=ipickbin, logplot=self._logplot)
			# no bin is selected so clear bin selections
			if number_of_selected_devices==0:
				self.bins=plothistRon(binmin=self.wd.Ron_Gon_histogram()['binmin'], binmax=self.wd.Ron_Gon_histogram()['binmax'], datahist=self.wd.Ron_Gon_histogram()['R'], figurecanvas=self._figure_hist, canvas=self._canvas_hist, xlabel=self.__xlabel, logplot=self._logplot)
				self.clearhistogrambindevicelist()
				self.selected_bin_only_but.setVisible(False)
				self.selected_bin_only_but.blockSignals(True)
			else:
				self.selected_bin_only_but.setVisible(True)
				self.selected_bin_only_but.blockSignals(False)
# #################################################################################################################################
# 	# user clicked on row header i.e. device name so plot device IV and/or other parameters
	def select_plot_menu(self,devicename):
		select_device_to_plot_menu(parent=self,cd=self.wd.DCd[devicename])
# #################################################################################################################################
# #################################################################################################################################
# clear list of bin-picked devices of selected devices
	def clearhistogrambindevicelist(self):
		self.Device_Listing_Table.clear()
		self.Device_Listing_Table.setRowCount(0)
		self.Device_Listing_Table.setColumnCount(0)
		self.Device_Listing_Table.setFixedHeight(0)
# #################################################################################################################################
########################################################################################################################
# set minimum and maximum for data filtering on histograms
	def minmaxpickhist(self,event):
		mods = QtWidgets.QApplication.keyboardModifiers()
		if len(self.wafername.text())>0:
			if event.button==1 and mods==QtCore.Qt.ShiftModifier:	# left mouse button clicked and we have a wafer selected so set lower bounds of histogram and replot histogram
				if len(self.__minRon)!=len(self.__maxRon): raise ValueError("ERROR! histerogram limit stacks not equal")
				if len(self.__minRon)<self.__maxstacksize:			# push new value onto stack if not at max stack size
					self.__maxRon.append(self.__maxRon[-1])
					self.__minRon.append(event.xdata)
				else: # rotate push settings onto stacks
					maxRontemp=self.__maxRon[-1]
					self.__maxRon.rotate(-1)
					self.__maxRon[-1]=maxRontemp
					self.__minRon.rotate(-1)
					self.__minRon[-1]=event.xdata		# set lower limit of histogram using mouse
				self._update()					# update plots and data
			if event.button==3 and mods==QtCore.Qt.ShiftModifier:	# right mouse button clicked and we have a wafer selected so set lower bounds of histogram and replot histogram
				if len(self.__minRon)!=len(self.__maxRon): raise ValueError("ERROR! histerogram limit stacks not equal")
				if len(self.__maxRon)<self.__maxstacksize:			# push new value onto stack if not at max stack size
					self.__minRon.append(self.__minRon[-1])
					self.__maxRon.append(event.xdata)
				else:
					minRontemp=self.__minRon[-1]
					self.__minRon.rotate(-1)
					self.__minRon[-1]=minRontemp
					self.__maxRon.rotate(-1)
					self.__maxRon[-1]=event.xdata		# set lower limit of histogram using mouse
				self._update()					# update plots and data
########################################################################################################################
# save state, settings and data
	def __save_state(self):
		dir_save=self.dirname+sub('save')
		if not os.path.exists(dir_save):
			os.makedirs(dir_save)				# if necessary, create the directory which will hold the saved state and data
		datasettings=[self._histogram_data_type, self.__minRon[-1], self.__maxRon[-1], self.__binsizeRondev, self._fractVdsfit, self.__binsizepolicy, self.__previousmeasurementtype, self.__ipickbin, self._Vgsarray,self.devicewidthspecified,self.wd.focfirstdevindex]
		print('data dump',dir_save+'/'+self.wd.get_wafername()+'_savedsettings.sav',dir_save+'/'+self.wd.get_wafername()+'_savedwaferdata.sav')
		pick.dump(datasettings,open(dir_save+'/'+self.wd.get_wafername()+'_savedsettings.sav',"wb"))
		pick.dump(self.wd.DCd,open(dir_save+'/'+self.wd.get_wafername()+'_savedwaferdata.sav',"wb"))
		#pick.dump(self.wd, open(dir_save + '/' + self.wd.get_wafername() + '_savedwaferdata.sav', "wb"))
########################################################################################################################
########################################################################################################################
# recall and reload saved state, settings and data original version
# 	def __recall_state(self):
# 		self.disableall()						# disable widgets so they don't throw unwanted signals during loading of the saved values
# 		dirdialog=QtWidgets.QFileDialog()
# 		dirdialog.ShowDirsOnly
# 		if not hasattr(self,"lastdirectory") or not os.path.exists(self.lastdirectory):
# 			if "Windows" in platform.system(): self.lastdirectory="C:\\"
# 			elif "Linux" in platform.system(): self.lastdirectory=str(os.path.expanduser("~"))
# 			else: raise ValueError("ERROR! Not a known OS")
# 		os.chdir(self.lastdirectory)
# 		dirnametemp= dirdialog.getExistingDirectory(self,self.lastdirectory)     # get selected directory name
# 		self.dirname=dirnametemp.replace("\\","/")
# 		dir_save=self.dirname+sub('save')
# 		try: filelisting=os.listdir(dir_save)
# 		except:
# 			m=QtWidgets.QMessageBox()
# 			m.setText("failed to load filelisting\n Apparently no complete set of previously saved data or settings found in directory "+dir_save+"\nMust load wafer data and re-compute")
# 			m.exec_()
# 			return
# 		filesaveddata = [f for f in filelisting if "savedwaferdata.sav" in f]
# 		filesavesettings = [f for f in filelisting if "savedsettings.sav" in f]
# 		if len(filesaveddata)>1 or len(filesavesettings)>1:
# 			m=QtWidgets.QMessageBox()
# 			m.setText("Ambiguous: found more than one file for saved data and/or saved settings.\nDelete unwanted files from the "+dir_save+" directory")
# 			m.exec_()
# 			return
# 		elif len(filesaveddata)==0. or len(filesavesettings)==0:
# 			m=QtWidgets.QMessageBox()
# 			m.setText("No complete set of previously saved data or settings found in directory "+dir_save+"\nMust load wafer data and re-compute")
# 			m.exec_()
# 			return
# 		else:			# all good so load data and settings and update widgets
# 			datasettings=pick.load(open(dir_save+'/'+filesavesettings[0],"rb"))		# get last saved settings
# 			self._histogram_data_type, self.__minRon[-1], self.__maxRon[-1], self.__binsizeRondev, includes, self._fractVdsfit, self.__binsizepolicy, self.__previousmeasurementtype, self.__ipickbin, self._Vgsarray=datasettings
# 			self.wd.DCd = pick.load(open(dir_save+'/'+filesaveddata[0],"rb"))
# 			#self.wd = pick.load(open(dir_save + '/' + filesaveddata[0], "rb"))
# 			# now set up widgets that depend on data ################
# 			self.set_includes.setText(includes)
# 			# set up Vgs selector and populate it with the available gate voltages which we measured
# 			self.__Vgs_selector_setup()
# 			#self.tableWidget.setRowCount(0)
# 			self.range_linearfit.setText(formatnum(self.wd.DCd[self.wd.focfirstdevindex].get_fractVdsfit_Ronfoc(),precision=2))
#
# 			if self.binsizepolicy.currentText()!='Directly Set':
# 				self.binsize_stddev.setEnabled(False)	# disable binsize setting unless we are setting it directly
# 			else: self.binsize_stddev.setEnabled(True)
#
# 			self.wafername.setText(self.wd.get_wafername())			# get wafername from saved data and set widget wafername display
# 			self.__binsizepolicy_changed()
# 			self.__update_binsizechanged()
# 			self.__get_type()
# 			self._update()
# 			self.enableall()
# 			return
########################################################################################################################
# recall and reload saved state, settings and data
	def __recall_state(self):
		dir_save=self.dirname+sub('save')
		datasettings=pick.load(open(dir_save+'/'+self.wd.get_wafername()+'_savedsettings.sav',"rb"))		# get last saved settings
		self._histogram_data_type, self.__minRon[-1], self.__maxRon[-1], self.__binsizeRondev, self._fractVdsfit, self.__binsizepolicy, self.__previousmeasurementtype, self.__ipickbin, self._Vgsarray,self.devicewidthspecified,self.wd.focfirstdevindex=datasettings
		self.wd.DCd = pick.load(open(dir_save+'/'+self.wd.get_wafername()+'_savedwaferdata.sav',"rb"))
		#self.wd = pick.load(open(dir_save + '/' + filesaveddata[0], "rb"))
		# now set up widgets that depend on data ################
		self.set_includes.setText("")
		# set up Vgs selector and populate it with the available gate voltages which we measured
		self.__Vgs_selector_setup()
		#self.tableWidget.setRowCount(0)
		self.range_linearfit.setText(formatnum(self.wd.DCd[self.wd.focfirstdevindex].get_fractVdsfit_Ronfoc(),precision=2))

		if self.binsizepolicy.currentText()!='Directly Set':
			self.binsize_stddev.setEnabled(False)	# disable binsize setting unless we are setting it directly
		else: self.binsize_stddev.setEnabled(True)

		self.wafername.setText(self.wd.get_wafername())			# get wafername from saved data and set widget wafername display
		self.__binsizepolicy_changed()
		self.__update_binsizechanged()
		self.wd.validdevices=list(self.wd.DCd.keys())           # do not filter devices on recall initially
		#self.__setup_type()
#		self.__get_type()
		#self._update()
		#self.enableall()
		return
########################################################################################################################
########################################################################################################################
# toggle IV plot to display or not display Ron Gon linear fit lines near Vds=0V
	def __set_linfit_linesdisplay(self):
		if self.__linfit_linesdisplay==True: self.__linfit_linesdisplay=False
		elif self.__linfit_linesdisplay==False: self.__linfit_linesdisplay=True
		# now update plots which display linear fit lines
		self.plotiv(self.tableWidget.currentRow(),0)
########################################################################################################################
# toggle between linear and log histogram data display - note this also affects how average and standard deviations are presented!
# a checked button means that the plot is linear
	def __loglinset(self):
		print("from actions_histogram.py __loglinset() line 971 is checked before?",self.log_linear_histogram_but.isChecked()) #debug
		#print("from actions_histogram.py __loglinset() line 971 is checkable?",self.log_linear_histogram_but.isCheckable()) #debug
		if self.log_linear_histogram_but.isChecked():			# Toggle from linear plots to log plots and log normal statistics (standard deviation and average)
			self.log_linear_histogram_but.setText("Log plots")
			self.log_linear_histogram_but.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(0,120,255)}')
			self._logplot=True
			self._update()
		else:
			print("from actions_histogram.py __loglinset() line 978 set linear") #debug
			self.log_linear_histogram_but.setText("Linear plots")		# then user has set to use linear plots and linear statistics (standard deviation and average)
			self.log_linear_histogram_but.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(100,200,255)}')
			self._logplot=False
			self._update()
########################################################################################################################
# user has requested to quit using X button
	def closeEvent(self,e):
		settingsfilename=os.path.join(self.app_set_dir,"pyhistogramsettings")
		filesettings = open(settingsfilename,'w')
		filesettings.write("last directory\t"+self.lastdirectory)
		print("quitting last directory is "+self.lastdirectory)
		#filesettings.write("last directory\t"+os.path.split(self.lastdirectory)[0])
		filesettings.close()
		e.accept()
# user has requested to quit using Quit button
	def quitbut(self):
		settingsfilename=os.path.join(self.app_set_dir,"pyhistogramsettings")
		filesettings = open(settingsfilename,'w')
		filesettings.write("last directory\t"+self.lastdirectory)
		print("quitting last directory is "+self.lastdirectory)
		#filesettings.write("last directory\t"+os.path.split(self.lastdirectory)[0])
		filesettings.close()
		quit()
		#return e.accept()
########################################################################################################################
# user has requested to open filter widget
# this is from
	def __open_filter_widget(self):
		try: self.filter.close()	# we want only one instance maximum of this widget open at any one time
		except: pass
			#self.filter.destroy(True)
		#del self.filter
		self.filter=FilterData(self)
		self.filter.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.filter.show()
		return
##########################################################################################################################################
# user has requested to open data dump widget
# StatisticsDump() is from file: actions_statistics_dump.py
	def __open_datadump_widget(self):
		try: self.ddump.close()		# we want only one instance maximum of this widget open at any one time
		except: pass
		self.ddump=StatisticsDump(self)
		self.ddump.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.ddump.show()
		return
##########################################################################################################################################
# user has requested to open a sorted device listing
# DeviceListing() class is in actions_devlisting.py
	def __open_device_listing(self):
		print("closing opening device listing from line 1155 in action_histogram.py") # debug
		try: self.devicelisting.close()
		except: pass
		try: del(self.devicelisting)
		except: pass
		if self.Vgs_comboBox.currentText()!='': Vgs=float(self.Vgs_comboBox.currentText())
		else: Vgs=None
		self.devicelisting=DeviceListing(self,Vgs=Vgs,minTLMlength=self.TLMlengthminimum.currentText(),maxTLMlength=self.TLMlengthmaximum.currentText(),fractVdsfit=self.range_linearfit.text())
		self.devicelisting.CloseDeviceListing.connect(self.__close_device_listing)					# clean up device listing widget on closing
		self.devicelisting.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.devicelisting.show()
		return
	def __close_device_listing(self):		# user closed device window listing
		print("delete devicelisting")
		del(self.devicelisting)

##########################################################################################################################################
# user has selected devices for analysis from wafer plot.
# When devices are selected, these devices will be exclusively analyzed
# this capability allows the user to perform statistics and analysis on select devices from the wafer map
	def set_selected_devices(self,selecteddevices=None):
		self.devicesselected=selecteddevices
		self._update()
########################################################################################################################################
# user chose to pack current data into database
	def __pack_database(self):
		self.pack_database_but.setText("Packing Database")
		self.pack_database_but.setStyleSheet("QPushButton { background-color : red; color : black; }")
		self.pack_database_but.repaint()
		self.repaint()
		#database_packer_device(wd=self.wd)
		# database_pack_transfer(wd=self.wd)
		# database_pack_1loop_transfer(wd=self.wd)
		self.pack_database_but.setText("Pack Database")
		self.pack_database_but.setStyleSheet("QPushButton { background-color : lightgreen; color : black; }")

########################################################################################################################################

##########################################################################################################################################
# user chose to narrow devices under consideration to selected bin in histogram. This could be useful for determining the relationship between bins and wafer location
	def __selectdevice_selectedbin(self):
		#print("from line 1311 actions_histogram.py",self.__ipickbin,self.devices_bin[self.__ipickbin])
		if hasattr(self,"devices_bin") and self.devices_bin!=None and len(self.devices_bin[self.__ipickbin])>1 and self.selected_bin_only_but.isChecked():             # then there are devices in the bin selected by the user from the histogram
			self.selected_bin_only_but.setText("devices only from bin")
			self.selected_bin_only_but.setStyleSheet("QPushButton { background-color : red; color : black; }")
			self.selected_bin_only_but.repaint()
			self.repaint()
			if hasattr(self,"devicesselected") and self.devicesselected!=None:
				self.devicesselectedprevious=list(self.devicesselected)               # save copy of original selected devices
			else: self.devicesselectedprevious=None
			self.devicesselected=list(self.devices_bin[self.__ipickbin])            # copy device names selected via the selected bin into the selected devices to filter
			self._update()
		else:
			if hasattr(self,"devicesselectedprevious") and self.devicesselectedprevious!=None:
				self.devicesselected=list(self.devicesselectedprevious)             # restore previous list if it exists
			else: self.devicesselected=None
			#self.bins=plothistRon(binmin=self.wd.Ron_Gon_histogram()['binmin'], binmax=self.wd.Ron_Gon_histogram()['binmax'], datahist=self.wd.Ron_Gon_histogram()['R'], figurecanvas=self._figure_hist, canvas=self._canvas_hist, xlabel=self.__xlabel, highlightbarindex=self.__ipickbin, logplot=self._logplot)
			self.selected_bin_only_but.setText("selected bin only")
			self.selected_bin_only_but.setStyleSheet("QPushButton { background-color : lightgreen; color : black; }")
			self.selected_bin_only_but.repaint()
			self.repaint()
			self._update()
#########################################################################################################################################
#########################################################################################################################################
# user changed smoothing factor for spline fit of transfer curve. The spline fit of the transfer curves are used to calculate Gm and Gm derivative
	def __changed_transfercurve_smoothing_factor(self):
		#print("from line 1341 actions_histogram.py")
		if  self.transfer_curve_smoothing_factor.text()==None or self.transfer_curve_smoothing_factor.text()=="": return          # nothing changed so just return
		if not is_number(self.transfer_curve_smoothing_factor.text()) or float(self.transfer_curve_smoothing_factor.text())<0.:
			self.transfer_curve_smoothing_factor.setText("1")
			m=QtWidgets.QMessageBox()
			m.setText("Illegal value set in transfercurve smoothing factor! setting to 1")
			m.exec_()
			self.transfer_curve_smoothing_factor_number=1
		elif is_number(self.transfer_curve_smoothing_factor.text()):
			if floatequal(self.transfer_curve_smoothing_factor_number,float(self.transfer_curve_smoothing_factor.text()),1E-2): return          # nothing to do since the smoothing factor has not significantly changed
			else: self.transfer_curve_smoothing_factor_number=float(self.transfer_curve_smoothing_factor.text())
		else: self.transfer_curve_smoothing_factor_number=None

		# update smoothing factors for all gm types
		for dk,d in self.wd.DCd.items():              # update smoothing factors, transfer curves and gm
			d.gm_T(smoothing_factor=self.transfer_curve_smoothing_factor_number)
			d.gm_TF(smoothing_factor=self.transfer_curve_smoothing_factor_number)
			d.gm_TR(smoothing_factor=self.transfer_curve_smoothing_factor_number)
			d.gm_T3(smoothing_factor=self.transfer_curve_smoothing_factor_number)
			d.gm_T4(smoothing_factor=self.transfer_curve_smoothing_factor_number)
		self.RefreshDeviceData.emit()
		self.update()

##########################################################################################################################################
# custom QTableWidget item to enable numerical sorting
###############################################################################
# subclass of item to enable custom sorting i.e. numeric
# http://stackoverflow.com/questions/2304199/how-to-sort-a-qtablewidget-with-my-own-code
class sItem(QtWidgets.QTableWidgetItem):
	def __init__(self,data=None):
		QtWidgets.QTableWidgetItem.__init__(self,data)
		self.data=data
	def __lt__(self, other):
		# try: print(float(str(self.data)),float(str(other.text())))
		# except:
		# 	print("exception")
		# 	print(self.data,other.text())

		#return float(str(self.data)) < float(str(other.text()))
		if is_number(self.data) and not is_number(other.text()): return False
		if is_number(other.text()) and not is_number(self.data): return True
		if is_number(self.data) and is_number(other.text()): return float(self.data)<float(other.text())
		return False
##########################################################################################################################################
#



