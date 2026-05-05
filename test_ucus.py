from fast_flights import get_flights, FlightData, Passengers

def bilet_fiyatlarini_getir():
    print("✈️ Google Flights üzerinden fiyatlar taranıyor...")
    try:
        sonuc = get_flights(
            flight_data=[FlightData(date="2026-06-06", from_airport="SZF", to_airport="SAW")],
            trip="one-way",
            seat="economy",
            passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
        )
        if sonuc.flights:
            en_ucuz = sonuc.flights[0]
            temiz_fiyat = int("".join(filter(str.isdigit, en_ucuz.price)))
            print(f"✅ BAŞARILI! Bulunan En Ucuz Fiyat: {temiz_fiyat} TL")
        else:
            print("❌ Uçuş bulunamadı.")
        sonuc = sonuc.flights[0]
        info = [getattr(sonuc, 'name', 'Bilinmiyor'), getattr(sonuc, 'departure', 'Bilinmiyor'), getattr(sonuc, 'arrival', 'Bilinmiyor')]
        
        rapor = ""
        rapor += f"  🆔 <b>{info[0]}</b>\n"
        rapor += f"  🆔 <b> {info[1]}| {info[2]}</b>\n"
        print(rapor)
    except Exception as e:
        print(f"❌ Bir hata oluştu: {e}")

if __name__ == "__main__":
    bilet_fiyatlarini_getir()