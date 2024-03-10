from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime
from datetime import datetime

"""

"""

SOURCE_TYPE_REPOSITORY = 'R' 
SOURCE_TYPE_NATIONAL   = 'N'
SOURCE_TYPE_REGIONAL   = 'L'

NAMESPACE_OPENDOAR = 'OPENDOAR'
NAMESPACE_SITEID = 'SITEID'

class Source(Model):
    __tablename__ = 'source'

    id = Column(Integer, primary_key=True)
    source_id = Column(String(20), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    url = Column(String(255))
    institution = Column(String(255))
    
    type = Column(String(1), default=SOURCE_TYPE_REPOSITORY )

    site_id = Column(Integer, nullable=False, index=True)
    national_site_id = Column(Integer)
    regional_site_id = Column(Integer, default=1)
    
    auth_token = Column(String(255))

    country_iso = Column(String(2), nullable=False)

    identifier_prefix = Column(String(255))
    identifier_map_regex = Column(String(255))
    identifier_map_replace = Column(String(255))
    identifier_map_filename = Column(String(255))
    identifier_map_type = Column(Integer, nullable=False, default=0) 

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return self.namespace_id + '::' + self.source_id

    
class Country(Model):
    __tablename__ = 'country'

    id = Column(Integer, primary_key=True)
    country_iso = Column(String(2), unique=True, nullable=False)
    site_id = Column(Integer, nullable=False, index=True)
    auth_token = Column(String(255), nullable=False)

    def __repr__(self):
        return self.country_iso

 