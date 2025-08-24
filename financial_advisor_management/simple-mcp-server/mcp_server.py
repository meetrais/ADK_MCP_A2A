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

def get_dummy_trading_analysis(market_data):
    """Generate dummy trading analysis for market data"""
    strategies = random.choice([
        ['Buy and Hold', 'Dollar Cost Averaging'],
        ['Momentum Trading', 'Mean Reversion'],
        ['Swing Trading', 'Day Trading'],
        ['Options Strategy', 'Pairs Trading']
    ])
    
    return {
        'trading_strategies': strategies,
        'entry_points': f'Recommended entry: {"Above resistance at current level" if random.random() > 0.5 else "On pullback to support"}. '
                       f'Technical signal: {"RSI oversold" if random.random() > 0.5 else "Moving average crossover"}.',
        'exit_points': f'Exit strategy: {"Take profit at {round(random.uniform(5, 15), 1)}% gain" if random.random() > 0.5 else f"Stop loss at {round(random.uniform(3, 8), 1)}% loss"}. '
                      f'Trailing stop recommended: {"Yes" if random.random() > 0.5 else "No"}.',
        'risk_management': {
            'max_position_size': f'{random.randint(2, 10)}%',
            'stop_loss_percentage': round(random.uniform(3, 8), 1),
            'risk_reward_ratio': f'1:{random.randint(2, 5)}'
        },
        'position_sizing': f'Recommended position: {"Conservative 2-3% of portfolio" if random.random() > 0.5 else "Moderate 4-6% of portfolio"}. '
                          f'Consider {"scaling in gradually" if random.random() > 0.5 else "single entry point"}.',
        'timeframe_analysis': {
            'short_term': random.choice(['Bullish', 'Bearish', 'Neutral']),
            'medium_term': random.choice(['Bullish', 'Bearish', 'Neutral']),
            'long_term': random.choice(['Bullish', 'Bearish', 'Neutral'])
        }
    }

def get_dummy_risk_analysis(portfolio_data):
    """Generate dummy risk analysis for portfolio data"""
    risk_factors = random.choice([
        ['Market Risk', 'Credit Risk', 'Liquidity Risk'],
        ['Concentration Risk', 'Currency Risk', 'Interest Rate Risk'],
        ['Operational Risk', 'Regulatory Risk', 'Inflation Risk']
    ])
    
    return {
        'overall_risk_score': round(random.uniform(1, 10), 1),
        'risk_level': random.choice(['LOW', 'MODERATE', 'HIGH', 'VERY_HIGH']),
        'risk_factors': risk_factors,
        'portfolio_volatility': round(random.uniform(10, 35), 2),
        'value_at_risk': {
            '1_day_5_percent': round(random.uniform(1000, 10000), 2),
            '1_week_5_percent': round(random.uniform(5000, 30000), 2),
            '1_month_5_percent': round(random.uniform(15000, 80000), 2)
        },
        'diversification_score': round(random.uniform(0.3, 0.9), 2),
        'risk_recommendations': f'Portfolio shows {"moderate" if random.random() > 0.5 else "high"} concentration risk. '
                               f'Consider {"increasing diversification" if random.random() > 0.5 else "reducing position sizes"}. '
                               f'{"Hedge against market downturns" if random.random() > 0.5 else "Monitor correlation between assets"}.',
        'stress_test_results': {
            'market_crash_scenario': f'{round(random.uniform(-15, -35), 1)}%',
            'interest_rate_spike': f'{round(random.uniform(-5, -15), 1)}%',
            'sector_rotation': f'{round(random.uniform(-8, 8), 1)}%'
        },
        'hedging_suggestions': random.choice([
            'Consider VIX calls for downside protection',
            'Add defensive sectors (utilities, consumer staples)',
            'Implement put spread strategies',
            'Increase cash allocation during volatile periods'
        ]),
        'correlation_analysis': {
            'intra_portfolio_correlation': round(random.uniform(0.2, 0.8), 2),
            'market_beta': round(random.uniform(0.7, 1.3), 2),
            'sector_concentration': f'{random.randint(15, 45)}% in top sector'
        }
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

@app.route('/trading-analyze', methods=['POST'])
def trading_analyze():
    """MCP endpoint for trading analysis"""
    print(f"MCP Server: Received trading analysis request")  # Debug log
    
    data = request.get_json()
    print(f"MCP Server: Request data: {data}")  # Debug log
    
    if not data or 'market_data' not in data:
        print("MCP Server: Error - No market data provided")  # Debug log
        return jsonify({
            'status': 'error',
            'message': 'Market data is required'
        }), 400
    
    market_data = data['market_data']
    print(f"MCP Server: Analyzing market data: {market_data}")  # Debug log
    
    analysis = get_dummy_trading_analysis(market_data)
    print(f"MCP Server: Generated trading analysis: {analysis}")  # Debug log
    
    response = {
        'status': 'success',
        'data': analysis
    }
    
    print(f"MCP Server: Sending trading response: {response}")  # Debug log
    return jsonify(response)

@app.route('/risk-analyze', methods=['POST'])
def risk_analyze():
    """MCP endpoint for risk analysis"""
    print(f"MCP Server: Received risk analysis request")  # Debug log
    
    data = request.get_json()
    print(f"MCP Server: Request data: {data}")  # Debug log
    
    if not data or 'portfolio_data' not in data:
        print("MCP Server: Error - No portfolio data provided")  # Debug log
        return jsonify({
            'status': 'error',
            'message': 'Portfolio data is required'
        }), 400
    
    portfolio_data = data['portfolio_data']
    print(f"MCP Server: Analyzing portfolio data: {portfolio_data}")  # Debug log
    
    analysis = get_dummy_risk_analysis(portfolio_data)
    print(f"MCP Server: Generated risk analysis: {analysis}")  # Debug log
    
    response = {
        'status': 'success',
        'data': analysis
    }
    
    print(f"MCP Server: Sending risk response: {response}")  # Debug log
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
