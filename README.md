# ROV_Connect

This application automatically scans for active ROV RTSP streams and launches them in VLC for viewing.

It features a minimal, modern UI inspired by Google and Apple designs, integrating the DeepTrekker and MarineStream logos.

## Quick Start (Windows Users)

**Download the latest executable from [GitHub Releases](https://github.com/yourusername/ROV_Connect/releases)**

1. Download `ROV_AutoConnect.exe` from the latest release
2. Ensure VLC is installed on your system
3. Run the executable - no Python installation required!

## Development Installation

1. Ensure Python is installed.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Ensure VLC is installed on your system.

## Usage

### Running from Source
```
python rov_autoconnect.py
```

### Running the Executable
Simply double-click `ROV_AutoConnect.exe`

- The UI will appear with logos and instructions.
- Click "Connect" to scan for ROV streams.
- Progress will be shown with a bar and status updates.
- If found, VLC will launch in fullscreen with the stream.

Customize the `POSSIBLE_RTSP_URLS` list in the script for your setup.

## Building the Executable

See [RELEASE.md](RELEASE.md) for detailed instructions on building and releasing the executable.

### Quick Build
```bash
pip install -r requirements.txt
python build_exe.py
```

The executable will be created in the `dist/` folder.

## System Requirements

- Windows 10/11
- VLC Media Player
- Network connection to ROV
- No Python installation required (for executable users)