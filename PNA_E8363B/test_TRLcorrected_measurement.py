# TRL calibration
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import visa
rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

#from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from pna import Pna
#import skrf as rf
from skrf.calibration import TRL
#%matplotlib inline
#from skrf.plotting import stylely
#stylely()

#
caldir="C:/Users/test/pna_calibration_data"
# load switch terms data files
# try:
# 	switch_terms = (rf.Network(caldir+'/forward_switchterm_SRI.s1p'),
#                 rf.Network(caldir+'/reverse_switchterm_SRI.s1p'))
# except:
# 	raise ValueError("ERROR! could not load one or both switch term files")
# # now measure TRL standards and save files
# trlopenfilename="TRLopens_SRI.s2p"
# trlthrufilename="TRLthru_SRI.s2p"
# trllinefilename="TRLline_SRI.s2p"
#devicename="27pS_port1open"
devicename="opens"
app=QtWidgets.QApplication(sys.argv)
pna = Pna(rm,1)         # setup PNA
message=QtWidgets.QMessageBox()
message.setText("Probe DUT")
message.exec_()
pna.pna_getS_2port(instrumentstate="2port_HF_TRL.sta",navg=8)       # get uncorrected opens S-parameter data (because no calset file was specified)
pna.writefile_spar(measurement_type="all_RI",pathname=caldir,devicename=devicename,wafername="uncorrected",xloc=0,yloc=0,Vds=0,Vgs=0,Id=0,Ig=0,devicenamemodifier="")
pna.writefile_spar(measurement_type="all_db",pathname=caldir,devicename=devicename,wafername="uncorrected",xloc=0,yloc=0,Vds=0,Vgs=0,Id=0,Ig=0,devicenamemodifier="")
# T=rf.Network(caldir+"/"+trlthrufilename)
# R=rf.Network(caldir+"/"+trlopenfilename)
# L=rf.Network(caldir+"/"+trllinefilename)
# measured=[T,R,L]
# trl=TRL(measured = measured,switch_terms = switch_terms)
# dut_raw = rf.Network('trl_data/mismatched line.s2p')
# dut_corrected = trl.apply_cal(dut_raw)
# dut_corrected.plot_s_db()
