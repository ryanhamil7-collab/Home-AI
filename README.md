# Home AI OS

A Linux-based operating system with deep AI integration. Home AI OS boots directly into an AI-native desktop environment where you can control your computer through natural language, computer vision, and autonomous agents.

## Overview

Home AI OS is built on Ubuntu 24.04 LTS and provides:

- **AI-First Interface**: Boots directly into Home AI kiosk mode
- **Computer Vision**: Live screen capture and analysis
- **Natural Language Control**: Give commands in plain English
- **Autonomous Agents**: AI that can navigate and control the desktop
- **Business Dashboard**: Financial tracking and automation
- **Self-Improvement**: AI can analyze and improve its own code
- **Safety-First**: Comprehensive security controls and audit logging

## Features

### Core OS Features
- Ubuntu 24.04 LTS base (stable, excellent hardware support)
- x86_64 architecture
- Xfce desktop environment (lightweight, reliable)
- Systemd services for AI components
- D-Bus integration for inter-process communication
- PolicyKit for safe privilege escalation
- AppArmor security profiles

### AI Features
- Ollama LLM engine (Mistral, Llama, Phi3)
- Live computer vision with screen capture
- Natural language command interface
- Autonomous desktop navigation
- Business intelligence and automation
- Self-improvement system with approval workflow

### System Integration
- GPU support (NVIDIA CUDA, AMD/Intel open-source)
- First-boot wizard for setup
- Automatic model downloading
- System monitoring and management
- Audit logging with tamper detection

## Quick Start

### Download ISO
```bash
# Coming soon - ISO download link
```

### Build from Source
```bash
# Clone repository
git clone https://github.com/ryanhamil7-collab/Home-AI-OS.git
cd Home-AI-OS

# Install build dependencies
sudo apt install live-build debootstrap

# Build ISO
sudo ./scripts/build-iso.sh

# Test in VM
./scripts/run-vm.sh
```

## Architecture

### Directory Structure
```
Home-AI-OS/
├── iso/                    # Live ISO build configuration
│   ├── config/            # live-build configs
│   ├── hooks/             # Build hooks
│   └── includes/          # Files to include in ISO
├── packages/              # Debian packages
│   ├── homeai-app/       # Main application package
│   ├── homeai-daemons/   # System services
│   └── homeai-meta/      # Meta-package
├── branding/              # OS branding
│   ├── wallpapers/
│   ├── plymouth/         # Boot splash
│   └── lightdm/          # Login theme
├── scripts/               # Build and utility scripts
├── systemd/               # Service unit files
├── dbus/                  # D-Bus service definitions
├── polkit/                # PolicyKit rules
└── docs/                  # Documentation
```

### System Services

**ollama.service**
- Runs Ollama LLM engine
- Multi-user service
- Manages model loading and inference

**homeai-agent.service**
- Background orchestration
- System monitoring
- Autonomous task execution
- Audit logging

**homeai-ui.desktop**
- Session autostart
- Launches PyQt6 GUI in kiosk mode
- Provides escape to desktop

## Development Phases

### Phase 1: MVP Live ISO (Current)
- [x] Repository structure
- [ ] Debian packaging
- [ ] Systemd services
- [ ] Kiosk session configuration
- [ ] Live-build ISO configuration
- [ ] First-boot wizard
- [ ] Bootable ISO

### Phase 2: Full OS
- [ ] Calamares installer
- [ ] OS update UI
- [ ] Driver wizard (NVIDIA/AMD)
- [ ] Switchable sessions
- [ ] System administration UI

### Phase 3: Advanced Features
- [ ] KDE Plasma + Wayland
- [ ] AI-guided system admin
- [ ] Voice/face unlock (opt-in)
- [ ] Automatic maintenance
- [ ] Rollback support (btrfs)

## Requirements

### Build Requirements
- Ubuntu 22.04+ or Debian 12+
- 8GB RAM minimum
- 50GB free disk space
- sudo access

### Runtime Requirements
- x86_64 CPU (Intel/AMD)
- 4GB RAM minimum (8GB recommended)
- 20GB disk space
- GPU: NVIDIA (CUDA) or AMD/Intel (open-source)
- Internet connection for first boot

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Home AI OS is open source. See [LICENSE](LICENSE) for details.

## Links

- **Home AI Application**: https://github.com/ryanhamil7-collab/Home-AI
- **Documentation**: [docs/](docs/)
- **Issues**: https://github.com/ryanhamil7-collab/Home-AI-OS/issues

## Credits

Built with:
- Ubuntu Linux
- Ollama
- PyQt6
- Python 3.11+
- And many other open source projects

---

**Status**: 🚧 Under Active Development - Phase 1 MVP
