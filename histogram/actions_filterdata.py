__author__ = 'viking'
from wafer_filter_settings import *
######
# class to filter data for histogram plots
# parent is WaferHist()
##########################################################################################################################################
# filter data popup
class FilterData(Ui_Wafer_Filter_Settings,QtWidgets.QDialog):
	def __init__(self,parent=None):
		super(FilterData,self).__init__(parent)
		self.setupUi(self)
		# set up on-off buttons for filters
		self.filter_gate_compliance_but.clicked.connect(self.__filter_gate_compliance)
		self.filter_drain_compliance_but.clicked.connect(self.__filter_drain_compliance)
		self.min_Idmax_but.clicked.connect(self.__filter_min_Idmax)
		self.max_Idmax_but.clicked.connect(self.__filter_max_Idmax)
		self.min_IdmaxFOC_but.clicked.connect(self.__filter_min_IdmaxFOC)
		self.max_IdmaxFOC_but.clicked.connect(self.__filter_max_IdmaxFOC)
		self.Igmax_min_but.clicked.connect(self.__filter_Igmax_min)
		self.Igmax_max_but.clicked.connect(self.__filter_Igmax_max)
		self.min_onoffratio_but.clicked.connect(self.__filter_min_onoffratio)
		self.max_onoffratio_but.clicked.connect(self.__filter_max_onoffratio)
		self.min_gmmax_but.clicked.connect(self.__filter_min_gmmax)
		self.max_gmmax_but.clicked.connect(self.__filter_max_gmmax)

		self.TLM_Rc_min_but.clicked.connect(self.__filter_TLM_Rc_min)
		self.TLM_Rc_max_but.clicked.connect(self.__filter_TLM_Rc_max)
		self.TLM_Rsh_min_but.clicked.connect(self.__filter_TLM_Rsh_min)
		self.TLM_Rsh_max_but.clicked.connect(self.__filter_TLM_Rsh_max)

		self.Ronmin_min_but.clicked.connect(self.__filter_Ronmin_min)
		self.Ronmin_max_but.clicked.connect(self.__filter_Ronmin_max)
		# values
		self.Idmax_min_selector.editingFinished.connect(self.__changed_min_Idmax)
		self.Idmax_max_selector.editingFinished.connect(self.__changed_max_Idmax)
		self.IdmaxFOC_min_selector.editingFinished.connect(self.__changed_min_IdmaxFOC)
		self.IdmaxFOC_max_selector.editingFinished.connect(self.__changed_max_IdmaxFOC)
		self.onoffratio_min_selector.editingFinished.connect(self.__changed_min_onoffratio)
		self.onoffratio_max_selector.editingFinished.connect(self.__changed_max_onoffratio)
		self.gmmax_min_selector.editingFinished.connect(self.__changed_min_gmmax)
		self.gmmax_max_selector.editingFinished.connect(self.__changed_max_gmmax)

		self.TLM_Rc_min_selector.editingFinished.connect(self.__changed_TLM_Rc_min)
		self.TLM_Rc_max_selector.editingFinished.connect(self.__changed_TLM_Rc_max)
		self.TLM_Rsh_min_selector.editingFinished.connect(self.__changed_TLM_Rsh_min)
		self.TLM_Rsh_max_selector.editingFinished.connect(self.__changed_TLM_Rsh_max)

		self.Ronmin_min_selector.editingFinished.connect(self.__changed_Ronmin_min)
		self.Ronmin_max_selector.editingFinished.connect(self.__changed_Ronmin_max)

		self.Igmax_min_selector.editingFinished.connect(self.__changed_Igmax_min)
		self.Igmax_max_selector.editingFinished.connect(self.__changed_Igmax_max)

		# wafer label at widget
		self.wafername=self.parent().wafername.text()
		self.wafer_label.setText("Wafer: "+self.parent().wafername.text())
		self.__setup()
	# set everything back to default on closing the filter widget

	def __setup(self):
		self.__buttoncheck(self.filter_gate_compliance_but,self.parent().wd.filtergatecompliance)
		self.__buttoncheck(self.filter_drain_compliance_but,self.parent().wd.filterdraincompliance)
		self.Idmax_min_selector.blockSignals(True)
		self.Idmax_min_selector.setText(str(self.parent().wd.filter_Idmax_min))
		self.min_Idmax_but.blockSignals(True)
		self.__buttoncheck(self.min_Idmax_but, True)
		self.min_Idmax_but.blockSignals(False)
		self.Idmax_min_selector.setEnabled(True)
		self.Idmax_min_selector.blockSignals(False)
		self.Idmax_max_selector.setEnabled(True)
		self.Idmax_max_selector.blockSignals(False)

		self.IdmaxFOC_min_selector.setEnabled(True)
		self.IdmaxFOC_min_selector.blockSignals(False)
		self.IdmaxFOC_max_selector.setEnabled(True)
		self.IdmaxFOC_max_selector.blockSignals(False)

		self.onoffratio_min_selector.blockSignals(True)
		self.onoffratio_min_selector.setText(str(self.parent().wd.filter_onoff_min))
		self.min_onoffratio_but.blockSignals(True)
		self.__buttoncheck(self.min_onoffratio_but, True)
		self.min_onoffratio_but.blockSignals(False)
		self.onoffratio_min_selector.setEnabled(True)
		self.onoffratio_min_selector.blockSignals(False)
		self.onoffratio_max_selector.setEnabled(True)
		self.onoffratio_max_selector.blockSignals(False)
		self.filterchanged=False
