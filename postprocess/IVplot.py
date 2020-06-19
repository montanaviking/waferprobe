__author__ = 'PMarsh Carbonics'
# plotting of IV characteristics
#from device_parameter_request import DeviceParameters
from mpl_toolkits.mplot3d import Axes3D
from PyQt5 import QtCore, QtWidgets
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import sys
sys.path.append("..")
try: from smithplot import SmithAxes
except: print("WARNING! no smith chart plotting available")
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
from utilities import formatnum
import matplotlib.cm as cm
import matplotlib.colors as col
import matplotlib.pyplot as plt
import matplotlib.patches as pch
import matplotlib as mpl
from scipy.interpolate import griddata
from calculated_parameters import convertRItoMA, convertMAtoRI
#from utilities import swapindex
import numpy as np
import time
#import pylab as pl

# plot IV characteristics of the device defined by cd which is a class of type DeviceParameters
# fitparameters is the fitting parameters for the Y-function and Id linear extrapolations
# e.g. fitparameters = "fractVgsfit 0.1, Y_Ids_fitorder 10."
def plotIV(cd,fitparameters):
	#plt.ion()									    # needed to allow redrawing of plot
	#cd.set_parameters_curvefit(fitparameters)
#    cd.writefile_ivtransfercalc()                   # write IV transfer curve results to file
	cd.get_orderfit()

	axislablesfont = 10
	axisfont = 12
	titlefont = 12
	legendfont=12
	annotefont=12
	figuretitlefont=15
	linew1=10.
	linew2=5.
	linew3=3.
	linew4=2.
	xyannote=[.5,0.95]

	figrow = 3
	figcol = 3
	# now let's plot the data
	f1=plt.figure(100,figsize=(10,10))
	wm = plt.get_current_fig_manager()
	wm.window.attributes('-topmost',1)

	## Id single sweep transfer curve
	if cd.Idfit_T()!= 'None':
		axsub=plt.subplot(figrow,figcol,1)
		plt.ticklabel_format(style='sci',scilimits=(1,1),axis='y')
		plt.xlabel("Vgs (V)",fontsize=axislablesfont)
		plt.ylabel("Id(A)",fontsize=axislablesfont)
		axsub.tick_params(axis='x',labelsize=axisfont)
		axsub.tick_params(axis='y',labelsize=axisfont)

		ax1=plt.plot(cd.Vgs_T(),cd.Id_T()-cd.Idleak_T()['I'],label="measured")
		plt.setp(ax1, linewidth=linew1, color='black')

		ax2=plt.plot(cd.Idfit_T()['Vgs'],cd.Idfit_T()['I'],label="fit")
		plt.setp(ax2, linewidth=linew2, color='lightblue')


		try: ax3=plt.plot(cd.Idlin_T()['Vgs'],cd.Idlin_T()['I'],label="linear fit")
		except: print("Warning cannot plot linear fit if single-swept transfer curve")
		try: plt.setp(ax3, linewidth=linew3, color='green')
		except: pass

		plt.title("Single-Swept Id",fontsize=titlefont)
		plt.legend(ncol=1,bbox_to_anchor=(.98,.28),borderaxespad=0,fontsize=legendfont)
		#plt.annotate('max gm '+str('{:5.1E}'.format(cd.gmmax_T())),xy=(xyannote),xycoords='axes fraction',fontsize=annotefont)
		plt.grid(True)

	## Id forward and reverse##############################################
	if cd.Idfit_TF()!= 'None':
		axsub=plt.subplot(figrow,figcol,2)
		plt.ticklabel_format(style='sci',scilimits=(1,1),axis='y')
		plt.xlabel("Vgs (V)",fontsize=axislablesfont)
		plt.ylabel("Id(A)",fontsize=axislablesfont)
		axsub.tick_params(axis='x',labelsize=axisfont)
		axsub.tick_params(axis='y',labelsize=axisfont)

		ax1=plt.plot(cd.Idfit_TF()['Vgs'],cd.Idfit_TF()['I'],label="forward")
		plt.setp(ax1, linewidth=linew2, color='red')

		try: ax2=plt.plot(cd.Idfit_TR()['Vgs'],cd.Idfit_TR()['I'],label="reverse")
		except: print("Warning cannot plot line fit of dual-swept transfer curve")
		try: plt.setp(ax2, linewidth=linew2, color='blue')
		except: pass

		plt.legend(ncol=1,bbox_to_anchor=(.98,0.2),borderaxespad=0,fontsize=legendfont)
		plt.title("Forward and Reverse Id",fontsize=titlefont)
		plt.grid(True)


	## Y single sweep########################################
	if cd.Yf_T()!= 'None':
		axsub=plt.subplot(figrow,figcol,3)
		plt.ticklabel_format(style='sci',scilimits=(1,1),axis='y')
		axsub.tick_params(axis='x',labelsize=axisfont)
		axsub.tick_params(axis='y',labelsize=axisfont)
		plt.xlabel("Vgs (V)",fontsize=axislablesfont)
		plt.ylabel("Y",fontsize=axislablesfont)

		try: ax1=plt.plot(cd.Yf_T()['Vgs'],cd.Yf_T()['Y'],label="forward")
		except: print("Warning cannot plot line fit of Yf")
		try: plt.setp(ax1, linewidth=linew1, color='black')
		except: pass

		try: ax2=plt.plot(cd.Yflin_T()['Vgs'],cd.Yflin_T()['Y'],label="forward")
		except: print("Warning cannot plot line fit of Yf")
		plt.setp(ax2, linewidth=linew2, color='green')

		plt.title("Single-Swept Y factor",fontsize=titlefont)
		plt.grid(True)
		plt.annotate('Rc= '+str('{:5.1E}'.format(cd.Rc_T()))+' ohms',xy=(xyannote),xycoords='axes fraction',fontsize=annotefont)
	#####################################################################################################################
	### Gm##################################################################################################
	if cd.gm_T()!='None' and cd.gm_TF()!='None' and cd.gm_TR()!='None':
		axsub=plt.subplot(figrow,figcol,4)
		plt.ticklabel_format(style='sci',scilimits=(1,1),axis='y')
		axsub.tick_params(axis='x',labelsize=axisfont)
		axsub.tick_params(axis='y',labelsize=axisfont)
		plt.xlabel("Vgs (V)",fontsize=axislablesfont)
		plt.ylabel("gm (S)",fontsize=axislablesfont)

		ax1=plt.plot(cd.gm_T()['Vgs'],cd.gm_T()['G'],label="single sweep")
		plt.setp(ax1, linewidth=linew1, color='black')

		ax2=plt.plot(cd.gm_TR()['Vgs'],cd.gm_TR()['G'],label="forward")
		plt.setp(ax2, linewidth=linew2, color='blue')

		ax3=plt.plot(cd.gm_TF()['Vgs'],cd.gm_TF()['G'],label="reverse")
		plt.setp(ax3, linewidth=linew3, color='red')

		plt.title("Transconductance",fontsize=titlefont)
		plt.legend(ncol=1,bbox_to_anchor=(.6,0.28),borderaxespad=0,fontsize=legendfont)
		plt.annotate('max gm '+str('{:5.1E}'.format(cd.gmmax_T()['G'])),xy=(xyannote),xycoords='axes fraction',fontsize=annotefont)
		plt.grid(True)
	#####################################################################################################################
	#family of curves
	####################################################################################################################
	if cd.IdIV_foc() != "None":
		axsub=plt.subplot(figrow,figcol,5)
		plt.ticklabel_format(style='sci',scilimits=(1,1),axis='y')
		axsub.tick_params(axis='x',labelsize=axisfont)
		axsub.tick_params(axis='y',labelsize=axisfont)
		plt.xlabel("Vds (V)",fontsize=axislablesfont)
		plt.ylabel("Id (A)",fontsize=axislablesfont)

		for ii in range(0,len(cd.IdIV_foc())):
			axfoc=plt.plot(cd.VdsIV_foc()[ii],cd.IdIV_foc()[ii])
			plt.setp(axfoc,linewidth=linew3, color='black')
			axfoc=plt.plot(cd.VdsIV_foc()[ii],cd.IdRonlin_foc()[ii])
			plt.setp(axfoc,linewidth=linew4, color='red')

		plt.title("family of curves",fontsize=titlefont)
		#plt.legend(ncol=1,bbox_to_anchor=(.6,0.28),borderaxespad=0,fontsize=legendfont)
		#plt.annotate('max gm '+str('{:5.1E}'.format(cd.gmmax_T())),xy=(xyannote),xycoords='axes fraction',fontsize=annotefont)
		plt.grid(True)
	#####################################################################################################################
	 #Ron from family of curves
	####################################################################################################################
	if cd.Ron_foc() != "None":
		axsub=plt.subplot(figrow,figcol,6)
		plt.ticklabel_format(style='sci',scilimits=(1,1),axis='y')
		axsub.tick_params(axis='x',labelsize=axisfont)
		axsub.tick_params(axis='y',labelsize=axisfont)
		plt.xlabel("Vgs (V)",fontsize=axislablesfont)
		plt.ylabel("Ron (ohms)",fontsize=axislablesfont)
		axfoc=plt.plot(cd.Ron_foc()['Vgs'],cd.Ron_foc()['R'])
		plt.setp(axfoc,linewidth=linew3, color='black')

		plt.title("On Resistance",fontsize=titlefont)
		plt.grid(True)

	#####################################################################################################################
	 #Id vs Vgs from family of curves
	####################################################################################################################
	# # if cd.Id_foc() != "None" and cd.Idfit_foc() != "None":
	#
	#     axsub=plt.subplot(figrow,figcol,7)
	#     plt.ticklabel_format(style='sci',scilimits=(1,1),axis='y')
	#     axsub.tick_params(axis='x',labelsize=axisfont)
	#     axsub.tick_params(axis='y',labelsize=axisfont)
	#     plt.xlabel("Vgs (V)",fontsize=axislablesfont)
	#     plt.ylabel("Id (A)",fontsize=axislablesfont)
	#     #print len(cd.Idfit_foc()['Vds']),len(cd.Id_foc()['Vds'])
	#     #quit()
	#     for id in range(0,len(cd.Idfit_foc()['Vds'])):
	#         axfoc=plt.plot(cd.Idfit_foc()['Vgs'],cd.Idfit_foc()['I'][id])
	#         plt.setp(axfoc,linewidth=linew4, color='black')
	#     #print cd.Id_foc()['Vds']
	#     for id in range(1, 1+len(cd.Idleak_foc()['Vds'])):
	#         axfoc=plt.plot(cd.Id_foc()['Vgs'],[cd.Id_foc()['I'][id][ig]-cd.Idleak_foc()['I'][id-1] for ig in range(0,len(cd.Id_foc()['Vgs']))])
	#         plt.setp(axfoc,linestyle='None', marker='o',color='black')
	#    # plt.title("Polynomial Fit Id from foc",fontsize=titlefont)
	#     #plt.legend(ncol=1,bbox_to_anchor=(.6,0.28),borderaxespad=0,fontsize=legendfont)
	#     #plt.annotate('max gm '+str('{:5.1E}'.format(cd.gmmax_T())),xy=(xyannote),xycoords='axes fraction',fontsize=annotefont)
	#     plt.grid(True)
	# ####################################################################################################################
	  #Y factor and Ylin vs Vgs from family of curves
	####################################################################################################################
	# if cd.Yf_foc() != "None" and cd.Yflin_foc() != "None":
	#     axsub=plt.subplot(figrow,figcol,8)
	#     plt.ticklabel_format(style='sci',scilimits=(1,1),axis='y')
	#     axsub.tick_params(axis='x',labelsize=axisfont)
	#     axsub.tick_params(axis='y',labelsize=axisfont)
	#     plt.xlabel("Vgs (V)",fontsize=axislablesfont)
	#     plt.ylabel("Y factor",fontsize=axislablesfont)
	#     #print len(cd.Idfit_foc()['Vds']),len(cd.Id_foc()['Vds'])
	#     #quit()
	#     for id in range(0,len(cd.Yf_foc()['Vds'])):
	#         axfoc=plt.plot(cd.Yf_foc()['Vgs'],cd.Yf_foc()['Y'][id])
	#         plt.setp(axfoc,linewidth=linew4, color='black')
	#     #print cd.Id_foc()['Vds']
	#     for id in range(0, len(cd.Yflin_foc()['Vds'])):
	#         axfoc=plt.plot(cd.Yflin_foc()['Vgs'],cd.Yflin_foc()['Y'][id])
	#         plt.setp(axfoc,linewidth=linew4, color='red')
	#    # plt.title("Polynomial Fit Id from foc",fontsize=titlefont)
	#     #plt.legend(ncol=1,bbox_to_anchor=(.6,0.28),borderaxespad=0,fontsize=legendfont)
	#     #plt.annotate('max gm '+str('{:5.1E}'.format(cd.gmmax_T())),xy=(xyannote),xycoords='axes fraction',fontsize=annotefont)
	#     plt.grid(True)
	# ####################################################################################################################
	#   # Rc vs Vds from family of curves
	# ####################################################################################################################
	if cd.Rc_foc() != "None":
		axsub=plt.subplot(figrow,figcol,9)
		plt.ticklabel_format(style='sci',scilimits=(1,1),axis='y')
		axsub.tick_params(axis='x',labelsize=axisfont)
		axsub.tick_params(axis='y',labelsize=axisfont)
		plt.xlabel("Vds (V)",fontsize=axislablesfont)
		plt.ylabel("Rc (ohms)",fontsize=axislablesfont)
		#print len(cd.Idfit_foc()['Vds']),len(cd.Id_foc()['Vds'])
		#quit()
		axfoc=plt.plot(cd.Rc_foc()['Vds'],cd.Rc_foc()['R'])
		plt.setp(axfoc,linewidth=linew4, color='black')
		  # plt.title("Polynomial Fit Id from foc",fontsize=titlefont)
		#plt.legend(ncol=1,bbox_to_anchor=(.6,0.28),borderaxespad=0,fontsize=legendfont)
		#plt.annotate('max gm '+str('{:5.1E}'.format(cd.gmmax_T())),xy=(xyannote),xycoords='axes fraction',fontsize=annotefont)
		plt.grid(True)
	####################################################################################################################

	plt.suptitle(cd.get_devicename()+"\nLocation: X "+str(cd.x())+" um    Y "+str(cd.y())+" um",fontsize=figuretitlefont)
	plt.tight_layout(pad=2,w_pad=1,h_pad=1,rect=[0,0,1,.95])
	#plt.show()

	plt.draw()
	plt.pause(0.0001)
	time.sleep(10)
	#plt.show()
