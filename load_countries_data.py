from dbschema import Namespace, Source, Country

from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import Session

from pytz import country_timezones

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

    mandatory_fields = ['country_iso', 'token']
    
    for field in column_idx_by_name.keys():
        if field not in mandatory_fields:
            print( "Mandatory field: " + field + ' not present in excel file')
            exit()


    # database
    engine = create_engine(database_connection_str)
    connection = engine.connect()
    metadata = MetaData()

    with Session(engine) as session:
        
        for row_idx in range(1,original_rows_size):

            row = original_rows[row_idx]

            country_iso = get_str(row, column_idx_by_name['country_iso'] )

            if country_iso.strip() != '': 

                token   = get_str(row, column_idx_by_name['token'] )
               
                tokenObj = Country(auth_token=token, country_iso=country_iso)     
                session.merge(tokenObj)

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

    parser.add_argument("-f",
                        "--excel_file_path",
                        help="excel file path",
                        required=True)

    
    return parser.parse_args()

if __name__ == "__main__":
    main()



