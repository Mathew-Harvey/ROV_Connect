#!/usr/bin/env python3
"""
Build script for ROV Auto-Connect executable
"""
import os
import subprocess
import sys
import shutil

def clean_build():
    """Clean previous build artifacts"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Clean .spec files
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            print(f"Removing {file}...")
            os.remove(file)

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building ROV Auto-Connect executable...")
    
    # PyInstaller command with options:
    # --onefile: Create a single executable file
    # --windowed: Don't show console window when running
    # --add-data: Include the logo files
    # --name: Set the executable name
    # --icon: Add an icon (optional, you can add an .ico file later)
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--add-data', 'deeptrekkerLogo.png;.',
        '--add-data', 'marinestreamLogo.png;.',
        '--name', 'ROV_AutoConnect',
        'rov_autoconnect.py'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Build completed successfully!")
        
        # Check if executable was created
        exe_path = os.path.join('dist', 'ROV_AutoConnect.exe')
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path) / (1024 * 1024)  # Size in MB
            print(f"Executable created: {exe_path}")
            print(f"Size: {size:.1f} MB")
        else:
            print("Error: Executable not found in dist folder")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False
    
    return True

def main():
    print("ROV Auto-Connect Build Script")
    print("=" * 40)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("PyInstaller found")
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
    
    # Clean previous builds
    clean_build()
    
    # Build executable
    if build_executable():
        print("\nBuild successful! The executable is in the 'dist' folder.")
        print("You can now create a GitHub release with this executable.")
    else:
        print("\nBuild failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 