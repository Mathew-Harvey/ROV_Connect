import subprocess  # For running external commands like checking VLC and ping
import cv2  # For validating RTSP streams (pip install opencv-python)
import sys  # For exiting the script if needed
import os  # For file/path operations
import tkinter as tk  # Built-in GUI library for simple window and buttons
import tkinter.ttk as ttk  # For styled widgets
from tkinter import messagebox  # For popup messages
import threading  # For running scanning in background
import time  # For spinner timing
import urllib.parse  # For parsing URLs
import webbrowser  # For opening links
import socket  # For port check

# List of possible RTSP URLs - customize this with your ROV's known addresses/ports
# Example: If ROV might be on different subnets or IPs, add them here
POSSIBLE_RTSP_URLS = [
    'rtsp://192.168.0.1:554/stream',
    'rtsp://192.168.0.100:554/stream',
    'rtsp://192.168.1.1:554/stream',
    'rtsp://192.168.1.100:554/stream',
    # Add more as needed, e.g., 'rtsp://user:pass@192.168.0.2:554/stream' for auth
]

# Common VLC installation paths (add more if you use custom installs)
VLC_PATHS = [
    r'C:\Program Files\VideoLAN\VLC\vlc.exe',
    r'C:\Program Files (x86)\VideoLAN\VLC\vlc.exe',
]

def get_vlc_path():
    """Check for VLC executable in common paths."""
    for path in VLC_PATHS:
        if os.path.exists(path):
            return path
    return None

def get_vlc_version(vlc_path):
    """Get VLC version string."""
    try:
        output = subprocess.check_output([vlc_path, '--version']).decode('utf-8')
        return output
    except Exception as e:
        return f"Error getting version: {str(e)}"

def prompt_install_vlc():
    """Show a popup prompting user to install VLC."""
    messagebox.showerror("VLC Not Found", "VLC is required but not installed.\n\nPlease download and install from https://www.videolan.org/vlc/.\nThen restart this app or your computer.")
    sys.exit(1)  # Exit the app

def spinner_animation(progress_label, stop_event):
    """Animate a spinner on the progress label."""
    spinner_chars = ['|', '/', '-', '\\']
    i = 0
    while not stop_event.is_set():
        char = spinner_chars[i % 4]
        current_text = progress_label.cget("text")
        new_text = current_text.rsplit(' ', 1)[0] if ' ' in current_text else current_text  # Remove old spinner
        def update():
            if not stop_event.is_set():
                progress_label.config(text=new_text + ' ' + char)
        root.after(0, update)
        i += 1
        time.sleep(0.2)
    # Clear spinner when done
    def clear():
        final_text = progress_label.cget("text").rsplit(' ', 1)[0] if ' ' in progress_label.cget("text") else ''
        progress_label.config(text=final_text)
    root.after(0, clear)

