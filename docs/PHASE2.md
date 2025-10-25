# Phase 2: Live Computer Vision & Autonomous Navigation

## Overview

Phase 2 adds live computer vision capabilities that enable the LLM to see and navigate the Windows desktop autonomously. This transforms Home AI from a chat-based assistant into a vision-enabled autonomous agent.

## New Capabilities

### 1. Live Screen Capture

**Module:** `src/home_ai/vision/screen_capture.py`

The `LiveScreenCapture` class provides continuous desktop monitoring:

```python
from home_ai.vision.screen_capture import get_screen_capture

# Get screen capture instance
screen_capture = get_screen_capture()

# Start continuous capture at 1 FPS
screen_capture.start_capture()

# Get current frame
frame = screen_capture.get_current_frame()

# Capture specific region
region_frame = screen_capture.capture_region(x=100, y=100, width=800, height=600)

# Stop capture
screen_capture.stop_capture()
```

**Features:**
- Configurable frame rate (default 1 FPS)
- Multi-monitor support
- Region capture
- Window-specific capture
- Frame callbacks for real-time processing
- Base64 encoding for LLM vision models

### 2. Vision-Enabled LLM

**Module:** `src/home_ai/vision/vision_llm.py`

The `VisionLLM` class integrates screen capture with LLM vision capabilities:

```python
from home_ai.vision.vision_llm import get_vision_llm

# Get vision LLM instance
vision_llm = get_vision_llm()

# Analyze current screen
analysis = vision_llm.analyze_screen()
print(analysis.description)
print(analysis.suggestions)

# Find UI element
element = vision_llm.find_element("Submit button")

# Get screen context for LLM
context = vision_llm.get_screen_context()
```

**Features:**
- Screen state analysis
- UI element detection
- Action suggestions
- Context generation for LLM prompts
- Continuous monitoring with callbacks

### 3. OCR Text Extraction

**Module:** `src/home_ai/vision/ocr.py`

The `OCREngine` class extracts text from screen captures:

```python
from home_ai.vision.ocr import get_ocr_engine, extract_text

# Extract all text from image
text = extract_text(image)

# Extract text with bounding boxes
engine = get_ocr_engine()
regions = engine.extract_text_regions(image)

for region in regions:
    print(f"{region.text} at ({region.x}, {region.y})")

# Find specific text
region = engine.find_text(image, "Submit")
if region:
    print(f"Found at ({region.x}, {region.y})")
```

**Features:**
- Full text extraction
- Bounding box detection
- Text search
- Structured data extraction (tables, forms)
- Confidence scores

**Requirements:**
- `pytesseract` Python package
- Tesseract OCR engine installed on system

### 4. Autonomous Navigation

**Module:** `src/home_ai/automation/navigator.py`

The `AutonomousNavigator` class enables LLM to control desktop:

```python
from home_ai.automation.navigator import get_navigator

navigator = get_navigator()

# Move mouse
result = navigator.move_mouse(x=500, y=300)

# Click
result = navigator.click(x=500, y=300, button="left")

# Type text
result = navigator.type_text("Hello, World!")

# Press keys
result = navigator.press_key("enter")
result = navigator.hotkey("ctrl", "c")

# Find and click text
result = navigator.find_and_click("Submit")

# Scroll
result = navigator.scroll(clicks=5)
```

**Features:**
- Mouse movement with smooth animation
- Click (left, right, middle, double)
- Keyboard input with intervals
- Hotkey combinations
- Text-based UI interaction
- Scroll control
- Failsafe (move to corner to abort)

**Safety:**
- All actions gated through policy engine
- Audit logging of every action
- Rate limiting
- Killswitch support

### 5. Window Management

**Module:** `src/home_ai/automation/window_manager.py`

The `WindowManager` class controls application windows:

```python
from home_ai.automation.window_manager import get_window_manager

window_manager = get_window_manager()

# List all windows
windows = window_manager.list_windows()

# Find window
window = window_manager.find_window("Chrome")

# Activate window
window_manager.activate_window("Chrome")

# Resize window
window_manager.resize_window("Chrome", width=1200, height=800)

# Move window
window_manager.move_window("Chrome", x=100, y=100)

# Snap window to screen edge
window_manager.snap_window("Chrome", position="left")

# Minimize/maximize
window_manager.minimize_window("Chrome")
window_manager.maximize_window("Chrome")

# Close window (requires confirmation)
window_manager.close_window("Chrome")
```

