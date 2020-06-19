# Phil Marsh, Carbonics Inc
# Amrel PPS 18-4D power supply control
import visa
from amrel_power_supply import *
from parameter_analyzer import *

compliance=0.5

rm=visa.ResourceManager()
print(rm.list_resources())
ps=amrelPowerSupply(rm,ptype=False)
pa=ParameterAnalyzer(rm,includeAMREL=True,ptype=False)
Vset=1.
pa.fetbiason_topgate(Vgs=-1,Vds=2.,gatecomp=0.1,draincomp=.4,maxchangeId=0.5,maxtime=1.,timeiter=0.2)
#err,comp,vout,Id=ps.setvoltage(Vset=Vset,compliance=compliance)
#Id,vout,comp=ps.get_Iout(compliance=compliance,Voutsetting=Vset)
pa.fetbiasoff()
#Vout=ps.get_Vout()
a=1
