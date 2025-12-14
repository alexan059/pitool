import hashlib
from pathlib import Path

from rich.progress import Progress


def calculate_hash(
    path: str,
    size: int | None = None,
    chunk_size: int = 4096,
    text: str = "[yellow]Calculating hash...[/yellow]",
) -> str:
    """Calculate SHA256 hash of file or device

    Args:
        path: Path to file or device
        size: Number of bytes to read (None = entire file)
        chunk_size: Bytes to read per chunk
        text: Progress bar description

    Returns:
        SHA256 hash as hex string
    """

    if size is None:
        size = Path(path).stat().st_size

    with Progress() as progress:
        task = progress.add_task(text, total=size)

        hasher = hashlib.sha256()
        bytes_read = 0

        with open(path, "rb") as f:
            while bytes_read < size:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
                bytes_read += len(chunk)
                progress.update(task, advance=len(chunk))

        return hasher.hexdigest()
