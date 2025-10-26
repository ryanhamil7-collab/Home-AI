# First Boot Wizard Guide

## Overview

The Home AI OS First Boot Wizard guides users through initial system setup after installing or booting the live ISO. It configures network, GPU drivers, AI models, user accounts, and privacy settings.

## Wizard Pages

### 1. Welcome Page

**Purpose:** Introduction to Home AI OS and wizard overview

**Content:**
- Welcome message
- Feature list (network, GPU, models, user, privacy)
- Next button to begin

**User Action:** Click Next to continue

---

### 2. Network Configuration

**Purpose:** Ensure internet connectivity for downloads

**Features:**
- Network status detection via NetworkManager
- Connection information display
- Quick access to Network Manager GUI
- Auto-refresh status

**User Actions:**
- Review network status
- Click "Open Network Manager" if not connected
- Configure WiFi/Ethernet
- Click Next when connected

**Technical Details:**
```bash
# Network check command
nmcli general status

# Launch Network Manager
nm-connection-editor
```

**Troubleshooting:**
- **No WiFi adapter:** Check hardware compatibility
- **Connection fails:** Verify credentials, check router
- **Ethernet not detected:** Check cable, driver support

---

### 3. GPU Detection

**Purpose:** Detect graphics hardware and install appropriate drivers

**Features:**
- Automatic GPU detection via lspci
- Driver recommendations based on hardware
- Three options:
  1. **NVIDIA proprietary** (recommended for NVIDIA GPUs)
  2. **Open-source Mesa** (default for AMD/Intel)
  3. **Skip installation** (use existing drivers)

**User Actions:**
- Review detected GPU
- Select driver option
- Click "Install Selected Driver"
- Wait for installation (if applicable)

**Technical Details:**
```bash
# GPU detection
lspci -nn | grep -E 'VGA|3D'

# NVIDIA driver installation (Phase 2)
pkcon install nvidia-driver-535

# Check driver status
nvidia-smi  # For NVIDIA
glxinfo | grep "OpenGL"  # For all
```

**Driver Options:**

| GPU Type | Recommended Driver | Notes |
|----------|-------------------|-------|
| NVIDIA GeForce/Quadro | NVIDIA proprietary | Best performance, CUDA support |
| AMD Radeon | Mesa (open-source) | Good performance, included |
| Intel HD/Iris | Mesa (open-source) | Included, works out of box |
| Other/Unknown | Skip | Use existing drivers |

**Troubleshooting:**
- **NVIDIA driver fails:** May need Secure Boot disabled
- **Black screen after install:** Boot to recovery, remove driver
- **Performance issues:** Check driver is loaded: `lsmod | grep nvidia`

---

### 4. AI Model Download

**Purpose:** Download LLM models for Home AI

**Features:**
- Model selection dropdown
- Size and RAM requirements displayed
- Download progress bar
- Skip option for later download

**Available Models:**

| Model | Size | RAM Required | Best For |
|-------|------|--------------|----------|
| mistral:7b-instruct | 4.1GB | 8GB | Recommended, best balance |
| llama3.2:3b | 2.0GB | 4GB | Smaller systems |
| phi3:mini | 2.3GB | 4GB | Fastest, good quality |

**User Actions:**
- Select model from dropdown
- Click "Download Model"
- Wait for download to complete
- Or click "Skip download" to download later

**Technical Details:**
```bash
# Download model
ollama pull mistral:7b-instruct

# Check downloaded models
ollama list

# Test model
ollama run mistral:7b-instruct "Hello"
```

**Troubleshooting:**
- **Download fails:** Check internet connection
- **Out of disk space:** Free up space, try smaller model
- **Slow download:** Large files, be patient
- **Model won't run:** Check RAM requirements

---

### 5. User Account

**Purpose:** Create primary user account

**Fields:**
- **Username:** System login name (lowercase, no spaces)
- **Full Name:** Display name
- **Password:** Minimum 6 characters
- **Confirm Password:** Must match
- **Administrator:** Checkbox to grant sudo access

**Validation:**
- Username required, alphanumeric + underscore/dash
- Password required, minimum 6 characters
- Passwords must match
- Full name optional

**User Actions:**
- Enter username (e.g., "john")
- Enter full name (e.g., "John Smith")
- Enter password
- Confirm password
- Check "Make this user an administrator" (recommended)
- Click Next

**Technical Details:**
```bash
# User creation (Phase 2 implementation)
useradd -m -s /bin/bash -c "Full Name" username
echo "username:password" | chpasswd

# Add to admin group
usermod -aG sudo,homeai-admin username

# Set up home directory
cp -r /etc/skel/. /home/username/
chown -R username:username /home/username
```

**Security Notes:**
- Use strong passwords (8+ characters, mixed case, numbers, symbols)
- Administrator access required for system changes
- Non-admin users can still use Home AI features

---

### 6. Privacy Settings

**Purpose:** Configure telemetry and update preferences

**Options:**

1. **Send anonymous usage statistics**
   - Default: OFF
   - Collects: Feature usage, performance metrics, error reports
   - Does NOT collect: Personal data, file contents, conversations

2. **Automatically install security updates**
   - Default: ON
   - Installs: Security patches automatically
   - Requires approval: Feature updates, major versions

**User Actions:**
- Review privacy options
- Check/uncheck telemetry
- Check/uncheck auto-updates (recommended: ON)
- Click Next

**Technical Details:**
```json
// Saved to ~/.home_ai/config.json
{
  "telemetry_enabled": false,
  "auto_updates": true,
  "first_boot_complete": true
}
```

