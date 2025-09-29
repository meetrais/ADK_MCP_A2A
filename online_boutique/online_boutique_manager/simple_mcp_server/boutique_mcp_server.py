# C:\Code\ADK_MCP_A2A\online_boutique\online_boutique_manager\simple_mcp_server\boutique_mcp_server.py

# --- MODIFICATIONS START ---
# Import the 'os' module to read environment variables
import os
# --- MODIFICATIONS END ---

from flask import Flask, request, jsonify
import random
import uuid
import hashlib
import hmac
import requests
from datetime import datetime, timedelta
from decimal import Decimal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Payment gateway configuration
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', '')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', '')
PAYMENT_WEBHOOK_SECRET = os.environ.get('PAYMENT_WEBHOOK_SECRET', 'default_webhook_secret')

# Real payment processing capabilities
try:
    import stripe
    # More robust check: ensure key exists, is not empty, and is not just whitespace
    STRIPE_AVAILABLE = bool(STRIPE_SECRET_KEY and STRIPE_SECRET_KEY.strip())
    
    if STRIPE_AVAILABLE:
        # Check for placeholder values
        if STRIPE_SECRET_KEY in ['sk_test_your_stripe_secret_key_here', 'your_stripe_secret_key_here']:
            logger.info("Stripe integration: ❌ Not configured (placeholder key detected)")
            logger.info("   Replace 'sk_test_your_stripe_secret_key_here' with your actual Stripe key")
            STRIPE_AVAILABLE = False
        # Validate the key format (Stripe keys start with sk_ for secret keys)
        elif not STRIPE_SECRET_KEY.startswith(('sk_test_', 'sk_live_')):
            logger.warning("Stripe secret key format appears invalid - should start with 'sk_test_' or 'sk_live_'")
            STRIPE_AVAILABLE = False
        else:
            stripe.api_key = STRIPE_SECRET_KEY
            logger.info("Stripe integration: ✅ Available")
    else:
        logger.info("Stripe integration: ❌ Not configured (no key provided)")
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("Stripe not available - install with: pip install stripe")

try:
    import paypalrestsdk
    # More robust check for both PayPal credentials
    PAYPAL_AVAILABLE = bool(
        PAYPAL_CLIENT_ID and PAYPAL_CLIENT_ID.strip() and
        PAYPAL_CLIENT_SECRET and PAYPAL_CLIENT_SECRET.strip()
    )
    
    if PAYPAL_AVAILABLE:
        # Check for placeholder values
        if (PAYPAL_CLIENT_ID in ['your_paypal_client_id_here'] or 
            PAYPAL_CLIENT_SECRET in ['your_paypal_client_secret_here']):
            logger.info("PayPal integration: ❌ Not configured (placeholder credentials detected)")
            logger.info("   Replace placeholder values with your actual PayPal credentials")
            PAYPAL_AVAILABLE = False
        else:
            paypalrestsdk.configure({
                "mode": os.environ.get('PAYPAL_MODE', 'sandbox'),  # sandbox or live
                "client_id": PAYPAL_CLIENT_ID,
                "client_secret": PAYPAL_CLIENT_SECRET
            })
            logger.info("PayPal integration: ✅ Available")
    else:
        logger.info("PayPal integration: ❌ Not configured (no credentials provided)")
except ImportError:
    PAYPAL_AVAILABLE = False
    logger.warning("PayPal not available - install with: pip install paypalrestsdk")

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

