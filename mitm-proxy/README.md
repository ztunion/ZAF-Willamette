# Willamette MITM Proxy

The Willamette MITM Proxy intercepts supported AI provider requests,
collects request metadata, resolves virtual API keys through the CMS gRPC
Service, replaces virtual credentials with real provider credentials, and
forwards the requests to their destinations.

## Responsibilities

- Intercept HTTP and HTTPS requests through mitmproxy
- Read connection metadata such as client IP, JA3, JA4, and SNI
- Extract a virtual credential from a supported request
- Call the CMS gRPC Service
- Replace the virtual credential with the real provider credential
- Forward the modified request to the provider

## Source layout

```text
mitm-proxy/
├── README.md
└── plugins/
    ├── request_replacer.py
    ├── credential_management.py
    ├── cms_client.py
    ├── cms.proto
    ├── cms_pb2.py
    ├── cms_pb2_grpc.py
    ├── ja_fingerprint.py
    ├── ip2geo_db.py
    ├── ip2asn_db.py
    └── ip2asn/
```

Important files:

| File | Purpose |
|---|---|
| `request_replacer.py` | Intercepts requests and replaces supported credentials |
| `credential_management.py` | Coordinates CMS lookup and policy evaluation |
| `cms_client.py` | Calls the CMS gRPC Service |
| `ja_fingerprint.py` | Provides TLS fingerprint information |
| `ip2geo_db.py` | Provides IP geolocation information |
| `ip2asn_db.py` | Provides ASN information |

## Supported behavior

The imported proxy implementation currently handles credentials in:

```http
Authorization: Bearer <virtual-key>
```

This format is used by providers such as OpenAI and Hugging Face.

The proxy also expects JA3 and JA4 metadata to be available. Requests may be
left unchanged when required metadata or credentials are missing.

## Not currently supported by the imported implementation

The following formats require separate extraction and replacement logic:

- Gemini `key` query parameter
- Gemini `x-goog-api-key` header
- Anthropic `x-api-key` header
- OAuth access-token flows
- Requests that do not pass through the configured proxy

A temporary Gemini query-parameter implementation was validated during
development, but it should be reviewed and integrated by the MITM Proxy owner
before being treated as production support.

## Prerequisites

- Linux VM or another supported mitmproxy host
- Python 3
- mitmproxy or mitmdump
- Network access to the CMS gRPC Service
- Network access to target AI providers
- A trusted mitmproxy CA certificate on test clients
- Required geo and ASN data files

## Run locally

From the `mitm-proxy` directory, install the required Python dependencies
for the plugin environment and launch mitmdump with the add-on entry point
used by the project.

A typical command is:

```bash
mitmdump   --listen-host 0.0.0.0   --listen-port 18080   -s plugins/request_replacer.py
```

The exact start command may differ when add-ons are registered from another
loader file or when custom mitmproxy options are required.

Verify that the proxy is listening:

```bash
ss -ltnp | grep 18080
```

## Configure a test client

Configure the client to use:

```text
http://<proxy-host>:18080
```

Install and trust the mitmproxy CA certificate on the test client before
testing HTTPS traffic.

## Test

1. Start the CMS gRPC Service.
2. Confirm a virtual key exists in the CMS.
3. Start the MITM Proxy.
4. Configure the Demo Client to use the proxy.
5. Send a request using a virtual Bearer credential.
6. Confirm the request reaches the provider successfully.
7. Review logs without exposing the real or virtual credential.

Useful log command for a systemd deployment:

```bash
sudo journalctl -u willamette-mitm -f
```

## Google Cloud deployment

The development proxy can run on a Compute Engine VM.

### 1. Create or use a VM

Use a Linux VM that can reach the CMS gRPC Service and provider endpoints.

### 2. Install the application

Clone the repository and install mitmproxy and project dependencies.

### 3. Create a systemd service

Example:

```ini
[Unit]
Description=Willamette MITM Proxy
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/<user>/ZAF/willamette/mitm-proxy
ExecStart=/usr/local/bin/mitmdump --listen-host 0.0.0.0 --listen-port 18080 -s plugins/request_replacer.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Adjust the username, installation path, Python environment, add-on entry
point, and CMS configuration for the VM.

Reload and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable willamette-mitm
sudo systemctl restart willamette-mitm
sudo systemctl status willamette-mitm
```

## Configuration

The exact CMS endpoint and authentication method depend on the deployed
client implementation.

Review these files before deployment:

- `plugins/cms_client.py`
- `plugins/cms_client_adc.py`
- `plugins/cms_client_gcloud.py`
- `plugins/credential_management.py`

Use Application Default Credentials, a dedicated service account, or the
approved project authentication method. Do not hard-code service-account
keys or API keys.

## Firewall

Do not allow unrestricted public access to the proxy port.

Restrict TCP port `18080` to approved tester IP addresses or trusted network
ranges. Publicly exposed proxy ports are commonly scanned and abused.

## Troubleshooting

### Request is not modified

Check that:

- the request uses `Authorization: Bearer`;
- JA3 and JA4 are available;
- the virtual key exists in the CMS;
- the proxy can reach the CMS gRPC Service;
- the client is actually using the proxy.

### HTTPS certificate errors

Install and trust the mitmproxy CA certificate on the test client.

### CMS lookup fails

Check the CMS endpoint, authentication configuration, IAM permissions,
network connectivity, and service logs.

### Provider returns an authentication error

Confirm the provider uses a credential format supported by the current
proxy implementation. Gemini API keys cannot be sent as Bearer tokens.

## Security

- Never log real API keys or authorization headers.
- Restrict proxy access by firewall or another access-control layer.
- Rotate credentials that may have been exposed.
- Use a dedicated Google Cloud service account with minimum permissions.
- Keep test and production credentials separate.