##### gate compliance filter switch##################################
	def __filter_gate_compliance(self):
		if self.filter_gate_compliance_but.isChecked():
			self.__buttoncheck(self.filter_gate_compliance_but,True)
			self.parent().wd.filtergatecompliance=True
			self.filterchanged=True
			#self.parent()._update()
		else:
			self.__buttoncheck(self.filter_gate_compliance_but,False)
			self.parent().wd.filtergatecompliance=False
			self.filterchanged=True
			#self.parent()._update()
################################################
#######drain compliance filter switch
	def __filter_drain_compliance(self):
		if self.filter_drain_compliance_but.isChecked():
			self.__buttoncheck(self.filter_drain_compliance_but,True)
			self.parent().wd.filterdraincompliance=True
			self.filterchanged=True
			#self.parent()._update()
		else:
			self.__buttoncheck(self.filter_drain_compliance_but,False)
			self.parent().wd.filterdraincompliance=False
			self.filterchanged=True
			#self.parent()._update()
##############################################################################################
# |Idmax|
######## user changed value
	def __changed_min_Idmax(self):
		self.__buttoncheck(self.min_Idmax_but,True)
		self.__filter_min_Idmax()
#######Idmax lower filter switch
	def __filter_min_Idmax(self):
		if self.min_Idmax_but.isChecked():
			self.Idmax_min_selector.setEnabled(True)
			self.Idmax_min_selector.blockSignals(False)
#			print("from action_histogram.py line 989, self.parent().wd.filter_Idmax_min", float(self.Idmax_min_selector.text()))
			try: self.parent().wd.filter_Idmax_min=float(self.Idmax_min_selector.text())		# get value
			except:	self.__buttoncheck(self.min_Idmax_but,False)
			# is the input valid?
			if self.min_Idmax_but.isChecked() and self.parent().wd.filter_Idmax_min>=0:
				if self.parent().wd.filter_Idmax_max!=None:
					if self.parent().wd.filter_Idmax_max>self.parent().wd.filter_Idmax_min  and self.parent().wd.filter_Idmax_min>=0:
						self.__buttoncheck(self.min_Idmax_but,True)
					else:
						self.parent().wd.filter_Idmax_min=None
						self.__buttoncheck(self.min_Idmax_but,False)
						self.Idmax_min_selector.setText("")
				else:
					self.__buttoncheck(self.min_Idmax_but,True)

			else:		# input not valid so leave unchecked and clear entry
				self.__buttoncheck(self.min_Idmax_but,False)
				self.parent().wd.filter_Idmax_min=None
				self.Idmax_min_selector.setText("")
		else:
			self.Idmax_min_selector.setEnabled(False)
			self.Idmax_min_selector.blockSignals(True)
			self.__buttoncheck(self.min_Idmax_but,False)
			self.parent().wd.filter_Idmax_min=None
		for devk in self.parent().wd.DCd: self.parent().wd.DCd[devk].Idmax_T()					# must read Idmax to properly update
		self.filterchanged=True
		#self.parent()._update()
#############################################
######## user changed value
	def __changed_max_Idmax(self):
		self.__buttoncheck(self.max_Idmax_but,True)
		self.__filter_max_Idmax()
#######Idmax upper filter switch
	def __filter_max_Idmax(self):
		if self.max_Idmax_but.isChecked():
			self.Idmax_max_selector.setEnabled(True)
			self.Idmax_max_selector.blockSignals(False)
			try: self.parent().wd.filter_Idmax_max=float(self.Idmax_max_selector.text())		# get value
			except:	self.__buttoncheck(self.max_Idmax_but,False)
			# is the input valid?
			if self.max_Idmax_but.isChecked() and self.parent().wd.filter_Idmax_max>=0:
				if self.parent().wd.filter_Idmax_min!=None:
					if self.parent().wd.filter_Idmax_max>self.parent().wd.filter_Idmax_min  and self.parent().wd.filter_Idmax_max>=0:
						self.__buttoncheck(self.max_Idmax_but,True)
					else:
						self.parent().wd.filter_Idmax_max=None
						self.__buttoncheck(self.max_Idmax_but,False)
						self.Idmax_max_selector.setText("")
				else:
					self.__buttoncheck(self.max_Idmax_but,True)
			else:		# input not valid so leave unchecked and clear entry
				self.__buttoncheck(self.max_Idmax_but,False)
				self.parent().wd.filter_Idmax_max=None
				self.Idmax_max_selector.setText("")
		else:
			self.Idmax_max_selector.setEnabled(False)
			self.Idmax_max_selector.blockSignals(True)
			self.__buttoncheck(self.max_Idmax_but,False)
			self.parent().wd.filter_Idmax_max=None
		for devk in self.parent().wd.DCd: self.parent().wd.DCd[devk].Idmax_T()					# must read Idmax to properly update
		self.filterchanged=True
		#self.parent()._update()
##############################################
# done with |Idmax|
###################################################################################################
##############################################################################################
# |Idmax|FOC
######## user changed value
	def __changed_min_IdmaxFOC(self):
		self.__buttoncheck(self.min_IdmaxFOC_but,True)
		self.__filter_min_IdmaxFOC()
