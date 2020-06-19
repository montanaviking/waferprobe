# database packer
# Phil Marsh Carbonics Inc
from analysisdbcreate import *
from sqlalchemy import and_
import datetime

##### add device base table if it hasn't
def __database_packer_device(wd=None):
	wname=wd.wafername.split('meas')[0]
	measurementrun=wd.wafername.split('meas')[1]
	dal=DataAccessLayer()
	dal.connect()
	ses=dal.Session()
	for k,d in wd.DCd.items():
		# pack Idmax and related parameters

		dname=d.devicename.split("__")[1]
		queryDevice=ses.query(Device).filter_by(wafername=wname,measurement_run=measurementrun,wafer_device_name=dname).first()

		if queryDevice==None:        # then need to add device since it's not already in the database
			ses.add(Device(wafername=wname,measurement_run=measurementrun,wafer_device_name=dname,X=d.x_location,Y=d.y_location,total_gate_width=d.devwidth))
			#print("from line 22 databasepacker")
		else:   # modify existing device
			queryDevice.X=d.x_location
			queryDevice.Y=d.y_location
			queryDevice.total_gate_width=d.devwidth
	ses.commit()
		# now add or update data for the device's database entry
		# add |Idmax| data
	dal=DataAccessLayer()
	dal.connect()
	return dal.Session(),wname,measurementrun
###############################################################################
###############################################################################
# family of curves database packer
# wd is the class of the wafer under analysis
# wd.DCd is the class of the device results
################################################################################
def database_pack_foc(wd=None):
	ses,wname,measurementrun=__database_packer_device(wd=wd)
	for k,d in wd.DCd.items():
		if d.Ron_foc()!=None:            # then this is a single-loop transfer curve
			dname=d.devicename.split("__")[1]
			datetime_measurement=datetime.datetime.strptime("".join([d.IVfoc_year," ",d.IVfoc_month," ",d.IVfoc_day," ",d.IVfoc_hour," ",d.IVfoc_minute," ",d.IVfoc_second]),"%Y %m %d %H %M %S")
			q=ses.query(Family_of_Curves).filter_by(wafername=wname, measurement_run=measurementrun, wafer_device_name=dname,temperature=293.).first()  # does the device already have an entry for a single-swept transfer curve?
			if d.ratioRon!=None: # is this an ORTH device?
				ratioRon=float(d.ratioRon)          # the float conversion is necessary because some of these are numpy floats and are not compatible with the database
			else:
				ratioRon=None
			if q==None:      # then need to add device data to database if it exists
					ses.add(Family_of_Curves(wafername=wname,measurement_run=measurementrun,wafer_device_name=dname,temperature=293.,                # primary keys
					                        data_file="".join([d.devicename,"_foc.xls"]),Idmax_1=float(d.Idmax_tf), On_Off_ratio_1=float(d.Idonoffratio_tf), Idmin_1=float(d.Idmin_tf),Igmax_1=float(d.Igmax_tf),IgatIdmin_1=float(d.IgatIdmin_tf),ORTHRatio_Idmax_1=ratioIdmax1,
											Idmax_2=float(d.Idmax_tr), On_Off_ratio_2=float(d.Idonoffratio_tr), Idmin_2=float(d.Idmin_tr),Igmax_2=float(d.Igmax_tr),IgatIdmin_2=float(d.IgatIdmin_tr),ORTHRatio_Idmax_2=ratioIdmax2,
					                        datetime_measurement=datetime_measurement))
			else:   # modify existing device
				# sweep 1
				q.Idmax_1=float(d.Idmax_tf)
				q.On_Off_ratio_1=float(d.Idonoffratio_tf)
				q.Idmin_1=float(d.Idmin_tf)
				q.Igmax_1=float(d.Igmax_tf)
				q.IgatIdmin_1=float(d.IgatIdmin_tf)
				q.ORTHRatio_Idmax_1=ratioIdmax1
				# sweep 2
				q.Idmax_2=float(d.Idmax_tr)
				q.On_Off_ratio_2=float(d.Idonoffratio_tr)
				q.Idmin_2=float(d.Idmin_tr)
				q.Igmax_2=float(d.Igmax_tr)
				q.IgatIdmin_2=float(d.IgatIdmin_tr)
				q.ORTHRatio_Idmax_2=ratioIdmax2

				q.datetime_measurement=datetime_measurement
	ses.commit()
################################################################################

