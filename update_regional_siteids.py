
from models import Source, Country
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import Session

from pytz import country_timezones
from datetime import datetime

import xlrd 
import xlwt
from xlutils.copy import copy

import os
import argparse
import logging
logger = logging.getLogger()

import requests
import json

from config import read_ini

DESCRIPTION = """
Usage Statistics Manager Database loading tool.
"""

def get_str(row, column_idx):
    value = row[column_idx].value
    if type(value) is float:
        return str(int(value))
    else:
        return str(value) 


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
    matomo_token = config["MATOMO"]["MATOMO_TOKEN"]
    matomo_url =  config["MATOMO"]["MATOMO_URL"]

    # database
    engine = create_engine(database_connection_str)
    connection = engine.connect()
    metadata = MetaData()

    with Session(engine) as session:
        # for each source 
        sources = session.query(Source).all()
        for source in sources:
            if source.type == 'N':
                country = session.query(Country).filter(Country.country_iso == source.country_iso).first()
                if country:
                    logger.debug("Updating siteid for regional source: %s" % source.name)
                    source.site_id = country.site_id
                    source.national_site_id = country.site_id
                    session.commit()
                else:
                    logger.error("Country not found: %s" % source.country_iso)

            if source.type == 'R':
                # if repository source then get the siteid from related country
                country = session.query(Country).filter(Country.country_iso == source.country_iso).first()
                if country:
                    logger.debug("Updating national_siteid for repository source: %s" % source.name)
                    source.national_site_id = country.site_id
                    session.commit()
    
    logger.debug("Done")


    

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

    parser.add_argument("-f",
                        "--excel_file_path",
                        help="excel file path",
                        required=True)

    
    return parser.parse_args()




if __name__ == "__main__":
    main()



