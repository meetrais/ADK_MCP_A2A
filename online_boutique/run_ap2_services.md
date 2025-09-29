# AP2 Autonomous Commerce System - Manual Startup Guide

## 🚀 Start Services in Separate PowerShell Terminals

You need to run each service in its own PowerShell terminal window. Here's the step-by-step process:

### PowerShell Terminal 1: MCP Server (Port 8080)
```powershell
cd C:\Code\ADK_MCP_A2A\online_boutique
python online_boutique_manager/simple_mcp_server/boutique_mcp_server.py
```

### PowerShell Terminal 2: Payment Processor Agent (Port 8092)
```powershell
cd C:\Code\ADK_MCP_A2A\online_boutique
python online_boutique_manager/sub_agents/payment_processor/agent.py
```

### PowerShell Terminal 3: AP2 Shopping Agent (Port 8090)
```powershell
cd C:\Code\ADK_MCP_A2A\online_boutique
python online_boutique_manager/shopping_agent.py
```

### PowerShell Terminal 4: Catalog Service Agent (Port 8095) - Optional
```powershell
cd C:\Code\ADK_MCP_A2A\online_boutique
python online_boutique_manager/sub_agents/catalog_service/agent.py
```

## ✅ Verify All Services Are Running

### PowerShell Terminal 5: Check Health Status
```powershell
cd C:\Code\ADK_MCP_A2A\online_boutique
python test_complete_ap2_flow.py
```

## 🧪 Test the Complete AP2 Flow

Once all services are running, test the autonomous commerce flow:

```powershell
# Test the AP2 flow with PowerShell
$response = Invoke-RestMethod -Uri "http://localhost:8090/chat" -Method POST -ContentType "application/json" -Body '{"message": "I want to buy red shoes for $99"}'
$response | ConvertTo-Json -Depth 10

# Alternative: Test with curl (if available)
curl -X POST http://localhost:8090/chat -H "Content-Type: application/json" -d '{"message": "I want to buy red shoes for $99"}'
```

## 📊 Expected Service Status

When all services are running, you should see:

| Service | Port | Status | Terminal |
|---------|------|--------|----------|
| MCP Server | 8080 | ✅ Running | Terminal 1 |
| Payment Processor | 8092 | ✅ Running | Terminal 2 |
| Shopping Agent | 8090 | ✅ Running | Terminal 3 |
| Catalog Service | 8095 | ✅ Running | Terminal 4 |

## 🔧 Troubleshooting

### If a service fails to start:
1. Check the error messages in the terminal
2. Ensure the port is not already in use
3. Verify dependencies are installed: `pip install -r requirements.txt`
4. Check that you're in the correct directory

### Common Issues:
- **Port already in use**: Kill the process using the port or use a different port
- **Import errors**: Make sure you're running from the `online_boutique` directory
- **Module not found**: Install requirements with `pip install -r requirements.txt`

## 🎯 Success Indicators

### 1. Each terminal should show:
- MCP Server: `🚀 Online Boutique MCP Server starting...`
- Payment Processor: `🚀 Payment Processor Agent starting on port 8092...`
- Shopping Agent: `🚀 AP2 Shopping Agent starting on port 8090...`
- Catalog Service: `🚀 Catalog Service Agent starting on port 8095...`

### 2. Health check should return:
```json
{
  "status": "healthy",
  "ap2_enabled": true,
  "supported_protocols": ["a2a", "ap2", "json-rpc-2.0"]
}
```

### 3. Complete flow test should show:
```
✅ AP2 Used: true
✅ Flow Completed: true
✅ Steps Completed: 6/6
```

## 🛍️ Test the 6-Step Flow

Once everything is running, the flow works as follows:

1. **User Request** → Shopping Agent (Port 8090)
2. **Shopping Agent** → Catalog Service (Port 8095) with IntentMandate
3. **Catalog Service** → Shopping Agent with CartMandate
4. **Shopping Agent** → Contact Collection
5. **Shopping Agent** → Payment Processor (Port 8092) with PaymentMandate
6. **Payment Result** → Shopping Agent → User

## 📝 Quick Commands Reference

```bash
# Check if all services are running
curl http://localhost:8080/health  # MCP Server
curl http://localhost:8092/health  # Payment Processor
curl http://localhost:8090/health  # Shopping Agent
curl http://localhost:8095/health  # Catalog Service

# Test the complete AP2 autonomous commerce flow
curl -X POST http://localhost:8090/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to buy red shoes for $99"}'

# Check active shopping sessions
curl http://localhost:8090/sessions

# Run comprehensive tests
python test_complete_ap2_flow.py
