from abc import ABC, abstractmethod

from src.platform.models import RemovableDevice


class PlatformHandler(ABC):
    """Abstract interface for platform-specific operations"""

    @abstractmethod
    def list_removable_devices(self) -> list[RemovableDevice]:
        """Return list of removable storage devices

        Returns:
            List of dicts with keys: 'id', 'name', 'size'
            Example: [{'id': '/dev/disk2', 'name': 'USB Drive', 'size': '32GB'}]
        """
        pass

    @abstractmethod
    def unmount_device(self, device_id: str) -> None:
        """Unmount a device before flashing"""
        pass

    @abstractmethod
    def flash_image(self, image_path: str, device_id: str) -> None:
        """Flash an image to device using dd"""
        pass

    @abstractmethod
    def mount_boot_partition(self, device_id: str) -> str:
        """Mount boot partition and return mount point path"""
        pass

    @abstractmethod
    def unmount_and_eject(self, device_id: str) -> None:
        """Unmount and eject device"""
        pass
