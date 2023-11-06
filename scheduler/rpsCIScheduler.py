# import rankerConfig
import time
import numpy as np
import sys
import configparser
import os
import pandas as pd
import datetime
from pathlib import Path
from google.cloud import datastore
from rpsMultiHostSolver import rpsOffloadingSolver
from Estimator import Estimator
from getInvocationRate import InvocationRate
import sys

# import psutil, os
import logging

logging.basicConfig(
    filename=str(Path(os.path.dirname(os.path.abspath(__file__))))
    + "/logs/scheduler.log",
    level=logging.INFO,
)


class CIScheduler:
    def __init__(self, triggerType):
        self.dateDFData = {}
        self.dateDFData["effected"] = []
        self.dateDFData["triggerType"] = []
        self.dateDFData["triggered"] = []
        triggerTime = datetime.datetime.now()
        self.dateDFData["triggered"].append(triggerTime)
        print(str(triggerTime) + " Scheduler triggered with: " + triggerType)
        self.dateDFData["triggerType"].append(triggerType)
        path = (
            str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/rankerConfig.ini"
        )
        self.config = configparser.ConfigParser()
        self.config.read(path)
        self.rankerConfig = self.config["settings"]
        self.workflow = self.rankerConfig["workflow"]
        self.solver_prog = self.rankerConfig["solver"]
        self.solver = rpsOffloadingSolver(self.solver_prog)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
            str(Path(os.path.dirname(os.path.abspath(__file__))))
            + "/key/schedulerKey.json"
        )
        self.datastore_client = datastore.Client()
        kind = "routingDecision"
        name = self.workflow
        routing_key = self.datastore_client.key(kind, name)
        self.routing = self.datastore_client.get(key=routing_key)
        self.suggestBestOffloadingMultiVM(triggerType)
        self.dateDFData = pd.DataFrame.from_dict(self.dateDFData)
        self.dateDF = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log-parser/get-workflow-logs/data/"
            + self.workflow
            + "/dateDate.pkl"
        )
        if os.path.isfile(self.dateDF):
            prevDataframeDate = pd.read_pickle(self.dateDF)
            newDataFrame = (
                pd.concat([prevDataframeDate, self.dateDFData])
                .drop_duplicates()
                .reset_index(drop=True)
            )
            newDataFrame.to_pickle(self.dateDF)
            newDataFrame.to_csv(
                (
                    str(
                        Path(os.path.dirname(os.path.abspath(__file__)))
                        .resolve()
                        .parents[0]
                    )
                    + "/log-parser/get-workflow-logs/data/"
                    + self.workflow
                    + "/dateDate.csv"
                )
            )
        else:
            self.dateDFData.to_pickle(self.dateDF)
            self.dateDFData.to_csv(
                (
                    str(
                        Path(os.path.dirname(os.path.abspath(__file__)))
                        .resolve()
                        .parents[0]
                    )
                    + "/log-parser/get-workflow-logs/data/"
                    + self.workflow
                    + "/dateDate.csv"
                )
            )

    def suggestBestOffloadingMultiVM(self, triggerType):
        if triggerType == "highLoad":
            logging.info("High load trigger type!")
            prevPercentage = self.routing["active"]
            match prevPercentage:
                case "25":
                    self.routing["active"] = "50"
                    self.datastore_client.put(self.routing)
                case "50":
                    self.routing["active"] = "75"
                    self.datastore_client.put(self.routing)
                case "75":
                    self.routing["active"] = "95"
                    self.datastore_client.put(self.routing)
                case "95":
                    self.resolveOffloadingSolutions()
                case other:
                    print("Unknown percentile")
        elif triggerType == "lowLoad":
            logging.info("Low load trigger type!")
            prevPercentage = self.routing["active"]
            match prevPercentage:
                case "95":
                    self.routing["active"] = "75"
                    self.datastore_client.put(self.routing)
                case "75":
                    self.routing["active"] = "50"
                    self.datastore_client.put(self.routing)
                case "50":
                    self.routing["active"] = "25"
                    self.datastore_client.put(self.routing)
                case "25":
                    self.resolveOffloadingSolutions()
                case other:
                    print("Unknown percentile")
        elif triggerType == "resolve":
            logging.info("Resolve trigger type!")
            self.resolveOffloadingSolutions()
        else:
            print("Unknown trigger type!")
        self.dateDFData["effected"].append(datetime.datetime.now())
        logging.info("Changed Decision!!!")
        logging.info(str(datetime.datetime.now()))

    def resolveOffloadingSolutions(self):
        x = Estimator(self.workflow)
        invocationRate = InvocationRate(self.workflow)
        # self.rates = invocationRate.getRPS()
        x.getCost()
        x.getPubSubMessageSize()
        mode = self.rankerConfig["mode"]
        alpha = float(self.rankerConfig["statisticalParameter"])
        # self.rps = float(self.rankerConfig["rps"])
        resources = open(
            str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/resources.txt",
            "r",
            os.O_NONBLOCK,
        )
        Lines = resources.readlines()
        cpus = Lines[0].split()
        memories = Lines[1].split()
        availableResources = []
        assert len(cpus) == len(
            memories
        ), "Both number of cores and memory should be provided for each VM"
        for i in range(len(cpus)):
            dict = {}
            dict["cores"] = float(cpus[i])
            dict["mem_mb"] = float(memories[i])
            availableResources.append(dict)
        if mode == "cost":
            decisionModes = ["default"]
        else:
            totalTripleDecisioin = x.tripleCaseDecision(len(cpus))
            if totalTripleDecisioin == True:
                decisionModes = ["default", "worst-case", "best-case"]
                logging.info("latency mode, similar distributions")
            else:
                decisionModes = ["default"]
                logging.info("latency mode, different distributions")

        print("AvailableResources ===", availableResources)
        logging.info("AvailableResources = {}".format(availableResources))
        # self.availableResources = rankerConfig.availResources
        toleranceWindow = int(self.rankerConfig["toleranceWindow"])
        logging.info("Going to resolve!!!")
        logging.info(str(datetime.datetime.now()))
        rates = invocationRate.getRPS()
        decisions = []
        prevDecision = None
        for percent in rates.keys():
            rate = rates[percent]
            for decisionMode in decisionModes:
                self.solver.configure(
                    self.workflow, mode, decisionMode, toleranceWindow, rate, False
                )
                x = self.solver.suggestBestOffloadingMultiVM(
                    availResources=availableResources,
                    alpha=alpha,
                    verbose=True,
                )
                logging.info("Decision for case: {}:{}".format(decisionMode, x))
                logging.info(str(datetime.datetime.now()))
                # print("Decision for case: {}:{}".format(decisionMode, x))
                if (len(decisionModes) != 1) and (x == "NotFound"):
                    logging.info(
                        "Not found solution for case: {}:{}, ignored in triple mode".format(
                            decisionMode, x
                        )
                    )
                elif (len(decisionModes) == 1) and (x == "NotFound"):
                    if prevDecision != None:
                        self.routing["routing" + "_" + str(percent)] = str(prevDecision)
                        logging.info(
                            "Not found solution for case: {}:{}, replaced in single mode to: {}".format(
                                decisionMode, x, prevDecision
                            )
                        )
                    else:
                        logging.info(
                            "Not found solution for case: {}:{}, ignored in single mode".format(
                                decisionMode, x
                            )
                        )
                else:
                    decisions.append(x)
            if len(decisions) == 0:
                continue
            # print("decisions::", decisions)
            AllZeroesFlag = True
            finalDecision = np.mean(decisions, axis=0)
            # print("Average for case:", finalDecision)
            finalDecision = finalDecision / 100
            capArray = [0]*(len(finalDecision))
            for i in range(len(capArray)):
                capArray[i] = np.full(len(finalDecision[i]), 0.9)
                finalDecision[i] = np.multiply(finalDecision[i], capArray[i])
            finalDecision = list(finalDecision)
            for function in range(len(finalDecision)):
                allZero = all(item == 0 for item in list(finalDecision[function]))
                if allZero == False:
                    AllZeroesFlag = False
                    break
            if AllZeroesFlag == True:
                for function in range(len(finalDecision)):
                    if function != 0:
                        vmOffset = np.full(len(finalDecision[function]), 0.05)
                        finalDecision[function] = np.maximum(
                            finalDecision[function], vmOffset
                        )
            for function in range(len(finalDecision)):
                finalDecision[function] = list(finalDecision[function])
            self.routing["routing" + "_" + str(percent)] = str(finalDecision)
            prevDecision = str(finalDecision)
            print(
                "Final Decision: {} for invcation rate: {} ({} percent)".format(
                    list(finalDecision), rate, percent
                )
            )
            logging.info(
                "Final Decision: {} for invcation rate: {} ({} percent)".format(
                    list(finalDecision), rate, percent
                )
            )
            logging.info(str(datetime.datetime.now()))
            decisions = []
        self.routing["active"] = "50"
        self.datastore_client.put(self.routing)


