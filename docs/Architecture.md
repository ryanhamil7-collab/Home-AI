# Architecture

## Overview

Home AI is built with a **security-first, modular architecture** that enforces deny-by-default permissions through a central policy engine.

## Design Principles

### 1. Security First
- **Deny-by-default**: All operations blocked unless explicitly allowed
- **Defense in depth**: Multiple layers of security checks
- **Immutable audit trail**: Tamper-evident logging
- **Emergency controls**: Killswitch for immediate pause

### 2. Modularity
- **Clear boundaries**: Each module has a single responsibility
- **Loose coupling**: Modules communicate through well-defined interfaces
- **Easy testing**: Each module can be tested independently
- **Extensibility**: New features can be added without modifying core

### 3. User Control
- **Granular toggles**: Fine-grained control over every capability
- **Transparency**: All actions logged and visible
- **Reversibility**: Undo/rollback where possible
- **Confirmation**: User approval for destructive operations

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Interface                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PyQt6 GUI   │  │ System Tray  │  │CustomTkinter │      │
│  │  (Main App)  │  │  (Quick      │  │  (Toggles)   │      │
│  │              │  │   Actions)   │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Command Layer                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              LLM Chat Interface                       │   │
│  │  • Natural language understanding                     │   │
│  │  • Command parsing and intent extraction             │   │
│  │  • Confidence scoring                                 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Security Gateway                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Policy Engine │  │ Rate Limiter │  │Audit Logger  │      │
│  │              │  │              │  │              │      │
│  │• Permission  │  │• Token bucket│  │• Hash chain  │      │
│  │  checks      │  │• Per-scope   │  │• Immutable   │      │
│  │• Path rules  │  │  limits      │  │• Tamper-proof│      │
│  │• Killswitch  │  │• Cooldowns   │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Execution Layer                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  File    │ │ Process  │ │ Network  │ │Financial │       │
│  │  Ops     │ │  Mgmt    │ │  Access  │ │  Ops     │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Window   │ │ Browser  │ │ Registry │ │ Hardware │       │
│  │  Mgmt    │ │  Auto    │ │  Access  │ │  Control │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    System Monitoring                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  • CPU, Memory, Disk, Network stats                  │   │
│  │  • Process tracking                                   │   │
│  │  • Behavior analysis                                  │   │
│  │  • Alert thresholds                                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### Configuration System (`core/config.py`)

**Responsibilities:**
- Load/save application settings
- Manage toggle states
- Encrypt sensitive configuration
- Provide global settings access

**Key Classes:**
- `Settings`: Main configuration container
- `SystemToggles`: System-level permissions
- `FinancialToggles`: Financial operation controls
- `LLMConfig`: LLM engine settings

**Design Decisions:**
- Pydantic for validation and type safety
- Encrypted storage using Fernet
- Singleton pattern for global access
- Environment variable overrides

### Policy Engine (`security/policy_engine.py`)

**Responsibilities:**
- Enforce permission checks
- Validate action parameters
- Implement killswitch
- Coordinate with audit logger

**Key Classes:**
- `PolicyEngine`: Central permission gateway
- `Action`: Typed action with scope and risk
- `ActionScope`: Categorization of operations
- `ActionRisk`: Risk level classification

**Flow:**
```
Action Request
    ↓
Check if paused (killswitch)
    ↓
Check scope-specific permissions
    ↓
Validate parameters (paths, amounts, etc.)
    ↓
Check rate limits
    ↓
Log attempt
    ↓
Return (allowed, reason)
```

**Design Decisions:**
- Deny-by-default: Returns False unless explicitly allowed
- Typed actions: Prevents ambiguity
- Immutable decisions: Once denied, cannot be overridden
- Audit integration: Every check is logged

### Audit Logger (`security/audit_logger.py`)

**Responsibilities:**
- Log all actions with full context
- Maintain hash chain for tamper detection
- Redact sensitive information
- Provide search and verification

