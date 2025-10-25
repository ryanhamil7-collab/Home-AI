"""Main application entry point."""

import sys
import argparse
from pathlib import Path
from loguru import logger

from home_ai.core.config import get_settings

settings = get_settings()
log_file = settings.log_dir / "home_ai.log"

logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    log_file,
    rotation="10 MB",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG"
)

logger.info("=" * 60)
logger.info("Home AI - Windows LLM PC Control System")
logger.info(f"Version: {settings.version}")
logger.info("=" * 60)


def check_dependencies() -> bool:
    """Check if all required dependencies are available."""
    missing = []
    
    try:
        from home_ai.llm.ollama_client import get_ollama_client
        client = get_ollama_client()
        if not client.check_server():
            logger.warning("Ollama server not running, will attempt to start")
    except Exception as e:
        logger.error(f"Ollama check failed: {e}")
        missing.append("ollama")
    
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        logger.error("PyQt6 not available")
        missing.append("PyQt6")
    
    try:
        import customtkinter
    except ImportError:
        logger.error("CustomTkinter not available")
        missing.append("customtkinter")
    
    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
        logger.error("Please install with: poetry install")
        return False
    
    return True


def initialize_system() -> bool:
    """Initialize all system components."""
    logger.info("Initializing system components...")
    
    try:
        from home_ai.core.config import get_settings
        settings = get_settings()
        logger.info("✓ Configuration loaded")
        
        from home_ai.security.audit_logger import get_audit_logger
        from home_ai.security.policy_engine import get_policy_engine
        from home_ai.security.rate_limiter import get_rate_limiter
        
        audit_logger = get_audit_logger()
        policy_engine = get_policy_engine()
        rate_limiter = get_rate_limiter()
        logger.info("✓ Security layer initialized")
        
        from home_ai.core.killswitch import get_killswitch
        killswitch = get_killswitch()
        killswitch.start()
        logger.info("✓ Emergency killswitch armed")
        
        from home_ai.llm.ollama_client import get_ollama_client
        llm_client = get_ollama_client()
        
        if not llm_client.check_server():
            logger.info("Starting Ollama server...")
            if not llm_client.start_server():
                logger.error("Failed to start Ollama server")
                return False
        
        optimal_model = llm_client.select_optimal_model()
        logger.info(f"Optimal model selected: {optimal_model}")
        
        if not llm_client.ensure_model(optimal_model):
            logger.warning(f"Failed to ensure model: {optimal_model}")
        
        logger.info("✓ LLM engine initialized")
        
        from home_ai.monitoring.system_monitor import get_system_monitor
        monitor = get_system_monitor()
        monitor.start_monitoring()
        logger.info("✓ System monitoring started")
        
        audit_logger.log_action(
            action_type="system",
            action="startup",
            status="executed",
            details={"version": settings.version}
        )
        
        logger.info("=" * 60)
        logger.info("System initialization complete")
        logger.info("SAFE MODE: All destructive operations disabled by default")
        logger.info(f"Emergency killswitch: {settings.security.emergency_killswitch_key}")
        logger.info("=" * 60)
        
        return True
    
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def run_gui() -> int:
    """Run the GUI application."""
    logger.info("Starting GUI...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from home_ai.ui.main_window import MainWindow
        
        app = QApplication(sys.argv)
        app.setApplicationName("Home AI")
        app.setOrganizationName("Home AI")
        
        window = MainWindow()
        window.show()
        
        return app.exec()
    
    except Exception as e:
        logger.error(f"GUI failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


def run_cli() -> int:
    """Run in CLI mode (for testing)."""
    logger.info("Running in CLI mode...")
    
    try:
        from home_ai.llm.ollama_client import get_ollama_client
        
        client = get_ollama_client()
        
        print("\n" + "=" * 60)
        print("Home AI - CLI Mode")
        print("Type 'quit' or 'exit' to quit")
        print("Type 'clear' to clear conversation history")
        print("=" * 60 + "\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit']:
                    break
                
                if user_input.lower() == 'clear':
                    client.clear_history()
                    print("Conversation history cleared.\n")
                    continue
                
                print("Assistant: ", end="", flush=True)
                
                for chunk in client.chat(user_input):
                    print(chunk, end="", flush=True)
                
                print("\n")
            
            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"\nError: {e}\n")
        
        return 0
    
    except Exception as e:
        logger.error(f"CLI mode failed: {e}")
        return 1


def shutdown_system() -> None:
    """Shutdown system components gracefully."""
    logger.info("Shutting down system...")
    
    try:
        from home_ai.monitoring.system_monitor import get_system_monitor
        monitor = get_system_monitor()
        monitor.stop_monitoring()
        
        from home_ai.core.killswitch import get_killswitch
        killswitch = get_killswitch()
        killswitch.stop()
        
        from home_ai.security.audit_logger import get_audit_logger
        audit_logger = get_audit_logger()
        audit_logger.log_action(
            action_type="system",
            action="shutdown",
            status="executed",
            details={}
        )
        
        logger.info("System shutdown complete")
    
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Home AI - Windows LLM PC Control System"
    )
    parser.add_argument(
        "--mode",
        choices=["gui", "cli"],
        default="gui",
        help="Run mode (default: gui)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
        logger.add(log_file, level="DEBUG")
    
    if not check_dependencies():
        return 1
    
    if not initialize_system():
        return 1
    
    try:
        if args.mode == "gui":
            return run_gui()
        else:
            return run_cli()
    
    finally:
        shutdown_system()


if __name__ == "__main__":
    sys.exit(main())
