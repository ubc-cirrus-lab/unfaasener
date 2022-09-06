#!/bin/bash

pip3 install -r ./requirements.txt

sudo apt install -y docker.io
sudo apt install -y libcurl*
sudo  usermod -a -G docker  $USER
