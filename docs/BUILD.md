# Building Home AI OS

This guide explains how to build a bootable ISO image of Home AI OS from source.

## Prerequisites

### Build System Requirements

**Operating System**: Ubuntu 22.04+ or Debian 12+

**Hardware**:
- 8GB RAM minimum (16GB recommended)
- 50GB free disk space
- x86_64 CPU
- Internet connection

**Software**:
```bash
sudo apt update
sudo apt install -y \
    live-build \
    debootstrap \
    squashfs-tools \
    xorriso \
    isolinux \
    syslinux-efi \
    grub-pc-bin \
    grub-efi-amd64-bin \
    mtools \
    git \
    curl \
    wget
```

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/ryanhamil7-collab/Home-AI-OS.git
cd Home-AI-OS
```

### 2. Build ISO

```bash
sudo ./scripts/build-iso.sh
```

This will:
- Configure live-build
- Download Ubuntu base system
- Install packages
- Run hooks (Ollama, Home AI)
- Create bootable ISO

**Build time**: 30-60 minutes depending on internet speed and CPU

### 3. Find ISO

```bash
ls -lh output/homeai-os-*.iso
```

## Testing

### Test in VM (QEMU)

```bash
# Install QEMU
sudo apt install qemu-system-x86

# Run VM
./scripts/run-vm.sh
```

**VM Configuration**:
- 4GB RAM
- 4 CPU cores
- 20GB virtual disk
- KVM acceleration (if available)

### Test in VirtualBox

1. Create new VM:
   - Type: Linux
   - Version: Ubuntu (64-bit)
   - RAM: 4096MB
   - Disk: 20GB VDI

2. Settings:
   - System → Enable EFI
   - Display → Video Memory: 128MB
   - Storage → Add ISO as optical drive

3. Start VM

### Write to USB

**⚠️ WARNING**: This will erase all data on the USB drive!

```bash
# Find USB device
lsblk

# Write ISO (replace /dev/sdX with your USB device)
sudo dd if=output/homeai-os-*.iso of=/dev/sdX bs=4M status=progress oflag=sync

# Verify
sudo sync
```

## Build Configuration

### Customizing Packages

Edit `iso/config/package-lists/homeai.list.chroot` to add/remove packages:

```bash
# Add package
echo "package-name" >> iso/config/package-lists/homeai.list.chroot

