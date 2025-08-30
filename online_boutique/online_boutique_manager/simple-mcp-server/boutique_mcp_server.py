from flask import Flask, request, jsonify
import random
from datetime import datetime, timedelta

app = Flask(__name__)

# Sample product data
SAMPLE_PRODUCTS = {
    'clothing': [
        {
            'id': 'CL001',
            'name': 'Elegant Silk Blouse',
            'price': 89.99,
            'description': 'Beautiful silk blouse perfect for office or evening wear',
            'sizes': ['XS', 'S', 'M', 'L', 'XL'],
            'colors': ['Ivory', 'Black', 'Navy'],
            'stock': random.randint(5, 25),
            'category': 'clothing'
        },
        {
            'id': 'CL002',
            'name': 'Designer Cocktail Dress',
            'price': 159.99,
            'description': 'Stunning cocktail dress for special occasions',
            'sizes': ['XS', 'S', 'M', 'L', 'XL'],
            'colors': ['Black', 'Burgundy', 'Emerald'],
            'stock': random.randint(3, 15),
            'category': 'clothing'
        },
        {
            'id': 'CL003',
            'name': 'Cashmere Sweater',
            'price': 129.99,
            'description': 'Luxurious cashmere sweater for ultimate comfort',
            'sizes': ['S', 'M', 'L', 'XL'],
            'colors': ['Cream', 'Grey', 'Camel'],
            'stock': random.randint(8, 20),
            'category': 'clothing'
        }
    ],
    'accessories': [
        {
            'id': 'AC001',
            'name': 'Leather Handbag',
            'price': 199.99,
            'description': 'Premium leather handbag with gold hardware',
            'colors': ['Black', 'Brown', 'Tan'],
            'stock': random.randint(5, 15),
            'category': 'accessories'
        },
        {
            'id': 'AC002',
            'name': 'Pearl Earrings',
            'price': 79.99,
            'description': 'Classic pearl drop earrings',
            'colors': ['White Pearl', 'Grey Pearl'],
            'stock': random.randint(10, 30),
            'category': 'accessories'
        }
    ],
    'shoes': [
        {
            'id': 'SH001',
            'name': 'Italian Leather Pumps',
            'price': 149.99,
            'description': 'Elegant Italian leather pumps with 3-inch heel',
            'sizes': ['6', '6.5', '7', '7.5', '8', '8.5', '9', '9.5', '10'],
            'colors': ['Black', 'Nude', 'Red'],
            'stock': random.randint(5, 20),
            'category': 'shoes'
        }
    ]
}

def get_dummy_products(category):
    """Generate product catalog for specified category"""
    if category.lower() == 'all':
        products = []
        for cat_products in SAMPLE_PRODUCTS.values():
            products.extend(cat_products)
        return products
    
    return SAMPLE_PRODUCTS.get(category.lower(), [])

def get_dummy_customer_support(inquiry):
    """Generate customer support response"""
    inquiry_lower = inquiry.lower()
    
    if 'return' in inquiry_lower or 'refund' in inquiry_lower:
        return {
            'response': 'Our return policy allows returns within 30 days of purchase. Items must be in original condition with tags attached.',
            'policy_details': {
                'return_window': '30 days',
                'condition_required': 'Original condition with tags',
                'refund_processing': '5-7 business days',
                'return_shipping': 'Free return shipping provided'
            },
            'next_steps': 'To initiate a return, please provide your order number and reason for return.'
        }
    
    elif 'shipping' in inquiry_lower or 'delivery' in inquiry_lower:
        return {
            'response': 'We offer multiple shipping options including standard (5-7 days) and express (2-3 days) delivery.',
            'shipping_options': {
                'standard': {'time': '5-7 business days', 'cost': 'Free over $75'},
                'express': {'time': '2-3 business days', 'cost': '$12.99'},
                'overnight': {'time': '1 business day', 'cost': '$24.99'}
            },
            'tracking': 'Tracking information will be provided once your order ships.'
        }
    
    elif 'size' in inquiry_lower or 'sizing' in inquiry_lower:
        return {
            'response': 'We provide detailed size charts for all our products. For personalized sizing assistance, please provide your measurements.',
            'size_guide': {
                'clothing': 'XS (0-2), S (4-6), M (8-10), L (12-14), XL (16-18)',
                'shoes': 'US standard sizing with half sizes available',
                'fit_guarantee': 'Free exchanges for size issues within 30 days'
            }
        }
    
    else:
        return {
            'response': 'Thank you for contacting us! Our customer service team is here to help with any questions about our products, orders, or policies.',
            'available_help': [
                'Product information and recommendations',
                'Order status and tracking',
                'Returns and exchanges',
                'Sizing assistance',
                'Payment and billing questions'
            ],
            'contact_hours': 'Monday-Friday 9AM-6PM EST, Saturday 10AM-4PM EST'
        }

