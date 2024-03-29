#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Michael S
# Created Date: Wed June 26 20:52:00 EST 2019
# =============================================================================

import os, sys
import datetime
import configparser
import pandas as pd
from pprint import pprint
lib_path = os.path.abspath(os.path.join('.','python_deribit'))
sys.path.append(lib_path)
import openapi_client

def read_config(config_path, section):
    """
    :param config_path: the location of configuration file
    :param section: section's name
    :return return an object contains configuration info
    """
    # Locate the configuration path
    script_dir = os.path.abspath(os.path.join('.','config'))
    abs_config_path = script_dir + config_path
    # Read configuration 
    config = configparser.ConfigParser()
    config.read(abs_config_path) 
    print(abs_config_path)
    print(script_dir)
    info = {}
    if config.has_section(section):
        params = config.items(section)
        for par in params:
            info[par[0]] = par[1]
    else:
        raise Exception('section {0} not found in the {1} file'.format(section, abs_config_path))
        
    return info

def _load_data(credentials):
    """
    Load data by using debrit API
    Need to put the openapi_client python in parent folder
    :param credentials: dic with key and secret information
    :return return the required data
    """
    conf = openapi_client.Configuration()
    client = openapi_client.api_client.ApiClient(conf)
    publicApi = openapi_client.api.public_api.PublicApi(client)
    response = publicApi.public_auth_get('client_credentials', '', '', credentials['auth_key'], credentials['auth_secret'], '', '', '', scope='session:test wallet:read')
    access_token = response['result']['access_token']
    # Set up token information
    conf_authed = openapi_client.Configuration()
    conf_authed.access_token = access_token
    client_authed =  openapi_client.api_client.ApiClient(conf_authed)
    # Create an instance of the market api class
    market_api_instance = openapi_client.api.market_data_api.MarketDataApi(client_authed)
    currency = 'BTC'
    kind = 'option'
    api_response = market_api_instance.public_get_book_summary_by_currency_get(currency, kind=kind)
    return api_response['result']

def _transform_data(data):
    final_data = []
    #  Generate a table as below format:
    # 'RowID', 'Date', 'volume', 'bid', 'last', 'ask', 'volume', '
    #  %change', 'change','strike'
    for ins in data:
        new_obj = {}
        new_obj['instrument_name'] = ins['instrument_name']
        name_collection = ins['instrument_name'].split('-')  
        if len(name_collection) > 3:
            new_obj['creation_time'] = datetime.datetime.fromtimestamp(ins['creation_timestamp']/1000.0).strftime('%m-%d-%Y')
            new_obj['expiry_date'] = datetime.datetime.strptime(name_collection[1], '%d%b%y').strftime('%m-%d-%Y')
            new_obj['strike_price'] = name_collection[2]
            new_obj['option_type'] = name_collection[3]
        
        new_obj['bid_price'] = ins['bid_price']
        new_obj['ask_price'] = ins['ask_price']
        new_obj['volume'] = ins['volume']
        new_obj['underlying_price'] = ins['underlying_price']
        final_data.append(new_obj)

    return final_data

def save_csv(data):
    df = pd.DataFrame(data)
    df.to_csv(r'final_data.csv',index=False)

if __name__ == "__main__":
    credentials = read_config('\config_prod.ini', 'deribit_credential')
    data = _load_data(credentials)
    final_data = _transform_data(data)
    save_csv(final_data)


# TODO: 
# 1. Add python-mongo connector to push data into mongo
# 2. Add python scheduler to forard data in a regular basis 