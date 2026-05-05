import json
import os
import requests
from dotenv import load_dotenv
from fast_flights import FlightQuery, Passengers, ShoppingOptions, create_query, get_flights

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

    # 1. Telegram'dan gelen komutları işle
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

    liste.sort(key=lambda x: (x['kalkis'], x['varis']))
    gecerli_rota = None

    for r in liste:
        try:
            print(f"Aranıyor: {r['kalkis']} -> {r['varis']}")
            
            # 2. DEĞİŞİKLİK: Sorguyu önceden TL ve Türkçe olarak oluşturuyoruz
            query = create_query(
                flights=[
                    FlightQuery(date=r['tarih'], from_airport=r['kalkis'], to_airport=r['varis'])
                ],
                trip="one-way",
                seat="economy",
                passengers=Passengers(adults=1),
                language="tr",
                currency="TRY"
            )

            # ShoppingOptions ile ucuzdan pahalıya sıralı çekiyoruz
            sonuc = get_flights(
                query,
                shopping=ShoppingOptions(ranking_mode="cheapest", result_sort="price")
            )

            # 3. DEĞİŞİKLİK: Sonuçları yeni yapıya göre okuyoruz
            if sonuc:
                ucus_info = sonuc[0]
                fiyat_metni = str(getattr(ucus_info, 'price', 'Bulunamadı'))
            else:
                ucus_info = None
                fiyat_metni = "Bulunamadı"

            # Fiyatı rakama çevirip güvenli kontrol yapıyoruz
            temiz_fiyat_str = "".join(filter(str.isdigit, fiyat_metni))
            temiz_fiyat = int(temiz_fiyat_str) if temiz_fiyat_str else float('inf')
            durum = "🔥 UYGUN!" if "TRY" in fiyat_metni and temiz_fiyat <= r['hedef'] else "⌛ Beklemede"
            
            su_anki_rota = (r['kalkis'], r['varis'])
            
            if su_anki_rota != gecerli_rota:
                if gecerli_rota is not None:
                    rapor += "------------------\n"
                rapor += f"📍 <b>{r['kalkis']} ✈️ {r['varis']}</b>\n"
                gecerli_rota = su_anki_rota
            
            # Eğer uçuş bulunduysa bilgileri al (name yerine airlines kullanılıyor)
            if ucus_info:
                # 1. Havayolu listesini metne çevir (Örn: ['AJet'] -> 'AJet')
                airlines_list = getattr(ucus_info, 'airlines', [])
                havayolu = ", ".join(airlines_list) if airlines_list else "Bilinmiyor"
                
                # 2. Uçuş saatleri, ana objenin içindeki 'flights' adlı alt listede duruyor
                if hasattr(ucus_info, 'flights') and len(ucus_info.flights) > 0:
                    ilk_bacak = ucus_info.flights[0] # SingleFlight objesi
                    kalkis_objesi = getattr(ilk_bacak, 'departure', None)
                    varis_objesi = getattr(ilk_bacak, 'arrival', None)
                else:
                    kalkis_objesi, varis_objesi = None, None

                # SimpleDatetime objesini "HH:MM" formatına çeviren yardımcı
                def saat_cevir(dt_obj):
                    try:
                        t = getattr(dt_obj, 'time', [])
                        if len(t) >= 2: return f"{t[0]:02d}:{t[1]:02d}"
                        elif len(t) == 1: return f"{t[0]:02d}:00"
                    except: pass
                    return "--:--"

                k_saat = saat_cevir(kalkis_objesi)
                v_saat = saat_cevir(varis_objesi)
            else:
                havayolu, k_saat, v_saat = "Uçuş Yok", "--:--", "--:--"

            rapor += f"  🆔 <b>{r['id']}</b> | 📅 {r['tarih']} | {havayolu}\n"
            rapor += f"  🕒 <b>{k_saat} ➡️ {v_saat}</b>\n"
            rapor += f"  💰 {fiyat_metni} | 🎯 {r['hedef']} | {durum}\n\n"
            
        except Exception as e:
            rapor += f"🆔 {r['id']}: {r['kalkis']}-{r['varis']} veri çekilemedi. ({e})\n\n"

    rapor += "\n<i>Not: Rota silmek için 'sil ID' yazıp gönderebilirsiniz.</i>"
    telegram_mesaj_gonder(rapor)

if __name__ == "__main__":
    main()