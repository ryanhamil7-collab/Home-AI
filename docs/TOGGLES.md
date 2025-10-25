# Toggle Controls Reference

Complete reference for all toggle controls in Home AI.

## Overview

Toggles control what operations the system is allowed to perform. All toggles start in the **SAFE** position (disabled for destructive operations).

**Toggle States:**
- ✅ **ENABLED** - Operation is allowed (subject to other checks)
- ❌ **DISABLED** - Operation is blocked by policy engine

## System Toggles

### Process Management

#### `allow_process_termination`
- **Default:** ❌ DISABLED
- **Risk:** HIGH
- **Description:** Allow terminating running processes
- **Use Cases:** Killing frozen applications, stopping services
- **Risks:** Can terminate critical system processes, cause data loss
- **Recommendation:** Only enable when needed, disable after use

#### `allow_process_creation`
- **Default:** ❌ DISABLED
- **Risk:** MEDIUM
- **Description:** Allow launching new processes/applications
- **Use Cases:** Opening applications, running scripts
- **Risks:** Can launch malware, execute arbitrary code
- **Recommendation:** Enable for application launching, use whitelist

#### `allow_service_control`
- **Default:** ❌ DISABLED
- **Risk:** HIGH
- **Description:** Allow starting/stopping Windows services
- **Use Cases:** Managing system services
- **Risks:** Can disable security services, break system functionality
- **Recommendation:** Requires admin privileges, use with extreme caution

#### `allow_startup_modification`
- **Default:** ❌ DISABLED
- **Risk:** HIGH
- **Description:** Allow modifying startup programs
- **Use Cases:** Managing autostart applications
- **Risks:** Can add malware to startup, disable security software
- **Recommendation:** Manual review required for all changes

### File System

#### `allow_file_read`
- **Default:** ✅ ENABLED
- **Risk:** SAFE
- **Description:** Allow reading file contents
- **Use Cases:** Viewing documents, analyzing files
- **Risks:** Minimal (read-only)
- **Recommendation:** Safe to keep enabled

#### `allow_file_write`
- **Default:** ❌ DISABLED
- **Risk:** MEDIUM
- **Description:** Allow creating and modifying files
- **Use Cases:** Saving documents, editing files
- **Risks:** Can overwrite important files, data loss
- **Recommendation:** Enable with path whitelist, backup before modifications

#### `allow_file_delete`
- **Default:** ❌ DISABLED
- **Risk:** HIGH
- **Description:** Allow deleting files
- **Use Cases:** Cleaning up, removing temporary files
- **Risks:** Permanent data loss, can delete system files
- **Recommendation:** Use recycle bin only, never permanent delete

#### `allow_folder_creation`
- **Default:** ❌ DISABLED
- **Risk:** LOW
- **Description:** Allow creating new folders
- **Use Cases:** Organizing files, creating project directories
- **Risks:** Minimal (can clutter filesystem)
- **Recommendation:** Safe to enable in whitelisted paths

#### `allow_file_execution`
- **Default:** ❌ DISABLED
- **Risk:** CRITICAL
- **Description:** Allow executing files (.exe, .bat, .ps1, etc.)
- **Use Cases:** Running scripts, launching installers
- **Risks:** Can execute malware, compromise system
- **Recommendation:** Only enable for trusted, verified files

### Network

#### `allow_internet_access`
- **Default:** ❌ DISABLED
- **Risk:** MEDIUM
- **Description:** Allow internet connections
- **Use Cases:** Web browsing, API calls, downloads
- **Risks:** Data exfiltration, malware download
- **Recommendation:** Enable with domain whitelist, monitor traffic

#### `allow_local_network`
- **Default:** ❌ DISABLED
- **Risk:** LOW
- **Description:** Allow local network (LAN) connections
- **Use Cases:** Network file shares, local services
- **Risks:** Can access other machines on network
- **Recommendation:** Enable for specific IPs only

#### `allow_firewall_modification`
- **Default:** ❌ DISABLED
- **Risk:** CRITICAL
- **Description:** Allow modifying Windows Firewall rules
- **Use Cases:** Opening ports, creating exceptions
- **Risks:** Can disable firewall, expose system
- **Recommendation:** Never enable, manual configuration only

### Registry

#### `allow_registry_read`
- **Default:** ❌ DISABLED
- **Risk:** LOW
- **Description:** Allow reading Windows Registry
- **Use Cases:** Checking settings, reading configuration
- **Risks:** Can expose sensitive information
- **Recommendation:** Enable for specific keys only

#### `allow_registry_write`
- **Default:** ❌ DISABLED
- **Risk:** CRITICAL
- **Description:** Allow modifying Windows Registry
- **Use Cases:** Changing system settings, installing software
- **Risks:** Can break Windows, disable security, cause boot failure
- **Recommendation:** Never enable, manual changes only with backup

