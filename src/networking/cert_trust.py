#!/usr/bin/env python3

import os
import sys
import subprocess
import tempfile
import argparse
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import load_env

def get_pi_user():
    """Get PI_USER from environment variable"""
    pi_user = os.environ.get('PI_USER')
    if not pi_user:
        print("[Error] PI_USER environment variable not set", file=sys.stderr)
        sys.exit(1)
    return pi_user

def download_root_ca(host, pi_user):
    """Download mkcert root CA from Pi using scp"""
    print(f"[Info] Downloading mkcert root CA from {host}...")

    # Create temporary directory for root CA
    temp_dir = tempfile.mkdtemp(prefix="pi_rootca_")
    root_ca_path = f"{pi_user}@{host}:~/.local/share/mkcert/rootCA.pem"
    local_ca_path = os.path.join(temp_dir, "rootCA.pem")

    try:
        # Download root CA using scp
        result = subprocess.run([
            'scp', root_ca_path, local_ca_path
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"[Error] Downloading root CA: {result.stderr}", file=sys.stderr)
            return None

        print(f"[Success] Root CA downloaded to: {local_ca_path}")
        return local_ca_path

    except Exception as e:
        print(f"[Error] Downloading root CA: {e}", file=sys.stderr)
        return None

def trust_root_ca(root_ca_path):
    """Trust mkcert root CA"""
    if not root_ca_path or not os.path.exists(root_ca_path):
        print("[Error] Root CA file not found", file=sys.stderr)
        return False

    print("[Info] Installing mkcert root CA...")

    # Try to add to system keychain first (requires sudo)
    print("[Info] Attempting to add root CA to system keychain (may require password)...")
    result = subprocess.run([
        'sudo', 'security', 'add-trusted-cert', '-d', '-r', 'trustRoot',
        '-k', '/Library/Keychains/System.keychain', root_ca_path
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("[Success] Root CA added to system keychain")
        return True
    else:
        print(f"[Warning] Could not add to system keychain: {result.stderr}")

        # Try user keychain as fallback
        print("[Info] Trying user keychain instead...")
        result = subprocess.run([
            'security', 'add-trusted-cert', '-d', '-r', 'trustRoot', root_ca_path
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("[Success] Root CA added to user keychain")
            return True
        else:
            print(f"[Error] Could not add root CA to keychain: {result.stderr}")
            return False

def cleanup_temp_file(file_path):
    """Clean up temporary root CA file"""
    if file_path and os.path.exists(file_path):
        temp_dir = os.path.dirname(file_path)
        import shutil
        shutil.rmtree(temp_dir)
        print(f"[Info] Cleaned up temporary file: {file_path}")

def main():
    load_env()

    parser = argparse.ArgumentParser(description="Download and trust Pi mkcert root CA")
    parser.add_argument("host", help="Hostname or IP address of the Pi")
    parser.add_argument("--keep", action="store_true", help="Keep downloaded root CA file (don't delete)")
    args = parser.parse_args()

    host = args.host
    pi_user = get_pi_user()

    print(f"[Info] Downloading and trusting mkcert root CA from {host} (user: {pi_user})")

    # Download root CA
    root_ca_path = download_root_ca(host, pi_user)
    if not root_ca_path:
        sys.exit(1)

    try:
        # Trust root CA
        if trust_root_ca(root_ca_path):
            print("[Success] Root CA successfully downloaded and trusted")
            print("[Info] Please restart your browser to see the changes")
        else:
            print("[Error] Failed to trust root CA")
            sys.exit(1)
    finally:
        # Clean up unless --keep flag is used
        if not args.keep:
            cleanup_temp_file(root_ca_path)

if __name__ == "__main__":
    main()