def get_dummy_payment_processing(cart_data):
    """Generate payment processing response"""
    total_amount = sum(item.get('price', 0) * item.get('quantity', 1) for item in cart_data.get('items', []))
    
    return {
        'order_id': f'OB{random.randint(10000, 99999)}',
        'total_amount': round(total_amount, 2),
        'payment_status': 'processed',
        'transaction_id': f'TXN{random.randint(100000, 999999)}',
        'payment_method': cart_data.get('payment_method', 'Credit Card'),
        'billing_address': cart_data.get('billing_address', 'Demo Address'),
        'confirmation': {
            'email_sent': True,
            'receipt_number': f'RCP{random.randint(100000, 999999)}',
            'estimated_shipping': (datetime.now() + timedelta(days=random.randint(5, 7))).strftime('%Y-%m-%d')
        }
    }

def get_dummy_shipping_info(order_data):
    """Generate shipping coordination response"""
    shipping_date = datetime.now() + timedelta(days=1)
    delivery_date = shipping_date + timedelta(days=random.randint(3, 7))
    
    return {
        'tracking_number': f'TRK{random.randint(1000000000, 9999999999)}',
        'shipping_method': order_data.get('shipping_method', 'Standard Shipping'),
        'estimated_delivery': delivery_date.strftime('%Y-%m-%d'),
        'shipping_address': order_data.get('shipping_address', 'Demo Shipping Address'),
        'shipping_status': 'preparing_for_shipment',
        'carrier': random.choice(['UPS', 'FedEx', 'USPS']),
        'shipping_cost': order_data.get('shipping_cost', 0.00),
        'delivery_instructions': order_data.get('delivery_instructions', 'Leave at door if no answer')
    }

def get_dummy_marketing_recommendations(customer_data):
    """Generate marketing and recommendations response"""
    return {
        'personalized_recommendations': [
            {
                'product_id': 'CL004',
                'name': 'Recommended Scarf',
                'price': 45.99,
                'reason': 'Complements your recent purchases'
            },
            {
                'product_id': 'AC003',
                'name': 'Matching Belt',
                'price': 65.99,
                'reason': 'Perfect for your style preferences'
            }
        ],
        'current_promotions': [
            {
                'type': 'discount',
                'description': '20% off accessories',
                'code': 'ACC20',
                'expires': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            },
            {
                'type': 'free_shipping',
                'description': 'Free shipping on orders over $75',
                'min_amount': 75.00
            }
        ],
        'loyalty_program': {
            'points_available': random.randint(50, 500),
            'tier': random.choice(['Silver', 'Gold', 'Platinum']),
            'next_reward': '$10 off at 100 points'
        }
    }

def get_dummy_catalog_service(query):
    """Generate catalog service response"""
    query_lower = query.lower()
    
    if 'search' in query_lower:
        return {
            'search_results': [
                {
                    'product_id': 'CL001',
                    'name': 'Elegant Silk Blouse',
                    'price': 89.99,
                    'match_score': 0.95,
                    'category': 'clothing'
                },
                {
                    'product_id': 'AC001',
                    'name': 'Leather Handbag',
                    'price': 199.99,
                    'match_score': 0.87,
                    'category': 'accessories'
                }
            ],
            'total_results': 2,
            'search_suggestions': ['silk shirts', 'leather bags', 'designer clothing'],
            'filters_applied': [],
            'search_time_ms': random.randint(50, 200)
        }
    
    elif 'categories' in query_lower:
        return {
            'categories': [
                {
                    'name': 'Clothing',
                    'id': 'clothing',
                    'product_count': 15,
                    'subcategories': ['Blouses', 'Dresses', 'Sweaters', 'Pants']
                },
                {
                    'name': 'Accessories',
                    'id': 'accessories',
                    'product_count': 8,
                    'subcategories': ['Handbags', 'Jewelry', 'Scarves', 'Belts']
                },
                {
                    'name': 'Shoes',
                    'id': 'shoes',
                    'product_count': 6,
                    'subcategories': ['Heels', 'Flats', 'Boots', 'Sneakers']
                }
            ],
            'featured_categories': ['New Arrivals', 'Sale Items', 'Best Sellers']
        }
    
    elif 'featured' in query_lower:
        return {
            'featured_products': [
                {
                    'product_id': 'CL002',
                    'name': 'Designer Cocktail Dress',
                    'price': 159.99,
                    'featured_reason': 'Best Seller',
                    'discount': '15% off'
                },
                {
                    'product_id': 'SH001',
                    'name': 'Italian Leather Pumps',
                    'price': 149.99,
                    'featured_reason': 'New Arrival',
                    'rating': 4.8
                }
            ],
            'collections': [
                {
                    'name': 'Spring Collection',
                    'products_count': 12,
                    'theme': 'Fresh and vibrant pieces for spring'
                },
                {
                    'name': 'Evening Wear',
                    'products_count': 8,
                    'theme': 'Elegant pieces for special occasions'
                }
            ]
        }
    
    else:
        return {
            'catalog_overview': {
                'total_products': 29,
                'categories': 3,
                'new_arrivals': 5,
                'on_sale': 7
            },
            'popular_searches': ['silk blouses', 'leather handbags', 'cocktail dresses'],
            'trending_categories': ['Clothing', 'Accessories'],
            'catalog_features': [
                'Advanced search with filters',
                'Category-based browsing',
                'Featured product collections',
                'Related product suggestions'
            ]
        }

