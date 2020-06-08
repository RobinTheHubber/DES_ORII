# -*- coding: utf-8 -*-
"""
Created on Sat Jun  6 15:02:37 2020

@author: robinDG
"""

import pandas as pd
import numpy as np

    
def prepare_data(dfMESExt, dfQ, bAgg=False):
    """
    purpose: 
        1. split dfMES into df's grouped by queue 
        2. convert queue's into AES units with bid/ask non-aggregated AES(Q_i, side)
    note: bAgg is False by default which means queue's will get seperated based on bid/ask en AES will be computed separately as well
    """
    dfQst = dfQ.copy()
    
    # split dfMES based on queue nr
    ldfMES = [df for _, df in dfMESExt.groupby(['ranking'])]
    ldfMES = [ldfMES[i]for i in range(0,12) if i != 5 and i != 11] # drop hidden orders and orders pertaining to queues outside rank 5
    
    # if AES must be aggregated: concatenate messages for queue -i and queue i
    if bAgg:
        ldfMESagg = []
        for i in range(0,5):
            ldfMESagg.append(pd.concat([ldfMES[i], ldfMES[i+5]], axis=0))
            ldfMESagg[i]['ranking'] = abs(ldfMESagg[i]['ranking']) # -i ranking -> i (w.l.o.g)
        ldfMES = ldfMESagg
       
    # compute AES grouped by queue, non-aggregated over bid/ask
    lAES = [df.mean()['size'] for df in ldfMES]
    
    # standardize by AES, rounding above to prevent sparsity
    for i in range(len(lAES)):
        iRank = ldfMES[i]['ranking'].iloc[0] # get queue ranking        
        dfQst[str(iRank)] = np.ceil(dfQ[str(iRank)] / lAES[i])
        dfQst[str(iRank)] = dfQst[str(iRank)].astype(int)
    
    return (ldfMES, dfQst)


def get_ATS(dfMES,dfLOB):
    """
    compute average trade size, i.e. only use market orders, for all LOB data "
    """
    
    # compute ATS for all market orders
    types = dfMES['type']
    lSelectAll = [iType in [5,4] for iType in types]
    dfMESall = dfMES[lSelectAll]
    dATSall = dfMESall['size'].mean()    
    
    # compute ATS without hidden order execution    
    lSelectNoHid = [iType == 4  for iType in types]
    dfMESnoHid = dfMES[lSelectNoHid]
    dATSnoHid = dfMESnoHid['size'].mean()    

    return(dATSall, dATSnoHid)
    
    
def spread_Ts(dfLOB, dfMES):
    """
    purpose: compute spread and fraction of time that spread == 1 tick (= 100)
    """
    psSpread = (dfLOB['ask price 1'] - dfLOB['bid price 1'])
    dTs = psSpread.value_counts()[100] / len(psSpread) 
    psSpreadNoHid = psSpread[dfMES['type'] != 5]
    dTsNoHid = psSpreadNoHid.value_counts()[100] / len(psSpread) 
    print(f'Ts with all orders: {dTs}')
    print(f'Ts excluding hidden orderders: {dTsNoHid}\n\n')    

    
    
def test_hidden_order_aftereffect(dfLOB,dfMES):
    """
    purpose: test whether residu of partially executed hidden market orders becomes visible in form of extra limit order seen in the LOB data/queue sizes.
    """    
    # extract prices from 
    lPriceCols = [0,2,4,6,8,10,12,14,16,18]    
    dfPrices = dfLOB[dfMES['type']==5].iloc[:,lPriceCols] # queue prices after hidden order 
    dfPriceLobs = dfLOB.iloc[:,lPriceCols] # all queue prices
    
    # check for every hidden order
    for i in range(1,len(dfPrices)):
        vPricesAfter = dfPrices.iloc[i] # queue price after hidden order 
        vPricesBef = dfPriceLobs.iloc[vPricesAfter.name,:] # queue price before hidden order 
        
        # if some hiddenorder got "converted", i.e. become visible in the form of, limit orders 
        # then this would return True for at least one price
        vBool = vPricesAfter > vPricesBef 
        if sum(vBool)>0:
            print(vPricesBef[vBool], vPricesAfter[vBool])
            
    
    
def add_order_size_bef_event(dfMES, dfQst, iRank):
    """
    purpose: add ordersize before every event to the dfMES pertaining to a specific queue
    dfMES contains all orders for a given queue
    """
    # retrieve sizes for queue for every event on this queue
    vInd= dfMES.index # indices at which an event has just occurred at this queue
    psSizeQueue = dfQst[iRank][vInd] # get queue size for these indices
    
    dfMES['q_i'] = psSizeQueue # store sizes back into queue's messages df
    
