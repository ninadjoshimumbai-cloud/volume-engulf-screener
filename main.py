import requests, os, time
from datetime import datetime

TOP34_DELTA = [
    'LINKUSD','FETUSD','PEPEUSD','ADAUSD','AVAXUSD','GALAUSD','LDOUSD','ALGOUSD',
    'NEARUSD','SANDUSD','JUPUSD','TONUSD','WIFUSD','INJUSD','ARUSD','ARBUSD',
    'ETHUSD','SUIUSD','FILUSD','POLUSD','FLOWUSD','IMXUSD','STXUSD','ATOMUSD',
    'TRXUSD','RNDRUSD','ETCUSD','SHIBUSD','HBARUSD','BCHUSD','TIAUSD','XRPUSD',
    'SOLUSD','VETUSD'
]
BINANCE_MAP = {c: c[:-3] + 'USDT' for c in TOP34_DELTA}

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram secrets not set")
        print(msg)
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        r = requests.post(url, json=data, timeout=10)
        print(f"Telegram sent: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Telegram error: {e}")

def fetch_daily(sym, limit=60):
    for _ in range(3):
        try:
            url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval=1d&limit={limit}"
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                url = url.replace("data-api.binance.vision","api.binance.com")
                r = requests.get(url, timeout=10)
            if r.status_code != 200: 
                return []
            data = r.json()
            return [[int(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])] for c in data]
        except Exception as e:
            print(f"Fetch error {sym}: {e}")
            time.sleep(0.5)
    return []

def main():
    print("Starting Daily Volume Engulf Screener - FIXED LOGIC")
    print("Logic: Kal (closed) vs Parso (closed)")
    
    engulf_list = []
    no_engulf = []

    for delta_sym in TOP34_DELTA:
        bin_sym = BINANCE_MAP[delta_sym]
        daily = fetch_daily(bin_sym, 60)
        
        if len(daily) < 3:
            print(f"{delta_sym}: Not enough data")
            continue
        
        # FIXED LOGIC
        # daily[-1] = Aaj ki running candle (IGNORE)
        # daily[-2] = Kal ki closed candle (PREVIOUS)
        # daily[-3] = Parso ki closed candle (PREVIOUS TO PREVIOUS)
        
        prev_prev = daily[-3]  # Parso
        prev = daily[-2]       # Kal - Last closed
        
        prev_prev_vol = float(prev_prev[5])
        prev_vol = float(prev[5])
        prev_close = float(prev[4])
        prev_open = float(prev[1])
        
        ratio = prev_vol / prev_prev_vol if prev_prev_vol > 0 else 0
        
        # ENGULF CHECK: Kal ka Volume > Parso ka Volume
        if prev_vol > prev_prev_vol:
            color = "🟢 GREEN" if prev_close > prev_open else "🔴 RED"
            strength = "🔥 STRONG" if ratio >= 1.5 else "✓ NORMAL"
            engulf_list.append({
                'coin': delta_sym,
                'ratio': ratio,
                'color': color,
                'strength': strength,
                'close': prev_close,
                'prev_vol': prev_vol,
                'prev_prev_vol': prev_prev_vol
            })
            print(f"✓ {delta_sym} ENGULF | {ratio:.2f}x | {color}")
        else:
            no_engulf.append(delta_sym)
            print(f"  {delta_sym} No engulf | {ratio:.2f}x")

    # Build Telegram message
    today = datetime.now().strftime('%Y-%m-%d')
    msg = f"*📊 DAILY VOLUME ENGULF - CLOSED CANDLES*\n"
    msg += f"Date: {today} | Check: Kal vs Parso\n"
    msg += f"Timeframe: 1D | Coins: TOP34 Delta\n"
    msg += f"--------------------------------\n"
    
    if engulf_list:
        engulf_list_sorted = sorted(engulf_list, key=lambda x: x['ratio'], reverse=True)
        msg += f"*✓ ENGULF FOUND: {len(engulf_list)}/{len(TOP34_DELTA)}*\n\n"
        for e in engulf_list_sorted:
            msg += f"{e['strength']} *{e['coin']}* | {e['ratio']:.2f}x | {e['color']} | ${e['close']:.4f}\n"
        
        msg += f"\n_Strong = 1.5x+ volume_\n"
        if no_engulf:
            msg += f"No Engulf: {', '.join(no_engulf[:8])}{'...' if len(no_engulf)>8 else ''}"
    else:
        msg += f"*No Volume Engulf*\nKal ka volume parso se kam tha sab me."

    print("\n" + msg)
    send_telegram(msg)

if __name__ == "__main__":
    main()
