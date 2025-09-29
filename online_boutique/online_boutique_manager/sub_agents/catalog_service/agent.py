from google.adk import Agent
import os
import sys

# Handle import for both direct execution and module usage
try:
    from . import prompt
    from ..payment_processor.ap2_base import (
        AP2EnabledAgent, A2AMessage, A2AMessagePart, A2aMessageBuilder,
        AP2PaymentUtilities, AP2Config,
        PAYMENT_MANDATE_DATA_KEY, CART_MANDATE_DATA_KEY, INTENT_MANDATE_DATA_KEY,
        IntentMandate, CartMandate, PaymentMandate
    )
except ImportError:
    # Direct execution - use absolute import
    # Add the current directory and payment_processor to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    payment_processor_dir = os.path.join(current_dir, '..', 'payment_processor')
    sys.path.insert(0, current_dir)
    sys.path.insert(0, payment_processor_dir)
    
    try:
        import prompt
    except ImportError:
        # Create a minimal prompt if not available
        class prompt:
            CATALOG_SERVICE_PROMPT = """
Role: Act as an advanced catalog service specialist for an online boutique.
You are responsible for managing the comprehensive product catalog, advanced search functionality, category organization, and featured product curation.

Your main responsibilities include:

1. Advanced Catalog Management:
   - Organize and maintain the complete product catalog structure
   - Manage product categories, subcategories, and hierarchies
   - Ensure product data consistency and accuracy
   - Handle catalog updates and new product additions

2. Search and Discovery:
   - Provide advanced search functionality across all products
   - Support filtering by multiple attributes (price, size, color, brand, etc.)
   - Implement intelligent search suggestions and autocomplete
   - Handle complex search queries and product matching

When customers need catalog services, use the get_catalog_data function to access our comprehensive catalog management system.

Format your responses to be well-organized and informative, helping customers discover products through both browsing and search functionality.
"""
    
    from ap2_base import (
        AP2EnabledAgent, A2AMessage, A2AMessagePart, A2aMessageBuilder,
        AP2PaymentUtilities, AP2Config,
        PAYMENT_MANDATE_DATA_KEY, CART_MANDATE_DATA_KEY, INTENT_MANDATE_DATA_KEY,
        IntentMandate, CartMandate, PaymentMandate
    )

from flask import Flask, request, jsonify
import json
import requests
import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

MODEL = "gemini-2.5-flash"

