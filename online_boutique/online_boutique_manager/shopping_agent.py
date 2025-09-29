#!/usr/bin/env python3
"""
AP2-Enabled Shopping Agent - Orchestrates the complete A2A + AP2 flow
Implements the 6-step autonomous commerce flow with proper AP2 mandates
"""

import os
import json
import uuid
import asyncio
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from typing import Dict, List, Optional, Any

# Import AP2 base classes
try:
    from sub_agents.payment_processor.ap2_base import (
        AP2EnabledAgent, A2AMessage, A2AMessagePart, A2aMessageBuilder,
        AP2PaymentUtilities, AP2Config,
        PAYMENT_MANDATE_DATA_KEY, CART_MANDATE_DATA_KEY, INTENT_MANDATE_DATA_KEY, CONTACT_ADDRESS_DATA_KEY,
        IntentMandate, CartMandate, PaymentMandate
    )
except ImportError:
    # Fallback imports for direct execution
    import sys
    sys.path.append('sub_agents/payment_processor')
    from ap2_base import (
        AP2EnabledAgent, A2AMessage, A2AMessagePart, A2aMessageBuilder,
        AP2PaymentUtilities, AP2Config,
        PAYMENT_MANDATE_DATA_KEY, CART_MANDATE_DATA_KEY, INTENT_MANDATE_DATA_KEY, CONTACT_ADDRESS_DATA_KEY,
        IntentMandate, CartMandate, PaymentMandate
    )

MODEL = "gemini-2.5-flash"