**Features:**
- Window enumeration
- Window search (exact/partial match)
- Activate/focus windows
- Resize and move
- Snap to screen edges
- Minimize/maximize/close
- Multi-monitor support

### 6. File Operations

**Module:** `src/home_ai/automation/file_operations.py`

The `FileOperations` class provides safe file manipulation:

```python
from home_ai.automation.file_operations import get_file_operations

file_ops = get_file_operations()

# Read file
content = file_ops.read_file("document.txt")

# Write file (creates backup)
success = file_ops.write_file("document.txt", "New content")

# Copy file
success = file_ops.copy_file("source.txt", "destination.txt")

# Move file (creates backup)
success = file_ops.move_file("old.txt", "new.txt")

# Delete file (creates backup)
success = file_ops.delete_file("unwanted.txt")

# List directory
files = file_ops.list_directory("/path/to/dir")

# Create directory
success = file_ops.create_directory("/path/to/new/dir")
```

**Safety Features:**
- Automatic backups before modifications
- Path whitelisting/blacklisting
- Policy engine permission checks
- Audit logging
- Restricted paths (Windows, Program Files)

### 7. CustomTkinter Toggle Panel

**Module:** `src/home_ai/ui/toggle_panel.py`

The `TogglePanel` class provides a dedicated control interface:

```python
from home_ai.ui.toggle_panel import create_toggle_panel

def on_toggle_change(toggle_name, new_value):
    print(f"{toggle_name} changed to {new_value}")

panel = create_toggle_panel(on_change=on_toggle_change)

# Run in main thread (blocking)
panel.run()

# Or run in background
panel.run_async()
```

**Features:**
- Always-on-top window
- Color-coded toggles (green/yellow/red)
- Grouped by category
- Real-time updates
- Save configuration button
- Dark theme

**Toggle Categories:**
- Master Controls (killswitch)
- System Operations (file, process, network)
- Registry Access
- Hardware Access (camera, microphone)
- Financial Operations
- Computer Vision

### 8. System Tray Integration

**Module:** `src/home_ai/ui/system_tray.py`

The `SystemTray` class provides quick access from taskbar:

```python
from home_ai.ui.system_tray import get_system_tray

tray = get_system_tray(
    on_show_dashboard=show_main_window,
    on_show_toggles=show_toggle_panel,
    on_exit=exit_app
)

# Run in background
tray.start_async()
```

**Menu Items:**
- Show Dashboard
- Toggle Controls
- Status (killswitch, permissions)
- Quick Actions (activate killswitch, lock financial, screenshot)
- View Logs
- Settings
- Exit

## GUI Integration

The main PyQt6 window now includes a **Vision** tab with:

1. **Live Capture Controls**
   - Start/Stop continuous capture
   - Take screenshot button
   - Vision system status

2. **Autonomous Navigation**
   - Enable/disable navigation
   - Real-time mouse position
   - Safety warnings

3. **Window Management**
   - List of all windows
   - Activate selected window
   - Window properties (position, size)

## Dependencies Added

```toml
# Computer vision
mss = "^9.0.0"           # Fast screen capture
pytesseract = "^0.3.10"  # OCR text extraction
```

**System Requirements:**
- Tesseract OCR engine (for text extraction)
  - Windows: Download from https://github.com/tesseract-ocr/tesseract
  - Add to PATH or set `TESSDATA_PREFIX` environment variable

## Usage Examples

### Example 1: Autonomous Form Filling

```python
from home_ai.vision.screen_capture import get_screen_capture
from home_ai.automation.navigator import get_navigator
from home_ai.vision.ocr import find_text

# Capture screen
screen_capture = get_screen_capture()
frame = screen_capture.capture_frame()

# Find form fields
name_field = find_text(frame.image, "Name:")
email_field = find_text(frame.image, "Email:")

# Navigate and fill
navigator = get_navigator()

if name_field:
    navigator.click(name_field.x + 100, name_field.y)
    navigator.type_text("John Doe")

if email_field:
    navigator.click(email_field.x + 100, email_field.y)
    navigator.type_text("john@example.com")

# Submit
navigator.find_and_click("Submit")
```

