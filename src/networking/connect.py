import os
import shutil
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

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
        "ssh",
        ["ssh", "-o", "StrictHostKeyChecking=accept-new", f"{user}@{hostname}.local"],
    )


@contextmanager
def download_from_pi(user: str, hostname: str, remote_path: str):
    """Download file from Pi via SCP, auto-cleanup after use

    Args:
        user: SSH username
        hostname: Pi hostname or IP
        remote_path: Remote file path on Pi

    Yields:
        Path: Local path to downloaded file

    Example:
        with download_from_pi("john", "pi", "~/.ssh/id_rsa.pub") as cert_path:
            process_file(cert_path)
    """
    temp_dir = tempfile.mkdtemp(prefix="pitool_")
    filename = Path(remote_path).name
    local_path = Path(temp_dir) / filename

    try:
        console.print(f"[cyan]Downloading {remote_path} from {hostname}...[/cyan]")

        subprocess.run(
            ["scp", f"{user}@{hostname}:{remote_path}", str(local_path)],
            check=True,
            capture_output=True,
        )

        console.print(f"[green]✓[/green] Downloaded to {local_path}")

        yield local_path

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else "Unknown error"
        raise RuntimeError(
            f"Failed to download from {hostname}.local:{remote_path}\n{error_msg}"
        ) from None

    finally:
        # Cleanup temp dir
        shutil.rmtree(temp_dir, ignore_errors=True)
