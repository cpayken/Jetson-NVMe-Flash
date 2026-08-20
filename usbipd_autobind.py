import subprocess
import re
import time
from datetime import datetime

# NVIDIA Vendor ID
VENDOR_ID = "0955"

print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting USBIPD Auto-Bind Monitor...")
print(f"Scanning for NVIDIA devices (Vendor ID: {VENDOR_ID})...\n")

last_seen_state = {}

while True:
    try:
        # Run usbipd list
        result = subprocess.run(["usbipd", "list"], capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        
        found_nvidia = False
        
        for line in lines:
            if VENDOR_ID in line:
                found_nvidia = True
                # Extract Bus ID (e.g., '2-6')
                match = re.search(r'^\s*(\d+-\d+)', line)
                if match:
                    bus_id = match.group(1)
                    is_shared = "Shared" in line or "Attached" in line
                    
                    # Print log only if status changed or device was just detected
                    if bus_id not in last_seen_state or last_seen_state[bus_id] != is_shared:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        
                        if not is_shared:
                            print(f"[{timestamp}] DETECTED: Unbound device on Bus {bus_id}. Binding now...")
                            bind_res = subprocess.run(
                                ["usbipd", "bind", "--busid", bus_id, "--force"],
                                capture_output=True,
                                text=True
                            )
                            if bind_res.returncode == 0:
                                print(f"[{timestamp}] SUCCESS: Bus {bus_id} bound to usbipd.")
                                last_seen_state[bus_id] = True
                            else:
                                print(f"[{timestamp}] ERROR: Failed to bind Bus {bus_id}: {bind_res.stderr.strip()}")
                        else:
                            print(f"[{timestamp}] STATUS: Bus {bus_id} is already shared/bound.")
                            last_seen_state[bus_id] = True

        if not found_nvidia and last_seen_state:
            # Device disconnected / reset completely
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] NOTICE: NVIDIA USB device disconnected / reset.")
            last_seen_state.clear()

    except FileNotFoundError:
        print("Error: 'usbipd' executable not found in PATH. Ensure usbipd-win is installed.")
        break
    except Exception as e:
        print(f"Unexpected error: {e}")

    time.sleep(1)
