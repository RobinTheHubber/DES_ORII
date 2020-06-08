# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 18:53:38 2020

@author: robinDG
"""
# =============================================================================
import numpy as np
import pandas as pd
import AP_plots as lplt
import AP_loading as load
import AP_comp_util as lcomp
import AP_model_est as est
# =============================================================================

"""
current decisions: 
        - AES non-aggregated of ask/bid 
        - queue's non-aggregated over ask/bid
"""

def main():
    sStock1 = 'AAPL'
    sStock2 = 'MSFT'
        
    (dfMES, dfLOB) = load.load_data(sStock2)    
        
    dfQPrice = pd.read_csv('QPrices.csv') # Queue prices 
    dfMESExt = pd.read_csv('MESExt.csv') # messages extended with corresponding rankings/queue indices
    dfQ = pd.read_csv('Qsizes_nonagg.csv') # Queue sizes (non standardized into AES)

    # truncate first 8 minutes of the time period (irregular patters at trade venue opening)    
    dfQ = dfQ.iloc[22000:,:]
    dfMESExt = dfMESExt.iloc[22000:,:]

    ##### non-aggregated both over queue's and AES #####
    (ldfMES, dfQst) = lcomp.prepare_data(dfMESExt, dfQ) # splits messages into different queue's and standardize LOB into AES units
    

    rankset = [i for i in range(-5,6) if i !=0]
    for i in range(0,10):
        iRank = str(rankset[i])
        lcomp.add_order_size_bef_event(ldfMES[i], dfQst, iRank) # add queue size before event
        
        
    """
    estimate model 1: dictionary with a dic for every queue with keys -5,-4,-3,-2,-1,1,2.3,4 and 5 (non string keys!). 
    # This dic for a given queue contains 3 dataframes, with keys 'intensity', 'CIlo' and 'CIup'. 
    # every df has a column for every parameter which are: 
    # lambda_cap: event frequency at queue size
    # lambda_l, lambda_c and lambda_m: three arrival/departure intensities 
    # rho: loading at queue size
    """
    dicModel1 = est.estimate_model_1(ldfMES, 0.4) 
    # plot results by indexing a queue out of model dictionary dicModel1. Example: first ask queue
    lplt.plot_intensities(dicModel1[-1])



    # uncomment below when wanting to use AGGREGATED model!!
    
    
    ##### same process, but aggregated queue's and AES over bid/ask#####
#    dfQagg = pd.DataFrame()
#    for i in range(1,6):
#        dfQagg[str(i)] = (dfQ[str(i)] + dfQ[str(-i)])/2
#    
#    (ldfMESagg, dfQstAgg) = lcomp.prepare_data(dfMESExt, dfQagg, bAgg=True) # splits messages into different queue's and standardize LOB into AES units
#
#    ranksetAgg = [i for i in range(1,6)]
#    for i in range(0,5):
#        iRank = str(ranksetAgg[i])
#        lcomp.add_order_size_bef_event(ldfMESagg[i], dfQstAgg, iRank) # add queue size before event
#
#    
#    lIntensitiesAgg = est.estimate_model_1(ldfMESagg,0.25) # estima parameters of model 1, a dataframe of intensities for every queue
#    lplt.plot_intensities(lIntensitiesAgg[:2])
#    
    
if __name__ == "__main__":
    main()    
    