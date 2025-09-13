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

The Financial Advisor Management System is built on a multi-agent architecture where specialized agents collaborate through both the MCP protocol and an enhanced Agent-to-Agent (A2A) protocol implementing JSON-RPC 2.0 standards to provide comprehensive financial advisory services.

<img width="1211" height="653" alt="image" src="https://github.com/user-attachments/assets/9e885142-19bc-4253-8672-3d8b8e9921cc" />


#### Core Components

**1. Main Financial Advisor Agent (`financial_advisor/agent.py`)**
- **Role**: Central orchestrator coordinating between specialized sub-agents
- **Framework**: Built on Google ADK using Gemini 2.5 Flash model
- **Communication**: Uses enhanced `EnhancedA2AAgentProxy` with JSON-RPC 2.0 protocol support and fallback to legacy HTTP
- **Architecture**: Features comprehensive A2A Agent Manager with protocol statistics, health monitoring, and task management
- **Protocol Features**: JSON-RPC 2.0 requests, agent discovery via `/.well-known/agent.json`, streaming support via SSE
- **Management Tools**: `create_agent_task`, `get_task_status_info`, and real-time health monitoring
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
- **Framework**: Enhanced A2A Server with full JSON-RPC 2.0 protocol support
- **Integration**: Communicates with MCP server for market data
- **Capabilities**: 8 specialized capabilities including:
  - Market data analysis and trend identification
  - Technical indicator calculations (RSI, MACD, Bollinger Bands)
  - Volume analysis and liquidity assessment
  - Sector rotation and correlation analysis
  - Earnings and fundamental data integration
  - Real-time data streaming and alerts
- **Protocol Features**: Agent card publishing, JSON-RPC 2.0 methods, task management, artifact generation
- **Communication**: Full A2A protocol with `/.well-known/agent.json`, `/chat`, `/health`, streaming via SSE

**2. Risk Analyst Agent (`sub_agents/risk_analyst/agent.py`)**
- **Purpose**: Comprehensive risk assessment and management
- **Port**: `8083`
- **Framework**: Enhanced A2A Server with full JSON-RPC 2.0 protocol support
- **Integration**: Uses MCP server for risk calculations
- **Capabilities**: 8 specialized capabilities including:
  - Portfolio risk scoring and VaR calculations
  - Stress testing and scenario analysis
  - Diversification and correlation analysis
  - Risk-adjusted return optimization
  - Hedging strategy development
  - Regulatory compliance monitoring
- **Protocol Features**: Agent card publishing, JSON-RPC 2.0 methods, task management, artifact generation
- **Output**: Structured risk assessment artifacts with comprehensive markdown reports

**3. Trading Analyst Agent (`sub_agents/trading_analyst/agent.py`)**
- **Purpose**: Trading strategy development and market analysis
- **Port**: `8082`
- **Framework**: Enhanced A2A Server with full JSON-RPC 2.0 protocol support
- **Integration**: Leverages MCP server for trading analysis
- **Capabilities**: 9 specialized capabilities including:
  - Advanced trading strategy development (Buy & Hold, Momentum, Mean Reversion, etc.)
  - Multi-timeframe technical analysis and signal generation
  - Risk-reward optimization and position sizing
  - Algorithmic trading strategy backtesting
  - Market regime detection and strategy adaptation
  - Options and derivatives strategy development
- **Protocol Features**: Agent card publishing, JSON-RPC 2.0 methods, task management, artifact generation
- **Output**: Comprehensive trading strategy artifacts and risk management plans

**4. Execution Analyst Agent (`sub_agents/execution_analyst/agent.py`)**
- **Purpose**: Trade execution optimization and portfolio management
- **Port**: `8081`
- **Framework**: Enhanced A2A Server with full JSON-RPC 2.0 protocol support
- **Integration**: Uses MCP server for execution analysis
- **Capabilities**: 9 specialized capabilities including:
  - Advanced order execution strategies and timing optimization
  - Transaction cost analysis and market impact assessment
  - Smart order routing and venue selection
  - Portfolio rebalancing and optimization
  - Execution performance measurement and analytics
  - Regulatory compliance and best execution monitoring
