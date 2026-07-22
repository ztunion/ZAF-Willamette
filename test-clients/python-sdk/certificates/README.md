# Willamette MITM Proxy CA Certificates

This directory intentionally does not contain a deployment certificate.

Every Willamette MITM Proxy deployment must generate or provide its own
certificate authority. Test clients must obtain the public CA certificate from
the exact proxy deployment they are testing.

## Why each deployment needs its own CA

Mitmproxy generates a unique certificate authority the first time it starts
with a new configuration directory. The CA signs the temporary interception
certificates presented to clients.

The configuration directory must be stored on persistent, access-controlled
storage. Replacing or deleting it generates a different CA and invalidates the
certificate already trusted by test clients.

## Generate a deployment CA automatically

On the proxy host, select a persistent configuration directory:

```bash
export WILLAMETTE_MITM_CONFDIR="$HOME/.willamette-mitm"
mkdir -p "$WILLAMETTE_MITM_CONFDIR"
chmod 700 "$WILLAMETTE_MITM_CONFDIR"
```

Start mitmdump with that directory:

```bash
mitmdump \
  --set confdir="$WILLAMETTE_MITM_CONFDIR" \
  --listen-host 0.0.0.0 \
  --listen-port 18080
```

On first start, mitmproxy generates the CA files automatically. Stop the
interactive process with `Ctrl+C` after confirming startup, or use the same
command and configuration directory in the service definition.

Always pass the same `confdir` to the proxy service. Do not create a new
configuration directory on each restart.

## Generated files

The configuration directory contains files similar to:

| File | Contents | Distribution |
|---|---|---|
| `mitmproxy-ca.pem` | CA certificate and private key | Never distribute or commit |
| `mitmproxy-ca-cert.pem` | Public CA certificate in PEM format | Distribute to approved clients |
| `mitmproxy-ca-cert.p12` | Public CA certificate in PKCS#12 format | Useful for Windows import |
| `mitmproxy-ca-cert.cer` | Public CA certificate with an Android-compatible extension | Useful for some Android devices |

Protect the complete configuration directory because it contains the CA private
key.

## Retrieve the public CA certificate

### Option 1: Use `mitm.it`

1. Start the Willamette MITM Proxy.
2. Configure the test device or browser to use the proxy.
3. Browse to:

```text
http://mitm.it
```

4. Download the certificate for the test platform.
5. Verify the fingerprint with the proxy administrator before trusting it.

### Option 2: Copy it from the proxy host

Copy only the public certificate:

```bash
scp <proxy-user>@<proxy-host>:<confdir>/mitmproxy-ca-cert.pem \
  certificates/mitmproxy-ca-cert.pem
```

For Windows certificate import, retrieve the PKCS#12 file when required:

```bash
scp <proxy-user>@<proxy-host>:<confdir>/mitmproxy-ca-cert.p12 \
  certificates/mitmproxy-ca-cert.p12
```

Never copy or expose:

```text
mitmproxy-ca.pem
```

## Verify the public certificate

The proxy administrator should publish the expected SHA-256 certificate
fingerprint through a separate trusted channel.

Windows:

```cmd
certutil -dump certificates\mitmproxy-ca-cert.pem
certutil -hashfile certificates\mitmproxy-ca-cert.pem SHA256
```

macOS or Linux:

```bash
openssl x509 \
  -in certificates/mitmproxy-ca-cert.pem \
  -noout \
  -subject \
  -issuer \
  -dates \
  -fingerprint \
  -sha256

sha256sum certificates/mitmproxy-ca-cert.pem
```

The OpenSSL fingerprint identifies the X.509 certificate. The file checksum
verifies the exact encoded file.

## Application-scoped Python trust

A combined CA bundle preserves the normal public roots and adds the active
Willamette deployment CA.

Install dependencies first:

```bash
pip install certifi
```

Windows Command Prompt:

```cmd
python -c "import certifi,pathlib; out=pathlib.Path('certificates/willamette-ca-bundle.pem'); out.write_bytes(pathlib.Path(certifi.where()).read_bytes()+b'\n'+pathlib.Path('certificates/mitmproxy-ca-cert.pem').read_bytes()); print(out.resolve())"

set SSL_CERT_FILE=%CD%\certificates\willamette-ca-bundle.pem
set REQUESTS_CA_BUNDLE=%CD%\certificates\willamette-ca-bundle.pem
```

macOS or Linux:

```bash
python - <<'PY'
import certifi
from pathlib import Path

output = Path("certificates/willamette-ca-bundle.pem")
output.write_bytes(
    Path(certifi.where()).read_bytes()
    + b"\n"
    + Path("certificates/mitmproxy-ca-cert.pem").read_bytes()
)
print(output.resolve())
PY

export SSL_CERT_FILE="$PWD/certificates/willamette-ca-bundle.pem"
export REQUESTS_CA_BUNDLE="$PWD/certificates/willamette-ca-bundle.pem"
```

The generated bundle is local test output and must not be committed.

## Optional operating-system trust

System-wide trust affects other applications and should only be configured on
approved test systems.

### Windows

Import the certificate through the Windows certificate UI, or run an
administrator Command Prompt:

```cmd
certutil -addstore -f Root certificates\mitmproxy-ca-cert.pem
```

### macOS

Use Keychain Access to import the certificate into an approved keychain and
configure trust. Remove it when testing is complete.

### Ubuntu or Debian

```bash
sudo cp certificates/mitmproxy-ca-cert.pem \
  /usr/local/share/ca-certificates/willamette-mitmproxy-ca.crt

sudo update-ca-certificates
```

## Use an externally managed custom CA

This is an advanced deployment option. Keep the private key on the proxy host
and restrict file access.

Create a CA:

```bash
openssl req \
  -x509 \
  -new \
  -nodes \
  -key ca.key \
  -sha256 \
  -out ca.crt \
  -addext keyUsage=critical,keyCertSign

cat ca.key ca.crt > mitmproxy-ca.pem
```

Place `mitmproxy-ca.pem` in the selected mitmproxy configuration directory,
then start mitmproxy with that directory:

```bash
mitmdump \
  --set confdir="/path/to/persistent/confdir" \
  --listen-port 18080
```

Only use a custom CA when ownership, storage, rotation, and revocation
responsibilities are clearly defined.

## Rotation

Rotate the CA when the private key may have been exposed or when required by
the deployment security policy.

1. Stop the proxy.
2. Securely archive or remove the old CA files.
3. Start the proxy with a new empty persistent configuration directory, or
   install a new approved custom CA.
4. Publish the new public certificate fingerprint.
5. Distribute the new public certificate.
6. Recreate application CA bundles.
7. Remove the old CA from client trust stores.
8. Restart and validate direct and proxied requests.

## Repository safety

Do not commit:

```text
mitmproxy-ca.pem
mitmproxy-ca-cert.pem
mitmproxy-ca-cert.p12
mitmproxy-ca-cert.cer
willamette-ca-bundle.pem
*.key
```

Public deployment certificates should be distributed through an approved
artifact or configuration channel rather than stored permanently in source
control.
