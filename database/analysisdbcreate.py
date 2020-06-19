# Phil Marsh Carbonics
# orm boilerplate
# create database for analysis data


from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import (Column, Integer, Numeric, String, DateTime, Float,DECIMAL,ForeignKey, Boolean, create_engine,func,types,text,ForeignKeyConstraint)
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy_utils import database_exists
import sys
Base=declarative_base()

thismodule=sys.modules[__name__]

class DataAccessLayer:
	def __init__(self):
		self.user="mysql+pymysql://montanaviking:nova@localhost"
		self.analysis_db="analysis_test"
		self.engine=create_engine(self.user)
		if not database_exists(self.user+"/"+self.analysis_db):
			self.engine.execute("CREATE DATABASE "+self.analysis_db)
		self.engine.execute("USE "+self.analysis_db)
		Base.metadata.create_all(self.engine)

	def connect(self):
		self.Session=sessionmaker(bind=self.engine)

	# def add_column(self,tablename=None, columnname=None,datatype="String(100)"):
	# 	if tablename==None or columnname==None or columnname=="" or tablename=="":
	# 		raise ValueError("ERROR! no table and/or no column name given!")
	# 	tbl=getattr(thismodule,tablename)
	# 
	# 	dt=getattr(types,datatype)
	# 	if not hasattr(tbl,columnname):
	# 		self.engine.execute(text("ALTER TABLE "+self.analysis_db+"."+tablename+" ADD COLUMN "+columnname+" "+ datatype))
	# 		setattr(tbl,columnname,Column(dt))

# general device characteristics
# the wafername is the unique name of the wafer e.g. H45, FL15, etc..
# the measurement_run refers to the particular measurement on the wafer, e.g. meas1, meas2, etc... usually performed after a process step. Wafers are typically measured several times during processing
# the wafer_device_name is the unique device designator within a wafer - this uniquely identifies a device on a wafer
# the data_file is the filename associated with the device measurement done to produce the respective parameters


class Device(Base):
	__tablename__ = 'Device'
	wafername=Column(String(300), index=True,primary_key=True)               # e.g. H45, FL15
	measurement_run=Column(String(300),index=True,primary_key=True )         # e.g. H45meas1, FL15meas2 etc....
	wafer_device_name=Column(String(300),index=True,primary_key=True)         # e.g. C5_R4_DV1_D33
	mask_name=Column(String(200),index=True)
	X=Column(Integer,index=True,primary_key=True,autoincrement=False)       # X-location in um on the wafer relative to the wafer's origin
	Y=Column(Integer,index=True,primary_key=True,autoincrement=False)          # Y-location in um on the wafer relative to the wafer's origin
	total_gate_width=Column(Integer,index=True,autoincrement=False)        # total device gate width in um
	gate_length=Column(Integer,index=True,autoincrement=False)              # device actual gate length and/or TLM length in um
	#measurement_timestamp=Column(DateTime,index=True,primary_key=True)

#DC parameters
class Transfer_Single(Base):
	__tablename__ = 'Transfer_curve_single'
	# source data file
	data_file=Column(String(200),index=True)
	# foreign keys
	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
	# test parameters Note that we must use DECIMAL for floating point numbers which are also primary keys and/or unique
	Vgs_slew_rate=Column(DECIMAL(4,1),primary_key=True,index=True)                          # rate of change of gate voltage during Vgs sweep
	Vgs_slew_rate_controlled=Column(Boolean,primary_key=True,index=True,default=False)               # True if slew rate is controlled, false otherwise
	Vds=Column(DECIMAL(4,3),primary_key=True,index=True)
	datetime_measurement=Column(DateTime)                           # date and time of the measurement
	temperature=Column(DECIMAL(4,1),primary_key=True,index=True,default=295)
	#polynomialfitorder=Column(Float(20))                            # order of polynomial used to fit Id(Vgs) to smooth it for calculation of Gm
	# measured parameters
	Idmax=Column(Float(20),index=True)                              # maximum absolute value of drain current
	On_Off_ratio=Column(Float(20),index=True)                       # absolute value of Idmax/Idmin
	Idmin=Column(Float(20),index=True)                              # this is the minimum absolute value of the drain current
	Igmax=Column(Float(20),index=True)                              # this is the maximum absolute value of the gate current
	ORTHRatio_Idmax=Column(Float(20),index=True)                    # the ration of |Idmax| 0deg device/|Idmax| 90 deg device for orthogonal devices
	IgatIdmin=Column(Float(20),index=True)                          # |gate current| at Vgs which minimizes |Id|

	#__table_args__ = (ForeignKeyConstraint([wafername,measurement_run,wafer_device_name],[Device.wafername,Device.measurement_run,Device.wafer_device_name]),{})

