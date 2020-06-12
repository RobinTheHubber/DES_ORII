# -*- coding: utf-8 -*-
"""
Created on Fri Jun 12 10:02:44 2020

@author: bpvan
"""
import numpy as np
import random
import numpy.random as rnd

NUMBER_OF_QUEUES = 4 #number of total limits Qi

# state is queue length and number of busy servers
class State ( object ):
    def __init__ ( self , _queueLength = 0 , _numQueues = NUMBER_OF_QUEUES, _max = 0,  ):
        self.states = [_queueLength]*_numQueues
        self.maxAllowed = _max
    
    def __getitem__(self,ind):
        return self.states[ind]
    
    def plusState(self,ind):
        self.states[ind] += 1
    
    def minusState(self,ind):
        self.states[ind] -= 1
    
class Queue ( object ):
    def __init__ ( self , _line = []):
        self.line = _line

     # adds at the end
    def addLimitOrder ( self , cust ):
         if len ( self.line )==0:
             self.line = [ cust ]
         else :
             self.line.append( cust )

     # returns and deletes customer with idnr i
    def cancelLimitOrder ( self ,i ):
        cust = next ( cus for cus in self . line if cus . getIdnr ()== i )
        self.line.remove ( cust )
        return cust

     # gets the customer in front and removes from queue
    def getFirstOrder ( self ):
        if self.line:
            cust = self . line . pop (0)
            return cust
    
    def emptyQueue(self):
        self.line = []
    
# limit order has identification number , and
# arrival time , and service time as a 3 - tuple info
class LimitOrder ( object ):
    def __init__ ( self , _idnr , _arrtime = np.inf ,
                       _sertime = np.inf ):
        self.info = ( _idnr , _arrtime , _sertime )

    def getIdnr ( self ):
         return self.info [0]

    def getArrTime( self ):
         return self.info [1]

    def getSerTime ( self ):
         return self.info [2]

# events are arrivals / departures from limit orders and market order arrival
# as 3 - tuple info ( time of event , type of event , and idnr)
# idnr for arrival is 0
# idnr for departures is 1
# idnr for market order arrival is market order idnr 
class Event ( object ):
    def __init__ ( self , _time = np.inf , _type = '', _idnr = 0):
        self . info = ( _time , _type , _idnr )

    def getTime ( self ):
        return self . info [0]

    def getType ( self ):
         return self . info [1]

    def getIdnr ( self ):
        return self . info [2]
    

# events are ordered chronologically
# always an arrival event
class Eventlist ( object ):
    def __init__ ( self , _elist = []):
        self . elist = _elist

 # adds according to event time
    def addEvent ( self , evt ):
        if len ( self . elist )==0:
            self . elist = [ evt ]

        else :
            te = evt . getTime ()
            if te > self . elist [ -1]. getTime ():
                self . elist . append ( evt )
            else :
                evstar = next ( ev for ev in self . elist
                               if ev . getTime () > te )
                evid = self . elist . index ( evstar )
                self . elist . insert ( evid , evt )

 # returns oldest event and removes from list
    def getFirstEvent ( self ):
        evt = self . elist . pop (0)
        return evt

 # deletes event as sociated with customer with idnr i
    def deleteEvent ( self ,i ):
        evt = next ( ev for ev in self . elist if ev . getIdnr ()== i )
        self . elist . remove ( evt )

# counter variables per run
 # queueArea = int Q(t)dt where Q(t)= length of queue at time t
 # waitingTime = sum W_k where W_k= waiting time of k-th customer
 # numArr = number of arrivals
 # numServed = number served
 # numOntime = number of customers startng their service on time
 # numWait = number of arrivals who go into queue upon arrival
class Qobservations ( object ):
    def __init__ ( self , _queueArea = 0 , _waitingTime = 0 ,
                  _numArr = 0 , _numServed = 0 , _numOntime = 0 , _numWait = 0):
        self . queueArea = _queueArea
        self . waitingTime = _waitingTime
        self . numArr = _numArr
        self . numServed = _numServed
        self . numOntime = _numOntime
        self . numWait = _numWait

    def addObs ( self , obs ):
         self . queueArea += obs . queueArea
         self . waitingTime += obs . waitingTime
         self . numArr += obs . numArr
         self . numServed += obs . numServed
         self . numOntime += obs . numOntime
         self . numWait += obs . numWait

# exponential variate
def ranexp ( rate ):
    return - np . log ( rnd . rand ()) / rate

def HandleArrival ( lamda , mu ,c , te , nc ,X ,Q, L , obs, i ):
    nc += 1
    ser = ranexp ( mu ) # required service time

    eva = Event ( te + ranexp ( lamda ) ,'arr' ,0) # next arrival
    L . addEvent ( eva )
    if X . maxAllowed < c : # there is a free agent
        X . maxAllowed += 1
        obs . numServed += 1
        obs . numOntime += 1
        evb = Event ( te + ser , 'dep', nc ) # departure from agent
        L . addEvent ( evb )
    else : # all agents busy , customer joins queue
       cust = LimitOrder ( nc , te , ser )
       Q . addLimitOrder ( cust )
       X.plusState(i)
       obs . numWait += 1

    return nc