#### `allow_registry_backup`
- **Default:** ✅ ENABLED
- **Risk:** SAFE
- **Description:** Allow creating registry backups
- **Use Cases:** Backup before modifications
- **Risks:** None (read-only operation)
- **Recommendation:** Keep enabled for safety

### Hardware

#### `allow_camera_access`
- **Default:** ❌ DISABLED
- **Risk:** HIGH
- **Description:** Allow accessing webcam
- **Use Cases:** Video calls, screenshots
- **Risks:** Privacy violation, surveillance
- **Recommendation:** Only enable when actively needed, indicator light should be on

#### `allow_microphone_access`
- **Default:** ❌ DISABLED
- **Risk:** HIGH
- **Description:** Allow accessing microphone
- **Use Cases:** Voice commands, recording
- **Risks:** Privacy violation, eavesdropping
- **Recommendation:** Only enable when actively needed

#### `allow_speaker_control`
- **Default:** ✅ ENABLED
- **Risk:** SAFE
- **Description:** Allow controlling speaker volume and output
- **Use Cases:** Adjusting volume, audio notifications
- **Risks:** Minimal (can be annoying)
- **Recommendation:** Safe to keep enabled

#### `allow_usb_access`
- **Default:** ❌ DISABLED
- **Risk:** MEDIUM
- **Description:** Allow accessing USB devices
- **Use Cases:** Reading USB drives, device management
- **Risks:** Can access sensitive data, spread malware
- **Recommendation:** Enable for specific devices only

#### `allow_bluetooth_control`
- **Default:** ❌ DISABLED
- **Risk:** MEDIUM
- **Description:** Allow controlling Bluetooth connections
- **Use Cases:** Connecting devices, file transfer
- **Risks:** Can connect to malicious devices
- **Recommendation:** Enable for trusted devices only

## Financial Toggles

### Master Control

#### `master_financial_toggle`
- **Default:** ❌ DISABLED
- **Risk:** CRITICAL
- **Description:** Master switch for ALL financial operations
- **Use Cases:** Enable financial features
- **Risks:** All financial risks apply when enabled
- **Recommendation:** Keep OFF unless actively using financial features
- **Note:** Must be ON for any financial operation to work

### Security

#### `require_2fa_confirmation`
- **Default:** ✅ ENABLED
- **Risk:** SAFE (security feature)
- **Description:** Require two-factor authentication for transactions
- **Use Cases:** Additional security layer
- **Risks:** None (improves security)
- **Recommendation:** Always keep enabled

#### `require_biometric`
- **Default:** ❌ DISABLED
- **Risk:** SAFE (security feature)
- **Description:** Require fingerprint/face recognition
- **Use Cases:** Additional security layer
- **Risks:** None (improves security)
- **Recommendation:** Enable if hardware supports it

#### `paper_trading_only`
- **Default:** ✅ ENABLED
- **Risk:** SAFE
- **Description:** Restrict to paper trading (simulated)
- **Use Cases:** Testing strategies without real money
- **Risks:** None (no real money)
- **Recommendation:** Keep enabled, real trading not supported in v1

### Banking

#### `allow_balance_check`
- **Default:** ✅ ENABLED
- **Risk:** SAFE
- **Description:** Allow viewing account balances
- **Use Cases:** Checking balances, monitoring accounts
- **Risks:** Minimal (read-only)
- **Recommendation:** Safe to enable

#### `allow_transaction_history`
- **Default:** ✅ ENABLED
- **Risk:** SAFE
- **Description:** Allow viewing transaction history
- **Use Cases:** Reviewing transactions, budgeting
- **Risks:** Minimal (read-only)
- **Recommendation:** Safe to enable

#### `allow_transfers`
- **Default:** ❌ DISABLED
- **Risk:** CRITICAL
- **Description:** Allow bank transfers
- **Use Cases:** Moving money between accounts
- **Risks:** Financial loss, unauthorized transfers
- **Recommendation:** Never enable in v1 (not implemented)

#### `allow_bill_pay`
- **Default:** ❌ DISABLED
- **Risk:** CRITICAL
- **Description:** Allow paying bills
- **Use Cases:** Automated bill payment
- **Risks:** Financial loss, incorrect payments
- **Recommendation:** Never enable in v1 (not implemented)

### Transaction Limits

#### `max_single_transaction`
- **Default:** $10.00
- **Risk:** MEDIUM
- **Description:** Maximum amount for a single transaction
- **Use Cases:** Limit exposure per transaction
- **Risks:** Can still lose money if limit is high
- **Recommendation:** Keep low ($10-$50), increase only if needed

#### `daily_limit`
- **Default:** $50.00
- **Risk:** MEDIUM
- **Description:** Maximum total transactions per day
- **Use Cases:** Limit daily exposure
- **Risks:** Can still lose money over time
- **Recommendation:** Keep low ($50-$200)

