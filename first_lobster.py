# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 18:53:38 2020

@author: robinDG
"""
# =============================================================================
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FormatStrFormatter
import shrimpy
plt.style.use('ggplot')
# =============================================================================

# set up shrimpy api and retrieve data
public_key = 'bea8edb348af22613041948908'
secret_key = 'df84c39fb49026dcad9d9912309487104987'
client = shrimpy.ShrimpyApiClient(public_key, secret_key)
ticker = client.get_ticker('bittrex')
supported_exchanges = client.get_supported_exchanges()


def get_live_orderbook(dicShrimpInf):
    orderbookscollection = client.get_orderbooks(
            dicShrimpInf['exchange'],  # exchange
    'XLM',      # base_symbol
        dicShrimpInf['quote'],      # quote_symbol
        dicShrimpInf['depth']       # limit
        )

    orderbookinfo = orderbookscollection[0]
    orderbooks = orderbookinfo['orderBooks']
    orderbooks = orderbooks[0]
    orderbook = orderbooks['orderBook']
    
    dfOrderbook = prep_orderbook(orderbook)
    return dfOrderbook

# define data manipulation and plotting for LOBs
def prep_orderbook(orderbook, show_me_the_money=False):
    sAsks, sBids = 'asks','bids'
    dfOrderbook = pd.DataFrame({})

    for sOrders in [sAsks,sBids]:
        dfOrders = pd.DataFrame(orderbook[sOrders])
        psQ = pd.to_numeric(dfOrders['quantity'])
        psP = pd.to_numeric(dfOrders['price'])
        dfOrderbook[sOrders + '_price'] = psP
        dfOrderbook[sOrders + '_quantity'] = psQ

    if show_me_the_money:
        show_lobster(dfOrderbook)
        
    return dfOrderbook

    
def show_lobster(dfOrderbook):    
    # Create 2x2 sub plots
    gs = gridspec.GridSpec(2, 2)
    plt.figure()
    
    
    ax1 = plt.subplot(gs[0,0])
    ax2 = plt.subplot(gs[0,1])
    ax = plt.subplot(gs[1,:])
    
    dfOrderbook.plot.barh(x='asks_price', y='asks_quantity', ax=ax1, color='red')
    dfOrderbook.plot.barh(x='bids_price', y='bids_quantity', ax=ax2, color='blue')
    
    ax.plot(dfOrderbook.iloc[:,0], dfOrderbook.iloc[:,1] , label='ask')
    ax.plot(dfOrderbook.iloc[:,2], dfOrderbook.iloc[:,3], label='bid')
    ax.plot((min(dfOrderbook.iloc[:,0]), max(dfOrderbook.iloc[:,2])), (0,0), label='spread')                
    ax.set(xlabel='price', ylabel= 'quantity')
    ax.legend()        
    plt.show()


def extract_lobsterdata(dfOrderbook):
    alldata = (dfOrderbook.iloc[:,0], dfOrderbook.iloc[:,2], dfOrderbook.iloc[:,1], dfOrderbook.iloc[:,3]) 
    return alldata

def update_liveplot(dfOrderbook, lines, pause_time = 1.0):
    plt.pause(pause_time)    
    
    data = extract_lobsterdata(dfOrderbook)
    (x1_data, x2_data, y1_data, y2_data) = data
    (line1, line2, line3) = lines
    line1.set_xdata(x1_data)
    line2.set_xdata(x2_data)
    line1.set_ydata(y1_data)
    line2.set_ydata(y2_data)   
    line3.set_xdata((max(x2_data),min(x1_data)))
    
    y_max = max(max(y1_data),max(y2_data))  
    x1_min, x2_max = min(x1_data), min(x2_data)
    
    if y_max >=line1.axes.get_ylim()[1] :
        plt.ylim(0, y_max  +np.std(y1_data))
    
    if x1_min <= line2.axes.get_xlim()[0] or x2_max >= line2.axes.get_xlim()[1] :
        plt.xlim(np.std(x1_data) + x1_min, x2_max + np.std(x1_data))

    
    return (line1, line2, line3) 

    
def set_liveplot(dfOrderbook,lines):
    if lines==():
        # this is the call to matplotlib that allows dynamic plotting
        plt.ion()
        plt.figure(figsize=(13,6))
        
        # get data from current order book 
        (x1_data, x2_data, y1_data, y2_data) = extract_lobsterdata(dfOrderbook)
        
        # create a variable for the line so we can later update it
        line1, = plt.plot(x1_data, y1_data , label='ask')
        line2, = plt.plot(x2_data, y2_data, label='bid')
        line3, = plt.plot((min(x1_data), max(x2_data)), (0,0), label='spread')                
        lines = (line1, line2, line3)
        plt.xlabel('price')
        plt.ylabel('quantity')
        plt.legend()        
        plt.show()  
    
    return lines


def showing_live_shrimps(dicShrimpInf):
    dfFirstShrimp = get_live_orderbook(dicShrimpInf)
    lines = set_liveplot(dfFirstShrimp, ())
    
    while True:
        dfLiveShrimp = get_live_orderbook(dicShrimpInf)
        lines = update_liveplot(dfLiveShrimp, lines, pause_time=5)

    
def main():
    dicShrimpInf = {'quote':'BTC','exchange':'bittrex','depth':20}
    showing_live_shrimps(dicShrimpInf)

    
if __name__ == "__main__":
    main()    
    
    
def basic_test():
    orderbookEarly, orderbookLater = get_orderbooks()
    dfShrimpEarly = conv_orderbook(orderbookEarly, show_me_the_money=True)
    dfShrimpLater = conv_orderbook(orderbookLater, show_me_the_money=True)
    return(dfShrimpEarly, dfShrimpLater)
    
    

def get_orderbooks():
    orderbookEarly = {'asks': [{'price': '0.00000760',
      'quantity': '133482.97424639'},
     {'price': '0.00000761', 'quantity': '217560.47731166'},
     {'price': '0.00000762', 'quantity': '41999.99999998'},
     {'price': '0.00000763', 'quantity': '152706.00000000'},
     {'price': '0.00000765', 'quantity': '2638.52242744'},
     {'price': '0.00000767', 'quantity': '33152.99799119'},
     {'price': '0.00000768', 'quantity': '88080.00000000'},
     {'price': '0.00000773', 'quantity': '298.82076219'},
     {'price': '0.00000774', 'quantity': '7291.97809489'},
     {'price': '0.00000775', 'quantity': '1603.92933498'}],
    'bids': [{'price': '0.00000757', 'quantity': '52192.75840361'},
     {'price': '0.00000756', 'quantity': '268522.87078305'},
     {'price': '0.00000755', 'quantity': '41999.99999999'},
     {'price': '0.00000753', 'quantity': '152706.00000000'},
     {'price': '0.00000752', 'quantity': '26367.83124588'},
     {'price': '0.00000751', 'quantity': '178928.27721897'},
     {'price': '0.00000750', 'quantity': '583.19083000'},
     {'price': '0.00000749', 'quantity': '88080.00000000'},
     {'price': '0.00000747', 'quantity': '31160.22356091'},
     {'price': '0.00000745', 'quantity': '75.19865771'}]}
    
    orderbookLater = {'asks': [{'price': '0.00000763', 'quantity': '103684.42001049'},
  {'price': '0.00000764', 'quantity': '122209.99999990'},
  {'price': '0.00000765', 'quantity': '185230.54381038'},
  {'price': '0.00000766', 'quantity': '152706.00000000'},
  {'price': '0.00000767', 'quantity': '1609.99055631'},
  {'price': '0.00000769', 'quantity': '2624.67191601'},
  {'price': '0.00000770', 'quantity': '93080.00000000'},
  {'price': '0.00000772', 'quantity': '19184.24938272'},
  {'price': '0.00000773', 'quantity': '298.82076219'},
  {'price': '0.00000775', 'quantity': '6603.92933498'}],
 'bids': [{'price': '0.00000761', 'quantity': '10566.28300000'},
  {'price': '0.00000760', 'quantity': '90360.27422491'},
  {'price': '0.00000759', 'quantity': '175404.99999960'},
  {'price': '0.00000758', 'quantity': '46808.15277412'},
  {'price': '0.00000757', 'quantity': '180979.59498632'},
  {'price': '0.00000756', 'quantity': '250.00000000'},
  {'price': '0.00000755', 'quantity': '2624.67191601'},
  {'price': '0.00000754', 'quantity': '171290.27120174'},
  {'price': '0.00000753', 'quantity': '75.22576361'},
  {'price': '0.00000752', 'quantity': '31291.98936170'}]}
    return orderbookEarly, orderbookLater

import time

# get data
sFilename = 'deribit_incremental_book_L2_2020-04-01_BTC-PERPETUAL.csv'
time_bef = time.time()
df = pd.read_csv(sFilename, header=0)
time_af = time.time()
print(time_af - time_bef)


dfAsk = df[df['side']=='ask']
dfBid = df[df['side']=='bid']


# obtain prices, counts of prices and quantitie
iNqueues = df.groupby('side')['price'].nunique()

"""
which queues do we use?
side 
ask    3949 different prices
bid    4181 different prices