########################################################################################################################
########################################################################################################################
# Class to plot wafer level parameters in a 3D topographical format
# cds are the IV parameters arrays (class DeviceParameters)
# retXsize, retYsize are the wafer reticle sizes and retXspace, retYspace are the reticle-reticle spacings
# devsize is the size of the device (both x and y)
# d are the data location and magnitude - e.g. d['X'], the x location, d['Y'] the y location, and d['D']
# the data magnitude (z-direction)
class PlotWafer_3D:
	def __init__(self,wafername,originX,originY,devsize,retXsize,retYsize,retXspace,retYspace,noretX,noretY):
		# setup 3D bar plots
		self.noplots=0                # number of plots currently in figure
		self.figrow=0                   # number of subplot rows currently in figure
		self.figcol=0                   # number of subplot columns currently in figure

		self.orgX = originX         # X location of the wafer origin relative to the lower left reticle lower left corner
		self.orgY = originY         # Y location of the wafer origin relative to the lower left reticle lower left corner
		self.devsize=devsize        # size of measured device as displayed on wafer map
		self.retX=retXsize          # X size of reticle
		self.retY=retYsize          # Y size of reticle
		self.noXret = noretX        # number of X (columns of reticles)
		self.noYret = noretY        # number of Y (rows of reticles)
		self.retXspace=retXspace    # X spacing between reticles
		self.retYspace=retYspace    # Y spacing between reticles

		self.dataX=[]               # plotting data array X locations
		self.dataY=[]               # plotting data array Y locations
		self.dataZ=[]               # plotting data values
		self.datatitle=[]           # titles of wafer data
		self.fig1=plt.figure(1,figsize=(18,12))
		plt.suptitle("Wafer "+wafername,fontsize=30)
		wm = plt.get_current_fig_manager()
		wm.window.attributes('-topmost',1)
	####################################################################################################################
	# plot wafer grid
	# noplots is the total number of plots in the figure
	# frow, fcol are the number of rows and columns in the figure
	# the subplots are added here in this function
	def __plotwafergrid(self,noplots,figrow,figcol):
		xpos=[]
		ypos=[]
		zpos=[]
		dx=[]
		dy=[]
		for iy in range(0,self.noYret):
			for ix in range(0,self.noXret):
				zpos.append(0.)
				dx.append(self.retX)
				dy.append(self.retY)
				xpos.append((ix+0.5)*self.retXspace + ix*self.retX)
				ypos.append((iy+0.5)*self.retYspace + iy*self.retY)

		# add reticle tiles
		self.ax = []        # clear out old plots so we can replot
		for ip in range(0,noplots):
			self.ax.append(self.fig1.add_subplot(figrow,figcol,ip,projection='3d'))
			self.ax[-1].bar3d(xpos, ypos, zpos, dx, dy, 0., color='yellow', edgecolor="black")   # wafer tiles are black
			self.ax[-1].set_zorder(0)
	####################################################################################################################
	# accumumate wafer plots
	# each call to this method adds a subplot for that data
	#def plotdatainput(self,datXin,datYin,datZin,dtitlein):

	####################################################################################################################
	# plot wafer data
	# datX is the X-location of the data in um and is an array with each element referring to separate plots
	# datY is the Y-location of the data in um and is an array with each element referring to separate plots
	# datZ is the plotted quantity of the data and is an array with each element referring to separate plots
	def plotwaferdata(self,datX,datY,datZ,dtitle):
		legendfont=12
		annotefont=12
		figuretitlefont=15
		axislabelsfont = 10
		axisfont = 12
		titlefont = 12

		#xyannote=[.5,0.95]

		#datX =[[x+self.orgX+self.retXspace/2 for x in datX[ip]] for ip in range(0,len(datX))]
		#datY = [y+self.orgY+self.retYspace/2 for y in datY]
		if not isinstance(datX[0],list):   # if input data are single values - just one plot, then make data into lists
			self.dataX=[datX]       # X location data array of wafer dataset
			self.dataY=[datY]       # Y location data array of wafer dataset
			self.dataZ=[datZ]       # values data array
			self.datatitle=[dtitle]
		else:       # data are already lists (more than one plot)
			self.dataX=datX       # X location data array of wafer dataset
			self.dataY=datY       # Y location data array of wafer dataset
			self.dataZ=datZ       # values data array
			self.datatitle=dtitle

		noplots = len(self.dataX)  # current number of plots = the current number of datasets to be plotted
		# find the number of rows and columns to plot
		figcol =int(round(np.sqrt(noplots)+.4999999999999))
		figrow = int(round(float(noplots)/float(figcol))+.5)
		#print (figcol, figrow)

		if (len(self.dataX[-1]) != len(self.dataY[-1])) or (len(self.dataX[-1]) != len(self.dataZ[-1])):
			raise ValueError("ERROR! different sized X Y Z array sizes in dataset!")
		self.__plotwafergrid(noplots,figrow,figcol)                # plot wafer reticle grid
		for ip in range(0,len(self.dataX)):                                 # plot all data sets to produce len(self.dataX) plots - one per data set. ip is the plot index
			norm = col.Normalize(min(self.dataZ[ip]),max(self.dataZ[ip]))
			cmap=cm.ScalarMappable(norm)
			cmap.set_cmap("Spectral")
			self.dataX[ip] = [x+self.orgX+self.retXspace/2 for x in self.dataX[ip]]
			self.dataY[ip] = [y+self.orgY+self.retYspace/2 for y in self.dataY[ip]]
			self.ax[ip].set_xlabel('X um',fontsize=axislabelsfont)
			self.ax[ip].set_ylabel('Y um',fontsize=axislabelsfont)
			self.ax[ip].tick_params(axis='x',labelsize=axisfont)
			self.ax[ip].tick_params(axis='y',labelsize=axisfont)
			self.ax[ip].tick_params(axis='z',labelsize=axisfont)
			self.ax[ip].set_title(self.datatitle[ip],fontsize=titlefont)
			dx = [self.devsize for i in range(0,len(self.dataZ[ip]))]       # x size of 3-d bar which represents the point of wafer data
			dy = [self.devsize for i in range(0,len(self.dataZ[ip]))]       # y size of 3-d bar which represents the point of wafer data
			self.ax[ip].bar3d(self.dataX[ip], self.dataY[ip], np.zeros(len(self.dataZ[ip])), dx, dy, self.dataZ[ip], color=cmap.to_rgba(self.dataZ[ip]), edgecolor="none")
			self.ax[ip].ticklabel_format(style='sci',scilimits=(-3,4),axis='z')
			self.ax[ip].set_zorder(10)
	########################################
########################################################################################################################
########################################################################################################################
# Class to plot wafer level parameters in a 2D colortile format
# cds are the IV parameters arrays (class DeviceParameters)
# retXsize, retYsize are the wafer reticle sizes and retXspace, retYspace are the reticle-reticle spacings
# devsize is the size of the device (both x and y)
# d are the data location and magnitude - e.g. d['X'], the x location, d['Y'] the y location, and d['D']
# the data magnitude (z-direction)
class PlotWafer:
	def __init__(self,wafername,originX,originY,devsize,retXsize,retYsize,retXspace,retYspace,noretX,noretY,fig):
		# setup 3D bar plots
		self.fig = fig
		self.noplots=0                # number of plots currently in figure
		self.figrow=0                   # number of subplot rows currently in figure
		self.figcol=0                   # number of subplot columns currently in figure

		self.orgX = originX         # X location of the wafer origin relative to the lower left reticle lower left corner
		self.orgY = originY         # Y location of the wafer origin relative to the lower left reticle lower left corner
		self.devsize=devsize        # size of measured device as displayed on wafer map
		self.retX=retXsize          # X size of reticle
		self.retY=retYsize          # Y size of reticle
		self.noXret = noretX        # number of X (columns of reticles)
		self.noYret = noretY        # number of Y (rows of reticles)
		self.retXspace=retXspace    # X spacing between reticles
		self.retYspace=retYspace    # Y spacing between reticles

		self.dataX=[]               # plotting data array X locations
		self.dataY=[]               # plotting data array Y locations
		self.dataZ=[]               # plotting data values
		self.datatitle=[]           # titles of wafer data

		#wm = plt.get_current_fig_manager()
		#wm.window.attributes('-topmost',1)
	####################################################################################################################
	# plot wafer grid
	# noplots is the total number of plots in the figure
	# frow, fcol are the number of rows and columns in the figure
	# the subplots are added here in this function
	# self.fnum is the fig number
	def __plotwafergrid(self):
		#self.fig=plt.figure(self.fnum,figsize=(12,12))

		#plt.suptitle("Wafer "+wafername,fontsize=30)
		# add reticle tiles
		try: del self.ax       # clear out old plots so we can replot
		except: pass
		#self.fig.cla()
		self.ax=self.fig.add_subplot(1,1,1)
		self.ax.autoscale(enable=False)
		print(self.ax.get_xlim())
		xmax = self.noXret*(self.retXspace+self.retX)	# maximum extent of reticle space in X direction
		ymax = self.noYret*(self.retYspace+self.retY)	# maximum extent of reticle space in Y direction
		self.ax.set_xlim([0.,xmax])
		self.ax.set_ylim([0.,ymax])
		for iry in range(0,self.noYret):		# rows of reticles
			for irx in range(0,self.noXret):	# columns of reticles
				xpos = (irx+0.5)*self.retXspace + irx*self.retX
				ypos = (iry+0.5)*self.retYspace + iry*self.retY
				s = pch.Rectangle((xpos,ypos),self.retX,self.retY,facecolor='grey',edgecolor="none")
				self.ax.add_patch(s)
	####################################################################################################################
	# plot single type of wafer data on a color-coded wafer plot
	# X is the X-location of the data in um and is an array with each element referring to separate plots
	# Y is the Y-location of the data in um and is an array with each element referring to separate plots
	# datZ is the plotted quantity of the data and is an array with each element referring to separate plots
	# lowerlimit is the lower limit of the plotted quantity datZ
	# upperlimit is the upper limite of the plotted quantity datZ
	# logscale = True, plot the absolute value of the data on a log10 scale
	def plotwaferdata(self,fn=None,canvas=None,X=None,Y=None,datZ=None,lowerlimit=None,upperlimit=None,logscale=False):
		legendfont=12
		annotefont=12
		figuretitlefont=15
		axislabelsfont = 10
		axisfont = 12
		titlefont = 12
		self.fnum=fn
		if fn==None or canvas==None or X==None or Y==None or datZ==None:
			raise ValueError("ERROR! missing parameters")
		#if (len(self.dataX[-1]) != len(self.dataY[-1])) or (len(self.dataX[-1]) != len(self.dataZ[-1])):
		#	raise ValueError("ERROR! different sized X Y Z array sizes in dataset!")
		self.__plotwafergrid()                # plot wafer reticle grid
		if lowerlimit==None: lowerlimit=min(datZ)
		if upperlimit==None: upperlimit=max(datZ)
		if logscale==False: norm = col.Normalize(lowerlimit,upperlimit)
		if logscale==True: norm = col.Normalize(np.log10(abs(lowerlimit)),np.log10(abs(upperlimit)))
		cmap=cm.ScalarMappable(norm)
		cmap.set_cmap("Spectral")
		dat_X = [x+self.orgX+self.retXspace/2 for x in X]	# X location of the wafer data point
		dat_Y = [y+self.orgY+self.retYspace/2 for y in Y] # Y location of the wafer data point
		self.ax.set_xlabel('X um',fontsize=axislabelsfont)
		self.ax.set_ylabel('Y um',fontsize=axislabelsfont)
		self.ax.tick_params(axis='x',labelsize=axisfont)
		self.ax.tick_params(axis='y',labelsize=axisfont)
		self.ax.set_title(self.datatitle,fontsize=titlefont)
		s=[]
		#print("lowerlimit, upperlimit",lowerlimit,upperlimit) #debug
		for id in range(0,len(datZ)):			# place a device color data tile for all devices on this data wafer plot
			if datZ[id]<=upperlimit and datZ[id]>=lowerlimit:
				if logscale==False:
					s.append(pch.Rectangle((dat_X[id],dat_Y[id]), self.devsize, self.devsize,facecolor=cmap.to_rgba(datZ[id]),edgecolor="none"))
				elif logscale==True:		# plot on a log scale
					s.append(pch.Rectangle((dat_X[id],dat_Y[id]), self.devsize, self.devsize,facecolor=cmap.to_rgba(np.log10(abs(datZ[id]))),edgecolor="none"))
				self.ax.add_patch(s[-1])
			else:
				s.append(pch.Rectangle((dat_X[id],dat_Y[id]), self.devsize, self.devsize,facecolor=cmap.to_rgba(datZ[id]),edgecolor="none"))		# needed to ensure that the picker will work and gets the right indicies
		self.ax.hold(False)
		#print("from IVplot.py plotwaferdata",self.ax.get_xlim()) # debug
		canvas.draw()
		return s
	########################################
	# display plot
	def showplot(self):
		plt.show()
########################################################################################################################
#plots family of curves for a single device
def plot_family_of_curves(cd,figure,canvas,plotlin=False,xmin=None,xmax=None,ymin=None,ymax=None,Vgs='all'):
	axislablesfont = 18
	axisfont = 18
	titlefont = 22
	legendfont=12
	annotefont=12
	figuretitlefont=15
	linew1=10.
	linew2=5.
	linew3=3.
	linew4=2.
	xyannote=[.5,0.95]

	figrow = 1
	figcol = 1
	plt.clf()
	figure.clear()

	if Vgs.lower()!="all":
		iVgsplot=min(range(len(cd.Vgs_IVfoc)), key=lambda i: abs(float(Vgs)-cd.Vgs_IVfoc[i][0]))          # find index of measured Vgs closest to that specified

	if len(cd.IdIV_foc())>0:
		axsub=figure.add_subplot(1,1,1)
		axsub.tick_params(axis='x',labelsize=axisfont)
		axsub.tick_params(axis='y',labelsize=axisfont)
		axsub.set_xlabel("Vds (V)",fontsize=axislablesfont)
		if cd.devwidth!=None and cd.devwidth>0.: axsub.set_ylabel("Drain Current (mA/mm)",fontsize=axislablesfont)

		else: axsub.set_ylabel("Drain Current (A)",fontsize=axislablesfont)
		if xmin == None: xmin = min([min(V) for V in cd.VdsIV_foc()])		# if not specified, chose the minimum of all gate voltages in the family of curves
		if xmax == None: xmax = max([max(V) for V in cd.VdsIV_foc()])		# if not specified, chose the maximum of all gate voltages in the family of curves
		axsub.set_xlim([xmin, xmax])
		if Vgs.lower()=='all': # plot all Vgs curves
			if ymin == None: ymin = min([min(I) for I in cd.IdIV_foc()])  # if not specified, chose the minimum of all gate voltages in the family of curves
			if ymax == None: ymax = max([max(I) for I in cd.IdIV_foc()])  # if not specified, chose the maximum of all gate voltages in the family of curves
		else:
			if ymin == None: ymin = min(cd.Id_IVfoc[iVgsplot])  # if not specified, chose the minimum of all gate voltages in the family of curves
			if ymax == None: ymax = max(cd.Id_IVfoc[iVgsplot])  # if not specified, chose the maximum of all gate voltages in the family of curves

		if max(abs(ymin),abs(ymax))<=1: axsub.yaxis.set_major_formatter(FormatStrFormatter('%5.1E'))
		if max(abs(ymin),abs(ymax))>1: axsub.yaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
		if max(abs(ymin),abs(ymax))>10: axsub.yaxis.set_major_formatter(FormatStrFormatter('%d'))

		axsub.set_ylim([ymin, ymax])
		if Vgs.lower()=='all':       #plot all Vgs curves
			for ii in range(0,len(cd.IdIV_foc())):
				axsub.plot(cd.VdsIV_foc()[ii],cd.IdIV_foc()[ii])
				if  cd.IdRonlin_foc()!=None and plotlin==True:		# plot the least-squares fit lines on the IV plots
					axsub.plot(cd.VdsIV_foc()[ii],cd.IdRonlin_foc()[ii],color='black')
		else:
			axsub.plot(cd.VdsIV_foc()[iVgsplot],cd.IdIV_foc()[iVgsplot])
			if  cd.IdRonlin_foc()!=None and plotlin==True:		# plot the least-squares fit lines on the IV plots
				axsub.plot(cd.VdsIV_foc()[iVgsplot],cd.IdRonlin_foc()[iVgsplot],color='black')

		axsub.set_title("Family of Curves",fontsize=titlefont)
		#plt.legend(ncol=1,bbox_to_anchor=(.6,0.28),borderaxespad=0,fontsize=legendfont)
		#plt.annotate('max gm '+str('{:5.1E}'.format(cd.gmmax_T())),xy=(xyannote),xycoords='axes fraction',fontsize=annotefont)
		axsub.grid(True)
		#axsub.hold(False)
		#axsub.clear()
		#plt.show()
		canvas.draw()
	else:						# pop up message to user to warn of missing data
		m=QtWidgets.QMessageBox()
		m.setText("".join(['Cannot plot IV data because they do not exist for device ',cd.get_devicename()]))
		m.exec_()
		del m
		#figure.delaxes(axsub)
	#####################################################################################################################