if __name__ == "__main__":
    checkingFlag = False
    start_time = time.time()
    triggerType = sys.argv[1]
    initType = sys.argv[1]
    if initType == "forced":
        triggerType = "resolve"
    # Added by mohamed to allow locking
    if os.path.exists(
        str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/lock.txt"
    ):
        print("LOCK EXISTSSS!!")
        if initType == "forced":
            logging.info(str(datetime.datetime.now()))
            logging.info("Forced trigger!!!")
            if not (
                os.path.exists(
                    str(Path(os.path.dirname(os.path.abspath(__file__))))
                    + "/forcedLock.txt"
                )
            ):
                with open(
                    str(Path(os.path.dirname(os.path.abspath(__file__))))
                    + "/forcedLock.txt",
                    "w",
                ) as f:
                    f.write("forced Lock")
                    f.close
        exit()
    with open(
        str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/lock.txt", "w"
    ) as f:
        f.write("lock")
        f.close
    if os.path.exists(
        str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/forcedLock.txt"
    ):
        triggerType = "resolve"
        checkingFlag = True
        logging.info("Forced to change to resolve!!!")
    pid = os.getpid()
    logging.info(str(pid))
    logging.info("LOCK CREATED!!!")
    logging.info(str(datetime.datetime.now()))
    # triggerType = "resolve"
    try:
        solver = CIScheduler(triggerType)
    except:
        logging.info("Scheduler failed to run!")
        print("ERROR: Scheduler failed to run!")
    os.remove(str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/lock.txt")
    if (
        os.path.exists(
            str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/forcedLock.txt"
        )
    ) and (checkingFlag == True):
        os.remove(
            str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/forcedLock.txt"
        )
    logging.info("Lock released!!!")
    logging.info(str(datetime.datetime.now()))
    # print(
    #     "LOCK removed-> search for lock file:",
    #     os.path.exists(
    #         str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/lock.txt"
    #     ),
    # )
    print("--- %s seconds ---" % (time.time() - start_time))