# this is one Vgs loop transfer curve - i.e. Vgs is swept from Vgs start to Vgs stop to Vgs start
class Transfer_1loop(Base):
	__tablename__ = 'Transfer_curve_1loop'
	# source data file
	data_file=Column(String(200),index=True)
	# foreign keys
	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
	# test parameters. Note that we must use DECIMAL for floating point numbers which are also primary keys and/or unique
	datetime_measurement=Column(DateTime)                           # date and time of the measurement
	Vgs_slew_rate=Column(DECIMAL(4,1),primary_key=True,index=True)                         # rate of change of gate voltage during Vgs sweep
	Vgs_slew_rate_controlled=Column(Boolean,primary_key=True,index=True,default=False)               # True if slew rate is controlled, false otherwise
	Vds=Column(DECIMAL(4,3),primary_key=True,index=True)               # drain voltage used in this measurement
	temperature=Column(DECIMAL(4,1),primary_key=True,index=True,default=295)
	#polynomialfitorder=Column(Float(20))                            # order of polynomial used to fit Id(Vgs) to smooth it for calculation of Gm
	# measured parameters
	Idmax_1=Column(Float(20),index=True)                    # maximum |Id| (absolute value of the drain current) for first portion of Vgs sweep
	Idmax_2=Column(Float(20),index=True)                    # maximum |Id| for 2nd portion of Vgs sweep
	#
	On_Off_ratio_1=Column(Float(20),index=True)
	On_Off_ratio_2=Column(Float(20),index=True)
	# minimum drain current (mA/mm)
	Idmin_1=Column(Float(20),index=True)
	Idmin_2=Column(Float(20),index=True)
	# maximum gate current(mA/mm)
	Igmax_1=Column(Float(20),index=True)
	Igmax_2=Column(Float(20),index=True)
	IgatIdmin_1=Column(Float(20),index=True)                # |gate current| at Vgs which minimizes |Id| for the 1st sweep
	IgatIdmin_2=Column(Float(20),index=True)                # |gate current| at Vgs which minimizes |Id| for the 2nd sweep
	# orthogonal device performance
	ORTHRatio_Idmax_1=Column(Float(20),index=True)                    # the ration of |Idmax| 0deg device/|Idmax| 90 deg device for orthogonal devices for the 1st sweep
	ORTHRatio_Idmax_2=Column(Float(20),index=True)                    # the ration of |Idmax| 0deg device/|Idmax| 90 deg device for orthogonal devices for the 2nd sweep
	# hysteresis voltage i.e. the maximum |Vgs| difference between 1st and 2nd sweeps of the Id(Vgs)
	Hysteresis_voltage12=Column(Float(20),index=True)