#####################################################################################################################
	# plot spectrum
####################################################################################################################
def plotspectrum(freq,spectrum,tit):
	axislablesfont = 10
	axisfont = 12
	titlefont = 12
	legendfont=12
	annotefont=12
	figuretitlefont=15
	linew1=10.
	linew2=5.
	linew3=3.
	linew4=2.


	figrow = 1
	figcol = 1
	# now let's plot the data
	figure=plt.figure(100,figsize=(10,10))
	#axsub=plt.subplot(figrow,figcol,1)
	axsub=figure.add_subplot(1,1,1)
	#axsub.set_yticklabel_format(style='sci',scilimits=(1,1))
	axsub.xaxis.set_major_formatter(FormatStrFormatter('%10.5f'))
	axsub.yaxis.set_major_formatter(FormatStrFormatter('%10.2f'))
	axsub.tick_params(axis='x',labelsize=axisfont)
	axsub.tick_params(axis='y',labelsize=axisfont)
	plt.xlabel("frequency GHz)",fontsize=axislablesfont)
	plt.ylabel("dBm",fontsize=axislablesfont)
	axsub.plot(freq/1E9,spectrum)
	plt.title(tit,fontsize=titlefont)
	plt.grid(True)
		# #plt.show()
		# canvas.draw()
		# figure.delaxes(axsub)
	plt.show()
	#plt.pause(0.0001)
	#time.sleep(10)

#####################################################################################################################
	# plot third order intercept points
####################################################################################################################
# Inputs:
# pfund is the fundamental power array - list of fundamental powers (input two-tone power of each tone)
# ptoiL is the array of the measured lower 3rd order distortion tone
# pinln is the fundamental power array extrapolated over a linear fit of the third order plot
# ptoiLlin is the linear fit and extrapolation of the lower 3rd order product
# ptoiH is the array of the measured upper frequency 3rd order distortion tone
def plotTOI(pfund_in=None,pfund_out=None, ptoiL=None, ptoiH=None, noisefloor=None, gain=None, ml=None, bl=None, mh=None, bh=None,mpout=None, canvas=None, figure=None, plotfundmin=None, plotfundmax=None):
	wm = plt.get_current_fig_manager()
	#wm.window.attributes('-topmost',1)
	wm.window.activateWindow()
	wm.window.raise_()
	axislablesfont = 10
	axisfont = 12
	titlefont = 12
	legendfont=12
	annotefont=12
	figuretitlefont=15
	linew1=10.
	linew2=5.
	linew3=3.
	linew4=2.
	minx=noisefloor-3.
	if plotfundmax!=None and  plotfundmax>plotfundmin:        # then set minimum and maximum levels as specified by calling method
		minx=plotfundmin
		maxx=plotfundmax
	else:
		minx=min(pfund_in)
		maxx=max(pfund_in)

	yticks = np.arange(-140,40,10)
	#plt.suptitle(cd.get_devicename()+"\nLocation: X "+str(cd.x())+" um    Y "+str(cd.y())+" um",fontsize=figuretitlefont)
	# now let's plot the data
	plt.clf()
	if figure!=None:
		figure.clear()
	else:
		figure=plt.figure(1,figsize=(10,10))
	axTOIL=figure.add_subplot(1,2,1)
	axTOIL.xaxis.set_major_formatter(FormatStrFormatter('%3.0f'))
	axTOIL.yaxis.set_major_formatter(FormatStrFormatter('%3.0f'))
	axTOIL.tick_params(axis='x',labelsize=axisfont)
	axTOIL.tick_params(axis='y',labelsize=axisfont)
	axTOIL.yaxis.set_ticks(yticks)
	plt.xlabel("fundamental DUT input power dBm)",fontsize=axislablesfont)
	plt.ylabel("DUT output power dBm",fontsize=axislablesfont)
	axTOIL.set_title("Lower Frequency 3rd Order Output Intercept",fontsize=titlefont)
	axTOIL.scatter(pfund_in, ptoiL)
	axTOIL.scatter(pfund_in, pfund_out)
	axTOIL.plot([minx,maxx],[ml*minx+bl,ml*maxx+bl],linewidth=linew4,color='red')                    # third order products linear fit
	axTOIL.plot([minx,maxx],[mpout*minx+gain,mpout*maxx+gain],linewidth=linew4,color='black')   							# fundamental line
	axTOIL.plot([minx,maxx],[noisefloor,noisefloor],linewidth=linew4,color='green')    						# plot the noise floor
	plt.grid(True)
	axTOIL.annotate('DUT output noise floor', xy=(pfund_out[0], noisefloor), xycoords='data', fontsize=annotefont)

	axTOIH=figure.add_subplot(1,2,2)
	axTOIH.xaxis.set_major_formatter(FormatStrFormatter('%3.0f'))
	axTOIH.yaxis.set_major_formatter(FormatStrFormatter('%3.0f'))
	axTOIH.tick_params(axis='x',labelsize=axisfont)
	axTOIH.tick_params(axis='y',labelsize=axisfont)
	axTOIH.yaxis.set_ticks(yticks)
	axTOIH.set_xlabel("fundamental DUT input power dBm)",fontsize=axislablesfont)
	axTOIH.set_ylabel("DUT output power dBm",fontsize=axislablesfont)
	axTOIH.set_title("Upper Frequency 3rd Order Output Intercept",fontsize=titlefont)
	axTOIH.scatter(pfund_in, ptoiH)
	axTOIH.scatter(pfund_in, pfund_out)
	axTOIH.plot([minx,maxx],[mh*minx+bh,mh*maxx+bh],linewidth=linew4,color='blue')       # third order products line
	axTOIH.plot([minx,maxx],[mpout*minx+gain,mpout*maxx+gain],linewidth=linew4,color='black')   							# fundamental line
	axTOIH.plot([minx,maxx],[noisefloor,noisefloor],linewidth=linew4,color='green')    						# plot the noise floor
	plt.grid(True)
	axTOIH.annotate('DUT output noise floor', xy=(pfund_out[0], noisefloor), xycoords='data', fontsize=annotefont)
	#
	# plt.title(tit,fontsize=titlefont)
	# plt.grid(True)
		# #plt.show()
		# canvas.draw()
		# figure.delaxes(axsub)
	if canvas==None:
		#plt.show()
		plt.draw()
		plt.pause(0.0001)
	else:
		# axTOIL.hold(False)
		# axTOIH.hold(False)
		#
		canvas.draw()
		axTOIL.clear()
		axTOIH.clear()
	#plt.draw()
	#plt.pause(0.0001)
	#plt.pause(0.0001)
	#time.sleep(10)

#####################################################################################################################
#####################################################################################################################
	# plot power compression characteristics
####################################################################################################################
# Inputs:
# pin is the DUT input power array
# pout is the DUT output power array
# gainm is the slope of the pout vs pin array to plot the least-squares linear fit - gainm should be very close to 1.
# gain is the DUT gain from the least squares linear fit of pout vs pin over the linear range of pin
def plotCompression(pin=None, pout=None, gain=None, gainm=None, inputcompression=None, outputcompression=None, xmin=None, xmax=None, canvas=None, figure=None):
	wm = plt.get_current_fig_manager()
	wm.window.activateWindow()
	#wm.window.attributes('-topmost',1)
	wm.window.raise_()
	axislablesfont = 10
	axisfont = 12
	titlefont = 12
	legendfont=12
	annotefont=12
	figuretitlefont=15
	linew1=10.
	linew2=5.
	linew3=3.
	linew4=2.
	if xmin==None or xmax==None:
		xmin=min(pin)
		xmax=max(pin)
	yticks = np.arange(-140,40,10)

	# now let's plot the data
	plt.clf()
	if figure!=None:
		figure.clear()
	else:
		figure=plt.figure(1,figsize=(10,10))
	axpow=figure.add_subplot(1,1,1)
	axpow.xaxis.set_major_formatter(FormatStrFormatter('%3.0f'))
	axpow.yaxis.set_major_formatter(FormatStrFormatter('%3.0f'))
	axpow.tick_params(axis='x',labelsize=axisfont)
	axpow.tick_params(axis='y',labelsize=axisfont)
	axpow.yaxis.set_ticks(yticks)
	plt.xlabel("Input power dBm)",fontsize=axislablesfont)
	plt.ylabel("Output power dBm",fontsize=axislablesfont)
	if inputcompression!=None and outputcompression!=None: axpow.set_title("Power Compression input "+formatnum(inputcompression,precision=1)+' dBm '+"output "+formatnum(outputcompression,precision=1)+' dBm',fontsize=titlefont)
	else:	axpow.set_title("Power Compression ",fontsize=titlefont)
	axpow.scatter(pin, pout)
	axpow.plot(pin,pout,linewidth=linew4,color='blue')                    # power output linear fit
	axpow.plot([xmin,xmax],[xmin+gain,xmax+gain],linewidth=linew4,color='red')                    # power output linear fit
	plt.grid(True)

	if canvas==None:
		#plt.show()
		plt.draw()
		plt.pause(0.0001)
	else:
		#axpow.hold(False)

		canvas.draw()
		axpow.clear()
	#plt.draw()
	#plt.pause(0.0001)
	#plt.pause(0.0001)
	#time.sleep(10)

#####################################################################################################################
#####################################################################################################################
	# plot TLM resistance fits vs sheet length
####################################################################################################################
# Inputs:
#
def plotTLM(cd=None,canvas=None,figure=None,xmin=None,xmax=None,ymin=None,ymax=None):
	haveTLMdata=True							# do we have TLM data for this device?
	if cd==None: raise ValueError("ERROR! no device given")
	if cd.Rc_TLM==None:
		print("ERROR no TLM data for device ",cd.devicename)
		haveTLMdata=False
		plt.clf()
		figure.clear()
		#axTLM.hold(False)
		canvas.draw()
		return False
		#raise ValueError("ERROR! no TLM data for this device")
	if canvas==None: raise ValueError("ERROR! no canvas given")
	if figure==None: raise ValueError("ERROR! no figure given")
	print("from line 751 in IVplot.py device name",cd.devicename,cd.get_devicename())

	axislablesfont = 16
	axisfont = 18
	titlefont = 20
	legendfont=12
	annotefont=12
	figuretitlefont=15
	linew1=10.
	linew2=5.
	linew3=3.
	linew4=2.

	# find linear fit line cd.Rsh_TLM is in ohms/sq and cd.Rc_TLM is in ohm*mm if cd.devwidth is specified otherwise it's just ohms.
	if cd.Rsh_TLM!=None:
		if cd.devwidth!=None and cd.devwidth>0: m=cd.Rsh_TLM/1000.				# since the device width was specified, set the sheet resistance to ohm*mm/um to plot with consistant units
		else: m=cd.Rsh_TLM
		b=2.*cd.Rc_TLM
		TLMfitlen=np.linspace(0.,1.1*max(cd.TLMlengths),5)
		TLMfitRon=[m*x+b for x in TLMfitlen]
	else:
		plt.clf()
		figure.clear()
		canvas.draw()
		return False

	#tit = str('{:5.1f}'.format(RTLM['Vgs'][iVgs]))
	#print(tit)	#debug
	#yticks = np.arange(0,max(RTLM['R'][iVgs]),1.E6)
	#plt.suptitle(cd.get_devicename()+"\nLocation: X "+str(cd.x())+" um    Y "+str(cd.y())+" um",fontsize=figuretitlefont)
	# now let's plot the data
	plt.clf()
	figure.clear()
	#figure.suptitle("Wafer "+wafername+"   TLM device "+sitename)
	axTLM=figure.add_subplot(1,1,1)

	if xmin==None: xmin=0.
	if xmax==None: xmax=max(TLMfitlen)
	axTLM.set_xlim([xmin,xmax])

	if ymin==None: ymin=min(cd.TLM_Ron)
	if ymax==None: ymax=max(TLMfitRon)
	axTLM.set_ylim([ymin,ymax])

	axTLM.xaxis.set_major_formatter(FormatStrFormatter('%3.2f'))
	axTLM.yaxis.set_major_formatter(FormatStrFormatter('%3.1E'))
	axTLM.tick_params(axis='x',labelsize=axisfont)
	axTLM.tick_params(axis='y',labelsize=axisfont)
	axTLM.set_xlabel("TLM length um",fontsize=axislablesfont)
	if cd.devwidth!=None and cd.devwidth>0: axTLM.set_ylabel("resistance ohm*mm",fontsize=axislablesfont)
	else: axTLM.set_ylabel("resistance ohms",fontsize=axislablesfont)

	axTLM.scatter(cd.TLMlengths,cd.TLM_Ron,color='red')
	axTLM.plot(TLMfitlen,TLMfitRon,linewidth=linew4,color='black')                    # linear fit
	if haveTLMdata: axTLM.set_title("TLM Ron vs TLM length",fontsize=titlefont)
	else:	axTLM.set_title("WARNING: No TLM Data - Stale Plot!",fontsize=titlefont)
	axTLM.grid(True)
	#axTLM.annotate('noise floor',xy=(min(pinln),noisefloor),xycoords='data',fontsize=annotefont)
	#
	#plt.title('Vgs = '+tit+' V',fontsize=titlefont)

	#if plottype=='canvas':		# then this a a canvas plot within wafermap

	canvas.draw()
	#axTLM.clear()
	#figure.delaxes(axTLM)

	#####################################################################################################################
