#!/usr/bin/env python3
import subprocess
import os
import sys
import time
import platform
import json
import shutil
from datetime import datetime
from pathlib import Path

# Configuration
IS_WINDOWS = platform.system() == 'Windows'
BACKUP_DIR = "Mobile_Backups"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    print(f"{Colors.OKCYAN}")
    print(r"""
    _   _                      ____  _             _   
   | \ | | __ _ _ __ _ __     / ___|(_)_ __ ___ __| |_ 
   |  \| |/ _` | '__| '_ \   | |   _| | '__/ __/ _` __|
   | |\  | (_| | |  | | | |  | |_| || | | | (_| (_| |_ 
   |_| \_|\__,_|_|  |_| |_|   \____|_|_|  \___\__,_(__|
                                                       
    """)
    print(f"{Colors.ENDC}{Colors.BOLD}--- Advanced Android Device Manager & Backup Suite ---{Colors.ENDC}\n")

def run_adb_command(command, timeout=30):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return ""
    except Exception as e:
        return ""

def check_dependencies():
    if not IS_WINDOWS:
        if os.geteuid() != 0:
            print(f"{Colors.FAIL}[!] Warning: Run with 'sudo' on Linux for best results!{Colors.ENDC}")
        print(f"{Colors.OKBLUE}[*] Checking dependencies...{Colors.ENDC}")
        deps = ['adb', 'fastboot']
        for dep in deps:
            if not shutil.which(dep):
                print(f"[!] {dep} not found. Please install android-tools-adb.")
                if os.geteuid() == 0:
                    print(f"[*] Installing {dep}...")
                    subprocess.run(['apt', 'install', '-y', 'android-tools-adb', 'android-tools-fastboot'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        if not shutil.which('adb'):
            print(f"{Colors.FAIL}[!] ADB not found. Please install ADB for Windows.{Colors.ENDC}")
            sys.exit(1)

def get_connected_devices():
    output = run_adb_command("adb devices")
    lines = output.split('\n')[1:]
    devices = []
    for line in lines:
        if '\tdevice' in line:
            devices.append(line.split('\t')[0])
    return devices

def get_device_info(device_id):
    cmd_prefix = f"adb -s {device_id}"
    info = {
        "model": run_adb_command(f"{cmd_prefix} shell getprop ro.product.model"),
        "brand": run_adb_command(f"{cmd_prefix} shell getprop ro.product.manufacturer"),
        "android": run_adb_command(f"{cmd_prefix} shell getprop ro.build.version.release"),
        "sdk": run_adb_command(f"{cmd_prefix} shell getprop ro.build.version.sdk"),
        "serial": run_adb_command(f"{cmd_prefix} get-serialno"),
        "battery": run_adb_command(f"{cmd_prefix} shell dumpsys battery | grep level | awk '{{print $2}}'"),
        "storage": run_adb_command(f"{cmd_prefix} shell df -h /data | tail -n 1 | awk '{{print $4}}'"),
    }
    return info

def full_backup(device_id):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"{device_id}_{timestamp}")
    os.makedirs(backup_path, exist_ok=True)
    
    print(f"\n{Colors.OKGREEN}[*] Starting Full Backup for {device_id}...{Colors.ENDC}")
    
    # Backup Apps List
    print("[*] Backing up installed apps list...")
    apps = run_adb_command(f"adb -s {device_id} shell pm list packages -3")
    with open(os.path.join(backup_path, "installed_apps.txt"), "w") as f:
        f.write(apps)
    
    # Backup Media
    print("[*] Backing up Media files (DCIM, Pictures, Music, Download)...")
    media_dirs = ["/sdcard/DCIM", "/sdcard/Pictures", "/sdcard/Music", "/sdcard/Download"]
    for mdir in media_dirs:
        safe_dir = mdir.replace("/", "_").replace("sdcard_", "")
        target_dir = os.path.join(backup_path, safe_dir)
        os.makedirs(target_dir, exist_ok=True)
        run_adb_command(f"adb -s {device_id} pull {mdir} {target_dir}")
    
    print(f"{Colors.OKGREEN}[+] Backup saved to: {backup_path}{Colors.ENDC}")

def restore_backup(device_id):
    print(f"\n{Colors.WARNING}Available Backups:{Colors.ENDC}")
    if not os.path.exists(BACKUP_DIR):
        print("[-] No backups found.")
        return
    
    backups = [d for d in os.listdir(BACKUP_DIR) if os.path.isdir(os.path.join(BACKUP_DIR, d))]
    if not backups:
        print("[-] No backups found.")
        return

    for i, b in enumerate(backups):
        print(f"[{i+1}] {b}")
    
    try:
        choice = int(input("Select backup number to restore: ")) - 1
        if 0 <= choice < len(backups):
            selected_backup = os.path.join(BACKUP_DIR, backups[choice])
            print(f"[*] Restoring from {selected_backup}...")
            
            for item in os.listdir(selected_backup):
                if item != "installed_apps.txt":
                    src = os.path.join(selected_backup, item)
                    print(f"[*] Pushing {item} to /sdcard/...")
                    run_adb_command(f"adb -s {device_id} push {src} /sdcard/")
            
            print(f"{Colors.OKGREEN}[+] Restore completed (Files placed in /sdcard/).{Colors.ENDC}")
        else:
            print("[-] Invalid selection.")
    except ValueError:
        print("[-] Invalid input.")

def file_explorer(device_id):
    current_path = "/sdcard"
    while True:
        print(f"\n📂 Path: {current_path}")
        output = run_adb_command(f"adb -s {device_id} shell ls -l {current_path}")
        print(output if output else "[-] Empty or Access Denied")
        print("\n[1] Open Folder  [2] Go Back  [3] Upload File  [4] Download File  [5] Exit")
        choice = input("Option: ")
        
        if choice == '1':
            fname = input("Folder Name: ")
            current_path = f"{current_path}/{fname}"
        elif choice == '2':
            parts = current_path.split("/")
            if len(parts) > 2:
                current_path = "/".join(parts[:-1])
            else:
                current_path = "/sdcard"
        elif choice == '3':
            lfile = input("Local File Path: ")
            if os.path.exists(lfile):
                run_adb_command(f"adb -s {device_id} push \"{lfile}\" \"{current_path}/\"")
                print("[+] Uploaded.")
            else:
                print("[-] File not found locally.")
        elif choice == '4':
            rfile = input("Remote File/Folder Name: ")
            run_adb_command(f"adb -s {device_id} pull \"{current_path}/{rfile}\"")
            print("[+] Downloaded.")
        elif choice == '5':
            break

def main():
    print_banner()
    check_dependencies()
    
    print("[*] Starting ADB Server...")
    run_adb_command("adb start-server")
    time.sleep(1)
    
    devices = get_connected_devices()
    if not devices:
        print(f"{Colors.FAIL}[!] No device connected. Enable USB Debugging and connect cable.{Colors.ENDC}")
        sys.exit(1)
    
    print(f"{Colors.OKGREEN}[+] {len(devices)} Device(s) found.{Colors.ENDC}")
    
    device = devices[0]
    if len(devices) > 1:
        print("Multiple devices found. Select one:")
        for i, d in enumerate(devices):
            info = get_device_info(d)
            print(f"[{i+1}] {d} ({info['brand']} {info['model']})")
        try:
            idx = int(input("Choice: ")) - 1
            if 0 <= idx < len(devices):
                device = devices[idx]
        except:
            pass
            
    info = get_device_info(device)
    print(f"\n{Colors.BOLD}Connected: {info['brand']} {info['model']} (Android {info['android']}){Colors.ENDC}")
    
    while True:
        print("\n" + "="*40)
        print("  🚀 UNIVERSAL MOBILE MASTER MENU")
        print("="*40)
        print("1. Detailed System Info")
        print("2. Full Backup (Media + Apps)")
        print("3. Restore from Backup")
        print("4. File Manager")
        print("5. Install APK")
        print("6. Screen Mirroring (Scrcpy)")
        print("7. Reboot Options")
        print("8. Exit")
        
        ch = input("\nChoice: ")
        
        if ch == '1':
            print(f"\nBrand: {info['brand']}\nModel: {info['model']}\nAndroid: {info['android']}\nSDK: {info['sdk']}\nBattery: {info['battery']}%\nFree Storage: {info['storage']}")
        elif ch == '2':
            full_backup(device)
        elif ch == '3':
            restore_backup(device)
        elif ch == '4':
            file_explorer(device)
        elif ch == '5':
            apk = input("APK Path: ")
            if os.path.exists(apk):
                print(run_adb_command(f"adb -s {device} install \"{apk}\""))
            else:
                print("[-] APK file not found.")
        elif ch == '6':
            print("[*] Launching Scrcpy... (Close window to return)")
            subprocess.run(["scrcpy"])
        elif ch == '7':
            print("1. Normal  2. Recovery  3. Bootloader")
            rch = input("Reboot Type: ")
            if rch == '1': run_adb_command(f"adb -s {device} reboot")
            elif rch == '2': run_adb_command(f"adb -s {device} reboot recovery")
            elif rch == '3': run_adb_command(f"adb -s {device} reboot bootloader")
        elif ch == '8':
            print("Exiting... Khuda Hafiz!")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