**Key Classes:**
- `AuditLogger`: Main logging interface
- `AuditEntry`: Single log entry with hash

**Hash Chain:**
```
Entry 1: hash(data1 + "0000...")
Entry 2: hash(data2 + hash1)
Entry 3: hash(data3 + hash2)
...
```

**Design Decisions:**
- Append-only: No modifications or deletions
- Hash chain: Detects tampering
- Daily rotation: Manageable file sizes
- JSONL format: Easy parsing and streaming

### Rate Limiter (`security/rate_limiter.py`)

**Responsibilities:**
- Prevent abuse and runaway automation
- Track actions per scope
- Enforce cooldown periods
- Provide usage statistics

**Algorithm:**
Token bucket with sliding window:
```
Window: 60 seconds
Capacity: 60 actions
Refill: Automatic as time passes
```

**Design Decisions:**
- Per-scope limits: Different limits for different operations
- Sliding window: More accurate than fixed windows
- Thread-safe: Uses locks for concurrent access
- Graceful degradation: Provides wait time when blocked

### LLM Engine (`llm/ollama_client.py`)

**Responsibilities:**
- Manage Ollama server lifecycle
- Handle model loading and switching
- Stream responses to UI
- Maintain conversation context

**Key Classes:**
- `OllamaClient`: Main LLM interface
- `ModelInfo`: Model metadata

**Features:**
- Auto-start Ollama server
- GPU detection and model selection
- Streaming for responsive UI
- Conversation history management

**Design Decisions:**
- Local-only: No cloud APIs
- Model hot-swapping: Change models without restart
- Streaming: Better UX for long responses
- Context management: Maintains conversation flow

### System Monitor (`monitoring/system_monitor.py`)

**Responsibilities:**
- Track system resources
- Monitor processes
- Detect anomalies
- Provide real-time stats

**Key Classes:**
- `SystemMonitor`: Main monitoring interface
- `SystemStats`: Snapshot of system state
- `ProcessInfo`: Process details

**Design Decisions:**
- Read-only: No system modifications
- Background thread: Continuous monitoring
- Configurable interval: Balance accuracy vs overhead
- Threshold alerts: Warn on high usage

### Killswitch (`core/killswitch.py`)

**Responsibilities:**
- Register global hotkey
- Immediately pause all operations
- Coordinate with policy engine
- Log emergency events

**Design Decisions:**
- Global hotkey: Works even when app not focused
- Immediate effect: Pauses before next action
- Logged: Emergency events are audited
- Reversible: Can resume after investigation

## Data Flow

### User Command Flow

```
1. User types command in chat
   ↓
2. LLM parses command → Action
   ↓
3. PolicyEngine.check_permission(action)
   ↓
4. RateLimiter.check_rate_limit(scope)
   ↓
5. AuditLogger.log_action("attempted")
   ↓
6. If allowed: Execute action
   ↓
7. AuditLogger.log_action("executed" | "failed")
   ↓
8. Return result to user
```

### Killswitch Flow

```
1. User presses Ctrl+Alt+Shift+K
   ↓
2. Killswitch.on_activate()
   ↓
3. PolicyEngine.pause_all()
   ↓
4. All pending actions blocked
   ↓
5. AuditLogger.log_action("emergency_pause")
   ↓
6. UI shows paused state
   ↓
7. User investigates issue
   ↓
8. User manually resumes (if safe)
```

### Monitoring Flow

```
1. SystemMonitor starts background thread
   ↓
2. Every 1 second:
   - Collect CPU, memory, disk, network stats
   - Get process list
   - Check thresholds
   ↓
3. Store in history (max 1 hour)
   ↓
4. UI polls for latest stats
   ↓
5. Display in monitoring tab
```

## Security Model

### Trust Boundaries

```
Untrusted:
- User input
- LLM output
- External files
- Network data

Trusted:
- Configuration (after validation)
- Audit logs (verified chain)
- System APIs (after permission check)

Security Gateway:
- Policy Engine validates all crossings
- Rate Limiter prevents abuse
- Audit Logger records all attempts
```

