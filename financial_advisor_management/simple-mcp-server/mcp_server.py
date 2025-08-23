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