#######IdmaxFOC lower filter switch
	def __filter_min_IdmaxFOC(self):
		if self.min_IdmaxFOC_but.isChecked():
			self.IdmaxFOC_min_selector.setEnabled(True)
			self.IdmaxFOC_min_selector.blockSignals(False)
			try: self.parent().wd.filter_IdmaxFOC_min=float(self.IdmaxFOC_min_selector.text())		# get value
			except:	self.__buttoncheck(self.min_IdmaxFOC_but,False)
			# is the input valid?
			if self.min_IdmaxFOC_but.isChecked() and self.parent().wd.filter_IdmaxFOC_min>=0:
				if self.parent().wd.filter_IdmaxFOC_max!=None:
					if self.parent().wd.filter_IdmaxFOC_max>self.parent().wd.filter_IdmaxFOC_min  and self.parent().wd.filter_IdmaxFOC_min>=0:
						self.__buttoncheck(self.min_IdmaxFOC_but,True)
					else:
						self.parent().wd.filter_IdmaxFOC_min=None
						self.__buttoncheck(self.min_IdmaxFOC_but,False)
						self.IdmaxFOC_min_selector.setText("")
				else:
					self.__buttoncheck(self.min_IdmaxFOC_but,True)

			else:		# input not valid so leave unchecked and clear entry
				self.__buttoncheck(self.min_IdmaxFOC_but,False)
				self.parent().wd.filter_IdmaxFOC_min=None
				self.IdmaxFOC_min_selector.setText("")
		else:
			self.IdmaxFOC_min_selector.setEnabled(False)
			self.IdmaxFOC_min_selector.blockSignals(True)
			self.__buttoncheck(self.min_IdmaxFOC_but,False)
			self.parent().wd.filter_IdmaxFOC_min=None
		for devk in self.parent().wd.DCd: self.parent().wd.DCd[devk].Idmax_foc(Vds=self.parent().Vds_FOC.text())					# must read IdmaxFOC to properly update
		self.filterchanged=True
		#self.parent()._update()
#############################################
######## user changed value
	def __changed_max_IdmaxFOC(self):
		self.__buttoncheck(self.max_IdmaxFOC_but,True)
		self.__filter_max_IdmaxFOC()
#######IdmaxFOC upper filter switch
	def __filter_max_IdmaxFOC(self):
		if self.max_IdmaxFOC_but.isChecked():
			self.IdmaxFOC_max_selector.setEnabled(True)
			self.IdmaxFOC_max_selector.blockSignals(False)
			try: self.parent().wd.filter_IdmaxFOC_max=float(self.IdmaxFOC_max_selector.text())		# get value
			except:	self.__buttoncheck(self.max_IdmaxFOC_but,False)
			# is the input valid?
			if self.max_IdmaxFOC_but.isChecked() and self.parent().wd.filter_IdmaxFOC_max>=0:
				if self.parent().wd.filter_IdmaxFOC_min!=None:
					if self.parent().wd.filter_IdmaxFOC_max>self.parent().wd.filter_IdmaxFOC_min  and self.parent().wd.filter_IdmaxFOC_max>=0:
						self.__buttoncheck(self.max_IdmaxFOC_but,True)
					else:
						self.parent().wd.filter_IdmaxFOC_max=None
						self.__buttoncheck(self.max_IdmaxFOC_but,False)
						self.IdmaxFOC_max_selector.setText("")
				else:
					self.__buttoncheck(self.max_IdmaxFOC_but,True)
			else:		# input not valid so leave unchecked and clear entry
				self.__buttoncheck(self.max_IdmaxFOC_but,False)
				self.parent().wd.filter_IdmaxFOC_max=None
				self.IdmaxFOC_max_selector.setText("")
		else:
			self.IdmaxFOC_max_selector.setEnabled(False)
			self.IdmaxFOC_max_selector.blockSignals(True)
			self.__buttoncheck(self.max_IdmaxFOC_but,False)
			self.parent().wd.filter_IdmaxFOC_maxFOC=None
		for devk in self.parent().wd.DCd: self.parent().wd.DCd[devk].Idmax_foc(Vds=self.parent().Vds_FOC.text())					# must read IdmaxFOC to properly update
		self.filterchanged=True
		#self.parent()._update()
##############################################
# done with |Idmax|FOC
###################################################################################################
##############################################################################################
# On-Off Ratio filter
######## user changed value
	def __changed_min_onoffratio(self):
		self.__buttoncheck(self.min_onoffratio_but,True)
		self.__filter_min_onoffratio()