class Transfer_2loop(Base):
	__tablename__ = 'Transfer_curve_2loop'
	# source data file
	data_file=Column(String(200),index=True)
	# foreign keys
	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
	# test parameters
	datetime_measurement=Column(DateTime)                           # date and time of the measurement
	Vgs_slew_rate=Column(DECIMAL(4,1),primary_key=True,index=True)                         # rate of change of gate voltage during Vgs sweep
	Vgs_slew_rate_controlled=Column(Boolean,primary_key=True,index=True,default=False)               # True if slew rate is controlled, false otherwise
	Vds=Column(DECIMAL(4,3),primary_key=True,index=True)               # drain voltage used in this measurement
	temperature=Column(DECIMAL(4,1),primary_key=True,index=True,default=295)
	#polynomialfitorder=Column(Float(20))                            # order of polynomial used to fit Id(Vgs) to smooth it for calculation of Gm
	# measured parameters
	Idmax_1=Column(Float(20),index=True)
	Idmax_2=Column(Float(20),index=True)
	Idmax_3=Column(Float(20),index=True)
	Idmax_4=Column(Float(20),index=True)
	#
	On_Off_ratio_1=Column(Float(20),index=True)
	On_Off_ratio_2=Column(Float(20),index=True)
	On_Off_ratio_3=Column(Float(20),index=True)
	On_Off_ratio_4=Column(Float(20),index=True)
	#
	Idmin_1=Column(Float(20),index=True)
	Idmin_2=Column(Float(20),index=True)
	Idmin_3=Column(Float(20),index=True)
	Idmin_4=Column(Float(20),index=True)
	#
	Igmax_1=Column(Float(20),index=True)
	Igmax_2=Column(Float(20),index=True)
	Igmax_3=Column(Float(20),index=True)
	Igmax_4=Column(Float(20),index=True)
	IgatIdmin_1=Column(Float(20),index=True)                # |gate current| at Vgs which minimizes |Id| for the 1st sweep
	IgatIdmin_2=Column(Float(20),index=True)                # |gate current| at Vgs which minimizes |Id| for the 2nd sweep
	IgatIdmin_3=Column(Float(20),index=True)                # |gate current| at Vgs which minimizes |Id| for the 3rd sweep
	IgatIdmin_4=Column(Float(20),index=True)                # |gate current| at Vgs which minimizes |Id| for the 4th sweep
	# orthogonal device performance
	ORTHRatio_Idmax_1=Column(Float(20),index=True)                    # the ration of |Idmax| 0deg device/|Idmax| 90 deg device for orthogonal devices for the 1st sweep
	ORTHRatio_Idmax_2=Column(Float(20),index=True)                    # the ration of |Idmax| 0deg device/|Idmax| 90 deg device for orthogonal devices for the 2nd sweep
	ORTHRatio_Idmax_3=Column(Float(20),index=True)                    # the ration of |Idmax| 0deg device/|Idmax| 90 deg device for orthogonal devices for the 3rd sweep
	ORTHRatio_Idmax_4=Column(Float(20),index=True)                    # the ration of |Idmax| 0deg device/|Idmax| 90 deg device for orthogonal devices for the 4th sweep
	# hysteresis voltage i.e. the maximum |Vgs| difference between 1st and 2nd sweeps of the Id(Vgs)
	Hysteresis_voltage12=Column(Float(20),index=True)

# Note: there can be only one set of Vgs and Vds values per measurement run for the foc.
# If you want to change the Vds and Vgs sweeps, you will need to designate another measurement run
class Family_of_Curves(Base):
	__tablename__='Family_of_curves'
	# source data file
	data_file=Column(String(200),index=True)
	# foreign keys
	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
	# test parameters
	# Vds_start=Column(DECIMAL(4,3),primary_key=True)             # starting value of the Vds sweep (voltage setting not measured Vds) however, if the set voltage is not available, then use the measured voltage
	# Vds_stop=Column(DECIMAL(4,3),primary_key=True)              # ending value of the Vds sweep (voltage setting not measured Vds) however, if the set voltage is not available, then use the measured voltage
	# nVds=Column(Integer,autoincrement=False,primary_key=True)   # number of Vds points in sweep
	# Vgs_start=Column(DECIMAL(4,3),primary_key=True)             # starting value of the Vgs sweep (voltage setting not measured Vds) however, if the set voltage is not available, then use the measured voltage
	# Vgs_stop=Column(DECIMAL(4,3),primary_key=True)              # ending value of the Vgs sweep (voltage setting not measured Vds) however, if the set voltage is not available, then use the measured voltage
	#nVgs=Column(Integer,autoincrement=False,primary_key=True)   # number of Vds points in sweep
	datetime_measurement=Column(DateTime)                           # date and time of the measurement
	temperature=Column(DECIMAL(4,1),primary_key=True,index=True,default=295)
	# measured parameters
	Ron=Column(Float(20),index=True)
	RonVgs=Column(Float(20),index=True)                                 # Vgs used to measure Ron, TLM structures, and ORTH Ron ratio
	Rsh=Column(Float(20),index=True)                                    # if this is part of a TLM structure, this is that TLM structure's calculated sheet resistance in ohms/square
	Rc=Column(Float(20),index=True)                                    # if this is part of a TLM structure, this is that TLM structure's calculated contact resistance in ohm*mm
	Ron_linfitfract=Column(Float(20),index=True)                        # fraction of Vds used to do least squares linear fit to extract Ron
	TLMminlengthfit=Column(Float(20),index=True)                       # this is the lower bound of TLM structure lengths in um used to calculate the least-squares linear fit to extract the TLM parameters Rsh and Rc
	TLMmaxlengthfit=Column(Float(20),index=True)                       # this is the upper bound of TLM structure lengths in um used to calculate the least-squares linear fit to extract the TLM parameters Rsh and Rc
	TLMlinfitquality=Column(Float(20),index=True)                   # quality parameter to eliminate outliers for the least squares linear fit of Rons used to calculate TLM Rc and Rsh minimum of 0=use all points to a maximum of 1=throw out points to get perfect fit -> two point linear fit
	ORTHRatio_Ron=Column(Float(20),index=True)                      # Ron ratio if this is an orthogonal structure

