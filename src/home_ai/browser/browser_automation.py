"""Browser automation with Selenium and safe profiles."""

import time
from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from loguru import logger

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
except ImportError:
    webdriver = None

try:
    import undetected_chromedriver as uc
except ImportError:
    uc = None

from home_ai.security.policy_engine import (
    get_policy_engine, Action, ActionScope, ActionRisk
)
from home_ai.security.audit_logger import get_audit_logger
from home_ai.core.config import get_settings


@dataclass
class BrowserProfile:
    """Browser profile configuration."""
    name: str
    user_data_dir: Path
    extensions: List[Path]
    blocked_domains: List[str]
    allowed_domains: List[str]
    disable_javascript: bool = False
    disable_images: bool = False
    headless: bool = False


class BrowserAutomation:
    """
    Browser automation with Selenium.
    Provides safe, controlled web browsing with security features.
    """
    
    def __init__(self, profile: Optional[BrowserProfile] = None):
        """
        Initialize browser automation.
        
        Args:
            profile: Browser profile to use (None for default)
        """
        if webdriver is None:
            raise ImportError("selenium required: pip install selenium")
        
        self.policy_engine = get_policy_engine()
        self.audit_logger = get_audit_logger()
        self.settings = get_settings()
        
        self.profile = profile or self._create_default_profile()
        self.driver: Optional[webdriver.Chrome] = None
        
        logger.info(f"BrowserAutomation initialized with profile: {self.profile.name}")
    
    def _create_default_profile(self) -> BrowserProfile:
        """Create default safe browser profile."""
        profile_dir = Path.home() / ".home_ai" / "browser_profiles" / "default"
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        return BrowserProfile(
            name="default",
            user_data_dir=profile_dir,
            extensions=[],
            blocked_domains=[],
            allowed_domains=[],
            disable_javascript=False,
            disable_images=False,
            headless=False
        )
    
    def _create_chrome_options(self) -> Options:
        """Create Chrome options with security settings."""
        options = Options()
        
        options.add_argument(f"--user-data-dir={self.profile.user_data_dir}")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        options.add_argument("--disable-web-security")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        if self.profile.headless:
            options.add_argument("--headless=new")
        
        if self.profile.disable_images:
            prefs = {"profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)
        
        if self.profile.disable_javascript:
            prefs = {"profile.managed_default_content_settings.javascript": 2}
            options.add_experimental_option("prefs", prefs)
        
        for extension_path in self.profile.extensions:
            if extension_path.exists():
                options.add_extension(str(extension_path))
        
        return options
    
    def start_browser(self, use_undetected: bool = True) -> bool:
        """
        Start browser instance.
        
        Args:
            use_undetected: Use undetected-chromedriver for stealth
        
        Returns:
            True if successful
        """
        action = Action(
            scope=ActionScope.NETWORK,
            operation="start_browser",
            risk=ActionRisk.MEDIUM,
            params={"profile": self.profile.name},
            description="Start web browser",
            requires_confirmation=True
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            logger.warning(f"Browser start blocked: {reason}")
            return False
        
        try:
            options = self._create_chrome_options()
            
            if use_undetected and uc is not None:
                self.driver = uc.Chrome(options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
            
            self.audit_logger.log_action(
                action_type="browser",
                action="start",
                status="executed",
                details={"profile": self.profile.name}
            )
            
            logger.info("Browser started successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            return False
    
    def navigate(self, url: str) -> bool:
        """
        Navigate to URL.
        
        Args:
            url: URL to navigate to
        
        Returns:
            True if successful
        """
        if not self.driver:
            logger.error("Browser not started")
            return False
        
        if not self._is_url_allowed(url):
            logger.warning(f"URL blocked by profile: {url}")
            return False
        
        action = Action(
            scope=ActionScope.NETWORK,
            operation="navigate",
            risk=ActionRisk.LOW,
            params={"url": url},
            description=f"Navigate to {url}",
            requires_confirmation=False
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            logger.warning(f"Navigation blocked: {reason}")
            return False
        
        try:
            self.driver.get(url)
            
            self.audit_logger.log_action(
                action_type="browser",
                action="navigate",
                status="executed",
                details={"url": url}
            )
            
            logger.info(f"Navigated to: {url}")
            return True
        
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    def _is_url_allowed(self, url: str) -> bool:
        """Check if URL is allowed by profile."""
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc
        
        for blocked in self.profile.blocked_domains:
            if blocked in domain:
                return False
        
        if self.profile.allowed_domains:
            for allowed in self.profile.allowed_domains:
                if allowed in domain:
                    return True
            return False  # Not in whitelist
        
        return True  # No whitelist, allow
    
    def find_element(self, by: str, value: str, timeout: int = 10) -> Optional[Any]:
        """
        Find element on page.
        
        Args:
            by: Locator strategy ("id", "name", "xpath", "css", "class", "tag")
            value: Locator value
            timeout: Wait timeout in seconds
        
        Returns:
            WebElement if found, None otherwise
        """
        if not self.driver:
            return None
        
        try:
            by_map = {
                "id": By.ID,
                "name": By.NAME,
                "xpath": By.XPATH,
                "css": By.CSS_SELECTOR,
                "class": By.CLASS_NAME,
                "tag": By.TAG_NAME,
                "link": By.LINK_TEXT,
                "partial_link": By.PARTIAL_LINK_TEXT
            }
            
            locator = by_map.get(by.lower(), By.ID)
            
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((locator, value)))
            
            return element
        
        except Exception as e:
            logger.error(f"Element not found: {e}")
            return None
    
    def click_element(self, by: str, value: str) -> bool:
        """Click an element."""
        element = self.find_element(by, value)
        if element:
            try:
                element.click()
                
                self.audit_logger.log_action(
                    action_type="browser",
                    action="click",
                    status="executed",
                    details={"by": by, "value": value}
                )
                
                return True
            except Exception as e:
                logger.error(f"Click failed: {e}")
        
        return False
    
    def type_text(self, by: str, value: str, text: str) -> bool:
        """Type text into an element."""
        element = self.find_element(by, value)
        if element:
            try:
                element.clear()
                element.send_keys(text)
                
                self.audit_logger.log_action(
                    action_type="browser",
                    action="type",
                    status="executed",
                    details={"by": by, "value": value, "length": len(text)}
                )
                
                return True
            except Exception as e:
                logger.error(f"Type failed: {e}")
        
        return False
    
    def get_text(self, by: str, value: str) -> Optional[str]:
        """Get text from an element."""
        element = self.find_element(by, value)
        if element:
            return element.text
        return None
    
    def get_attribute(self, by: str, value: str, attribute: str) -> Optional[str]:
        """Get attribute from an element."""
        element = self.find_element(by, value)
        if element:
            return element.get_attribute(attribute)
        return None
    
    def execute_script(self, script: str) -> Any:
        """Execute JavaScript in browser."""
        if not self.driver:
            return None
        
        action = Action(
            scope=ActionScope.NETWORK,
            operation="execute_script",
            risk=ActionRisk.MEDIUM,
            params={"script": script[:100]},
            description="Execute JavaScript",
            requires_confirmation=True
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            logger.warning(f"Script execution blocked: {reason}")
            return None
        
        try:
            result = self.driver.execute_script(script)
            
            self.audit_logger.log_action(
                action_type="browser",
                action="execute_script",
                status="executed",
                details={"script_length": len(script)}
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return None
    
    def take_screenshot(self, filepath: Optional[Path] = None) -> Optional[Path]:
        """Take screenshot of current page."""
        if not self.driver:
            return None
        
        try:
            if filepath is None:
                screenshots_dir = Path.home() / "Documents" / "HomeAI" / "screenshots"
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                filepath = screenshots_dir / f"browser_{int(time.time())}.png"
            
            self.driver.save_screenshot(str(filepath))
            
            self.audit_logger.log_action(
                action_type="browser",
                action="screenshot",
                status="executed",
                details={"filepath": str(filepath)}
            )
            
            logger.info(f"Screenshot saved: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None
    
    def get_page_source(self) -> Optional[str]:
        """Get HTML source of current page."""
        if self.driver:
            return self.driver.page_source
        return None
    
    def get_current_url(self) -> Optional[str]:
        """Get current URL."""
        if self.driver:
            return self.driver.current_url
        return None
    
    def get_title(self) -> Optional[str]:
        """Get page title."""
        if self.driver:
            return self.driver.title
        return None
    
    def go_back(self) -> bool:
        """Navigate back."""
        if self.driver:
            try:
                self.driver.back()
                return True
            except Exception as e:
                logger.error(f"Go back failed: {e}")
        return False
    
    def go_forward(self) -> bool:
        """Navigate forward."""
        if self.driver:
            try:
                self.driver.forward()
                return True
            except Exception as e:
                logger.error(f"Go forward failed: {e}")
        return False
    
    def refresh(self) -> bool:
        """Refresh page."""
        if self.driver:
            try:
                self.driver.refresh()
                return True
            except Exception as e:
                logger.error(f"Refresh failed: {e}")
        return False
    
    def close_tab(self) -> bool:
        """Close current tab."""
        if self.driver:
            try:
                self.driver.close()
                return True
            except Exception as e:
                logger.error(f"Close tab failed: {e}")
        return False
    
    def switch_to_tab(self, index: int) -> bool:
        """Switch to tab by index."""
        if self.driver:
            try:
                self.driver.switch_to.window(self.driver.window_handles[index])
                return True
            except Exception as e:
                logger.error(f"Switch tab failed: {e}")
        return False
    
    def new_tab(self, url: Optional[str] = None) -> bool:
        """Open new tab."""
        if self.driver:
            try:
                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                
                if url:
                    self.navigate(url)
                
                return True
            except Exception as e:
                logger.error(f"New tab failed: {e}")
        return False
    
    def get_cookies(self) -> List[Dict[str, Any]]:
        """Get all cookies."""
        if self.driver:
            return self.driver.get_cookies()
        return []
    
    def add_cookie(self, cookie: Dict[str, Any]) -> bool:
        """Add a cookie."""
        if self.driver:
            try:
                self.driver.add_cookie(cookie)
                return True
            except Exception as e:
                logger.error(f"Add cookie failed: {e}")
        return False
    
    def delete_cookie(self, name: str) -> bool:
        """Delete a cookie."""
        if self.driver:
            try:
                self.driver.delete_cookie(name)
                return True
            except Exception as e:
                logger.error(f"Delete cookie failed: {e}")
        return False
    
    def delete_all_cookies(self) -> bool:
        """Delete all cookies."""
        if self.driver:
            try:
                self.driver.delete_all_cookies()
                return True
            except Exception as e:
                logger.error(f"Delete cookies failed: {e}")
        return False
    
    def wait_for_element(self, by: str, value: str, timeout: int = 10) -> bool:
        """Wait for element to be present."""
        element = self.find_element(by, value, timeout)
        return element is not None
    
    def is_element_visible(self, by: str, value: str) -> bool:
        """Check if element is visible."""
        element = self.find_element(by, value, timeout=2)
        if element:
            return element.is_displayed()
        return False
    
    def stop_browser(self) -> bool:
        """Stop browser instance."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                
                self.audit_logger.log_action(
                    action_type="browser",
                    action="stop",
                    status="executed",
                    details={}
                )
                
                logger.info("Browser stopped")
                return True
            except Exception as e:
                logger.error(f"Failed to stop browser: {e}")
        
        return False


_browser_automation: Optional[BrowserAutomation] = None


def get_browser_automation(profile: Optional[BrowserProfile] = None) -> BrowserAutomation:
    """Get or create global browser automation instance."""
    global _browser_automation
    if _browser_automation is None:
        _browser_automation = BrowserAutomation(profile=profile)
    return _browser_automation
