
from models import Source
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


    # read excel file
    filename = args.excel_file_path
    wbook = xlrd.open_workbook(filename) 
    sheet = wbook.sheet_by_index(0) 
    first_row = sheet.row(0)  # 1st row  
    column_idx_by_name = dict([ (cell.value, idx)  for idx, cell in enumerate(first_row) ] )
    original_rows_size = sheet.nrows
    original_rows = list([row for row in sheet.get_rows()]) # get all tows
    wbook.release_resources()
    del wbook

    # open excel file for writing
    wbook = xlrd.open_workbook(filename)
    wr_wbook = copy(wbook)
    wr_sheet = wr_wbook.get_sheet(0)

    mandatory_fields = ['namespace_id','source_id', 'name', 'institution', 'type', 'url', 'site_id', 'country_iso', 'token']
    
    for field in mandatory_fields:
        if field not in column_idx_by_name.keys() :
            print( "Mandatory field: " + field + ' not present in excel file')
            exit()


    # database
    engine = create_engine(database_connection_str)
    connection = engine.connect()
    metadata = MetaData()

    with Session(engine) as session:
        
        for row_idx in range(1,original_rows_size):

            row = original_rows[row_idx]

            source_id = get_str(row, column_idx_by_name['namespace_id'] ) + "::" + get_str(row, column_idx_by_name['source_id'] ) 
            
            if source_id.strip() != '': 

                name    = get_str(row, column_idx_by_name['name'] ) 
                type    = get_str(row, column_idx_by_name['type'] )
                site_id = get_str(row, column_idx_by_name['site_id'] )
                

                token   = get_str(row, column_idx_by_name['token'] )
                url     = get_str(row, column_idx_by_name['url'] )
                institution = get_str(row, column_idx_by_name['institution'] )
                country_iso = get_str(row, column_idx_by_name['country_iso'] )
               
                print("Processing source "+source_id)    
                source = Source(source_id=source_id, name=name, type=type, site_id=site_id, auth_token=token, url=url, institution=institution, country_iso=country_iso)  
                existing_source = session.query(Source).filter(Source.source_id == source_id)

                if ( existing_source.count() == 0 ):
                    session.add(source)
                    session.commit()
                    print("Source "+source_id+" added")
                else:
                    print("Source "+source_id+" already exists, updating changes")

                    if ( existing_source.one().auth_token != token ):
                        print("Updating token for source "+source_id)
                        existing_source.update({Source.auth_token: token}, synchronize_session='fetch')
                        session.commit()

                    if ( existing_source.one().name != name ):
                        print("Updating name for source "+source_id)
                        existing_source.update({Source.name: name}, synchronize_session='fetch')
                        session.commit()
                    
                    if ( existing_source.one().type != type ):
                        print("Updating type for source "+source_id)
                        existing_source.update({Source.type: type}, synchronize_session='fetch')
                        session.commit()

                    if ( existing_source.one().url != url ):
                        print("Updating url for source "+source_id)
                        existing_source.update({Source.url: url}, synchronize_session='fetch')
                        session.commit()

                    if ( existing_source.one().institution != institution ):
                        print("Updating institution for source "+source_id)
                        existing_source.update({Source.institution: institution}, synchronize_session='fetch')
                        session.commit()

                    if ( existing_source.one().country_iso != country_iso ):
                        print("Updating country_iso for source "+source_id)
                        existing_source.update({Source.country_iso: country_iso}, synchronize_session='fetch')
                        session.commit()

                    #uptate site_id, national_site_id, regional_site_id
                    if ( existing_source.one().site_id != site_id ):
                        print("Updating site_id for source "+source_id)
                        existing_source.update({Source.site_id: site_id}, synchronize_session='fetch')
                        session.commit()

                 

                        
                    print("Source "+source_id+" processed")

        
    
    return token

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



