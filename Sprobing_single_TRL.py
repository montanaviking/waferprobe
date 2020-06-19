# this probes one device by measuring uncorrected data and correcting the data outside the PNA
#import pylab as pl
import visa
#from utilities import formatnum
import time
from skrf.calibration import TRL
from skrf.calibration import MultilineTRL

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

#from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from pna import Pna                                                                 # network analyzer
#from old.plotSmeas import dataPlotter
from device_parameter_request import DeviceParameters

pna = Pna(rm,1)                                                                    # setup network analyzer


pathname_pna_cal="C:/Users/test/python/data/pnadata"

#pathname="C:/Users/test/focus_setups/power/July12_2019/"
#pathname="C:/Users/test/python/data/QH4meas11/"
#wafername="QH4meas11"
X=0
Y=0

Vgs_bias=0
Vds_bias=0
runno="meas1"
wafername="WF211_manual"

wafername=wafername+runno

# get switch terms
pna.getswitchtermsPNA(instrumentstatefilename="swfHF.sta",average=32)

pna.writefile_swfactors(pathname=pathname_pna_cal,filenamemod="7pSTRL")
print("done")