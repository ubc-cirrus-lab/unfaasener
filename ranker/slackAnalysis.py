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
import networkx as nx
from criticalpath import Node
import plotly.express as px
from IPython.display import Image
from pathlib import Path

class slackAnalysis:

    def __init__(self, mode, sp, inputName, workflow):
        self.workflow = workflow
        jsonPath = str(Path(os.getcwd()).resolve().parents[0]) + "/log_parser/get_workflow_logs/data/" + self.workflow+".json"
        dataframePath = str(Path(os.getcwd()).resolve().parents[0]) + "/log_parser/get_workflow_logs/data/" + self.workflow + "/generatedData.pkl"
        with open(jsonPath, 'r') as json_file:
            workflow_json = json.load(json_file)
        dataframe = pd.read_pickle(dataframePath)
        df = dataframe.loc[dataframe["inputs"] == inputName]
        df = df.drop(columns=["reqID", "inputs"])
        NI = len(df)
        initial = workflow_json["initFunc"]
        self.initial = initial
        workflowFunctions = workflow_json["workflowFunctions"]
        successors = workflow_json["successors"]
        self.successors = successors
        memory = workflow_json["memory"]
        self.slackAnalysisData = {}
        self.pricing_resolution = 100
        self.workflowFunctions = workflowFunctions
        self.es = {}
        self.NI = NI
        self.ef = {}
        self.ls = {}
        self.lf = {}
        self.df = df
        self.slackPath = {}
        self.searchSlacks = []
        self.searchFuns= []
        self.dependencies = []
        self.tasks = {}
        self.mode = mode
        if mode == "cost":
            self.costCalc(df, sp, workflowFunctions, successors)
            self.memory = memory
        if mode == "latency":
            self.latencyCalc(df, sp)
        self.duration, self.crPath = self.findCriticalPath(self.tasks, self.dependencies)
        self.completeESEF(initial)
        self.completeLSLF(self.duration, self.crPath)
        # self.getSlackDataframe()
        
        
    def getSlackDataframe(self):
        self.slackAnalysisData["es"] = []
        self.slackAnalysisData["id"] = []
        self.slackAnalysisData["cost"] = [0]*len(self.df.columns)
        self.slackAnalysisData["path"] = [0]*len(self.df.columns)
        self.slackAnalysisData["NI"] = [self.NI]*len(self.df.columns)
        self.slackAnalysisData["ls"] = []
        self.slackAnalysisData["ef"] = []
        self.slackAnalysisData["lf"] = []
        self.slackAnalysisData["duration"] = []
        self.slackAnalysisData["slackTime"] = []
        self.slackAnalysisData["function"] = self.df.columns
        for func in self.slackAnalysisData["function"]:
            if func in self.workflowFunctions:
                self.slackAnalysisData["id"].append(self.workflowFunctions.index(func))
            else:
