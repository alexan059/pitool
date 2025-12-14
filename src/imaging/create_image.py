#!/usr/bin/env python3

import urllib.request
import subprocess
import argparse
import json
import sys
import re
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import load_env

def hash_password(password):
    try:
        result = subprocess.run(
            ["openssl", "passwd", "-6", password],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f'[Error] Password hashing failed: {e}')
        exit(1)

def load_config():
    load_env()

    keys = ["WIFI_SSID", "WIFI_PASSWORD", "COUNTRY_CODE", "HOSTNAME", "OP_ITEM_VAULT", "OP_ITEM_ID", "RPI_IMAGE", "PI_USER", "PI_PASSWORD", "TIMEZONE"]
    config = {k: os.environ.get(k, "") for k in keys}

    config["PI_PASSWORD"] = hash_password(config["PI_PASSWORD"])

    try:
        command = ["op", "read", f'op://{config["OP_ITEM_VAULT"]}/{config["OP_ITEM_ID"]}/public key']
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f'[Warning] 1Password CLI error: {result.stderr}')
            config["SSH_PUBLIC_KEY"] = ""
        else:
            config["SSH_PUBLIC_KEY"] = result.stdout.strip()
    except subprocess.CalledProcessError:
        config["SSH_PUBLIC_KEY"] = ""

    return config

def select_sd_card():
    result = subprocess.run(
        ["diskutil", "list"],
        capture_output=True,
        text=True,
        check=True
    )
    lines = result.stdout.splitlines()
    disks = []
    for line in lines:
        if "external, physical" in line:
            parts = line.strip().split()
            if parts:
                disk_id = parts[0]
                info = subprocess.run(["diskutil", "info", disk_id], capture_output=True, text=True)
                if re.search(r"Protocol:\s+.*USB", info.stdout):
                    disks.append(disk_id)

    if not disks:
        print("[Error] No external USB disks found.")
        exit(1)

    print("Available USB disks:")
    for i, disk in enumerate(disks, 1):
        print(f"{i}. {disk}")

    try:
        index = int(input("Select disk number to use: ")) - 1
        selected = disks[index]
    except (ValueError, IndexError):
        print("[Error] Invalid selection.")
        exit(1)

    confirm = input(f'You selected {selected}. Continue? (y/n): ').strip().lower()
    if confirm != "y":
        exit(1)

    return selected

def find_raspios_url(image, json_url = "https://downloads.raspberrypi.org/os_list_imagingutility_v3.json"):
    with urllib.request.urlopen(json_url) as response:
        data = json.load(response)

    for os_entry in data.get("os_list", []):
        subitems = os_entry.get("subitems", [])
        for item in subitems:
            url = item.get("url", "")
            if image in url:
                return url

    print(f'[Error] No URL found for image: {image}')
    exit(1)

def download_raspios(url):
    filename = url.split("/")[-1]
    image_dir = os.path.join(os.getcwd(), ".rpi")
    os.makedirs(image_dir, exist_ok=True)
    image_path = os.path.join(image_dir, filename)

    if os.path.exists(image_path):
        print("[Info] Image already downloaded.")
        return image_path

    def show_progress(count, block_size, total_size):
        percent = int(count * block_size * 100 / total_size)
        sys.stdout.write(f'\rDownloading {filename}... {percent}%')
        sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, image_path, reporthook=show_progress)
        print()
    except Exception as e:
        print(f'\n[Error] Failed to download image: {e}')
        exit(1)

    return image_path

def generate_bootstrap_script(config, with_ansible=False):
    template_path = os.path.join(os.getcwd(), "templates", "bootstrap.sh.template")

    with open(template_path, "r") as f:
        content = f.read()

    # Add Ansible installation if requested
    config["ANSIBLE_INSTALL"] = "apt -y install ansible" if with_ansible else ""

    for key, value in config.items():
        placeholder = f'{{%{key}%}}'
        content = content.replace(placeholder, value)

    return content

def generate_firstrun_script(config, bootstrap_script=False, with_ansible=False):
    template_path = os.path.join(os.getcwd(), "templates", "firstrun.sh.template")
    output_path = os.path.join(os.getcwd(), ".rpi", "firstrun.sh")

    config["BOOTSTRAP_SCRIPT"] = generate_bootstrap_script(config, with_ansible) if bootstrap_script else ""

    with open(template_path, "r") as f:
        content = f.read()

    for key, value in config.items():
        placeholder = f'{{%{key}%}}'
        content = content.replace(placeholder, value)

    with open(output_path, "w") as f:
        f.write(content)

    os.chmod(output_path, 0o755)
    return output_path

def cleanup_firstrun_script(debug=False):
    path = os.path.join(os.getcwd(), ".rpi", "firstrun.sh")
    if os.path.exists(path):
        if debug:
            print(f'[DEBUG] Skipping deletion of: {path}')
        else:
            os.remove(path)

def run_rpi_imager(image_path, device_path, script_path):
    try:
        cmd = [
            "rpi-imager", "--cli",
            "--first-run-script", script_path,
            image_path, device_path
        ]

        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f'[Error] rpi-imager failed: {e}')
        exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep-scripts", action="store_true", help="keep generated scripts after flashing")
    parser.add_argument("--dry-run", action="store_true", help="download image and generate bootstrap script only")
    parser.add_argument("--with-ansible", action="store_true", help="include Ansible installation in bootstrap script")
    parser.add_argument("command", nargs="?", choices=["clean"], help="optional command (e.g., 'clean')")

    args = parser.parse_args()

    if args.command == "clean":
        print("[Success] Cleaned up first run script")
        cleanup_firstrun_script(debug=args.keep_scripts)
        return

    # Default: create image flow
    keep_scripts = args.keep_scripts
    dry_run = args.dry_run
    with_ansible = args.with_ansible

    config = load_config()
    device_path = None if dry_run else select_sd_card()
    image_url = find_raspios_url(config["RPI_IMAGE"])
    image_path = download_raspios(image_url)
    script_path = generate_firstrun_script(config, True, with_ansible)

    if dry_run:
        print("[Success] Only downloaded image and created scripts")
        return

    run_rpi_imager(image_path, device_path, script_path)

    cleanup_firstrun_script(debug=keep_scripts)

if __name__ == "__main__":
    main()
