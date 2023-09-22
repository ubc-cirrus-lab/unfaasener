#!/bin/bash

workflow="$1"
hostcount="$2"
solvingMode="$3"
mode="resolve"

# please run this script from the home directory of the unfaasener project

# making sure that by default are functions run on serverless
# python3 scheduler/resetRoutingDecisions.py $workflow $hostcount
docker container stop $(docker container ls -aq)
# clean all privious metadata, logs, and caches for that workflow
python3 scheduler/resetLastDecisions.py $workflow $hostcount $solvingMode

# initialize Julia Solver
mkfifo ./scheduler/juliaStdin
mkfifo ./scheduler/juliaStdout
julia scheduler/rpsMultiVMSolver.jl &

# clean the host execution agent queue
python3 host-agents/execution-agent/cleanup-queue.py vmSubscriber1 vm0

# get the most recent serverless logs for the specified workflow
python3 log-parser/get-workflow-logs/getWorkflowLogs.py $workflow 1 

# running the monitoring scripts and the predictor agent in the background
cd host-agents/monitoring-agent
./monitoringAgent &
pidFour=$!
sleep 10

# running the vm execution agent in the background
cd ../execution-agent
python3 vmModule.py vmSubscriber1 vm0 &
pidOne=$!

# periodically (every 10m) collecting the execution logs of the workflow in the background
cd ../..
python3 log-parser/get-workflow-logs/getWorkflowLogs.py $workflow 0 &
pidTwo=$!

# periodically performing garbage collection (every 1h) on the datastore(unused merging points data) and the dataframe
python3 scheduler/garbageCollector.py &
pidThree=$!



# terminating background processes upon termination of this script
trap "kill ${pidOne} ${pidTwo} ${pidThree} ${pidFour}; echo -n \"END\" > scheduler/juliaStdin; python3 log-parser/get-workflow-logs/getWorkflowLogs.py ${workflow} 1; python3 setup-tests/combineDataframes.py; exit 1" INT SIGINT SIGTERM EXIT
wait



