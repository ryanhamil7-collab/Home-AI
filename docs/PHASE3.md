# Phase 3: Advanced Automation & Application Integration

## Overview

Phase 3 adds comprehensive automation capabilities including browser automation, workflow orchestration, task scheduling, and application integrations. This transforms Home AI into a full automation platform.

## New Capabilities

### 1. Browser Automation

**Module:** `src/home_ai/browser/browser_automation.py`

Full Selenium integration with security features:

```python
from home_ai.browser.browser_automation import BrowserAutomation, BrowserProfile
from pathlib import Path

# Create safe browser profile
profile = BrowserProfile(
    name="safe_browsing",
    user_data_dir=Path.home() / ".home_ai" / "browser_profiles" / "safe",
    extensions=[],
    blocked_domains=["malicious.com"],
    allowed_domains=[],  # Empty = allow all except blocked
    disable_javascript=False,
    disable_images=False,
    headless=False
)

# Initialize browser
browser = BrowserAutomation(profile=profile)

# Start browser
browser.start_browser(use_undetected=True)

# Navigate
browser.navigate("https://example.com")

# Find and interact with elements
browser.click_element("id", "submit-button")
browser.type_text("name", "email", "user@example.com")

# Execute JavaScript
result = browser.execute_script("return document.title;")

# Take screenshot
browser.take_screenshot()

# Stop browser
browser.stop_browser()
```

**Features:**
- Selenium WebDriver integration
- Undetected ChromeDriver for stealth
- Safe browser profiles with security settings
- Domain whitelist/blacklist
- JavaScript and image control
- Headless mode support
- Cookie management
- Multi-tab support
- Screenshot capture
- JavaScript execution

**Security:**
- All navigation gated through policy engine
- Domain filtering
- Audit logging of all actions
- Confirmation for script execution
- Sandboxed profiles

### 2. Workflow Automation

**Module:** `src/home_ai/workflows/workflow_engine.py`

Multi-step workflow orchestration:

```python
from home_ai.workflows.workflow_engine import (
    get_workflow_engine, Workflow, WorkflowStep, StepType
)

engine = get_workflow_engine()

# Create workflow
steps = [
    WorkflowStep(
        step_type=StepType.NAVIGATE,
        params={"url": "https://example.com"},
        description="Navigate to example.com"
    ),
    WorkflowStep(
        step_type=StepType.WAIT,
        params={"duration": 2.0},
        description="Wait 2 seconds"
    ),
    WorkflowStep(
        step_type=StepType.SCREENSHOT,
        params={"filepath": "/path/to/screenshot.png"},
        description="Take screenshot"
    )
]

workflow = engine.create_workflow(
    name="example_workflow",
    description="Example automation workflow",
    steps=steps,
    tags=["example", "demo"]
)

# Execute workflow
execution = engine.execute_workflow(workflow)

print(f"Status: {execution.status.value}")
print(f"Steps completed: {execution.current_step}/{execution.total_steps}")
```

**Step Types:**
- `NAVIGATE` - Browser navigation
- `CLICK` - Click element
- `TYPE` - Type text
- `WAIT` - Wait for duration
- `SCREENSHOT` - Capture screen
- `EXECUTE_SCRIPT` - Run JavaScript
- `FILE_OPERATION` - File manipulation
- `WINDOW_OPERATION` - Window management
- `CONDITION` - Conditional logic
- `LOOP` - Repeat steps
- `CUSTOM` - Custom handlers

**Features:**
- Multi-step execution
- Error handling (stop, continue, retry)
- Retry logic with configurable attempts
- Pause/resume/cancel execution
- Workflow persistence (JSON storage)
- Custom step handlers
- Execution history
- Results tracking

**Error Handling:**
```python
step = WorkflowStep(
    step_type=StepType.CLICK,
    params={"by": "id", "value": "button"},
    description="Click button",
    timeout=30,
    retry_count=3,
    on_error="retry"  # "stop", "continue", or "retry"
)
```

### 3. Task Scheduling

**Module:** `src/home_ai/workflows/task_scheduler.py`

APScheduler integration for automated execution:

