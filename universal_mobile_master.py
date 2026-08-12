#!/usr/bin/env python3
import subprocess
import os
import sys
import threading
import time
import platform
import shutil
from datetime import datetime

# GUI Library Import (Tkinter is built-in with Python)
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, filedialog
except ImportError:
    print("Error: Tkinter not found. Please install python3-tk")
    sys.exit(1)

class UniversalMobileMaster:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Universal Mobile Master Pro - by Rafay")
        self.root.geometry("900x700")
        self.root.configure(bg="#2b2b2b")
        
        # Variables
        self.device_id = None
        self.is_connected = False
        self.adb_path = "adb"
        
        # Styles
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=("Arial", 10, "bold"), padding=6)
        style.configure("TLabel", background="#2b2b2b", foreground="white", font=("Arial", 10))
        style.configure("Header.TLabel", font=("Arial", 16, "bold"), foreground="#00ff88")
        style.configure("Status.TLabel", font=("Arial", 12, "bold"), foreground="#ffaa00")
        
        # --- UI Layout ---
        
        # Header
        header_frame = tk.Frame(root, bg="#1e1e1e", height=80)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        lbl_title = tk.Label(header_frame, text="📱 UNIVERSAL MOBILE MASTER PRO", 
                             font=("Arial", 20, "bold"), bg="#1e1e1e", fg="#00ff88")
        lbl_title.pack(pady=10)
        
        self.lbl_status = tk.Label(header_frame, text="⚪ Waiting for Device...", 
                                   font=("Arial", 12), bg="#1e1e1e", fg="#aaaaaa")
        self.lbl_status.pack()
        
        # Main Content Area
        main_frame = tk.Frame(root, bg="#2b2b2b")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left Panel: Controls
        control_frame = tk.LabelFrame(main_frame, text="Control Panel", bg="#383838", fg="white", font=("Arial", 12, "bold"))
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Connection Buttons
        btn_frame_conn = tk.Frame(control_frame, bg="#383838")
        btn_frame_conn.pack(pady=10, fill=tk.X)
        
        ttk.Button(btn_frame_conn, text="🔄 Refresh Devices", command=self.scan_devices).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame_conn, text="🔌 Force Reconnect", command=self.restart_adb).pack(fill=tk.X, pady=2)
        
        tk.Label(control_frame, text="--- Info & Backup ---", bg="#383838", fg="#888888").pack(pady=5)
        
        ttk.Button(control_frame, text="📊 Get Device Info", command=lambda: self.run_task(self.get_device_info)).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="💾 Full Backup (Media)", command=lambda: self.run_task(self.full_backup)).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="📂 Open File Manager", command=self.open_file_manager).pack(fill=tk.X, pady=2)
        
        tk.Label(control_frame, text="--- Advanced Tools ---", bg="#383838", fg="#888888").pack(pady=5)
        
        ttk.Button(control_frame, text="📸 Screen Mirror (Scrcpy)", command=self.launch_scrcpy).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="📲 Install APK", command=self.install_apk).pack(fill=tk.X, pady=2)
        
        tk.Label(control_frame, text="--- Power Options (Safe) ---", bg="#383838", fg="#888888").pack(pady=5)
        
        ttk.Button(control_frame, text="🔄 Reboot System", command=lambda: self.safe_reboot("reboot")).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="🛠️ Reboot Recovery", command=lambda: self.safe_reboot("recovery")).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="⚡ Reboot Bootloader", command=lambda: self.safe_reboot("bootloader")).pack(fill=tk.X, pady=2)
        
        # Right Panel: Console Output
        console_frame = tk.LabelFrame(main_frame, text="Live Console Output", bg="#383838", fg="white", font=("Arial", 12, "bold"))
        console_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.console = scrolledtext.ScrolledText(console_frame, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10), insertbackground='white')
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initial Scan
        self.log("System Initialized. Waiting for device connection...")
        self.scan_devices()

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console.see(tk.END)
        self.root.update_idletasks()

    def run_task(self, task_func):
        if not self.device_id:
            messagebox.showwarning("No Device", "Please connect a device and click 'Refresh Devices'.")
            return
        # Run heavy tasks in thread to keep GUI responsive
        threading.Thread(target=task_func, daemon=True).start()

    def run_adb(self, command, timeout=10):
        try:
            full_cmd = f"{self.adb_path} -s {self.device_id} {command}" if self.device_id else f"{self.adb_path} {command}"
            result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            return result.stdout.strip()
        except Exception as e:
            return f"Error: {str(e)}"

    def scan_devices(self):
        self.log("Scanning for devices...")
        output = self.run_adb("devices")
        lines = output.split('\n')[1:]
        devices = [line.split('\t')[0] for line in lines if '\tdevice' in line]
        
        if devices:
            self.device_id = devices[0]
            self.is_connected = True
            self.lbl_status.config(text=f"✅ Connected: {self.device_id}", fg="#00ff88")
            self.log(f"Device Found: {self.device_id}")
            
            # Fetch Model Name asynchronously
            threading.Thread(target=self.fetch_model_name, daemon=True).start()
        else:
            self.device_id = None
            self.is_connected = False
            self.lbl_status.config(text="❌ No Device Found", fg="#ff4444")
            self.log("No authorized device found. Check USB Debugging.")

    def fetch_model_name(self):
        model = self.run_adb("shell getprop ro.product.model")
        brand = self.run_adb("shell getprop ro.product.manufacturer")
        if model:
            self.lbl_status.config(text=f"✅ {brand} {model} ({self.device_id})", fg="#00ff88")

    def restart_adb(self):
        self.log("Restarting ADB Server...")
        subprocess.run(f"{self.adb_path} kill-server", shell=True)
        time.sleep(1)
        subprocess.run(f"{self.adb_path} start-server", shell=True)
        time.sleep(2)
        self.scan_devices()

    def get_device_info(self):
        self.log("Fetching detailed system info...")
        info_map = [
            ("Brand", "getprop ro.product.manufacturer"),
            ("Model", "getprop ro.product.model"),
            ("Android Ver", "getprop ro.build.version.release"),
            ("SDK Level", "getprop ro.build.version.sdk"),
            ("Battery %", "dumpsys battery | grep level | awk '{print $2}'"),
            ("CPU Arch", "getprop ro.product.cpu.abi"),
        ]
        
        details = ""
        for label, cmd in info_map:
            val = self.run_adb(f"shell {cmd}")
            details += f"{label}: {val}\n"
        
        storage = self.run_adb("shell df -h /data | tail -n 1 | awk '{print $4}'")
        details += f"Free Storage: {storage}\n"
        
        self.log("--- Device Info ---\n" + details)
        messagebox.showinfo("Device Information", details)

    def full_backup(self):
        if not messagebox.askyesno("Confirm Backup", "Start full media backup? This may take time."):
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = f"Backup_{self.device_id}_{timestamp}"
        os.makedirs(backup_folder, exist_ok=True)
        
        self.log(f"Starting backup to folder: {backup_folder}")
        
        dirs_to_pull = ["/sdcard/DCIM", "/sdcard/Pictures", "/sdcard/Download", "/sdcard/Music"]
        
        for d in dirs_to_pull:
            self.log(f"Pulling {d}...")
            # Use -a to preserve attributes, handle errors gracefully
            cmd = f"{self.adb_path} -s {self.device_id} pull -a {d} {backup_folder}/"
            subprocess.run(cmd, shell=True)
            
        self.log("✅ Backup Completed Successfully!")
        messagebox.showinfo("Success", f"Backup saved in:\n{os.path.abspath(backup_folder)}")

    def safe_reboot(self, mode):
        modes = {"reboot": "Normal System", "recovery": "Recovery Mode", "bootloader": "Fastboot/Bootloader"}
        warn_msg = f"Are you sure you want to reboot to {modes[mode]}?\n\n⚠️ If your cable is loose or drivers missing, you might lose connection!"
        
        if messagebox.askyesno("Confirm Reboot", warn_msg):
            self.log(f"Rebooting to {mode}...")
            self.run_adb(f"reboot {mode}")
            self.device_id = None
            self.lbl_status.config(text="⏳ Device Rebooting...", fg="#ffaa00")
            self.log("Device disconnected. Waiting for it to come back online...")
            # Auto refresh after 30 seconds
            self.root.after(30000, self.scan_devices)

    def launch_scrcpy(self):
        self.log("Launching Screen Mirroring (Scrcpy)...")
        if not shutil.which("scrcpy"):
            messagebox.showerror("Missing Tool", "Scrcpy is not installed.\nRun: sudo apt install scrcpy")
            return
        subprocess.Popen(["scrcpy"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def install_apk(self):
        filename = filedialog.askopenfilename(filetypes=[("APK Files", "*.apk")])
        if filename:
            self.log(f"Installing {filename}...")
            output = self.run_adb(f"install \"{filename}\"")
            self.log(output)
            if "Success" in output:
                messagebox.showinfo("Success", "App Installed Successfully!")
            else:
                messagebox.showerror("Failed", f"Installation Failed:\n{output}")

    def open_file_manager(self):
        # Simple popup for file management logic could be added here
        # For now, opening a simple dialog to pull/push
        self.log("Opening File Manager interface...")
        fm_win = tk.Toplevel(self.root)
        fm_win.title("Simple File Manager")
        fm_win.geometry("400x300")
        
        tk.Label(fm_win, text=f"Managing: {self.device_id}", font=("Arial", 12, "bold")).pack(pady=10)
        
        def pull_file():
            remote = entry_remote.get()
            if remote:
                self.run_adb(f"pull {remote} ./")
                self.log(f"Pulled {remote} to current folder")
                messagebox.showinfo("Done", "File downloaded to script folder")
        
        def push_file():
            local = filedialog.askopenfilename()
            if local:
                self.run_adb(f"push \"{local}\" /sdcard/Download/")
                self.log(f"Pushed {local} to /sdcard/Download/")
                messagebox.showinfo("Done", "File uploaded to Download folder")

        tk.Label(fm_win, text="Remote Path (e.g., /sdcard/photo.jpg):").pack()
        entry_remote = tk.Entry(fm_win, width=40)
        entry_remote.pack(pady=5)
        
        tk.Button(fm_win, text="⬇️ Download to PC", command=pull_file, bg="#dddddd").pack(pady=5)
        tk.Button(fm_win, text="⬆️ Upload from PC", command=push_file, bg="#dddddd").pack(pady=5)
        tk.Button(fm_win, text="Close", command=fm_win.destroy).pack(pady=20)

if __name__ == "__main__":
    # Check ADB existence
    if not shutil.which("adb"):
        print("ADB not found! Installing...")
        os.system("sudo apt update && sudo apt install android-tools-adb android-tools-fastboot -y")
    
    root = tk.Tk()
    app = UniversalMobileMaster(root)
    root.mainloop()
