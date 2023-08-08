#!/bin/bash
cd zookeeper
mvn clean
mvn package

cd ../host-agents/monitoring-agent
./compile.sh