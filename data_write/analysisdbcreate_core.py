# Phil Marsh Carbonics
# orm boilerplate
# create database for analysis data

from sqlalchemy import MetaData

from datetime import datetime
from sqlalchemy import (Table, Column, Integer, Numeric,Index, create_engine, String, DateTime, Float,DECIMAL,ForeignKey, Boolean,func,types,text,ForeignKeyConstraint,and_,or_,not_,insert,update)
from sqlalchemy.sql import  select
from sqlalchemy_utils import database_exists
import sys

analysis_db_metadata=MetaData()

thismodule=sys.modules[__name__]


TLMstructure=Table('TLMstructure',analysis_db_metadata,
    Column('name',String(300),index=True,primary_key=True),         # name of the TLM structure
    Column('wafername',String(300),primary_key=True,index=True),
	Column('measurement_run',String(300),primary_key=True,index=True),                                          # number of the measurement
    Column('Vgs_Ron',String(20),primary_key=True,index=True),      # Vgs used to measure the on resistance
    Column('Rc',Float(30),index=True),                              # TLM structure contact resistance in ohm*mm. Gate width MUST be specified for the underlying devices to get an entry here
    Column('Rsh',Float(30),index=True),                              # TLM structure sheet resistance in ohms/square. Gate width MUST be specified for the underlying devices to get an entry here
	Column('minimum_TLM_fitlength',Float(30)),                                # minimum TLM S-D spacing in um which is fitted to a least-squares linear fit line to determine TLM structure Rc and Rsh
    Column('maximum_TLM_fitlength',Float(30))                                 # maximum TLM S-D spacing in um which is fitted to a least-squares linear fit line to determine TLM structure Rc and Rsh
    )


ORTHstructure=Table('ORTHstructure',analysis_db_metadata,
    Column('name',String(300),index=True,primary_key=True),             # name of the ORTH structure
    Column('wafername',String(300),primary_key=True,index=True),
	Column('measurement_run',String(300),primary_key=True,index=True),                                          # number of the measurement
    Column('Vds_trans',String(20),primary_key=True,index=True),               # drain voltage used for transfer curve which determines |Idmax|
    Column('Vgs_trans',String(20),primary_key=True,index=True),             # gate voltage at maximum |Idmax|
    Column('Vgs_Ron',String(20),primary_key=True,index=True),          # Vgs used to measure the on resistance
    Column('ORTHRatio_Idmax',Float(20),index=False),                    # the ration of |Idmax| 0deg device/|Idmax| 90 deg device for orthogonal devices for single transfer curve sweep
    Column('ORTHRatio_Ron',Float(20),index=False)
    )


#DC parameters###############################################################################################
# DC parameters:
# unless otherwise noted, currents are all in mA/mm if the gate widths are specifed.
# Gate widths MUST be specified

Device=Table('Device',analysis_db_metadata,
    # primary keys, uniquely define device measurement - Must be unique in this table
	Column('wafername',String(300),primary_key=True,index=True),
	#Column('measurement_run',String(10),primary_key=True,index=True),                   # number and/or designator of the measurement
	Column('device_name',String(300),primary_key=True,index=True),             # the wafer device name is the device name unique to a device on the wafer mask
    ## geometry parameters of device
	Column('X',Integer,index=True,primary_key=True,autoincrement=False),       # X-location in um on the wafer relative to the wafer's origin
	Column('Y',Integer,index=True,primary_key=True,autoincrement=False),          # Y-location in um on the wafer relative to the wafer's origin
	Column('total_gate_width',Integer,index=True,autoincrement=False),        # total device gate width in um
	Column('gate_length',Float(20)),                              # device actual gate length and/or TLM length in um
    Column('S-D_spacing',Float(20)),                              # device actual source-drain metal spacing
    Column('T-top_length',Float(20)),                              # device actual T-top metal length)
    Column('lead_resistance',Float(20)),                                   # total lead resistance in ohm*mm
    Column('link',String(1000))                                  # link to files processing etc
               )

	# test parameters Note that we must use DECIMAL for floating point numbers which are also primary keys and/or unique
    ##########################################################################################################
	##### single sweep transfer curve swept in the positive direction
	# each Transferdata data set requires a row of this table
