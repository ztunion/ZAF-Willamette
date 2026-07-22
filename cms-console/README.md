# Willamette CMS Console

The Willamette CMS Console is a FastAPI web application for creating and
managing virtual API keys and their associated access-policy configuration.
It is the administrative interface used to prepare key mappings consumed by
the Willamette CMS gRPC service and MITM proxy.

## What this component does

An administrator can register a real provider key, receive a virtual key, and
configure policy values for the key. The application stores the real key in
Google Secret Manager and stores the virtual key, provider metadata, policy,
and Secret Manager reference in Firestore.

```text
Administrator
     |
     | browser
     v
Willamette CMS Console
     |                         |
     |                         +--> Secret Manager: real provider key
     +----------------------------> Firestore: virtual key and policy
                                      |
                                      v
                            CMS gRPC service / MITM proxy
```

The console configures policy data. It does not itself inspect AI-provider
traffic or enforce network, JA3, JA4, or country restrictions.

## Supported functionality

| Capability | Status | Notes |
|---|---|---|
| Administrator login | Supported | Controlled by configured administrator credentials and session signing key. |
| Create a virtual key | Supported | Stores the submitted real provider key in Secret Manager. |
| List saved keys and policies | Supported | Reads metadata from Firestore. |
| Edit policy configuration | Supported | Updates the Firestore policy record. |
| Delete a key record | Supported | Removes the Firestore record in the current implementation. |
| IP validation configuration | Supported | Enable/disable and save allowed CIDR ranges. |
| JA3 validation configuration | Supported | Enable/disable and save one or more JA3 values. |
| JA4 validation configuration | Supported | Enable/disable and save one or more JA4 values. |
| Country validation configuration | Supported | Enable/disable and save one or more country codes. |
| Multiple providers | Supported | The provider is stored with the key mapping. |

## Not currently supported

The current console does not provide:

- enforcement of saved policy values;
- automatic verification that a provider key is valid;
- provider-key rotation workflows;
- secret-version cleanup when a Firestore record is deleted;
- per-user roles or multiple administrator accounts;
- an approval workflow;
- audit-history views;
- bulk import or export;
- automatic removal of old Secret Manager versions;
- self-service access for general users.

Deleting a record from the console currently removes the Firestore mapping but
may leave the Secret Manager secret and its versions in place. Review and clean
up the corresponding secret separately when deletion is intended to be final.

## Repository layout

Expected structure:

```text
webpage
├── app
│   ├── templates
│   │   ├── dashboard.html
│   │   └── login.html
│   ├── auth.py
│   ├── config.py
│   ├── main.py
│   ├── secret_store.py
│   └── storage.py
├── Dockerfile
├── README.md
└── requirements.txt
```

## Prerequisites

For local development:

- Python 3.12 or later;
- Google Cloud CLI;
- a Google Cloud project;
- Firestore in Native mode;
- Secret Manager API enabled;
- Application Default Credentials with Firestore and Secret Manager access.

## Configuration

| Environment variable | Required | Description |
|---|---|---|
| `GCP_PROJECT` | Yes | Project that contains Firestore and Secret Manager. |
| `ADMIN_USERNAME` | Yes | Username for the application login. |
| `ADMIN_PASSWORD` | Yes | Password for the application login. |
| `APP_SECRET_KEY` | Yes | Long random value used to sign application sessions. |
| `PORT` | Cloud Run only | Listening port supplied by Cloud Run. |

Use separate values for development and production. Do not commit these values
to Git.

Generate a session-signing value with Python:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Local setup

### 1. Create and activate a virtual environment

Windows Command Prompt:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Authenticate to Google Cloud

```bash
gcloud auth application-default login
```

### 4. Set local configuration

Windows Command Prompt:

```cmd
set GCP_PROJECT=<PROJECT_ID>
set ADMIN_USERNAME=<LOCAL_ADMIN_USERNAME>
set ADMIN_PASSWORD=<LOCAL_ADMIN_PASSWORD>
set APP_SECRET_KEY=<LOCAL_RANDOM_SESSION_KEY>
```

