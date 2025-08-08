
# volcalc/bs.py
import math
from scipy.stats import norm
from scipy.optimize import brentq

def bs_call_price(S, K, T, r, q, sigma):
    """
    European Black-Scholes call price (continuous dividend yield q).
    S: spot
    K: strike
    T: time to expiry in years
    r: risk-free rate
    q: dividend yield
    sigma: vol
    """
    if T <= 0:
        return max(S - K, 0.0)
    if sigma <= 0:
        # intrinsic under zero vol (approx)
        return max(S * math.exp(-q*T) - K * math.exp(-r*T), 0.0)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * math.exp(-q*T) * norm.cdf(d1) - K * math.exp(-r*T) * norm.cdf(d2)

def implied_vol_call(market_price, S, K, T, r, q, sigma_bounds=(1e-6, 5.0)):
    """
    Invert Black-Scholes for a call to find implied vol using Brent's method.
    Returns NaN if inversion fails.
    """
    if market_price is None or market_price <= 0:
        return 0.0
    # Price bounds check
    f_low = max(S * math.exp(-q*T) - K * math.exp(-r*T), 0.0)
    f_high = S * math.exp(-q*T)
    # If market price outside theoretical bounds, return NaN
    if market_price < f_low - 1e-8 or market_price > f_high + 1e-8:
        return float('nan')
    def objective(s):
        return bs_call_price(S, K, T, r, q, s) - market_price
    try:
        iv = brentq(objective, sigma_bounds[0], sigma_bounds[1], maxiter=200)
        return iv
    except Exception:
        try:
            iv = brentq(objective, sigma_bounds[0], 2.0, maxiter=200)
            return iv
        except Exception:
            return float('nan')