- **Protocol Features**: Agent card publishing, JSON-RPC 2.0 methods, task management, artifact generation
- **Output**: Detailed execution strategies and comprehensive cost analysis artifacts

### Key Features

#### Enhanced Agent-to-Agent Communication (A2A)
- **JSON-RPC 2.0 Protocol**: Full implementation of JSON-RPC 2.0 specification for standardized messaging
- **Agent Discovery**: Automatic agent discovery via `/.well-known/agent.json` endpoint with comprehensive agent cards
- **Task Management**: Complete task lifecycle management with states (submitted, working, input-required, completed, failed, cancelled)
- **Message Structure**: Support for multiple message part types (TextPart, FilePart, DataPart) with rich content handling
- **Artifacts**: Tangible output generation with metadata, versioning, and structured data formats
- **Streaming Support**: Real-time updates via Server-Sent Events (SSE) for long-running tasks
- **Protocol Auto-Detection**: Enhanced proxy with automatic protocol detection and fallback to legacy HTTP
- **Health Monitoring**: Comprehensive health checks with protocol statistics and performance metrics
- **Standards-Based**: Built on HTTP, JSON-RPC 2.0, and SSE standards for maximum compatibility

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
│   ├── agent.py              # Main coordinator with enhanced A2A proxy system
│   ├── a2a_protocol.py       # Complete A2A protocol implementation with JSON-RPC 2.0
│   ├── prompt.py             # System prompts and workflow instructions
│   ├── simple-mcp-server/    # MCP server implementation
│   │   └── mcp_server.py     # Flask server with financial analysis tools
│   ├── sub_agents/           # Specialized financial agents
│   │   ├── data_analyst/     # Market data analysis (port 8080)
│   │   │   ├── agent.py      # Enhanced A2A server with JSON-RPC 2.0 support
│   │   │   └── prompt.py     # Data analyst instructions
│   │   ├── execution_analyst/ # Trade execution (port 8081)
│   │   │   ├── agent.py      # Enhanced A2A server with JSON-RPC 2.0 support
│   │   │   └── prompt.py     # Execution analyst instructions
│   │   ├── risk_analyst/     # Risk assessment (port 8083)
│   │   │   ├── agent.py      # Enhanced A2A server with JSON-RPC 2.0 support
│   │   │   └── prompt.py     # Risk analyst instructions
│   │   └── trading_analyst/  # Trading strategies (port 8082)
│   │       ├── agent.py      # Enhanced A2A server with JSON-RPC 2.0 support
│   │       └── prompt.py     # Trading analyst instructions
│   └── tools/                # Shared utilities (currently empty)
├── pyproject.toml           # Poetry configuration with ADK dependencies
└── README.md               # This documentation
```

### Enhanced Agent Communication Flow

1. **User Request**: Client interacts with financial coordinator via ADK web interface
2. **Agent Discovery**: Coordinator discovers available agents via `/.well-known/agent.json` endpoints
3. **Protocol Detection**: Enhanced proxy automatically detects JSON-RPC 2.0 support with fallback to legacy HTTP
4. **Task Creation**: Coordinator creates structured A2A tasks with unique IDs and lifecycle management
5. **JSON-RPC Communication**: Standardized JSON-RPC 2.0 requests sent with method identification and structured parameters
6. **Agent Processing**: Sub-agents process requests using their specialized capabilities and generate artifacts
7. **MCP Integration**: Sub-agents call MCP server for specialized financial analysis and data
8. **Streaming Updates**: Real-time task progress updates via Server-Sent Events (SSE) for long-running operations
9. **Artifact Generation**: Agents create structured output artifacts with metadata and versioning
10. **Response Assembly**: Results aggregated with comprehensive error handling and protocol statistics
11. **Client Delivery**: Final analysis presented to user in structured markdown format with embedded artifacts

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
