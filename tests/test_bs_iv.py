
# tests/test_bs_iv.py
from volcalc.bs import bs_call_price, implied_vol_call

def test_bs_iv_roundtrip():
    S=100; K=105; T=0.5; r=0.01; q=0.0; sigma=0.25
    price = bs_call_price(S,K,T,r,q,sigma)
    iv = implied_vol_call(price,S,K,T,r,q)
    assert abs(iv - sigma) < 1e-3
