# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'waferdata_histogram.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Histogram(object):
    def setupUi(self, Histogram):
        Histogram.setObjectName("Histogram")
        Histogram.resize(763, 624)
        Histogram.setFocusPolicy(QtCore.Qt.TabFocus)
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(Histogram)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.wafernamelabel = QtWidgets.QLabel(Histogram)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wafernamelabel.sizePolicy().hasHeightForWidth())
        self.wafernamelabel.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.wafernamelabel.setFont(font)
        self.wafernamelabel.setObjectName("wafernamelabel")
        self.horizontalLayout_13.addWidget(self.wafernamelabel)
        self.wafername = QtWidgets.QLineEdit(Histogram)
        self.wafername.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.wafername.setFont(font)
        self.wafername.setAcceptDrops(False)
        self.wafername.setReadOnly(True)
        self.wafername.setObjectName("wafername")
        self.horizontalLayout_13.addWidget(self.wafername)
        self.verticalLayout_2.addLayout(self.horizontalLayout_13)
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.Vgs_label = QtWidgets.QLabel(Histogram)
        self.Vgs_label.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Vgs_label.setFont(font)
        self.Vgs_label.setObjectName("Vgs_label")
        self.horizontalLayout_12.addWidget(self.Vgs_label)
        self.Vgs_comboBox = QtWidgets.QComboBox(Histogram)
        self.Vgs_comboBox.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Vgs_comboBox.setFont(font)
        self.Vgs_comboBox.setObjectName("Vgs_comboBox")
        self.horizontalLayout_12.addWidget(self.Vgs_comboBox)
        self.Vds_FOC_label = QtWidgets.QLabel(Histogram)
        self.Vds_FOC_label.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Vds_FOC_label.setFont(font)
        self.Vds_FOC_label.setObjectName("Vds_FOC_label")
        self.horizontalLayout_12.addWidget(self.Vds_FOC_label)
        self.Vds_FOC = QtWidgets.QLineEdit(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Vds_FOC.setFont(font)
        self.Vds_FOC.setInputMethodHints(QtCore.Qt.ImhFormattedNumbersOnly)
        self.Vds_FOC.setReadOnly(False)
        self.Vds_FOC.setObjectName("Vds_FOC")
        self.horizontalLayout_12.addWidget(self.Vds_FOC)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_12.addItem(spacerItem)
        self.verticalLayout_2.addLayout(self.horizontalLayout_12)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.horizontalLayout_15 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.horizontalLayout_8.addLayout(self.horizontalLayout_15)
        self.Yf_checkBox = QtWidgets.QCheckBox(Histogram)
        self.Yf_checkBox.setObjectName("Yf_checkBox")
        self.horizontalLayout_8.addWidget(self.Yf_checkBox)
        self.deltaVgs_thres_label = QtWidgets.QLabel(Histogram)
        self.deltaVgs_thres_label.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.deltaVgs_thres_label.setFont(font)
        self.deltaVgs_thres_label.setObjectName("deltaVgs_thres_label")
        self.horizontalLayout_8.addWidget(self.deltaVgs_thres_label)
        self.delta_Vgs_thres = QtWidgets.QLineEdit(Histogram)
        self.delta_Vgs_thres.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.delta_Vgs_thres.setFont(font)
        self.delta_Vgs_thres.setToolTip("")
        self.delta_Vgs_thres.setInputMethodHints(QtCore.Qt.ImhFormattedNumbersOnly)
        self.delta_Vgs_thres.setReadOnly(False)
        self.delta_Vgs_thres.setObjectName("delta_Vgs_thres")
        self.horizontalLayout_8.addWidget(self.delta_Vgs_thres)
        self.Yf_Vgsfitrange_label = QtWidgets.QLabel(Histogram)
        self.Yf_Vgsfitrange_label.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Yf_Vgsfitrange_label.setFont(font)
        self.Yf_Vgsfitrange_label.setObjectName("Yf_Vgsfitrange_label")
        self.horizontalLayout_8.addWidget(self.Yf_Vgsfitrange_label)
        self.Yf_Vgsfitrange_frac = QtWidgets.QLineEdit(Histogram)
        self.Yf_Vgsfitrange_frac.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Yf_Vgsfitrange_frac.setFont(font)
        self.Yf_Vgsfitrange_frac.setToolTip("")
        self.Yf_Vgsfitrange_frac.setInputMethodHints(QtCore.Qt.ImhFormattedNumbersOnly)
        self.Yf_Vgsfitrange_frac.setReadOnly(False)
        self.Yf_Vgsfitrange_frac.setObjectName("Yf_Vgsfitrange_frac")
        self.horizontalLayout_8.addWidget(self.Yf_Vgsfitrange_frac)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_8.addItem(spacerItem1)
        self.verticalLayout_2.addLayout(self.horizontalLayout_8)
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.parameterlabel = QtWidgets.QLabel(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.parameterlabel.setFont(font)
        self.parameterlabel.setObjectName("parameterlabel")
        self.horizontalLayout_11.addWidget(self.parameterlabel)
        self.measurementtype = QtWidgets.QComboBox(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.measurementtype.setFont(font)
        self.measurementtype.setEditable(False)
        self.measurementtype.setObjectName("measurementtype")
        self.horizontalLayout_11.addWidget(self.measurementtype)
        self.verticalLayout_2.addLayout(self.horizontalLayout_11)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem2)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.set_includes_label = QtWidgets.QLabel(Histogram)
        self.set_includes_label.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.set_includes_label.setFont(font)
        self.set_includes_label.setAlignment(QtCore.Qt.AlignCenter)
        self.set_includes_label.setObjectName("set_includes_label")
        self.verticalLayout_4.addWidget(self.set_includes_label)
        self.set_includes = QtWidgets.QLineEdit(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.set_includes.setFont(font)
        self.set_includes.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.set_includes.setAcceptDrops(False)
        self.set_includes.setWhatsThis("")
        self.set_includes.setReadOnly(False)
        self.set_includes.setObjectName("set_includes")
        self.verticalLayout_4.addWidget(self.set_includes)
        self.verticalLayout_2.addLayout(self.verticalLayout_4)
        self.horizontalLayout_9.addLayout(self.verticalLayout_2)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.averagelabel = QtWidgets.QLabel(Histogram)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.averagelabel.sizePolicy().hasHeightForWidth())
        self.averagelabel.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.averagelabel.setFont(font)
        self.averagelabel.setObjectName("averagelabel")
        self.horizontalLayout_3.addWidget(self.averagelabel)
        self.average = QtWidgets.QLineEdit(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.average.setFont(font)
        self.average.setReadOnly(True)
        self.average.setObjectName("average")
        self.horizontalLayout_3.addWidget(self.average)
        self.standarddeviation = QtWidgets.QLabel(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.standarddeviation.setFont(font)
        self.standarddeviation.setObjectName("standarddeviation")
        self.horizontalLayout_3.addWidget(self.standarddeviation)
        self.standard_deviation = QtWidgets.QLineEdit(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.standard_deviation.setFont(font)
        self.standard_deviation.setReadOnly(True)
        self.standard_deviation.setObjectName("standard_deviation")
        self.horizontalLayout_3.addWidget(self.standard_deviation)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.log_linear_histogram_but = QtWidgets.QPushButton(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.log_linear_histogram_but.setFont(font)
        self.log_linear_histogram_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.log_linear_histogram_but.setStyleSheet("background-color: hsv(100, 200, 255);\n"
"color: rgb(0, 0,0);")
        self.log_linear_histogram_but.setCheckable(True)
        self.log_linear_histogram_but.setChecked(False)
        self.log_linear_histogram_but.setAutoDefault(False)
        self.log_linear_histogram_but.setObjectName("log_linear_histogram_but")
        self.horizontalLayout_4.addWidget(self.log_linear_histogram_but)
        self.label_numberofdevices = QtWidgets.QLabel(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_numberofdevices.setFont(font)
        self.label_numberofdevices.setObjectName("label_numberofdevices")
        self.horizontalLayout_4.addWidget(self.label_numberofdevices)
        self.numberofdevices = QtWidgets.QLineEdit(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.numberofdevices.setFont(font)
        self.numberofdevices.setReadOnly(True)
        self.numberofdevices.setObjectName("numberofdevices")
        self.horizontalLayout_4.addWidget(self.numberofdevices)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.selectmintype = QtWidgets.QComboBox(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.selectmintype.setFont(font)
        self.selectmintype.setObjectName("selectmintype")
        self.selectmintype.addItem("")
        self.selectmintype.addItem("")
        self.horizontalLayout_5.addWidget(self.selectmintype)
        self.minimum = QtWidgets.QLineEdit(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.minimum.setFont(font)
        self.minimum.setObjectName("minimum")
        self.horizontalLayout_5.addWidget(self.minimum)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.selectmaxtype = QtWidgets.QComboBox(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.selectmaxtype.setFont(font)
        self.selectmaxtype.setObjectName("selectmaxtype")
        self.selectmaxtype.addItem("")
        self.selectmaxtype.addItem("")
        self.horizontalLayout_6.addWidget(self.selectmaxtype)
        self.maximum = QtWidgets.QLineEdit(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.maximum.setFont(font)
        self.maximum.setObjectName("maximum")
        self.horizontalLayout_6.addWidget(self.maximum)
        self.verticalLayout.addLayout(self.horizontalLayout_6)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.range_lin_fit_label = QtWidgets.QLabel(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.range_lin_fit_label.setFont(font)
        self.range_lin_fit_label.setObjectName("range_lin_fit_label")
        self.horizontalLayout_7.addWidget(self.range_lin_fit_label)
        self.range_linearfit = QtWidgets.QLineEdit(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.range_linearfit.setFont(font)
        self.range_linearfit.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.range_linearfit.setAcceptDrops(True)
        self.range_linearfit.setObjectName("range_linearfit")
        self.horizontalLayout_7.addWidget(self.range_linearfit)
        self.transfer_curve_smoothing_factor_label = QtWidgets.QLabel(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.transfer_curve_smoothing_factor_label.setFont(font)
        self.transfer_curve_smoothing_factor_label.setObjectName("transfer_curve_smoothing_factor_label")
        self.horizontalLayout_7.addWidget(self.transfer_curve_smoothing_factor_label)
        self.transfer_curve_smoothing_factor = QtWidgets.QLineEdit(Histogram)
        self.transfer_curve_smoothing_factor.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.transfer_curve_smoothing_factor.setFont(font)
        self.transfer_curve_smoothing_factor.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.transfer_curve_smoothing_factor.setAcceptDrops(True)
        self.transfer_curve_smoothing_factor.setObjectName("transfer_curve_smoothing_factor")
        self.horizontalLayout_7.addWidget(self.transfer_curve_smoothing_factor)
        self.verticalLayout.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_16 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_16.setObjectName("horizontalLayout_16")
        self.TLM_lin_fit_label = QtWidgets.QLabel(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.TLM_lin_fit_label.setFont(font)
        self.TLM_lin_fit_label.setObjectName("TLM_lin_fit_label")
        self.horizontalLayout_16.addWidget(self.TLM_lin_fit_label)
        self.TLM_fit_quality = QtWidgets.QLineEdit(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.TLM_fit_quality.setFont(font)
        self.TLM_fit_quality.setAcceptDrops(True)
        self.TLM_fit_quality.setObjectName("TLM_fit_quality")
        self.horizontalLayout_16.addWidget(self.TLM_fit_quality)
        self.minTLMlength_label = QtWidgets.QLabel(Histogram)
        self.minTLMlength_label.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.minTLMlength_label.setFont(font)
        self.minTLMlength_label.setObjectName("minTLMlength_label")
        self.horizontalLayout_16.addWidget(self.minTLMlength_label)
        self.TLMlengthminimum = QtWidgets.QComboBox(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.TLMlengthminimum.setFont(font)
        self.TLMlengthminimum.setEditable(False)
        self.TLMlengthminimum.setObjectName("TLMlengthminimum")
        self.horizontalLayout_16.addWidget(self.TLMlengthminimum)
        self.maxTLMlength_label = QtWidgets.QLabel(Histogram)
        self.maxTLMlength_label.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.maxTLMlength_label.setFont(font)
        self.maxTLMlength_label.setObjectName("maxTLMlength_label")
        self.horizontalLayout_16.addWidget(self.maxTLMlength_label)
        self.TLMlengthmaximum = QtWidgets.QComboBox(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.TLMlengthmaximum.setFont(font)
        self.TLMlengthmaximum.setEditable(False)
        self.TLMlengthmaximum.setObjectName("TLMlengthmaximum")
        self.horizontalLayout_16.addWidget(self.TLMlengthmaximum)
        self.verticalLayout.addLayout(self.horizontalLayout_16)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.binsizepolicy_label = QtWidgets.QLabel(Histogram)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.binsizepolicy_label.sizePolicy().hasHeightForWidth())
        self.binsizepolicy_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.binsizepolicy_label.setFont(font)
        self.binsizepolicy_label.setObjectName("binsizepolicy_label")
        self.horizontalLayout_2.addWidget(self.binsizepolicy_label)
        self.binsizepolicy = QtWidgets.QComboBox(Histogram)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.binsizepolicy.sizePolicy().hasHeightForWidth())
        self.binsizepolicy.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.binsizepolicy.setFont(font)
        self.binsizepolicy.setObjectName("binsizepolicy")
        self.horizontalLayout_2.addWidget(self.binsizepolicy)
        self.label_binsize = QtWidgets.QLabel(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_binsize.setFont(font)
        self.label_binsize.setObjectName("label_binsize")
        self.horizontalLayout_2.addWidget(self.label_binsize)
        self.binsize_stddev = QtWidgets.QLineEdit(Histogram)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.binsize_stddev.setFont(font)
        self.binsize_stddev.setObjectName("binsize_stddev")
        self.horizontalLayout_2.addWidget(self.binsize_stddev)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_9.addLayout(self.verticalLayout)
        self.verticalLayout_5.addLayout(self.horizontalLayout_9)
        self.plotframe = QtWidgets.QFrame(Histogram)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plotframe.sizePolicy().hasHeightForWidth())
        self.plotframe.setSizePolicy(sizePolicy)
        self.plotframe.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.plotframe.setFrameShadow(QtWidgets.QFrame.Raised)
        self.plotframe.setObjectName("plotframe")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.plotframe)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.opendirbut = QtWidgets.QPushButton(self.plotframe)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.opendirbut.setFont(font)
        self.opendirbut.setFocusPolicy(QtCore.Qt.TabFocus)
        self.opendirbut.setAutoDefault(False)
        self.opendirbut.setObjectName("opendirbut")
        self.horizontalLayout.addWidget(self.opendirbut)
        self.save_state_but = QtWidgets.QPushButton(self.plotframe)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.save_state_but.setFont(font)
        self.save_state_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.save_state_but.setObjectName("save_state_but")
        self.horizontalLayout.addWidget(self.save_state_but)
        self.pack_database_but = QtWidgets.QPushButton(self.plotframe)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.pack_database_but.setFont(font)
        self.pack_database_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.pack_database_but.setObjectName("pack_database_but")
        self.horizontalLayout.addWidget(self.pack_database_but)
        self.open_filter_but = QtWidgets.QPushButton(self.plotframe)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.open_filter_but.setFont(font)
        self.open_filter_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.open_filter_but.setObjectName("open_filter_but")
        self.horizontalLayout.addWidget(self.open_filter_but)
        self.export_but = QtWidgets.QPushButton(self.plotframe)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.export_but.setFont(font)
        self.export_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.export_but.setObjectName("export_but")
        self.horizontalLayout.addWidget(self.export_but)
        self.device_list_but = QtWidgets.QPushButton(self.plotframe)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.device_list_but.setFont(font)
        self.device_list_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.device_list_but.setObjectName("device_list_but")
        self.horizontalLayout.addWidget(self.device_list_but)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.Device_Listing_Table = DevTable(self.plotframe)
        self.Device_Listing_Table.setMaximumSize(QtCore.QSize(16777215, 200))
        self.Device_Listing_Table.setStatusTip("")
        self.Device_Listing_Table.setWhatsThis("")
        self.Device_Listing_Table.setObjectName("Device_Listing_Table")
        self.Device_Listing_Table.setColumnCount(0)
        self.Device_Listing_Table.setRowCount(0)
        self.Device_Listing_Table.horizontalHeader().setCascadingSectionResizes(True)
        self.Device_Listing_Table.horizontalHeader().setStretchLastSection(True)
        self.Device_Listing_Table.verticalHeader().setCascadingSectionResizes(True)
        self.verticalLayout_3.addWidget(self.Device_Listing_Table)
        self.chartcontrolHBOX = QtWidgets.QHBoxLayout()
        self.chartcontrolHBOX.setObjectName("chartcontrolHBOX")
        self.backview_but = QtWidgets.QPushButton(self.plotframe)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.backview_but.setFont(font)
        self.backview_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.backview_but.setObjectName("backview_but")
        self.chartcontrolHBOX.addWidget(self.backview_but)
        self.forwardview_but = QtWidgets.QPushButton(self.plotframe)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.forwardview_but.setFont(font)
        self.forwardview_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.forwardview_but.setObjectName("forwardview_but")
        self.chartcontrolHBOX.addWidget(self.forwardview_but)
        self.fullview_but = QtWidgets.QPushButton(self.plotframe)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.fullview_but.setFont(font)
        self.fullview_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.fullview_but.setObjectName("fullview_but")
        self.chartcontrolHBOX.addWidget(self.fullview_but)
        self.selected_bin_only_but = QtWidgets.QPushButton(self.plotframe)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.selected_bin_only_but.setFont(font)
        self.selected_bin_only_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.selected_bin_only_but.setCheckable(True)
        self.selected_bin_only_but.setObjectName("selected_bin_only_but")
        self.chartcontrolHBOX.addWidget(self.selected_bin_only_but)
        self.histograph_image_to_clipboard_but = QtWidgets.QPushButton(self.plotframe)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.histograph_image_to_clipboard_but.setFont(font)
        self.histograph_image_to_clipboard_but.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.histograph_image_to_clipboard_but.setObjectName("histograph_image_to_clipboard_but")
        self.chartcontrolHBOX.addWidget(self.histograph_image_to_clipboard_but)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.chartcontrolHBOX.addItem(spacerItem3)
        self.quit_but = QtWidgets.QPushButton(self.plotframe)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.quit_but.setFont(font)
        self.quit_but.setFocusPolicy(QtCore.Qt.NoFocus)
        self.quit_but.setObjectName("quit_but")
        self.chartcontrolHBOX.addWidget(self.quit_but)
        self.verticalLayout_3.addLayout(self.chartcontrolHBOX)
        self.plotframebox = QtWidgets.QHBoxLayout()
        self.plotframebox.setObjectName("plotframebox")
        self.verticalLayout_3.addLayout(self.plotframebox)
        self.verticalLayout_5.addWidget(self.plotframe)
        self.plotframe.raise_()

        self.retranslateUi(Histogram)
        QtCore.QMetaObject.connectSlotsByName(Histogram)

    def retranslateUi(self, Histogram):
        _translate = QtCore.QCoreApplication.translate
        Histogram.setWindowTitle(_translate("Histogram", "Histogram"))
        self.wafernamelabel.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">This is the name of the wafer and directory currently under analysis.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">The directory name MUST match the wafer name.</p></body></html>"))
        self.wafernamelabel.setText(_translate("Histogram", "Wafer Name"))
        self.wafername.setToolTip(_translate("Histogram", "Wafer Name"))
        self.Vgs_label.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Selected Vgs:</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">This selects the Vgs for all analysis which requires the family of curves data</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">examples of which are Ron, Gon, TLM data, ratio Ron data etc...</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Analysis will be performed assuming the selected Vgs which selects a curve from the</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">family of curves. Changing this will update all data dependent upon Vgs.</p></body></html>"))
        self.Vgs_label.setText(_translate("Histogram", "select Vgs for FOC"))
        self.Vgs_comboBox.setToolTip(_translate("Histogram", "Gate voltage setting"))
        self.Vgs_comboBox.setWhatsThis(_translate("Histogram", "This is the gate voltage setting"))
        self.Vds_FOC_label.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Selected Vgs:</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">This selects the Vgs for all analysis which requires the family of curves data</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">examples of which are Ron, Gon, TLM data, ratio Ron data etc...</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Analysis will be performed assuming the selected Vgs which selects a curve from the</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">family of curves. Changing this will update all data dependent upon Vgs.</p></body></html>"))
        self.Vds_FOC_label.setText(_translate("Histogram", "Vds_FOC for |Idmax|@Vds"))
        self.Yf_checkBox.setText(_translate("Histogram", " Y-function Analysis"))
        self.deltaVgs_thres_label.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Selected Vgs:</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">This selects the Vgs for all analysis which requires the family of curves data</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">examples of which are Ron, Gon, TLM data, ratio Ron data etc...</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Analysis will be performed assuming the selected Vgs which selects a curve from the</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">family of curves. Changing this will update all data dependent upon Vgs.</p></body></html>"))
        self.deltaVgs_thres_label.setText(_translate("Histogram", "deltaVgsthres"))
        self.delta_Vgs_thres.setText(_translate("Histogram", "-0.5"))
        self.Yf_Vgsfitrange_label.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Selected Vgs:</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">This selects the Vgs for all analysis which requires the family of curves data</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">examples of which are Ron, Gon, TLM data, ratio Ron data etc...</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Analysis will be performed assuming the selected Vgs which selects a curve from the</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">family of curves. Changing this will update all data dependent upon Vgs.</p></body></html>"))
        self.Yf_Vgsfitrange_label.setText(_translate("Histogram", "Yf Vgs  fit range fract"))
        self.Yf_Vgsfitrange_frac.setText(_translate("Histogram", "0.1"))
        self.parameterlabel.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Parameter selector:</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Selects parameter to be displayed on histogram.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">If you get the warning message &quot;no devices&quot;</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">then try to adjust the parameter selector to find a </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">parameter for which there are data. The parameter </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">selector MUST be set to data that exists for any analysis</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">to proceed.</p></body></html>"))
        self.parameterlabel.setText(_translate("Histogram", "Parameter"))
        self.measurementtype.setToolTip(_translate("Histogram", "Data Format: Resistance (Ron) or Conductance (Gon)"))
        self.measurementtype.setWhatsThis(_translate("Histogram", "Ron @ Vds=0V is the slope of Ids/Vds at Vds=0V\n"
"Ron @ |Vds|=maximum is the maximum Vds/Id at maximum Vds\n"
"Gon s are similar to the above but are conductances = 1/Ron"))
        self.set_includes_label.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\"><span style=\" color:#000000;\">Boolean selector:</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Selects devices for analysis based on their names</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Default is to analyze all devices.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">This is a reverse Polish Boolean evaluator</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Operators (binary-two arguments): and, or, xor - call them bx</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Operators (unary-one argument): not - call it ux</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Format for search terms (strings) with operators bx, ux is:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">A B ba C ua bb D bc .......</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">where ba operates on A and B, ua operates on C, bb operates on the two results of</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">of ba and ua and bc this result and D. Example:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Aa Bla and Cz not and D or is equivalent to:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">((Aa and Bla) and not Cz) and D</span></p></body></html>"))
        self.set_includes_label.setText(_translate("Histogram", "data filename filter"))
        self.set_includes.setToolTip(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Boolean selector:</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Selects devices for analysis based on their names</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Default is to analyze all devices.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">This is a reverse Polish Boolean evaluator</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Operators (binary-two arguments): and, or, xor - call them bo</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Operators (unary-one argument): not - call it ux</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Format for search terms (strings) with operators bx, ux is:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">A B ba C ua bb D bc .......</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">where ba operates on A and B, ua operates on C, bb operates on the two results of</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">of ba and ua and bc this result and D. Example:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Aa Bla and Cz not and D or is equivalent to:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">((Aa and Bla) and not Cz) and D</span></p></body></html>"))
        self.averagelabel.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Average of all data visible within the hysteresis plot.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">When Linear plots button is green and selected, this is the arithmetic mean of the data.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">When log plots (button turns red) is selected, this is the geometric (log average) mean.</p></body></html>"))
        self.averagelabel.setText(_translate("Histogram", "average"))
        self.standarddeviation.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Standard Deviation of all data visible within the hysteresis plot.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">When Linear plots button is green and selected, this is the simple standard deviation of the data.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">When log plots (button turns red) is selected, this is the standard deviation of the log of the data.</p></body></html>"))
        self.standarddeviation.setText(_translate("Histogram", "standard deviation"))
        self.standard_deviation.setToolTip(_translate("Histogram", "Of selected range"))
        self.log_linear_histogram_but.setText(_translate("Histogram", "Linear plots"))
        self.label_numberofdevices.setText(_translate("Histogram", "number of devices"))
        self.selectmintype.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Lower limit of data analysis on the histogram displayed as number of standard deviations below mean or a simple value.</p></body></html>"))
        self.selectmintype.setItemText(0, _translate("Histogram", "Std Dev below mean"))
        self.selectmintype.setItemText(1, _translate("Histogram", "Value"))
        self.selectmaxtype.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Upper limit of data analysis on the histogram displayed as number of standard deviations below mean or a simple value.</p></body></html>"))
        self.selectmaxtype.setItemText(0, _translate("Histogram", "Std Dev above mean"))
        self.selectmaxtype.setItemText(1, _translate("Histogram", "Value"))
        self.range_lin_fit_label.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Range of Vds over which an Id vs Vds curve is fit to a line to determine Ron, Gon.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">The Id(Vds) curve is that at a Vgs selected by the user on the Vgs selector of this GUI window.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">This curve fit range starts at Vds=0 and extends to maximum negative Vds * the range fit.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.range_lin_fit_label.setText(_translate("Histogram", "FOC Ron Range Fit"))
        self.transfer_curve_smoothing_factor_label.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Range of Vds over which an Id vs Vds curve is fit to a line to determine Ron, Gon.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">The Id(Vds) curve is that at a Vgs selected by the user on the Vgs selector of this GUI window.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">This curve fit range starts at Vds=0 and extends to maximum negative Vds * the range fit.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.transfer_curve_smoothing_factor_label.setText(_translate("Histogram", "transfer curve smoothing factor"))
        self.TLM_lin_fit_label.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Range of Vds over which an Id vs Vds curve is fit to a line to determine Ron, Gon.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">The Id(Vds) curve is that at a Vgs selected by the user on the Vgs selector of this GUI window.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">This curve fit range starts at Vds=0 and extends to maximum negative Vds * the range fit.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.TLM_lin_fit_label.setText(_translate("Histogram", "TLM linear fit quality"))
        self.minTLMlength_label.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\"><span style=\" color:#000000;\">Minimum channel length of TLM devices.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\"><span style=\" color:#000000;\">Allows user to select the minimum available channel length of devices in the TLM</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\"><span style=\" color:#000000;\">structures to use in performing TLM analysis of Rc and Rsh (contact and sheet resistance)</span></p></body></html>"))
        self.minTLMlength_label.setText(_translate("Histogram", "TLM min length um"))
        self.TLMlengthminimum.setToolTip(_translate("Histogram", "Data Format: Resistance (Ron) or Conductance (Gon)"))
        self.TLMlengthminimum.setWhatsThis(_translate("Histogram", "Ron @ Vds=0V is the slope of Ids/Vds at Vds=0V\n"
"Ron @ |Vds|=maximum is the maximum Vds/Id at maximum Vds\n"
"Gon s are similar to the above but are conductances = 1/Ron"))
        self.maxTLMlength_label.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Maximum channel length of TLM devices.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Allows user to select the maximum available channel length of devices in the TLM</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">structures to use in performing TLM analysis of Rc and Rsh (contact and sheet resistance)</span></p></body></html>"))
        self.maxTLMlength_label.setText(_translate("Histogram", "TLM max length um"))
        self.TLMlengthmaximum.setToolTip(_translate("Histogram", "Data Format: Resistance (Ron) or Conductance (Gon)"))
        self.TLMlengthmaximum.setWhatsThis(_translate("Histogram", "Ron @ Vds=0V is the slope of Ids/Vds at Vds=0V\n"
"Ron @ |Vds|=maximum is the maximum Vds/Id at maximum Vds\n"
"Gon s are similar to the above but are conductances = 1/Ron"))
        self.binsizepolicy_label.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">User-selection of the method by which histogram bin size is determined</p></body></html>"))
        self.binsizepolicy_label.setText(_translate("Histogram", "Bin Size Policy"))
        self.label_binsize.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">User manual setting for histogram bin size.</p></body></html>"))
        self.label_binsize.setText(_translate("Histogram", "bin size stddev"))
        self.opendirbut.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">User to select wafer directory to open and analyze.</span></p></body></html>"))
        self.opendirbut.setText(_translate("Histogram", "&open directory"))
        self.save_state_but.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">User saves data to open later</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Should reduce loading time of analysis.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">WARNING: Not working yet!</span></p></body></html>"))
        self.save_state_but.setText(_translate("Histogram", "&Save State"))
        self.pack_database_but.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">User saves data to open later</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Should reduce loading time of analysis.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">WARNING: Not working yet!</span></p></body></html>"))
        self.pack_database_but.setText(_translate("Histogram", "Pack Database"))
        self.open_filter_but.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">This opens a new window which allows the user to filter data for analysis by</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">data values. For example, the user can exclude devices having |Idmax| less than or </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">greater than the user-specified values. This is often used to remove bad devices from the analysis.</span></p></body></html>"))
        self.open_filter_but.setText(_translate("Histogram", "filter"))
        self.export_but.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">This opens a new window which allows the user to obtain TLM device Ron and other parameters from statistical averaged data for each TLM element.</span></p></body></html>"))
        self.export_but.setText(_translate("Histogram", "Export statistics"))
        self.device_list_but.setWhatsThis(_translate("Histogram", "<html><head/><body><p><span style=\" color:#000000;\">This opens a new window which allows the user to obtain a device listing of device names on the wafer with the devices\' measured/calculated parameters in columns.</span></p></body></html>"))
        self.device_list_but.setText(_translate("Histogram", "device list"))
        self.Device_Listing_Table.setToolTip(_translate("Histogram", "<html><head/><body><p><span style=\" color:#000000; background-color:#ffffff;\">Device listing from selected bin of the histogram. Note that a ctrl-f opens a window which allows the user to place a Boolean expression to selectively display devices.</span></p><p><span style=\" color:#000000; background-color:#ffffff;\">Left mouse click on parameter (header) to sort. </span></p><p><span style=\" color:#000000; background-color:#ffffff;\">Shift+left mouse click on parameter to select it for copy to clipboard - the selected columns will change color. </span></p><p><span style=\" color:#000000; background-color:#ffffff;\">After selecting all desired parameters, cntl-c to copy them to clipboard. </span></p><p><span style=\" color:#000000; background-color:#ffffff;\">Right mouse click deselects all. </span></p><p><span style=\" color:#000000; background-color:#ffffff;\">Shift right click to load individual cells to clipboard. </span></p><p><span style=\" color:#000000; background-color:#ffffff;\">Left mouse click on device name will allow plotting of selected device parameters.</span></p></body></html>"))
        self.backview_but.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Send the histogram view back to the previous setting.</p></body></html>"))
        self.backview_but.setText(_translate("Histogram", "&back"))
        self.forwardview_but.setWhatsThis(_translate("Histogram", "<html><head/><body><p><span style=\" color:#000000;\">Send the histogram view forward to the next saved setting.</span></p></body></html>"))
        self.forwardview_but.setText(_translate("Histogram", "&forward"))
        self.fullview_but.setWhatsThis(_translate("Histogram", "<html><head/><body><p><span style=\" color:#000000;\">Send the histogram to full span to view all available data i.e. this is the default setting.</span></p></body></html>"))
        self.fullview_but.setText(_translate("Histogram", "&full view"))
        self.selected_bin_only_but.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Send the histogram view back to the previous setting.</p></body></html>"))
        self.selected_bin_only_but.setText(_translate("Histogram", "selected bin only"))
        self.histograph_image_to_clipboard_but.setWhatsThis(_translate("Histogram", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#000000;\">Send the histogram view back to the previous setting.</p></body></html>"))
        self.histograph_image_to_clipboard_but.setText(_translate("Histogram", "histograph image->&clipboard"))
        self.quit_but.setText(_translate("Histogram", "Quit"))

from devtable import DevTable