class RF_linear_parameters(Base):
	__tablename__ = 'RF_linear_parameters'
	data_file=Column(String(200),index=True)
	# foreign keys
	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
	# measurement conditions
	datetime_measurement=Column(DateTime)                           # date and time of the measurement
	Vds=Column(DECIMAL(4,3),primary_key=True,index=True)            # actual value
	Vgs=Column(DECIMAL(4,3),primary_key=True,index=True)
	temperature=Column(DECIMAL(4,1),primary_key=True,index=True,default=295)
	# measured DC parameters during RF measurement
	Id=Column(Float(20),index=True)                 # mA/mm
	Ig=Column(Float(20),index=True)                 # mA/mm
	drainstatus=(String(1))
	gatestatus=(String(1))
	# RF parameters
	ft=Column(Float(20),index=True)
	fmax=Column(Float(20),index=True)
	RFGm=Column(Float(20),index=True)                   # equivalent RF Gm (transconductance)
	RFGm_frequency=Column(Float(20),index=True)         # RF frequency where the RF Gm is tabulated
#
###########
#Tabulated as neasured and derived data arrays
# tabulated raw DC data array for single-swept transfer curve
#####################################################################################################################
# single-swept transfer curve
#####################################################################################################################
class Data_Transfer_Single(Base):        # Single-swept transfer curve
	__tablename__ = 'Data_transfer'
	index=Column(Integer,autoincrement=False,primary_key=True)
	# Device
	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
	# test parameters
	Vgs_slew_rate=Column(ForeignKey(Transfer_Single.Vgs_slew_rate),primary_key=True,index=True)         # this is a measured value and may or may not match the prescribed value in Tranfer_Single
	Vgs_slew_rate_controlled=Column(ForeignKey(Transfer_Single.Vgs_slew_rate_controlled),primary_key=True,index=True)      # True if slew rate is controlled, false otherwise
	Vds_requested=Column(ForeignKey(Transfer_Single.Vds),primary_key=True,index=True)      # the requested Vds value
	Vgs_requested=Column(DECIMAL(4,3),index=True)      # the requested Vgs value
	temperature=Column(ForeignKey(Transfer_Single.temperature),primary_key=True,index=True)
	# measured parameters.
	Vds=Column(Float(20))                # Vds is a measured value and may or may not match the requested value
	Vgs=Column(Float(20))                # Vgs is the measured gate voltage and may or may not match the requested value
	Id=Column(Float(20))
	drainstatus=(String(1))
	gatestatus=(String(1))

class Data_Transfer_Single_splinefit(Base):        # spline fit of Single-swept transfer curve
	__tablename__ = 'Data_transfer_spline'
	index=Column(Integer,autoincrement=False,primary_key=True)
	# Device
	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
	# test parameters
	Vgs_slew_rate=Column(ForeignKey(Transfer_Single.Vgs_slew_rate),primary_key=True,index=True)         # this is a measured value and may or may not match the prescribed value in Tranfer_Single
	Vgs_slew_rate_controlled=Column(ForeignKey(Transfer_Single.Vgs_slew_rate_controlled),primary_key=True,index=True)      # True if slew rate is controlled, false otherwise
	Vds_requested=Column(ForeignKey(Transfer_Single.Vds),primary_key=True,index=True)      # the requested Vds value
	temperature=Column(ForeignKey(Transfer_Single.temperature),primary_key=True,index=True)
	# measured parameters.
	Vgs=Column(Float(20))                # Vgs are the Vgs points from the spline fit
	Id=Column(Float(20))                # spline fit of Id
	Gm=Column(Float(20))                # Gm extracted from spline fit of Id

