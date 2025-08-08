
# volcalc/surface.py
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from .bs import implied_vol_call

def compute_implied_vols(df_calls, r=0.01, q=0.0):
    """
    df_calls must have: strike, lastPrice (or mid), expirationDate, spot
    Returns df with 'iv' column and 'time_to_expiry' in years
    """
    out = df_calls.copy()
    # Use mid price if available
    if 'bid' in out.columns and 'ask' in out.columns:
        out['mid'] = (out['bid'].fillna(0) + out['ask'].fillna(0)) / 2
    elif 'lastPrice' in out.columns:
        out['mid'] = out['lastPrice']
    else:
        out['mid'] = out.get('last', 0.0)
    out['expirationDate'] = pd.to_datetime(out['expirationDate'], utc=True)
    now = pd.Timestamp.now(tz='UTC')
    eps = 1e-12
    out['time_to_expiry'] = ((out['expirationDate'] - now).dt.total_seconds() / (365.25*24*3600)).clip(lower=eps)
    S = out['spot'].iloc[0] if 'spot' in out.columns else None
    ivs = []
    for _, row in out.iterrows():
        try:
            iv = implied_vol_call(row['mid'], S, row['strike'], row['time_to_expiry'], r, q)
        except Exception:
            iv = float('nan')
        ivs.append(iv)
    out['iv'] = ivs
    return out

def make_surface_grid(df_iv, n_strikes=50, n_times=50, use_moneyness=True):
    """
    Produce grid X=time (days), Y=strike or moneyness, Z=iv
    Returns dict with X, Y, Z and labels.
    """
    df = df_iv.dropna(subset=['iv'])
    if df.empty:
        return None
    df = df.copy()
    df['days_to_expiry'] = df['time_to_expiry'] * 365.25
    if use_moneyness:
        if 'spot' in df.columns and df['spot'].notnull().any():
            S = df['spot'].iloc[0]
        else:
            S = df['strike'].median()
        df['moneyness'] = df['strike'] / S
        y = np.linspace(df['moneyness'].min()*0.95, df['moneyness'].max()*1.05, n_strikes)
        yi = 'moneyness'
    else:
        y = np.linspace(df['strike'].min()*0.95, df['strike'].max()*1.05, n_strikes)
        yi = 'strike'
    x = np.linspace(df['days_to_expiry'].min(), df['days_to_expiry'].max(), n_times)
    X, Y = np.meshgrid(x, y)
    points = np.vstack((df['days_to_expiry'], df[yi])).T
    values = df['iv'].values
    Z = griddata(points, values, (X, Y), method='linear')
    # fallback for NaNs
    mask = np.isnan(Z)
    if mask.any():
        Z_nearest = griddata(points, values, (X, Y), method='nearest')
        Z[mask] = Z_nearest[mask]
    return {'X': X, 'Y': Y, 'Z': Z, 'x_label': 'Days to expiry', 'y_label': yi}
