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
        print(msg)
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        r = requests.post(url, json=data, timeout=10)
        print(f"Telegram: {r.status_code}")
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

def get_candle_color(open_p, close_p):
    if close_p > open_p: return "GREEN"
    elif close_p < open_p: return "RED"
    else: return "DOJI"

def main():
    print("SCREENER: Volume Engulf + Color Flip (Kal vs Parso)")
    engulf_list = []
    no_engulf = []

    for delta_sym in TOP34_DELTA:
        bin_sym = BINANCE_MAP[delta_sym]
        daily = fetch_daily(bin_sym, 60)
        if len(daily) < 3: continue
        
        prev_prev = daily[-3]  # Parso
        prev = daily[-2]       # Kal
        
        pp_open, pp_close, pp_vol = float(prev_prev[1]), float(prev_prev[4]), float(prev_prev[5])
        p_open, p_close, p_vol = float(prev[1]), float(prev[4]), float(prev[5])
        
        pp_color = get_candle_color(pp_open, pp_close)
        p_color = get_candle_color(p_open, p_close)
        
        ratio = p_vol / pp_vol if pp_vol>0 else 0
        
        # CONDITION 1: Volume Engulf
        vol_engulf = p_vol > pp_vol
        
        # CONDITION 2: Color Flip - GREEN to RED or RED to GREEN
        color_flip = (pp_color == "GREEN" and p_color == "RED") or (pp_color == "RED" and p_color == "GREEN")
        # Doji ko invalid maan rahe hai
        
        if vol_engulf and color_flip:
            strength = "🔥 STRONG" if ratio >= 1.5 else "✓ NORMAL"
            # Flip direction
            flip_txt = f"{pp_color}→{p_color}"
            if pp_color=="GREEN" and p_color=="RED": emoji = "🔴 Bearish Engulf"
            else: emoji = "🟢 Bullish Engulf"
            
            engulf_list.append({
                'coin': delta_sym,
                'ratio': ratio,
                'strength': strength,
                'flip': flip_txt,
                'emoji': emoji,
                'close': p_close,
                'p_vol': p_vol,
                'pp_vol': pp_vol
            })
            print(f"✓ {delta_sym} {flip_txt} {ratio:.2f}x")
        else:
            reason = []
            if not vol_engulf: reason.append("no vol")
            if not color_flip: reason.append(f"same color {pp_color}->{p_color}")
            no_engulf.append(delta_sym)
            print(f"  {delta_sym} No - {', '.join(reason)}")

    today = datetime.now().strftime('%Y-%m-%d')
    msg = f"*📊 VOLUME ENGULF + COLOR FLIP*\n"
    msg += f"Date: {today} | Kal vs Parso (Closed)\n"
    msg += f"Logic: Vol↑ + Color GREEN↔RED\n"
    msg += f"--------------------------------\n"
    
    if engulf_list:
        engulf_list = sorted(engulf_list, key=lambda x: x['ratio'], reverse=True)
        msg += f"*✓ FOUND: {len(engulf_list)}/{len(TOP34_DELTA)}*\n\n"
        for e in engulf_list:
            msg += f"{e['strength']} *{e['coin']}* | {e['flip']} | {e['ratio']:.2f}x | {e['emoji']} | ${e['close']:.4f}\n"
    else:
        msg += f"*No Engulf + Flip Today*\n"
        msg += f"Ya toh volume kam tha ya color same tha."

    print("\n" + msg)
    send_telegram(msg)

if __name__ == "__main__":
    main()
