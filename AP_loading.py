
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 18:53:38 2020

@author: robinDG
"""
# =============================================================================
import pandas as pd
import time
# =============================================================================

def fetch_LOB_column_names(iLevels=5):
    """
    purpose: build column names for dfLOB 
    """
    tColumnNamesBasis= ['ask price ', 'ask size ', 'bid price ', 'bid size ']
    tColumnNames = [0] * iLevels*4
    for i in range(0,iLevels):    
        tColumnNames[i*4:i*4 + 4] = [name + str(i+1) for name in tColumnNamesBasis]

    return tColumnNames

def basic_info(dfMES, timeDelta):
    """
    purpose: print basic info on loaded LOBSTER data
    """
    iNoHalts = len(dfMES[dfMES["type"]==7])
    dTimePassed = dfMES['time'][len(dfMES)-1] - dfMES['time'][0]

    print(f'Number of halts during trading period: {iNoHalts}')
    print(f'Loading duration: {timeDelta} seconds')
    print(f'Total time passed during trading data: {round(dTimePassed/3600,1)} hours')
    print(f'Number of orders: ', len(dfMES))

def load_data(sStock):
    """
    purpose: get message data and LOB data from stock security 2012 6th of june
    stock is chosen through parameter sStock (e.g. sStock='MSFT')
    For data description: see ReadMe file 
    """
    # fetch data    
    sFilenameMES = sStock + '_2012-06-21_34200000_57600000_message_5.csv'
    sFilenameLOB = sStock + '_2012-06-21_34200000_57600000_orderbook_5.csv'
    timeBef = time.time()
    dfMES = pd.read_csv(sFilenameMES, header=0)
    dfLOB = pd.read_csv(sFilenameLOB, header=0)
    timeAf = time.time()
    timeDelta = timeAf - timeBef
    
    # set column names for both dataframes
    tColumnNamesMES = ('time','type','id','size', 'price','side')
    tColumnNamesLOB = fetch_LOB_column_names()
    dfMES.columns = tColumnNamesMES    
    dfLOB.columns = tColumnNamesLOB
    
    # print some basic info     
#    basic_info(dfMES, timeDelta)
    
    return (dfMES, dfLOB)