#####################################################################################################################
	# plot Ron Gon histogram
####################################################################################################################
# Inputs:
# Vgsarray[iVg] is the array of gate voltages
# binmin[ib], binmax[ib] are respectively the minimum and maximum Ron values represented in the bin at bin index ib
# Rhist is the array of contact resistances or conductances to be plotted it is indexed: Rhist[iVgs][ib][idev]
# where iVgs is the gate voltage index, ib is the bin index,
# Vgs is the selected gate voltage to plot i.e. the gate voltage is selected from Vgsarray
# figurecanvas is the figure pointer sent when we are embedding the plot in a wafermap canvas
# canvas is the canvas pointer sent when we are embedding the plot in a wafermap canvas

def plothistRon(binmin=None,binmax=None,datahist=None,figurecanvas=None,canvas=None,xlabel=None,highlightbarindex=None,clearplot=None,logplot=False):
	if canvas!=None and figurecanvas !=None:
		plottype='canvas'
		figure=figurecanvas
		#plt.close(figure)
	else:
		plottype='standalone'
		wm = plt.get_current_fig_manager()
		wm.window.attributes('-topmost',1)
		figure=plt.figure(1,figsize=(10,10))

	# axislablesfont = 20
	# axisfonty = 25
	axislablesfont = 16
	axisfonty = 14
	# titlefont =20
	# legendfont=12
	# annotefont=12
	# figuretitlefont=18
	# linew1=10.
	# linew2=5.
	# linew3=3.
	# linew4=2.

	#tit = str('{:5.1f}'.format(Vgsarray[iVgs]))
	# now let's plot the data
	plt.clf()
	figure.clear()
	#figure.suptitle("Wafer "+wafername+"   TLM device "+sitename)
	ax=figure.add_subplot(1,1,1)
	ax.clear()
	if clearplot==True:		# clear the plot on request
		ax.clear()
		canvas.draw()
		return

	if logplot:
		ax.set_xscale('log')
		ax.xaxis.set_major_formatter(FormatStrFormatter('%3.0E'))
		axisfontx=14
	else:
		ax.set_xscale('linear')
		formatter=mpl.ticker.ScalarFormatter(useMathText=True)
		formatter.set_scientific(True)
		formatter.set_powerlimits((-3,3))
		ax.xaxis.set_major_formatter(formatter)
		#ax.xaxis.set_major_formatter(mpl.ticker.ScalarFormatter(useMathText=True))
		axisfontx=14
	#
	#ax.yaxis.set_major_formatter(mpl.ticker.ScalarFormatter(useMathText=True, useOffset=False))
	ax.yaxis.set_major_formatter(FormatStrFormatter('%3.0f'))
	ax.tick_params(axis='x',labelsize=axisfontx)
	ax.tick_params(axis='y',labelsize=axisfonty)

	if xlabel!=None: ax.set_xlabel(xlabel,fontsize=axislablesfont)
	ax.set_ylabel("Device percentage %",fontsize=axislablesfont)

	binsize = [binmax[i]-binmin[i] for i in range(0,len(binmax))]
	Rnum = [len(p) for p in datahist]		# Rnum[ib] is the number for each bin indexed by ib
	if abs(sum(Rnum))>1E-40:
		Rper = [100.*float(p)/float(sum(Rnum)) for p in Rnum]
	else:
		Rper=[0. for p in Rnum]
	##debug
	# sump=0.
	# for p in Rnum:
	# 	print(p)
	# 	sump+=p
	# print("sum p",sump)
	#print("mean",Rhist[iVgs])
	####

	bars=ax.bar(binmin,Rper,binsize,color='black',)
	#print("bars",bars)
	if highlightbarindex != None and highlightbarindex>=0 and highlightbarindex<len(binmin):
		ax.bar(binmin[highlightbarindex],Rper[highlightbarindex],binsize[highlightbarindex],color='black',edgecolor='red',zorder=20)
	ax.grid(True)
	if plottype=='canvas':		# then this a a canvas plot within wafermap
		#ax.hold(False)
		canvas.draw()
		#figure.delaxes(ax)
		return bars			# so that we can retrieve location of mouse on a bar
	else: plt.show()
#####################################################################################################################
# plot forward or forward + reverse transfer curves
## Id single and double sweep
def plot_transfer(cd,figure=None,canvas=None,removeleakage=True, single_double='single',logplot=False,plotsplinefit=False,legendon=True,plotIg=False,xmin=None,xmax=None,ymin=None,ymax=None):
	axislablesfont = 18
	axisfont = 18
	titlefont = 20
	legendfont=12
	annotefont=12
	figuretitlefont=15
	linew1=10.
	linew2=5.
	linew3=3.
	linew4=2.
	xyannote=[.5,0.95]
	minVgs_T=9999999999
	maxVgs_T=-9999999999
	minVgs_TF=minVgs_T
	maxVgs_TF=maxVgs_T
	minVgs_TF=minVgs_T
	maxVgs_TF=maxVgs_T
	minVgs_T3=minVgs_T
	maxVgs_T3=maxVgs_T
	minVgs_T4=minVgs_T
	maxVgs_T4=maxVgs_T

	figrow = 1
	figcol = 1
	plt.clf()
	figure.clear()
	if ((hasattr(cd,'Id_T') and len(cd.Id_T())>0) or (hasattr(cd,'Id_TF') and len(cd.Id_TF())>0)) and figure!=None and canvas !=None:
		ax=figure.add_subplot(1,1,1)
		ax.xaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
		ax.yaxis.set_major_formatter(FormatStrFormatter('%5.1E'))
		ax.set_xlabel("Gate Voltage (V)",fontsize=axislablesfont)
		if cd.devwidth!=None and cd.devwidth>0.: ax.set_ylabel("Drain Current (mA/mm)",fontsize=axislablesfont)
		else: ax.set_ylabel("Drain Current (A)",fontsize=axislablesfont)
		ax.tick_params(axis='x',labelsize=axisfont)
		ax.tick_params(axis='y',labelsize=axisfont)
		if logplot: ax.set_yscale('log')
		#else: ax.set_yscale('linear')


		if single_double=='single':						# single transfer curve plot
			if xmin==None: xmin_ = min(cd.Vgs_T())
			else: xmin_=xmin
			if xmax==None: xmax_ = max(cd.Vgs_T())
			else: xmax_=xmax
			ax.set_xlim([xmin_, xmax_])
			if np.average(np.diff(cd.Vgs_IVt))>=0.: linestyle='dashed'      # positive-going Vgs
			else:   linestyle='solid'       # negative-going Vgs
			if removeleakage==True:		# remove leakage current from plots?
				if not logplot:
					if ymin==None: ymin_=min(np.subtract(cd.Id_T(), cd.Idleak_T()['I']))
					else: ymin_=ymin
					if ymax==None: ymax_=max(np.subtract(cd.Id_T(), cd.Idleak_T()['I']))
					else: ymax_=ymax
					ax.set_ylim([ymin_, ymax_])
					ax.set_yscale('linear')
					ax.plot(cd.Vgs_T(),cd.Id_T()-cd.Idleak_T()['I'],label="measured",linewidth=linew4,color='black',zorder=30,linestyle=linestyle)
					if plotsplinefit: ax.plot(cd.Idfit_T()['Vgs'],cd.Idfit_T()['I']-cd.Idleak_T()['I'],label="fit",linewidth=linew1,color='red',zorder=1)
				else:
					if ymin == None: ymin_ = min(np.abs(np.subtract(cd.Id_T(),cd.Idleak_T()['I'])))
					else: ymin_ = ymin
					if ymax == None: ymax_ = max(np.abs(np.subtract(cd.Id_T(),cd.Idleak_T()['I'])))
					else: ymax_ = ymax
					ax.set_ylim([ymin_, ymax_])
					ax.set_yscale('log')
					ax.plot(cd.Vgs_T(),np.abs(cd.Id_T()-cd.Idleak_T()['I']),label="measured",linewidth=linew4,color='black',zorder=30,linestyle=linestyle)
					if plotsplinefit: ax.plot(cd.Idfit_T()['Vgs'],np.abs(np.subtract(cd.Idfit_T()['I'],cd.Idleak_T()['I'])),label="fit",linewidth=linew1,color='red',zorder=1)
			elif removeleakage==False:
				if not logplot:
					if ymin==None:
						if plotIg: ymin_=min([min(cd.Id_T()),min(cd.Ig_T())])
						else: ymin_=min(cd.Id_T())
					else: ymin_=ymin
					if ymax==None:
						if plotIg: ymax_=max([max(cd.Id_T()),max(cd.Ig_T())])
						else: ymax_=max(cd.Id_T())
					else: ymax_=ymax
					ax.set_ylim([ymin_, ymax_])
					ax.set_yscale('linear')
					ax.plot(cd.Vgs_T(),cd.Id_T(),label="measured Id",linewidth=linew4,color='black',zorder=30,linestyle=linestyle)
					if plotsplinefit: ax.plot(cd.Idfit_T()['Vgs'],cd.Idfit_T()['I'],label="fit",linewidth=linew1,color='red',zorder=1)              # also plot the spline fit if requested
					if plotIg: ax.plot(cd.Vgs_T(),cd.Ig_T(),label='measured Ig',linewidth=linew4,color='blue',zorder=2)                             # plot gate current vs Vgs if requested
					#ax.plot(cd.Idlin_T()['Vgs'],cd.Idlin_T()['I'],label="linear fit",linewidth=linew3,color='green',zorder=2)
				else:
					print("from line 997 in IVplot.py plotIg=",plotIg, min([min(np.abs(cd.Id_T())),min(np.abs(cd.Ig_T()))]))
					if ymin==None:
						if plotIg: ymin_=min(min(np.abs(cd.Id_T())),min(np.abs(cd.Ig_T())))
						else: ymin_=min(np.abs(cd.Id_T()))
					else: ymin_=ymin
					if ymax==None:
						if plotIg: ymax_=max([max(np.abs(cd.Id_T())),max(np.abs(cd.Ig_T()))])
						else: ymax_=max(np.abs(cd.Id_T()))
					else: ymax_=ymax
					ax.set_ylim([ymin_, ymax_])
					ax.set_yscale('log')
					ax.plot(cd.Vgs_T(),np.abs(cd.Id_T()),label="measured Id",linewidth=linew4,color='black',zorder=30,linestyle=linestyle)
					if plotsplinefit: ax.plot(cd.Idfit_T()['Vgs'],np.abs(cd.Idfit_T()['I']),label="fit",linewidth=linew1,color='red',zorder=1)
					if plotIg: ax.plot(cd.Vgs_T(),np.abs(cd.Ig_T()),label='measured Ig',linewidth=linew4,color='blue',zorder=2)                             # plot gate current vs Vgs if requested
			else:
				raise ValueError("ERROR! illegal parameter specification for removeleakage which must be True or False")

			ax.set_title("Single-Swept Id Vds="+str('{:5.2f}'.format(cd.Vds_T(),fontsize=titlefont))+" V")

		elif single_double=='double' and len(cd.Vgs_TF())>0 and len(cd.Vgs_TR())>0 and len(cd.Id_TF())>0 and len(cd.Id_TR())>0:		# this is a double plot (forward and reverse swept) Leakage current is NOT ever removed in this mode
			if len(cd.Vgs_TF())>0:				# then we have no single-swept curve
				minVgs_TF=1E30
				maxVgs_TF=-1E30
			else:
				minVgs_TF=min(cd.Vgs_TF())
				maxVgs_TF=max(cd.Vgs_TF())

			if xmin == None: xmin_ = min(minVgs_TF, min(cd.Vgs_TF()))
			else: xmin_ = xmin
			if xmax == None: xmax_ = max(maxVgs_TF, max(cd.Vgs_TF()))
			else:xmax_ = xmax

			ax.set_xlim([xmin_, xmax_])
			if not logplot:
				# forward (sweep 1) and reverse (sweep 2)
				if ymin==None:
					if plotIg: ymin_=min([min(cd.Id_TF()),min(cd.Id_TR()),min(cd.Ig_TF()),min(cd.Ig_TR())])
					else: ymin_=min(min(cd.Id_TF()),min(cd.Id_TR()))
				else: ymin_=ymin
				if ymax == None:
					if plotIg: ymax_ = max([max(cd.Id_TF()),max(cd.Id_TR()),max(cd.Ig_TF()),max(cd.Ig_TR())])
					else: ymax_ = max(max(cd.Id_TF()), max(cd.Id_TR()))
				else: ymax_=ymax
				ax.set_ylim([ymin_, ymax_])
				print("from line 1041 in IVploy.py ymin_ ymax_",ymin_,ymax_)
				ax.set_yscale('linear')
				if np.average(np.diff(cd.Vgs_IVtf))>=0: linestyle='dashed'  # negative-going Vgs
				else: linestyle='solid' # positive-going Vgs
				ax.plot(cd.Vgs_TF(),cd.Id_TF(),label="Id 1st sweep",linewidth=linew3,color='darkred',zorder=30,linestyle=linestyle)	# first curve

				if plotsplinefit: ax.plot(cd.Idfit_TF()['Vgs'],cd.Idfit_TF()['I'],label="Id 1stfit",linewidth=linew1,color='lightgreen',zorder=1)
				if plotIg: ax.plot(cd.Vgs_TF(),cd.Ig_TF(),label='Ig 1st sweep',linewidth=linew4,color='orange',zorder=2)                             # plot gate current vs Vgs if requested

				if np.average(np.diff(cd.Vgs_IVtr))>=0: linestyle='dashed'        # positive-going Vgs
				else: linestyle='solid'
				ax.plot(cd.Vgs_TR(), cd.Id_TR(), label="Id 2nd sweep", linewidth=linew3, color='darkblue', zorder=30, linestyle=linestyle)  # 2nd curve Vgs swept positive direction
				if plotsplinefit: ax.plot(cd.Idfit_TR()['Vgs'], cd.Idfit_TR()['I'], label="Id 2ndfit", linewidth=linew1, color='lightgreen', zorder=1)
				if plotIg: ax.plot(cd.Vgs_TR(),cd.Ig_TR(),label='Ig 2nd sweep',linewidth=linew4,color='lightblue',zorder=2)                             # plot gate current vs Vgs if requested

				ax.set_title("Dual Swept Id Vds=" + str('{:5.2f}'.format(cd.Vds_TF(), fontsize=titlefont)) + " V")
				# If we have a four-sweep transfer curve then plot the following:
				if len(cd.Id_T3())>0 and len(cd.Id_T4())>0:
					if xmin==None: xmin_= min(minVgs_T,min(cd.Vgs_TF()),min(cd.Vgs_T3()),min(cd.Vgs_T4()))
					if xmax==None: xmax_ = max(maxVgs_T, max(cd.Vgs_TF()), max(cd.Vgs_T3()), max(cd.Vgs_T4()))
					ax.set_xlim([xmin_, xmax_])
					if ymin == None: ymin_ = min(ymin_,min(cd.Id_T3()), min(cd.Id_T4()))
					else: ymin_ = ymin
					if ymax==None: ymax_ = max(ymax_,max(cd.Id_T3()), max(cd.Id_T4()))
					else: ymax_=ymax
					#TODO fix y scaliing
					ax.set_ylim([ymin_, ymax_])
					ax.set_yscale('linear')
					if np.average(np.diff(cd.Vgs_IVt3))>=0: linestyle='dashed'  # positive-going Vgs
					else: linestyle='solid' # negative-going Vgs
					ax.plot(cd.Vgs_T3(), cd.Id_T3(), label="3rd sweep", linewidth=linew4, color='red', zorder=30, linestyle=linestyle)  # 3rd curve

					if plotsplinefit: ax.plot(cd.Idfit_T3()['Vgs'], cd.Idfit_T3()['I'], label="3rdfit", linewidth=linew1, color='lightgreen', zorder=1)

					if np.average(np.diff(cd.Vgs_IVt4))>=0: linestyle='dashed'  # positive-going Vgs
					else: linestyle='solid' # negative-going Vgs
					ax.plot(cd.Vgs_T4(), cd.Id_T4(), label="4th sweep", linewidth=linew4, color='magenta', zorder=30, linestyle=linestyle)  # 4th curve
					if plotsplinefit: ax.plot(cd.Idfit_T4()['Vgs'], cd.Idfit_T4()['I'], label="4thfit", linewidth=linew1, color='lightgreen', zorder=1)
					ax.set_title("Four Swept Id Vds=" + str('{:5.2f}'.format(cd.Vds_TF(), fontsize=titlefont)) + " V")
			else:   # this is a log plot
				# forward (sweep 1) and reverse (sweep 2)
				if ymin == None:
					if plotIg: ymin_ = min(min(np.abs(cd.Id_TF())),min(np.abs(cd.Id_TR())),min(np.abs(cd.Ig_TF())),min(np.abs(cd.Ig_TR())))
					else: ymin_ = min(min(np.abs(cd.Id_TF())), min(np.abs(cd.Id_TR())))
				else: ymin_ = ymin
				if ymax == None:
					if plotIg: ymax_ = max(max(np.abs(cd.Id_TF())), max(np.abs(cd.Id_TR())),max(np.abs(cd.Ig_TF())),max(np.abs(cd.Ig_TR())))
					else: ymax_ = max(max(np.abs(cd.Id_TF())), max(np.abs(cd.Id_TR())))
				else: ymax_ = ymax
				ax.set_ylim([ymin_, ymax_])
				ax.set_yscale('log')
				if np.average(np.diff(cd.Vgs_IVtf))>=0: linestyle='dashed'  # positive-going Vgs sweep
				else: linestyle='solid' # negative-going Vgs sweep
				ax.plot(cd.Vgs_TF(),np.abs(cd.Id_TF()),label="1st sweep",linewidth=linew3,color='darkred',zorder=30, linestyle=linestyle)
				if plotsplinefit: ax.plot(cd.Idfit_TF()['Vgs'],np.abs(cd.Idfit_TF()['I']),label="1stfit",linewidth=linew1,color='lightgreen',zorder=1)
				if plotIg: ax.plot(cd.Vgs_TF(),np.abs(cd.Ig_TF()),label='Ig 1st sweep',linewidth=linew4,color='blue',zorder=2, linestyle=linestyle)                             # plot gate current vs Vgs if requested

				if np.average(np.diff(cd.Vgs_IVtr))>=0: linestyle='dashed'  # positive-going Vgs sweep
				else: linestyle='solid' # negative-going Vgs sweep
				ax.plot(cd.Vgs_TR(),np.abs(cd.Id_TR()),label="2nd sweep",linewidth=linew3,color='darkblue',zorder=30, linestyle=linestyle)
				if plotsplinefit: ax.plot(cd.Idfit_TR()['Vgs'],np.abs(cd.Idfit_TR()['I']),label="2ndfit",linewidth=linew1,color='lightgreen',zorder=1)
				if plotIg: ax.plot(cd.Vgs_TR(),np.abs(cd.Ig_TR()),label='Ig 2nd sweep',linewidth=linew4,color='blue',zorder=2, linestyle=linestyle)

				ax.set_title("Logscale Dual Swept Id Vds=" + str('{:5.2f}'.format(cd.Vds_TF(), fontsize=titlefont)) + " V")
				# If we have a four-sweep transfer curve then plot the following:
				if len(cd.Id_T3())>0 and len(cd.Id_T4())>0:
					if xmin == None: xmin_ = min(minVgs_T, min(cd.Vgs_TF()), min(cd.Vgs_T3()), min(cd.Vgs_T4()))
					if xmax == None: xmax_ = max(maxVgs_T, max(cd.Vgs_TF()), max(cd.Vgs_T3()), max(cd.Vgs_T4()))
					ax.set_xlim([xmin_, xmax_])
					if ymin == None: ymin_ = min(ymin_,min(np.abs(cd.Id_T3())), min(np.abs(cd.Id_T4())))
					else: ymin_ = ymin
					if ymax == None: ymax_ = max(ymax_,max(np.abs(cd.Id_T3())), max(np.abs(cd.Id_T4())))
					else: ymax_ = ymax
					ax.set_ylim([ymin_, ymax_])
					if np.average(np.diff(cd.Vgs_IVt3))>=0: linestyle='dashed'  # positive-going Vgs
					else: linestyle='solid' # negative-going Vgs
					ax.plot(cd.Vgs_T3(), np.abs(cd.Id_T3()), label="3rd sweep", linewidth=linew4, color='red', zorder=30, linestyle=linestyle)
					if plotsplinefit: ax.plot(cd.Idfit_T3()['Vgs'], np.abs(cd.Idfit_T3()['I']), label="3rdfit", linewidth=linew1, color='lightgreen', zorder=1)
					if np.average(np.diff(cd.Vgs_IVt4))>=0: linestyle='dashed'  # positive-going Vgs
					else: linestyle='solid' # negative-going Vgs
					ax.plot(cd.Vgs_T4(), np.abs(cd.Id_T4()), label="4th sweep", linewidth=linew4, color='magenta', zorder=30, linestyle=linestyle)
					if plotsplinefit: ax.plot(cd.Idfit_T4()['Vgs'], np.abs(cd.Idfit_T4()['I']), label="4thfit", linewidth=linew1, color='lightgreen', zorder=1)
					ax.set_title("Logscale Four Swept Id Vds="+str('{:5.2f}'.format(cd.Vds_TF(),fontsize=titlefont))+" V")

		elif single_double=='double' and (len(cd.Vgs_TF())>0 or len(cd.Vgs_TR())>0 or len(cd.Id_TF())>0 or len(cd.Id_TR())>0):
			ax.set_title("NO dual-swept transfer data")
		else:
			raise ValueError("ERROR! incorrect parameter specification for single_double which must be single or double")
		ax.grid(True)
	#plt.legend(ncol=1,bbox_to_anchor=(.98,.28),borderaxespad=0,fontsize=legendfont)
	#plt.annotate('max gm '+str('{:5.1E}'.format(cd.gmmax_T())),xy=(xyannote),xycoords='axes fraction',fontsize=annotefont)
	elif figure==None: raise ValueError("ERROR! No figure supplied")
	elif canvas==None: raise ValueError("ERROR! No canvas supplied")
	elif cd.Id_T()=='None': raise ValueError("ERROR! No transfer curve data supplied")
	if legendon:
		try: ax.legend(loc='lower right')
		except: pass
	if figure!=None and canvas!=None:
		#ax.clear()
		#
		canvas.draw()
		#ax.clear()
