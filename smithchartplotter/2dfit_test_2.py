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
#directory="/home/viking/Desktop/owncloudsync/X.Selected_Measurements/USC_April18_2017/RF_power/"
directory="/home/viking/ownCloud/X.Selected_Measurements/USC_April18_2017/RF_power/"
filename="aligned_nanotube_Feb13_2016__Vds-1.5_Vgs-1.00_R10_C14_TOI.xls"
Rho,outputTOI_average,outputTOI_lower,outputTOI_upper,gain=read_OIP3_vs_reflection_coefficients(directory+filename)
minreflectionreal=np.min(np.real(Rho))
maxreflectionreal=np.max(np.real(Rho))
minreflectionimag=np.min(np.imag(Rho))
maxreflectionimag=np.max(np.imag(Rho))

ref_real_int=np.linspace(minreflectionreal,maxreflectionreal,100)
ref_imag_int=np.linspace(minreflectionimag,maxreflectionimag,100)
#
# ref_real_int=np.linspace(-.7,.7,100)
# ref_imag_int=np.linspace(-.7,.7,100)



paraplotint=griddata((np.real(Rho),np.imag(Rho)),outputTOI_average,(ref_real_int[None,:] ,ref_imag_int[:,None]),method='cubic')


Preint,Pimint=np.meshgrid(ref_real_int,ref_imag_int)
#levels=np.arange(0,5,.1)
#deltatoi=(max(outputTOI_average)-min(outputTOI_average))/5
levels=np.linspace(min(outputTOI_average),max(outputTOI_average),5)
Rhoint=[[complex(Preint[i][j],Pimint[i][j]) for j in range(0,np.shape(Preint)[1]) ] for i in range(0,np.shape(Preint)[0])]

Zreint=[[((1+Rhoint[i][j])/(1-Rhoint[i][j])).real for j in range(0,np.shape(Rhoint)[1])] for i in range(0,np.shape(Rhoint)[0])]
Zimint=[[((1+Rhoint[i][j])/(1-Rhoint[i][j])).imag for j in range(0,np.shape(Rhoint)[1])] for i in range(0,np.shape(Rhoint)[0])]

znorm=[(1+Rho[i])/(1-Rho[i]) for i in range(0,len(Rho))]

# xx,yy=np.mgrid(x,y)
fig=plt.figure()
ax=fig.add_subplot(1,1,1,projection='smith')

CS=ax.contourf(Zreint,Zimint,paraplotint,levels=levels,datatype='SmithAxes.S_PARAMETER')

ax.scatter(np.real(znorm),np.imag(znorm),color='black')
#ax.clabel(CS,inline=1,fontsize=5,datatype='SmithAxes.S_PARAMETER')
ax.grid(True)
plt.show()