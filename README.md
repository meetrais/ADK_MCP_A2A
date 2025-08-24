# Multi-Agent Financial Advisor Management System

A sophisticated multi-agent financial advisory system built using Model Context Protocol(MCP), Agent to Agent protocol(A2A) and Google Agent Development Kit(ADK).

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
   - Create a `.env` file inside the `financial_advisor_management/financial_advisor` directory
   - Add the following entry to the `.env` file:
     ```
     GOOGLE_API_KEY=YourGoogleAPIKeyHere
     ```

3. **Navigate to the project directory:**
   ```bash
   cd financial_advisor_management
   ```

4. **Create and activate conda environment:**
   ```bash
   conda create --name ama
   conda activate ama
   ```

5. **Install dependencies:**
   ```bash
   poetry install
   ```

6. **Run the system:**
   Open multiple terminals in your IDE and run the following commands in separate terminals:

   **Terminal 1 - MCP Server:**
   ```bash
   poetry run python financial_advisor/simple-mcp-server/mcp_server.py
   ```

   **Terminal 2 - Data Analyst Agent:**
   ```bash
   poetry run python -m financial_advisor.sub_agents.data_analyst.agent
   ```

   **Terminal 3 - Execution Analyst Agent:**
   ```bash
   poetry run python -m financial_advisor.sub_agents.execution_analyst.agent
   ```

   **Terminal 4 - Risk Analyst Agent:**
   ```bash
   poetry run python -m financial_advisor.sub_agents.risk_analyst.agent
   ```

   **Terminal 5 - Trading Analyst Agent:**
   ```bash
   poetry run python -m financial_advisor.sub_agents.trading_analyst.agent
   ```

   **Terminal 6 - Web Interface:**
   ```bash
   adk web
   ```

## 2. Code Overview

### System Architecture

The Financial Advisor Management System is built on a multi-agent architecture where specialized agents collaborate through both the MCP protocol and Agent-to-Agent (A2A) HTTP communication to provide comprehensive financial advisory services.  

<img width="1211" height="653" alt="image" src="https://github.com/user-attachments/assets/9e885142-19bc-4253-8672-3d8b8e9921cc" />


#### Core Components

**1. Main Financial Advisor Agent (`financial_advisor/agent.py`)**
- **Role**: Central orchestrator coordinating between specialized sub-agents
- **Framework**: Built on Google ADK using Gemini 2.5 Flash model
- **Communication**: Uses A2A proxy agents to communicate with sub-agents via HTTP
- **Architecture**: Implements `A2AAgentProxy` class for seamless integration with external agents
- **Port Configuration**:
  - Data Analyst: `localhost:8080`
  - Execution Analyst: `localhost:8081`
  - Trading Analyst: `localhost:8082`
  - Risk Analyst: `localhost:8083`

**2. MCP Server (`financial_advisor/simple-mcp-server/mcp_server.py`)**
- **Purpose**: Provides financial analysis tools and mock data services
- **Technology**: Flask-based REST API server
- **Port**: `localhost:3001`
- **Endpoints**:
  - `/analyze` - Market data analysis for tickers
  - `/execution-analyze` - Execution strategy analysis
  - `/trading-analyze` - Trading strategy analysis
  - `/risk-analyze` - Risk assessment analysis
  - `/health` - Health check endpoint
- **Data**: Generates realistic mock financial data for demonstrations

#### Specialized Sub-Agents

**1. Data Analyst Agent (`sub_agents/data_analyst/agent.py`)**
- **Purpose**: Market data collection, processing, and analysis
- **Port**: `8080`
- **Integration**: Communicates with MCP server for market data
- **Capabilities**:
  - Stock ticker analysis
  - Price and volume data processing
  - Market trend analysis
  - Trading recommendations
- **Communication**: Provides A2A endpoints (`/chat`, `/agent-card`, `/health`)

**2. Risk Analyst Agent (`sub_agents/risk_analyst/agent.py`)**
- **Purpose**: Comprehensive risk assessment and management
- **Port**: `8083`
- **Integration**: Uses MCP server for risk calculations
- **Capabilities**:
  - Portfolio risk scoring (1-10 scale)
  - Value-at-Risk (VaR) calculations
  - Stress testing scenarios
  - Diversification analysis
  - Correlation analysis
  - Hedging recommendations