class PaymentProcessor:
    """Real payment processing with multiple gateway support"""
    
    @staticmethod
    def validate_payment_data(payment_data):
        """Validate payment data structure"""
        required_fields = ['amount', 'currency', 'payment_method']
        for field in required_fields:
            if field not in payment_data:
                raise ValueError(f"Missing required field: {field}")
        
        amount = payment_data['amount']
        if not isinstance(amount, (int, float, Decimal)) or amount <= 0:
            raise ValueError("Amount must be a positive number")
        
        currency = payment_data['currency'].upper()
        if currency not in ['USD', 'EUR', 'GBP', 'CAD', 'AUD']:
            raise ValueError(f"Unsupported currency: {currency}")
        
        return True
    
    @staticmethod
    def process_stripe_payment(payment_data):
        """Process payment through Stripe"""
        if not STRIPE_AVAILABLE:
            raise Exception("Stripe not configured")
        
        try:
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(payment_data['amount'] * 100),  # Stripe expects cents
                currency=payment_data['currency'].lower(),
                payment_method_types=['card'],
                description=payment_data.get('description', 'AP2 Payment'),
                metadata={
                    'ap2_transaction': 'true',
                    'order_id': payment_data.get('order_id', str(uuid.uuid4())),
                    'customer_id': payment_data.get('customer_id', 'anonymous')
                }
            )
            
            # For real implementation, you would confirm with payment method
            # For now, we'll simulate confirmation
            confirmed_intent = stripe.PaymentIntent.confirm(
                intent.id,
                payment_method=payment_data.get('payment_method_id', 'pm_card_visa')
            )
            
            return {
                'success': True,
                'transaction_id': confirmed_intent.id,
                'status': confirmed_intent.status,
                'amount': payment_data['amount'],
                'currency': payment_data['currency'],
                'payment_method': 'stripe_card',
                'gateway': 'stripe',
                'gateway_response': {
                    'payment_intent_id': confirmed_intent.id,
                    'client_secret': confirmed_intent.client_secret
                }
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'stripe_error',
                'gateway': 'stripe'
            }
    
    @staticmethod
    def process_paypal_payment(payment_data):
        """Process payment through PayPal"""
        if not PAYPAL_AVAILABLE:
            raise Exception("PayPal not configured")
        
        try:
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": payment_data.get('return_url', 'http://localhost:8092/payment/success'),
                    "cancel_url": payment_data.get('cancel_url', 'http://localhost:8092/payment/cancel')
                },
                "transactions": [{
                    "item_list": {
                        "items": payment_data.get('items', [{
                            "name": "AP2 Payment",
                            "sku": "ap2_001",
                            "price": str(payment_data['amount']),
                            "currency": payment_data['currency'],
                            "quantity": 1
                        }])
                    },
                    "amount": {
                        "total": str(payment_data['amount']),
                        "currency": payment_data['currency']
                    },
                    "description": payment_data.get('description', 'AP2 Payment Transaction')
                }]
            })
            
            if payment.create():
                return {
                    'success': True,
                    'transaction_id': payment.id,
                    'status': 'created',
                    'amount': payment_data['amount'],
                    'currency': payment_data['currency'],
                    'payment_method': 'paypal',
                    'gateway': 'paypal',
                    'gateway_response': {
                        'payment_id': payment.id,
                        'approval_url': next((link.href for link in payment.links if link.rel == 'approval_url'), None)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': payment.error,
                    'error_type': 'paypal_error',
                    'gateway': 'paypal'
                }
                
        except Exception as e:
            logger.error(f"PayPal error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'paypal_error',
                'gateway': 'paypal'
            }
    
    @staticmethod
    def process_mock_payment(payment_data):
        """Mock payment processing for development/testing"""
        logger.info("Processing mock payment - NOT A REAL TRANSACTION")
        
        # Simulate payment processing delay
        import time
        time.sleep(0.1)
        
        # Simulate some failures for testing
        if payment_data.get('amount', 0) >= 1000:
            return {
                'success': False,
                'error': 'Amount too large for mock processing',
                'error_type': 'mock_limit_exceeded',
                'gateway': 'mock'
            }
        
        return {
            'success': True,
            'transaction_id': f'mock_{uuid.uuid4().hex[:16]}',
            'status': 'succeeded',
            'amount': payment_data['amount'],
            'currency': payment_data['currency'],
            'payment_method': 'mock_card',
            'gateway': 'mock',
            'gateway_response': {
                'mock_transaction': True,
                'processed_at': datetime.utcnow().isoformat()
            }
        }

def process_real_payment(cart_data):
    """Process real payment with multiple gateway support"""
    try:
        # Extract payment information
        if isinstance(cart_data, str):
            import json
            cart_data = json.loads(cart_data)
        
        # Calculate total amount
        total_amount = 0
        if 'items' in cart_data:
            total_amount = sum(
                item.get('price', 0) * item.get('quantity', 1) 
                for item in cart_data['items']
            )
        elif 'amount' in cart_data:
            total_amount = cart_data['amount']
        
        # Prepare payment data
        payment_data = {
            'amount': round(float(total_amount), 2),
            'currency': cart_data.get('currency', 'USD'),
            'payment_method': cart_data.get('payment_method', 'card'),
            'description': cart_data.get('description', 'Online Boutique Purchase'),
            'order_id': cart_data.get('order_id', f'OB_{uuid.uuid4().hex[:8]}'),
            'customer_id': cart_data.get('customer_id'),
            'payment_method_id': cart_data.get('payment_method_id'),
            'items': cart_data.get('items', [])
        }
        
        # Validate payment data
        PaymentProcessor.validate_payment_data(payment_data)
        
        # Determine payment gateway
        gateway = cart_data.get('gateway', 'auto')
        
        # Process payment based on gateway preference
        if gateway == 'stripe' and STRIPE_AVAILABLE:
            result = PaymentProcessor.process_stripe_payment(payment_data)
        elif gateway == 'paypal' and PAYPAL_AVAILABLE:
            result = PaymentProcessor.process_paypal_payment(payment_data)
        elif gateway == 'auto':
            # Auto-select available gateway
            if STRIPE_AVAILABLE:
                result = PaymentProcessor.process_stripe_payment(payment_data)
            elif PAYPAL_AVAILABLE:
                result = PaymentProcessor.process_paypal_payment(payment_data)
            else:
                logger.warning("No real payment gateways configured, using mock")
                result = PaymentProcessor.process_mock_payment(payment_data)
        else:
            # Fallback to mock
            logger.warning(f"Requested gateway '{gateway}' not available, using mock")
            result = PaymentProcessor.process_mock_payment(payment_data)
        
        # Add additional order information
        if result['success']:
            result.update({
                'order_id': payment_data['order_id'],
                'processed_at': datetime.utcnow().isoformat(),
                'receipt_number': f'RCP_{uuid.uuid4().hex[:8]}',
                'payment_processing': 'real' if result['gateway'] != 'mock' else 'mock'
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Payment processing error: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_type': 'processing_error',
            'gateway': 'unknown'
        }

def get_dummy_payment_processing(cart_data):
    """Legacy function - redirects to real payment processing"""
    logger.info("Legacy payment function called - redirecting to real payment processing")
    result = process_real_payment(cart_data)
    
    # Convert to legacy format for backward compatibility
    if result['success']:
        return {
            'order_id': result.get('order_id', f'OB{random.randint(10000, 99999)}'),
            'total_amount': result['amount'],
            'payment_status': 'processed',
            'transaction_id': result['transaction_id'],
            'payment_method': result['payment_method'],
            'gateway': result['gateway'],
            'confirmation': {
                'email_sent': True,
                'receipt_number': result.get('receipt_number', f'RCP{random.randint(100000, 999999)}'),
                'estimated_shipping': (datetime.now() + timedelta(days=random.randint(5, 7))).strftime('%Y-%m-%d')
            }
        }
    else:
        return {
            'order_id': None,
            'payment_status': 'failed',
            'error': result['error'],
            'error_type': result['error_type'],
            'gateway': result['gateway']
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
    data = request.get_json()
    
    if not data or 'category' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Product category is required'
        }), 400
    
    category = data['category']
    products = get_dummy_products(category)
    
    response = {
        'status': 'success',
        'data': {
            'category': category,
            'products': products,
            'total_count': len(products)
        }
    }
    
    return jsonify(response)

@app.route('/customer-support', methods=['POST'])
def customer_support():
    """MCP endpoint for customer support"""
    data = request.get_json()
    
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
    """MCP endpoint for real payment processing with AP2 support"""
    data = request.get_json()
    
    if not data or 'cart_data' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Cart data is required'
        }), 400
    
    cart_data = data['cart_data']
    
    try:
        # Process payment using real payment processor
        payment_result = process_real_payment(cart_data)
        
        if payment_result['success']:
            response = {
                'status': 'success',
                'data': {
                    'order_id': payment_result['order_id'],
                    'total_amount': payment_result['amount'],
                    'payment_status': 'processed',
                    'transaction_id': payment_result['transaction_id'],
                    'payment_method': payment_result['payment_method'],
                    'gateway': payment_result['gateway'],
                    'gateway_response': payment_result.get('gateway_response', {}),
                    'processed_at': payment_result['processed_at'],
                    'receipt_number': payment_result['receipt_number'],
                    'payment_processing': payment_result['payment_processing'],
                    'confirmation': {
                        'email_sent': True,
                        'receipt_number': payment_result['receipt_number'],
                        'estimated_shipping': (datetime.now() + timedelta(days=random.randint(5, 7))).strftime('%Y-%m-%d')
                    }
                }
            }
        else:
            response = {
                'status': 'error',
                'message': payment_result['error'],
                'error_type': payment_result['error_type'],
                'gateway': payment_result['gateway'],
                'data': {
                    'payment_status': 'failed',
                    'order_id': None,
                    'transaction_id': None
                }
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Payment processing endpoint error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Payment processing failed: {str(e)}',
            'error_type': 'server_error',
            'data': {
                'payment_status': 'failed',
                'order_id': None,
                'transaction_id': None
            }
        }), 500

