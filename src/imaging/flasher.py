from pathlib import Path

from InquirerPy import inquirer

from src.platform import get_platform_handler
from src.platform.models import RemovableDevice


def list_devices() -> list[RemovableDevice]:
    platform = get_platform_handler()
    devices = platform.list_removable_devices()

    return devices


def prompt_for_device(devices: list[RemovableDevice]) -> RemovableDevice:
    if not devices:
        raise ValueError("No devices found for selection")

    choices = [
        {"name": f"{dev.node} | {dev.name} | {dev.size}", "value": dev}
        for dev in devices
    ]

    selected = inquirer.select(message="Select a device", choices=choices).execute()

    return selected


def flash_device(image_path: Path, device: RemovableDevice):
    platform = get_platform_handler()
    platform.flash_image(str(image_path.resolve()), device.node)