@app.route('/products', methods=['POST'])
def get_products():
    """MCP endpoint for product catalog"""
    print(f"MCP Server: Received products request")  # Debug log
    
    data = request.get_json()
    print(f"MCP Server: Request data: {data}")  # Debug log
    
    if not data or 'category' not in data:
        print("MCP Server: Error - No category provided")  # Debug log
        return jsonify({
            'status': 'error',
            'message': 'Product category is required'
        }), 400
    
    category = data['category']
    print(f"MCP Server: Getting products for category: {category}")  # Debug log
    
    products = get_dummy_products(category)
    print(f"MCP Server: Generated products: {len(products)} items")  # Debug log
    
    response = {
        'status': 'success',
        'data': {
            'category': category,
            'products': products,
            'total_count': len(products)
        }
    }
    
    print(f"MCP Server: Sending products response")  # Debug log
    return jsonify(response)

@app.route('/customer-support', methods=['POST'])
def customer_support():
    """MCP endpoint for customer support"""
    print(f"MCP Server: Received customer support request")  # Debug log
    
    data = request.get_json()
    print(f"MCP Server: Request data: {data}")  # Debug log
    
    if not data or 'inquiry' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Customer inquiry is required'
        }), 400
    
    inquiry = data['inquiry']
    support_response = get_dummy_customer_support(inquiry)
    
    response = {
        'status': 'success',
        'data': support_response
    }
    
    return jsonify(response)

@app.route('/payment-process', methods=['POST'])
def payment_process():
    """MCP endpoint for payment processing"""
    print(f"MCP Server: Received payment processing request")  # Debug log
    
    data = request.get_json()
    
    if not data or 'cart_data' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Cart data is required'
        }), 400
    
    cart_data = data['cart_data']
    payment_response = get_dummy_payment_processing(cart_data)
    
    response = {
        'status': 'success',
        'data': payment_response
    }
    
    return jsonify(response)

@app.route('/shipping-coordinate', methods=['POST'])
def shipping_coordinate():
    """MCP endpoint for shipping coordination"""
    print(f"MCP Server: Received shipping coordination request")  # Debug log
    
    data = request.get_json()
    
    if not data or 'order_data' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Order data is required'
        }), 400
    
    order_data = data['order_data']
    shipping_response = get_dummy_shipping_info(order_data)
    
    response = {
        'status': 'success',
        'data': shipping_response
    }
    
    return jsonify(response)

@app.route('/marketing-recommendations', methods=['POST'])
def marketing_recommendations():
    """MCP endpoint for marketing recommendations"""
    print(f"MCP Server: Received marketing recommendations request")  # Debug log
    
    data = request.get_json()
    
    if not data or 'customer_data' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Customer data is required'
        }), 400
    
    customer_data = data['customer_data']
    marketing_response = get_dummy_marketing_recommendations(customer_data)
    
    response = {
        'status': 'success',
        'data': marketing_response
    }
    
    return jsonify(response)

@app.route('/catalog-service', methods=['POST'])
def catalog_service():
    """MCP endpoint for catalog service"""
    print(f"MCP Server: Received catalog service request")  # Debug log
    
    data = request.get_json()
    print(f"MCP Server: Request data: {data}")  # Debug log
    
    if not data or 'query' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Catalog query is required'
        }), 400
    
    query = data['query']
    catalog_response = get_dummy_catalog_service(query)
    
    response = {
        'status': 'success',
        'data': catalog_response
    }
    
    return jsonify(response)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with API info"""
    return jsonify({
        'message': 'Online Boutique MCP Server',
        'version': '1.0.0',
        'endpoints': {
            'products': 'POST /products',
            'customer-support': 'POST /customer-support',
            'payment-process': 'POST /payment-process',
            'shipping-coordinate': 'POST /shipping-coordinate',
            'marketing-recommendations': 'POST /marketing-recommendations',
            'health': 'GET /health'
        },
        'example_requests': {
            'products': {'category': 'clothing'},
            'customer-support': {'inquiry': 'return policy'},
            'payment-process': {'cart_data': {'items': [], 'payment_method': 'Credit Card'}},
            'shipping-coordinate': {'order_data': {'order_id': 'OB12345'}},
            'marketing-recommendations': {'customer_data': {'preferences': 'clothing'}}
        }
    })

if __name__ == '__main__':
    print("🚀 Online Boutique MCP Server starting...")
    print("🛍️ Ready to provide e-commerce services!")
    print("🔍 Test with: curl -X POST http://localhost:3002/products -H \"Content-Type: application/json\" -d '{\"category\":\"clothing\"}'")
    
    app.run(host='localhost', port=3002, debug=False)
