##############################################
##  Object and Functions to use in Processes to be spun out and monitored with queue
##  Functions called with this 'wrapper' should end with an optional multiprocessing queue object
##  Functions should use "Puts" to write to logging INFO and msg queue
##  Use NewList and NewDict to pass data to be altered in process
##  Use GetArray and GetDict to retreive data from process
##  See example __main__ for additional usage example
##############################################

import configparser
import time
import multiprocessing
import logging
import os

###---Start up Tasks---
logging.basicConfig(level=logging.INFO,format='%(levelname)s:%(funcName)s[%(lineno)d]:%(message)s')
cfg = configparser.ConfigParser()
g_szIniPath = os.getenv('MIFRAME_INI', '/home/admin/projects/miframe/fwww/miframe.ini')
if not os.path.exists(g_szIniPath):
    logging.critical(f"Can't find config file {g_szIniPath}")
    exit()
cfg.read(g_szIniPath)

class MifProcess():
    def __init__(self, hFunction = None):
        self.process = None
        self.queue = multiprocessing.Queue()
        self.manager = multiprocessing.Manager()
        self.lock = self.manager.Lock()
        self.function = hFunction
        self.data = {}
        self.description = ""
        return

    def SetFunction(self, hFunction, description = ""):
        if not hFunction:
            logging.warning(f"Function is None")
            return(False)
        if self.process:
            logging.warning(f"process exists")
            return(False)
        self.function = hFunction
        self.description = description
        return
        
    def SetArgs(self,tArgs = None):
        if self.process is not None:
            logging.debug(f"process not None")
            return(False)
        #unpack * tuple to make new tuple
        tArgsQueue = (*tArgs,self.queue)
        self.process = multiprocessing.Process(target=self.function,args=tArgsQueue)
        return(True)
    
    def Start(self):
        if self.process is None:
            logging.debug(f"process is None")
            return(False)
        if self.process.is_alive():
            logging.debug(f"process is alive")
            return(False)
        try:
            self.process.start()
        except AssertionError:
            logging.error(f"cannot start process twice")
            return(False)
        return(True)
        
    def IsAlive(self):
        if self.process is None:
            logging.debug(f"process is None")
            return(False)
        if self.process.is_alive():
            # ~ logging.debug(f"process is alive")
            return(True)
        logging.debug(f"process not alive")
        return(False)       

    def Join(self, nTime = None):
        if self.process is None:
            logging.debug(f"process is None")
            return(False)
        self.process.join(nTime)
        return(False)       

    def Get(self):
        if self.queue.empty():
            return(None)
        return(self.queue.get(False))

    def Close(self):
        if self.process is None:
            logging.debug(f"process is None")
            return(False)
        if self.process.is_alive():
            logging.warning(f"close requested on running process. blocking until done")
            self.process.join()
        self.process.close()
        self.process = None
        return(True)
        
    def NewList(self, key, a = None):
        self.data[key] = self.manager.list()
        if a:
            for i in a:
                self.data[key].append(i)
        return(self.data[key])
        
    def NewDict(self, key, d = None):
        self.data[key] = self.manager.dict()
        if d:
            for k in d.keys():
                self.data[key][k] = d[k]
        return(self.data[key])
        
    def DataExists(self, key):
        return(key in self.data.keys())
        
    def GetDataRaw(self, key):
        if key not in self.data:
            return(None)
        return(self.data[key])
        
    def GetArray(self, key):
        if key not in self.data:
            return(None)
        a = []
        for i in range(0,len(self.data[key])):
            a.append(self.data[key][i])
        return(a)

    def GetDict(self, key):
        if key not in self.data:
            return(None)
        d = {}
        for k in data[key].keys():
            d[k] = self.data[key][k]
        return(d)
        
def Puts(s, mpQueue = None):
#put string s into multiprocessing queue q and logging.debug
    if mpQueue:
        mpQueue.put(s)
    logging.info(f"{s}")
    return()

#######----------Testing Functions
# from mpwrapper import TBuildList, TAddList, TUpdateList
def TNew(nWait = 0):
    r = {}
    r['i'] = 0
    r['t'] = time.process_time_ns()
    time.sleep(nWait)
    return(r)
    
def TUpdateRec(mp, r, nWait):
    time.sleep(nWait)
    if r:
        r['i'] += 1
        r['u'] = time.process_time_ns()

def TBuildList(a = None, mpQ = None):
    if a is None:
        a = []
    for i in range(0,5):
        a.append(TNew())
    Puts(f"List Built", mpQ)
    return(a)
        
def TAddList(a, nWait, mpQ = None):
    Puts("Adding",mpQ)
    for i in range(0,5):
        a.append(TNew())
        Puts(f"Adding {a[-1]}", mpQ)
        time.sleep(nWait)
    Puts("Done",mpQ)
    return(a)
    
def TUpdateList(a, i, nWait, mpQ = None):
    if i in range(0,len(a)):
        TUpdateRec(a[i])
        Puts(f"update {a[i]}",mpQ)
    return()
    
def T2xAddList(a, nWait, mpQ = None):
    Puts(f"[H]Add List (1)", mpQ)
    Puts(f"Starting First Add List", mpQ)
    TAddList(a, nWait, mpQ)
    Puts(f"[H]Add List (2)", mpQ)
    Puts(f"Starting Second Add List", mpQ)
    TAddList(a, nWait, mpQ)
    Puts(f"Complete 2x Add List", mpQ)
    return

#----------MAIN------------    
if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    
    tStart = time.process_time()
    multiprocessing.set_start_method('spawn')
    mp = MifProcess(TAddList)
    tWait = .1
    
    a = TBuildList()
    
    pa = mp.NewList('a',a)

    mp.SetArgs((pa,tWait))
    mp.Start()
    
    if not mp.Start():
        logging.debug(f"No Start")

    while mp.IsAlive():
        msg = mp.Get()
        if msg:
            logging.debug(f"alive loop [{msg}]")
                
    mp.Close()

    if not mp.Start():
        logging.debug(f"No Start")
        mp.SetArgs((pa,tWait))
        mp.Start()
    else:
        logging.debug(f"Start")

    mp.Close()
    
    mp.SetFunction(TUpdateList)
    mp.SetArgs((pa,tWait,mp.queue))
    mp.Start()
    mp.Join()

    a = mp.GetArray('a')
    logging.debug(f"N:{len(a)} {a}")

    tEnd = time.process_time()
    logging.debug(f"Run time: {tEnd-tStart}")
