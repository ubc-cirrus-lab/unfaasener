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


class generateData:
    def __init__(self, funcPaths, workflow, initFunc, workflowFunctions, successors):


        self.workflow  = workflow

        jsonPath = str(Path(os.getcwd()).resolve().parents[1]) + "/scheduler/data/"+ self.workflow+"-prevCost.json"
        with open(jsonPath, 'r') as json_file:
            prevCost_json = json.load(json_file)
        with open(os.getcwd()+"/data/" + self.workflow+".json", 'r') as json_file:
            workflow_json = json.load(json_file)
        memory = workflow_json["memory"]
        predecessors = workflow_json["predecessors"]
        data = {}
        reqIDs = []
        inputs=[]
        func1S = []
        generatedData={}
        generatedData2={}
        for path in funcPaths:
            with open(path) as json_file:
                data[(path.split("/")[-1]).split(",")[0]]=(json.load(json_file))

        for req in data[initFunc]:
            reqIDs.append(req)
            inputs.append(data[initFunc][req]['message'])
        generatedData["reqID"] = reqIDs
        generatedData["inputs"] = inputs

        addedFuns = []
        mergedFuns = []
        mergedDict = {}
        for func in workflowFunctions:
            if (len(predecessors[workflowFunctions.index(func)]) > 1):
                for p in predecessors[workflowFunctions.index(func)]: 
                    name = func+"*"+p 
                    addedFuns.append(name)
                workflowFunctions = workflowFunctions + addedFuns
                mergedFuns.append(func)
                mergedDict[func] = {}
                mergedDict[func]["start"] = {}
                mergedDict[func]["finish"] = {}
                mergedDict[func]["duration"] = {}
                # workflowFunctions.remove(func)
        print("MERGED")
        print(mergedFuns)
        for func in workflowFunctions:
            if func not in mergedFuns:
                generatedData2[func+"-Start"] = []
                generatedData2[func+"-Finish"] = []
                if "*" not in func:
                    generatedData[func+", Cost"] = []
                    generatedData[func+", Latency"] = []
                newData = data[func]
                for req in reqIDs:
                    start = newData[req]["start"]
                    start = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S.%f")
                    generatedData2[func+"-Start"].append(start)
                    finish = newData[req]["finish"]
                    finish = datetime.datetime.strptime(finish, "%Y-%m-%d %H:%M:%S.%f")
                    generatedData2[func+"-Finish"].append(finish)
                    difference = finish - start
                    if "*" not in func:
                        generatedData[func+", Cost"].append(difference.microseconds/1000)
                        generatedData[func+", Latency"].append(difference.microseconds/1000)
                    GB = memory[workflowFunctions.index(func.split("*")[0])]
                    if GB ==  0.128:
                        Ghz = 0.2
                    elif GB == 0.256:
                        Ghz = 0.4
                    elif GB == 0.512:
                        Ghz = 0.8
                    elif GB == 1:
                        Ghz = 1.4
                    elif GB == 2:
                        Ghz = 2.4
                    elif GB == 4:
                        Ghz = 4.8
                    elif GB == 8:
                        Ghz = 4.8
                    prevCost_json["GB-Sec"] = prevCost_json["GB-Sec"] + (math.ceil((difference.microseconds/1000)/100))*0.1*GB
                    prevCost_json["GHz-Sec"] = prevCost_json["GHz-Sec"] + (math.ceil((difference.microseconds/1000)/100))*0.1*Ghz
                    if "*" in func:
                        if req not in mergedDict[func.split("*")[0]]["start"]:
                            mergedDict[func.split("*")[0]]["start"][req] = start
                            mergedDict[func.split("*")[0]]["finish"][req] = finish
                            mergedDict[func.split("*")[0]]["duration"][req] = difference.microseconds/1000
                        else:
                            mergedDict[func.split("*")[0]]["finish"][req]=max(finish, mergedDict[func.split("*")[0]]["finish"][req])
                            mergedDict[func.split("*")[0]]["duration"][req] += difference.microseconds/1000
        for func in mergedDict:
            generatedData2[func+"-Start"] = []
            generatedData2[func+"-Finish"] = []
            generatedData[func+", Cost"] = []
            generatedData[func+", Latency"] = []
            for req in reqIDs:
                generatedData2[func+"-Finish"].append(mergedDict[func]["finish"][req])
                generatedData2[func+"-Start"].append(mergedDict[func]["start"][req])
                generatedData[func+", Cost"].append(mergedDict[func]["duration"][req])
                generatedData[func+", Latency"].append((mergedDict[func]["finish"][req] - mergedDict[func]["start"][req]).microseconds/1000)


        for func in workflowFunctions:
            if "*" in func:
                 generatedData [func.split("*")[1]+"-"+func.split("*")[0]] = [((a_i - b_i).microseconds/1000) for a_i, b_i in zip(generatedData2[func.split("*")[0]+"-Start"], generatedData2[func.split("*")[1]+"-Finish"])]
            
            else:
                if func in mergedFuns:
                    print(successors[workflowFunctions.index(func)])
                for successor in successors[workflowFunctions.index(func)]:
                    if func+"-"+successor not in generatedData:
                        generatedData [func+"-"+successor] = [((a_i - b_i).microseconds/1000) for a_i, b_i in zip(generatedData2[successor+"-Start"], generatedData2[func+"-Finish"])]

        prevCost_json["NI"] = prevCost_json["NI"] + (len(generatedData["reqID"])* len(workflowFunctions))
        print(generatedData)
        df = pd.DataFrame(generatedData)
        print(df)
        jsonPath = str(Path(os.getcwd()).resolve().parents[1]) + "/scheduler/data/"+ self.workflow+"-prevCost.json"
        with open(jsonPath, 'w') as json_file:
            json.dump(prevCost_json ,json_file)
        json_file.close()
        df.to_pickle(os.getcwd()+"/data/"+self.workflow +"/generatedData.pkl")
        df.to_csv(os.getcwd()+"/data/"+self.workflow +"/CSV-generatedData.csv")
        print("Data File Saved")