**Privacy Commitment:**
- No personal data collection
- No conversation logging
- No file content scanning
- Open-source audit trail
- User control over all data

---

### 7. Completion

**Purpose:** Confirm setup complete

**Content:**
- Success message
- Summary of configured settings
- Instructions to click Finish

**User Actions:**
- Review completion message
- Click Finish to start Home AI OS

**What Happens Next:**
1. Configuration saved to `~/.home_ai/config.json`
2. Wizard closes
3. Home AI main interface launches
4. System ready to use

---

## Running the Wizard

### Automatic (First Boot)

The wizard runs automatically on first boot if `~/.home_ai/config.json` doesn't exist or `first_boot: true`.

### Manual Launch

```bash
# Run wizard manually
/opt/home-ai/venv/bin/python /usr/local/bin/first-boot-wizard.py

# Or via launcher
homeai-first-boot-wizard
```

### Skip Wizard

To skip the wizard (advanced users):

```bash
# Create config file
mkdir -p ~/.home_ai
cat > ~/.home_ai/config.json << EOF
{
  "version": "0.1.0",
  "first_boot_complete": true,
  "username": "$(whoami)",
  "telemetry_enabled": false,
  "auto_updates": true
}
EOF
```

---

## Configuration File

**Location:** `~/.home_ai/config.json`

**Format:**
```json
{
  "version": "0.1.0",
  "first_boot_complete": true,
  "username": "john",
  "fullname": "John Smith",
  "telemetry_enabled": false,
  "auto_updates": true,
  "gpu_driver": "nvidia",
  "ai_model": "mistral:7b-instruct",
  "network_configured": true
}
```

**Fields:**
- `version`: Config format version
- `first_boot_complete`: Skip wizard if true
- `username`: Primary user
- `fullname`: Display name
- `telemetry_enabled`: Usage statistics
- `auto_updates`: Automatic security updates
- `gpu_driver`: Installed driver type
- `ai_model`: Downloaded AI model
- `network_configured`: Network setup complete

---

## Troubleshooting

### Wizard Won't Start

**Symptoms:** Wizard doesn't appear on first boot

**Solutions:**
1. Check if config exists: `cat ~/.home_ai/config.json`
2. Delete config to re-run: `rm ~/.home_ai/config.json`
3. Run manually: `/usr/local/bin/first-boot-wizard.py`
4. Check logs: `journalctl -u homeai-agent`

### Network Page Stuck

**Symptoms:** Can't proceed past network page

**Solutions:**
1. Click "Open Network Manager"
2. Configure connection
3. Click "Check Network" button (if available)
4. Skip if offline: Edit config manually

### GPU Installation Fails

**Symptoms:** Driver installation errors

**Solutions:**
1. Select "Skip installation"
2. Install drivers manually after setup
3. Check Secure Boot status (disable for NVIDIA)
4. Review logs: `dmesg | grep -i gpu`

### Model Download Fails

**Symptoms:** Download errors or timeouts

**Solutions:**
1. Check internet connection
2. Try smaller model (phi3:mini)
3. Skip and download later: `ollama pull mistral:7b-instruct`
4. Check disk space: `df -h`

### User Creation Fails

**Symptoms:** Can't create user account

**Solutions:**
1. Use different username (may be taken)
2. Ensure password meets requirements
3. Check passwords match
4. Skip wizard, create user manually:
   ```bash
   sudo useradd -m -s /bin/bash username
   sudo passwd username
   ```

### Wizard Crashes

**Symptoms:** Wizard closes unexpectedly

**Solutions:**
1. Check Python/PyQt6 installed
2. Run from terminal to see errors
3. Check logs: `~/.home_ai/wizard.log`
4. Skip wizard, configure manually

---

## Advanced Configuration

### Pre-seed Configuration

For automated deployments, pre-create config:

```bash
# Create config before first boot
mkdir -p /home/newuser/.home_ai
cat > /home/newuser/.home_ai/config.json << EOF
{
  "version": "0.1.0",
  "first_boot_complete": true,
  "username": "newuser",
  "telemetry_enabled": false,
  "auto_updates": true
}
EOF
chown -R newuser:newuser /home/newuser/.home_ai
```

### Unattended Setup

For enterprise deployments:

```bash
# Disable wizard
systemctl disable homeai-first-boot.service

# Pre-configure all settings
# (See enterprise deployment guide)
```

### Custom Wizard Pages

To add custom pages (Phase 3):

```python
# Add to first-boot-wizard.py
class CustomPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Custom Setup")
        # Add custom widgets

# Add to wizard
wizard.addPage(CustomPage())
```

---

## Phase 2 Enhancements

Planned improvements:

1. **Real Driver Installation**
   - Actual NVIDIA driver installation
   - AMD driver configuration
   - Secure Boot handling
   - Reboot prompts

2. **Real Model Downloads**
   - Ollama integration
   - Progress tracking
   - Bandwidth throttling
   - Resume support

3. **User Creation**
   - Actual useradd/passwd calls
   - Group management
   - Home directory setup
   - SSH key generation

4. **System Integration**
   - LightDM user configuration
   - Autologin setup
   - Session selection
   - Desktop customization

5. **Recovery Options**
   - Wizard reset button
   - Safe mode boot
   - Configuration backup
   - Rollback support

---

## See Also

- [BUILD.md](BUILD.md) - Building Home AI OS
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [README.md](README.md) - Project overview
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
