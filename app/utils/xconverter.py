import requests
from datetime import datetime, timedelta
from flask import jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

# Global cache for exchange rates
rates_cache = {}
CACHE_DURATION = timedelta(hours=6)  # Cache rates for 6 hours

def get_exchange_rate(from_currency, to_currency):
    """Get exchange rate with caching - no API key required"""
    from_curr = from_currency.upper()
    to_curr = to_currency.upper()
    
    if from_curr == to_curr:
        return 1.0
    
    cache_key = f"{from_curr}_{to_curr}"
    
    # Check cache first
    if cache_key in rates_cache:
        rate, timestamp = rates_cache[cache_key]
        if datetime.now() - timestamp < CACHE_DURATION:
            return rate
    
    # Fetch new rate from API - NO API KEY NEEDED
    try:
        url = f"https://open.er-api.com/v6/latest/{from_curr}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get('result') == 'success':  # Different success indicator
            rate = data['rates'][to_curr]
            rates_cache[cache_key] = (rate, datetime.now())
            return rate
        else:
            current_app.logger.error(f"API error: {data.get('error-type')}")
            return None
    except Exception as e:
        current_app.logger.error(f"Exchange rate error: {str(e)}")
        return None
    
    return None