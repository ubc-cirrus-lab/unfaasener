#!/bin/bash

pip3 install -r ./requirements.txt

sudo apt install -y docker.io
sudo apt-get install -y libpstreams-dev
sudo apt-get install build-essential
sudo  usermod -a -G docker  $USER
arr=("ChatBotWorkflow" "DNAVisualizationWorkflow" "ImageProcessingWorkflow" "RegressionTuningWorkflow" "Text2SpeechCensoringWorkflow" "VideoAnalyticsWorkflow")
cd ./scheduler/data
for dirname in "${arr[@]}"
do
    mkdir "$dirname"
done 
cd ../../
cd ./log_parser/get_workflow_logs/data
for dirname in "${arr[@]}"
do
    mkdir "$dirname"
done 
echo "Please exit your current session and relogin"
