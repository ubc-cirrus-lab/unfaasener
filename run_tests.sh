#!/bin/bash

# solver tests
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
cd ../

# host agent tests
cp ./tests/host_agents/predictor_test.cpp vm-agent/monitoring-agent/
cd vm-agent/monitoring-agent
g++ -std=c++14 -I . predictor_test.cpp -o predictor_test
./predictor_test
rm ./predictor_test*
