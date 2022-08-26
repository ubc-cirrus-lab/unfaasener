#!/bin/bash
workflow="$1"
numvm="$2"
solvingMode="$3"
mode="resolve"

# making sure that by default are functions run on serverless
# python3 ~/de-serverlessization/scheduler/resetRoutingDecisions.py $workflow $numvm

# clean all privious metadata, logs, and caches for that workflow
python3 ~/de-serverlessization/scheduler/resetLastDecisions.py $workflow $numvm $solvingMode

# get the most recent serverless logs for the specified workflow
python3 ~/de-serverlessization/log_parser/get_workflow_logs/getWorkflowLogs.py $workflow 1 

# running the scheduler
python3 ~/de-serverlessization/scheduler/rpsCIScheduler.py $mode 

# running the vm execution agent in the background
python3 ~/de-serverlessization/vm-agent/execution-agent/vmModule.py &
pidOne=$!

# periodically (every 10m) collecting the execution logs of the workflow in the background
python3 ~/de-serverlessization/log_parser/get_workflow_logs/getWorkflowLogs.py $workflow 0 &
pidTwo=$!

# periodically performing garbage collection (every 1h) on the datastore(unused merging points data) and the dataframe
python3 ~/de-serverlessization/scheduler/garbageCollector.py &
pidThree=$!

# running the monitoring scripts and the predictor agent in the background
cd ~/de-serverlessization/vm-agent/monitoring-agent
./monitoring-agent &
pidFour=$!

# terminating background processes upon termination of this script
trap "kill ${pidOne} ${pidTwo} ${pidThree} ${pidFour}; exit 1" INT SIGINT SIGTERM EXIT
wait