####### lower filter switch
	def __filter_min_onoffratio(self):
		if self.min_onoffratio_but.isChecked():
			self.onoffratio_min_selector.setEnabled(True)
			self.onoffratio_min_selector.blockSignals(False)
			try: self.parent().wd.filter_onoff_min=float(self.onoffratio_min_selector.text())		# get value
			except:	self.__buttoncheck(self.min_onoffratio_but,False)
			# is the input valid?
			if self.min_onoffratio_but.isChecked() and self.parent().wd.filter_onoff_min>=0:
				if self.parent().wd.filter_onoff_max!=None:
					if self.parent().wd.filter_onoff_max>self.parent().wd.filter_onoff_min  and self.parent().wd.filter_onoff_min>=0:
						self.__buttoncheck(self.min_onoffratio_but,True)
					else:
						self.parent().wd.filter_onoff_min=None
						self.__buttoncheck(self.min_onoffratio_but,False)
						self.onoffratio_min_selector.setText("")
				else:
					self.__buttoncheck(self.min_onoffratio_but,True)
			else:		# input not valid so leave unchecked and clear entry
				self.__buttoncheck(self.min_onoffratio_but,False)
				self.parent().wd.filter_onoff_min=None
				self.onoffratio_min_selector.setText("")			# clear entry
		else:
			self.onoffratio_min_selector.setEnabled(False)
			self.onoffratio_min_selector.blockSignals(True)
			self.__buttoncheck(self.min_onoffratio_but,False)
			self.parent().wd.filter_onoff_min=None
		for devk in self.parent().wd.DCd: self.parent().wd.DCd[devk].Idmax_T()					# must read Idmax to properly update
		self.filterchanged=True
		#self.parent()._update()
#############################################
######## user changed value
	def __changed_max_onoffratio(self):
		self.__buttoncheck(self.max_onoffratio_but,True)
		self.__filter_max_onoffratio()
#######upper filter switch
	def __filter_max_onoffratio(self):
		if self.max_onoffratio_but.isChecked():
			self.onoffratio_max_selector.setEnabled(True)
			self.onoffratio_max_selector.blockSignals(False)
			try: self.parent().wd.filter_onoff_max=float(self.onoffratio_max_selector.text())		# get value
			except:	self.__buttoncheck(self.max_onoffratio_but,False)
			# is the input valid?
			if self.max_onoffratio_but.isChecked() and self.parent().wd.filter_onoff_max>=0:
				if self.parent().wd.filter_onoff_min!=None:
					if self.parent().wd.filter_onoff_max>self.parent().wd.filter_onoff_min  and self.parent().wd.filter_onoff_max>=0:
						self.__buttoncheck(self.max_onoffratio_but,True)
					else:
						self.parent().wd.filter_onoff_max=None
						self.__buttoncheck(self.max_onoffratio_but,False)
						self.onoffratio_max_selector.setText("")
				else:
					self.__buttoncheck(self.max_onoffratio_but,True)
			else:		# input not valid so leave unchecked and clear entry
				self.__buttoncheck(self.max_onoffratio_but,False)
				self.parent().wd.filter_onoff_max=None
				self.onoffratio_max_selector.setText("")
		else:
			self.onoffratio_max_selector.setEnabled(False)
			self.onoffratio_max_selector.blockSignals(True)
			self.__buttoncheck(self.max_onoffratio_but,False)
			self.parent().wd.filter_onoff_max=None
		for devk in self.parent().wd.DCd: self.parent().wd.DCd[devk].Idmax_T()					# must read Idmax to properly update
		self.filterchanged=True
		#self.parent()._update()
##############################################
# done with On-Off ratio Filter
###################################################################################################
#############################################################################################
# Gmmax filter
######## user changed value
	def __changed_min_gmmax(self):
		self.__buttoncheck(self.min_gmmax_but,True)
		self.__filter_min_gmmax()
####### lower filter switch
	def __filter_min_gmmax(self):
		if self.min_gmmax_but.isChecked():
			self.gmmax_min_selector.setEnabled(True)
			self.gmmax_min_selector.blockSignals(False)
			try: self.parent().wd.filter_gmmax_min=float(self.gmmax_min_selector.text())		# get value
			except:	self.__buttoncheck(self.min_gmmax_but,False)
			# is the input valid?
			if self.min_gmmax_but.isChecked() and self.parent().wd.filter_gmmax_min>=0:
				if self.parent().wd.filter_gmmax_max!=None:
					if self.parent().wd.filter_gmmax_max>self.parent().wd.filter_gmmax_min  and self.parent().wd.filter_gmmax_min>=0:
						self.__buttoncheck(self.min_gmmax_but,True)
					else:
						self.parent().wd.filter_gmmax_min=None
						self.__buttoncheck(self.min_gmmax_but,False)
						self.gmmax_min_selector.setText("")
				else:
					self.__buttoncheck(self.min_gmmax_but,True)
			else:		# input not valid so leave unchecked and clear entry
				self.__buttoncheck(self.min_gmmax_but,False)
				self.parent().wd.filter_gmmax_min=None
				self.gmmax_min_selector.setText("")			# clear entry
		else:
			self.gmmax_min_selector.setEnabled(False)
			self.gmmax_min_selector.blockSignals(True)
			self.__buttoncheck(self.min_gmmax_but,False)
			self.parent().wd.filter_gmmax_min=None
		for devk in self.parent().wd.DCd: self.parent().wd.DCd[devk].gmmax_T()					# must read gmmax to properly update
		self.filterchanged=True
		#self.parent()._update()
#############################################
######## user changed value
	def __changed_max_gmmax(self):
		self.__buttoncheck(self.max_gmmax_but,True)
		self.__filter_max_gmmax()