def get_catalog_data(query: str) -> dict:
    """
    Get catalog data from MCP server.
    
    Args:
        query (str): Catalog query (e.g., 'search', 'categories', 'featured')
        
    Returns:
        dict: Catalog data results from MCP server
    """
    try:
        # Get MCP server URL from environment variable, fallback to localhost for local dev
        mcp_server_url = os.environ.get('MCP_SERVER_URL', 'http://localhost:3002')
        catalog_url = f"{mcp_server_url}/catalog-service"
        
        # Call MCP server
        response = requests.post(
            catalog_url,
            json={'query': query},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result['status'] == 'success':
                return result['data']
        
        return {
            'status': 'error',
            'message': f'Failed to get catalog data. Server returned: {response.status_code}'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error connecting to MCP server: {str(e)}'
        }

class AP2CatalogAgent(AP2EnabledAgent):
    """AP2-enabled Catalog Agent that handles IntentMandates and returns CartMandates"""
    
    def __init__(self):
        super().__init__("catalog_service_agent")
        self.config = AP2Config()
        
        # Sample product catalog
        self.products = [
            {"id": "SHOE001", "name": "Red Leather Shoes", "price": 99.0, "category": "shoes", "stock": 10},
            {"id": "SHOE002", "name": "Blue Running Shoes", "price": 79.99, "category": "shoes", "stock": 15},
            {"id": "DRESS001", "name": "Black Evening Dress", "price": 159.99, "category": "clothing", "stock": 5},
            {"id": "DRESS002", "name": "Red Cocktail Dress", "price": 120.0, "category": "clothing", "stock": 8},
            {"id": "SHIRT001", "name": "White Cotton Shirt", "price": 45.0, "category": "clothing", "stock": 20},
        ]
    
    async def handle_ap2_message(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle AP2 messages with IntentMandates"""
        try:
            # Extract IntentMandate
            intent_mandates = self.extract_ap2_data(message, INTENT_MANDATE_DATA_KEY, IntentMandate)
            
            if intent_mandates:
                intent_mandate = intent_mandates[0]
                return await self._process_intent_mandate(intent_mandate, message)
            else:
                return await self._handle_other_ap2_data(message)
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"AP2 message processing error: {str(e)}",
                "agent": self.agent_name
            }
    
    async def handle_legacy_message(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle legacy messages by converting to product search"""
        try:
            # Extract search query from message
            text_content = ""
            for part in message.parts:
                if part.type == "text":
                    text_content += str(part.content) + " "
            
            search_query = text_content.strip()
            
            # Search products
            products = self._search_products(search_query)
            
            return {
                "response": {
                    "products": products,
                    "search_query": search_query,
                    "total_results": len(products)
                },
                "agent": self.agent_name,
                "status": "success",
                "processing_mode": "legacy_product_search"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Legacy message processing error: {str(e)}",
                "agent": self.agent_name
            }
    
    async def _process_intent_mandate(self, intent_mandate, message: A2AMessage) -> Dict[str, Any]:
        """Process IntentMandate and return CartMandate"""
        try:
            # Extract user intent from natural language description
            user_intent = intent_mandate.natural_language_description if hasattr(intent_mandate, 'natural_language_description') else str(intent_mandate.get('natural_language_description', ''))
            
            # Search for relevant products
            products = self._search_products(user_intent)
            
            if products:
                # Create CartMandate from found products
                cart_mandate = self._create_cart_mandate_from_products(products, user_intent, message.context_id)
                
                # Create AP2 response message
                response_message = self.create_ap2_message(
                    f"Found {len(products)} products matching your request",
                    message.context_id
                ).add_data(CART_MANDATE_DATA_KEY, cart_mandate).build()
                
                return {
                    "response": response_message.to_dict(),
                    "agent": self.agent_name,
                    "status": "success",
                    "processing_mode": "ap2_intent_to_cart_mandate",
                    "products_found": len(products)
                }
            else:
                # No products found - return empty cart mandate
                empty_cart = self._create_empty_cart_mandate(user_intent, message.context_id)
                
                response_message = self.create_ap2_message(
                    "No products found matching your request",
                    message.context_id
                ).add_data(CART_MANDATE_DATA_KEY, empty_cart).build()
                
                return {
                    "response": response_message.to_dict(),
                    "agent": self.agent_name,
                    "status": "success",
                    "processing_mode": "ap2_empty_cart_mandate",
                    "products_found": 0
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"IntentMandate processing error: {str(e)}",
                "agent": self.agent_name
            }
    
    def _search_products(self, query: str) -> List[Dict]:
        """Search products based on query"""
        query_lower = query.lower()
        matching_products = []
        
        for product in self.products:
            # Simple keyword matching
            if (query_lower in product["name"].lower() or 
                query_lower in product["category"].lower() or
                any(keyword in product["name"].lower() for keyword in query_lower.split())):
                matching_products.append(product)
        
        # If no exact matches, return some default products
        if not matching_products and self.products:
            matching_products = self.products[:2]  # Return first 2 as fallback
        
        return matching_products
    
    def _create_cart_mandate_from_products(self, products: List[Dict], description: str, context_id: str) -> Dict:
        """Create CartMandate from product list"""
        try:
            # Convert products to cart items
            cart_items = []
            total_amount = 0
            
            for product in products[:3]:  # Limit to 3 products
                cart_items.append({
                    "label": product["name"],
                    "price": product["price"],
                    "quantity": 1,
                    "product_id": product["id"],
                    "category": product["category"]
                })
                total_amount += product["price"]
            
            # Create CartMandate structure
            cart_mandate = {
                "cart_id": str(uuid.uuid4()),
                "contents": {
                    "payment_request": {
                        "details": {
                            "id": str(uuid.uuid4()),
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
                "description": description,
                "merchant": "catalog_service",
                "context_id": context_id
            }
            
            return cart_mandate
            
        except Exception as e:
            # Fallback cart mandate
            return self._create_empty_cart_mandate(description, context_id)
    
    def _create_empty_cart_mandate(self, description: str, context_id: str) -> Dict:
        """Create empty CartMandate when no products found"""
        return {
            "cart_id": str(uuid.uuid4()),
            "contents": {
                "payment_request": {
                    "details": {
                        "id": str(uuid.uuid4()),
                        "total": {
                            "label": "Total",
                            "amount": {
                                "currency": self.config.default_currency,
                                "value": 0.0
                            }
                        },
                        "display_items": []
                    }
                }
            },
            "user_confirmation_required": True,
            "created_at": datetime.utcnow().isoformat(),
            "description": description,
            "merchant": "catalog_service",
            "context_id": context_id,
            "empty": True
        }
    
    async def _handle_other_ap2_data(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle other AP2 data types"""
        return {
            "response": "AP2 data received by catalog service",
            "agent": self.agent_name,
            "status": "success",
            "processing_mode": "ap2_generic"
        }

# Initialize AP2 catalog agent
ap2_catalog_agent = AP2CatalogAgent()

# Traditional agent for backwards compatibility
try:
    # Try to use the imported prompt
    prompt_instruction = prompt.CATALOG_SERVICE_PROMPT
except AttributeError:
    # Fallback if attribute doesn't exist
    prompt_instruction = """
Role: Act as an advanced catalog service specialist for an online boutique.
You are responsible for managing the comprehensive product catalog, advanced search functionality, category organization, and featured product curation.

Your main responsibilities include:

1. Advanced Catalog Management:
   - Organize and maintain the complete product catalog structure
   - Manage product categories, subcategories, and hierarchies
   - Ensure product data consistency and accuracy
   - Handle catalog updates and new product additions

2. Search and Discovery:
   - Provide advanced search functionality across all products
   - Support filtering by multiple attributes (price, size, color, brand, etc.)
   - Implement intelligent search suggestions and autocomplete
   - Handle complex search queries and product matching

When customers need catalog services, use the get_catalog_data function to access our comprehensive catalog management system.

Format your responses to be well-organized and informative, helping customers discover products through both browsing and search functionality.
"""

catalog_service_agent = Agent(
    model=MODEL,
    name="catalog_service_agent",
    instruction=prompt_instruction,
    output_key="catalog_service_output",
    tools=[get_catalog_data],
)

# Flask app for A2A protocol
app = Flask(__name__)

# Agent card
AGENT_CARD = {
    "name": "catalog_service_agent",
    "description": "Catalog service agent that provides advanced catalog management and search using MCP server",
    "version": "1.0",
    "capabilities": ["catalog_management", "product_search", "category_management", "featured_products", "mcp_integration"],
    "model": MODEL,
    "endpoints": {
        "chat": "/chat",
        "card": "/agent-card"
    },
    "input_format": "text",
    "output_format": "json",
    "data_source": "MCP Server"
}

@app.route('/agent-card', methods=['GET'])
def get_agent_card():
    """Return the agent card describing capabilities"""
    return jsonify(AGENT_CARD)

@app.route('/chat', methods=['POST'])
def chat():
    """Main endpoint for A2A communication"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        # Use AP2 agent for processing
        message_data = {
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "context_id": data.get("context_id", f"catalog_session_{uuid.uuid4().hex[:8]}")
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
            result = loop.run_until_complete(ap2_catalog_agent.handle_message(a2a_message))
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

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "agent": "catalog_service_agent",
        "ap2_enabled": True,
        "supported_protocols": ["a2a", "ap2", "json-rpc-2.0"],
        "capabilities": ["IntentMandate", "CartMandate", "product_search"]
    })

def run_server(host="0.0.0.0", port=8095):
    """Function kept for backwards compatibility when running directly"""
    server_port = int(os.environ.get("PORT", port))
    print(f"🚀 Catalog Service Agent starting on port {server_port}...")
    app.run(host=host, port=server_port, debug=False)

if __name__ == '__main__':
    run_server()
