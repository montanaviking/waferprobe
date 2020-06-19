# Phil Marsh Carbonics
# orm boilerplate


# Phil Marsh Carbonics
# orm boilerplate

from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import (Column, Integer, Numeric, String, DateTime, ForeignKey, Boolean, create_engine,func,types)
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy_utils import database_exists
Base=declarative_base()
user="mysql+pymysql://montanaviking:nova@localhost"
analysis_db="analysis_test"


class DataAccessLayer:
	def __init__(self):
		#self.engine=None
		self.engine=create_engine(user)
		if not database_exists(user+"/"+analysis_db):
			self.engine.execute("CREATE DATABASE "+analysis_db)
		self.engine.execute("USE "+analysis_db)
		Base.metadata.create_all(self.engine)

	def connect(self):
		self.Session=sessionmaker(bind=self.engine)

class DCdata(Base):
	__tablename__ = 'DCdata'
	unique_devicename=Column(String(500),primary_key=True )
	wafername=Column(String(500), index=True)
	mask_location=Column(String(500), index=True)

dal=DataAccessLayer()
#self.engine=create_engine("mysql+pymysql://montanaviking:nova@localhost/Carbonics_test")