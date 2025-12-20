# pitool

Automated Raspberry Pi boot drive provisioning with cloud-init.

> **Platform Support:** Currently macOS only. Uses `diskutil` and `dd` for direct drive flashing. Linux and Windows support planned.
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
- Direct drive flashing via `dd`
- Smart caching with hash verification

## Usage

### Installation

```bash
git clone <repository-url>
cd pitool
uv sync --dev
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

**Flash boot drive:**
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

**Trust Pi's mkcert certificates:**
```bash
uv run pitool trust
```

Downloads and trusts the Pi's mkcert root CA certificate in your macOS keychain. 
Required for accessing Pi services with local HTTPS certificates. Restart your browser after installation.

## Development

**Tooling:**

- [uv](https://github.com/astral-sh/uv) (package manager)
- [hatchling](https://hatch.pypa.io/) (build backend)
- [Task](https://taskfile.dev) (task runner)

**Install Task:**
```bash
brew install go-task
```

**Available tasks:**

```bash
# Install dependencies
task sync
# or
uv sync --dev

# Run CLI directly
task run -- flash
task run -- passwd
task run -- connect
task run -- trust

# Lint code
task check

# Format code
task format
```

See `Taskfile.yml` for all available tasks.

## License

MIT License - See [LICENSE](LICENSE)
