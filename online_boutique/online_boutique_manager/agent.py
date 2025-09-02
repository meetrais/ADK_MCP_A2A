import os
from flask import Flask, jsonify

from google.adk.agents import LlmAgent, BaseAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from typing import AsyncGenerator
import requests
import json

try:
    from . import prompt
except ImportError:
    import prompt

MODEL = "gemini-2.5-flash"

class A2AAgentProxy(BaseAgent):
    def __init__(self, name: str, agent_url: str, description: str = None):
        super().__init__(
            name=name,
            description=description or f"A2A proxy for {name} agent"
        )
        self._agent_url = agent_url
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        response_text = "Unknown error occurred"
        
        try:
            user_message = "Perform analysis"
            if hasattr(ctx, 'tool_input') and ctx.tool_input:
                user_message = str(ctx.tool_input)
            elif hasattr(ctx, 'message') and ctx.message and ctx.message.parts:
                user_message = ctx.message.parts[0].text
            
            response = requests.post(
                f"{self._agent_url}/chat",
                json={"message": user_message},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_payload = result.get("response", f"No response from {self.name}")
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
        
        content = types.Content(
            role='model',
            parts=[types.Part(text=response_text)]
        )
        
        yield Event(
            author=self.name,
            content=content
        )
    
    def get_agent_info(self) -> dict:
        try:
            response = requests.get(f"{self._agent_url}/agent-card", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return {"name": self.name, "status": "unavailable"}

A2A_AGENTS = {
    "shipping_service": {
        "url": "http://localhost:8090",
        "description": "Call shipping service agent via A2A protocol for shipping and delivery management"
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

a2a_agents = {}
for agent_name, config in A2A_AGENTS.items():
    a2a_agents[agent_name] = A2AAgentProxy(
        name=agent_name,
        agent_url=config["url"],
        description=config["description"]
    )

shipping_service_a2a_agent = a2a_agents["shipping_service"]
customer_service_a2a_agent = a2a_agents["customer_service"]
payment_processor_a2a_agent = a2a_agents["payment_processor"]
shipping_service_a2a_agent = a2a_agents["shipping_service"]
marketing_manager_a2a_agent = a2a_agents["marketing_manager"]
catalog_service_a2a_agent = a2a_agents["catalog_service"]

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
        AgentTool(agent=shipping_service_a2a_agent),
        AgentTool(agent=customer_service_a2a_agent),
        AgentTool(agent=payment_processor_a2a_agent),
        AgentTool(agent=shipping_service_a2a_agent),
        AgentTool(agent=marketing_manager_a2a_agent),
        AgentTool(agent=catalog_service_a2a_agent),
    ],
)

root_agent = online_boutique_coordinator

def run_server(host="0.0.0.0", port=8080):
    app = Flask(__name__)
    app.config['DEBUG'] = False
    app.config['TESTING'] = False

    @app.route("/health")
    def health_check():
        return jsonify({"status": "healthy"}), 200

    @app.route("/")
    def index():
        return jsonify({
            "message": "Online Boutique Coordinator is running.",
            "status": "healthy"
        })

    @app.route("/chat", methods=["POST"])
    def chat():
        try:
            from flask import request
            from google.adk.agents.invocation_context import InvocationContext
            from google.genai.types import Content, Part
            
            data = request.get_json()
            
            if not data or 'message' not in data:
                return jsonify({"error": "No message provided"}), 400
            
            user_message = data['message']
            
            if any(keyword in user_message.lower() for keyword in ['shipping', 'delivery', 'track', 'ship', 'logistics']):
                try:
                    response = requests.post(
                        'http://localhost:8090/chat',
                        json={'message': 'shipping'},
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        shipping_data = response.json()
                        return jsonify({
                            "response": {
                                "coordinator_message": "I can help you with shipping information!",
                                "shipping_service_data": shipping_data.get('response', {}),
                                "workflow": "Coordinator → Shipping Service (HTTP) → MCP Server"
                            },
                            "agent": "online_boutique_coordinator", 
                            "status": "success"
                        })
                        
                except Exception as e:
                    pass
            
            elif any(keyword in user_message.lower() for keyword in ['search', 'categories', 'featured', 'find', 'browse categories', 'what categories']):
                try:
                    if 'categories' in user_message.lower():
                        query = 'categories'
                    elif 'featured' in user_message.lower():
                        query = 'featured'  
                    elif 'search' in user_message.lower():
                        query = 'search'
                    else:
                        query = 'categories'
                    
                    response = requests.post(
                        'http://localhost:8095/chat',
                        json={'message': query},
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        catalog_data = response.json()
                        return jsonify({
                            "response": {
                                "coordinator_message": "Here's what I found in our catalog!",
                                "catalog_service_data": catalog_data.get('response', {}),
                                "workflow": "Coordinator → Catalog Service (HTTP) → MCP Server"
                            },
                            "agent": "online_boutique_coordinator",
                            "status": "success"
                        })
                        
                except Exception as e:
                    pass
            
            elif any(keyword in user_message.lower() for keyword in ['shipping', 'delivery', 'ship', 'deliver', 'track', 'tracking', 'shipping cost', 'shipping rate', 'how long', 'when will', 'return policy']):
                try:
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
                        query = 'general'
                    
                    response = requests.post(
                        'http://localhost:8093/chat',
                        json={'message': query},
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        shipping_data = response.json()
                        return jsonify({
                            "response": {
                                "coordinator_message": "Here's the shipping information you requested!",
                                "shipping_service_data": shipping_data.get('response', {}),
                                "workflow": "Coordinator → Shipping Service (HTTP)"
                            },
                            "agent": "online_boutique_coordinator",
                            "status": "success"
                        })
                        
                except Exception as e:
                    pass
            
            return jsonify({
                "response": f"Hello! I'm your Online Boutique Coordinator. I can help you find products, process orders, and provide customer support. You asked about: '{user_message}'. Try asking about clothing, sweaters, or other products!",
                "agent": "online_boutique_coordinator",
                "status": "success"
            })
            
        except Exception as e:
            return jsonify({
                "error": f"Error processing request: {str(e)}",
                "status": "error"
            }), 500

    server_port = int(os.environ.get("PORT", port))
    app.run(host=host, port=server_port, debug=False, threaded=True)

if __name__ == '__main__':
    run_server()