################################################################################
# single-swept transfer curves database packer
################################################################################
def database_pack_transfer(wd=None):
	ses,wname,measurementrun=__database_packer_device(wd=wd)
	for k,d in wd.DCd.items():
		if hasattr(d,"Idmax_t") and d.Idmax_t!=None:
			dname=d.devicename.split("__")[1]
			datetime_measurement=datetime.datetime.strptime("".join([d.IVt_year," ",d.IVt_month," ",d.IVt_day," ",d.IVt_hour," ",d.IVt_minute," ",d.IVt_second]),"%Y %m %d %H %M %S")
			q=ses.query(Transfer_Single).filter_by(wafername=wname,measurement_run=measurementrun,wafer_device_name=dname,Vgs_slew_rate=d.Vgsslew_IVt,Vgs_slew_rate_controlled=False,Vds=d.Vds_IVt,temperature=293.).first()  # does the device already have an entry for a single-swept transfer curve?

			if d.ratioIdmax!=None: # is this an ORTH device?
				ratioIdmax=float(d.ratioIdmax)          # the float conversion is necessary because some of these are numpy floats and are not compatible with the database
			else:
				ratioIdmax=None

			if q==None:      # then need to add device data to database if it exists
					ses.add(Transfer_Single(data_file="".join([d.devicename,"_transfer.xls"]),wafername=wname,measurement_run=measurementrun,wafer_device_name=dname,Vgs_slew_rate=d.Vgsslew_IVt, Vds=float(d.Vds_IVt),temperature=293.,
					                        Idmax=float(d.Idmax_t), On_Off_ratio=float(d.Idonoffratio_t), Idmin=float(d.Idmin_t),Igmax=float(d.Igmax_t),IgatIdmin=float(d.IgatIdmin_t),
					                        ORTHRatio_Idmax=ratioIdmax,
					                        datetime_measurement=datetime_measurement))
			else:   # modify existing device
				q.Idmax=float(d.Idmax_t)
				q.On_Off_ratio=float(d.Idonoffratio_t)
				q.Idmin=float(d.Idmin_t)
				q.Igmax=float(d.Idmax_t)
				q.ORTHRatio_Idmax=ratioIdmax
				q.IgatIdmin=float(d.IgatIdmin_t)
				q.datetime_measurement=datetime_measurement
	ses.commit()
################################################################################
###############################################################################
# single loop transfer curves database packer
################################################################################
def database_pack_1loop_transfer(wd=None):
	ses,wname,measurementrun=__database_packer_device(wd=wd)
	for k,d in wd.DCd.items():
		if hasattr(d,"Idmax_tf") and d.Idmax_tf != None and (not hasattr(d,"Idmax_t3") or d.Idmax_t3==None):            # then this is a single-loop transfer curve
			dname=d.devicename.split("__")[1]
			datetime_measurement=datetime.datetime.strptime("".join([d.IVtfr_year," ",d.IVtfr_month," ",d.IVtfr_day," ",d.IVtfr_hour," ",d.IVtfr_minute," ",d.IVtfr_second]),"%Y %m %d %H %M %S")
			q=ses.query(Transfer_1loop).filter_by(wafername=wname, measurement_run=measurementrun, wafer_device_name=dname, Vgs_slew_rate=d.Vgsslew_IVtfr, Vgs_slew_rate_controlled=False, Vds=d.Vds_IVtfr, temperature=293.).first()  # does the device already have an entry for a single-swept transfer curve?
			if d.ratioIdmaxF!=None: # is this an ORTH device?
					ratioIdmax1=float(d.ratioIdmaxF)          # the float conversion is necessary because some of these are numpy floats and are not compatible with the database
					ratioIdmax2=float(d.ratioIdmaxR)
			else:
				ratioIdmax1=None
				ratioIdmax2=None

			if q==None:      # then need to add device data to database if it exists
					ses.add(Transfer_1loop(data_file="".join([d.devicename,"_transferloop.xls"]),wafername=wname,measurement_run=measurementrun,wafer_device_name=dname,Vgs_slew_rate=d.Vgsslew_IVtfr, Vds=float(d.Vds_IVtfr),temperature=293.,
					                        Idmax_1=float(d.Idmax_tf), On_Off_ratio_1=float(d.Idonoffratio_tf), Idmin_1=float(d.Idmin_tf),Igmax_1=float(d.Igmax_tf),IgatIdmin_1=float(d.IgatIdmin_tf),ORTHRatio_Idmax_1=ratioIdmax1,
											Idmax_2=float(d.Idmax_tr), On_Off_ratio_2=float(d.Idonoffratio_tr), Idmin_2=float(d.Idmin_tr),Igmax_2=float(d.Igmax_tr),IgatIdmin_2=float(d.IgatIdmin_tr),ORTHRatio_Idmax_2=ratioIdmax2,
                                            Hysteresis_voltage12=float(d.Vhyst12()),
					                        datetime_measurement=datetime_measurement))
			else:   # modify existing device
				# sweep 1
				q.Idmax_1=float(d.Idmax_tf)
				q.On_Off_ratio_1=float(d.Idonoffratio_tf)
				q.Idmin_1=float(d.Idmin_tf)
				q.Igmax_1=float(d.Igmax_tf)
				q.IgatIdmin_1=float(d.IgatIdmin_tf)
				q.ORTHRatio_Idmax_1=ratioIdmax1
				# sweep 2
				q.Idmax_2=float(d.Idmax_tr)
				q.On_Off_ratio_2=float(d.Idonoffratio_tr)
				q.Idmin_2=float(d.Idmin_tr)
				q.Igmax_2=float(d.Igmax_tr)
				q.IgatIdmin_2=float(d.IgatIdmin_tr)
				q.ORTHRatio_Idmax_2=ratioIdmax2
				q.Hysteresis_voltage=float(d.Vhyst12())
				q.datetime_measurement=datetime_measurement
	ses.commit()
################################################################################

