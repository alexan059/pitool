import lzma
import shutil
from pathlib import Path

import requests
from InquirerPy import inquirer
from platformdirs import user_cache_dir
from rich.panel import Panel
from rich.progress import Progress

from src.console import console
from src.imaging.models import RaspberryPiImage
from src.utils import calculate_hash

# Last checked: 2025-12-12
# API Version: v4
API_URL = "https://downloads.raspberrypi.org/os_list_imagingutility_v4.json"

CACHE_DIR = Path(user_cache_dir("pitool"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _should_include_image(img: dict) -> bool:
    """Check if image should be included"""
    return (
        "Raspberry Pi OS" in img.get("name", "")
        and img.get("init_format") == "cloudinit-rpi"
    )


def fetch_image_list() -> list[RaspberryPiImage]:
    """Fetch Raspberry Pi OS images with cloud-init support

    Returns:
        List of dicts with: name, url, release_date, extract_size
    """
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        raise ConnectionError(f"Failed to fetch image list: {e}") from None

    result = []
    for item in data.get("os_list", []):
        if "subitems" in item:
            for subitem in item.get("subitems", []):
                if _should_include_image(subitem):
                    result.append(RaspberryPiImage.from_dict(subitem))
        else:
            if _should_include_image(item):
                result.append(RaspberryPiImage.from_dict(item))

    return result


def prompt_for_image(images: list[RaspberryPiImage]) -> RaspberryPiImage:
    """Prompt user to select an image

    Args:
        images: List of available images

    Returns:
        Selected image
    """
    choices = [{"name": img.name, "value": img} for img in images]

    selected = inquirer.select(
        message="Select a Raspberry Pi OS image:", choices=choices
    ).execute()

    return selected


def _extract_image(compressed_path: Path, expected_size: int) -> Path:
    """Extract .xz compressed image

    Args:
        compressed_path: Path to .img.xz file
        expected_size: Expected uncompressed size (for progress)
    """
    uncompressed_path = Path(str(compressed_path).removesuffix(".xz"))

    if uncompressed_path.exists():
        console.print("[green]✓[/green] Using cached extracted image")
        return uncompressed_path

    with Progress() as progress:
        task = progress.add_task(
            f"[magenta]Extracting[/magenta] {compressed_path.name}...",
            total=expected_size,
        )

        bytes_written = 0
        with (
            lzma.open(compressed_path, "rb") as compressed_file,
            open(uncompressed_path, "wb") as output,
        ):
            while True:
                chunk = compressed_file.read(8192)
                if not chunk:
                    break
                output.write(chunk)
                bytes_written += len(chunk)
                progress.update(task, completed=bytes_written)

    return uncompressed_path


def _verify_hash(file_path: Path, stored_hash: str) -> bool:
    size = file_path.stat().st_size

    calculated_hash = calculate_hash(
        str(file_path.resolve()),
        size=size,
        text=f"[yellow]Verifying image[/yellow] {file_path.name}...",
    )

    return calculated_hash == stored_hash


def download_image(image: RaspberryPiImage) -> Path:
    """Download a Raspberry Pi OS image with caching and verification

    Args:
        image: The image to download

    Returns:
        Path to the downloaded image file

    Raises:
        ValueError: If hash verification fails
    """
    filename = image.url.split("/")[-1]

    cache_download_path = CACHE_DIR / filename
    cache_extracted_path = CACHE_DIR / filename.replace(".xz", "")

    # TODO: prompt for latest version if available or use --latest flag
    if cache_extracted_path.exists():
        console.print(
            f"[green]✓[/green] Using cached image: [cyan]{filename.replace('.xz', '')}[/cyan]"
        )
        return cache_extracted_path

    if cache_download_path.exists():
        console.print("[yellow]Found cached download, extracting...[/yellow]")
        extracted_path = _extract_image(cache_download_path, image.extract_size)
        if not _verify_hash(extracted_path, image.extract_sha256):
            extracted_path.unlink()
            cache_download_path.unlink()
            raise ValueError(f"Failed to verify image integrity: {filename}")
        cache_download_path.unlink()
        return extracted_path

    console.print(
        Panel(
            f"[bold]{image.name}[/bold]\n"
            f"Size: {image.image_download_size / (1024**2):.1f} MB\n"
            f"Release: {image.release_date}",
            title="Downloading",
            border_style="cyan",
        )
    )

    with requests.get(image.url, stream=True) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))

        with Progress() as progress:
            task = progress.add_task(
                f"[cyan]Downloading[/cyan] {filename}...", total=total
            )

            try:
                with open(cache_download_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                            progress.update(task, advance=len(chunk))
            except Exception:
                if cache_download_path.exists():
                    cache_download_path.unlink()
                raise

        cache_path = _extract_image(cache_download_path, image.extract_size)

        if not _verify_hash(cache_path, image.extract_sha256):
            cache_path.unlink()
            cache_download_path.unlink()
            raise ValueError(f"Failed to verify image integrity: {filename}")

    cache_download_path.unlink()

    console.print(f"[green]✓ Download complete:[/green] {filename}")

    return cache_path


def clear_download_cache() -> None:
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        console.print("[cyan]Download cache cleared...[/cyan]")
