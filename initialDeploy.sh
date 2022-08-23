#!/bin/bash
# trap "exit" INT TERM ERR
# trap "pkill python" EXIT
# trap 'kill $(jobs -p)' EXIT
workflow="$1"
numvm="$2"
solvingMode="$3"
mode="resolve"
# date
python3 ~/de-serverlessization/scheduler/resetRoutingDecisions.py $workflow $numvm
python3 ~/de-serverlessization/scheduler/resetLastDecisions.py $workflow $numvm $solvingMode
python3 ~/de-serverlessization/log_parser/get_workflow_logs/getWorkflowLogs.py $workflow 1 
# date
python3 ~/de-serverlessization/scheduler/rpsCIScheduler.py $mode 
python3 ~/de-serverlessization/vm-agent/execution-agent/vmModule.py &
pidOne=$!
python3 ~/de-serverlessization/log_parser/get_workflow_logs/getWorkflowLogs.py $workflow 0 &
pidTwo=$!
python3 ~/de-serverlessization/scheduler/garbageCollector.py &
pidThree=$!
cd ~/de-serverlessization/vm-agent/monitoring-agent
./monitoring-agent &
pidFour=$!
trap "kill ${pidOne} ${pidTwo} ${pidThree} ${pidFour}; exit 1" INT SIGINT SIGTERM EXIT
wait





# for i in {1 .. 50}
# do
#         curl -X POST "https://northamerica-northeast1-ubc-serverless-ghazal.cloudfunctions.net/${headerFunction}" --data {"message":"${input}"} -H "Content-Type:application/json"
#         sleep 1
# done