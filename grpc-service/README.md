# Willamette CMS gRPC Service

The Willamette CMS gRPC service stores virtual API-key mappings and returns the
provider key and policy associated with a virtual key. It is designed to be
called by the Willamette MITM proxy, not directly by end-user applications.

## What this component does

The service provides a central API for creating and resolving virtual keys.
Real provider keys are stored in Google Secret Manager. Key metadata and policy
configuration are stored in Google Cloud Firestore.

Typical request flow:

```text
Demo client or application
        |
        | provider request with a virtual key
        v
Willamette MITM proxy
        |
        | ResolveApiKey(virtual_key)
        v
Willamette CMS gRPC service
        |                         |
        |                         +--> Secret Manager: real provider key
        +----------------------------> Firestore: provider, status, policy
        |
        v
MITM proxy replaces the virtual key and forwards the request
```

The CMS returns policy data to the caller. The current implementation does not
enforce IP, JA3, JA4, or country policy itself. Policy enforcement belongs in
the MITM or another policy-decision component.

## Supported functionality

| Capability | Status | Notes |
|---|---|---|
| Create a virtual API key | Supported | `CreateApiKey` stores the real key in Secret Manager and metadata in Firestore. |
| Resolve a virtual key | Supported | `ResolveApiKey` returns the real key, provider, and policy. |
| Read one key and policy | Supported | `GetKeyPolicy` returns the same stored information for one virtual key. |
| List all stored policies | Supported | `ListPolicies` returns every record in the `api_keys` collection. |
| IP policy fields | Stored and returned | CIDR values are not validated or enforced by this service. |
| JA3 policy fields | Stored and returned | Fingerprints are not validated or enforced by this service. |
| JA4 policy fields | Stored and returned | Fingerprints are not validated or enforced by this service. |
| Country policy fields | Stored and returned | Country codes are not validated or enforced by this service. |
| OpenAI-style virtual-key prefix | Supported | Generated with an `sk-` prefix. |
| Anthropic-style virtual-key prefix | Supported | Generated with an `sk-ant-` prefix. |
| Hugging Face-style virtual-key prefix | Supported | Generated with an `hf_` prefix. |
| Other providers | Partially supported | Generated with a generic `vk-` prefix. |

## Not currently supported

The current service does not provide:

- policy enforcement or allow/deny decisions;
- update, disable, revoke, or delete RPCs;
- status checks during key resolution;
- pagination for `ListPolicies`;
- audit logging or change history;
- request-field validation beyond Protocol Buffers types;
- per-provider validation of real keys;
- gRPC reflection or an application-level health RPC;
- application-level authorization or role-based access control;
- TLS termination inside the container.

When deployed on Cloud Run, TLS is terminated by Cloud Run and the service
should remain protected by Cloud Run IAM.

## gRPC API

The service definition is in `app/cms.proto`.

| RPC | Purpose |
|---|---|
| `CreateApiKey` | Create a virtual key, store the real key, and save policy metadata. |
| `GetKeyPolicy` | Retrieve one stored key mapping and policy. |
| `ResolveApiKey` | Resolve a virtual key for use by the MITM proxy. |
| `ListPolicies` | Return all stored mappings and policies. |

The policy message contains:

- `ip_validation_enabled` and `allowed_ip_ranges`;
- `ja3_validation_enabled` and `allowed_ja3`;
- `ja4_validation_enabled` and `allowed_ja4`;
- `country_validation_enabled` and `allowed_countries`.

## Data storage

### Firestore

Collection:

```text
api_keys
```

Each document uses the virtual API key as its document ID and stores fields
similar to:

```text
virtual_api_key
provider
secret_version
status
owner
policy
```

### Secret Manager

The real provider key is stored as a Secret Manager secret version. Firestore
stores the full secret-version resource name, not the real key itself.

The current implementation creates a secret when it does not already exist and
adds a new version when the same secret ID is reused.

## Important development behavior

`server.py` currently calls `seed_test_data_if_missing()` at startup. This adds
placeholder OpenAI, Hugging Face, and Anthropic test records to Firestore and
Secret Manager when they are absent.

