# Phil Marsh Carbonics
# orm boilerplate
from analysisdbcreatetest import *
from sqlalchemy import ForeignKey, Boolean
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import backref,relationship
from sqlalchemy import MetaData
from sqlalchemy import text
from migrate.changeset import *


#
devicetoadd="H48meas1__C4_R5_ORTH_9A"
wafername=devicetoadd.split('meas1')[0]
masklocation=devicetoadd.split('__')[1]
dal.connect()


#dal.engine.execute(text("ALTER TABLE analysis_test.DCdata ADD COLUMN Ron FLOAT"))
session=dal.Session()
query=session.query(DCdata)

dal.engine.execute(text("ALTER TABLE analysis_test.DCdata ADD COLUMN Ron Float"))
DCdata.Ron=Column(types.Float)
	# session=dal.Session()
	# query=session.query(DCdata)
print("made it here")
results=query.filter(DCdata.unique_devicename==devicetoadd)
cnt=results.count()
rdict=[{u: r.__dict__[u] for u in r.__dict__.keys() if u!='_sa_instance_state'} for r in results]
for r in rdict:
	print(r,cnt)
if cnt>0:
	results.delete()

# if not hasattr(DCdata,'Ron'):
# #qlc=text('ALTER TABLE DCdata ADD COLUMN Ron FLOAT')
# 	# dal.engine.execute(text("USE analysis_test"))
# 	dal.engine.execute(text("ALTER TABLE analysis_test.DCdata ADD COLUMN Ron FLOAT"))


p1=DCdata(unique_devicename=devicetoadd,wafername=wafername, mask_location=masklocation, Ron=1.456)
session.add(p1)
session.commit()



#1 = DCdata(unique_devicename=devicetoadd,wafername=wafername, mask_location=masklocation)
#p2 = Process(process_name="Cu-1", process_type="metal_evaporation")
#session.add(p1)
#session.add(p2)
#session.commit()