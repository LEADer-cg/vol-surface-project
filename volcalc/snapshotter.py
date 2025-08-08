
# volcalc/snapshotter.py
from apscheduler.schedulers.background import BackgroundScheduler
from .fetcher import get_option_chain
from .surface import compute_implied_vols
from .db import SessionLocal, Snapshot, OptionPoint, init_db
import logging

logger = logging.getLogger(__name__)

def take_snapshot(ticker, r=0.01, q=0.0):
    df = get_option_chain(ticker)
    if df.empty:
        logger.warning("No option data returned for %s", ticker)
        return None
    df_iv = compute_implied_vols(df, r=r, q=q)
    session = SessionLocal()
    try:
        snap = Snapshot(ticker=ticker, fetched_at=df_iv['fetched_at'].max().to_pydatetime() if 'fetched_at' in df_iv else None,
                        spot=float(df_iv['spot'].iloc[0]) if 'spot' in df_iv else None, r=r, q=q, meta={})
        session.add(snap)
        session.flush()
        for _, row in df_iv.iterrows():
            op = OptionPoint(snapshot_id=snap.id,
                             strike=float(row.get('strike')) if row.get('strike') is not None else None,
                             expiration=row.get('expirationDate').to_pydatetime() if row.get('expirationDate') is not None else None,
                             mid=float(row.get('mid')) if row.get('mid') is not None else None,
                             iv=float(row.get('iv')) if row.get('iv') is not None else None,
                             data={})
            session.add(op)
        session.commit()
        logger.info("Snapshot saved for %s id=%s", ticker, snap.id)
        return snap.id
    except Exception as e:
        session.rollback()
        logger.exception("Failed to persist snapshot: %s", e)
    finally:
        session.close()

def start_scheduler(tickers, interval_minutes=30):
    init_db()
    sched = BackgroundScheduler()
    for t in tickers:
        # use default args capture
        def job(ticker=t):
            return take_snapshot(ticker)
        sched.add_job(job, 'interval', minutes=interval_minutes, id=f"snap_{t}")
    sched.start()
    return sched
