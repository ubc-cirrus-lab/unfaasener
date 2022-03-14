## How to get a private key for having access to google cloud monitoring?

1. Go to the Service Account's section of IAM & Admin in the google cloud console. 

<img src="./ServiceAccount.png" alt="Service Account Section"/>


2. Click on create a service account.

<img src="./CreateServiceAccount.png" alt="Creating a service account"/>

3. Choose a name, and select Monitoring Admin and Monitoring Viewer's roles for this service account.

<img src="./Roles.png" alt="Roles"/>

4. When the service account is created, click on the keys section, and add a new key for this service account.

<img src="./AddKey.png" alt="Adding a key"/>

5. Download the key's file and replace the path in monitoring.py with the path to the downloaded key:
```
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = THE-PATH-TO-YOUR-KEY 
```

The key will look like the following pattern:

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