#### `monthly_limit`
- **Default:** $500.00
- **Risk:** MEDIUM
- **Description:** Maximum total transactions per month
- **Use Cases:** Limit monthly exposure
- **Risks:** Can accumulate losses
- **Recommendation:** Keep reasonable ($500-$2000)

#### `cooldown_between_transactions`
- **Default:** 300 seconds (5 minutes)
- **Risk:** SAFE (security feature)
- **Description:** Minimum time between transactions
- **Use Cases:** Prevent rapid-fire transactions
- **Risks:** None (improves security)
- **Recommendation:** Keep at least 5 minutes

## Path Configuration

### `restricted_paths`
- **Default:** `["C:\Windows", "C:\Program Files", "C:\Program Files (x86)"]`
- **Description:** Paths that are ALWAYS blocked for write/delete operations
- **Recommendation:** Never modify, protects system files

### `whitelisted_paths`
- **Default:** `["C:\Users\{username}\Documents\AI_Workspace"]`
- **Description:** Paths where file operations are allowed (if toggle enabled)
- **Recommendation:** Add your working directories, avoid system paths

## Toggle Combinations

### Safe Combinations

**Read-Only Mode (Default):**
```
✅ allow_file_read
✅ allow_speaker_control
✅ allow_balance_check
✅ allow_transaction_history
❌ All other toggles
```

**Basic Automation:**
```
✅ allow_file_read
✅ allow_file_write (whitelisted paths only)
✅ allow_folder_creation
✅ allow_process_creation (whitelisted apps)
✅ allow_speaker_control
❌ All destructive operations
```

**Advanced Automation:**
```
✅ allow_file_read
✅ allow_file_write
✅ allow_file_delete (recycle bin only)
✅ allow_folder_creation
✅ allow_process_creation
✅ allow_process_termination (with confirmation)
✅ allow_internet_access (whitelisted domains)
✅ allow_speaker_control
❌ Financial operations
❌ Registry modifications
❌ System file access
```

### Dangerous Combinations

**⚠️ Never Enable Together:**
- `allow_file_execution` + `allow_internet_access` (can download and run malware)
- `allow_registry_write` + `allow_startup_modification` (can persist malware)
- `allow_transfers` + high transaction limits (financial loss)
- `allow_firewall_modification` + `allow_internet_access` (expose system)

## Editing Toggles

### Via Code (Phase 1)

```python
from home_ai.core.config import get_settings

settings = get_settings()

# Enable file write in workspace
settings.system_toggles.allow_file_write = True

# Set financial limits
settings.financial_toggles.max_single_transaction = 25.00
settings.financial_toggles.daily_limit = 100.00

# Save changes
settings.save_to_file()
```

### Via GUI (Phase 2+)

CustomTkinter toggle panel will provide visual controls:
- Toggle switches for each setting
- Color coding (green=safe, yellow=caution, red=dangerous)
- Confirmation dialogs for dangerous toggles
- Preset profiles (Safe, Moderate, Advanced)

## Best Practices

1. **Start Conservative**
   - Keep default settings initially
   - Only enable what you need
   - Test with non-critical data

2. **Enable Incrementally**
   - Enable one toggle at a time
   - Test thoroughly before enabling more
   - Monitor audit logs for issues

3. **Use Whitelists**
   - Restrict file operations to specific paths
   - Limit network access to specific domains
   - Whitelist applications for process creation

4. **Set Limits**
   - Keep transaction limits low
   - Use rate limiting
   - Set session timeouts

5. **Review Regularly**
   - Audit enabled toggles monthly
   - Disable unused features
   - Check for new security recommendations

6. **Emergency Procedures**
   - Know the killswitch: `Ctrl+Alt+Shift+K`
   - Keep backups of important data
   - Document your toggle configuration

## Troubleshooting

### "Operation blocked by policy"

1. Check if relevant toggle is enabled
2. Verify path is not restricted
3. Check rate limits
4. Review audit logs for details

### "Rate limit exceeded"

1. Wait for cooldown period
2. Check current rate: Tools → Rate Limiter Stats
3. Reduce automation frequency
4. Increase rate limit if appropriate

### "Financial operation failed"

1. Verify `master_financial_toggle` is ON
2. Check transaction limits
3. Verify 2FA if required
4. Check cooldown period

## Security Reminders

- 🔒 **Default Deny:** If unsure, keep disabled
- 🔍 **Monitor Logs:** Check audit logs regularly
- ⚡ **Killswitch:** `Ctrl+Alt+Shift+K` stops everything
- 💾 **Backup:** Before enabling destructive operations
- 🎯 **Whitelist:** Use path/domain whitelists
- 💰 **Financial:** Keep master toggle OFF unless actively using

---

**Remember: When in doubt, keep it disabled. You can always enable later.**