#####################################################################################################################
# plot forward or forward + reverse transconductance
## Id single and double sweep
def plot_gm(cd,figure=None,canvas=None, single_double='single',legendon=True,xmin=None,xmax=None,ymin=None,ymax=None):
	axislablesfont = 18
	axisfont = 18
	titlefont = 22
	legendfont=12
	annotefont=12
	figuretitlefont=15
	linew1=10.
	linew2=5.
	linew3=3.
	linew4=2.
	xyannote=[.5,0.95]

	figrow = 1
	figcol = 1
	plt.clf()
	figure.clear()

	if len(cd.Id_T())>0 and figure!=None and canvas !=None:
		ax=figure.add_subplot(1,1,1)
		ax.xaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
		#ax.yaxis.set_major_formatter(FormatStrFormatter('%5.1E'))
		ax.set_xlabel("Gate Voltage (V)",fontsize=axislablesfont)
		if cd.devwidth!=None and cd.devwidth>0.: ax.set_ylabel("Transconductance (mS/mm)",fontsize=axislablesfont)
		else: ax.set_ylabel("Transconductance (S)",fontsize=axislablesfont)
		ax.tick_params(axis='x',labelsize=axisfont)
		ax.tick_params(axis='y',labelsize=axisfont)
		if single_double=='single':						# single transfer curve plot
			if xmin == None: xmin = min(cd.gm_T()['Vgs'])
			if xmax == None: xmax = max(cd.gm_T()['Vgs'])
			if ymin == None: ymin = min(cd.gm_T()['G'])
			if ymax == None: ymax = max(cd.gm_T()['G'])
			if max(abs(ymin),abs(ymax))<=1: ax.yaxis.set_major_formatter(FormatStrFormatter('%5.1E'))
			if max(abs(ymin),abs(ymax))>1: ax.yaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
			if max(abs(ymin),abs(ymax))>10: ax.yaxis.set_major_formatter(FormatStrFormatter('%d'))
			ax.set_xlim([xmin, xmax])
			ax.set_ylim([ymin, ymax])
			ax.plot(cd.gm_T()['Vgs'],cd.gm_T()['G'],label="measured",linewidth=linew4,color='black',zorder=30)
			ax.set_title("Single-Swept Gm Vds="+str('{:5.1f}'.format(cd.Vds_T(),fontsize=titlefont))+" V")
		elif single_double=='double':		# this is a double plot (forward and reverse swept) Leakage current is NOT ever removed in this mode
			if xmin == None: xmin = min(min(cd.gm_TF()['Vgs']),min(cd.gm_TR()['Vgs']))
			if xmax == None: xmax = max(max(cd.gm_TF()['Vgs']),max(cd.gm_TR()['Vgs']))
			if ymin == None: ymin = min(min(cd.gm_TF()['G']), min(cd.gm_TR()['G']))
			if ymax == None: ymax = max(max(cd.gm_TF()['G']), max(cd.gm_TR()['G']))
			if max(abs(ymin),abs(ymax))<=1: ax.yaxis.set_major_formatter(FormatStrFormatter('%5.1E'))
			if max(abs(ymin),abs(ymax))>1: ax.yaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
			if max(abs(ymin),abs(ymax))>10: ax.yaxis.set_major_formatter(FormatStrFormatter('%d'))
			ax.set_xlim([xmin, xmax])
			ax.set_ylim([ymin, ymax])
			ax.plot(cd.gm_TF()['Vgs'],cd.gm_TF()['G'],label="1st sweep",linewidth=linew3,color='darkred')	# gm from 1st swept transfer curve
			ax.plot(cd.gm_TR()['Vgs'],cd.gm_TR()['G'],label="2nd sweep",linewidth=linew3,color='darkblue')	# gm from 2nd swept transfer curve
			ax.set_title("Dual Swept Gm (S) Vds=" + str('{:5.2f}'.format(cd.Vds_TF(), fontsize=titlefont)) + " V")
		elif single_double=='double' and len(cd.gm_T3())>0 and len(cd.gm_T4())>0:
			if xmin == None: xmin = min(min(cd.gm_TF()['Vgs']), min(cd.gm_TR()['Vgs']),min(cd.gm_T3()['Vgs']),min(cd.gm_T4()['Vgs']))
			if xmax == None: xmax = max(max(cd.gm_TF()['Vgs']), max(cd.gm_TR()['Vgs']),max(cd.gm_T3()['Vgs']),max(cd.gm_T4()['Vgs']))
			if ymin == None: ymin = min(min(cd.gm_TF()['G']), min(cd.gm_TR()['G']),min(cd.gm_T3()['G']), min(cd.gm_T3()['G']))
			if xmax == None: ymax = max(max(cd.gm_TF()['G']), max(cd.gm_TR()['G']),max(cd.gm_T3()['G']), max(cd.gm_T3()['G']))
			if max(abs(ymin),abs(ymax))<=1: ax.yaxis.set_major_formatter(FormatStrFormatter('%5.1E'))
			if max(abs(ymin),abs(ymax))>1: ax.yaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
			if max(abs(ymin),abs(ymax))>10: ax.yaxis.set_major_formatter(FormatStrFormatter('%d'))

			ax.set_xlim([xmin, xmax])
			ax.set_ylim([ymin, ymax])
			ax.plot(cd.gm_TF()['Vgs'], cd.gm_TF()['G'], label="1st sweep", linewidth=linew3, color='darkred')  # gm from 1st swept transfer curve
			ax.plot(cd.gm_TR()['Vgs'], cd.gm_TR()['G'], label="2nd sweep", linewidth=linew3, color='darkblue')  # gm from 2nd swept transfer curve
			ax.plot(cd.gm_T3()['Vgs'], cd.gm_T3()['G'], label="3rd sweep", linewidth=linew4, color='red')  # gm from 3rd swept transfer curve
			ax.plot(cd.gm_T4()['Vgs'], cd.gm_T4()['G'], label="4th sweep", linewidth=linew4, color='magenta')  # gm from 4th swept transfer curve
			ax.set_title("Four Swept Gm (S) Vds=" + str('{:5.2f}'.format(cd.Vds_T3(), fontsize=titlefont)) + " V")
		else:
			raise ValueError("ERROR! incorrect parameter specification for single_double which must be single or double")
		ax.grid(True)
	#plt.legend(ncol=1,bbox_to_anchor=(.98,.28),borderaxespad=0,fontsize=legendfont)
	#plt.annotate('max gm '+str('{:5.1E}'.format(cd.gmmax_T())),xy=(xyannote),xycoords='axes fraction',fontsize=annotefont)
	elif figure==None: raise ValueError("ERROR! No figure supplied")
	elif canvas!=None: raise ValueError("ERROR! No canvas supplied")
	elif cd.gm_T()=='None': raise ValueError("ERROR! No gm data supplied")
	if legendon: ax.legend(loc='upper right')
	if figure!=None and canvas!=None:
		#ax.clear()
		canvas.draw()
