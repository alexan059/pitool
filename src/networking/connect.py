import os
import subprocess
import time

from src.console import console


def wait_for_pi(hostname: str):
    """Ping hostname until it responds or timeout"""

    with console.status(
        f"[green]Waiting for {hostname} to come online...[/green]",
        spinner="bouncingBall",
    ):
        while True:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "1", f"{hostname}.local"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                break
            time.sleep(0.5)  # Small delay to avoid rapid-fire on instant failures


def connect_to_pi(user: str, hostname: str):
    """SSH to user@hostname"""

    # Remove old host key if it exists
    subprocess.run(
        ["ssh-keygen", "-R", f"{hostname}"], capture_output=True, check=False
    )

    # Connect with auto-accept new key
    os.execvp(
        "ssh", ["ssh", "-o", "StrictHostKeyChecking=accept-new", f"{user}@{hostname}"]
    )