- **Output**: Detailed risk assessment with volatility metrics and hedging suggestions

**3. Trading Analyst Agent (`sub_agents/trading_analyst/agent.py`)**
- **Purpose**: Trading strategy development and market analysis
- **Port**: `8082`
- **Integration**: Leverages MCP server for trading analysis
- **Capabilities**:
  - Trading strategy generation (Buy & Hold, Momentum, Mean Reversion, etc.)
  - Entry and exit point identification
  - Risk-reward ratio calculations
  - Position sizing recommendations
  - Multi-timeframe analysis (short, medium, long-term)

**4. Execution Analyst Agent (`sub_agents/execution_analyst/agent.py`)**
- **Purpose**: Trade execution optimization and portfolio management
- **Port**: `8081`
- **Integration**: Uses MCP server for execution analysis
- **Capabilities**:
  - Order type recommendations (Market, Limit, Stop-Loss, etc.)
  - Execution timing optimization
  - Transaction cost analysis
  - Broker recommendations
  - Market impact assessment

### Key Features

#### Agent-to-Agent Communication (A2A)
- **HTTP-based Protocol**: Each agent runs as an independent Flask server
- **RESTful Endpoints**: Standardized `/chat`, `/agent-card`, and `/health` endpoints
- **Proxy Architecture**: Main coordinator uses `A2AAgentProxy` for seamless communication
- **Async Support**: Built on ADK's async event system for non-blocking operations
- **Error Handling**: Comprehensive error handling and timeout management

#### Financial Analysis Pipeline
1. **Data Collection**: Data Analyst gathers market information via MCP server
2. **Risk Assessment**: Risk Analyst evaluates portfolio risks and exposures
3. **Strategy Development**: Trading Analyst develops investment strategies
4. **Execution Planning**: Execution Analyst optimizes trade implementation
5. **Coordination**: Financial Coordinator orchestrates the entire process

#### Structured Financial Advisory Process
Based on the system prompts, the workflow follows a methodical approach:

1. **User Introduction**: System presents capabilities and disclaimers
2. **Market Analysis**: User provides ticker symbol for analysis
3. **Strategy Development**: User specifies risk tolerance and investment horizon
4. **Execution Planning**: System develops optimal execution strategy
5. **Risk Evaluation**: Comprehensive risk assessment of the complete plan
6. **Markdown Output**: Results presented in structured markdown format

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
financial_advisor_management/
├── financial_advisor/
│   ├── agent.py              # Main coordinator with A2A proxy system
│   ├── prompt.py             # System prompts and workflow instructions
│   ├── simple-mcp-server/    # MCP server implementation
│   │   └── mcp_server.py     # Flask server with financial analysis tools
│   ├── sub_agents/           # Specialized financial agents
│   │   ├── data_analyst/     # Market data analysis (port 8080)
│   │   │   ├── agent.py      # A2A-enabled data analysis agent
│   │   │   └── prompt.py     # Data analyst instructions
│   │   ├── execution_analyst/ # Trade execution (port 8081)
│   │   │   ├── agent.py      # A2A-enabled execution agent
│   │   │   └── prompt.py     # Execution analyst instructions
│   │   ├── risk_analyst/     # Risk assessment (port 8083)
│   │   │   ├── agent.py      # A2A-enabled risk analysis agent
│   │   │   └── prompt.py     # Risk analyst instructions
│   │   └── trading_analyst/  # Trading strategies (port 8082)
│   │       ├── agent.py      # A2A-enabled trading agent
│   │       └── prompt.py     # Trading analyst instructions
│   └── tools/                # Shared utilities (currently empty)
├── pyproject.toml           # Poetry configuration with ADK dependencies
└── README.md               # This documentation
```

### Agent Communication Flow

1. **User Request**: Client interacts with financial coordinator via ADK web interface
2. **Agent Orchestration**: Coordinator determines which sub-agents to invoke
3. **A2A Communication**: HTTP POST requests sent to sub-agent `/chat` endpoints
4. **MCP Integration**: Sub-agents call MCP server for specialized financial analysis
5. **Response Assembly**: Results aggregated and formatted by coordinator
6. **Client Delivery**: Final analysis presented to user in markdown format

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

This architecture provides a robust, scalable, and maintainable foundation for comprehensive financial advisory services through specialized agent collaboration.
