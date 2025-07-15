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
        
        # Update progress before checking
        def update_progress():
            progress_label.config(text=f"Checking {url} ({i+1}/{len(urls)})")
            progress_bar['value'] = i
        root.after(0, update_progress)
        
        result = check_rtsp_url(url)
        
        if result:
            active_url = result
            # Update progress to show completion
            def update_complete():
                progress_bar['value'] = len(urls)
                progress_label.config(text=f"Found active stream at {url}")
            root.after(0, update_complete)
            break
        else:
            # Update progress after failed check
            def update_failed():
                progress_bar['value'] = i + 1
            root.after(0, update_failed)
    
    result_callback(active_url)

def launch_vlc(vlc_path, rtsp_url):
    """Launch VLC with the RTSP URL in fullscreen mode using full path."""
    # Flags: --fullscreen for full screen, --no-video-title-show to hide title
    subprocess.Popen([vlc_path, rtsp_url, '--fullscreen', '--no-video-title-show'])
    print(f"Launched VLC with: {rtsp_url}")

def scan_complete(active_url):
    global scan_thread
    if active_url:
        launch_vlc(vlc_path, active_url)
        messagebox.showinfo("Success", f"Connected to ROV stream at {active_url}.\nVLC is now open - use screen capture for broadcasting.")
    else:
        messagebox.showerror("Error", "No active RTSP stream found.\nCheck ROV connection, network cable, and URL list in the script.")
    
    # Reset UI
    connect_button.config(text="Connect to ROV Stream", state=tk.NORMAL)
    def reset():
        progress_bar['value'] = 0
        progress_label.config(text="")
    root.after(0, reset)

def start_connection():
    global vlc_path, scan_thread
    connect_button.config(text="Scanning for ROV streams...", state=tk.DISABLED)
    vlc_path = get_vlc_path()
    if not vlc_path:
        connect_button.config(text="Connect to ROV Stream", state=tk.NORMAL)
        prompt_install_vlc()
        return
    
    # Show VLC version and ask to proceed
    version_info = get_vlc_version(vlc_path)
    proceed = messagebox.askyesno("VLC Detected", f"VLC found at {vlc_path}\n\n{version_info}\n\nAccept and proceed?")
    if not proceed:
        sys.exit(0)
    
    # Start scanning in thread
    urls = POSSIBLE_RTSP_URLS
    stop_event = threading.Event()
    progress_bar['maximum'] = len(urls)
    progress_bar['value'] = 0
    progress_label.config(text="Starting scan...")
    
    def result_callback(result):
        scan_complete(result)
    
    scan_thread = threading.Thread(target=find_active_rtsp, args=(urls, progress_label, result_callback, stop_event))
    scan_thread.start()

def open_vlc_link(event):
    webbrowser.open("https://www.videolan.org/vlc/")

# GUI Setup - Amazing minimal UI with light theme inspired by Apple/Google
root = tk.Tk()
root.title("ROV Auto-Connect")
root.geometry("800x600")
root.config(bg="#ffffff")  # Pure white background

# Configure window icon and make it look modern
root.resizable(False, False)
root.configure(bg='#ffffff')

# Create custom styles for Apple/Google inspired design
style = ttk.Style()
style.theme_use("clam")

# Configure styles for light theme
style.configure("Main.TFrame", background="#ffffff")
style.configure("Title.TLabel", 
                background="#ffffff", 
                foreground="#1d1d1f", 
                font=("SF Pro Display", 24, "bold"))
style.configure("Subtitle.TLabel", 
                background="#ffffff", 
                foreground="#86868b", 
                font=("SF Pro Text", 14))
style.configure("Body.TLabel", 
                background="#ffffff", 
                foreground="#1d1d1f", 
                font=("SF Pro Text", 12))
style.configure("Link.TLabel", 
                background="#ffffff", 
                foreground="#007aff", 
                font=("SF Pro Text", 12, "underline"),
                cursor="hand2")
style.configure("Primary.TButton", 
                background="#007aff", 
                foreground="#ffffff", 
                font=("SF Pro Text", 14, "bold"), 
                padding=(30, 12),
                borderwidth=0)
style.map("Primary.TButton", 
          background=[("active", "#005bb5"), ("disabled", "#d1d1d6")])
style.configure("Horizontal.TProgressbar", 
                background="#007aff", 
                troughcolor="#f2f2f7", 
                borderwidth=0,
                lightcolor="#007aff",
                darkcolor="#007aff")

