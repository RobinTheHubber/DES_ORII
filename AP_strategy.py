# -*- coding: utf-8 -*-
"""
Created on Tue Jun 30 16:12:51 2020

@author: bpvan
"""

# =============================================================================
import numpy as np
import AP_first_lobster as estimates 
from AP_SIM_classes import Eventlist, LOBState, Qobservations
from AP_SIM_orderhandling import handle_limit_order, handle_market_order, handle_cancellation_order, schedule_unplanned
import AP_SIM_utilities as util 
from AP_SIM_classes import Order

# =============================================================================
# =============================================================================
TOTAL_CAPITAL = 60 #in AES
PERIODS = 10 #number of sub periods
TIME = 10 #seconds
SCHEDULE = 'linear'
TACTIC = 'faf'
sID = 't'

NUMBER_OF_QUEUES = estimates.get_NUMBER_OF_QUEUES() #number of total limits Qi
# takes like 10 sec to run. Gives complete intensity estimates of model 1 
# and the bounds corresponding to the queue size categoreis per queue
dicBounds, dicModel = estimates.get_bounds_and_model1_est() 

# TODO make AES ordertype and queue dependent!
dicAES = {}
for ind in dicBounds.keys():
    dicAES[ind] = {'l':80,'m':80,'c':80}
# =============================================================================
    
def scheduling():
    lInvestments = [0]*PERIODS
    for i in range(PERIODS):
        if SCHEDULE == 'linear':
            lInvestments[i] = TOTAL_CAPITAL/PERIODS
        else: 
            if i == 0:
                lInvestments[i] = TOTAL_CAPITAL*(np.exp(-i/4)-np.exp(-(i-1)/20))
            else: lInvestments[i] = TOTAL_CAPITAL*(np.exp(-i/4)-np.exp(-(i-1)/20)) + TOTAL_CAPITAL*(np.exp(-(i-1)/4)-np.exp(-(i-2)/20))
                
    return lInvestments