### Example 2: Window Organization

```python
from home_ai.automation.window_manager import get_window_manager

window_manager = get_window_manager()

# Snap Chrome to left half
window_manager.snap_window("Chrome", "left")

# Snap VS Code to right half
window_manager.snap_window("Visual Studio Code", "right")

# Maximize terminal
window_manager.maximize_window("Terminal")
```

### Example 3: Continuous Monitoring

```python
from home_ai.vision.screen_capture import get_screen_capture
from home_ai.vision.vision_llm import get_vision_llm

def on_frame_analysis(analysis):
    if "error" in analysis.description.lower():
        print(f"Alert: {analysis.description}")

vision_llm = get_vision_llm()
vision_llm.continuous_monitoring(on_frame_analysis)
```

## Security Considerations

### Permission Gating

All Phase 2 operations are gated through the policy engine:

```python
# Every action creates an Action object
action = Action(
    scope=ActionScope.SYSTEM,
    operation="mouse_click",
    risk=ActionRisk.LOW,
    params={"x": 500, "y": 300},
    description="Click at (500, 300)",
    requires_confirmation=False
)

# Policy engine checks permission
allowed, reason = policy_engine.check_permission(action)
```

### Audit Logging

All actions are logged with full context:

```python
audit_logger.log_action(
    action_type="navigation",
    action="click",
    status="executed",
    details={"x": 500, "y": 300, "button": "left"}
)
```

### Rate Limiting

Navigation actions are rate-limited to prevent runaway automation:

```python
# Default: 60 actions per minute per scope
rate_limiter.check_rate_limit(ActionScope.SYSTEM)
```

### Killswitch

Emergency killswitch (Ctrl+Alt+Shift+K) immediately stops all automation:

```python
from home_ai.core.killswitch import get_killswitch

killswitch = get_killswitch()
if killswitch.is_active():
    # All operations blocked
    return False
```

## Testing

Run Phase 2 tests:

```bash
pytest tests/test_vision.py
pytest tests/test_navigator.py
pytest tests/test_window_manager.py
pytest tests/test_file_operations.py
```

## Known Limitations

1. **Vision Model Integration**: Full vision LLM integration (llava, bakllava) is prepared but requires Ollama vision model support
2. **OCR Accuracy**: Depends on Tesseract quality and screen resolution
3. **Window Detection**: Some UWP apps may not be detected by pygetwindow
4. **Cross-Platform**: Currently Windows-focused (pywin32, pywinauto)

## Future Enhancements (Phase 3)

- Browser automation with Selenium
- Application-specific integrations
- Workflow automation and macros
- Advanced vision model integration
- Multi-agent coordination
- Voice control integration

## Troubleshooting

### Vision capture not working
- Check if `mss` is installed: `pip install mss`
- Verify screen permissions on Windows

### OCR not extracting text
- Install Tesseract: https://github.com/tesseract-ocr/tesseract
- Add Tesseract to PATH
- Set `TESSDATA_PREFIX` environment variable

### Navigation blocked
- Check policy engine settings
- Verify toggles are enabled
- Check audit logs for denial reasons

### Window management fails
- Some apps require admin privileges
- UWP apps may not be accessible
- Try running Home AI as administrator

## Performance Tips

1. **Reduce capture FPS** for lower CPU usage:
   ```python
   screen_capture.set_fps(0.5)  # 1 frame every 2 seconds
   ```

2. **Capture specific regions** instead of full screen:
   ```python
   frame = screen_capture.capture_region(x, y, width, height)
   ```

3. **Disable continuous capture** when not needed:
   ```python
   screen_capture.stop_capture()
   ```

4. **Use window-specific capture**:
   ```python
   frame = screen_capture.capture_window("Chrome")
   ```

## Conclusion

Phase 2 transforms Home AI into a vision-enabled autonomous agent capable of seeing, understanding, and navigating the Windows desktop. All capabilities are built with security-first principles, comprehensive audit logging, and user control through granular toggles.