@app.route('/payment-real', methods=['POST'])
def payment_process_real():
    """Direct endpoint for real payment processing"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'Payment data is required'
        }), 400
    
    try:
        # Process payment directly
        payment_result = process_real_payment(data)
        
        return jsonify({
            'status': 'success' if payment_result['success'] else 'error',
            'data': payment_result
        })
        
    except Exception as e:
        logger.error(f"Direct payment processing error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'error_type': 'processing_error'
        }), 500

@app.route('/payment/webhook', methods=['POST'])
def payment_webhook():
    """Webhook endpoint for payment gateway notifications"""
    try:
        # Verify webhook signature
        signature = request.headers.get('X-Webhook-Signature', '')
        payload = request.get_data()
        
        # Simple signature verification (implement proper HMAC verification in production)
        expected_signature = hmac.new(
            PAYMENT_WEBHOOK_SECRET.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("Invalid webhook signature")
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Parse webhook data
        webhook_data = request.get_json()
        
        # Log webhook for processing
        logger.info(f"Payment webhook received: {webhook_data.get('type', 'unknown')}")
        
        # Process different webhook types
        webhook_type = webhook_data.get('type', '')
        
        if webhook_type == 'payment.succeeded':
            # Handle successful payment
            transaction_id = webhook_data.get('data', {}).get('id', '')
            logger.info(f"Payment succeeded: {transaction_id}")
            
        elif webhook_type == 'payment.failed':
            # Handle failed payment
            transaction_id = webhook_data.get('data', {}).get('id', '')
            logger.warning(f"Payment failed: {transaction_id}")
            
        return jsonify({'status': 'received'}), 200
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 500

@app.route('/payment/status/<transaction_id>', methods=['GET'])
def payment_status(transaction_id):
    """Check payment status"""
    try:
        # In a real implementation, you would query the payment gateway
        # For now, return a mock status
        status_data = {
            'transaction_id': transaction_id,
            'status': 'completed',
            'amount': 99.0,
            'currency': 'USD',
            'processed_at': datetime.utcnow().isoformat(),
            'gateway': 'mock'
        }
        
        return jsonify({
            'status': 'success',
            'data': status_data
        })
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/shipping-coordinate', methods=['POST'])
def shipping_coordinate():
    """MCP endpoint for shipping coordination"""
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
    data = request.get_json()
    
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

# --- MODIFICATIONS START ---
# This function is now the main entry point for starting the server.
def run_server(host="0.0.0.0", port=None):
    """Starts the MCP Flask server."""
    # Get port from environment variable, fallback to 8080 for local dev
    if port is None:
        port = int(os.environ.get("PORT", 8080))
    
    print("🚀 Online Boutique MCP Server starting...")
    print(f"🛍️ Listening on {host}:{port}")
    
    # Use waitress for production deployment instead of Flask dev server
    try:
        from waitress import serve
        print("Using Waitress WSGI server for production")
        serve(app, host=host, port=port)
    except ImportError:
        print("Waitress not available, using Flask dev server")
        app.run(host=host, port=port, debug=False)

# For Gunicorn compatibility - keep the function for backwards compatibility
# but when using Gunicorn, it will directly use the 'app' object
if __name__ == '__main__':
    run_server()
# --- MODIFICATIONS END ---
