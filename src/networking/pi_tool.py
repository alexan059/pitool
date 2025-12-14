#!/usr/bin/env python3

import os
import time
import subprocess
import argparse

def is_online(host):
    return os.system(f"ping -c 1 {host} > /dev/null 2>&1") == 0

def play_sound():
    subprocess.run(["afplay", "/System/Library/Sounds/Ping.aiff"])

def clean_known_hosts(host):
    home_dir = os.path.expanduser("~")
    auth_keys_path = os.path.join(home_dir, ".ssh", "known_hosts")

    if not os.path.exists(auth_keys_path):
        print(f'[Warning] known_hosts file does not exist: {auth_keys_path}')
        return

    with open(auth_keys_path, "r") as f:
        lines = f.readlines()

    filtered_lines = [line for line in lines if host not in line]

    with open(auth_keys_path, "w") as f:
        f.writelines(filtered_lines)

    print(f"[Success] Cleaned known_hosts: removed lines containing '{host}'.")

def main():
    parser = argparse.ArgumentParser(description="Play a sound when a host (e.g. Raspberry Pi) comes online.")
    parser.add_argument("host", help="Hostname or IP address of the Raspberry Pi (e.g., raspberrypi.local)")
    parser.add_argument("--interval", type=int, default=5, help="Ping interval in seconds (default: 5)")
    parser.add_argument("--clean", action="store_true", help="Clean known_hosts of entries containing the host")
    args = parser.parse_args()

    host = args.host
    interval = args.interval

    if args.clean:
        clean_known_hosts(host)
        exit(0)

    print(f"Pinging {host} every {interval}s...")

    while True:
        if is_online(host):
            print(f"[Success] {host} is online!")
            play_sound()
            break
        else:
            print(f"[Info] Waiting for {host}...")
        time.sleep(interval)

if __name__ == "__main__":
    main()
