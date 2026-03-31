from flask import Flask, render_template, request, redirect, url_for
import requests
import sqlite3
import threading
import datetime

app = Flask(__name__)

# ================== UBAH 3 BAGIAN INI ==================
INDIWTf_TOKEN = "9863f19e46b1d9137dd8c6d2c78ebf67"
TELEGRAM_BOT_TOKEN = "8664199635:AAFRgbcRhlGTUbm24BpmF5Z9-93AVi22gdM"
TELEGRAM_CHAT_ID = "-5170702655"

DOMAINS = [
    "daywinbetmerahputih.com",
    "terasgobet.com",
    # Tambahkan domain kamu di sini
]
# ======================================================

def init_db():
    conn = sqlite3.connect('domains.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS status 
                 (domain TEXT PRIMARY KEY, status TEXT, last_check TEXT)''')
    conn.commit()
    conn.close()

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, json=data, timeout=10)
    except:
        pass

def cek_domain(domain):
    try:
        url = f"https://indiwtf.com/api/check?domain={domain}&token={INDIWTf_TOKEN}"
        r = requests.get(url, timeout=15)
        data = r.json()

        status = "AMAN"
        if data.get("status") == "blocked":
            status = "BLOKIR"
        elif "error" in str(data).lower():
            status = "ERROR"

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect('domains.db')
        c = conn.cursor()
        c.execute("REPLACE INTO status VALUES (?, ?, ?)", (domain, status, now))
        conn.commit()
        conn.close()

        if status == "BLOKIR":
            send_telegram(f"🚨 <b>DOMAIN DIBLOKIR</b>\nDomain: {domain}\nWaktu: {now}")

        return status
    except:
        return "ERROR"

def background_checker():
    while True:
        for domain in DOMAINS:
            cek_domain(domain)
        time.sleep(300)

@app.route('/')
def dashboard():
    conn = sqlite3.connect('domains.db')
    c = conn.cursor()
    c.execute("SELECT * FROM status ORDER BY domain")
    rows = c.fetchall()
    conn.close()

    domains_list = [{'domain': row[0], 'status': row[1], 'last_check': row[2]} for row in rows]

    for d in DOMAINS:
        if not any(x['domain'] == d for x in domains_list):
            domains_list.append({'domain': d, 'status': 'WAITING', 'last_check': 'Belum dicek'})

    return render_template('index.html', domains=domains_list)

@app.route('/refresh')
def refresh():
    for domain in DOMAINS:
        cek_domain(domain)
    return redirect(url_for('dashboard'))

@app.route('/add', methods=['POST'])
def add_domain():
    new_domain = request.form.get('domain', '').strip()
    if new_domain and new_domain not in DOMAINS:
        DOMAINS.append(new_domain)
        cek_domain(new_domain)
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    threading.Thread(target=background_checker, daemon=True).start()