def placeFirstOrder(lOrders,iN,Events,dCurrentInv,X,tc):
    iQ = util.get_best_limit(X,'bid')
    dPrice = X.dicQprices[iQ]
    
    iN = int(dCurrentInv//dicAES[iQ]['l']) #both in line 52 and 53, I take the AES of limit orders
    iRest = dCurrentInv - iN * dicAES[iQ]['l']
    
    placeOrder(Events,lOrders,iN,tc,dPrice)
        
    return dPrice,iN,iRest
    
def placeOrder(Events,lOrders,iN,tc,dPrice):
    for i in range(iN):
        order = Order(_type='l', _idnr = sID + str(i) , _size = 1, _price = dPrice, _arrtime = tc+i*10^(-3))
        Events.Order (order)
        lOrders.append(Order)
        
        
def priceCheck(iN, X,dOld_refprice, dPrice,Events,lOrders,dCurrentInv): 
    dAmountCancelled = 0
    iRest = 0
    if TACTIC == 'faf':
        if X.pref != dOld_refprice: #reference price has changed
            dAmountCancelled = removeOrders(Events,dPrice,lOrders,X)                    
    else:
        for ind, price in X.dicQprices.items():  
            if price == dPrice:
                iQ = ind
        if iQ != util.get_best_limit(X,'bid') or len(X.dicLimorders[iQ] == len(lOrders)): #either best price has changed or the only oreder left in best queue 
            dAmountCancelled = removeOrders(Events,dPrice,lOrders,X)
            iN = int(dCurrentInv//dicAES[iQ+1])
            iRest = dCurrentInv - iN * dicAES[iQ+1]['m']
            placeOrder(Events,lOrders,iN)
            
    return dAmountCancelled , iRest

def removeOrders(Events,dPrice,lOrders,X,lInds):
    removelist = []
    for ev in lOrders:            
        if ev.getPrice() == dPrice:
            removelist.append(ev)
    for ev in removelist:    
        lOrders.remove(ev)
        Events.elist.remove(ev)
    
    for index in lInds:
        if X.dicQprices[index] == dPrice:
            ind = index

    dAES = dicAES[ind]
    iR = len(removelist)
    dAmountCancelled = iR * dAES
    return dAmountCancelled

def endPeriod(dTotalRest,Events,dPrice,lOrders,X,lExecutedinPeriod,iPeriod,lNumberofExecuted,tc):
    dAmountCancelled = removeOrders(Events,dPrice,lOrders,X)
    dTotalRest +=dAmountCancelled
    

    iIndexBestAsk = util.get_best_limit(X,'ask')
    dPriceBestAsk = X.dicQprices[iIndexBestAsk]
    dAES = dicAES[iIndexBestAsk]                        
    lExecutedinPeriod[iPeriod] += dAES
    iN = dTotalRest//dAES
    if iN > len(X.dicLimorders[iIndexBestAsk]):
        iN = len(X.dicLimorders[iIndexBestAsk])
    dRest = dTotalRest - iN * dAES  # we hadden hier als index dicAES[iQ+1]
    for i in range(iN):
        order = Order(_type='ma', _idnr = np.nan , _size = 1, _price = dPriceBestAsk, _arrtime = tc+i*10^(-3))
        Events.Order (order)
    lNumberofExecuted[iPeriod] += iN   
    return dRest

def execution(Events,lID,lOrders,lInds,X,lExecutedinPeriod,lNumberOfExecuted,iPeriod):
    lAllids = [ev.getIdnr() for ev in Events.elist] 
    idExecuted =  next(Id for Id in lID if Id not in lAllids)
    evExecuted = next ( ev for ev in lOrders if ev . getIdnr ()== idExecuted)
    lOrders.remove(evExecuted)
    orderprice = evExecuted.getPrice()
    for index in lInds:
        if X.dicQprices[index] == orderprice:
            ind = index
    dAES = dicAES[ind]                        
    lExecutedinPeriod[iPeriod] += dAES
    lNumberOfExecuted[iPeriod] += 1

#def performance():
    
            

def simrun (T, bCollect=False):
    """
    purpose: # simulation run until end of day T
    # all random times are exponential
    """
    
    lInvestments = scheduling()
    lOrders = []
    lCancelledinPeriod = [0] * PERIODS
    lExecutedinPeriod = [0] * PERIODS
    lNumberOfExecuted = [0] * PERIODS
    
    tc = 0 # current time
    dicA = util.initFlowDic() # number of arrivals for every queue
    dicD = util.initFlowDic() # number of departures for every queue
    X = LOBState () # initialize lobstate
    
    # init plotinfo for dynamic plotting
    dicPlotInf = {'prices':[],'sizes':[], 'time':[], 'deps':[], 'arrs': []}
    if bCollect:
        dicPlotInf['time'].append(tc)
        dicPlotInf['sizes'].append(list(X.dicSizes.values()))
        dicPlotInf['prices'].append(list(X.dicQprices.values()))

    
    lInds = list(X.dicSizes.keys()) # queue indices
    Events = Eventlist() 
    obs = Qobservations ()        
    util.init_Orders(Events, X, lInds)    

    queueBegin = util.initFlowDic()
    queueArea = util.initFlowDic()
    util.addQueueArea(queueBegin, X.dicLimorders, ti=1)  # store initial queue lengths 
    
    iPeriod = 0
    iN = 0
    dRestofPeriod = 0
    bSubBegin = True
    bFinish = False
    while not bFinish:
        if bSubBegin:
           dCurrentInv = lInvestments[iPeriod] + dRestofPeriod
           dPrice,iN,iRestinPeriod = placeFirstOrder(lOrders,iN,Events,dCurrentInv,X,tc)
           lID = [ev.getIdnr() for ev in lOrders]
           iPeriod += 1
           bSubBegin = False
           dLower = TIME*iPeriod - 10^(-4)
           dUpper = TIME*iPeriod + 10^(-4)
           
        dOldRef = X.pref
        
        order = Events.getFirstorder () # next order
        te = order.getTime ()
        tp = order.getType ()        
        ti = te - tc        
        util.addQueueArea(queueArea, X.dicLimorders, ti) # keep track of #orders waiting at every queue

        if tp == 'l': # limit order
            handle_limit_order(dicA, te, order, X, Events)
            schedule_unplanned(order, X, Events, te) # schedule events that were not able to be re-planned due to limit shortage
        
        elif tp == 'ma':  # market order on ask side
            iNrids = len(lID)
            handle_market_order(te, order, X, Events, dicD, sSide='ask')
            if len(lOrders) != iNrids:
                execution(Events,lID,lOrders,lInds,X,lExecutedinPeriod,lNumberOfExecuted,iPeriod)
                
        elif tp == 'mb': # market order on bid size 
            handle_market_order(te, order, X, Events, dicD, sSide='bid')
        else: # cancellation order 
            handle_cancellation_order(te, order, X, Events, dicD)
        
        dAmountCancelled, iRest = priceCheck(iN,X,dOldRef,dPrice,Events,lOrders,dCurrentInv)
        lCancelledinPeriod[iPeriod] += dAmountCancelled
        iRestinPeriod += iRest
        
        
        tc = te
        if tc < dUpper and tc > dLower:
            iPeriod += 1
            if iPeriod > PERIODS:
                bFinish = True
            dTotalRest = iRestinPeriod + lCancelledinPeriod[iPeriod]
            dRestofPeriod = endPeriod(dTotalRest,Events,dPrice,lOrders,X,lExecutedinPeriod,iPeriod,lNumberOfExecuted,tc)
            
            bSubBegin = True
#            performance()
            
            
        if bCollect:    
            dicPlotInf['time'].append(te)
            dicPlotInf['prices'].append(list(X.dicQprices.values()))
            dicPlotInf['sizes'].append(list(X.dicSizes.values()))
            dicPlotInf['deps'].append(dicD.copy())
            dicPlotInf['arrs'].append(dicA.copy())       


    util.averageFlow(queueArea, te) # average queue length for every queue
    obs . numArr = dicA
    obs . numDep = dicD
    obs . queueArea = queueArea
    obs . queueBegin =  queueBegin
    return obs, dicPlotInf


def simulations (T, n):
    """
    purpose: # do n runs , collect statistics and report output
    """            
    cumobs = Qobservations()
    for j in range ( n ):
        obs, dicPlotInf = simrun (T)
        cumobs.addObs ( obs )
        print('\n'*2)
        
    # take average of all observation measures among sims. every observation is a dictionary with info for every queue
    util.averageFlow(cumobs.queueArea , n)
    util.averageFlow(cumobs.queueBegin, n)
    util.averageFlow(cumobs.numArr, n)
    util.averageFlow(cumobs.numDep, n)

    L, B, A, D = cumobs.queueArea, cumobs.queueBegin, cumobs.numArr, cumobs.numDep
    
    print(f"duration per sim: {T} second")
    print (f'average queue begin length L in queue 1: {B}')
    print(f'average queue length L in queue 1: {L}')
    print(f'average number of arrivals A: {A}')
    print(f'average number of departures D: {D}')
    [a - d for a,d in zip(A.keys(),D.keys())]
    print(f'')

def main():
    np.random.seed(1998)

    T = 600.0 # seconds
    n = 2 # number of runs
    simulations(T, n)


if __name__ == '__main__':
    main()
    

