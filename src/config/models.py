from dataclasses import dataclass


@dataclass
class WifiConfig:
    ssid: str
    password: str
    country_code: str

    @classmethod
    def from_dict(cls, data: dict) -> "WifiConfig":
        return cls(**data)


@dataclass
class UserConfig:
    name: str
    password: str
    ssh_public_key: str

    @classmethod
    def from_dict(cls, data: dict) -> "UserConfig":
        return cls(**data)


@dataclass
class PiConfig:
    name: str
    hostname: str
    wifi: WifiConfig
    user: UserConfig
    timezone: str
    locale: str
    update: bool = False
    upgrade: bool = False
    packages: list[str] | None = None
    reboot: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "PiConfig":
        packages = data.get("packages", [])
        update = data.get("update", False)
        upgrade = data.get("upgrade", False)
        reboot = data.get("reboot", False)

        return cls(
            name=data["name"],
            hostname=data["hostname"],
            wifi=WifiConfig.from_dict(data["wifi"]),
            user=UserConfig.from_dict(data["user"]),
            timezone=data["timezone"],
            locale=data["locale"],
            update=update,
            upgrade=upgrade,
            packages=packages if packages else None,
            reboot=reboot,
        )


@dataclass
class PiToolConfig:
    raspberry_pis: list[PiConfig]

    @classmethod
    def from_dict(cls, data: dict) -> "PiToolConfig":
        return cls(
            raspberry_pis=[PiConfig.from_dict(pi) for pi in data["raspberry_pis"]]
        )
