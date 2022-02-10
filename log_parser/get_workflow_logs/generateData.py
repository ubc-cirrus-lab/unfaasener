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


class generateData:
    def __init__(self, funcPaths, workflow, initFunc, workflowFunctions, successors):
        self.workflow  = workflow

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


        for func in workflowFunctions:
            for successor in successors[workflowFunctions.index(func)]:
                generatedData [func+"-"+successor] = [((a_i - b_i).microseconds/1000) for a_i, b_i in zip(generatedData2[successor+"-Start"], generatedData2[func+"-Finish"])]


        print(generatedData)
        df = pd.DataFrame(generatedData)
        print(df)
        df.to_pickle(os.getcwd()+"/data/"+self.workflow +"/generatedData.pkl")
        df.to_csv(os.getcwd()+"/data/"+self.workflow ++"/CSV-generatedData.pkl")
        print("Data File Saved")
