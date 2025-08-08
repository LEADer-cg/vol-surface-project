
# volcalc/fetcher.py
import yfinance as yf
import pandas as pd

def get_option_chain(ticker: str):
    tk = yf.Ticker(ticker)
    expiries = tk.options  # list of date strings 'YYYY-MM-DD'
    rows = []
    # Attempt to get latest close as spot
    hist = tk.history(period="1d")
    if hist is None or hist.empty:
        spot = None
    else:
        spot = hist['Close'].iloc[-1]
    for exp in expiries:
        try:
            oc = tk.option_chain(exp)
            calls = oc.calls.copy()
            calls['expirationDate'] = pd.to_datetime(exp)
            calls['spot'] = spot
            rows.append(calls)
        except Exception:
            # skip expiry if fetching fails
            continue
    if not rows:
        return pd.DataFrame()
    df = pd.concat(rows, ignore_index=True)
    # convert numeric columns
    for col in ['strike', 'lastPrice', 'bid','ask','openInterest','volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df['fetched_at'] = pd.Timestamp.utcnow()
    return df
