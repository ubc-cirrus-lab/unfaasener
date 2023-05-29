# How to get a private key for having access to google cloud services?

### 1. Go to the Service Account's section of IAM & Admin in the google cloud console. 

  <img src="./Images/ServiceAccount.png" alt="Service Account Section"/>

---

### 2. Click on create a service account.

  <img src="./Images/CreateServiceAccount.png" alt="Creating a service account"/>

---

### 3. Choose a name, and required roles for this service account.
Three following keys are used in this project: 

  * **Monitoring key:** To monitor the history of Pub/Sub message sizes, select the Monitoring Admin and Monitoring Viewer roles for the service account associated with the `monitoringKey.json` key located in the current directory.

    <img src="./Images/Roles.png" alt="Roles"/>

  * **Scheduler key:** To store the decisions to the Datastore, select the Cloud Datastore Owner role for the service account associated with the `schedulerKey.json` key located in the current directory.

    <img src="./Images/rolesScheduler.png" alt="Roles"/>

  * **Host agent key:** To enable the periodic storage of host logs to the Datastore, as well as the download of Google Cloud Functions and execution of incoming requests, select the Cloud Datastore Owner, Cloud Functions Admin, Pub/Sub Publisher, and Pub/Sub Subscriber roles for the service account associated with the `vmExeModule.json` key. This key is located in this [directory](../../host-agents/execution-agent/).
  

    <img src="./Images/rolesHostAgent.png" alt="Roles"/>

---

### 4. For each service account, when the service account is created, click on the keys section, and add a new key for this service account.

  <img src="./Images/AddKey.png" alt="Adding a key"/>

---


### 5. Download the key file and place it in the appropriate directory along with the names previously mentioned in step 3.
<!-- ```
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = THE-PATH-TO-YOUR-KEY 
``` -->

The pattern for each key will appear as follows:

```
{
  "type": "service_account",
  "project_id": YOUR-PROJECT-NAME,
  "private_key_id": YOUR-PRIVATE-KEY-ID,
  "private_key": "-----BEGIN PRIVATE KEY-----\n-YOUR-PRIVATE-KEY-\n-----END PRIVATE KEY-----\n",
  "client_email": EMAIL-ASSIGNED-TO-THIS-SERVICE-ACCOUNT
  "client_id": YOUR-CLIENT-ID,
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": YOUR-CLIENT-CERT-URL
}
```