#####################################################################################################################
# plot unilateral power gain derived from measured S-parameters
#	The frequency axis is log and we plot only dB data
# def plot_Umax(cd,figure=None,canvas=None,xmin=None,xmax=None,ymin=None,ymax=None,plotextrapolation=True):
# 	if figure==None: raise ValueError("ERROR! No figure supplied")
# 	elif canvas==None: raise ValueError("ERROR! No canvas supplied")
# 	elif not hasattr(cd,"UMAX"): raise ValueError("ERROR! No UMAX data supplied")
# 	axislablesfont = 12
# 	axisfont = 12
# 	titlefont = 12
# 	legendfont=12
# 	annotefont=12
# 	figuretitlefont=15
# 	linew1=10.
# 	linew2=5.
# 	linew3=3.
# 	linew4=2.
# 	xyannote=[.5,0.95]
#
# 	figrow = 1
# 	figcol = 1
# 	plt.clf()
# 	figure.clear()
#
# 	ax=figure.add_subplot(1,1,1)
# 	ax.set_xscale('log')					# log frequency axis
# 	ax.xaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
# 	ax.yaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
# 	ax.set_xlabel("Frequency GHz",fontsize=axislablesfont)
# 	ax.set_ylabel("Unilateral Gain dB",fontsize=axislablesfont)
# 	ax.tick_params(axis='x',labelsize=axisfont)
# 	ax.tick_params(axis='y',labelsize=axisfont)
# 	maxfreq=max(cd.freq)
# 	minfreq=min(cd.freq)
# 	if xmin!=None and xmax!=None:
# 		ax.set_xlim([xmin,xmax])
# 		minfreq=xmin
# 		maxfreq=xmax
# 	if ymin!=None and ymax!=None:
# 		ax.set_ylim([ymin,ymax])
# 	ax.plot(cd.freq/1.E9,10.*np.log10(cd.UMAX),label="measured",linewidth=linew4,color='black',zorder=30)
# 	if plotextrapolation:
# 		UMAX=[np.log10(cd.UMAX_fmaxextrapolation()['m']*minfreq+cd.UMAX_fmaxextrapolation()['b']),np.log10(cd.UMAX_fmaxextrapolation()['m']*maxfreq+cd.UMAX_fmaxextrapolation()['b'])]
# 		ax.plot([minfreq/1.E9,maxfreq/1.E9],UMAX,label="measured",linewidth=linew4,color='red',zorder=30)
#
# 	ax.set_title("Unilateral Power Gain Vds= "+formatnum(cd.Vds_Spar(),precision=1)+" V "+"Id= "+formatnum(cd.Id_Spar(),precision=2)+" A",fontsize=titlefont)
#
# 	ax.grid(True)
# 	ax.hold(False)
# 	canvas.draw()
#####################################################################################################################
#####################################################################################################################
# dB magnitude plots of the measured two-port parameters
#	The frequency axis is log and we plot only dB data. Frequency is input in Hz
# type is a keyword which includes S11, S21, S12, S22 to indicate which set of S-parameters to plot
# when supplied, cd.devwidth is the total device gate width in mm
def plot_twoportparameters_dB(cd,figure=None,canvas=None,xmin=None,xmax=None,ymin=None,ymax=None,type=None,ft_extrapolation=True,fmax_extrapolation=True):
	if figure==None: raise ValueError("ERROR! No figure supplied")
	elif canvas==None: raise ValueError("ERROR! No canvas supplied")
	elif not hasattr(cd,"s21"): raise ValueError("ERROR! No S-parameter data supplied")
	elif not type.lower() in ['s11db','s21db','s12db','s22db','h11db','h21db','h12db','h22db','umaxdb','gmaxdb']: raise ValueError("ERROR! need to specify type of plot")
	#or "h12" in type.lower() or "h21" in type.lower() or "h22" in type.lower():
	axislablesfont = 18
	axisfont = 18
	titlefont = 22
	legendfont=12
	annotefont=12
	figuretitlefont=15
	linew1=10.
	linew2=5.
	linew3=3.
	linew4=4.
	xyannote=[.5,0.95]

	figrow = 1
	figcol = 1
	plt.clf()
	figure.clear()

	ax=figure.add_subplot(1,1,1)
	ax.set_xscale('log')					# log frequency axis
	ax.xaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
	ax.yaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
	ax.set_xlabel("Frequency GHz",fontsize=axislablesfont)
	ax.set_ylabel("dB",fontsize=axislablesfont)
	ax.tick_params(axis='x',labelsize=axisfont)
	ax.tick_params(axis='y',labelsize=axisfont)
	fscale=1.E9					# GHz
	freq=[f/fscale for f in cd.freq]				# convert frequencies to GHz scale
	maxfreq=max(freq)
	minfreq=min(freq)
	if xmin==None:
		xmin=minfreq
	else: xmin*=1.E-9
	if xmax==None:
		xmax=maxfreq
	else: xmax*=1.E-9
	############ dB S-parameters
	if "s11db" in type.lower():		# plot S11dB note that Spar('s11db') returns a complex number with the real part as |S11| dB and the imaginary as the phase in degrees of S11 the same is true for all the S-parameters dB data
		paratitle='S11'
		if ymin==None: ymin=min(np.real(cd.Spar('s11db')))
		if ymax==None: ymax=max(np.real(cd.Spar('s11db')))
		ax.plot(freq,np.real(cd.Spar('s11db')),label=paratitle,linewidth=linew4,zorder=30)
	if "s21db" in type.lower():		# plot H21
		paratitle='S21'
		if ymin==None: ymin=min(np.real(cd.Spar('s21db')))
		if ymax==None: ymax=max(np.real(cd.Spar('s21db')))
		ax.plot(freq,np.real(cd.Spar('s21db')),label=paratitle,linewidth=linew4,zorder=30)
	if "s12db" in type.lower():		# plot H12
		paratitle='S12'
		if ymin==None: ymin=min(np.real(cd.Spar('s12db')))
		if ymax==None: ymax=max(np.real(cd.Spar('s12db')))
		ax.plot(cd.freq/1.E9,np.real(cd.Spar('s12db')),label=paratitle,linewidth=linew4,zorder=30)
	if "s22db" in type.lower():		# plot H22
		paratitle = 'S22'
		if ymin==None: ymin=min(np.real(cd.Spar('s22db')))
		if ymax==None: ymax=max(np.real(cd.Spar('s22db')))
		paratitle='S22'
		ax.plot(freq,np.real(cd.Spar('s22db')),label=paratitle,linewidth=linew4,zorder=30)
	################
	############ dB H-parameters
	if "h11db" in type.lower():		# plot H11
		paratitle='H11'
		if ymin==None: ymin=min(np.real(cd.Hpar('h11db')))
		if ymax==None: ymax=max(np.real(cd.Hpar('h11db')))
		ax.plot(freq,cd.Hpar('h11db'),label=paratitle,linewidth=linew4,zorder=30)
	if "h21db" in type.lower():		# plot H21
		paratitle='H21'
		#if ymin==None: ymin=min(np.real(cd.Hpar('h21db')))
		if ymin==None: ymin=0.      # default to 0dB for minimum H21
		if ymax==None: ymax=max(np.real(cd.Hpar('h21db')))
		ax.plot(freq,cd.Hpar('h21db'),label=paratitle,linewidth=linew4,color='black',zorder=30)
		if ft_extrapolation:			# then we want to plot the log-linear extrapolation of |H21|dB that would give ft
			y=[cd.ftextrapolation()['m']*np.log10(xmin*fscale)+cd.ftextrapolation()['b'], cd.ftextrapolation()['m']*np.log10(xmax*fscale)+cd.ftextrapolation()['b']]
			ax.plot([xmin,xmax],y,label="fmax ext",linewidth=linew2,color='red',zorder=3)
	if "h12db" in type.lower():		# plot H12
		paratitle='H12'
		if ymin==None: ymin=min(np.real(cd.Hpar('h12db')))
		if ymax==None: ymax=max(np.real(cd.Hpar('h12db')))
		ax.plot(cd.freq/1.E9,cd.Hpar('h12db'),label=paratitle,linewidth=linew4,zorder=30)
	if "h22db" in type.lower():		# plot H22
		if ymin==None: ymin=min(np.real(cd.Hpar('h22db')))
		if ymax==None: ymax=max(np.real(cd.Hpar('h22db')))
		paratitle='H22'
		ax.plot(freq,np.real(cd.Hpar('h22db')),label=paratitle,linewidth=linew4,zorder=30)
	################
	############ UMAX unilateral power gain
	if "umaxdb" in type.lower():		# plot H21
		paratitle='UMAX'
		#if ymin==None: ymin=min(cd.Umax('db'))
		if ymin==None: ymin=0.
		if ymax==None: ymax=max(cd.Umax('db'))
		ax.plot(freq,cd.Umax('db'),label=paratitle,linewidth=linew4,zorder=30)
		if fmax_extrapolation:			# then we want to plot the log-linear extrapolation of |H21|dB that would give ft
			y=[cd.fmaxextrapolation()['m']*np.log10(xmin*fscale)+cd.fmaxextrapolation()['b'], cd.fmaxextrapolation()['m']*np.log10(xmax*fscale)+cd.fmaxextrapolation()['b']]
			ax.plot([xmin,xmax],y,label="fmax ext",linewidth=linew2,zorder=3)
	################
	###########Gmax maximum available stable gain
	if "gmaxdb" in type.lower():		# plot maximum stable gain
		paratitle='GMAX'
		#if ymin==None: ymin=min(cd.Gmax('db')['gain'])
		if ymin==None: ymin=0.
		if ymax==None: ymax=max(cd.Gmax('db')['gain'])
		# plot line segment by segment to color it according to whether the gain is conditionally or unconditionally stable
		for ifreq in range(1,len(freq)-1):
			if cd.Kfactor[ifreq]<1.: linecolor='red'		# conditionally stable
			else: linecolor='blue'							# unconditionally stable
			ax.plot(freq[ifreq-1:ifreq+1],cd.Gmax('db')['gain'][ifreq-1:ifreq+1],label=paratitle,linewidth=linew4,color=linecolor,zorder=30)
	ax.set_xlim([xmin,xmax])
	ax.set_ylim([ymin,ymax])

	#ax.set_title(paratitle+"dB Vds= "+formatnum(cd.Vds_Spar(),precision=1)+" V "+"Id= "+formatnum(cd.Id_Spar(),precision=2)+" A",fontsize=titlefont)
	#if cd.devwidth!=None and cd.devwidth>0.: ax.set_title("".join([paratitle,"dB Vds= ",formatnum(cd.Vds_Spar(),precision=1)," V Vgs= ",formatnum(cd.Vgs_Spar(),precision=1), " V Id= ",formatnum(1.E6*cd.Id_Spar()/cd.devwidth,precision=2)," mA/mm"]),fontsize=titlefont)
	if cd.devwidth!=None and cd.devwidth>0.: ax.set_title("".join([paratitle,"dB Vds= ",formatnum(cd.Vds_Spar(),precision=1)," V Vgs= ",formatnum(cd.Vgs_Spar(),precision=1), " V Id= ",formatnum(cd.Id_Spar(),precision=2)," mA/mm"]),fontsize=titlefont)
	else: ax.set_title("".join([paratitle,"dB Vds= ",formatnum(cd.Vds_Spar(),precision=1)," V Vgs= ",formatnum(cd.Vgs_Spar(),precision=1), " V Id= ",formatnum(cd.Id_Spar(),precision=2)," A"]),fontsize=titlefont)

	ax.grid(True)
	#ax.hold(False)
	canvas.draw()
#####################################################################################################################
#####################################################################################################################
# plot Yfunction and optionally the best linear fit
## if mlin != None then plot the best least-squares fit line, y=mlin*x+blin
def plot_Yf(cd,figure=None,canvas=None,mlin=None,blin=0.,plotlin=False,xmin=None,xmax=None,ymin=None,ymax=None):
	axislablesfont = 18
	axisfont = 18
	titlefont = 22
	legendfont=12
	annotefont=12
	figuretitlefont=15
	linew1=10.
	linew2=5.
	linew3=3.
	linew4=2.
	xyannote=[.5,0.95]

	figrow = 1
	figcol = 1
	plt.clf()
	figure.clear()
	if len(cd.Id_T())>0 and figure!=None and canvas !=None:
		ax=figure.add_subplot(1,1,1)
		ax.xaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
		ax.yaxis.set_major_formatter(FormatStrFormatter('%5.1E'))
		ax.set_xlabel("Gate Voltage (V)",fontsize=axislablesfont)
		ax.set_ylabel("Y function",fontsize=axislablesfont)
		ax.tick_params(axis='x',labelsize=axisfont)
		ax.tick_params(axis='y',labelsize=axisfont)

		if xmin!=None and xmax!=None:
			ax.set_xlim([xmin,xmax])
		if ymin!=None and ymax!=None:
			ax.set_ylim([ymin,ymax])
		print("from line 1471 in IVplot.py ymin,ymax",ymin,ymax)
		if plotlin:
			if cd.Yflin_T()!=None and len(cd.Yflin_t)>1: ax.plot(cd.Yflin_T()['Vgs'],cd.Yflin_T()['Y'],label="Yf best linear fit",linewidth=linew1,color='red',zorder=1)
			else:	# pop up message to user to warn of missing data
				m=QtWidgets.QMessageBox()
				m.setText("".join(['Cannot plot YFM linear fit data because they do not exist for device ',cd.get_devicename()]))
				m.exec_()
				del m
		ax.plot(cd.Yf_T()['Vgs'],cd.Yf_T()['Y'],label="Yf",linewidth=linew3,color='green',zorder=2)

		ax.set_title("Y-function from Single-Swept Transfer Curve Vds="+str('{:5.1f}'.format(cd.Vds_T(),fontsize=titlefont))+" V")
		ax.grid(True)
	#plt.legend(ncol=1,bbox_to_anchor=(.98,.28),borderaxespad=0,fontsize=legendfont)
	#plt.annotate('max gm '+str('{:5.1E}'.format(cd.gmmax_T())),xy=(xyannote),xycoords='axes fraction',fontsize=annotefont)
	elif figure==None: raise ValueError("ERROR! No figure supplied")
	elif canvas!=None: raise ValueError("ERROR! No canvas supplied")
	elif cd.Id_T()=='None': raise ValueError("ERROR! No transfer curve data supplied")
	if figure!=None and canvas!=None:
		ax.hold(False)
		canvas.draw()
#####################################################################################################################
#####################################################################################################################
# plot Id vs Vgs for transfer curves (not used)

