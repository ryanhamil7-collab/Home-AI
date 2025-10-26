# Home AI OS Architecture

## Overview

Home AI OS is a Linux-based operating system built on Ubuntu 24.04 LTS with deep AI integration. The system boots directly into an AI-native desktop environment where users can control their computer through natural language, computer vision, and autonomous agents.

## System Architecture

### Layer 1: Base OS (Ubuntu 24.04 LTS)
- **Kernel**: Linux 6.8+
- **Init System**: systemd
- **Package Manager**: apt/dpkg
- **Display Server**: Xorg (Phase 1), Wayland (Phase 3)
- **Desktop Environment**: Xfce (Phase 1), KDE Plasma (Phase 3)
- **Audio**: PipeWire with PulseAudio compatibility
- **Network**: NetworkManager
- **Security**: AppArmor, PolicyKit

### Layer 2: System Services
- **ollama.service**: LLM engine (multi-user)
- **homeai-agent.service**: Background orchestration and monitoring
- **homeai-audit.service**: Audit logging and integrity checking

### Layer 3: Session Layer
- **Home AI Session**: Custom Xfce session with kiosk mode
- **LightDM**: Display manager with autologin
- **homeai-ui.desktop**: Autostart entry for PyQt6 GUI

### Layer 4: Application Layer
- **Home AI Application**: PyQt6 GUI with 6 tabs
  - Vision: Live screen capture and AI analysis
  - Commands: Natural language interface
  - Business: Financial dashboard
  - Monitoring: System stats and processes
  - Logs: Tamper-proof audit logs
  - Self-Improve: Code analysis and updates

### Layer 5: Integration Layer
- **D-Bus Services**: org.homeai.Control for IPC
- **PolicyKit Rules**: Safe privilege escalation
- **XDG Portals**: Screen capture, file access (Wayland)

## Component Details

### Ollama Service

**Purpose**: Runs LLM inference engine for AI features

**Configuration**:
```ini
[Unit]
Description=Ollama LLM Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ollama
Group=ollama
ExecStart=/usr/bin/ollama serve
Restart=always
RestartSec=3
Environment="OLLAMA_HOST=127.0.0.1:11434"
Environment="OLLAMA_MODELS=/var/lib/ollama/models"

[Install]
WantedBy=multi-user.target
```

**Models**:
- mistral:7b-instruct (default)
- llama3.2:3b (fallback)
- llava:7b (vision analysis)
- phi3:mini (low-resource)

### Home AI Agent Service

**Purpose**: Background orchestration, monitoring, autonomous tasks

**Configuration**:
```ini
[Unit]
Description=Home AI Background Agent
After=ollama.service
Requires=ollama.service

[Service]
Type=simple
User=homeai
Group=homeai
WorkingDirectory=/opt/home-ai
ExecStart=/opt/home-ai/venv/bin/python -m home_ai.agents.background
Restart=always
RestartSec=5
Environment="PYTHONPATH=/opt/home-ai"

[Install]
WantedBy=multi-user.target
```

**Responsibilities**:
- System monitoring
- Autonomous task execution
- Audit logging
- Resource management
- Alert generation

### Home AI UI Session

**Purpose**: Launches PyQt6 GUI in kiosk mode

**Session File** (`/usr/share/xsessions/homeai.desktop`):
```ini
[Desktop Entry]
Name=Home AI Session
Comment=AI-Native Desktop Environment
Exec=/usr/bin/homeai-session
Type=Application
DesktopNames=XFCE;HomeAI
```

**Session Script** (`/usr/bin/homeai-session`):
```bash
#!/bin/bash
# Start Xfce components
xfce4-session &

# Wait for desktop to be ready
sleep 2

# Launch Home AI in kiosk mode
/opt/home-ai/venv/bin/python -m home_ai.main --kiosk
```

**Autostart** (`~/.config/autostart/homeai-ui.desktop`):
```ini
[Desktop Entry]
Type=Application
Name=Home AI
Exec=/opt/home-ai/venv/bin/python -m home_ai.main --kiosk
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
```

## D-Bus Integration

### Service Definition

**File**: `/usr/share/dbus-1/system-services/org.homeai.Control.service`

```ini
[D-BUS Service]
Name=org.homeai.Control
Exec=/opt/home-ai/venv/bin/python -m home_ai.dbus.service
User=root
SystemdService=homeai-dbus.service
```

### Interface

**Methods**:
- `InstallPackage(package_name: str) -> bool`
- `UpdateSystem() -> bool`
- `RestartService(service_name: str) -> bool`
- `GetSystemInfo() -> dict`
- `ExecuteCommand(command: str, args: list) -> dict`

**Signals**:
- `SystemUpdateAvailable(version: str, description: str)`
- `SecurityAlert(level: str, message: str)`
- `TaskCompleted(task_id: str, result: dict)`

