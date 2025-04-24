from flask import Flask, render_template, redirect, url_for, request, jsonify
import os
import subprocess
import sys
import stripe  # Add Stripe import

# Import Stripe configuration
try:
    from . import stripe_config
except ImportError:
    import stripe_config

# Create the Flask app with explicit template and static folder paths
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Stripe configuration
stripe.api_key = stripe_config.STRIPE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY = stripe_config.STRIPE_PUBLISHABLE_KEY
STRIPE_WEBHOOK_SECRET = stripe_config.STRIPE_WEBHOOK_SECRET
YOUR_DOMAIN = stripe_config.YOUR_DOMAIN
ENABLE_SIMULATION = stripe_config.ENABLE_SIMULATION

# --- Routes ---

@app.route('/')
def index():
    """Displays the main landing/fundraiser page."""
    print("Rendering index.html")
    return render_template('index.html')

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """
    Creates a Stripe checkout session and redirects to the Stripe payment page.
    After payment, Stripe will redirect to the success URL with the session ID.
    """
    try:
        # Use the simulated checkout if ENABLE_SIMULATION is True
        if ENABLE_SIMULATION:
            print("Simulating Stripe Checkout (ENABLE_SIMULATION=True)")
            return redirect(url_for('success'))
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Chess AI Opponent Access',
                            'description': 'Access to play against AI chess opponents of varying difficulty levels',
                            'images': [f"{YOUR_DOMAIN}/static/images/chess_fundraiser.png"],
                        },
                        'unit_amount': 100,  # $1.00 in cents
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=f"{YOUR_DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{YOUR_DOMAIN}/",
        )
        print(f"Created Stripe checkout session: {checkout_session.id}")
        return redirect(checkout_session.url, code=303)
    
    except Exception as e:
        print(f"Error creating Stripe checkout session: {e}")
        return jsonify(error=str(e)), 500

@app.route('/success')
def success():
    """
    Handles the successful payment redirect from Stripe.
    In a real app, verify the payment was successful using the session_id.
    """
    session_id = request.args.get('session_id')
    
    if session_id:
        try:
            # Verify the payment was successful with Stripe
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid":
                print(f"Verified successful payment for session {session_id}")
            else:
                print(f"Payment not complete for session {session_id}")
        except Exception as e:
            print(f"Error verifying payment: {e}")
    else:
        print("No session_id provided. This is either a simulated payment or direct access.")
    
    # Redirect to game settings regardless
    return redirect(url_for('game_settings'))

@app.route('/settings')
def game_settings():
    """Displays the game settings page (difficulty/color selection)."""
    print("Loading game settings page...")
    return render_template('settings.html')

@app.route('/start-game')
def start_game():
    """
    Starts the Pygame chess application with the selected parameters.
    Parameters:
    - difficulty: AI difficulty level (0-4)
    - color: Player color (white/black)
    """
    difficulty = request.args.get('difficulty', '0')
    color = request.args.get('color', 'white')
    
    # Convert to the format expected by the pygame app
    color_value = '1' if color == 'black' else '0'  # 0 for white, 1 for black
    
    try:
        # Path to the main.py file
        main_py_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'main.py'))
        print(f"Looking for main.py at: {main_py_path}")
        
        if not os.path.exists(main_py_path):
            return jsonify({
                'status': 'error',
                'message': f'Could not find main.py at path: {main_py_path}'
            }), 404
        
        # Prepare the command with proper arguments
        # On Windows, use 'python' or 'py' for PowerShell/CMD
        
        # Try using Python executable directly
        if sys.platform == 'win32':
            # Windows: Use start command to launch in a new window
            cmd = ['start', 'cmd', '/c', sys.executable, main_py_path, 
                   '--skill', difficulty, '--color', color_value]
            shell_required = True
        else:
            # Linux/Mac: Standard execution
            cmd = [sys.executable, main_py_path, 
                   '--skill', difficulty, '--color', color_value]
            shell_required = False
        
        # Start the game in a new process
        print(f"Starting game with: difficulty={difficulty}, color={color}")
        print(f"Command: {' '.join(cmd)}")
        
        # Using subprocess.Popen to start the process without waiting for it to complete
        process = subprocess.Popen(cmd, shell=shell_required)
        
        # Return a success message
        return jsonify({
            'status': 'success',
            'message': 'Game started successfully!',
            'params': {
                'difficulty': difficulty,
                'color': color
            }
        })
    
    except Exception as e:
        # If there's an error, return an error message
        print(f"Error starting game: {e}")
        
        # Try an alternative method as a fallback
        try:
            print("Trying alternative launch method...")
            if sys.platform == 'win32':
                # Create a batch file to launch the game
                batch_content = f'@echo off\ncd "{os.path.dirname(main_py_path)}"\n"{sys.executable}" "{main_py_path}" --skill {difficulty} --color {color_value}\npause'
                batch_path = os.path.join(os.path.dirname(main_py_path), "launch_game.bat")
                
                with open(batch_path, 'w') as f:
                    f.write(batch_content)
                
                # Execute the batch file
                os.startfile(batch_path)
                
                return jsonify({
                    'status': 'success',
                    'message': 'Game started using alternative method!',
                    'params': {
                        'difficulty': difficulty,
                        'color': color
                    }
                })
        except Exception as fallback_error:
            print(f"Alternative launch method also failed: {fallback_error}")
        
        return jsonify({
            'status': 'error',
            'message': f'Error starting game: {e}. Please try running main.py directly.'
        }), 500

# --- Debug route to check environment ---
@app.route('/debug')
def debug():
    """Provides debug information about the Flask app's environment."""
    debug_info = {
        'template_folder': app.template_folder,
        'static_folder': app.static_folder,
        'templates_exist': os.path.exists(app.template_folder),
        'static_exists': os.path.exists(app.static_folder),
        'index_html_exists': os.path.exists(os.path.join(app.template_folder, 'index.html')),
        'settings_html_exists': os.path.exists(os.path.join(app.template_folder, 'settings.html')),
        'main_py_exists': os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'main.py'))),
        'cwd': os.getcwd(),
        'python_path': sys.executable,
    }
    return jsonify(debug_info)

# --- Stripe webhook handling (for asynchronous payment events) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events for payment completion, refunds, etc."""
    event = None
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        print(f"Invalid payload: {e}")
        return jsonify(success=False), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print(f"Invalid signature: {e}")
        return jsonify(success=False), 400
    
    # Handle the event
    if event.type == 'checkout.session.completed':
        session = event.data.object
        print(f"Payment successful for session {session.id}")
        # You can save customer info in your database here if needed
        # customer_email = session.customer_details.email
    
    return jsonify(success=True)

# --- Run the App ---
if __name__ == '__main__':
    print(f"Template folder: {app.template_folder}")
    print(f"Static folder: {app.static_folder}")
    print(f"Working directory: {os.getcwd()}")
    
    # Use 0.0.0.0 to make it accessible on your network if needed,
    # otherwise 127.0.0.1 (localhost) is fine.
    # Debug=True is helpful during development but should be OFF in production.
    app.run(debug=True, host='0.0.0.0', port=5000)