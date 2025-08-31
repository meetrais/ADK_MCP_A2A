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

from . import prompt

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
    "shipping_coordinator": {
        "url": "http://localhost:8093", 
        "description": "Call shipping coordinator agent via A2A protocol for order fulfillment and delivery"
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

# Create A2A agent proxies from configuration
a2a_agents = {}
for agent_name, config in A2A_AGENTS.items():
    a2a_agents[agent_name] = A2AAgentProxy(
        name=agent_name,  # Use the exact name without suffix for tool recognition
        agent_url=config["url"],
        description=config["description"]
    )

# Get specific agents
product_manager_a2a_agent = a2a_agents["product_manager"]
customer_service_a2a_agent = a2a_agents["customer_service"]
payment_processor_a2a_agent = a2a_agents["payment_processor"]
shipping_coordinator_a2a_agent = a2a_agents["shipping_coordinator"]
marketing_manager_a2a_agent = a2a_agents["marketing_manager"]
catalog_service_a2a_agent = a2a_agents["catalog_service"]
print("A2A Agents initialized")

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
        AgentTool(agent=shipping_coordinator_a2a_agent), # A2A call via proxy
        AgentTool(agent=marketing_manager_a2a_agent),    # A2A call via proxy
        AgentTool(agent=catalog_service_a2a_agent),      # A2A call via proxy
    ],
)

root_agent = online_boutique_coordinator

# --- MODIFICATIONS START ---
# This function starts a web server to keep the container running and handle health checks.
def run_server(host="0.0.0.0", port=8080):
    """Starts a Flask web server for the coordinator agent."""
    app = Flask(__name__)

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

    # Get the port from the environment variable if it exists, otherwise use the default.
    # This is crucial for GKE to route traffic correctly.
    server_port = int(os.environ.get("PORT", port))
    
    print(f"🚀 Boutique Coordinator server starting on {host}:{server_port}")
    app.run(host=host, port=server_port)

# This allows running the server directly for testing if needed.
if __name__ == '__main__':
    run_server()
# --- MODIFICATIONS END ---