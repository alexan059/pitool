# pitool

Automated Raspberry Pi SD card provisioning with cloud-init.

> **Platform Support:** Currently macOS only. Uses `diskutil` and `dd` for direct SD card flashing. Linux and Windows support planned.
>
> **Why not rpi-imager?** Raspberry Pi Imager 2.0+ removed CLI support (`--cli` flag), so we use direct `dd` flashing with platform abstractions for future cross-platform compatibility.

## Requirements

- **macOS** (Darwin)
- **Python 3.12+**
- **uv** (package manager)
- **OpenSSL** (for password hashing)

## Tech Stack

**Package Manager:** [uv](https://github.com/astral-sh/uv)

**Dependencies:**
- `typer` - CLI framework
- `rich` - Terminal formatting
- `inquirerpy` - Interactive prompts
- `jinja2` - Cloud-init template rendering
- `pyyaml` - Configuration loading
- `requests` - Image downloads
- `platformdirs` - Cross-platform cache directories

**Architecture:**
- Cloud-init based provisioning (Raspberry Pi OS Trixie+)
- Platform abstraction for future Linux/Windows support
- Direct SD card flashing via `dd`
- Smart caching with hash verification

## Usage

### Installation

```bash
git clone <repository-url>
cd pitool
uv sync
```

### Configuration

Create `pitool.yml`:

```yaml
raspberry_pis:
  - name: pi
    hostname: raspberrypi
    wifi:
      country_code: DE
      ssid: "YourWiFiSSID"
      password: "YourWiFiPassword"
    user:
      name: pi
      password: "$6$salt$hashedpassword"  # Use `pitool passwd` to generate
      ssh_public_key: "ssh-ed25519 AAAA..."
    timezone: Europe/Berlin
    locale: en_US.UTF-8
    update: true
    upgrade: true
    packages:
      - ansible
    reboot: true
```

See `pitool.example.yml` for reference.

### Commands

**Generate password hash:**
```bash
uv run pitool passwd
```

**Flash SD card:**
```bash
uv run pitool flash

# Clear download cache first
uv run pitool flash --clear-cache
```

**Connect to Pi:**
```bash
uv run pitool connect
```

Waits for Pi to come online, removes old SSH host key, and connects via SSH.

## Development

This project uses [Task](https://taskfile.dev) for development workflows.

**Install Task:**
```bash
brew install go-task
```

**Available tasks:**

```bash
# Install dependencies
task sync

# Run CLI directly
task run -- flash
task run -- passwd
task run -- connect

# Lint code
task check

# Format code
task format
```

See `Taskfile.yml` for all available tasks.

## License

MIT License - See [LICENSE](LICENSE)