def add_ranking_to_messages(dfMES, dfQPrice):
    """
    purpose: compute the queue ranking for every transaction in order 
    to compute relevant statistics such as AES
    """
    # init emmpty list to store the queue rank for every message
    lQrankings = [0] * len(dfMES)    
    lInd = dfQPrice.columns
    mQPrice = np.array(dfQPrice)
    for i in range(len(dfMES)):
        
        # get price 
        dPrice = dfMES['price'][i]

        # extract LOB state 
        if dfMES['type'][i]==1:
            # if  type is limit order then price may not turn back in pre-order queues state, so then use post-order queues state
            vQPrice = mQPrice[i,:]
        elif dfMES['type'][i]==5: # skip hidden order exec., i.e., iQrank = 0 for hidden order exec.
            continue
        else:            
            vQPrice = mQPrice[i-1,:]
        
        # check which queue corresponds to the current order
        vBool = vQPrice == dPrice
        
        # if queue is outside scope of first five levels, store 99 (must be int)
        if sum(vBool) == 0:
            iQrank = 99
        else:
            k = np.where(vQPrice == dPrice)
        # access price of psQPrice to get corresponding ranking of the queue and store in lQrankings
            iQrank = int(lInd[k][0])
        lQrankings[i] = iQrank
    
    # add ranking to message data frame 
    dfMESExt = pd.concat([dfMES,pd.Series(lQrankings)], axis=1)
    lColnames = list(dfMESExt.columns )
    lColnames[-1] = 'ranking'
    dfMESExt.columns = lColnames
    
    dfMESExt['ranking'].astype(int)
    
    return dfMESExt


def create_queue_prices(dfLOB):
    """
    purpose: compute queue price at every recorded lOB state
    """
    psAsk = dfLOB['ask price 1'] 
    psBid = dfLOB['bid price 1'] 
    psSpread = (psAsk - psBid) / 100
    psSpread = psSpread.astype(int)
    psMid = (psAsk + psBid) / 2
    
    
    # create vector to correct ref prices. if spread is odd we take midprice as ref price.
    # if spread is even we either add 0.5 tick from midprice or subtrack 0.5 from midprice based on previous reference price
    vCorrect =  np.zeros(len(dfLOB))
    for i in range(1,psSpread.index[-1]+1):
        if psSpread[i] % 2 == 0:
            if psMid[i] != psMid[i-1]:
                if psMid[i] > psMid[i-1]: 
                    vCorrect[i] = -0.5 # if last midprice was smaller, tend to smaller side
                else:
                    vCorrect[i] = 0.5 # if last midprice was bigger, tend to larger side
            else:
                vCorrect[i] = vCorrect[i-1]
                
    vCorrect[0:18] = 0.5 # choose randomly for first ref price (as we obviously don't have the midprice before the first recorded ref price)   
            
    
    # create vector with deviations to take for computing queues if ref price == midpric 
    dfQPrice = pd.DataFrame()
    vPriceDelta = np.zeros(10)
    lColnames = ['1', '-1', '2', '-2', '3', '-3', '4', '-4', '5', '-5']

    for j in (0,1):
        if j ==0: 
            f = -1
        else: 
            f=1 
        for i in range(0,5):
            vPriceDelta [i*2 + j] = f* 50 +  f * i* 100

    vPriceDelta = np.reshape(vPriceDelta, (1,-1))    
    
    # repeat into matrix 
    mPriceDelta = np.repeat(vPriceDelta , len(dfLOB), axis = 0)
    
    
    # compute queue price with correcting factor for if ref price != midprice: note columns names are wrong but completely useless for mQPrice anyway
    for i in range(10):
        dfQPrice[lColnames[i]] = mPriceDelta[:,i] + psMid + vCorrect * 100

    dfQPrice = dfQPrice.astype(int)
    
    return dfQPrice

def compute_queue_sizes(dfLOB, dfQPrice):
    """
    purpose: compute the queue sizes of the first five levels for both bid/ask sides. 
    making use of price
    note: Non standardized (in AES) sizes are stored
    """
    
    # extract all LOB prices and sizes separately and convert df's to np.array form matrices for efficiency/time profit
    mQ = np.zeros((dfQPrice.shape[0],dfQPrice.shape[1]))
    mQPrice = np.array(dfQPrice)
    mLOB = np.array(dfLOB)
    mQPrice = mQPrice.astype(int)
    vIndPrices = [i for i in range(0,20) if i %2==0]
    vIndSizes = [i for i in range(0,20) if i %2==1]
    mLOBPrices = mLOB[:,vIndPrices]  
    mLOBSizes = mLOB[:,vIndSizes]  
    
    # 1. check for prices of first five levels (function of pref) to overlap with the prices of a given observation of the queues
    # 2. when there are overlapping prices, to store the corresponding sizes (non AES standardized) in a new matrix Q 
    # 3. time it all while doing so    
    import time
    timea = time.time()
    for i in range(len(mLOBPrices)):
        for j in range((mQPrice.shape[1])):
            price = mQPrice[i,j]            
            psBool = price == mLOBPrices[i,:]
            if sum(psBool) > 0:
                mQ[i][j] = mLOBSizes[i,psBool]
        
    timeb = time.time()
    print(f'time took to compute queue sizes: {round((timeb - timea)/60,2)} minutes')
    
    # set the queue prices of the best five levels, which are stored with dfQPrice
    lColumnnames = dfQPrice.columns
    dfQ = pd.DataFrame(mQ, dtype=int)
    dfQ.columns = lColumnnames
    
    return dfQ




