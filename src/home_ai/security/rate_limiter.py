"""Rate limiter for action throttling."""

import time
from collections import deque
from typing import Dict, Optional
from dataclasses import dataclass
from loguru import logger
import threading


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    max_actions: int  # Maximum actions
    window_seconds: int  # Time window in seconds
    
    @property
    def actions_per_minute(self) -> float:
        """Calculate actions per minute."""
        return (self.max_actions / self.window_seconds) * 60


class RateLimiter:
    """
    Token bucket rate limiter for action throttling.
    Prevents abuse and runaway automation.
    """
    
    def __init__(self, max_actions_per_minute: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_actions_per_minute: Maximum actions allowed per minute
        """
        self.config = RateLimitConfig(
            max_actions=max_actions_per_minute,
            window_seconds=60
        )
        
        self._action_times: Dict[str, deque] = {}
        self._lock = threading.Lock()
        
        logger.info(f"RateLimiter initialized: {max_actions_per_minute} actions/minute")
    
    def check_rate_limit(self, scope: str = "global") -> tuple[bool, Optional[float]]:
        """
        Check if action is within rate limit.
        
        Args:
            scope: Scope to check (e.g., "global", "file", "network")
        
        Returns:
            (allowed: bool, wait_time: Optional[float])
            If not allowed, wait_time indicates seconds to wait
        """
        with self._lock:
            current_time = time.time()
            
            if scope not in self._action_times:
                self._action_times[scope] = deque()
            
            action_times = self._action_times[scope]
            
            cutoff_time = current_time - self.config.window_seconds
            while action_times and action_times[0] < cutoff_time:
                action_times.popleft()
            
            if len(action_times) < self.config.max_actions:
                return True, None
            
            oldest_time = action_times[0]
            wait_time = oldest_time + self.config.window_seconds - current_time
            
            logger.warning(
                f"Rate limit exceeded for scope '{scope}': "
                f"{len(action_times)}/{self.config.max_actions} in {self.config.window_seconds}s"
            )
            
            return False, max(0, wait_time)
    
    def record_action(self, scope: str = "global") -> None:
        """
        Record an action for rate limiting.
        
        Args:
            scope: Scope to record (e.g., "global", "file", "network")
        """
        with self._lock:
            current_time = time.time()
            
            if scope not in self._action_times:
                self._action_times[scope] = deque()
            
            self._action_times[scope].append(current_time)
    
    def get_current_rate(self, scope: str = "global") -> float:
        """
        Get current action rate for a scope.
        
        Returns:
            Actions per minute
        """
        with self._lock:
            if scope not in self._action_times:
                return 0.0
            
            current_time = time.time()
            action_times = self._action_times[scope]
            
            cutoff_time = current_time - self.config.window_seconds
            while action_times and action_times[0] < cutoff_time:
                action_times.popleft()
            
            if not action_times:
                return 0.0
            
            time_span = current_time - action_times[0]
            if time_span == 0:
                return 0.0
            
            return (len(action_times) / time_span) * 60
    
    def reset(self, scope: Optional[str] = None) -> None:
        """
        Reset rate limiter.
        
        Args:
            scope: Specific scope to reset, or None for all scopes
        """
        with self._lock:
            if scope is None:
                self._action_times.clear()
                logger.info("Rate limiter reset (all scopes)")
            elif scope in self._action_times:
                self._action_times[scope].clear()
                logger.info(f"Rate limiter reset (scope: {scope})")
    
    def get_stats(self) -> Dict[str, Dict[str, any]]:
        """Get rate limiter statistics."""
        with self._lock:
            stats = {}
            current_time = time.time()
            
            for scope, action_times in self._action_times.items():
                cutoff_time = current_time - self.config.window_seconds
                valid_times = [t for t in action_times if t >= cutoff_time]
                
                stats[scope] = {
                    "current_count": len(valid_times),
                    "max_count": self.config.max_actions,
                    "window_seconds": self.config.window_seconds,
                    "current_rate": self.get_current_rate(scope),
                    "utilization_percent": (len(valid_times) / self.config.max_actions) * 100
                }
            
            return stats


_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        from home_ai.core.config import get_settings
        settings = get_settings()
        _rate_limiter = RateLimiter(
            max_actions_per_minute=settings.security.rate_limit_actions_per_minute
        )
    return _rate_limiter