DCtransfer=Table('DCtransfer',analysis_db_metadata,
    # primary keys, uniquely define device measurement - Must be unique in this table
	Column('wafername',ForeignKey('Device.wafername'),primary_key=True,index=True),
	Column('measurement_run',String(50),primary_key=True,index=True),                   # number and/or designator of the measurement
	Column('wafer_device_name',ForeignKey('Device.device_name'),primary_key=True,index=True),             # the wafer device name is the device name unique to a device on the wafer mask
    Column('datetime',DateTime,primary_key=True,index=True),                           # date and time of the measurement
	Column('sweep_profile',String(50),primary_key=True,index=True),                     # sweep directions e.g. +-, -+ 0-+-0 or -, were + means sweep Vgs in positive direction (increasing positive gate voltage)
	Column('temperature_C',DECIMAL(5.1),primary_key=True,index=True,default=25.0),
    Column('Vgs_slew_rate',Float(20),index=True),                          # rate of change of gate voltage during Vgs sweep
    Column('Vgs_slew_rate_controlled',Boolean,primary_key=True,index=True,default=False),               # True if slew rate is controlled, false otherwise
	Column('Vds',Float(20),index=True),                 # drain voltage used for this transfer curve

	Column('Idmax',Float(20),index=True),                              # maximum absolute value of drain current from the spline fit of Id(Vgs)
	Column('On_Off_ratio',Float(20),index=True),                       # absolute value of Idmax/Idmin
	Column('Idmin',Float(20),index=True),                              # this is the minimum absolute value of the directly measured drain current
	Column('Igmax',Float(20),index=True),                              # this is the maximum absolute value of the directly measured gate current
    Column('VgsatIdmin',Float(20),index=True),                         # Vgs which minimizes |Id|
	Column('IgatIdmin',Float(20),index=True),                         # |gate current| at Vgs which minimizes |Id|
	Column('gmmax',Float(20),index=True),                                # maximum Gm from single-swept transfer curve measurement as derived from spline fit of Id(Vgs)
    Column('gate_atcompliance',Boolean,index=True,default=False),                  # is drain status at single transfer curve sweep ever not in compliance?
    Column('drain_atcompliance',Boolean,index=True,default=False),                  # is drain status at single transfer curve sweep ever not in compliance?
	##################################################################
	# foreign keys for composite structures
    Column('ORTHstructure_name',ForeignKey('ORTHstructure.name'),index=True),      # ORTH device structure name - based on single-swept transfer curve data
    Column('TLM_structure_name',ForeignKey('TLMstructure.name'),index=True)        # TLM device structure name - based on single-swept foc (family of curves) data Ron
	)

############################################################################################################
# IV family of curves
DCfoc=Table('DCfoc',analysis_db_metadata,
    Column('wafername',ForeignKey('Device.wafername'),primary_key=True,index=True),
	Column('measurement_run',String(50),primary_key=True,index=True),                   # number and/or designator of the measurement
	Column('wafer_device_name',ForeignKey('Device.device_name'),primary_key=True,index=True),             # the wafer device name is the device name unique to a device on the wafer mask
    Column('datetime',DateTime,primary_key=True,index=True),                           # date and time of the measurement
	Column('sweep_profile',DateTime,primary_key=True,index=True),                     # sweep directions e.g. +-, -+ 0-+-0 or -, were + means sweep Vgs in positive direction (increasing positive gate voltage)
	Column('temperature_C',DECIMAL(5.1),primary_key=True,index=True,default=25),
    Column('Vds_slew_rate_controlled',Boolean,default=False),
    Column('Vds_slew_rate',Float(20)),
# data
    Column('Ron',Float(20)),                                                         # on-state resistance which is corrected by the lead resistance
	Column('Idmax(Vds)',Float(20)),
    Column('VdsIdmax',Float(20)),
	Column('gate_atcompliance',Boolean,index=True,default=False),                  # is drain status at single transfer curve sweep ever not in compliance?
    Column('drain_atcompliance',Boolean,index=True,default=False),                  # is drain status at single transfer curve sweep ever not in compliance?
# foreign keys for composite structures
    Column('ORTHstructure_name',ForeignKey('ORTHstructure.name'),index=True),      # ORTH device structure name - based on single-swept transfer curve data
    Column('TLM_structure_name',ForeignKey('TLMstructure.name'),index=True)        # TLM device structure name - based on single-swept foc (family of curves) data Ron
            )

