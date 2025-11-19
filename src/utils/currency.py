import os
import json
import requests
from functools import lru_cache
from typing import Tuple, Optional

# Example FX API endpoint
FX_API_URL = "https://api.exchangerate.host/latest?base=USD"

# Fallback static rates (used if FX API fails)
STATIC_FX_RATES = {
    "USD": 1.0,
    "MMK": 2100.0,
    "THB": 35.5,
    "MYR": 4.7,
    "KHR": 4100.0,
    "EUR": 0.94,
    "INR": 83.0
}

# Country → Currency Code
COUNTRY_TO_CURRENCY = {
    "MM": "MMK",  # Myanmar
    "TH": "THB",  # Thailand
    "MY": "MYR",  # Malaysia
    "KH": "KHR",  # Cambodia
    "IN": "INR",  # India
    "FR": "EUR",
    "DE": "EUR",
    "US": "USD",
}

# Currency → Symbol
CURRENCY_SYMBOL = {
    "USD": "$",
    "MMK": "Ks",
    "THB": "฿",
    "MYR": "RM",
    "KHR": "៛",
    "EUR": "€",
    "INR": "₹"
}

# Fake IP-based country detection (can be replaced with geoip2)
def detect_country_from_ip(ip_address: str) -> str:
    # For real prod, use geoip2 / IP-API / MaxMind
    if ip_address.startswith("103."):
        return "MM"
    elif ip_address.startswith("1."):
        return "TH"
    elif ip_address.startswith("203."):
        return "MY"
    else:
        return "US"

def detect_currency_from_ip(ip_address: str) -> str:
    country = detect_country_from_ip(ip_address)
    return COUNTRY_TO_CURRENCY.get(country, "USD")

@lru_cache(maxsize=1)
def get_latest_fx_rates() -> dict:
    try:
        response = requests.get(FX_API_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("rates", STATIC_FX_RATES)
    except Exception as e:
        print(f"[currency] FX API failed: {e}")
    return STATIC_FX_RATES

def get_fx_rate(currency_code: str) -> float:
    rates = get_latest_fx_rates()
    return float(rates.get(currency_code, STATIC_FX_RATES.get(currency_code, 1.0)))

def convert_usd_to(currency_code: str, amount_usd: float) -> float:
    rate = get_fx_rate(currency_code)
    return round(amount_usd * rate, 2)

def get_currency_display(ip_address: str) -> dict:
    currency_code = detect_currency_from_ip(ip_address)
    symbol = CURRENCY_SYMBOL.get(currency_code, "$")
    rate = get_fx_rate(currency_code)
    return {
        "currency": currency_code,
        "symbol": symbol,
        "fx_rate": rate
    }

# Optional: convert to human string for UI
def format_currency(amount_usd: float, ip_address: str) -> str:
    info = get_currency_display(ip_address)
    local_amount = convert_usd_to(info["currency"], amount_usd)
    return f"{info['symbol']}{local_amount}"