#######upper filter switch
	def __filter_max_gmmax(self):
		if self.max_gmmax_but.isChecked():
			self.gmmax_max_selector.setEnabled(True)
			self.gmmax_max_selector.blockSignals(False)
			try: self.parent().wd.filter_gmmax_max=float(self.gmmax_max_selector.text())		# get value
			except:	self.__buttoncheck(self.max_gmmax_but,False)
			# is the input valid?
			if self.max_gmmax_but.isChecked() and self.parent().wd.filter_gmmax_max>=0:
				if self.parent().wd.filter_gmmax_min!=None:
					if self.parent().wd.filter_gmmax_max>self.parent().wd.filter_gmmax_min  and self.parent().wd.filter_gmmax_max>=0:
						self.__buttoncheck(self.max_gmmax_but,True)
					else:
						self.parent().wd.filter_gmmax_max=None
						self.__buttoncheck(self.max_gmmax_but,False)
						self.gmmax_max_selector.setText("")
				else:
					self.__buttoncheck(self.max_gmmax_but,True)
			else:		# input not valid so leave unchecked and clear entry
				self.__buttoncheck(self.max_gmmax_but,False)
				self.parent().wd.filter_gmmax_max=None
				self.gmmax_max_selector.setText("")
		else:
			self.gmmax_max_selector.setEnabled(False)
			self.gmmax_max_selector.blockSignals(True)
			self.__buttoncheck(self.max_gmmax_but,False)
			self.parent().wd.filter_gmmax_max=None
		for devk in self.parent().wd.DCd: self.parent().wd.DCd[devk].gmmax_T()					# must read gmmax to properly update
		self.filterchanged=True
		#self.parent()._update()
##############################################
# done with Gmmax Filter
###################################################################################################
#############################################################################################
# TLM Rc (contact resistance) filter
######## user changed value
	def __changed_TLM_Rc_min(self):
		self.__buttoncheck(self.TLM_Rc_min_but,True)
		self.__filter_TLM_Rc_min()
####### lower filter switch
	def __filter_TLM_Rc_min(self):
		if self.TLM_Rc_min_but.isChecked():
			self.TLM_Rc_min_selector.setEnabled(True)
			self.TLM_Rc_min_selector.blockSignals(False)
			try: self.parent().wd.filter_TLM_Rc_min=float(self.TLM_Rc_min_selector.text())		# get value
			except:	self.__buttoncheck(self.TLM_Rc_min_but,False)								# turn off filter button if no value set
			# is the input valid?
			if self.TLM_Rc_min_but.isChecked() and self.parent().wd.filter_TLM_Rc_min>=0:	# filter only positive Rc values
				if self.parent().wd.filter_TLM_Rc_max!=None:
					if self.parent().wd.filter_TLM_Rc_max>self.parent().wd.filter_TLM_Rc_min  and self.parent().wd.filter_TLM_Rc_min>=0:
						self.__buttoncheck(self.TLM_Rc_min_but,True)
					else:
						self.parent().wd.filter_TLM_Rc_min=None
						self.__buttoncheck(self.TLM_Rc_min_but,False)
						self.TLM_Rc_min_selector.setText("")
				else:
					self.__buttoncheck(self.TLM_Rc_min_but,True)
			else:		# input not valid so leave unchecked and clear entry
				self.__buttoncheck(self.TLM_Rc_min_but,False)
				self.parent().wd.filter_TLM_Rc_min=None
				self.TLM_Rc_min_selector.setText("")			# clear entry
		else:
			self.TLM_Rc_min_selector.setEnabled(False)
			self.TLM_Rc_min_selector.blockSignals(True)
			self.__buttoncheck(self.TLM_Rc_min_but,False)
			self.parent().wd.filter_TLM_Rc_min=None
		for devk in self.parent().wd.DCd: self.parent().wd.DCd[devk].Ron_foc()					# must read Ron to properly update
		self.filterchanged=True
		#self.parent()._update()
#############################################
######## user changed value
	def __changed_TLM_Rc_max(self):
		self.__buttoncheck(self.TLM_Rc_max_but,True)
		self.__filter_TLM_Rc_max()
#######upper filter switch
	def __filter_TLM_Rc_max(self):
		if self.TLM_Rc_max_but.isChecked():
			self.TLM_Rc_max_selector.setEnabled(True)
			self.TLM_Rc_max_selector.blockSignals(False)
			try: self.parent().wd.filter_TLM_Rc_max=float(self.TLM_Rc_max_selector.text())		# get value
			except:	self.__buttoncheck(self.TLM_Rc_max_but,False)
			# is the input valid?
			if self.TLM_Rc_max_but.isChecked() and self.parent().wd.filter_TLM_Rc_max>=0:
				if self.parent().wd.filter_TLM_Rc_min!=None:
					if self.parent().wd.filter_TLM_Rc_max>self.parent().wd.filter_TLM_Rc_min  and self.parent().wd.filter_TLM_Rc_max>=0:
						self.__buttoncheck(self.TLM_Rc_max_but,True)
					else:
						self.parent().wd.filter_TLM_Rc_max=None
						self.__buttoncheck(self.TLM_Rc_max_but,False)
						self.TLM_Rc_max_selector_selector.setText("")
				else:
					self.__buttoncheck(self.TLM_Rc_max_but,True)
			else:		# input not valid so leave unchecked and clear entry
				self.__buttoncheck(self.TLM_Rc_max_but,False)
				self.parent().wd.filter_TLM_Rc_max=None
				self.TLM_Rc_max_selector.setText("")
		else:
			self.TLM_Rc_max_selector.setEnabled(False)
			self.TLM_Rc_max_selector.blockSignals(True)
			self.__buttoncheck(self.TLM_Rc_max_but,False)
			self.parent().wd.filter_TLM_Rc_max=None
		for devk in self.parent().wd.DCd: self.parent().wd.DCd[devk].Ron_foc()					# must read Ron to properly update
		self.filterchanged=True
		#self.parent()._update()