```python
from home_ai.workflows.task_scheduler import get_task_scheduler
from datetime import datetime, timedelta

scheduler = get_task_scheduler()

# Schedule with cron expression
task_id = scheduler.schedule_workflow_cron(
    workflow_name="daily_backup",
    cron_expression="0 2 * * *"  # 2 AM daily
)

# Schedule at intervals
task_id = scheduler.schedule_workflow_interval(
    workflow_name="health_check",
    interval_seconds=3600  # Every hour
)

# Schedule one-time execution
run_date = datetime.now() + timedelta(hours=1)
task_id = scheduler.schedule_workflow_once(
    workflow_name="one_time_task",
    run_date=run_date
)

# List scheduled tasks
tasks = scheduler.list_scheduled_tasks()

# Pause/resume tasks
scheduler.pause_task(task_id)
scheduler.resume_task(task_id)

# Unschedule task
scheduler.unschedule_task(task_id)
```

**Cron Expression Examples:**
- `"0 9 * * *"` - 9 AM daily
- `"0 */2 * * *"` - Every 2 hours
- `"0 9 * * 1-5"` - 9 AM weekdays
- `"0 0 1 * *"` - First day of month
- `"*/15 * * * *"` - Every 15 minutes

**Features:**
- Cron-based scheduling
- Interval-based scheduling
- One-time scheduled execution
- Pause/resume tasks
- Task persistence
- Automatic workflow execution
- Audit logging

### 4. Application Launcher

**Module:** `src/home_ai/integrations/app_launcher.py`

Safe application launching with whitelist:

```python
from home_ai.integrations.app_launcher import get_app_launcher

launcher = get_app_launcher()

# Launch whitelisted application
pid = launcher.launch_application("chrome", args=["--incognito"])

# Check if running
is_running = launcher.is_application_running("chrome")

# Get launched applications
apps = launcher.get_launched_applications()

# Terminate application
launcher.terminate_application(pid)

# Add to whitelist
launcher.add_to_whitelist(
    app_name="custom_app",
    path="C:\\Path\\To\\App.exe",
    risk=ActionRisk.LOW
)
```

**Pre-configured Applications:**
- Chrome
- Firefox
- VS Code
- Notepad
- Calculator
- Terminal (cmd.exe)
- PowerShell

**Features:**
- Application whitelist
- Process tracking
- Resource monitoring (CPU, memory)
- Safe termination
- Launch with arguments
- Risk-based permissions

### 5. Macro Recording (Planned)

**Module:** `src/home_ai/workflows/macro_recorder.py`

Record and playback user actions:

```python
from home_ai.workflows.macro_recorder import get_macro_recorder

recorder = get_macro_recorder()

# Start recording
recorder.start_recording()

# ... perform actions ...

# Stop recording
events = recorder.stop_recording()

# Save macro
recorder.save_macro("my_macro", events)

# Load and playback
events = recorder.load_macro("my_macro")
recorder.playback_macro(events, speed=1.0)

# Convert to workflow
recorder.convert_to_workflow(events, "my_workflow", "Converted from macro")
```

## Usage Examples

### Example 1: Automated Web Scraping

```python
from home_ai.workflows.workflow_engine import get_workflow_engine, WorkflowStep, StepType

engine = get_workflow_engine()

steps = [
    WorkflowStep(
        step_type=StepType.NAVIGATE,
        params={"url": "https://news.ycombinator.com"},
        description="Navigate to Hacker News"
    ),
    WorkflowStep(
        step_type=StepType.WAIT,
        params={"duration": 2.0},
        description="Wait for page load"
    ),
    WorkflowStep(
        step_type=StepType.SCREENSHOT,
        params={"filepath": "hn_screenshot.png"},
        description="Capture screenshot"
    )
]

workflow = engine.create_workflow(
    name="scrape_hn",
    description="Scrape Hacker News",
    steps=steps
)

execution = engine.execute_workflow(workflow)
```

### Example 2: Scheduled Daily Backup

```python
from home_ai.workflows.task_scheduler import get_task_scheduler
from home_ai.workflows.workflow_engine import get_workflow_engine, WorkflowStep, StepType

# Create backup workflow
engine = get_workflow_engine()

steps = [
    WorkflowStep(
        step_type=StepType.FILE_OPERATION,
        params={
            "operation": "copy",
            "source": "C:\\Important\\Data",
            "destination": "D:\\Backups\\Data"
        },
        description="Backup important data"
    )
]

workflow = engine.create_workflow(
    name="daily_backup",
    description="Daily data backup",
    steps=steps
)

# Schedule for 2 AM daily
scheduler = get_task_scheduler()
scheduler.schedule_workflow_cron(
    workflow_name="daily_backup",
    cron_expression="0 2 * * *"
)
```

