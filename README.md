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

Install globally as a [uv tool](https://docs.astral.sh/uv/concepts/tools/):

```bash
# From GitHub
uv tool install git+https://github.com/alexan059/pitool.git

# Or from a local clone
uv tool install --from . pitool
```

This puts `pitool` on your `PATH` (run `uv tool update-shell` once if it isn't).

For development, clone and sync instead:

```bash
git clone https://github.com/alexan059/pitool.git
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
pitool passwd
```

**Flash boot drive:**
```bash
pitool flash

# Clear download cache first
pitool flash --clear-cache
```

**Connect to Pi:**
```bash
pitool connect
```

Waits for Pi to come online, removes old SSH host key, and connects via SSH.

**Trust Pi's mkcert certificates:**
```bash
pitool trust
```

Downloads and trusts the Pi's mkcert root CA certificate in your macOS keychain. 
Required for accessing Pi services with local HTTPS certificates. Restart your browser after installation.

## Development

**Tooling:**

- [uv](https://github.com/astral-sh/uv) (package manager)
- [hatchling](https://hatch.pypa.io/) (build backend)
- [Task](https://taskfile.dev) (task runner, optional, convenience wrapper around `uv` commands)

**Install Task** (optional):
```bash
brew install go-task
```

**Available tasks:**

| Task            | Equivalent                       | Description                          |
|-----------------|----------------------------------|--------------------------------------|
| `task sync`     | `uv sync --dev`                  | Install dependencies                 |
| `task install`  | `uv tool install --from . pitool`| Install pitool globally as a uv tool |
| `task run -- X` | `uv run pitool X`                | Run CLI command (e.g. `flash`)       |
| `task check`    | `uv run ruff check .`            | Lint code                            |
| `task format`   | `uv run ruff format .`           | Format code                          |

See `Taskfile.yml` for the source of truth.

## License

MIT License - See [LICENSE](LICENSE)