#####################################################################################################################
########## one loop transfer curve
#####################################################################################################################
class Data_Transfer_1loop_1(Base):        # first sweep of single loop-swept transfer curve through one loop of Vgs
	__tablename__ = 'Data_1-loop_transfer_1st'
	index=Column(Integer,autoincrement=False,primary_key=True)
	# Device
	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
	# test parameters
	Vgs_slew_rate=Column(ForeignKey(Transfer_1loop.Vgs_slew_rate),primary_key=True,index=True)         # this is a measured value and may or may not match the prescribed value in Tranfer_Single
	Vgs_slew_rate_controlled=Column(ForeignKey(Transfer_1loop.Vgs_slew_rate_controlled),primary_key=True,index=True)      # True if slew rate is controlled, false otherwise
	Vds_requested=Column(ForeignKey(Transfer_1loop.Vds),primary_key=True,index=True)      # the requested Vds value
	Vgs_requested=Column(DECIMAL(4,3),index=True)      # the requested Vgs value
	temperature=Column(ForeignKey(Transfer_1loop.temperature),primary_key=True,index=True) # in the future, this is a measured value and may or may not match the prescribed value in Tranfer_Single
	# measured parameters
	Vds=Column(Float(20),index=True)                    # Vds is a measured value and may or may not match the requested value
	Vgs=Column(Float(20),index=True)                    # Vgs is the measured gate voltage and may or may not match the requested value
	Id=Column(Float(20),index=True)
	drainstatus=(String(1))
	gatestatus=(String(1))

# class Data_Transfer_1loop_1_splinefit(Base):        # spline fit
# 	__tablename__ = 'Data_1-loop_transfer_1st_spline'
# 	index=Column(Integer,autoincrement=False,primary_key=True)
# 	# Device
# 	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
# 	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
# 	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
# 	# test parameters
# 	Vgs_slew_rate=Column(ForeignKey(Transfer_1loop.Vgs_slew_rate),primary_key=True,index=True)         # this is a measured value and may or may not match the prescribed value in Tranfer_Single
# 	Vgs_slew_rate_controlled=Column(ForeignKey(Transfer_1loop.Vgs_slew_rate_controlled),primary_key=True,index=True)      # True if slew rate is controlled, false otherwise
# 	Vds_requested=Column(ForeignKey(Transfer_1loop.Vds),primary_key=True,index=True)      # the requested Vds value
# 	temperature=Column(ForeignKey(Transfer_1loop.temperature),primary_key=True,index=True)
# 	# measured parameters.
# 	Vgs=Column(Float(20))                # Vgs are the Vgs points from the spline fit
# 	Id=Column(Float(20))                # spline fit of Id
# 	Gm=Column(Float(20))                # Gm extracted from spline fit of Id

class Data_Transfer_1loop_2(Base):        # second sweep of singl loop-swept transfer curve through one loop of Vgs
	__tablename__ = 'Data_1-loop_transfer_2nd'
	index=Column(Integer,autoincrement=False,primary_key=True)
	# Device
	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
	# test parameters
	Vgs_slew_rate=Column(ForeignKey(Transfer_1loop.Vgs_slew_rate),primary_key=True,index=True)         # this is a measured value and may or may not match the prescribed value in Tranfer_Single
	Vgs_slew_rate_controlled=Column(ForeignKey(Transfer_1loop.Vgs_slew_rate_controlled),primary_key=True,index=True)      # True if slew rate is controlled, false otherwise
	Vds_requested=Column(ForeignKey(Transfer_1loop.Vds),primary_key=True,index=True)      # the requested Vds value
	Vgs_requested=Column(DECIMAL(4,3),index=True)      # the requested Vgs value
	temperature=Column(ForeignKey(Transfer_1loop.temperature),primary_key=True,index=True) # in the future, this is a measured value and may or may not match the prescribed value in Tranfer_Single
	# measured parameters
	Vds=Column(Float(20),index=True)                    # Vds is a measured value and may or may not match the requested value
	Vgs=Column(Float(20),index=True)                    # Vgs is the measured gate voltage and may or may not match the requested value
	Id=Column(Float(20),index=True)
	drainstatus=(String(1))
	gatestatus=(String(1))

