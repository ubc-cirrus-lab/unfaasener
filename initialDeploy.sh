#!/bin/bash
workflow="$1"
hostcount="$2"
solvingMode="$3"
mode="resolve"

# making sure that by default are functions run on serverless
# python3 ~/de-serverlessization/scheduler/resetRoutingDecisions.py $workflow $hostcount
docker container stop $(docker container ls -aq)
# clean all privious metadata, logs, and caches for that workflow
python3 ~/de-serverlessization/scheduler/resetLastDecisions.py $workflow $hostcount $solvingMode

# clean the host execution agent queue
python3 ~/de-serverlessization/host-agents/execution-agent/cleanup-queue.py vmSubscriber1 vm0

# get the most recent serverless logs for the specified workflow
python3 ~/de-serverlessization/log-parser/get_workflow_logs/getWorkflowLogs.py $workflow 1 

# running the scheduler
# python3 ~/de-serverlessization/scheduler/rpsCIScheduler.py $mode 

# running the monitoring scripts and the predictor agent in the background
cd ~/de-serverlessization/host-agents/monitoring-agent
./monitoringAgent &
pidFour=$!
sleep 10
# running the vm execution agent in the background
python3 ~/de-serverlessization/host-agents/execution-agent/vmModule.py vmSubscriber1 vm0 &
pidOne=$!

# periodically (every 10m) collecting the execution logs of the workflow in the background
python3 ~/de-serverlessization/log-parser/get_workflow_logs/getWorkflowLogs.py $workflow 0 &
pidTwo=$!

# periodically performing garbage collection (every 1h) on the datastore(unused merging points data) and the dataframe
python3 ~/de-serverlessization/scheduler/garbageCollector.py &
pidThree=$!



# terminating background processes upon termination of this script
trap "kill ${pidOne} ${pidTwo} ${pidThree} ${pidFour}; python3 ~/de-serverlessization/log-parser/get_workflow_logs/getWorkflowLogs.py ${workflow} 1; python3 ~/de-serverlessization/setup-tests/combineDataframes.py; exit 1" INT SIGINT SIGTERM EXIT
wait



