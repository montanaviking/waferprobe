# TRL measure standards
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import visa
rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

#from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from pna import Pna
#import skrf as rf
#from skrf.calibration import TRL
#%matplotlib inline

caldir="C:/Users/test/pna_calibration_data"


# now measure TRL standards and save files
trlopenfilename="TRLopens"
trlthrufilename="TRLthru"
trllinefilename="TRLline"
app=QtWidgets.QApplication(sys.argv)
pna = Pna(rm,1)         # setup PNA
message=QtWidgets.QMessageBox()
message.setText("Raise probes and measure TRL opens")
message.exec_()
pna.pna_getS_2port(instrumentstate="2port_HF_TRL.sta",navg=4)       # get uncorrected opens S-parameter data (because no calset file was specified)
pna.writefile_spar(measurement_type="all_RI",pathname=caldir,devicename=trlopenfilename,wafername="",xloc=0,yloc=0,Vds=0,Vgs=0,Id=0,Ig=0,devicenamemodifier="")
message.setText("probe TRL thru")
message.exec_()
pna.pna_getS_2port(instrumentstate="2port_HF_TRL.sta",navg=4)       # get uncorrected opens S-parameter data (because no calset file was specified)
pna.writefile_spar(measurement_type="all_RI",pathname=caldir,devicename=trlthrufilename,wafername="",xloc=0,yloc=0,Vds=0,Vgs=0,Id=0,Ig=0,devicenamemodifier="")
message.setText("probe TRL 7pS line")
message.exec_()
pna.pna_getS_2port(instrumentstate="2port_HF_TRL.sta",navg=4)       # get uncorrected opens S-parameter data (because no calset file was specified)
pna.writefile_spar(measurement_type="all_RI",pathname=caldir,devicename=trllinefilename,wafername="",xloc=0,yloc=0,Vds=0,Vgs=0,Id=0,Ig=0,devicenamemodifier="")