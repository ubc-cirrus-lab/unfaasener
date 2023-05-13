# UnFaaSener
[![Build Status](https://github.com/ubc-cirrus-lab/unfaasener/actions/workflows/python-app.yml/badge.svg)](https://github.com/ubc-cirrus-lab/unfaasener/actions/workflows/python-app.yml) [![GitHub license](https://img.shields.io/badge/license-Apache%202-blue.svg)](https://github.com/ubc-cirrus-lab/unfaasener/blob/main/LICENSE)


Seamless Integration of Serverless and VM-based Cloud Applications for Increased Cost Efficiency

## Setting Up and Building the Tool

To set up the dependencies for the tool, we can then simply run the following script:
> **_NOTE:_**  In case of leader failure, the leaderFailure variable in the setup.sh needs to be set to 1 (```leaderFailure=1```) in order to retrieve host logs from the datastore.
```
./setup.sh 
```
Then, run the following script to build those components that need to be compiled:
```
./build.sh
```

## Acknowledgments

This work was supported in part by the Natural Sciences and Engineering Research Council of Canada (NSERC).
We are also thankful for cloud resources made available to us by the Digital Research Alliance of Canada, the Google Cloud Research Credits program, and the AWS Cloud Credit for Research program.
