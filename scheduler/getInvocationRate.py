import json
import datetime
from sys import getsizeof
import time
import os
import pandas as pd
import numpy as np
import math
from pathlib import Path
import statistics


class InvocationRate:
    def __init__(self, workflow):
        self.workflow = workflow
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + self.workflow
            + ".json"
        )
        dfDir = Path(str(Path(os.path.dirname(os.path.abspath(__file__))).parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + self.workflow
            + "/")
        invocationFilesNames = [file.name for file in dfDir.iterdir() if ((file.name.startswith('invocationRates')) and (file.name.endswith('.pkl')))]
        # if os.path.isfile(
        #     str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
        #     + "/log_parser/get_workflow_logs/data/"
        #     + self.workflow
        #     + "/invocationRates.pkl"
        # ):
        if len(invocationFilesNames) != 0 :
            invocationFilesNames = [a.replace(".pkl", "") for a in invocationFilesNames]
            versions = [int((a.split(","))[1]) for a in invocationFilesNames]
            lastVersion = max(versions)
            newVersion = lastVersion + 1
            dataframePath = (
                str(
                    Path(os.path.dirname(os.path.abspath(__file__)))
                    .resolve()
                    .parents[0]
                )
                + "/log_parser/get_workflow_logs/data/"
                + self.workflow
                + "/invocationRates,"+str(lastVersion)+".pkl"
            )
            self.dataframe = pd.read_pickle(dataframePath)
        elif os.path.isfile(
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + self.workflow
            + "/invocationRates.csv"
        ):
            dataframePath = (
                str(
                    Path(os.path.dirname(os.path.abspath(__file__)))
                    .resolve()
                    .parents[0]
                )
                + "/log_parser/get_workflow_logs/data/"
                + self.workflow
                + "/invocationRates.csv"
            )
            self.dataframe = pd.read_csv(dataframePath)
        else:
            print("Dataframe not found!")
            self.dataframe = None
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        self.dataframe = self.dataframe.to_frame().reset_index()
        # self.getRPS()

    def getRPS(self):
        self.dataframe["start"] = pd.to_datetime(self.dataframe["start"])
        self.dataframe.sort_values(by=["start"], ascending=True, inplace=True)
        # print(self.dataframe["start"])
        # print(self.dataframe["start"].diff())
        diff = (
            self.dataframe["start"]
            .diff()
            .apply(lambda x: (x / np.timedelta64(1, "ms")))
            .fillna(0)
            .astype("int64")
        )
        diff = np.array(diff)
        diff = diff[1:]
        diff = diff / 1000
        diff = 1 / diff
        # print(diff)
        percentiles = [25, 50, 75, 95]
        results = {}
        results[50] = np.percentile(diff, 50)
        results[25] = min((0.75*results[50]), (np.percentile(diff, 25)))
        results[75] = max((1.25*results[50]), (np.percentile(diff, 75)))
        results[95] = max((1.45*results[50]), (np.percentile(diff, 95)))
        # for percent in percentiles:
        #     results[percent] = np.percentile(diff, percent)
        print("Invocation Rates: ", results)
        return results

        # x = self.dataframe.resample('min', on='start').start.count().array
        # ## countt = np.array(np.unique(x, return_counts=True)).T
        # ## print(countt)
        # x = x[x != 0]
        # countt = np.array(np.unique(x, return_counts=True))
        # print(countt)
        # x = [e/60  for e in x]
        # countt = np.array(np.unique(x, return_counts=True)).T
        # print(countt)
        ## m = np.amax(x)

        # Per95 = np.percentile(x, 96)
        # print(Per95)


if __name__ == "__main__":

    start_time = time.time()
    rps = InvocationRate("Text2SpeechCensoringWorkflow")
    res = rps.getRPS()
    print("--- %s seconds ---" % (time.time() - start_time))
