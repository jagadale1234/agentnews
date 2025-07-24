#!/usr/bin/env python3
"""
Cloud Web Interface for AgentNews Subscription Management
========================================================

A Flask-based web interface with database integration for handling
subscribe/unsubscribe requests with unsubscribe tokens.
"""

try:
    from flask import Flask, request, render_template_string, redirect, url_for, flash
except ImportError:
    print("Flask not installed. Install with: pip install flask")
    exit(1)

import os
import logging
from agent_news_cloud import DatabaseManager, CloudNewsletterEmailer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here-change-in-production')

# HTML Templates
MAIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AgentNews - AI Agent Newsletter</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            max-width: 600px; 
            margin: 50px auto; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            background: white; 
            padding: 40px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #333;
            margin: 0;
            font-size: 2.5em;
        }
        .header .subtitle {
            color: #666;
            margin-top: 10px;
            font-size: 1.1em;
        }
        .button { 
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white; 
            padding: 12px 25px; 
            border: none; 
            border-radius: 25px; 
            cursor: pointer; 
            font-size: 16px;
            transition: all 0.3s ease;
            width: 100%;
            margin-top: 10px;
        }
        .button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        .unsubscribe { 
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
        }
        .message { 
            margin: 20px 0; 
            padding: 15px; 
            border-radius: 10px; 
            font-weight: 500;
        }
        .success { 
            background: #d4edda; 
            color: #155724; 
            border: 1px solid #c3e6cb; 
        }
        .error { 
            background: #f8d7da; 
            color: #721c24; 
            border: 1px solid #f5c6cb; 
        }
        input[type="email"] { 
            width: 100%; 
            padding: 15px; 
            margin: 10px 0; 
            border: 2px solid #ddd; 
            border-radius: 10px; 
            font-size: 16px;
            transition: border-color 0.3s ease;
            box-sizing: border-box;
        }
        input[type="email"]:focus {
            outline: none;
            border-color: #667eea;
        }
        .form-section {
            margin: 30px 0;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .form-section h3 {
            margin-top: 0;
            color: #333;
        }
        hr { 
            border: none; 
            height: 2px; 
            background: linear-gradient(to right, #667eea, #764ba2);
            margin: 30px 0; 
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 0.9em;
        }
        .stats {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
            color: #1565c0;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AgentNews</h1>
            <div class="subtitle">Your AI Agent Newsletter</div>
        </div>
        
        <div class="stats">
            {{ subscriber_count }} active subscribers receiving weekly AI agent updates
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="message {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="form-section">
            <h3>Subscribe to AgentNews</h3>
            <p>Get the latest AI agent news and updates delivered to your inbox every week.</p>
            <form method="POST" action="{{ url_for('subscribe') }}">
                <input type="email" name="email" placeholder="Enter your email address" required>
                <button type="submit" class="button">Subscribe Now</button>
            </form>
        </div>
        
        <hr>
        
        <div class="form-section">
            <h3>Unsubscribe from AgentNews</h3>
            <p>Sorry to see you go! You can unsubscribe at any time.</p>
            <form method="POST" action="{{ url_for('unsubscribe') }}">
                <input type="email" name="email" placeholder="Enter your email address" required>
                <button type="submit" class="button unsubscribe">Unsubscribe</button>
            </form>
        </div>
        
        <div class="footer">
            <p>
                <strong>AgentNews</strong> delivers curated AI agent news and insights.<br>
                We respect your privacy and you can unsubscribe at any time.<br>
                <small>Powered by AI • Updated Weekly • Privacy First</small>
            </p>
        </div>
    </div>
</body>
</html>
"""

SUCCESS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AgentNews - {{ action|title }} Successful</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            max-width: 600px; 
            margin: 50px auto; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            background: white; 
            padding: 40px; 
            border-radius: 15px; 
            text-align: center; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .success { 
            color: #155724; 
        }
        .success h1 {
            font-size: 3em;
            margin: 20px 0;
        }
        .button { 
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white; 
            padding: 12px 25px; 
            border: none; 
            border-radius: 25px; 
            text-decoration: none; 
            display: inline-block; 
            margin-top: 30px;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        .button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        .info {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="success">
            {% if action == 'subscribe' %}
                <h1>Welcome to AgentNews!</h1>
                <div class="info">
                    <p><strong>Subscription Confirmed!</strong></p>
                    <p>You'll receive the latest AI agent news in your inbox every Monday.</p>
                    <p>Check your email for our next newsletter!</p>
                </div>
            {% else %}
                <h1>Successfully Unsubscribed</h1>
                <div class="info">
                    <p><strong>You've been unsubscribed from AgentNews.</strong></p>
                    <p>You won't receive any more newsletters from us.</p>
                    <p>If you change your mind, you can always subscribe again!</p>
                </div>
            {% endif %}
        </div>
        <a href="{{ url_for('index') }}" class="button">← Back to Homepage</a>
    </div>
</body>
</html>
"""

UNSUBSCRIBE_TOKEN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AgentNews - Confirm Unsubscribe</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            max-width: 600px; 
            margin: 50px auto; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            background: white; 
            padding: 40px; 
            border-radius: 15px; 
            text-align: center; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .button { 
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white; 
            padding: 12px 25px; 
            border: none; 
            border-radius: 25px; 
            text-decoration: none; 
            display: inline-block; 
            margin: 10px;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        .button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        .button.cancel {
            background: #6c757d;
        }
        .warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            color: #856404;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>AgentNews Unsubscribe</h1>
        
        <div class="warning">
            <h3>Are you sure you want to unsubscribe?</h3>
            <p>You'll no longer receive weekly AI agent news and updates.</p>
            <p><strong>Email:</strong> {{ email }}</p>
        </div>
        
        <form method="POST" style="display: inline;">
            <input type="hidden" name="token" value="{{ token }}">
            <input type="hidden" name="confirm" value="yes">
            <button type="submit" class="button">Yes, Unsubscribe Me</button>
        </form>
        
        <a href="{{ url_for('index') }}" class="button cancel">Cancel</a>
    </div>
</body>
</html>
"""

def get_database():
    """Get database manager instance"""
    database_url = os.getenv('DATABASE_URL')
    try:
        return DatabaseManager(database_url)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

@app.route('/')
def index():
    """Main page with subscriber count"""
    db = get_database()
    subscriber_count = db.get_subscriber_count() if db else 0
    return render_template_string(MAIN_TEMPLATE, subscriber_count=subscriber_count)

@app.route('/subscribe', methods=['POST'])
def subscribe():
    """Handle subscription requests"""
    email = request.form.get('email', '').strip().lower()
    
    if not email:
        flash('Please enter a valid email address.', 'error')
        return redirect(url_for('index'))
    
    db = get_database()
    if not db:
        flash('Service temporarily unavailable. Please try again later.', 'error')
        return redirect(url_for('index'))
    
    success, message, is_new_subscriber = db.add_subscriber(email)
    
    if success:
        logger.info(f"Web subscription: {email} (new: {is_new_subscriber})")
        
        # Send welcome email to new subscribers
        if is_new_subscriber:
            try:
                gmail_user = os.getenv('GMAIL_USER')
                gmail_password = os.getenv('GMAIL_APP_PASSWORD')
                
                if gmail_user and gmail_password:
                    emailer = CloudNewsletterEmailer(gmail_user, gmail_password, os.getenv('DATABASE_URL'))
                    welcome_sent = emailer.send_welcome_email(email)
                    
                    if welcome_sent:
                        logger.info(f"Welcome email sent to new subscriber: {email}")
                    else:
                        logger.warning(f"Failed to send welcome email to: {email}")
                else:
                    logger.warning("Gmail credentials not available for welcome email")
                    
            except Exception as e:
                logger.error(f"Error sending welcome email to {email}: {e}")
                # Don't fail the subscription if welcome email fails
        
        return render_template_string(SUCCESS_TEMPLATE, action='subscribe')
    else:
        flash(message, 'error')
        return redirect(url_for('index'))

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    """Handle unsubscribe requests"""
    # Handle token-based unsubscribe (from email links)
    token = request.args.get('token') or request.form.get('token')
    
    if token:
        return handle_token_unsubscribe(token)
    
    # Handle email-based unsubscribe (from web form)
    if request.method == 'POST':
        return handle_email_unsubscribe()
    
    # GET request without token - redirect to main page
    return redirect(url_for('index'))

def handle_token_unsubscribe(token):
    """Handle unsubscribe with token"""
    db = get_database()
    if not db:
        flash('Service temporarily unavailable. Please try again later.', 'error')
        return redirect(url_for('index'))
    
    # Check if this is a confirmation
    if request.method == 'POST' and request.form.get('confirm') == 'yes':
        # Find subscriber by token and unsubscribe
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                if db.is_postgres:
                    cursor.execute("""
                        UPDATE subscribers 
                        SET is_active = %s, unsubscribed_at = CURRENT_TIMESTAMP
                        WHERE unsubscribe_token = %s AND is_active = %s
                        RETURNING email
                    """, (False, token, True))
                    result = cursor.fetchone()
                    email = result[0] if result else None
                else:
                    cursor.execute("""
                        SELECT email FROM subscribers 
                        WHERE unsubscribe_token = ? AND is_active = 1
                    """, (token,))
                    result = cursor.fetchone()
                    email = result[0] if result else None
                    
                    if email:
                        cursor.execute("""
                            UPDATE subscribers 
                            SET is_active = 0, unsubscribed_at = CURRENT_TIMESTAMP
                            WHERE unsubscribe_token = ?
                        """, (token,))
                
                if email:
                    conn.commit()
                    logger.info(f"Token unsubscribe successful: {email}")
                    return render_template_string(SUCCESS_TEMPLATE, action='unsubscribe')
                else:
                    flash('Invalid or expired unsubscribe link.', 'error')
                    return redirect(url_for('index'))
                    
        except Exception as e:
            logger.error(f"Error processing token unsubscribe: {e}")
            flash('An error occurred. Please try again later.', 'error')
            return redirect(url_for('index'))
    
    # Show confirmation page
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            if db.is_postgres:
                cursor.execute("""
                    SELECT email FROM subscribers 
                    WHERE unsubscribe_token = %s AND is_active = %s
                """, (token, True))
            else:
                cursor.execute("""
                    SELECT email FROM subscribers 
                    WHERE unsubscribe_token = ? AND is_active = 1
                """, (token,))
            
            result = cursor.fetchone()
            if result:
                email = result[0]
                return render_template_string(UNSUBSCRIBE_TOKEN_TEMPLATE, token=token, email=email)
            else:
                flash('Invalid or expired unsubscribe link.', 'error')
                return redirect(url_for('index'))
                
    except Exception as e:
        logger.error(f"Error validating unsubscribe token: {e}")
        flash('An error occurred. Please try again later.', 'error')
        return redirect(url_for('index'))

def handle_email_unsubscribe():
    """Handle unsubscribe by email address"""
    email = request.form.get('email', '').strip().lower()
    
    if not email:
        flash('Please enter a valid email address.', 'error')
        return redirect(url_for('index'))
    
    db = get_database()
    if not db:
        flash('Service temporarily unavailable. Please try again later.', 'error')
        return redirect(url_for('index'))
    
    success, message = db.remove_subscriber(email)
    
    if success:
        logger.info(f"Web unsubscribe: {email}")
        return render_template_string(SUCCESS_TEMPLATE, action='unsubscribe')
    else:
        flash(message, 'error')
        return redirect(url_for('index'))

@app.route('/health')
def health_check():
    """Health check endpoint"""
    db = get_database()
    if db:
        count = db.get_subscriber_count()
        return {'status': 'healthy', 'subscribers': count}
    else:
        return {'status': 'unhealthy', 'error': 'database connection failed'}, 500

if __name__ == '__main__':
    print("AgentNews Cloud Web Interface")
    print("=" * 40)
    
    # Get port from environment (Railway sets this automatically)
    port = int(os.getenv('PORT', 5000))
    
    print(f"Starting web server on port {port}...")
    print(f"Environment: {'Production' if os.getenv('DATABASE_URL') else 'Development'}")
    
    # Check database connection
    db = get_database()
    if db:
        count = db.get_subscriber_count()
        print(f"Database connected - {count} active subscribers")
    else:
        print("Database connection failed - check DATABASE_URL")
    
    # Run with production settings if DATABASE_URL is set (cloud deployment)
    if os.getenv('DATABASE_URL'):
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("Visit https://agentnews-production.up.railway.app to manage subscriptions")
        print("Press Ctrl+C to stop")
        app.run(debug=True, host='0.0.0.0', port=port)
