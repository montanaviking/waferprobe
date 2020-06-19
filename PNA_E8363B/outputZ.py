# measures output drain impedance vs time
# sweeps drain voltage
# outputs:
# frequency in Hz
# period in sec which is the period of the Vds sweep
# timestamps[time index] which is the time points of the impedance and Vds data vs time in seconds
# S22[Vgs index][time index]        # drain reflection coefficient measured via CW time domain mode from the pna at a single frequency when Vds is swept with a constant stepped Vgs
# Id[Vgs index][time index]         # drain current (A) measured via the oscilloscope when Vds is swept with a constant stepped Vgs
# Vds[Vgs index][time index]         # drain voltage applied measured via the oscilloscope when Vds is swept with a constant stepped Vgs, This normally does not depend on Vgs but is recorded this way for consistency
# Co[Vgs index][time index]         # output capacitance, Farad, when Vds is swept with a constant stepped Vgs
# Go[Vgs index][time index]         # output conductance, siemens, when Vds is swept with a constant stepped Vgs from S22
# Vgs[Vgs index]

import numpy as np
from oscilloscope import *
from amrel_power_supply import *
from pulsegenerator import *
from pulsed_measurements import ramped_sweep_gate
from loadpull_system_calibration import *               # gets the calibration parameter to convert the differential voltage to Id
from pna import *
from pulsed_measurements import *
from calculated_parameters import convertS22vstimeto_goco, gammatoYZ

def measure_outputZ_sweptVds(rm=None,frequency=1.5E9,gatebiassource=None,scope=None,pna=None,siggen=None,Pin=-15,period=0.01,IFbandwidth=40000,npts=50,numberofaverages=8,Vgs_start=None,Vgs_stop=None,Vgs_step=None,Vds_start=0,Vds_stop=-1,drainterminated=True):
	if siggen==None: siggen=PulseGeneratorDG1022(rm=rm)
	if gatebiassource==None: gatebiassource=amrelPowerSupply(rm=rm)
	if scope==None: scope=OscilloscopeDS1052E(rm=rm,shortoutput=True,filter=True)
	if pna==None: pna=Pna(rm=rm,readdefaultconfig=False)
	singleVgs=False
	if abs(Vgs_stop-Vgs_start)<1E-10 or Vgs_step<1E-10:
		nVgs=1
		singleVgs=True
	else: nVgs=int(abs(Vgs_stop-Vgs_start)/Vgs_step)+1
	if Vds_start<Vds_stop:
		Vdslow=Vds_start
		Vdshigh=Vds_stop
	else:
		Vdslow=Vds_stop
		Vdshigh=Vds_start
	if not singleVgs: Vgslist=np.linspace(start=Vgs_start,stop=Vgs_stop,num=nVgs)
	else:   Vgslist=[Vgs_start]

	S22vstime=[]
	Idvstime=[]
	Vdsvstime=[]
	Covstime=[]         # drain capacitance (farads) vs Vgs and time
	govstime=[]         # drain conductance (farads) vs Vgs and time
	Zout = []             # output impedance (complex) vs Vgs and time
	Yout = []           # output admittance (complex) vs Vgs and time
	gatestatus=[]
	err=[]
	timestamps=np.linspace(start=0, stop=period,num=200).tolist()
	for Vgs in Vgslist:
		retstat=gatebiassource.setvoltage(Vset=abs(Vgs),compliance=0.001)
		err.append(retstat[0])
		gatestatus.append(retstat[1])
		if gatestatus[-1]!='N': print("WARNING! gate shorted")
		timestampsscope,Id_raw,Vds_raw=ramped_sweep_drain(scope=scope,pulsegenerator=siggen,period=period,drainterminated=drainterminated,Vdslow=Vdslow,Vdshigh=Vdshigh,average=10,volttocurrentcalibrationfactor=volttocurrentcalibrationfactor,drainminguess=Vdslow-.5,drainmaxguess=Vdshigh+0.5)         # get Id vs time for swept drain voltage. voltagetocurrentcalibrationfactor is from loadpull_system_calibration
		timestampspna,s22_raw=pna.getS22_time(sweeptime=period,frequency=frequency,power=Pin,numberofpoints=npts,ifbandwidth=IFbandwidth,navg=numberofaverages)               # get S22 vs time for swept drain voltage
		s22_raw_real=[s.real for s in s22_raw]
		s22_raw_imag=[s.imag for s in s22_raw]
		Vdsvstime.append([np.interp(t,timestampsscope,Vds_raw) for t in timestamps])
		Idvstime.append([np.interp(t,timestampsscope,Id_raw) for t in timestamps])
		S22vstime.append([complex(np.interp(t,timestampspna,s22_raw_real),np.interp(t,timestampspna,s22_raw_imag)) for t in timestamps])        # interpolated real+jimaginary S22(t)
		retgo,retco=convertS22vstimeto_goco(s22=S22vstime[-1],frequency=frequency)
		govstime.append(retgo)
		Covstime.append(retco)
		Zout.append([gammatoYZ(gamma=s22,Z=True) for s22 in S22vstime[-1]])
		Yout.append([gammatoYZ(gamma=s22,Z=False) for s22 in S22vstime[-1]])
	siggen.pulsetrainoff()
	gatebiassource.output_off()
	ret={'frequency':frequency,'period':period,'Pin':Pin,'gatesupplyerrormessage':err,'gatestatus':gatestatus,'timestamps':timestamps,'Vgs':Vgslist,'S22':S22vstime,'Id':Idvstime,'Vds':Vdsvstime,'Co':Covstime,'Go':govstime, 'Zout':Zout, 'Yout':Yout}
	return ret


