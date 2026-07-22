# Willamette Demo Client for Windows

This directory contains Windows-specific setup and build instructions for
the Willamette Demo Client.

The shared application source is located at:

```text
../app.py
```

For supported providers, proxy configuration, usage, testing, and known
limitations, see the main [Demo Client README](../README.md).

## Prerequisites

- Windows 10 or later
- Python 3.11 or later
- pip
- Tkinter
- Internet access to the selected AI provider
- Access to the Willamette MITM Proxy when testing proxy mode

## Run from source

Run these commands from the `demo-client` directory:

```cmd
python -m venv .venv
.venv\Scripts\activate

python -m pip install --upgrade pip
pip install requests

python app.py
```

## Build the Windows executable

Install PyInstaller:

```cmd
pip install pyinstaller
```

Build the executable:

```cmd
python -m PyInstaller ^
  --onefile ^
  --windowed ^
  --name WillametteDemoClient ^
  app.py
```

The executable is created at:

```text
dist\WillametteDemoClient.exe
```

## Test the executable

Run:

```cmd
dist\WillametteDemoClient.exe
```

Validate both:

1. Direct Provider mode using a real provider key.
2. Willamette Proxy mode using a configured virtual key.

Do not commit files from `.venv`, `build`, or `dist`.
