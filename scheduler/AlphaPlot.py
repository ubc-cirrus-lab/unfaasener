from MINLPSolver import OffloadingSolver
from tabnanny import verbose
from mip import *
import os
import json
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()
import itertools
import numpy as np
from matplotlib.ticker import StrMethodFormatter


class AlphaPlot:

        def __init__(self, workflow):
            self.workflow = workflow
            #########
            self.decisionMode = "default"
            self.mode = "cost"
            self.toleranceWindow = 0
            #########
            self.resultsDataFrame = {}
            self.jsonPath = str(Path(os.getcwd()).resolve().parents[0]) + "/log_parser/get_workflow_logs/data/" + workflow+".json"
            with open(self.jsonPath, 'r') as json_file:
                self.workflow_json = json.load(json_file)
            number = len(self.workflow_json["workflowFunctions"])
            self.alphas = np.arange(0, 1.05, 0.05)
            self.initialDecisions = [list(i) for i in itertools.product([0, 1], repeat=number)]
            self.addedColdStartsPerAlpha = {}
            self.costPerAlpha = {}
            for alpha in self.alphas:
                self.addedColdStartsPerAlpha[alpha] = []
                self.costPerAlpha[alpha] = []
            


        def getData(self):
            self.resultsDataFrame["Alpha"] = []
            self.resultsDataFrame["Cost"] = []
            self.resultsDataFrame["ColdStarts"] = []
            self.resultsDataFrame["initialDecision"] = []
            self.resultsDataFrame["initialDecisionIndex"] = []
            for alpha in self.alphas:
                counter = 0 
                for decision in self.initialDecisions:
                    self.getDecision(decision, alpha, counter)
                    counter += 1


            # for alpha in self.alphas:
            #     for item in range(len(self.costPerAlpha[alpha])):
            #         self.resultsDataFrame["Alpha"].append(float("{:.2f}".format(alpha)))
            #         self.resultsDataFrame["Cost"].append(self.costPerAlpha[alpha][item])
            #         self.resultsDataFrame["ColdStarts"].append(self.addedColdStartsPerAlpha[alpha][item])

            resultsDF = pd.DataFrame(self.resultsDataFrame)
            resultsDF.to_pickle(os.getcwd()+ "/data/plots/HeatMap, "+self.workflow +", AlphaPlotResults.pkl")
            resultsDF.to_csv(os.getcwd()+"/data/plots/HeatMap, "+self.workflow+",AlphaPlotResults.csv")
            self.getPlot(resultsDF)
            return resultsDF




        
        def getPlot(self,df):
            sns.set(style="whitegrid")
            paper_rc = {'lines.linewidth': 3, 'lines.markersize': 5}  
            sns.set_context("paper", rc = paper_rc)   
            plt.rc('font', size=22,weight='bold')
            plt.rc('xtick', labelsize=22)
            plt.rc('ytick', labelsize=22)
            plt.figure(figsize=(25, 15))
            # df["Alpha"] = (1- df["Alpha"])
            # plot = sns.pointplot(x="Alpha", y="ColdStarts", data=df, capsize=.2, linewidth = 5,  color = '#1c6274')
            # plt.xlabel('Locality Weight (alpha)', fontsize = 26, fontweight = 'bold')
            # plt.ylabel('Migration Induced ColdStarts',  fontsize = 26, fontweight = 'bold')
            # plt.title(('Migration Induced ColdStarts Vs Locality Weight - ' + self.workflow), fontweight = 'bold', fontsize = 32)
            # df["initialDecision"] = str(df["initialDecision"])
            # cs = df[['initialDecisionIndex', 'Alpha', 'ColdStarts']].copy()
            cs = df.pivot("initialDecisionIndex", "Alpha", "ColdStarts")
            plot = sns.heatmap(cs, cmap='coolwarm')
            plt.xlabel('Locality Weight (alpha)', fontsize = 26, fontweight = 'bold')
            # plt.ylabel('Migration Induced ColdStarts',  fontsize = 26, fontweight = 'bold')
            plt.ylabel('Initial State',  fontsize = 26, fontweight = 'bold')
            plt.title(('Migration Induced ColdStarts Heatmap - ' + self.workflow), fontweight = 'bold', fontsize = 32)
            # plt.title(('Migration Induced ColdStarts Vs Locality Weight - ' + self.workflow), fontweight = 'bold', fontsize = 32)
            fig = plot.get_figure()
            fig.savefig(os.getcwd()+"/plots/HeatMap, "+self.workflow+", coldStarts-alpha.png") 
            plt.figure(figsize=(25, 15))
            # plot2 = sns.pointplot(x="Alpha", y="Cost", data=df, capsize=.2, linewidth = 5)
            cost = df.pivot("initialDecisionIndex", "Alpha", "Cost")
            # cost = df[['initialDecisionIndex', 'Alpha', 'Cost']].copy()
            # cs = df.pivot("initialDecision", "Alpha", "ColdStarts")
            plot2 = sns.heatmap(cost,  cmap='coolwarm')
            plt.xlabel('Locality Weight (alpha)', fontsize = 26, fontweight = 'bold')
            # plt.ylabel('Cost',  fontsize = 26, fontweight = 'bold')
            plt.ylabel('Initial State',  fontsize = 26, fontweight = 'bold')
            plt.title(('Cost Heatmap - ' + self.workflow), fontweight = 'bold', fontsize = 32)
            # plt.title(('Cost Vs Locality Weight - ' + self.workflow), fontweight = 'bold', fontsize = 32)
            fig2 = plot2.get_figure()
            fig2.savefig(os.getcwd()+"/plots/HeatMap, "+self.workflow+", cost-alpha.png") 


        def getDecision(self, decision, alpha, counter):
            with open(self.jsonPath, 'r') as json_file:
                workflow_json = json.load(json_file)
            workflow_json["lastDecision"] = decision
            with open(self.jsonPath, 'w') as json_file:
                json.dump(workflow_json, json_file)
            solver = OffloadingSolver(None, None, self.workflow, self.mode, self.decisionMode, self.toleranceWindow)
            availResources =  {'cores':1000, 'mem_mb':500000}
            x, cost = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
            introducedColdStarts = 0
            for i in range(len(x)):
                if x[i] != decision[i]:
                    introducedColdStarts +=1
            (self.addedColdStartsPerAlpha[alpha]).append(introducedColdStarts)
            (self.costPerAlpha[alpha]).append(cost)
            self.resultsDataFrame["Alpha"].append(float("{:.2f}".format(alpha)))
            self.resultsDataFrame["Cost"].append(cost)
            self.resultsDataFrame["ColdStarts"].append(introducedColdStarts)
            self.resultsDataFrame["initialDecision"].append(decision)
            self.resultsDataFrame["initialDecisionIndex"].append(counter)
            print("Alpha:{}, Decision:{} --> Cost:{}, ColdStarts:{}".format(alpha, decision, cost,introducedColdStarts))

            

if __name__ == "__main__":
    workflow = "ImageProcessingWorkflow"
    # workflow = "Text2SpeechCensoringWorkflow"
    obj = AlphaPlot(workflow)
    # data = obj.getData()
    dataframe = pd.read_csv("/Users/ghazal/Desktop/UBC/Research/de-serverlessization/scheduler/data/plots/HeatMap, ImageProcessingWorkflow,AlphaPlotResults.csv")
    obj.getPlot(dataframe)