############################################################################################################
# RF parameters
RFSpar=Table('RFSpar',analysis_db_metadata,
    Column('wafername',ForeignKey('Device.wafername'),primary_key=True,index=True),
	Column('measurement_run',String(50),primary_key=True,index=True),                   # number and/or designator of the measurement
	Column('wafer_device_name',ForeignKey('Device.device_name'),primary_key=True,index=True),             # the wafer device name is the device name unique to a device on the wafer mask
    Column('datetime',DateTime,primary_key=True,index=True),                           # date and time of the measurement
    Column('Vds',Float(20),primary_key=True,index=True),                # drain voltage at S-parameter measurement
    Column('Vgs',Float(20),primary_key=True,index=True),                # gate voltage at S-parameter measurement
	Column('temperature_C',DECIMAL(5.1),primary_key=True,index=True,default=25),
    Column('RFGm_frequency',Float(20)),                                             # RF frequency at which RF gm is calculated from S-parameters
# data
    Column('Id',Float(20)),                # drain current (mA/mm) at S-parameter measurement
    Column('gatecompliance',Boolean),                # gate compliance ever occur during measurement?
    Column('draincompliance',Boolean),                # drain compliance ever occur during measurement?

    Column('RFGm',Float(20)),
    Column('fmax',Float(20)),                                                         # on-state resistance which is corrected by the lead resistance
    Column('ft',Float(20))
             )

############################################################################################################
# RF TOI best case (third order intercept) parameters
# RFTOI=Table('RFTOI',analysis_db_metadata,
#     Column('wafername',ForeignKey('Device.wafername'),primary_key=True,index=True),
# 	Column('measurement_run',String(50),primary_key=True,index=True),                   # number and/or designator of the measurement
# 	Column('wafer_device_name',ForeignKey('Device.device_name'),primary_key=True,index=True),             # the wafer device name is the device name unique to a device on the wafer mask
#     Column('datetime',DateTime,primary_key=True,index=True),                           # date and time of the measurement
#     Column('Vds',ForeignKey('TOIdata.Vds'),primary_key=True,index=True),                # drain voltage at TOI measurement
#     Column('Vgs',ForeignKey('TOIdata.Vgs'),primary_key=True,index=True),                # gate voltage at TOI measurement
#     Column('frequency',ForeignKey('TOIdata.frequency'),primary_key=True),                                             # RF frequency in GHz
#     Column('temperature_C',ForeignKey('TOIdata.temperature_C'),primary_key=True),
# # data
#     Column('Id',ForeignKey('TOIdata.Id')),                # drain current (mA/mm) at TOI measurement at optimum impedance and maximum tested RF fundamental power
#     Column('gatecompliance',ForeignKey('TOIdata.gatecompliance'),primary_key=True,index=True),                # gate compliance ever occur during measurement?
#     Column('draincompliance',ForeignKey('TOIdata.draincompliance'),primary_key=True,index=True),                # drain compliance ever occur during measurement?
#     Column('TOI',Float(20)),                                                                # third order output intercept point (dBm)
#     Column('gain',Float(20)),
#     Column('Rhoopt_mag',Float(20)),                                                         # magnitude of the optimum reflection coefficient which maximizes the TOI
#     Column('Rhoopt_ang',Float(20))
#             )
######################################################

