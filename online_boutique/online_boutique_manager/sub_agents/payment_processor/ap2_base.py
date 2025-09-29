"""
AP2-enabled Base Agent Class
Agent Payment Protocol 2 (AP2) integration for A2A multi-agent systems
"""

import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

# Real AP2 imports - using actual library structure
try:
    from ap2.types.mandate import IntentMandate, CartMandate, PaymentMandate
    from ap2.types.payment_request import (
        PaymentRequest, PaymentResponse, PaymentMethodData,
        PaymentDetailsInit, PaymentItem, PaymentCurrencyAmount
    )
    from ap2.types.contact_picker import ContactAddress
    # Check if artifact_utils exists
    try:
        from ap2 import artifact_utils
    except ImportError:
        # Create a simple artifact_utils if not available
        class artifact_utils:
            @staticmethod
            def find_canonical_objects(artifacts, data_key, model_class):
                """Simple implementation of artifact utils"""
                if data_key in artifacts:
                    data = artifacts[data_key]
                    if isinstance(data, dict):
                        try:
                            return [model_class(**data)]
                        except Exception as e:
                            print(f"Error creating {model_class.__name__}: {e}")
                            return [data]
                    elif isinstance(data, list):
                        return [model_class(**item) if isinstance(item, dict) else item for item in data]
                return []
    
    AP2_AVAILABLE = True
    print("✅ Real AP2 library loaded successfully with correct imports!")
except ImportError as e:
    print(f"❌ AP2 library import failed: {e}")
    print("Please install AP2: pip install git+https://github.com/google-agentic-commerce/AP2.git@main")
    AP2_AVAILABLE = False
    raise ImportError(f"AP2 library is required but not found: {e}")

# Standard AP2 Data Keys
INTENT_MANDATE_DATA_KEY = "ap2.mandates.IntentMandate"
CART_MANDATE_DATA_KEY = "ap2.mandates.CartMandate"
PAYMENT_MANDATE_DATA_KEY = "ap2.mandates.PaymentMandate"
CONTACT_ADDRESS_DATA_KEY = "contact_picker.ContactAddress"
PAYMENT_METHOD_DATA_DATA_KEY = "payment_request.PaymentMethodData"

@dataclass
class A2AMessagePart:
    """A2A Message Part with AP2 support"""
    type: str
    content: Any
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class A2AMessage:
    """Enhanced A2A message structure with AP2 data support"""
    parts: List[A2AMessagePart]
    timestamp: str
    message_id: str
    context_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "parts": [{"type": part.type, "content": part.content, "metadata": part.metadata} for part in self.parts],
            "timestamp": self.timestamp,
            "message_id": self.message_id,
            "context_id": self.context_id,
            "artifacts": self.get_artifacts()
        }
    
    def get_artifacts(self) -> Dict[str, Any]:
        """Extract AP2 artifacts from message parts"""
        artifacts = {}
        for part in self.parts:
            if part.type == "data" and part.metadata:
                data_key = part.metadata.get("data_key")
                if data_key:
                    artifacts[data_key] = part.content
        return artifacts

class A2aMessageBuilder:
    """Builder pattern for creating A2A messages with AP2 data"""
    
    def __init__(self):
        self.parts = []
        self.context_id = None
        self.message_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()
    
    def set_context_id(self, context_id: str):
        """Set the context ID for message correlation"""
        self.context_id = context_id
        return self
    
    def add_text(self, text: str):
        """Add text content to message"""
        self.parts.append(A2AMessagePart(
            type="text",
            content=text
        ))
        return self
    
    def add_data(self, data_key: str, data: Any):
        """Add AP2 data with specific key"""
        self.parts.append(A2AMessagePart(
            type="data",
            content=data,
            metadata={"data_key": data_key}
        ))
        return self
    
    def build(self) -> A2AMessage:
        """Build the final A2A message"""
        return A2AMessage(
            parts=self.parts,
            timestamp=self.timestamp,
            message_id=self.message_id,
            context_id=self.context_id
        )