# Main container with scrollable frame for better layout
main_frame = ttk.Frame(root, style="Main.TFrame")
main_frame.pack(expand=True, fill="both", padx=40, pady=40)

# Title
title_label = ttk.Label(main_frame, text="ROV Auto-Connect", style="Title.TLabel")
title_label.pack(pady=(0, 10))

# Subtitle
subtitle_label = ttk.Label(main_frame, text="Automatically discover and connect to ROV video streams", style="Subtitle.TLabel")
subtitle_label.pack(pady=(0, 20))

# Logo section
logo_frame = ttk.Frame(main_frame, style="Main.TFrame")
logo_frame.pack(pady=(0, 20))

# Load and display logos
try:
    # Load logos and resize using subsample for better control
    print("Loading DeepTrekker logo...")
    deeptrekker_logo = tk.PhotoImage(file="deeptrekkerLogo.png")
    print(f"DeepTrekker logo loaded: {deeptrekker_logo.width()}x{deeptrekker_logo.height()}")
    
    print("Loading MarineStream logo...")
    marinestream_logo = tk.PhotoImage(file="marinestreamLogo.png")
    print(f"MarineStream logo loaded: {marinestream_logo.width()}x{marinestream_logo.height()}")
    
    # Calculate proper dimensions to maintain aspect ratio
    # Target height of 60px, calculate width proportionally
    deeptrekker_height = 60
    deeptrekker_width = int(deeptrekker_logo.width() * deeptrekker_height / deeptrekker_logo.height())
    
    marinestream_height = 60
    marinestream_width = int(marinestream_logo.width() * marinestream_height / marinestream_logo.height())
    
    # Create labels with calculated dimensions to maintain aspect ratio
    deeptrekker_label = tk.Label(logo_frame, image=deeptrekker_logo, bg="#ffffff", width=deeptrekker_width, height=deeptrekker_height)
    deeptrekker_label.pack(side=tk.LEFT, padx=20)
    
    marinestream_label = tk.Label(logo_frame, image=marinestream_logo, bg="#ffffff", width=marinestream_width, height=marinestream_height)
    marinestream_label.pack(side=tk.LEFT, padx=20)
    
    # Keep references to prevent garbage collection
    # Use setattr to avoid linter warnings about unknown attributes
    setattr(root, 'deeptrekker_logo', deeptrekker_logo)
    setattr(root, 'marinestream_logo', marinestream_logo)
except Exception as e:
    print(f"Could not load logos: {e}")
    # Fallback text if logos can't be loaded
    fallback_label = ttk.Label(logo_frame, text="DeepTrekker + MarineStream", style="Subtitle.TLabel")
    fallback_label.pack()

# Instructions section
instructions_frame = ttk.Frame(main_frame, style="Main.TFrame")
instructions_frame.pack(pady=(0, 20))

instructions_text = "Ensure VLC is installed on your system. Click the link below to download if needed."
instructions_label = ttk.Label(instructions_frame, text=instructions_text, style="Body.TLabel", wraplength=500, justify=tk.CENTER)
instructions_label.pack(pady=(0, 10))

# Clickable VLC download link
vlc_link_text = "Download VLC Media Player"
vlc_link_label = ttk.Label(instructions_frame, text=vlc_link_text, style="Link.TLabel")
vlc_link_label.pack()
vlc_link_label.bind("<Button-1>", open_vlc_link)

# Progress section
progress_frame = ttk.Frame(main_frame, style="Main.TFrame")
progress_frame.pack(pady=(0, 15))

progress_label = ttk.Label(progress_frame, text="", style="Body.TLabel")
progress_label.pack(pady=(0, 10))

progress_bar = ttk.Progressbar(progress_frame, 
                              orient="horizontal", 
                              length=400, 
                              mode="determinate", 
                              style="Horizontal.TProgressbar")
progress_bar.pack()

# Connect button
button_frame = ttk.Frame(main_frame, style="Main.TFrame")
button_frame.pack(pady=(15, 0))

connect_button = ttk.Button(button_frame, 
                           text="Connect to ROV Stream", 
                           command=start_connection, 
                           style="Primary.TButton")
connect_button.pack()

# Error handling for GUI
try:
    root.mainloop()
except Exception as e:
    print(f"Error: {e}")
    messagebox.showerror("Unexpected Error", f"An error occurred: {e}")