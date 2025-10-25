# Safety and Security Considerations

## Overview

Home AI is designed with a **security-first, deny-by-default** approach. This document outlines the safety features, threat model, and best practices.

## Core Safety Principles

### 1. Deny-by-Default
Every potentially dangerous operation is **disabled by default**. You must explicitly enable each capability through toggle controls.

**Default State:**
- ✅ Read operations: Allowed
- ❌ Write operations: Blocked
- ❌ Delete operations: Blocked
- ❌ Network access: Blocked
- ❌ Financial operations: Blocked
- ❌ System modifications: Blocked

### 2. Defense in Depth

Multiple layers of protection:

```
User Request
    ↓
Command Parser (sanitization)
    ↓
Policy Engine (permission check)
    ↓
Rate Limiter (abuse prevention)
    ↓
Confirmation Dialog (user approval)
    ↓
Sandbox Test (dry run)
    ↓
Audit Logger (record action)
    ↓
Executor (perform action)
    ↓
Audit Logger (record result)
```

### 3. Emergency Controls

**Killswitch:** `Ctrl+Alt+Shift+K`
- Immediately pauses all operations
- Blocks new actions
- Logs emergency event
- Requires manual resume

**Manual Override:**
- All automated actions can be manually stopped
- UI remains responsive during operations
- Background threads are cancellable

## Threat Model

### What We Protect Against

#### 1. Accidental Damage
**Threat:** User accidentally requests destructive operation
**Mitigation:**
- Confirmation dialogs for all destructive actions
- Dry-run preview before execution
- Undo stack for reversible operations
- Automatic backups before modifications

#### 2. Runaway Automation
**Threat:** Infinite loops or excessive automation
**Mitigation:**
- Rate limiting (60 actions/minute)
- Action count monitoring
- Automatic pause on suspicious patterns
- Killswitch for immediate stop

#### 3. LLM Misinterpretation
**Threat:** LLM misunderstands command and performs wrong action
**Mitigation:**
- Confidence thresholds (require 85%+ confidence)
- Confirmation for low-confidence actions
- Explicit action preview before execution
- User can review and modify parsed commands

#### 4. Malicious Prompts
**Threat:** Adversarial prompts attempting to bypass safety
**Mitigation:**
- Policy engine enforces hard limits (LLM cannot override)
- Input sanitization and validation
- Command injection prevention
- Restricted path access

#### 5. Financial Loss
**Threat:** Unauthorized or accidental financial transactions
**Mitigation:**
- Master financial toggle (OFF by default)
- Paper trading only in v1 (no real money)
- Transaction limits ($10 single, $50 daily, $500 monthly)
- 2FA confirmation required
- 5-minute cooldown between transactions
- Read-only mode for account viewing

#### 6. Data Exfiltration
**Threat:** Sensitive data sent to external services
**Mitigation:**
- Local LLM only (no cloud APIs)
- Network access disabled by default
- Audit logging of all network requests
- No credential storage in plaintext
- Windows Credential Manager integration

#### 7. Privilege Escalation
**Threat:** Gaining unauthorized system access
**Mitigation:**
- Runs in user mode by default
- Elevation only on-demand for specific operations
- No automatic privilege escalation
- Restricted system directory access

### What We Don't Protect Against

❌ **Physical access to machine** - If attacker has physical access, they can bypass software controls

❌ **Compromised OS** - If Windows is already compromised, this application cannot provide security

❌ **Social engineering** - If user is tricked into enabling dangerous toggles

❌ **Zero-day exploits** - Unknown vulnerabilities in dependencies

## Security Features

### Audit Logging

**Immutable Append-Only Logs**
- Every action logged with full context
- Hash chain prevents tampering
- Timestamp, user, action, status, details
- Sensitive data redacted (passwords, keys, etc.)

**Log Verification:**
```python
from home_ai.security.audit_logger import get_audit_logger
audit_logger = get_audit_logger()
is_valid = audit_logger.verify_chain()  # Returns True if untampered
```

**Log Location:** `~/.home_ai/logs/audit/audit_YYYY-MM-DD.jsonl`

### Policy Engine

**Permission Matrix:**
```python
Action → Policy Check → Allowed/Denied

Examples:
- Read file in workspace → ✅ Allowed
- Write file in workspace → ❌ Denied (toggle off)
- Delete file in C:\Windows → ❌ Denied (restricted path)
- Network request → ❌ Denied (toggle off)
- Terminate process → ❌ Denied (toggle off)
```

**Path Restrictions:**
- **Restricted (always blocked):** `C:\Windows`, `C:\Program Files`, system directories
- **Whitelisted (allowed if toggle on):** `C:\Users\{username}\Documents\AI_Workspace`
- **Custom whitelist:** Configurable in settings

### Rate Limiting

**Token Bucket Algorithm:**
- 60 actions per minute (default)
- Separate limits per scope (file, network, process, etc.)
- Automatic cooldown when limit exceeded
- Prevents infinite loops and abuse

