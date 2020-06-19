__author__ = 'PMarsh Carbonics'
# test of TLM postprocessing

from old.device_parameter_Ron_TLM import *

from IVplot import plotTLM
from utilities import *

maxL=0.6        # maximum TLM length to consider for sheet resistance and Rc
mingm=1.E-10
#pathname = 'c:/Users/test/python/waferprobe/data/RES_Aug21_2015waf'
pathname = '/home/viking/documents_2/MicrocraftX_LLC/customers/Carbonics/projects/documents/wafer_tests/H34_Aug2015'
#devT = Tlm(pathname,"H31_Aug21_2015__MQ1_ST2_MO_RT1_DV4_TLM",maxL,mingm)
#print (len(devT.RTLM()['Vgs']),len(devT.RTLM()['L']),len(devT.RTLM()['R']))
# for ig in range(0,len(devT.RTLM()['Vgs'])):
#     #print("Vgs,L,Rc",devT.RTLM()['Vgs'][ig],devT.RTLM()['L'][ig],devT.RTLM()['R'][ig])
#     print("Vgs,L,Rc",devT.RTLM()['Vgs'][ig],devT.RTLM()['L'][ig],devT.RTLM()['R'][ig])
#print(pathname+sub("DC"),getfilelisting(pathname,'.xls','TLM'))
dfiles = file_to_devicename(inputdevlisting=getfilelisting(pathname+sub("DC"),'.xls','TLM'),deleteendstrings=['_TLM'])
#print (dfiles)

for idev in range(0,len(dfiles)):
	devT = Tlm(pathname,dfiles[idev],maxL,mingm)
	print (devT.get_sitename())
	if devT.RTLM()!='None': plotTLM(devT.RTLM(),devT.RTLMlinfit(),devT.get_wafername(),devT.get_sitename(),-15)
	del devT