##############################################
# done with TLM Rc (TLM contact resistance) Filter
#############################################################################################
# TLM Rsh (sheet resistance) filter
######## user changed value
	def __changed_TLM_Rsh_min(self):
		self.__buttoncheck(self.TLM_Rsh_min_but,True)
		self.__filter_TLM_Rsh_min()
####### lower filter switch
	def __filter_TLM_Rsh_min(self):
		if self.TLM_Rsh_min_but.isChecked():
			self.TLM_Rsh_min_selector.setEnabled(True)
			self.TLM_Rsh_min_selector.blockSignals(False)
			try: self.parent().wd.filter_TLM_Rsh_min=float(self.TLM_Rsh_min_selector.text())		# get value
			except:	self.__buttoncheck(self.TLM_Rsh_min_but,False)								# turn off filter button if no value set
			# is the input valid?
			if self.TLM_Rsh_min_but.isChecked() and self.parent().wd.filter_TLM_Rsh_min>=0:	# filter only positive Rsh values
				if self.parent().wd.filter_TLM_Rsh_max!=None:
					if self.parent().wd.filter_TLM_Rsh_max>self.parent().wd.filter_TLM_Rsh_min  and self.parent().wd.filter_TLM_Rsh_min>=0:
						self.__buttoncheck(self.TLM_Rsh_min_but,True)
					else:
						self.parent().wd.filter_TLM_Rsh_min=None
						self.__buttoncheck(self.TLM_Rsh_min_but,False)
						self.TLM_Rsh_min_selector.setText("")
				else:
					self.__buttoncheck(self.TLM_Rsh_min_but,True)
			else:		# input not valid so leave unchecked and clear entry
				self.__buttoncheck(self.TLM_Rsh_min_but,False)
				self.parent().wd.filter_TLM_Rsh_min=None
				self.TLM_Rsh_min_selector.setText("")			# clear entry
		else:
			self.TLM_Rsh_min_selector.setEnabled(False)
			self.TLM_Rsh_min_selector.blockSignals(True)
			self.__buttoncheck(self.TLM_Rsh_min_but,False)
			self.parent().wd.filter_TLM_Rsh_min=None
		for devk in self.parent().wd.DCd: self.parent().wd.DCd[devk].Ron_foc()					# must read Ron to properly update
		self.filterchanged=True
		#self.parent()._update()
#############################################
######## user changed value
	def __changed_TLM_Rsh_max(self):
		self.__buttoncheck(self.TLM_Rsh_max_but,True)
		self.__filter_TLM_Rsh_max()
#######upper filter switch
	def __filter_TLM_Rsh_max(self):
		if self.TLM_Rsh_max_but.isChecked():
			self.TLM_Rsh_max_selector.setEnabled(True)
			self.TLM_Rsh_max_selector.blockSignals(False)
			try: self.parent().wd.filter_TLM_Rsh_max=float(self.TLM_Rsh_max_selector.text())		# get value
			except:	self.__buttoncheck(self.TLM_Rsh_max_but,False)
			# is the input valid?
			if self.TLM_Rsh_max_but.isChecked() and self.parent().wd.filter_TLM_Rsh_max>=0:
				if self.parent().wd.filter_TLM_Rsh_min!=None:
					if self.parent().wd.filter_TLM_Rsh_max>self.parent().wd.filter_TLM_Rsh_min  and self.parent().wd.filter_TLM_Rsh_max>=0:
						self.__buttoncheck(self.TLM_Rsh_max_but,True)
					else:
						self.parent().wd.filter_TLM_Rsh_max=None
						self.__buttoncheck(self.TLM_Rsh_max_but,False)
						self.TLM_Rsh_max_selector_selector.setText("")
				else:
					self.__buttoncheck(self.TLM_Rsh_max_but,True)
			else:		# input not valid so leave unchecked and clear entry
				self.__buttoncheck(self.TLM_Rsh_max_but,False)
				self.parent().wd.filter_TLM_Rsh_max=None
				self.TLM_Rsh_max_selector.setText("")
		else:
			self.TLM_Rsh_max_selector.setEnabled(False)
			self.TLM_Rsh_max_selector.blockSignals(True)
			self.__buttoncheck(self.TLM_Rsh_max_but,False)
			self.parent().wd.filter_TLM_Rsh_max=None
		for devk in self.parent().wd.DCd: self.parent().wd.DCd[devk].Ron_foc()					# must read Ron to properly update
		self.filterchanged=True
		#self.parent()._update()
##############################################
# done with TLM Rsh (TLM sheet resistance) Filter
###################################################################################################
#############################################################################################
# Ron filter - apply a filter to the minimum value of Ron from the family of curves - calculated at the gate voltage giving the minimum Ron
######## user changed value
	def __changed_Ronmin_min(self):
		self.__buttoncheck(self.Ronmin_min_but,True)
		self.__filter_Ronmin_min()
