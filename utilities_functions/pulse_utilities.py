# Phil Marsh Carbonics Inc
##################################################################################################################################################
# autoscale the scope
# pulsesetbot, pulsesettop are the lower and upper voltages to be output by the pulse generator
# top is the high voltage that the scope will read whereas bot is the low voltage that the scope will be expected to read - these are guesses and the initial scope voltage scale MUST be able to read these levels upon start of the autoscaleing
# returns:
# minv = minimum voltage on the selected channel
# maxv = maximum measured voltage from the scope on the selected channel
# actualpulsewidth = pulse width setting of the pulse generator
# actualvoltagelow = pulse generator minimum voltage setting as read back from pulse generator
# actualvoltagehigh = pulse generator maximum voltage setting as read back from pulse generator
def autoscale(pulse=None, scope=None, pulsewidth=None, period=None, channel=1, scopebottomscale_guess=-2, scopetopscale_guess=0., pulsegen_min_voltage=-1.5, pulsegen_max_voltage=1, probeattenuation=1, pulsegeneratoroutputZ="INF"):
	midscale= (scopetopscale_guess + scopebottomscale_guess)/2.
	mindeltascale=0.004*probeattenuation
	#actualpulsewidth,actualvoltagelow,actualvoltagehigh=pulse.set_pulsesetup_singlepulse(polarity="-",pulsewidth=pulsewidth,period=period,voltagelow=pulsegen_min_voltage,voltagehigh=pulsegen_max_voltage,pulsegeneratoroutputZ=pulsegeneratoroutputZ)
	actualpulsewidth,actualvoltagelow,actualvoltagehigh=pulse.set_pulsesetup_continuous(polarity="-",pulsewidth=pulsewidth,period=period,voltagelow=pulsegen_min_voltage,voltagehigh=pulsegen_max_voltage,pulsegeneratoroutputZ=pulsegeneratoroutputZ)
	pulse.pulsetrainon()
	scope.set_channel(displaychannel=True, channel=channel, bottomscale=scopebottomscale_guess - (midscale - scopebottomscale_guess), topscale=scopetopscale_guess + (scopetopscale_guess - midscale), probeattenuation=probeattenuation)
	if channel==1: scope.set_channel(displaychannel=False,channel=2)
	elif channel==2: scope.set_channel(displaychannel=False,channel=1)
	soaktime=scope.capture2ndpulse()
	print("Vtop = ",scope.get_minmaxvoltage(channel=channel, top=True))
	minv=scope.get_minmaxvoltage(channel=channel, top=False)
	maxv=scope.get_minmaxvoltage(channel=channel, top=True)
	if minv<100 and maxv<100:
		scopetopscale_guess=maxv+0.2*(maxv-minv)
		scopebottomscale_guess=minv-0.2*(maxv-minv)
	atminscale=scope.set_channel(displaychannel=True, channel=channel, bottomscale=scopebottomscale_guess, topscale=scopetopscale_guess, probeattenuation=probeattenuation)
	##maxv=scope.get_minmaxvoltage(channel=1, scopetopscale_guess=True)
	atminscale=False              # is the signal too small to fill the scope range and is the scope already set to its minimum scale?
	while (minv>100 or minv<=scope.get_voltagerange(channel=channel)[0]):
		#midscale= (scopebottomscale_guess + scopetopscale_guess)/2.
		midscale=(scope.get_voltagerange(channel=channel)[0]+scope.get_voltagerange(channel=channel)[1])/2.
		scopebottomscale_guess= scopebottomscale_guess - max(abs(midscale - scope.get_voltagerange(channel=channel)[0]),mindeltascale)
		scopetopscale_guess=scopetopscale_guess+max(abs(midscale - scope.get_voltagerange(channel=channel)[0]),mindeltascale)               # added July 15, 2019
		#scopebottomscale_guess = scope.get_voltagerange(channel=channel)[0]-
		atminscale=scope.set_channel(displaychannel=True, channel=channel, bottomscale=scopebottomscale_guess, topscale=scopetopscale_guess, probeattenuation=probeattenuation)
		soaktime=scope.capture2ndpulse()
		minv=scope.get_minmaxvoltage(channel=channel, top=False)
		print("from pulse_utilities.py line 38 loop scopebottomscale_guess,minv,atminscale ", scopebottomscale_guess,scopetopscale_guess, minv,maxv,atminscale)
	scopebottomscale_guess= minv-0.2*abs(scope.get_voltagerange(channel=channel)[0]-scope.get_voltagerange(channel=channel)[1])
	atminscale=scope.set_channel(displaychannel=True, channel=channel, bottomscale=scopebottomscale_guess, topscale=scopetopscale_guess, probeattenuation=probeattenuation)
	soaktime=scope.capture2ndpulse()
	maxv=scope.get_minmaxvoltage(channel=channel, top=True)
	minv=scope.get_minmaxvoltage(channel=channel, top=False)
	print("line 44 pulse_utilities.py minv, maxv",minv,maxv)
	atminscale=False
	while (maxv>100. or maxv>=scope.get_voltagerange(channel=channel)[1]) or (minv>100 or minv<=scope.get_voltagerange(channel=channel)[0]):
		while (maxv>100. or maxv>=scope.get_voltagerange(channel=channel)[1]):
			midscale=(scope.get_voltagerange(channel=channel)[0]+scope.get_voltagerange(channel=channel)[1])/2.
			scopetopscale_guess=scopetopscale_guess+max(abs(midscale - scope.get_voltagerange(channel=channel)[1]),mindeltascale)
			atminscale=scope.set_channel(displaychannel=True, channel=channel, bottomscale=scopebottomscale_guess, topscale=scopetopscale_guess, probeattenuation=probeattenuation)
			soaktime=scope.capture2ndpulse()
			maxv=scope.get_minmaxvoltage(channel=channel, top=True)
			print("from pulse_utilities.py line 52 scopebottomscale_guess,maxv,atminscale ", scopebottomscale_guess,scopetopscale_guess, minv,maxv,atminscale)
		minv=scope.get_minmaxvoltage(channel=channel, top=False)

		while (minv>100 or minv<=scope.get_voltagerange(channel=channel)[0]):
			#midscale= (scopebottomscale_guess + scopetopscale_guess)/2.
			midscale=(scope.get_voltagerange(channel=channel)[0]+scope.get_voltagerange(channel=channel)[1])/2.
			scopebottomscale_guess= scopebottomscale_guess - max(abs(midscale - scope.get_voltagerange(channel=channel)[0]),mindeltascale)
			atminscale=scope.set_channel(displaychannel=True, channel=channel, bottomscale=scopebottomscale_guess, topscale=scopetopscale_guess, probeattenuation=probeattenuation)
			soaktime=scope.capture2ndpulse()
			minv=scope.get_minmaxvoltage(channel=channel, top=False)
			print("from pulse_utilities.py line 63 loop scopebottomscale_guess,minv,atminscale ", scopebottomscale_guess,scopetopscale_guess, minv,maxv,atminscale)
		maxv=scope.get_minmaxvoltage(channel=channel, top=True)
		scopebottomscale_guess=min(minv - 0.2 * abs(maxv - minv), minv - 0.005)
		scopetopscale_guess=max(maxv + 0.2 * abs(maxv - minv), maxv + 0.005)
		scope.set_channel(displaychannel=True, channel=channel, bottomscale=scopebottomscale_guess, topscale=scopetopscale_guess, probeattenuation=probeattenuation)
		soaktime=scope.capture2ndpulse()
		minv=scope.get_minmaxvoltage(channel=channel, top=False)
		maxv=scope.get_minmaxvoltage(channel=channel, top=True)
	print("line 67 pulse_utilities.py 2nd minv, maxv",minv,maxv)
	# scopebottomscale_guess=min(minv - 0.2 * abs(maxv - minv), minv - 0.005)
	# scopetopscale_guess=max(maxv + 0.2 * abs(maxv - minv), maxv + 0.005)
	# scope.set_channel(displaychannel=True, channel=channel, bottomscale=scopebottomscale_guess, topscale=scopetopscale_guess, probeattenuation=probeattenuation)
	# #scope.set_dualchannel(ch1_bottomscale=scopebottomscale_guess,ch1_topscale=scopetopscale_guess,ch2_bottomscale=scopebottomscale_guess,ch2_topscale=scopetopscale_guess)
	# soaktime=scope.capture2ndpulse()
	# minv=scope.get_minmaxvoltage(channel=channel, top=False)
	# maxv=scope.get_minmaxvoltage(channel=channel, top=True)
	# #midscale= (minv + scopetopscale_guess) / 2.
	# print("from pulse_utilities.py line 76 minv,scopebottomscale_guess,maxv,scopetopscale_guess",scopebottomscale_guess,scopetopscale_guess, minv,maxv,atminscale)
	# if minv>100: raise ValueError("signal minimum too low")
	# if maxv>100: raise ValueError("signal maximum too high")
	scopebottomscale_guess=min(minv-0.15*abs(maxv-minv),minv-0.0025)
	#scopebottomscale_guess= minv - 0.01        # changed
	scopetopscale_guess=max(maxv+0.15*abs(maxv-minv),maxv+0.0025)
	print("from pulse_utilities.py line 82 scopebottomscale_guess,scopetopscale_guess,minv,maxv",scopebottomscale_guess,scopetopscale_guess, minv,maxv,atminscale)
	scope.set_channel(displaychannel=True, channel=channel, bottomscale=scopebottomscale_guess, topscale=scopetopscale_guess, probeattenuation=probeattenuation)
	soaktime=scope.capture2ndpulse()
	minvlast=minv
	maxvlast=maxv
	minv=scope.get_minmaxvoltage(channel=channel, top=False)
	maxv=scope.get_minmaxvoltage(channel=channel, top=True)
	print("from pulse_utilities.py line 89 scopebottomscale_guess,scopetopscale_guess,minv,maxv",scopebottomscale_guess,scopetopscale_guess, minv,maxv,atminscale)
	atminscale=False
	while (minv>1E10 or maxv>1E10):
		bottomscale,topscale=scope.get_voltagerange(channel=channel)
		deltascale=(topscale-bottomscale)/32.                   # volts/1/4 div
		if minv>1E10:           # then correct lower bounds saturation
			scopebottomscale_guess=scopebottomscale_guess - deltascale
		scope.set_channel(displaychannel=True, channel=channel, bottomscale=scopebottomscale_guess, topscale=scopetopscale_guess, probeattenuation=probeattenuation)
		soaktime=scope.capture2ndpulse()
		minv=scope.get_minmaxvoltage(channel=channel, top=False)
		maxv=scope.get_minmaxvoltage(channel=channel, top=True)
		bottomscale,topscale=scope.get_voltagerange(channel=channel)
		deltascale=(topscale-bottomscale)/32.                   # volts/1/4 div
		if maxv>1E10:
			scopetopscale_guess=scopetopscale_guess + deltascale
		scope.set_channel(displaychannel=True, channel=channel, bottomscale=scopebottomscale_guess, topscale=scopetopscale_guess, probeattenuation=probeattenuation)
		soaktime=scope.capture2ndpulse()
		minv=scope.get_minmaxvoltage(channel=channel, top=False)
		maxv=scope.get_minmaxvoltage(channel=channel, top=True)
	return minv,maxv,actualpulsewidth,actualvoltagelow,actualvoltagehigh