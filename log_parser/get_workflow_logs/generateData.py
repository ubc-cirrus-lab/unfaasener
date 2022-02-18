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

        jsonPath = str(Path(os.getcwd()).resolve().parents[1]) + "/ranker/data/"+ self.workflow+"-prevCost.json"
        with open(jsonPath, 'r') as json_file:
            prevCost_json = json.load(json_file)
        with open(os.getcwd()+"/data/" + self.workflow+".json", 'r') as json_file:
            workflow_json = json.load(json_file)
        memory = workflow_json["memory"]
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
        for func in workflowFunctions:
            generatedData2[func+"-Start"] = []
            generatedData2[func+"-Finish"] = []
            generatedData[func] = []
            newData = data[func]
            for req in reqIDs:
                start = newData[req]["start"]
                start = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S.%f")
                generatedData2[func+"-Start"].append(start)
                finish = newData[req]["finish"]
                finish = datetime.datetime.strptime(finish, "%Y-%m-%d %H:%M:%S.%f")
                generatedData2[func+"-Finish"].append(finish)
                difference = finish - start
                generatedData[func].append(difference.microseconds/1000)
                GB = memory[workflowFunctions.index(func)]
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
                



        for func in workflowFunctions:
            for successor in successors[workflowFunctions.index(func)]:
                generatedData [func+"-"+successor] = [((a_i - b_i).microseconds/1000) for a_i, b_i in zip(generatedData2[successor+"-Start"], generatedData2[func+"-Finish"])]

        prevCost_json["NI"] = prevCost_json["NI"] + (len(generatedData["reqID"])* len(workflowFunctions))
        print(generatedData)
        df = pd.DataFrame(generatedData)
        print(df)
        jsonPath = str(Path(os.getcwd()).resolve().parents[1]) + "/ranker/data/"+ self.workflow+"-prevCost.json"
        with open(jsonPath, 'w') as json_file:
            json.dump(prevCost_json ,json_file)
        json_file.close()
        df.to_pickle(os.getcwd()+"/data/"+self.workflow +"/generatedData.pkl")
        df.to_csv(os.getcwd()+"/data/"+self.workflow +"/CSV-generatedData.csv")
        print("Data File Saved")
