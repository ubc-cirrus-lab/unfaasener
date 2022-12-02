#!/bin/bash

# solver tests
# get data
cp -a ./tests/solver/data/. ./scheduler/data/
cp -a ./tests/logCollector/. ./log_parser/get_workflow_logs/data/
cp ./tests/solver/rps_cost_test.py ./scheduler
cp ./tests/solver/rps_latency_test.py ./scheduler
cd ./scheduler
if command -v python &> /dev/null
then
    python rps_cost_test.py
    python rps_latency_test.py 
elif command -v python3 &> /dev/null
then
    python3 rps_cost_test.py
    python3 rps_latency_test.py 
fi
rm rps_cost_test.py
rm rps_latency_test.py
cd ./data
arr=("TestCase10Workflow" "TestCase11Workflow" "TestCase2Workflow" "TestCase3Workflow" "TestCase4Workflow" "TestCaseWorkflow")
for item in "${arr[@]}"
do
    rm -rf "$item"
done
cd ../../
cd ./log_parser/get_workflow_logs/data
for item in "${arr[@]}"
do
    rm -rf "$item"
done
cd ../../../
# host agent tests
cp ./tests/host_agents/predictor_test.cpp vm-agent/monitoring-agent/
cd vm-agent/monitoring-agent
g++ -std=c++14 -I . predictor_test.cpp -o predictor_test
./predictor_test
rm ./predictor_test*
