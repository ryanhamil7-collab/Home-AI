# Home AI - Windows LLM PC Control System

A sophisticated Windows PC control system powered by local LLMs (Mistral/Llama via Ollama) with granular toggle controls for every feature.

## 🚨 IMPORTANT: SAFE MODE BY DEFAULT

**This system starts in SAFE MODE with all destructive operations disabled by default.**

- ✅ Read-only operations: ENABLED
- ❌ File write/delete: DISABLED
- ❌ Process termination: DISABLED
- ❌ Network access: DISABLED
- ❌ Financial operations: DISABLED (master toggle OFF)
- ❌ Registry modifications: DISABLED

**Emergency Killswitch:** `Ctrl+Alt+Shift+K` - Immediately pauses all operations

## Features (Phase 1)

### ✅ Implemented
- **LLM Chat Interface** - Streaming chat with local Ollama models
- **System Monitoring** - Real-time CPU, memory, disk, network, and process monitoring (read-only)
- **Policy Engine** - Deny-by-default security with granular permission controls
- **Audit Logging** - Immutable append-only logs with hash chain verification
- **Rate Limiting** - Prevents runaway automation (60 actions/minute default)
- **Emergency Killswitch** - Global hotkey to immediately pause all operations
- **PyQt6 GUI** - Professional tabbed interface with dark theme
- **Auto GPU Detection** - Automatically selects optimal model based on hardware

### 🚧 Coming in Phase 2+
- CustomTkinter toggle control panel
- System tray integration
- Window management (resize, move, switch)
- File operations (with confirmations and backups)
- Browser automation (safe profiles only)
- Task automation and scheduling
- Financial integrations (paper trading only)

## Installation

### Prerequisites

