import json
import os
import requests
from dotenv import load_dotenv
from fast_flights import get_flights, FlightData, Passengers

load_dotenv()

# Yapılandırma
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CONFIG_DOSYASI = os.getenv("KONFIG_DOSYASI")

def telegram_get_updates():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    response = requests.get(url).json()
    return response.get("result", [])

def telegram_mesaj_gonder(mesaj):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"})

def listeyi_oku():
    if os.path.exists(CONFIG_DOSYASI):
        with open(CONFIG_DOSYASI, "r") as f:
            return json.load(f)
    return []

def listeyi_kaydet(liste):
    with open(CONFIG_DOSYASI, "w") as f:
        json.dump(liste, f, indent=2)

def main():
    liste = listeyi_oku()
    updates = telegram_get_updates()
    degisiklik_var = False
    bilgi_notu = ""

    # 1. Telegram'dan gelen komutları işle (Örn: "sil 1" veya "ekle IST LHR 2026-06-15 4000")
    for update in updates:
        if "message" in update and str(update["message"]["chat"]["id"]) == CHAT_ID:
            text = update["message"]["text"].lower()
            
            if text.startswith("sil "):
                silinecek_id = int(text.split(" ")[1])
                liste = [r for r in liste if r["id"] != silinecek_id]
                degisiklik_var = True
                bilgi_notu += f"✅ ID {silinecek_id} listeden çıkarıldı.\n"
            
            elif text.startswith("ekle "):
                # Format: ekle IST LHR 2026-06-15 4000
                parcalar = text.split(" ")
                yeni_id = max([r["id"] for r in liste], default=0) + 1
                yeni_rota = {
                    "id": yeni_id,
                    "kalkis": parcalar[1].upper(),
                    "varis": parcalar[2].upper(),
                    "tarih": parcalar[3],
                    "hedef": int(parcalar[4])
                }
                liste.append(yeni_rota)
                degisiklik_var = True
                bilgi_notu += f"✅ Yeni rota eklendi (ID: {yeni_id}).\n"

    if degisiklik_var:
        listeyi_kaydet(liste)

    # 2. Uçuşları Tara
    rapor = "📊 <b>UÇUŞ DURUM RAPORU</b>\n\n"
    if bilgi_notu: rapor += f"{bilgi_notu}\n"

    # Rotaları gruplamak için kalkış ve varış noktasına göre sıralıyoruz
    liste.sort(key=lambda x: (x['kalkis'], x['varis']))
    
    gecerli_rota = None

    for r in liste:
        try:
            print(f"Aranıyor: {r['kalkis']} -> {r['varis']}")
            sonuc = get_flights(
                flight_data=[FlightData(date=r['tarih'], from_airport=r['kalkis'], to_airport=r['varis'])],
                trip="one-way", seat="economy",
                passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0)
            )
            fiyat_metni = sonuc.flights[0].price if sonuc.flights else "Bulunamadı"
            # Fiyat uygunluk kontrolü
            durum = "🔥 UYGUN!" if "TRY" in fiyat_metni and int("".join(filter(str.isdigit, fiyat_metni))) <= r['hedef'] else "⌛ Beklemede"
            
            su_anki_rota = (r['kalkis'], r['varis'])
            
            # Eğer rota değiştiyse (yeni bir şehir çiftine geçildiyse)
            if su_anki_rota != gecerli_rota:
                # İlk rotadan sonra geliyorsa ayırıcı ekle
                if gecerli_rota is not None:
                    rapor += "------------------\n"
                # Rota başlığını yaz (Örn: IST ✈️ LHR)
                rapor += f"📍 <b>{r['kalkis']} ✈️ {r['varis']}</b>\n"
                gecerli_rota = su_anki_rota
            
            ucus_info = sonuc.flights[0]

            info = {
                "name": str(getattr(ucus_info, 'name', 'Bilinmiyor')),
                "departure": str(getattr(ucus_info, 'departure', 'Bilinmiyor')),
                "arrival": str(getattr(ucus_info, 'arrival', 'Bilinmiyor'))
            }

            rapor += f"  🆔 <b>{r['id']}</b> | 📅 {r['tarih']} | {info['name']}\n"
            rapor += f"  🆔 <b> {info['departure']}| {info['arrival']}</b>\n"
            rapor += f"  💰 {fiyat_metni} | 🎯 {r['hedef']} | {durum}\n\n"
            
        except Exception as e:
            rapor += f"🆔 {r['id']}: {r['kalkis']}-{r['varis']} veri çekilemedi.\n"

    rapor += "\n<i>Not: Rota silmek için 'sil ID' yazıp gönderebilirsiniz.</i>"
    telegram_mesaj_gonder(rapor)

if __name__ == "__main__":
    main()