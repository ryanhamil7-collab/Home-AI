# Self-Improvement System

## Overview

The Self-Improvement System enables Home AI to autonomously analyze its own code, propose improvements, and apply changes with your approval. This creates a feedback loop where the system can evolve and improve over time.

## Key Features

### 🔍 Automated Code Analysis
- Scans Python files for improvement opportunities
- Uses LLM (Mistral) to analyze code quality, performance, and best practices
- Identifies specific, actionable improvements
- Calculates cyclomatic complexity and code metrics

### ✅ Comprehensive Validation
- **Syntax checking**: Ensures all proposed code is valid Python
- **Import analysis**: Detects dangerous imports and function calls
- **Security scanning**: Identifies hardcoded secrets, SQL injection risks, command injection
- **Complexity analysis**: Flags overly complex functions
- **Static analysis**: Runs ruff and mypy if available
- **Test execution**: Runs pytest to ensure changes don't break functionality
- **Risk scoring**: Calculates risk from 0.0 (safe) to 1.0 (dangerous)

### 🔒 Safety-First Design
- **Restricted areas**: Cannot modify security, safety, or financial code without explicit permission
- **Change limits**: Maximum 10 files and 500 lines per proposal
- **Automatic backups**: Full code snapshot before every change
- **Git integration**: All changes tracked with commits and branches
- **Rollback capability**: One-click restore from backup
- **Approval required**: No changes applied without your explicit approval

### 💾 Backup System
- Creates full snapshots of source code and configuration
- Stores backups in `~/.home_ai/backups/self_improve/`
- Includes manifest with timestamp, git commit, Python version
- Automatic cleanup keeps last 10 backups
- Rollback restores exact previous state

### 🌳 Git Integration
- Creates proposal branches: `self/proposal-{timestamp}-{slug}`
- Commits changes with descriptive messages
- Tags backups for easy reference
- Tracks all changes in version control

## User Interface

### Self-Improvement Tab

The Self-Improvement tab provides a complete interface for managing code improvements:

#### Analysis Controls
- **🔍 Analyze Code**: Start automated code analysis (analyzes up to 5 files)
- **🔄 Refresh**: Reload proposals list

#### Proposal Cards

Each proposal displays:

**Header:**
- Proposal ID
- Status badge (PENDING/APPROVED/REJECTED/APPLIED)
- Risk level badge (LOW/MEDIUM/HIGH)

**Details:**
- Description of improvement
- File path and scope (files/lines affected)
- Expected benefits

**Validation Results:**
- Risk score progress bar (color-coded)
- Check results (syntax, imports, security, complexity, ruff, mypy, tests)
- Errors and warnings (if any)

**Proposed Changes:**
- Diff preview showing code changes

**Actions:**
- **Pending**: ✅ Approve or ❌ Reject
- **Approved**: 🚀 Apply Changes
- **Applied**: ↩️ Rollback

## Workflow

### 1. Analysis Phase

```
User clicks "Analyze Code"
    ↓
System scans Python files (excludes restricted areas)
    ↓
LLM analyzes each file for improvements
    ↓
Generates improvement proposals
    ↓
Validates each proposal (syntax, security, tests)
    ↓
Queues proposals with validation results
```

### 2. Review Phase

```
User reviews proposals in GUI
    ↓
Examines description, rationale, risk level
    ↓
Reviews validation results and warnings
    ↓
Inspects proposed code changes (diff)
    ↓
Decides: Approve or Reject
```

### 3. Application Phase

```
User clicks "Apply Changes" on approved proposal
    ↓
System creates full backup
    ↓
Creates git branch (self/proposal-{id})
    ↓
Applies code changes
    ↓
Commits changes with descriptive message
    ↓
Marks proposal as applied
    ↓
User can rollback if needed
```

## Safety Constraints

### Restricted Directories
By default, these directories cannot be modified:
- `security/` - Security and audit systems
- `safety/` - Safety controls and policy engine
- `policy/` - Policy enforcement

### Restricted Files
These files require explicit permission:
- `policy_engine.py`
- `audit_logger.py`
- `spending_caps.py`
- `rate_limiter.py`

### Change Limits
- Maximum 10 files per proposal
- Maximum 500 lines per proposal
- These limits prevent overly broad refactors

### Validation Requirements
All proposals must pass:
- Syntax validation (no Python syntax errors)
- Import safety (no dangerous imports)
- Security checks (no hardcoded secrets, injection risks)
- Complexity checks (functions not overly complex)

Optional checks (if tools available):
- Ruff linting
- Mypy type checking
- Pytest test suite

## Risk Levels

### Low Risk (Green)
- Documentation improvements
- Code formatting
- Simple refactoring
- Adding comments or docstrings
- **Risk Score**: < 0.3

### Medium Risk (Yellow)
- Performance optimizations
- Refactoring with multiple changes
- Adding new functionality
- **Risk Score**: 0.3 - 0.7

### High Risk (Red)
- Changes to critical systems
- Complex refactoring
- Multiple errors or warnings
- **Risk Score**: > 0.7

## Configuration

### Analyzer Settings

Located in `src/home_ai/self_improve/analyzer.py`:

```python
# Directories that require explicit permission
RESTRICTED_DIRS = ["security", "safety", "policy"]

# Files that require explicit permission
RESTRICTED_FILES = [
    "policy_engine.py",
    "audit_logger.py",
    "spending_caps.py",
    "rate_limiter.py",
]

# Maximum changes per proposal
MAX_FILES_PER_PROPOSAL = 10
MAX_LINES_PER_PROPOSAL = 500
```

