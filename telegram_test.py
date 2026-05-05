import requests

# BotFather'dan aldığın uzun şifre
BOT_TOKEN = "8674442880:AAFPYhsGnSXlDJzGTl-CfNA4m_knaVEdk8Q" 

# Kendi numaran
CHAT_ID = "1360758527" 

def telegram_mesaj_gonder(mesaj):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML" # Metni kalın/eğik yazabilmek için
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print("✅ Mesaj başarıyla telefonuna gönderildi! Bildirim geldi mi?")
    else:
        print(f"❌ Bir hata oluştu: {response.text}")

# Test mesajımızı gönderelim
test_mesaji = "🚨 <b>DİKKAT!</b>\n\nİstanbul - Londra uçuşu <b>3500 TL</b>'ye düştü!\n\nHemen kontrol et."

telegram_mesaj_gonder(test_mesaji)