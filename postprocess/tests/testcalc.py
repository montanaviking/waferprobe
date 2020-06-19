__author__ = 'PMarsh Carbonics'
# test of calculation of Rc, gm, etc...
from device_parameter_request import DeviceParameters
import matplotlib.pyplot as plt
import pylab as pl

pathname = 'c:/Users/test/python/waferprobe/data'
devicename = 'lot_test1_waf#_1die_0_0_dev_cfet0'
cd = DeviceParameters(pathname,devicename,"fractVgsfit 0.1, Y_Ids_fitorder 10.")
cd.writefile_ivtransfercalc()

axislablesfont = 10
axisfont = 12
titlefont = 12
linew1=10.
linew2=5.
linew3=3.

# now let's plot the data
plt.figure(1,figsize=(8,8))

## Id single sweep
axsub=plt.subplot(2,2,1)

plt.ticklabel_format(style='sci',scilimits=(1,1),axis='y')
plt.xlabel("Vgs (V)",fontsize=axislablesfont)
axsub.tick_params(axis='x',labelsize=axisfont)
axsub.tick_params(axis='y',labelsize=axisfont)
plt.ylabel("Id(A)",fontsize=axislablesfont)
ax1=plt.plot(cd.Vgs_T(),cd.Id_T()-cd.Idleak_T()['I'],label="measured")
plt.setp(ax1, linewidth=linew1, color='black')
plt.legend()
ax2=plt.plot(cd.Vgs_T(),cd.Idfit_T(),label="fit")
plt.setp(ax2, linewidth=linew2, color='lightblue')
plt.legend()
ax3=plt.plot(cd.Vgs_T(),cd.Idlin_T(),label="linear fit")
plt.setp(ax3, linewidth=linew3, color='green')
plt.legend()
plt.title("Single-Swept Id",fontsize=titlefont)
plt.grid(True)
## Id forward and reverse
axsub=plt.subplot(2,2,2)
plt.tight_layout(pad=4,w_pad=4.,h_pad=4.)
plt.ticklabel_format(style='sci',scilimits=(1,1),axis='y')
plt.xlabel("Vgs (V)",fontsize=axislablesfont)
axsub.tick_params(axis='x',labelsize=axisfont)
axsub.tick_params(axis='y',labelsize=axisfont)
plt.ylabel("Id(A)",fontsize=axislablesfont)
ax1=plt.plot(cd.Vgs_TF(),cd.Idfit_TF())
plt.title("Forward and Reverse Id",fontsize=titlefont)
plt.setp(ax1, linewidth=linew2, color='red')
ax2=plt.plot(cd.Vgs_TR(),cd.Idfit_TR())
plt.setp(ax2, linewidth=linew2, color='blue')
plt.grid(True)
## Y single sweep
axsub=plt.subplot(2,2,3)
plt.ticklabel_format(style='sci',scilimits=(1,1),axis='y')
plt.xlabel("Vgs (V)",fontsize=axislablesfont)
axsub.tick_params(axis='x',labelsize=axisfont)
axsub.tick_params(axis='y',labelsize=axisfont)
plt.ylabel("Y",fontsize=axislablesfont)
ax1=plt.plot(cd.Vgs_T(),cd.Yf_T())
plt.title("Single-Swept Y factor",fontsize=titlefont)
plt.setp(ax1, linewidth=linew1, color='black')
ax2=plt.plot(cd.Vgs_T(),cd.Yflin_T())
plt.setp(ax2, linewidth=linew2, color='green')
plt.grid(True)
### Gm
axsub=plt.subplot(2,2,4)
plt.ticklabel_format(style='sci',scilimits=(1,1),axis='y')
plt.xlabel("Vgs (V)",fontsize=axislablesfont)
axsub.tick_params(axis='x',labelsize=axisfont)
axsub.tick_params(axis='y',labelsize=axisfont)
plt.ylabel("gm (S)",fontsize=axislablesfont)
plt.title("Transconductance",fontsize=titlefont)

ax1=plt.plot(cd.Vgs_T(),cd.gm_T())
plt.setp(ax1, linewidth=linew1, color='black')

ax2=plt.plot(cd.Vgs_TF(),cd.gm_TR())
plt.setp(ax2, linewidth=linew2, color='blue')

ax3=plt.plot(cd.Vgs_TF(),cd.gm_TF())
plt.setp(ax3, linewidth=linew3, color='red')

plt.grid(True)


plt.tight_layout(pad=2,w_pad=0.5,h_pad=1.)
plt.show()

