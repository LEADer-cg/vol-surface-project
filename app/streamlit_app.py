
# app/streamlit_app.py
import streamlit as st
import pandas as pd
from volcalc.fetcher import get_option_chain
from volcalc.surface import compute_implied_vols, make_surface_grid
from volcalc.db import SessionLocal, Snapshot, OptionPoint
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Vol Surface Explorer")

st.title("Implied Volatility Surface Explorer")
ticker = st.text_input("Ticker", value="AAPL")
mode = st.radio("Mode", ["Live fetch (yfinance)", "Historic snapshots (DB)"])

r = st.number_input("Risk-free rate (r)", value=0.01, format="%.4f")
q = st.number_input("Dividend yield (q)", value=0.0, format="%.4f")

if st.button("Fetch & Plot"):
    if mode == "Live fetch (yfinance)":
        df = get_option_chain(ticker)
        if df.empty:
            st.error("No options found.")
        else:
            df_iv = compute_implied_vols(df, r=r, q=q)
            surf = make_surface_grid(df_iv)
            if surf is None:
                st.error("Insufficient data to build surface.")
            else:
                fig = go.Figure(data=[go.Surface(x=surf['X'], y=surf['Y'], z=surf['Z'])])
                fig.update_layout(scene=dict(xaxis_title=surf['x_label'], yaxis_title=surf['y_label'], zaxis_title='Implied Vol'))
                st.plotly_chart(fig, use_container_width=True)
    else:
        session = SessionLocal()
        snaps = session.query(Snapshot).filter(Snapshot.ticker==ticker).order_by(Snapshot.fetched_at.desc()).limit(50).all()
        if not snaps:
            st.warning("No snapshots for ticker in DB.")
        else:
            choice = st.selectbox("Choose snapshot", [f"{s.id} - {s.fetched_at}" for s in snaps])
            sid = int(choice.split(' - ')[0])
            points = session.query(OptionPoint).filter(OptionPoint.snapshot_id==sid).all()
            df = pd.DataFrame([{'strike':p.strike,'iv':p.iv,'expiration':p.expiration} for p in points])
            if df.empty:
                st.error("No points in snapshot.")
            else:
                df['expiration'] = pd.to_datetime(df['expiration'])
                df['time_to_expiry'] = (df['expiration'] - pd.Timestamp.utcnow()).dt.total_seconds()/(365.25*24*3600)
                df['days_to_expiry'] = df['time_to_expiry']*365.25
                try:
                    # Attach a fake spot column for moneyness calculation if missing
                    if 'spot' not in df.columns:
                        df['spot'] = df['strike'].median()
                    surf = make_surface_grid(df.rename(columns={'strike':'strike','iv':'iv','time_to_expiry':'time_to_expiry','spot': 'spot'}))
                    if surf is None:
                        st.error("Unable to construct surface from snapshot data.")
                    else:
                        fig = go.Figure(data=[go.Surface(x=surf['X'], y=surf['Y'], z=surf['Z'])])
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.write(df.head())
                    st.error("Failed to build surface: " + str(e))
        session.close()
