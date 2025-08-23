from flask import Flask, request, jsonify
import random

app = Flask(__name__)

def get_dummy_analysis(ticker):
    """Generate dummy financial analysis for any ticker"""
    price = round(random.uniform(50, 250), 2)
    change = round(random.uniform(-10, 10), 2)
    change_percent = round((change / price) * 100, 2)
    
    return {
        'ticker': ticker.upper(),
        'price': price,
        'change': change,
        'change_percent': change_percent,
        'volume': random.randint(1000000, 50000000),
        'market_cap': random.randint(100, 500) * 1_000_000_000,
        'analysis': f'{ticker.upper()} is currently trading at ${price}. '
                   f'The stock has {"gained" if change >= 0 else "lost"} ${abs(change)} '
                   f'({abs(change_percent)}%) today. Trading volume is moderate. '
                   f'Technical indicators suggest a {"bullish" if random.random() > 0.5 else "bearish"} trend.',
        'recommendation': random.choice(['BUY', 'HOLD', 'SELL']),
        'risk_level': random.choice(['LOW', 'MEDIUM', 'HIGH'])
    }

def get_dummy_execution_analysis(strategy_data):
    """Generate dummy execution analysis for trading strategies"""
    order_types = random.choice([
        ['Market Orders', 'Limit Orders'], 
        ['Stop-Loss Orders', 'Take-Profit Orders'],
        ['Bracket Orders', 'Iceberg Orders']
    ])
    
    return {
        'execution_strategy': f'Recommended execution strategy based on provided trading strategy. '
                            f'Analysis suggests using {"gradual accumulation" if random.random() > 0.5 else "swift execution"} approach.',
        'order_types': order_types,
        'timing_recommendations': f'Best execution times: {"Market open (9:30-10:30 AM)" if random.random() > 0.5 else "Mid-day (11:00 AM - 2:00 PM)"}. '
                                f'Avoid {"end of day" if random.random() > 0.5 else "lunch hour"} trading.',
        'cost_analysis': {
            'estimated_commission': round(random.uniform(5, 25), 2),
            'spread_cost': round(random.uniform(0.1, 0.5), 2),
            'market_impact': random.choice(['LOW', 'MEDIUM', 'HIGH'])
        },
        'risk_considerations': f'Key risks: {"Slippage during volatile periods" if random.random() > 0.5 else "Liquidity constraints"}. '
                             f'Recommended position sizing: {"Small to medium" if random.random() > 0.5 else "Medium to large"}.',
        'broker_recommendations': random.choice([
            'Interactive Brokers - Low fees, advanced tools',
            'TD Ameritrade - User-friendly, good research',
            'E*TRADE - Balanced platform, decent fees'
        ])
    }

@app.route('/analyze', methods=['POST'])
def analyze():
    """MCP endpoint for financial analysis"""
    print(f"MCP Server: Received request")  # Debug log
    
    data = request.get_json()
    print(f"MCP Server: Request data: {data}")  # Debug log
    
    if not data or 'ticker' not in data:
        print("MCP Server: Error - No ticker provided")  # Debug log
        return jsonify({
            'status': 'error',
            'message': 'Ticker symbol is required'
        }), 400
    
    ticker = data['ticker']
    print(f"MCP Server: Analyzing ticker: {ticker}")  # Debug log
    
    analysis = get_dummy_analysis(ticker)
    print(f"MCP Server: Generated analysis: {analysis}")  # Debug log
    
    response = {
        'status': 'success',
        'data': analysis
    }
    
    print(f"MCP Server: Sending response: {response}")  # Debug log
    return jsonify(response)

@app.route('/execution-analyze', methods=['POST'])
def execution_analyze():
    """MCP endpoint for execution analysis"""
    print(f"MCP Server: Received execution analysis request")  # Debug log
    
    data = request.get_json()
    print(f"MCP Server: Request data: {data}")  # Debug log
    
    if not data or 'strategy_data' not in data:
        print("MCP Server: Error - No strategy data provided")  # Debug log
        return jsonify({
            'status': 'error',
            'message': 'Strategy data is required'
        }), 400
    
    strategy_data = data['strategy_data']
    print(f"MCP Server: Analyzing strategy: {strategy_data}")  # Debug log
    
    analysis = get_dummy_execution_analysis(strategy_data)
    print(f"MCP Server: Generated execution analysis: {analysis}")  # Debug log
    
    response = {
        'status': 'success',
        'data': analysis
    }
    
    print(f"MCP Server: Sending execution response: {response}")  # Debug log
    return jsonify(response)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with API info"""
    return jsonify({
        'message': 'Simple Python MCP Server for Financial Analysis',
        'version': '1.0.0',
        'endpoints': {
            'analyze': 'POST /analyze',
            'health': 'GET /health'
        },
        'example_request': {
            'ticker': 'MSFT'
        }
    })

if __name__ == '__main__':
    print("🚀 Simple Python MCP Server starting...")
    print("📊 Ready to provide dummy financial analysis!")
    print("🔍 Test with: curl -X POST http://localhost:3001/analyze -H \"Content-Type: application/json\" -d '{\"ticker\":\"MSFT\"}'")
    
    app.run(host='localhost', port=3001, debug=False)