class AP2ShoppingAgent(AP2EnabledAgent):
    """
    AP2-enabled Shopping Agent that orchestrates the complete autonomous commerce flow:
    
    1. User Request → Shopping Agent
       ↓ (A2A + IntentMandate)
    2. Shopping Agent → Merchant Agents  
       ↓ (A2A + CartMandate)
    3. Merchant Agent → Shopping Agent
       ↓ (A2A + ContactAddress)
    4. Shopping Agent → Merchant Agent (cart update)
       ↓ (A2A + PaymentMandate)
    5. Shopping Agent → Payment Processor
       ↓ (A2A + Payment Result)
    6. Payment Processor → Shopping Agent → User
    """
    
    def __init__(self):
        super().__init__("ap2_shopping_agent")
        self.config = AP2Config()
        
        # Agent URLs for A2A communication
        self.agent_urls = {
            "catalog_service": os.environ.get("CATALOG_SERVICE_URL", "http://localhost:8095"),
            "customer_service": os.environ.get("CUSTOMER_SERVICE_URL", "http://localhost:8091"),
            "shipping_service": os.environ.get("SHIPPING_SERVICE_URL", "http://localhost:8093"),
            "payment_processor": os.environ.get("PAYMENT_PROCESSOR_URL", "http://localhost:8092"),
            "marketing_manager": os.environ.get("MARKETING_MANAGER_URL", "http://localhost:8094"),
        }
        
        # Session storage for managing multi-step flows
        self.active_sessions = {}
        
    async def handle_ap2_message(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle AP2-enabled messages - entry point for AP2 flow"""
        try:
            # Check if this is a response to an ongoing session
            context_id = message.context_id
            if context_id and context_id in self.active_sessions:
                return await self._handle_session_response(message)
            
            # Extract AP2 mandates
            intent_mandates = self.extract_ap2_data(message, INTENT_MANDATE_DATA_KEY, IntentMandate)
            cart_mandates = self.extract_ap2_data(message, CART_MANDATE_DATA_KEY, CartMandate)
            payment_mandates = self.extract_ap2_data(message, PAYMENT_MANDATE_DATA_KEY, PaymentMandate)
            
            if intent_mandates:
                return await self._process_intent_mandate(intent_mandates[0], message)
            elif cart_mandates:
                return await self._process_cart_mandate(cart_mandates[0], message)
            elif payment_mandates:
                return await self._process_payment_mandate(payment_mandates[0], message)
            else:
                return await self._handle_other_ap2_data(message)
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"AP2 message processing error: {str(e)}",
                "agent": self.agent_name
            }
    
    async def handle_legacy_message(self, message: A2AMessage) -> Dict[str, Any]:
        """
        Handle legacy non-AP2 messages by converting to AP2 flow
        This triggers the 6-step autonomous commerce flow
        """
        try:
            # Step 1: User Request → Shopping Agent
            # Extract text content and create IntentMandate
            text_content = ""
            for part in message.parts:
                if part.type == "text":
                    text_content += str(part.content) + " "
            
            user_request = text_content.strip()
            
            # Create IntentMandate from user request
            intent_mandate = self._create_intent_mandate_from_text(user_request)
            
            # Create session to track this flow
            session_id = f"session_{uuid.uuid4().hex[:8]}"
            self.active_sessions[session_id] = {
                "step": 1,
                "user_request": user_request,
                "intent_mandate": intent_mandate,
                "context_id": message.context_id or session_id,
                "created_at": datetime.utcnow().isoformat(),
                "flow_data": {}
            }
            
            # Step 2: Shopping Agent → Merchant Agents (with IntentMandate)
            return await self._step2_query_merchants(session_id, intent_mandate, message)
            
        except Exception as e:
            return {
                "status": "error", 
                "error": f"Legacy message processing error: {str(e)}",
                "agent": self.agent_name
            }
    
    def _create_intent_mandate_from_text(self, user_text: str) -> IntentMandate:
        """Convert user natural language to IntentMandate"""
        try:
            # Parse the user request to extract intent
            expiry = datetime.now() + timedelta(hours=self.max_intent_expiry_hours)
            
            return IntentMandate(
                natural_language_description=user_text,
                user_cart_confirmation_required=self.require_user_confirmation,
                intent_expiry=expiry.isoformat(),
                merchants=None,  # Allow any merchant
                requires_refundability=False
            )
        except Exception as e:
            # Fallback simple intent
            return {
                "natural_language_description": user_text,
                "user_cart_confirmation_required": True,
                "intent_expiry": (datetime.now() + timedelta(hours=24)).isoformat(),
                "merchants": None,
                "requires_refundability": False
            }
    
    async def _step2_query_merchants(self, session_id: str, intent_mandate, message: A2AMessage) -> Dict[str, Any]:
        """
        Step 2: Shopping Agent → Merchant Agents
        Send IntentMandate to relevant merchant agents and expect CartMandate back
        """
        try:
            session = self.active_sessions[session_id]
            session["step"] = 2
            
            # Determine which merchant agents to query based on intent
            relevant_agents = self._determine_relevant_agents(intent_mandate.natural_language_description)
            
            # Create A2A message with IntentMandate
            a2a_message = A2aMessageBuilder().set_context_id(session["context_id"]) \
                .add_text(f"Processing user intent: {intent_mandate.natural_language_description}") \
                .add_data(INTENT_MANDATE_DATA_KEY, intent_mandate.__dict__ if hasattr(intent_mandate, '__dict__') else intent_mandate) \
                .build()
            
            # Query each relevant agent
            merchant_responses = {}
            for agent_name in relevant_agents:
                try:
                    response = await self._send_a2a_message(agent_name, a2a_message)
                    merchant_responses[agent_name] = response
                except Exception as e:
                    print(f"Failed to query {agent_name}: {e}")
                    merchant_responses[agent_name] = {"error": str(e)}
            
            # Store responses and move to step 3
            session["flow_data"]["merchant_responses"] = merchant_responses
            session["step"] = 3
            
            return await self._step3_process_merchant_responses(session_id, merchant_responses, message)
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Step 2 processing error: {str(e)}",
                "agent": self.agent_name,
                "session_id": session_id
            }
    
    def _determine_relevant_agents(self, user_request: str) -> List[str]:
        """Determine which agents to query based on user request"""
        request_lower = user_request.lower()
        agents = []
        
        # Product-related requests
        if any(keyword in request_lower for keyword in ['buy', 'find', 'search', 'product', 'item', 'shoes', 'clothing', 'dress']):
            agents.append('catalog_service')
        
        # Always include marketing for recommendations
        agents.append('marketing_manager')
        
        # If no specific agents identified, default to catalog
        if not agents:
            agents.append('catalog_service')
            
        return agents
    
    async def _step3_process_merchant_responses(self, session_id: str, merchant_responses: Dict, message: A2AMessage) -> Dict[str, Any]:
        """
        Step 3: Process merchant responses and extract CartMandate
        Merchant Agent → Shopping Agent (A2A + CartMandate)
        """
        try:
            session = self.active_sessions[session_id]
            session["step"] = 3
            
            # Process merchant responses to build cart
            cart_items = []
            best_response = None
            
            for agent_name, response_data in merchant_responses.items():
                if "error" not in response_data:
                    # Extract cart-relevant information
                    items = self._extract_cart_items_from_response(agent_name, response_data)
                    cart_items.extend(items)
                    
                    if not best_response:
                        best_response = response_data
            
            if not cart_items:
                # Create fallback cart item from original request
                cart_items = self._create_fallback_cart_items(session["user_request"])
            
            # Create CartMandate
            cart_mandate = self._create_cart_mandate(cart_items, session["user_request"])
            
            # Store cart and move to step 4
            session["flow_data"]["cart_mandate"] = cart_mandate
            session["flow_data"]["cart_items"] = cart_items
            session["step"] = 4
            
            return await self._step4_request_contact_address(session_id, cart_mandate, message)
            
        except Exception as e:
            return {
                "status": "error", 
                "error": f"Step 3 processing error: {str(e)}",
                "agent": self.agent_name,
                "session_id": session_id
            }
    
    def _extract_cart_items_from_response(self, agent_name: str, response_data: Dict) -> List[Dict]:
        """Extract cart items from agent response"""
        items = []
        
        try:
            # Handle different response formats from different agents
            if agent_name == "catalog_service":
                # Look for product information
                products = response_data.get("products", [])
                for product in products:
                    items.append({
                        "label": product.get("name", "Product"),
                        "price": product.get("price", 99.0),
                        "quantity": 1,
                        "product_id": product.get("id", str(uuid.uuid4()))
                    })
            
            elif agent_name == "marketing_manager":
                # Look for recommended products
                recommendations = response_data.get("personalized_recommendations", [])
                for rec in recommendations:
                    items.append({
                        "label": rec.get("name", "Recommended Item"),
                        "price": rec.get("price", 79.99),
                        "quantity": 1,
                        "product_id": rec.get("product_id", str(uuid.uuid4()))
                    })
            
        except Exception as e:
            print(f"Error extracting items from {agent_name}: {e}")
        
        return items
    
    def _create_fallback_cart_items(self, user_request: str) -> List[Dict]:
        """Create fallback cart items when no merchant data available"""
        # Simple parsing to extract item and price
        import re
        
        price_match = re.search(r'\$(\d+(?:\.\d{2})?)', user_request)
        item_match = re.search(r'(?:buy|find|get)\s+(.+?)(?:\s+for|\s*$)', user_request, re.IGNORECASE)
        
        price = float(price_match.group(1)) if price_match else 99.0
        item_name = item_match.group(1).strip() if item_match else "Item"
        
        return [{
            "label": item_name,
            "price": price,
            "quantity": 1,
            "product_id": f"fallback_{uuid.uuid4().hex[:8]}"
        }]
    
    def _create_cart_mandate(self, cart_items: List[Dict], description: str) -> Dict:
        """Create CartMandate from cart items"""
        try:
            # Calculate total
            total_amount = sum(item["price"] * item["quantity"] for item in cart_items)
            
            # Create AP2 payment request structure
            payment_request = AP2PaymentUtilities.create_payment_request(
                cart_items, 
                total_amount,
                self.config.default_currency
            )
            
            cart_mandate = {
                "cart_id": str(uuid.uuid4()),
                "contents": {
                    "payment_request": {
                        "details": {
                            "id": payment_request.details.id if payment_request else str(uuid.uuid4()),
                            "total": {
                                "label": "Total",
                                "amount": {
                                    "currency": self.config.default_currency,
                                    "value": total_amount
                                }
                            },
                            "display_items": cart_items
                        }
                    }
                },
                "user_confirmation_required": self.config.require_user_confirmation,
                "created_at": datetime.utcnow().isoformat(),
                "description": description
            }
            
            return cart_mandate
            
        except Exception as e:
            # Fallback cart mandate
            total_amount = sum(item["price"] * item["quantity"] for item in cart_items)
            return {
                "cart_id": str(uuid.uuid4()),
                "total_amount": total_amount,
                "currency": self.config.default_currency,
                "items": cart_items,
                "description": description,
                "created_at": datetime.utcnow().isoformat()
            }
    
    async def _step4_request_contact_address(self, session_id: str, cart_mandate: Dict, message: A2AMessage) -> Dict[str, Any]:
        """
        Step 4: Shopping Agent → Merchant Agent (cart update)
        Request ContactAddress for shipping/billing
        """
        try:
            session = self.active_sessions[session_id]
            session["step"] = 4
            
            # For this demo, we'll simulate contact address collection
            # In a real implementation, this would query user data or prompt for address
            
            contact_address = {
                "address_line_1": "123 Demo Street",
                "address_line_2": "",
                "city": "Demo City", 
                "state": "CA",
                "postal_code": "12345",
                "country": "US",
                "phone": "+1234567890",
                "email": "demo@example.com"
            }
            
            # Store contact address and move to step 5
            session["flow_data"]["contact_address"] = contact_address
            session["step"] = 5
            
            return await self._step5_create_payment_mandate(session_id, contact_address, message)
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Step 4 processing error: {str(e)}",
                "agent": self.agent_name,
                "session_id": session_id
            }
    
    async def _step5_create_payment_mandate(self, session_id: str, contact_address: Dict, message: A2AMessage) -> Dict[str, Any]:
        """
        Step 5: Shopping Agent → Payment Processor
        Create PaymentMandate and send to payment processor
        """
        try:
            session = self.active_sessions[session_id]
            session["step"] = 5
            
            cart_mandate = session["flow_data"]["cart_mandate"]
            
            # Create PaymentMandate
            payment_mandate = {
                "mandate_id": str(uuid.uuid4()),
                "cart_contents": cart_mandate,
                "payment_methods_accepted": self.config.supported_payment_methods,
                "billing_address": contact_address,
                "shipping_address": contact_address,
                "currency": self.config.default_currency,
                "requires_confirmation": self.config.require_user_confirmation,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
            
            # Send PaymentMandate to payment processor
            a2a_message = A2aMessageBuilder().set_context_id(session["context_id"]) \
                .add_text("Processing payment mandate") \
                .add_data(PAYMENT_MANDATE_DATA_KEY, payment_mandate) \
                .build()
            
            payment_response = await self._send_a2a_message("payment_processor", a2a_message)
            
            # Store payment response and complete flow
            session["flow_data"]["payment_response"] = payment_response
            session["step"] = 6
            
            return await self._step6_complete_flow(session_id, payment_response, message)
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Step 5 processing error: {str(e)}",
                "agent": self.agent_name,
                "session_id": session_id
            }
    
    async def _step6_complete_flow(self, session_id: str, payment_response: Dict, message: A2AMessage) -> Dict[str, Any]:
        """
        Step 6: Payment Processor → Shopping Agent → User
        Complete the autonomous commerce flow and return result to user
        """
        try:
            session = self.active_sessions[session_id]
            session["step"] = 6
            session["completed_at"] = datetime.utcnow().isoformat()
            
            # Extract payment result
            payment_success = payment_response.get("status") == "success"
            
            # Create final response message
            if payment_success:
                # Extract transaction details
                response_data = payment_response.get("response", {})
                if isinstance(response_data, dict) and "artifacts" in response_data:
                    payment_result = response_data["artifacts"].get("ap2_payment_result", {})
                    transaction_id = payment_result.get("transaction_id", "unknown")
                    amount = payment_result.get("amount", 0)
                    
                    success_message = f"🎉 Payment successful! Your order has been processed.\n\n" \
                                    f"Transaction ID: {transaction_id}\n" \
                                    f"Amount: ${amount}\n" \
                                    f"Order will be shipped to your address."
                else:
                    success_message = "🎉 Payment successful! Your order has been processed."
                
                final_response = self.create_ap2_message(
                    success_message,
                    session["context_id"]
                ).add_data("order_confirmation", {
                    "session_id": session_id,
                    "payment_result": payment_response,
                    "cart_summary": session["flow_data"]["cart_mandate"],
                    "completion_time": session["completed_at"],
                    "ap2_flow_completed": True
                }).build()
                
            else:
                error_message = f"❌ Payment failed: {payment_response.get('error', 'Unknown error')}\n\n" \
                              f"Please check your payment details and try again."
                
                final_response = self.create_ap2_message(
                    error_message,
                    session["context_id"]
                ).add_data("order_failure", {
                    "session_id": session_id,
                    "error_details": payment_response,
                    "retry_available": True
                }).build()
            
            # Clean up session (optional - could keep for order history)
            # del self.active_sessions[session_id]
            
            return {
                "response": final_response.to_dict(),
                "agent": self.agent_name,
                "status": "success",
                "processing_mode": "ap2_autonomous_commerce_flow",
                "ap2_used": True,
                "session_id": session_id,
                "flow_completed": True,
                "steps_completed": 6
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Step 6 completion error: {str(e)}",
                "agent": self.agent_name,
                "session_id": session_id
            }
    
    async def _send_a2a_message(self, agent_name: str, message: A2AMessage) -> Dict[str, Any]:
        """Send A2A message to another agent"""
        try:
            agent_url = self.agent_urls.get(agent_name)
            if not agent_url:
                raise Exception(f"Unknown agent: {agent_name}")
            
            # Convert A2AMessage to JSON
            message_data = message.to_dict()
            
            # Send HTTP request
            response = requests.post(
                f"{agent_url}/ap2/message",
                json=message_data,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # Fallback to regular chat endpoint
                response = requests.post(
                    f"{agent_url}/chat", 
                    json={"message": message.parts[0].content if message.parts else ""},
                    timeout=30,
                    headers={'Content-Type': 'application/json'}
                )
                return response.json() if response.status_code == 200 else {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"error": f"A2A communication failed: {str(e)}"}
    
    async def _handle_session_response(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle responses in ongoing sessions"""
        context_id = message.context_id
        session = self.active_sessions.get(context_id, {})
        
        # Process based on current step
        current_step = session.get("step", 1)
        
        if current_step == 3:
            # Handle merchant responses
            return await self._step3_process_merchant_responses(context_id, {}, message)
        elif current_step == 5:
            # Handle payment processor response
            return await self._step6_complete_flow(context_id, {}, message)
        else:
            return {
                "status": "error", 
                "error": f"Unexpected session state: step {current_step}",
                "agent": self.agent_name
            }
    
    # ... (implement other required methods from base class)
    
    async def _process_intent_mandate(self, intent_mandate, message: A2AMessage) -> Dict[str, Any]:
        """Handle incoming IntentMandate"""
        # This would be called if another agent sends us an IntentMandate
        return await self._step2_query_merchants(f"external_{uuid.uuid4().hex[:8]}", intent_mandate, message)
    
    async def _process_cart_mandate(self, cart_mandate, message: A2AMessage) -> Dict[str, Any]:
        """Handle incoming CartMandate"""
        return {
            "response": "CartMandate received and processed",
            "agent": self.agent_name,
            "status": "success",
            "processing_mode": "ap2_cart_mandate"
        }
    
    async def _process_payment_mandate(self, payment_mandate, message: A2AMessage) -> Dict[str, Any]:
        """Handle incoming PaymentMandate"""
        return {
            "response": "PaymentMandate received and processed", 
            "agent": self.agent_name,
            "status": "success",
            "processing_mode": "ap2_payment_mandate"
        }
    
    async def _handle_other_ap2_data(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle other AP2 data types"""
        return {
            "response": "AP2 data received by shopping agent",
            "agent": self.agent_name,
            "status": "success",
            "processing_mode": "ap2_generic"
        }

# Initialize the shopping agent
shopping_agent = AP2ShoppingAgent()

# Flask app for HTTP interface
app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "agent": "ap2_shopping_agent",
        "ap2_enabled": True,
        "supported_protocols": ["a2a", "ap2", "json-rpc-2.0"],
        "flow_steps": 6,
        "autonomous_commerce": True
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Main endpoint for user requests - triggers AP2 autonomous commerce flow"""
    try:
        data = request.get_json()
        message_content = data.get('message', '')
        
        if not message_content:
            return jsonify({"error": "No message provided"}), 400
        
        # Create A2A message
        message_data = {
            "message": message_content,
            "timestamp": datetime.utcnow().isoformat(),
            "context_id": data.get("context_id", f"shopping_session_{uuid.uuid4().hex[:8]}")
        }
        
        return handle_message_sync(message_data)
        
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
        
        return handle_message_sync(data)
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

def handle_message_sync(message_data: dict):
    """Synchronous wrapper for AP2 message handling"""
    try:
        # Convert to A2AMessage
        a2a_message = create_a2a_message_from_data(message_data)
        
        # Run async handler
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(shopping_agent.handle_message(a2a_message))
            return jsonify(result)
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({
            "error": f"Message processing error: {str(e)}",
            "status": "error"
        }), 500

def create_a2a_message_from_data(message_data: dict) -> A2AMessage:
    """Convert message data to A2AMessage format"""
    try:
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
        
        elif 'message' in message_data:
            # Simple message format
            parts = [A2AMessagePart(type='text', content=message_data['message'])]
            
            return A2AMessage(
                parts=parts,
                timestamp=message_data.get('timestamp', datetime.utcnow().isoformat()),
                message_id=str(uuid.uuid4()),
                context_id=message_data.get('context_id')
            )
        
        else:
            # Fallback
            parts = [A2AMessagePart(type='text', content=str(message_data))]
            return A2AMessage(
                parts=parts,
                timestamp=datetime.utcnow().isoformat(),
                message_id=str(uuid.uuid4()),
                context_id=None
            )
    
    except Exception as e:
        # Ultimate fallback
        parts = [A2AMessagePart(type='text', content=str(message_data))]
        return A2AMessage(
            parts=parts,
            timestamp=datetime.utcnow().isoformat(),
            message_id=str(uuid.uuid4()),
            context_id=None
        )

@app.route('/sessions', methods=['GET'])
def get_active_sessions():
    """Debug endpoint to view active sessions"""
    return jsonify({
        "active_sessions": list(shopping_agent.active_sessions.keys()),
        "session_count": len(shopping_agent.active_sessions),
        "sessions_detail": shopping_agent.active_sessions
    })

@app.route('/sessions/<session_id>', methods=['GET'])
def get_session_details(session_id):
    """Get details of a specific session"""
    session = shopping_agent.active_sessions.get(session_id)
    if session:
        return jsonify(session)
    else:
        return jsonify({"error": "Session not found"}), 404

def run_server(host="0.0.0.0", port=8090):
    """Run the shopping agent server"""
    server_port = int(os.environ.get("PORT", port))
    print(f"🚀 AP2 Shopping Agent starting on port {server_port}...")
    print(f"🛍️ Autonomous Commerce Flow: 6-step A2A + AP2 enabled")
    app.run(host=host, port=server_port, debug=False)

if __name__ == '__main__':
    run_server()