# class Data_Transfer_1loop_2_splinefit(Base):        # spline fit
# 	__tablename__ = 'Data_1-loop_transfer_2nd_spline'
# 	index=Column(Integer,autoincrement=False,primary_key=True)
# 	# Device
# 	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
# 	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
# 	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
# 	# test parameters
# 	Vgs_slew_rate=Column(ForeignKey(Transfer_1loop.Vgs_slew_rate),primary_key=True,index=True)         # this is a measured value and may or may not match the prescribed value in Tranfer_Single
# 	Vgs_slew_rate_controlled=Column(ForeignKey(Transfer_1loop.Vgs_slew_rate_controlled),primary_key=True,index=True)      # True if slew rate is controlled, false otherwise
# 	Vds_requested=Column(ForeignKey(Transfer_1loop.Vds),primary_key=True,index=True)      # the requested Vds value
# 	temperature=Column(ForeignKey(Transfer_1loop.temperature),primary_key=True,index=True)
# 	# measured parameters.
# 	Vgs=Column(Float(20))                # Vgs are the Vgs points from the spline fit
# 	Id=Column(Float(20))                # spline fit of Id
# 	Gm=Column(Float(20))                # Gm extracted from spline fit of Id
###############################################################################################################
# ######################### two loop transfer curve############################################################
##############################################################################################################
#
class Data_Transfer_2loop_1(Base):        # first sweep of single loop-swept transfer curve through one loop of Vgs
	__tablename__ = 'Data_2-loop_transfer_1st'
	index=Column(Integer,autoincrement=False,primary_key=True)
	# Device
	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
	# test parameters
	Vgs_slew_rate=Column(ForeignKey(Transfer_2loop.Vgs_slew_rate),primary_key=True,index=True)         # this is a measured value and may or may not match the prescribed value in Tranfer_Single
	Vgs_slew_rate_controlled=Column(ForeignKey(Transfer_2loop.Vgs_slew_rate_controlled),primary_key=True,index=True)      # True if slew rate is controlled, false otherwise
	Vds_requested=Column(ForeignKey(Transfer_2loop.Vds),primary_key=True,index=True)      # the requested Vds value
	Vgs_requested=Column(DECIMAL(4,3),index=True)      # the requested Vgs value
	temperature=Column(ForeignKey(Transfer_2loop.temperature),primary_key=True,index=True) # in the future, this is a measured value and may or may not match the prescribed value in Tranfer_Single
	# measured parameters
	Vds=Column(Float(20),index=True)                    # Vds is a measured value and may or may not match the requested value
	Vgs=Column(Float(20),index=True)                    # Vgs is the measured gate voltage and may or may not match the requested value
	Id=Column(Float(20),index=True)
	drainstatus=(String(1))
	gatestatus=(String(1))
# class Data_Transfer_2loop_1_splinefit(Base):        # spline fit
# 	__tablename__ = 'Data_2-loop_transfer_1st_spline'
# 	index=Column(Integer,autoincrement=False,primary_key=True)
# 	# Device
# 	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
# 	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
# 	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
# 	# test parameters
# 	Vgs_slew_rate=Column(ForeignKey(Transfer_2loop.Vgs_slew_rate),primary_key=True,index=True)         # this is a measured value and may or may not match the prescribed value in Tranfer_Single
# 	Vgs_slew_rate_controlled=Column(ForeignKey(Transfer_2loop.Vgs_slew_rate_controlled),primary_key=True,index=True)      # True if slew rate is controlled, false otherwise
# 	Vds_requested=Column(ForeignKey(Transfer_2loop.Vds),primary_key=True,index=True)      # the requested Vds value
# 	temperature=Column(ForeignKey(Transfer_2loop.temperature),primary_key=True,index=True)
# 	# measured parameters.
# 	Vgs=Column(Float(20))                # Vgs are the Vgs points from the spline fit
# 	Id=Column(Float(20))                # spline fit of Id
# 	Gm=Column(Float(20))                # Gm extracted from spline fit of Id