# Rebuild
sudo ./scripts/build-iso.sh
```

### Customizing Hooks

Hooks run during ISO build to customize the system.

**Location**: `iso/hooks/live/*.hook.chroot`

**Existing hooks**:
- `0010-install-ollama.hook.chroot` - Installs Ollama
- `0020-install-homeai.hook.chroot` - Installs Home AI

**Create new hook**:
```bash
#!/bin/bash
# iso/hooks/live/0030-my-hook.hook.chroot
set -e

echo "Running my custom hook..."
# Your commands here

chmod +x iso/hooks/live/0030-my-hook.hook.chroot
```

### Customizing Branding

**Wallpaper**:
```bash
cp my-wallpaper.jpg branding/wallpapers/default.jpg
```

**Plymouth (boot splash)**:
```bash
# Add custom plymouth theme to branding/plymouth/
```

**LightDM (login screen)**:
```bash
# Customize branding/lightdm/
```

## Advanced Configuration

### live-build Options

Edit `scripts/build-iso.sh` to change live-build configuration:

```bash
lb config \
    --architectures amd64 \
    --distribution noble \
    --archive-areas "main restricted universe multiverse" \
    --mirror-bootstrap "http://archive.ubuntu.com/ubuntu/" \
    --binary-images iso-hybrid \
    --bootappend-live "boot=live components quiet splash" \
    --iso-application "Home AI OS" \
    --iso-volume "HomeAI-OS"
```

**Key options**:
- `--architectures`: CPU architecture (amd64, arm64)
- `--distribution`: Ubuntu release (noble = 24.04)
- `--archive-areas`: Package repositories
- `--mirror-bootstrap`: Ubuntu mirror
- `--bootappend-live`: Kernel boot parameters

### Kernel Parameters

Edit boot parameters in `iso/config/bootloaders/`:

```bash
# Example: Add nomodeset for GPU compatibility
bootappend-live="boot=live components quiet splash nomodeset"
```

### Preseed Configuration

Automate installation with preseed:

```bash
# Create preseed file
cat > iso/config/preseed/custom.cfg << 'EOF'
# Locale
d-i debian-installer/locale string en_US.UTF-8

# Keyboard
d-i keyboard-configuration/xkb-keymap select us

# Network
d-i netcfg/choose_interface select auto
d-i netcfg/get_hostname string homeai
d-i netcfg/get_domain string local

# User account
d-i passwd/user-fullname string Home AI User
d-i passwd/username string homeai
d-i passwd/user-password password homeai
d-i passwd/user-password-again password homeai
EOF
```

## Troubleshooting

### Build Fails

**Check logs**:
```bash
tail -f output/build.log
```

**Common issues**:

1. **Out of disk space**:
   ```bash
   df -h
   # Clean up
   sudo rm -rf build/
   ```

2. **Network timeout**:
   ```bash
   # Use different mirror
   lb config --mirror-bootstrap "http://us.archive.ubuntu.com/ubuntu/"
   ```

3. **Permission denied**:
   ```bash
   # Must run as root
   sudo ./scripts/build-iso.sh
   ```

### ISO Won't Boot

1. **Verify ISO integrity**:
   ```bash
   sha256sum -c output/homeai-os-*.iso.sha256
   ```

2. **Check USB write**:
   ```bash
   # Use different tool
   sudo apt install etcher-electron
   ```

3. **Try different boot mode**:
   - UEFI vs Legacy BIOS
   - Disable Secure Boot in BIOS

### VM Issues

1. **Slow performance**:
   ```bash
   # Enable KVM
   sudo modprobe kvm
   sudo modprobe kvm_intel  # or kvm_amd
   ```

2. **Display issues**:
   ```bash
   # Change video driver
   qemu-system-x86_64 ... -vga std  # or -vga qxl
   ```

## Clean Build

Remove all build artifacts:

```bash
# Clean build directory
sudo rm -rf build/

# Clean output (keeps ISOs)
sudo rm -rf output/build.log

# Full clean (removes ISOs too)
sudo rm -rf build/ output/
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Build ISO

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install dependencies
      run: |
        sudo apt update
        sudo apt install -y live-build debootstrap
    
    - name: Build ISO
      run: sudo ./scripts/build-iso.sh
    
    - name: Upload ISO
      uses: actions/upload-artifact@v3
      with:
        name: homeai-os-iso
        path: output/*.iso
```

## Development Workflow

### Iterative Development

For faster iteration during development:

1. **Build base once**:
   ```bash
   sudo ./scripts/build-iso.sh
   ```

2. **Modify hooks only**:
   ```bash
   # Edit hooks
   vim iso/hooks/live/0020-install-homeai.hook.chroot
   
   # Rebuild (faster, reuses base)
   cd build
   sudo lb build
   ```

3. **Test in VM**:
   ```bash
   ./scripts/run-vm.sh
   ```

### Debugging Hooks

Add debug output to hooks:

```bash
#!/bin/bash
set -e
set -x  # Print commands

echo "DEBUG: Starting hook"
# Your commands
echo "DEBUG: Hook complete"
```

Check hook output in build log:
```bash
grep "DEBUG:" output/build.log
```

## Performance Optimization

### Parallel Downloads

```bash
# Edit /etc/apt/apt.conf.d/99parallel
echo 'Acquire::Queue-Mode "host";' | sudo tee /etc/apt/apt.conf.d/99parallel
echo 'Acquire::http::Pipeline-Depth "5";' | sudo tee -a /etc/apt/apt.conf.d/99parallel
```

### Local Mirror

Use local Ubuntu mirror for faster builds:

```bash
lb config --mirror-bootstrap "http://localhost/ubuntu/"
```

### Caching

Cache downloaded packages:

```bash
mkdir -p cache/
lb config --cache-packages true --cache-packages-chroot true
```

## Security

### Signing ISO

Sign ISO for verification:

```bash
# Generate key
gpg --gen-key

# Sign ISO
gpg --detach-sign --armor output/homeai-os-*.iso

# Verify
gpg --verify output/homeai-os-*.iso.asc output/homeai-os-*.iso
```

### Secure Boot

Enable Secure Boot support (Phase 2):

```bash
lb config --uefi-secure-boot enable
```

## Contributing

### Submitting Changes

1. Fork repository
2. Create feature branch
3. Make changes
4. Test build
5. Submit pull request

### Testing Checklist

- [ ] ISO builds successfully
- [ ] ISO boots in VM
- [ ] ISO boots on real hardware
- [ ] All services start
- [ ] GUI launches
- [ ] No errors in logs

## Resources

- **live-build Manual**: https://live-team.pages.debian.net/live-manual/
- **Ubuntu Wiki**: https://help.ubuntu.com/community/LiveCDCustomization
- **Debian Live**: https://www.debian.org/devel/debian-live/

## Support

- **Issues**: https://github.com/ryanhamil7-collab/Home-AI-OS/issues
- **Discussions**: https://github.com/ryanhamil7-collab/Home-AI-OS/discussions
- **Documentation**: https://github.com/ryanhamil7-collab/Home-AI-OS/tree/main/docs
