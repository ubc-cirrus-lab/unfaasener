#!/bin/bash

g++ -std=c++14 -I .  -I /usr/include/pstreams/ agent.cpp -o monitoringAgent

# # nevigate to scheduler folder to start the api (TODO: need to improve based on leader election feature)
# cd ../../scheduler
# python3 ./scheduler_api.py

# Change to the directory containing the Java code and pom.xml
cd ../../zookeeper

# Set the serverId variable
serverId="1"

# Run the Java program using Maven
mvn exec:java -Dexec.mainClass=com.zk.UpdatePredictionData -Dexec.args="$serverId"

