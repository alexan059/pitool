# Pi Automation

> **⚠️ macOS Only**: This tool uses macOS-specific utilities (`diskutil`, `afplay`, `security`) and is not compatible with Linux or Windows.

Automates Raspberry Pi SD card image creation with pre-configured WiFi, SSH, hostname, and user settings.

## Installation

### Prerequisites
- macOS
- Python 3.x
- [Raspberry Pi Imager 1.x](https://github.com/raspberrypi/rpi-imager/releases) with `--cli` support
  - **Note:** rpi-imager 2.0+ removed the `--cli` flag. Use version 1.x.
- `openssl` (usually pre-installed on macOS)
- [1Password CLI](https://developer.1password.com/docs/cli) (optional, for SSH key retrieval)

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd pitool
   ```

2. **Make the CLI executable:**
   ```bash
   chmod +x pitool
   ```

3. **Create your configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## CLI Usage

The `pitool` script provides a unified interface to all automation tools:

```bash
# Create Raspberry Pi SD card image
./pitool image

# Create image with Ansible installation (for post-boot provisioning)
./pitool image --with-ansible

# Keep generated scripts after flashing (for debugging)
./pitool image --keep-scripts

# Dry run: download and generate scripts without flashing
./pitool image --dry-run

# Monitor Pi connectivity
./pitool monitor pi.local

# Monitor with custom ping interval
./pitool monitor pi.local --interval 10

# Clean SSH known_hosts entries for a host
./pitool monitor pi.local --clean

# Download and trust Pi certificates
./pitool trust pi.local
```

## Python Tools

You can also run the tools directly:

### Image Creation Tool (`src/imaging/create_image.py`)
Automates Raspberry Pi SD card image creation with custom configurations.

**Usage:**
```bash
# Via CLI (recommended)
./pitool image

# With Ansible installation for provisioning
./pitool image --with-ansible

# Keep scripts after flashing
./pitool image --keep-scripts

# Or run directly
python3 src/imaging/create_image.py --with-ansible --keep-scripts
```

**Requirements:**
- `.env` file with configuration
- 1Password CLI (`op`) for SSH key retrieval (optional)
- `rpi-imager` 1.x CLI tool
- `templates/bootstrap.sh.template` and `templates/firstrun.sh.template`

**Environment Variables:**
```
WIFI_SSID=your_wifi_name
WIFI_PASSWORD=your_wifi_password
HOSTNAME=pi-hostname
OP_ITEM_VAULT=vault_name
OP_ITEM_ID=item_id
RPI_IMAGE=image_name (e.g., "lite_arm64")
PI_USER=username
PI_PASSWORD=plain_password
```

### Network Monitor Tool (`src/networking/pi_tool.py`)
Monitors Pi connectivity and manages SSH known_hosts.

**Usage:**
```bash
# Via CLI (recommended)
./pitool monitor raspberrypi.local

# Custom ping interval (default: 5 seconds)
./pitool monitor raspberrypi.local --interval 10

# Clean known_hosts entries (useful after reimaging Pi)
./pitool monitor raspberrypi.local --clean

# Or run directly
python3 src/networking/pi_tool.py raspberrypi.local --interval 10 --clean
```

### Certificate Trust Tool (`src/networking/cert_trust.py`)
Downloads and trusts SSL certificates from Pi using mkcert.

**Usage:**
```bash
# Via CLI (recommended)
./pitool trust pi.local

# Or run directly
python3 src/networking/cert_trust.py pi.local
```

**Requirements:**
- `PI_USER` environment variable set
- `mkcert` installed on local machine
- SSH access to the Pi
- Certificates located in `~/traefik/certs/` on the Pi

## Imaging and Initial Startup

- Inspired by: https://gist.github.com/bashtheshell/010d70f7643f171096ad9462ea86324b

Check deployment was successful:

```shell
tail -f /var/log/bootstrap.log
```

## Tested Configuration

**Hardware:** Raspberry Pi 4 Model B (2GB)

**Workflow:**
```bash
# 1. Create and flash SD card with Ansible
./pitool image --with-ansible

# 2. Insert SD card into Pi and power on

# 3. Monitor Pi until it comes online
./pitool monitor raspberrypi.local --interval 10

# 4. Clean SSH known_hosts (if previously connected)
./pitool monitor raspberrypi.local --clean

# 5. SSH into the Pi
ssh pi@raspberrypi.local
```

### Testing Certificate Trust

**On the Pi:**
```bash
# Install mkcert
sudo apt update
sudo apt install -y wget libnss3-tools
wget https://github.com/FiloSottile/mkcert/releases/download/v1.4.4/mkcert-v1.4.4-linux-arm64
chmod +x mkcert-v1.4.4-linux-arm64
sudo mv mkcert-v1.4.4-linux-arm64 /usr/local/bin/mkcert

# Generate root CA and certificates
mkcert -install
mkcert raspberrypi.local localhost 127.0.0.1

# Setup Apache with SSL
sudo apt install -y apache2
sudo cp raspberrypi.local+2.pem /etc/ssl/certs/
sudo cp raspberrypi.local+2-key.pem /etc/ssl/private/

# Configure SSL site
sudo tee /etc/apache2/sites-available/default-ssl.conf > /dev/null << 'EOF'
<VirtualHost _default_:443>
    ServerName raspberrypi.local
    DocumentRoot /var/www/html
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/raspberrypi.local+2.pem
    SSLCertificateKeyFile /etc/ssl/private/raspberrypi.local+2-key.pem
</VirtualHost>
EOF

sudo a2enmod ssl
sudo a2ensite default-ssl
sudo systemctl restart apache2
```

**On your Mac:**
```bash
# Trust the Pi's mkcert root CA
./pitool trust raspberrypi.local

# Visit https://raspberrypi.local in your browser
# Should show green lock (trusted certificate)
```

Everything worked as expected!