def HandleDeparture ( AWT , te ,X ,Q ,L , obs, i ):
    if X[i] != 0: # takes the first in line
        X.maxAllowed -= 1
        first = Q.getFirstOrder() # delete from queue
        X.minusState(i)
        w = te - first.getArrTime() # waiting time
        obs . waitingTime += w
        if w < AWT :
            obs . numOntime += 1
        obs . numServed += 1
    
        j = first . getIdnr ()
        ser = first . getSerTime ()
        evb = Event ( te + ser , 'dep', j ) # departure from agent
        L . addEvent ( evb )
    
def HandleMarketOrder(AWT , te ,X , vLimits , mEvents , obs, i, nc, tp ):
    size = np.random.uniform(low=1,high=nc)
    mid = NUMBER_OF_QUEUES/2 - 1
    
    if tp == 'sell':
        bestbuy = vLimits[mid]    
        bestbuy = SubtractOrder(AWT, te, X, size, bestbuy, mEvents[mid], vLimits, tp)
        return nc
    else:
        bestsell = vLimits[mid+1]
        bestsell = SubtractOrder(AWT, te, X, size, bestsell, mEvents[mid+1], vLimits, mid+1,tp)
        return nc
    
def SubtractOrder(AWT, te, X, size, Q, L, vLimits, mid,tp):
    while Q.line[0] < size:
         size = size - Q.line[0]
         HandleDeparture(AWT, te, X, Q, L)
            
    if size != 0:
        if tp == 'sell':
            H = vLimits[mid-1]
            SubtractOrder(size, H, L, vLimits, mid-1,tp)
        else: 
            H = vLimits[mid+1]
            SubtractOrder(size, H, L, vLimits, mid+1, tp)
            
    
# do n runs , collect statistics and report output
def simulations ( lamda , mu ,N ,T , AWT , n ):
    cumobs = Qobservations ()
    for j in range ( n ):
        obs = simrun ( lamda , mu ,N ,T , AWT )
        cumobs . addObs ( obs )

    L = cumobs . queueArea / n
    W = cumobs . waitingTime / n
    PW = cumobs . numWait / n
    SL = cumobs . numOntime / n

    print ('average queue length L :', L )
    print ('average waiting time W :', W )
    print ('delay probability P_w :', PW )
    print ('service level SL :', SL )


# simulation run until end of day T
 # all random times are exponential
 # AWT = accepted waiting time
def simrun ( lamda , mu ,c ,T , AWT ):
    tc = 0 # current time
    nc = 0 # number of arrivals

    X = State ()
    vLimits = [Queue() for i in range(NUMBER_OF_QUEUES)] #Q
    mEvents = [Eventlist() for i in range(NUMBER_OF_QUEUES)] #L
    obs = Qobservations ()
    
    evt = Event ( ranexp ( lamda ) ,'arr' ,0) # first arrival
    for i in range(NUMBER_OF_QUEUES):
        mEvents[i].addEvent(evt)
        
        
#    mEvents[NUMBER_OF_QUEUES // 2 - 1] . addEvent ( evt )
    
    

    while tc < T :
        i = random.choice([i for i in range(NUMBER_OF_QUEUES)])
#        i = NUMBER_OF_QUEUES // 2 - 1
        evt = mEvents[i].getFirstEvent () # next event
        te = evt.getTime ()
        tp = evt.getType ()
        print(tp)
        ti = te - tc
        obs.queueArea += ti * X[i]

        if tp == 'arr': # arrival event
            nc = HandleArrival ( lamda , mu ,c , te , nc ,X , vLimits[i], mEvents[i] , obs, i )
        else: HandleDeparture ( AWT , te , X , vLimits[i], mEvents[i] , obs, i )
#        elif: tp == 'dep' : # departure event
#            HandleDeparture ( AWT , te , X , vLimits[i], mEvents[i] , obs, i )
#        else: 
#            nc = HandleMarketOrder(AWT , te ,X , vLimits , mEvents, obs, i, nc,tp)
        tc = te

    obs . queueArea /= te # average queue length
    (obs . waitingTime / obs . numServed) if obs.numServed !=0 else obs.waitingTime # average waiting time
    obs . numArr = nc
    (obs . numOntime / obs . numServed) if obs.numServed != 0 else obs.numOntime# fraction served on time
    obs . numWait /= nc # prob of waiting ( delay prob )

    return obs

def main():
    np.random.seed(123)
    
    mu = 0.2 # per minute : 5 minutes average service
    rho = 0.8 # utilization
    c = 5 # number of servers
    lamda = rho * c * mu # arrivals per minute
    AWT = 0.5 # half minute
    T = 360.0 # minutes (5 hrs)
    n = 200 # number of runs

    simulations( lamda , mu ,c ,T , AWT , n )
    
    print('arrival rate lamda =', lamda )




if __name__ == '__main__':
    main()
