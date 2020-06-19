# main wafer probing routine
import visa
from utilities import formatnum
from create_probeconstellations_devices.probe_constellations_map import *
import time

rm = visa.ResourceManager()                                                         # setup GPIB communications
print (rm.list_resources())

from parameter_analyzer import ParameterAnalyzer                                    # IV and bias
from cascade import CascadeProbeStation                                                    # Cascade wafer prober

iv = ParameterAnalyzer(rm)                                                          # setup IV and bias
maxallowedproberesistance=8
maxallowedproberesistancedifference=4.

# set up of IV and bias voltages
# family of curves
# Vgs_focstart = -30
# Vgs_focstop = -30
# Vgs_focnpts = 1

# Vds_focstart = 0.
# Vds_focstop = -1.
# Vds_focnpts =21

Vgs_trans_start_ss=0.
Vgs_trans_stop_ss=-30.
Vgs_trans_step_ss=-0.5


# common to both
#gatecomp = 5E-5                                                                   # gate current compliance in A
gatecomp = 50E-6                                                                   # gate current compliance in A
#gatecomp = 0.01
draincomp = 0.1                                                                   # drain current compliance in A
draincompmApermm=150.                                        # drain compliance in mA/mm used for loop hysteresis transfer curves and anything else which isn't autoranged
draincompmApermmlow=15.                                        # drain compliance in mA/mm used for loop hysteresis transfer curves and anything else which isn't autoranged
#draincomplow = 0.001                                                                   # drain current compliance in A - this is for the low Vds test. Compliance is reduced to allow accurate Id measurement at low Vds and low expected currents

#Vgs_bias = -10.                                                                      # gate bias for S-parameters
#validation to see if device warrents further testing
#goodId=100.E-9                        # drain current must exceed this to qualify device for further testing
#goodIg=50.E-6                          # gate current must be LESS than this amount to qualify device for further testing
#goodIg=50E-6                          # gate current must be LESS than this amount to qualify device for further testing
Vgs_validation = -20.
Vds0_validation = -1.
Vds1_validation = -1.

wafername="L41"
runnumber=8

