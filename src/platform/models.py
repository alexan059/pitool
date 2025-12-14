from dataclasses import dataclass


@dataclass
class ExternalDevice:
    id: str
    node: str
    name: str
    size: str
    protocol: str
    location: str