# def plot_Id_transfer(cd,figure=None,canvas=None,mlin=None,blin=0.,xmin=None,xmax=None,ymin=None,ymax=None,type="single"):
# 	axislablesfont = 18
# 	axisfont = 18
# 	titlefont = 22
# 	legendfont=12
# 	annotefont=12
# 	figuretitlefont=15
# 	linew1=10.
# 	linew2=5.
# 	linew3=3.
# 	linew4=2.
# 	xyannote=[.5,0.95]
#
# 	figrow = 1
# 	figcol = 1
# 	plt.clf()
# 	figure.clear()
#
# 	if cd.Id_T() != 'None' and figure!=None and canvas !=None:
# 		ax=figure.add_subplot(1,1,1)
# 		ax.xaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
# 		ax.yaxis.set_major_formatter(FormatStrFormatter('%5.1E'))
# 		ax.set_xlabel("Gate Voltage (V)",fontsize=axislablesfont)
# 		ax.set_ylabel("Id (A)",fontsize=axislablesfont)
# 		ax.tick_params(axis='x',labelsize=axisfont)
# 		ax.tick_params(axis='y',labelsize=axisfont)
#
# 		if xmin!=None and xmax!=None:
# 			ax.set_xlim([xmin,xmax])
# 		if ymin!=None and ymax!=None:
# 			ax.set_ylim([ymin,ymax])
# 		if type.lower()=="single transfer":				# plot the single-swept transfer curve Id(Vgs)
# 			ax.plot(cd.Vgs_T(),cd.Id_T(),label="Id",linewidth=linew3,color='black',zorder=2)
# 			ax.set_title("Id vs Vgs from Single-Swept Transfer Curve Vds="+str('{:5.1f}'.format(cd.Vds_T(),fontsize=titlefont))+" V")
# 		elif type.lower()=="double transfer" or type.lower()=="dual transfer":
# 			ax.plot(cd.Vgs_TF(),cd.Id_TF(),label="Id forward swept",linewidth=linew3,color='red',zorder=2)
# 			ax.plot(cd.Vgs_TR(),cd.Id_TR(),label="Id reverse swept",linewidth=linew3,color='blue',zorder=2)
# 			ax.set_title("Id vs Vgs from Double-Swept Transfer Curve Vds="+str('{:5.1f}'.format(cd.Vds_TF(),fontsize=titlefont))+" V")
# 		ax.grid(True)
# 	#plt.legend(ncol=1,bbox_to_anchor=(.98,.28),borderaxespad=0,fontsize=legendfont)
# 	#plt.annotate('max gm '+str('{:5.1E}'.format(cd.gmmax_T())),xy=(xyannote),xycoords='axes fraction',fontsize=annotefont)
# 	elif figure==None: raise ValueError("ERROR! No figure supplied")
# 	elif canvas!=None: raise ValueError("ERROR! No canvas supplied")
# 	elif cd.Id_T()=='None': raise ValueError("ERROR! No transfer curve data supplied")
# 	if figure!=None and canvas!=None:
# 		ax.hold(False)
# 		canvas.draw()
#####################################################################################################################
#####################################################################################################################
# plot points on Smith Chart
## data are complex real+jimaginary
def plot_smith_selectedpoints(data,canvas=None,figure=None,datatype="reflection",title="",interpolate=0,pointsonly=True,rectstart=None,rectstop=None):
	Z0=50.
	if canvas==None or figure==None: raise ValueError("ERROR! One of canvas or figure missing")
	if datatype.lower()=="reflection" or datatype.lower()=="r": datatype=SmithAxes.S_PARAMETER
	elif datatype.lower()=="impedance" or datatype.lower()=="z": datatype=SmithAxes.Z_PARAMETER
	elif datatype.lower()=="admittance" or datatype.lower()=="y": datatype=SmithAxes.Y_PARAMETER
	#fig=FigureCanvas(figure=plt.figure(1,figsize=(8,8),frameon=False))
	ax = plt.subplot(1,1,1,projection='smith')
	#ax.plot([],interpolate=0,datatype=datatype)
	ax.clear()
	if title!="": ax.set_title(title)
	data=np.multiply(Z0,data)
	#if rectstart!=None and rectstop!=None:
	#ax.add_patch(pch.Rectangle((0,0),.2,.2))
	if len(data)>0:
		if datatype==SmithAxes.Z_PARAMETER:
			if pointsonly:              # plot data as single points
				for d in data:
					ax.plot(d,interpolate=0,datatype=datatype)
			else:   # plot a line
				ax.plot(np.multiply(Z0,data),interpolate=interpolate,datatype=datatype)
		elif datatype==SmithAxes.S_PARAMETER:
			if pointsonly:              # plot data as single points
				for d in data:
					ax.plot(d,interpolate=0,datatype=datatype)
			else:
				ax.plot(data,interpolate=interpolate,datatype=datatype)
	#ax.hold(False)
	canvas.draw()
#####################################################################################################################
#####################################################################################################################
# plot parameter contours on Smith Chart
## NOT IMPLEMENTED YET
def plot_smith_contours(parameters=None,reflections=None,canvas=None,figure=None,numberofmeshpoints=100,title=""):
	if len(reflections)!=len(parameters): raise ValueError("ERROR! number of x,y pairs is not equal to the number of Z values")
	if canvas==None or figure==None: raise ValueError("ERROR! One of canvas or figure missing")
	ax = plt.subplot(1, 1, 1, projection='smith')
	ax.clear()
	if title!="": ax.set_title(title)
	gammas=np.array([convertMAtoRI(mag=r[0],ang=r[1]) for r in reflections])
	zsri=np.divide(np.add(1,gammas),np.subtract(1,gammas))            # convert reflections to normalized impedance
	zs=np.array([z.real,z.imag] for z in zsri)                        # convert real+jimaginary normalized impedance to [real,imaginary] (both floats)

	# find min and max of real and imaginary parts
	zmin_real=np.min(zs[:][0])
	zmax_real=np.max(zs[:][0])
	zmin_imag=np.min(zs[:][1])
	zmax_imag=np.min(zs[:][1])
	rr,ri=np.meshgrid(np.linspace(zmin_real,zmax_real,numberofmeshpoints),np.linspace(zmin_imag,zmax_imag,numberofmeshpoints))            # set up grid to hold calculated interpolated results
	paragrid=griddata(zs,parameters,(rr,ri),method='cubic')



	CS=ax.contour(xx,yy,zcub,levels=levels,datatype=SmithAxes.S_PARAMETER)
	ax.clabel(CS,inline=1,fontsize=10,datatype=SmithAxes.S_PARAMETER)
	ax.grid(True)
	if len(data)>0:
		if datatype==SmithAxes.Z_PARAMETER:
			if pointsonly:              # plot data as single points
				for d in data:
					ax.plot(d,interpolate=0,datatype=datatype)
			else:   # plot a line
				ax.plot(np.multiply(Z0,data),interpolate=interpolate,datatype=datatype)
		elif datatype==SmithAxes.S_PARAMETER:
			if pointsonly:              # plot data as single points
				for d in data:
					ax.plot(d,interpolate=0,datatype=datatype)
			else:
				ax.plot(data,interpolate=interpolate,datatype=datatype)
	#ax.hold(False)
	canvas.draw()
#####################################################################################################################
########################################################################################################################
#plots family of curves for a single device
def plot_family_of_curves_loop(cd,figure,canvas,plotlin=False,xmin=None,xmax=None,ymin=None,ymax=None,Vgs='all'):
	axislablesfont = 18
	axisfont = 18
	titlefont = 22
	legendfont=12
	annotefont=12
	figuretitlefont=15
	linew1=10.
	linew2=5.
	linew3=3.
	linew4=2.
	xyannote=[.5,0.95]

	figrow = 1
	figcol = 1

	plt.clf()
	figure.clear()
	loopfoc1=cd.get_Id_loopfoc1(swapindx=False)     # data indexed [iVgs][iVds]
	loopfoc2=cd.get_Id_loopfoc2(swapindx=False)     # data indexed [iVgs][iVds]
	if np.average(np.diff(loopfoc1['Vds']))>=0: linestyle1='dashed'  # negative-going Vds
	else: linestyle1='solid' # positive-going Vds
	if np.average(np.diff(loopfoc2['Vds']))>=0: linestyle2='dashed'  # negative-going Vds
	else: linestyle2='solid' # positive-going Vds
	if Vgs.lower()!="all":
		iVgsplot=min(range(len(loopfoc1['Vgs'])), key=lambda i: abs(float(Vgs)-loopfoc1['Vgs'][i][0]))          # find index of measured Vgs closest to that specified
	if len(loopfoc1['Id'])>0:
		#axsub=plt.subplot(figrow,figcol,1)
		axsub=figure.add_subplot(1,1,1)
		#axsub.set_yticklabel_format(style='sci',scilimits=(1,1))
		axsub.tick_params(axis='x',labelsize=axisfont)
		axsub.tick_params(axis='y',labelsize=axisfont)
		axsub.set_xlabel("Vds (V)",fontsize=axislablesfont)
		if cd.devwidth!=None and cd.devwidth>0.: axsub.set_ylabel("Drain Current (mA/mm)",fontsize=axislablesfont)

		else: axsub.set_ylabel("Drain Current (A)",fontsize=axislablesfont)
		if xmin == None: xmin = min(min(loopfoc1['Vds']),min(loopfoc2['Vds']))		# if not specified, chose the minimum of all gate voltages in the family of curves
		if xmax == None: xmax = max(max(loopfoc1['Vds']),max(loopfoc2['Vds']))		# if not specified, chose the maximum of all gate voltages in the family of curves
		axsub.set_xlim([xmin, xmax])
		if Vgs.lower()=='all': # plot all Vgs curves
			if ymin == None: ymin = min([min([min(Id) for Id in loopfoc1['Id']]),min([min(Id) for Id in loopfoc2['Id']])])  # if not specified, chose the minimum of all drain current values in the family of curves
			if ymax == None: ymax = max([max([max(Id) for Id in loopfoc1['Id']]),max([max(Id) for Id in loopfoc2['Id']])])  # if not specified, chose the maximum of all drain current values in the family of curves
		else:
			if ymin == None: ymin = min(min(loopfoc1['Id'][iVgsplot]),min(loopfoc2['Id'][iVgsplot]))  # if not specified, chose the minimum of all drain current values in the family of curves
			if ymax == None: ymax = max(max(loopfoc1['Id'][iVgsplot]),max(loopfoc2['Id'][iVgsplot]))  # if not specified, chose the maximum of all drain current values in the family of curves
		if max(abs(ymin),abs(ymax))<=1: axsub.yaxis.set_major_formatter(FormatStrFormatter('%5.1E'))
		if max(abs(ymin),abs(ymax))>1: axsub.yaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
		if max(abs(ymin),abs(ymax))>10: axsub.yaxis.set_major_formatter(FormatStrFormatter('%d'))

		axsub.set_ylim([ymin, ymax])

		if Vgs.lower()=='all':       #plot all Vgs curves
			for iVgs in range(0,len(loopfoc1['Id'])):
				axsub.plot(cd.Vds_loopfoc1[iVgs],loopfoc1['Id'][iVgs],color='red', linestyle=linestyle1)
			for iVgs in range(0,len(loopfoc2['Id'])):
				axsub.plot(cd.Vds_loopfoc2[iVgs],loopfoc2['Id'][iVgs],color='blue', linestyle=linestyle2)
		else:
			axsub.plot(cd.Vds_loopfoc1[iVgsplot],loopfoc1['Id'][iVgsplot],color='red', linestyle=linestyle1)
			axsub.plot(cd.Vds_loopfoc2[iVgsplot],loopfoc2['Id'][iVgsplot],color='blue', linestyle=linestyle2)

		axsub.set_title("Family of Curves",fontsize=titlefont)

		axsub.grid(True)
		#axsub.hold(False)
		#axsub.clear()
		#plt.show()
		canvas.draw()
	else:						# pop up message to user to warn of missing data
		m=QtWidgets.QMessageBox()
		m.setText("".join(['Cannot plot IV data because they do not exist for device ',cd.get_devicename()]))
		m.exec_()
		del m
		#figure.delaxes(axsub)
	#####################################################################################################################
	########################################################################################################################
#plots family of curves for a single device
# Vgs allows the user to pick which Vgs curve is shown, Vgs=None shows all Vgs curves
def plot_family_of_curves_4loop(cd,figure,canvas,legendon=True,xmin=None,xmax=None,ymin=None,ymax=None,Vgs='all'):
	axislablesfont = 18
	axisfont = 18
	titlefont = 22
	legendfont=12
	annotefont=12
	figuretitlefont=15
	linew1=10.
	linew2=5.
	linew3=3.
	linew4=2.
	xyannote=[.5,0.95]

	figrow = 1
	figcol = 1

	plt.clf()
	figure.clear()
	loop4foc1=cd.get_Id_4loopfoc1(swapindx=False)     # data indexed [iVgs][iVds]
	loop4foc2=cd.get_Id_4loopfoc2(swapindx=False)     # data indexed [iVgs][iVds]
	loop4foc3=cd.get_Id_4loopfoc3(swapindx=False)     # data indexed [iVgs][iVds]
	loop4foc4=cd.get_Id_4loopfoc4(swapindx=False)     # data indexed [iVgs][iVds]
	if np.average(np.diff(loop4foc1['Vds']))>=0: linestyle1='dashed'  # negative-going Vds
	else: linestyle1='solid' # positive-going Vds
	if np.average(np.diff(loop4foc2['Vds']))>=0: linestyle2='dashed'  # negative-going Vds
	else: linestyle2='solid' # positive-going Vds
	if np.average(np.diff(loop4foc3['Vds']))>=0: linestyle3='dashed'  # negative-going Vds
	else: linestyle3='solid' # positive-going Vds
	if np.average(np.diff(loop4foc4['Vds']))>=0: linestyle4='dashed'  # negative-going Vds
	else: linestyle4='solid' # positive-going Vds

	if Vgs.lower()!="all":
		iVgsplot=min(range(len(loop4foc1['Vgs'])), key=lambda i: abs(float(Vgs)-loop4foc1['Vgs'][i][0]))          # find index of measured Vgs closest to that specified
	if len(loop4foc1['Id'])>0:
		axsub=figure.add_subplot(1,1,1)
		axsub.tick_params(axis='x',labelsize=axisfont)
		axsub.tick_params(axis='y',labelsize=axisfont)
		axsub.set_xlabel("Vds (V)",fontsize=axislablesfont)
		if cd.devwidth!=None and cd.devwidth>0.: axsub.set_ylabel("Drain Current (mA/mm)",fontsize=axislablesfont)

		else: axsub.set_ylabel("Drain Current (A)",fontsize=axislablesfont)
		if xmin == None: xmin = min(min(loop4foc1['Vds']),min(loop4foc2['Vds']))		# if not specified, chose the minimum of all gate voltages in the family of curves
		if xmax == None: xmax = max(max(loop4foc1['Vds']),max(loop4foc2['Vds']))		# if not specified, chose the maximum of all gate voltages in the family of curves
		axsub.set_xlim([xmin, xmax])
		if Vgs.lower()=='all': # plot all Vgs curves
			if ymin == None: ymin = min([min([min(Id) for Id in loop4foc1['Id']]),min([min(Id) for Id in loop4foc2['Id']]),min([min(Id) for Id in loop4foc3['Id']]),min([min(Id) for Id in loop4foc4['Id']])])  # if not specified, chose the minimum of all drain current values in the family of curves
			if ymax == None: ymax = max([max([max(Id) for Id in loop4foc1['Id']]),max([max(Id) for Id in loop4foc2['Id']]),max([max(Id) for Id in loop4foc3['Id']]),max([max(Id) for Id in loop4foc4['Id']])])  # if not specified, chose the maximum of all drain current values in the family of curves
		else:
			if ymin==None: ymin=min(min(loop4foc1['Id'][iVgsplot]),min(loop4foc2['Id'][iVgsplot]),min(loop4foc2['Id'][iVgsplot]),min(loop4foc3['Id'][iVgsplot]),min(loop4foc4['Id'][iVgsplot]))
			if ymax==None: ymax=max(max(loop4foc1['Id'][iVgsplot]),max(loop4foc2['Id'][iVgsplot]),max(loop4foc2['Id'][iVgsplot]),max(loop4foc3['Id'][iVgsplot]),max(loop4foc4['Id'][iVgsplot]))
		if max(abs(ymin),abs(ymax))<=1: axsub.yaxis.set_major_formatter(FormatStrFormatter('%5.1E'))
		if max(abs(ymin),abs(ymax))>1: axsub.yaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
		if max(abs(ymin),abs(ymax))>10: axsub.yaxis.set_major_formatter(FormatStrFormatter('%d'))

		axsub.set_ylim([ymin, ymax])

		if Vgs.lower()=='all':       #plot all Vgs curves
			# plot the first Vgs curves just to get the legend
			axsub.plot(cd.Vds_4loopfoc1[0],loop4foc1['Id'][0],label="sweep 1",color='darkred',linestyle=linestyle1)
			axsub.plot(cd.Vds_4loopfoc2[0],loop4foc2['Id'][0],label="sweep 2",color='darkblue',linestyle=linestyle2)
			axsub.plot(cd.Vds_4loopfoc3[0],loop4foc3['Id'][0],label="sweep 3",color='red',linestyle=linestyle3)
			axsub.plot(cd.Vds_4loopfoc4[0],loop4foc4['Id'][0],label="sweep 4",color='magenta',linestyle=linestyle4)

			# plot the rest of the Vgs curves
			for iVgs in range(1,len(loop4foc1['Id'])):
				axsub.plot(cd.Vds_4loopfoc1[iVgs],loop4foc1['Id'][iVgs],color='darkred',linestyle=linestyle1)
			for iVgs in range(1,len(loop4foc2['Id'])):
				axsub.plot(cd.Vds_4loopfoc2[iVgs],loop4foc2['Id'][iVgs],color='darkblue',linestyle=linestyle2)
			for iVgs in range(1,len(loop4foc3['Id'])):
				axsub.plot(cd.Vds_4loopfoc3[iVgs],loop4foc3['Id'][iVgs],color='red',linestyle=linestyle3)
			for iVgs in range(1,len(loop4foc4['Id'])):
				axsub.plot(cd.Vds_4loopfoc4[iVgs],loop4foc4['Id'][iVgs],color='magenta',linestyle=linestyle4)
		else:   # plot just one Vgs curve
			axsub.plot(cd.Vds_4loopfoc1[iVgsplot],loop4foc1['Id'][iVgsplot],label="sweep 1",color='darkred',linestyle=linestyle1)
			axsub.plot(cd.Vds_4loopfoc2[iVgsplot],loop4foc2['Id'][iVgsplot],label="sweep 2",color='darkblue',linestyle=linestyle2)
			axsub.plot(cd.Vds_4loopfoc3[iVgsplot],loop4foc3['Id'][iVgsplot],label="sweep 3",color='red',linestyle=linestyle3)
			axsub.plot(cd.Vds_4loopfoc4[iVgsplot],loop4foc4['Id'][iVgsplot],label="sweep 4",color='magenta',linestyle=linestyle4)

		axsub.set_title("Family of Curves",fontsize=titlefont)

		axsub.grid(True)
		if legendon:
			try: axsub.legend(loc='lower right')
			except: pass
		canvas.draw()
	else:						# pop up message to user to warn of missing data
		m=QtWidgets.QMessageBox()
		m.setText("".join(['Cannot plot IV data because they do not exist for device ',cd.get_devicename()]))
		m.exec_()
		del m
		#figure.delaxes(axsub)
