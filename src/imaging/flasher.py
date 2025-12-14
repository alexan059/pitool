from pathlib import Path

from InquirerPy import inquirer

from src.platform import get_platform_handler
from src.platform.models import ExternalDevice


def list_devices() -> list[ExternalDevice]:
    platform = get_platform_handler()
    devices = platform.list_external_devices()

    return devices


def prompt_for_device(devices: list[ExternalDevice]) -> ExternalDevice:
    if not devices:
        raise ValueError("No devices found for selection")

    choices = [
        {"name": f"{dev.node} | {dev.name} | {dev.size}", "value": dev}
        for dev in devices
    ]

    selected = inquirer.select(message="Select a device", choices=choices).execute()

    return selected


def flash_device(image_path: Path, device: ExternalDevice):
    platform = get_platform_handler()
    platform.flash_image(str(image_path.resolve()), device.node)
