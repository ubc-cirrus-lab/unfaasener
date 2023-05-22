# UnFaaSener
[![Build Status](https://github.com/ubc-cirrus-lab/unfaasener/actions/workflows/python-app.yml/badge.svg)](https://github.com/ubc-cirrus-lab/unfaasener/actions/workflows/python-app.yml) [![GitHub license](https://img.shields.io/badge/license-Apache%202-blue.svg)](https://github.com/ubc-cirrus-lab/unfaasener/blob/main/LICENSE)

Are you currently using serverless offerings in conjunction with pre-paid VMs? 
Or do you have on-premise computational capacity that already incurs capital and operating costs? 
If so, why not leverage those resources to reduce your serverless bills?

UnFaaSener is a lightweight framework designed to empower serverless developers to decrease their expenses by harnessing non-serverless compute resources.
Whether it's your VMs, on-premise servers, or personal computers, UnFaaSener allows you to make the most of these underutilized resources.

UnFaaSener is not a new serverless platform, nor does it require any support from today's production serverless platforms.
It seamlessly integrates with existing pub/sub services to glue your serverless applications and offloading hosts.

UnFaaSener has been thoroughly tested and evaluated on [Google Cloud Functions](https://cloud.google.com/functions).
Our [research paper](https://www.usenix.org/conference/atc23/presentation/sadeghian) on it will appear at the 2023 USENIX Annual Technical Conference ([ATC '23](https://www.usenix.org/conference/atc23)).

## Setting Up and Building the Tool

To set up the dependencies for the tool simply run the following script:
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