class Data_Transfer_2loop_2(Base):        # second sweep of singl loop-swept transfer curve through one loop of Vgs
	__tablename__ = 'Data_2-loop_transfer_2nd'
	index=Column(Integer,autoincrement=False,primary_key=True)
	# Device
	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
	# test parameters
	Vgs_slew_rate=Column(ForeignKey(Transfer_2loop.Vgs_slew_rate),primary_key=True,index=True)         # this is a measured value and may or may not match the prescribed value in Tranfer_Single
	Vgs_slew_rate_controlled=Column(ForeignKey(Transfer_2loop.Vgs_slew_rate_controlled),primary_key=True,index=True)      # True if slew rate is controlled, false otherwise
	Vds_requested=Column(ForeignKey(Transfer_2loop.Vds),primary_key=True,index=True)      # the requested Vds value
	Vgs_requested=Column(DECIMAL(4,3),index=True)      # the requested Vgs value
	temperature=Column(ForeignKey(Transfer_2loop.temperature),primary_key=True,index=True) # in the future, this is a measured value and may or may not match the prescribed value in Tranfer_Single
	#measured parameters
	Vds=Column(Float(20),index=True)                    # Vds is a measured value and may or may not match the requested value
	Vgs=Column(Float(20),index=True)                    # Vgs is the measured gate voltage and may or may not match the requested value
	Id=Column(Float(20),index=True)
	drainstatus=(String(1))
	gatestatus=(String(1))
# class Data_Transfer_2loop_2_splinefit(Base):        # spline fit
# 	__tablename__ = 'Data_2-loop_transfer_2nd_spline'
# 	index=Column(Integer,autoincrement=False,primary_key=True)
# 	# Device
# 	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
# 	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
# 	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
# 	# test parameters
# 	Vgs_slew_rate=Column(ForeignKey(Transfer_2loop.Vgs_slew_rate),primary_key=True,index=True)         # this is a measured value and may or may not match the prescribed value in Tranfer_Single
# 	Vgs_slew_rate_controlled=Column(ForeignKey(Transfer_2loop.Vgs_slew_rate_controlled),primary_key=True,index=True)      # True if slew rate is controlled, false otherwise
# 	Vds_requested=Column(ForeignKey(Transfer_2loop.Vds),primary_key=True,index=True)      # the requested Vds value
# 	temperature=Column(ForeignKey(Transfer_2loop.temperature),primary_key=True,index=True)
# 	# measured parameters.
# 	Vgs=Column(Float(20))                # Vgs are the Vgs points from the spline fit
# 	Id=Column(Float(20))                # spline fit of Id
# 	Gm=Column(Float(20))                # Gm extracted from spline fit of Id

class Data_Transfer_2loop_3(Base):        # first sweep of single loop-swept transfer curve through one loop of Vgs
	__tablename__ = 'Data_2-loop_transfer_3rd'
	index=Column(Integer,autoincrement=False,primary_key=True)
	# Device
	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
	# test parameters
	Vgs_slew_rate=Column(ForeignKey(Transfer_2loop.Vgs_slew_rate),primary_key=True,index=True)         # this is a measured value and may or may not match the prescribed value in Tranfer_Single
	Vgs_slew_rate_controlled=Column(ForeignKey(Transfer_2loop.Vgs_slew_rate_controlled),primary_key=True,index=True)      # True if slew rate is controlled, false otherwise
	Vds_requested=Column(ForeignKey(Transfer_2loop.Vds),primary_key=True,index=True)      # the requested Vds value
	Vgs_requested=Column(DECIMAL(4,3),index=True)      # the requested Vgs value
	temperature=Column(ForeignKey(Transfer_2loop.temperature),primary_key=True,index=True) # in the future, this is a measured value and may or may not match the prescribed value in Tranfer_Single
	#measured parameters
	Vds=Column(Float(20),index=True)                    # Vds is a measured value and may or may not match the requested value
	Vgs=Column(Float(20),index=True)                    # Vgs is the measured gate voltage and may or may not match the requested value
	Id=Column(Float(20),index=True)
	drainstatus=(String(1))
	gatestatus=(String(1))
# class Data_Transfer_2loop_3_splinefit(Base):        # spline fit
# 	__tablename__ = 'Data_2-loop_transfer_3rd_spline'
# 	index=Column(Integer,autoincrement=False,primary_key=True)
# 	# Device
# 	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
# 	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
# 	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
# 	# test parameters
# 	Vgs_slew_rate=Column(ForeignKey(Transfer_2loop.Vgs_slew_rate),primary_key=True,index=True)         # this is a measured value and may or may not match the prescribed value in Tranfer_Single
# 	Vgs_slew_rate_controlled=Column(ForeignKey(Transfer_2loop.Vgs_slew_rate_controlled),primary_key=True,index=True)      # True if slew rate is controlled, false otherwise
# 	Vds_requested=Column(ForeignKey(Transfer_2loop.Vds),primary_key=True,index=True)      # the requested Vds value
# 	temperature=Column(ForeignKey(Transfer_2loop.temperature),primary_key=True,index=True)
# 	# measured parameters.
# 	Vgs=Column(Float(20))                # Vgs are the Vgs points from the spline fit
# 	Id=Column(Float(20))                # spline fit of Id
# 	Gm=Column(Float(20))                # Gm extracted from spline fit of Id