####### lower filter switch
	def __filter_Ronmin_min(self):
		if self.Ronmin_min_but.isChecked():
			self.Ronmin_min_selector.setEnabled(True)
			self.Ronmin_min_selector.blockSignals(False)
			try: self.parent().wd.filter_Ronmin_min=float(self.Ronmin_min_selector.text())		# get value
			except:	self.__buttoncheck(self.Ronmin_min_but,False)								# turn off filter button if no value set
			# is the input valid?
			if self.Ronmin_min_but.isChecked() and self.parent().wd.filter_Ronmin_min>=0:	# filter only positive Rsh values
				if self.parent().wd.filter_Ronmin_max!=None:
					if self.parent().wd.filter_Ronmin_max>self.parent().wd.filter_Ronmin_min  and self.parent().wd.filter_Ronmin_min>=0:
						self.__buttoncheck(self.Ronmin_min_but,True)
					else:
						self.parent().wd.filter_Ronmin_min=None
						self.__buttoncheck(self.Ronmin_min_but,False)
						self.Ronmin_min_selector.setText("")
				else:
					self.__buttoncheck(self.Ronmin_min_but,True)
			else:		# input not valid so leave unchecked and clear entry
				self.__buttoncheck(self.Ronmin_min_but,False)
				self.parent().wd.filter_Ronmin_min=None
				self.Ronmin_min_selector.setText("")			# clear entry
		else:
			self.Ronmin_min_selector.setEnabled(False)
			self.Ronmin_min_selector.blockSignals(True)
			self.__buttoncheck(self.Ronmin_min_but,False)
			self.parent().wd.filter_Ronmin_min=None
		for devk in self.parent().wd.DCd: self.parent().wd.DCd[devk].Ron_foc()					# must read Ron to properly update
		self.filterchanged=True
		#self.parent()._update()
#############################################
######## user changed value
	def __changed_Ronmin_max(self):
		self.__buttoncheck(self.Ronmin_max_but,True)
		self.__filter_Ronmin_max()
#######upper filter switch
	def __filter_Ronmin_max(self):
		if self.Ronmin_max_but.isChecked():
			self.Ronmin_max_selector.setEnabled(True)
			self.Ronmin_max_selector.blockSignals(False)
			try: self.parent().wd.filter_Ronmin_max=float(self.Ronmin_max_selector.text())		# get value
			except:	self.__buttoncheck(self.Ronmin_max_but,False)
			# is the input valid?
			if self.Ronmin_max_but.isChecked() and self.parent().wd.filter_Ronmin_max>=0:
				if self.parent().wd.filter_Ronmin_min!=None:
					if self.parent().wd.filter_Ronmin_max>self.parent().wd.filter_Ronmin_min  and self.parent().wd.filter_Ronmin_max>=0:
						self.__buttoncheck(self.Ronmin_max_but,True)
					else:
						self.parent().wd.filter_Ronmin_max=None
						self.__buttoncheck(self.Ronmin_max_but,False)
						self.Ronmin_max_selector_selector.setText("")
				else:
					self.__buttoncheck(self.Ronmin_max_but,True)
			else:		# input not valid so leave unchecked and clear entry
				self.__buttoncheck(self.Ronmin_max_but,False)
				self.parent().wd.filter_Ronmin_max=None
				self.Ronmin_max_selector.setText("")
		else:
			self.Ronmin_max_selector.setEnabled(False)
			self.Ronmin_max_selector.blockSignals(True)
			self.__buttoncheck(self.Ronmin_max_but,False)
			self.parent().wd.filter_Ronmin_max=None
		for devk in self.parent().wd.DCd: self.parent().wd.DCd[devk].Ron_foc()					# must read Ron to properly update
		self.filterchanged=True
		#self.parent()._update()
