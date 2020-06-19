__author__ = 'PMarsh Carbonics'
# test wafer analysis package
from wafer_analysis import WaferData
from IVplot import *
wd = WaferData(pathname="c:/Users/test/python/waferprobe/data/wafer3",wafername="wafer3",Y_Ids_fitorder=8)
# wd.write_waferparameter("Rc_T")
# wd.write_waferparameter("MAXGM_T")
# wd.write_waferparameter("VTH_T")
#wtrans = wd.__get_parameters()
wd.write_waferparameter_Rc('T')
wd.write_waferparameter_maxgm("T")
wd.write_waferparameter_Vth_T()
for ii in range(0,len(wd.DCd)-4):
    plotIV(wd.DCd[ii],"fractVgsfit 0.1, Y_Ids_fitorder 8")

#pwaf = PlotWafer(wd.get_wafername(),450,450,300,12195,13650,3060,4550,4,4)
#pwaf.plotwaferdata([wd.maxgm_T()['X'],wd.maxgm_T()['X']],[wd.maxgm_T()['Y'],wd.maxgm_T()['Y']],[wd.maxgm_T()['G'],wd.maxgm_T()['G']],["max Gm T","max Gm T2"])
#pwX=[wd.maxgm('T')['X'],wd.maxgm('TF')['X'],wd.maxgm('TR')['X']]
#pwY=[wd.maxgm('T')['Y'],wd.maxgm('TF')['Y'],wd.maxgm('TR')['Y']]
#pwG=[wd.maxgm('T')['G'],wd.maxgm('TF')['G'],wd.maxgm('TR')['G']]
#pwaf.plotwaferdata(pwX,pwY,pwG,["max Gm T","max Gm TF","max Gm TR"])
fnum=1

#pwaf.plotwaferdata(fnum,11,wd.maxgm('T')['X'],wd.maxgm('T')['Y'],wd.maxgm('T')['G'])
#pwaf.showplot()


