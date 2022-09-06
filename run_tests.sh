#!/bin/bash

cp ./tests/rps_cost_test.py ./scheduler
cp ./tests/rps_latency_test.py ./scheduler
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