This is useful for a development environment, but it should be removed,
disabled with configuration, or guarded by an explicit development flag before
production use.

The code also defaults `GCP_PROJECT` to `santiam`. Set `GCP_PROJECT` explicitly
in every environment so the service cannot accidentally write to the wrong
Google Cloud project.

## Repository layout

```text
.
├── app
│   ├── client_test.py
│   ├── cms.proto
│   ├── cms_pb2.py
│   ├── cms_pb2_grpc.py
│   ├── secret_store.py
│   ├── server.py
│   └── storage.py
├── Dockerfile
├── README.md
└── requirements.txt
```

## Prerequisites

For local development:

- Python 3.12 or later;
- Google Cloud CLI;
- access to a Google Cloud project;
- a Firestore database in Native mode;
- Secret Manager API enabled;
- Application Default Credentials with permission to use Firestore and Secret
  Manager.

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

### 3. Authenticate for local Google Cloud access

```bash
gcloud auth application-default login
```

Set the project explicitly.

Windows Command Prompt:

```cmd
set GCP_PROJECT=<PROJECT_ID>
```

PowerShell:

```powershell
$env:GCP_PROJECT = "<PROJECT_ID>"
```

macOS or Linux:

```bash
export GCP_PROJECT=<PROJECT_ID>
```

### 4. Start the service

From the service root:

```bash
python app/server.py
```

The service listens on port `8080` unless `PORT` is set.

### 5. Regenerate gRPC files after changing `cms.proto`

```bash
python -m grpc_tools.protoc \
  -I app \
  --python_out=app \
  --grpc_python_out=app \
  app/cms.proto
```

Commit `cms_pb2.py` and `cms_pb2_grpc.py` whenever the proto contract changes.

## Local testing

Because startup reads and writes Firestore and Secret Manager, local testing
uses the configured Google Cloud project. Use a development project rather
than production.

### Basic source validation

```bash
python -m compileall app
```

### Test with grpcurl

Install `grpcurl`, start the service, and run:

```bash
grpcurl \
  -plaintext \
  -proto app/cms.proto \
  -d '{"virtual_api_key":"sk-willamette-test-virtual-001"}' \
  localhost:8080 \
  willamette.cms.v1.CmsService/ResolveApiKey
```

List all records:

```bash
grpcurl \
  -plaintext \
  -proto app/cms.proto \
  -d '{}' \
  localhost:8080 \
  willamette.cms.v1.CmsService/ListPolicies
```

Expected results:

- a known virtual key returns `found: true`;
- an unknown virtual key returns `found: false`;
- Firestore contains a document in `api_keys`;
- Secret Manager contains the secret version referenced by the Firestore
  document.

Do not paste real provider keys into test logs or screenshots.

## Google Cloud deployment

The service is intended for Cloud Run. Cloud Run should be configured for
HTTP/2 end-to-end because this is a gRPC service.

The examples below use:

```text
Project: <PROJECT_ID>
Region: <REGION>
Service: willamette-cms-grpc
Service account: willamette-cms@<PROJECT_ID>.iam.gserviceaccount.com
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

### 3. Create Firestore if the project does not already have a database

Choose the database location carefully; it cannot be freely changed later.

```bash
gcloud firestore databases create --location=<FIRESTORE_LOCATION>
```

The application uses the default Firestore database.

### 4. Create a dedicated runtime service account

```bash
gcloud iam service-accounts create willamette-cms \
  --display-name="Willamette CMS runtime"
```

Grant Firestore read/write access:

```bash
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:willamette-cms@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
```

The current code creates secrets, adds secret versions, and reads secret
payloads. The simplest development role is:

```bash
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:willamette-cms@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/secretmanager.admin"
```

For production, replace the broad Secret Manager Admin role with a custom role
or narrower secret-level permissions that allow only the required create,
version-add, and access operations.

### 5. Deploy privately to Cloud Run

Run this command from the service root, where the Dockerfile is located:

```bash
gcloud run deploy willamette-cms-grpc \
  --source . \
  --project <PROJECT_ID> \
  --region <REGION> \
  --service-account willamette-cms@<PROJECT_ID>.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT=<PROJECT_ID> \
  --use-http2 \
  --no-allow-unauthenticated