### Example 3: Application Automation

```python
from home_ai.integrations.app_launcher import get_app_launcher
from home_ai.automation.window_manager import get_window_manager
import time

launcher = get_app_launcher()
window_manager = get_window_manager()

# Launch VS Code
pid = launcher.launch_application("vscode")

# Wait for window
time.sleep(3)

# Organize window
window_manager.snap_window("Visual Studio Code", "left")

# Launch browser
launcher.launch_application("chrome", args=["https://docs.python.org"])

time.sleep(2)

# Snap browser to right
window_manager.snap_window("Chrome", "right")
```

## Integration with Existing Features

### Vision + Browser Automation

```python
from home_ai.browser.browser_automation import get_browser_automation
from home_ai.vision.screen_capture import get_screen_capture
from home_ai.vision.ocr import extract_text

browser = get_browser_automation()
screen_capture = get_screen_capture()

# Navigate
browser.start_browser()
browser.navigate("https://example.com")

# Capture and analyze
frame = screen_capture.capture_frame()
text = extract_text(frame.image)

print(f"Page text: {text}")

browser.stop_browser()
```

### Workflows + Navigation

```python
from home_ai.workflows.workflow_engine import get_workflow_engine, WorkflowStep, StepType
from home_ai.automation.navigator import get_navigator

# Register custom navigation handler
engine = get_workflow_engine()

def handle_navigation_step(step, execution):
    navigator = get_navigator()
    x, y = step.params["x"], step.params["y"]
    return navigator.click(x, y).success

engine.register_step_handler(StepType.CLICK, handle_navigation_step)

# Now workflows can use navigation
steps = [
    WorkflowStep(
        step_type=StepType.CLICK,
        params={"x": 500, "y": 300},
        description="Click at coordinates"
    )
]
```

## Security Considerations

### Browser Security

1. **Profile Isolation**: Each profile has separate user data directory
2. **Domain Filtering**: Whitelist/blacklist for allowed domains
3. **Script Execution**: Requires confirmation for JavaScript
4. **Cookie Isolation**: Separate cookie storage per profile
5. **Extension Control**: Only approved extensions loaded

### Workflow Security

1. **Step Validation**: Each step checked by policy engine
2. **Audit Logging**: All workflow executions logged
3. **Error Containment**: Failed steps don't crash system
4. **Resource Limits**: Timeouts prevent runaway workflows
5. **Pause/Cancel**: Emergency controls available

### Scheduler Security

1. **Workflow Validation**: Only existing workflows can be scheduled
2. **Execution Logging**: All scheduled executions audited
3. **Rate Limiting**: Prevents excessive scheduling
4. **Permission Checks**: Scheduled workflows respect permissions

## Performance Tips

1. **Headless Browsing**: Use `headless=True` for faster execution
2. **Disable Images**: Set `disable_images=True` for faster page loads
3. **Workflow Optimization**: Minimize wait steps, use efficient selectors
4. **Scheduler Intervals**: Don't schedule too frequently (minimum 60s recommended)
5. **Process Cleanup**: Always terminate launched applications when done

## Troubleshooting

### Browser Issues

**Chrome not found:**
- Install Chrome or update path in whitelist
- Check `BrowserProfile.user_data_dir` permissions

**Elements not found:**
- Increase timeout in `find_element()`
- Use more specific selectors
- Add wait steps before interactions

### Workflow Issues

**Steps failing:**
- Check audit logs for error details
- Increase `timeout` on failing steps
- Use `on_error="continue"` for non-critical steps

**Workflows not executing:**
- Verify workflow exists: `engine.list_workflows()`
- Check policy engine permissions
- Review audit logs

### Scheduler Issues

**Tasks not running:**
- Verify scheduler is started: `scheduler.start()`
- Check cron expression syntax
- Review `list_scheduled_tasks()` output

**Tasks running multiple times:**
- Check for duplicate task IDs
- Verify `replace_existing=True` in schedule calls

## Future Enhancements (Phase 4)

- Voice control integration
- Multi-agent coordination
- Advanced vision model integration (llava, bakllava)
- Workflow marketplace
- Cloud workflow sync
- Mobile app integration

## Conclusion

Phase 3 provides comprehensive automation capabilities that enable Home AI to orchestrate complex multi-step workflows, automate browser interactions, schedule recurring tasks, and manage applications safely. All features maintain the security-first approach with policy engine gating, audit logging, and user control.