def check_rtsp_url(url):
    """Check a single RTSP URL with ping, port check, and short timeout."""
    parsed = urllib.parse.urlparse(url)
    ip = parsed.hostname
    port = parsed.port or 554
    if not ip:
        return None

    # Ping the IP with 1s timeout
    print(f"Pinging {ip}...")
    ping_cmd = ['ping', '-n', '1', '-w', '1000', ip]
    ret = subprocess.call(ping_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if ret != 0:
        print(f"Ping failed for {ip}")
        return None

    # Check if port is open with 1s timeout
    print(f"Checking port {port} on {ip}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.connect((ip, port))
        sock.close()
    except Exception as e:
        print(f"Port check failed for {ip}:{port}: {str(e)}")
        return None

    # Append FFmpeg options for timeout (stimeout in microseconds, 2s)
    timeout_url = url + '?rtsp_flags=prefer_tcp&stimeout=2000000'

    # Check RTSP with timeout
    print(f"Checking RTSP {timeout_url}...")
    try:
        cap = cv2.VideoCapture(timeout_url)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None and frame.size != 0:
                cap.release()
                return url  # Return original URL without params
        cap.release()
    except Exception as e:
        print(f"Error checking {url}: {str(e)}")
    return None

def find_active_rtsp(urls, progress_label, result_callback, stop_event):
    """Scan URLs sequentially in background thread, showing each in UI."""
    active_url = None
    for i, url in enumerate(urls):
        if stop_event.is_set():
            return
        def update_progress():
            progress_label.config(text=f"Checking {url} ({i+1}/{len(urls)})")
        root.after(0, update_progress)
        result = check_rtsp_url(url)
        if result:
            active_url = result
            break  # Stop early if found
    result_callback(active_url)

def launch_vlc(vlc_path, rtsp_url):
    """Launch VLC with the RTSP URL in fullscreen mode using full path."""
    # Flags: --fullscreen for full screen, --no-video-title-show to hide title
    subprocess.Popen([vlc_path, rtsp_url, '--fullscreen', '--no-video-title-show'])
    print(f"Launched VLC with: {rtsp_url}")

def scan_complete(active_url):
    global spinner_stop_event, scan_thread
    spinner_stop_event.set()
    if active_url:
        launch_vlc(vlc_path, active_url)
        messagebox.showinfo("Success", f"Connected to ROV stream at {active_url}.\nVLC is now open - use screen capture for broadcasting.")
    else:
        messagebox.showerror("Error", "No active RTSP stream found.\nCheck ROV connection, network cable, and URL list in the script.")
    connect_button.config(text="Connect", state=tk.NORMAL)  # Re-enable button

def start_connection():
    global vlc_path, spinner_stop_event, scan_thread
    connect_button.config(text="Scanning...", state=tk.DISABLED)  # Disable button during scan
    vlc_path = get_vlc_path()
    if not vlc_path:
        connect_button.config(text="Connect", state=tk.NORMAL)
        prompt_install_vlc()
        return
    
    # Show VLC version and ask to proceed
    version_info = get_vlc_version(vlc_path)
    proceed = messagebox.askyesno("VLC Detected", f"VLC found at {vlc_path}\n\n{version_info}\n\nAccept and proceed?")
    if not proceed:
        sys.exit(0)
    
    # Start scanning in thread
    urls = POSSIBLE_RTSP_URLS
    spinner_stop_event = threading.Event()
    spinner_thread = threading.Thread(target=spinner_animation, args=(progress_label, spinner_stop_event))
    spinner_thread.start()
    
    def result_callback(result):
        scan_complete(result)
    
    scan_thread = threading.Thread(target=find_active_rtsp, args=(urls, progress_label, result_callback, spinner_stop_event))
    scan_thread.start()

def open_vlc_link(event):
    webbrowser.open("https://www.videolan.org/vlc/")

# GUI Setup - Minimal sexy UI with dark theme
root = tk.Tk()
root.title("ROV Auto-Connect")
root.geometry("450x250")
root.config(bg="#1e1e1e")  # Dark background

style = ttk.Style()
style.theme_use("clam")  # Modern theme
style.configure("TLabel", background="#1e1e1e", foreground="#ffffff", font=("Arial", 12))
style.configure("TButton", background="#007bff", foreground="#ffffff", font=("Arial", 12, "bold"), padding=10, borderwidth=0)
style.map("TButton", background=[("active", "#0056b3")])

# Instructions label with clickable link
instructions_text = "Ensure VLC is installed (click here to download if needed) and restart your computer after installation.\nClick 'Connect' to find and launch ROV stream in VLC."
label = ttk.Label(root, text=instructions_text, wraplength=400, justify=tk.LEFT, style="TLabel")
label.pack(pady=20)
label.config(foreground="#4da6ff", cursor="hand2")  # Blue link color
label.bind("<Button-1>", open_vlc_link)

progress_label = ttk.Label(root, text="", style="TLabel")
progress_label.pack()

connect_button = ttk.Button(root, text="Connect", command=start_connection, style="TButton")
connect_button.pack(pady=20)

# Error handling for GUI
try:
    root.mainloop()
except Exception as e:
    print(f"Error: {e}")
    messagebox.showerror("Unexpected Error", f"An error occurred: {e}")