1. **Windows 10/11** (64-bit)
2. **Python 3.11** or higher
3. **Ollama** - Install from [https://ollama.ai](https://ollama.ai)
4. **Poetry** (recommended) or pip

### Quick Start

```bash
# Clone the repository
git clone https://github.com/ryanhamil7-collab/Home-AI.git
cd Home-AI

# Install with Poetry (recommended)
poetry install

# Or install with pip
pip install -e .

# Create .env file (optional for Phase 1)
cp .env.example .env

# Run the application
poetry run python -m home_ai.main

# Or in CLI mode for testing
poetry run python -m home_ai.main --mode cli
```

### First Run

On first run, the system will:
1. Check if Ollama is installed and running
2. Detect your GPU (NVIDIA CUDA preferred, CPU fallback)
3. Select optimal model based on available VRAM:
   - **8GB+ VRAM**: `mistral:7b-instruct`
   - **4-8GB VRAM**: `llama3.2:3b`
   - **<4GB or CPU**: `phi3:mini`
4. Download the selected model (may take a few minutes)
5. Start in SAFE MODE with all destructive operations disabled

## Usage

### GUI Mode (Default)

```bash
poetry run python -m home_ai.main
```

The GUI provides:
- **Chat Tab**: Streaming chat with the LLM
- **Monitoring Tab**: Real-time system statistics and process list
- **Toggles Tab**: View current toggle states (editing in future version)
- **Audit Logs Tab**: View recent actions and security events

### CLI Mode (Testing)

```bash
poetry run python -m home_ai.main --mode cli
```

Interactive command-line chat interface for testing.

### Debug Mode

```bash
poetry run python -m home_ai.main --debug
```

Enables verbose debug logging.

## Configuration

Configuration is stored in `~/.home_ai/config/settings.json` (encrypted).

### Key Settings

```python
# LLM Configuration
preferred_model = "mistral:7b-instruct"
temperature = 0.7
context_window = 4096

# Security
enable_audit_log = True
require_confirmation = True
sandbox_mode = True
rate_limit_actions_per_minute = 60

# Emergency Killswitch
emergency_killswitch_key = "ctrl+alt+shift+k"
```

### Editing Toggles

For Phase 1, edit toggles by modifying the config file or using the Settings class:

```python
from home_ai.core.config import get_settings

settings = get_settings()
settings.system_toggles.allow_file_read = True
settings.system_toggles.allow_file_write = False  # Keep disabled
settings.save_to_file()
```

## Safety Features

### 1. Deny-by-Default Policy
Every potentially dangerous operation must be explicitly enabled. The policy engine blocks all actions by default.

### 2. Emergency Killswitch
Press `Ctrl+Alt+Shift+K` at any time to immediately pause all operations. The system will:
- Stop all in-progress actions
- Block new actions
- Log the emergency pause
- Require manual resume

### 3. Audit Logging
Every action is logged with:
- Timestamp
- Action type and details
- User who initiated
- Status (attempted, executed, blocked, failed)
- Hash chain for tamper detection

Verify log integrity: Tools → Verify Audit Log

### 4. Rate Limiting
Maximum 60 actions per minute by default. Prevents:
- Runaway automation
- Accidental loops
- Abuse

### 5. Path Restrictions
File operations are restricted to:
- **Whitelisted**: `C:\Users\{username}\Documents\AI_Workspace`
- **Blocked**: `C:\Windows`, `C:\Program Files`, system directories

### 6. Financial Safety
- Master toggle OFF by default
- Paper trading only (no real transactions in v1)
- Transaction limits: $10 single, $50 daily, $500 monthly
- 2FA confirmation required
- 5-minute cooldown between transactions

## Architecture

```
home_ai/
├── core/           # Config, killswitch, event bus
├── security/       # Policy engine, audit logger, rate limiter
├── llm/            # Ollama client, streaming, context management
├── ui/             # PyQt6 GUI, system tray
├── monitoring/     # System stats, process tracking
├── automation/     # Actions, executors (Phase 2+)
├── apps/           # Per-app controls (Phase 2+)
├── workflows/      # Scheduling, macros (Phase 2+)
├── browser/        # Selenium automation (Phase 2+)
└── finance/        # Paper trading (Phase 2+)
```

### Key Components

- **PolicyEngine**: Central gateway for all operations, enforces permissions
- **AuditLogger**: Immutable append-only logs with hash chain
- **RateLimiter**: Token bucket rate limiting per scope
- **OllamaClient**: LLM inference with streaming and model management
- **SystemMonitor**: Read-only monitoring of system resources
- **Killswitch**: Emergency pause mechanism

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Quality

```bash
# Format code
poetry run black src/

# Lint
poetry run ruff check src/

# Type check
poetry run mypy src/
```

### Project Structure

```bash
Home-AI/
├── src/home_ai/        # Source code
├── tests/              # Unit tests
├── docs/               # Documentation
├── config/             # Config templates
├── data/               # Runtime data
├── logs/               # Application logs
└── pyproject.toml      # Dependencies
```

## Troubleshooting

### Ollama Not Found

```bash
# Install Ollama from https://ollama.ai
# Or check if it's in PATH
ollama --version
```

### Model Download Fails

```bash
# Manually pull model
ollama pull mistral:7b-instruct

# Or use smaller model
ollama pull phi3:mini
```

### GPU Not Detected

The system will automatically fall back to CPU mode. For NVIDIA GPU:

```bash
# Check CUDA installation
nvidia-smi

# Verify Ollama sees GPU
ollama run mistral:7b-instruct "test"
```

### Permission Errors

Run as Administrator for operations that require elevation (service control, registry, etc.). The system will request elevation on-demand.

### Killswitch Not Working

Ensure `pynput` is installed:

```bash
poetry add pynput
```

## Documentation

- **[SAFETY.md](docs/SAFETY.md)** - Security considerations and threat model
- **[TOGGLES.md](docs/TOGGLES.md)** - Complete toggle reference
- **[Architecture.md](docs/Architecture.md)** - System architecture and design decisions

## Roadmap

### Phase 1: Core Foundation ✅
- [x] LLM chat interface
- [x] System monitoring (read-only)
- [x] Policy engine and security
- [x] Audit logging
- [x] Emergency killswitch
- [x] PyQt6 GUI

### Phase 2: Safe Interactions (Next)
- [ ] CustomTkinter toggle panel
- [ ] System tray integration
- [ ] Window management
- [ ] File operations (read-only first)
- [ ] Application launcher

### Phase 3: Controlled Modifications
- [ ] File write/delete (with confirmations)
- [ ] Browser automation
- [ ] Task automation
- [ ] Macro recording

### Phase 4: Advanced Features
- [ ] Financial integrations (paper trading)
- [ ] Advanced workflows
- [ ] Multi-monitor support
- [ ] Voice control

## Contributing

This is a personal project for educational purposes. Contributions welcome via pull requests.

## License

MIT License - See LICENSE file for details.

## Disclaimer

**This software is for educational and research purposes only.**

- ⚠️ **Paper trading only** - No real financial transactions
- ⚠️ **Use at your own risk** - Test thoroughly before relying on automation
- ⚠️ **No warranty** - Provided as-is without guarantees
- ⚠️ **Security** - Review code before granting system access

## Support

For issues, questions, or feedback:
- GitHub Issues: [https://github.com/ryanhamil7-collab/Home-AI/issues](https://github.com/ryanhamil7-collab/Home-AI/issues)
- Documentation: See `docs/` directory

---

**Remember: The emergency killswitch is `Ctrl+Alt+Shift+K`**