PowerShell:

```powershell
$env:GCP_PROJECT = "<PROJECT_ID>"
$env:ADMIN_USERNAME = "<LOCAL_ADMIN_USERNAME>"
$env:ADMIN_PASSWORD = "<LOCAL_ADMIN_PASSWORD>"
$env:APP_SECRET_KEY = "<LOCAL_RANDOM_SESSION_KEY>"
```

macOS or Linux:

```bash
export GCP_PROJECT=<PROJECT_ID>
export ADMIN_USERNAME=<LOCAL_ADMIN_USERNAME>
export ADMIN_PASSWORD=<LOCAL_ADMIN_PASSWORD>
export APP_SECRET_KEY=<LOCAL_RANDOM_SESSION_KEY>
```

### 5. Start the console

From the `webpage` directory:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Open:

```text
http://127.0.0.1:8080/login
```

## How to use the console

1. Sign in with the configured administrator credentials.
2. Select the provider.
3. Enter the real provider API key.
4. Enable only the policy checks required for that key.
5. Add allowed IP ranges, JA3 values, JA4 values, and country codes as needed.
6. Save the record.
7. Copy the generated virtual key and provide only that virtual key to the
   demo client or application.
8. Use the edit action to update policy values.
9. Use delete only after confirming whether the corresponding Secret Manager
   secret must also be removed.

Never expose the real provider key to users of the virtual key.

## Local testing

Use a development Google Cloud project and a non-production provider key.

### Test checklist

1. Open `/login` and confirm invalid credentials are rejected.
2. Sign in with the configured administrator credentials.
3. Create a record using a test provider key.
4. Confirm a virtual key is displayed.
5. Confirm Firestore contains the new mapping.
6. Confirm Secret Manager contains the real-key secret version.
7. Edit each policy toggle and verify Firestore updates.
8. Refresh the page and confirm the saved values remain.
9. Delete the record and confirm the Firestore document is removed.
10. Check Secret Manager separately; the secret may still exist.
11. Resolve the virtual key through the gRPC service or MITM proxy.
12. Confirm the real provider key never appears in browser logs or screenshots.

### Source validation

```bash
python -m compileall app
```

## Google Cloud deployment

The console is intended to run on Cloud Run. Keep it private and grant access
only to approved administrators, or place it behind an approved end-user
authentication layer such as IAP.

The examples below use:

```text
Project: <PROJECT_ID>
Region: <REGION>
Service: ztu-cms-webpage
Service account: willamette-cms-console@<PROJECT_ID>.iam.gserviceaccount.com
```

### 1. Select the project

```bash
gcloud config set project <PROJECT_ID>
```

### 2. Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  firestore.googleapis.com \
  secretmanager.googleapis.com
```

### 3. Create Firestore if needed

```bash
gcloud firestore databases create --location=<FIRESTORE_LOCATION>
```

Skip this command when the project already has a default Firestore database.

### 4. Create a runtime service account

```bash
gcloud iam service-accounts create willamette-cms-console \
  --display-name="Willamette CMS Console runtime"
```

Grant Firestore access:

```bash
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:willamette-cms-console@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
```

The application creates and accesses provider-key secrets. The broad
development role is:

```bash
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:willamette-cms-console@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/secretmanager.admin"
```

Use narrower permissions or a custom role in production.

### 5. Store console configuration securely

For a quick development deployment, environment variables can be supplied
directly. For production, store administrator credentials and the session key
in Secret Manager and expose them to the Cloud Run revision as environment
variables.

Example secret creation:

```bash
printf '%s' '<ADMIN_USERNAME>' | \
  gcloud secrets create willamette-admin-username --data-file=-

printf '%s' '<ADMIN_PASSWORD>' | \
  gcloud secrets create willamette-admin-password --data-file=-

printf '%s' '<APP_SECRET_KEY>' | \
  gcloud secrets create willamette-app-secret-key --data-file=-
