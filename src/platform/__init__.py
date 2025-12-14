import platform

from src.platform.base import PlatformHandler
from src.platform.macos import MacOSPlatform


def get_platform_handler() -> PlatformHandler:
    system = platform.system()

    if system == "Darwin":
        return MacOSPlatform()
    elif system == "Linux":
        raise NotImplementedError("Linux support coming soon")
    elif system == "Windows":
        raise NotImplementedError("Windows support coming soon")
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
