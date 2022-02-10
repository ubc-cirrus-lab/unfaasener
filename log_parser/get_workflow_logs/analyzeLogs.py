import subprocess
import json
import shlex
import datetime
from sys import getsizeof
import time
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import math
import pandas as pd

class AnalyzeLogs:
    def __init__(self, logsFile, publisherExeFile, msgExeFile, function, initFunc, workflow):
            print(function)
            self.workflow = workflow
            self.initFunction = initFunc
            self.function = function
            self.timeDiff = []
            self.messageSizeArray = []
            self.execodes = []
            self.reqIDs = []
            self.reqMsgDic = {}
            self.funcExecodes = []
            self.latencyPerExeCode = {}
            with open(logsFile) as json_file:
                writeLogs = json.load(json_file)
                self.logs = writeLogs[self.function]
                self.initLogs = writeLogs[self.initFunction]
            with open(publisherExeFile) as json_file:
                self.execodes = json.load(json_file)
            with open(msgExeFile) as json_file:
                self.msgExe = json.load(json_file)
            self.fetchReqIDs()
#             self.getData()
#             print(self.function + " DONE")
        
    

    def fetchReqIDs(self):
        for id in self.execodes:
            for entry in self.initLogs:
                    if(entry['execution_id'] == id and ("WARNING:root:" in entry['log']) ):
                        reqID = entry['log'].replace("WARNING:root:", "")
                        self.reqIDs.append(reqID)
                        self.reqMsgDic[reqID] = self.msgExe[id]
                        break

    def getData(self):
        print(self.function)
        data = {}
        reqExeMap = {}
        counter = 0
        for id in self.reqIDs:
            foundFlag = False
            for entry in self.logs:
                if entry['log'] is not None:
                    if(("WARNING:root:"+id) in entry['log']):
                        counter += 1
                        self.funcExecodes.append(entry['execution_id'])
                        reqExeMap[entry['execution_id']] = id
                        foundFlag = True
                        break
            if foundFlag == False:
                print(id+" NOT FOUND")
        print("finalCounter: "+ str(counter))
        for id in self.funcExecodes:
            data[reqExeMap[id]] = {}
            data[reqExeMap[id]]["message"] = self.reqMsgDic[reqExeMap[id]]
            for entry in self.logs:

                if(entry['execution_id'] == id and (entry['log'] == "Function execution started") ):
                    if entry['time_utc'].endswith('Z'):
                        entry['time_utc'] = entry['time_utc'][:-1]+".000"
#                     dateStart = datetime.datetime.strptime(entry['time_utc'], "%Y-%m-%d %H:%M:%S.%f")
                    dateStart = entry['time_utc']
                    data[reqExeMap[id]]["start"]  = dateStart
                elif (entry['execution_id'] == id and ("finished with status" in entry['log']) ):
                    if entry['time_utc'].endswith('Z'):
                        entry['time_utc'] = entry['time_utc'][:-1]+".000"
#                     dateFinish = datetime.datetime.strptime(entry['time_utc'], "%Y-%m-%d %H:%M:%S.%f")
                    dateFinish = entry['time_utc']
                    data[reqExeMap[id]]["finish"]  = dateFinish
        print(len(data))
        with open(os.getcwd()+"/data/"+ self.workflow+ "/"+str(self.function)+', data.json', 'a') as outfile:
            json.dump(data, outfile)
        print(self.function + " DONE")
        return os.getcwd()+"/data/"+ self.workflow+ "/"+str(self.function)+', data.json'
            