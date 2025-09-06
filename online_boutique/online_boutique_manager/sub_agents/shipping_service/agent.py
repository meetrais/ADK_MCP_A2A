from google.adk import Agent
# Handle import for both direct execution and module usage
try:
    from . import prompt
except ImportError:
    # Direct execution - use absolute import
    import prompt
from flask import Flask, request, jsonify
import json
import requests
import os

MODEL = "gemini-2.5-flash"

def get_shipping_info(query_type: str) -> dict:
    """
    Get shipping information and handle shipping-related queries.
    
    Args:
        query_type (str): Type of shipping query (e.g., 'rates', 'tracking', 'delivery', 'policies')
        
    Returns:
        dict: Shipping information results
    """
    try:
        # Handle different types of shipping queries
        shipping_data = {}
        
        if 'rate' in query_type.lower() or 'cost' in query_type.lower() or 'price' in query_type.lower():
            shipping_data = {
                'status': 'success',
                'type': 'shipping_rates',
                'data': {
                    'standard_shipping': {
                        'name': 'Standard Shipping',
                        'cost': '$5.99',
                        'delivery_time': '5-7 business days',
                        'description': 'Reliable delivery for most orders'
                    },
                    'express_shipping': {
                        'name': 'Express Shipping',
                        'cost': '$12.99',
                        'delivery_time': '2-3 business days',
                        'description': 'Faster delivery for urgent orders'
                    },
                    'overnight_shipping': {
                        'name': 'Overnight Shipping',
                        'cost': '$24.99',
                        'delivery_time': '1 business day',
                        'description': 'Next-day delivery for rush orders'
                    },
                    'free_shipping': {
                        'name': 'Free Standard Shipping',
                        'cost': '$0.00',
                        'delivery_time': '5-7 business days',
                        'description': 'Free shipping on orders over $50'
                    }
                }
            }
        
        elif 'track' in query_type.lower() or 'status' in query_type.lower():
            shipping_data = {
                'status': 'success',
                'type': 'tracking_info',
                'data': {
                    'tracking_help': 'To track your order, please provide your order number and email address.',
                    'tracking_url': 'https://boutique.example.com/tracking',
                    'contact_support': 'For tracking assistance, contact customer service at support@boutique.com'
                }
            }
        
        elif 'deliver' in query_type.lower() or 'time' in query_type.lower():
            shipping_data = {
                'status': 'success',
                'type': 'delivery_info',
                'data': {
                    'delivery_areas': ['United States', 'Canada', 'United Kingdom', 'European Union'],
                    'standard_delivery': '5-7 business days',
                    'express_delivery': '2-3 business days',
                    'overnight_delivery': '1 business day',
                    'international_delivery': '10-15 business days',
                    'note': 'Delivery times may vary based on location and product availability'
                }
            }
        
        elif 'polic' in query_type.lower() or 'return' in query_type.lower():
            shipping_data = {
                'status': 'success',
                'type': 'shipping_policies',
                'data': {
                    'return_policy': {
                        'return_window': '30 days from delivery',
                        'return_shipping': 'Customer responsible for return shipping costs',
                        'free_returns': 'Free returns on defective items'
                    },
                    'shipping_policies': {
                        'processing_time': '1-2 business days',
                        'weekend_processing': 'Orders placed on weekends ship on Monday',
                        'holiday_shipping': 'Shipping may be delayed during holidays'
                    }
                }
            }
        
        else:
            # General shipping information
            shipping_data = {
                'status': 'success',
                'type': 'general_shipping_info',
                'data': {
                    'available_services': ['Standard Shipping', 'Express Shipping', 'Overnight Shipping'],
                    'free_shipping_threshold': '$50.00',
                    'shipping_regions': ['US', 'Canada', 'UK', 'EU'],
                    'customer_service': 'support@boutique.com',
                    'help_topics': ['Shipping Rates', 'Order Tracking', 'Delivery Times', 'Return Policy']
                }
            }
        
        return shipping_data
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error processing shipping request: {str(e)}'
        }

# Agent definition for shipping service
shipping_service_agent = Agent(
    model=MODEL,
    name="shipping_service_agent",
    instruction=prompt.SHIPPING_SERVICE_PROMPT,
    output_key="shipping_service_output",
    tools=[get_shipping_info],
)

# Flask app for A2A protocol
app = Flask(__name__)

# Agent card
AGENT_CARD = {
    "name": "shipping_service_agent",
    "description": "Shipping service agent that handles shipping rates, tracking, delivery information, and shipping policies",
    "version": "1.0",
    "capabilities": ["shipping_rates", "order_tracking", "delivery_info", "shipping_policies", "customer_support"],
    "model": MODEL,
    "endpoints": {
        "chat": "/chat",
        "card": "/agent-card"
    },
    "input_format": "text",
    "output_format": "json",
    "data_source": "Internal Shipping System"
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
        
        # Directly call the tool function to bypass the complex runner
        response_text = get_shipping_info(query_type=message)
        
        return jsonify({
            "response": response_text,
            "agent": "shipping_service_agent",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "agent": "shipping_service_agent"})

def run_server(host="0.0.0.0", port=8080):
    """Function kept for backwards compatibility when running directly"""
    server_port = int(os.environ.get("PORT", port))
    print(f"🚀 Shipping Service Agent starting on port {server_port}...")
    app.run(host=host, port=server_port, debug=False)

if __name__ == '__main__':
    run_server()