#####################################################################################################################
########################################################################################################################
#plots Id and/or Ig vs time for a step in Vgs
def plot_pulsedVgs_timedomain(cd,figure,canvas,logplot=False,legendon=True,plotIg=False,xmin=None,xmax=None,ymin=None,ymax=None):
	#cd.set_parameters_curvefit(fitparameters)
#    cd.writefile_ivtransfercalc()                   # write IV transfer curve results to file
	#cd.get_orderfit()
	#print("device ",cd.get_devicename()) #debug
	axislablesfont = 18
	axisfont = 18
	titlefont = 20
	legendfont=12
	annotefont=12
	figuretitlefont=15
	linew1=10.
	linew2=5.
	linew3=3.
	linew4=2.
	xyannote=[.5,0.95]

	figrow = 1
	figcol = 1

	plt.clf()
	figure.clear()
	yminlogspecified=True
	ymaxlogspecified=True
	if len(cd.get_pulsedVgs())>0:
		axsub=figure.add_subplot(1,1,1)
		axsub.tick_params(axis='x',labelsize=axisfont)
		axsub.tick_params(axis='y',labelsize=axisfont)
		axsub.set_xlabel("time Sec",fontsize=axislablesfont)
		if cd.devwidth!=None and cd.devwidth>0.: axsub.set_ylabel("Current (mA/mm)",fontsize=axislablesfont)
		else: axsub.set_ylabel("Current (A)",fontsize=axislablesfont)

		if xmin == None: xmin = np.min(cd.timestamp_pulsedVgs)		# if not specified, chose the minimum of all timesteps
		if xmax == None: xmax = np.max(cd.timestamp_pulsedVgs)		# if not specified, chose the maximum of all timesteps
		axsub.set_xlim([xmin, xmax])
		axsub.set_xscale('log')                     # set timescale to log
		if not logplot:     # is y scale logarithmic?
			if plotIg:
				if ymin == None: ymin = min(np.min(cd.Id_pulsedVgs),np.min(cd.Ig_pulsedVgs))  # if not specified, chose the minimum of all Id and Ig
				if ymax == None: ymax = max(np.max(cd.Id_pulsedVgs),np.max(cd.Ig_pulsedVgs))  # if not specified, chose the maximum of all Id and Ig
			else:
				if ymin == None: ymin = np.min(cd.Id_pulsedVgs)  # if not specified, chose the minimum of all Id
				if ymax == None: ymax = np.max(cd.Id_pulsedVgs)  # if not specified, chose the maximum of all Id
			axsub.set_yscale('linear')
		else: # logarithmic y scale on
			if plotIg:
				if ymin == None: ymin = min(np.min(np.abs(cd.Id_pulsedVgs)),np.min(np.abs(cd.Ig_pulsedVgs)))  # if not specified, chose the minimum of all Id and Ig
				if ymax == None: ymax = max(np.max(np.abs(cd.Id_pulsedVgs)),np.max(np.abs(cd.Ig_pulsedVgs)))  # if not specified, chose the maximum of all Id and Ig
			else:
				if ymin == None:
					yminlogspecified=False
					ymin = np.min(np.abs(cd.Id_pulsedVgs))  # if not specified, chose the minimum of all Id and Ig
				if ymax == None:
					ymaxlogspecified=False
					ymax = np.max(np.abs(cd.Id_pulsedVgs))  # if not specified, chose the maximum of all Id and Ig
			if not yminlogspecified and not ymaxlogspecified and int(np.log10(ymax))-int(np.log10(ymin))<1:
				ymin=pow(10.,int(np.log10(ymin)))
				ymax=pow(10.,np.ceil(np.log10(ymax)))
			axsub.set_yscale('log')

		if max(abs(ymin),abs(ymax))<=1: axsub.yaxis.set_major_formatter(FormatStrFormatter('%5.1E'))
		if max(abs(ymin),abs(ymax))>1: axsub.yaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
		if max(abs(ymin),abs(ymax))>10: axsub.yaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
		if logplot: axsub.yaxis.set_major_formatter(FormatStrFormatter('%5.1E'))


		axsub.set_ylim([ymin, ymax])

		for iVgs in range(0,len(cd.Vgs_pulsedVgs)):
			if logplot: axsub.plot(cd.timestamp_pulsedVgs[iVgs],np.abs(cd.Id_pulsedVgs[iVgs]),label="Id, Vgs ="+formatnum(cd.Vgs_pulsedVgs[iVgs]))
			else: axsub.plot(cd.timestamp_pulsedVgs[iVgs],cd.Id_pulsedVgs[iVgs],label="Id, Vgs ="+formatnum(cd.Vgs_pulsedVgs[iVgs]))
			if plotIg:      # then plot gate current vs time too
				if logplot: axsub.plot(cd.timestamp_pulsedVgs[iVgs],np.abs(cd.Ig_pulsedVgs[iVgs]),label="Ig, Vgs ="+formatnum(cd.Vgs_pulsedVgs[iVgs]))
				else: axsub.plot(cd.timestamp_pulsedVgs[iVgs],cd.Ig_pulsedVgs[iVgs],label="Ig, Vgs ="+formatnum(cd.Vgs_pulsedVgs[iVgs]))
		axsub.set_title("Current vs Time, Vds= "+formatnum(cd.Vds_pulsedVgs,precision=2)+" V Vgsq= "+formatnum(cd.quiescent_Vgs_pulsedVgs)+" V Tq= "+formatnum(cd.quiescent_time_pulsedVgs,precision=1)+" sec",fontsize=titlefont)

		axsub.grid(True)

		if legendon:
			try: axsub.legend(loc='lower right')
			except: pass
		canvas.draw()
	else:						# pop up message to user to warn of missing data
		m=QtWidgets.QMessageBox()
		m.setText("".join(['Cannot plot time transient data because they do not exist for device ',cd.get_devicename()]))
		m.exec_()
		del m
		#figure.delaxes(axsub)
	#####################################################################################################################
	########################################################################################################################
#plots Id and/or Ig vs time for a step in Vds
def plot_pulsedVds_timedomain(cd,figure,canvas,logplot=False,legendon=True,plotIg=False,xmin=None,xmax=None,ymin=None,ymax=None):
	axislablesfont = 18
	axisfont = 18
	titlefont = 20
	legendfont=12
	annotefont=12
	figuretitlefont=15
	linew1=10.
	linew2=5.
	linew3=3.
	linew4=2.
	xyannote=[.5,0.95]

	figrow = 1
	figcol = 1

	plt.clf()
	figure.clear()
	yminlogspecified=True
	ymaxlogspecified=True
	if len(cd.get_pulsedVds())>0:
		axsub=figure.add_subplot(1,1,1)
		axsub.tick_params(axis='x',labelsize=axisfont)
		axsub.tick_params(axis='y',labelsize=axisfont)
		axsub.set_xlabel("time Sec",fontsize=axislablesfont)
		if cd.devwidth!=None and cd.devwidth>0.: axsub.set_ylabel("Current (mA/mm)",fontsize=axislablesfont)
		else: axsub.set_ylabel("Current (A)",fontsize=axislablesfont)

		if xmin == None: xmin = np.min(cd.timestamp_pulsedVds)		# if not specified, chose the minimum of all timesteps
		if xmax == None: xmax = np.max(cd.timestamp_pulsedVds)		# if not specified, chose the maximum of all timesteps
		axsub.set_xlim([xmin, xmax])
		axsub.set_xscale('log')                     # set timescale to log
		if not logplot:     # is y scale logarithmic?
			if plotIg:
				if ymin == None: ymin = min(np.min(cd.Id_pulsedVds),np.min(cd.Ig_pulsedVds))  # if not specified, chose the minimum of all Id and Ig
				if ymax == None: ymax = max(np.max(cd.Id_pulsedVds),np.max(cd.Ig_pulsedVds))  # if not specified, chose the maximum of all Id and Ig
			else:
				if ymin == None: ymin = np.min(cd.Id_pulsedVds)  # if not specified, chose the minimum of all Id
				if ymax == None: ymax = np.max(cd.Id_pulsedVds)  # if not specified, chose the maximum of all Id
			axsub.set_yscale('linear')
		else: # logarithmic y scale on
			if plotIg:
				if ymin == None: ymin = min(np.min(np.abs(cd.Id_pulsedVds)),np.min(np.abs(cd.Ig_pulsedVds)))  # if not specified, chose the minimum of all Id and Ig
				if ymax == None: ymax = max(np.max(np.abs(cd.Id_pulsedVds)),np.max(np.abs(cd.Ig_pulsedVds)))  # if not specified, chose the maximum of all Id and Ig
			else:
				if ymin == None:
					yminlogspecified=False
					ymin = np.min(np.abs(cd.Id_pulsedVds))  # if not specified, chose the minimum of all Id and Ig
				if ymax == None:
					ymaxlogspecified=False
					ymax = np.max(np.abs(cd.Id_pulsedVds))  # if not specified, chose the maximum of all Id and Ig
			if not yminlogspecified and not ymaxlogspecified and int(np.log10(ymax))-int(np.log10(ymin))<1:
				ymin=pow(10.,int(np.log10(ymin)))
				ymax=pow(10.,np.ceil(np.log10(ymax)))
			axsub.set_yscale('log')

		if max(abs(ymin),abs(ymax))<=1: axsub.yaxis.set_major_formatter(FormatStrFormatter('%5.1E'))
		if max(abs(ymin),abs(ymax))>1: axsub.yaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
		if max(abs(ymin),abs(ymax))>10: axsub.yaxis.set_major_formatter(FormatStrFormatter('%5.1f'))
		if logplot: axsub.yaxis.set_major_formatter(FormatStrFormatter('%5.1E'))


		axsub.set_ylim([ymin, ymax])

		for iVds in range(0,len(cd.Vds_pulsedVds)):
			if logplot: axsub.plot(cd.timestamp_pulsedVds[iVds],np.abs(cd.Id_pulsedVds[iVds]),label="Id, Vds ="+formatnum(cd.Vds_pulsedVds[iVds]))
			else: axsub.plot(cd.timestamp_pulsedVds[iVds],cd.Id_pulsedVds[iVds],label="Id, Vds ="+formatnum(cd.Vds_pulsedVds[iVds]))
			if plotIg:      # then plot gate current vs time too
				if logplot: axsub.plot(cd.timestamp_pulsedVds[iVds],np.abs(cd.Ig_pulsedVds[iVds]),label="Ig, Vds ="+formatnum(cd.Vds_pulsedVds[iVds]))
				else: axsub.plot(cd.timestamp_pulsedVds[iVds],cd.Ig_pulsedVds[iVds],label="Ig, Vds ="+formatnum(cd.Vds_pulsedVds[iVds]))
		axsub.set_title("Current vs Time, Vgs= "+formatnum(cd.Vgs_pulsedVds,precision=2)+" V Vdsq= "+formatnum(cd.quiescent_Vds_pulsedVds)+" V Tq= "+formatnum(cd.quiescent_time_pulsedVds,precision=1)+" sec",fontsize=titlefont)

		axsub.grid(True)

		if legendon:
			try: axsub.legend(loc='lower right')
			except: pass
		canvas.draw()
	else:						# pop up message to user to warn of missing data
		m=QtWidgets.QMessageBox()
		m.setText("".join(['Cannot plot time transient data because they do not exist for device ',cd.get_devicename()]))
		m.exec_()
		del m
		#figure.delaxes(axsub)
	#####################################################################################################################