class Data_Transfer_2loop_4(Base):        # second sweep of singl loop-swept transfer curve through one loop of Vgs
	__tablename__ = 'Data_2-loop_transfer_4th'
	index=Column(Integer,autoincrement=False,primary_key=True)
	# Device
	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
	# test parameters
	Vgs_slew_rate=Column(ForeignKey(Transfer_2loop.Vgs_slew_rate),primary_key=True,index=True)         # this is a measured value and may or may not match the prescribed value in Tranfer_Single
	Vgs_slew_rate_controlled=Column(ForeignKey(Transfer_2loop.Vgs_slew_rate_controlled),primary_key=True,index=True)      # True if slew rate is controlled, false otherwise
	Vds_requested=Column(ForeignKey(Transfer_2loop.Vds),primary_key=True,index=True)      # the requested Vds value
	Vgs_requested=Column(DECIMAL(4,3),index=True)      # the requested Vgs value
	temperature=Column(ForeignKey(Transfer_2loop.temperature),primary_key=True,index=True) # in the future, this is a measured value and may or may not match the prescribed value in Tranfer_Single
	#measured parameters	Vds=Column(Float(20),index=True)                    # Vds is a measured value and may or may not match the requested value
	Vgs=Column(Float(20),index=True)                    # Vgs is the measured gate voltage and may or may not match the requested value
	Id=Column(Float(20),index=True)
	drainstatus=(String(1))
	gatestatus=(String(1))
# class Data_Transfer_2loop_4_splinefit(Base):        # spline fit
# 	__tablename__ = 'Data_2-loop_transfer_4th_spline'
# 	index=Column(Integer,autoincrement=False,primary_key=True)
# 	# Device
# 	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
# 	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
# 	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
# 	# test parameters
# 	Vgs_slew_rate=Column(ForeignKey(Transfer_2loop.Vgs_slew_rate),primary_key=True,index=True)         # this is a measured value and may or may not match the prescribed value in Tranfer_Single
# 	Vgs_slew_rate_controlled=Column(ForeignKey(Transfer_2loop.Vgs_slew_rate_controlled),primary_key=True,index=True)      # True if slew rate is controlled, false otherwise
# 	Vds_requested=Column(ForeignKey(Transfer_2loop.Vds),primary_key=True,index=True)      # the requested Vds value
# 	temperature=Column(ForeignKey(Transfer_2loop.temperature),primary_key=True,index=True)
# 	# measured parameters.
# 	Vgs=Column(Float(20))                # Vgs are the Vgs points from the spline fit
# 	Id=Column(Float(20))                # spline fit of Id
# 	Gm=Column(Float(20))                # Gm extracted from spline fit of Id
###############################################################################################################################################################
# done with transfer curves
################################################################################################################################################################

###############################################################################################################################################################
# S-parameter data
################################################################################################################################################################
class S_parameters(Base):
	__tablename__='S_parameters'
	wafername=Column(ForeignKey(Device.wafername),primary_key=True,index=True)
	measurement_run=Column(ForeignKey(Device.measurement_run),primary_key=True,index=True)
	wafer_device_name=Column(ForeignKey(Device.wafer_device_name),primary_key=True,index=True)
	# measurement conditions
	Vds=Column(ForeignKey(RF_linear_parameters.Vds),primary_key=True,index=True)
	Vgs=Column(ForeignKey(RF_linear_parameters.Vgs),primary_key=True,index=True)
	frequency=Column(Float(20))                     # frequency in GHz
	S11re=Column(Float(20))                         # real part
	S11im=Column(Float(20))                         # imaginary part
	S21re=Column(Float(20))                         # real part
	S21im=Column(Float(20))                         # imaginary part
	S12re=Column(Float(20))                         # real part
	S12im=Column(Float(20))                         # imaginary part
	S22re=Column(Float(20))                         # real part
	S22im=Column(Float(20))                         # imaginary part