##########################################################################################################################################
# Raw stored data
# these data sets are generated and stored during measurement
##########################################################################################################################################
# raw transfer curve data as measured by instrument. These data are not scaled to gate length and no lead resistance has been compensated for
# These are just raw current and voltages as read by the parameter analyzer
# note that the slew rate data are contained in the DCtransfer table.
Transferdata=Table('Transferdata',analysis_db_metadata,
	Column('wafername',ForeignKey('DCtransfer.wafername'),primary_key=True,index=True),
	Column('measurement_run',ForeignKey('DCtransfer.measurement_run'),primary_key=True,index=True),
	Column('wafer_device_name',ForeignKey('DCtransfer.wafer_device_name'),primary_key=True,index=True),
	Column('datetime',ForeignKey('DCtransfer.datetime'),primary_key=True,index=True),
    Column('sweep_profile',ForeignKey('DCtransfer.sweep_profile'),primary_key=True,index=True),                     # sweep directions e.g. +-, -+ 0-+-0 or -, were + means sweep Vgs in positive direction (increasing positive gate voltage)
    Column('temperature_C',ForeignKey('DCtransfer.temperature_C'),primary_key=True,index=True),
    ### now the data
    Column('Vgs',Float(20)),
    Column('Vds',Float(20)),
    Column('Id',Float(20)),
	Column('Ig',Float(20)),
    Column('drainstatus',String(5)),
    Column('gatestatus',String(5)),
	Column('timestamp',Float(20)),
    Column('sweep_number',Integer)
                   )
# # family of curves
FOCdata=Table('FOCdata',analysis_db_metadata,
    Column('wafername',ForeignKey('DCfoc.wafername'),primary_key=True,index=True),
	Column('measurement_run',ForeignKey('DCfoc.measurement_run'),primary_key=True,index=True),
	Column('wafer_device_name',ForeignKey('DCfoc.wafer_device_name'),primary_key=True,index=True),
	Column('datetime',ForeignKey('DCfoc.datetime'),primary_key=True,index=True),
    Column('sweep_profile',ForeignKey('DCfoc.sweep_profile'),primary_key=True,index=True),                     # sweep directions e.g. +-, -+ 0-+-0 or -, were + means sweep Vgs in positive direction (increasing positive gate voltage)
    Column('temperature_C',ForeignKey('DCfoc.temperature_C'),primary_key=True),
    ### now the data
    Column('Vgs',Float(20)),
    Column('Vds',Float(20)),
    Column('Id',Float(20)),
	Column('Ig',Float(20)),
    Column('drainstatus',String(5)),
    Column('gatestatus',String(5)),
	Column('timestamp',Float(20)),
    Column('sweep_number',Integer)
             )
# # S-parameters
RFSpardata=Table('RFSpardata',analysis_db_metadata,
    Column('wafername',ForeignKey('RFSpar.wafername'),primary_key=True,index=True),
	Column('measurement_run',ForeignKey('RFSpar.measurement_run'),primary_key=True,index=True),
	Column('wafer_device_name',ForeignKey('RFSpar.wafer_device_name'),primary_key=True,index=True),
	Column('datetime',ForeignKey('RFSpar.datetime'),primary_key=True,index=True),
    Column('Vds',ForeignKey('RFSpar.Vds'),primary_key=True,index=True),                # drain voltage at S-parameter measurement
    Column('Vgs',ForeignKey('RFSpar.Vgs'),primary_key=True,index=True),                # gate voltage at S-parameter measurement
    Column('temperature_C',ForeignKey('RFSpar.temperature_C'),primary_key=True),
## data
    Column('frequency_GHz',DECIMAL(20,3)),
    Column('S11_re',Float(20)),
    Column('S11_im',Float(20)),
    Column('S21_re',Float(20)),
    Column('S21_im',Float(20)),
    Column('S12_re',Float(20)),
    Column('S12_im',Float(20)),
    Column('S22_re',Float(20)),
    Column('S22_im',Float(20))
               )


#user="mysql+pymysql://montanaviking:nova@localhost"
user="mysql+pymysql://montanaviking:nova@Sibyl"
analysis_db="analysis_test"
analysis_db_engine=create_engine(user)
if not database_exists(user+"/"+analysis_db):
	analysis_db_engine.execute("CREATE DATABASE "+analysis_db)
analysis_db_engine.execute("USE "+analysis_db)
analysis_db_metadata.create_all(analysis_db_engine)
analysis_db_con=analysis_db_engine.connect()
