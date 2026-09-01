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
        print(f"Telegram sent: {r.status_code}")
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
            if r.status_code != 200: return []
            data = r.json()
            return [[int(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])] for c in data]
        except:
            time.sleep(0.5)
    return []

def main():
    print("Starting Daily Volume Engulf Screener...")
    engulf_list = []
    no_engulf = []

    for delta_sym in TOP34_DELTA:
        bin_sym = BINANCE_MAP[delta_sym]
        daily = fetch_daily(bin_sym, 60)
        if len(daily) < 2: continue
        
        prev = daily[-2]
        curr = daily[-1]
        prev_vol = float(prev[5])
        curr_vol = float(curr[5])
        prev_close = float(prev[4])
        curr_close = float(curr[4])
        curr_open = float(curr[1])
        
        ratio = curr_vol / prev_vol if prev_vol>0 else 0
        
        if curr_vol > prev_vol:
            color = "🟢 GREEN" if curr_close > curr_open else "🔴 RED"
            strength = "🔥 STRONG" if ratio >= 1.5 else "✓ NORMAL"
            engulf_list.append({
                'coin': delta_sym,
                'ratio': ratio,
                'color': color,
                'strength': strength,
                'close': curr_close,
                'curr_vol': curr_vol,
                'prev_vol': prev_vol
            })
        else:
            no_engulf.append(delta_sym)

    # Build Telegram message
    today = datetime.now().strftime('%Y-%m-%d')
    msg = f"*📊 DAILY VOLUME ENGULF SCREENER*\n"
    msg += f"Date: {today}\n"
    msg += f"Timeframe: 1D | Coins: TOP34 Delta\n"
    msg += f"--------------------------------\n"
    
    if engulf_list:
        # Sort by ratio
        engulf_list_sorted = sorted(engulf_list, key=lambda x: x['ratio'], reverse=True)
        msg += f"*✓ ENGULF FOUND: {len(engulf_list)}/{len(TOP34_DELTA)}*\n\n"
        for e in engulf_list_sorted:
            msg += f"{e['strength']} *{e['coin']}* | {e['ratio']:.2f}x | {e['color']} | ${e['close']:.4f}\n"
        
        msg += f"\n*Strong = 1.5x+ volume*\n"
        msg += f"No Engulf: {', '.join(no_engulf[:10])}{'...' if len(no_engulf)>10 else ''}"
    else:
        msg += f"*No Volume Engulf Today*\nAll 34 coins me kal se kam volume hai."

    print(msg)
    send_telegram(msg)

if __name__ == "__main__":
    main()
