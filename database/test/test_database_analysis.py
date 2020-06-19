# Phil Marsh Carbonics
# orm boilerplate
from analysisdbcreate import *
from sqlalchemy import ForeignKey, Boolean
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import backref,relationship
from sqlalchemy import MetaData
from sqlalchemy import text
from migrate.changeset import *


#
datafilename1="H48meas1__C4_R5_ORTH_9A_transfer.xls"
devicetoadd1="H48meas1__C4_R5_ORTH_9A"
wafername1=devicetoadd1.split('meas1')[0]
measurement_run1=devicetoadd1.split('__')[0]
masklocation1=devicetoadd1.split('__')[1]

datafilename2="H48meas1__C6_R2_ORTH_8A_transfer.xls"
devicetoadd2="H48meas1__C6_R2_ORTH_8A"
wafername2=devicetoadd2.split('meas1')[0]
measurement_run2=devicetoadd1.split('__')[0]
masklocation2=devicetoadd2.split('__')[1]

datafilename3="H48meas2__C6_R2_ORTH_8A_transfer.xls"
devicetoadd3="H48meas2__C6_R2_ORTH_8A"
wafername3=devicetoadd3.split('meas2')[0]
measurement_run3=devicetoadd3.split('__')[0]
masklocation3=devicetoadd3.split('__')[1]

dal=DataAccessLayer()
dal.connect()

#
session=dal.Session()
#queryDC_parameters=session.query(Transfer_Single).join(Device,Device.wafer_device_name==Transfer_Single.wafer_device_name)
#results=queryDC_parameters.filter(Device.wafer_device_name=='C4_R5_ORTH_9A')

queryDC_parameters=session.query(Transfer_Single)
results=queryDC_parameters.filter(Transfer_Single.wafer_device_name=='C6_R2_ORTH_8A')

#print(results)

#
# print("results for device only")
# cnt=results.count()

for r in results:
	r.Idmax=3.3
	session.commit()

for r in results: print(r.Idmax)

rdict=[{u: r.__dict__[u] for u in r.__dict__.keys() if u!='_sa_instance_state'} for r in results]
for r in rdict:
	print(r)

# print("results for IV only")
# rdict=[{u: r.__dict__[u] for u in r.__dict__.keys() if u!='_sa_instance_state'} for r in resultsiv]
# for r in rdict:
# 	print(r)

# if cnt>0:
#	results.delete()

#
#

#p1=Device(wafername=wafername1, measurement_run=measurement_run1,wafer_device_name=masklocation1)
session.add(Device(wafername=wafername1, measurement_run=measurement_run1,wafer_device_name=masklocation1,total_gate_width=None))
p1=Device(wafername=wafername2, measurement_run=measurement_run2,wafer_device_name=masklocation2)
session.add(p1)
p1=Device(wafername=wafername3, measurement_run=measurement_run3,wafer_device_name=masklocation3)
session.add(p1)
session.commit()
p2=Transfer_Single(data_file=datafilename1,wafername=wafername1,measurement_run=measurement_run1,wafer_device_name=masklocation1,Idmax=1.2E-7)
session.add(p2)
p2=Transfer_Single(data_file=datafilename2,wafername=wafername2,measurement_run=measurement_run2,wafer_device_name=masklocation2,Idmax=1.3)
session.add(p2)


p2=Transfer_Single(data_file=datafilename3,wafername=wafername3,measurement_run=measurement_run3,wafer_device_name=masklocation3,Idmax=1.8)
session.add(p2)

session.commit()
