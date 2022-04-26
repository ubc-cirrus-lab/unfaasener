from random import randint
from scipy import rand
from sympy import N
import numpy as np
import math
import logging

class scheduler:

    def __init__(self, windowSize) :
        logging.basicConfig(filename='logs/scheduler.log', level=logging.INFO)
        self.windowSize = windowSize
        self.lastServerlessCV = 100000
        self.lastVMCV = 100000
        self.serverlessObservations = []
        self.vmObservations = []

    def getCV(self, array):
        # if len(array) < self.windowSize:
        #     return 1
        cv = lambda x: np.std(x) / np.mean(x)
        logging.info("std: {}".format(np.std(np.array(array))))
        logging.info("mean: {}".format(np.mean(np.array(array))))
        return cv(array)

    def getConfidence(self):
        if (len(self.serverlessObservations) < self.windowSize or  len(self.vmObservations) < self.windowSize):
            return 0
        newServerlessCV = self.getCV(self.serverlessObservations[-1*self.windowSize:])
        newVMCV= self.getCV(self.vmObservations[-1*self.windowSize:])
        x = abs(newServerlessCV - self.lastServerlessCV) + abs(newVMCV - self.lastVMCV)
        logging.info("x:{}".format(x))
        logging.info("Serverless Last Observations: {},  new CV: {}, old CV: {}".format((self.serverlessObservations[-1*self.windowSize:]), newServerlessCV, self.lastServerlessCV))
        logging.info("VM Last Observations:{}, new CV: {}, old CV: {}".format((self.vmObservations[-1*self.windowSize:]), newVMCV, self.lastVMCV))
        self.lastServerlessCV = newServerlessCV
        self.lastVMCV = newVMCV
        confidence = math.exp(-1*x)
        return confidence*100
    
    def addObservation(self, value, offloaded):
        if offloaded:
            self.vmObservations.append(value)
        else:
            self.serverlessObservations.append(value)

    def offloadingDecision(self, confidenceChar):
        confidence = (ord(confidenceChar)-65)*2
        random = randint(0,100)
        if random <= confidence:
            return 1
        else:
            return 0

    def getMappedValue(self, confidence):
        val = chr(int(confidence/2)+65)
        return val

# (ord(x)-65)*2

if __name__ == "__main__":
    windowSize = 6
    s = scheduler(windowSize)
    for num in range(12):
        val1  = randint(1,100)
        s.addObservation(val1, False)
        val2  = randint(3,800)
        s.addObservation(val2, True)
        confidence = s.getConfidence()
        print("Confidence: {}".format(confidence))
        print("MappedValue:{}".format(s.getMappedValue(confidence)))

    




         