side max count prices
ask    p=6304.5, c=45177 -> roughly 0.2% of all the data
bid    p=6226.0, c=42434 -> roughly 0.2% of all the data
"""

psCounts = df.groupby('side')['price'].value_counts()
psAskCounts = psCounts['ask']
psBidCounts = psCounts['bid']

psQuants = df.groupby('side')['amount'].value_counts()
psQuantsAsk = psCounts['ask']
psQuantsBid = psCounts['bid']

dfAsk['amount'].value_counts() # 1% of all data has q=0 (fortunately)

def plot_price_freq(dfAsk, dfBid):
    fig, ((ax1, ax2),(ax3,ax4)) = plt.subplots(2,2)
    fig.suptitle('Queue exploration - Frequency of prices')
    ax1.set_title('Frequency of ask prices: clipped < 7000')
    ax2.set_title('Frequency of bid prices: clipped > 6000')
    ax3.set_title('Frequency of ask prices')
    ax4.set_title('Frequency of bid prices')
    dfAsk[dfAsk['price']<7000]['price'].hist(ax=ax1, bins=30, color='red')
    dfBid[dfBid['price']>6000]['price'].hist(ax=ax2, bins = 30, color='blue')
    dfAsk['price'].hist(ax=ax3, bins=30, color='red')
    dfBid['price'].hist(ax=ax4, bins = 30,color='blue')
    plt.show()

def plot_price_sum_of_quants(psAskSumQ, psBidSumQ):
    fig, (ax1, ax2) = plt.subplots(1,2)
#    fig.suptitle('Queue exploration - Frequency of prices')
#    ax1.set_title('Frequency of ask prices')
#    ax2.set_title('Frequency of bid prices')
#    psAskSumQ.hist(ax=ax1, bins=30)
#    psBidSumQ.hist(ax=ax2, bins = 30)
    plt.show()




def plot_evolution_HFqueues(psAskCounts,psBidCounts,dfAsk,dfBid):
    top3Asks = psAskCounts.iloc[0:3]
    top3Bids = psBidCounts.iloc[0:3]
    
    fig, axs = plt.subplots(2,3)
    
    fig.suptitle('highest frequency queues - ask above vs bid below')
    axs[0][0].set_ylabel('quantity')
    axs[1][1].set_xlabel('passed time in hours')
    
    dfs = (dfAsk, dfBid)
    top3 = (top3Asks,top3Bids)
    for i in range(0,2):
        top3side = top3[i]
        dfSide = dfs[i]
        for j in range(0,3):    
            # select and prep df for given price in top 3 of bid/ask 
            price = top3side.index[j]
            count = top3side.iloc[j]
            dfSel = dfSide[df['price']==price]
            dfSel.index = (dfSel['timestamp'] - min(dfSel['timestamp']))/3600000000 # convert index into hours passed 
        
            ax = axs[i][j]
            ax.plot(dfSel.index , dfSel['amount'])
            ax.set_title(f'price={price},count={count}')
        
    
    plt.show()l
    
    
    #### PROBLEM: MULTIPLE TIMESTAMPS FOR SAME PRICE??