### Permission Model

**Hierarchy:**
```
Master Toggles (e.g., master_financial_toggle)
    ↓
Category Toggles (e.g., allow_file_write)
    ↓
Path/Domain Whitelists
    ↓
Rate Limits
    ↓
User Confirmation (for high-risk)
```

**Example: File Write**
```
1. Check: system_toggles.allow_file_write
2. Check: path not in restricted_paths
3. Check: path in whitelisted_paths (if whitelist exists)
4. Check: rate limit not exceeded
5. Confirm: user approves (if configured)
6. Execute: perform write
7. Backup: keep copy for undo
```

## Extension Points

### Adding New Capabilities

1. **Define Action Scope**
   ```python
   class ActionScope(Enum):
       NEW_FEATURE = "new_feature"
   ```

2. **Add Toggles**
   ```python
   class SystemToggles(BaseModel):
       allow_new_feature: bool = False
   ```

3. **Implement Permission Check**
   ```python
   def _check_new_feature_permission(self, action):
       if not self.settings.system_toggles.allow_new_feature:
           return False, "New feature disabled"
       return True, "Allowed"
   ```

4. **Create Executor**
   ```python
   class NewFeatureExecutor:
       def execute(self, action):
           # Implementation
           pass
   ```

5. **Add Tests**
   ```python
   def test_new_feature_permission():
       # Test cases
       pass
   ```

### Adding New Toggles

1. Add to appropriate config class
2. Set safe default value
3. Document in TOGGLES.md
4. Add permission check in PolicyEngine
5. Add UI control (Phase 2+)
6. Add tests

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**
   - Only load modules when needed
   - Defer heavy initialization

2. **Caching**
   - Cache permission checks (with TTL)
   - Cache model responses (optional)
   - Cache system stats (1 second)

3. **Background Processing**
   - LLM inference in separate thread
   - Monitoring in background thread
   - Audit logging is async-friendly

4. **Resource Limits**
   - Rate limiting prevents overload
   - Context window limits memory
   - Log rotation prevents disk fill

### Scalability

**Current Design:**
- Single-user, single-machine
- Local LLM (no API rate limits)
- Lightweight monitoring (< 1% CPU)

**Future Considerations:**
- Multi-user support (separate configs)
- Distributed monitoring
- Cloud LLM fallback

## Testing Strategy

### Unit Tests
- Each module tested independently
- Mock external dependencies
- Focus on edge cases and error handling

### Integration Tests
- Test module interactions
- Verify security gateway works end-to-end
- Test killswitch effectiveness

### Security Tests
- Attempt to bypass policy engine
- Test audit log tampering detection
- Verify rate limiting works
- Test privilege escalation prevention

## Deployment

### Development
```bash
poetry install
poetry run python -m home_ai.main --debug
```

### Production
```bash
poetry install --no-dev
poetry run python -m home_ai.main
```

### Packaging (Future)
```bash
poetry build
pyinstaller home_ai.spec
```

## Future Architecture

### Phase 2+

**Planned Additions:**
- CustomTkinter toggle panel (separate process)
- System tray with quick actions
- Plugin system for extensions
- Remote monitoring dashboard
- Multi-machine coordination

**Architectural Changes:**
- Event bus for loose coupling
- Plugin API with sandboxing
- RESTful API for remote control
- WebSocket for real-time updates

## Conclusion

The architecture prioritizes **security, transparency, and user control** while maintaining **modularity and extensibility**. The deny-by-default policy engine ensures that no operation can bypass security checks, and the immutable audit trail provides accountability.

Key architectural decisions:
- ✅ Security gateway for all operations
- ✅ Deny-by-default permissions
- ✅ Immutable audit logging
- ✅ Emergency killswitch
- ✅ Modular, testable design
- ✅ Local-first (no cloud dependencies)