**Current Rate:**
```python
from home_ai.security.rate_limiter import get_rate_limiter
rate_limiter = get_rate_limiter()
current_rate = rate_limiter.get_current_rate("global")  # Actions/minute
```

### Encryption

**Configuration Encryption:**
- Settings stored encrypted with Fernet (symmetric encryption)
- Encryption key stored in `~/.home_ai/config/.key` (600 permissions)
- Sensitive data never in plaintext

**Credential Storage:**
- Windows Credential Manager integration
- DPAPI encryption for local secrets
- No hardcoded credentials

### Sandbox Mode

**Dry-Run Testing:**
- Test actions in isolated environment first
- Preview changes before committing
- Rollback on failure
- Backup before modifications

**File Operations:**
- Copy files to temp location
- Test modifications
- Only commit if successful
- Keep backup for undo

## Best Practices

### For Users

1. **Start in Safe Mode**
   - Keep default settings initially
   - Only enable toggles you understand
   - Test with non-critical data first

2. **Review Actions**
   - Always review confirmation dialogs
   - Check dry-run previews
   - Verify file paths and parameters

3. **Monitor Audit Logs**
   - Regularly check logs for unexpected actions
   - Verify log chain integrity
   - Investigate suspicious patterns

4. **Use Killswitch**
   - Memorize: `Ctrl+Alt+Shift+K`
   - Test it works before relying on automation
   - Use immediately if something seems wrong

5. **Backup Important Data**
   - System backups before enabling write operations
   - Keep copies of critical files
   - Test restore procedures

6. **Limit Financial Access**
   - Keep master financial toggle OFF
   - Use paper trading only
   - Set conservative transaction limits
   - Enable 2FA

### For Developers

1. **Never Bypass Policy Engine**
   - All actions must go through policy checks
   - No direct OS calls without permission
   - Enforce at module boundaries

2. **Validate All Inputs**
   - Sanitize user inputs
   - Validate file paths
   - Check parameter types and ranges
   - Prevent command injection

3. **Log Everything**
   - Log all actions (attempted, executed, failed)
   - Include full context
   - Redact sensitive data
   - Use structured logging

4. **Fail Securely**
   - Default to deny on errors
   - Don't expose error details to LLM
   - Log failures for debugging
   - Graceful degradation

5. **Test Security**
   - Unit tests for policy engine
   - Fuzzing for input validation
   - Penetration testing
   - Code review for security issues

## Incident Response

### If Killswitch Activated

1. **Assess Situation**
   - Check audit logs for recent actions
   - Review system state
   - Identify what triggered killswitch

2. **Investigate**
   - Verify log chain integrity
   - Check for unauthorized actions
   - Review toggle states

3. **Remediate**
   - Undo problematic actions if possible
   - Restore from backup if needed
   - Adjust toggles to prevent recurrence

4. **Resume**
   - Only resume when situation is understood
   - Consider more restrictive settings
   - Monitor closely after resume

### If Suspicious Activity Detected

1. **Pause System**
   - Use killswitch immediately
   - Stop all automation

2. **Review Logs**
   - Check audit logs for anomalies
   - Verify all actions were authorized
   - Look for patterns

3. **Check Integrity**
   - Verify audit log chain
   - Check file modifications
   - Review network activity

4. **Report**
   - Document findings
   - Report bugs/vulnerabilities
   - Share lessons learned

## Compliance and Privacy

### Data Collection

**What We Collect:**
- System statistics (CPU, memory, disk)
- Process information
- User actions and commands
- LLM interactions

**What We DON'T Collect:**
- Personal identifiable information (PII)
- Passwords or credentials
- Financial account details
- Browsing history (unless explicitly requested)

**Data Storage:**
- All data stored locally
- No cloud uploads
- Encrypted at rest
- User controls retention

### Privacy

- **Local LLM:** All inference happens locally, no data sent to cloud
- **No Telemetry:** No usage statistics sent to developers
- **No Tracking:** No analytics or tracking code
- **User Control:** User owns all data and can delete anytime

## Security Updates

### Keeping Secure

1. **Update Regularly**
   ```bash
   git pull
   poetry update
   ```

2. **Monitor Dependencies**
   - Check for security advisories
   - Update vulnerable packages
   - Review changelogs

3. **Review Logs**
   - Check for failed login attempts
   - Monitor unusual patterns
   - Verify log integrity

4. **Backup Configuration**
   - Export settings regularly
   - Keep backup of encryption key
   - Document custom toggles

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT** open a public GitHub issue
2. Email security details to: [security contact]
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work on a fix.

## Conclusion

Security is a shared responsibility. The system provides strong defaults and multiple layers of protection, but users must:

- Understand what they're enabling
- Review actions before approval
- Monitor system behavior
- Use killswitch when needed
- Keep software updated

**Remember: The emergency killswitch is `Ctrl+Alt+Shift+K`**
