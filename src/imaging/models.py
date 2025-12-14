from dataclasses import dataclass


@dataclass
class RaspberryPiImage:
    name: str
    description: str
    icon: str
    url: str
    extract_size: int
    extract_sha256: str
    image_download_size: int
    release_date: str
    init_format: str
    devices: list[str]
    capabilities: list[str]

    @classmethod
    def from_dict(cls, data: dict) -> "RaspberryPiImage":
        return cls(**data)
