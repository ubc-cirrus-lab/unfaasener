#!/bin/bash
# Step 0: Install and consigure Zookeeper
cd /usr/local
sudo chown $USER:$USER -R /usr/local
sudo wget https://archive.apache.org/dist/zookeeper/zookeeper-3.8.1/apache-zookeeper-3.8.1-bin.tar.gz
sudo tar -xvf apache-zookeeper-3.8.1-bin.tar.gz
sudo chown $USER:$USER -R apache-zookeeper-3.8.1-bin
# sudo ln -s apache-zookeeper-3.8.1-bin zookeeper
# sudo chown -h $USER:$USER zookeeper

# Create the Zookeeper cluster directory
mkdir /usr/local/zookeeper-cluster

# Copy Zookeeper to each node directory
ZOOKEEPER_VERSION="apache-zookeeper-3.8.1-bin"
cp -r "$ZOOKEEPER_VERSION" /usr/local/zookeeper-cluster/zookeeper-1
cp -r "$ZOOKEEPER_VERSION" /usr/local/zookeeper-cluster/zookeeper-2
cp -r "$ZOOKEEPER_VERSION" /usr/local/zookeeper-cluster/zookeeper-3

# Create data directories and rename config files
sudo mkdir -p /data/zookeeper-cluster/zookeeper-1
sudo mkdir -p /data/zookeeper-cluster/zookeeper-2
sudo mkdir -p /data/zookeeper-cluster/zookeeper-3

mv "/usr/local/zookeeper-cluster/zookeeper-1/conf/zoo_sample.cfg" "/usr/local/zookeeper-cluster/zookeeper-1/conf/zoo.cfg"
mv "/usr/local/zookeeper-cluster/zookeeper-2/conf/zoo_sample.cfg" "/usr/local/zookeeper-cluster/zookeeper-2/conf/zoo.cfg"
mv "/usr/local/zookeeper-cluster/zookeeper-3/conf/zoo_sample.cfg" "/usr/local/zookeeper-cluster/zookeeper-3/conf/zoo.cfg"

# Configure each Zookeeper node with dataDir and clientPort
ZOOKEEPER_NODES=("zookeeper-1" "zookeeper-2" "zookeeper-3")
ZOOKEEPER_PORTS=("2181" "2182" "2183")
for i in "${!ZOOKEEPER_NODES[@]}"; do
  NODE_DIR="/usr/local/zookeeper-cluster/${ZOOKEEPER_NODES[$i]}"
  CLIENT_PORT="${ZOOKEEPER_PORTS[$i]}"
  sudo sed -i "s/^clientPort=.*/clientPort=$CLIENT_PORT/" "$NODE_DIR/conf/zoo.cfg"
  sudo sed -i "s|^dataDir=.*|dataDir=/data/zookeeper-cluster/${ZOOKEEPER_NODES[$i]}|" "$NODE_DIR/conf/zoo.cfg"
done

# Configure cluster servers in zoo.cfg
echo "server.1=localHost:2881:3881" >> /usr/local/zookeeper-cluster/zookeeper-1/conf/zoo.cfg
echo "server.2=localHost:2882:3882" >> /usr/local/zookeeper-cluster/zookeeper-1/conf/zoo.cfg
echo "server.3=localHost:2883:3883" >> /usr/local/zookeeper-cluster/zookeeper-1/conf/zoo.cfg
echo "server.1=localHost:2881:3881" >> /usr/local/zookeeper-cluster/zookeeper-2/conf/zoo.cfg
echo "server.2=localHost:2882:3882" >> /usr/local/zookeeper-cluster/zookeeper-2/conf/zoo.cfg
echo "server.3=localHost:2883:3883" >> /usr/local/zookeeper-cluster/zookeeper-2/conf/zoo.cfg
echo "server.1=localHost:2881:3881" >> /usr/local/zookeeper-cluster/zookeeper-3/conf/zoo.cfg
echo "server.2=localHost:2882:3882" >> /usr/local/zookeeper-cluster/zookeeper-3/conf/zoo.cfg
echo "server.3=localHost:2883:3883" >> /usr/local/zookeeper-cluster/zookeeper-3/conf/zoo.cfg

# Create myid files with the server IDs
echo "1" >> /data/zookeeper-cluster/zookeeper-1/myid
echo "2" >> /data/zookeeper-cluster/zookeeper-2/myid
echo "3" >> /data/zookeeper-cluster/zookeeper-3/myid

# Start the Zookeeper cluster
/usr/local/zookeeper-cluster/zookeeper-1/bin/zkServer.sh --config /usr/local/zookeeper-cluster/zookeeper-1/conf start
/usr/local/zookeeper-cluster/zookeeper-2/bin/zkServer.sh --config /usr/local/zookeeper-cluster/zookeeper-2/conf start
/usr/local/zookeeper-cluster/zookeeper-3/bin/zkServer.sh --config /usr/local/zookeeper-cluster/zookeeper-3/conf start

# Check the status of each instance
/usr/local/zookeeper-cluster/zookeeper-1/bin/zkServer.sh status
/usr/local/zookeeper-cluster/zookeeper-2/bin/zkServer.sh status
/usr/local/zookeeper-cluster/zookeeper-3/bin/zkServer.sh status

# Connect to Zookeeper CLI
/usr/local/zookeeper-cluster/zookeeper-3/bin/zkCli.sh -server localhost:2181,localhost:2182,localhost:2183

# /usr/local/zookeeper-cluster/zookeeper-1/bin/zkServer.sh stop
# /usr/local/zookeeper-cluster/zookeeper-2/bin/zkServer.sh stop
# /usr/local/zookeeper-cluster/zookeeper-3/bin/zkServer.sh stop