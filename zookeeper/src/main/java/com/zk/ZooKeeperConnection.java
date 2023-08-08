package com.zk;

import java.io.IOException;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

import org.apache.zookeeper.WatchedEvent;
import org.apache.zookeeper.Watcher;
import org.apache.zookeeper.Watcher.Event.KeeperState;
import org.apache.zookeeper.ZooKeeper;
import org.apache.zookeeper.ZooKeeper.States;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ZooKeeperConnection implements Watcher {
    protected static final Logger LOGGER = LoggerFactory.getLogger(ZooKeeperConnection.class);
    private CountDownLatch connectedSignal = new CountDownLatch(1);

    public ZooKeeper zk;
    public static final int RETRY_PERIOD_SECONDS = 2;
    private static final int SESSION_TIMEOUT = 2000000;
    private static final int CONNECT_TIMEOUT = 3000;
    private static String internalHost = "";
    private boolean debug = false;

    /**
     * Constructor.
     *
     * @param debug Debug mode flag.
     */
    public ZooKeeperConnection(boolean debug) {
        this.debug = debug;
    }

    // Method to connect zookeeper ensemble.
    public void connect(String hosts) throws IOException, InterruptedException {
        internalHost = hosts;
        zk = new ZooKeeper(internalHost, SESSION_TIMEOUT, this);

        connectedSignal.await(CONNECT_TIMEOUT, TimeUnit.MILLISECONDS);

        LOGGER.info(">>>>>>>>>>>>>>> Zookeeper: " + hosts + " , connected.");
    }

    @Override
    public void process(WatchedEvent event) {
        if (event.getState() == KeeperState.SyncConnected) {
            LOGGER.info("zk SyncConnected");
            connectedSignal.countDown();
        } else if (event.getState().equals(KeeperState.Disconnected)) {
            LOGGER.warn("zk Disconnected");
        } else if (event.getState().equals(KeeperState.Expired)) {
            if (!debug) {
                LOGGER.error("zk Expired");
                reconnect();
            } else {
                LOGGER.info("zk Expired");
            }
        } else if (event.getState().equals(KeeperState.AuthFailed)) {
            LOGGER.error("zk AuthFailed");
        }
    }

    public synchronized void reconnect() {
        LOGGER.info("start to reconnect....");
        int retries = 0;
        while (true) {
            try {
                if (!zk.getState().equals(States.CLOSED)) {
                    break;
                }
                LOGGER.warn("zookeeper lost connection, reconnect");
                close();
                connect(internalHost);
            } catch (Exception e) {
                LOGGER.error(retries + "\t" + e.toString());
                // sleep then retry
                try {
                    LOGGER.warn("sleep " + RETRY_PERIOD_SECONDS);
                    TimeUnit.SECONDS.sleep(RETRY_PERIOD_SECONDS);
                } catch (InterruptedException e1) {
                }
            }
        }
    }

    public void close() throws InterruptedException {
        zk.close();
    }

    public ZooKeeper getZk() {
        return zk;
    }

    public void setZk(ZooKeeper zk) {
        this.zk = zk;
    }
}