#                 TO_DO: Ask about communication ID 
                self.slackAnalysisData["id"].append("-")
                
            self.slackAnalysisData["es"].append(self.es[func])
            self.slackAnalysisData["ls"].append(self.ls[func])
            self.slackAnalysisData["ef"].append(self.ef[func])
            self.slackAnalysisData["lf"].append(self.lf[func])
            self.slackAnalysisData["duration"].append(self.tasks[func])
            slack = self.lf[func] - self.ef[func]
            if slack < 10^-12 or slack< -10^-12:
                slack = 0
            self.slackAnalysisData["slackTime"].append(slack)
        if self.mode == "cost":
            self.slackAnalysisData["Memory(GB)"] = self.memory
            priceDuration = (np.ceil(np.array(self.slackAnalysisData["duration"])/self.pricing_resolution)*self.pricing_resolution)
            # self.slackAnalysisData["GB-sec"] = (np.array(self.slackAnalysisData["Memory(GB)"]) * priceDuration)/1000
            for i in range(len(self.df.columns)):
                self.slackAnalysisData["cost"][i] = self.cost_estimator(self.slackAnalysisData["NI"][i], self.slackAnalysisData["duration"][i], self.slackAnalysisData["Memory(GB)"][i])
        self.findPaths()
        listFuns = list(self.slackAnalysisData["function"])
        pathID = 1
        for key in self.slackPath.keys():
            print(key)
            for f in self.slackPath[key]:
                self.slackAnalysisData["path"][listFuns.index(f)] = pathID
            pathID +=1
        slackDF = pd.DataFrame(self.slackAnalysisData)
        slackDF.to_pickle(os.getcwd()+ "/data/"+self.workflow +", "+self.mode+",slackData.pkl")
        return slackDF


    def findPaths(self):
        index = (list(self.slackAnalysisData["function"])).index(self.initial)
        self.slackPath[self.slackAnalysisData["slackTime"][index]] = [self.initial]
        self.searchSlacks.append(self.slackAnalysisData["slackTime"][index])
        self.searchFuns.append(self.initial)
        for sfun in self.searchFuns:
            self.iterateSearch(sfun, self.searchSlacks[self.searchFuns.index(sfun)])
        print(self.slackPath)

        
        
    def iterateSearch(self, func, sslack):
        for suc in self.successors[self.workflowFunctions.index(func)]:
            if self.slackAnalysisData["slackTime"][(list(self.slackAnalysisData["function"])).index(suc)] == sslack:
                if suc not in self.slackPath[sslack]:
                    self.slackPath[sslack].append(suc)
                self.iterateSearch(suc, sslack)

            else:
                if (self.slackAnalysisData["slackTime"][(list(self.slackAnalysisData["function"])).index(suc)]) not in self.slackPath.keys():
                    self.slackPath[self.slackAnalysisData["slackTime"][(list(self.slackAnalysisData["function"])).index(suc)]] = [suc]
                    self.searchFuns.append(suc)
                    self.searchSlacks.append(self.slackAnalysisData["slackTime"][(list(self.slackAnalysisData["function"])).index(suc)])



    def costCalc(self, df, sp, workflowFunctions, successors):
        df = df[workflowFunctions]
        self.df = df
        for col in df.columns:
            if sp == "mean":
                self.tasks[col] = df[col].mean()
            else:
                self.tasks[col] = df[col].quantile(sp)

        functionTasks = workflowFunctions
        for func in workflowFunctions:
            index = workflowFunctions.index(func)
            for i in successors[index]:
                self.dependencies.append((func, i ))
        
    def completeESEF(self, initial):
        self.es[initial] = 0
        self.ef[initial] = self.tasks[initial]
        nextSteps = []
        for d in self.dependencies:
            if d[0] == initial:
                if d[1] in self.es:
                    self.es[d[1]] = max( self.es[d[1]], self.ef[initial])
                    self.ef[d[1]] = self.es[d[1]] + self.tasks[d[1]]
                else:
                    self.es[d[1]] = self.ef[initial]
                    self.ef[d[1]] = self.es[d[1]] + self.tasks[d[1]]
                nextSteps.append(d[1])
        for n in nextSteps:
            initial = n
            for d in self.dependencies:
                if d[0] == initial:
                    if d[1] in self.es:
                        self.es[d[1]] = max( self.es[d[1]], self.ef[initial])
                        self.ef[d[1]] = self.es[d[1]] + self.tasks[d[1]]
                    else:
                        self.es[d[1]] = self.ef[initial]
                        self.ef[d[1]] = self.es[d[1]] + self.tasks[d[1]]
                    nextSteps.append(d[1])
        
        
        
    def completeLSLF(self, duration, criticalPath):
        terminals = []
        for d in self.dependencies:
            terminalFlag = True
            for d2 in self.dependencies:
                if d[1] == d2[0]:
                    terminalFlag = False
                    break
            if terminalFlag == True:
                terminals.append(d[1])
        for t in terminals:
            self.lf[t] = duration 
            self.ls[t] = duration - self.tasks[t]
            
        for t in terminals:
            for d in self.dependencies:
                if d[1] == t:
                    if d[0] in self.lf:
                        self.lf[d[0]] = min( self.lf[d[0]], self.ls[t])
                        self.ls[d[0]] = max(0, self.lf[d[0]] - self.tasks[d[0]])
                    else:
                        self.lf[d[0]] = self.ls[t]
                        self.ls[d[0]] = max(0, self.lf[d[0]] - self.tasks[d[0]])
                        
                    terminals.append(d[0])     
    

    def latencyCalc(self, df, sp):
        for col in df.columns:
            if sp == "mean":
                self.tasks[col] = df[col].mean()
            else:
                self.tasks[col] = df[col].quantile(sp)

        functionTasks = list(df.columns)
        for func in functionTasks:
            if "-" not in func:
                for func2 in functionTasks:
                    if ("-" in func2) and (func2.split("-")[0] == func):
                        index = functionTasks.index(func)
                        self.dependencies.append((func, func2))
            else:
                self.dependencies.append((func, func.split("-")[1]))


    def findCriticalPath(self, tasks, dependencies):
        print(tasks)
        workflow = Node("Workflow")
        for t in tasks:
            workflow.add(Node(t, duration = tasks[t]))
        for d in dependencies:
            workflow.link(d[0], d[1])
        workflow.update_all()
        crit_path = [str(n) for n in workflow.get_critical_path()]
        workflow_duration = workflow.duration

        print(f"The current critical path is: {crit_path}")
        print("."*50)
        print(f"The current workflow duration is: {workflow_duration} milliseconds")
        return workflow_duration, crit_path
    
    def cost_estimator(self, NI, ET, GB):
        free_tier_invocations = 2000000
        free_tier_GB = 400000
        free_tier_GHz = 200000
        unit_price_invocation = 0.0000004
        unit_price_GB = 0.0000025
        unit_price_GHz = 0.0000100

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
        cost = ((NI-free_tier_invocations)*unit_price_invocation) + ( ( (NI*(math.ceil(ET/100))*0.1*GB) - free_tier_GB )*unit_price_GB ) + ( ( (NI*(math.ceil(ET/100))*0.1*Ghz) - free_tier_GHz )*unit_price_GHz )
        return max(0, cost)


if __name__ == "__main__":
    # mode = "cost"
    # sp = "mean"
    mode = "latency"
    sp = 0.95
    workflow = "ImageProcessingWorkflow"
    input = "Final-test1.jpg"
    # workflow = "Text2SpeechCensoringWorkflow"
    # input = "Ach it was hopeless. That was what ye felt. These bastards. What can ye do but. Except start again so he started again. That was what he did he started again … ye just plough on, ye plough on, ye just fucking plough on … ye just fucking push ahead, ye get fucking on with it"

    slackAnalysisObj = slackAnalysis(mode,sp, input, workflow)
    slackDF = slackAnalysisObj.getSlackDataframe()
    print(slackDF)



