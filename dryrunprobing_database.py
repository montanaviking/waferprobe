# main wafer probing routine
import visa
from utilities import formatnum
from create_probeconstellations_devices.probe_constellations_map import *

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())


from cascade import CascadeProbeStation                                                    # Cascade wafer prober

pathname = "C:/Users/test/python/data/L6meas3"
wafername="L3"
runnumber=1
wafername_runno=wafername+"meas"+str(runnumber)
cascade = CascadeProbeStation(rm=rm,dryrun=True)         # setup Cascade NO probeplan file here! This also moves
probc=ConstellationsdB(maskname="TLMORTH2finger",wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
probeconstellations=probc.get_probing_constellations(probe_device_list="W40-TLM",probe_device_andlist="4um")
firsttime=True
totalnumbercleans=0
for pconst in probeconstellations:
	print("from line 60 in dryrunprobing_database.py ", pconst["name"])
	cascade.move_XY_nocontact(X=pconst["X"], Y=pconst["Y"])
	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
	devicenames=[device[0]["name"],device[1]["name"]]

	print ("probing devices ",devicenames[0]," ",devicenames[1], " x0, y0 = ", device[0]["X"]," ",device[0]["Y"] ," x1, y1 = ",device[1]["X"]," ",device[1]["Y"])


cascade.move_separate()
# #del cascade
print("done probing wafer")