## PolicyKit Rules

**File**: `/usr/share/polkit-1/rules.d/50-homeai.rules`

```javascript
polkit.addRule(function(action, subject) {
    if (action.id == "org.homeai.install-package" &&
        subject.isInGroup("homeai-admin")) {
        return polkit.Result.AUTH_ADMIN;
    }
});

polkit.addRule(function(action, subject) {
    if (action.id == "org.homeai.restart-service" &&
        subject.isInGroup("homeai-admin")) {
        return polkit.Result.AUTH_ADMIN;
    }
});
```

## Security Model

### AppArmor Profiles

**Ollama Profile** (`/etc/apparmor.d/usr.bin.ollama`):
```
#include <tunables/global>

/usr/bin/ollama {
  #include <abstractions/base>
  #include <abstractions/nameservice>
  
  /usr/bin/ollama mr,
  /var/lib/ollama/** rw,
  /tmp/** rw,
  
  # GPU access
  /dev/nvidia* rw,
  /dev/dri/** rw,
  
  # Network
  network inet stream,
  network inet6 stream,
  
  # Deny dangerous operations
  deny /etc/shadow r,
  deny /root/** rw,
}
```

**Home AI Agent Profile** (`/etc/apparmor.d/opt.home-ai.agent`):
```
#include <tunables/global>

/opt/home-ai/venv/bin/python {
  #include <abstractions/base>
  #include <abstractions/python>
  
  /opt/home-ai/** r,
  /home/*/.home_ai/** rw,
  
  # System monitoring
  /proc/** r,
  /sys/** r,
  
  # D-Bus
  dbus send,
  dbus receive,
  
  # Deny sensitive areas
  deny /etc/shadow r,
  deny /root/** rw,
  deny /home/*/.ssh/** rw,
}
```

### Privilege Escalation

All privileged operations must:
1. Go through D-Bus service
2. Require PolicyKit authentication
3. Be logged to audit log
4. Have user confirmation dialog

**Example Flow**:
```
User clicks "Install Package" in GUI
    ↓
GUI calls D-Bus method org.homeai.Control.InstallPackage()
    ↓
PolicyKit prompts for authentication
    ↓
User enters password
    ↓
D-Bus service executes apt install
    ↓
Operation logged to audit log
    ↓
Result returned to GUI
```

## File System Layout

```
/
├── opt/
│   └── home-ai/                    # Application installation
│       ├── venv/                   # Python virtual environment
│       ├── src/                    # Source code
│       ├── config/                 # Default configuration
│       └── models/                 # Cached models (symlink to /var/lib)
├── usr/
│   ├── bin/
│   │   ├── homeai                  # CLI wrapper
│   │   └── homeai-session          # Session launcher
│   ├── share/
│   │   ├── applications/
│   │   │   └── homeai.desktop      # Desktop entry
│   │   ├── xsessions/
│   │   │   └── homeai.desktop      # Session entry
│   │   ├── dbus-1/
│   │   │   └── system-services/    # D-Bus services
│   │   └── polkit-1/
│   │       └── rules.d/            # PolicyKit rules
│   └── lib/
│       └── systemd/
│           └── system/             # Service units
├── var/
│   └── lib/
│       ├── ollama/                 # Ollama data
│       │   └── models/             # LLM models
│       └── homeai/                 # Application data
├── etc/
│   ├── systemd/
│   │   └── system/                 # Service overrides
│   ├── apparmor.d/                 # Security profiles
│   └── homeai/                     # System configuration
└── home/
    └── <user>/
        └── .home_ai/               # User data
            ├── config/             # User configuration
            ├── logs/               # Audit logs
            ├── backups/            # Self-improvement backups
            └── data/               # Application data
```

## Boot Process

### 1. GRUB Bootloader
- Loads Linux kernel
- Passes kernel parameters
- Shows branded splash screen

### 2. Kernel Initialization
- Hardware detection
- Driver loading
- Mount root filesystem

### 3. Systemd Init
- Starts system services
- Mounts filesystems
- Configures network

### 4. Service Startup
```
network-online.target
    ↓
ollama.service (starts LLM engine)
    ↓
homeai-agent.service (starts background agent)
    ↓
homeai-dbus.service (starts D-Bus service)
    ↓
graphical.target
    ↓
lightdm.service (display manager)
    ↓
Home AI Session (user login)
    ↓
homeai-ui (PyQt6 GUI in kiosk mode)
```

### 5. First Boot Wizard
On first boot, user is guided through:
1. Language and timezone selection
2. Network configuration
3. GPU driver detection and installation
4. Model download (mistral:7b-instruct)
5. User account creation
6. Privacy settings

## Network Architecture

