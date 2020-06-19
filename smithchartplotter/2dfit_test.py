# test 2-D interpolation
from scipy.interpolate import griddata
from scipy.interpolate import interp2d
from read_reflection_parametervsreflection import read_OIP3_vs_reflection_coefficients
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import numpy as np
from smithplot import SmithAxes
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
from utilities import formatnum
import matplotlib.cm as cm
import matplotlib.colors as col
import matplotlib.patches as pch
import matplotlib as mpl
#
# directory="/home/viking/Desktop/owncloudsync/X.Selected_Measurements/USC_April18_2017/RF_power/"
# filename="aligned_nanotube_Feb13_2016__Vds-1.5_Vgs-1.00_R10_C14_TOI.xls"
# Rho,outputTOI_average,outputTOI_lower,outputTOI_upper,gain=read_OIP3_vs_reflection_coefficients(directory+filename)
# minreflectionreal=np.min(np.real(Rho))
# maxreflectionreal=np.max(np.real(Rho))
# minreflectionimag=np.min(np.imag(Rho))
# maxreflectionimag=np.max(np.imag(Rho))


pre=np.linspace(-.4,.4,8)
pim=np.linspace(-.6,.6,12)
Pre,Pim=np.meshgrid(pre,pim)

#Rho=[[complex(pre[j],pim[i]) for j in range(0,len(pre))] for i in range(0,len(pim))]
rho=[complex(pre[j],pim[i]) for i in range(0,len(pim)) for j in range(0,len(pre))]
para=np.array([abs(rho[i]) for i in range(0,len(rho))])



#f=griddata(Pre,Pim,para,method='cubic')

#Zre=[[((1+Rho[i][j])/(1-Rho[i][j])).real for j in range(0,np.shape(Rho)[1])] for i in range(0,np.shape(Rho)[1])]
#Zim=[[((1+Rho[i][j])/(1-Rho[i][j])).imag for j in range(0,np.shape(Rho)[1])] for i in range(0,np.shape(Rho)[1])]
paraplot=[[abs(complex(pre[j],pim[i])) for i in range(0,len(pim))] for j in range(0,len(pre))]


#f=interp2d(Pre,Pim,paraplot,kind='cubic')
paraplotint=griddata((np.real(rho),np.imag(rho)),para,(np.linspace(-.6,.6,100)[None,:] ,np.linspace(-.6,.6,100)[:,None]),method='cubic')
#paraplotint=griddata((np.real(Rho),np.imag(Rho)),outputTOI_average,(np.linspace(minreflectionreal,maxreflectionreal,100)[None,:] ,np.linspace(minreflectionimag,maxreflectionimag,100)[:,None]),method='cubic')

#rhogrid=np.complex(np.linspace(-.5,.5,100),np.linspace(-.6,.6,120))

# zre=[((1+p)/(1-p)).real for p in rhogrid ]
# zim=[((1+p)/(1-p)).imag for p in rhogrid ]

#Preint,Pimint=np.meshgrid(np.linspace(minreflectionreal,maxreflectionreal,100),np.linspace(minreflectionimag,maxreflectionimag,100))
Preint,Pimint=np.meshgrid(np.linspace(-.6,.6,100),np.linspace(-.6,.6,100))
levels=np.arange(0,1,.1)
Rhoint=[[complex(Preint[i][j],Pimint[i][j]) for j in range(0,np.shape(Preint)[1]) ] for i in range(0,np.shape(Preint)[0])]
#paraplot1=[[1/abs(complex(Rhoint[i][j])) for j in range(0,np.shape(Rhoint)[1])] for i in range(0,np.shape(Rhoint)[0])]
#paraplotint=f(np.linspace(-.5,.5,100),np.linspace(-.6,.6,120))
#paraplotint=[[f(Preint[i][j],Pimint[i][j]) for j in range(0,np.shape(Preint)[1]) ] for i in range(0,np.shape(Preint)[0])]
Zreint=[[((1+Rhoint[i][j])/(1-Rhoint[i][j])).real for j in range(0,np.shape(Rhoint)[1])] for i in range(0,np.shape(Rhoint)[0])]
Zimint=[[((1+Rhoint[i][j])/(1-Rhoint[i][j])).imag for j in range(0,np.shape(Rhoint)[1])] for i in range(0,np.shape(Rhoint)[0])]

# xx,yy=np.mgrid(x,y)
fig=plt.figure()
ax=fig.add_subplot(1,1,1,projection='smith')

CS=ax.contour(Zreint,Zimint,paraplotint,datatype='SmithAxes.S_PARAMETER')
ax.clabel(CS,inline=1,fontsize=10,datatype='SmithAxes.S_PARAMETER')
ax.grid(True)
plt.show()