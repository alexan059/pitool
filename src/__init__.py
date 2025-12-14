#!/usr/bin/env python3

import sys
import subprocess
import argparse
import os

def main():
    """Main CLI entry point for Pi automation tools"""
    parser = argparse.ArgumentParser(description="Pi automation CLI tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Image creation command
    image_parser = subparsers.add_parser('image', help='Create Raspberry Pi SD card images')
    image_parser.add_argument('--keep-scripts', action='store_true', help='Keep generated scripts after flashing')
    image_parser.add_argument('--dry-run', action='store_true', help='Download image and generate bootstrap script only')
    image_parser.add_argument('--with-ansible', action='store_true', help='Include Ansible installation in bootstrap script')
    image_parser.add_argument('action', nargs='?', choices=['clean'], help='Optional action (e.g., clean)')
    
    # Network monitoring command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor Pi connectivity')
    monitor_parser.add_argument('host', help='Hostname or IP address of the Pi')
    monitor_parser.add_argument('--interval', type=int, default=5, help='Ping interval in seconds')
    monitor_parser.add_argument('--clean', action='store_true', help='Clean known_hosts entries')
    
    # Certificate trust command
    trust_parser = subparsers.add_parser('trust', help='Download and trust Pi certificates')
    trust_parser.add_argument('host', help='Hostname or IP address of the Pi')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Get the project root directory (parent of tools directory)
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(tools_dir)
    
    if args.command == 'image':
        tool_path = os.path.join(tools_dir, 'imaging', 'create_image.py')
        cmd = ['python3', tool_path]

        if args.keep_scripts:
            cmd.append('--keep-scripts')
        if args.dry_run:
            cmd.append('--dry-run')
        if args.with_ansible:
            cmd.append('--with-ansible')
        if args.action:
            cmd.append(args.action)
            
    elif args.command == 'monitor':
        tool_path = os.path.join(tools_dir, 'networking', 'pi_tool.py')
        cmd = ['python3', tool_path, args.host]
        
        if args.interval != 5:
            cmd.extend(['--interval', str(args.interval)])
        if args.clean:
            cmd.append('--clean')
            
    elif args.command == 'trust':
        tool_path = os.path.join(tools_dir, 'networking', 'cert_trust.py')
        cmd = ['python3', tool_path, args.host]
    
    # Change to project root before executing (for relative paths in tools)
    original_cwd = os.getcwd()
    os.chdir(project_root)
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    finally:
        os.chdir(original_cwd)