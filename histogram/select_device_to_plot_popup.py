from devicelisting import *
from utilities import parse_rpn
from actions_plot_widget import *

#################################################################################################################################
	# user clicked on row header i.e. device name so plot device IV and/or other parameters
	# cd is the single device selected to display its data, parent is the parent widget
def select_device_to_plot_menu(parent=None,cd=None):
	devfoc=None
	devt=None
	devRF=None
	devtd=None
	devloopfoc=None
	devloop4foc=None
	devpulsedVgs=None
	devpulsedVds=None

	#print("from actions_devlisting line 120 device name is", devicename)
	# find device with this name

	if len(cd.Id_foc())>0 and len(cd.Id_foc())>0:devfoc=cd                  # single-swept family of curves plot
	if len(cd.Id_T())>0 and len(cd.Id_T())>0: devt=cd						# single transfer curve plot
	if len(cd.Id_TF())>0 and len(cd.Id_TF())>0: devtd=cd					# double-swept (forward then reverse) transfer curve plot
	if len(cd.get_Id_loopfoc1())>0: devloopfoc=cd                           # double-swept family of curves plot (one loop)
	if len(cd.get_Id_4loopfoc1())>0: devloop4foc=cd                         # 4-swept family of curves plot (two loops)
	if len(cd.get_pulsedVgs())>0: devpulsedVgs=cd                           # time-domain Id, Ig for pulsed Vgs
	if len(cd.get_pulsedVds())>0: devpulsedVds=cd                           # time-domain Id, Ig, for pulsed Vds
	if 'NO' not in cd.Spar('s11') and cd.Spar('s11')!=None: devRF=cd		# do we have any RF data for this wafer?

	############### setup of drop-down menu
	select_popmenu=QtWidgets.QMenu()		# plot type selector

	if devfoc!=None:				# have family of curves data
		foc_popaction=select_popmenu.addAction('family of curves')
		if cd.Rc_TLM!=None:
			TLM_popaction=select_popmenu.addAction('TLM Ron vs source-drain spacing')

	if devloopfoc!=None:				# have double-swept family of curves data
		loopfoc_popaction=select_popmenu.addAction('family of curves double-swept')

	if devloop4foc!=None:				# have double-swept family of curves data
		loop4foc_popaction=select_popmenu.addAction('family of curves 4-swept')

	if devt!=None:
		Id_t_popaction=select_popmenu.addAction('single-swept transfer curve Id')
		Yf_popaction=select_popmenu.addAction('Yf')
		gm_t_popaction=select_popmenu.addAction('Gm from forward transfer curve')

	if devtd!=None:
		#print("from select_device_to_plot_popup.py line 36 add pop") # debug
		Id_td_popaction=select_popmenu.addAction('forward and reverse swept transfer curves Id')
		gm_tfr_popaction=select_popmenu.addAction('Gm from forward and reverse transfer curves')

	if devRF!=None:
		s11db_popaction=select_popmenu.addAction('S11 dB')
		s22db_popaction=select_popmenu.addAction('S22 dB')
		s21db_popaction=select_popmenu.addAction('S21 dB')
		h21db_popaction=select_popmenu.addAction('H21 dB')
		umaxdb_popaction=select_popmenu.addAction('maximum unilateral gain dB')
		gmaxdb_popaction=select_popmenu.addAction('maximum available gain dB')

	if devpulsedVgs!=None:
		pulsedVgs_popaction=select_popmenu.addAction('time domain from pulsed Vgs')

	if devpulsedVds!=None:
		pulsedVds_popaction=select_popmenu.addAction('time domain from pulsed Vds')
	###### end of drop-down menu setup

	selectplot=select_popmenu.exec_(QtGui.QCursor.pos())

	if 	devfoc!=None and selectplot==foc_popaction:					# plot family of curves
		focplot=PlotGraphWidget(parent=parent,dev=devfoc,plottype='family_of_curves')
		focplot.show()
	if 	devfoc!=None and cd.Rc_TLM!=None and selectplot==TLM_popaction:					# plot TLM curves
		focplot=PlotGraphWidget(parent=parent,dev=devfoc,plottype='TLM')
		focplot.show()

	if devloopfoc!=None and selectplot==loopfoc_popaction:          # plot double-swept family of curves
		loopfocplot=PlotGraphWidget(parent=parent,dev=devloopfoc,plottype='double_swept_family_of_curves')
		loopfocplot.show()
	if devloop4foc!=None and selectplot==loop4foc_popaction:          # plot double-swept family of curves
		loopfocplot=PlotGraphWidget(parent=parent,dev=devloop4foc,plottype='4_swept_family_of_curves')
		loopfocplot.show()

	if devt!=None:
		if selectplot==Id_t_popaction:					# plot Id(Vgs) for the single-swept transfer curve
			Idtplot=PlotGraphWidget(parent=parent,dev=devt,plottype='single transfer')
			Idtplot.show()
		elif selectplot==gm_t_popaction:
			gmtplot=PlotGraphWidget(parent=parent,dev=devt,plottype='gm_T')							# plot gm from spline fit of single-swept transfer function
			gmtplot.show()
		elif selectplot==Yf_popaction:					# plot Y-function
			Yfplot=PlotGraphWidget(parent=parent,dev=devt,plottype='Yf')
			Yfplot.show()
	if devtd!=None:
		if selectplot==Id_td_popaction:					# plot Id(Vgs) for the single-swept transfer curve
			Idtplot=PlotGraphWidget(parent=parent,dev=devtd,plottype='double transfer')
			Idtplot.show()
		elif selectplot==gm_tfr_popaction:
			gmtplot=PlotGraphWidget(parent=parent,dev=devtd,plottype='gm_TFR')							# plot gm from spline fit of dual-swept transfer function
			gmtplot.show()

	if devRF!=None:
		if selectplot==s11db_popaction:
			s11plot=PlotGraphWidget(parent=parent,dev=devRF,plottype='s11db')
			s11plot.show()
		elif selectplot==s22db_popaction:
			s22plot=PlotGraphWidget(parent=parent,dev=devRF,plottype='s22db')
			s22plot.show()
		elif selectplot==s21db_popaction:
			s21plot=PlotGraphWidget(parent=parent,dev=devRF,plottype='s21db')
			s21plot.show()
		elif selectplot==h21db_popaction:
			h21plot=PlotGraphWidget(parent=parent,dev=devRF,plottype='h21db')
			h21plot.show()
		elif selectplot==umaxdb_popaction:
			umaxplot=PlotGraphWidget(parent=parent,dev=devRF,plottype='umaxdb')
			umaxplot.show()
		elif selectplot==gmaxdb_popaction:
			gmaxplot=PlotGraphWidget(parent=parent,dev=devRF,plottype='gmaxdb')
			gmaxplot.show()

	if devpulsedVgs!=None and selectplot==pulsedVgs_popaction:          # plot Id vs time (Id(t)) for pulsed Vgs
		pulsedVgsplot=PlotGraphWidget(parent=parent,dev=devpulsedVgs,plottype='time_domain_from_pulsedVgs')
		pulsedVgsplot.show()

	if devpulsedVds!=None and selectplot==pulsedVds_popaction:          # plot Id vs time (Id(t)) for pulsed Vgs
		pulsedVgsplot=PlotGraphWidget(parent=parent,dev=devpulsedVds,plottype='time_domain_from_pulsedVds')
		pulsedVgsplot.show()
###############################################################################################################################