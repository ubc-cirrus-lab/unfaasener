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
## Deploying the system
To deploy the system, follow these steps:
1. **Giving the required credentials:** To create the necassary credentials for using UnFaaSener, follow the instructions [here](./scheduler/key/).
2. **Adding a new host:**  In order to incorporate a new host into UnFaaSener, you must assign a new pubsub topic to the host and ensure that the host subscribes to this topic. To achieve this within Google Cloud Functions, please follow the steps outlined below:
    1. **Create a Pub/Sub Topic:** 
        * Access the Pub/Sub service page on the Google Cloud Console.
        * Navigate to the "Topics" section and click on "CREATE TOPIC". This topic will serve as the communication channel for the host.
        * The host topics follow the naming pattern `vmTopic+n`, where `n` represents the host number. For example, if you want to add the third host, name the topic as `vmTopic3`.

    2. **Configure Subscription:**
        * To enable the host to receive messages published to the topic, create a subscription for the topic.
        * Go to the "Subscriptions" section and click on "CREATE SUBSCRIPTION".
        * Provide a unique subscription ID that will be used by the host execution agent.
        * Select "never expire" for the expiration period if you want the host to be available indefinitely.
            <img src="./scheduler/key/Images/expire.png" alt="expireSubsciption"/>
        * For providing a level of fault tolerance, enable dead lettering while creating the subscription. You need to choose the dead-letter topic for your host subscription, which is assigned to another host. By default, we assign the topic of (host_i + 1)%numhosts as the dead-letter topic for host_i.
            <img src="./scheduler/key/Images/deadLetter.png" alt="deadLetterTopic"/>
1. **Deploymet script:**
    * To ensure that all functions initially run as serverless fuctions by default, run [this](./scheduler/resetRoutingDecisions.py) script before sending the traffic. This script ensures that the routing decisions are reset.
        ```
        python3 ./scheduler/resetRoutingDecisions.py [benchmark name] [number of offloading hosts]
        ``` 
    * Start the system using the [deployment script](./initialDeploy.sh). 
    This script launches the system, prepares the initial state, and starts the host agents.
    You can simply run the following script with the following arguments:
        ```
        ./initialDeploy.sh [benchmark name] [number of offloading hosts] [optimization mode (latency/cost)]
        ``` 
## Acknowledgments

This work was supported in part by the Natural Sciences and Engineering Research Council of Canada (NSERC).
We are also thankful for cloud resources made available to us by the Digital Research Alliance of Canada, the Google Cloud Research Credits program, and the AWS Cloud Credit for Research program.
