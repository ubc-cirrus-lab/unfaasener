import subprocess
import json
import shlex
from sys import getsizeof
import time
import os
import math


class CreateGCFLogs:
    def __init__(self, wordsNum, interval, count, sleepTime, testingLargeMessages, invoker, function):
        self.function = function
        self.count = count
        self.testingLargeMessages = testingLargeMessages
        self.messagesize = {}
        self.sleepTime = sleepTime
        self.invoker = invoker
        self.timeDiff = []
        self.execodes = []
        self.allLogs = []
        self.writeLogs = {}
        self.subscriberExe = {}
        self.publisherFinishedTime = {}
        self.wordsNum = wordsNum
        self.interval = interval
        if self.invoker == "vm":
            self.getLogPeriod = math.floor(1000 / (self.count*3))
        else:
            self.getLogPeriod = math.floor(1000 / (self.count*8))
        self.finalWord = False
        self.getBenchmark()

    def getBenchmark(self):
        if self.testingLargeMessages == 1:
            self.messages = self.createLargeWords()
        else:
            self.messages = self.createWords(self.wordsNum, self.interval)
        self.getLogCounter = 0
        for msg in self.messages:
            if msg == self.messages[-1]:
                self.finalWord = True
            self.getLogCounter += 1
            self.getLatency(msg)
        self.saveResults()
        print("Files are saved")
            
    def createLargeWords(self):
        messages = []
        sizes = [(100-49), (1000-49), (10000-49), (100000-49)]
        for size in sizes:
            msg = "x" * size
            messages.append(msg)
        return messages
        
    def saveResults(self):
        with open(os.getcwd()+"/data/" +str(self.invoker)+ ", "+str(self.wordsNum)+ ", "+str(self.interval)+ ", "+str(self.count)+ ", publisheExeIDs.json", "w") as publisherExeID:
            json.dump(self.execodes, publisherExeID)


            
            
    
    
    def createWords(self, num, interval):
        final = ((num-1)*interval)+2
        messages = []
        for wordNum in range(1, final,interval):
            message = "h"
            for eachNum in range(wordNum):
                message += "i"
            messages.append(message)
        return messages            
            
        
        
    def getLatency(self, msg):
        self.callGCF(msg)
        if((self.getLogCounter == self.getLogPeriod) or (self.finalWord == True)):
            self.getLogCounter = 0
            time.sleep(20)
            logs = self.getLogs()

            
        
         
    def callGCF(self, msg):
        for c in range(self.count):
            if self.invoker == "vm":
                res = subprocess.check_output(shlex.split("curl -X POST \"https://northamerica-northeast1-ubc-serverless-ghazal.cloudfunctions.net/publisher\" --data '{\"message\":\"" + (msg)+"\", \"subscriber\":\"" + self.invoker +"\", \"function\":\"" + self.function + "\"}' -H \"Content-Type:application/json\""))
            else:
                res = subprocess.check_output(shlex.split("curl -X POST \"https://northamerica-northeast1-ubc-serverless-ghazal.cloudfunctions.net/publisher\" --data '{\"message\":\"" + (msg)+"\", \"subscriber\":\"" + self.invoker + "\"}' -H \"Content-Type:application/json\""))
            resString = res.decode("utf-8")
            exeId = resString
            print("-----------------"+ str(c)+ "-----------------")
            print("Execution ID: " + exeId)
            self.execodes.append(exeId)
            time.sleep(self.sleepTime)
        print("Message "+ msg+ " with "+ str(getsizeof(msg)) +" bytes is called for " + str(self.count) + " times!")
        
        
        
    def getLogs(self):
        
        project_list_logs = "gcloud functions logs read  --region northamerica-northeast1 --format json --limit 1000"
        project_logs = subprocess.check_output(shlex.split(project_list_logs))
        project_logs_json = json.loads(project_logs)
        (self.allLogs).extend(project_logs_json)
        if (self.finalWord == True):
            self.writeLogs["data"]= self.allLogs
            with open(os.getcwd()+"/data/" + str(self.invoker)+ ", "+str(self.wordsNum)+ ", "+str(self.interval)+ ", "+str(self.count)+ ', data.json', 'a') as outfile:
                json.dump(self.writeLogs, outfile)
        return project_logs_json        