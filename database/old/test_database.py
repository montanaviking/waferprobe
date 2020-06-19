# Phil Marsh Carbonics
# orm boilerplate
from db import *
#
class process(Base):
	__tablename__ = 'process'
	process_name=Column(String(20), primary_key=True)
	process_type=Column(String(50),index=True)
class process_step(Base):
	__tablename__ = 'process_step'
	Process_Step=Column(Integer, primary_key=True)
	Process_Name=Column(String(50),ForeignKey('process.process_name'),index=True)
	Date_Time=Column(DateTime,index=True)
class metal_film(Base):
	__tablename__='metal_film'
	metal_type=Column(String(20),primary_key=True)
	evaporation_equipment=Column(String(20),ForeignKey('equipment.equipment_name'),index=True)
class equipment(Base):
	__tablename__='equipment'
	equipment_name=Column(String(20),primary_key=True)
	equipment_function=Column(String(20),index=True)

	# def __repr__(self):
	# 	return "process(process_name='{self.process_name}', process_type='{self.process_type}')".format(self=self)

dal.connect()
session=dal.Session()
query=session.query(process_step)
resultsall=query.all()
results=query.filter(process_step.Process_Name.contains("Gate"))
rdict=[{u: r.__dict__[u] for u in r.__dict__.keys() if u!='_sa_instance_state'} for r in results.all()]
for r in rdict:
	print(r)
#query.delete()
#p1 = process_step(Process_Name="Gate_Lithography")
session.add(equipment(equipment_name='Temescal1', equipment_function='metal_evaporator'))
session.add(equipment(equipment_name='acid_bay', equipment_function='wet_processing'))
session.commit()
session.add(metal_film(metal_type='Ti',evaporation_equipment='Temescal1'))
session.add(metal_film(metal_type='Al',evaporation_equipment='Temescal1'))

session.commit()