import os
import pandas as pd
from pathlib import Path
import configparser


configpath = (
    str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
    + "/scheduler/rankerConfig.ini"
)
config = configparser.ConfigParser()
config.read(configpath)
rankerConfig = config["settings"]
workflow = rankerConfig["workflow"]
dfDir = Path(
    str(Path(os.path.dirname(os.path.abspath(__file__))).parents[0])
    + "/log_parser/get_workflow_logs/data/"
    + workflow
    + "/"
)
dfFilesNames = [
    file.name
    for file in dfDir.iterdir()
    if ((file.name.startswith("generatedDataFrame")) and (file.name.endswith(".pkl")))
]

if len(dfFilesNames) != 0:
    dfFilesNames = [a.replace(".pkl", "") for a in dfFilesNames]
    versions = [int((a.split(","))[1]) for a in dfFilesNames]
    lastVersion = max(versions)
    dataframePath = (
        str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
        + "/log_parser/get_workflow_logs/data/"
        + workflow
        + "/generatedDataFrame,"
        + str(lastVersion)
        + ".pkl"
    )
    serverlessDF = pd.read_pickle(dataframePath)

else:
    print("Dataframe not found!")
    serverlessDF = None
vmcachePath = (
    str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
    + "/host-agents/execution-agent/data/cachedVMData.csv"
)
if os.path.isfile(vmcachePath):
    vmData = pd.read_csv(vmcachePath)
else:
    vmData = None
if vmData is not None:
    dataframe = pd.concat([serverlessDF, vmData], ignore_index=True)
else:
    dataframe = serverlessDF
dataframe.to_csv((os.path.dirname(os.path.abspath(__file__))) + "/FinalDF.csv")