```

Grant the runtime service account access to those configuration secrets:

```bash
gcloud secrets add-iam-policy-binding willamette-admin-username \
  --member="serviceAccount:willamette-cms-console@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding willamette-admin-password \
  --member="serviceAccount:willamette-cms-console@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding willamette-app-secret-key \
  --member="serviceAccount:willamette-cms-console@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 6. Deploy the private Cloud Run service

Run this command from the `webpage` directory:

```bash
gcloud run deploy ztu-cms-webpage \
  --source . \
  --project <PROJECT_ID> \
  --region <REGION> \
  --service-account willamette-cms-console@<PROJECT_ID>.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT=<PROJECT_ID> \
  --set-secrets ADMIN_USERNAME=willamette-admin-username:latest,ADMIN_PASSWORD=willamette-admin-password:latest,APP_SECRET_KEY=willamette-app-secret-key:latest \
  --no-allow-unauthenticated
```

### 7. Grant approved administrators access

```bash
gcloud run services add-iam-policy-binding ztu-cms-webpage \
  --project <PROJECT_ID> \
  --region <REGION> \
  --member="user:<ADMIN_EMAIL>" \
  --role="roles/run.invoker"
```

Cloud Run IAM and the application's own login are separate controls.

For a private development test in a browser, use the Cloud Run proxy from a
Linux, macOS, WSL, or Cygwin environment:

```bash
gcloud run services proxy ztu-cms-webpage \
  --project <PROJECT_ID> \
  --region <REGION> \
  --port 8080
```

Then open:

```text
http://127.0.0.1:8080/login
```

For regular browser access by approved users, enable IAP directly on Cloud Run
or use the organization's approved IAP/load-balancer configuration. Do not
make the console public merely to avoid the private-service authentication
step.

### 8. Verify the deployment

```bash
gcloud run services describe ztu-cms-webpage \
  --project <PROJECT_ID> \
  --region <REGION>
```

Confirm:

- unauthenticated access is disabled;
- the correct runtime service account is selected;
- `GCP_PROJECT` points to the intended project;
- the three configuration secrets are attached;
- the latest revision is serving traffic.

## Deployment configurations

### Local development

- Uses Application Default Credentials from the developer account.
- Uses local environment variables.
- Runs with Uvicorn reload enabled.
- Should use a development Google Cloud project.

### Shared development or QA

- Runs on private Cloud Run.
- Uses a dedicated runtime service account.
- Uses non-production provider keys.
- Limits access to the development team.

### Production

- Runs on private Cloud Run or behind IAP.
- Uses dedicated, least-privilege service identities.
- Stores administrator configuration in Secret Manager.
- Disables debug and reload behavior.
- Requires audit logging, key lifecycle procedures, and secret cleanup.
- Uses production Firestore and Secret Manager resources isolated from test.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Login page does not load | Cloud Run IAM access is missing or the latest revision is unhealthy. |
| Login always fails | `ADMIN_USERNAME` or `ADMIN_PASSWORD` is not set on the active revision. |
| Session resets immediately | `APP_SECRET_KEY` is missing or changed between revisions. |
| Firestore read/write error | Runtime identity lacks `roles/datastore.user`. |
| Secret creation or access error | Runtime identity lacks the required Secret Manager permissions. |
| Data appears in the wrong project | `GCP_PROJECT` is wrong or not set. |
| Deleted key still appears in Secret Manager | Current delete behavior removes only the Firestore record. |

View logs:

```bash
gcloud run services logs read ztu-cms-webpage \
  --project <PROJECT_ID> \
  --region <REGION> \
  --limit 100
```

## Security notes

- Do not make the administrative console publicly available without an approved
  authentication layer.
- Never commit administrator credentials, session keys, or provider keys.
- Use Secret Manager for production configuration.
- Rotate credentials that appear in shell history, screenshots, chat, or logs.
- Keep real provider keys out of Firestore and browser responses.
- Confirm secret cleanup whenever a key mapping is deleted.
