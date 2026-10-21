#!/usr/bin/env python3
"""Fetch public daily historical OHLC into static JSON. Never submits orders."""
import datetime as dt
import json
import pathlib
import sys
import yfinance as yf

ROOT = pathlib.Path(__file__).resolve().parent
DEST = ROOT / 'data'
DEST.mkdir(exist_ok=True)
SYMBOLS = {'GOLD': 'GC=F', 'BTC': 'BTC-USD', 'USDJPY': 'JPY=X'}
errors = []
for market, ticker in SYMBOLS.items():
    try:
        frame = yf.download(ticker, period='2y', interval='1d', auto_adjust=False, progress=False, threads=False)
        if frame.empty:
            raise ValueError('API returned no data')
        if getattr(frame.columns, 'nlevels', 1) > 1:
            frame.columns = frame.columns.get_level_values(0)
        frame = frame.dropna(subset=['Open','High','Low','Close'])
        rows = []
        for timestamp, row in frame.iterrows():
            prices = {key: float(row[col]) for key, col in [('open','Open'),('high','High'),('low','Low'),('close','Close')]}
            if min(prices.values()) <= 0:
                continue
            rows.append({'date': timestamp.strftime('%Y-%m-%d'), **{k: round(v, 8) for k,v in prices.items()}})
        if len(rows) < 70:
            raise ValueError(f'Only {len(rows)} valid bars')
        payload = {'market': market, 'symbol': ticker, 'source': 'Yahoo Finance via yfinance ('+ticker+')',
                   'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'rows': rows}
        (DEST / f'{market}.json').write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':'))+'\n')
        print(f'{market}: {len(rows)} rows through {rows[-1]["date"]}')
    except Exception as exc:
        errors.append(f'{market}: {exc}')
        print(errors[-1], file=sys.stderr)
if errors:
    print('Failed markets retain their last successful data (if any).', file=sys.stderr)
    sys.exit(1)