class AP2EnabledAgent(ABC):
    """Base class for agents with AP2 capabilities"""
    
    def __init__(self, name: str):
        self.agent_name = name
        self.ap2_extension_uri = "https://github.com/google-agentic-commerce/ap2/v1"
        self.default_currency = "USD"
        self.max_intent_expiry_hours = 24
        self.require_user_confirmation = True
        self.supported_payment_methods = [
            "basic-card",
            "https://google.com/pay"
        ]
    
    def create_ap2_message(self, text: str, context_id: str = None) -> A2aMessageBuilder:
        """Helper to create A2A messages with AP2 extensions"""
        builder = A2aMessageBuilder()
        if context_id:
            builder.set_context_id(context_id)
        return builder.add_text(text)
    
    def extract_ap2_data(self, message: A2AMessage, data_key: str, model_class=None):
        """Extract AP2 objects from A2A message artifacts"""
        if not AP2_AVAILABLE:
            return []
        
        artifacts = message.get_artifacts()
        data = artifacts.get(data_key)
        if data and model_class:
            try:
                if isinstance(data, dict):
                    return [model_class(**data)]
                elif isinstance(data, list):
                    return [model_class(**item) for item in data]
            except Exception as e:
                print(f"Error extracting AP2 data: {e}")
        return [data] if data else []
    
    def has_ap2_data(self, message: A2AMessage) -> bool:
        """Check if A2A message contains AP2 mandate data"""
        artifacts = message.get_artifacts()
        ap2_keys = [
            INTENT_MANDATE_DATA_KEY,
            CART_MANDATE_DATA_KEY,
            PAYMENT_MANDATE_DATA_KEY
        ]
        return any(key in artifacts for key in ap2_keys)
    
    def validate_mandate_expiry(self, mandate_with_expiry) -> bool:
        """Check if mandate hasn't expired"""
        if not hasattr(mandate_with_expiry, 'intent_expiry'):
            return True
        
        try:
            expiry_str = mandate_with_expiry.intent_expiry
            if expiry_str.endswith('Z'):
                expiry_str = expiry_str[:-1] + '+00:00'
            expiry = datetime.fromisoformat(expiry_str)
            return datetime.now(timezone.utc) < expiry
        except Exception:
            return True  # If we can't parse, assume it's valid
    
    @abstractmethod
    async def handle_ap2_message(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle AP2-enabled messages - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def handle_legacy_message(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle legacy non-AP2 messages - must be implemented by subclasses"""
        pass
    
    async def handle_message(self, message: A2AMessage) -> Dict[str, Any]:
        """Main message handler that routes to AP2 or legacy handling"""
        if self.has_ap2_data(message):
            return await self.handle_ap2_message(message)
        else:
            return await self.handle_legacy_message(message)

class AP2PaymentUtilities:
    """Utility functions for AP2 payment processing"""
    
    @staticmethod
    def create_intent_from_user_request(user_request: str, expiry_hours: int = 24):
        """Convert user natural language to IntentMandate"""
        if not AP2_AVAILABLE:
            return None
        
        expiry = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
        return IntentMandate(
            natural_language_description=user_request,
            user_cart_confirmation_required=True,
            intent_expiry=expiry.isoformat(),
            merchants=None,  # Allow any merchant
            requires_refundability=False
        )
    
    @staticmethod
    def extract_payment_total(cart_mandate) -> float:
        """Extract total payment amount from cart mandate"""
        if not cart_mandate or not hasattr(cart_mandate, 'contents'):
            return 0.0
        
        try:
            return cart_mandate.contents.payment_request.details.total.amount.value
        except AttributeError:
            return 0.0
    
    @staticmethod
    def create_payment_item(label: str, amount: float, currency: str = "USD"):
        """Create a payment item for AP2"""
        if not AP2_AVAILABLE:
            return None
        
        return PaymentItem(
            label=label,
            amount=PaymentCurrencyAmount(
                currency=currency,
                value=amount
            ),
            refund_period=30
        )
    
    @staticmethod
    def create_payment_request(items: List[Dict[str, Any]], total_amount: float, 
                             currency: str = "USD", request_id: str = None):
        """Create a payment request from items"""
        if not AP2_AVAILABLE:
            return None
        
        if not request_id:
            request_id = str(uuid.uuid4())
        
        payment_items = []
        for item in items:
            payment_item = AP2PaymentUtilities.create_payment_item(
                item.get('label', 'Item'),
                item.get('amount', 0.0),
                currency
            )
            if payment_item:
                payment_items.append(payment_item)
        
        total_item = AP2PaymentUtilities.create_payment_item("Total", total_amount, currency)
        
        return PaymentRequest(
            method_data=[PaymentMethodData(supported_methods="basic-card")],
            details=PaymentDetailsInit(
                id=request_id,
                display_items=payment_items,
                total=total_item
            )
        )

class AP2Config:
    """Configuration class for AP2 integration"""
    
    def __init__(self):
        self.ap2_enabled = AP2_AVAILABLE
        self.ap2_extension_uri = "https://github.com/google-agentic-commerce/ap2/v1"
        self.default_currency = "USD"
        self.max_intent_expiry_hours = 24
        self.require_user_confirmation = True
        self.supported_payment_methods = [
            "basic-card",
            "https://google.com/pay"
        ]
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ap2_enabled": self.ap2_enabled,
            "ap2_extension_uri": self.ap2_extension_uri,
            "default_currency": self.default_currency,
            "max_intent_expiry_hours": self.max_intent_expiry_hours,
            "require_user_confirmation": self.require_user_confirmation,
            "supported_payment_methods": self.supported_payment_methods
        }
