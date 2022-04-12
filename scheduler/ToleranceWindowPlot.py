import sys
sys.path.append("..")
from distutils import core
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


class AlphaPlot:

        def __init__(self, workflow):
            self.workflow = workflow
            self.resultsDataFrame = {}
            self.resultsDataFrame["Alpha"] = []
            self.resultsDataFrame["Cost"] = []
            self.resultsDataFrame["latency"] = []
            self.resultsDataFrame["ToleranceWindow"] = []
            #########
            self.decisionMode = "default"
            self.mode = "latency"
            #########
            self.jsonPath = str(Path(os.getcwd()).resolve().parents[0]) + "/log_parser/get_workflow_logs/data/" + workflow+".json"
            with open(self.jsonPath, 'r') as json_file:
                self.workflow_json = json.load(json_file)
            number = len(self.workflow_json["workflowFunctions"])
            # self.alphas = np.arange(0, 1.2, 0.2)
            self.alphas = [0.5]
            self.initialDecisions = [list(i) for i in itertools.product([0, 1], repeat=number)]
            


        def getData(self):
            tw = [0, 25, 50, 100, 1000]
            for tolerance in tw:
                for alpha in self.alphas:
                    for decision in self.initialDecisions:
                        print("tolerance {}".format(tolerance))
                        self.getDecision(decision, alpha, 1000, 500000, tolerance)
                print("tolerance {} Done!!".format(tolerance))
            resultsDF = pd.DataFrame(self.resultsDataFrame)
            resultsDF.to_pickle(os.getcwd()+ "/data/plots/Tolerance,  Alpha = 0.5, "+self.workflow +", AlphaPlotResults.pkl")
            resultsDF.to_csv(os.getcwd()+"/data/plots/Tolerance,  Alpha = 0.5, "+self.workflow+",AlphaPlotResults.csv")
            self.getPlot(resultsDF)
            return resultsDF




        
        def getPlot(self,df):
            sns.set(style="whitegrid")
            sns.color_palette("husl")
            paper_rc = {'lines.linewidth': 3, 'lines.markersize': 5}  
            sns.set_context("paper", rc = paper_rc)  
            plt.rc('font', size=22,weight='bold')
            plt.rc('xtick', labelsize=22)
            plt.rc('ytick', labelsize=22)
            plt.figure(figsize=(25, 15))
            plot = sns.pointplot(x="ToleranceWindow", y="latency", capsize=.2, hue="Alpha",data=df, linewidth = 5,  palette="CMRmap_r")
            # leg_handles = plot.get_legend_handles_labels()[0]
            # plot.legend(leg_handles, ['Unlimited', "0", "2" ,"5", "8"], title='Available Cores')
            plt.xlabel('Tolerance Window(milliseconds)', fontsize = 26, fontweight = 'bold')
            plt.legend(fontsize=24, title_fontsize = 24,title='Locality Weight (Alpha)')
            plt.ylabel('Added Latency',  fontsize = 26, fontweight = 'bold')
            plt.title(('Added Latency Vs Tolerance Window - ' + self.workflow), fontweight = 'bold', fontsize = 32)
            fig = plot.get_figure()
            fig.savefig(os.getcwd()+"/plots/Tolerance,  Alpha = 0.5, "+self.workflow+", Added Latency-alpha.png") 
            plt.figure(figsize=(25, 15))
            plot2 = sns.pointplot(x="ToleranceWindow", y="Cost",capsize=.2, hue="Alpha",data=df, linewidth = 5,  palette="CMRmap_r")
            # leg_handles = plot2.get_legend_handles_labels()[0]
            # plot2.legend(leg_handles, ['Unlimited', "0", "2" ,"5", "8"], title='Available Cores')
            plt.xlabel('Tolerance Window(milliseconds)', fontsize = 26, fontweight = 'bold')
            plt.ylabel('Cost Function Value',  fontsize = 26, fontweight = 'bold')
            plt.legend(fontsize=24, title_fontsize = 24, title='Locality Weight (Alpha)')
            plt.title(('Cost Function Value Vs Tolerance Window - ' + self.workflow), fontweight = 'bold', fontsize = 32)
            fig2 = plot2.get_figure()
            fig2.savefig(os.getcwd()+"/plots/Tolerance, Alpha = 0.5, "+self.workflow+", cost-alpha.png") 


        def getDecision(self, decision, alpha, cores, mem, toleranceWindow):
            with open(self.jsonPath, 'r') as json_file:
                workflow_json = json.load(json_file)
            workflow_json["lastDecision"] = decision
            with open(self.jsonPath, 'w') as json_file:
                json.dump(workflow_json, json_file)
            solver = OffloadingSolver(None, None, self.workflow, self.mode, self.decisionMode, toleranceWindow)
            availResources =  {'cores':cores, 'mem_mb':mem}
            x, cost, latency = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
            self.resultsDataFrame["Alpha"].append(float("{:.2f}".format(alpha)))
            self.resultsDataFrame["Cost"].append(cost)
            self.resultsDataFrame["latency"].append(latency)
            self.resultsDataFrame["ToleranceWindow"].append(toleranceWindow)
            print("Alpha:{}, Decision:{} --> Cost:{}, latency:{}".format(alpha, decision, cost,latency))

            

if __name__ == "__main__":
    # workflow = "ImageProcessingWorkflow"
    workflow = "Text2SpeechCensoringWorkflow"
    obj = AlphaPlot(workflow)
    data = obj.getData()
    # dataframe = pd.read_csv("/Users/ghazal/Desktop/UBC/Research/de-serverlessization/scheduler/data/plots/Tolerance, Alpha = 0.5, Text2SpeechCensoringWorkflow,AlphaPlotResults.csv")
    # obj.getPlot(dataframe)



