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
        if os.path.isfile(
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + self.workflow
            + "/invocationRates.pkl"
        ):
            dataframePath = (
                str(
                    Path(os.path.dirname(os.path.abspath(__file__)))
                    .resolve()
                    .parents[0]
                )
                + "/log_parser/get_workflow_logs/data/"
                + self.workflow
                + "/invocationRates.pkl"
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
        for percent in percentiles:
            results[percent] = np.percentile(diff, percent)
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