### Validator Settings

Located in `src/home_ai/self_improve/validator.py`:

Risk score calculation:
- Each error: +0.2 risk
- Each warning: +0.05 risk
- Syntax failure: +0.3 risk
- Security failure: +0.2 risk
- Test failure: +0.1 risk

## File Locations

### Source Code
- `src/home_ai/self_improve/analyzer.py` - Code analysis engine
- `src/home_ai/self_improve/validator.py` - Proposal validation
- `src/home_ai/self_improve/backup_manager.py` - Backup system
- `src/home_ai/self_improve/git_manager.py` - Git operations
- `src/home_ai/self_improve/approval_queue.py` - Proposal management
- `src/home_ai/self_improve/orchestrator.py` - Workflow coordination
- `src/home_ai/ui/self_improve_tab.py` - GUI interface

### Data Storage
- Backups: `~/.home_ai/backups/self_improve/`
- Proposals: `~/.home_ai/config/self_improve/queue/`
- Audit logs: `~/.home_ai/logs/audit.log`

## Best Practices

### For Users

1. **Start with low-risk proposals**: Approve documentation and formatting changes first
2. **Review diffs carefully**: Always inspect the proposed code changes
3. **Check validation results**: Pay attention to errors and warnings
4. **Test after applying**: Verify the system still works correctly
5. **Keep backups**: Don't delete old backups immediately
6. **Use rollback if needed**: Don't hesitate to revert problematic changes

### For Developers

1. **Keep proposals small**: Focus on specific, targeted improvements
2. **Write clear descriptions**: Explain what and why
3. **Provide rationale**: Help users understand the benefit
4. **Test thoroughly**: Ensure validation catches issues
5. **Document changes**: Update docs when modifying behavior

## Troubleshooting

### Analysis Produces No Proposals

**Possible causes:**
- All code is already optimal
- Restricted areas excluded most files
- LLM didn't identify improvements

**Solutions:**
- Increase `max_files` parameter
- Check logs for analysis errors
- Verify LLM is responding correctly

### Validation Fails

**Possible causes:**
- Syntax errors in proposed code
- Import issues
- Test failures

**Solutions:**
- Review validation errors in proposal card
- Reject proposal and try again
- Check if tests are passing before analysis

### Apply Changes Fails

**Possible causes:**
- Git conflicts
- File permissions
- Backup creation failed

**Solutions:**
- Check audit logs for details
- Verify git repository is clean
- Ensure sufficient disk space

### Rollback Fails

**Possible causes:**
- Backup not found
- File permissions
- Disk space

**Solutions:**
- Check backup directory exists
- Verify backup manifest is valid
- Manually restore from backup directory

## Security Considerations

### Audit Trail
All self-improvement operations are logged:
- Analysis runs
- Proposal creation
- Approvals and rejections
- Changes applied
- Rollbacks

### Tamper Detection
- Audit log uses hash chain for integrity
- Backups include manifest with checksums
- Git commits provide version history

### Access Control
- Only user can approve proposals
- No automatic application of changes
- Restricted areas protected by default

## Future Enhancements

Potential improvements for future versions:

1. **Scheduled Analysis**: Automatic daily/weekly code analysis
2. **Collaborative Learning**: Share anonymized improvements across instances
3. **A/B Testing**: Test changes in sandbox before applying
4. **Performance Metrics**: Track improvement impact over time
5. **Custom Rules**: User-defined analysis rules and constraints
6. **Diff Editing**: Allow users to modify proposals before applying
7. **Batch Operations**: Approve/apply multiple proposals at once
8. **Integration Tests**: Run full integration tests before applying

## API Reference

### Orchestrator

```python
from home_ai.self_improve.orchestrator import get_orchestrator

orchestrator = get_orchestrator()

# Analyze code and generate proposals
proposal_ids = orchestrator.analyze_and_propose(max_files=5)

# Get pending proposals
pending = orchestrator.get_pending_proposals()

# Approve a proposal
orchestrator.approve_proposal(proposal_id)

# Apply approved proposal
orchestrator.apply_proposal(proposal_id)

# Rollback applied proposal
orchestrator.rollback_proposal(proposal_id)

# Get history
history = orchestrator.get_proposal_history(limit=50)
```

### Backup Manager

```python
from home_ai.self_improve.backup_manager import get_backup_manager

backup_mgr = get_backup_manager()

# Create backup
backup = backup_mgr.create_backup("My backup")

# List backups
backups = backup_mgr.list_backups()

# Restore backup
backup_mgr.restore_backup(backup_id)

# Cleanup old backups
deleted = backup_mgr.cleanup_old_backups(keep_count=10)
```

### Git Manager

```python
from home_ai.self_improve.git_manager import get_git_manager

git_mgr = get_git_manager()

# Create proposal branch
git_mgr.create_proposal_branch(proposal_id)

# Commit changes
git_mgr.commit_changes("Self-improvement: Add docstrings")

# Create backup tag
git_mgr.create_backup_tag()

# Get diff
diff = git_mgr.get_diff(file_path)
```

## Conclusion

The Self-Improvement System provides a safe, controlled way for Home AI to evolve and improve over time. By combining automated analysis, comprehensive validation, and user approval, it enables continuous improvement while maintaining safety and security.

Always review proposals carefully, start with low-risk changes, and don't hesitate to rollback if something doesn't work as expected.
