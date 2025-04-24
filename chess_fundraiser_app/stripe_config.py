# Stripe Configuration

# Your Stripe API keys
# Replace these with your actual keys from the Stripe Dashboard
# https://dashboard.stripe.com/apikeys

# Test keys have the prefix 'sk_test_' and 'pk_test_'
# Production keys have the prefix 'sk_live_' and 'pk_live_'

# IMPORTANT: Never commit your secret keys to version control
# In production, use environment variables instead

# Test mode keys (safe to use during development)
STRIPE_SECRET_KEY = "sk_test_your_test_secret_key"  # Replace with your test secret key
STRIPE_PUBLISHABLE_KEY = "pk_test_your_test_publishable_key"  # Replace with your test publishable key
STRIPE_WEBHOOK_SECRET = "whsec_your_webhook_secret"  # Replace with your webhook secret

# Your domain for Stripe to redirect back to
YOUR_DOMAIN = "http://localhost:5000"

# Set to True to use test keys, False to use live keys
USE_TEST_KEYS = True

# Enable simulation mode (skips actual Stripe API calls)
ENABLE_SIMULATION = True  # Set to False to use real Stripe payments 