```

The Dockerfile compiles `cms.proto` during the image build and starts
`server.py` on the Cloud Run `PORT` value.

### 6. Grant invocation permission

Grant `roles/run.invoker` only to the MITM service account and approved
operators.

Example for a service account:

```bash
gcloud run services add-iam-policy-binding willamette-cms-grpc \
  --project <PROJECT_ID> \
  --region <REGION> \
  --member="serviceAccount:<CALLER_SERVICE_ACCOUNT>" \
  --role="roles/run.invoker"
```

### 7. Confirm the service configuration

```bash
gcloud run services describe willamette-cms-grpc \
  --project <PROJECT_ID> \
  --region <REGION>
```

Confirm that:

- the service is private;
- HTTP/2 is enabled;
- `GCP_PROJECT` is correct;
- the dedicated runtime service account is selected;
- the latest revision is serving traffic.

## Testing the Cloud Run deployment

Get the service URL:

```bash
gcloud run services describe willamette-cms-grpc \
  --project <PROJECT_ID> \
  --region <REGION> \
  --format="value(status.url)"
```

The gRPC host is the service URL without `https://` and without a path.

Create an identity token whose audience is the full Cloud Run URL, then pass it
as gRPC metadata.

PowerShell example:

```powershell
$serviceUrl = "https://<CLOUD_RUN_HOST>"
$token = gcloud auth print-identity-token --audiences=$serviceUrl

grpcurl `
  -proto app/cms.proto `
  -H "authorization: Bearer $token" `
  -d '{}' `
  <CLOUD_RUN_HOST>:443 `
  willamette.cms.v1.CmsService/ListPolicies
```

macOS or Linux example:

```bash
SERVICE_URL="https://<CLOUD_RUN_HOST>"
TOKEN="$(gcloud auth print-identity-token --audiences="$SERVICE_URL")"

grpcurl \
  -proto app/cms.proto \
  -H "authorization: Bearer $TOKEN" \
  -d '{}' \
  <CLOUD_RUN_HOST>:443 \
  willamette.cms.v1.CmsService/ListPolicies
```

`app/client_test.py` can also be used, but its `HOST` constant must match the
deployed Cloud Run host and its `TOKEN` environment variable must contain a
valid identity token.

## Configuration reference

| Setting | Required | Default | Description |
|---|---|---|---|
| `GCP_PROJECT` | Yes | `santiam` in current code | Project containing Firestore and Secret Manager. Always set explicitly. |
| `PORT` | No | `8080` | Listening port. Cloud Run sets this automatically. |

## Operational checks

View recent logs:

```bash
gcloud run services logs read willamette-cms-grpc \
  --project <PROJECT_ID> \
  --region <REGION> \
  --limit 100
```

Stream logs:

```bash
gcloud beta run services logs tail willamette-cms-grpc \
  --project <PROJECT_ID> \
  --region <REGION>
```

Common failures:

| Symptom | Likely cause |
|---|---|
| Container starts but RPC calls fail | HTTP/2 was not enabled on Cloud Run. |
| `403` or unauthenticated response | Caller lacks `roles/run.invoker` or sent the wrong identity-token audience. |
| Firestore permission error | Runtime service account lacks `roles/datastore.user`. |
| Secret Manager permission error | Runtime service account cannot create, version, or access secrets. |
| Data appears in the wrong project | `GCP_PROJECT` was omitted or set incorrectly. |
| Startup writes unexpected test data | `seed_test_data_if_missing()` is still enabled. |

## Security notes

- Keep the service private.
- Never log real provider keys or complete `ResolveApiKey` responses.
- Treat `ListPolicies`, `GetKeyPolicy`, and `ResolveApiKey` as highly sensitive
  because they return real key material.
- Use a dedicated runtime service account and least-privilege IAM.
- Remove or guard startup seed data before production.
- Add audit logging, key status checks, and revocation before production use.
- Rotate any real key that has appeared in chat, command history, screenshots,
  or logs.
