!/bin/bash

pip3 install -r ./requirements.txt

sudo apt install -y docker.io
sudo apt install -y libcurl*
sudo apt-get install -y libpstreams-dev
sudo  usermod -a -G docker  $USER
arr=("ChatBotWorkflow" "DNAVisualizationWorkflow" "ImageProcessingWorkflow" "RegressionTuningWorkflow" "Text2SpeechCensoringWorkflow" "VideoAnalyticsWorkflow")
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
if [ $1 -eq 1 ]
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
