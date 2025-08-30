# Multi-Agent Online Boutique Management System

A sophisticated multi-agent e-commerce system built using Model Context Protocol(MCP), Agent to Agent protocol(A2A) and Google Agent Development Kit(ADK). This system replicates the financial advisor architecture to provide comprehensive online shopping experience.

## 1. Setup

### Prerequisites
- Python 3.9+
- Conda package manager
- Poetry dependency manager
- Google API key

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/meetrais/ADK_MCP_A2A.git
   cd ADK_MCP_A2A
   ```

2. **Set up environment variables:**
   - Create a `.env` file inside the `online_boutique/online_boutique_manager` directory
   - Add the following entry to the `.env` file:
     ```
     GOOGLE_API_KEY=YourGoogleAPIKeyHere
     ```

3. **Navigate to the project directory:**
   ```bash
   cd online_boutique
   ```

4. **Create and activate conda environment:**
   ```bash
   conda create --name boutique
   conda activate boutique
   ```

5. **Install dependencies:**
   ```bash
   poetry install
   ```

6. **Run the system:**
   Open multiple terminals in your IDE and run the following commands in separate terminals:

   **Terminal 1 - MCP Server:**
   ```bash
   poetry run python online_boutique_manager/simple-mcp-server/boutique_mcp_server.py
   ```

   **Terminal 2 - Product Manager Agent:**
   ```bash
   poetry run python -m online_boutique_manager.sub_agents.product_manager.agent
   ```

   **Terminal 3 - Customer Service Agent:**
   ```bash
   poetry run python -m online_boutique_manager.sub_agents.customer_service.agent
   ```

   **Terminal 4 - Payment Processor Agent:**
   ```bash
   poetry run python -m online_boutique_manager.sub_agents.payment_processor.agent
   ```

   **Terminal 5 - Catalog Service Agent:**
   ```bash
   poetry run python -m online_boutique_manager.sub_agents.catalog_service.agent
   ```

   **Terminal 6 - Web Interface:**
   ```bash
   adk web
   ```

## 2. Code Overview

### System Architecture

The Online Boutique Management System is built on a multi-agent architecture where specialized agents collaborate through both the MCP protocol and Agent-to-Agent (A2A) HTTP communication to provide comprehensive e-commerce services.

#### Core Components

**1. Main Online Boutique Coordinator (`online_boutique_manager/agent.py`)**
- **Role**: Central orchestrator coordinating between specialized e-commerce sub-agents
- **Framework**: Built on Google ADK using Gemini 2.5 Flash model
- **Communication**: Uses A2A proxy agents to communicate with sub-agents via HTTP
- **Architecture**: Implements `A2AAgentProxy` class for seamless integration with external agents
- **Port Configuration**:
  - Product Manager: `localhost:8090`
  - Customer Service: `localhost:8091`
  - Payment Processor: `localhost:8092`
  - Shipping Coordinator: `localhost:8093`
  - Marketing Manager: `localhost:8094`
  - Catalog Service: `localhost:8095`

**2. MCP Server (`online_boutique_manager/simple-mcp-server/boutique_mcp_server.py`)**
- **Purpose**: Provides e-commerce tools and mock data services
- **Technology**: Flask-based REST API server
- **Port**: `localhost:3002`
- **Endpoints**:
  - `/products` - Product catalog management
  - `/customer-support` - Customer service responses
  - `/payment-process` - Payment processing
  - `/shipping-coordinate` - Shipping coordination
  - `/marketing-recommendations` - Marketing and promotions
  - `/catalog-service` - Advanced catalog operations
  - `/health` - Health check endpoint
- **Data**: Generates realistic mock e-commerce data for demonstrations

#### Specialized Sub-Agents

**1. Product Manager Agent (`sub_agents/product_manager/agent.py`)**
- **Purpose**: Product catalog and inventory management
- **Port**: `8090`
- **Integration**: Communicates with MCP server for product data
- **Capabilities**:
  - Product catalog retrieval and display
  - Inventory status and availability
  - Product discovery and recommendations
  - Category-based product organization
- **Communication**: Provides A2A endpoints (`/chat`, `/agent-card`, `/health`)

**2. Customer Service Agent (`sub_agents/customer_service/agent.py`)**
- **Purpose**: Customer support and assistance
- **Port**: `8091`
- **Integration**: Uses MCP server for support responses
- **Capabilities**:
  - Customer inquiry handling
  - Return and exchange policy information
  - Shipping and delivery inquiries
  - Size and product guidance
  - Order status assistance
- **Output**: Detailed customer support with policy information and next steps

**3. Payment Processor Agent (`sub_agents/payment_processor/agent.py`)**
- **Purpose**: Secure payment processing and checkout
- **Port**: `8092`
- **Integration**: Leverages MCP server for payment processing
- **Capabilities**:
  - Multiple payment method support
  - Secure checkout processing
  - Order confirmation and receipts
  - Transaction validation
  - Payment security compliance
- **Output**: Complete payment processing with order confirmations

**4. Catalog Service Agent (`sub_agents/catalog_service/agent.py`)**
- **Purpose**: Advanced catalog management and search
- **Port**: `8095`
- **Integration**: Uses MCP server for catalog operations
- **Capabilities**:
  - Advanced product search functionality
  - Category management and organization
  - Featured product curation
  - Product filtering and discovery
  - Search suggestions and recommendations
- **Output**: Comprehensive catalog services with search results and categories

### Key Features

#### Agent-to-Agent Communication (A2A)
- **HTTP-based Protocol**: Each agent runs as an independent Flask server
- **RESTful Endpoints**: Standardized `/chat`, `/agent-card`, and `/health` endpoints
- **Proxy Architecture**: Main coordinator uses `A2AAgentProxy` for seamless communication
- **Async Support**: Built on ADK's async event system for non-blocking operations
- **Error Handling**: Comprehensive error handling and timeout management

#### E-commerce Shopping Pipeline
1. **Product Discovery**: Catalog Service provides advanced search and browsing
2. **Product Information**: Product Manager delivers detailed product data
3. **Customer Support**: Customer Service assists throughout the journey
4. **Checkout Process**: Payment Processor handles secure transactions
5. **Coordination**: Main Coordinator orchestrates the entire experience

#### Structured Shopping Experience
Based on the system prompts, the workflow follows a customer-centric approach:

1. **Welcome Introduction**: System presents capabilities and shopping options
2. **Product Discovery**: Customers browse categories or search for specific items
3. **Product Selection**: Detailed product information and recommendations
4. **Customer Support**: Assistance with questions, sizing, and policies
5. **Secure Checkout**: Payment processing with order confirmation
6. **Order Fulfillment**: Shipping coordination and tracking information

### Technology Stack

- **Framework**: Google ADK (Agent Development Kit)
- **LLM Model**: Gemini 2.5 Flash
- **Communication**: 
  - A2A Protocol (HTTP/REST)
  - MCP (Model Context Protocol)
- **Language**: Python 3.9+
- **Web Framework**: Flask
- **Dependency Management**: Poetry
- **Environment Management**: Conda
- **Data Format**: JSON for inter-agent communication

### Project Structure

```
online_boutique/
├── online_boutique_manager/
│   ├── agent.py              # Main coordinator with A2A proxy system
│   ├── prompt.py             # System prompts and workflow instructions
│   ├── simple-mcp-server/    # MCP server implementation
│   │   └── boutique_mcp_server.py # Flask server with e-commerce tools
│   ├── sub_agents/           # Specialized e-commerce agents
│   │   ├── product_manager/  # Product catalog management (port 8090)
│   │   │   ├── agent.py      # A2A-enabled product management agent
│   │   │   └── prompt.py     # Product manager instructions
│   │   ├── customer_service/ # Customer support (port 8091)
│   │   │   ├── agent.py      # A2A-enabled customer service agent
│   │   │   └── prompt.py     # Customer service instructions
│   │   ├── payment_processor/ # Payment processing (port 8092)
│   │   │   ├── agent.py      # A2A-enabled payment agent
│   │   │   └── prompt.py     # Payment processor instructions
│   │   └── catalog_service/  # Advanced catalog (port 8095)
│   │       ├── agent.py      # A2A-enabled catalog service agent
│   │       └── prompt.py     # Catalog service instructions
│   └── tools/                # Shared utilities (currently empty)
├── pyproject.toml           # Poetry configuration with ADK dependencies
└── README.md               # This documentation
```

### Agent Communication Flow

1. **Customer Request**: Client interacts with boutique coordinator via ADK web interface
2. **Agent Orchestration**: Coordinator determines which sub-agents to invoke
3. **A2A Communication**: HTTP POST requests sent to sub-agent `/chat` endpoints
4. **MCP Integration**: Sub-agents call MCP server for specialized e-commerce operations
5. **Response Assembly**: Results aggregated and formatted by coordinator
6. **Customer Delivery**: Final shopping assistance presented to customer

### Dependencies

**Core Dependencies:**
- `google-cloud-aiplatform[adk,agent-engines]` - ADK framework
- `google-genai` - Gemini model integration
- `google-adk` - Agent development tools
- `flask` - Web framework for A2A communication
- `requests` - HTTP client for inter-service communication
- `pydantic` - Data validation and parsing
- `python-dotenv` - Environment variable management

**Development Dependencies:**
- `pytest` - Testing framework
- `black` - Code formatting
- `pytest-asyncio` - Async testing support

### Security Notice
This system is designed for demonstration and educational purposes. All transactions are simulated - no real payments are processed.

This architecture provides a robust, scalable, and maintainable foundation for comprehensive e-commerce services through specialized agent collaboration, following the same proven patterns as the financial advisor system.
