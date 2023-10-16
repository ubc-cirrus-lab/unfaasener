# !/bin/bash

leaderFailure=0
if command -v julia &> /dev/null
then
    julia setupJulia.jl
else
    echo "Error: Julia is not installed on your system."
    echo "Do you want to install Julia? (y/n)"
    read installJulia
    if [ $installJulia == "y" ]
    then
        if [ "$(uname)" == "Linux" ] && [ "$(uname -m)" == "x86_64" ]
        then
            echo "Downloading Julia..."
            wget https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-1.9.3-linux-x86_64.tar.gz
            echo "Extracting Julia..."
            tar -xvzf julia-1.9.3-linux-x86_64.tar.gz
            echo "Installing Julia..."
            sudo cp -r julia-1.9.3 /opt/
            sudo ln -s /opt/julia-1.9.3/bin/julia /usr/local/bin/julia
            echo "Julia has been installed."
        elif [ "$(uname)" == "Linux" ] && [ "$(uname -m)" == "aarch64" ]
        then
            echo "Downloading Julia..."
            wget https://julialang-s3.julialang.org/bin/linux/aarch64/1.9/julia-1.9.3-linux-aarch64.tar.gz
            echo "Extracting Julia..."
            tar -xvzf julia-1.9.3-linux-aarch64.tar.gz
            echo "Installing Julia..."
            sudo cp -r julia-1.9.3 /opt/
            sudo ln -s /opt/julia-1.9.3/bin/julia /usr/local/bin/julia
            echo "Julia has been installed."
        else
            echo "Please download Julia from https://julialang.org/downloads/, install it, and then re-run this script."
            exit 1
        fi
        julia setupJulia.jl
    else
        echo "Please install Julia and re-run this script."
        exit 1
    fi
fi

if command -v pip &> /dev/null
then
    echo "pip is installed"
else
    echo "pip is not installed"
    echo "Do you want to install pip? (y/n)"
    read installPip
    if [ $installPip == "y" ]
    then
        sudo apt install -y python3-pip
    else
        echo "Please install pip and re-run this script."
        exit 1
    fi
fi
python3 -m pip install -r requirements.txt
sudo apt install -y docker.io
sudo apt-get install -y libpstreams-dev
sudo apt-get install build-essential
sudo  usermod -a -G docker  $USER
arr=("DNAVisualizationWorkflow" "ImageProcessingWorkflow" "RegressionTuningWorkflow" "Text2SpeechCensoringWorkflow" "VideoAnalyticsWorkflow")
cd ./scheduler/data
for dirname in "${arr[@]}"
do
    if [ -d "$dirname" ]
    then
        echo "Directory $dirname exists."
    else
        mkdir "$dirname"
    fi
done 
cd ../
if [ -d "logs" ]
then
    echo "Directory logs exists for the scheduler."
else
    mkdir logs
fi
cd ../
cd ./log-parser/get-workflow-logs/data
for dirname in "${arr[@]}"
do
    if [ -d "$dirname" ]
    then
        echo "Directory $dirname exists."
    else
        mkdir "$dirname"
    fi
done 
cd ../
if [ -d "logs" ]
then
    echo "Directory logs exists for the log collector."
else
    mkdir logs
fi
cd ../../
cd ./host-agents/execution-agent
if [ -d "logs" ]
then
    echo "Directory logs exists for the host agents."
else
    mkdir logs
fi
if [ -d "data" ]
then
    echo "Directory data exists for the host agents."
else
    mkdir data
fi
cd ../../
if [ $leaderFailure -eq 1 ]
then
    cd ./log-parser/get-workflow-logs
    if command -v python &> /dev/null
    then
        python getNewDatastoreLogs.py
    elif command -v python3 &> /dev/null
    then
        python3 getNewDatastoreLogs.py
    fi
fi
echo "Please exit your current session and relogin"
