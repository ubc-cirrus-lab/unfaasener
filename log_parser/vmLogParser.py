
from re import X
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
from pathlib import Path
# .....TO-DO: Implement parser for vm logs.....
# input: json file in this format:{'1a2211aa1a014a5694becc85d78b03f4': 
# {'Text2SpeechCensoringWorkflow_Text2Speech': '2022-05-28 17:10:11.152690;2022-05-28 17:10:13.119145', 
# 'Text2SpeechCensoringWorkflow_Conversion': '2022-05-28 17:10:13.328205;2022-05-28 17:10:15.280813', 
# 'Text2SpeechCensoringWorkflow_MergedFunction': '2022-05-28 17:10:14.849704;2022-05-28 17:10:16.368501
# _2022-05-28 17:10:17.127005;2022-05-28 17:10:18.605733', 'Text2SpeechCensoringWorkflow_Compression': '2022-05-28 17:10:15.499992;2022-05-28 17:10:17.238899', 'Text2SpeechCensoringWorkflow_Censor': '2022-05-28 17:10:18.783882;2022-05-28 17:10:21.594467'}}



class vmLogParser:
    def __init__(self, vmNum):
        self.vmNum = vmNum
        # jsonPath and content for that vm
        self.vmData = {}



    def extractData(self):
        for reqID in self.vmData.keys():
            self.dictData = {}
            self.dictData["function"] = []
            self.dictData["reqID"] = []
            self.dictData["start"] = []
            self.dictData["finish"] = []
            self.dictData["mergingPoint"] = []
            self.dictData["host"] = []
            self.dictData["duration"] = []
            for func in (self.vmData[reqID]).keys():
                self.workflow = func.split("_")[0]
                branches = len((self.vmData[reqID][func]).split("_"))
                if branches == 1:
                    self.dictData["function"].append(func)
                    self.dictData["reqID"].append(reqID)
                    start = ((self.vmData[reqID][func]).split(";"))[0]
                    if (start).endswith('Z'):
                        start = (start)[:-1]+".000"
                        start = datetime.datetime.strptime((start), "%Y-%m-%d %H:%M:%S.%f")
                    finish = ((self.vmData[reqID][func]).split(";"))[1]
                    if (finish).endswith('Z'):
                        finish = (finish)[:-1]+".000"
                        finish = datetime.datetime.strptime((finish), "%Y-%m-%d %H:%M:%S.%f")
                    self.dictData["start"].append(start)
                    self.dictData["finish"].append(finish)
                    self.dictData["mergingPoint"].append(None)
                    self.dictData["host"].append("vm" + str(self.vmNum))
                    self.dictData["duration"].append(((finish - start).total_seconds())*1000)
                else:
                    branches = ((self.vmData[reqID][func]).split("_"))
                    for branch in branches:
                        self.dictData["function"].append(func)
                        self.dictData["reqID"].append(reqID)
                        start = (branch.split(";"))[0]
                        if (start).endswith('Z'):
                            start = (start)[:-1]+".000"
                            start = datetime.datetime.strptime((start), "%Y-%m-%d %H:%M:%S.%f")
                        finish = (branch.split(";"))[1]
                        if (finish).endswith('Z'):
                            finish = (finish)[:-1]+".000"
                            finish = datetime.datetime.strptime((finish), "%Y-%m-%d %H:%M:%S.%f")
                        self.dictData["start"].append(start)
                        self.dictData["finish"].append(finish)
                        self.dictData["mergingPoint"].append(None)
                        self.dictData["host"].append("vm" + str(self.vmNum))
                        self.dictData["duration"].append(((finish - start).total_seconds())*1000)
            df = pd.DataFrame(self.dictData)
            if (os.path.isfile(os.getcwd()+"/data/"+self.workflow +"/generatedDataFrame.pkl")):
                        prevDataframe = pd.read_pickle(os.getcwd()+"/data/"+self.workflow +"/generatedDataFrame.pkl")
                        newDataFrame = pd.concat([prevDataframe, df]).drop_duplicates().reset_index(drop=True)
                        newDataFrame.to_pickle(os.getcwd()+"/data/"+self.workflow +"/generatedDataFrame.pkl")
                        newDataFrame.to_csv(os.getcwd()+"/data/"+self.workflow +"/generatedDataFrame.csv")

            else:
                        df.to_pickle(os.getcwd()+"/data/"+self.workflow +"/generatedDataFrame.pkl")
                        df.to_csv(os.getcwd()+"/data/"+self.workflow +"/generatedDataFrame.csv")

