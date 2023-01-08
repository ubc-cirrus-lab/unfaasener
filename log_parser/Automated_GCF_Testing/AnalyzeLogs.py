import json
import datetime
import os
import matplotlib.pyplot as plt
import pandas as pd

class AnalyzeLogs:
    def __init__(self, logsFile, publisherExeFile, vmData, subType):
        self.timeDiff = []
        self.subType = subType
        self.messageSizeArray = []
        self.execodes = []
        self.latencyPerExeCode = {}
        if self.subType == "vm":
            with open(vmData) as json_file:
                self.vmData = json.load(json_file)
        with open(logsFile) as json_file:
            writeLogs = json.load(json_file)
            self.logs = writeLogs["data"]
        with open(publisherExeFile) as json_file:
            self.execodes = json.load(json_file)
        
    
    def parseLogs(self):
        self.fetchExeIDs()
        logsDataFrame = self.getData()
        print("--------------Results-------------")
        print(logsDataFrame)
        print((logsDataFrame.groupby(['Bytes'])).describe())
        return logsDataFrame
            
            
    def getData(self):
        data = {'Bytes': self.messageSizeArray, 'Latency': self.timeDiff}
        logsDF = pd.DataFrame(data)
        return logsDF    
    
    def fetchExeIDs(self):
        if self.subType == "gcf":
            for id in self.execodes:
                startFlag = False
                endFlag = False
                sizeFlag = False
                for entry in self.logs:
                    if(entry['execution_id'] == id and entry['log'] == "Function execution started"):
                        index = self.logs.index(entry)
                        for log in self.logs[:index]:
                            if (log['execution_id'] == id and ("WARNING:root:" in log['log']) ):
                                identifier = log['log']
                                identifier = identifier.replace("WARNING:root:", "")
                                ####
                                break
                        index = self.logs.index(log)
                        for log in self.logs[:index]:
                                if ((identifier in (log['log'])) and (log['name'] == "secondSubscriber")) :
                                    subscriberIndex = self.logs.index(log)
                                    self.subscriberExeID = log['execution_id']
                                    attributes = log['log'].split(",")
                                    for attr in attributes:
                                        if "publishedTime" in attr:
                                            dateFinishedLog = attr.replace("publishedTime:", "")
                                            if dateFinishedLog.endswith('Z'):
                                                dateFinishedLog = dateFinishedLog[:-1]+".000"
                                            dateFinish = datetime.datetime.strptime(dateFinishedLog, "%Y-%m-%d %H:%M:%S.%f")
                                            endFlag = True
                                        elif "messageSize" in attr:
                                            sizeFlag = True
                                            msgSize = attr.replace("messageSize:", "")
                                    for each in self.logs[(subscriberIndex+1):]:
                                        if ((each['log']) == "Function execution started" and each['name'] == "secondSubscriber" and each['execution_id'] == self.subscriberExeID):
                                            if each['time_utc'].endswith('Z'):
                                                each['time_utc'] = each['time_utc'][:-1]+".000"
                                            dateStart = datetime.datetime.strptime(each['time_utc'], "%Y-%m-%d %H:%M:%S.%f")
                                            startFlag = True
                                if endFlag == True and startFlag == True:
                                    break





                        difference = dateStart - dateFinish
                        self.timeDiff.append(difference.microseconds/1000)
                        self.messageSizeArray.append(msgSize)
                        self.latencyPerExeCode[id] = difference.microseconds/1000
                        break
                        
        elif self.subType == "vm":
            for id in self.execodes:
                startFlag = False
                endFlag = False
                sizeFlag = False
                for entry in self.logs:
                    if(entry['execution_id'] == id and entry['log'] == "Function execution started"):
                        index = self.logs.index(entry)
                        for log in self.logs[:index]:
                            if (log['execution_id'] == id and ("WARNING:root:" in log['log']) ):
                                identifier = log['log']
                                identifier = identifier.replace("WARNING:root:", "")
                                break 
                for each in self.vmData:
                    if each == identifier:
                        start = self.vmData[each]["receivedDate"]
                        if start.endswith('Z'):
                            start = start[:-1]+".000"
                        dateStart = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S.%f")
                        startFlag = True
                        end = self.vmData[each]["publishTime"]
                        if end.endswith('Z'):
                            end = end[:-1]+".000"
                        dateFinish = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S.%f")
                        endFlag = True
                        msgSize = self.vmData[each]["msgSize"]
                        sizeFlag = True
                        difference = dateStart - dateFinish
                        self.timeDiff.append(difference.microseconds/1000)
                        self.messageSizeArray.append(msgSize)
                        self.latencyPerExeCode[id] = difference.microseconds/1000
                        break
                
                        
                        
            
        

            
    def createPlot(self, logsDataFrame):
        fig, ax = plt.subplots(figsize=(8,5)) 
        meanDF, ninetyPercentileDF, medianDF = self.getStatistics(logsDataFrame)
        print(logsDataFrame.groupby(['Bytes']).groups.keys())
        ax.plot(logsDataFrame.groupby(['Bytes']).groups.keys(), meanDF.Latency, color="#f05988", marker="o", label="Mean Latency")
        ax.plot(logsDataFrame.groupby(['Bytes']).groups.keys(), ninetyPercentileDF.Latency,color="#55bcbd",marker="o", label="95-Percentile Latency")
        ax.plot(logsDataFrame.groupby(['Bytes']).groups.keys(), medianDF.Latency,color="#1c6274",marker="o", label="Median Latency")
        plt.legend(loc = 'best')
        ax.set_yscale('log')
#         ax.set_xscale('log')
        plt.show()
        
        
    def saveData(self,df):
        runningTime = str(datetime.datetime.utcnow())
        df.to_pickle(os.getcwd()+"/data/" +runningTime+".pkl")
        with open(os.getcwd()+"/data/" +"Latency-Bytes, "+runningTime+".json", "w") as latencyFile:
            json.dump(df, latencyFile)
        
            
            
    def plotEachGp(self, df):
        for gp in df.groupby(['Bytes']).groups.keys():  
            axarr = ((df.groupby(['Bytes'])).get_group(gp)).hist(cumulative=True, column=["Latency"], density = 1)
            for ax in axarr.flatten():
                ax.set_xlabel("Latency for "+ str(gp)+" bytes")
        
        
    def getStatistics(self, logsDF):
        meanDF = logsDF.groupby(['Bytes']).mean()
        ninetyPercentileDF = logsDF.groupby(['Bytes']).quantile(0.95) 
        medianDF = logsDF.groupby(['Bytes']).median() 
        print("--------------MEAN-------------")
        print(meanDF)

        print("--------------95 Percentile-------------")
        print(ninetyPercentileDF)

        print("--------------MEDIAN-------------")
        print(medianDF)
        return meanDF, ninetyPercentileDF, medianDF
    