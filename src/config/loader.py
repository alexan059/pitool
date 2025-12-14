from pathlib import Path

import typer
import yaml

from .models import PiToolConfig


def load_config(path: str = "pitool.yml") -> PiToolConfig:
    config_path = Path.cwd() / path

    try:
        with config_path.open() as file:
            config = yaml.safe_load(file)
            return PiToolConfig.from_dict(config)
    except FileNotFoundError:
        raise typer.BadParameter(f"Config file not found: {path}") from None
