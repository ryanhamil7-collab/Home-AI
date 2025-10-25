"""Stripe integration for payment processing."""

import os
from typing import Dict, Any, Optional, List
from loguru import logger

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("Stripe not installed. Install with: pip install stripe")

from home_ai.security.audit_logger import get_audit_logger
from home_ai.security.policy_engine import get_policy_engine, Action, ActionScope, ActionRisk


class StripeIntegration:
    """
    Stripe integration for payment processing.
    
    Supports:
    - Payment processing
    - Subscription management
    - Customer management
    - Webhook handling
    - Test mode for development
    """
    
    def __init__(self, api_key: Optional[str] = None, test_mode: bool = True):
        """
        Initialize Stripe integration.
        
        Args:
            api_key: Stripe API key (or use STRIPE_API_KEY env var)
            test_mode: Use test mode (default True for safety)
        """
        if not STRIPE_AVAILABLE:
            raise ImportError("Stripe not installed")
        
        self.audit_logger = get_audit_logger()
        self.policy_engine = get_policy_engine()
        
        self.api_key = api_key or os.getenv("STRIPE_API_KEY")
        if not self.api_key:
            logger.warning("No Stripe API key provided")
        
        self.test_mode = test_mode
        
        if self.api_key:
            stripe.api_key = self.api_key
        
        logger.info(f"StripeIntegration initialized (test_mode={test_mode})")
    
    def create_payment_intent(self, amount: float, currency: str = "usd",
                             description: str = "", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create payment intent.
        
        Args:
            amount: Amount in dollars
            currency: Currency code
            description: Payment description
            metadata: Optional metadata
        
        Returns:
            Payment intent details
        """
        action = Action(
            scope=ActionScope.FINANCIAL,
            operation="create_payment_intent",
            risk=ActionRisk.HIGH,
            params={"amount": amount, "currency": currency},
            description=f"Create payment intent: ${amount}",
            requires_confirmation=True
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            return {"success": False, "error": f"Permission denied: {reason}"}
        
        try:
            amount_cents = int(amount * 100)
            
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                description=description,
                metadata=metadata or {}
            )
            
            result = {
                "success": True,
                "intent_id": intent.id,
                "amount": amount,
                "currency": currency,
                "status": intent.status,
                "client_secret": intent.client_secret
            }
            
            self.audit_logger.log_action(
                action_type="stripe",
                action="create_payment_intent",
                status="completed",
                details=result
            )
            
            logger.info(f"Created payment intent: {intent.id}")
            return result
        
        except Exception as e:
            logger.error(f"Payment intent creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def create_customer(self, email: str, name: Optional[str] = None,
                       metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create Stripe customer.
        
        Args:
            email: Customer email
            name: Customer name
            metadata: Optional metadata
        
        Returns:
            Customer details
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            
            result = {
                "success": True,
                "customer_id": customer.id,
                "email": email,
                "name": name
            }
            
            self.audit_logger.log_action(
                action_type="stripe",
                action="create_customer",
                status="completed",
                details={"customer_id": customer.id}
            )
            
            logger.info(f"Created customer: {customer.id}")
            return result
        
        except Exception as e:
            logger.error(f"Customer creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def create_subscription(self, customer_id: str, price_id: str,
                           trial_days: int = 0) -> Dict[str, Any]:
        """
        Create subscription.
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            trial_days: Trial period in days
        
        Returns:
            Subscription details
        """
        action = Action(
            scope=ActionScope.FINANCIAL,
            operation="create_subscription",
            risk=ActionRisk.HIGH,
            params={"customer_id": customer_id, "price_id": price_id},
            description="Create subscription",
            requires_confirmation=True
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            return {"success": False, "error": f"Permission denied: {reason}"}
        
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                trial_period_days=trial_days if trial_days > 0 else None
            )
            
            result = {
                "success": True,
                "subscription_id": subscription.id,
                "customer_id": customer_id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end
            }
            
            self.audit_logger.log_action(
                action_type="stripe",
                action="create_subscription",
                status="completed",
                details=result
            )
            
            logger.info(f"Created subscription: {subscription.id}")
            return result
        
        except Exception as e:
            logger.error(f"Subscription creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Get Stripe account balance.
        
        Returns:
            Balance details
        """
        try:
            balance = stripe.Balance.retrieve()
            
            result = {
                "success": True,
                "available": [
                    {"amount": b.amount / 100, "currency": b.currency}
                    for b in balance.available
                ],
                "pending": [
                    {"amount": b.amount / 100, "currency": b.currency}
                    for b in balance.pending
                ]
            }
            
            logger.info("Retrieved Stripe balance")
            return result
        
        except Exception as e:
            logger.error(f"Balance retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    def list_charges(self, limit: int = 10) -> Dict[str, Any]:
        """
        List recent charges.
        
        Args:
            limit: Number of charges to retrieve
        
        Returns:
            List of charges
        """
        try:
            charges = stripe.Charge.list(limit=limit)
            
            result = {
                "success": True,
                "charges": [
                    {
                        "id": c.id,
                        "amount": c.amount / 100,
                        "currency": c.currency,
                        "status": c.status,
                        "description": c.description,
                        "created": c.created
                    }
                    for c in charges.data
                ]
            }
            
            logger.info(f"Retrieved {len(charges.data)} charges")
            return result
        
        except Exception as e:
            logger.error(f"Charge listing failed: {e}")
            return {"success": False, "error": str(e)}


_stripe_integration: Optional[StripeIntegration] = None


def get_stripe_integration(test_mode: bool = True) -> StripeIntegration:
    """Get or create Stripe integration instance."""
    global _stripe_integration
    if _stripe_integration is None:
        _stripe_integration = StripeIntegration(test_mode=test_mode)
    return _stripe_integration
