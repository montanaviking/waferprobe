# Phil Marsh Carbonics
# orm boilerplate


# Phil Marsh Carbonics
# orm boilerplate

from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import (Column, Integer, Numeric, String, DateTime, ForeignKey, Boolean, create_engine)
from sqlalchemy.orm import relationship, backref, sessionmaker
Base=declarative_base()

class DataAccessLayer:
	def __init__(self):
		self.engine=None
		#self.conn_string="mysql+pymysql:///montanaviking:nova@localhost/test"

	def connect(self):
		self.engine=create_engine("mysql+pymysql://montanaviking:nova@localhost/Carbonics_test")
		Base.metadata.create_all(self.engine)
		self.Session=sessionmaker(bind=self.engine)

dal=DataAccessLayer()