# de-serverlessization
[![Build Status](https://github.com/ubc-cirrus-lab/de-serverlessization/actions/workflows/python-app.yml/badge.svg)](https://github.com/ubc-cirrus-lab/de-serverlessization/actions/workflows/python-app.yml)

Seamless Integration of Serverless and VM-based Cloud Applications for Increased Cost Efficiency

## Setting Up and Building the Tool

To set up the dependencies for the tool simply run the following script. The input would be 1 in case of leader failure in order to retrieve host logs from the datastore, and 0 otherwise.
```
./setup.sh 1: In case of leader failure
./setup.sh 0: Otherwise
```
Then, run the following script to build those components that need to be compiled:
```
./build.sh
```

## Acknowledgments

This work was supported in part by the Natural Sciences and Engineering Research Council of Canada (NSERC).
We are also thankful for cloud resources made available to us by the Digital Research Alliance of Canada, the Google Cloud Research Credits program, and the AWS Cloud Credit for Research program.
