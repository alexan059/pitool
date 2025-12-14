from dataclasses import dataclass


@dataclass
class RemovableDevice:
    id: str
    node: str
    name: str
    size: str
    protocol: str
    removable: bool
