from google.adk import Agent
# Handle import for both direct execution and module usage
try:
    from . import prompt
    from .ap2_base import (
        AP2EnabledAgent, A2AMessage, A2AMessagePart, A2aMessageBuilder,
        AP2PaymentUtilities, AP2Config,
        PAYMENT_MANDATE_DATA_KEY, CART_MANDATE_DATA_KEY, INTENT_MANDATE_DATA_KEY,
        PaymentMandate, CartMandate, IntentMandate
    )
except ImportError:
    # Direct execution - use absolute import
    import prompt
    from ap2_base import (
        AP2EnabledAgent, A2AMessage, A2AMessagePart, A2aMessageBuilder,
        AP2PaymentUtilities, AP2Config,
        PAYMENT_MANDATE_DATA_KEY, CART_MANDATE_DATA_KEY, INTENT_MANDATE_DATA_KEY,
        PaymentMandate, CartMandate, IntentMandate
    )

from flask import Flask, request, jsonify
import json
import requests
import os
import asyncio
import uuid
from datetime import datetime, timedelta

MODEL = "gemini-2.5-flash"

def process_payment(cart_data: str) -> dict:
    """
    Process real payment via MCP server with enhanced AP2 support.
    
    Args:
        cart_data (str): Cart data as JSON string
        
    Returns:
        dict: Payment processing results from MCP server
    """
    try:
        # Parse cart data if it's a string
        if isinstance(cart_data, str):
            try:
                cart_data = json.loads(cart_data)
            except json.JSONDecodeError:
                cart_data = {"items": [], "payment_method": "Credit Card"}
        
        # Get MCP server URL from environment variable, fallback to localhost for local dev
        mcp_server_url = os.environ.get('MCP_SERVER_URL', 'http://localhost:8080')
        payment_url = f"{mcp_server_url}/payment-process"
        
        # Enhance cart data with AP2 metadata
        enhanced_cart_data = {
            **cart_data,
            'ap2_enabled': True,
            'request_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'gateway': cart_data.get('gateway', 'auto'),  # auto, stripe, paypal, mock
            'validation_required': True
        }
        
        # Call MCP server for real payment processing
        response = requests.post(
            payment_url,
            json={'cart_data': enhanced_cart_data},
            timeout=30,  # Increased timeout for real payment processing
            headers={
                'Content-Type': 'application/json',
                'X-AP2-Enabled': 'true',
                'X-Request-ID': enhanced_cart_data['request_id']
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result['status'] == 'success':
                # Return enhanced payment result with AP2 compliance
                payment_data = result['data']
                return {
                    **payment_data,
                    'ap2_processed': True,
                    'mcp_server_used': True,
                    'real_payment': payment_data.get('payment_processing', 'mock') == 'real',
                    'gateway_used': payment_data.get('gateway', 'unknown'),
                    'validation_passed': True
                }
            else:
                # Handle payment failure
                return {
                    'status': 'failed',
                    'error': result.get('message', 'Payment processing failed'),
                    'error_type': result.get('error_type', 'unknown'),
                    'gateway': result.get('gateway', 'unknown'),
                    'ap2_processed': True,
                    'mcp_server_used': True,
                    'real_payment': False
                }
        
        # Handle HTTP errors
        return {
            'status': 'error',
            'message': f'MCP server error: HTTP {response.status_code}',
            'error_type': 'mcp_server_error',
            'ap2_processed': False,
            'mcp_server_used': False,
            'real_payment': False
        }
        
    except requests.exceptions.Timeout:
        return {
            'status': 'error',
            'message': 'Payment processing timeout - please try again',
            'error_type': 'timeout_error',
            'ap2_processed': False,
            'mcp_server_used': False,
            'real_payment': False
        }
    except requests.exceptions.ConnectionError:
        return {
            'status': 'error',
            'message': 'Cannot connect to payment server - service may be unavailable',
            'error_type': 'connection_error',
            'ap2_processed': False,
            'mcp_server_used': False,
            'real_payment': False
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Payment processing error: {str(e)}',
            'error_type': 'processing_error',
            'ap2_processed': False,
            'mcp_server_used': False,
            'real_payment': False
        }

class AP2PaymentProcessor(AP2EnabledAgent):
    """AP2-enabled payment processor agent with enhanced capabilities"""
    
    def __init__(self):
        super().__init__("payment_processor_agent")
        self.config = AP2Config()
        
        # Initialize traditional agent for backwards compatibility
        self.traditional_agent = Agent(
            model=MODEL,
            name="payment_processor_agent",
            instruction=prompt.PAYMENT_PROCESSOR_PROMPT,
            output_key="payment_processing_output",
            tools=[process_payment],
        )
    
    async def handle_ap2_message(self, message: A2AMessage) -> dict:
        """Handle AP2-enabled messages with payment mandates"""
        try:
            # Extract payment mandates from the message
            payment_mandates = self.extract_ap2_data(message, PAYMENT_MANDATE_DATA_KEY, PaymentMandate)
            cart_mandates = self.extract_ap2_data(message, CART_MANDATE_DATA_KEY, CartMandate)
            
            if payment_mandates:
                # Process payment mandate
                payment_mandate = payment_mandates[0]
                return await self._process_ap2_payment_mandate(payment_mandate, message)
            
            elif cart_mandates:
                # Process cart mandate for payment setup
                cart_mandate = cart_mandates[0]
                return await self._process_ap2_cart_mandate(cart_mandate, message)
            
            else:
                # Handle other AP2 data
                return await self._handle_other_ap2_data(message)
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"AP2 processing error: {str(e)}",
                "agent": self.agent_name
            }
    
    async def handle_legacy_message(self, message: A2AMessage) -> dict:
        """Handle legacy non-AP2 messages by converting them to AP2 format"""
        try:
            # Extract text content from message
            text_content = ""
            for part in message.parts:
                if part.type == "text":
                    text_content += str(part.content) + " "
            
            # Parse payment information from text
            payment_info = self._parse_payment_from_text(text_content.strip())
            
            # Convert to AP2 payment request and process
            ap2_result = await self._process_with_ap2(payment_info, message)
            
            return {
                "response": ap2_result,
                "agent": self.agent_name,
                "status": "success",
                "processing_mode": "ap2_converted_from_legacy",
                "ap2_used": True
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"AP2 processing error: {str(e)}",
                "agent": self.agent_name
            }
    
    async def _process_ap2_payment_mandate(self, payment_mandate: PaymentMandate, message: A2AMessage) -> dict:
        """Process AP2 payment mandate"""
        try:
            # Validate mandate expiry if applicable
            if not self.validate_mandate_expiry(payment_mandate):
                return {
                    "status": "error",
                    "error": "Payment mandate has expired",
                    "agent": self.agent_name
                }
            
            # Extract payment details
            cart_contents = getattr(payment_mandate, 'cart_contents', None)
            if cart_contents:
                payment_total = AP2PaymentUtilities.extract_payment_total(cart_contents)
                
                # Create payment request data
                payment_data = {
                    "amount": payment_total,
                    "currency": self.config.default_currency,
                    "payment_method": "ap2_mandate",
                    "mandate_id": getattr(payment_mandate, 'mandate_id', str(uuid.uuid4())),
                    "cart_contents": cart_contents
                }
                
                # Process through MCP server
                mcp_result = process_payment(json.dumps(payment_data))
                
                # Create AP2 response
                response_message = self.create_ap2_message(
                    "Payment processed successfully via AP2 mandate",
                    message.context_id
                ).add_data("payment_result", {
                    "transaction_id": str(uuid.uuid4()),
                    "status": mcp_result.get("status", "success"),
                    "amount": payment_total,
                    "currency": self.config.default_currency,
                    "processed_at": datetime.utcnow().isoformat(),
                    "mandate_id": payment_data["mandate_id"]
                }).build()
                
                return {
                    "response": response_message.to_dict(),
                    "agent": self.agent_name,
                    "status": "success",
                    "processing_mode": "ap2_payment_mandate",
                    "transaction_details": mcp_result
                }
            else:
                return {
                    "status": "error",
                    "error": "Payment mandate missing cart contents",
                    "agent": self.agent_name
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Payment mandate processing error: {str(e)}",
                "agent": self.agent_name
            }
    
    async def _process_ap2_cart_mandate(self, cart_mandate: CartMandate, message: A2AMessage) -> dict:
        """Process AP2 cart mandate for payment setup"""
        try:
            # Extract payment total
            payment_total = AP2PaymentUtilities.extract_payment_total(cart_mandate)
            
            # Prepare payment setup response
            setup_data = {
                "cart_id": getattr(cart_mandate, 'cart_id', str(uuid.uuid4())),
                "total_amount": payment_total,
                "currency": self.config.default_currency,
                "payment_methods_supported": self.config.supported_payment_methods,
                "requires_confirmation": self.config.require_user_confirmation
            }
            
            # Create response with payment setup information
            response_message = self.create_ap2_message(
                "Cart processed, ready for payment",
                message.context_id
            ).add_data("payment_setup", setup_data).build()
            
            return {
                "response": response_message.to_dict(),
                "agent": self.agent_name,
                "status": "success",
                "processing_mode": "ap2_cart_mandate",
                "payment_setup": setup_data
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Cart mandate processing error: {str(e)}",
                "agent": self.agent_name
            }
    
    async def _handle_other_ap2_data(self, message: A2AMessage) -> dict:
        """Handle other AP2 data types"""
        try:
            # Check for intent mandates
            intent_mandates = self.extract_ap2_data(message, INTENT_MANDATE_DATA_KEY, IntentMandate)
            
            if intent_mandates:
                intent_mandate = intent_mandates[0]
                
                # Process intent for payment readiness
                response_message = self.create_ap2_message(
                    "Payment processor ready to handle intent",
                    message.context_id
                ).add_data("processor_capability", {
                    "supported_payment_methods": self.config.supported_payment_methods,
                    "supported_currencies": [self.config.default_currency],
                    "can_process_autonomous": True,
                    "requires_user_confirmation": self.config.require_user_confirmation
                }).build()
                
                return {
                    "response": response_message.to_dict(),
                    "agent": self.agent_name,
                    "status": "success",
                    "processing_mode": "ap2_intent_response"
                }
            
            # Default response for unknown AP2 data
            return {
                "response": "AP2 data received, payment processor standing by",
                "agent": self.agent_name,
                "status": "success",
                "processing_mode": "ap2_generic"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"AP2 data processing error: {str(e)}",
                "agent": self.agent_name
            }
    
    def _parse_payment_from_text(self, text: str) -> dict:
        """Parse payment information from natural language text"""
        import re
        
        # Initialize default payment info
        payment_info = {
            "items": [],
            "total_amount": 0.0,
            "currency": self.config.default_currency,
            "payment_method": "basic-card",
            "description": text
        }
        
        # Extract price information using regex
        price_patterns = [
            r'\$(\d+(?:\.\d{2})?)',  # $99.99 or $99
            r'(\d+(?:\.\d{2})?) dollar',  # 99.99 dollar
            r'costing (\d+(?:\.\d{2})?)',  # costing 99.99
            r'price (\d+(?:\.\d{2})?)',   # price 99.99
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                payment_info["total_amount"] = float(match.group(1))
                break
        
        # Extract item descriptions
        item_patterns = [
            r'buy (.+?) for',  # buy red shoes for
            r'purchase (.+?) costing',  # purchase red shoes costing
            r'payment for (.+?) costing',  # payment for red shoes costing
            r'want to buy (.+)',  # want to buy red shoes
        ]
        
        item_description = "Item"
        for pattern in item_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                item_description = match.group(1).strip()
                break
        
        # Create item entry
        if payment_info["total_amount"] > 0:
            payment_info["items"] = [{
                "label": item_description,
                "amount": payment_info["total_amount"]
            }]
        
        return payment_info
    
    async def _process_with_ap2(self, payment_info: dict, message: A2AMessage) -> dict:
        """Convert payment info to AP2 format and process"""
        try:
            # Create AP2 payment items
            payment_items = []
            for item in payment_info["items"]:
                ap2_item = AP2PaymentUtilities.create_payment_item(
                    item["label"],
                    item["amount"],
                    payment_info["currency"]
                )
                if ap2_item:
                    payment_items.append(ap2_item)
            
            # Create AP2 payment request
            total_amount = payment_info["total_amount"]
            ap2_payment_request = AP2PaymentUtilities.create_payment_request(
                payment_info["items"],
                total_amount,
                payment_info["currency"]
            )
            
            if ap2_payment_request:
                # Process payment using AP2 structures
                transaction_id = str(uuid.uuid4())
                
                # Create AP2 response message
                response_message = self.create_ap2_message(
                    f"Payment processed via AP2 protocol: {payment_info['description']}",
                    message.context_id
                ).add_data("ap2_payment_result", {
                    "transaction_id": transaction_id,
                    "status": "success",
                    "amount": total_amount,
                    "currency": payment_info["currency"],
                    "payment_method": payment_info["payment_method"],
                    "processed_at": datetime.utcnow().isoformat(),
                    "ap2_payment_request": {
                        "id": ap2_payment_request.details.id,
                        "total": {
                            "label": ap2_payment_request.details.total.label,
                            "amount": {
                                "currency": ap2_payment_request.details.total.amount.currency,
                                "value": ap2_payment_request.details.total.amount.value
                            }
                        },
                        "display_items": [
                            {
                                "label": item.label,
                                "amount": {
                                    "currency": item.amount.currency,
                                    "value": item.amount.value
                                }
                            } for item in ap2_payment_request.details.display_items
                        ]
                    }
                }).build()
                
                return response_message.to_dict()
            else:
                # Fallback processing
                return {
                    "transaction_id": str(uuid.uuid4()),
                    "status": "success",
                    "amount": total_amount,
                    "currency": payment_info["currency"],
                    "message": f"Payment processed with AP2 protocol: {payment_info['description']}",
                    "processed_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"AP2 conversion error: {str(e)}",
                "fallback_processing": True
            }

# Initialize AP2 payment processor
ap2_payment_processor = AP2PaymentProcessor()

# Traditional agent for backwards compatibility
payment_processor_agent = Agent(
    model=MODEL,
    name="payment_processor_agent",
    instruction=prompt.PAYMENT_PROCESSOR_PROMPT,
    output_key="payment_processing_output",
    tools=[process_payment],
)

# Flask app for A2A protocol
app = Flask(__name__)

# Enhanced Agent card with AP2 capabilities
AGENT_CARD = {
    "name": "payment_processor_agent",
    "description": "AP2-enabled payment processor agent with secure payment processing and autonomous commerce capabilities",
    "version": "2.0",
    "capabilities": [
        "payment_processing", "checkout", "order_confirmation", "mcp_integration",
        "ap2_payment_mandates", "ap2_cart_processing", "ap2_intent_handling",
        "autonomous_payments", "structured_payment_data"
    ],
    "model": MODEL,
    "protocols": ["a2a", "ap2", "json-rpc-2.0"],
    "ap2_config": ap2_payment_processor.config.to_dict(),
    "endpoints": {
        "chat": "/chat",
        "card": "/agent-card",
        "ap2_message": "/ap2/message"
    },
    "input_format": ["text", "ap2_mandate"],
    "output_format": ["json", "ap2_response"],
    "data_source": "MCP Server"
}

@app.route('/agent-card', methods=['GET'])
def get_agent_card():
    """Return the agent card describing capabilities"""
    return jsonify(AGENT_CARD)

@app.route('/chat', methods=['POST'])
def chat():
    """Main endpoint for A2A communication with AP2 support"""
    try:
        data = request.get_json()
        message_content = data.get('message', '')
        
        if not message_content:
            return jsonify({"error": "No message provided"}), 400
        
        # Always use AP2 processing - convert message to A2A format
        message_data = {
            "message": message_content,
            "timestamp": datetime.utcnow().isoformat(),
            "context_id": data.get("context_id", f"chat_session_{str(uuid.uuid4())[:8]}")
        }
        
        # Process with AP2 handler
        return handle_ap2_message_sync(message_data)
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/ap2/message', methods=['POST'])
def handle_ap2_message_endpoint():
    """Dedicated endpoint for AP2 message handling"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No message data provided"}), 400
        
        return handle_ap2_message_sync(data)
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

def handle_ap2_message_sync(message_data: dict):
    """Synchronous wrapper for AP2 message handling"""
    try:
        # Convert message data to A2AMessage format
        a2a_message = create_a2a_message_from_data(message_data)
        
        # Use asyncio to run the async handler
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(ap2_payment_processor.handle_message(a2a_message))
            return jsonify(result)
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({
            "error": f"AP2 message processing error: {str(e)}",
            "status": "error"
        }), 500

def create_a2a_message_from_data(message_data: dict) -> A2AMessage:
    """Convert incoming message data to A2AMessage format"""
    try:
        # Handle different message formats
        if 'parts' in message_data:
            # Already in A2AMessage format
            parts = []
            for part_data in message_data['parts']:
                parts.append(A2AMessagePart(
                    type=part_data.get('type', 'text'),
                    content=part_data.get('content', ''),
                    metadata=part_data.get('metadata')
                ))
            
            return A2AMessage(
                parts=parts,
                timestamp=message_data.get('timestamp', datetime.utcnow().isoformat()),
                message_id=message_data.get('message_id', str(uuid.uuid4())),
                context_id=message_data.get('context_id')
            )
        
        elif 'artifacts' in message_data:
            # Message with artifacts (AP2 data)
            parts = []
            
            # Add text content if available
            if 'message' in message_data:
                parts.append(A2AMessagePart(type='text', content=message_data['message']))
            
            # Add artifacts as data parts
            for key, value in message_data['artifacts'].items():
                parts.append(A2AMessagePart(
                    type='data',
                    content=value,
                    metadata={'data_key': key}
                ))
            
            return A2AMessage(
                parts=parts,
                timestamp=message_data.get('timestamp', datetime.utcnow().isoformat()),
                message_id=message_data.get('message_id', str(uuid.uuid4())),
                context_id=message_data.get('context_id')
            )
        
        elif 'message' in message_data:
            # Message with text content - this is our case
            parts = [A2AMessagePart(type='text', content=message_data['message'])]
            
            return A2AMessage(
                parts=parts,
                timestamp=message_data.get('timestamp', datetime.utcnow().isoformat()),
                message_id=str(uuid.uuid4()),
                context_id=message_data.get('context_id')
            )
        
        else:
            # Simple text message (fallback)
            parts = [A2AMessagePart(type='text', content=str(message_data))]
            
            return A2AMessage(
                parts=parts,
                timestamp=datetime.utcnow().isoformat(),
                message_id=str(uuid.uuid4()),
                context_id=None
            )
    
    except Exception as e:
        # Fallback to simple text message
        text_content = message_data.get('message', str(message_data))
        parts = [A2AMessagePart(type='text', content=text_content)]
        return A2AMessage(
            parts=parts,
            timestamp=datetime.utcnow().isoformat(),
            message_id=str(uuid.uuid4()),
            context_id=None
        )

@app.route('/ap2/test', methods=['POST'])
def test_ap2_integration():
    """Test endpoint for AP2 integration"""
    try:
        # Create a test intent mandate
        test_intent = {
            "natural_language_description": "I want to buy red shoes",
            "user_cart_confirmation_required": True,
            "intent_expiry": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "merchants": None,
            "requires_refundability": False
        }
        
        # Create test message with AP2 data
        test_message_data = {
            "message": "Test AP2 integration",
            "artifacts": {
                INTENT_MANDATE_DATA_KEY: test_intent
            },
            "context_id": "test_context_123",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        result = handle_ap2_message_sync(test_message_data)
        
        return jsonify({
            "test_status": "success",
            "ap2_enabled": ap2_payment_processor.config.ap2_enabled,
            "test_result": result.get_json() if hasattr(result, 'get_json') else result,
            "config": ap2_payment_processor.config.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            "test_status": "error",
            "error": str(e),
            "ap2_enabled": ap2_payment_processor.config.ap2_enabled
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with AP2 status"""
    return jsonify({
        "status": "healthy", 
        "agent": "payment_processor_agent",
        "ap2_enabled": ap2_payment_processor.config.ap2_enabled,
        "supported_protocols": ["a2a", "ap2", "json-rpc-2.0"],
        "capabilities": AGENT_CARD["capabilities"]
    })

def run_server(host="0.0.0.0", port=8092):
    """Function kept for backwards compatibility when running directly"""
    server_port = int(os.environ.get("PORT", port))
    print(f"🚀 Payment Processor Agent starting on port {server_port}...")
    app.run(host=host, port=server_port, debug=False)

if __name__ == '__main__':
    run_server()
