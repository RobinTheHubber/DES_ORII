# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 15:48:50 2020

@author: robinDG
"""
# =============================================================================
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FormatStrFormatter
import matplotlib.animation as animation 
plt.style.use('ggplot')
# =============================================================================
  

def extract_LOB(psLOB, iLevel=5):
    """
    purpose: extract prices and quantities from a single LOB state using indices 
    """
    pricesInd = [i%2==0 for i in range(0,iLevel*4)]
    sizeInd = [i%2==1 for i in range(0,iLevel*4)]
    prices = psLOB[pricesInd] /10000
    sizes = psLOB[sizeInd]
    
    vInd = np.argsort(prices)
    prices = prices[vInd]
    sizes = sizes[vInd]
    
  
    return (prices, sizes)

def LOB_histogram(psLOB, time, iLevel=5):
    """
    purpose: make histogram of single LOB state at time "time"
    """
    (prices, sizes) = extract_LOB(psLOB)
    plt.title(f'level-{iLevel} limits at time:{round(time,2)}')    
    pricelabels = ['$' + str(price) for price in prices]
    plt.barh(np.arange(0,10),sizes, color=['red']*iLevel + ['blue']*iLevel, tick_label = pricelabels)


def plot_intensities(dicModel1Qinf):
    """
    purpose: plotting intensity functions, either for model 1, 2 or 3
    """
    # extract/prepare data
    dfInt = dicModel1Qinf['intensity']
    dfCIlo = dicModel1Qinf['CIlo']
    dfCIup = dicModel1Qinf['CIup']
    
    dfInt = dfInt.sort_index().iloc[1:,:]
    dfCIlo = dfCIlo.sort_index().iloc[1:,:]
    dfCIup = dfCIup.sort_index().iloc[1:,:]

    iN = len(dfInt.index)
    
    
    # plot data: intensities and its CFs in same axis obviously
    color = 'red'
    colorCIlo = 'blue'
    colorCIup = 'green'

    fig, ax = plt.subplots(nrows=2,ncols=3)
    ax[0][0].plot(dfInt.index, dfInt['lambda_cap'], color=color, label='lambda_cap')
    ax[0][0].plot(dfInt.index, dfCIlo['lambda_cap'], color=colorCIlo, label='lambda_cap_CIlo', linewidth=0.4)
    ax[0][0].plot(dfInt.index, dfCIup['lambda_cap'], color=colorCIup, label='lambda_cap_CIup', linewidth=0.4)
    ax[0][1].plot(dfInt.index[:iN-1],dfInt['rho'].iloc[:iN-1], color=color, label='rho')
    ax[1][0].plot(dfInt.index,dfInt['lambda_l'], color=color, label='lambda_l')
    ax[1][1].plot(dfInt.index,dfInt['lambda_c'], color=color, label='lambda_c')
    ax[1][2].plot(dfInt.index,dfInt['lambda_m'], color=color, label='lambda_m')
    
        
    for axs in ax:
        for axss in axs:
            axss.legend()

    plt.show()
    

def midprice(dfLOB, psTime):
    """
    purpose: show midprice over time
    """
    psTime = (psTime - psTime[0])/3600
    fig, ax = plt.subplots()
    
    xticks = [i/2 for i in range(0,14)]
    ax.set_xticks(xticks)
    ax.set_xticklabels([str(tick) for tick in xticks])
    psAsk = dfLOB['ask price 1'] / 10000
    psBid = dfLOB['bid price 1'] / 10000
    psMid = (psAsk + psBid) / 2
    
    

    ax.plot(psTime, psMid, color='black')
    
    ax.set_xlabel('time in hours passed')
    ax.set_ylabel('midprice in $')
    plt.show()
    

def mid_price_zoom_in(dfLOB, psTime, lInt):
    """
    purpose: show midprice over time within a specific interval lInt = (a,b) measured in minutes
    """
    
    (a,b) = lInt
    psAsk = dfLOB['ask price 1'] / 10000
    psBid = dfLOB['bid price 1'] / 10000
    psMid = (psAsk + psBid) / 2
    psTime = (psTime - psTime[0])/60
    psMin = psTime[(psTime < b) & (psTime > a)]    
    plt.plot(psMin, psMid[psMin.index[0]:psMin.index[-1]+1])    
    plt.set_xlabel('time in minutes passed')
    plt.set_ylabel('midprice in $')
    plt.show()
    
def show_AES_sparsity(dfQst):
    """
    purpose: illustrate sparsity in AES for queue's 3,4 and -4
    note: only for non-aggregated queues
    """
    fig, (ax1,ax2,ax3) = plt.subplots(nrows=1, ncols=3)
    dfQst['3'].hist(bins=len(dfQst['2'].value_counts()), ax = ax1)
    dfQst['4'].hist(bins=len(dfQst['2'].value_counts()), ax = ax2)
    dfQst['-4'].hist(bins=len(dfQst['2'].value_counts()), ax = ax3, color='blue')
    plt.show()
            
    
def plot_queue_sizes(dfMES, dfQ, bAgg=False):
    """
    purpose: show queue sizes over time for first two queues over time
    """    
    psTime = dfMES['time']
    psTime = (psTime - psTime[0])/3600
    fig, ax = plt.subplots(nrows=2,ncols=2)
    xticks = [i/2 for i in range(0,14)]
    for axs in ax:
        for axss in axs:           
            axss.set_xticks(xticks)
            axss.set_xticklabels([str(tick) for tick in xticks])
        
    color = 'red'     
    if not bAgg:
        color = 'blue'
    
    psB1 = dfQ.iloc[:,0]
    psA1 = dfQ.iloc[:,1]
    psB2 = dfQ.iloc[:,2]
    psA2 = dfQ.iloc[:,3]

    ax[0][0].plot(psTime, psB1, color='red')
    ax[0][1].plot(psTime, psA1, color=color)
    ax[1][0].plot(psTime, psB2, color='red')
    ax[1][1].plot(psTime, psA2, color=color)
    plt.show()

"""
purpose: show fun dynamic plot of queue's over time
uncomment below when using!
weird issue: cannot nest animation into function, this is a well known problem online still to be fixed 
"""   
def animate(i):
   # Example data
    while i<100000:
        psLOB = dfLOB.iloc[i*6000,:]
        (prices, sizes) = extract_LOB(psLOB)
        pricelabels = ['$' + str(price) for price in prices]
        ax.set_yticklabels(pricelabels)
        sTitle =  "Dynamic LOB: " + str(round((dfMES['time'][6000*i]- dfMES['time'][0])/60,0)) + ' mins elapsed'
        title = ax.text(0.5,0.95,str(sTitle), bbox={'facecolor':'w', 'alpha':0.5, 'pad':5},transform=ax.transAxes, ha="center")        
        rects = ax.barh(np.arange(0,10), sizes, align='center',
                color=['red']*5 + ['blue']*5, ecolor='None')
        return [rect for rect in rects] + [title]
#
#psLOB = dfLOB.iloc[0,:]
#(prices, sizes) = extract_LOB(psLOB)
#pricelabels = ['$' + str(price) for price in prices]
#plt.rcdefaults()
#fig, ax = plt.subplots()
#ax.set_yticks(range(0,10))
#ax.set_yticklabels(pricelabels)
##ax.set_xlim((0,50000))
#ax.invert_yaxis() 
#ax.set_xlabel('queue size')    
#
#
#ani = animation.FuncAnimation(fig,animate, frames=100000, blit=False
#                            ,interval=400,repeat=False)
#
#plt.show() 


