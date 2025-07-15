# ROV Auto-Connect Release Guide

## Building the Executable

### Prerequisites
- Python 3.7 or higher
- Windows 10/11 (for Windows executable)
- VLC Media Player installed on target system

### Local Build
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the build script:
   ```bash
   python build_exe.py
   ```

3. The executable will be created in the `dist/` folder as `ROV_AutoConnect.exe`

## GitHub Releases

### Automatic Release (Recommended)
1. Create and push a new version tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. GitHub Actions will automatically:
   - Build the executable
   - Create a new release
   - Upload the executable file

### Manual Release
1. Build the executable locally using the steps above
2. Go to your GitHub repository
3. Click "Releases" in the right sidebar
4. Click "Create a new release"
5. Choose a tag (e.g., v1.0.0)
6. Upload the `ROV_AutoConnect.exe` file from the `dist/` folder
7. Add release notes describing changes

## What's Included in the Executable

The executable is a self-contained Windows application that includes:
- Python runtime
- OpenCV library for RTSP stream validation
- Tkinter GUI framework
- All required dependencies
- Logo files (DeepTrekker and MarineStream)

**Size**: Approximately 50-100 MB (depending on dependencies)

## User Requirements

Users only need:
- Windows 10/11
- VLC Media Player installed
- Network connection to ROV

No Python installation required on the user's system.

## Troubleshooting

### Build Issues
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Make sure logo files are in the project root
- Check that PyInstaller is installed: `pip install pyinstaller`

### Runtime Issues
- Users must have VLC installed
- Windows Defender may flag the executable (add to exclusions)
- Some antivirus software may require whitelisting

## Version History

### v1.0.0
- Initial release
- Automatic ROV stream discovery
- Modern GUI interface
- VLC integration
- Support for multiple RTSP URLs 