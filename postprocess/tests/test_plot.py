__author__ = 'PMarsh Carbonics'
# plot Sparameters
import matplotlib.pyplot as plt
import pylab as pl
import mwavepy as mv
import numpy as np
import time
################################################################
# plotting smith charts
class dataPlotter:
#	pl.ion()									# needed to allow redrawing of plot
	def __init__(self):							# set up for dynamic plotting of smith charts
		pl.ion()									# needed to allow redrawing of plot
#		pl.show()

	def smithplotSpar(self,fullfilename,porta,portb):
#		pl.figure(1)
		pl.figure(1,figsize=(8,20))
		pl.subplot(2,1,1)
		Sparplot = mv.Network(fullfilename)
		Sparplot.plot_s_smith(m=porta,n=portb)
		pl.draw()
		plt.pause(0.0001)
#		pl.clf()
	def clearplot(self):						# clears the plot
		pl.clf()
	def draw(self):
		pl.draw()
	def close(self):
		pl.close()

#############################################################
# rectangular plots of 2-port S-parameters - format is real/imaginary
# Inputs:	frequencies is the frequency array in GHz
# 			spar are the complex S-parameter array (vs frequency)
#class SpardBplot:								# plot S-parameter in log magnitude plot
#	pl.ion()									# interactive mode to allow redrawing of plots
#	def __init__(self):
#		pl.figure(1)
#		pl.show()

	def spardBplot(self,freq,spar,sylabel):				# plot S parameter array in dB vs frequency. The Sparameter are complex numbers while the frequency is in Hz
		# convert S parameter to dB
#		sdB = [np.log10(abs(s)) for s in spar]			# get S-parameter in dB
		# now plot
		sp = [s.real for s in spar]
		fig=pl.figure(1,figsize=(8,20))
		ax=fig.add_subplot(2,1,2)
		pl.grid(True)
		#ax.axis('equal')
		#ax.set_title("S21")
		#mgr = pl.get_current_fig_manager()
		#mgr.window.setGeometry(50,100,640,545)
		#pl.figure(1).canvas.manager.window.attributes('-topmost',1)
		#pl.figure(1).canvas.manager.window.move(400,100)

		pl.plot(freq,sp,lw=.3)
		pl.xlabel("frequency GHz")
		pl.ylabel(sylabel)
		pl.draw()
		plt.pause(0.0001)
#		while 1:
#			pl.draw()
#			time.sleep(1)


