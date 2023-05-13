# !/bin/bash

leaderFailure=0
pip3 install -r ./requirements.txt

sudo apt install -y docker.io
sudo apt-get install -y libpstreams-dev
sudo apt-get install build-essential
sudo  usermod -a -G docker  $USER
arr=("DNAVisualizationWorkflow" "ImageProcessingWorkflow" "RegressionTuningWorkflow" "Text2SpeechCensoringWorkflow" "VideoAnalyticsWorkflow")
cd ./scheduler/data
for dirname in "${arr[@]}"
do
    mkdir "$dirname"
done 
cd ../
mkdir logs
cd ../
cd ./log_parser/get_workflow_logs/data
for dirname in "${arr[@]}"
do
    mkdir "$dirname"
done 
cd ../
mkdir logs
cd ../../
cd ./vm-agent/execution-agent
mkdir logs
mkdir data
cd ../../
if [ $leaderFailure -eq 1 ]
then
cd ./log_parser/get_workflow_logs
if command -v python &> /dev/null
then
    python getNewDatastoreLogs.py
elif command -v python3 &> /dev/null
then
    python3 getNewDatastoreLogs.py
fi 
fi
echo "Please exit your current session and relogin"
