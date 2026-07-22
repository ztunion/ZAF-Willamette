# Willamette Demo Client for macOS

This directory contains macOS-specific setup and build instructions for
the Willamette Demo Client.

The shared application source is located at:

```text
../app.py
```

For supported providers, proxy configuration, usage, testing, and known
limitations, see the main [Demo Client README](../README.md).

## Prerequisites

- macOS
- Python 3.11 or later
- pip
- Tkinter
- Internet access to the selected AI provider
- Access to the Willamette MITM Proxy when testing proxy mode

The macOS application must be built on macOS. A Windows build cannot
produce a reliable macOS `.app` bundle.

## Run from source

Run these commands from the `demo-client` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install requests

python app.py
```

## Build the macOS application

Install PyInstaller:

```bash
pip install pyinstaller
```

Build the application:

```bash
python -m PyInstaller \
  --windowed \
  --name WillametteDemoClient \
  app.py
```

The application bundle is created at:

```text
dist/WillametteDemoClient.app
```

## Test the application

Run:

```bash
open dist/WillametteDemoClient.app
```

Validate both:

1. Direct Provider mode using a real provider key.
2. Willamette Proxy mode using a configured virtual key.

## Create a distribution ZIP

```bash
cd dist

ditto -c -k \
  --sequesterRsrc \
  --keepParent \
  WillametteDemoClient.app \
  WillametteDemoClient-mac.zip
```

Unsigned applications may be blocked by macOS Gatekeeper. Signing and
notarization are required for production distribution.

Do not commit files from `.venv`, `build`, or `dist`.
