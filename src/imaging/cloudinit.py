import secrets
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.config.models import PiConfig
from src.paths import TEMPLATES_DIR


def generate_cloudinit_files(pi_config: PiConfig, output_dir: Path):
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

    suffix = secrets.token_hex(4)

    user_data = env.get_template("user-data.j2").render(
        hostname=pi_config.hostname,
        user=pi_config.user,
        timezone=pi_config.timezone,
        locale=pi_config.locale,
        update=pi_config.update,
        upgrade=pi_config.upgrade,
        packages=pi_config.packages,
        reboot=pi_config.reboot,
    )

    network_config = env.get_template("network-config.j2").render(
        wifi=pi_config.wifi,
    )

    meta_data = env.get_template("meta-data.j2").render(
        hostname=pi_config.hostname,
        instance_id=f"{pi_config.hostname}-{suffix}",
    )

    (output_dir / "user-data").write_text(user_data)
    (output_dir / "network-config").write_text(network_config)
    (output_dir / "meta-data").write_text(meta_data)