##############################################
# done with Ron Filter
###################################################################################################
#############################################################################################
# |Igmax| filter
######## user changed value
	def __changed_Igmax_min(self):
		self.__buttoncheck(self.Igmax_min_but, True)
		self.__filter_Igmax_min()
	####### lower filter switch
	def __filter_Igmax_min(self):
		if self.Igmax_min_but.isChecked():
			self.Igmax_min_selector.setEnabled(True)
			self.Igmax_min_selector.blockSignals(False)
			try:
				self.parent().wd.filter_Igmax_min = float(self.Igmax_min_selector.text())  # get value
			except:
				self.__buttoncheck(self.Igmax_min_but, False)  # turn off filter button if no value set
			# is the input valid?
			if self.Igmax_min_but.isChecked() and self.parent().wd.filter_Igmax_min >= 0:  # filter only positive Rsh values
				if self.parent().wd.filter_Igmax_max != None:
					if self.parent().wd.filter_Igmax_max > self.parent().wd.filter_Igmax_min and self.parent().wd.filter_Igmax_min >= 0:
						self.__buttoncheck(self.Igmax_min_but, True)
					else:
						self.parent().wd.filter_Igmax_min = None
						self.__buttoncheck(self.Igmax_min_but, False)
						self.Igmax_min_selector.setText("")
				else:
					self.__buttoncheck(self.Igmax_min_but, True)
			else:  # input not valid so leave unchecked and clear entry
				self.__buttoncheck(self.Igmax_min_but, False)
				self.parent().wd.filter_Igmax_min = None
				self.Igmax_min_selector.setText("")  # clear entry
		else:
			self.Igmax_min_selector.setEnabled(False)
			self.Igmax_min_selector.blockSignals(True)
			self.__buttoncheck(self.Igmax_min_but, False)
			self.parent().wd.filter_Igmax_min = None
		for devk in self.parent().wd.DCd:
			self.parent().wd.DCd[devk].Igmax_T()  # must read to properly update
			self.parent().wd.DCd[devk].Igmax_TF()
			self.parent().wd.DCd[devk].Igmax_TR()
		self.filterchanged=True
		#self.parent()._update()
	#############################################
	######## user changed value
	def __changed_Igmax_max(self):
		self.__buttoncheck(self.Igmax_max_but, True)
		self.__filter_Igmax_max()

	#######upper filter switch
	def __filter_Igmax_max(self):
		if self.Igmax_max_but.isChecked():
			self.Igmax_max_selector.setEnabled(True)
			self.Igmax_max_selector.blockSignals(False)
			try:
				self.parent().wd.filter_Igmax_max = float(self.Igmax_max_selector.text())  # get value 
			except:
				self.__buttoncheck(self.Igmax_max_but, False)
			# is the input valid?
			if self.Igmax_max_but.isChecked() and self.parent().wd.filter_Igmax_max >= 0:
				if self.parent().wd.filter_Igmax_min != None:
					if self.parent().wd.filter_Igmax_max > self.parent().wd.filter_Igmax_min and self.parent().wd.filter_Igmax_max >= 0:
						self.__buttoncheck(self.Igmax_max_but, True)
					else:
						self.parent().wd.filter_Igmax_max = None
						self.__buttoncheck(self.Igmax_max_but, False)
						self.Igmax_max_selector_selector.setText("")
				else:
					self.__buttoncheck(self.Igmax_max_but, True)
			else:  # input not valid so leave unchecked and clear entry
				self.__buttoncheck(self.Igmax_max_but, False)
				self.parent().wd.filter_Igmax_max = None
				self.Igmax_max_selector.setText("")
		else:
			self.Igmax_max_selector.setEnabled(False)
			self.Igmax_max_selector.blockSignals(True)
			self.__buttoncheck(self.Igmax_max_but, False)
			self.parent().wd.filter_Igmax_max = None
		for devk in self.parent().wd.DCd:
			self.parent().wd.DCd[devk].Igmax_T()  # must read to properly update
			self.parent().wd.DCd[devk].Igmax_TF()
			self.parent().wd.DCd[devk].Igmax_TR()
		self.filterchanged=True
		#self.parent()._update()
##############################################
# done with |Igmax| Filter
###################################################################################################
# turns button on and off
	def __buttoncheck(self,but,CU):		# to check a button
		if CU:		# button is to be or is checked
			but.setChecked(True)
			but.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(100,200,255)}')
			#but.setStyleSheet('QPushButton {color:rgb(0,0,0)}')
			but.setText("On")
		else:		# button is to be or is unchecked
			but.setChecked(False)
			but.setStyleSheet('QPushButton {color:rgb(0,0,0);background-color:hsv(0,120,255)}')
			#but.setStyleSheet('QPushButton {color:rgb(0,0,0)}')
			but.setText("Off")
########################################################################################################################
# close event
	def closeEvent(self,e):
		print("from actions_filterdata.py  line 291 Actually close")	# debug
		self.Idmax_min_selector.blockSignals(True)
		self.Idmax_min_selector.blockSignals(True)
		self.IdmaxFOC_min_selector.blockSignals(True)
		self.IdmaxFOC_min_selector.blockSignals(True)
		self.onoffratio_min_selector.blockSignals(True)
		self.onoffratio_max_selector.blockSignals(True)
		self.gmmax_min_selector.blockSignals(True)
		self.gmmax_max_selector.blockSignals(True)
		self.filter_drain_compliance_but.blockSignals(True)
		self.filter_gate_compliance_but.blockSignals(True)

		self.parent().wd.filter_Idmax_min=None
		self.parent().wd.filter_Idmax_max=None
		self.parent().wd.filter_IdmaxFOC_min=None
		self.parent().wd.filter_IdmaxFOC_max=None
		self.parent().wd.filter_onoff_min=None
		self.parent().wd.filter_onoff_max=None
		self.parent().wd.filter_gmmax_min=None
		self.parent().wd.filter_gmmax_max=None
		self.parent().wd.filterdraincompliance=True
		self.parent().wd.filtergatecompliance=True
		self.parent().wd.filter_TLM_Rc_min=None
		self.parent().wd.filter_TLM_Rc_max=None
		self.parent().wd.filter_TLM_Rsh_min=None
		self.parent().wd.filter_TLM_Rsh_max=None
		self.parent().wd.filter_Ronmin_min=None
		self.parent().wd.filter_Ronmin_max=None
		self.parent().wd.filter_Igmax_min = None
		self.parent().wd.filter_Igmax_max = None
		self.parent()._update()
		e.accept()
################################################################
# mouse leaves filter widget so update then
	def leaveEvent(self, le):
		focused_widget=QtWidgets.QApplication.focusWidget()
		if focused_widget!=None: focused_widget.clearFocus()
		if self.filterchanged:                  # were any parameters changed in the filter?
			self.parent()._update()
			self.filterchanged=False
			#m.close()
		le.accept()
#################################################################