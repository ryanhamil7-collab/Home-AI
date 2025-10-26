#!/usr/bin/env python3
"""Home AI OS - Main Application Entry Point."""

import sys
import argparse
from pathlib import Path
from loguru import logger

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    Path.home() / ".home_ai" / "logs" / "homeai_{time}.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG"
)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Home AI OS - AI-Native Desktop Environment")
    parser.add_argument("--mode", choices=["gui", "cli", "kiosk"], default="gui", help="Launch mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--kiosk", action="store_true", help="Launch in kiosk mode (fullscreen)")
    
    args = parser.parse_args()
    
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    logger.info("Starting Home AI OS...")
    logger.info(f"Mode: {args.mode}")
    
    try:
        if args.mode == "gui" or args.mode == "kiosk":
            from home_ai_os.ui.main_window import run_gui
            kiosk_mode = args.mode == "kiosk" or args.kiosk
            return run_gui(kiosk=kiosk_mode)
        
        elif args.mode == "cli":
            from home_ai_os.ui.cli import run_cli
            return run_cli()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