wafername_runno=wafername+"meas"+str(runnumber)
pathname = "C:/Users/test/python/data/"+wafername_runno
cascade = CascadeProbeStation(rm=rm)         # setup Cascade NO probeplan file here! This also moves
probc=ConstellationsdB(maskname="v6_2finger_dual_backtrim",wafer_name=wafername,run_number=runnumber)   # set up probe constellations from database
#probeconstellations=probc.get_probing_constellations(devicesubstringnamelogic='or', devicesubstringnames=['T50_D12','T50_D13','T100_D13','SHORT1'],startprobenumber=0,stopprobenumber=100000)
probeconstellations=probc.get_probing_constellations(devicesubstringnamelogic='or', devicesubstringnames=['R4','R7'],startprobenumber=237,stopprobenumber=100000)
firsttime=True
totalnumbercleans=0
for pconst in probeconstellations:
	if totalnumbercleans>50:
		print("Total number of cleaning cycles >50 so we have poor contacts quitting!")
		quit()
	print("from line 63 in IVprobingdualTLM_database.py device name, test order", pconst["name"], pconst["testorder"])
	cascade.move_XY(X=pconst["X"], Y=pconst["Y"])                       # move to DUT to probe
	device=probc.get_probing_devices(constellation_name=pconst["name"])    # get names list of all devices in this probe constellation
	devicenames=[device[0]["name"],device[1]["name"]]
	if "SHORT1" in pconst["name"] or "SHORT1" in devicenames[0]:         # then these are a probe resistance test device
		Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=0.1, Vds1=0.1, gatecomp=gatecomp, draincomp0=0.05, draincomp1=0.05)
		iv.fetbiasoff()
		proberesistance0=0.1/Id0val
		proberesistance1=0.1/Id1val
		print("testing probe resistance0 =",formatnum(proberesistance0,precision=2))
		print("testing probe resistance1 =",formatnum(proberesistance1,precision=2))
		cleaniter=0
		while (proberesistance0>maxallowedproberesistance or proberesistance1>maxallowedproberesistance or abs(proberesistance1-proberesistance0)>maxallowedproberesistancedifference) and cleaniter<3:
		#while proberesistance1>maxallowedproberesistance  and cleaniter<3:
			if cleaniter==0: totalnumbercleans+=1               # keep track of total number of cleaning cycles
			res0before=proberesistance0
			res1before=proberesistance1
			cascade.cleanprobe(auxstagenumber=12, number_cleaning_contacts=2)          # clean on sticky probe cleaner first then dry abrasive probe cleaner pad 2nd
			Id0val,Id1val,Igval,Id0compstatval,Id1compstatval,Igcompstatval=iv.fetbiason_dual_backgate(Vgs=Vgs_validation, Vds0=0.1, Vds1=0.1, gatecomp=gatecomp, draincomp0=0.05, draincomp1=0.05)
			iv.fetbiasoff()
			proberesistance0=0.1/Id0val
			proberesistance1=0.1/Id1val
			print("cleaning loop probe resistance0 =",formatnum(proberesistance0,precision=2))
			print("cleaning loop probe resistance1 =",formatnum(proberesistance1,precision=2))
			cleaniter+=1
			iv.writefile_probecleanlog(pathname=pathname, devicenames=devicenames, wafername=wafername_runno,probe0resistance_beforeclean=res0before, probe0resistance_afterclean=proberesistance0, probe1resistance_beforeclean=res1before, probe1resistance_afterclean=proberesistance1, cleaniter=cleaniter)
		# measure shorted device and record resistance IV
		iv.measure_ivfoc_dual_backgate('2', Vds_start=-0.1, Vds_stop=0.1, draincomp=0.1, Vds_npts=11, Vgs_start=0., Vgs_stop=0., gatecomp=gatecomp, Vgs_npts=1)
		iv.writefile_ivfoc_dual(pathname=pathname, devicenames=devicenames, wafername=wafername_runno, xloc0=device[0]["X"], yloc0=device[0]["Y"],xloc1=device[1]["X"],yloc1=device[1]["Y"])
		iv.fetbiason_dual_backgate(Vgs=0., Vds0=0., Vds1=0., gatecomp=gatecomp, draincomp0=0.05, draincomp1=0.05)           # hard set DC bias to zero prior to probing next device to ensure no charge buildup
	else:
		for Vds in [-0.001,-0.01,-0.05,-0.1]:
			# set full-scale drain current ranges to avoid autoranging
			if Vds==-0.001:
				devicenamemodifier="Vds_0p001"
				if 'T50' in devicenames[0]: draincomp=0.0001          # sets full scale Id range
				elif 'B50' in devicenames[0]: draincomp=0.00001
				elif 'T100' in devicenames[0]: draincomp=0.0001
				elif 'B100' in devicenames[0]: draincomp=0.00001
				else: raise ValueError("ERROR! no valid device name")

			elif Vds==-0.01:
				devicenamemodifier="Vds_0p01"
				if 'T50' in devicenames[0]: draincomp=0.001          # sets full scale Id range
				elif 'B50' in devicenames[0]: draincomp=0.0001
				elif 'T100' in devicenames[0]: draincomp=0.001
				elif 'B100' in devicenames[0]: draincomp=0.0001
				else: raise ValueError("ERROR! no valid device name")

			elif Vds==-0.05:
				devicenamemodifier="Vds_0p05"
				if 'T50' in devicenames[0]: draincomp=0.01          # sets full scale Id range
				elif 'B50' in devicenames[0]: draincomp=0.001
				elif 'T100' in devicenames[0]: draincomp=0.01
				elif 'B100' in devicenames[0]: draincomp=0.001
				else: raise ValueError("ERROR! no valid device name")

			elif Vds==-0.1:
				devicenamemodifier="Vds_0p1"
				if 'T50' in devicenames[0]: draincomp=1.E-2         # sets full scale Id range
				elif 'B50' in devicenames[0]: draincomp=1.E-2
				elif 'T100' in devicenames[0]: draincomp=1E-2
				elif 'B100' in devicenames[0]: draincomp=1.E-3
				else: raise ValueError("ERROR! no valid device name")
			else: raise ValueError("ERROR! no valid Vds value")
			#devicenamemodifier+="2nd"
			iv.measure_ivtransfer_dual_backgate(inttime="4", Iautorange=False, delayfactor=1,filterfactor=2,integrationtime=2, sweepdelay=0.2,holdtime=6, Vds=Vds, Vgs_start=Vgs_trans_start_ss, Vgs_stop=Vgs_trans_stop_ss, Vgs_step=Vgs_trans_step_ss, gatecomp=gatecomp, draincomp=draincomp)
			#iv.measure_ivtransfer_dual_backgate(inttime="2", Iautorange=True, delayfactor=2,filterfactor=2,integrationtime=2, sweepdelay=0.1,holdtime=0, Vds=Vds, Vgs_start=Vgs_trans_start_ss, Vgs_stop=Vgs_trans_stop_ss, Vgs_step=Vgs_trans_step_ss, gatecomp=gatecomp, draincomp=draincomp)
			iv.writefile_ivtransfer_dual(pathname=pathname, wafername=wafername_runno, devicenames=devicenames, devicenamemodifier=devicenamemodifier, xloc0=device[0]["X"], yloc0=device[0]["Y"], xloc1=device[1]["X"], yloc1=device[1]["Y"])
	cascade.move_separate()
	iv.groundoutputs()      # lower chuck then set outputs = 0V shorted
cascade.move_separate()
cascade.unlockstage()
# #del cascade
print("done probing wafer")
