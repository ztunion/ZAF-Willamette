# mitmproxy Plugins

This directory contains mitmproxy addons that act as a transparent AI API proxy.
Clients send requests with a placeholder handle token; the proxy intercepts them,
authenticates the client against the CMS, and forwards the request with the real
vendor API key.

---

## 1. Connection Flow

```
Client
  │
  │  HTTPS request
  │  Authorization: Bearer <handle>
  ▼
mitmproxy (plugins loaded)
  │
  ├─ [TLS ClientHello]
  │     ja_fingerprint.py
  │       └─ Compute JA3 / JA4 fingerprints
  │          → stored on flow.client_conn
  │
  ├─ [HTTP request]
  │     request_replacer.py
  │       ├─ Read IP, JA3, JA4, handle from request
  │       ├─ CredentialManagement.get_new_api_key()
  │       │     ├─ ip2asn.py  → resolve IP to ASN / country / ISP
  │       │     └─ CMSClient  → look up real vendor key for this handle
  │       └─ Replace Authorization: Bearer <handle>
  │                            with Authorization: Bearer <real_vendor_key>
  │
  ▼
AI Vendor API (OpenAI, HuggingFace, …)
  │
  └─ Response forwarded back to client unchanged
```

### Steps in detail

| Step | Component | What happens |
|------|-----------|--------------|
| 1 | `ja_fingerprint.py` | Parses the TLS ClientHello and computes JA3 (MD5) and JA4 fingerprints. Stores them on `flow.client_conn.ja3` / `.ja4`. |
| 2 | `request_replacer.py` | On every HTTP request, reads the fingerprints, the source IP, and the `Authorization: Bearer` handle. |
| 3 | `credential_management.py` | Resolves the handle to a real vendor API key. Also performs GeoIP enrichment via `ip2asn.py`. |
| 4 | `cms_client.py` | Contacts the CMS server to look up credentials and access policies for the handle. Caches results with TTL. |
| 5 | `ip2asn.py` | Looks up the client IP in a local SQLite database to get ASN, country, and ISP. |

### CMS API endpoints used

| Endpoint | Purpose |
|----------|---------|
| `GET /api/credentials/lookup?handle=…&vendor=…` | Fetch real vendor API key |
| `GET /api/policies/lookup?handle=…` | Fetch access policy (time range, IP CIDR, ASN, country, JA4) |
| `POST /api/logs/insert` | Record access log |

---

## 2. Plugin Files

### `ja_fingerprint.py`
Computes **JA3** and **JA4** TLS fingerprints from the raw ClientHello.

- Listens on the `tls_clienthello` mitmproxy hook.
- Filters out GREASE values before hashing.
- JA3: `MD5(version,ciphers,extensions,curves,points)`
- JA4: `t<ver><sni><#ciphers><#exts><alpn>_<cipher_hash>_<ext+sigalg_hash>`
- Stores results on `flow.client_conn.ja3` and `flow.client_conn.ja4` for use by downstream addons.

---

### `request_replacer.py`
The main mitmproxy addon. Intercepts every HTTP request and replaces the Bearer token.

- Skips requests that have no JA3/JA4 (non-TLS or fingerprint not yet computed).
- Extracts the client IP, URL, and handle from the `Authorization` header.
- Delegates key resolution to `CredentialManagement`.
- Writes the resolved key back into the `Authorization` header before the request is forwarded.

---

### `credential_management.py`
Resolves a client handle to a real vendor API key.

> **TODO — needs rewrite**
>
> The current implementation is a **temporary stub** that hard-codes API keys by
> token prefix (`hf_` → HuggingFace key, `sk-` → OpenAI key). It does not contact
> the CMS at all.
>
> It must be rewritten to call `CMSClient.fetch_credential()` and
> `CMSClient.check_policies()` so that key resolution and access control are driven
> by the live CMS database instead of hard-coded values.

Planned behaviour after rewrite:
1. Call `CMSClient.fetch_credential(handle, vendor)` to get the real API key.
2. Call `CMSClient.check_policies(handle)` to enforce time-range, IP CIDR, ASN, country, and JA4 rules.
3. Call `CMSClient.log_access(...)` to record each request.

---

### `cms_client.py`
HTTP client for the remote CMS server (`https://cms.ztunion.com`).

- Provides both synchronous and async methods (`fetch_credential` / `afetch_credential`, etc.).
- TTL caches for credentials (default 60 s) and policies (default 600 s) to avoid hitting the CMS on every request.
- Cache can be invalidated externally via `update_credential_cache()`, `update_policy_cache()`, and `invalidate()` — intended for use with CMS webhook events.
- Configured via environment variables:
  - `CMS_BASE_URL` (default: `https://cms.ztunion.com`)
  - `BACKEND_API_KEY` — Bearer token used to authenticate with the CMS.

---

### `ip2asn.py`
Offline IP geolocation using the [`ip2asn`](https://pypi.org/project/ip2asn/) PyPI library.

- Maps IPv4 addresses to ASN, country code, and ISP/owner name.
- Wraps `ip2asn.IP2ASN` and exposes an `IP2ASNDatabase` interface with context manager support.
- Data source: a TSV file downloaded from [iptoasn.com](https://iptoasn.com/).
- Default database path: `ip2asn/database.tsv` (relative to the project root)
- Used by `CredentialManagement` to enrich requests with GeoIP context before policy evaluation.
- Provides both synchronous (`lookup`) and async (`alookup`) interfaces.

**Downloading / updating the database:**

```bash
# First-time download or update (bundled CLI from the ip2asn package)
ip2asn --fetch -f ip2asn/database.tsv
```

---

## 3. Running the Proxy

### Prerequisites

```bash
pip install mitmproxy httpx ip2asn
```

Download the IP2ASN database (requires network access, ~10 MB):

```bash
ip2asn --fetch
```

The file is saved to `ip2asn/database.tsv` inside the project root.
Re-run periodically to keep routing data current (weekly is sufficient for most use cases).

Set environment variables:

```bash
export CMS_BASE_URL=https://cms.ztunion.com
export BACKEND_API_KEY=<your-cms-api-key>
```

### Start mitmproxy

Load all addons and choose a listen port:

```bash
mitmproxy \
  --listen-port 8443 \
  --ssl-insecure \
  -s plugins/ja_fingerprint.py \
  -s plugins/request_replacer.py
```

Or in headless mode:

```bash
mitmdump \
  --listen-port 8443 \
  --ssl-insecure \
  -s plugins/ja_fingerprint.py \
  -s plugins/request_replacer.py
```

### Port selection

| Port | Notes |
|------|-------|
| **8080** | Default mitmproxy port. **Blocked by many VPNs** (common corporate VPN policy treats 8080 as a non-standard HTTP port and drops traffic). Avoid in production or when clients may be behind a VPN. |
| **8443** | Recommended alternative. Passes through most VPN policies as it resembles HTTPS alternate traffic. |
| **443** | Ideal if the proxy runs on a dedicated host; requires root or `CAP_NET_BIND_SERVICE`. |

### Client configuration

Configure the client to route HTTPS traffic through the proxy and trust the mitmproxy CA certificate:

```bash
# Example: curl
curl --proxy http://<proxy-host>:8443 \
     --cacert ~/.mitmproxy/mitmproxy-ca-cert.pem \
     https://api.openai.com/v1/chat/completions \
     -H "Authorization: Bearer <your-handle>"
```

The mitmproxy CA certificate is generated on first run and stored at
`~/.mitmproxy/mitmproxy-ca-cert.pem`. Install it as a trusted root on the client
OS or pass it explicitly as shown above.
