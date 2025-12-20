import hashlib
import re
import subprocess
from pathlib import Path

from InquirerPy import inquirer
from rich.panel import Panel
from rich.progress import Progress

from src.console import console
from src.platform.base import PlatformHandler
from src.platform.models import ExternalDevice
from src.utils import calculate_hash


def _get_device_info(device: str) -> ExternalDevice:
    disk = subprocess.run(["diskutil", "info", device], capture_output=True, text=True)
    text = disk.stdout

    patterns = {
        "id": r"Device Identifier:\s+(.+)",
        "node": r"Device Node:\s+(.+)",
        "name": r"Device / Media Name:\s+(.+)",
        "size": r"Disk Size:\s+([0-9.]+ [A-Z]+)",
        "protocol": r"Protocol:\s+(.+)",
        "location": r"Device Location:\s+(.+)",
    }

    info = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            info[key] = match.group(1).strip()

    return ExternalDevice(
        id=info.get("id"),
        node=info.get("node"),
        name=info.get("name"),
        size=info.get("size"),
        protocol=info.get("protocol"),
        location=info.get("location"),
    )


def _hash_device(device_path: str, size: int) -> str:
    with Progress() as progress:
        task = progress.add_task("[yellow]Hashing device...[/yellow]", total=size)

        hasher = hashlib.sha256()
        bytes_read = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        # Use sudo dd to read device, NO count parameter
        proc = subprocess.Popen(
            ["sudo", "dd", f"if={device_path}", "bs=1m", "status=none"],
            stdout=subprocess.PIPE,
        )

        # Read EXACTLY size bytes from stdout
        while bytes_read < size:
            to_read = min(chunk_size, size - bytes_read)
            chunk = proc.stdout.read(to_read)
            if not chunk:
                break
            hasher.update(chunk)
            bytes_read += len(chunk)
            progress.update(task, advance=len(chunk))

        # Terminate dd (we got what we needed)
        proc.terminate()
        proc.wait()

        return hasher.hexdigest()


def _verify_flashed_device(image_path: str, device_id: str):
    """Verify flashed image matches source by comparing hashes"""

    console.print("[cyan]Verifying flashed image on device...[/cyan]")

    image_size = Path(image_path).stat().st_size
    raw_device = device_id.replace("/dev/disk", "/dev/rdisk")

    source_hash = calculate_hash(
        image_path, text="[yellow]Calculating image hash...[/yellow]"
    )
    device_hash = _hash_device(raw_device, image_size)

    return source_hash == device_hash


