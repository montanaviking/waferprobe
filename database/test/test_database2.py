# Phil Marsh Carbonics
# orm boilerplate
from carbonicstestdb import *
from sqlalchemy import ForeignKey, Boolean
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import backref,relationship
from sqlalchemy import MetaData
#
class XCompany_or_Location(Base):
	__tablename__ = 'XCompany_or_Location'
	Company=Column(String(1000),primary_key=True )
	Area_of_Expertise_Product=Column(String(500))
	Contact_Person=Column(String(500) )
	Company_Address=Column(String(1000))
	Main_Phone=Column(String(50))
	Fax=Column(String(50))

class XContact_Person(Base):
	__tablename__ = 'XContact_Person'
	__table_args__=(ForeignKeyConstraint(['Company'],['XCompany_or_Location.Company']),)
	Name=Column(String(50), primary_key=True)
	Area_of_Expertise_Product=Column(String(500))
	Job_Title=Column(String(100))
	Email=Column(String(100))
	Office_Phone=Column(String(500))
	Mobile_Phone=Column(String(5000))
	Mobile_Phone_2=Column(String(500))
	home_phone=Column(String(100))
	fax=Column(String(500))
	Personal_Website=Column(String(600))
	Company=Column(String(500),ForeignKey('XCompany_or_Location.Company'))
	# def __repr__(self):
	# 	return "XContact_Person(Name='{self.Name}', Area_of_Expertise_Product='{self.Area_of_Expertise_Product}',Company='{self.Company}')".format(self=self)
#ForeignKeyConstraint(['XCompany_or_Location.Contact_Person'],['XContact_Person.Name'])

print(str())

dal.connect()
session=dal.Session()
query=session.query(XContact_Person)

resultsall=query.all()
#resultsjoin=
#print("all =",resultsall)
results=query.filter(XContact_Person.Company.contains("Maury"))
# results2=results.filter(XContact_Person.Name.contains("Step"))
rdict=[{u: r.__dict__[u] for u in r.__dict__.keys() if u!='_sa_instance_state'} for r in results.all()]
for r in rdict:
	print(r)

#query.delete()
p1 = XContact_Person(Name="Joe cool",Area_of_Expertise_Product="cool dude", Company="Joe Cool's company")
#p2 = Process(process_name="Cu-1", process_type="metal_evaporation")
session.add(p1)
#session.add(p2)
session.commit()