from pathlib import Path

import typer

from src.config.loader import load_config
from src.config.passwd import generate_hashed_password
from src.imaging.cloudinit import generate_cloudinit_files
from src.imaging.downloader import (
    clear_download_cache,
    download_image,
    fetch_image_list,
    prompt_for_image,
)
from src.imaging.flasher import flash_device, list_devices, prompt_for_device
from src.networking.connect import connect_to_pi, wait_for_pi
from src.platform import get_platform_handler

app = typer.Typer()


@app.command("flash")
def flash(clear_cache: bool = False):
    """Flash a configured Raspberry Pi image"""

    if clear_cache:
        clear_download_cache()

    # Gather the configuration
    # TODO: enable multiple pis
    pi_config = load_config()

    # download image
    images = fetch_image_list()
    selected_image = prompt_for_image(images)
    download_path = download_image(selected_image)

    # flash device
    devices = list_devices()
    selected_device = prompt_for_device(devices)
    flash_device(download_path, selected_device)

    # generate boot partition cloud-init files
    platform = get_platform_handler()
    mount_partition = platform.mount_boot_partition(selected_device.node)
    generate_cloudinit_files(pi_config.raspberry_pis[0], Path(mount_partition))

    # finish
    platform.unmount_and_eject(selected_device.node)


@app.command("passwd")
def passwd():
    generate_hashed_password()


@app.command("connect")
def connect():
    """Wait for Pi to come online and connect via SSH"""
    pi_config = load_config()
    pi = pi_config.raspberry_pis[0]

    wait_for_pi(pi.hostname)
    connect_to_pi(pi.user.name, pi.hostname)


def main():
    app()


if __name__ == "__main__":
    main()
