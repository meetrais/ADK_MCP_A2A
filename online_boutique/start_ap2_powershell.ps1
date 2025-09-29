# PowerShell Script to Start AP2 Autonomous Commerce System
# Run this script to open multiple PowerShell terminals for each service

Write-Host "🚀 Starting AP2 Autonomous Commerce System" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🛍️ 6-Step A2A + AP2 Flow Implementation" -ForegroundColor Yellow
Write-Host "   1. User Request → Shopping Agent" -ForegroundColor White
Write-Host "   2. Shopping Agent → Merchant Agents (IntentMandate)" -ForegroundColor White
Write-Host "   3. Merchant Agent → Shopping Agent (CartMandate)" -ForegroundColor White
Write-Host "   4. Shopping Agent → Contact Collection" -ForegroundColor White
Write-Host "   5. Shopping Agent → Payment Processor (PaymentMandate)" -ForegroundColor White
Write-Host "   6. Payment Result → Shopping Agent → User" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "online_boutique_manager")) {
    Write-Host "❌ Please run this script from the online_boutique directory" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "`n🔧 Installing dependencies..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Failed to install dependencies. Please run: pip install -r requirements.txt" -ForegroundColor Yellow
}

Write-Host "`n🚀 Opening PowerShell terminals for each service..." -ForegroundColor Green

# Terminal 1: MCP Server (Port 8080)
Write-Host "Opening Terminal 1: MCP Server (Port 8080)" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; Write-Host '🏪 MCP Server (Port 8080)' -ForegroundColor Green; python online_boutique_manager/simple_mcp_server/boutique_mcp_server.py"

Start-Sleep -Seconds 2

# Terminal 2: Payment Processor Agent (Port 8092)  
Write-Host "Opening Terminal 2: Payment Processor Agent (Port 8092)" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; Write-Host '💳 Payment Processor Agent (Port 8092)' -ForegroundColor Green; python online_boutique_manager/sub_agents/payment_processor/agent.py"

Start-Sleep -Seconds 2

# Terminal 3: AP2 Shopping Agent (Port 8090)
Write-Host "Opening Terminal 3: AP2 Shopping Agent (Port 8090)" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; Write-Host '🛍️ AP2 Shopping Agent (Port 8090)' -ForegroundColor Green; python online_boutique_manager/shopping_agent.py"

Start-Sleep -Seconds 2

# Terminal 4: Catalog Service Agent (Port 8095) - Optional
Write-Host "Opening Terminal 4: Catalog Service Agent (Port 8095)" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; Write-Host '📦 Catalog Service Agent (Port 8095)' -ForegroundColor Green; python online_boutique_manager/sub_agents/catalog_service/agent.py"

Write-Host "`n⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "`n✅ All service terminals have been opened!" -ForegroundColor Green
Write-Host "`n📋 Service Information:" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🛍️ Shopping Agent (Main):     http://localhost:8090" -ForegroundColor White
Write-Host "💳 Payment Processor:         http://localhost:8092" -ForegroundColor White
Write-Host "🏪 MCP Server:               http://localhost:8080" -ForegroundColor White
Write-Host "📦 Catalog Service:          http://localhost:8095" -ForegroundColor White

Write-Host "`n🧪 Test Commands:" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "# Health check all services:" -ForegroundColor Yellow
Write-Host "Invoke-RestMethod -Uri 'http://localhost:8080/health'" -ForegroundColor White
Write-Host "Invoke-RestMethod -Uri 'http://localhost:8092/health'" -ForegroundColor White
Write-Host "Invoke-RestMethod -Uri 'http://localhost:8090/health'" -ForegroundColor White
Write-Host "Invoke-RestMethod -Uri 'http://localhost:8095/health'" -ForegroundColor White

Write-Host "`n# Test the complete AP2 flow:" -ForegroundColor Yellow
Write-Host '$response = Invoke-RestMethod -Uri "http://localhost:8090/chat" -Method POST -ContentType "application/json" -Body \'{"message": "I want to buy red shoes for $99"}\'' -ForegroundColor White
Write-Host '$response | ConvertTo-Json -Depth 10' -ForegroundColor White

Write-Host "`n# Run comprehensive tests:" -ForegroundColor Yellow
Write-Host "python test_complete_ap2_flow.py" -ForegroundColor White

Write-Host "`n📖 For detailed instructions, see: run_ap2_services.md" -ForegroundColor Green

# Offer to run tests
Write-Host "`n🤔 Would you like to run the test suite now? (y/N)" -ForegroundColor Yellow
$response = Read-Host

if ($response -eq "y" -or $response -eq "Y") {
    Write-Host "`n🧪 Running AP2 test suite..." -ForegroundColor Green
    Start-Sleep -Seconds 5  # Give services more time to start
    try {
        python test_complete_ap2_flow.py
    } catch {
        Write-Host "⚠️ Tests failed to run. Services may still be starting." -ForegroundColor Yellow
        Write-Host "Try running 'python test_complete_ap2_flow.py' manually in a few moments." -ForegroundColor White
    }
}

Write-Host "`n🎉 AP2 System startup complete!" -ForegroundColor Green
Write-Host "Check each terminal window to ensure services are running properly." -ForegroundColor White
Read-Host "`nPress Enter to exit this startup script"