class MacOSPlatform(PlatformHandler):
    def list_external_devices(self) -> list[ExternalDevice]:
        result = subprocess.run(
            ["diskutil", "list"], capture_output=True, text=True, check=True
        )

        lines = result.stdout.splitlines()
        disks = []

        for line in lines:
            if "external, physical" not in line:
                continue

            device, *_ = line.strip().split()
            external_device = _get_device_info(device)

            if (
                external_device.protocol != "USB"
                or external_device.location != "External"
            ):
                continue

            disks.append(external_device)

        return disks

    def _require_external_device(self, device_id: str):
        """Guard against non-external devices"""

        # Never allow disk0 (system disk)
        if "disk0" in device_id:
            raise ValueError("Refusing to write to disk0 (system disk)")

        # Verify it's an external device
        devices = self.list_external_devices()
        valid_nodes = [d.node for d in devices]

        if device_id not in valid_nodes:
            raise ValueError(f"Device {device_id} is not a external device")

    def unmount_device(self, device_id: str) -> None:
        self._require_external_device(device_id)

        console.print(f"[cyan]Unmounting {device_id}...[/cyan]")

        try:
            subprocess.run(
                ["diskutil", "unmountDisk", device_id],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to unmount device: {device_id}: {e.stderr}"
            ) from None

        console.print("[green]✓[/green] Device unmounted")

    def flash_image(
        self, image_path: str, device_id: str, verify: bool = False
    ) -> None:
        """Flash image to device with safety checks"""

        self._require_external_device(device_id)

        # Verify image exists
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image does not exist: {image_path}")

        # Verify it's a disk image
        file_check = subprocess.run(
            ["file", image_path], capture_output=True, text=True
        )
        if (
            "DOS/MBR boot sector" not in file_check.stdout
            and "block special" not in file_check.stdout
        ):
            raise ValueError(
                "File doesn't appear to be a disk image: {file_check.stdout}"
            )

        image_resolved_path = Path(image_path)
        devices = self.list_external_devices()
        device_info = next((d for d in devices if d.node == device_id), None)

        console.print(
            Panel(
                f"[bold]This will erase all data on:[/bold]\n"
                f"  Device: [red]{device_id}[/red]\n"
                f"  Name: {device_info.name if device_info else 'Unknown'}\n"
                f"  Size: {device_info.size if device_info else 'Unknown'}\n"
                f"  Image: {image_resolved_path.name}\n",
                title="WARNING",
                border_style="yellow",
            )
        )

        confirmed = inquirer.confirm(
            message="Are you sure you want to continue?", default=False
        ).execute()

        if not confirmed:
            console.print("[yellow]Cancelled by user[/yellow]")
            return

        self.unmount_device(device_id)

        # convert to raw device for faster write speed
        raw_device = device_id.replace("/dev/disk", "/dev/rdisk")

        console.print(
            f"[yellow]Flashing {image_resolved_path.name} to {device_id}...[/yellow]"
        )

        total_size = image_resolved_path.stat().st_size

        with Progress() as progress:
            task = progress.add_task("[cyan]Flashing image...", total=total_size)
            proc = subprocess.Popen(
                [
                    "sudo",
                    "/bin/dd",
                    f"if={str(image_resolved_path.resolve())}",
                    f"of={raw_device}",
                    "bs=1m",
                    "status=progress",
                ],
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            for line in proc.stderr:
                match = re.search(r"(\d+) bytes", line)
                if match:
                    bytes_written = int(match.group(1))
                    progress.update(task, completed=bytes_written)

            proc.wait()

            if proc.returncode != 0:
                raise RuntimeError("Failed to flash image")

        console.print("[green]✓ Image flashed successfully[/green]")

        # TODO: not working
        # if verify and not _verify_flashed_device(image_path, device_id):
        #     raise RuntimeError(
        #         "Verification failed! Flashed image doesn't match source"
        #     )
        #
        # console.print("[green]✓ Image verified successfully[/green]")

    def mount_boot_partition(self, device_id: str) -> str:
        console.print(f"[cyan]Looking for boot partition on {device_id}...[/cyan]")

        try:
            result = subprocess.run(
                ["diskutil", "mountDisk", device_id],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            raise RuntimeError("Failed to mount boot partition") from None

        try:
            result = subprocess.run(
                ["diskutil", "list", device_id],
                capture_output=True,
                text=True,
                check=True,
            )
            match = re.search(r"bootfs.*\s(disk\d+s\d+)", result.stdout)
            if not match:
                raise RuntimeError("Boot partition not found")
            boot_partition = match.group(1).strip()
        except subprocess.CalledProcessError:
            raise RuntimeError(
                f"Failed to list disk partitions for {device_id}"
            ) from None

        try:
            result = subprocess.run(
                ["diskutil", "info", boot_partition],
                capture_output=True,
                text=True,
                check=True,
            )
            if not re.search(r"Mounted:\s+Yes", result.stdout):
                raise RuntimeError("Not mounted")
            match = re.search(r"Mount Point:\s+(.+)", result.stdout)
            if not match:
                raise RuntimeError("Mount point not found")
            mount_point = match.group(1).strip()
        except subprocess.CalledProcessError:
            raise RuntimeError("Failed to get boot partition info") from None

        return mount_point

    def unmount_and_eject(self, device_id: str) -> None:
        self.unmount_device(device_id)

        try:
            subprocess.run(
                ["diskutil", "eject", device_id], check=True, capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to eject device: {device_id}: {e.stderr}"
            ) from None

        console.print("[green]✓[/green] Device ejected")

    def trust_certificate(self, cert_path: str) -> None:
        """Trust certificate using macOS security command

        Args:
            cert_path: Path to .pem certificate file
        """
        if not Path(cert_path).exists():
            raise FileNotFoundError(f"Certificate not found: {cert_path}")

        console.print("[cyan]Installing certificate to keychain...[/cyan]")

        cmd = ["security", "add-trusted-cert", "-d", "-r", "trustRoot"]

        try:
            subprocess.run(
                ["sudo", *cmd, "-k", "/Library/Keychains/System.keychain", cert_path],
                check=True,
                capture_output=True,
                text=True,
            )
            console.print("[green]✓[/green] Certificate trusted (system keychain)")

            return
        except subprocess.CalledProcessError:
            console.print(
                "[yellow]System keychain failed, trying user keychain...[/yellow]"
            )

        # Fallback to user keychain
        try:
            subprocess.run(
                [*cmd, cert_path],
                check=True,
                capture_output=True,
                text=True,
            )
            console.print("[green]✓[/green] Certificate trusted (user keychain)")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else "Unknown error"
            raise RuntimeError(f"Failed to trust certificate: {error_msg}") from None
