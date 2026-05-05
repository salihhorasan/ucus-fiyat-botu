from fast_flights import FlightQuery, Passengers, ShoppingOptions, create_query, get_flights

def bilet_fiyatlarini_getir():
    print("✈️ Google Flights üzerinden fiyatlar taranıyor...")
    try:
        # 1. ADIM: Sorguyu ve Para Birimini/Dili Oluştur (Dokümantasyondaki gibi)
        query = create_query(
            flights=[
                FlightQuery(
                    date="2026-06-06",
                    from_airport="SZF",
                    to_airport="SAW",
                ),
            ],
            trip="one-way",
            seat="economy",
            passengers=Passengers(adults=1),
            language="tr",   # Türkçe zorlaması
            currency="TRY",  # TL zorlaması
        )

        # 2. ADIM: Uçuşları Çek (ShoppingOptions ile ucuzdan pahalıya)
        results = get_flights(
            query,
            shopping=ShoppingOptions(
                ranking_mode="cheapest",
                result_sort="price",
            ),
        )

        # 3. ADIM: Sonuçları Oku (Dokümantasyonda doğrudan liste döndüğü görülüyor)
        if results:
            print(results)
            en_ucuz = results[0]
            
            # Dokümantasyonda 'price' ve 'airlines' olarak kullanılmış
            fiyat_metni = getattr(en_ucuz, 'price', 'Bulunamadı')
            temiz_fiyat = int("".join(filter(str.isdigit, str(fiyat_metni)))) if any(c.isdigit() for c in str(fiyat_metni)) else 0
            
            print(f"✅ BAŞARILI! Gelen Ham Fiyat: {fiyat_metni}")
            print(f"💰 Temizlenen Rakam: {temiz_fiyat} TL")
            print("-" * 20)
            
            h_adi = getattr(en_ucuz, 'airlines', 'Bilinmiyor')
            
            rapor = ""
            rapor += f"  ✈️ <b>{h_adi}</b>\n"
            rapor += f"  💰 {fiyat_metni}\n"
            print(rapor)
            
        else:
            print("❌ Uçuş bulunamadı.")
            
    except Exception as e:
        print(f"❌ Bir hata oluştu: {e}")

if __name__ == "__main__":
    bilet_fiyatlarini_getir()