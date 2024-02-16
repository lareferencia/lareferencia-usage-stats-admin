from dbschema import Namespace, Source

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

    mandatory_fields = ['namespace_id', 'source_id', 'name', 'institution', 'type', 'url', 'site_id', 'country_iso', 'token']
    
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

            namespace_id = get_str(row, column_idx_by_name['namespace_id'] ) 
            source_id = get_str(row, column_idx_by_name['source_id'] ) 
            
            if namespace_id.strip() != '' and  source_id.strip() != '': 

                name    = get_str(row, column_idx_by_name['name'] ) 
                type    = get_str(row, column_idx_by_name['type'] )
                site_id = get_str(row, column_idx_by_name['site_id'] )
                token   = get_str(row, column_idx_by_name['token'] )
                url     = get_str(row, column_idx_by_name['url'] )
                institution = get_str(row, column_idx_by_name['institution'] )
                country_iso = get_str(row, column_idx_by_name['country_iso'] )
               
                #check si el sitio ya existe en matotmo
                if site_id is None or site_id.strip() == "":

                    print("Celda site_id vacía, creando sitio en matomo")
                    
                    try:
                        site_name = country_iso + " - " + source_id + " - " + name
                        timezone = get_timezone_from_iso(country_iso)
                        create_site(matomo_url, matomo_token, site_name, url, timezone)
                        
                        #Obtener el nuevo site_id y guardarlo en la base y en el excel
                        site_id = get_site_id(matomo_url, matomo_token, url)
                        print (site_id)

                        #print("Writing site_id "+new_site_id+" on "+str(row_idx)+"-"+str(column_idx_by_name['site_id']))
                        wr_sheet.write(row_idx, column_idx_by_name['site_id'], site_id)
                        
                    except Exception as e:
                        print (e)
                    

                # #Si el registro aún no tiene token
                if token is None or token.strip() == "":
                    #print("Celda token vacía")
                    set_site_access(matomo_url, matomo_token, site_id, country_iso)
                    
                    #Escribir el token del país en la celda correspondiente
                    token = get_token(country_iso, connection, metadata, engine)
                   
                    #print("Writing token "+country_token+" on "+str(row_idx)+"-"+str(column_idx_by_name['token']))
                    wr_sheet.write(row_idx, column_idx_by_name['token'], token)
                    
                source = Source(namespace_id=namespace_id, source_id=source_id, name=name, type=type, site_id=site_id, token=token, url=url, institution=institution, country_iso=country_iso)  
                existing_source = session.query(Source).filter(Source.namespace_id == namespace_id, Source.source_id == source_id)

                if ( existing_source.count() == 0 ):
                    session.add(source)
                    session.commit()
                    print("Source "+namespace_id+"-"+source_id+" added")
                else:
                    print("Source "+namespace_id+"-"+source_id+" already exists, updating changes")

                    if ( site_id is not None and site_id.strip() != "" and str(existing_source.one().site_id) != str(site_id)  ):
                        print("Updating site_id for source "+namespace_id+"-"+source_id)
                        existing_source.update({Source.site_id: site_id}, synchronize_session='fetch')
                        session.commit()

                    if ( existing_source.one().token != token ):
                        print("Updating token for source "+namespace_id+"-"+source_id)
                        existing_source.update({Source.token: token}, synchronize_session='fetch')
                        session.commit()

                    if ( existing_source.one().name != name ):
                        print("Updating name for source "+namespace_id+"-"+source_id)
                        existing_source.update({Source.name: name}, synchronize_session='fetch')
                        session.commit()
                    
                    if ( existing_source.one().type != type ):
                        print("Updating type for source "+namespace_id+"-"+source_id)
                        existing_source.update({Source.type: type}, synchronize_session='fetch')
                        session.commit()

                    if ( existing_source.one().url != url ):
                        print("Updating url for source "+namespace_id+"-"+source_id)
                        existing_source.update({Source.url: url}, synchronize_session='fetch')
                        session.commit()

                    if ( existing_source.one().institution != institution ):
                        print("Updating institution for source "+namespace_id+"-"+source_id)
                        existing_source.update({Source.institution: institution}, synchronize_session='fetch')
                        session.commit()

                        
                    print("Source "+namespace_id+"-"+source_id+" processed")

        wr_wbook.save('updated_%s_%s' % (datetime.now().strftime("%Y%m%d_%H%M%S"),filename) )        


def get_token(country_iso, connection, metadata, engine):
    token = ''

    country = Table('country', metadata, autoload=True, autoload_with=engine)

    query = select([country.columns.auth_token]).where(country.columns.country_iso == country_iso)
    token = connection.execute(query).scalar()
    
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


def create_site(matomo_url, matomo_token, site_name, urls, timezone):
    print(site_name)
    r = requests.get(matomo_url + '/index.php?module=API&method=SitesManager.addSite&siteName=' + site_name + '&urls=' + urls + '&timezone=' + timezone + '&token_auth=' + matomo_token + '&force_api_session=1')
    print(r.status_code)


def get_timezone_from_iso(country):
    
    try:
        timezones = country_timezones(country)
    except:
        print('TimeZone: UTC')
        print("{} does not appear to be a valid ISO 3166 country code.".format(country))
        return 'UTC'

    #timezones = country_timezones(country)
    
    if not len(timezones):
        print('TimeZone: UTC')
        print("{} does not appear to be a valid ISO 3166 country code.".format(country))
        return 'UTC'
    else:
        print('TimeZone: '+timezones[0])
        return timezones[0] 
            

def get_site_id(matomo_url, matomo_token, urls):
    r3 = requests.get( matomo_url + '/index.php?module=API&method=SitesManager.getSitesIdFromSiteUrl&url=' + urls + '&format=JSON&token_auth=' + matomo_token + '&force_api_session=1').text
    print (r3)
    new_site_id = (json.loads(r3[1:-1])['idsite'])
    return new_site_id


def set_site_access(matomo_url, matomo_token, new_site_id, country):
    user_login = get_username_from_iso(country)
    r2 = requests.get(matomo_url + '/index.php?module=API&method=UsersManager.setUserAccess&userLogin=' + user_login + '&access=write&idSites=' + new_site_id+'&token_auth=' + matomo_token + '&force_api_session=1')

def get_username_from_iso(country):
    return 'admin'

    user_login = 'nodo' + country.lower()
    return user_login

if __name__ == "__main__":
    main()



