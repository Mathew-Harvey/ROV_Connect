import subprocess
import cv2  # pip install opencv-python
import sys
import os
from tkinter import messagebox  # For simple popups (optional)

# List of possible RTSP URLs (customize this based on your ROV's known addresses)
POSSIBLE_RTSP_URLS = [
    'rtsp://192.168.0.1:554/stream',
    'rtsp://192.168.0.100:554/stream',
    'rtsp://192.168.1.1:554/stream',
    # Add more, or generate dynamically e.g., for ip in range(1, 255): f'rtsp://192.168.0.{ip}:554/stream'
]

def is_vlc_installed():
    try:
        # Check if VLC is in PATH and runnable
        subprocess.check_output(['vlc', '--version'])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_vlc():
    # This is tricky to fully automate without admin/elevation. For now, prompt user.
    # Alternative: Download installer silently and run it (requires admin).
    messagebox.showerror("VLC Not Found", "VLC is not installed. Please download and install from https://www.videolan.org/vlc/")
    sys.exit(1)  # Or open the URL automatically: import webbrowser; webbrowser.open('https://www.videolan.org/vlc/')

def find_active_rtsp_url(urls):
    for url in urls:
        print(f"Checking {url}...")  # Log for debugging
        cap = cv2.VideoCapture(url)
        if cap.isOpened():
            # Optional: Read a frame to confirm it's not just connecting but has data
            ret, frame = cap.read()
            if ret:
                cap.release()
                return url
            cap.release()
    return None

def launch_vlc(rtsp_url):
    # Launch VLC in fullscreen (adjust flags as needed, e.g., --no-video-title-show)
    subprocess.Popen(['vlc', rtsp_url, '--fullscreen'])

if __name__ == '__main__':
    if not is_vlc_installed():
        install_vlc()
    
    active_url = find_active_rtsp_url(POSSIBLE_RTSP_URLS)
    if active_url:
        launch_vlc(active_url)
        print(f"Stream found and launched: {active_url}")
    else:
        messagebox.showerror("Error", "No active RTSP stream found. Check ROV connection and cable.")
        sys.exit(1)