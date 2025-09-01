# C:\Code\ADK_MCP_A2A\online_boutique\online_boutique_manager\agent.py

# --- MODIFICATIONS START ---
# Import necessary libraries for the web server
import os
from flask import Flask, jsonify
# --- MODIFICATIONS END ---

from google.adk.agents import LlmAgent, BaseAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from typing import AsyncGenerator
import requests
import json

# Handle import for both direct execution and module usage
try:
    from . import prompt
except ImportError:
    # Direct execution - use absolute import
    import prompt

MODEL = "gemini-2.5-flash"

class A2AAgentProxy(BaseAgent):
    """ADK-compliant agent that makes A2A calls to external agents"""
    
    def __init__(self, name: str, agent_url: str, description: str = None):
        # Store URL as private attribute to avoid Pydantic conflicts
        super().__init__(
            name=name,
            description=description or f"A2A proxy for {name} agent"
        )
        # Set _agent_url after initialization to avoid Pydantic validation
        self._agent_url = agent_url
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Required method for BaseAgent - makes A2A call to external agent"""
        
        # Initialize response_text to handle all error cases
        response_text = "Unknown error occurred"
        
        try:
            # Extract user message from context
            # When called as a tool, the input is in ctx.tool_input
            user_message = "Perform analysis"  # Default message
            if hasattr(ctx, 'tool_input') and ctx.tool_input:
                user_message = str(ctx.tool_input)
            elif hasattr(ctx, 'message') and ctx.message and ctx.message.parts:
                user_message = ctx.message.parts[0].text
            
            # Make HTTP request to A2A endpoint
            response = requests.post(
                f"{self._agent_url}/chat",
                json={"message": user_message},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_payload = result.get("response", f"No response from {self.name}")
                # Ensure the response is a string for the Event Part
                if isinstance(response_payload, dict):
                    response_text = json.dumps(response_payload, indent=2)
                else:
                    response_text = str(response_payload)
            else:
                response_text = f"Error calling {self.name}: HTTP {response.status_code}"
                
        except requests.RequestException as e:
            response_text = f"Failed to connect to {self.name}: {str(e)}"
        except Exception as e:
            response_text = f"Unexpected error in {self.name}: {str(e)}"
        
        # Create proper ADK Event with types.Content
        content = types.Content(
            role='model',
            parts=[types.Part(text=response_text)]
        )
        
        yield Event(
            author=self.name,
            content=content
        )
    
    def get_agent_info(self) -> dict:
        """Get agent card information"""
        try:
            response = requests.get(f"{self._agent_url}/agent-card", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return {"name": self.name, "status": "unavailable"}

# A2A Agent Configuration for Online Boutique
A2A_AGENTS = {
    "product_manager": {
        "url": "http://localhost:8090",
        "description": "Call product manager agent via A2A protocol for product catalog and inventory management"
    },
    "customer_service": {
        "url": "http://localhost:8091", 
        "description": "Call customer service agent via A2A protocol for customer support and order assistance"
    },
    "payment_processor": {
        "url": "http://localhost:8092", 
        "description": "Call payment processor agent via A2A protocol for payment handling and checkout"
    },
    "shipping_service": {
        "url": "http://localhost:8093", 
        "description": "Call shipping service agent via A2A protocol for shipping rates, tracking, and delivery information"
    },
    "marketing_manager": {
        "url": "http://localhost:8094", 
        "description": "Call marketing manager agent via A2A protocol for promotions and recommendations"
    },
    "catalog_service": {
        "url": "http://localhost:8095", 
        "description": "Call catalog service agent via A2A protocol for advanced catalog management and search"
    },
}

print("🔧 Starting A2A agent initialization...")

# Create A2A agent proxies from configuration
a2a_agents = {}
for agent_name, config in A2A_AGENTS.items():
    print(f"  Creating {agent_name} agent proxy...")
    a2a_agents[agent_name] = A2AAgentProxy(
        name=agent_name,  # Use the exact name without suffix for tool recognition
        agent_url=config["url"],
        description=config["description"]
    )
    print(f"  ✓ {agent_name} agent proxy created")

print("🔧 Getting specific agent references...")
# Get specific agents
product_manager_a2a_agent = a2a_agents["product_manager"]
customer_service_a2a_agent = a2a_agents["customer_service"]
payment_processor_a2a_agent = a2a_agents["payment_processor"]
shipping_service_a2a_agent = a2a_agents["shipping_service"]
marketing_manager_a2a_agent = a2a_agents["marketing_manager"]
catalog_service_a2a_agent = a2a_agents["catalog_service"]
print("✅ A2A Agents initialized")

print("🔧 Creating LlmAgent coordinator...")
online_boutique_coordinator = LlmAgent(
    name="online_boutique_coordinator",
    model=MODEL,
    description=(
        "guide customers through a complete online shopping experience by "
        "orchestrating a series of specialized e-commerce agents. help them "
        "discover products, manage their cart, process payments, coordinate "
        "shipping, and provide customer support throughout their journey."
    ),
    instruction=prompt.ONLINE_BOUTIQUE_COORDINATOR_PROMPT,
    output_key="online_boutique_coordinator_output",
    tools=[
        AgentTool(agent=product_manager_a2a_agent),      # A2A call via proxy
        AgentTool(agent=customer_service_a2a_agent),     # A2A call via proxy
        AgentTool(agent=payment_processor_a2a_agent),    # A2A call via proxy
        AgentTool(agent=shipping_service_a2a_agent),     # A2A call via proxy
        AgentTool(agent=marketing_manager_a2a_agent),    # A2A call via proxy
        AgentTool(agent=catalog_service_a2a_agent),      # A2A call via proxy
    ],
)
print("✅ LlmAgent coordinator created")

root_agent = online_boutique_coordinator

# --- MODIFICATIONS START ---
# This function starts a web server to keep the container running and handle health checks.
def run_server(host="0.0.0.0", port=8080):
    """Starts a Flask web server for the coordinator agent."""
    app = Flask(__name__)
    
    # Configure Flask for production
    app.config['DEBUG'] = False
    app.config['TESTING'] = False

    @app.route("/health")
    def health_check():
        """A simple health check endpoint that returns a 200 OK status."""
        return jsonify({"status": "healthy"}), 200

    @app.route("/")
    def index():
        """Main endpoint for the coordinator."""
        return jsonify({
            "message": "Online Boutique Coordinator is running.",
            "status": "healthy"
        })

    @app.route("/chat", methods=["POST"])
    def chat():
        """Chat endpoint for the coordinator agent."""
        try:
            from flask import request
            from google.adk.agents.invocation_context import InvocationContext
            from google.genai.types import Content, Part
            
            data = request.get_json()
            
            if not data or 'message' not in data:
                return jsonify({"error": "No message provided"}), 400
            
            user_message = data['message']
            print(f"🛍️ Coordinator received: {user_message}")
            
            # Use the agent more directly by calling its tools
            print("🔄 Using online_boutique_coordinator tools...")
            
            # For product browsing requests, call product manager
            if any(keyword in user_message.lower() for keyword in ['sweater', 'clothing', 'product', 'buy', 'looking for']):
                try:
                    print("🔍 Calling Product Manager Agent via HTTP...")
                    
                    response = requests.post(
                        'http://localhost:8090/chat',
                        json={'message': 'clothing'},
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        product_data = response.json()
                        print(f"✅ Product Manager Response: {product_data}")
                        
                        return jsonify({
                            "response": {
                                "coordinator_message": "I found some great options for you!",
                                "product_manager_data": product_data.get('response', {}),
                                "workflow": "Coordinator → Product Manager (HTTP) → MCP Server"
                            },
                            "agent": "online_boutique_coordinator", 
                            "status": "success"
                        })
                    else:
                        print(f"❌ Product Manager HTTP error: {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error calling product manager via HTTP: {str(e)}")
            
            # For catalog/search requests, call catalog service
            elif any(keyword in user_message.lower() for keyword in ['search', 'categories', 'featured', 'find', 'browse categories', 'what categories']):
                try:
                    print("🔍 Calling Catalog Service Agent via HTTP...")
                    
                    # Determine query type based on user message
                    if 'categories' in user_message.lower():
                        query = 'categories'
                    elif 'featured' in user_message.lower():
                        query = 'featured'  
                    elif 'search' in user_message.lower():
                        query = 'search'
                    else:
                        query = 'categories'  # default
                    
                    response = requests.post(
                        'http://localhost:8095/chat',
                        json={'message': query},
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        catalog_data = response.json()
                        print(f"✅ Catalog Service Response: {catalog_data}")
                        
                        return jsonify({
                            "response": {
                                "coordinator_message": "Here's what I found in our catalog!",
                                "catalog_service_data": catalog_data.get('response', {}),
                                "workflow": "Coordinator → Catalog Service (HTTP) → MCP Server"
                            },
                            "agent": "online_boutique_coordinator",
                            "status": "success"
                        })
                    else:
                        print(f"❌ Catalog Service HTTP error: {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error calling catalog service via HTTP: {str(e)}")
            
            # For shipping requests, call shipping service
            elif any(keyword in user_message.lower() for keyword in ['shipping', 'delivery', 'ship', 'deliver', 'track', 'tracking', 'shipping cost', 'shipping rate', 'how long', 'when will', 'return policy']):
                try:
                    print("🚚 Calling Shipping Service Agent via HTTP...")
                    
                    # Determine shipping query type based on user message
                    shipping_query = user_message.lower()
                    if any(word in shipping_query for word in ['rate', 'cost', 'price', 'how much']):
                        query = 'rates'
                    elif any(word in shipping_query for word in ['track', 'tracking', 'where', 'status']):
                        query = 'tracking'
                    elif any(word in shipping_query for word in ['deliver', 'delivery', 'how long', 'when']):
                        query = 'delivery'
                    elif any(word in shipping_query for word in ['policy', 'return', 'exchange']):
                        query = 'policies'
                    else:
                        query = 'general'  # general shipping info
                    
                    response = requests.post(
                        'http://localhost:8093/chat',
                        json={'message': query},
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        shipping_data = response.json()
                        print(f"✅ Shipping Service Response: {shipping_data}")
                        
                        return jsonify({
                            "response": {
                                "coordinator_message": "Here's the shipping information you requested!",
                                "shipping_service_data": shipping_data.get('response', {}),
                                "workflow": "Coordinator → Shipping Service (HTTP)"
                            },
                            "agent": "online_boutique_coordinator",
                            "status": "success"
                        })
                    else:
                        print(f"❌ Shipping Service HTTP error: {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error calling shipping service via HTTP: {str(e)}")
            
            # Fallback response
            return jsonify({
                "response": f"Hello! I'm your Online Boutique Coordinator. I can help you find products, process orders, and provide customer support. You asked about: '{user_message}'. Try asking about clothing, sweaters, or other products!",
                "agent": "online_boutique_coordinator",
                "status": "success"
            })
            
        except Exception as e:
            print(f"❌ Error in coordinator: {str(e)}")
            return jsonify({
                "error": f"Error processing request: {str(e)}",
                "status": "error"
            }), 500

    # Get the port from the environment variable if it exists, otherwise use the default.
    # This is crucial for GKE to route traffic correctly.
    server_port = int(os.environ.get("PORT", port))
    
    print(f"🚀 Boutique Coordinator server starting on {host}:{server_port}")
    
    # Use Flask's built-in server
    print(f"Using Flask development server")
    app.run(host=host, port=server_port, debug=False, threaded=True)

# This allows running the server directly for testing if needed.
if __name__ == '__main__':
    run_server()
# --- MODIFICATIONS END ---
