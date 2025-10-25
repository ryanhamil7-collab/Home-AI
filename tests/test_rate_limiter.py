"""Tests for rate limiter."""

import pytest
import time

from home_ai.security.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test RateLimiter class."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter for testing."""
        return RateLimiter(max_actions_per_minute=10)
    
    def test_allow_under_limit(self, rate_limiter):
        """Test that actions under limit are allowed."""
        for i in range(5):
            allowed, wait_time = rate_limiter.check_rate_limit("test")
            assert allowed is True
            assert wait_time is None
            rate_limiter.record_action("test")
    
    def test_block_over_limit(self, rate_limiter):
        """Test that actions over limit are blocked."""
        for i in range(10):
            rate_limiter.record_action("test")
        
        allowed, wait_time = rate_limiter.check_rate_limit("test")
        assert allowed is False
        assert wait_time is not None
        assert wait_time > 0
    
    def test_separate_scopes(self, rate_limiter):
        """Test that different scopes have separate limits."""
        for i in range(10):
            rate_limiter.record_action("file")
        
        allowed, wait_time = rate_limiter.check_rate_limit("network")
        assert allowed is True
    
    def test_get_current_rate(self, rate_limiter):
        """Test getting current rate."""
        for i in range(5):
            rate_limiter.record_action("test")
            time.sleep(0.1)
        
        rate = rate_limiter.get_current_rate("test")
        assert rate > 0
    
    def test_reset(self, rate_limiter):
        """Test resetting rate limiter."""
        for i in range(10):
            rate_limiter.record_action("test")
        
        allowed, _ = rate_limiter.check_rate_limit("test")
        assert allowed is False
        
        rate_limiter.reset("test")
        
        allowed, _ = rate_limiter.check_rate_limit("test")
        assert allowed is True
