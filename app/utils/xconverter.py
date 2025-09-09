import requests
from flask import current_app
from datetime import datetime, timedelta
from functools import wraps

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
            return None
    except Exception as e:
        return None
    
    return None

# Cache for exchange rates
_rates_cache = {
    'data': None,
    'timestamp': None,
    'base_currency': None,
    'expiry': timedelta(hours=6)
}


def fetch_exchange_rates(base_currency):
    """Fetch exchange rates from API or return cached version if still valid"""
    global _rates_cache

    # Check if cache is valid for the base_currency
    if (_rates_cache['data'] is not None and 
        _rates_cache['base_currency'] == base_currency and
        _rates_cache['timestamp'] and 
        (datetime.now() - _rates_cache['timestamp']) < _rates_cache['expiry']):
        current_app.logger.info("Returning cached exchange rates")
        return _rates_cache['data']

    try:
        url = f'https://open.er-api.com/v6/latest/{base_currency}'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('result') != 'success':
            current_app.logger.error(f"API error: {data.get('error-type', 'Unknown error')}")
            return None

        rates = data['rates']
        # Update cache
        _rates_cache['data'] = rates
        _rates_cache['timestamp'] = datetime.now()
        _rates_cache['base_currency'] = base_currency

        return rates

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Request error: {str(e)}")
        return None
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
        return None

# 'buyPrice' is what the bank pays for foreign currency (lower rate).
BUY_MARGIN_PERCENT = 0.0158
# 'sellPrice' is what the bank charges for foreign currency (higher rate).
SELL_MARGIN_PERCENT = 0.0106

def apply_margins(rates, base_currency, target_currencies):
    """
    Apply buy/sell margins to exchange rates.
    The rates are expressed in the base_currency. For example, if the base is NGN,
    the rate for USD will be how many NGN it costs to buy or sell 1 USD.
    """
    formatted_rates = []
    
    for currency in target_currencies:
        if currency == base_currency:
            continue
            
        rate = rates.get(currency)  # This is target_currency per 1 unit of base_currency
        if rate is not None and rate > 0:
            # Invert rate to get base_currency per 1 unit of target_currency
            inverse_rate = 1 / rate
            
            buy_price = inverse_rate * (1 - BUY_MARGIN_PERCENT)
            sell_price = inverse_rate * (1 + SELL_MARGIN_PERCENT)
            
            formatted_rates.append({
                "currency": currency,
                "buyPrice": f"{buy_price:,.2f}",
                "sellPrice": f"{sell_price:,.2f}"
            })
    
    return formatted_rates
