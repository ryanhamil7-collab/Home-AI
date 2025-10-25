"""Twitter/X integration for social media automation."""

import os
from typing import Dict, Any, Optional, List
from loguru import logger

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    logger.warning("Tweepy not installed. Install with: pip install tweepy")

from home_ai.security.audit_logger import get_audit_logger
from home_ai.security.policy_engine import get_policy_engine, Action, ActionScope, ActionRisk


class TwitterIntegration:
    """
    Twitter/X integration for social media automation.
    
    Supports:
    - Tweet posting
    - Timeline reading
    - User information
    - Search
    - Engagement tracking
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None,
                 access_token: Optional[str] = None, access_secret: Optional[str] = None):
        """
        Initialize Twitter integration.
        
        Args:
            api_key: Twitter API key (or use TWITTER_API_KEY env var)
            api_secret: Twitter API secret (or use TWITTER_API_SECRET env var)
            access_token: Access token (or use TWITTER_ACCESS_TOKEN env var)
            access_secret: Access secret (or use TWITTER_ACCESS_SECRET env var)
        """
        if not TWEEPY_AVAILABLE:
            raise ImportError("Tweepy not installed")
        
        self.audit_logger = get_audit_logger()
        self.policy_engine = get_policy_engine()
        
        self.api_key = api_key or os.getenv("TWITTER_API_KEY")
        self.api_secret = api_secret or os.getenv("TWITTER_API_SECRET")
        self.access_token = access_token or os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = access_secret or os.getenv("TWITTER_ACCESS_SECRET")
        
        self.client = None
        if all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            try:
                self.client = tweepy.Client(
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_secret
                )
                logger.info("TwitterIntegration initialized successfully")
            except Exception as e:
                logger.error(f"Twitter client initialization failed: {e}")
        else:
            logger.warning("Twitter credentials not provided")
    
    def post_tweet(self, text: str, media_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Post a tweet.
        
        Args:
            text: Tweet text (max 280 characters)
            media_ids: Optional media IDs
        
        Returns:
            Tweet details
        """
        if not self.client:
            return {"success": False, "error": "Twitter client not initialized"}
        
        action = Action(
            scope=ActionScope.NETWORK,
            operation="post_tweet",
            risk=ActionRisk.MEDIUM,
            params={"text": text[:50]},
            description=f"Post tweet: {text[:50]}...",
            requires_confirmation=True
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            return {"success": False, "error": f"Permission denied: {reason}"}
        
        try:
            if len(text) > 280:
                return {"success": False, "error": "Tweet exceeds 280 characters"}
            
            response = self.client.create_tweet(
                text=text,
                media_ids=media_ids
            )
            
            result = {
                "success": True,
                "tweet_id": response.data["id"],
                "text": text,
                "ai_generated": True
            }
            
            self.audit_logger.log_action(
                action_type="twitter",
                action="post_tweet",
                status="completed",
                details=result
            )
            
            logger.info(f"Posted tweet: {response.data['id']}")
            return result
        
        except Exception as e:
            logger.error(f"Tweet posting failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user_info(self, username: str) -> Dict[str, Any]:
        """
        Get user information.
        
        Args:
            username: Twitter username
        
        Returns:
            User details
        """
        if not self.client:
            return {"success": False, "error": "Twitter client not initialized"}
        
        try:
            user = self.client.get_user(username=username)
            
            if not user.data:
                return {"success": False, "error": "User not found"}
            
            result = {
                "success": True,
                "user_id": user.data.id,
                "username": user.data.username,
                "name": user.data.name,
                "description": user.data.description
            }
            
            logger.info(f"Retrieved user info: {username}")
            return result
        
        except Exception as e:
            logger.error(f"User info retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    def search_tweets(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Search tweets.
        
        Args:
            query: Search query
            max_results: Maximum results to return
        
        Returns:
            Search results
        """
        if not self.client:
            return {"success": False, "error": "Twitter client not initialized"}
        
        try:
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=max_results
            )
            
            if not tweets.data:
                return {"success": True, "tweets": []}
            
            result = {
                "success": True,
                "tweets": [
                    {
                        "id": t.id,
                        "text": t.text,
                        "author_id": t.author_id
                    }
                    for t in tweets.data
                ]
            }
            
            logger.info(f"Found {len(tweets.data)} tweets for query: {query}")
            return result
        
        except Exception as e:
            logger.error(f"Tweet search failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_timeline(self, max_results: int = 10) -> Dict[str, Any]:
        """
        Get user timeline.
        
        Args:
            max_results: Maximum results to return
        
        Returns:
            Timeline tweets
        """
        if not self.client:
            return {"success": False, "error": "Twitter client not initialized"}
        
        try:
            me = self.client.get_me()
            if not me.data:
                return {"success": False, "error": "Could not get user info"}
            
            tweets = self.client.get_users_tweets(
                id=me.data.id,
                max_results=max_results
            )
            
            if not tweets.data:
                return {"success": True, "tweets": []}
            
            result = {
                "success": True,
                "tweets": [
                    {
                        "id": t.id,
                        "text": t.text
                    }
                    for t in tweets.data
                ]
            }
            
            logger.info(f"Retrieved {len(tweets.data)} timeline tweets")
            return result
        
        except Exception as e:
            logger.error(f"Timeline retrieval failed: {e}")
            return {"success": False, "error": str(e)}


_twitter_integration: Optional[TwitterIntegration] = None


def get_twitter_integration() -> TwitterIntegration:
    """Get or create Twitter integration instance."""
    global _twitter_integration
    if _twitter_integration is None:
        _twitter_integration = TwitterIntegration()
    return _twitter_integration