### Local Services
- **Ollama API**: http://127.0.0.1:11434
- **Home AI D-Bus**: system bus
- **Home AI Agent**: Unix socket

### External Services (Optional)
- **Model Downloads**: https://ollama.ai
- **System Updates**: Ubuntu repositories
- **Telemetry**: opt-in anonymous usage stats

### Firewall Rules
```bash
# Allow outbound for updates and models
ufw allow out 80/tcp
ufw allow out 443/tcp

# Block inbound by default
ufw default deny incoming

# Allow SSH (optional, disabled by default)
# ufw allow 22/tcp
```

## Update Mechanism

### System Updates
- Managed by `unattended-upgrades`
- Security updates applied automatically
- Feature updates require user approval
- Rollback via btrfs snapshots (Phase 3)

### Application Updates
- Home AI app updates via apt repository
- Models updated via Ollama
- Self-improvement updates require approval

### Update Flow
```
unattended-upgrades checks for updates
    ↓
Security updates applied automatically
    ↓
Feature updates queued
    ↓
User notified via GUI
    ↓
User reviews and approves
    ↓
Updates applied
    ↓
System reboot if needed
```

## Performance Optimization

### CPU Scheduling
- Ollama service: nice -10 (higher priority)
- Home AI agent: nice 0 (normal)
- Background tasks: nice 10 (lower priority)

### Memory Management
- Ollama: 4GB reserved
- Home AI: 2GB reserved
- System: 2GB minimum
- Swap: 8GB recommended

### GPU Allocation
- Ollama: Primary GPU access
- Vision system: Shared GPU access
- Desktop compositor: Fallback to CPU if needed

### Disk I/O
- Models on SSD recommended
- Logs on separate partition (optional)
- Automatic log rotation

## Monitoring and Telemetry

### System Metrics
- CPU usage per service
- Memory usage per service
- GPU utilization
- Disk I/O
- Network traffic

### Application Metrics
- LLM inference time
- Vision analysis latency
- Command execution time
- User interaction patterns

### Privacy
- All telemetry is opt-in
- No personal data collected
- Anonymous usage statistics only
- Data stored locally by default

## Disaster Recovery

### Backup Strategy
- User data: `~/.home_ai/` backed up daily
- Configuration: `/etc/homeai/` backed up on change
- Models: Re-downloadable, not backed up
- System: btrfs snapshots (Phase 3)

### Recovery Options
1. **Safe Mode**: Boot to standard desktop
2. **Recovery Console**: TTY access
3. **Live USB**: Boot from installation media
4. **Rollback**: Restore from snapshot (Phase 3)

### Recovery Boot Entry
```
menuentry 'Home AI OS (Recovery Mode)' {
    linux /boot/vmlinuz root=UUID=... ro recovery nomodeset
    initrd /boot/initrd.img
}
```

## Future Enhancements

### Phase 2
- Calamares installer
- Driver wizard
- OS update UI
- Session switcher

### Phase 3
- KDE Plasma + Wayland
- PipeWire screen capture
- Voice/face unlock
- Automatic maintenance

### Phase 4
- ARM64 support
- Distributed hive mind
- Federated learning
- Cloud sync (opt-in)

## Technical Specifications

### Minimum Requirements
- CPU: x86_64, 2 cores, 2.0 GHz
- RAM: 4GB
- Disk: 20GB
- GPU: Optional (CPU fallback)

### Recommended Requirements
- CPU: x86_64, 4+ cores, 3.0+ GHz
- RAM: 8GB+
- Disk: 50GB+ SSD
- GPU: NVIDIA (4GB+ VRAM) or AMD/Intel

### Supported Hardware
- **CPU**: Intel, AMD (x86_64)
- **GPU**: NVIDIA (CUDA), AMD (ROCm), Intel (oneAPI)
- **Storage**: HDD, SSD, NVMe
- **Network**: Ethernet, Wi-Fi
- **Display**: 1920x1080 minimum

## Development Tools

### Build Tools
- `live-build`: ISO creation
- `debootstrap`: Base system
- `dpkg-dev`: Package building
- `git`: Version control

### Testing Tools
- `qemu-system-x86_64`: VM testing
- `virt-manager`: VM management
- `pytest`: Unit testing
- `shellcheck`: Script validation

### Debugging Tools
- `journalctl`: System logs
- `dbus-monitor`: D-Bus debugging
- `strace`: System call tracing
- `gdb`: Debugging

## References

- Ubuntu Documentation: https://help.ubuntu.com
- Debian Live Manual: https://live-team.pages.debian.net/live-manual/
- systemd Documentation: https://systemd.io
- D-Bus Specification: https://dbus.freedesktop.org/doc/
- PolicyKit Documentation: https://www.freedesktop.org/software/polkit/docs/
