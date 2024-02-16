from sqlalchemy import create_engine, MetaData, Table, Integer, String, \
    Column, DateTime, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from datetime import datetime


import os
import argparse
import logging

from config import read_ini

logger = logging.getLogger()

Base = declarative_base()

SOURCE_TYPE_REPOSITORY = 'R' 
SOURCE_TYPE_NATIONAL   = 'N'
SOURCE_TYPE_REGIONAL   = 'L'

NAMESPACE_OPENDOAR = 'OPENDOAR'
NAMESPACE_SITEID = 'SITEID'

class Source(Base):
    __tablename__ = 'source'
    source_id = Column(String(20), primary_key=True)
    namespace_id = Column(String(15), ForeignKey('namespace.namespace_id'), primary_key=True)

    name = Column(String(255), nullable=False)
    url = Column(String(255))
    institution = Column(String(255))
    country_iso = Column(String(2), ForeignKey('country.country_iso'), nullable=False)

    type = Column(String(1), default=SOURCE_TYPE_REPOSITORY )

    site_id = Column(Integer, nullable=False)
    token = Column(String(255))

    created_on = Column(DateTime(), default=datetime.now)
    updated_on = Column(DateTime(), default=datetime.now, onupdate=datetime.now)
    
    namespace = relationship("Namespace", back_populates="sources")
       
class Namespace(Base):
    __tablename__ = 'namespace'
    namespace_id = Column(String(15), primary_key=True)
    name = Column(String(255), nullable=False)
    
    sources = relationship("Source", back_populates="namespace")

class Country(Base):
    __tablename__ = 'country'
    country_iso = Column(String(2), primary_key=True)
    auth_token = Column(String(255), nullable=False)
    
DESCRIPTION = """
Usage Statistics Manager Database creation tool.
"""

def main():

    args = parse_args()

    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.WARNING

    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)
    logger.debug("Verbose: %s" % args.verbose)

      #config
    config = read_ini(args.config_file_path);
    database_connection_str = config["DB"]["CONNECTION"] 

    engine = create_engine(database_connection_str)
    connection = engine.connect()
    metadata = MetaData()

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        namespace_opendoar = Namespace(namespace_id=NAMESPACE_OPENDOAR, name='OpenDOAR ID')
        namespace_siteid = Namespace(namespace_id=NAMESPACE_SITEID, name='Matomo Site ID')
    
        session.add_all([namespace_opendoar,namespace_siteid])
        session.commit()


def parse_args():

    parser = argparse.ArgumentParser(description=DESCRIPTION)
    
    parser.add_argument("-v",
                        "--verbose",
                        help="increase output verbosity",
                        default=False,
                        action="store_true")

    parser.add_argument("-c",
                    "--config_file_path",
                    default='config.ini',
                    help="config file",
                    required=False)

      
    return parser.parse_args()


if __name__ == "__main__":
    main()

