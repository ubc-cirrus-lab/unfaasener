# ZooKeeper Environment Setup

## Overview

This guide outlines the process of setting up a ZooKeeper cluster environment. The current focus of ZooKeeper development involves enhancing the monitoring capabilities by allowing the monitoring agent to upload predicted CPU and memory data to the ZooKeeper Command Line Interface (CLI) instead of storing it locally. This facilitates data retrieval by the leader host for making informed offloading decisions.

## Purpose
This guide provides step-by-step instructions for configuring a ZooKeeper cluster in a replicated mode across multiple servers. For production scenarios, it is recommended to deploy ZooKeeper in a multi-host environment with a minimum of 3 servers. The included `configure.sh` script facilitates the setup of 3 servers on the local host. This script can be customized to incorporate the IP addresses of offloading hosts as required.

** Note: After the implementation of the leader election feature, adjustments to the `configure.sh` script may be necessary. **

## Step 1: Install and Configure ZooKeeper

Make the `configure.sh` script executable and run it to install and configure ZooKeeper:

    ```bash
    chmod +x configure.sh
    ./configure.sh
    ```

## Step 2: Build the Maven Project

### You have two options for building the Maven project:
1. Manual build:
   a. Open a terminal and navigate to the root of the ZooKeeper project folder:

    ```bash
    cd zookeeper
    ```
    b. Build the Maven project to compile the Java code:

    ```bash
    mvn clean
    mvn package
    ```

2. Automated build:
   Execute the `./build.sh` script in the root folder to setup the zookeeper and monitoring agent.


## Step 3: Running zookeeper and monitoring agent together

1. Navigate to the host-agents/monitoring-agent folder

    ```bash
    cd host-agents/monitoring-agent/
    ```

2. Compile the script and start the zookeeper connection

    ```bash
    ./compile.sh
    ```
    You will probably see the console printing results of zookeeper constantly updating the data.

3. Open a new terminal, run the monitoring agent

    ```bash
    ./monitoringAgent
    ```

## Step 3: Stop the ZooKeeper Cluster (Optional)

1. If you want to stop the ZooKeeper cluster, use the following commands:

    ```bash
    /usr/local/zookeeper-cluster/zookeeper-1/bin/zkServer.sh stop
    /usr/local/zookeeper-cluster/zookeeper-2/bin/zkServer.sh stop
    /usr/local/zookeeper-cluster/zookeeper-3/bin/zkServer.sh stop
    ```

Reference to: https://zookeeper.apache.org/doc/r3.6.2/zookeeperProgrammers.html 
