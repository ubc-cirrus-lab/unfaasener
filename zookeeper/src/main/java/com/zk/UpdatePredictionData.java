package com.zk;

import org.apache.zookeeper.*;
import org.apache.log4j.Level;
import org.apache.log4j.Logger;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Properties;

public class UpdatePredictionData {
    public static final String PREDICTION_PATH = "/pred";
    public static final String CPU_PATH = "/cpu";
    public static final String MEMORY_PATH = "/mem";

    public static ZooKeeper zk;
    public static ZooKeeperConnection conn;

    private static String getZookeeperHosts() {
        Properties props = new Properties();
        try {
            ClassLoader loader = Thread.currentThread().getContextClassLoader();
            InputStream stream = loader.getResourceAsStream("hostip.properties");
            props.load(stream);
        } catch (IOException e) {
             
        }
        return props.getProperty("zookeeper.hosts");
    }

    private static void createOrUpdateNode(ZooKeeper zk, String path, String data) {
        long startTime = System.currentTimeMillis(); // Record start time

        try {
            if (zk.exists(path, false) == null) {
                // Node doesn't exist, create it first
                zk.create(path, data.getBytes(StandardCharsets.UTF_8), ZooDefs.Ids.OPEN_ACL_UNSAFE,
                        CreateMode.PERSISTENT);
                System.out.println("---------- Created znode " + path + " ---------- ");
            } else {
                // Node exists, update its data
                zk.setData(path, data.getBytes(StandardCharsets.UTF_8), -1);
                System.out.println("---------- Updated " + path + " with data: " + data + " ----------");
            }

            long endTime = System.currentTimeMillis(); // Record end time
            System.out.println(
                    ">>>>>>>>>>>>>>>>> Time taken for updating data on " + path + ": " + (endTime - startTime) + "ms");

        } catch (KeeperException | InterruptedException e) {
             
        }
    }

    private static void updateFromPropertiesFile(ZooKeeper zk, int serverID) {
        try {
            Properties prop = new Properties();
            ClassLoader loader = Thread.currentThread().getContextClassLoader();
            InputStream stream = loader.getResourceAsStream("prediction.properties");
            prop.load(stream);

            String cpuPrediction = prop.getProperty("cpu");
            String memoryPrediction = prop.getProperty("mem");

            if (cpuPrediction == null || memoryPrediction == null) {
                System.err.println(">>>> Missing prediction values in properties file.");
                return;
            }

            String cpuPath = getServerPath(serverID, CPU_PATH);
            String memoryPath = getServerPath(serverID, MEMORY_PATH);

            createOrUpdateNode(zk, cpuPath, cpuPrediction);
            createOrUpdateNode(zk, memoryPath, memoryPrediction);

        } catch (IOException e) {
             
        }
    }

    private static String getServerPath(int serverID, String path) {
        return PREDICTION_PATH + "/server_" + serverID + path;
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java UpdatePredictionData <serverID>");
            return;
        }

        // Set ZooKeeper logger level to INFO
        Logger zkLogger = Logger.getLogger("org.apache.zookeeper");
        zkLogger.setLevel(Level.INFO);

        int serverID = Integer.parseInt(args[0]);

        String hostPort = getZookeeperHosts(); // Read ZooKeeper hosts from hostip.properties

        try {
            conn = new ZooKeeperConnection(true);
            conn.connect(hostPort);
            zk = conn.getZk();

            if (zk != null) {
                System.out.println("---------- Successfully connected to ZooKeeper ----------");

                String serverPath = PREDICTION_PATH + "/server_" + serverID;
                createOrUpdateNode(zk, PREDICTION_PATH, "");
                createOrUpdateNode(zk, serverPath, "");

                while (true) {
                    updateFromPropertiesFile(zk, serverID);
                    Thread.sleep(100); // Sleep for 0.1 second before updating again
                }
            } else {
                System.err.println("---------- Error connecting to ZooKeeper server ----------");
            }
        } catch (Exception e) {
             
        }
    }
}
