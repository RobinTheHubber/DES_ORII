# -*- coding: utf-8 -*-
"""
Created on Sat Jun  6 22:03:01 2020

@author: robinDG

module for estimating models 1-3
"""

import numpy as np
import pandas as pd



def estimate_model_1(ldfMES, alpha):
    """
    estimate model 1, independent 1-dim B&D processes making use of maxLik.
    Intensities are functions of the size of the queue only
    """
    iN = len(ldfMES)
    dicModel1 = {} # dic to store dataframe containing all estimated intensities for each queue
    
    for i in range(0,iN):
        dicIntensityInf = estimate_queue_model1(ldfMES[i], alpha)
        iRank = ldfMES[i]['ranking'].iloc[0]
        dicModel1[iRank] = dicIntensityInf
    
    return dicModel1



def init_est_frames(iN, lQsizes):    
    """
    purpose: initialize empty df's for intensities and confidence interval lower -and upperbounds
    """
        
    dfLambda = pd.DataFrame() # df to store intensities
    dfLambda['lambda_cap'] = np.zeros(iN)
    dfLambda['lambda_l'] = np.zeros(iN)
    dfLambda['lambda_c'] = np.zeros(iN)
    dfLambda['lambda_m'] = np.zeros(iN)    
    dfLambda.index = lQsizes
    
    dfCIlo = pd.DataFrame() # df to store intensity lower bounds
    dfCIlo['lambda_cap'] = np.zeros(iN)
    dfCIlo['lambda_l'] = np.zeros(iN)
    dfCIlo['lambda_c'] = np.zeros(iN)
    dfCIlo['lambda_m'] = np.zeros(iN)    
    dfCIlo.index = lQsizes
    
    dfCIup = pd.DataFrame() # df to store intensity upper bounds
    dfCIup['lambda_cap'] = np.zeros(iN)
    dfCIup['lambda_l'] = np.zeros(iN)
    dfCIup['lambda_c'] = np.zeros(iN)
    dfCIup['lambda_m'] = np.zeros(iN)    
    dfCIup.index = lQsizes
    
    return dfLambda, dfCIlo, dfCIup 

def estimate_queue_model1(dfMES, alpha, iN=20):
    """
    purpose: estimate parameters for a single queue 
    the df here is not regular dfMES, i.e. all orders, but the orders pertaining to a particular queue 
    iN: max of queue size which still occurs with significant probability
    """
    def get_hf_Qsizes(alpha):
        """
        purpose: get queue sizes (in AES) that occur most frequent such that the cumsum of frequency is roughly 1-alpha of the total of orders
        """
        psAEScounts = dfMES['q_i'].value_counts()
        percentiles = psAEScounts.cumsum() / len(dfMES) 
        likelivals = percentiles[percentiles < (1-alpha)]
        lQsizes = likelivals.index
        return lQsizes
    
    psDeltaTime = dfMES['time'].diff() # set detla time: time between de current order (event) and last order (event) in the queue
    lQsizes = get_hf_Qsizes(alpha)
    iN = len(lQsizes)

    dfLambda, dfCIlo, dfCIup = init_est_frames(iN, lQsizes)
    
    # fill dataframe with intensities and CIs
    for i in range(0,iN):
        iQsize = lQsizes[i]
        
        # estimate intensities and CIs
        lEst = estimate_queue_at_size_model1(dfMES[dfMES['q_i']==iQsize], psDeltaTime)
        
        # fill df's with estimated intensities and CIs
        dfLambda.iloc[i,:4] = lEst[0]
        dfCIlo.iloc[i,:4] = lEst[1]
        dfCIup.iloc[i,:4] = lEst[2]
    
    compute_loadings(dfLambda, dfCIlo, dfCIup) # compute loadings rho with CIs
    
    dicIntensyInf = {"intensity":dfLambda, "CIlo":dfCIlo, "CIup":dfCIup}
    return dicIntensyInf

    

def estimate_queue_at_size_model1(dfMES, psDeltaTime):
    """
    purpose: estimate parameters for a single queue at a given size
    the input here is not regular dfMES, i.e. all orders, but the orders pertaining to a particular queue of a given size
    """
    
    # estimate intensities
    iN = len(dfMES)
    psDeltaTimeGivenSize = psDeltaTime[dfMES.index]
    dCapLambda = (np.mean(psDeltaTimeGivenSize))**-1 # #events/sec 
    iL = sum(dfMES['type']==1)
    iM = sum(dfMES['type']==4)
    iC =  sum((dfMES['type']>1) & (dfMES['type']<4)) # aggregate partial cancellation orders as comple cancellations ( use iC = iN - iL - iM to speed up)
    dLambda_l = dCapLambda * iL / iN 
    dLambda_m = dCapLambda * iM / iN 
    dLambda_c = dCapLambda * iC / iN 
    
    lLambda = [dCapLambda, dLambda_l, dLambda_c, dLambda_m] # list with estimated intensities for the queue at the given size
    
    
    
    # TODO!!: compute asymptotic (non-valid?) confidence intervals

    dCIloCapLambda = dCapLambda - 1.96 * dCapLambda / np.sqrt(iN)
    dCIloLambda_l = 0
    dCIloLambda_c = 0
    dCIloLambda_m = 0
    
    dCIupCapLambda = dCapLambda + 1.96 * dCapLambda / np.sqrt(iN)
    dCIupLambda_l = 0
    dCIupLambda_c = 0 
    dCIupLambda_m = 0
    
    # lists with estimated CIs for the queue at the given size
    lCIlo = [dCIloCapLambda , dCIloLambda_l, dCIloLambda_c, dCIloLambda_m]
    lCIup = [dCIupCapLambda, dCIupLambda_l, dCIupLambda_c, dCIupLambda_m]
    return (lLambda, lCIlo, lCIup)
    
    
def compute_loadings(dfInt, dfCIlo, dfCIup):
    """
    purpose: computing loadings as faction of incoming flow over outgoing flow 
    TODO: CI computation
    """
    mInt = np.array(dfInt)
    vRho = np.zeros(len(dfInt))
    for i in range(len(dfInt)-1):
        dRho = mInt[i,1] / (mInt[i+1,2]  + mInt[i+1,3])
        vRho[i] = dRho 


    vCIloRho = np.zeros(len(dfInt))
    vCIupRho = np.zeros(len(dfInt))

    psRho = pd.Series(vRho)
    psCIloRho = pd.Series(vCIloRho)
    psCIupRho = pd.Series(vCIupRho) 
    
    psRho.index = dfInt.index    
    psCIloRho.index = dfInt.index    
    psCIupRho.index = dfInt.index    

    dfInt['rho'] = psRho
    dfCIlo['rho'] = psCIloRho
    dfCIup['rho'] = psCIupRho
    
    
def compute_conf_levels(dfMES, dAlph):
    """
    purpose: comopute 1-alpha confidence levels for intensity functions using CLT derived intervals
    """
    # TODO: everything
    s = 1
    
    
    